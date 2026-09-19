//! Events as a score: the other view of `TImap`'s texture, and of `TEmap`'s ensemble.
//!
//! The notation is drawn at the labels' pixel size along the plot's x axis. It opens at the scale
//! where notes are readable, from the start; zooming and panning work as in the plot, and a double
//! click returns to the readable scale. The bar under the times shows the part in view, and
//! dragging it moves the view. Hovering a note inverts it and names it. An ensemble's textures
//! are staves under each other, sharing the axis.

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
    action, bar_action, format_value, repaint, to_index, Anchor, Bar, Gesture, Label, Message,
    Palette, Pointer, Ticks, Window, BAR_HEIGHT, LABEL_SCALE,
};
use crate::figure::{
    notation::{Axis, Note, Run, Score},
    Domain, Event,
};

const RIGHT: f32 = 6.0;
/// Space after the clefs: before the notation starts, and before it's hidden behind them.
const CLEF_GAP: i32 = 8;
const CLEF_MARGIN: i32 = 2;
/// Space between the plate and what's under it.
const GUTTER: f32 = 4.0;
/// Space between one texture's staves and the next's.
const PART_GAP: f32 = 12.0;
/// Space between the textures' names and their staves.
const NAME_GAP: f32 = 8.0;
/// Pixels per time label.
const X_LABEL_SPACING: f32 = 64.0;
/// The narrowest part of the axis to zoom in to, in seconds or events.
const MIN_SECONDS: f64 = 0.1;
const MIN_EVENTS: f64 = 2.0;
/// Notation pixels around a hovered note's head, in its inverted box.
const BOX_ACROSS: i32 = 2;
const BOX_DOWN: i32 = 3;

/// A texture's notation in a score: an ensemble's parts are named, a single texture's is not.
pub(crate) struct Part<'a> {
    /// The texture's name, empty when the score shows only it.
    pub(crate) name: &'a str,
    /// Its events, engraved.
    pub(crate) score: &'a Score,
    /// The events themselves, for what hovering says about them.
    pub(crate) events: &'a [Event],
}

/// Show `parts` along one axis measuring `domain`, in `palette`.
pub(crate) fn view<'a>(
    parts: Vec<Part<'a>>,
    domain: Domain,
    palette: Palette,
) -> Element<'a, Message> {
    let height = height(&parts);
    Canvas::new(Staves {
        parts,
        domain,
        palette,
    })
    .width(Length::Fill)
    .height(height)
    .into()
}

/// The staves, the times under them, the bar, and a line for the hovered note.
fn height(parts: &[Part<'_>]) -> f32 {
    plate_height(parts) + GUTTER + Label::height() + BAR_HEIGHT + GUTTER + Label::height()
}

fn plate_height(parts: &[Part<'_>]) -> f32 {
    let staves: f32 = parts.iter().map(part_height).sum();
    staves + PART_GAP * parts.len().saturating_sub(1) as f32
}

fn part_height(part: &Part<'_>) -> f32 {
    part.score.height() as f32 * LABEL_SCALE
}

struct Staves<'a> {
    parts: Vec<Part<'a>>,
    domain: Domain,
    palette: Palette,
}

#[derive(Debug, Default)]
struct State {
    pointer: Pointer,
    bar: Bar,
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
        let layout = Layout::new(self, state.window, bounds.width);
        let mut window = state.window.unwrap_or(layout.window);
        if let Some(changed) =
            state
                .bar
                .update(event, bounds, layout.bar_area(), cursor, &mut window)
        {
            if changed {
                state.window = Some(window);
                state.cache.clear();
            }
            return bar_action(changed);
        }
        let gesture = state.pointer.gesture(event, bounds, cursor);
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
            Gesture::None | Gesture::Hover | Gesture::Press | Gesture::Click(_) => false,
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
        if state.pointer.dragging() || state.bar.dragging() {
            return mouse::Interaction::Grabbing;
        }
        let layout = Layout::new(self, state.window, bounds.width);
        match cursor.position_in(bounds) {
            Some(at) if layout.bar_area().contains(at) => mouse::Interaction::Pointer,
            Some(at) if layout.note_at(at).is_some() => mouse::Interaction::Crosshair,
            _ => mouse::Interaction::default(),
        }
    }
}

/// Where everything is, for a width and zoom.
struct Layout<'a, 'p> {
    parts: &'p [Part<'a>],
    domain: Domain,
    palette: Palette,
    width: f32,
    /// The part of the axis in view, as fractions of the whole.
    window: Window,
}

impl<'a, 'p> Layout<'a, 'p> {
    fn new(staves: &'p Staves<'a>, window: Option<Window>, width: f32) -> Self {
        let mut layout = Self {
            parts: &staves.parts,
            domain: staves.domain,
            palette: staves.palette,
            width,
            window: Window::default(),
        };
        layout.window = window.unwrap_or_else(|| layout.readable());
        layout
    }

    /// The whole axis: from the first part's start to the last one's end.
    fn extent(&self) -> (f64, f64) {
        let (start, end) = self.parts.iter().map(|part| part.score.extent()).fold(
            (f64::INFINITY, f64::NEG_INFINITY),
            |(start, end), (from, to)| (start.min(from), end.max(to)),
        );
        if start.is_finite() && end > start {
            (start, end)
        } else {
            (0.0, 1.0)
        }
    }

    /// The part in view at the readable scale, from the start: everything, if it fits. The
    /// densest texture sets the scale.
    fn readable(&self) -> Window {
        let (start, end) = self.extent();
        let scale = self
            .parts
            .iter()
            .map(|part| part.score.readable_scale())
            .fold(0.0, f64::max)
            .max(f64::EPSILON);
        let columns = f64::from(self.area().width / LABEL_SCALE);
        let span = columns / scale / (end - start);
        Window {
            start: 0.0,
            end: span.min(1.0),
        }
    }

    fn min_span(&self) -> f64 {
        let (start, end) = self.extent();
        let min = match self.domain {
            Domain::Time => MIN_SECONDS,
            Domain::Events => MIN_EVENTS,
        };
        min / (end - start)
    }

    /// Room for the textures' names, left of their staves.
    fn names_width(&self) -> f32 {
        let widest = self
            .parts
            .iter()
            .map(|part| Label::new(part.name).width())
            .fold(0.0, f32::max);
        if widest > 0.0 {
            widest + NAME_GAP
        } else {
            0.0
        }
    }

    /// How far the clefs reach, in notation pixels.
    fn clefs(&self) -> i32 {
        self.parts
            .iter()
            .map(|part| part.score.clef_width())
            .max()
            .unwrap_or(0)
    }

    /// Where the x axis is drawn, in pixels: after the names and the clefs.
    fn area(&self) -> Rectangle {
        let left = self.names_width() + (self.clefs() + CLEF_GAP) as f32 * LABEL_SCALE;
        Rectangle::new(
            Point::new(left, 0.0),
            Size::new(
                (self.width - left - RIGHT).max(1.0),
                plate_height(self.parts),
            ),
        )
    }

    /// Where a part's notation starts down the plate.
    fn part_top(&self, index: usize) -> f32 {
        self.parts
            .iter()
            .take(index)
            .map(|part| part_height(part) + PART_GAP)
            .sum()
    }

    /// A part's notation rows, from the top of the plate.
    fn part_rows(&self, index: usize) -> i32 {
        (self.part_top(index) / LABEL_SCALE).round() as i32
    }

    /// The visible part of the axis.
    fn visible(&self) -> (f64, f64) {
        let (start, end) = self.extent();
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
            self.names_rows() + self.clefs() + CLEF_MARGIN,
            ((self.width - RIGHT) / LABEL_SCALE).floor() as i32,
        )
    }

    /// The names' columns, which the clefs stand after.
    fn names_rows(&self) -> i32 {
        (self.names_width() / LABEL_SCALE).round() as i32
    }

    fn times_y(&self) -> f32 {
        plate_height(self.parts) + GUTTER
    }

    /// The bar's row, under the times.
    fn bar_area(&self) -> Rectangle {
        Bar::area(self.area(), self.times_y() + Label::height())
    }

    fn readout_y(&self) -> f32 {
        self.times_y() + Label::height() + BAR_HEIGHT + GUTTER
    }

    /// The note under `at`, with its part and where the part sits.
    fn note_at(&self, at: Point) -> Option<(usize, &'a Note)> {
        let column = (at.x / LABEL_SCALE).floor() as i32;
        let row = (at.y / LABEL_SCALE).floor() as i32;
        let (left, right) = self.columns();
        if column < left || column >= right {
            return None;
        }
        let axis = self.axis();
        self.parts.iter().enumerate().find_map(|(index, part)| {
            let note = part
                .score
                .note_at(&axis, column, row - self.part_rows(index))?;
            Some((index, note))
        })
    }

    fn draw(&self, frame: &mut Frame) {
        let palette = self.palette;
        frame.fill_rectangle(
            Point::ORIGIN,
            Size::new(self.width, height(self.parts)),
            palette.page,
        );
        // the names stand on the page, beside the plate, as a texture's name does in a plot
        frame.fill_rectangle(
            Point::new(self.names_width(), 0.0),
            Size::new(self.width - self.names_width(), plate_height(self.parts)),
            palette.plate,
        );

        let axis = self.axis();
        let (left, right) = self.columns();
        let names = self.names_rows();
        for (index, part) in self.parts.iter().enumerate() {
            let top = self.part_rows(index);
            fill_runs(frame, &shift(self.staff_lines(part), 0, top), palette.staff);
            fill_runs(
                frame,
                &shift(part.score.pinned().to_vec(), names, top),
                palette.mark,
            );
            fill_runs(
                frame,
                &shift(part.score.runs(&axis, left, right), 0, top),
                palette.mark,
            );
            if !part.name.is_empty() {
                Label::new(part.name).draw(
                    frame,
                    Point::new(0.0, self.part_top(index) + part_height(part) / 2.0),
                    Anchor::CenterWest,
                    palette.label,
                );
            }
        }

        self.draw_times(frame);
        Bar::draw(frame, self.bar_area(), self.window, palette);
    }

    /// A part's staff lines, across the plate.
    fn staff_lines(&self, part: &Part<'_>) -> Vec<Run> {
        let left = self.names_rows();
        let length = ((self.width / LABEL_SCALE).ceil() as i32 - left).max(0);
        part.score
            .staves()
            .iter()
            .flat_map(|staff| {
                (0..5).map(move |line| Run {
                    x: left,
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
        let min_step = match self.domain {
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

    /// Invert the note under the pointer in a box, and name it under the bar.
    fn draw_hover(&self, frame: &mut Frame, at: Point) {
        let Some((index, note)) = self.note_at(at) else {
            return;
        };
        let Some(part) = self.parts.get(index) else {
            return;
        };
        let top = self.part_rows(index);
        let axis = self.axis();
        let (x, y, width, height) = note.bounds(&axis);
        let (left, upper) = (x - BOX_ACROSS, y + top - BOX_DOWN);
        let (right, lower) = (x + width + BOX_ACROSS, y + top + height + BOX_DOWN);
        let s = LABEL_SCALE;
        frame.fill_rectangle(
            Point::new(left as f32 * s, upper as f32 * s),
            Size::new((right - left) as f32 * s, (lower - upper) as f32 * s),
            self.palette.hover,
        );
        let inside = |run: &Run| run.y >= upper && run.y < lower;
        let lines: Vec<Run> = shift(self.staff_lines(part), 0, top)
            .into_iter()
            .map(|run| Run {
                x: left,
                y: run.y,
                length: right - left,
            })
            .filter(inside)
            .collect();
        fill_runs(frame, &lines, self.palette.plate);
        let notation: Vec<Run> = shift(part.score.runs(&axis, left, right), 0, top)
            .into_iter()
            .filter(inside)
            .collect();
        fill_runs(frame, &notation, self.palette.plate);

        let Some(event) = part.events.get(note.event) else {
            return;
        };
        let name = if part.name.is_empty() {
            String::new()
        } else {
            format!("{} ", part.name)
        };
        let text = format!(
            "{name}{}: {}  dur {}  amp {}",
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

/// Move runs across and down, as a part sits under the ones before it.
fn shift(runs: Vec<Run>, across: i32, down: i32) -> Vec<Run> {
    runs.into_iter()
        .map(|run| Run {
            x: run.x + across,
            y: run.y + down,
            length: run.length,
        })
        .collect()
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
    use crate::app::theme::Mode;

    /// 64 eighths at 120 BPM: sixteen seconds, longer than the output is wide.
    fn events(pitch: f64) -> Vec<Event> {
        (0..64)
            .map(|i| Event {
                time: f64::from(i) * 0.25,
                duration: 0.25,
                sustain: 0.25,
                sounds: true,
                pitch: pitch + f64::from(i % 8),
                amplitude: 0.7,
                tempo: 120.0,
            })
            .collect()
    }

    fn staves(parts: Vec<Part<'_>>) -> Staves<'_> {
        Staves {
            parts,
            domain: Domain::Time,
            palette: Mode::Light.colors().figure(),
        }
    }

    fn part<'a>(name: &'a str, score: &'a Score, events: &'a [Event]) -> Part<'a> {
        Part {
            name,
            score,
            events,
        }
    }

    #[test]
    fn scores_open_at_the_readable_scale() {
        let events = events(0.0);
        let score = Score::new(&events, Domain::Time);
        let staves = staves(vec![part("", &score, &events)]);
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
        let events = events(0.0);
        let score = Score::new(&events, Domain::Time);
        let program = staves(vec![part("", &score, &events)]);
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
    fn dragging_the_bar_moves_the_view() {
        let events = events(0.0);
        let score = Score::new(&events, Domain::Time);
        let program = staves(vec![part("", &score, &events)]);
        let bounds = Rectangle::new(Point::ORIGIN, Size::new(696.0, 200.0));
        let zoomed = Window {
            start: 0.0,
            end: 0.25,
        };
        let bar = Layout::new(&program, Some(zoomed), 696.0).bar_area();
        let press = canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left));
        let release = canvas::Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left));
        let moved = canvas::Event::Mouse(mouse::Event::CursorMoved {
            position: Point::new(bar.x + bar.width, bar.center_y()),
        });
        let middle = mouse::Cursor::Available(Point::new(bar.center_x(), bar.center_y()));
        let end = mouse::Cursor::Available(Point::new(bar.x + bar.width, bar.center_y()));

        // clicking the track puts the thumb under the pointer
        let mut state = State {
            window: Some(zoomed),
            ..State::default()
        };
        let action = canvas::Program::update(&program, &mut state, &press, bounds, middle);
        assert!(action.is_some(), "the bar takes the press");
        let window = state.window.expect("clicking the bar keeps a window");
        assert!(window.start > 0.0, "the view moved along");
        assert!((window.span() - zoomed.span()).abs() < 1e-12, "same scale");

        // and dragging it carries the view to the end
        canvas::Program::update(&program, &mut state, &moved, bounds, end);
        let dragged = state.window.expect("dragging the bar keeps a window");
        assert!(dragged.start > window.start, "the view followed the thumb");
        assert!((dragged.end - 1.0).abs() < 1e-12, "and stops at the end");

        // the drag ends with the button, so later moves are the figure's
        canvas::Program::update(&program, &mut state, &release, bounds, end);
        assert!(!state.bar.dragging());
    }

    #[test]
    fn hovering_finds_notes_and_not_the_clefs() {
        let events = events(0.0);
        let score = Score::new(&events, Domain::Time);
        let staves = staves(vec![part("", &score, &events)]);
        let layout = Layout::new(&staves, None, 696.0);
        let axis = layout.axis();
        let found = (0..score.height()).find_map(|row| {
            let at = Point::new(
                (axis.x(0.5) + 3) as f32 * LABEL_SCALE,
                row as f32 * LABEL_SCALE,
            );
            layout.note_at(at)
        });
        assert_eq!(found.map(|(_, note)| note.event), Some(2));
        assert!(layout.note_at(Point::new(5.0, 30.0)).is_none());
    }

    #[test]
    fn an_ensemble_stacks_its_textures() {
        let high = events(12.0);
        let low = events(-24.0);
        let (first, second) = (
            Score::new(&high, Domain::Time),
            Score::new(&low, Domain::Time),
        );
        let staves = staves(vec![part("a", &first, &high), part("bass", &second, &low)]);
        let layout = Layout::new(&staves, None, 696.0);

        assert!(layout.names_width() > 0.0, "the names take room");
        assert!(layout.part_top(0).abs() < f32::EPSILON);
        assert!(layout.part_top(1) >= part_height(&staves.parts[0]));
        assert!(plate_height(&staves.parts) > part_height(&staves.parts[0]));

        // a note of the second texture is found under the first one's staves
        let axis = layout.axis();
        let rows = (plate_height(&staves.parts) / LABEL_SCALE) as i32;
        let found = (0..rows).find_map(|row| {
            let at = Point::new(
                (axis.x(0.5) + 3) as f32 * LABEL_SCALE,
                row as f32 * LABEL_SCALE,
            );
            layout.note_at(at).filter(|&(index, _)| index == 1)
        });
        assert!(found.is_some(), "the lower texture's notes are hovered too");
    }

    #[test]
    fn event_mode_uses_slots() {
        let events = events(0.0);
        let score = Score::new(&events, Domain::Events);
        let mut staves = staves(vec![part("", &score, &events)]);
        staves.domain = Domain::Events;
        let axis = Layout::new(&staves, None, 696.0).axis();
        assert_eq!(axis.x(1.0) - axis.x(0.0), 16);
    }
}
