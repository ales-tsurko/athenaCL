//! Keep a drag inside widget state so batched native events cannot lose its source or target.

use std::{path::PathBuf, time::Duration};

use iced::{
    advanced::{mouse, Shell},
    keyboard::{self, Modifiers},
    time::Instant,
    window, Event, Point, Rectangle,
};

use crate::app::browser::{drag::Targets, Browser, Message};

const DRAG_DISTANCE: f32 = 6.0;
const EXPAND_DELAY: Duration = Duration::from_millis(650);
const SCROLL_INTERVAL: Duration = Duration::from_millis(33);

#[derive(Debug, Default)]
pub(crate) struct Gesture {
    press: Option<Press>,
    hover: Option<Hover>,
}

impl Gesture {
    pub(crate) fn engaged(&self) -> bool {
        self.press.is_some()
    }

    pub(crate) fn active(&self) -> bool {
        self.press.as_ref().is_some_and(|press| press.dragging)
    }

    pub(crate) fn highlight(&self) -> Option<Rectangle> {
        self.hover.as_ref().map(|hover| hover.bounds)
    }

    pub(crate) fn interaction(&self) -> Option<mouse::Interaction> {
        // what is dragged is carried, as a hand carries it, and refused where it cannot go
        self.active().then_some(if self.hover.is_some() {
            mouse::Interaction::Grabbing
        } else {
            mouse::Interaction::NoDrop
        })
    }

    pub(crate) fn click(
        &mut self,
        path: PathBuf,
        modifiers: Modifiers,
        double: bool,
        position: Option<Point>,
        browser: &Browser,
    ) -> Message {
        *self = Self::default();
        if !double && modifiers.is_empty() && !browser.busy && browser.edit.is_none() {
            if let Some(position) = position.filter(|_| path != browser.root) {
                self.press = Some(Press {
                    start: position,
                    path: path.clone(),
                    sources: browser.selected.targets(&path),
                    dragging: false,
                    last_scroll: Instant::now(),
                });
                // Preserve a multi-selection until release: pressing one of its rows starts a
                // drag of the whole selection, while an ordinary click still collapses it.
                if browser.selected.contains(&path) {
                    return Message::Context(path);
                }
            }
        }
        Message::Click(path, modifiers, double)
    }

    pub(crate) fn update(
        &mut self,
        event: &Event,
        position: Option<Point>,
        browser: &Browser,
        targets: &Targets,
        shell: &mut Shell<'_, Message>,
    ) -> bool {
        if browser.busy || browser.edit.is_some() {
            *self = Self::default();
            return false;
        }
        match event {
            Event::Window(window::Event::Unfocused)
            | Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Right)) => {
                *self = Self::default();
                shell.request_redraw();
                return false;
            }
            Event::Keyboard(keyboard::Event::KeyPressed {
                key: keyboard::Key::Named(keyboard::key::Named::Escape),
                ..
            }) if self.press.is_some() => {
                *self = Self::default();
                shell.request_redraw();
                return true;
            }
            _ => (),
        }
        let Some(press) = self.press.as_mut() else {
            return false;
        };
        if matches!(event, Event::Mouse(mouse::Event::CursorMoved { .. }))
            && position.is_some_and(|position| position.distance(press.start) >= DRAG_DISTANCE)
        {
            press.dragging = true;
        }
        let now = match event {
            Event::Window(window::Event::RedrawRequested(now)) => *now,
            _ => Instant::now(),
        };
        if press.dragging {
            let target = position
                .and_then(|position| targets.folder_at(position, browser))
                .filter(|(directory, _)| {
                    !press
                        .sources
                        .iter()
                        .any(|source| directory.starts_with(source))
                        && press
                            .sources
                            .iter()
                            .any(|source| source.parent() != Some(directory.as_path()))
                });
            match (target, &mut self.hover) {
                (Some((path, bounds)), Some(hover)) if hover.path == path => {
                    hover.bounds = bounds;
                }
                (Some((path, bounds)), _) => {
                    self.hover = Some(Hover {
                        path,
                        bounds,
                        expand_at: Some(now + EXPAND_DELAY),
                    });
                }
                (None, _) => self.hover = None,
            }
            if let Some(hover) = &mut self.hover {
                if hover.path == browser.root || browser.expanded.contains(&hover.path) {
                    hover.expand_at = None;
                }
                if let Some(deadline) = hover.expand_at {
                    if now >= deadline {
                        shell.publish(Message::RevealFolder(hover.path.clone()));
                        hover.expand_at = None;
                    } else {
                        shell.request_redraw_at(deadline);
                    }
                }
            }
            let scroll = position.map_or(0.0, |position| targets.scroll_at(position));
            if scroll != 0.0 {
                if now >= press.last_scroll + SCROLL_INTERVAL {
                    shell.publish(Message::Scroll(scroll));
                    press.last_scroll = now;
                }
                shell.request_redraw_at(press.last_scroll + SCROLL_INTERVAL);
            }
            if matches!(
                event,
                Event::Mouse(mouse::Event::CursorMoved { .. } | mouse::Event::CursorLeft)
            ) {
                shell.request_redraw();
            }
        }
        if matches!(
            event,
            Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left))
        ) {
            let press = self.press.take().expect("a press is active");
            if press.dragging {
                if let Some(hover) = self.hover.take() {
                    shell.publish(Message::Move(press.sources, hover.path));
                }
            } else {
                shell.publish(Message::Click(press.path, Modifiers::empty(), false));
            }
            self.hover = None;
            shell.request_redraw();
            return true;
        }
        self.active() && matches!(event, Event::Mouse(mouse::Event::CursorMoved { .. }))
    }
}

#[derive(Debug)]
struct Press {
    start: Point,
    path: PathBuf,
    sources: Vec<PathBuf>,
    dragging: bool,
    last_scroll: Instant,
}

#[derive(Debug)]
struct Hover {
    path: PathBuf,
    bounds: Rectangle,
    expand_at: Option<Instant>,
}
