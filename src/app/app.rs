//! Application's GUI.

use iced::futures::sink::SinkExt;
use iced::stream;
use iced::widget::{
    button, column, container, container::Style as ContainerStyle, horizontal_space, pick_list,
    row, scrollable, text, text::Style as TextStyle, text_input,
};
use iced::{time, Element, Font, Subscription, Task};
use iced_aw::widget::number_input;
use rfd::FileDialog;

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
    scratch_dir: String,
    input_id: String,
    path_lib: Vec<String>,
    texture_lib: Vec<String>,
    active_path: String, // not system path, but athenaCL pitch path
    active_texture: String,
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

        interpreter::INTERPRETER_WORKER
            .interp_sender
            .send_blocking(interpreter::Message::GetScratchDir)
            .expect("the channel is unbound");

        Self {
            midi_player_state,
            answer: String::new(),
            output,
            question: None,
            scratch_dir: String::new(),
            input_id: "input".to_owned(),
            path_lib: Vec::new(),
            texture_lib: Vec::new(),
            active_path: String::new(),
            active_texture: String::new(),
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
pub fn update(state: &mut State, message: Message) -> Task<Message> {
    match message {
        Message::InputChanged(val) => {
            state.answer = val;
        }
        Message::SetScratchDir => {
            if let Some(value) = pick_directory("Choose scratch folder") {
                interpreter::INTERPRETER_WORKER
                    .interp_sender
                    .send_blocking(interpreter::Message::SendCmd(format!("apdir x {value}")))
                    .expect("the channel is unbound");
            }
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
                        return Task::none();
                    }
                    state
                        .midi_player_state
                        .controller
                        .set_position(player.position);
                    state.midi_player_state.update_tempo();
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
        Message::SetTempo(tempo) => {
            state.midi_player_state.set_tempo(tempo);
        }
        Message::PiSelected(value) => {
            interpreter::INTERPRETER_WORKER
                .interp_sender
                .send_blocking(interpreter::Message::SendCmd(format! {"pio {value}"}))
                .expect("cannot send message to the interpreter");
        }
        Message::TiSelected(value) => {
            interpreter::INTERPRETER_WORKER
                .interp_sender
                .send_blocking(interpreter::Message::SendCmd(format! {"tio {value}"}))
                .expect("cannot send message to the interpreter");
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

                return text_input::focus(state.input_id.clone());
            }
            interpreter::Message::Error(output) | interpreter::Message::PythonError(output) => {
                state.answer = "".to_owned();
                state.output.push(Output::Error(output));

                return text_input::focus(state.input_id.clone());
            }
            interpreter::Message::Ask(prompt) => {
                state.answer = "".to_owned();
                state.question = Some(prompt);

                return text_input::focus(state.input_id.clone());
            }
            interpreter::Message::LoadMidi(path) => {
                state.output.push(Output::MidiPlayer(MidiPlayerState {
                    is_playing: false,
                    path: path.into(),
                    id: state.output.len(),
                    position: 0.0,
                }));
            }
            interpreter::Message::ScratchDir(value) => {
                state.scratch_dir = value;
            }
            interpreter::Message::PathLibUpdated(path_lib) => {
                state.path_lib = path_lib;
            }
            interpreter::Message::TextureLibUpdated(texture_lib) => {
                state.texture_lib = texture_lib;
            }
            interpreter::Message::ActivePathSet(path_name) => {
                state.active_path = path_name;
            }
            interpreter::Message::ActiveTextureSet(texture_name) => {
                state.active_texture = texture_name;
            }
            _ => (),
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

    Task::none()
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

    let mut col = column![
        view_top_panel(state),
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
    ];
    if let Some(prompt) = view_prompt(state) {
        col = col.push(prompt);
    }

    container(col.push(view_input(state)).push(view_bottom_panel(state)))
        .padding([18, 40])
        .width(TERM_WIDTH * FONT_WIDTH)
        .height(iced::Length::Fill)
        .into()
}

fn view_top_panel(state: &State) -> Element<Message> {
    row![
        button(text("").font(iced_fonts::NERD_FONT).size(16.0))
            .style(button::text)
            .on_press(Message::SetScratchDir),
        text(&state.scratch_dir),
    ]
    .align_y(iced::Alignment::Center)
    .into()
}

fn view_output(output: &Output) -> Element<Message> {
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

fn view_prompt(state: &State) -> Option<Element<Message>> {
    state.question.as_ref().map(|q| {
        container(text(q))
            .style(|theme: &iced::Theme| ContainerStyle {
                background: Some(theme.palette().primary.into()),
                ..Default::default()
            })
            .padding(10)
            .width(iced::Length::Fill)
            .into()
    })
}

fn view_input(state: &State) -> Element<Message> {
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

    let (placeholder, on_submit_msg) = match &state.question {
        Some(question) => (
            "type answer",
            Message::Answer(question.to_owned(), state.answer.clone()),
        ),
        None => (
            "type a command or 'help'",
            interpreter::Message::SendCmd(state.answer.clone()).into(),
        ),
    };

    container(
        text_input(placeholder, &state.answer)
            .id(state.input_id.clone())
            .style(normal_style)
            .on_input(Message::InputChanged)
            .on_submit(on_submit_msg)
            .line_height(1.7),
    )
    .into()
}

fn view_bottom_panel(state: &State) -> Element<Message> {
    row![
        view_pici_chooser(state),
        horizontal_space(),
        text("󰟚").font(iced_fonts::NERD_FONT).size(16),
        text("=").size(16),
        number_input(state.midi_player_state.tempo(), 20..=600, Message::SetTempo,)
            .step(1)
            .width(60.0),
    ]
    .spacing(10.0)
    .padding([18, 0])
    .align_y(iced::Alignment::Center)
    .into()
}

fn view_pici_chooser(state: &State) -> Element<Message> {
    let pi_selection = if state.active_path.is_empty() {
        None
    } else {
        Some(state.active_path.clone())
    };
    let ti_selection = if state.active_texture.is_empty() {
        None
    } else {
        Some(state.active_texture.clone())
    };

    row![
        text("Path:"),
        pick_list(state.path_lib.as_slice(), pi_selection, Message::PiSelected).placeholder("{pi}"),
        text("Texture:"),
        pick_list(
            state.texture_lib.as_slice(),
            ti_selection,
            Message::TiSelected
        )
        .placeholder("{ti}")
    ]
    .align_y(iced::Alignment::Center)
    .spacing(10)
    .into()
}

fn pick_directory(title: &str) -> Option<String> {
    // let initial_dir = env::current_dir().unwrap_or_default();
    FileDialog::new()
        .set_title(title)
        // .set_directory(initial_dir)
        .set_can_create_directories(true)
        .pick_folder()
        .map(|pb| pb.to_string_lossy().to_string())
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
    SetTempo(u16),
    SetScratchDir,
    PiSelected(String),
    TiSelected(String),
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
