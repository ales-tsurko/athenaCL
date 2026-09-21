//! Playback-only preferences; these never change render or export settings.

use std::{
    fs,
    io::{self, Write},
    path::{Path, PathBuf},
};

use iced::Task;
use serde::{Deserialize, Serialize};

use crate::app::{history::preferences_dir, playback::Message};

pub(crate) const STEPS: u8 = 12;
const RECENT_LIMIT: usize = 8;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct Settings {
    pub(crate) volume: u8,
    pub(crate) muted: bool,
    pub(crate) soundfont: Option<PathBuf>,
    pub(crate) recent: Vec<PathBuf>,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            volume: STEPS,
            muted: false,
            soundfont: None,
            recent: Vec::new(),
        }
    }
}

impl Settings {
    #[expect(
        clippy::cast_sign_loss,
        reason = "the level is clamped to the unsigned slider range"
    )]
    pub(crate) fn set_volume(&mut self, value: f64) {
        self.volume = (value.clamp(0.0, 1.0) * f64::from(STEPS)).round() as u8;
        self.muted = false;
    }

    pub(crate) fn gain(&self) -> f32 {
        if self.muted {
            0.0
        } else {
            f32::from(self.volume) / f32::from(STEPS)
        }
    }

    pub(crate) fn percent(&self) -> u8 {
        ((u16::from(self.volume) * 100 + u16::from(STEPS) / 2) / u16::from(STEPS)) as u8
    }

    pub(crate) fn select(&mut self, path: Option<PathBuf>) {
        if let Some(path) = &path {
            self.recent.retain(|entry| entry != path);
            self.recent.insert(0, path.clone());
            self.recent.truncate(RECENT_LIMIT);
        }
        self.soundfont = path;
    }

    fn read(path: &Path) -> Result<Self, String> {
        let bytes = match fs::read(path) {
            Ok(bytes) => bytes,
            Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(Self::default()),
            Err(error) => return Err(error.to_string()),
        };
        let mut settings: Self =
            serde_json::from_slice(&bytes).map_err(|error| error.to_string())?;
        settings.volume = settings.volume.min(STEPS);
        for path in settings
            .soundfont
            .iter_mut()
            .chain(settings.recent.iter_mut())
        {
            if let Ok(canonical) = path.canonicalize() {
                *path = canonical;
            }
        }
        let mut seen = std::collections::HashSet::new();
        settings.recent.retain(|path| seen.insert(path.clone()));
        settings.recent.truncate(RECENT_LIMIT);
        Ok(settings)
    }

    pub(super) fn write(&self, path: &Path) -> Result<(), String> {
        let write = || -> Result<(), Box<dyn std::error::Error>> {
            let directory = path.parent().ok_or("No preferences directory")?;
            fs::create_dir_all(directory)?;
            let mut file = tempfile::NamedTempFile::new_in(directory)?;
            serde_json::to_writer_pretty(file.as_file_mut(), self)?;
            file.flush()?;
            file.persist(path)?;
            Ok(())
        };
        write().map_err(|error| error.to_string())
    }
}

/// Serialize background saves, coalescing slider changes while a write is in flight.
#[derive(Debug, Default)]
pub(crate) struct Preferences {
    pub(crate) settings: Settings,
    pub(crate) menu_open: bool,
    path: Option<PathBuf>,
    writer: Option<std::thread::JoinHandle<()>>,
    dirty: bool,
}

impl Preferences {
    pub(crate) fn load() -> (Self, Option<String>) {
        let Some(directory) = preferences_dir() else {
            return (
                Self::default(),
                Some("No playback preferences directory".into()),
            );
        };
        Self::at(directory.join(".athenacl-playback.json"))
    }

    pub(super) fn at(path: PathBuf) -> (Self, Option<String>) {
        match Settings::read(&path) {
            Ok(settings) => (
                Self {
                    settings,
                    path: Some(path),
                    menu_open: false,
                    writer: None,
                    dirty: false,
                },
                None,
            ),
            // Preserve unreadable preferences; use defaults in memory until the next launch.
            Err(error) => (
                Self::default(),
                Some(format!("Could not load playback preferences: {error}")),
            ),
        }
    }

    pub(crate) fn save(&mut self) -> Task<Message> {
        self.dirty = true;
        if self.writer.is_some() {
            return Task::none();
        }
        let Some(path) = self.path.clone() else {
            return Task::none();
        };
        self.dirty = false;
        let settings = self.settings.clone();
        let (sender, receiver) = async_channel::bounded(1);
        self.writer = Some(std::thread::spawn(move || {
            drop(sender.send_blocking(Message::Saved(settings.write(&path))));
        }));
        Task::stream(receiver)
    }

    pub(crate) fn saved(&mut self) -> Task<Message> {
        self.writer = None;
        if self.dirty {
            self.save()
        } else {
            Task::none()
        }
    }
}

impl Drop for Preferences {
    fn drop(&mut self) {
        // Finish the small pending write on shutdown. A newer coalesced level must be saved after
        // that writer, even if its completion never reached the closing UI.
        if let Some(writer) = self.writer.take() {
            if writer.join().is_err() {
                eprintln!("The playback preferences writer stopped unexpectedly");
            }
        }
        if self.dirty {
            if let Some(path) = &self.path {
                if let Err(error) = self.settings.write(path) {
                    eprintln!("Could not save playback preferences: {error}");
                }
            }
        }
    }
}
