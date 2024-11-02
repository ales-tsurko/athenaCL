use std::path::PathBuf;

use super::app::Message;
use cpal::{
    traits::{DeviceTrait, HostTrait, StreamTrait},
    Stream as AudioStream, StreamConfig,
};
use iced::{
    widget::{button, row, slider, text},
    Element,
};
use midi_player::{Player, PlayerController, Settings as PlayerSettings};

pub(crate) struct GlobalState {
    pub(crate) controller: PlayerController,
    _audio_stream: AudioStream,
    pub(crate) playing_id: Option<usize>,
    pub(crate) tempo: u16,
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

#[derive(Debug)]
pub(crate) struct State {
    pub(crate) is_playing: bool,
    pub(crate) path: PathBuf,
    pub(crate) id: usize,
    pub(crate) position: f64,
}

pub(crate) fn view(state: &State) -> Element<Message> {
    let disabled = !state.path.exists() && !state.is_playing;
    let label = text(if state.is_playing { "" } else { "" })
        .font(iced_fonts::NERD_FONT)
        .align_x(iced::Alignment::Center)
        .size(24);
    let message = if state.is_playing {
        Message::StopMidi(state.id)
    } else {
        Message::PlayMidi(state.id)
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
            Message::ChangePlayingPosition(state.id, v)
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
