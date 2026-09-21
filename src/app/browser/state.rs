//! Cached browser state. Only explicit actions and filesystem notifications start work.

use std::{
    collections::BTreeSet,
    path::{Path, PathBuf},
    thread,
};

use iced::{
    keyboard::{self, key::Named, Modifiers},
    widget::operation,
    Task,
};

use crate::app::browser::{
    filesystem::{Kind, Listing, Opened, Operation},
    resize::Width,
    selection::Selection,
};

pub(crate) const NAME_INPUT: &str = "browser-name";
pub(crate) const TREE: &str = "browser-tree";

#[derive(Debug, Default)]
pub(crate) struct Browser {
    pub(crate) visible: bool,
    pub(crate) width: Width,
    pub(crate) root: PathBuf,
    pub(crate) expanded: BTreeSet<PathBuf>,
    pub(crate) listing: Listing,
    pub(crate) selected: Selection,
    pub(crate) clipboard: Vec<PathBuf>,
    pub(crate) edit: Option<Edit>,
    pub(crate) name: String,
    pub(crate) status: Option<String>,
    pub(crate) busy: bool,
    pub(crate) scanning: bool,
    /// Whether keys are the tree's: since a click in it, until one elsewhere or typing.
    pub(crate) focused: bool,
    select_after_scan: Option<Vec<PathBuf>>,
    dirty: bool,
    generation: u64,
    pub(crate) watch_epoch: u64,
}

impl Browser {
    pub(crate) fn set_root(&mut self, root: PathBuf) -> Task<Message> {
        if self.root == root {
            return Task::none();
        }
        self.root = root;
        self.generation += 1;
        self.expanded.clear();
        self.listing = Listing::default();
        self.selected = Selection::default();
        self.clipboard.clear();
        self.edit = None;
        self.status = None;
        self.scanning = false;
        self.busy = false;
        self.select_after_scan = None;
        self.refresh()
    }

    pub(crate) fn update(&mut self, message: Message) -> (Task<Message>, Option<Effect>) {
        match message {
            Message::Toggle => return (self.toggle(), None),
            Message::Resize(width) => self.width.set(width),
            Message::Scroll(y) => {
                return (
                    operation::scroll_by(
                        TREE,
                        iced::widget::scrollable::AbsoluteOffset { x: 0.0, y },
                    ),
                    None,
                );
            }
            Message::Click(path, modifiers, double) => {
                self.focused = true;
                return (self.click(path, modifiers, double), None);
            }
            Message::Context(path) => {
                self.focused = true;
                self.selected.context(path);
            }
            Message::Key(key, modifiers) => return self.key(&key, modifiers),
            Message::Blur => self.focused = false,
            Message::Expand(path) => {
                if !self.expanded.remove(&path) {
                    self.expanded.insert(path);
                }
                return (self.refresh(), None);
            }
            Message::RevealFolder(path) => {
                if self.expanded.insert(path) {
                    return (self.refresh(), None);
                }
            }
            Message::Move(paths, directory) => return self.move_files(paths, directory),
            Message::Open(path) => return (self.open(path), None),
            Message::Refresh => {
                self.watch_epoch += 1;
                self.status = None;
                return (self.refresh(), Some(Effect::Changed));
            }
            Message::Changed(root) if root == self.root => {
                return (self.refresh(), Some(Effect::Changed));
            }
            Message::Copy(path) => self.clipboard = self.selected.targets(&path),
            Message::Paste(directory) => return self.paste(directory),
            Message::Edit(edit) if !self.busy => {
                return (self.begin_edit(edit), None);
            }
            Message::Name(name) => self.name = name,
            Message::Cancel => self.edit = None,
            Message::Confirm if !self.busy => return self.confirm(),
            Message::ChooseRoot if !self.busy => return (Task::none(), Some(Effect::ChooseRoot)),
            Message::Scanned(generation, result) => {
                return (self.scanned(generation, result), None)
            }
            Message::WatchFailed(root, error) if root == self.root => {
                self.status = Some(format!(
                    "Automatic refresh unavailable: {error}. Use Refresh."
                ));
            }
            Message::Finished(generation, result) => {
                return (self.finished(generation, result), Some(Effect::Changed));
            }
            Message::Opened(generation, path, result) if generation == self.generation => {
                return (Task::none(), Some(Effect::Opened(path, result)));
            }
            _ => (),
        }
        (Task::none(), None)
    }

    fn toggle(&mut self) -> Task<Message> {
        self.visible = !self.visible;
        if self.visible {
            self.refresh()
        } else {
            self.edit = None;
            self.focused = false;
            Task::none()
        }
    }

    /// What a key does to the tree while it has the keyboard: the arrows move through it, and the
    /// context menu's actions have the keys it shows beside them.
    fn key(
        &mut self,
        key: &keyboard::Key,
        modifiers: Modifiers,
    ) -> (Task<Message>, Option<Effect>) {
        let entries = &self.listing.entries;
        let lead = self.selected.lead().map(Path::to_path_buf);
        let folder = |path: &Path| {
            entries
                .iter()
                .any(|entry| entry.path == path && entry.kind == Kind::Folder)
        };
        let message = match (key.as_ref(), lead) {
            (keyboard::Key::Named(Named::ArrowUp | Named::ArrowDown), _) => {
                let step = if key == &keyboard::Key::Named(Named::ArrowUp) {
                    -1
                } else {
                    1
                };
                self.selected.step(step, modifiers.shift(), entries);
                return (Task::none(), None);
            }
            (keyboard::Key::Character(c), _)
                if modifiers.command() && c.eq_ignore_ascii_case("a") =>
            {
                self.selected.all(entries);
                return (Task::none(), None);
            }
            (keyboard::Key::Named(Named::Escape), _) => {
                self.selected.clear();
                self.focused = false;
                return (Task::none(), None);
            }
            // a folder opens and closes; out of a closed one, the left arrow goes to its parent
            (keyboard::Key::Named(Named::ArrowRight), Some(lead))
                if folder(&lead) && !self.expanded.contains(&lead) =>
            {
                Message::Expand(lead)
            }
            (keyboard::Key::Named(Named::ArrowLeft), Some(lead)) => {
                if folder(&lead) && self.expanded.contains(&lead) {
                    Message::Expand(lead)
                } else {
                    if let Some(parent) = lead.parent().filter(|parent| folder(parent)) {
                        self.selected.only(parent.to_path_buf());
                    }
                    return (Task::none(), None);
                }
            }
            (keyboard::Key::Named(Named::Enter), Some(lead)) => Message::Open(lead),
            (keyboard::Key::Character(c), Some(lead))
                if modifiers.command() && c.eq_ignore_ascii_case("o") =>
            {
                Message::Open(lead)
            }
            (keyboard::Key::Named(Named::F2), Some(lead)) if self.selected.len() <= 1 => {
                Message::Edit(Edit::Rename(lead))
            }
            (keyboard::Key::Named(Named::Delete | Named::Backspace), Some(lead)) => {
                Message::Edit(Edit::Delete(self.selected.targets(&lead)))
            }
            (keyboard::Key::Character(c), Some(lead))
                if modifiers.command() && c.eq_ignore_ascii_case("c") =>
            {
                Message::Copy(lead)
            }
            (keyboard::Key::Character(c), lead)
                if modifiers.command() && c.eq_ignore_ascii_case("v") =>
            {
                Message::Paste(self.directory_for(lead.as_deref()))
            }
            (keyboard::Key::Character(c), lead)
                if modifiers.command() && modifiers.shift() && c.eq_ignore_ascii_case("n") =>
            {
                Message::Edit(Edit::CreateFolder(self.directory_for(lead.as_deref())))
            }
            _ => return (Task::none(), None),
        };
        self.update(message)
    }

    /// Where something pasted or made beside `path` goes: into it, if it is a folder, or else
    /// beside it; with nothing selected, into the root.
    pub(crate) fn directory_for(&self, path: Option<&Path>) -> PathBuf {
        let Some(path) = path else {
            return self.root.clone();
        };
        let folder = path == self.root
            || self
                .listing
                .entries
                .iter()
                .any(|entry| entry.path == path && entry.kind == Kind::Folder);
        if folder {
            path.to_path_buf()
        } else {
            path.parent().unwrap_or(&self.root).to_path_buf()
        }
    }

    fn click(&mut self, path: PathBuf, modifiers: Modifiers, double: bool) -> Task<Message> {
        if double {
            if modifiers.is_empty() {
                return self.open(path);
            }
        } else {
            self.selected.click(path, modifiers, &self.listing.entries);
        }
        Task::none()
    }

    fn move_files(
        &mut self,
        paths: Vec<PathBuf>,
        directory: PathBuf,
    ) -> (Task<Message>, Option<Effect>) {
        if self.busy || self.edit.is_some() {
            return (Task::none(), None);
        }
        let paths: Vec<_> = paths
            .into_iter()
            .filter(|path| path.parent() != Some(directory.as_path()))
            .collect();
        if paths.is_empty() {
            return (Task::none(), None);
        }
        self.select_after_scan = Some(
            paths
                .iter()
                .filter_map(|path| path.file_name().map(|name| directory.join(name)))
                .collect(),
        );
        if directory != self.root {
            self.expanded.insert(directory.clone());
        }
        self.run(
            paths
                .into_iter()
                .map(|source| Operation::Move {
                    source,
                    directory: directory.clone(),
                })
                .collect(),
        )
    }

    fn paste(&mut self, directory: PathBuf) -> (Task<Message>, Option<Effect>) {
        if self.busy || self.clipboard.is_empty() {
            return (Task::none(), None);
        }
        self.run(
            self.clipboard
                .iter()
                .map(|source| Operation::Copy {
                    source: source.clone(),
                    directory: directory.clone(),
                })
                .collect(),
        )
    }

    fn scanned(&mut self, generation: u64, result: Result<Listing, String>) -> Task<Message> {
        if generation != self.generation {
            return Task::none();
        }
        self.scanning = false;
        match result {
            Ok(listing) => {
                if !self.busy && !self.dirty {
                    if let Some(paths) = self.select_after_scan.take() {
                        self.selected.replace(paths);
                    }
                }
                self.selected.retain(&listing.entries);
                self.listing = listing;
            }
            Err(error) => {
                self.listing = Listing::default();
                self.listing.errors.push(error);
            }
        }
        if self.dirty {
            self.refresh()
        } else {
            Task::none()
        }
    }

    fn finished(&mut self, generation: u64, result: Result<(), String>) -> Task<Message> {
        if generation != self.generation {
            return Task::none();
        }
        self.busy = false;
        self.status = result.err();
        if self.status.is_some() {
            self.select_after_scan = None;
        }
        if self.status.is_none() {
            self.edit = None;
        }
        self.refresh()
    }

    fn refresh(&mut self) -> Task<Message> {
        self.dirty = true;
        if self.scanning || !self.visible || self.root.as_os_str().is_empty() {
            return Task::none();
        }
        self.dirty = false;
        self.scanning = true;
        let (root, expanded, generation) =
            (self.root.clone(), self.expanded.clone(), self.generation);
        background(
            move || Listing::read(&root, &expanded).map_err(|error| error.to_string()),
            move |result| Message::Scanned(generation, result),
        )
    }

    fn open(&mut self, path: PathBuf) -> Task<Message> {
        if self.busy {
            return Task::none();
        }
        self.selected.only(path.clone());
        if self
            .listing
            .entries
            .iter()
            .any(|entry| entry.path == path && entry.kind == Kind::Folder)
        {
            return self.update(Message::Expand(path)).0;
        }
        let (root, generation, shown_path) = (self.root.clone(), self.generation, path.clone());
        background(
            move || Opened::read(&root, &path).map_err(|error| error.to_string()),
            move |result| Message::Opened(generation, shown_path.clone(), result),
        )
    }

    fn confirm(&mut self) -> (Task<Message>, Option<Effect>) {
        let Some(edit) = &self.edit else {
            return (Task::none(), None);
        };
        let operations = match edit {
            Edit::Rename(path) => vec![Operation::Rename {
                path: path.clone(),
                name: self.name.clone(),
            }],
            Edit::Delete(paths) => paths.iter().cloned().map(Operation::Delete).collect(),
            Edit::CreateFolder(directory) => vec![Operation::CreateFolder {
                directory: directory.clone(),
                name: self.name.clone(),
            }],
        };
        self.run(operations)
    }

    fn begin_edit(&mut self, edit: Edit) -> Task<Message> {
        self.name = match &edit {
            Edit::Rename(path) => path
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .into_owned(),
            _ => String::new(),
        };
        let needs_name = !matches!(edit, Edit::Delete(_));
        self.edit = Some(edit);
        self.status = None;
        if needs_name {
            operation::focus(NAME_INPUT).chain(operation::select_all(NAME_INPUT))
        } else {
            Task::none()
        }
    }

    fn run(&mut self, operations: Vec<Operation>) -> (Task<Message>, Option<Effect>) {
        self.busy = true;
        self.status = None;
        let changing: Vec<_> = operations
            .iter()
            .filter_map(Operation::changing)
            .map(PathBuf::from)
            .collect();
        let effect = (!changing.is_empty()).then_some(Effect::Changing(changing));
        let (root, generation) = (self.root.clone(), self.generation);
        // The future starts after the app handles Changing and releases the affected players.
        let task = background(
            move || Operation::run_all(&operations, &root),
            move |result| Message::Finished(generation, result),
        );
        (task, effect)
    }
}

#[derive(Debug, Clone)]
/// An inline file action awaiting a name or deletion confirmation.
pub enum Edit {
    Rename(PathBuf),
    Delete(Vec<PathBuf>),
    CreateFolder(PathBuf),
}

#[derive(Debug)]
pub(crate) enum Effect {
    Opened(PathBuf, Result<Opened, String>),
    Changing(Vec<PathBuf>),
    Changed,
    ChooseRoot,
}

/// Actions from the scratch browser and results of its background work.
#[derive(Debug, Clone)]
pub enum Message {
    Toggle,
    Resize(f32),
    Scroll(f32),
    Click(PathBuf, Modifiers, bool),
    Context(PathBuf),
    /// A key pressed while the tree has the keyboard.
    Key(keyboard::Key, Modifiers),
    /// A click somewhere else: keys are no longer the tree's.
    Blur,
    Expand(PathBuf),
    RevealFolder(PathBuf),
    Move(Vec<PathBuf>, PathBuf),
    Open(PathBuf),
    Refresh,
    Changed(PathBuf),
    WatchFailed(PathBuf, String),
    Scanned(u64, Result<Listing, String>),
    Copy(PathBuf),
    Paste(PathBuf),
    Edit(Edit),
    Name(String),
    Cancel,
    Confirm,
    Finished(u64, Result<(), String>),
    Opened(u64, PathBuf, Result<Opened, String>),
    ChooseRoot,
}

/// Blocking filesystem work never runs on the UI or the async executor's worker threads.
fn background<T: Send + 'static>(
    work: impl FnOnce() -> Result<T, String> + Send + 'static,
    result: impl Fn(Result<T, String>) -> Message + Send + 'static,
) -> Task<Message> {
    Task::perform(
        async move {
            let (sender, receiver) = async_channel::bounded(1);
            thread::Builder::new()
                .name("scratch-files".into())
                .spawn(move || {
                    if let Err(error) = sender.send_blocking(work()) {
                        eprintln!("File browser closed: {error}");
                    }
                })
                .map_err(|error| error.to_string())?;
            receiver.recv().await.map_err(|error| error.to_string())?
        },
        result,
    )
}
