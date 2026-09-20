use std::{
    collections::HashMap, error::Error, fs::File, io::BufReader, path::PathBuf, time::Duration,
};

use cpal::{
    traits::{DeviceTrait, HostTrait, StreamTrait},
    Stream as AudioStream, StreamConfig,
};
use iced::{
    alignment::Vertical,
    mouse, time,
    widget::{
        self, button,
        canvas::{self, Canvas},
        container, row, text,
    },
    Color, Element, Length, Point, Rectangle, Renderer, Size, Task, Theme,
};
use midi_player::{Player, PlayerController, Settings as PlayerSettings};
use rodio::{
    mixer::Mixer, source::Source, Decoder, DeviceSinkBuilder, MixerDeviceSink,
    Player as AudioPlayer,
};

use super::{app, pixel, theme::Colors};

/// Segments of the progress bar, and the gap between them.
const SEGMENTS: usize = 40;
const SEGMENT_GAP: f32 = 2.0;

pub(crate) struct GlobalState {
    midi_player_controller: PlayerController,
    /// The audio outputs, kept alive here; tests run without them.
    output: Option<AudioOutput>,
    playing_track: Option<PlayerId>,
    tempo: u16,
    audio_player_cache: HashMap<PathBuf, AudioPlayerController>,
}

/// The streams the players play through, kept alive for as long as the state lives.
struct AudioOutput {
    _midi_renderer: AudioStream,
    _device_sink: MixerDeviceSink,
    mixer: Mixer,
}

impl AudioOutput {
    /// Open the default device's outputs: a stream for the midi renderer, a mixer for files.
    fn open(midi_player: Player) -> Self {
        let device_sink =
            DeviceSinkBuilder::open_default_sink().expect("Default audio stream should work");
        let mixer = device_sink.mixer().clone();

        Self {
            _midi_renderer: start_midi_renderer(midi_player),
            _device_sink: device_sink,
            mixer,
        }
    }

    /// Where audio files are played.
    fn mixer(&self) -> &Mixer {
        &self.mixer
    }
}

impl GlobalState {
    pub(crate) fn new(sf: &str) -> Self {
        let settings = PlayerSettings::builder().build();
        let (player, controller) = Player::new(sf, settings)
            .expect("midi player should be initialized with default settings and soundfont");

        Self {
            midi_player_controller: controller,
            output: Some(AudioOutput::open(player)),
            playing_track: None,
            tempo: 120,
            audio_player_cache: HashMap::new(),
        }
    }

    /// A state without audio outputs, for tests.
    #[cfg(test)]
    pub(crate) fn headless() -> Self {
        let settings = PlayerSettings::builder().build();
        let (player, controller) = Player::new(soundfont::path(), settings)
            .expect("midi player should be initialized with default settings and soundfont");
        drop(player);

        Self {
            midi_player_controller: controller,
            output: None,
            playing_track: None,
            tempo: 120,
            audio_player_cache: HashMap::new(),
        }
    }

    /// Where audio files are played.
    fn mixer(&self) -> &Mixer {
        self.output
            .as_ref()
            .expect("audio outputs are open unless the state is a test's")
            .mixer()
    }

    fn play(&mut self, track: &mut Track) -> Result<(), Box<dyn Error>> {
        if !track.path.exists() {
            track.is_playing = false;
            return Ok(()); // this is handled by gui
        }

        match track.id {
            PlayerId::Midi(_) => self.play_midi(track)?,
            PlayerId::Audio(_) => self.play_audio(track),
        }

        track.is_playing = true;
        self.playing_track = Some(track.id);

        Ok(())
    }

    fn play_midi(&mut self, track: &Track) -> Result<(), Box<dyn Error>> {
        self.midi_player_controller.set_file(Some(&track.path))?;
        self.midi_player_controller.set_position(track.position);
        self.set_tempo(self.tempo);
        self.midi_player_controller.play();

        Ok(())
    }

    fn play_audio(&mut self, track: &Track) {
        // the path has checked for existence at this point
        let mixer = self.mixer().clone();
        let controller = self
            .audio_player_cache
            .entry(track.path.clone())
            .or_insert_with(|| AudioPlayerController::new(track, &mixer));
        controller.set_position(track.position);
        controller.play(track);
    }

    fn pause(&mut self, track: &mut Track) {
        match track.id {
            PlayerId::Midi(_) => self.midi_player_controller.stop(),
            PlayerId::Audio(_) => self.pause_audio(track),
        }

        track.is_playing = false;
        self.playing_track = self.playing_track.filter(|playing| *playing != track.id);
    }

    /// Pause the audio file of `track`, if it has been played before.
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

    /// Whether `id` is the track currently playing.
    fn is_playing(&self, id: PlayerId) -> bool {
        self.playing_track.is_some_and(|playing| playing == id)
    }

    /// Seek the playing track, whichever kind of player it uses.
    fn seek(&self, track: &Track, position: f64) {
        match track.id {
            PlayerId::Midi(_) => self.midi_player_controller.set_position(position),
            PlayerId::Audio(_) => {
                if let Some(controller) = self.audio_player_cache.get(&track.path) {
                    controller.set_position(position);
                }
            }
        }
    }

    pub(crate) fn tempo(&self) -> u16 {
        self.tempo
    }

    pub(crate) fn set_tempo(&mut self, tempo: u16) {
        self.tempo = tempo;
        self.midi_player_controller.set_tempo(tempo as f32);
    }

    pub(crate) fn playing(&self) -> bool {
        self.playing_track.is_some()
    }

    fn on_tick(&mut self, track: &mut Track) {
        let position = match track.id {
            PlayerId::Midi(_) => self.midi_player_controller.position(),
            PlayerId::Audio(_) => self
                .audio_player_cache
                .get(&track.path)
                .map(|c| c.position())
                .unwrap_or_default(),
        };

        track.position = position;

        if position >= 1.0 {
            track.is_playing = false;
            track.position = 0.0;
            self.playing_track = None;
        }
    }
}

/// Start the stream that renders the midi player's output.
fn start_midi_renderer(mut player: Player) -> AudioStream {
    let host = cpal::default_host();
    let device = host
        .default_output_device()
        .expect("No output device available");
    let channels = 2_usize;
    let config = StreamConfig {
        channels: channels as u16,
        sample_rate: player.settings().sample_rate,
        buffer_size: cpal::BufferSize::Fixed(player.settings().audio_buffer_size),
    };

    let err_fn = |err| eprintln!("An error occurred on the output audio stream: {}", err);

    let mut left = vec![0f32; player.settings().audio_buffer_size as usize];
    let mut right = vec![0f32; player.settings().audio_buffer_size as usize];

    let stream = device
        .build_output_stream(
            &config,
            move |data: &mut [f32], _: &cpal::OutputCallbackInfo| {
                player.render(&mut left, &mut right);

                for (frame, (left, right)) in data
                    .chunks_exact_mut(channels)
                    .zip(left.iter().zip(right.iter()))
                {
                    if let [dst_left, dst_right, ..] = frame {
                        *dst_left = *left;
                        *dst_right = *right;
                    }
                }
            },
            err_fn,
            None,
        )
        .expect("cannot build the midi renderer's output audio stream");

    stream.play().expect("cannot run audio stream");

    stream
}

// we need this type to keep the duration of the file
struct AudioPlayerController {
    player: AudioPlayer,
    duration: Duration,
}

impl AudioPlayerController {
    fn new(track: &Track, mixer: &Mixer) -> Self {
        let file = File::open(&track.path).expect("the track exists: playing checked it");
        let file = BufReader::new(file);
        let source = Decoder::new(file).expect("there should not be unsupported file formats");
        let duration = source
            .total_duration()
            .expect("duration is finite and known for an audio file");
        let player = AudioPlayer::connect_new(mixer);
        player.append(source);
        Self { player, duration }
    }

    fn play(&mut self, track: &Track) {
        self.maybe_reinit(track);
        self.player.play()
    }

    fn pause(&self) {
        self.player.pause()
    }

    fn position(&self) -> f64 {
        self.player.get_pos().as_secs_f64() / self.duration.as_secs_f64()
    }

    fn set_position(&self, position: f64) {
        let position = self.duration.mul_f64(position);
        self.player
            .try_seek(position)
            .expect("seek should work for an audio file");
    }

    /// When the file plays to the end, the player's source is exhausted, so it cannot replay the
    /// file; this function decodes the file again and appends it.
    ///
    /// It should be called before play.
    fn maybe_reinit(&mut self, track: &Track) {
        if !self.player.empty() {
            return;
        }
        let file = File::open(&track.path).expect("the track exists: playing checked it");
        let file = BufReader::new(file);
        let source = Decoder::new(file).expect("there should not be unsupported file formats");
        let duration = source
            .total_duration()
            .expect("duration is finite and known for an audio file");
        self.player.append(source);

        self.duration = duration;
    }
}

pub(crate) fn update(
    output: &mut Vec<app::Output>,
    state: &mut GlobalState,
    message: Message,
) -> Task<Message> {
    match message {
        Message::Play(track_id) => play(output, state, track_id),
        Message::Pause(id) => pause(output, state, id),
        Message::ChangePosition(id, position) => change_position(output, state, id, position),
        Message::SetTempo(tempo) => state.set_tempo(tempo),
        Message::Tick(_) => tick(output, state),
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
}

/// A track: its play button, its progress in segments, and its kind.
pub(crate) fn view(track: &Track, colors: Colors) -> Element<'_, Message> {
    if !track.path.exists() && !track.is_playing {
        return text(format!(
            "File {} does not exist.",
            track.path.to_string_lossy()
        ))
        .color(colors.dim)
        .into();
    }
    let (glyph, message) = if track.is_playing {
        ('\u{f04c}', Message::Pause(track.id))
    } else {
        ('\u{f04b}', Message::Play(track.id))
    };
    let play =
        button(container(text(glyph).font(iced_fonts::NERD_FONT).size(14)).center(Length::Fill))
            .width(36)
            .height(36)
            .padding(0)
            .style(colors.block_button())
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
/// The app's own soundfont is half a gigabyte kept in Git LFS, which CI doesn't fetch. Tests need
/// a player, not a sound, so they get the smallest soundfont rustysynth accepts, built here: one
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
        let path = std::env::temp_dir().join("athenacl-test.mid");
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
}
