//! Application state, event handling, and rendering.
use std::sync::Arc;

use iced::{
    advanced::widget::{self, operation::scrollable::AbsoluteOffset},
    alignment::Vertical,
    font,
    futures::sink::SinkExt,
    keyboard, never, stream, time,
    widget::{
        button, column, container, operation, pick_list, responsive, rich_text, row,
        scrollable::{self, Direction},
        space, span, text, Button, Column, PickList, Row,
    },
    window, Color, Element, Font, Length, Padding, Rectangle, Subscription, Task, Theme, Vector,
};
use rfd::FileDialog;
use rustyline::history::SearchDirection;

use crate::{
    app::{
        browser::{Browser, Message as BrowserMessage},
        completion::{Action as CompletionAction, Sources, Suggestions},
        figure::{self, Palette},
        history::{self, History},
        icons::Icon,
        manual, pixel,
        player::{self, GlobalState as GlobalPlayerState, Track as PlayerState},
        scrollbar,
        terminal_input::Input,
        theme::{Colors, Mode},
    },
    figure::{notation::Score, Domain, Event, Figure},
    interpreter::{self, Question},
    manual as manual_source,
    manual::Page as ManualPage,
};
use super::{bars, playback};

/// The log's original page width, including its side padding.
const LOG_MAX_WIDTH: f32 = 800.0;
/// Room for the browser, its file-action panel, and a usable log.
pub const MIN_WINDOW_SIZE: (f32, f32) = (1040.0, 640.0);
pub(super) const WINDOW_PADDING: f32 = 40.0;
/// The bars across the top and bottom of the page, and the frames of controls in them.
pub(super) const HEADER_HEIGHT: f32 = 56.0;
pub(super) const BOTTOM_BAR_HEIGHT: f32 = 76.0;
pub(in crate::app) const FRAME_HEIGHT: f32 = 36.0;
/// Space between the items of a group in the header and bottom bar: a label, its control, and
/// the button that goes with it.
pub(in crate::app) const BAR_SPACING: f32 = 12.0;
/// Space between those groups, twice that inside them, so each reads as one.
pub(super) const GROUP_SPACING: f32 = 2.0 * BAR_SPACING;
/// The width available to each entry in the output.
#[cfg(test)]
pub(super) const OUTPUT_WIDTH: f32 =
    LOG_MAX_WIDTH - 2.0 * WINDOW_PADDING - scrollbar::RESERVED_WIDTH;
/// A picker's width: room for its longest option, its arrow, and never less than this.
const PICKER_CHARACTER: f32 = 8.4;
const PICKER_ARROW: f32 = 44.0;
const PICKER_WIDTH: f32 = 104.0;
const PICKER_PADDING: f32 = 8.0;
/// The longest scratch folder path the header shows whole.
pub(super) const PATH_CHARACTERS: usize = 24;
/// The manual on the web, for `AUdoc www`.
const MANUAL_URL: &str = "https://athenacl.alestsurko.by";
/// The tempo's range, in beats per minute, and the widths of the box it's typed in and of its
/// steppers.
const TEMPO: std::ops::RangeInclusive<u16> = 20..=600;
pub(super) const TEMPO_WIDTH: f32 = 52.0;
pub(super) const STEPPER_WIDTH: f32 = 24.0;
/// Room either side of an answer's word in its button.
const ANSWER_PADDING: u16 = 10;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";
/// The built-in sound font, shipped beside the executable with its license rather than built into
/// it.
pub(super) const SOUND_FONT: &str = "resources/FluidR3_GM.sf2";

/// athenaCL GUI.
pub struct State {
    pub(super) answer: String,
    pub(super) history: History,
    pub(super) suggestions: Suggestions,
    pub(super) output: Vec<Output>,
    pub(super) question: Option<Query>,
    pub(super) player_state: GlobalPlayerState,
    pub(super) playback: crate::app::playback::Preferences,
    pub(super) scratch_dir: String,
    pub(super) browser: Browser,
    pub(super) input_id: String,
    pub(super) path_lib: Vec<String>,
    pub(super) texture_lib: Vec<String>,
    pub(super) active_path: String, // not system path, but athenaCL pitch path
    pub(super) active_texture: String,
    pub(super) mode: Mode,
    /// How figures of events open: as the last one was switched to.
    pub(super) figure_view: View,
    /// The tempo as typed.
    pub(super) tempo: String,
    /// A page of the manual the running command showed, to scroll to once the command is done:
    /// what the command prints after it would push the page's start out of view.
    pub(super) reveal: Option<usize>,
    /// The AthenaObject's file, and whether it holds unsaved work, for the window's title.
    pub(super) document: interpreter::Document,
}

impl State {
    pub(super) fn update_completion(&mut self, action: CompletionAction) -> Task<Message> {
        match action {
            CompletionAction::Edit(value, cursor) => self.edit_command(value, cursor),
            CompletionAction::Cycle(backwards, value, cursor) => {
                return self.complete_command(backwards, value, cursor);
            }
            CompletionAction::Select(index) => return self.accept_suggestion(index),
            CompletionAction::Dismiss => self.suggestions.dismiss(),
        }
        Task::none()
    }

    fn completion(&mut self) -> (&mut Suggestions, Sources<'_>) {
        (
            &mut self.suggestions,
            Sources {
                history: &self.history,
                paths: &self.path_lib,
                textures: &self.texture_lib,
            },
        )
    }

    fn edit_command(&mut self, value: String, cursor: Option<usize>) {
        if self.question.is_none() {
            let (suggestions, sources) = self.completion();
            suggestions.edit(&value, cursor, sources);
            self.answer = value;
        }
    }

    fn complete_command(&mut self, backwards: bool, value: String, cursor: usize) -> Task<Message> {
        if self.question.is_some() {
            return Task::none();
        }
        self.edit_command(value, Some(cursor));
        let (suggestions, sources) = self.completion();
        let completion = suggestions.cycle(backwards, sources);
        self.apply_completion(completion)
    }

    fn accept_suggestion(&mut self, index: usize) -> Task<Message> {
        if self.question.is_some() {
            return Task::none();
        }
        let completion = self.suggestions.accept(index);
        self.apply_completion(completion)
    }

    /// Fill the input without submitting; Enter executes the command.
    fn apply_completion(&mut self, completion: Option<(String, usize)>) -> Task<Message> {
        let Some((value, cursor)) = completion else {
            return Task::none();
        };
        self.answer = value;
        operation::focus(self.input_id.clone())
            .chain(operation::move_cursor_to(self.input_id.clone(), cursor))
    }
}

/// How the app draws: its own monospaced font at the log's size, and no antialiasing.
///
/// Headless renders use the same, so that what they draw is what the app draws.
pub fn settings() -> iced::Settings {
    iced::Settings {
        id: Some(APPLICATION_ID.to_string()),
        default_text_size: 14.into(),
        default_font: Font::with_name("Fira Mono"),
        fonts: vec![
            include_bytes!("../../../resources/fonts/Fira_Mono/FiraMono-Bold.ttf")
                .as_slice()
                .into(),
            include_bytes!("../../../resources/fonts/Fira_Mono/FiraMono-Medium.ttf")
                .as_slice()
                .into(),
            include_bytes!("../../../resources/fonts/Fira_Mono/FiraMono-Regular.ttf")
                .as_slice()
                .into(),
        ],
        // figures are pixel art: without multisampling, their pixels stay sharp at any offset
        antialiasing: false,
        ..Default::default()
    }
}

/// The app as it opens: the prompt already has the caret, so the first command can just be typed.
pub fn boot() -> (State, Task<Message>) {
    let state = State::default();
    let focus = operation::focus(state.input_id.clone());
    (state, focus)
}

impl std::fmt::Debug for State {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("State").finish_non_exhaustive()
    }
}

impl Default for State {
    fn default() -> Self {
        let mut midi_player_state =
            GlobalPlayerState::new(&playback::builtin_soundfont().to_string_lossy());
        let (playback, playback_error) = crate::app::playback::Preferences::load();
        midi_player_state.set_volume(playback.settings.gain());
        if let Some(path) = &playback.settings.soundfont {
            midi_player_state.restore_soundfont(path);
        }
        for message in [
            interpreter::Message::GetScratchDir,
            interpreter::Message::GetAppearance,
            interpreter::Message::GetCompletions,
        ] {
            interpreter::INTERPRETER_WORKER
                .interp_sender
                .send_blocking(message)
                .expect("the channel is unbound");
        }

        let tempo = midi_player_state.tempo().to_string();
        let mut history = History::default();
        let mut output = Vec::new();
        if let Some(error) = playback_error {
            output.push(Output::Error(error));
        }
        if let Err(error) = history.load_default() {
            output.push(Output::Error(format!(
                "Could not load command history: {error}"
            )));
        }
        Self {
            player_state: midi_player_state,
            playback,
            answer: String::new(),
            history,
            suggestions: Suggestions::default(),
            output,
            question: None,
            scratch_dir: String::new(),
            browser: Browser::default(),
            input_id: "input".to_owned(),
            path_lib: Vec::new(),
            texture_lib: Vec::new(),
            active_path: String::new(),
            active_texture: String::new(),
            mode: Mode::default(),
            figure_view: View::default(),
            reveal: None,
            document: interpreter::Document::default(),
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
    /// A page of the manual, from `AUdoc`.
    Manual(Box<ManualPage>),
    /// Text captured when a file was opened; later edits to the file do not rewrite the log.
    File {
        path: std::path::PathBuf,
        content: String,
    },
}

/// The active path and texture, as athenaCL's prompt shows them.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub(crate) struct Prompt {
    path: String,
    texture: String,
}

/// A question from the interpreter, waiting to be answered.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct Query {
    prompt: String,
    question: Question,
    /// Which of the answers is picked: the arrows move it, return takes it.
    picked: usize,
}

impl Query {
    /// A question as it arrives, with its default answer picked.
    fn new(prompt: String, question: Question) -> Self {
        let picked = match question {
            Question::Text => 0,
            Question::YesNo { default } | Question::YesNoCancel { default } => {
                usize::from(!default)
            }
        };
        Self {
            prompt,
            question,
            picked,
        }
    }

    /// Move the pick by `step` answers, stopping at either end.
    fn move_pick(&mut self, step: i32) {
        let last = self.question.answers().len().saturating_sub(1);
        self.picked = if step < 0 {
            self.picked.saturating_sub(step.unsigned_abs() as usize)
        } else {
            self.picked
                .saturating_add(step.unsigned_abs() as usize)
                .min(last)
        };
    }

    /// The answer that is picked.
    fn picked(&self) -> Option<&'static str> {
        self.question.answers().get(self.picked).copied()
    }
}

/// A figure in the output, and how it's shown.
#[derive(Debug)]
pub(crate) struct FigureOutput {
    figure: Arc<Figure>,
    /// Its events as a score: a texture's, or one for each of an ensemble's. Empty when the
    /// figure has no events.
    scores: Vec<Arc<Score>>,
    pub(super) view: View,
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
        Message::Completion(action) => return state.update_completion(action),
        Message::Submit => return submit(state),
        Message::Answer(value) => return answer_current(state, value),
        Message::Key(..) | Message::TreeKey(..) | Message::Typed(_) => {
            return use_keyboard(state, message)
        }
        Message::ManualLink(index, target) => return follow_manual_link(state, index, &target),
        Message::RecallHistory { direction, focused } => {
            return recall_history(state, direction, focused)
        }
        Message::Browser(message) => return state.update_browser(message),
        Message::Playback(message) => return state.update_playback(message),
        Message::PiSelected(value) => send_command(format!("pio {value}")),
        Message::TiSelected(value) => send_command(format!("tio {value}")),
        Message::SetMode(mode) => set_mode(state, mode),
        Message::FigureView(index, view) => show_figure_as(state, index, view),
        Message::TempoChanged(value) => return set_tempo_text(state, value),
        Message::TempoStep(step) => return step_tempo(state, step),
        Message::Figure(message) => return update_figure(state, message),
        Message::Interpreter(message) => return update_interpreter(state, message),
        Message::Player(message) => return state.update_player(message),
        Message::WindowOpened(id) => return route_quit(id),
        Message::CloseRequested => return request_quit(state),
    }

    Task::none()
}

/// Point Cmd+Q and the app menu's Quit at the window's close button, so that quitting that way
/// offers to save unsaved work too.
fn route_quit(id: window::Id) -> Task<Message> {
    window::run(id, |window| {
        let routed = match window.window_handle() {
            Ok(handle) => close_on_quit::route(handle.as_raw()).map_err(|error| error.to_string()),
            Err(error) => Err(error.to_string()),
        };
        if let Err(error) = routed {
            eprintln!("Cmd+Q quits without offering to save: {error}");
        }
    })
    .discard()
}

/// Quit, as the window's close button and Cmd+Q ask: the interpreter first offers to save unsaved
/// work. A question already waiting is brought into view instead, to be answered first.
fn request_quit(state: &mut State) -> Task<Message> {
    if state.question.is_some() {
        return operation::scroll_to(
            LOG,
            AbsoluteOffset {
                x: None,
                y: Some(0.0),
            },
        )
        .chain(operation::focus(state.input_id.clone()));
    }
    update_interpreter(state, interpreter::Message::SendCmd("quit".to_owned()))
}

/// Send what's typed: the answer to the question, or a command. It's read now rather than when
/// the input was drawn, so nothing typed since is lost.
fn submit(state: &mut State) -> Task<Message> {
    state.suggestions.clear();
    let typed = state.answer.clone();
    match state.question.clone() {
        Some(query) => answer(state, &query.prompt, typed),
        None => {
            let recorded = state.history.record(&typed);
            if typed.trim().is_empty() {
                state.answer.clear();
                return Task::none();
            }
            let task = update_interpreter(state, interpreter::Message::SendCmd(typed));
            if let Err(error) = recorded {
                state.output.push(Output::Error(format!(
                    "Could not save command history: {error}"
                )));
            }
            task
        }
    }
}

/// Add `typed` to the end of the line being typed, and give it focus back: whatever was clicked
/// last, as output selected to copy, typing is for the prompt.
fn type_at_prompt(state: &mut State, typed: &str) -> Task<Message> {
    if state.browser.edit.is_some() {
        return Task::none();
    }
    state.browser.focused = false;
    let value = format!("{}{typed}", state.answer);
    match &state.question {
        // the answers' switch takes no typing
        Some(query) if !query.question.answers().is_empty() => return Task::none(),
        Some(_) => state.answer = value,
        None => {
            let cursor = value.chars().count();
            state.edit_command(value, Some(cursor));
        }
    }
    operation::focus(state.input_id.clone())
}

/// Keys and text no widget took.
fn use_keyboard(state: &mut State, message: Message) -> Task<Message> {
    match message {
        Message::Key(key, modifiers) => press_key(state, &key, modifiers),
        Message::TreeKey(key, modifiers, prompt) => press_tree_key(state, key, modifiers, prompt),
        Message::Typed(typed) => type_at_prompt(state, &typed),
        _ => Task::none(),
    }
}

/// What a key no widget took is for: an open file form, the file tree, or the prompt.
fn press_key(
    state: &mut State,
    key: &keyboard::Key,
    modifiers: keyboard::Modifiers,
) -> Task<Message> {
    if state.browser.edit.is_some() {
        return match key {
            keyboard::Key::Named(keyboard::key::Named::Escape) if !state.browser.busy => {
                state.update_browser(BrowserMessage::Cancel)
            }
            _ => Task::none(),
        };
    }
    // after a click in the file tree, keys are its own, unless the prompt has taken them back
    if state.browser.focused && state.browser.visible && state.question.is_none() {
        let key = key.clone();
        return operation::is_focused(state.input_id.clone())
            .map(move |prompt| Message::TreeKey(key.clone(), modifiers, prompt));
    }
    press_key_at_prompt(state, key, modifiers)
}

/// A key for the file tree, unless the prompt has taken the keyboard back since the tree was
/// clicked: then it is the prompt's again.
fn press_tree_key(
    state: &mut State,
    key: keyboard::Key,
    modifiers: keyboard::Modifiers,
    prompt_focused: bool,
) -> Task<Message> {
    if prompt_focused {
        state.browser.focused = false;
        return press_key_at_prompt(state, &key, modifiers);
    }
    state.update_browser(BrowserMessage::Key(key, modifiers))
}

/// Browse commands when the input is focused, or move and take a question's picked answer.
fn press_key_at_prompt(
    state: &mut State,
    key: &keyboard::Key,
    modifiers: keyboard::Modifiers,
) -> Task<Message> {
    let Some(query) = state.question.as_mut() else {
        if let Some(direction) = history::direction(key, modifiers) {
            return operation::is_focused(state.input_id.clone())
                .map(move |focused| Message::RecallHistory { direction, focused });
        }
        return Task::none();
    };
    if query.question.answers().is_empty() {
        return Task::none();
    }
    match key {
        keyboard::Key::Named(keyboard::key::Named::ArrowLeft) => query.move_pick(-1),
        keyboard::Key::Named(keyboard::key::Named::ArrowRight) => query.move_pick(1),
        keyboard::Key::Named(keyboard::key::Named::Enter) => {
            if let Some(answer) = query.picked() {
                return answer_current(state, answer.to_owned());
            }
        }
        _ => (),
    }
    Task::none()
}

/// Apply a history key after checking focus. A question may have arrived in the meantime.
fn recall_history(state: &mut State, direction: SearchDirection, focused: bool) -> Task<Message> {
    if focused && state.question.is_none() {
        match state.history.recall(direction, &state.answer) {
            Ok(Some(command)) => {
                state.answer = command;
                state.suggestions.clear();
                return operation::move_cursor_to_end(state.input_id.clone());
            }
            Ok(None) => (),
            Err(error) => state
                .output
                .push(Output::Error(format!("Could not recall command: {error}"))),
        }
    }
    Task::none()
}

/// Open `url` in whatever the system uses for the web.
fn open_in_browser(url: &str) {
    if let Err(err) = open::that_detached(url) {
        eprintln!("cannot open {url}: {err}");
    }
}

/// Follow a link in the page of the manual at `index`: turn that page to the one it leads to, where
/// it is, or open the web in a browser.
fn follow_manual_link(state: &mut State, index: usize, target: &str) -> Task<Message> {
    if target.contains("://") || target.starts_with("mailto:") {
        open_in_browser(target);
        return Task::none();
    }
    let page = manual_source::request_of(target)
        .ok_or_else(|| format!("the manual has no page at {target}"))
        .and_then(|request| manual_source::read(&request));
    match (page, state.output.get_mut(index)) {
        (Ok(page), Some(Output::Manual(shown))) => {
            **shown = page;
            operation::focus(state.input_id.clone()).chain(reveal(index))
        }
        (Ok(page), _) => push_output(state, Output::Manual(Box::new(page))),
        (Err(message), _) => push_output(state, Output::Error(message)),
    }
}

/// Put what `request` asks for into the log, to read from its start once the command is done.
fn show_manual(state: &mut State, request: &manual_source::Request) -> Task<Message> {
    if *request == manual_source::Request::Web {
        open_in_browser(MANUAL_URL);
    }
    match manual_source::read(request) {
        Ok(page) => {
            state.reveal = Some(state.output.len());
            push_output(state, Output::Manual(Box::new(page)))
        }
        Err(message) => push_output(state, Output::Error(message)),
    }
}

/// The id of the log, which is scrolled to a page of the manual.
const LOG: &str = "log";

/// The id of the page of the manual at `index` in the log.
fn page_id(index: usize) -> String {
    format!("manual-{index}")
}

/// Scroll the log to the start of the page of the manual at `index`.
pub(super) fn reveal(index: usize) -> Task<Message> {
    iced::advanced::widget::operate(StartOf {
        log: LOG.into(),
        target: page_id(index).into(),
        log_bounds: None,
        top: None,
    })
    .then(|offset| operation::scroll_to(LOG, offset))
}

/// Finds how far the log is to be scrolled for the widget with the `target` id to start at the top
/// of its view.
struct StartOf {
    log: widget::Id,
    target: widget::Id,
    /// The log's view and all it holds.
    log_bounds: Option<(Rectangle, Rectangle)>,
    top: Option<f32>,
}

impl widget::Operation<AbsoluteOffset<Option<f32>>> for StartOf {
    fn traverse(
        &mut self,
        operate: &mut dyn FnMut(&mut dyn widget::Operation<AbsoluteOffset<Option<f32>>>),
    ) {
        operate(self);
    }

    fn container(&mut self, id: Option<&widget::Id>, bounds: Rectangle) {
        if id == Some(&self.target) {
            self.top = Some(bounds.y);
        }
    }

    fn scrollable(
        &mut self,
        id: Option<&widget::Id>,
        bounds: Rectangle,
        content_bounds: Rectangle,
        _translation: Vector,
        _state: &mut dyn widget::operation::Scrollable,
    ) {
        if id == Some(&self.log) {
            self.log_bounds = Some((bounds, content_bounds));
        }
    }

    fn finish(&self) -> widget::operation::Outcome<AbsoluteOffset<Option<f32>>> {
        let (Some((view, content)), Some(top)) = (self.log_bounds, self.top) else {
            return widget::operation::Outcome::None;
        };
        // the log keeps to its end, so it is scrolled by how far its view is from there
        let from_end = (content.height - view.height).max(0.0) - (top - content.y);
        widget::operation::Outcome::Some(AbsoluteOffset {
            x: None,
            y: Some(from_end.max(0.0)),
        })
    }
}

/// Reply to the question on screen.
fn answer_current(state: &mut State, value: String) -> Task<Message> {
    let Some(query) = state.question.clone() else {
        return Task::none();
    };
    answer(state, &query.prompt, value)
}

/// Reply to the interpreter's question.
fn answer(state: &mut State, question: &str, value: String) -> Task<Message> {
    state.question = None;
    state.answer.clear();
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
pub(super) fn set_scratch_dir() {
    if let Some(value) = pick_directory("Choose scratch folder") {
        interpreter::INTERPRETER_WORKER
            .interp_sender
            .send_blocking(interpreter::Message::SetScratchDir(value))
            .expect("the interpreter channel is unbounded");
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
            state.suggestions.clear();
            state.history.reset();
            state.answer = "".to_owned();
            state.output.push(Output::Command {
                prompt: prompt(state),
                command: cmd.to_owned(),
            });
            send_command(cmd.to_owned());

            Task::none()
        }
        interpreter::Message::Post(output) => push_result(state, Output::Normal(output)),
        interpreter::Message::Error(output) | interpreter::Message::PythonError(output) => {
            push_result(state, Output::Error(output))
        }
        interpreter::Message::Ask { prompt, question } => {
            state.suggestions.clear();
            state.history.reset();
            state.answer = "".to_owned();
            state.question = Some(Query::new(prompt, question));

            operation::focus(state.input_id.clone())
        }
        interpreter::Message::LoadMidi(path) => {
            let id = player::PlayerId::Midi(state.output.len());
            state.output.push(Output::Player(PlayerState {
                is_playing: false,
                path: path.into(),
                id,
                position: 0.0,
            }));

            // a playback command's result is heard at once, not left paused for the play button
            state.update_player(player::Message::Play(id))
        }
        interpreter::Message::LoadAudio(path) => {
            let id = player::PlayerId::Audio(state.output.len());
            state.output.push(Output::Player(PlayerState {
                is_playing: false,
                path: path.into(),
                id,
                position: 0.0,
            }));

            state.update_player(player::Message::Play(id))
        }
        interpreter::Message::Manual(request) => show_manual(state, &request),
        interpreter::Message::Figure(figure) => {
            state.output.push(Output::Figure(FigureOutput {
                scores: engrave(&figure),
                figure,
                view: state.figure_view,
            }));

            Task::none()
        }
        interpreter::Message::ScratchDir(value) => {
            let task = state.browser.set_root(value.clone().into());
            state.scratch_dir = value;
            task.map(Message::Browser)
        }
        interpreter::Message::Appearance(name) => {
            state.mode = Mode::from_name(&name).unwrap_or_default();

            Task::none()
        }
        interpreter::Message::Completions(commands) => {
            let (suggestions, sources) = state.completion();
            suggestions.set_commands(commands, sources);
            Task::none()
        }
        interpreter::Message::PathLibUpdated(path_lib) => {
            state.path_lib = path_lib;
            refresh_suggestions(state);
            Task::none()
        }
        interpreter::Message::TextureLibUpdated(texture_lib) => {
            state.texture_lib = texture_lib;
            refresh_suggestions(state);
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
        interpreter::Message::Document(document) => {
            state.document = document;

            Task::none()
        }
        interpreter::Message::Quit => iced::exit(),
        _ => Task::none(),
    }
}

fn refresh_suggestions(state: &mut State) {
    let (suggestions, sources) = state.completion();
    suggestions.refresh(sources);
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
pub(super) fn push_output(state: &mut State, output: Output) -> Task<Message> {
    state.output.push(output);
    refocus(state)
}

/// Give the input its focus back, unless a file form in the browser has it.
fn refocus(state: &State) -> Task<Message> {
    if state.browser.edit.is_some() {
        Task::none()
    } else {
        operation::focus(state.input_id.clone())
    }
}

/// Show what a command printed as it finished, and then the start of the page of the manual it
/// showed, if it showed one. A command that printed nothing, as one cancelled, leaves no line.
fn push_result(state: &mut State, output: Output) -> Task<Message> {
    let focus = match output {
        Output::Normal(text) if text.is_empty() => refocus(state),
        output => push_output(state, output),
    };
    match state.reveal.take() {
        Some(index) => focus.chain(reveal(index)),
        None => focus,
    }
}

/// The iced theme: the look's.
pub fn theme(state: &State) -> Theme {
    state.mode.theme()
}

/// The window's title: the name of the AthenaObject's file, when it has one, marked while it holds
/// unsaved work, as macOS titles documents.
pub fn title(state: &State) -> String {
    let name = state
        .document
        .path
        .as_deref()
        .and_then(std::path::Path::file_name)
        .map_or_else(
            || "athenaCL".to_owned(),
            |name| name.to_string_lossy().into_owned(),
        );
    if state.document.edited {
        format!("{name} — Edited")
    } else {
        name
    }
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<'_, Message> {
    let colors = state.mode.colors();
    let log = responsive(move |size| {
        scrollable::Scrollable::with_direction(
            view_log(state, colors, size.width - scrollbar::RESERVED_WIDTH),
            Direction::Vertical(scrollbar::vertical()),
        )
        .anchor_bottom()
        .id(LOG)
        .style(colors.scrollbar())
        .width(Length::Fill)
        .height(Length::Fill)
        .into()
    });
    let log = container(log)
        // The shared body now supplies the outer gutters; retain the log's original content width
        // so widening the window does not stretch terminal output.
        .max_width(LOG_MAX_WIDTH - 2.0 * WINDOW_PADDING)
        .height(Length::Fill)
        .width(Length::Fill);
    let log = container(log)
        .center_x(Length::Fill)
        .height(Length::Fill)
        .padding(Padding::ZERO.bottom(12));
    let sidebar: Element<'_, Message> = if state.browser.visible {
        row![
            container(state.browser.view(colors).map(Message::Browser)).id("file-browser"),
            state.browser.divider(colors).map(Message::Browser),
        ]
        .height(Length::Fill)
        .into()
    } else {
        space().width(0).into()
    };
    // Keep the log at the same child index: toggling the browser must retain its scroll, input
    // focus and figure zoom state.
    let body = row![sidebar, log]
        .spacing(if state.browser.visible {
            WINDOW_PADDING
        } else {
            0.0
        })
        .padding([0.0, WINDOW_PADDING])
        .width(Length::Fill)
        .height(Length::Fill);

    let page = column![
        bars::Bar::Header.view(state, colors),
        container(rule(colors.ink, 1.0)).padding([0.0, WINDOW_PADDING]),
        body,
        container(rule(colors.ink, 1.0)).padding([0.0, WINDOW_PADDING]),
        bars::Bar::Footer.view(state, colors),
    ]
    .width(Length::Fill)
    .height(Length::Fill);

    container(page)
        .width(Length::Fill)
        .height(Length::Fill)
        .into()
}

/// The output: each command with what it printed and showed.
fn view_log(state: &State, colors: Colors, width: f32) -> Element<'_, Message> {
    let palette = colors.figure();
    let mut entries: Vec<Column<'_, Message>> = Vec::new();
    for (index, output) in state.output.iter().enumerate() {
        let element = view_output(index, output, state, colors, palette, width);
        match entries.last_mut() {
            Some(entry) if !matches!(output, Output::Command { .. }) => {
                let taken = std::mem::replace(entry, Column::new());
                *entry = taken.push(element);
            }
            _ => entries.push(column![element].spacing(8)),
        }
    }
    entries.push(view_input(state, colors, width));
    Column::with_children(entries.into_iter().map(Element::from))
        .spacing(18)
        .padding([20, 0])
        .width(Length::Fill)
        .into()
}

pub(super) fn view_output<'a>(
    index: usize,
    output: &'a Output,
    state: &'a State,
    colors: Colors,
    palette: Palette,
    width: f32,
) -> Element<'a, Message> {
    // what the log prints can be selected to copy
    let selectable =
        |text| iced_selection::text(text).style(Colors::selectable(colors.ink, colors.rule));
    match output {
        Output::Normal(msg) => selectable(msg).into(),
        Output::Command { prompt, command } => {
            let mut bold = Font::with_name("Fira Mono");
            bold.weight = font::Weight::Bold;
            row![
                view_prompt(prompt, colors),
                selectable(command).font(bold).size(15),
            ]
            .spacing(10)
            .align_y(Vertical::Center)
            .into()
        }
        Output::Error(msg) => row![view_error_tag(colors), selectable(msg)]
            .spacing(10)
            .into(),
        Output::Player(track) => player::view(track, colors, width).map(Message::Player),
        Output::Figure(figure) => {
            container(view_figure(index, figure, state, colors, palette, width))
                .width(width)
                .into()
        }
        Output::Manual(page) => container(
            manual::view(page, width, state.mode)
                .map(move |target| Message::ManualLink(index, target)),
        )
        .id(page_id(index))
        .into(),
        Output::File { path, content } => container(
            column![
                text(path.display().to_string()).size(12).color(colors.dim),
                scrollable::Scrollable::new(selectable(content).wrapping(text::Wrapping::None))
                    .id(format!("file-scroll-{index}"))
                    .direction(Direction::Horizontal(scrollbar::horizontal().spacing(8)))
                    .style(colors.scrollbar())
                    .width(width),
            ]
            .spacing(8),
        )
        .id(page_id(index))
        .into(),
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
    .wrapping(text::Wrapping::None)
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
    width: f32,
) -> Element<'a, Message> {
    let plot =
        figure::view(&output.figure, width, &state.active_texture, palette).map(Message::Figure);
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
    let view_as = |label: &str, view: View| {
        segment(
            label,
            colors,
            output.view == view,
            Message::FigureView(index, view),
        )
    };
    let switch = switch(
        colors,
        [view_as("PLOT", View::Plot), view_as("SCORE", View::Score)],
    );

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
fn view_input(state: &State, colors: Colors, width: f32) -> Column<'_, Message> {
    // a question that offers answers is answered from them alone, so there is nothing to type
    if let Some(query) = &state.question {
        if !query.question.answers().is_empty() {
            let line = row![
                pixel::label("ANSWER", colors.dim),
                view_answers(query, colors)
            ]
            .spacing(10)
            .align_y(Vertical::Center);
            return column![view_query(&query.prompt, colors), line].spacing(8);
        }
    }

    let (label, placeholder) = match &state.question {
        Some(_) => (pixel::label("ANSWER", colors.dim), "type answer"),
        None => (
            view_prompt(&prompt(state), colors),
            "type a command or 'help'",
        ),
    };
    let input = Input::new(placeholder, &state.answer, colors)
        .id(state.input_id.clone())
        .on_submit(Message::Submit);
    let input = if state.question.is_none() {
        input
            .on_edit(|value, cursor| CompletionAction::Edit(value, cursor).into())
            .on_complete(|backwards, value, cursor| {
                CompletionAction::Cycle(backwards, value, cursor).into()
            })
            .on_dismiss(
                state
                    .suggestions
                    .is_open()
                    .then_some(CompletionAction::Dismiss.into()),
            )
    } else {
        input.on_input(Message::InputChanged)
    };
    let line = row![label, input]
        .spacing(10)
        .align_y(Vertical::Center)
        .width(width);

    match &state.question {
        Some(query) => column![view_query(&query.prompt, colors), line].spacing(8),
        None => column![line]
            .extend(state.suggestions.view(colors, width, |index| {
                CompletionAction::Select(index).into()
            }))
            .spacing(10),
    }
}

/// The answers a question offers, as a switch like the look's: the picked one is filled, the
/// arrows move it and return takes it.
fn view_answers<'a>(query: &Query, colors: Colors) -> Element<'a, Message> {
    let answers = query.question.answers();
    let mut switch = row![];
    for (index, &word) in answers.iter().enumerate() {
        if index > 0 {
            switch = switch.push(rule_across(colors.ink));
        }
        let picked = index == query.picked;
        switch = switch.push(
            button(container(pixel::label(word, answer_ink(picked, colors))).center(Length::Fill))
                .height(Length::Fill)
                .padding([0, ANSWER_PADDING])
                .style(colors.segment(picked))
                .on_press(Message::Answer(word.to_owned())),
        );
    }
    framed(colors, switch)
}

/// A pixel label draws in one color, so the chosen answer's has to be the filled one's.
fn answer_ink(chosen: bool, colors: Colors) -> Color {
    if chosen {
        colors.paper
    } else {
        colors.ink
    }
}

/// One of the bottom bar's pickers, wide enough for its longest option.
pub(super) fn picker<'a>(
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
    // as high as every other control in the bars: the text's line fills what the padding leaves
    pick_list(options.to_vec(), selected, on_select)
        .placeholder("none")
        .padding([PICKER_PADDING, 10.0])
        .text_line_height(iced::widget::text::LineHeight::Absolute(
            (FRAME_HEIGHT - 2.0 * PICKER_PADDING).into(),
        ))
        .width((longest * PICKER_CHARACTER + PICKER_ARROW).clamp(PICKER_WIDTH, 160.0))
        .style(colors.picker())
        .menu_style(colors.menu())
}

/// One of the tempo's steppers, stacked half each in the tempo's frame.
pub(super) fn stepper<'a>(colors: Colors, icon: Icon, step: i32) -> Button<'a, Message> {
    icon.button(colors.bare())
        .width(STEPPER_WIDTH)
        .height(Length::Fill)
        .on_press(Message::TempoStep(step))
}

/// Controls sharing one ink frame: the tempo and its steppers, the volume and its mute.
pub(in crate::app) fn framed<'a, M: 'a>(colors: Colors, content: Row<'a, M>) -> Element<'a, M> {
    container(content.align_y(Vertical::Center))
        .height(FRAME_HEIGHT)
        .padding(1)
        .style(colors.frame())
        .into()
}

/// A framed row of segments, a rule between each: a figure's switch between its plot and score,
/// the turns at the end of a page of the manual.
pub(in crate::app) fn switch<'a, M: 'a>(
    colors: Colors,
    segments: impl IntoIterator<Item = Element<'a, M>>,
) -> Element<'a, M> {
    let mut row = Row::new();
    for (index, segment) in segments.into_iter().enumerate() {
        if index > 0 {
            row = row.push(rule_across(colors.ink));
        }
        row = row.push(segment);
    }
    container(row)
        .height(24)
        .padding(1)
        .style(colors.frame())
        .into()
}

/// A segment of a switch, labelled `label` and filled when `chosen`, that sends `message`; without
/// one, it is dimmed and does nothing.
pub(in crate::app) fn segment<'a, M: Clone + 'a>(
    label: &str,
    colors: Colors,
    chosen: bool,
    message: impl Into<Option<M>>,
) -> Element<'a, M> {
    let message = message.into();
    let ink = match (chosen, message.is_some()) {
        (true, _) => colors.paper,
        (false, true) => colors.ink,
        (false, false) => colors.dim,
    };
    button(
        container(pixel::label(label, ink))
            .height(Length::Fill)
            .align_y(Vertical::Center),
    )
    .height(Length::Fill)
    .padding([0, 8])
    .style(colors.segment(chosen))
    .on_press_maybe(message)
    .into()
}

/// A rule across the window, `thickness` high.
pub(super) fn rule<'a>(color: Color, thickness: f32) -> Element<'a, Message> {
    container(space())
        .width(Length::Fill)
        .height(thickness)
        .style(Colors::fill(color))
        .into()
}

/// A 1 pixel rule down its row.
pub(in crate::app) fn rule_across<'a, M: 'a>(color: Color) -> Element<'a, M> {
    container(space())
        .width(1)
        .height(Length::Fill)
        .style(Colors::fill(color))
        .into()
}

/// A path, shortened from the front to `characters`.
pub(in crate::app) fn shorten(path: &str, characters: usize) -> String {
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
    Completion(CompletionAction),
    /// Send what's typed.
    Submit,
    Answer(String),
    /// A link or a turn in the page of the manual at an output index: another of its pages, or a
    /// url to open in a browser.
    ManualLink(usize, manual::Link),
    /// A key no widget took: command recall or the answers' switch.
    Key(keyboard::Key, keyboard::Modifiers),
    /// A key for the file tree, and whether the prompt has since taken the keyboard back.
    TreeKey(keyboard::Key, keyboard::Modifiers, bool),
    /// Text typed while nothing that takes it had focus: it is for the prompt.
    Typed(String),
    /// A history key, with the result of checking the command input's focus.
    RecallHistory {
        direction: SearchDirection,
        focused: bool,
    },
    Browser(BrowserMessage),
    Playback(crate::app::playback::Message),
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
    /// The window has opened: Cmd+Q is pointed at its close button.
    WindowOpened(window::Id),
    /// The window's close button, or Cmd+Q, asks to quit.
    CloseRequested,
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

impl From<CompletionAction> for Message {
    fn from(action: CompletionAction) -> Self {
        Self::Completion(action)
    }
}

/// What a key no widget took is for: text typed is for the prompt, and other keys recall commands
/// or move the answers' switch.
fn key_message(event: keyboard::Event) -> Message {
    match event {
        keyboard::Event::KeyPressed {
            key,
            modifiers,
            text,
            ..
        } => match text {
            Some(text)
                if !modifiers.command()
                    && !modifiers.control()
                    && !text.chars().any(char::is_control) =>
            {
                Message::Typed(text.to_string())
            }
            _ => Message::Key(key, modifiers),
        },
        _ => Message::Key(keyboard::Key::Unidentified, keyboard::Modifiers::empty()),
    }
}

/// Interpreter messages, audio output changes, keyboard input and active playback ticks.
pub fn subscription(state: &State) -> Subscription<Message> {
    let keys = keyboard::listen().map(key_message);
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

    Subscription::batch([
        interpreter_listener,
        position_listener,
        player::subscription(&state.player_state).map(Message::Player),
        state.browser.subscription().map(Message::Browser),
        keys,
        window::open_events().map(Message::WindowOpened),
        window::close_requests().map(|_| Message::CloseRequested),
    ])
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
            history: History::default(),
            suggestions: Suggestions::default(),
            output: Vec::new(),
            question: None,
            player_state: GlobalPlayerState::headless(),
            playback: crate::app::playback::Preferences::default(),
            scratch_dir: String::new(),
            browser: Browser::default(),
            input_id: "input".to_owned(),
            path_lib: vec!["path".to_owned()],
            texture_lib: vec!["texture".to_owned()],
            active_path: "path".to_owned(),
            active_texture: "texture".to_owned(),
            mode: Mode::Light,
            figure_view: View::Plot,
            tempo: "120".to_owned(),
            reveal: None,
            document: interpreter::Document::default(),
        }
    }

    /// Complete only application messages; layout operations are exercised by the GUI tests.
    fn finish_playback(state: &mut State, task: Task<Message>) {
        use iced::futures::{executor::block_on, StreamExt};
        use iced_test::runtime::{task::into_stream, Action};
        let Some(mut stream) = into_stream(task) else {
            return;
        };
        while let Some(action) = block_on(stream.next()) {
            if let Action::Output(message) = action {
                let next = update(state, message);
                finish_playback(state, next);
            }
        }
    }

    #[test]
    fn playback_settings_apply_mute_restore_and_dialog_cancellation() {
        use crate::app::playback::Message as Control;
        let mut state = state();
        for message in [Control::Volume(2.0 / 3.0), Control::Mute, Control::Mute] {
            drop(update(&mut state, Message::Playback(message)));
        }
        assert_eq!(state.playback.settings.volume, 8);
        assert!(!state.playback.settings.muted);
        drop(update(&mut state, Message::Playback(Control::Mute)));
        drop(update(&mut state, Message::Playback(Control::Volume(0.5))));
        assert_eq!(state.playback.settings.volume, 6);
        assert!(
            !state.playback.settings.muted,
            "adjusting the meter unmutes"
        );
        drop(update(&mut state, Message::Playback(Control::Menu(true))));
        assert!(state.playback.menu_open);
        // The native chooser's future remains unpolled in a headless test.
        drop(update(&mut state, Message::Playback(Control::Choose)));
        assert!(!state.playback.menu_open);
        drop(update(&mut state, Message::Playback(Control::Chosen(None))));
        assert!(state.active_soundfont().is_none());
        assert!(state.output.is_empty());
        drop(update(
            &mut state,
            Message::Playback(Control::Saved(Ok(()))),
        ));
        drop(update(
            &mut state,
            Message::Playback(Control::Saved(Err("read-only preferences".into()))),
        ));
        assert!(
            matches!(state.output.as_slice(), [Output::Error(message)] if message.contains("read-only preferences"))
        );
    }

    #[test]
    fn missing_soundfonts_report_once_and_keep_the_previous_sound() {
        use crate::app::playback::Message as Control;
        let directory = tempfile::tempdir().expect("scratch folder");
        let missing = directory.path().join("removed.sf2");
        let mut state = state();
        let task = update(
            &mut state,
            Message::Playback(Control::Chosen(Some(missing))),
        );
        assert!(state.player_state.loading_soundfont());
        finish_playback(&mut state, task);
        assert!(!state.player_state.loading_soundfont());
        assert!(state.active_soundfont().is_none());
        assert!(state.playback.settings.soundfont.is_none());
        assert!(state.playback.settings.recent.is_empty());
        assert!(
            matches!(state.output.as_slice(), [Output::Error(message)] if message.contains("Could not load sound font"))
        );
        let task = update(&mut state, Message::Playback(Control::Select(None)));
        finish_playback(&mut state, task);
        assert_eq!(
            state.output.len(),
            1,
            "selecting the active built-in adds no errors"
        );
    }

    /// A minimal valid MIDI file: one format-0 track holding a note and its end.
    fn midi_file(dir: &std::path::Path) -> std::path::PathBuf {
        let path = dir.join("song.mid");
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

    /// One second of quiet mono PCM audio.
    fn audio_file(dir: &std::path::Path) -> std::path::PathBuf {
        let path = dir.join("render.wav");
        let data_size = 44100u32 * 2;
        let mut wav = b"RIFF".to_vec();
        wav.extend((36 + data_size).to_le_bytes());
        wav.extend(b"WAVEfmt ");
        wav.extend(16u32.to_le_bytes());
        wav.extend(1u16.to_le_bytes()); // PCM
        wav.extend(1u16.to_le_bytes()); // mono
        wav.extend(44100u32.to_le_bytes());
        wav.extend((44100u32 * 2).to_le_bytes());
        wav.extend(2u16.to_le_bytes());
        wav.extend(16u16.to_le_bytes());
        wav.extend(b"data");
        wav.extend(data_size.to_le_bytes());
        for _ in 0..44100 {
            wav.extend(1000i16.to_le_bytes());
        }
        std::fs::write(&path, wav).expect("write test audio");
        path
    }

    #[test]
    fn browser_files_become_snapshots_and_players_in_the_log() {
        use crate::app::browser::Opened;
        let mut state = state();
        let dir = tempfile::tempdir().expect("scratch folder");
        let path = dir.path().join("notes.txt");
        std::fs::write(&path, "original notes").expect("text file");
        drop(update(
            &mut state,
            Message::Browser(BrowserMessage::Opened(
                0,
                path.clone(),
                Ok(Opened::Text("original notes".into())),
            )),
        ));
        std::fs::remove_file(&path).expect("remove source");
        for (name, kind) in [("song.mid", Opened::Midi), ("song.wav", Opened::Audio)] {
            drop(update(
                &mut state,
                Message::Browser(BrowserMessage::Opened(0, dir.path().join(name), Ok(kind))),
            ));
        }
        drop(update(
            &mut state,
            Message::Browser(BrowserMessage::Changed(std::path::PathBuf::new())),
        ));
        assert!(
            matches!(state.output.first(), Some(Output::File { content, .. }) if content == "original notes")
        );
        assert!(
            matches!(state.output.get(2), Some(Output::Player(track)) if track.id == PlayerId::Midi(2))
        );
        assert!(
            matches!(state.output.get(4), Some(Output::Player(track)) if track.id == PlayerId::Audio(4))
        );
        state.question = Some(text_query("name: "));
        drop(update(
            &mut state,
            Message::Browser(BrowserMessage::Opened(0, path, Ok(Opened::Athena))),
        ));
        assert!(
            matches!(state.output.last(), Some(Output::Error(message)) if message.contains("current question"))
        );
    }

    #[test]
    fn keys_are_the_trees_until_the_prompt_takes_them_back() {
        use iced::futures::{executor::block_on, StreamExt};
        use iced_test::runtime::{task::into_stream, Action};
        let dir = tempfile::tempdir().expect("scratch folder");
        for name in ["a.txt", "b.txt"] {
            std::fs::write(dir.path().join(name), "notes").expect("file");
        }
        let mut state = state();
        drop(update_interpreter(
            &mut state,
            interpreter::Message::ScratchDir(dir.path().to_string_lossy().into_owned()),
        ));
        let task = update(&mut state, Message::Browser(BrowserMessage::Toggle));
        for action in block_on(into_stream(task).expect("initial scan").collect::<Vec<_>>()) {
            if let Action::Output(message) = action {
                drop(update(&mut state, message));
            }
        }
        let (a, b) = (dir.path().join("a.txt"), dir.path().join("b.txt"));
        drop(update(
            &mut state,
            Message::Browser(BrowserMessage::Click(
                a.clone(),
                keyboard::Modifiers::empty(),
                false,
            )),
        ));
        assert!(
            state.browser.focused,
            "a click in the tree gives it the keys"
        );

        let down = |prompt| {
            Message::TreeKey(
                keyboard::Key::Named(keyboard::key::Named::ArrowDown),
                keyboard::Modifiers::empty(),
                prompt,
            )
        };
        drop(update(&mut state, down(false)));
        assert!(
            state.browser.selected.contains(&b),
            "the tree takes the key"
        );
        drop(update(&mut state, down(true)));
        assert!(
            state.browser.selected.contains(&b) && !state.browser.focused,
            "once the prompt has the keyboard, keys are its own"
        );

        state.browser.focused = true;
        drop(update(&mut state, Message::Typed("x".to_owned())));
        assert!(!state.browser.focused, "typing is for the prompt");
        assert_eq!(state.answer, "x");
    }

    #[test]
    fn browser_name_edits_do_not_type_into_the_command_or_answer_a_question() {
        let mut state = state();
        state.answer = "draft".into();
        state.question = Some(Query::new(
            "Save? ".into(),
            Question::YesNo { default: true },
        ));
        state.browser.edit = Some(crate::app::browser::Edit::CreateFolder("scratch".into()));
        drop(update(&mut state, Message::Typed("x".into())));
        drop(update(
            &mut state,
            Message::Key(enter(), keyboard::Modifiers::empty()),
        ));
        assert_eq!(state.answer, "draft");
        assert!(state.question.is_some());
        assert!(state.output.is_empty());
        drop(update(
            &mut state,
            Message::Key(
                keyboard::Key::Named(keyboard::key::Named::Escape),
                keyboard::Modifiers::empty(),
            ),
        ));
        assert!(state.browser.edit.is_none());
    }

    #[test]
    fn browser_and_log_render_at_minimum_and_wide_window_sizes() {
        use iced::futures::{executor::block_on, StreamExt};
        use iced_test::runtime::{task::into_stream, Action};
        let dir = tempfile::tempdir().expect("scratch folder");
        std::fs::create_dir(dir.path().join("scores")).expect("folder");
        std::fs::write(dir.path().join("notes.txt"), "notes").expect("file");
        std::fs::write(dir.path().join("render.wav"), b"RIFF").expect("audio");
        let mut state = state();
        drop(update_interpreter(
            &mut state,
            interpreter::Message::ScratchDir(dir.path().to_string_lossy().into_owned()),
        ));
        let task = update(&mut state, Message::Browser(BrowserMessage::Toggle));
        let stream = into_stream(task).expect("initial scan");
        for action in block_on(stream.collect::<Vec<_>>()) {
            if let Action::Output(message) = action {
                drop(update(&mut state, message));
            }
        }
        state.output.push(Output::Normal(
            "The scratch folder's readable files appear here.".into(),
        ));
        for mode in [Mode::Light, Mode::Dark] {
            state.mode = mode;
            for width in [MIN_WINDOW_SIZE.0, 1600.0] {
                let mut simulator = iced_test::Simulator::with_size(
                    settings(),
                    Size::new(width, MIN_WINDOW_SIZE.1),
                    view(&state),
                );
                let file = simulator.find("notes.txt").expect("browser file");
                let browser = simulator
                    .find(iced_test::selector::id("file-browser"))
                    .expect("browser panel")
                    .bounds();
                assert!(
                    (browser.x - WINDOW_PADDING).abs() < 1.0,
                    "browser shares the header and footer gutter"
                );
                let log = simulator
                    .find(iced_test::selector::id(LOG))
                    .expect("log")
                    .bounds();
                assert!(log.width <= LOG_MAX_WIDTH - 2.0 * WINDOW_PADDING);
                assert!(log.x + log.width <= width - WINDOW_PADDING + 1.0);
                let input = simulator
                    .find(iced_test::selector::id("input"))
                    .expect("command input");
                assert!(file.visible_bounds().expect("visible file").x < state.browser.width.get());
                assert!(
                    input.visible_bounds().expect("visible prompt").x >= state.browser.width.get()
                );
                let tempo = simulator
                    .find(iced_test::selector::id("tempo-control"))
                    .expect("tempo control")
                    .visible_bounds()
                    .expect("visible tempo");
                let volume = simulator
                    .find(iced_test::selector::id("master-volume"))
                    .expect("master volume")
                    .visible_bounds()
                    .expect("visible volume");
                assert!(tempo.x + tempo.width < volume.x);
                assert!((volume.x + volume.width - (width - WINDOW_PADDING)).abs() < 1.0);
                let modes = simulator
                    .find(iced_test::selector::id("appearance-control"))
                    .expect("appearance control")
                    .visible_bounds()
                    .expect("visible appearance control");
                assert!((modes.x + modes.width - (width - WINDOW_PADDING)).abs() < 1.0);
                let _ = simulator
                    .click(iced_test::selector::id("toggle-file-browser"))
                    .expect("browser toggle button");
                let _ = simulator
                    .click(iced_test::selector::id("browser-change-folder"))
                    .expect("scratch folder chooser");
                let snapshot = simulator
                    .snapshot(&theme(&state))
                    .expect("browser and log render");
                if let Ok(directory) = std::env::var("ATHENACL_BROWSER_PREVIEW") {
                    crate::app::snapshot::pixels(&snapshot)
                        .save(
                            std::path::Path::new(&directory)
                                .join(format!("browser-{}-{width}.png", mode.name())),
                        )
                        .expect("preview");
                }
                let messages: Vec<_> = simulator.into_messages().collect();
                assert!(messages
                    .iter()
                    .any(|message| matches!(message, Message::Browser(BrowserMessage::Toggle))));
                assert!(messages.iter().any(|message| matches!(
                    message,
                    Message::Browser(BrowserMessage::ChooseRoot)
                )));
            }
        }
    }

    #[test]
    fn only_opened_text_files_scroll_sideways_while_the_rest_of_the_log_wraps() {
        use iced::{mouse, Event};
        use iced_test::{selector, Simulator};

        let mut state = state();
        let line = "wrapping command output 音  ".repeat(6);
        // Fill a wrapped line with the embedded font, regardless of the system's CJK fallback.
        let normal = format!("Output: {line}\n{}", "word ".repeat(30));
        let command = format!("Command: {line}");
        let error = format!("Error: {line}");
        let file = format!("File: {}\nSecond line", line.repeat(3));
        let second_file = format!("Independent file: {}", line.repeat(3));
        let prose = format!("Manual: {line}");
        let code = format!("Code: {line}\nAnother explicit line");
        let question = format!("Question: {line}");
        state.question = Some(text_query(&question));
        state.output = vec![
            Output::Normal(normal.clone()),
            Output::Command {
                prompt: prompt(&state),
                command: command.clone(),
            },
            Output::Error(error.clone()),
            Output::File {
                path: "scratch/notes.txt".into(),
                content: file.clone(),
            },
            Output::File {
                path: "scratch/other.txt".into(),
                content: second_file.clone(),
            },
            Output::Manual(Box::new(ManualPage {
                title: "Manual".into(),
                blocks: vec![
                    manual_source::Block::Paragraph(vec![manual_source::Span::plain(&prose)]),
                    manual_source::Block::Code(code.clone()),
                ],
                nav: manual_source::Nav::default(),
            })),
            Output::Player(PlayerState {
                is_playing: false,
                path: file!().into(),
                id: PlayerId::Audio(6),
                position: 0.0,
            }),
        ];
        for mode in [Mode::Light, Mode::Dark] {
            state.mode = mode;
            for sidebar in [false, true] {
                state.browser.visible = sidebar;
                state.browser.width.set(480.0);
                let mut simulator = Simulator::with_size(
                    settings(),
                    Size::new(MIN_WINDOW_SIZE.0, 1600.0),
                    view(&state),
                );
                // Iced reserves scrollbar space only when the log overflows vertically.
                let selector::Target::Scrollable { content_bounds, .. } =
                    simulator.find(selector::id(LOG)).expect("log")
                else {
                    panic!("scrollable log")
                };
                for text in [&normal, &command, &error, &question, &code] {
                    let bounds = simulator
                        .find(text.as_str())
                        .expect("wrapped log text")
                        .bounds();
                    assert!(
                        bounds.x >= content_bounds.x - 1.0
                            && bounds.x + bounds.width
                                <= content_bounds.x + content_bounds.width + 1.0,
                        "text fits the log: {bounds:?} within {content_bounds:?}"
                    );
                    assert!(bounds.height > 36.0, "long lines wrap: {bounds:?}");
                }
                let manual = simulator
                    .find(selector::id(page_id(5)))
                    .expect("manual page")
                    .bounds();
                assert!(
                    manual.width <= content_bounds.width + 1.0 && manual.height > 80.0,
                    "manual wraps within the log: {manual:?}"
                );
                let preview = simulator.find(file.as_str()).expect("file preview");
                let bounds = preview.bounds();
                assert!(
                    bounds.width > MIN_WINDOW_SIZE.0,
                    "file keeps its natural width"
                );
                assert!(
                    bounds.height > 30.0 && bounds.height < 40.0,
                    "only explicit newlines add height"
                );
                let input = simulator
                    .find(selector::id("input"))
                    .expect("input")
                    .visible_bounds()
                    .expect("visible input");
                assert!(input.width > 100.0 && input.width < content_bounds.width);
                let fixed = [&normal, &second_file, &question];
                let positions: Vec<_> = fixed
                    .iter()
                    .map(|text| {
                        simulator
                            .find(text.as_str())
                            .expect("neighbor")
                            .visible_bounds()
                    })
                    .collect();
                simulator.point_at(preview.visible_bounds().expect("visible file").center());
                let _ = simulator.simulate([Event::Mouse(mouse::Event::WheelScrolled {
                    delta: mouse::ScrollDelta::Pixels { x: -400.0, y: 0.0 },
                })]);
                for (id, offset) in [
                    ("file-scroll-3", 400.0),
                    ("file-scroll-4", 0.0),
                    ("log", 0.0),
                ] {
                    let selector::Target::Scrollable { translation, .. } =
                        simulator.find(selector::id(id)).expect("scrollable")
                    else {
                        panic!("scrollable target")
                    };
                    assert!(
                        (translation.x - offset).abs() < 1.0,
                        "independent offset for {id}: {translation:?}"
                    );
                }
                for (text, position) in fixed.into_iter().zip(positions) {
                    assert_eq!(
                        simulator
                            .find(text.as_str())
                            .expect("fixed neighbor")
                            .visible_bounds(),
                        position
                    );
                }
                assert_eq!(
                    simulator
                        .find(selector::id("input"))
                        .expect("fixed input")
                        .visible_bounds(),
                    Some(input)
                );
                let _ = simulator
                    .snapshot(&theme(&state))
                    .expect("independently scrolled file renders");
            }
        }
    }

    fn text_query(prompt: &str) -> Query {
        Query::new(prompt.to_owned(), Question::Text)
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

    fn completion_catalog(state: &mut State) {
        let commands = ["TIls", "TIn", "TIo"]
            .into_iter()
            .map(|name| interpreter::CommandCompletion {
                name: name.to_owned(),
                description: "TextureInstance".to_owned(),
            })
            .collect();
        drop(update(
            state,
            Message::Interpreter(interpreter::Message::Completions(commands)),
        ));
    }

    #[test]
    fn suggestions_fill_the_input_without_submitting_and_ignore_questions() {
        let mut state = state();
        completion_catalog(&mut state);
        drop(update(
            &mut state,
            CompletionAction::Edit("ti".to_owned(), Some(2)).into(),
        ));
        drop(update(
            &mut state,
            CompletionAction::Cycle(false, "ti".to_owned(), 2).into(),
        ));
        assert_eq!(state.answer, "TIls ");
        assert!(state.output.is_empty());
        assert!(state.history.recent().next().is_none());
        drop(update(
            &mut state,
            CompletionAction::Cycle(false, "TIls ".to_owned(), 5).into(),
        ));
        assert_eq!(state.answer, "TIn ");
        drop(update(&mut state, CompletionAction::Dismiss.into()));
        assert!(!state.suggestions.is_open());
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Ask {
                prompt: "name".to_owned(),
                question: Question::Text,
            }),
        ));
        drop(update(
            &mut state,
            Message::InputChanged("answer".to_owned()),
        ));
        drop(update(
            &mut state,
            CompletionAction::Cycle(false, "ti".to_owned(), 2).into(),
        ));
        drop(update(&mut state, CompletionAction::Select(0).into()));
        drop(update(
            &mut state,
            CompletionAction::Edit("stale".to_owned(), Some(5)).into(),
        ));
        assert_eq!(state.answer, "answer");
        assert!(!state.suggestions.is_open());
    }

    #[test]
    fn batched_pointer_events_still_resize_the_browser_beside_the_log() {
        use iced::{mouse, Event, Point};
        let mut state = state();
        state.browser.visible = true;
        completion_catalog(&mut state);
        drop(update(
            &mut state,
            CompletionAction::Edit("ti".into(), Some(2)).into(),
        ));
        let mut simulator =
            iced_test::Simulator::with_size(settings(), Size::new(1120.0, 760.0), view(&state));
        // The native event loop supplies the final cursor position for this whole batch.
        simulator.point_at(Point::new(600.0, 200.0));
        let _ = simulator.simulate([
            Event::Mouse(mouse::Event::CursorMoved {
                position: Point::new(WINDOW_PADDING + state.browser.width.get() + 3.0, 200.0),
            }),
            Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
            Event::Mouse(mouse::Event::CursorMoved {
                position: Point::new(600.0, 200.0),
            }),
            Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)),
        ]);
        for message in simulator.into_messages() {
            drop(update(&mut state, message));
        }
        assert!((state.browser.width.get() - 480.0).abs() < 1.0);
    }

    #[test]
    fn suggestions_render_in_both_themes_and_can_be_clicked() {
        for mode in [Mode::Light, Mode::Dark] {
            for width in [MIN_WINDOW_SIZE.0, 1600.0] {
                let mut state = state();
                state.mode = mode;
                state.browser.visible = true;
                state.browser.width.set(480.0);
                state
                    .output
                    .push(Output::Normal("Existing log output".into()));
                completion_catalog(&mut state);
                drop(update(
                    &mut state,
                    CompletionAction::Edit("ti".to_owned(), Some(2)).into(),
                ));
                let mut simulator: iced_test::Simulator<'_, Message> =
                    iced_test::Simulator::with_size(
                        settings(),
                        Size::new(width, MIN_WINDOW_SIZE.1),
                        view(&state),
                    );
                let output = simulator.find("Existing log output").expect("log output");
                let bounds = output
                    .visible_bounds()
                    .expect("log remains visible with suggestions");
                assert!(
                    bounds.x.is_finite() && bounds.y.is_finite(),
                    "finite log position: {bounds:?}"
                );
                let _ = simulator
                    .snapshot(&mode.theme())
                    .expect("suggestions render");
                let _ = simulator
                    .click(iced_test::selector::id("input"))
                    .expect("focus");
                let _ = simulator.click("TIo").expect("suggestion");
                let messages: Vec<_> = simulator.into_messages().collect();
                for message in messages {
                    drop(update(&mut state, message));
                }
                assert_eq!(state.answer, "TIo ");
                assert_eq!(state.output.len(), 1);
            }
        }
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

        state.question = Some(text_query("name: "));
        drop(update(&mut state, Message::InputChanged("x".to_owned())));
        drop(update(&mut state, Message::Submit));
        assert!(state.question.is_none());
        assert!(matches!(state.output.last(), Some(Output::Normal(text)) if text == "name: x"));
        assert_eq!(
            state
                .history
                .recall(SearchDirection::Reverse, "")
                .expect("recall")
                .as_deref(),
            Some("tin a 0"),
            "answers are not commands"
        );
    }

    #[test]
    fn history_recall_requires_command_input_focus_and_no_question() {
        let mut state = state();
        state.history.record("help").expect("record");
        state.answer = "draft".to_owned();
        drop(update(
            &mut state,
            Message::RecallHistory {
                direction: SearchDirection::Reverse,
                focused: false,
            },
        ));
        assert_eq!(state.answer, "draft", "another control has focus");

        for question in [Question::Text, Question::YesNo { default: true }] {
            state.question = Some(Query::new("question".to_owned(), question));
            drop(update(
                &mut state,
                Message::RecallHistory {
                    direction: SearchDirection::Reverse,
                    focused: true,
                },
            ));
            assert_eq!(
                state.answer, "draft",
                "questions also reject pending recall tasks"
            );
        }
        state.question = None;
        drop(update(
            &mut state,
            Message::RecallHistory {
                direction: SearchDirection::Reverse,
                focused: true,
            },
        ));
        assert_eq!(state.answer, "help");
    }

    #[test]
    fn history_drafts_and_edits_survive_late_interpreter_output() {
        let mut state = state();
        state.history.record("help").expect("record");
        state.answer = "draft".to_owned();
        drop(update(
            &mut state,
            Message::RecallHistory {
                direction: SearchDirection::Reverse,
                focused: true,
            },
        ));
        drop(update(
            &mut state,
            Message::InputChanged("help tin".to_owned()),
        ));
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Post("done".to_owned())),
        ));
        assert_eq!(state.answer, "help tin");
        drop(update(
            &mut state,
            Message::RecallHistory {
                direction: SearchDirection::Forward,
                focused: true,
            },
        ));
        assert_eq!(state.answer, "draft");
        drop(update(
            &mut state,
            Message::RecallHistory {
                direction: SearchDirection::Reverse,
                focused: true,
            },
        ));
        assert_eq!(
            state.answer, "help",
            "editing the recalled input preserves its stored entry"
        );
    }

    #[test]
    fn the_input_leaves_history_keys_for_the_keyboard_subscription() {
        use iced::{
            event::Status,
            keyboard::{key::Named, Modifiers},
            Event,
        };

        let state = state();
        let mut simulator: iced_test::Simulator<'_, Message> =
            iced_test::Simulator::new(view_input(&state, state.mode.colors(), OUTPUT_WIDTH));
        let _ = simulator
            .click(iced_test::selector::id("input"))
            .expect("focus the command input");
        for key in [Named::ArrowUp, Named::ArrowDown] {
            assert_eq!(simulator.tap_key(key), Status::Ignored);
        }
        for (key, text) in [("p", "\u{10}"), ("n", "\u{e}")] {
            let key = keyboard::Key::Character(key.into());
            let statuses = simulator.simulate([
                Event::Keyboard(keyboard::Event::ModifiersChanged(Modifiers::CTRL)),
                Event::Keyboard(keyboard::Event::KeyPressed {
                    key: key.clone(),
                    modified_key: key,
                    physical_key: keyboard::key::Physical::Unidentified(
                        keyboard::key::NativeCode::Unidentified,
                    ),
                    location: keyboard::Location::Standard,
                    modifiers: Modifiers::CTRL,
                    text: Some(text.into()),
                    repeat: false,
                }),
            ]);
            assert_eq!(statuses.last(), Some(&Status::Ignored));
        }
        assert!(
            simulator.into_messages().all(|message| matches!(
                message, Message::Completion(CompletionAction::Edit(value, _)) if value.is_empty()
            )),
            "history shortcuts insert no text"
        );
    }

    #[test]
    fn a_yes_no_question_starts_on_its_default() {
        for default in [true, false] {
            let query = Query::new("save? ".to_owned(), Question::YesNo { default });
            assert_eq!(query.picked(), Some(if default { "YES" } else { "NO" }));
        }
    }

    #[test]
    fn the_arrows_move_the_pick_and_stop_at_the_ends() {
        let mut query = Query::new("save? ".to_owned(), Question::YesNoCancel { default: true });
        assert_eq!(query.picked(), Some("YES"));

        query.move_pick(1);
        assert_eq!(query.picked(), Some("NO"));
        query.move_pick(1);
        assert_eq!(query.picked(), Some("CANCEL"));
        query.move_pick(1);
        assert_eq!(query.picked(), Some("CANCEL"), "it stops at the last");

        query.move_pick(-1);
        assert_eq!(query.picked(), Some("NO"));
        query.move_pick(-5);
        assert_eq!(query.picked(), Some("YES"), "and at the first");
    }

    #[test]
    fn return_answers_with_the_picked_one() {
        let mut state = state();
        state.question = Some(Query::new(
            "save? ".to_owned(),
            Question::YesNo { default: true },
        ));
        drop(update(
            &mut state,
            Message::Key(arrow_right(), keyboard::Modifiers::empty()),
        ));
        drop(update(
            &mut state,
            Message::Key(enter(), keyboard::Modifiers::empty()),
        ));

        assert!(state.question.is_none());
        assert!(matches!(state.output.last(), Some(Output::Normal(t)) if t == "save? NO"));
    }

    #[test]
    fn keys_do_nothing_without_a_question_that_offers_answers() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Key(enter(), keyboard::Modifiers::empty()),
        ));
        assert!(state.output.is_empty());

        state.question = Some(text_query("name: "));
        drop(update(
            &mut state,
            Message::Key(enter(), keyboard::Modifiers::empty()),
        ));
        assert!(
            state.question.is_some(),
            "a typed answer is not taken by return"
        );
    }

    #[test]
    fn a_link_turns_its_page_where_it_is() {
        let mut state = state();
        state.output = vec![
            Output::Command {
                prompt: Prompt::default(),
                command: "audoc".to_owned(),
            },
            Output::Manual(Box::new(
                manual_source::read(&manual_source::Request::Contents).expect("contents"),
            )),
            Output::Normal("done".to_owned()),
        ];
        let second = manual_source::contents()[1].clone();
        drop(update(
            &mut state,
            Message::ManualLink(1, second.path.clone()),
        ));
        assert_eq!(state.output.len(), 3, "no page is added");
        assert!(matches!(
            state.output.get(1),
            Some(Output::Manual(page)) if page.title == second.title
        ));

        drop(update(
            &mut state,
            Message::ManualLink(1, "chapter99/nothing.md".to_owned()),
        ));
        assert!(
            matches!(state.output.get(1), Some(Output::Manual(page)) if page.title == second.title)
        );
        assert!(matches!(state.output.last(), Some(Output::Error(_))));
    }

    #[test]
    fn a_page_a_command_shows_is_read_from_its_start_once_the_command_is_done() {
        let mut state = state();
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Manual(
                manual_source::Request::Chapter(1),
            )),
        ));
        assert_eq!(state.reveal, Some(0));
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::Post(
                "AUdoc display complete.\n".to_owned(),
            )),
        ));
        assert_eq!(state.reveal, None);
    }

    #[test]
    fn the_log_is_scrolled_from_its_end_to_where_a_page_starts() {
        let find = |top: f32| {
            let start = StartOf {
                log: LOG.into(),
                target: page_id(0).into(),
                log_bounds: Some((
                    Rectangle::new(iced::Point::new(0.0, 50.0), iced::Size::new(600.0, 100.0)),
                    Rectangle::new(iced::Point::new(0.0, 50.0), iced::Size::new(600.0, 500.0)),
                )),
                top: Some(top),
            };
            match widget::Operation::finish(&start) {
                widget::operation::Outcome::Some(offset) => offset.y,
                _ => None,
            }
        };
        // 400 can be scrolled; a page 150 down the log is 250 from where the log ends
        assert_eq!(find(200.0), Some(250.0));
        // a page at the very end cannot be scrolled past it
        assert_eq!(find(500.0), Some(0.0));
    }

    fn pressed(
        key: keyboard::Key,
        modifiers: keyboard::Modifiers,
        text: Option<&str>,
    ) -> keyboard::Event {
        keyboard::Event::KeyPressed {
            key: key.clone(),
            modified_key: key,
            physical_key: keyboard::key::Physical::Unidentified(
                keyboard::key::NativeCode::Unidentified,
            ),
            location: keyboard::Location::Standard,
            modifiers,
            repeat: false,
            text: text.map(Into::into),
        }
    }

    #[test]
    fn text_typed_where_nothing_takes_it_goes_to_the_prompt() {
        let t = keyboard::Key::Character("t".into());
        assert!(matches!(
            key_message(pressed(t.clone(), keyboard::Modifiers::empty(), Some("t"))),
            Message::Typed(typed) if typed == "t"
        ));
        // shortcuts, and keys that type nothing to read, keep their meaning
        for (key, modifiers, text) in [
            (t, keyboard::Modifiers::COMMAND, Some("t")),
            (enter(), keyboard::Modifiers::empty(), Some("\r")),
            (arrow_right(), keyboard::Modifiers::empty(), None),
        ] {
            assert!(matches!(
                key_message(pressed(key, modifiers, text)),
                Message::Key(..)
            ));
        }

        let mut state = state();
        for typed in ["t", "in"] {
            drop(update(&mut state, Message::Typed(typed.to_owned())));
        }
        assert_eq!(state.answer, "tin");

        state.answer.clear();
        state.question = Some(text_query("name: "));
        drop(update(&mut state, Message::Typed("x".to_owned())));
        assert_eq!(state.answer, "x", "an answer is typed as a command is");

        state.question = Some(Query::new(
            "sure? ".to_owned(),
            Question::YesNo { default: true },
        ));
        drop(update(&mut state, Message::Typed("y".to_owned())));
        assert_eq!(state.answer, "x", "the answers' switch takes no typing");
    }

    fn arrow_right() -> keyboard::Key {
        keyboard::Key::Named(keyboard::key::Named::ArrowRight)
    }

    fn enter() -> keyboard::Key {
        keyboard::Key::Named(keyboard::key::Named::Enter)
    }

    #[test]
    fn only_questions_with_set_answers_offer_them() {
        assert!(Question::Text.answers().is_empty());
        assert_eq!(Question::YesNo { default: true }.answers(), ["YES", "NO"]);
        assert_eq!(
            Question::YesNoCancel { default: false }.answers(),
            ["YES", "NO", "CANCEL"]
        );
    }

    #[test]
    fn the_title_names_the_athena_object_s_file_and_marks_unsaved_work() {
        let mut state = state();
        assert_eq!(title(&state), "athenaCL");

        let document = |path: Option<&str>, edited| {
            Message::Interpreter(interpreter::Message::Document(interpreter::Document {
                path: path.map(Into::into),
                edited,
            }))
        };
        drop(update(&mut state, document(None, true)));
        assert_eq!(title(&state), "athenaCL — Edited");
        drop(update(
            &mut state,
            document(Some("/music/canon.xml"), false),
        ));
        assert_eq!(title(&state), "canon.xml");
        drop(update(&mut state, document(Some("/music/canon.xml"), true)));
        assert_eq!(title(&state), "canon.xml — Edited");
    }

    #[test]
    fn quitting_waits_for_the_question_on_screen() {
        let mut state = state();
        state.question = Some(Query::new(
            "destroy the current AthenaObject? ".to_owned(),
            Question::YesNo { default: false },
        ));

        drop(update(&mut state, Message::CloseRequested));

        assert!(
            state.output.is_empty(),
            "nothing is sent until it's answered"
        );
        assert!(state.question.is_some());
    }

    #[test]
    fn a_settled_quit_closes_the_app() {
        use iced::futures::{executor::block_on, StreamExt};
        use iced_test::runtime::{task::into_stream, Action};
        let mut state = state();

        let task = update(&mut state, Message::Interpreter(interpreter::Message::Quit));

        let stream = into_stream(task).expect("an exit");
        let actions = block_on(stream.collect::<Vec<_>>());
        assert!(matches!(actions.as_slice(), [Action::Exit]));
    }

    #[test]
    fn a_command_that_shows_nothing_leaves_no_line() {
        let mut state = state();
        let post = |text: &str| Message::Interpreter(interpreter::Message::Post(text.to_owned()));

        drop(update(&mut state, post("")));
        assert!(state.output.is_empty());
        drop(update(&mut state, post("done")));
        assert!(matches!(state.output.as_slice(), [Output::Normal(text)] if text == "done"));
    }

    #[test]
    fn answers_clear_the_question() {
        let mut state = state();
        state.question = Some(text_query("name: "));
        drop(update(&mut state, Message::Answer("x".to_owned())));

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
        assert_eq!(
            state.answer, "typed",
            "output preserves the next command's draft"
        );

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
            Message::Interpreter(interpreter::Message::Ask {
                prompt: "name".to_owned(),
                question: Question::Text,
            }),
        ));

        assert_eq!(state.question, Some(text_query("name")));
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
    fn playback_commands_start_playing() {
        let dir = tempfile::tempdir().expect("scratch folder");
        let mut state = state();
        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::LoadMidi(
                midi_file(dir.path()).to_string_lossy().into_owned(),
            )),
        ));
        assert!(state.player_state.playing());
        assert!(matches!(state.output.first(), Some(Output::Player(track)) if track.is_playing));

        drop(update(
            &mut state,
            Message::Interpreter(interpreter::Message::LoadAudio(
                audio_file(dir.path()).to_string_lossy().into_owned(),
            )),
        ));
        // one player sounds at a time: the audio command stops the MIDI
        let (Some(Output::Player(midi)), Some(Output::Player(audio))) =
            (state.output.first(), state.output.get(1))
        else {
            panic!("both players stay in the log");
        };
        assert!(!midi.is_playing);
        assert!(audio.is_playing);
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
        state.question = Some(text_query("question"));
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
