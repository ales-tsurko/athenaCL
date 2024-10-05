//! Application's GUI.

use iced::futures::sink::SinkExt;
use iced::stream;
use iced::widget::{
    button, column, container, container::Style as ContainerStyle, opaque, row, scrollable, stack,
    text, text::Style as TextStyle, text_input, vertical_space,
};
use iced::{Alignment, Element, Font, Subscription};

use crate::interpreter;

/// System application ID.
pub const APPLICATION_ID: &str = "by.alestsurko.athenacl";

/// athenaCL GUI.
pub struct State {
    // interpreter: Interpreter,
}

impl Default for State {
    fn default() -> Self {
        // let interpreter = Interpreter::new().expect("error initializing interpreter");
        // Self { interpreter }
        Self {}
    }
}

/// The iced update function.
pub fn update(state: &mut State, message: Message) {
    match message {
        // Message::SendCommand(value) => {
            // let output = match state.interpreter.run_cmd(&value) {
            //     Ok(output) => output,
            //     Err(err) => return update(state, Message::PushError(err.to_string())),
            // };
            // let output_v = state
            //     .outputs
            //     .last_mut()
            //     .expect("There should always be at least one output view")
            //     .1;
            // output_v.set_output(output);
            // output_v.set_cmd(&value);
            // state.cmd = String::new();
        // }
        _ => todo!(),
    }
}

/// The top-level iced view function.
pub fn view(state: &State) -> Element<Message> {
    container(text("hello")).into()
}

/// The iced message type.
#[allow(missing_docs)]
#[derive(Debug, Clone)]
pub enum Message {
    InterpreterMessage(interpreter::Message),
}

#[allow(missing_docs)]
pub fn subscription(_: &State) -> Subscription<Message> {
    // this worker runs async loop to make the worker, which runs on a System's thread communicate
    // with our app, whithout blocking the event loop of iced...
    Subscription::run(|| {
        let receiver = interpreter::INTERPRETER_WORKER.receiver.clone();

        stream::channel(1000, |mut output| async move {
            loop {
                if let Ok(msg) = receiver.recv().await {
                    let _ = output.send(msg).await;
                }
            }
        })
    })
    .map(Message::InterpreterMessage)
}
