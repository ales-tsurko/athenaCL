//! Application's GUI.

use chrono::{DateTime, Local};
use iced::widget::{
    button, column, container, container::Style as ContainerStyle, row, scrollable, text,
    text_input,
};
use iced::{Alignment, Element, Font, Length};
use indexmap::IndexMap;
use uuid::{timestamp, Uuid};

use crate::interpreter::Interpreter;
use output::OutputViewState;

mod output;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";

/// athenaCL GUI.
pub struct State {
    cmd: String,
    outputs: IndexMap<Uuid, OutputViewState>,
    errors: IndexMap<Uuid, ErrorState>,
    interpreter: Interpreter,
}

/// The state used for the errors, which shown in the output container.
#[allow(missing_docs)]
#[derive(Clone, Debug, Default)]
pub struct ErrorState {
    pub id: Uuid,
    pub message: String,
    pub timestamp: DateTime<Local>,
}

impl Default for State {
    fn default() -> Self {
        let interpreter = Interpreter::new().expect("error initializing interpreter");
        let init_output = OutputViewState::default().with_width(800.0);
        let outputs = [(init_output.id(), init_output)].into();
        Self {
            cmd: String::new(),
            outputs,
            interpreter,
            errors: IndexMap::new(),
        }
    }
}

/// The iced update function.
pub fn update(state: &mut State, message: Message) {
    match message {
        Message::PromptInputChanged(value) => {
            state.cmd = value;
        }
        Message::SendCommand(value) => {
            let output = match state.interpreter.run_cmd(&value) {
                Ok(output) => output,
                Err(err) => return update(state, Message::PushError(err.to_string())),
            };
            let output_v = state
                .outputs
                .last_mut()
                .expect("There should always be at least one output view")
                .1;
            output_v.set_output(output);
            output_v.set_cmd(&value);
            state.cmd = String::new();
        }
        Message::SetPinOutput((id, value)) => {
            if let Some(output) = state.outputs.get_mut(&id) {
                output.set_pinned(value);
                let output_v = OutputViewState::default().with_width(800.0);
                state.outputs.insert(output_v.id(), output_v);
            }
            if !value && state.outputs.len() != 1 {
                state.outputs.shift_remove(&id);
            }
        }
        Message::PushError(message) => {
            let id = Uuid::new_v4();
            state.errors.insert(
                id,
                ErrorState {
                    id,
                    message,
                    timestamp: Local::now(),
                },
            );
        }
        Message::CloseError(id) => {
            state.errors.swap_remove(&id);
        }
    }
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<Message> {
    let errors = column(
        state
            .errors
            .iter()
            .map(|(_, state)| view_error(state))
            .collect::<Vec<_>>(),
    );
    let outputs = column(
        state
            .outputs
            .iter()
            .map(|(_, o)| output::view(o))
            .collect::<Vec<_>>(),
    );
    column![
        row![
            text_input(r#"Enter a command or "?" for help"#, &state.cmd)
                .font(Font::MONOSPACE)
                .on_input(|value| Message::PromptInputChanged(value))
                .on_submit(Message::SendCommand(state.cmd.to_owned())),
            button("cmd").on_press(Message::SendCommand("cmd".to_string())),
            button("help").on_press(Message::SendCommand("help".to_string())),
        ]
        .spacing(10.0)
        .width(800.0),
        scrollable(column![errors, outputs].width(800.0)),
    ]
    .padding(20)
    .spacing(10.0)
    .width(Length::Fill)
    .align_x(Alignment::Center)
    .into()
}

fn view_error<'a>(state: &'a ErrorState) -> iced::Element<'a, Message> {
    let mut msg_font = Font::MONOSPACE;
    msg_font.weight = iced::font::Weight::Bold;
    let timestamp = state.timestamp.format("%T    %a, %e %b %Y").to_string();

    container(row![
        column![
            text(&state.message).font(msg_font),
            text(timestamp).size(11.0)
        ]
        .spacing(10.0)
        .width(iced::Length::Fill),
        button("close")
            .style(iced::widget::button::text)
            .on_press(Message::CloseError(state.id))
    ])
    .style(|theme: &iced::Theme| ContainerStyle {
        background: Some(iced::Background::Color(theme.palette().danger)),
        ..Default::default()
    })
    .width(iced::Length::Fill)
    .padding(20.0)
    .into()
}

/// The iced message type.
#[allow(missing_docs)]
#[derive(Debug, Clone)]
pub enum Message {
    PromptInputChanged(String),
    SendCommand(String),
    SetPinOutput((Uuid, bool)),
    PushError(String),
    CloseError(Uuid),
}
