//! The shared segmented slider used for playheads and master volume.

use std::cell::Cell;

use iced::{
    advanced::mouse,
    widget::{self, canvas},
    Color, Point, Rectangle, Renderer, Size, Theme,
};

use crate::app::theme::Colors;

/// A continuous playhead, or a stepped level when `steps` is set.
pub(crate) struct Slider<F> {
    pub(crate) position: f64,
    pub(crate) count: usize,
    pub(crate) colors: Colors,
    pub(crate) steps: Option<u8>,
    pub(crate) on_change: F,
}

impl<F> Slider<F> {
    pub(crate) fn position_at(x: f32, width: f32) -> f64 {
        f64::from((x / width.max(1.0)).clamp(0.0, 1.0))
    }

    fn snap(&self, position: f64) -> f64 {
        let position = position.clamp(0.0, 1.0);
        self.steps.map_or(position, |steps| {
            (position * f64::from(steps)).round() / f64::from(steps)
        })
    }
}

impl<Message, F: Fn(f64) -> Message> canvas::Program<Message> for Slider<F> {
    type State = State;

    fn update(
        &self,
        state: &mut State,
        event: &canvas::Event,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Option<widget::Action<Message>> {
        let change =
            |position| widget::Action::publish((self.on_change)(self.snap(position))).and_capture();
        match event {
            canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)) => {
                let at = cursor.position_in(bounds)?;
                let click = mouse::Click::new(at, mouse::Button::Left, state.click);
                let reset = self.steps.is_some() && click.kind() == mouse::click::Kind::Double;
                state.dragging = !reset;
                state.click = Some(click);
                Some(change(if reset {
                    1.0
                } else {
                    Self::position_at(at.x, bounds.width)
                }))
            }
            canvas::Event::Mouse(mouse::Event::CursorMoved { position }) if state.dragging => Some(
                change(Self::position_at(position.x - bounds.x, bounds.width)),
            ),
            canvas::Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)) => {
                state.dragging = false;
                None
            }
            canvas::Event::Mouse(mouse::Event::WheelScrolled { delta })
                if cursor.is_over(bounds) =>
            {
                let steps = f64::from(self.steps?);
                let (mouse::ScrollDelta::Lines { y, .. } | mouse::ScrollDelta::Pixels { y, .. }) =
                    delta;
                (*y != 0.0).then(|| change(self.position + f64::from(y.signum()) / steps))
            }
            canvas::Event::Window(iced::window::Event::Unfocused) => {
                state.dragging = false;
                state.click = None;
                None
            }
            _ => None,
        }
    }

    fn draw(
        &self,
        state: &State,
        renderer: &Renderer,
        _theme: &Theme,
        bounds: Rectangle,
        _cursor: mouse::Cursor,
    ) -> Vec<canvas::Geometry> {
        let key = (
            self.position,
            self.count,
            self.colors.lit,
            self.colors.unlit,
        );
        if state.key.replace(Some(key)) != Some(key) {
            state.cache.clear();
        }
        vec![state.cache.draw(renderer, bounds.size(), |frame| {
            let count = self.count.max(1) as f32;
            let gap = 2.0;
            let width = (bounds.width - gap * (count - 1.0)) / count;
            let played = (self.position.clamp(0.0, 1.0) as f32 * count).round();
            for index in 0..self.count {
                let segment = index as f32;
                let x = (segment * (width + gap)).round();
                let right = ((segment + 1.0) * (width + gap) - gap).round();
                frame.fill_rectangle(
                    Point::new(x, 0.0),
                    Size::new((right - x).max(0.0), bounds.height),
                    if segment < played {
                        self.colors.lit
                    } else {
                        self.colors.unlit
                    },
                );
            }
        })]
    }

    fn mouse_interaction(
        &self,
        state: &State,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> mouse::Interaction {
        if state.dragging || cursor.is_over(bounds) {
            mouse::Interaction::Pointer
        } else {
            mouse::Interaction::default()
        }
    }
}

/// Interaction and geometry survive rebuilding the view and unrelated playback ticks.
#[derive(Default)]
pub(crate) struct State {
    dragging: bool,
    click: Option<mouse::Click>,
    cache: canvas::Cache,
    key: Cell<Option<(f64, usize, Color, Color)>>,
}
