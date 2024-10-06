//! Application's GUI.

use std::collections::VecDeque;

use iced::futures::sink::SinkExt;
use iced::widget::{
    button, column, container, container::Style as ContainerStyle, opaque, row, scrollable, stack,
    text, text::Style as TextStyle, text_input, vertical_space,
};
use iced::{padding, stream};
use iced::{Alignment, Element, Font, Subscription};

use crate::interpreter::{self, InterpreterResult};

const TERM_WIDTH: u16 = 80;
const FONT_WIDTH: u16 = 10;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";

/// athenaCL GUI.
#[derive(Debug, Default)]
pub struct State {
    answer: String,
    output: VecDeque<Output>,
    question: Option<String>,
}

#[derive(Debug)]
enum Output {
    Normal(String),
    Command(String),
    Error(String),
}

/// The iced update function.
pub fn update(state: &mut State, message: Message) {
    match message {
        Message::InputChanged(val) => {
            state.answer = val;
        }
        Message::InterpreterMessage(msg) => match msg {
            interpreter::Message::SendCmd(_) => {
                // state
                //     .output
                //     .push_front(Output::Command(state.input.clone()));
                state.answer = "".to_owned();
                interpreter::INTERPRETER_WORKER
                    .interp_sender
                    .send_blocking(msg)
                    .expect("cannot send message to the interpreter");
            }
            interpreter::Message::Post(output) => {
                state.answer = "".to_owned();
                state.output.push_front(Output::Normal(output));
            }
            interpreter::Message::Error(output) | interpreter::Message::PythonError(output) => {
                state.answer = "".to_owned();
                state.output.push_front(Output::Error(output));
            }
            interpreter::Message::Ask(prompt) => {
                state.answer = "".to_owned();
                state.question = Some(prompt);
            }
            _ => (),
        },
        Message::Answer(question, value) => {
            state.question = None;
            state
                .output
                .push_front(Output::Normal(format!("{question}{value}")));
            interpreter::INTERPRETER_WORKER
                .response_sender
                .send_blocking(value)
                .expect("cannot send message to response receiver");
        }
    }
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<Message> {
    let output = column(
        state
            .output
            .iter()
            .to_owned()
            .map(view_output)
            .map(Into::into)
            .collect::<Vec<_>>(),
    );

    container(column![view_prompt(state), scrollable(output).width(iced::Length::Fill)])
        .padding(40)
        .width(TERM_WIDTH * FONT_WIDTH)
        .into()
}

fn view_output<'a>(output: &'a Output) -> Element<'a, Message> {
    let text = match output {
        Output::Normal(msg) => text(msg),
        Output::Command(msg) => {
            let mut font = Font::MONOSPACE;
            font.weight = iced::font::Weight::Bold;
            text(msg).font(font).size(16.0)
        }
        Output::Error(msg) => text(msg)
            .style(|theme: &iced::Theme| TextStyle {
                color: Some(theme.palette().danger),
            })
    };

    container(text).padding([40, 0]).into()
}

fn view_prompt<'a>(state: &'a State) -> Element<'a, Message> {
    match &state.question {
        Some(question) => text_input(&question, &state.answer)
            .on_input(Message::InputChanged)
            .on_submit(Message::Answer(question.to_owned(), state.answer.clone()))
            .into(),
        None => text_input("type command or 'help'", &state.answer)
            .on_input(Message::InputChanged)
            .on_submit(interpreter::Message::SendCmd(state.answer.clone()).into())
            .into(),
    }
}

/// The iced message type.
#[allow(missing_docs)]
#[derive(Debug, Clone)]
pub enum Message {
    InputChanged(String),
    InterpreterMessage(interpreter::Message),
    Answer(String, String),
}

impl From<interpreter::Message> for Message {
    fn from(value: interpreter::Message) -> Self {
        Self::InterpreterMessage(value)
    }
}

#[allow(missing_docs)]
pub fn subscription(_: &State) -> Subscription<Message> {
    // this worker runs async loop to make the worker, which runs on a System's thread communicate
    // with our app, whithout blocking the event loop of iced...
    Subscription::run(|| {
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
    .map(Message::InterpreterMessage)
}
