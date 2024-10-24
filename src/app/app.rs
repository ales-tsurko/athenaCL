//! Application's GUI.

use iced::futures::{join, sink::SinkExt};
use iced::stream;
use iced::widget::{column, container, scrollable, text, text::Style as TextStyle, text_input};
use iced::{time, Element, Font, Subscription};

use super::midi_player::{self, GlobalState as GlobalMidiPlayerState, State as MidiPlayerState};
use crate::interpreter;

const TERM_WIDTH: u16 = 80;
const FONT_WIDTH: u16 = 10;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";
// TODO it should be configurable so users could choose they own sf
const SOUND_FONT: &str = "./resources/SGM-v2.01-YamahaGrand-Guit-Bass-v2.7.sf2";

/// athenaCL GUI.
pub struct State {
    answer: String,
    output: Vec<Output>,
    question: Option<String>,
    midi_player_state: GlobalMidiPlayerState,
}

impl Default for State {
    fn default() -> Self {
        let midi_player_state = GlobalMidiPlayerState::new(SOUND_FONT);
        let output = vec![Output::Normal(
            r#"
                       _   _                        ___   __  
                  __ _| |_| |__   ___ _ __   __ _  / __\ / /  
                 / _` | __| '_ \ / _ \ '_ \ / _` |/ /   / /   
                | (_| | |_| | | |  __/ | | | (_| / /___/ /___ 
                 \__,_|\__|_| |_|\___|_| |_|\__,_\____/\____/ 

                            Welcome to athenaCL!
                    Type your commands in the input below.
"#
            .to_owned(),
        )];
        Self {
            midi_player_state,
            answer: String::new(),
            output,
            question: None,
        }
    }
}

#[derive(Debug)]
enum Output {
    Normal(String),
    Command(String),
    Error(String),
    MidiPlayer(MidiPlayerState),
}

/// The iced update function.
pub fn update(state: &mut State, message: Message) {
    match message {
        Message::InputChanged(val) => {
            state.answer = val;
        }
        Message::PlayMidi(id) => {
            if let Some(playing_id) = state.midi_player_state.playing_id {
                if let Some(Output::MidiPlayer(player_state)) = state.output.get_mut(playing_id) {
                    player_state.is_playing = false;
                    state.midi_player_state.playing_id = None;
                }
            }

            if let Some(Output::MidiPlayer(player)) = state.output.get_mut(id) {
                player.is_playing = true;
                if player.path.exists() {
                    if let Err(e) = state
                        .midi_player_state
                        .controller
                        .set_file(Some(&player.path))
                    {
                        state.output.push(Output::Error(e.to_string()));
                        return;
                    }
                    state.midi_player_state.controller.set_position(player.position);
                    state.midi_player_state.controller.play();
                    state.midi_player_state.playing_id = Some(id);
                }
            }
        }
        Message::StopMidi(id) => {
            if let Some(Output::MidiPlayer(player_state)) = state.output.get_mut(id) {
                player_state.is_playing = false;
                state.midi_player_state.controller.stop();
                if let Some(playing_id) = state.midi_player_state.playing_id {
                    if playing_id == id {
                        state.midi_player_state.playing_id = None;
                    }
                }
            }
        }
        Message::ChangePlayingPosition(id, position) => {
            if let Some(Output::MidiPlayer(player_state)) = state.output.get_mut(id) {
                player_state.position = position;

                if let Some(playing_id) = state.midi_player_state.playing_id {
                    if playing_id == id {
                        state.midi_player_state.controller.set_position(position);
                    }
                }
            }
        }
        Message::Tick(_) => {
            if let Some(playing_id) = state.midi_player_state.playing_id {
                if let Some(Output::MidiPlayer(player_state)) = state.output.get_mut(playing_id) {
                    let position = state.midi_player_state.controller.position();

                    player_state.position = position;

                    if position >= 1.0 {
                        player_state.is_playing = false;
                        player_state.position = 0.0;
                        state.midi_player_state.playing_id = None;
                    }
                }
            }
        }
        Message::InterpreterMessage(msg) => match msg {
            interpreter::Message::SendCmd(ref cmd) => {
                state.answer = "".to_owned();
                state.output.push(Output::Command(cmd.to_owned()));
                interpreter::INTERPRETER_WORKER
                    .interp_sender
                    .send_blocking(msg)
                    .expect("cannot send message to the interpreter");
            }
            interpreter::Message::Post(output) => {
                state.answer = "".to_owned();
                state.output.push(Output::Normal(output));
            }
            interpreter::Message::Error(output) | interpreter::Message::PythonError(output) => {
                state.answer = "".to_owned();
                state.output.push(Output::Error(output));
            }
            interpreter::Message::Ask(prompt) => {
                state.answer = "".to_owned();
                state.question = Some(prompt);
            }
            interpreter::Message::LoadMidi(path) => {
                state.output.push(Output::MidiPlayer(MidiPlayerState {
                    is_playing: false,
                    path: path.into(),
                    id: state.output.len(),
                    position: 0.0,
                }));
            }
        },
        Message::Answer(question, value) => {
            state.question = None;
            state
                .output
                .push(Output::Normal(format!("{question}{value}")));
            interpreter::INTERPRETER_WORKER
                .response_sender
                .send_blocking(value)
                .expect("cannot send message to response receiver");
        }
    }
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<Message> {
    use iced::widget::scrollable::{Catalog, Status};

    let output = column(
        state
            .output
            .iter()
            .to_owned()
            .map(view_output)
            .map(Into::into)
            .collect::<Vec<_>>(),
    );

    container(column![
        scrollable(output.padding(20.0))
            .style(|theme: &iced::Theme, status: Status| {
                let mut style = theme.style(&<iced::Theme as Catalog>::default(), status);
                let mut background = theme.palette().background;
                background.r *= 0.7;
                background.g *= 0.7;
                background.b *= 0.7;

                style.container = style.container.background(background);

                style
            })
            .width(iced::Length::Fill)
            .height(iced::Length::Fill)
            .anchor_bottom(),
        view_prompt(state),
    ])
    .padding(40)
    .width(TERM_WIDTH * FONT_WIDTH)
    .height(iced::Length::Fill)
    .into()
}

fn view_output<'a>(output: &'a Output) -> Element<'a, Message> {
    match output {
        Output::Normal(msg) => container(text(msg)),
        Output::Command(msg) => {
            let mut font = Font::MONOSPACE;
            font.weight = iced::font::Weight::Bold;
            container(text(msg).font(font).size(18.0))
        }
        Output::Error(msg) => container(text(msg).style(|theme: &iced::Theme| TextStyle {
            color: Some(theme.palette().danger),
        })),
        Output::MidiPlayer(state) => container(midi_player::view(state)),
    }
    .padding([10, 0])
    .into()
}

fn view_prompt<'a>(state: &'a State) -> Element<'a, Message> {
    use iced::widget::text_input::{Catalog, Status};

    let normal_style = |theme: &iced::Theme, status: Status| {
        let mut style = theme.style(&<iced::Theme as Catalog>::default(), status);

        style.border = iced::Border {
            width: 0.0,
            ..Default::default()
        };
        style.background = theme
            .palette()
            .background
            .inverse()
            .scale_alpha(0.03)
            .into();

        style
    };

    let question_style = move |theme: &iced::Theme, status: Status| {
        let mut style = normal_style(theme, status);
        style.placeholder = theme.palette().primary;
        style
    };

    let text_input = match &state.question {
        Some(question) => text_input(&question, &state.answer)
            .style(question_style)
            .on_input(Message::InputChanged)
            .on_submit(Message::Answer(question.to_owned(), state.answer.clone())),
        None => text_input("type command or 'help'", &state.answer)
            .style(normal_style)
            .on_input(Message::InputChanged)
            .on_submit(interpreter::Message::SendCmd(state.answer.clone()).into()),
    };

    container(text_input).height(40).into()
}

/// The iced message type.
#[allow(missing_docs)]
#[derive(Debug, Clone)]
pub enum Message {
    InputChanged(String),
    InterpreterMessage(interpreter::Message),
    Answer(String, String),
    PlayMidi(usize),
    StopMidi(usize),
    // id, position
    ChangePlayingPosition(usize, f64),
    Tick(time::Instant),
}

impl From<interpreter::Message> for Message {
    fn from(value: interpreter::Message) -> Self {
        Self::InterpreterMessage(value)
    }
}

#[allow(missing_docs)]
pub fn subscription(state: &State) -> Subscription<Message> {
    // this worker runs async loop to make the worker, which runs on a System's thread communicate
    // with our app, whithout blocking the event loop of iced

    // let position_observer = state.midi_player_state.controller.new_position_observer();
    let interpreter_listener = Subscription::run(|| {
        let receiver = interpreter::INTERPRETER_WORKER.gui_receiver.clone();

        stream::channel(1000, |mut output| async move {
            loop {
                if let Ok(msg) = receiver.recv().await {
                    match msg {
                        interpreter::Message::SendCmd(_) => (),
                        _ => {
                            let _ = output.send(msg).await;
                        }
                    }
                }
            }
        })
    })
    .map(Message::InterpreterMessage);

    let position_listener = if state.midi_player_state.controller.is_playing() {
        time::every(time::Duration::from_millis(20)).map(Message::Tick)
    } else {
        Subscription::none()
    };

    Subscription::batch([interpreter_listener, position_listener])
}
