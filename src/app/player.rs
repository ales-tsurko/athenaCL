use std::path::PathBuf;

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

use super::app;

pub(crate) struct GlobalState {
    controller: PlayerController,
    _audio_stream: AudioStream,
    playing_id: Option<PlayerId>,
    tempo: u16,
}

impl GlobalState {
    pub(crate) fn new(sf: &str) -> Self {
        let settings = PlayerSettings::builder().build();
        let (player, controller) = Player::new(sf, settings)
            .expect("midi player should be initialized with default settings and soundfont");
        let audio_stream = Self::start_audio_loop(player);

        Self {
            controller,
            _audio_stream: audio_stream,
            playing_id: None,
            tempo: 120,
        }
    }

    pub(crate) fn playing(&self) -> bool {
        self.controller.is_playing()
    }

    fn start_audio_loop(mut player: Player) -> AudioStream {
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

    pub(crate) fn tempo(&self) -> u16 {
        self.tempo
    }

    pub(crate) fn set_tempo(&mut self, tempo: u16) {
        self.tempo = tempo;
        self.controller.set_tempo(tempo as f32);
    }

    pub(crate) fn update_tempo(&mut self) {
        self.set_tempo(self.tempo);
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
pub(crate) struct State {
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

pub(crate) fn update(
    output: &mut Vec<app::Output>,
    state: &mut GlobalState,
    message: Message,
) -> Task<Message> {
    match message {
        Message::Play(id) => {
            if let Some(playing_id) = state.playing_id {
                if let Some(app::Output::Player(player_state)) = output.get_mut(playing_id.inner())
                {
                    player_state.is_playing = false;
                    state.playing_id = None;
                }
            }

            if let Some(app::Output::Player(player)) = output.get_mut(id.inner()) {
                if player.path.exists() {
                    player.is_playing = true;
                    if let Err(e) = state.controller.set_file(Some(&player.path)) {
                        output.push(app::Output::Error(e.to_string()));
                        return Task::none();
                    }
                    state.controller.set_position(player.position);
                    state.update_tempo();
                    state.controller.play();
                    state.playing_id = Some(id);
                } else {
                    player.is_playing = false;
                }
            }
        }
        Message::Pause(id) => {
            if let Some(app::Output::Player(player_state)) = output.get_mut(id.inner()) {
                player_state.is_playing = false;
                state.controller.stop();
                if let Some(playing_id) = state.playing_id {
                    if playing_id == id {
                        state.playing_id = None;
                    }
                }
            }
        }
        Message::ChangePosition(id, position) => {
            if let Some(app::Output::Player(player_state)) = output.get_mut(id.inner()) {
                player_state.position = position;

                if let Some(playing_id) = state.playing_id {
                    if playing_id == id {
                        state.controller.set_position(position);
                    }
                }
            }
        }
        Message::SetTempo(tempo) => {
            state.set_tempo(tempo);
        }
        Message::Tick(_) => {
            if let Some(playing_id) = state.playing_id {
                if let Some(app::Output::Player(player_state)) = output.get_mut(playing_id.inner())
                {
                    let position = state.controller.position();

                    player_state.position = position;

                    if position >= 1.0 {
                        player_state.is_playing = false;
                        player_state.position = 0.0;
                        state.playing_id = None;
                    }
                }
            }
        }
    }

    Task::none()
}

pub(crate) fn view(state: &State) -> Element<Message> {
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
