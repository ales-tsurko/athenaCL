//! Application's GUI.

use iced::widget::{column, text, text_input};
use iced::{Alignment, Element, Font, Length, Sandbox, Settings, Size};

use crate::interpreter::Interpreter;
use output::OutputView;

mod output;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";

/// athenaCL GUI.
pub struct App {
    cmd: String,
    output: OutputView,
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
        Self {
            cmd: String::new(),
            output: OutputView::default().with_width(800.0),
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
                self.output.update(Some(output));
                self.cmd = String::new();
            }
        }
    }

    fn view(&self) -> Element<'_, Message> {
        column![
            text_input(r#"Enter a command or "?" for help"#, &self.cmd)
                .font(Font::MONOSPACE)
                .on_input(|value| Message::PromptInputChanged(value))
                .on_submit(Message::SendCommand(self.cmd.to_owned()))
                .width(800),
            self.output.view()
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
}
