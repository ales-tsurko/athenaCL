//! Application's GUI.

use iced::widget::{button, column, row, scrollable, text_input};
use iced::{Alignment, Element, Font, Length};
use indexmap::IndexMap;
use uuid::Uuid;

use crate::interpreter::Interpreter;
use output::OutputViewState;

mod output;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";

/// athenaCL GUI.
pub struct State {
    cmd: String,
    outputs: IndexMap<Uuid, OutputViewState>,
    interpreter: Interpreter,
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
            let output = state.interpreter.run_cmd(&value);
            let output_v = state
                .outputs
                .last_mut()
                .expect("There should always be at least one output view")
                .1;
            output_v.set_output(Some(output));
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
    }
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<Message> {
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
        scrollable(outputs),
    ]
    .padding(20)
    .spacing(10.0)
    .width(Length::Fill)
    .align_x(Alignment::Center)
    .into()
}

/// The iced message type.
#[allow(missing_docs)]
#[derive(Debug, Clone)]
pub enum Message {
    PromptInputChanged(String),
    SendCommand(String),
    SetPinOutput((Uuid, bool)),
}
