//! Connect the scratch browser to the interpreter and immutable log entries.

use std::path::PathBuf;

use iced::Task;

use crate::{
    app::{
        app::{push_output, reveal, Message, Output, State},
        browser::{Effect, Message as BrowserMessage, Opened},
    },
    interpreter,
};

impl State {
    pub(super) fn update_browser(&mut self, message: BrowserMessage) -> Task<Message> {
        let (task, effect) = self.browser.update(message);
        let task = task.map(Message::Browser);
        let follow = match effect {
            Some(Effect::Changing(paths)) => {
                let physical: Vec<_> = paths
                    .iter()
                    .map(|path| path.canonicalize().unwrap_or_else(|_| path.clone()))
                    .collect();
                self.player_state.release_files(&mut self.output, |file| {
                    paths.iter().any(|path| file.starts_with(path))
                        || file
                            .canonicalize()
                            .is_ok_and(|file| physical.iter().any(|path| file.starts_with(path)))
                });
                Task::none()
            }
            Some(Effect::Changed) => {
                self.player_state
                    .release_files(&mut self.output, |file| !file.exists());
                Task::none()
            }
            Some(Effect::Opened(path, result)) => match result {
                Ok(opened) => self.open_browser_file(path, opened),
                Err(error) => push_output(self, Output::Error(error)),
            },
            Some(Effect::ChooseRoot) => {
                crate::app::app::set_scratch_dir();
                Task::none()
            }
            None => Task::none(),
        };
        Task::batch([task, follow])
    }

    fn open_browser_file(&mut self, path: PathBuf, opened: Opened) -> Task<Message> {
        match opened {
            Opened::Text(content) => {
                let index = self.output.len();
                push_output(self, Output::File { path, content }).chain(reveal(index))
            }
            Opened::Athena if self.question.is_some() => push_output(
                self,
                Output::Error("Answer the current question before loading an AthenaObject.".into()),
            ),
            Opened::Athena => {
                let Some(value) = path.to_str() else {
                    return push_output(
                        self,
                        Output::Error("AthenaObject paths must be valid Unicode.".into()),
                    );
                };
                interpreter::INTERPRETER_WORKER
                    .interp_sender
                    .send_blocking(interpreter::Message::LoadAthenaObject(value.into()))
                    .expect("the interpreter channel is unbounded");
                push_output(
                    self,
                    Output::Normal(format!("Loading AthenaObject: {}", path.display())),
                )
            }
            Opened::Midi | Opened::Audio => {
                // Keep the PathBuf intact, including filesystem names that are not Unicode.
                self.output.push(Output::Normal(path.display().to_string()));
                let index = self.output.len();
                let id = if opened == Opened::Midi {
                    crate::app::player::PlayerId::Midi(index)
                } else {
                    crate::app::player::PlayerId::Audio(index)
                };
                push_output(
                    self,
                    Output::Player(crate::app::player::Track {
                        path,
                        id,
                        is_playing: false,
                        position: 0.0,
                    }),
                )
            }
        }
    }
}
