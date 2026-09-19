//! Application's GUI.
use std::{env, sync::Arc};

use iced::{
    futures::sink::SinkExt,
    stream, time,
    widget::{
        button, column, container, container::Style as ContainerStyle, operation, pick_list, row,
        scrollable, space, text, text::Style as TextStyle, text_input,
    },
    Element, Font, Subscription, Task,
};
use rfd::FileDialog;

use super::{
    figure,
    player::{self, GlobalState as GlobalPlayerState, Track as PlayerState},
};
use crate::{figure::Figure, interpreter};

const TERM_WIDTH: u16 = 80;
const FONT_WIDTH: u16 = 10;
const WINDOW_PADDING: u16 = 40;
const OUTPUT_PADDING: u16 = 20;
/// The width available to each entry in the output.
const OUTPUT_WIDTH: f32 = (TERM_WIDTH * FONT_WIDTH - 2 * (WINDOW_PADDING + OUTPUT_PADDING)) as f32;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";
// TODO it should be configurable so users could choose they own sf
pub(super) const SOUND_FONT: &str = "resources/SGM-v2.01-YamahaGrand-Guit-Bass-v2.7.sf2";

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

impl std::fmt::Debug for State {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("State").finish_non_exhaustive()
    }
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
    Figure(Arc<Figure>),
}

/// The iced update function.
pub fn update(state: &mut State, message: Message) -> Task<Message> {
    match message {
        Message::InputChanged(val) => state.answer = val,
        Message::Answer(question, value) => return answer(state, &question, value),
        Message::SetScratchDir => set_scratch_dir(),
        Message::PiSelected(value) => send_command(format!("pio {value}")),
        Message::TiSelected(value) => send_command(format!("tio {value}")),
        Message::Figure(message) => return update_figure(state, message),
        Message::Interpreter(message) => return update_interpreter(state, message),
        Message::Player(message) => {
            return player::update(&mut state.output, &mut state.player_state, message)
                .map(Message::Player)
        }
    }

    Task::none()
}

/// Reply to the interpreter's question.
fn answer(state: &mut State, question: &str, value: String) -> Task<Message> {
    state.question = None;
    state
        .output
        .push(Output::Normal(format!("{question}{value}")));
    interpreter::INTERPRETER_WORKER
        .response_sender
        .send_blocking(value)
        .expect("cannot send message to response receiver");

    Task::none()
}

/// Let the user choose the scratch directory, and use it.
fn set_scratch_dir() {
    if let Some(value) = pick_directory("Choose scratch folder") {
        send_command(format!("apdir x {value}"));
    }
}

/// Send a command to the interpreter.
fn send_command(cmd: String) {
    interpreter::INTERPRETER_WORKER
        .interp_sender
        .send_blocking(interpreter::Message::SendCmd(cmd))
        .expect("cannot send message to the interpreter");
}

/// Select the texture or clone clicked on a figure.
fn update_figure(state: &mut State, message: figure::Message) -> Task<Message> {
    match message {
        figure::Message::SelectTexture(texture) => update(state, Message::TiSelected(texture)),
        figure::Message::SelectClone { texture, clone } => {
            for cmd in [format!("tio {texture}"), format!("tco {clone}")] {
                send_command(cmd);
            }

            Task::none()
        }
    }
}

/// Apply what the interpreter reports.
fn update_interpreter(state: &mut State, message: interpreter::Message) -> Task<Message> {
    match message {
        interpreter::Message::SendCmd(ref cmd) => {
            state.answer = "".to_owned();
            state.output.push(Output::Command(cmd.to_owned()));
            send_command(cmd.to_owned());

            Task::none()
        }
        interpreter::Message::Post(output) => push_output(state, Output::Normal(output)),
        interpreter::Message::Error(output) | interpreter::Message::PythonError(output) => {
            push_output(state, Output::Error(output))
        }
        interpreter::Message::Ask(prompt) => {
            state.answer = "".to_owned();
            state.question = Some(prompt);

            operation::focus(state.input_id.clone())
        }
        interpreter::Message::LoadMidi(path) => {
            state.output.push(Output::Player(PlayerState {
                is_playing: false,
                path: path.into(),
                id: player::PlayerId::Midi(state.output.len()),
                position: 0.0,
            }));

            Task::none()
        }
        interpreter::Message::LoadAudio(path) => {
            state.output.push(Output::Player(PlayerState {
                is_playing: false,
                path: path.into(),
                id: player::PlayerId::Audio(state.output.len()),
                position: 0.0,
            }));

            Task::none()
        }
        interpreter::Message::Figure(figure) => {
            state.output.push(Output::Figure(figure));

            Task::none()
        }
        interpreter::Message::ScratchDir(value) => {
            state.scratch_dir = value;

            Task::none()
        }
        interpreter::Message::PathLibUpdated(path_lib) => {
            state.path_lib = path_lib;

            Task::none()
        }
        interpreter::Message::TextureLibUpdated(texture_lib) => {
            state.texture_lib = texture_lib;

            Task::none()
        }
        interpreter::Message::ActivePathSet(path_name) => {
            state.active_path = path_name;

            Task::none()
        }
        interpreter::Message::ActiveTextureSet(texture_name) => {
            state.active_texture = texture_name;

            Task::none()
        }
        _ => Task::none(),
    }
}

/// Show the interpreter's output, returning focus to the input.
fn push_output(state: &mut State, output: Output) -> Task<Message> {
    state.answer = "".to_owned();
    state.output.push(output);

    operation::focus(state.input_id.clone())
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<'_, Message> {
    use iced::widget::scrollable::{Catalog, Status};

    let output = column(
        state
            .output
            .iter()
            .to_owned()
            .map(|output| view_output(output, &state.active_texture))
            .collect::<Vec<_>>(),
    );

    let mut col = column![
        view_top_panel(state),
        scrollable(output.padding(OUTPUT_PADDING))
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
        .padding([18, WINDOW_PADDING])
        .width(f32::from(TERM_WIDTH * FONT_WIDTH))
        .height(iced::Length::Fill)
        .into()
}

fn view_top_panel(state: &State) -> Element<'_, Message> {
    row![
        button(text("").font(iced_fonts::NERD_FONT).size(16.0))
            .style(button::text)
            .on_press(Message::SetScratchDir),
        text(&state.scratch_dir),
    ]
    .align_y(iced::Alignment::Center)
    .into()
}

fn view_output<'a>(output: &'a Output, active_texture: &'a str) -> Element<'a, Message> {
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
        Output::Figure(figure) => {
            container(figure::view(figure, OUTPUT_WIDTH, active_texture).map(Message::Figure))
        }
    }
    .padding([10, 0])
    .into()
}

fn view_prompt(state: &State) -> Option<Element<'_, Message>> {
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

fn view_input(state: &State) -> Element<'_, Message> {
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

fn view_bottom_panel(state: &State) -> Element<'_, Message> {
    row![
        view_pici_chooser(state),
        space::horizontal(),
        player::view_tempo(&state.player_state).map(Message::Player)
    ]
    .spacing(10.0)
    .padding([18, 0])
    .align_y(iced::Alignment::Center)
    .into()
}

fn view_pici_chooser(state: &State) -> Element<'_, Message> {
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
#[expect(
    missing_docs,
    reason = "the variants mirror the input fields and modules they carry"
)]
#[derive(Debug, Clone)]
pub enum Message {
    InputChanged(String),
    Answer(String, String),
    SetScratchDir,
    PiSelected(String),
    TiSelected(String),
    Interpreter(interpreter::Message),
    Player(player::Message),
    Figure(figure::Message),
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

/// The iced subscription: forwards interpreter messages and, while playing, player ticks.
pub fn subscription(state: &State) -> Subscription<Message> {
    // this worker runs async loop to make the worker, which runs on a System's thread communicate
    // with our app, whithout blocking the event loop of iced

    // let position_observer = state.midi_player_state.controller.new_position_observer();
    let interpreter_listener = Subscription::run(|| {
        let receiver = interpreter::INTERPRETER_WORKER.gui_receiver.clone();

        stream::channel(1000, async move |mut output| loop {
            if let Ok(msg) = receiver.recv().await {
                match msg {
                    interpreter::Message::SendCmd(_) => (),
                    _ => {
                        if output.send(msg).await.is_err() {
                            break;
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

#[cfg(test)]
mod tests {
    use player::PlayerId;
    use iced::{Point, Size};

    use super::*;
    use crate::figure::{
        Automaton, Domain, Ensemble, Figure, Graph, Lane, Mark, Palette, Parameters, Rgb, Texture,
    };

    fn state() -> State {
        State {
            answer: String::new(),
            output: Vec::new(),
            question: None,
            player_state: GlobalPlayerState::headless(),
            scratch_dir: String::new(),
            input_id: "input".to_owned(),
            path_lib: vec!["path".to_owned()],
            texture_lib: vec!["texture".to_owned()],
            active_path: "path".to_owned(),
            active_texture: "texture".to_owned(),
        }
    }

    fn palette() -> Palette {
        let shade = Rgb(0x40, 0x40, 0x40);
        Palette {
            background: Rgb(0xff, 0xff, 0xff),
            grid: shade,
            margin: Rgb(0xd0, 0xd0, 0xd0),
            main: Rgb(0x30, 0x60, 0x30),
            main_frame: Rgb(0x10, 0x40, 0x10),
            alt: Rgb(0x30, 0x30, 0x60),
            alt_frame: Rgb(0x10, 0x10, 0x40),
            title: Rgb(0, 0, 0),
            label: shade,
            unit: Rgb(0, 0, 0),
        }
    }

    fn automaton() -> Figure {
        Figure::Automaton(Automaton {
            palette: palette(),
            title: vec!["f{t}k{3}r{1}".to_owned()],
            cells: vec![vec![0.0, 1.0, 0.5], vec![1.0, 0.0, 1.0]],
            max: Some(2.0),
        })
    }

    fn ensemble() -> Figure {
        let lane = |name: &str, start: f64, end: f64, muted: bool| Lane {
            name: name.to_owned(),
            start,
            end,
            muted,
        };
        Figure::Ensemble(Ensemble {
            palette: palette(),
            textures: vec![
                Texture {
                    lane: lane("a", 0.0, 10.0, false),
                    clones: vec![lane("x", 2.0, 12.0, true)],
                },
                Texture {
                    lane: lane("b", 5.0, 20.0, false),
                    clones: Vec::new(),
                },
            ],
        })
    }

    fn parameters() -> Figure {
        Figure::Parameters(Parameters {
            palette: palette(),
            domain: Domain::Time,
            detailed: true,
            graphs: vec![Graph {
                title: "amplitude: randomBeta".to_owned(),
                marks: vec![
                    Mark {
                        start: 0.0,
                        end: 4.0,
                        value: 0.25,
                    },
                    Mark {
                        start: 4.0,
                        end: 12.0,
                        value: 0.75,
                    },
                ],
            }],
        })
    }

    #[test]
    fn input_changes_the_answer() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::InputChanged("hello".to_owned()),
        ));
        assert_eq!(state.answer, "hello");
    }

    #[test]
    fn answers_clear_the_question() {
        let mut state = state();
        state.question = Some("name: ".to_owned());
        drop(update(
            &mut state,
            Message::Answer("name: ".to_owned(), "x".to_owned()),
        ));

        assert!(state.question.is_none());
        assert!(matches!(state.output.first(), Some(Output::Normal(text)) if text == "name: x"));
    }

    #[test]
    fn commands_echo_to_the_output() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::SendCmd("help".to_owned())),
        ));

        assert!(matches!(state.output.first(), Some(Output::Command(cmd)) if cmd == "help"));
        assert!(state.answer.is_empty());
    }

    #[test]
    fn selections_send_commands() {
        let mut state = state();
        drop(update(&mut state, Message::PiSelected("path".to_owned())));
        drop(update(
            &mut state,
            Message::TiSelected("texture".to_owned()),
        ));
        drop(update(
            &mut state,
            Message::Figure(figure::Message::SelectTexture("texture".to_owned())),
        ));
        drop(update(
            &mut state,
            Message::Figure(figure::Message::SelectClone {
                texture: "texture".to_owned(),
                clone: "clone".to_owned(),
            }),
        ));
    }

    #[test]
    fn interpreter_outputs_and_errors_show() {
        let mut state = state();
        state.answer = "typed".to_owned();

        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Post("done".to_owned())),
        ));
        assert!(matches!(state.output.first(), Some(Output::Normal(text)) if text == "done"));
        assert!(state.answer.is_empty());

        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Error("err".to_owned())),
        ));
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::PythonError("py".to_owned())),
        ));
        assert!(state.output.len() == 3);
    }

    #[test]
    fn interpreter_questions_show() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Ask("name".to_owned())),
        ));

        assert_eq!(state.question.as_deref(), Some("name"));
    }

    #[test]
    fn loaded_files_become_players() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::LoadMidi("m.mid".to_owned())),
        ));
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::LoadAudio("a.aiff".to_owned())),
        ));

        assert!(
            matches!(state.output.first(), Some(Output::Player(t)) if matches!(t.id, PlayerId::Midi(0)))
        );
        assert!(
            matches!(state.output.last(), Some(Output::Player(t)) if matches!(t.id, PlayerId::Audio(1)))
        );
    }

    #[test]
    fn figures_show_in_the_output() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Figure(Arc::new(ensemble()))),
        ));

        assert!(matches!(state.output.first(), Some(Output::Figure(_))));
    }

    #[test]
    fn interpreter_updates_the_state() {
        let mut state = state();
        let messages = [
            interpreter::Message::ScratchDir("/tmp".to_owned()),
            interpreter::Message::PathLibUpdated(vec!["lib".to_owned()]),
            interpreter::Message::TextureLibUpdated(vec!["lib".to_owned()]),
            interpreter::Message::ActivePathSet("pi".to_owned()),
            interpreter::Message::ActiveTextureSet("ti".to_owned()),
            interpreter::Message::GetScratchDir,
        ];
        for message in messages {
            drop(update(&mut state, Message::Interpreter(message)));
        }

        assert_eq!(state.scratch_dir, "/tmp");
        assert_eq!(state.path_lib, ["lib".to_owned()]);
        assert_eq!(state.texture_lib, ["lib".to_owned()]);
        assert_eq!(state.active_path, "pi");
        assert_eq!(state.active_texture, "ti");
    }

    #[test]
    fn player_messages_reach_the_player() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Player(player::Message::SetTempo(96)),
        ));

        assert_eq!(state.player_state.tempo(), 96);
    }

    #[test]
    fn every_output_kind_renders() {
        let outputs = [
            Output::Normal("normal".to_owned()),
            Output::Command("command".to_owned()),
            Output::Error("error".to_owned()),
            Output::Player(PlayerState {
                is_playing: false,
                path: "no-such-file.aiff".into(),
                id: PlayerId::Audio(0),
                position: 0.5,
            }),
            Output::Figure(Arc::new(automaton())),
        ];
        for output in &outputs {
            let _ = view_output(output, "texture");
        }
    }

    #[test]
    fn the_gui_renders_every_output() {
        let mut state = state();
        state.output = vec![
            Output::Normal("normal".to_owned()),
            Output::Command("command".to_owned()),
            Output::Error("error".to_owned()),
            Output::Player(PlayerState {
                is_playing: false,
                path: "no-such-file.aiff".into(),
                id: PlayerId::Audio(0),
                position: 0.5,
            }),
            Output::Figure(Arc::new(automaton())),
            Output::Figure(Arc::new(ensemble())),
            Output::Figure(Arc::new(parameters())),
        ];
        state.question = Some("question".to_owned());

        let theme = iced::Theme::Light;
        let mut simulator = iced_test::Simulator::with_size(
            iced::Settings::default(),
            Size::new(800.0, 4000.0),
            view(&state),
        );

        // sweep the pointer down the output: every figure draws its hover overlay
        for y in (0..3900).step_by(50) {
            simulator.point_at(Point::new(400.0, y as f32));
            let _ = simulator.snapshot(&theme).expect("the gui renders");
        }
    }
}
