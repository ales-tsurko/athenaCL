//! Command recall over rustyline's bounded, file-backed history.

use std::{env, fmt, io, path::PathBuf};

use iced::keyboard::{key::Named, Key, Modifiers};
use rustyline::{
    error::ReadlineError,
    history::{FileHistory, History as _, SearchDirection},
    Config,
};

/// The latest commands to keep, both in memory and on disk.
const CAPACITY: usize = 1_000;

/// The history backend and the input being browsed. Editing a recalled line only changes the input;
/// moving past the newest entry restores the draft saved on the first move backwards.
pub(super) struct History {
    entries: FileHistory,
    /// Only unsaved commands; a failed write keeps these for the next submission.
    pending: FileHistory,
    config: Config,
    path: Option<PathBuf>,
    position: Option<usize>,
    draft: String,
}

impl History {
    fn with_capacity(capacity: usize) -> Self {
        let config = Config::builder()
            .max_history_size(capacity)
            .expect("the history capacity is valid")
            .history_ignore_dups(true)
            .expect("FileHistory supports ignoring consecutive duplicates")
            .history_ignore_space(false)
            .build();
        Self {
            entries: FileHistory::with_config(&config),
            pending: FileHistory::with_config(&config),
            config,
            path: None,
            position: None,
            draft: String::new(),
        }
    }

    /// Load the history beside athenaCL's preferences, respecting the test directory override.
    pub fn load_default(&mut self) -> rustyline::Result<()> {
        let directory = env::var_os("ATHENACL_PREFS_DIR")
            .map(PathBuf::from)
            .or_else(preferences_dir)
            .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "no preferences directory"))?;
        self.load(directory.join(".athenacl-history"))
    }

    /// Start with an empty history when the file is missing. A failed load leaves this instance in
    /// memory only, so subsequent commands cannot overwrite a file we could not read.
    fn load(&mut self, path: PathBuf) -> rustyline::Result<()> {
        let mut loaded = Self::with_capacity(self.config.max_history_size());
        match loaded.entries.load(&path) {
            Ok(()) => (),
            Err(ReadlineError::Io(error)) if error.kind() == io::ErrorKind::NotFound => (),
            Err(error) => return Err(error),
        }
        loaded.path = Some(path);
        *self = loaded;
        Ok(())
    }

    /// Remember a command as typed, even if execution fails. Append after each submission so
    /// history survives an interrupted session; rustyline merges other sessions' saved entries.
    pub fn record(&mut self, command: &str) -> rustyline::Result<()> {
        self.reset();
        if command.trim().is_empty() {
            return Ok(());
        }
        let added = self.entries.add(command)?;
        if let Some(path) = &self.path {
            if added {
                let _ = self.pending.add(command)?;
            }
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            // A fresh writer avoids rustyline's timestamp-only append shortcut. Windows can
            // report an unchanged mtime after another session writes, so always merge and trim
            // under the file lock. Keep pending commands if any file operation fails.
            self.pending.append(path)?;
            self.pending = FileHistory::with_config(&self.config);
        }
        Ok(())
    }

    /// Move through the entries, returning a replacement for the input only when it changes.
    pub fn recall(
        &mut self,
        direction: SearchDirection,
        input: &str,
    ) -> rustyline::Result<Option<String>> {
        let position = match (direction, self.position) {
            (SearchDirection::Reverse, None) => {
                let Some(last) = self.entries.len().checked_sub(1) else {
                    return Ok(None);
                };
                self.draft = input.to_owned();
                last
            }
            (SearchDirection::Reverse, Some(0)) | (SearchDirection::Forward, None) => {
                return Ok(None);
            }
            (SearchDirection::Reverse, Some(position)) => position - 1,
            (SearchDirection::Forward, Some(position)) => {
                if position + 1 == self.entries.len() {
                    self.position = None;
                    return Ok(Some(std::mem::take(&mut self.draft)));
                }
                position + 1
            }
        };
        let entry = self
            .entries
            .get(position, direction)?
            .map(|result| result.entry.into_owned());
        if entry.is_some() {
            self.position = Some(position);
        }
        Ok(entry)
    }

    /// A new command or question starts outside history navigation.
    pub fn reset(&mut self) {
        self.position = None;
        self.draft.clear();
    }
}

impl Default for History {
    fn default() -> Self {
        Self::with_capacity(CAPACITY)
    }
}

impl fmt::Debug for History {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("History")
            .field("len", &self.entries.len())
            .field("path", &self.path)
            .field("position", &self.position)
            .finish_non_exhaustive()
    }
}

/// Only plain arrows and control-P/N browse history; other modified keys keep their meaning.
pub(super) fn direction(key: &Key, modifiers: Modifiers) -> Option<SearchDirection> {
    match key.as_ref() {
        Key::Named(Named::ArrowUp) if modifiers.is_empty() => Some(SearchDirection::Reverse),
        Key::Named(Named::ArrowDown) if modifiers.is_empty() => Some(SearchDirection::Forward),
        Key::Character("p") if modifiers == Modifiers::CTRL => Some(SearchDirection::Reverse),
        Key::Character("n") if modifiers == Modifiers::CTRL => Some(SearchDirection::Forward),
        _ => None,
    }
}

/// Follow the same platform locations as Python's `drawer.getPrefsDir`.
fn preferences_dir() -> Option<PathBuf> {
    #[cfg(windows)]
    {
        if let Some(directory) = env::var_os("APPDATA") {
            return Some(directory.into());
        }
        if let Some(home) = env::var_os("USERPROFILE") {
            let directory = PathBuf::from(home).join("Application Data");
            if directory.exists() {
                return Some(directory);
            }
        }
    }
    env::home_dir()
}

#[cfg(test)]
mod tests {
    use SearchDirection::{Forward, Reverse};

    use super::*;

    #[test]
    fn browsing_preserves_the_draft_and_stored_commands() {
        let mut history = History::default();
        assert_eq!(history.recall(Reverse, "draft").expect("recall"), None);
        assert_eq!(history.recall(Forward, "draft").expect("recall"), None);
        for command in ["pin a 0", "tin a 1"] {
            history.record(command).expect("record");
        }

        assert_eq!(
            history.recall(Reverse, "draft").expect("recall").as_deref(),
            Some("tin a 1")
        );
        assert_eq!(
            history
                .recall(Reverse, "edited")
                .expect("recall")
                .as_deref(),
            Some("pin a 0")
        );
        assert_eq!(history.recall(Reverse, "pin a 0").expect("recall"), None);
        assert_eq!(
            history
                .recall(Forward, "pin a 0")
                .expect("recall")
                .as_deref(),
            Some("tin a 1")
        );
        assert_eq!(
            history
                .recall(Forward, "tin a 1")
                .expect("recall")
                .as_deref(),
            Some("draft")
        );
        assert_eq!(history.recall(Forward, "draft").expect("recall"), None);
    }

    #[test]
    fn submissions_reset_navigation_and_filter_only_blanks_and_consecutive_duplicates() {
        let mut history = History::default();
        for command in [
            "help",
            "help",
            " \t ",
            "unknown command",
            "help",
            "  pin 音 0",
        ] {
            history.record(command).expect("record");
        }
        assert_eq!(
            history
                .entries
                .iter()
                .map(String::as_str)
                .collect::<Vec<_>>(),
            ["help", "unknown command", "help", "  pin 音 0"]
        );
        let _ = history.recall(Reverse, "old draft").expect("recall");
        history.record("edited command").expect("record");
        assert_eq!(history.recall(Forward, "new draft").expect("recall"), None);
        assert_eq!(
            history
                .recall(Reverse, "new draft")
                .expect("recall")
                .as_deref(),
            Some("edited command")
        );
        assert_eq!(
            history
                .recall(Forward, "edited command")
                .expect("recall")
                .as_deref(),
            Some("new draft")
        );
    }

    #[test]
    fn history_keeps_only_the_latest_commands() {
        let mut history = History::default();
        for number in 0..CAPACITY + 2 {
            history
                .record(&format!("command {number}"))
                .expect("record");
        }
        assert_eq!(history.entries.len(), CAPACITY);
        assert_eq!(
            history.entries.iter().next().map(String::as_str),
            Some("command 2")
        );
    }

    #[test]
    fn persistent_history_merges_sessions_and_trims_the_file() {
        for unchanged_timestamp in [false, true] {
            let directory = tempfile::tempdir().expect("scratch history directory");
            let path = directory.path().join("nested/history");
            let mut first = History::with_capacity(3);
            first
                .load(path.clone())
                .expect("a missing file starts empty");
            first.record("help").expect("create history");
            let mut second = History::with_capacity(3);
            second.load(path.clone()).expect("load another session");

            first.record("pin 音 0").expect("append first session");
            let modified = std::fs::metadata(&path)
                .expect("history metadata")
                .modified()
                .expect("history timestamp");
            second
                .record(r"apdir x C:\Music\scores")
                .expect("merge second session");
            if unchanged_timestamp {
                // Reproduce a filesystem reporting the same timestamp for another session's write.
                // The first session must still discover that the file has reached its entry limit.
                std::fs::OpenOptions::new()
                    .write(true)
                    .open(&path)
                    .expect("open history")
                    .set_modified(modified)
                    .expect("restore history timestamp");
            }
            first
                .record("tin a 0")
                .expect("merge and trim first session");
            let mut reopened = History::default();
            reopened.load(path).expect("reopen history");
            assert_eq!(
                reopened
                    .entries
                    .iter()
                    .map(String::as_str)
                    .collect::<Vec<_>>(),
                ["pin 音 0", r"apdir x C:\Music\scores", "tin a 0"],
                "unchanged timestamp: {unchanged_timestamp}",
            );
        }
    }

    #[test]
    fn failed_writes_retry_all_pending_commands_including_on_a_duplicate_submission() {
        let directory = tempfile::tempdir().expect("scratch history directory");
        let path = directory.path().join("history");
        let mut history = History::default();
        history.load(path.clone()).expect("missing file");
        std::fs::create_dir(&path).expect("block history writes");
        assert!(history.record("help").is_err());
        assert!(history.record("pin 音 0").is_err());
        std::fs::remove_dir(&path).expect("unblock history writes");
        history.record("pin 音 0").expect("retry pending entries");
        history.record("tin a 0").expect("append once after retry");

        let mut reopened = History::default();
        reopened.load(path).expect("reopen history");
        assert_eq!(
            reopened
                .entries
                .iter()
                .map(String::as_str)
                .collect::<Vec<_>>(),
            ["help", "pin 音 0", "tin a 0"],
        );
    }

    #[test]
    fn failed_file_operations_leave_in_memory_recall_usable() {
        let directory = tempfile::tempdir().expect("scratch history directory");
        let path = directory.path().join("history");
        let mut history = History::default();
        history.load(path.clone()).expect("missing file");
        std::fs::create_dir(&path).expect("block the history file with a directory");
        assert!(history.record("help").is_err());
        assert_eq!(
            history
                .recall(Reverse, "")
                .expect("in-memory recall")
                .as_deref(),
            Some("help")
        );

        let unreadable = directory.path().join("invalid-utf8");
        std::fs::write(&unreadable, [0xff]).expect("invalid history file");
        let mut history = History::default();
        assert!(history.load(unreadable.clone()).is_err());
        history
            .record("help")
            .expect("in-memory history after a failed load");
        assert_eq!(std::fs::read(unreadable).expect("original file"), [0xff]);
    }

    #[test]
    fn modified_arrows_and_other_control_keys_do_not_browse() {
        assert_eq!(
            direction(&Key::Named(Named::ArrowUp), Modifiers::empty()),
            Some(Reverse)
        );
        assert_eq!(
            direction(&Key::Named(Named::ArrowDown), Modifiers::empty()),
            Some(Forward)
        );
        assert_eq!(
            direction(&Key::Character("p".into()), Modifiers::CTRL),
            Some(Reverse)
        );
        assert_eq!(
            direction(&Key::Character("n".into()), Modifiers::CTRL),
            Some(Forward)
        );
        for modifiers in [
            Modifiers::SHIFT,
            Modifiers::ALT,
            Modifiers::LOGO,
            Modifiers::CTRL,
        ] {
            assert_eq!(direction(&Key::Named(Named::ArrowUp), modifiers), None);
        }
        assert_eq!(
            direction(&Key::Character("p".into()), Modifiers::empty()),
            None
        );
        assert_eq!(
            direction(
                &Key::Character("p".into()),
                Modifiers::CTRL | Modifiers::SHIFT
            ),
            None
        );
        assert_eq!(
            direction(&Key::Character("c".into()), Modifiers::CTRL),
            None
        );
    }
}
