use std::collections::HashMap;
use std::error::Error;
use std::fs::File;
use std::io::BufReader;
use std::path::PathBuf;
use std::time::Duration;

use cpal::{
    traits::{DeviceTrait, HostTrait, StreamTrait},
    Stream as AudioStream, StreamConfig,
};
use iced::{
    time,
    widget::{button, row, slider, text},
    Element, Task,
};
use iced_aw::number_input;
use midi_player::{Player, PlayerController, Settings as PlayerSettings};
use rodio::{source::Source, Decoder, OutputStream, OutputStreamHandle, Sink};

use super::app;

pub(crate) struct GlobalState {
    midi_player_controller: PlayerController,
    _audio_stream: AudioStream,
    _output_stream: OutputStream,
    stream_handle: OutputStreamHandle,
    playing_track: Option<PlayerId>,
    tempo: u16,
    audio_player_cache: HashMap<PathBuf, AudioPlayerController>,
}

impl GlobalState {
    pub(crate) fn new(sf: &str) -> Self {
        let settings = PlayerSettings::builder().build();
        let (player, controller) = Player::new(sf, settings)
            .expect("midi player should be initialized with default settings and soundfont");
        let audio_stream = Self::start_midi_renderer(player);
        let (_output_stream, stream_handle) =
            OutputStream::try_default().expect("Default audio stream should work");

        Self {
            midi_player_controller: controller,
            _audio_stream: audio_stream,
            playing_track: None,
            tempo: 120,
            _output_stream,
            stream_handle,
            audio_player_cache: HashMap::new(),
        }
    }

    fn start_midi_renderer(mut player: Player) -> AudioStream {
        let host = cpal::default_host();
        let device = host
            .default_output_device()
            .expect("No output device available");
        let channels = 2_usize;
        let config = StreamConfig {
            channels: channels as u16,
            sample_rate: cpal::SampleRate(player.settings().sample_rate),
            buffer_size: cpal::BufferSize::Fixed(player.settings().audio_buffer_size),
        };

        let err_fn = |err| eprintln!("An error occurred on the output audio stream: {}", err);

        let mut left = vec![0f32; player.settings().audio_buffer_size as usize];
        let mut right = vec![0f32; player.settings().audio_buffer_size as usize];

        let stream = device
            .build_output_stream(
                &config,
                move |data: &mut [f32], _: &cpal::OutputCallbackInfo| {
                    let sample_count = data.len() / channels;

                    player.render(&mut left, &mut right);

                    if !left.is_empty() {
                        for i in 0..sample_count {
                            data[channels * i] = left[i];
                            data[channels * i + 1] = right[i];
                        }
                    }
                },
                err_fn,
                None,
            )
            .unwrap();

        stream.play().expect("cannot run audio stream");

        stream
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
        let controller = self
            .audio_player_cache
            .entry(track.path.clone())
            .or_insert_with(|| AudioPlayerController::new(track, &self.stream_handle));
        controller.set_position(track.position);
        controller.play(track, &self.stream_handle);
    }

    fn pause(&mut self, track: &mut Track) {
        match track.id {
            PlayerId::Midi(_) => self.midi_player_controller.stop(),
            PlayerId::Audio(_) => {
                if let Some(controller) = self.audio_player_cache.get(&track.path) {
                    controller.pause();
                }
            }
        }

        track.is_playing = false;
        if let Some(playing_id) = self.playing_track {
            if playing_id == track.id {
                self.playing_track = None;
            }
        }
    }

    fn set_position(&mut self, track: &mut Track, position: f64) {
        track.position = position;

        if let Some(playing_id) = self.playing_track {
            if playing_id == track.id {
                match playing_id {
                    PlayerId::Midi(_) => self.midi_player_controller.set_position(position),
                    PlayerId::Audio(_) => {
                        if let Some(controller) = self.audio_player_cache.get(&track.path) {
                            controller.set_position(position);
                        }
                    }
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

// we need this type to keep the duration of the file
struct AudioPlayerController {
    sink: Sink,
    duration: Duration,
}

impl AudioPlayerController {
    fn new(track: &Track, stream_handle: &OutputStreamHandle) -> Self {
        let file = File::open(&track.path).unwrap();
        let file = BufReader::new(file);
        let source = Decoder::new(file).expect("there should not be unsupported file formats");
        let duration = source
            .total_duration()
            .expect("duration is finite and known for an audio file");
        let sink =
            Sink::try_new(stream_handle).expect("sink should be initialized from default stream");
        sink.append(source);
        Self { sink, duration }
    }

    fn play(&mut self, track: &Track, stream_handle: &OutputStreamHandle) {
        self.maybe_reinit(track, stream_handle);
        self.sink.play()
    }

    fn pause(&self) {
        self.sink.pause()
    }

    fn position(&self) -> f64 {
        self.sink.get_pos().as_secs_f64() / self.duration.as_secs_f64()
    }

    fn set_position(&self, position: f64) {
        let position = self.duration.mul_f64(position);
        self.sink
            .try_seek(position)
            .expect("seek should work for an audio file");
    }

    /// When the file plays to the end, sink becomes empty and can't play this file anymore. This
    /// function reinitializes the sink in this case.
    ///
    /// It should be called before play.
    fn maybe_reinit(&mut self, track: &Track, stream_handle: &OutputStreamHandle) {
        if self.sink.len() > 0 {
            return;
        }
        let file = File::open(&track.path).unwrap();
        let file = BufReader::new(file);
        let source = Decoder::new(file).expect("there should not be unsupported file formats");
        let duration = source
            .total_duration()
            .expect("duration is finite and known for an audio file");
        let sink =
            Sink::try_new(stream_handle).expect("sink should be initialized from default stream");
        sink.append(source);

        self.sink = sink;
        self.duration = duration;
    }
}

pub(crate) fn update(
    output: &mut Vec<app::Output>,
    state: &mut GlobalState,
    message: Message,
) -> Task<Message> {
    match message {
        Message::Play(track_id) => {
            // if another file is playing - stop it
            if let Some(app::Output::Player(track)) = state
                .playing_track
                .and_then(|playing_track| output.get_mut(playing_track.inner()))
            {
                state.pause(track);
            }

            // play
            if let Some(app::Output::Player(track)) = output.get_mut(track_id.inner()) {
                if let Err(e) = state.play(track) {
                    output.push(app::Output::Error(e.to_string()));
                    return Task::none();
                }
            }
        }
        Message::Pause(id) => {
            if let Some(app::Output::Player(track)) = output.get_mut(id.inner()) {
                state.pause(track);
            }
        }
        Message::ChangePosition(id, position) => {
            if let Some(app::Output::Player(track)) = output.get_mut(id.inner()) {
                state.set_position(track, position);
            }
        }
        Message::SetTempo(tempo) => {
            state.set_tempo(tempo);
        }
        Message::Tick(_) => {
            if let Some(app::Output::Player(track)) = state
                .playing_track
                .and_then(|id| output.get_mut(id.inner()))
            {
                state.on_tick(track);
            }
        }
    }

    Task::none()
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

pub(crate) fn view(state: &Track) -> Element<Message> {
    let disabled = !state.path.exists() && !state.is_playing;
    let label = text(if state.is_playing { "" } else { "" })
        .font(iced_fonts::NERD_FONT)
        .align_x(iced::Alignment::Center)
        .size(24);
    let message = if state.is_playing {
        Message::Pause(state.id)
    } else {
        Message::Play(state.id)
    };
    let button = button(label);
    let player = row![
        if disabled {
            button
        } else {
            button.on_press(message)
        }
        .width(50),
        slider(0.0..=1.0, state.position, |v| {
            Message::ChangePosition(state.id, v)
        })
        .step(0.001)
    ]
    .align_y(iced::Alignment::Center)
    .spacing(10.0);

    if disabled {
        text(format!(
            "File {} does not exist.",
            state.path.to_string_lossy()
        ))
        .style(text::danger)
        .into()
    } else {
        player.into()
    }
}

pub(crate) fn view_tempo(global_state: &GlobalState) -> Element<Message> {
    row![
        text("󰟚").font(iced_fonts::NERD_FONT).size(16),
        text("=").size(16),
        number_input(global_state.tempo(), 20..=600, Message::SetTempo)
            .step(1)
            .width(60.0),
    ]
    .spacing(10.0)
    .align_y(iced::Alignment::Center)
    .into()
}
