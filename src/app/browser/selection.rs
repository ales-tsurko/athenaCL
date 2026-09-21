//! Selection follows the visible tree order, with a stable anchor for Shift-click.

use std::{
    collections::BTreeSet,
    path::{Path, PathBuf},
};

use iced::keyboard::Modifiers;

use crate::app::browser::filesystem::Entry;

#[derive(Debug, Default)]
pub(crate) struct Selection {
    paths: BTreeSet<PathBuf>,
    anchor: Option<PathBuf>,
    /// The entry the keyboard moves from: the last one clicked or stepped to.
    lead: Option<PathBuf>,
}

impl Selection {
    pub(crate) fn contains(&self, path: &Path) -> bool {
        self.paths.contains(path)
    }

    pub(crate) fn len(&self) -> usize {
        self.paths.len()
    }

    pub(crate) fn lead(&self) -> Option<&Path> {
        self.lead.as_deref()
    }

    pub(crate) fn only(&mut self, path: PathBuf) {
        self.paths = BTreeSet::from([path.clone()]);
        self.anchor = Some(path.clone());
        self.lead = Some(path);
    }

    pub(crate) fn replace(&mut self, paths: Vec<PathBuf>) {
        self.anchor = paths.first().cloned();
        self.lead = paths.first().cloned();
        self.paths = paths.into_iter().collect();
    }

    pub(crate) fn clear(&mut self) {
        *self = Self::default();
    }

    /// Every entry shown, keeping where the keyboard is.
    pub(crate) fn all(&mut self, entries: &[Entry]) {
        self.paths = entries.iter().map(|entry| entry.path.clone()).collect();
        if self.lead.is_none() {
            self.lead = entries.first().map(|entry| entry.path.clone());
        }
        self.anchor = self.lead.clone();
    }

    /// Move the lead `step` entries through `entries` and select it alone, or, `extending`,
    /// everything from the anchor to it. With nothing selected, the first or last entry is taken.
    pub(crate) fn step(&mut self, step: isize, extending: bool, entries: &[Entry]) {
        let last = entries.len().saturating_sub(1);
        let current = self
            .lead
            .as_ref()
            .and_then(|lead| entries.iter().position(|entry| &entry.path == lead));
        let index = match current {
            Some(index) => index.saturating_add_signed(step).min(last),
            None if step < 0 => last,
            None => 0,
        };
        let Some(entry) = entries.get(index) else {
            return;
        };
        let modifiers = if extending && current.is_some() {
            Modifiers::SHIFT
        } else {
            Modifiers::empty()
        };
        self.click(entry.path.clone(), modifiers, entries);
    }

    pub(crate) fn click(&mut self, path: PathBuf, modifiers: Modifiers, entries: &[Entry]) {
        self.lead = Some(path.clone());
        let additive = modifiers.command();
        if modifiers.shift() {
            let anchor = self
                .anchor
                .as_ref()
                .and_then(|anchor| entries.iter().position(|entry| &entry.path == anchor));
            let end = entries.iter().position(|entry| entry.path == path);
            if let (Some(start), Some(end)) = (anchor, end) {
                if !additive {
                    self.paths.clear();
                }
                self.paths.extend(
                    entries
                        .iter()
                        .take(start.max(end) + 1)
                        .skip(start.min(end))
                        .map(|entry| entry.path.clone()),
                );
                return;
            }
        }
        if additive {
            if !self.paths.remove(&path) {
                self.paths.insert(path.clone());
            }
            self.anchor = Some(path);
        } else {
            self.only(path);
        }
    }

    pub(crate) fn context(&mut self, path: PathBuf) {
        if !self.contains(&path) {
            self.only(path);
        }
    }

    /// Hidden or removed entries cannot remain selected for a later destructive action.
    pub(crate) fn retain(&mut self, entries: &[Entry]) {
        self.paths
            .retain(|path| entries.iter().any(|entry| &entry.path == path));
        let shown = |path: &Option<PathBuf>| {
            path.as_ref()
                .is_some_and(|path| entries.iter().any(|entry| &entry.path == path))
        };
        if !shown(&self.anchor) {
            self.anchor = None;
        }
        if !shown(&self.lead) {
            self.lead = None;
        }
    }

    /// A selected folder already includes its selected descendants in copy/delete operations.
    pub(crate) fn targets(&self, context: &Path) -> Vec<PathBuf> {
        if !self.contains(context) {
            return vec![context.into()];
        }
        self.paths
            .iter()
            .filter(|path| {
                !path
                    .ancestors()
                    .skip(1)
                    .any(|parent| self.paths.contains(parent))
            })
            .cloned()
            .collect()
    }
}
