//! Application's GUI.

use iced::widget::{column, scrollable, text_input};
use iced::{Alignment, Element, Font, Length, Sandbox, Settings, Size};
use indexmap::IndexMap;
use uuid::Uuid;

use crate::interpreter::Interpreter;
use output::OutputView;

mod output;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";

/// athenaCL GUI.
pub struct App {
    cmd: String,
    outputs: IndexMap<Uuid, OutputView>,
    interpreter: Interpreter,
}

impl App {
    /// Get iced application settings.
    pub fn settings<Flags: Default>() -> Settings<Flags> {
        Settings {
            id: Some(APPLICATION_ID.into()),
            window: iced::window::Settings {
                min_size: Some(Size::new(800.0, 600.0)),
                position: iced::window::Position::Centered,
                ..Default::default()
            },
            antialiasing: true,
            ..Default::default()
        }
    }
}

impl Sandbox for App {
    type Message = Message;

    fn new() -> Self {
        let interpreter = Interpreter::new().expect("error initializing interpreter");
        let init_output = OutputView::new().with_width(800.0);
        let outputs = [(init_output.id(), init_output)].into();
        Self {
            cmd: String::new(),
            outputs,
            interpreter,
        }
    }

    fn title(&self) -> String {
        String::from("athenaCL")
    }

    fn update(&mut self, message: Message) {
        match message {
            Message::PromptInputChanged(value) => {
                self.cmd = value;
            }
            Message::SendCommand(value) => {
                let output = self.interpreter.run_cmd(&value);
                let output_v = self
                    .outputs
                    .last_mut()
                    .expect("There should always be at least one output view")
                    .1;
                output_v.set_output(Some(output));
                output_v.set_cmd(&self.cmd);
                self.cmd = String::new();
            }
            Message::SetPinOutput((id, value)) => {
                if let Some(output) = self.outputs.get_mut(&id) {
                    output.set_pinned(value);
                    let output_v = OutputView::new().with_width(800.0);
                    self.outputs.insert(output_v.id(), output_v);
                }
                if !value && self.outputs.len() != 1 {
                    self.outputs.shift_remove(&id);
                }
            }
        }
    }

    fn view(&self) -> Element<'_, Message> {
        let outputs = column(
            self.outputs
                .iter()
                .map(|(_, o)| o.view())
                .collect::<Vec<_>>(),
        );
        column![
            text_input(r#"Enter a command or "?" for help"#, &self.cmd)
                .font(Font::MONOSPACE)
                .on_input(|value| Message::PromptInputChanged(value))
                .on_submit(Message::SendCommand(self.cmd.to_owned()))
                .width(800),
            scrollable(outputs),
        ]
        .padding(20)
        .align_items(Alignment::Center)
        .width(Length::Fill)
        .align_items(Alignment::Center)
        .into()
    }
}

#[derive(Debug, Clone)]
pub enum Message {
    PromptInputChanged(String),
    SendCommand(String),
    SetPinOutput((Uuid, bool)),
}
