//! Application's GUI.
use std::{env, sync::Arc};

use iced::{
    alignment::Vertical,
    font,
    futures::sink::SinkExt,
    never, stream, time,
    widget::{
        button, column, container, operation, pick_list, rich_text, row,
        scrollable::{self, Direction, Scrollbar},
        space, span, text, text_input, Button, Column, PickList, Row,
    },
    Color, Element, Font, Length, Subscription, Task, Theme,
};
use rfd::FileDialog;

use crate::{
    app::{
        figure::{self, Palette},
        icons::Icon,
        pixel,
        player::{self, GlobalState as GlobalPlayerState, Track as PlayerState},
        theme::{Colors, Mode},
    },
    figure::{notation::Score, Domain, Event, Figure},
    interpreter,
};

/// The page's width: the window resizes, the page doesn't.
const WINDOW_WIDTH: f32 = 800.0;
/// The smallest the window goes: the page, and room for a few entries.
pub const MIN_WINDOW_SIZE: (f32, f32) = (WINDOW_WIDTH, 480.0);
const WINDOW_PADDING: f32 = 40.0;
/// The bars across the top and bottom of the page, and the frames of controls in them.
const HEADER_HEIGHT: f32 = 56.0;
const BOTTOM_BAR_HEIGHT: f32 = 76.0;
const FRAME_HEIGHT: f32 = 36.0;
/// Space between items in the header and bottom bar.
const BAR_SPACING: f32 = 12.0;
/// The scrollbar: a hairline track and a thin thumb, easy to grab.
const SCROLLBAR: f32 = 1.0;
const SCROLLER: f32 = 3.0;
const SCROLLBAR_MARGIN: f32 = 4.0;
/// Space between the output and its scrollbar.
const SCROLLBAR_SPACING: f32 = 13.0;
/// The width available to each entry in the output.
const OUTPUT_WIDTH: f32 = WINDOW_WIDTH
    - 2.0 * WINDOW_PADDING
    - SCROLLBAR.max(SCROLLER)
    - 2.0 * SCROLLBAR_MARGIN
    - SCROLLBAR_SPACING;
/// A picker's width: room for its longest option, its arrow, and never less than this.
const PICKER_CHARACTER: f32 = 8.4;
const PICKER_ARROW: f32 = 44.0;
const PICKER_WIDTH: f32 = 104.0;
/// The longest scratch folder path the header shows whole.
const PATH_CHARACTERS: usize = 48;
/// The tempo's range, in beats per minute, and the widths of the box it's typed in and of its
/// steppers.
const TEMPO: std::ops::RangeInclusive<u16> = 20..=600;
const TEMPO_WIDTH: f32 = 52.0;
const STEPPER_WIDTH: f32 = 24.0;

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
    mode: Mode,
    /// How figures of events open: as the last one was switched to.
    figure_view: View,
    /// The tempo as typed.
    tempo: String,
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
        for message in [
            interpreter::Message::GetScratchDir,
            interpreter::Message::GetAppearance,
        ] {
            interpreter::INTERPRETER_WORKER
                .interp_sender
                .send_blocking(message)
                .expect("the channel is unbound");
        }

        let tempo = midi_player_state.tempo().to_string();
        Self {
            player_state: midi_player_state,
            answer: String::new(),
            output: Vec::new(),
            question: None,
            scratch_dir: String::new(),
            input_id: "input".to_owned(),
            path_lib: Vec::new(),
            texture_lib: Vec::new(),
            active_path: String::new(),
            active_texture: String::new(),
            mode: Mode::default(),
            figure_view: View::default(),
            tempo,
        }
    }
}

#[derive(Debug)]
pub(crate) enum Output {
    Normal(String),
    /// A command as entered, with the active path and texture it was entered at.
    Command {
        prompt: Prompt,
        command: String,
    },
    Error(String),
    Player(PlayerState),
    Figure(FigureOutput),
}

/// The active path and texture, as athenaCL's prompt shows them.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub(crate) struct Prompt {
    path: String,
    texture: String,
}

/// A figure in the output, and how it's shown.
#[derive(Debug)]
pub(crate) struct FigureOutput {
    figure: Arc<Figure>,
    /// Its events as a score: a texture's, or one for each of an ensemble's. Empty when the
    /// figure has no events.
    scores: Vec<Arc<Score>>,
    view: View,
}

/// How a figure of events is shown: as graphs, or as a score.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum View {
    /// Graphs of the parameters.
    #[default]
    Plot,
    /// The events as notation.
    Score,
}

/// The iced update function.
pub fn update(state: &mut State, message: Message) -> Task<Message> {
    match message {
        Message::InputChanged(val) => state.answer = val,
        Message::Submit => return submit(state),
        Message::Answer(question, value) => return answer(state, &question, value),
        Message::SetScratchDir => set_scratch_dir(),
        Message::PiSelected(value) => send_command(format!("pio {value}")),
        Message::TiSelected(value) => send_command(format!("tio {value}")),
        Message::SetMode(mode) => set_mode(state, mode),
        Message::FigureView(index, view) => show_figure_as(state, index, view),
        Message::TempoChanged(value) => return set_tempo_text(state, value),
        Message::TempoStep(step) => return step_tempo(state, step),
        Message::Figure(message) => return update_figure(state, message),
        Message::Interpreter(message) => return update_interpreter(state, message),
        Message::Player(message) => {
            return player::update(&mut state.output, &mut state.player_state, message)
                .map(Message::Player)
        }
    }

    Task::none()
}

/// Send what's typed: the answer to the question, or a command. It's read now rather than when
/// the input was drawn, so nothing typed since is lost.
fn submit(state: &mut State) -> Task<Message> {
    let typed = state.answer.clone();
    match state.question.clone() {
        Some(question) => answer(state, &question, typed),
        None => update_interpreter(state, interpreter::Message::SendCmd(typed)),
    }
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

/// Switch the look, and save it.
fn set_mode(state: &mut State, mode: Mode) {
    state.mode = mode;
    interpreter::INTERPRETER_WORKER
        .interp_sender
        .send_blocking(interpreter::Message::SetAppearance(mode.name().to_owned()))
        .expect("cannot send message to the interpreter");
}

/// Show the figure at `index` as graphs or a score; later figures open the same way.
fn show_figure_as(state: &mut State, index: usize, view: View) {
    if let Some(Output::Figure(figure)) = state.output.get_mut(index) {
        figure.view = view;
        state.figure_view = view;
    }
}

/// Follow the typed tempo, using it once it's a tempo.
fn set_tempo_text(state: &mut State, value: String) -> Task<Message> {
    let tempo = value
        .parse::<u16>()
        .ok()
        .filter(|tempo| TEMPO.contains(tempo));
    state.tempo = value;
    match tempo {
        Some(tempo) => update(state, Message::Player(player::Message::SetTempo(tempo))),
        None => Task::none(),
    }
}

/// Raise or lower the tempo by `step` beats per minute.
fn step_tempo(state: &mut State, step: i32) -> Task<Message> {
    let tempo = (i32::from(state.player_state.tempo()) + step)
        .clamp(i32::from(*TEMPO.start()), i32::from(*TEMPO.end()));
    let tempo = u16::try_from(tempo).unwrap_or(*TEMPO.start());
    state.tempo = tempo.to_string();
    update(state, Message::Player(player::Message::SetTempo(tempo)))
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
            state.output.push(Output::Command {
                prompt: prompt(state),
                command: cmd.to_owned(),
            });
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
            state.output.push(Output::Figure(FigureOutput {
                scores: engrave(&figure),
                figure,
                view: state.figure_view,
            }));

            Task::none()
        }
        interpreter::Message::ScratchDir(value) => {
            state.scratch_dir = value;

            Task::none()
        }
        interpreter::Message::Appearance(name) => {
            state.mode = Mode::from_name(&name).unwrap_or_default();

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

/// A figure's events as a score: a texture's, or one for each of an ensemble's.
fn engrave(figure: &Figure) -> Vec<Arc<Score>> {
    let score = |events: &[Event], domain| Arc::new(Score::new(events, domain));
    match figure {
        Figure::Parameters(parameters) if !parameters.events.is_empty() => {
            vec![score(&parameters.events, parameters.domain)]
        }
        Figure::Ensemble(ensemble)
            if ensemble
                .textures
                .iter()
                .any(|texture| !texture.events.is_empty()) =>
        {
            ensemble
                .textures
                .iter()
                .map(|texture| score(&texture.events, Domain::Time))
                .collect()
        }
        _ => Vec::new(),
    }
}

/// The prompt now: the active path and texture.
fn prompt(state: &State) -> Prompt {
    Prompt {
        path: state.active_path.clone(),
        texture: state.active_texture.clone(),
    }
}

/// Show the interpreter's output, returning focus to the input.
fn push_output(state: &mut State, output: Output) -> Task<Message> {
    state.answer = "".to_owned();
    state.output.push(output);

    operation::focus(state.input_id.clone())
}

/// The iced theme: the look's.
pub fn theme(state: &State) -> Theme {
    state.mode.theme()
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<'_, Message> {
    let colors = state.mode.colors();
    let log = scrollable::Scrollable::with_direction(
        view_log(state, colors),
        Direction::Vertical(
            Scrollbar::new()
                .width(SCROLLBAR)
                .scroller_width(SCROLLER)
                .margin(SCROLLBAR_MARGIN)
                .spacing(SCROLLBAR_SPACING),
        ),
    )
    .anchor_bottom()
    .style(colors.scrollbar())
    .width(Length::Fill)
    .height(Length::Fill);

    let page = column![
        view_header(state, colors),
        rule(colors.ink, 1.0),
        container(log)
            .padding([0.0, WINDOW_PADDING])
            .height(Length::Fill),
        space().height(12),
        rule(colors.ink, 1.0),
        view_bottom_bar(state, colors),
    ]
    .width(WINDOW_WIDTH)
    .height(Length::Fill);

    container(page)
        .center_x(Length::Fill)
        .height(Length::Fill)
        .into()
}

/// The wordmark, the scratch folder and the look.
fn view_header(state: &State, colors: Colors) -> Element<'_, Message> {
    let folder = Icon::Folder
        .button(colors.outlined())
        .width(FRAME_HEIGHT)
        .height(FRAME_HEIGHT)
        .on_press(Message::SetScratchDir);
    let segment = |icon: Icon, mode: Mode| {
        icon.button(colors.segment(state.mode == mode))
            .width(32)
            .height(Length::Fill)
            .on_press(Message::SetMode(mode))
    };
    let modes = framed(
        colors,
        row![
            segment(Icon::CircleOutline, Mode::Light),
            rule_across(colors.ink),
            segment(Icon::CircleFilled, Mode::Dark),
        ],
    );

    bar(
        HEADER_HEIGHT,
        row![
            pixel::wordmark(colors.ink),
            space::horizontal(),
            pixel::label("SCRATCH", colors.dim),
            text(shorten(&state.scratch_dir, PATH_CHARACTERS)).size(12),
            folder,
            modes,
        ],
    )
}

/// The output: each command with what it printed and showed.
fn view_log(state: &State, colors: Colors) -> Element<'_, Message> {
    let palette = colors.figure();
    let mut entries: Vec<Column<'_, Message>> = Vec::new();
    for (index, output) in state.output.iter().enumerate() {
        let element = view_output(index, output, state, colors, palette);
        match entries.last_mut() {
            Some(entry) if !matches!(output, Output::Command { .. }) => {
                let taken = std::mem::replace(entry, Column::new());
                *entry = taken.push(element);
            }
            _ => entries.push(column![element].spacing(8)),
        }
    }
    entries.push(view_input(state, colors));
    Column::with_children(entries.into_iter().map(Element::from))
        .spacing(18)
        .padding([20, 0])
        .width(Length::Fill)
        .into()
}

fn view_output<'a>(
    index: usize,
    output: &'a Output,
    state: &'a State,
    colors: Colors,
    palette: Palette,
) -> Element<'a, Message> {
    match output {
        Output::Normal(msg) => text(msg).into(),
        Output::Command { prompt, command } => {
            let mut bold = Font::with_name("Fira Mono");
            bold.weight = font::Weight::Bold;
            row![
                view_prompt(prompt, colors),
                text(command).font(bold).size(15),
            ]
            .spacing(10)
            .align_y(Vertical::Center)
            .into()
        }
        Output::Error(msg) => row![view_error_tag(colors), text(msg)].spacing(10).into(),
        Output::Player(track) => player::view(track, colors).map(Message::Player),
        Output::Figure(figure) => view_figure(index, figure, state, colors, palette),
    }
}

/// athenaCL's prompt: `pi{path}ti{texture} ::`.
fn view_prompt<'a>(prompt: &Prompt, colors: Colors) -> Element<'a, Message> {
    rich_text![
        span("pi{").color(colors.dim),
        span(prompt.path.clone()).color(colors.ink),
        span("}ti{").color(colors.dim),
        span(prompt.texture.clone()).color(colors.ink),
        span("} ::").color(colors.dim),
    ]
    .on_link_click(never)
    .into()
}

fn view_error_tag<'a>(colors: Colors) -> Element<'a, Message> {
    container(pixel::label("ERR", colors.on_block))
        .padding([3, 5])
        .style(colors.block(true))
        .into()
}

/// A figure; a figure of events also has its score, and a switch between the two.
fn view_figure<'a>(
    index: usize,
    output: &'a FigureOutput,
    state: &'a State,
    colors: Colors,
    palette: Palette,
) -> Element<'a, Message> {
    let plot = figure::view(&output.figure, OUTPUT_WIDTH, &state.active_texture, palette)
        .map(Message::Figure);
    let (parts, domain) = match output.figure.as_ref() {
        Figure::Parameters(parameters) => (
            output
                .scores
                .iter()
                .map(|score| figure::Part {
                    name: "",
                    score,
                    events: &parameters.events,
                })
                .collect::<Vec<_>>(),
            parameters.domain,
        ),
        Figure::Ensemble(ensemble) => (
            ensemble
                .textures
                .iter()
                .zip(&output.scores)
                .map(|(texture, score)| figure::Part {
                    name: &texture.lane.name,
                    score,
                    events: &texture.events,
                })
                .collect(),
            Domain::Time,
        ),
        Figure::Automaton(_) => (Vec::new(), Domain::Time),
    };
    if parts.is_empty() {
        return plot;
    }
    let score = figure::score(parts, domain, palette).map(Message::Figure);
    // both stay in the output so each keeps its zoom: the one not shown has no height
    let shown = |element: Element<'a, Message>, view: View| {
        container(element)
            .height(if output.view == view {
                Length::Shrink
            } else {
                Length::Fixed(0.0)
            })
            .clip(true)
    };
    let segment = |label: &str, view: View| {
        let chosen = output.view == view;
        button(
            container(pixel::label(
                label,
                if chosen { colors.paper } else { colors.ink },
            ))
            .height(Length::Fill)
            .align_y(Vertical::Center),
        )
        .height(Length::Fill)
        .padding([0, 8])
        .style(colors.segment(chosen))
        .on_press(Message::FigureView(index, view))
    };
    let switch = container(row![
        segment("PLOT", View::Plot),
        rule_across(colors.ink),
        segment("SCORE", View::Score),
    ])
    .height(24)
    .padding(1)
    .style(colors.frame());

    column![
        shown(plot, View::Plot),
        shown(score, View::Score),
        row![space::horizontal(), switch],
    ]
    .spacing(8)
    .into()
}

/// The interpreter's question, in a block.
fn view_query<'a>(question: &'a str, colors: Colors) -> Element<'a, Message> {
    container(
        row![
            pixel::label("QUERY", colors.on_block),
            text(question).color(colors.on_block),
        ]
        .spacing(12)
        .align_y(Vertical::Center),
    )
    .padding([10, 14])
    .width(Length::Fill)
    .style(colors.block(false))
    .into()
}

/// The line being typed, at the end of the output: an answer to the question, or a command at the
/// prompt.
fn view_input(state: &State, colors: Colors) -> Column<'_, Message> {
    let (label, placeholder) = match &state.question {
        Some(_) => (pixel::label("ANSWER", colors.dim), "type answer"),
        None => (
            view_prompt(&prompt(state), colors),
            "type a command or 'help'",
        ),
    };
    let line = row![
        label,
        text_input(placeholder, &state.answer)
            .id(state.input_id.clone())
            .style(colors.input())
            .on_input(Message::InputChanged)
            .on_submit(Message::Submit)
            .padding(0)
            .size(14),
    ]
    .spacing(10)
    .align_y(Vertical::Center);

    match &state.question {
        Some(question) => column![view_query(question, colors), line].spacing(8),
        None => column![line],
    }
}

/// The active path and texture, and the tempo.
fn view_bottom_bar(state: &State, colors: Colors) -> Element<'_, Message> {
    // The icon's final transparent column completes the same visible gap as label-to-input.
    let tempo_label = row![Icon::Metronome, pixel::label("TEMPO", colors.dim)]
        .spacing(BAR_SPACING - 1.0)
        .align_y(Vertical::Center);

    // the tempo is typed, or stepped up and down
    let tempo = framed(
        colors,
        row![
            text_input("", &state.tempo)
                .on_input(Message::TempoChanged)
                .style(colors.input())
                .padding([0, 10])
                .width(TEMPO_WIDTH)
                .size(14),
            rule_across(colors.ink),
            column![
                stepper(colors, Icon::ChevronUp, 1),
                rule(colors.ink, 1.0),
                stepper(colors, Icon::ChevronDown, -1),
            ]
            .width(STEPPER_WIDTH),
        ],
    );

    bar(
        BOTTOM_BAR_HEIGHT,
        row![
            pixel::label("PATH", colors.dim),
            picker(
                colors,
                &state.path_lib,
                &state.active_path,
                Message::PiSelected
            ),
            pixel::label("TEXTURE", colors.dim),
            picker(
                colors,
                &state.texture_lib,
                &state.active_texture,
                Message::TiSelected
            ),
            space::horizontal(),
            tempo_label,
            tempo,
        ],
    )
}

/// One of the bottom bar's pickers, wide enough for its longest option.
fn picker<'a>(
    colors: Colors,
    options: &[String],
    active: &str,
    on_select: fn(String) -> Message,
) -> PickList<'a, String, Vec<String>, String, Message> {
    let selected = (!active.is_empty()).then(|| active.to_owned());
    let longest = options
        .iter()
        .map(|option| option.chars().count())
        .max()
        .unwrap_or(0) as f32;
    pick_list(options.to_vec(), selected, on_select)
        .placeholder("none")
        .padding([8, 10])
        .width((longest * PICKER_CHARACTER + PICKER_ARROW).max(PICKER_WIDTH))
        .style(colors.picker())
        .menu_style(colors.menu())
}

/// One of the tempo's steppers, stacked half each in the tempo's frame.
fn stepper<'a>(colors: Colors, icon: Icon, step: i32) -> Button<'a, Message> {
    icon.button(colors.bare())
        .width(STEPPER_WIDTH)
        .height(Length::Fill)
        .on_press(Message::TempoStep(step))
}

/// A bar across the page, `height` high: the header, and the bottom bar.
fn bar<'a>(height: f32, content: Row<'a, Message>) -> Element<'a, Message> {
    container(content.spacing(BAR_SPACING).align_y(Vertical::Center))
        .padding([0.0, WINDOW_PADDING])
        .height(height)
        .align_y(Vertical::Center)
        .into()
}

/// Controls sharing one ink frame: the look switch, the tempo.
fn framed<'a>(colors: Colors, content: Row<'a, Message>) -> Element<'a, Message> {
    container(content.align_y(Vertical::Center))
        .height(FRAME_HEIGHT)
        .padding(1)
        .style(colors.frame())
        .into()
}

/// A rule across the window, `thickness` high.
fn rule<'a>(color: Color, thickness: f32) -> Element<'a, Message> {
    container(space())
        .width(Length::Fill)
        .height(thickness)
        .style(Colors::fill(color))
        .into()
}

/// A 1 pixel rule down its row.
fn rule_across<'a>(color: Color) -> Element<'a, Message> {
    container(space())
        .width(1)
        .height(Length::Fill)
        .style(Colors::fill(color))
        .into()
}

/// A path, shortened from the front to `characters`.
fn shorten(path: &str, characters: usize) -> String {
    let count = path.chars().count();
    if count <= characters {
        return path.to_owned();
    }
    let tail: String = path.chars().skip(count - characters + 1).collect();
    format!("…{tail}")
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
    /// Send what's typed.
    Submit,
    Answer(String, String),
    SetScratchDir,
    PiSelected(String),
    TiSelected(String),
    SetMode(Mode),
    /// Show the figure at an output index as graphs or a score.
    FigureView(usize, View),
    TempoChanged(String),
    TempoStep(i32),
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
    use iced::{Point, Size};
    use player::PlayerId;

    use super::*;
    use crate::figure::{
        Automaton, Domain, Ensemble, Event, Figure, Graph, Lane, Mark, Parameters, Texture,
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
            mode: Mode::Light,
            figure_view: View::Plot,
            tempo: "120".to_owned(),
        }
    }

    fn automaton() -> Figure {
        Figure::Automaton(Automaton {
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
            textures: vec![
                Texture {
                    lane: lane("a", 0.0, 10.0, false),
                    clones: vec![lane("x", 2.0, 12.0, true)],
                    events: events(),
                },
                Texture {
                    lane: lane("b", 5.0, 20.0, false),
                    clones: Vec::new(),
                    events: events(),
                },
            ],
        })
    }

    fn events() -> Vec<Event> {
        (0..24)
            .map(|i| Event {
                time: f64::from(i) * 0.25,
                duration: 0.25,
                sustain: 0.25,
                sounds: i % 7 != 6,
                pitch: f64::from(i % 12),
                amplitude: 0.5 + f64::from(i % 4) * 0.15,
                tempo: 120.0,
            })
            .collect()
    }

    fn parameters() -> Figure {
        let events = events();
        Figure::Parameters(Parameters {
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
            events,
        })
    }

    fn figure(state: &mut State, figure: Figure) {
        drop(update(
            state,
            Message::Interpreter(interpreter::Message::Figure(Arc::new(figure))),
        ));
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
    fn submitting_sends_what_is_typed_now() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::InputChanged("tin a 0".to_owned()),
        ));
        drop(update(&mut state, Message::Submit));
        assert!(matches!(
            state.output.first(),
            Some(Output::Command { command, .. }) if command == "tin a 0"
        ));

        state.question = Some("name: ".to_owned());
        drop(update(&mut state, Message::InputChanged("x".to_owned())));
        drop(update(&mut state, Message::Submit));
        assert!(state.question.is_none());
        assert!(matches!(state.output.last(), Some(Output::Normal(text)) if text == "name: x"));
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
    fn commands_echo_to_the_output_with_their_prompt() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::SendCmd("help".to_owned())),
        ));

        assert!(matches!(
            state.output.first(),
            Some(Output::Command { prompt, command })
                if command == "help" && prompt.path == "path" && prompt.texture == "texture"
        ));
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
        figure(&mut state, ensemble());

        // an ensemble's textures each get a score
        assert!(matches!(
            state.output.first(),
            Some(Output::Figure(FigureOutput { scores, .. })) if !scores.is_empty()
        ));
    }

    #[test]
    fn figures_of_events_get_a_score_and_remember_the_view() {
        let mut state = state();
        figure(&mut state, parameters());
        assert!(matches!(
            state.output.first(),
            Some(Output::Figure(FigureOutput { scores, view: View::Plot, .. })) if scores.len() == 1
        ));

        drop(update(&mut state, Message::FigureView(0, View::Score)));
        figure(&mut state, parameters());
        assert!(matches!(
            state.output.last(),
            Some(Output::Figure(FigureOutput {
                view: View::Score,
                ..
            }))
        ));
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
            interpreter::Message::Appearance("dark".to_owned()),
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
        assert_eq!(state.mode, Mode::Dark);
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
    fn the_tempo_is_typed_and_stepped() {
        let mut state = state();
        drop(update(&mut state, Message::TempoChanged("9".to_owned())));
        assert_eq!(state.player_state.tempo(), 120, "9 is not a tempo yet");
        drop(update(&mut state, Message::TempoChanged("96".to_owned())));
        assert_eq!(state.player_state.tempo(), 96);
        drop(update(&mut state, Message::TempoStep(1)));
        assert_eq!(state.player_state.tempo(), 97);
        assert_eq!(state.tempo, "97");
        drop(update(&mut state, Message::TempoChanged("600".to_owned())));
        drop(update(&mut state, Message::TempoStep(1)));
        assert_eq!(state.player_state.tempo(), 600);
    }

    #[test]
    fn long_paths_keep_their_end() {
        assert_eq!(shorten("/a/b", 10), "/a/b");
        assert_eq!(shorten("/Users/me/music/athcl", 8), "…c/athcl");
    }

    #[test]
    fn the_gui_renders_every_output_in_the_light_look() {
        renders_every_output(Mode::Light);
    }

    #[test]
    fn the_gui_renders_every_output_in_the_dark_look() {
        renders_every_output(Mode::Dark);
    }

    /// Draw every kind of output in `mode`, hovering down the whole output.
    ///
    /// One look per test: each snapshot is a whole page rendered, which takes minutes on a
    /// machine without a gpu, and as two tests the looks are drawn side by side.
    fn renders_every_output(mode: Mode) {
        let mut state = state();
        state.output = vec![
            Output::Normal("normal".to_owned()),
            Output::Command {
                prompt: Prompt::default(),
                command: "command".to_owned(),
            },
            Output::Error("error".to_owned()),
            Output::Player(PlayerState {
                is_playing: false,
                path: "no-such-file.aiff".into(),
                id: PlayerId::Audio(0),
                position: 0.5,
            }),
        ];
        figure(&mut state, automaton());
        figure(&mut state, ensemble());
        figure(&mut state, parameters());
        figure(&mut state, parameters());
        drop(update(&mut state, Message::FigureView(7, View::Score)));
        // An existing path reaches the controls; the missing file above tests the error label.
        for is_playing in [false, true] {
            state.output.push(Output::Player(PlayerState {
                is_playing,
                path: file!().into(),
                id: PlayerId::Audio(1),
                position: 0.5,
            }));
        }
        state.question = Some("question".to_owned());
        state.mode = mode;

        let theme = theme(&state);
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
