//! A texture's events as a score: `TImap`'s other view of them.
//!
//! The notation is drawn at the labels' pixel size along the plot's x axis. It opens at the scale
//! where notes are readable, from the texture's start; zooming and panning work as in the plot,
//! and a double click returns to the readable scale. The bar under the times shows the part of
//! the texture in view. Hovering a note inverts it and names it.

use std::cell::Cell;

use iced::{
    mouse,
    widget::{
        self,
        canvas::{self, Canvas, Frame},
    },
    Color, Element, Length, Point, Rectangle, Renderer, Size, Theme,
};

use super::{
    action, format_value, repaint, to_index, Anchor, Gesture, Label, Message, Palette, Pointer,
    Ticks, Window, LABEL_SCALE,
};
use crate::figure::{
    notation::{Axis, Run, Score},
    Domain, Parameters,
};

const RIGHT: f32 = 6.0;
/// Space after the clefs: before the notation starts, and before it's hidden behind them.
const CLEF_GAP: i32 = 8;
const CLEF_MARGIN: i32 = 2;
/// Space between the plate and what's under it.
const GUTTER: f32 = 4.0;
/// The bar showing the part in view: its track and its thumb.
const TRACK: f32 = 1.0;
const THUMB: f32 = 3.0;
/// Pixels per time label.
const X_LABEL_SPACING: f32 = 64.0;
/// The narrowest part of the axis to zoom in to, in seconds or events.
const MIN_SECONDS: f64 = 0.1;
const MIN_EVENTS: f64 = 2.0;
/// Notation pixels around a hovered note's head, in its inverted box.
const BOX_ACROSS: i32 = 2;
const BOX_DOWN: i32 = 3;

/// Show `parameters`' events, engraved as `score`, in `palette`.
pub(crate) fn view<'a>(
    parameters: &'a Parameters,
    score: &'a Score,
    palette: Palette,
) -> Element<'a, Message> {
    Canvas::new(Staves {
        parameters,
        score,
        palette,
    })
    .width(Length::Fill)
    .height(height(score))
    .into()
}

/// The plate, the times under it, the bar, and a line for the hovered note.
fn height(score: &Score) -> f32 {
    plate_height(score) + GUTTER + Label::height() + GUTTER + THUMB + GUTTER + Label::height()
}

fn plate_height(score: &Score) -> f32 {
    score.height() as f32 * LABEL_SCALE
}

struct Staves<'a> {
    parameters: &'a Parameters,
    score: &'a Score,
    palette: Palette,
}

#[derive(Debug, Default)]
struct State {
    pointer: Pointer,
    /// The part of the axis in view, once zoomed or panned: until then, the readable part from
    /// the start.
    window: Option<Window>,
    cache: canvas::Cache,
    painted: Cell<Option<Palette>>,
}

impl canvas::Program<Message> for Staves<'_> {
    type State = State;

    fn update(
        &self,
        state: &mut State,
        event: &canvas::Event,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Option<widget::Action<Message>> {
        let gesture = state.pointer.gesture(event, bounds, cursor);
        let layout = Layout::new(self, state.window, bounds.width);
        let area = layout.area();
        let min_span = layout.min_span();
        let changed = match gesture {
            Gesture::Zoom { at, factor } => {
                let anchor = ((at.x - area.x) / area.width).clamp(0.0, 1.0);
                state.window.get_or_insert(layout.window).zoom(
                    f64::from(anchor),
                    f64::from(factor),
                    min_span,
                )
            }
            Gesture::Pan { delta, .. } => state
                .window
                .get_or_insert(layout.window)
                .pan(f64::from(-delta.x / area.width)),
            Gesture::Reset => state.window.take().is_some(),
            Gesture::None | Gesture::Press | Gesture::Click(_) => false,
        };
        if changed {
            state.cache.clear();
        }
        action(gesture, changed, None)
    }

    fn draw(
        &self,
        state: &State,
        renderer: &Renderer,
        _theme: &Theme,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Vec<canvas::Geometry> {
        let layout = Layout::new(self, state.window, bounds.width);
        repaint(&state.cache, &state.painted, self.palette);
        let content = state
            .cache
            .draw(renderer, bounds.size(), |frame| layout.draw(frame));
        let mut hover = Frame::new(renderer, bounds.size());
        if let Some(at) = cursor.position_in(bounds) {
            if !state.pointer.dragging() {
                layout.draw_hover(&mut hover, at);
            }
        }
        vec![content, hover.into_geometry()]
    }

    fn mouse_interaction(
        &self,
        state: &State,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> mouse::Interaction {
        if state.pointer.dragging() {
            return mouse::Interaction::Grabbing;
        }
        let layout = Layout::new(self, state.window, bounds.width);
        match cursor.position_in(bounds) {
            Some(at) if layout.note_at(at).is_some() => mouse::Interaction::Crosshair,
            _ => mouse::Interaction::default(),
        }
    }
}

/// Where everything is, for a width and zoom.
struct Layout<'a> {
    parameters: &'a Parameters,
    score: &'a Score,
    palette: Palette,
    width: f32,
    /// The part of the axis in view, as fractions of the score's extent.
    window: Window,
}

impl<'a> Layout<'a> {
    fn new(staves: &Staves<'a>, window: Option<Window>, width: f32) -> Self {
        let mut layout = Self {
            parameters: staves.parameters,
            score: staves.score,
            palette: staves.palette,
            width,
            window: Window::default(),
        };
        layout.window = window.unwrap_or_else(|| layout.readable());
        layout
    }

    /// The part in view at the readable scale, from the start: everything, if it fits.
    fn readable(&self) -> Window {
        let (start, end) = self.score.extent();
        let columns = f64::from(self.area().width / LABEL_SCALE);
        let span = columns / self.score.readable_scale() / (end - start);
        Window {
            start: 0.0,
            end: span.min(1.0),
        }
    }

    fn min_span(&self) -> f64 {
        let (start, end) = self.score.extent();
        let min = match self.parameters.domain {
            Domain::Time => MIN_SECONDS,
            Domain::Events => MIN_EVENTS,
        };
        min / (end - start)
    }

    /// Where the x axis is drawn, in pixels: after the clefs.
    fn area(&self) -> Rectangle {
        let left = (self.score.clef_width() + CLEF_GAP) as f32 * LABEL_SCALE;
        Rectangle::new(
            Point::new(left, 0.0),
            Size::new(
                (self.width - left - RIGHT).max(1.0),
                plate_height(self.score),
            ),
        )
    }

    /// The visible part of the axis.
    fn visible(&self) -> (f64, f64) {
        let (start, end) = self.score.extent();
        let span = end - start;
        (
            start + self.window.start * span,
            start + self.window.end * span,
        )
    }

    /// The x axis in notation pixels.
    fn axis(&self) -> Axis {
        let area = self.area();
        let (start, end) = self.visible();
        Axis {
            origin: (area.x / LABEL_SCALE).round() as i32,
            start,
            scale: f64::from(area.width / LABEL_SCALE) / (end - start),
        }
    }

    /// The notation's columns: just after the clefs, up to the right edge.
    fn columns(&self) -> (i32, i32) {
        (
            self.score.clef_width() + CLEF_MARGIN,
            ((self.width - RIGHT) / LABEL_SCALE).floor() as i32,
        )
    }

    fn times_y(&self) -> f32 {
        plate_height(self.score) + GUTTER
    }

    fn bar_y(&self) -> f32 {
        self.times_y() + Label::height() + GUTTER
    }

    fn readout_y(&self) -> f32 {
        self.bar_y() + THUMB + GUTTER
    }

    fn note_at(&self, at: Point) -> Option<&'a crate::figure::notation::Note> {
        let column = (at.x / LABEL_SCALE).floor() as i32;
        let row = (at.y / LABEL_SCALE).floor() as i32;
        let (left, right) = self.columns();
        if column < left || column >= right {
            return None;
        }
        self.score.note_at(&self.axis(), column, row)
    }

    fn draw(&self, frame: &mut Frame) {
        let palette = self.palette;
        let plate = plate_height(self.score);
        frame.fill_rectangle(
            Point::ORIGIN,
            Size::new(self.width, self.height()),
            palette.page,
        );
        frame.fill_rectangle(Point::ORIGIN, Size::new(self.width, plate), palette.plate);

        let lines = self.staff_lines();
        fill_runs(frame, &lines, palette.staff);
        fill_runs(frame, self.score.pinned(), palette.mark);
        let (left, right) = self.columns();
        fill_runs(
            frame,
            &self.score.runs(&self.axis(), left, right),
            palette.mark,
        );

        self.draw_times(frame);
        self.draw_bar(frame);
    }

    fn height(&self) -> f32 {
        height(self.score)
    }

    /// Every staff's lines, across the plate.
    fn staff_lines(&self) -> Vec<Run> {
        let length = (self.width / LABEL_SCALE).ceil() as i32;
        self.score
            .staves()
            .iter()
            .flat_map(|staff| {
                (0..5).map(move |line| Run {
                    x: 0,
                    y: staff.top + 4 * line,
                    length,
                })
            })
            .collect()
    }

    /// The axis' values under the plate.
    fn draw_times(&self, frame: &mut Frame) {
        let (start, end) = self.visible();
        let area = self.area();
        let count = to_index(f64::from(area.width / X_LABEL_SPACING));
        let min_step = match self.parameters.domain {
            Domain::Time => 0.001,
            Domain::Events => 1.0,
        };
        let ticks = Ticks::new(start, end, count.max(2), min_step);
        for &value in &ticks.values {
            let x = area.x + ((value - start) / (end - start)) as f32 * area.width;
            let label = Label::new(&ticks.format(value));
            let at = Point::new(x.round(), self.times_y());
            let bounds = label.bounds(at, Anchor::NorthCenter);
            if bounds.x >= 0.0 && bounds.x + bounds.width <= self.width {
                label.draw(frame, at, Anchor::NorthCenter, self.palette.label);
            }
        }
    }

    /// A hairline track under the times, with a thumb over the part in view.
    fn draw_bar(&self, frame: &mut Frame) {
        let area = self.area();
        let y = self.bar_y();
        frame.fill_rectangle(
            Point::new(area.x, y + (THUMB - TRACK) / 2.0),
            Size::new(area.width, TRACK),
            self.palette.track,
        );
        let left = (area.x + self.window.start as f32 * area.width).round();
        let right = (area.x + self.window.end as f32 * area.width).round();
        frame.fill_rectangle(
            Point::new(left, y),
            Size::new((right - left).max(THUMB), THUMB),
            self.palette.label,
        );
    }

    /// Invert the note under the pointer in a box, and name it under the bar.
    fn draw_hover(&self, frame: &mut Frame, at: Point) {
        let Some(note) = self.note_at(at) else {
            return;
        };
        let axis = self.axis();
        let (x, y, width, height) = note.bounds(&axis);
        let (left, top) = (x - BOX_ACROSS, y - BOX_DOWN);
        let (right, bottom) = (x + width + BOX_ACROSS, y + height + BOX_DOWN);
        let s = LABEL_SCALE;
        frame.fill_rectangle(
            Point::new(left as f32 * s, top as f32 * s),
            Size::new((right - left) as f32 * s, (bottom - top) as f32 * s),
            self.palette.hover,
        );
        let inside = |run: &Run| run.y >= top && run.y < bottom;
        let lines: Vec<Run> = self
            .staff_lines()
            .into_iter()
            .filter(inside)
            .map(|run| Run {
                x: left,
                y: run.y,
                length: right - left,
            })
            .collect();
        fill_runs(frame, &lines, self.palette.plate);
        let notation: Vec<Run> = self
            .score
            .runs(&axis, left, right)
            .into_iter()
            .filter(inside)
            .collect();
        fill_runs(frame, &notation, self.palette.plate);

        let Some(event) = self.parameters.events.get(note.event) else {
            return;
        };
        let text = format!(
            "{}: {}  dur {}  amp {}",
            note.event,
            note.name,
            format_value(event.duration),
            format_value(event.amplitude)
        );
        Label::new(&text).draw(
            frame,
            Point::new(self.area().x, self.readout_y()),
            Anchor::NorthWest,
            self.palette.label,
        );
    }
}

/// Fill runs of notation pixels in `color`.
fn fill_runs(frame: &mut Frame, runs: &[Run], color: Color) {
    let s = LABEL_SCALE;
    for run in runs {
        frame.fill_rectangle(
            Point::new(run.x as f32 * s, run.y as f32 * s),
            Size::new(run.length as f32 * s, s),
            color,
        );
    }
}

#[cfg(test)]
mod tests {
    use iced::keyboard;

    use super::*;
    use crate::{app::theme::Mode, figure::Event};

    fn parameters(domain: Domain) -> Parameters {
        // 64 eighths at 120 BPM: sixteen seconds, longer than the output is wide
        let events = (0..64)
            .map(|i| Event {
                time: f64::from(i) * 0.25,
                duration: 0.25,
                sustain: 0.25,
                sounds: true,
                pitch: f64::from(i % 8),
                amplitude: 0.7,
                tempo: 120.0,
            })
            .collect();
        Parameters {
            domain,
            detailed: false,
            graphs: Vec::new(),
            events,
        }
    }

    fn staves<'a>(parameters: &'a Parameters, score: &'a Score) -> Staves<'a> {
        Staves {
            parameters,
            score,
            palette: Mode::Light.colors().figure(),
        }
    }

    #[test]
    fn scores_open_at_the_readable_scale() {
        let parameters = parameters(Domain::Time);
        let score = Score::new(&parameters.events, parameters.domain);
        let staves = staves(&parameters, &score);
        let layout = Layout::new(&staves, None, 696.0);
        // the shortest note, an eighth, gets ten notation pixels
        let axis = layout.axis();
        assert_eq!(axis.x(0.25) - axis.x(0.0), 10);
        assert!(layout.window.end < 1.0);

        // a wide view shows everything, spread out
        let wide = Layout::new(&staves, None, 4000.0);
        assert!((wide.window.end - 1.0).abs() < 1e-12);
    }

    #[test]
    fn zooming_starts_from_the_readable_window_and_resets_to_it() {
        let parameters = parameters(Domain::Time);
        let score = Score::new(&parameters.events, parameters.domain);
        let program = staves(&parameters, &score);
        let bounds = Rectangle::new(Point::ORIGIN, Size::new(696.0, 200.0));
        let at = mouse::Cursor::Available(Point::new(300.0, 40.0));
        let command = canvas::Event::Keyboard(keyboard::Event::ModifiersChanged(
            keyboard::Modifiers::COMMAND,
        ));
        let zoom = canvas::Event::Mouse(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Pixels { x: 0.0, y: 60.0 },
        });
        let press = canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left));

        let mut state = State::default();
        let readable = Layout::new(&program, None, 696.0).window;
        canvas::Program::update(&program, &mut state, &command, bounds, at);
        canvas::Program::update(&program, &mut state, &zoom, bounds, at);
        let zoomed = state.window.expect("zooming keeps a window");
        assert!(zoomed.span() < readable.span());

        canvas::Program::update(&program, &mut state, &press, bounds, at);
        canvas::Program::update(&program, &mut state, &press, bounds, at);
        assert!(
            state.window.is_none(),
            "a double click returns to the readable scale"
        );
    }

    #[test]
    fn hovering_finds_notes_and_not_the_clefs() {
        let parameters = parameters(Domain::Time);
        let score = Score::new(&parameters.events, parameters.domain);
        let staves = staves(&parameters, &score);
        let layout = Layout::new(&staves, None, 696.0);
        let axis = layout.axis();
        let note = score.note_at(&axis, axis.x(0.5) + 3, 0);
        assert!(note.is_none(), "row 0 is above every note");

        let found = (0..score.height()).find_map(|row| {
            let at = Point::new(
                (axis.x(0.5) + 3) as f32 * LABEL_SCALE,
                row as f32 * LABEL_SCALE,
            );
            layout.note_at(at)
        });
        assert_eq!(found.map(|note| note.event), Some(2));
        assert!(layout.note_at(Point::new(5.0, 30.0)).is_none());
    }

    #[test]
    fn event_mode_uses_slots() {
        let parameters = parameters(Domain::Events);
        let score = Score::new(&parameters.events, parameters.domain);
        let staves = staves(&parameters, &score);
        let axis = Layout::new(&staves, None, 696.0).axis();
        assert_eq!(axis.x(1.0) - axis.x(0.0), 16);
    }
}
