//! Playback state, transport messages and track controls.

use std::{
    collections::HashMap,
    error::Error,
    fs::File,
    path::{Path, PathBuf},
    time::Duration,
};

use iced::{
    alignment::Vertical,
    mouse, time,
    widget::{
        self,
        canvas::{self, Canvas},
        row, text,
    },
    Color, Element, Length, Point, Rectangle, Renderer, Size, Subscription, Task, Theme,
};
use rodio::{mixer::Mixer, source::Source, Decoder, Player as AudioPlayer};

use crate::app::{
    app,
    icons::Icon,
    pixel,
    player::{
        events::Events,
        output::{AudioOutput, DeviceKey, MidiResume, Opened, OutputError},
    },
    theme::Colors,
};

/// Segments of the progress bar, and the gap between them.
const SEGMENTS: usize = 40;
const SEGMENT_GAP: f32 = 2.0;

pub(crate) struct GlobalState {
    output: Option<AudioOutput>,
    soundfont: String,
    events: Events,
    /// Identifies the current output attempt; late callbacks from retired streams are ignored.
    generation: u64,
    opening: Option<u64>,
    retry: bool,
    checking: bool,
    last_error: Option<String>,
    /// Headless tests use the transport without device subscriptions.
    enabled: bool,
    playing_track: Option<PlayerId>,
    /// Retain the last MIDI channel state even when switching outputs while paused.
    midi_track: Option<PlayerId>,
    tempo: u16,
    audio_player_cache: HashMap<PathBuf, AudioPlayerController>,
}

impl GlobalState {
    pub(crate) fn new(sf: &str) -> Self {
        let events = Events::new();
        events.changed(0);
        Self {
            output: None,
            soundfont: sf.into(),
            events,
            generation: 0,
            opening: None,
            retry: false,
            checking: false,
            last_error: None,
            enabled: true,
            playing_track: None,
            midi_track: None,
            tempo: 120,
            audio_player_cache: HashMap::new(),
        }
    }

    #[cfg(test)]
    pub(crate) fn headless() -> Self {
        let mut state = Self::new(soundfont::path());
        state.output = Some(AudioOutput::headless(soundfont::path(), 44100).0);
        state.enabled = false;
        state
    }

    fn play(&mut self, track: &mut Track) -> Result<(), Box<dyn Error>> {
        if !track.path.exists() {
            track.is_playing = false;
            self.playing_track = self.playing_track.filter(|id| *id != track.id);
            return Ok(()); // the view displays the missing file
        }
        if self.output.is_some() {
            match track.id {
                PlayerId::Midi(_) => self.play_midi(track)?,
                PlayerId::Audio(_) => self.play_audio(track)?,
            }
        }
        // During reconnection this is the user's intent; ticks remain suspended.
        track.is_playing = true;
        self.playing_track = Some(track.id);
        Ok(())
    }

    fn play_midi(&mut self, track: &Track) -> Result<(), Box<dyn Error>> {
        if let Some(output) = &mut self.output {
            let resume = MidiResume {
                path: track.path.clone(),
                position: track.position,
                tempo: self.tempo,
                playing: true,
            };
            if output.prepared_midi.take().as_ref() != Some(&resume) {
                output.midi.set_file(Some(&track.path))?;
                output.midi.set_position(track.position);
            }
            output.midi.set_tempo(f32::from(self.tempo));
            output.play_midi();
            self.midi_track = Some(track.id);
        }
        Ok(())
    }

    fn play_audio(&mut self, track: &Track) -> Result<(), Box<dyn Error>> {
        let Some(output) = &self.output else {
            return Ok(());
        };
        // Seek the decoder before connecting it: rodio's Player::try_seek waits for the audio
        // callback, which may have stopped after a device disconnect.
        let controller = AudioPlayerController::new(track, &output.mixer)?;
        self.audio_player_cache
            .entry(track.path.clone())
            .insert_entry(controller)
            .get()
            .player
            .play();
        Ok(())
    }

    fn pause(&mut self, track: &mut Track) {
        if self.is_playing(track.id) && self.output.is_some() {
            match track.id {
                PlayerId::Midi(_) => {
                    if let Some(output) = &mut self.output {
                        output.pause_midi();
                    }
                }
                PlayerId::Audio(_) => self.pause_audio(track),
            }
            self.on_tick(track);
        }
        track.is_playing = false;
        self.playing_track = self.playing_track.filter(|playing| *playing != track.id);
    }

    fn pause_audio(&self, track: &Track) {
        if let Some(controller) = self.audio_player_cache.get(&track.path) {
            controller.pause();
        }
    }

    fn set_position(&mut self, track: &mut Track, position: f64) {
        track.position = position;
        if self.is_playing(track.id) {
            self.seek(track, position);
        }
    }

    fn is_playing(&self, id: PlayerId) -> bool {
        self.playing_track.is_some_and(|playing| playing == id)
    }

    fn seek(&mut self, track: &Track, position: f64) {
        match track.id {
            PlayerId::Midi(_) => {
                if let Some(output) = &self.output {
                    output.midi.set_position(position);
                }
            }
            PlayerId::Audio(_) => {
                if let Err(error) = self.play_audio(track) {
                    eprintln!("Cannot seek audio: {error}");
                }
            }
        }
    }

    pub(crate) fn tempo(&self) -> u16 {
        self.tempo
    }

    pub(crate) fn set_tempo(&mut self, tempo: u16) {
        self.tempo = tempo;
        if let Some(output) = &mut self.output {
            output.midi.set_tempo(f32::from(tempo));
        }
    }

    pub(crate) fn playing(&self) -> bool {
        self.playing_track.is_some() && self.output.is_some()
    }

    /// Release media before it moves or disappears. Log entries deliberately retain their old
    /// paths.
    pub(crate) fn release_files(
        &mut self,
        entries: &mut [app::Output],
        affected: impl Fn(&Path) -> bool,
    ) {
        let mut released_midi = false;
        let mut released = false;
        for entry in entries {
            if let app::Output::Player(track) = entry {
                if affected(&track.path) {
                    released |=
                        self.playing_track == Some(track.id) || self.midi_track == Some(track.id);
                    self.pause(track);
                    self.audio_player_cache.remove(&track.path);
                    if self.midi_track == Some(track.id) {
                        self.midi_track = None;
                        released_midi = true;
                    }
                }
            }
        }
        if released_midi {
            if let Some(output) = &mut self.output {
                output.prepared_midi = None;
                // MIDI is already in memory, with no open file handle. Do not enqueue an unload:
                // midi-player's one-slot queue can be full while an output is disconnected.
            }
        }
        // A device reconnect may still be preparing a MIDI file which has just been removed.
        if released && self.opening.is_some() {
            self.generation += 1;
            self.events.set_generation(self.generation);
        }
    }

    fn on_tick(&mut self, track: &mut Track) {
        let Some(output) = &self.output else {
            return;
        };
        let position = match track.id {
            PlayerId::Midi(_) => output.midi.position(),
            PlayerId::Audio(_) => self
                .audio_player_cache
                .get(&track.path)
                .map(|controller| controller.position())
                .unwrap_or(track.position),
        };
        track.position = position;
        if position >= 1.0 {
            track.is_playing = false;
            track.position = 0.0;
            self.playing_track = None;
        }
    }

    /// Save the live playhead before releasing anything tied to the old mixer.
    fn suspend_output(&mut self, tracks: &mut [app::Output]) {
        if let Some(output) = &mut self.output {
            output.pause();
        }
        if let Some(app::Output::Player(track)) =
            self.playing_track.and_then(|id| tracks.get_mut(id.inner()))
        {
            self.pause_audio(track);
            self.on_tick(track);
        }
        self.audio_player_cache.clear();
        self.output = None;
        self.checking = false;
    }

    fn reopen(&mut self, tracks: &mut [app::Output]) -> Task<Message> {
        self.generation += 1;
        self.events.set_generation(self.generation);
        self.retry = false;
        if self.opening.is_some() {
            // Finish the existing open before starting another large SoundFont load.
            return Task::none();
        }
        self.suspend_output(tracks);
        self.open(tracks)
    }

    fn open(&mut self, tracks: &[app::Output]) -> Task<Message> {
        let generation = self.generation;
        self.events.set_generation(generation);
        self.opening = Some(generation);
        let sf = self.soundfont.clone();
        let events = self.events.clone();
        let resume = self
            .playing_track
            .filter(|id| matches!(id, PlayerId::Midi(_)))
            .or(self.midi_track)
            .and_then(|id| tracks.get(id.inner()))
            .and_then(|output| match output {
                app::Output::Player(track) if matches!(track.id, PlayerId::Midi(_)) => {
                    Some(MidiResume {
                        path: track.path.clone(),
                        position: track.position,
                        tempo: self.tempo,
                        playing: self.playing_track == Some(track.id),
                    })
                }
                _ => None,
            });
        Message::background(move || {
            let result = Opened::new(AudioOutput::open(&sf, events, generation, resume));
            Message::OutputOpened(generation, result)
        })
    }

    fn opened(
        &mut self,
        tracks: &mut Vec<app::Output>,
        generation: u64,
        opened: Opened,
    ) -> Task<Message> {
        let Some(result) = opened.take() else {
            return Task::none();
        };
        if self.opening != Some(generation) {
            return Task::none();
        }
        self.opening = None;
        if generation != self.generation {
            drop(result);
            return self.open(tracks);
        }
        match result.and_then(|output| {
            output.start()?;
            Ok(output)
        }) {
            Ok(output) => {
                self.output = Some(output);
                self.retry = false;
                self.last_error = None;
                if let Some(app::Output::Player(track)) =
                    self.playing_track.and_then(|id| tracks.get_mut(id.inner()))
                {
                    if let Err(error) = self.play(track) {
                        track.is_playing = false;
                        self.playing_track = None;
                        tracks.push(app::Output::Error(error.to_string()));
                    }
                }
            }
            Err(error) => {
                self.retry = error.retryable();
                if !self.retry {
                    if let Some(app::Output::Player(track)) =
                        self.playing_track.and_then(|id| tracks.get_mut(id.inner()))
                    {
                        track.is_playing = false;
                    }
                    self.playing_track = None;
                }
                if !matches!(error, OutputError::Changed) {
                    let message = error.to_string();
                    if self.last_error.as_ref() != Some(&message) {
                        tracks.push(app::Output::Error(message.clone()));
                        self.last_error = Some(message);
                    }
                }
            }
        }
        Task::none()
    }

    /// Only backends without route notifications need this slow background check.
    fn check_output(&mut self) -> Task<Message> {
        if self.checking {
            return Task::none();
        }
        let Some(output) = &self.output else {
            return Task::none();
        };
        let device = output.device.clone();
        let generation = self.generation;
        self.checking = true;
        Message::background(move || {
            let unchanged = DeviceKey::current().is_ok_and(|current| current == device);
            Message::OutputChecked(generation, unchanged)
        })
    }
}

/// Output notifications stay subscribed even when no track is playing.
pub(crate) fn subscription(state: &GlobalState) -> Subscription<Message> {
    if !state.enabled {
        return Subscription::none();
    }
    let recovery = if state.retry && state.opening.is_none() {
        time::every(Duration::from_secs(1))
            .with(state.generation)
            .map(|(generation, _)| Message::RetryOutput(generation))
    } else if state
        .output
        .as_ref()
        .is_some_and(|output| output.needs_poll)
    {
        time::every(Duration::from_secs(2))
            .with(state.generation)
            .map(|(generation, _)| Message::CheckOutput(generation))
    } else {
        Subscription::none()
    };
    Subscription::batch([state.events.subscription(), recovery])
}

/// The decoded file's clock, including the position where its current source started.
struct AudioPlayerController {
    player: AudioPlayer,
    duration: Duration,
    offset: Duration,
}

impl AudioPlayerController {
    fn new(track: &Track, mixer: &Mixer) -> Result<Self, Box<dyn Error>> {
        let mut source = Decoder::try_from(File::open(&track.path)?)?;
        let duration = source
            .total_duration()
            .filter(|duration| !duration.is_zero())
            .ok_or("Cannot determine the audio file's duration")?;
        let offset = duration.mul_f64(track.position.clamp(0.0, 1.0));
        source.try_seek(offset)?;
        let player = AudioPlayer::connect_new(mixer);
        player.pause();
        player.append(source);
        Ok(Self {
            player,
            duration,
            offset,
        })
    }

    fn pause(&self) {
        self.player.pause();
    }

    fn position(&self) -> f64 {
        if self.player.empty() {
            return 1.0;
        }
        (self.offset + self.player.get_pos()).as_secs_f64() / self.duration.as_secs_f64()
    }
}

pub(crate) fn update(
    output: &mut Vec<app::Output>,
    state: &mut GlobalState,
    message: Message,
) -> Task<Message> {
    if state.opening.is_some()
        && matches!(
            message,
            Message::Play(_)
                | Message::Pause(_)
                | Message::ChangePosition(_, _)
                | Message::SetTempo(_)
        )
    {
        // A prepared synthesizer must match the user's latest transport state.
        state.generation += 1;
        state.events.set_generation(state.generation);
    }
    match message {
        Message::Play(track_id) => {
            play(output, state, track_id);
            if state.output.is_none() && state.opening.is_none() {
                return state.reopen(output);
            }
        }
        Message::Pause(id) => pause(output, state, id),
        Message::ChangePosition(id, position) => change_position(output, state, id, position),
        Message::SetTempo(tempo) => state.set_tempo(tempo),
        Message::Tick(_) => tick(output, state),
        Message::OutputChanged(generation) if generation == state.generation => {
            return state.reopen(output);
        }
        Message::OutputOpened(generation, result) => {
            return state.opened(output, generation, result)
        }
        Message::RetryOutput(generation)
            if generation == state.generation && state.retry && state.opening.is_none() =>
        {
            return state.reopen(output)
        }
        Message::CheckOutput(generation) if generation == state.generation => {
            return state.check_output();
        }
        Message::OutputChecked(generation, unchanged) if generation == state.generation => {
            state.checking = false;
            if !unchanged {
                return state.reopen(output);
            }
        }
        Message::OutputChanged(_)
        | Message::RetryOutput(_)
        | Message::CheckOutput(_)
        | Message::OutputChecked(_, _) => (),
    }

    Task::none()
}

/// Stop whatever else is playing, then play the track with `id`.
fn play(output: &mut Vec<app::Output>, state: &mut GlobalState, id: PlayerId) {
    // if another file is playing - stop it
    if let Some(app::Output::Player(track)) = state
        .playing_track
        .and_then(|playing_track| output.get_mut(playing_track.inner()))
    {
        state.pause(track);
    }

    // play
    if let Some(app::Output::Player(track)) = output.get_mut(id.inner()) {
        if let Err(e) = state.play(track) {
            output.push(app::Output::Error(e.to_string()));
        }
    }
}

/// Pause the track with `id`.
fn pause(output: &mut [app::Output], state: &mut GlobalState, id: PlayerId) {
    if let Some(app::Output::Player(track)) = output.get_mut(id.inner()) {
        state.pause(track);
    }
}

/// Move the track with `id` to `position`.
fn change_position(
    output: &mut [app::Output],
    state: &mut GlobalState,
    id: PlayerId,
    position: f64,
) {
    if let Some(app::Output::Player(track)) = output.get_mut(id.inner()) {
        state.set_position(track, position);
    }
}

/// Follow the playing track's position.
fn tick(output: &mut [app::Output], state: &mut GlobalState) {
    if let Some(app::Output::Player(track)) = state
        .playing_track
        .and_then(|id| output.get_mut(id.inner()))
    {
        state.on_tick(track);
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PlayerId {
    Midi(usize),
    Audio(usize),
}

impl PlayerId {
    pub(crate) fn inner(&self) -> usize {
        match self {
            PlayerId::Midi(v) => *v,
            PlayerId::Audio(v) => *v,
        }
    }
}

impl From<PlayerId> for usize {
    fn from(value: PlayerId) -> Self {
        match value {
            PlayerId::Midi(v) => v,
            PlayerId::Audio(v) => v,
        }
    }
}

#[derive(Debug)]
pub(crate) struct Track {
    pub(crate) is_playing: bool,
    pub(crate) path: PathBuf,
    pub(crate) id: PlayerId,
    pub(crate) position: f64,
}

#[derive(Debug, Clone)]
pub enum Message {
    Play(PlayerId),
    Pause(PlayerId),
    ChangePosition(PlayerId, f64),
    SetTempo(u16),
    Tick(time::Instant),
    OutputChanged(u64),
    OutputOpened(u64, Opened),
    RetryOutput(u64),
    CheckOutput(u64),
    OutputChecked(u64, bool),
}

impl Message {
    /// Keep device access and SoundFont loading off the UI and audio callback threads.
    fn background(work: impl FnOnce() -> Self + Send + 'static) -> Task<Self> {
        let (sender, receiver) = async_channel::bounded(1);
        std::thread::spawn(move || {
            // Cancellation drops an unclaimed output and its stream.
            drop(sender.send_blocking(work()));
        });
        Task::stream(receiver)
    }
}

/// A track: its play button, its progress in segments, and its kind.
pub(crate) fn view(track: &Track, colors: Colors, width: f32) -> Element<'_, Message> {
    if !track.path.exists() && !track.is_playing {
        return text(format!(
            "File {} does not exist.",
            track.path.to_string_lossy()
        ))
        .color(colors.dim)
        .into();
    }
    let (icon, message) = if track.is_playing {
        (Icon::Pause, Message::Pause(track.id))
    } else {
        (Icon::Play, Message::Play(track.id))
    };
    let play = icon
        .button(colors.block_button())
        .width(36)
        .height(36)
        .on_press(message);
    let progress = Canvas::new(Progress {
        id: track.id,
        position: track.position,
        lit: colors.lit,
        unlit: colors.unlit,
    })
    .width(Length::Fill)
    .height(10);
    let kind = match track.id {
        PlayerId::Midi(_) => "MIDI",
        PlayerId::Audio(_) => "AUDIO",
    };

    row![play, progress, pixel::label(kind, colors.dim)]
        .width(width)
        .spacing(12)
        .align_y(Vertical::Center)
        .into()
}

/// A track's progress as a row of segments: those played are lit. Clicking or dragging along it
/// seeks.
struct Progress {
    id: PlayerId,
    position: f64,
    lit: Color,
    unlit: Color,
}

impl Progress {
    /// Where along the bar `x` is, from 0 to 1.
    fn position_at(x: f32, width: f32) -> f64 {
        f64::from((x / width.max(1.0)).clamp(0.0, 1.0))
    }
}

impl canvas::Program<Message> for Progress {
    /// Whether the bar is being dragged.
    type State = bool;

    fn update(
        &self,
        dragging: &mut bool,
        event: &canvas::Event,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Option<widget::Action<Message>> {
        let seek = |x: f32| {
            widget::Action::publish(Message::ChangePosition(
                self.id,
                Self::position_at(x, bounds.width),
            ))
            .and_capture()
        };
        match event {
            canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)) => {
                let at = cursor.position_in(bounds)?;
                *dragging = true;
                Some(seek(at.x))
            }
            canvas::Event::Mouse(mouse::Event::CursorMoved { .. }) if *dragging => {
                let at = cursor.position()?;
                Some(seek(at.x - bounds.x))
            }
            canvas::Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)) => {
                *dragging = false;
                None
            }
            _ => None,
        }
    }

    fn draw(
        &self,
        _dragging: &bool,
        renderer: &Renderer,
        _theme: &Theme,
        bounds: Rectangle,
        _cursor: mouse::Cursor,
    ) -> Vec<canvas::Geometry> {
        let mut frame = canvas::Frame::new(renderer, bounds.size());
        let count = SEGMENTS as f32;
        let width = (bounds.width - SEGMENT_GAP * (count - 1.0)) / count;
        let played = self.position.clamp(0.0, 1.0) as f32 * count;
        for index in 0..SEGMENTS {
            let segment = index as f32;
            let x = (segment * (width + SEGMENT_GAP)).round();
            let right = ((segment + 1.0) * (width + SEGMENT_GAP) - SEGMENT_GAP).round();
            let color = if segment < played.round() {
                self.lit
            } else {
                self.unlit
            };
            frame.fill_rectangle(
                Point::new(x, 0.0),
                Size::new(right - x, bounds.height),
                color,
            );
        }
        vec![frame.into_geometry()]
    }

    fn mouse_interaction(
        &self,
        dragging: &bool,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> mouse::Interaction {
        if *dragging || cursor.is_over(bounds) {
            mouse::Interaction::Pointer
        } else {
            mouse::Interaction::default()
        }
    }
}

/// The soundfont tests play through.
///
/// The app's own soundfont is half a gigabyte kept in Git LFS, which CI doesn't fetch. Tests need a
/// player, not a sound, so they get the smallest soundfont rustysynth accepts, built here: one
/// preset of one instrument of one silent sample.
#[cfg(test)]
mod soundfont {
    use std::{path::PathBuf, sync::OnceLock};

    /// A zone's generator naming the instrument it plays, and a zone's naming the sample.
    const INSTRUMENT: u16 = 41;
    const SAMPLE_ID: u16 = 53;
    /// Silent sample data, as 16-bit samples. The sample ends inside it, as rustysynth checks.
    const WAVE: [u8; 16] = [0; 16];
    const SAMPLE_END: u32 = 4;
    const SAMPLE_LOOP_END: u32 = 3;

    /// Where this process wrote its soundfont: each writes its own, as tests run in parallel.
    pub(super) fn path() -> &'static str {
        static PATH: OnceLock<String> = OnceLock::new();
        PATH.get_or_init(|| {
            // beside this process' other test files, all under the one directory to sweep away
            let dir: PathBuf = std::env::temp_dir()
                .join("athenacl-tests")
                .join(std::process::id().to_string());
            std::fs::create_dir_all(&dir).expect("the test directory should be created");
            let path = dir.join("soundfont.sf2");
            std::fs::write(&path, bytes()).expect("the test soundfont should be written");
            path.to_string_lossy().into_owned()
        })
    }

    /// The soundfont itself: a RIFF file of an info, a sample data and a parameter list.
    fn bytes() -> Vec<u8> {
        let info = list(b"INFO", &chunk(b"ifil", &[2, 0, 1, 0]));
        let sample_data = list(b"sdta", &chunk(b"smpl", &WAVE));

        // every list names one thing and ends with a terminal record, which is never played
        let mut parameters = chunk(b"phdr", &[preset("silence", 0), preset("EOP", 1)].concat());
        parameters.extend(chunk(b"pbag", &[zone(0), zone(1)].concat()));
        parameters.extend(chunk(
            b"pgen",
            &[generator(INSTRUMENT, 0), generator(0, 0)].concat(),
        ));
        parameters.extend(chunk(
            b"inst",
            &[instrument("silence", 0), instrument("EOI", 1)].concat(),
        ));
        parameters.extend(chunk(b"ibag", &[zone(0), zone(1)].concat()));
        parameters.extend(chunk(
            b"igen",
            &[generator(SAMPLE_ID, 0), generator(0, 0)].concat(),
        ));
        parameters.extend(chunk(b"shdr", &[sample("silence"), sample("EOS")].concat()));

        let mut form = b"sfbk".to_vec();
        form.extend(info);
        form.extend(sample_data);
        form.extend(list(b"pdta", &parameters));
        chunk(b"RIFF", &form)
    }

    /// A RIFF chunk: its name, its length, and its content.
    fn chunk(id: &[u8; 4], body: &[u8]) -> Vec<u8> {
        let mut out = id.to_vec();
        out.extend(u32::try_from(body.len()).unwrap_or(u32::MAX).to_le_bytes());
        out.extend(body);
        out
    }

    /// A list chunk, whose content starts with the kind of list it is.
    fn list(kind: &[u8; 4], body: &[u8]) -> Vec<u8> {
        let mut inner = kind.to_vec();
        inner.extend(body);
        chunk(b"LIST", &inner)
    }

    /// A name, in the twenty bytes records start with.
    fn name(text: &str) -> [u8; 20] {
        let mut out = [0; 20];
        for (slot, byte) in out.iter_mut().zip(text.bytes()) {
            *slot = byte;
        }
        out
    }

    /// A preset: its name, its patch and bank, the zone it starts at, and unused catalog numbers.
    fn preset(text: &str, zone: u16) -> Vec<u8> {
        let mut out = name(text).to_vec();
        out.extend(0u16.to_le_bytes());
        out.extend(0u16.to_le_bytes());
        out.extend(zone.to_le_bytes());
        out.extend([0; 12]);
        out
    }

    /// An instrument: its name, and the zone it starts at.
    fn instrument(text: &str, zone: u16) -> Vec<u8> {
        let mut out = name(text).to_vec();
        out.extend(zone.to_le_bytes());
        out
    }

    /// A zone: where its generators start, and where its modulators would.
    fn zone(generator: u16) -> Vec<u8> {
        let mut out = generator.to_le_bytes().to_vec();
        out.extend(0u16.to_le_bytes());
        out
    }

    /// A generator: what it sets, and what to.
    fn generator(operator: u16, amount: u16) -> Vec<u8> {
        let mut out = operator.to_le_bytes().to_vec();
        out.extend(amount.to_le_bytes());
        out
    }

    /// A sample: its name, its span of the wave data, its loop, its rate and its pitch.
    fn sample(text: &str) -> Vec<u8> {
        let mut out = name(text).to_vec();
        out.extend(0u32.to_le_bytes());
        out.extend(SAMPLE_END.to_le_bytes());
        out.extend(0u32.to_le_bytes());
        out.extend(SAMPLE_LOOP_END.to_le_bytes());
        out.extend(44100u32.to_le_bytes());
        out.extend([60, 0]);
        out.extend(0u16.to_le_bytes());
        out.extend(1u16.to_le_bytes());
        out
    }
}

#[cfg(test)]
mod tests {
    #![expect(clippy::float_cmp, reason = "the tests assert exact positions")]

    use super::*;

    fn track(id: PlayerId) -> Track {
        Track {
            is_playing: true,
            path: "no-such-file.aiff".into(),
            id,
            position: 0.0,
        }
    }

    #[test]
    fn missing_audio_files_do_not_play() {
        let mut state = GlobalState::headless();
        let mut output = vec![app::Output::Player(track(PlayerId::Audio(0)))];
        drop(update(
            &mut output,
            &mut state,
            Message::Play(PlayerId::Audio(0)),
        ));

        let Some(app::Output::Player(track)) = output.first() else {
            panic!("the track stays in the output");
        };
        assert!(!track.is_playing);
        assert!(!state.playing());
    }

    /// A minimal valid MIDI file: one format-0 track holding a note and its end.
    fn midi_file() -> PathBuf {
        let path = std::env::temp_dir().join(format!("athenacl-test-{}.mid", std::process::id()));
        std::fs::write(
            &path,
            [
                // header: `MThd`, 6 bytes, format 0, one track, 96 ticks per beat
                0x4D, 0x54, 0x68, 0x64, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x01, 0x00, 0x60,
                // track: `MTrk`, 12 bytes, a note on, a note off 96 ticks later, the end
                0x4D, 0x54, 0x72, 0x6B, 0x00, 0x00, 0x00, 0x0C, 0x00, 0x90, 0x3C, 0x50, 0x60, 0x80,
                0x3C, 0x00, 0x00, 0xFF, 0x2F, 0x00,
            ],
        )
        .expect("writing a test midi file works");
        path
    }

    #[test]
    fn midi_files_start_playing() {
        let mut state = GlobalState::headless();
        let mut midi = track(PlayerId::Midi(0));
        midi.path = midi_file();
        let mut output = vec![app::Output::Player(midi)];
        drop(update(
            &mut output,
            &mut state,
            Message::Play(PlayerId::Midi(0)),
        ));

        let Some(app::Output::Player(track)) = output.first() else {
            panic!("the track stays in the output");
        };
        assert!(track.is_playing);
        assert!(state.playing());
    }

    #[test]
    fn releasing_a_folder_stops_its_players_and_leaves_old_log_paths() {
        let directory = tempfile::tempdir().expect("scratch folder");
        let midi_path = directory.path().join("song.mid");
        let audio_path = directory.path().join("render.wav");
        std::fs::copy(midi_file(), &midi_path).expect("MIDI fixture");
        std::fs::copy(audio_file(), &audio_path).expect("audio fixture");
        let mut state = GlobalState::headless();
        let mut output = vec![
            app::Output::Player(Track {
                path: midi_path.clone(),
                ..track(PlayerId::Midi(0))
            }),
            app::Output::Player(Track {
                path: audio_path.clone(),
                ..track(PlayerId::Audio(1))
            }),
        ];
        play(&mut output, &mut state, PlayerId::Midi(0));
        play(&mut output, &mut state, PlayerId::Audio(1));
        assert!(state.playing());
        assert!(state.audio_player_cache.contains_key(&audio_path));
        state.release_files(&mut output, |path| path.starts_with(directory.path()));
        assert!(!state.playing());
        assert!(state.audio_player_cache.is_empty());
        assert!(state.midi_track.is_none());
        assert!(output
            .iter()
            .all(|entry| matches!(entry, app::Output::Player(track) if !track.is_playing)));
        let renamed = directory.path().join("new.mid");
        std::fs::rename(&midi_path, renamed).expect("released MIDI can move");
        std::fs::remove_file(&audio_path)
            .expect("released audio can be deleted, including on Windows");
        assert_eq!(first_track(&output).path, midi_path);
        assert!(!first_track(&output).path.exists());
        play(&mut output, &mut state, PlayerId::Midi(0));
        assert!(!state.playing());
    }

    #[test]
    fn releasing_unrelated_files_does_not_interrupt_playback_or_reconnection() {
        let mut state = GlobalState::headless();
        let mut midi = track(PlayerId::Midi(0));
        midi.path = midi_file();
        state.play(&mut midi).expect("play");
        let mut output = vec![app::Output::Player(midi)];
        state.opening = Some(state.generation);
        let generation = state.generation;
        state.release_files(&mut output, |_| false);
        assert!(state.playing());
        assert_eq!(state.generation, generation);
        state.release_files(&mut output, |_| true);
        assert!(!state.playing());
        assert!(
            state.generation > generation,
            "a late reconnect cannot resurrect deleted media"
        );
    }

    #[test]
    fn broken_midi_files_report_an_error() {
        let mut state = GlobalState::headless();
        let mut midi = track(PlayerId::Midi(0));
        midi.path = "Cargo.toml".into();
        let mut output = vec![app::Output::Player(midi)];
        drop(update(
            &mut output,
            &mut state,
            Message::Play(PlayerId::Midi(0)),
        ));

        assert!(matches!(output.last(), Some(app::Output::Error(_))));
        assert!(!state.playing());
    }

    #[test]
    fn playing_a_track_stops_the_other_one() {
        let mut state = GlobalState::headless();
        state.playing_track = Some(PlayerId::Midi(1));
        let mut output = vec![
            app::Output::Player(track(PlayerId::Midi(1))),
            app::Output::Player(track(PlayerId::Audio(0))),
        ];
        drop(update(
            &mut output,
            &mut state,
            Message::Play(PlayerId::Audio(0)),
        ));

        let Some(app::Output::Player(stopped)) = output.first() else {
            panic!("the midi track stays in the output");
        };
        assert!(!stopped.is_playing);
    }

    #[test]
    fn pausing_stops_the_playing_track() {
        let mut state = GlobalState::headless();
        state.playing_track = Some(PlayerId::Audio(0));

        let mut paused = track(PlayerId::Audio(0));
        state.pause(&mut paused);

        assert!(!paused.is_playing);
        assert!(!state.playing());
    }

    #[test]
    fn pausing_keeps_another_track_playing() {
        let mut state = GlobalState::headless();
        state.playing_track = Some(PlayerId::Midi(0));

        let mut paused = track(PlayerId::Audio(0));
        state.pause(&mut paused);

        assert!(state.playing());
    }

    #[test]
    fn positions_seek_only_the_playing_track() {
        let mut state = GlobalState::headless();
        state.playing_track = Some(PlayerId::Audio(0));

        let mut playing = track(PlayerId::Audio(0));
        state.set_position(&mut playing, 0.5);
        assert_eq!(playing.position, 0.5);

        let mut idle = track(PlayerId::Midi(1));
        state.set_position(&mut idle, 0.25);
        assert_eq!(idle.position, 0.25);
    }

    #[test]
    fn ticks_follow_the_midi_player() {
        let mut state = GlobalState::headless();
        state.playing_track = Some(PlayerId::Midi(0));
        let mut output = vec![app::Output::Player(track(PlayerId::Midi(0)))];
        drop(update(
            &mut output,
            &mut state,
            Message::Tick(time::Instant::now()),
        ));

        assert!(
            state.playing(),
            "a missing midi file does not end the track"
        );
    }

    #[test]
    fn ticks_follow_the_audio_player() {
        let mut state = GlobalState::headless();
        state.playing_track = Some(PlayerId::Audio(0));
        let mut output = vec![app::Output::Player(track(PlayerId::Audio(0)))];
        drop(update(
            &mut output,
            &mut state,
            Message::Tick(time::Instant::now()),
        ));

        let Some(app::Output::Player(track)) = output.first() else {
            panic!("the track stays in the output");
        };
        assert_eq!(track.position, 0.0);
    }

    #[test]
    fn the_tempo_updates() {
        let mut state = GlobalState::headless();
        drop(update(&mut Vec::new(), &mut state, Message::SetTempo(144)));
        assert_eq!(state.tempo(), 144);
    }

    #[test]
    fn the_progress_bar_seeks_where_it_is_clicked() {
        let bar = Progress {
            id: PlayerId::Midi(0),
            position: 0.0,
            lit: Color::BLACK,
            unlit: Color::WHITE,
        };
        let bounds = Rectangle::new(Point::new(100.0, 20.0), Size::new(400.0, 10.0));
        let at = mouse::Cursor::Available(Point::new(200.0, 25.0));
        let press = canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left));
        let mut dragging = false;
        let action = canvas::Program::update(&bar, &mut dragging, &press, bounds, at)
            .expect("clicking seeks");
        assert!(matches!(
            action.into_inner().0,
            Some(Message::ChangePosition(PlayerId::Midi(0), position)) if (position - 0.25).abs() < 1e-9
        ));
        assert!(dragging);
        assert_eq!(Progress::position_at(-5.0, 400.0), 0.0);
        assert_eq!(Progress::position_at(900.0, 400.0), 1.0);
    }

    #[test]
    fn unknown_tracks_are_ignored() {
        let mut state = GlobalState::headless();
        let mut output = Vec::new();
        drop(update(
            &mut output,
            &mut state,
            Message::Pause(PlayerId::Audio(9)),
        ));
        drop(update(
            &mut output,
            &mut state,
            Message::ChangePosition(PlayerId::Midi(9), 0.1),
        ));
        drop(update(
            &mut output,
            &mut state,
            Message::Tick(time::Instant::now()),
        ));
    }

    fn audio_file() -> PathBuf {
        let path = std::env::temp_dir().join(format!("athenacl-switch-{}.wav", std::process::id()));
        let data_size = 44100u32 * 2;
        let mut wav = b"RIFF".to_vec();
        wav.extend((36 + data_size).to_le_bytes());
        wav.extend(b"WAVEfmt ");
        wav.extend(16u32.to_le_bytes());
        wav.extend(1u16.to_le_bytes()); // PCM
        wav.extend(1u16.to_le_bytes()); // mono
        wav.extend(44100u32.to_le_bytes());
        wav.extend((44100u32 * 2).to_le_bytes());
        wav.extend(2u16.to_le_bytes());
        wav.extend(16u16.to_le_bytes());
        wav.extend(b"data");
        wav.extend(data_size.to_le_bytes());
        for _ in 0..44100 {
            wav.extend(1000i16.to_le_bytes());
        }
        std::fs::write(&path, wav).expect("write test audio");
        path
    }

    fn first_track(output: &[app::Output]) -> &Track {
        let Some(app::Output::Player(track)) = output.first() else {
            panic!("track remains present");
        };
        track
    }

    /// Complete a simulated device open, without using a physical audio device.
    fn connect(
        state: &mut GlobalState,
        output: &mut Vec<app::Output>,
        rate: u32,
    ) -> crate::app::player::output::Renderer {
        state.generation += 1;
        state.opening = Some(state.generation);
        let (device, renderer) = AudioOutput::headless(soundfont::path(), rate);
        drop(update(
            output,
            state,
            Message::OutputOpened(state.generation, Opened::new(Ok(device))),
        ));
        renderer
    }

    #[test]
    fn midi_output_switch_preserves_position_and_tempo() {
        let mut state = GlobalState::headless();
        let mut midi = track(PlayerId::Midi(0));
        midi.path = midi_file();
        midi.position = 0.25;
        state.set_tempo(144);
        state.play(&mut midi).expect("play MIDI");
        let mut output = vec![app::Output::Player(midi)];
        state.suspend_output(&mut output);
        assert!(!state.playing());
        assert!(first_track(&output).is_playing);
        let position = first_track(&output).position;
        assert!((position - 0.25).abs() < 1.0 / 96.0);

        let mut renderer = connect(&mut state, &mut output, 48000);
        let device = state.output.as_ref().expect("new output");
        assert!((device.midi.position() - position).abs() < 1.0 / 96.0);
        assert_eq!(device.midi.tempo(), Some(144.0));
        assert!(state.playing());
        renderer.render(&mut [0.0f32; 9600], 2);
        state.on_tick(match output.first_mut() {
            Some(app::Output::Player(track)) => track,
            _ => panic!("track"),
        });
        assert!(first_track(&output).position > 0.25);
    }

    #[test]
    fn audio_output_switch_reconnects_the_source_at_its_position() {
        let mut state = GlobalState::headless();
        let (device, mut renderer) = AudioOutput::headless(soundfont::path(), 44100);
        state.output = Some(device);
        let mut audio = track(PlayerId::Audio(0));
        audio.path = audio_file();
        state.play(&mut audio).expect("play audio");
        let mut samples = [0.0f32; 8820];
        renderer.render(&mut samples, 2);
        assert!(samples.iter().any(|sample| *sample > 0.01));

        let mut output = vec![app::Output::Player(audio)];
        state.suspend_output(&mut output);
        let position = first_track(&output).position;
        assert!(position > 0.05 && position < 0.2);
        assert!(state.audio_player_cache.is_empty());

        let mut replacement = connect(&mut state, &mut output, 48000);
        assert_eq!(first_track(&output).position, position);
        replacement.render(&mut samples, 2);
        assert!(samples.iter().any(|sample| *sample > 0.01));
        assert!(
            state
                .audio_player_cache
                .values()
                .next()
                .expect("new source")
                .position()
                > position
        );
    }

    #[test]
    fn pause_and_seek_during_reconnection_are_respected() {
        let mut state = GlobalState::headless();
        let mut midi = track(PlayerId::Midi(0));
        midi.path = midi_file();
        state.play(&mut midi).expect("play MIDI");
        let mut output = vec![app::Output::Player(midi)];
        state.suspend_output(&mut output);
        state.opening = Some(state.generation);
        drop(update(
            &mut output,
            &mut state,
            Message::ChangePosition(PlayerId::Midi(0), 0.5),
        ));
        drop(update(
            &mut output,
            &mut state,
            Message::Pause(PlayerId::Midi(0)),
        ));
        assert_eq!(state.generation, 2);
        assert_eq!(state.opening, Some(0));
        assert!(state.events.is_current(2));
        drop(connect(&mut state, &mut output, 48000));
        assert!(!state.playing());
        assert!(!first_track(&output).is_playing);
        assert_eq!(first_track(&output).position, 0.5);
        assert!(!state.output.as_ref().expect("new output").midi.is_playing());
    }

    #[test]
    fn missing_output_retries_without_repeating_errors_or_losing_the_playhead() {
        let mut state = GlobalState::headless();
        let mut midi = track(PlayerId::Midi(0));
        midi.path = midi_file();
        midi.position = 0.5;
        state.play(&mut midi).expect("play MIDI");
        let mut output = vec![app::Output::Player(midi)];
        state.suspend_output(&mut output);
        let saved = first_track(&output).position;
        for generation in 1..=2 {
            state.generation = generation;
            state.opening = Some(generation);
            drop(update(
                &mut output,
                &mut state,
                Message::OutputOpened(generation, Opened::new(Err(OutputError::NoDevice))),
            ));
            drop(update(
                &mut output,
                &mut state,
                Message::Tick(time::Instant::now()),
            ));
        }
        assert!(state.retry);
        assert_eq!(output.len(), 2); // one track, one error
        assert_eq!(first_track(&output).position, saved);
        drop(connect(&mut state, &mut output, 48000));
        assert!(state.playing());
        assert!(!state.retry);
        assert!(state.last_error.is_none());
    }

    #[test]
    fn retired_stream_notifications_and_duplicate_completions_are_ignored() {
        let mut state = GlobalState::headless();
        state.generation = 2;
        let mut output = Vec::new();
        drop(update(&mut output, &mut state, Message::OutputChanged(1)));
        drop(update(
            &mut output,
            &mut state,
            Message::OutputChecked(1, false),
        ));
        drop(update(&mut output, &mut state, Message::RetryOutput(1)));
        assert!(state.output.is_some());
        assert!(state.opening.is_none());
        let opened = Opened::new(Err(OutputError::NoDevice));
        state.opening = Some(2);
        // Model an in-flight open: a cloned completion may only be consumed once.
        state.output = None;
        drop(update(
            &mut output,
            &mut state,
            Message::OutputOpened(2, opened.clone()),
        ));
        drop(update(
            &mut output,
            &mut state,
            Message::OutputOpened(2, opened),
        ));
        assert_eq!(output.len(), 1);
    }

    #[test]
    fn device_changes_during_an_open_are_coalesced() {
        let mut state = GlobalState::headless();
        state.output = None;
        state.generation = 2;
        state.opening = Some(2);
        let mut output = Vec::new();
        drop(update(&mut output, &mut state, Message::OutputChanged(2)));
        drop(update(&mut output, &mut state, Message::OutputChanged(2)));
        assert_eq!(state.generation, 3);
        assert_eq!(state.opening, Some(2));
    }

    #[test]
    fn renderer_fills_large_and_partial_blocks_and_integer_outputs() {
        let (device, mut renderer) = AudioOutput::headless(soundfont::path(), 44100);
        let source = rodio::buffer::SamplesBuffer::new(
            std::num::NonZero::new(2).expect("stereo"),
            std::num::NonZero::new(44100).expect("rate"),
            vec![0.25f32; 2200],
        );
        device.mixer.add(source);
        let mut samples = [0i16; 2054]; // >256 frames, with a final partial render block
        renderer.render(&mut samples, 2);
        assert!(samples.iter().all(|sample| *sample == 8192));
        let mut silence = [1.0f32; 4096];
        renderer.render(&mut silence, 2);
        assert!(silence.iter().skip(146).all(|sample| *sample == 0.0));
    }

    #[test]
    fn midi_reconstruction_advances_to_the_playhead_and_can_be_cancelled() {
        let (mut device, mut renderer) = AudioOutput::headless(soundfont::path(), 48000);
        let mut resume = MidiResume {
            path: midi_file(),
            position: 0.5,
            tempo: 144,
            playing: true,
        };
        device
            .restore_midi(&mut renderer, Some(resume.clone()), || false)
            .expect("reconstruct MIDI");
        assert_eq!(device.prepared_midi.as_ref(), Some(&resume));
        assert!((device.midi.position() - 0.5).abs() < 1.0 / 96.0);
        assert_eq!(device.midi.tempo(), Some(144.0));
        let (mut device, mut renderer) = AudioOutput::headless(soundfont::path(), 48000);
        resume.playing = false;
        assert!(matches!(
            device.restore_midi(&mut renderer, Some(resume), || true),
            Err(OutputError::Changed)
        ));
        assert!(device.prepared_midi.is_none());
    }

    #[test]
    fn missing_idle_midi_files_do_not_block_audio_reconnection() {
        let directory = tempfile::tempdir().expect("temporary directory");
        let (mut device, mut renderer) = AudioOutput::headless(soundfont::path(), 44100);
        let mut resume = MidiResume {
            path: directory.path().join("removed.mid"),
            position: 0.5,
            tempo: 120,
            playing: false,
        };
        device
            .restore_midi(&mut renderer, None, || false)
            .expect("no MIDI snapshot to restore");
        device
            .restore_midi(&mut renderer, Some(resume.clone()), || false)
            .expect("an idle file must not block audio");
        assert!(device.prepared_midi.is_none());
        assert!(!device.midi.is_playing());

        device.mixer.add(rodio::buffer::SamplesBuffer::new(
            std::num::NonZero::new(2).expect("stereo"),
            std::num::NonZero::new(44100).expect("rate"),
            vec![0.25f32; 4],
        ));
        let mut samples = [0.0f32; 4];
        renderer.render(&mut samples, 2);
        assert_eq!(samples, [0.25; 4]);

        resume.playing = true;
        assert!(matches!(
            device.restore_midi(&mut renderer, Some(resume), || false),
            Err(OutputError::MidiFile(_))
        ));
    }

    #[test]
    #[ignore = "requires a physical audio device; plays silence"]
    fn real_audio_output_can_be_rebuilt() {
        let events = Events::new();
        for generation in 0..2 {
            events.set_generation(generation);
            let output = AudioOutput::open(soundfont::path(), events.clone(), generation, None)
                .expect("open the system default output");
            output.start().expect("start the output");
            std::thread::sleep(Duration::from_millis(50));
            drop(output);
        }
    }
}
