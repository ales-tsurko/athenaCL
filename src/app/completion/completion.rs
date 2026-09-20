//! Match only on edits or catalog changes, and keep a stable set while Tab cycles it.

use std::{collections::HashSet, ops::Range};

use iced::widget::text_input;

use crate::{app::history::History, interpreter::CommandCompletion};

/// Suggestions and their current cycle; no interpreter calls or searches during drawing.
#[derive(Debug, Default)]
pub(crate) struct Suggestions {
    commands: Vec<CommandCompletion>,
    input: String,
    cursor: Option<usize>,
    pub(super) candidates: Vec<Candidate>,
    pub(super) selected: Option<usize>,
    dismissed: bool,
}

impl Suggestions {
    pub(crate) fn set_commands(
        &mut self,
        mut commands: Vec<CommandCompletion>,
        sources: Sources<'_>,
    ) {
        commands.sort_by_cached_key(|command| command.name.to_ascii_lowercase());
        self.commands = commands;
        self.refresh(sources);
    }

    /// Cursor positions are UTF-8 byte offsets. None means a selection or IME preedit.
    pub(crate) fn edit(&mut self, input: &str, cursor: Option<usize>, sources: Sources<'_>) {
        if self.input == input && self.cursor == cursor {
            return;
        }
        input.clone_into(&mut self.input);
        self.cursor = cursor;
        self.dismissed = false;
        self.rebuild(sources, false);
    }

    /// Refresh names when another command creates, renames or removes a path or texture.
    pub(crate) fn refresh(&mut self, sources: Sources<'_>) {
        if !self.dismissed {
            self.rebuild(sources, false);
        }
    }

    pub(crate) fn is_open(&self) -> bool {
        !self.candidates.is_empty()
    }

    pub(crate) fn dismiss(&mut self) {
        self.dismissed = true;
        self.reset_matches();
    }

    fn reset_matches(&mut self) {
        self.candidates.clear();
        self.selected = None;
    }

    pub(crate) fn clear(&mut self) {
        self.reset_matches();
        self.dismissed = false;
        self.input.clear();
        self.cursor = None;
    }

    /// First Tab takes the first match, Shift+Tab the last; subsequent presses wrap around.
    /// Explicit Tab also offers commands on an empty line.
    pub(crate) fn cycle(
        &mut self,
        backwards: bool,
        sources: Sources<'_>,
    ) -> Option<(String, usize)> {
        if self.candidates.is_empty() {
            self.dismissed = false;
            self.rebuild(sources, true);
        }
        let count = self.candidates.len();
        if count == 0 {
            return None;
        }
        let index = match (self.selected, backwards) {
            (None, false) => 0,
            (None | Some(0), true) => count - 1,
            (Some(index), true) => index - 1,
            (Some(index), false) => (index + 1) % count,
        };
        self.accept(index)
    }

    /// Return the full line and Iced's grapheme cursor index, preserving text after the token.
    pub(crate) fn accept(&mut self, index: usize) -> Option<(String, usize)> {
        let candidate = self.candidates.get(index)?;
        self.input.clone_from(&candidate.value);
        self.cursor = Some(candidate.cursor);
        let caret = text_input::Value::new(self.input.get(..candidate.cursor)?).len();
        self.selected = Some(index);
        let result = (self.input.clone(), caret);
        // A unique completion is finished. The next Tab can complete its next argument.
        if self.candidates.len() == 1 {
            self.reset_matches();
        }
        Some(result)
    }

    fn rebuild(&mut self, sources: Sources<'_>, explicit: bool) {
        self.reset_matches();
        let Some(context) = self
            .cursor
            .and_then(|cursor| Context::new(&self.input, cursor))
        else {
            return;
        };
        if !explicit && self.input.trim().is_empty() {
            return;
        }
        if context.before.is_empty()
            || matches!(context.before.as_slice(), [name] if name.eq_ignore_ascii_case("help") || *name == "?")
        {
            for command in &self.commands {
                if command
                    .name
                    .to_ascii_lowercase()
                    .starts_with(&context.prefix.to_ascii_lowercase())
                {
                    self.candidates
                        .push(context.replace(&command.name, &command.description));
                }
            }
        } else if let Some((names, description)) = context.names(&sources) {
            let mut names: Vec<_> = names.iter().collect();
            names.sort();
            for name in names {
                if name
                    .to_lowercase()
                    .starts_with(&context.prefix.to_lowercase())
                {
                    self.candidates.push(context.replace(name, description));
                }
            }
        }
        if self.cursor == Some(self.input.len()) && !self.input.trim().is_empty() {
            for command in sources.history.recent() {
                if history_matches(command.trim_start(), self.input.trim_start()) {
                    let leading = self.input.len() - self.input.trim_start().len();
                    let value = format!(
                        "{}{}",
                        self.input.get(..leading).unwrap_or_default(),
                        command.trim_start()
                    );
                    if value != self.input {
                        self.candidates.push(Candidate {
                            cursor: value.len(),
                            label: command.trim().to_owned(),
                            value,
                            description: "history".to_owned(),
                        });
                    }
                }
            }
        }
        let mut seen = HashSet::new();
        self.candidates.retain(|candidate| {
            let (command, args) = split_command(candidate.value.trim());
            seen.insert(format!("{}{args}", command.to_ascii_lowercase()))
        });
    }
}

/// Edits and explicit actions from the command input and its suggestion list.
#[derive(Debug, Clone)]
pub enum Action {
    /// Text or caret changed; None indicates selection or IME composition.
    Edit(String, Option<usize>),
    /// Complete at the current caret, cycling backwards when the first value is true.
    Cycle(bool, String, usize),
    /// Insert a clicked suggestion without running it.
    Select(usize),
    /// Hide suggestions until editing resumes or Tab is pressed again.
    Dismiss,
}

/// The parts of the session that can change independently of the command catalog.
#[derive(Debug, Clone, Copy)]
pub(crate) struct Sources<'a> {
    pub history: &'a History,
    pub paths: &'a [String],
    pub textures: &'a [String],
}

#[derive(Debug)]
pub(super) struct Candidate {
    value: String,
    cursor: usize,
    pub(super) label: String,
    pub(super) description: String,
}

/// Only the token at the caret is replaced; arguments and leading whitespace stay untouched.
struct Context<'a> {
    input: &'a str,
    token: Range<usize>,
    prefix: &'a str,
    before: Vec<&'a str>,
}

impl<'a> Context<'a> {
    fn new(input: &'a str, cursor: usize) -> Option<Self> {
        let left = input.get(..cursor)?;
        let right = input.get(cursor..)?;
        let start = left
            .char_indices()
            .rev()
            .find(|(_, c)| c.is_whitespace())
            .map_or(0, |(offset, c)| offset + c.len_utf8());
        let end = cursor + right.find(char::is_whitespace).unwrap_or(right.len());
        Some(Self {
            input,
            token: start..end,
            prefix: input.get(start..cursor)?,
            before: input.get(..start)?.split_whitespace().collect(),
        })
    }

    fn names<'s>(&self, sources: &Sources<'s>) -> Option<(&'s [String], &'static str)> {
        let command = self.before.first()?.to_ascii_lowercase();
        let first = self.before.len() == 1;
        match command.as_str() {
            "pio" | "piv" | "picp" | "pimv" if first => Some((sources.paths, "path")),
            "pirm" => Some((sources.paths, "path")),
            "tio" | "tiv" | "ticp" | "timv" if first => Some((sources.textures, "texture")),
            "tirm" | "timute" => Some((sources.textures, "texture")),
            _ => None,
        }
    }

    fn replace(&self, word: &str, description: &str) -> Candidate {
        let before = self.input.get(..self.token.start).unwrap_or_default();
        let after = self.input.get(self.token.end..).unwrap_or_default();
        let suffix = if after.is_empty() { " " } else { after };
        let value = format!("{before}{word}{suffix}");
        let cursor = before.len() + word.len() + suffix.chars().next().map_or(0, char::len_utf8);
        Candidate {
            value,
            cursor,
            label: word.to_owned(),
            description: description.to_owned(),
        }
    }
}

fn split_command(input: &str) -> (&str, &str) {
    input.split_at(input.find(char::is_whitespace).unwrap_or(input.len()))
}

fn history_matches(command: &str, prefix: &str) -> bool {
    let (name, args) = split_command(command);
    let (typed, rest) = split_command(prefix);
    if rest.is_empty() {
        name.to_ascii_lowercase()
            .starts_with(&typed.to_ascii_lowercase())
    } else {
        name.eq_ignore_ascii_case(typed) && args.starts_with(rest)
    }
}
