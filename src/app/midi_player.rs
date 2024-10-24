use std::path::PathBuf;

use super::app::Message;
use cpal::{
    traits::{DeviceTrait, HostTrait, StreamTrait},
    Stream as AudioStream, StreamConfig,
};
use iced::{
    widget::{button, row, slider, svg},
    Element,
};
use midi_player::{Player, PlayerController, Settings as PlayerSettings};

const PLAY_SVG_ICON: &str = include_str!("../../resources/img/play.svg");
const PAUSE_SVG_ICON: &str = include_str!("../../resources/img/pause.svg");

pub(crate) struct GlobalState {
    pub(crate) controller: PlayerController,
    audio_stream: AudioStream,
    pub(crate) playing_id: Option<usize>,
}

impl GlobalState {
    pub(crate) fn new(sf: &str) -> Self {
        let settings = PlayerSettings::builder().build();
        let (player, controller) = Player::new(sf, settings)
            .expect("midi player should be initialized with default settings and soundfont");
        let audio_stream = Self::start_audio_loop(player);

        Self {
            controller,
            audio_stream,
            playing_id: None,
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
}

#[derive(Debug)]
pub(crate) struct State {
    pub(crate) is_playing: bool,
    pub(crate) path: PathBuf,
    pub(crate) id: usize,
    pub(crate) position: f64,
}

pub(crate) fn view<'a>(state: &'a State) -> Element<'a, Message> {
    let label = svg(if state.is_playing {
        "resources/img/pause.svg"
    } else {
        "resources/img/play.svg"
    });
    let message = if state.is_playing {
        Message::StopMidi(state.id)
    } else {
        Message::PlayMidi(state.id)
    };
    row![
        button(label).on_press(message).width(60.0),
        slider(0.0..=1.0, state.position, |v| {
            Message::ChangePlayingPosition(state.id, v)
        }).step(0.001)
    ]
    .align_y(iced::Alignment::Center)
    .spacing(10.0)
    .into()
}
