//! Application's GUI.
use std::env;

use iced::futures::sink::SinkExt;
use iced::stream;
use iced::widget::{
    button, column, container, container::Style as ContainerStyle, horizontal_space, pick_list,
    row, scrollable, text, text::Style as TextStyle, text_input,
};
use iced::{time, Element, Font, Subscription, Task};
use rfd::FileDialog;

use super::player::{self, GlobalState as GlobalPlayerState, Track as PlayerState};
use crate::interpreter;

const TERM_WIDTH: u16 = 80;
const FONT_WIDTH: u16 = 10;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";
// TODO it should be configurable so users could choose they own sf
const SOUND_FONT: &str = "resources/SGM-v2.01-YamahaGrand-Guit-Bass-v2.7.sf2";

/// athenaCL GUI.
pub struct State {
    answer: String,
    output: Vec<Output>,
    question: Option<String>,
    player_state: GlobalPlayerState,
    scratch_dir: String,
    input_id: String,
    path_lib: Vec<String>,
    texture_lib: Vec<String>,
    active_path: String, // not system path, but athenaCL pitch path
    active_texture: String,
}

impl Default for State {
    fn default() -> Self {
        let mut exe_dir = env::current_exe().expect(
            "executable directory should be available for standard
            distributions of supported platforms (macOS, Windows, Ubuntu). The executable is also
            not a symbolic link.",
        );
        exe_dir.pop();
        exe_dir.push(SOUND_FONT);
        let midi_player_state = GlobalPlayerState::new(&exe_dir.as_os_str().to_string_lossy());
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
            player_state: midi_player_state,
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
pub(crate) enum Output {
    Normal(String),
    Command(String),
    Error(String),
    Player(PlayerState),
}

/// The iced update function.
pub fn update(state: &mut State, message: Message) -> Task<Message> {
    match message {
        Message::InputChanged(val) => {
            state.answer = val;
        }
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
        Message::SetScratchDir => {
            if let Some(value) = pick_directory("Choose scratch folder") {
                interpreter::INTERPRETER_WORKER
                    .interp_sender
                    .send_blocking(interpreter::Message::SendCmd(format!("apdir x {value}")))
                    .expect("the channel is unbound");
            }
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
        Message::Interpreter(msg) => match msg {
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
                state.output.push(Output::Player(PlayerState {
                    is_playing: false,
                    path: path.into(),
                    id: player::PlayerId::Midi(state.output.len()),
                    position: 0.0,
                }));
            }
            interpreter::Message::LoadAudio(path) => {
                state.output.push(Output::Player(PlayerState {
                    is_playing: false,
                    path: path.into(),
                    id: player::PlayerId::Audio(state.output.len()),
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
        Message::Player(message) => {
            return player::update(&mut state.output, &mut state.player_state, message)
                .map(Message::Player)
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
        Output::Player(state) => container(player::view(state).map(Message::Player)),
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
        player::view_tempo(&state.player_state).map(Message::Player)
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
        text("PI:"),
        pick_list(state.path_lib.as_slice(), pi_selection, Message::PiSelected).placeholder("{pi}"),
        text("TI:"),
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
    Answer(String, String),
    SetScratchDir,
    PiSelected(String),
    TiSelected(String),
    Interpreter(interpreter::Message),
    Player(player::Message),
}

impl From<interpreter::Message> for Message {
    fn from(value: interpreter::Message) -> Self {
        Self::Interpreter(value)
    }
}

impl From<player::Message> for Message {
    fn from(value: player::Message) -> Self {
        Self::Player(value)
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
    .map(Message::Interpreter);

    let position_listener = if state.player_state.playing() {
        time::every(time::Duration::from_millis(20))
            .map(player::Message::Tick)
            .map(Message::Player)
    } else {
        Subscription::none()
    };

    Subscription::batch([interpreter_listener, position_listener])
}
