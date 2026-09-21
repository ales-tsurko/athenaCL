//! File recognition and operations. Paths are kept as paths, never interpreted as commands.

use std::{
    collections::BTreeSet,
    fs::{self, File, OpenOptions},
    io::{self, Read},
    path::{Component, Path, PathBuf},
};

use quick_xml::{events::Event, Reader};
use thiserror::Error;

const SAMPLE_SIZE: u64 = 8192;
const TEXT_LIMIT: u64 = 1024 * 1024;

/// A snapshot of the expanded portion of the scratch tree.
#[derive(Debug, Clone, Default)]
pub struct Listing {
    pub(crate) entries: Vec<Entry>,
    pub(crate) errors: Vec<String>,
}

impl Listing {
    pub(crate) fn read(root: &Path, expanded: &BTreeSet<PathBuf>) -> Result<Self, Error> {
        let mut listing = Self::default();
        listing.directory(root, expanded, 0)?;
        Ok(listing)
    }

    fn directory(
        &mut self,
        path: &Path,
        expanded: &BTreeSet<PathBuf>,
        depth: usize,
    ) -> Result<(), Error> {
        let mut entries = Vec::new();
        for item in fs::read_dir(path).at(path)? {
            let item = item.at(path)?;
            let path = item.path();
            if let Ok(kind) = Kind::read(&path) {
                entries.push(Entry { path, kind, depth });
            }
        }
        entries.sort_by_cached_key(|entry| {
            (
                entry.kind != Kind::Folder,
                entry.name().to_lowercase(),
                entry.path.clone(),
            )
        });
        for entry in entries {
            let descend = entry.kind == Kind::Folder && expanded.contains(&entry.path);
            let path = entry.path.clone();
            self.entries.push(entry);
            if descend {
                if let Err(error) = self.directory(&path, expanded, depth + 1) {
                    self.errors.push(error.to_string());
                }
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub(crate) struct Entry {
    pub(crate) path: PathBuf,
    pub(crate) kind: Kind,
    pub(crate) depth: usize,
}

impl Entry {
    pub(crate) fn name(&self) -> String {
        self.path
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .into_owned()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Kind {
    Folder,
    Athena,
    Audio,
    Midi,
    SoundFont,
    Text,
}

impl Kind {
    fn read(path: &Path) -> Result<Self, Error> {
        let metadata = fs::symlink_metadata(path).at(path)?;
        if metadata.is_dir() {
            return Ok(Self::Folder);
        }
        // Do not follow links: they can leave the scratch tree or create directory cycles.
        if !metadata.is_file() {
            return Err(Error::Unsupported(path.to_owned()));
        }
        let mut sample = Vec::new();
        File::open(path)
            .at(path)?
            .take(SAMPLE_SIZE)
            .read_to_end(&mut sample)
            .at(path)?;
        if sample.starts_with(b"MThd") {
            return Ok(Self::Midi);
        }
        let extension = path
            .extension()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_ascii_lowercase();
        if extension == "sf2" {
            return Ok(Self::SoundFont);
        }
        // Formats enabled by rodio's Symphonia features. Decoding errors are reported by the
        // player.
        if matches!(
            extension.as_str(),
            "wav"
                | "wave"
                | "aif"
                | "aiff"
                | "aifc"
                | "flac"
                | "mp3"
                | "mp2"
                | "mp1"
                | "ogg"
                | "oga"
                | "aac"
                | "m4a"
                | "mp4"
                | "caf"
                | "mkv"
                | "webm"
        ) {
            return Ok(Self::Audio);
        }
        let content = decode_text(&sample, metadata.len() > SAMPLE_SIZE)
            .ok_or_else(|| Error::Unsupported(path.to_owned()))?;
        let mut reader = Reader::from_str(&content);
        loop {
            match reader.read_event() {
                Ok(Event::Start(tag) | Event::Empty(tag)) => {
                    return Ok(if tag.name().as_ref() == "athenaObject" {
                        Self::Athena
                    } else {
                        Self::Text
                    });
                }
                Ok(Event::Decl(_) | Event::Comment(_) | Event::PI(_) | Event::DocType(_)) => (),
                Ok(Event::Text(text)) if text.as_ref().chars().all(char::is_whitespace) => (),
                _ => return Ok(Self::Text),
            }
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
/// A readable file, or an immutable snapshot of its text.
pub enum Opened {
    Athena,
    Audio,
    Midi,
    SoundFont,
    Text(String),
}

impl Opened {
    pub(crate) fn read(root: &Path, path: &Path) -> Result<Self, Error> {
        within(root, path)?;
        match Kind::read(path)? {
            Kind::Athena => Ok(Self::Athena),
            Kind::Audio => Ok(Self::Audio),
            Kind::Midi => Ok(Self::Midi),
            Kind::SoundFont => Ok(Self::SoundFont),
            Kind::Text => Self::read_text(path),
            Kind::Folder => Err(Error::Invalid("Open a file, or expand the folder.".into())),
        }
    }

    fn read_text(path: &Path) -> Result<Self, Error> {
        let mut bytes = Vec::new();
        File::open(path)
            .at(path)?
            .take(TEXT_LIMIT + 1)
            .read_to_end(&mut bytes)
            .at(path)?;
        let truncated = bytes.len() as u64 > TEXT_LIMIT;
        if truncated {
            bytes.pop();
        }
        let mut content =
            decode_text(&bytes, truncated).ok_or_else(|| Error::Unsupported(path.to_owned()))?;
        if truncated {
            content.push_str("\n\n[Text truncated after 1 MiB]");
        }
        Ok(Self::Text(content))
    }
}

#[derive(Debug, Clone)]
pub(crate) enum Operation {
    Copy { source: PathBuf, directory: PathBuf },
    Move { source: PathBuf, directory: PathBuf },
    Rename { path: PathBuf, name: String },
    Delete(PathBuf),
    CreateFolder { directory: PathBuf, name: String },
}

impl Operation {
    /// Try every selected item. A partial failure is reported without concealing completed work.
    pub(crate) fn run_all(operations: &[Self], root: &Path) -> Result<(), String> {
        let errors: Vec<_> = operations
            .iter()
            .filter_map(|operation| {
                // A confirmed deletion may be retried after another selected item failed, or after
                // an external process has already removed it.
                if let Self::Delete(path) = operation {
                    if path.try_exists().is_ok_and(|exists| !exists) {
                        return None;
                    }
                }
                operation.run(root).err().map(|error| error.to_string())
            })
            .collect();
        if errors.is_empty() {
            Ok(())
        } else {
            let message = errors.join("\n");
            Err(if operations.len() > 1 {
                format!(
                    "Some items could not be changed; other items may have completed.\n{message}"
                )
            } else {
                message
            })
        }
    }

    pub(crate) fn changing(&self) -> Option<&Path> {
        match self {
            Self::Move { source, .. } => Some(source),
            Self::Rename { path, .. } | Self::Delete(path) => Some(path),
            _ => None,
        }
    }

    pub(crate) fn run(&self, root: &Path) -> Result<(), Error> {
        match self {
            Self::Move { source, directory } => {
                not_root(root, source)?;
                let source_real = within(root, source)?;
                let directory_real = within(root, directory)?;
                if directory_real.starts_with(&source_real) {
                    return Err(Error::Invalid(
                        "A folder cannot be moved into itself.".into(),
                    ));
                }
                if source_real.parent() == Some(directory_real.as_path()) {
                    return Ok(());
                }
                let name = source
                    .file_name()
                    .ok_or_else(|| Error::Invalid("The file has no name.".into()))?;
                let destination = directory.join(name);
                vacant(&destination)?;
                fs::rename(source, &destination).at(source)
            }
            Self::Copy { source, directory } => {
                let source_real = within(root, source)?;
                let directory_real = within(root, directory)?;
                if directory_real.starts_with(&source_real) {
                    return Err(Error::Invalid(
                        "A folder cannot be copied into itself.".into(),
                    ));
                }
                let destination = copy_destination(source, directory)?;
                copy_tree(source, &destination)
            }
            Self::Rename { path, name } => {
                not_root(root, path)?;
                let parent = path
                    .parent()
                    .ok_or_else(|| Error::Invalid("No parent folder.".into()))?;
                let destination = named_child(root, parent, name)?;
                if destination == *path {
                    return Ok(());
                }
                vacant(&destination)?;
                fs::rename(path, &destination).at(path)
            }
            Self::Delete(path) => {
                not_root(root, path)?;
                if path.is_dir() {
                    fs::remove_dir_all(path).at(path)
                } else {
                    fs::remove_file(path).at(path)
                }
            }
            Self::CreateFolder { directory, name } => {
                let destination = named_child(root, directory, name)?;
                fs::create_dir(&destination).at(&destination)
            }
        }
    }
}

/// Verify both the existing path and its resolved location. Links are not browser entries.
fn within(root: &Path, path: &Path) -> Result<PathBuf, Error> {
    let chosen_root = path == root;
    let root = root.canonicalize().at(root)?;
    let resolved = path.canonicalize().at(path)?;
    if !resolved.starts_with(root)
        || (!chosen_root
            && fs::symlink_metadata(path)
                .at(path)?
                .file_type()
                .is_symlink())
    {
        return Err(Error::Invalid(
            "This path is outside the scratch folder or is a symbolic link.".into(),
        ));
    }
    Ok(resolved)
}

fn not_root(root: &Path, path: &Path) -> Result<(), Error> {
    if within(root, path)? == root.canonicalize().at(root)? {
        return Err(Error::Invalid(
            "The scratch folder itself cannot be renamed or deleted here.".into(),
        ));
    }
    Ok(())
}

fn named_child(root: &Path, directory: &Path, name: &str) -> Result<PathBuf, Error> {
    within(root, directory)?;
    let mut components = Path::new(name).components();
    if name.is_empty()
        || name.contains(['/', '\\', '\0'])
        || !matches!(components.next(), Some(Component::Normal(_)))
        || components.next().is_some()
    {
        return Err(Error::Invalid("Enter a single file or folder name.".into()));
    }
    Ok(directory.join(name))
}

fn vacant(path: &Path) -> Result<(), Error> {
    match fs::symlink_metadata(path) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(source) => Err(Error::Io {
            path: path.into(),
            source,
        }),
        Ok(_) => Err(Error::Invalid(format!(
            "{} already exists.",
            path.display()
        ))),
    }
}

fn copy_destination(source: &Path, directory: &Path) -> Result<PathBuf, Error> {
    let name = source
        .file_name()
        .ok_or_else(|| Error::Invalid("The file has no name.".into()))?;
    let destination = directory.join(name);
    if vacant(&destination).is_ok() {
        return Ok(destination);
    }
    for number in 1..10_000 {
        let mut name = if source.is_dir() {
            source.file_name()
        } else {
            source.file_stem()
        }
        .unwrap_or_default()
        .to_os_string();
        name.push(if number == 1 {
            " copy".to_owned()
        } else {
            format!(" copy {number}")
        });
        if source.is_file() {
            if let Some(extension) = source.extension() {
                name.push(".");
                name.push(extension);
            }
        }
        let destination = directory.join(name);
        if vacant(&destination).is_ok() {
            return Ok(destination);
        }
    }
    Err(Error::Invalid("No unused copy name is available.".into()))
}

fn copy_tree(source: &Path, destination: &Path) -> Result<(), Error> {
    let metadata = fs::symlink_metadata(source).at(source)?;
    if metadata.is_dir() {
        fs::create_dir(destination).at(destination)?;
        let result = copy_children(source, destination);
        if result.is_err() {
            // Only the new directory created above is removed on failure.
            if let Err(error) = fs::remove_dir_all(destination) {
                eprintln!("Cannot remove incomplete copy: {error}");
            }
        }
        result
    } else if metadata.is_file() {
        let mut input = File::open(source).at(source)?;
        let mut output = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(destination)
            .at(destination)?;
        let result = io::copy(&mut input, &mut output)
            .at(destination)
            .map(|_| ());
        drop(output);
        if result.is_err() {
            if let Err(error) = fs::remove_file(destination) {
                eprintln!("Cannot remove incomplete copy: {error}");
            }
        }
        result
    } else {
        Err(Error::Invalid(format!(
            "Cannot copy symbolic links or special files: {}",
            source.display()
        )))
    }
}

fn copy_children(source: &Path, destination: &Path) -> Result<(), Error> {
    for entry in fs::read_dir(source).at(source)? {
        let entry = entry.at(source)?;
        copy_tree(&entry.path(), &destination.join(entry.file_name()))?;
    }
    Ok(())
}

/// UTF-8 and BOM-marked UTF-16, rejecting binary control bytes. A prefix may end mid-character.
fn decode_text(bytes: &[u8], partial: bool) -> Option<String> {
    let text = if bytes.starts_with(&[0xff, 0xfe]) || bytes.starts_with(&[0xfe, 0xff]) {
        let little = bytes.first() == Some(&0xff);
        let body = bytes.get(2..)?;
        if !partial && body.len() % 2 != 0 {
            return None;
        }
        let mut units: Vec<_> = body
            .as_chunks::<2>()
            .0
            .iter()
            .map(|pair| {
                if little {
                    u16::from_le_bytes(*pair)
                } else {
                    u16::from_be_bytes(*pair)
                }
            })
            .collect();
        if partial
            && units
                .last()
                .is_some_and(|unit| (0xd800..=0xdbff).contains(unit))
        {
            units.pop();
        }
        String::from_utf16(&units).ok()?
    } else {
        let bytes = bytes.strip_prefix(b"\xef\xbb\xbf").unwrap_or(bytes);
        match std::str::from_utf8(bytes) {
            Ok(text) => text.to_owned(),
            Err(error) if partial && error.error_len().is_none() => {
                std::str::from_utf8(bytes.get(..error.valid_up_to())?)
                    .ok()?
                    .to_owned()
            }
            Err(_) => return None,
        }
    };
    (!text
        .chars()
        .any(|c| c.is_control() && !matches!(c, '\n' | '\r' | '\t' | '\u{c}')))
    .then_some(text)
}

trait At<T> {
    fn at(self, path: &Path) -> Result<T, Error>;
}

impl<T> At<T> for io::Result<T> {
    fn at(self, path: &Path) -> Result<T, Error> {
        self.map_err(|source| Error::Io {
            path: path.to_owned(),
            source,
        })
    }
}

#[derive(Debug, Error)]
pub(crate) enum Error {
    #[error("{}: {source}", path.display())]
    Io { path: PathBuf, source: io::Error },
    #[error("{0}")]
    Invalid(String),
    #[error("Cannot read {} as an AthenaObject, audio, MIDI or text file.", .0.display())]
    Unsupported(PathBuf),
}
