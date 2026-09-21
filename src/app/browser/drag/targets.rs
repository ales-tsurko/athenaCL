//! Resolve row bounds through the tree's scroll offset and viewport.

use std::{any::Any, path::PathBuf};

use iced::{
    advanced::widget::{operation::Scrollable, Id, Operation},
    Point, Rectangle, Vector,
};

use crate::app::browser::{filesystem::Kind, state::TREE, Browser};

pub(crate) struct Targets {
    rows: Vec<(PathBuf, Rectangle)>,
    clip: Rectangle,
    offset: Vector,
    pending: Option<(Vector, Rectangle)>,
    scroll: Option<(Rectangle, f32, f32)>,
}

impl Targets {
    pub(crate) fn new(viewport: Rectangle) -> Self {
        Self {
            rows: Vec::new(),
            clip: viewport,
            offset: Vector::ZERO,
            pending: None,
            scroll: None,
        }
    }

    pub(crate) fn folder_at(
        &self,
        position: Point,
        browser: &Browser,
    ) -> Option<(PathBuf, Rectangle)> {
        self.rows
            .iter()
            .find(|(path, bounds)| {
                bounds.contains(position)
                    && (*path == browser.root
                        || browser
                            .listing
                            .entries
                            .iter()
                            .any(|entry| entry.path == *path && entry.kind == Kind::Folder))
            })
            .cloned()
    }

    pub(crate) fn scroll_at(&self, position: Point) -> f32 {
        let Some((bounds, offset, maximum)) = self.scroll else {
            return 0.0;
        };
        if !bounds.contains(position) {
            return 0.0;
        }
        if position.y < bounds.y + 24.0 && offset > 0.0 {
            -12.0
        } else if position.y > bounds.y + bounds.height - 24.0 && offset < maximum {
            12.0
        } else {
            0.0
        }
    }
}

impl Operation for Targets {
    fn traverse(&mut self, operate: &mut dyn FnMut(&mut dyn Operation)) {
        let previous = (self.offset, self.clip);
        if let Some((offset, clip)) = self.pending.take() {
            self.offset = offset;
            self.clip = clip;
        }
        operate(self);
        (self.offset, self.clip) = previous;
    }

    fn scrollable(
        &mut self,
        id: Option<&Id>,
        bounds: Rectangle,
        content_bounds: Rectangle,
        translation: Vector,
        _state: &mut dyn Scrollable,
    ) {
        let bounds = bounds - self.offset;
        let clip = bounds.intersection(&self.clip).unwrap_or_default();
        self.pending = Some((self.offset + translation, clip));
        if id == Some(&Id::from(TREE)) {
            self.scroll = Some((
                clip,
                translation.y,
                (content_bounds.height - bounds.height).max(0.0),
            ));
        }
    }

    fn custom(&mut self, _id: Option<&Id>, bounds: Rectangle, state: &mut dyn Any) {
        if let Some(path) = state.downcast_ref::<PathBuf>() {
            if let Some(bounds) = (bounds - self.offset).intersection(&self.clip) {
                self.rows.push((path.clone(), bounds));
            }
        }
    }
}
