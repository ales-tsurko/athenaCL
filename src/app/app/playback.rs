//! Connect playback preferences to the shared output and native sound font chooser.

use std::path::Path;

use iced::Task;

use crate::app::{
    app::{push_output, Message, Output, State, SOUND_FONT},
    playback::Message as PlaybackMessage,
    player,
};

impl State {
    pub(super) fn update_playback(&mut self, message: PlaybackMessage) -> Task<Message> {
        match message {
            PlaybackMessage::Volume(value) => {
                self.playback.settings.set_volume(value);
            }
            PlaybackMessage::Mute => self.playback.settings.muted = !self.playback.settings.muted,
            PlaybackMessage::Menu(open) => {
                self.playback.menu_open = open;
                return Task::none();
            }
            PlaybackMessage::Choose => {
                self.playback.menu_open = false;
                return Task::perform(
                    async {
                        rfd::AsyncFileDialog::new()
                            .set_title("Choose a sound font")
                            .add_filter("Sound font", &["sf2"])
                            .pick_file()
                            .await
                            .map(|file| file.path().to_owned())
                    },
                    |path| Message::Playback(PlaybackMessage::Chosen(path)),
                );
            }
            PlaybackMessage::Chosen(None) => return Task::none(),
            PlaybackMessage::Chosen(Some(path)) => return self.select_soundfont(Some(&path)),
            PlaybackMessage::Select(path) => return self.select_soundfont(path.as_deref()),
            PlaybackMessage::Saved(result) => {
                let task = self.playback.saved().map(Message::Playback);
                return match result {
                    Ok(()) => task,
                    Err(error) => Task::batch([
                        task,
                        push_output(
                            self,
                            Output::Error(format!("Could not save playback preferences: {error}")),
                        ),
                    ]),
                };
            }
        }
        self.player_state.set_volume(self.playback.settings.gain());
        self.playback.save().map(Message::Playback)
    }

    pub(super) fn select_soundfont(&mut self, path: Option<&Path>) -> Task<Message> {
        self.playback.menu_open = false;
        let builtin = self.player_state.builtin_soundfont();
        let path = path
            .map(|path| path.canonicalize().unwrap_or_else(|_| path.to_owned()))
            .filter(|path| {
                *path
                    != builtin
                        .canonicalize()
                        .unwrap_or_else(|_| builtin.to_owned())
            })
            .unwrap_or_else(|| builtin.to_owned());
        self.update_player(player::Message::SelectSoundFont(path))
    }

    pub(super) fn update_player(&mut self, message: player::Message) -> Task<Message> {
        let task =
            player::update(&mut self.output, &mut self.player_state, message).map(Message::Player);
        let save = if !self.player_state.loading_soundfont() {
            let active = self.active_soundfont().map(Path::to_owned);
            if self.playback.settings.soundfont != active {
                self.playback.settings.select(active);
                self.playback.save().map(Message::Playback)
            } else {
                Task::none()
            }
        } else {
            Task::none()
        };
        Task::batch([task, save])
    }

    pub(super) fn active_soundfont(&self) -> Option<&Path> {
        let path = self.player_state.soundfont();
        (path != self.player_state.builtin_soundfont()).then_some(path)
    }
}

pub(super) fn builtin_soundfont() -> std::path::PathBuf {
    std::env::current_exe()
        .expect("the application has an executable path")
        .parent()
        .expect("the executable has a directory")
        .join(SOUND_FONT)
}
