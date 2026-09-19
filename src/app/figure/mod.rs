//! Interactive figures in the output, drawn in athenaCL's style.
//!
//! Figures span the output's width. ⌘-scroll zooms around the pointer, dragging (or scrolling
//! sideways) pans, and a double click shows the whole figure again. Labels are drawn in athenaCL's
//! bitmap font at the same size whatever the zoom, and axes relabel as it changes.

mod automaton;
mod ensemble;
mod parameters;

use std::time::{Duration, Instant};

use iced::keyboard;
use iced::mouse;
use iced::widget::canvas::{self, Frame};
use iced::{Color, Element, Point, Rectangle, Size, Vector};

use crate::figure::font::{Bitmap, Font};
use crate::figure::{Figure, Rgb};

/// Messages from figures.
#[derive(Debug, Clone)]
pub enum Message {
    /// A texture was clicked on the ensemble timeline.
    SelectTexture(String),
    /// A clone was clicked on the ensemble timeline.
    SelectClone {
        /// The clone's texture.
        texture: String,
        /// The clone.
        clone: String,
    },
}

/// Show a figure `width` wide, marking `active_texture` on ensemble timelines.
pub(crate) fn view<'a>(
    figure: &'a Figure,
    width: f32,
    active_texture: &'a str,
) -> Element<'a, Message> {
    match figure {
        Figure::Parameters(parameters) => parameters::view(parameters),
        Figure::Ensemble(ensemble) => ensemble::view(ensemble, active_texture),
        Figure::Automaton(automaton) => automaton::view(automaton, width),
    }
}

/// Screen pixels per font pixel: half again athenaCL's size, which is three device pixels per font
/// pixel on a Retina display.
const LABEL_SCALE: f32 = 1.5;
/// The height of a line of labels: the micro font's 7 pixel cells, at label scale.
const LABEL_HEIGHT: f32 = 7.0 * LABEL_SCALE;
/// Empty columns between characters, as in athenaCL's graphs.
const KERN: usize = 1;
/// Scroll distance of a mouse wheel notch, in pixels.
const LINE: f32 = 40.0;
/// How much scrolling zooms: a notch zooms by about a fifth.
const ZOOM_SPEED: f32 = 0.005;
/// How far a press can move and still be a click.
const CLICK_DISTANCE: f32 = 3.0;
/// How soon a second press makes a double click.
const DOUBLE_CLICK: Duration = Duration::from_millis(300);

fn color(Rgb(r, g, b): Rgb) -> Color {
    Color::from_rgb8(r, g, b)
}

/// Fill the part of `area` inside `clip`.
fn fill(frame: &mut Frame, area: Rectangle, clip: Rectangle, color: Color) {
    if let Some(area) = area.intersection(&clip) {
        frame.fill_rectangle(area.position(), area.size(), color);
    }
}

/// A frame `thickness` wide just inside `area`, clipped to `clip`.
fn outline(frame: &mut Frame, area: Rectangle, clip: Rectangle, thickness: f32, color: Color) {
    let Rectangle {
        x,
        y,
        width,
        height,
    } = area;
    let sides = [
        Rectangle::new(Point::new(x, y), Size::new(width, thickness)),
        Rectangle::new(
            Point::new(x, y + height - thickness),
            Size::new(width, thickness),
        ),
        Rectangle::new(Point::new(x, y), Size::new(thickness, height)),
        Rectangle::new(
            Point::new(x + width - thickness, y),
            Size::new(thickness, height),
        ),
    ];
    for side in sides {
        fill(frame, side, clip, color);
    }
}

/// Text in athenaCL's micro font, at the label size.
struct Label(Bitmap);

impl Label {
    fn new(text: &str) -> Self {
        Self(Font::Micro.render(text, KERN))
    }

    fn width(&self) -> f32 {
        self.0.width() as f32 * LABEL_SCALE
    }

    /// The height of a line of labels.
    fn height() -> f32 {
        LABEL_HEIGHT
    }

    /// The area the label covers when drawn with its `anchor` at `at`.
    fn bounds(&self, at: Point, anchor: Anchor) -> Rectangle {
        let (x, y) = anchor.offset(self.0.width(), self.0.height());
        Rectangle::new(
            Point::new(
                at.x.round() + x * LABEL_SCALE,
                at.y.round() + y * LABEL_SCALE,
            ),
            Size::new(self.width(), self.0.height() as f32 * LABEL_SCALE),
        )
    }

    fn draw(&self, frame: &mut Frame, at: Point, anchor: Anchor, color: Color) {
        let origin = self.bounds(at, anchor).position();
        for (y, x, length) in self.0.runs() {
            frame.fill_rectangle(
                origin + Vector::new(x as f32, y as f32) * LABEL_SCALE,
                Size::new(length as f32 * LABEL_SCALE, LABEL_SCALE),
                color,
            );
        }
    }

    /// Draw on a patch of `background`, so it reads over whatever is behind it.
    fn draw_on(
        &self,
        frame: &mut Frame,
        at: Point,
        anchor: Anchor,
        color: Color,
        background: Color,
    ) {
        let bounds = self.bounds(at, anchor).expand(LABEL_SCALE * 2.0);
        frame.fill_rectangle(bounds.position(), bounds.size(), background);
        self.draw(frame, at, anchor, color);
    }
}

/// Which point of a label is placed at its position, as in athenaCL's `gridText`.
#[derive(Debug, Clone, Copy)]
enum Anchor {
    NorthWest,
    NorthCenter,
    NorthEast,
    CenterWest,
    CenterEast,
}

impl Anchor {
    /// Offset of the label's top-left corner from its anchor, in font pixels, as athenaCL
    /// computes it.
    fn offset(self, width: usize, height: usize) -> (f32, f32) {
        // athenaCL's `_gridCenter`: half, rounded half to even, less one
        let center = |length: usize| (length as f64 * 0.5).round_ties_even() as f32 - 1.0;
        match self {
            Self::NorthWest => (0.0, 0.0),
            Self::NorthCenter => (-center(width), 0.0),
            Self::NorthEast => (-(width as f32), 0.0),
            Self::CenterWest => (0.0, -center(height)),
            Self::CenterEast => (-(width as f32), -center(height)),
        }
    }
}

/// Round values across a range, for axis labels.
#[derive(Debug, Clone, PartialEq)]
struct Ticks {
    step: f64,
    values: Vec<f64>,
}

impl Ticks {
    /// At most about `count` values across `min..=max`, in steps of 1, 2 or 5 times a power of ten,
    /// and no finer than `min_step`.
    fn new(min: f64, max: f64, count: usize, min_step: f64) -> Self {
        let span = max - min;
        if !(span > 0.0 && span.is_finite()) {
            return Self {
                step: min_step,
                values: vec![min],
            };
        }
        let raw = span / count.max(1) as f64;
        let magnitude = 10f64.powf(raw.log10().floor());
        let step = [1.0, 2.0, 5.0, 10.0]
            .into_iter()
            .map(|multiple| multiple * magnitude)
            .find(|&step| step >= raw * (1.0 - 1e-9))
            .unwrap_or(10.0 * magnitude)
            .max(min_step);
        let first = (min / step).ceil();
        let values = (0..)
            .map(|i| (first + i as f64) * step)
            .take_while(|&value| value <= max + step * 1e-9)
            .collect();
        Self { step, values }
    }

    /// A value with as many decimals as the step needs.
    fn format(&self, value: f64) -> String {
        let decimals = (-self.step.log10().floor()).clamp(0.0, 6.0) as usize;
        let value = if value.abs() < self.step * 1e-9 {
            0.0
        } else {
            value
        };
        format!("{value:.decimals$}")
    }
}

/// A value as athenaCL prints graph values: at most four decimals.
fn format_value(value: f64) -> String {
    let text = format!("{value:.4}");
    let text = text.trim_end_matches('0').trim_end_matches('.');
    if text == "-0" {
        "0".to_owned()
    } else {
        text.to_owned()
    }
}

/// The visible part of an axis, as fractions of its whole extent.
#[derive(Debug, Clone, Copy, PartialEq)]
struct Window {
    start: f64,
    end: f64,
}

impl Default for Window {
    fn default() -> Self {
        Self {
            start: 0.0,
            end: 1.0,
        }
    }
}

impl Window {
    fn span(self) -> f64 {
        self.end - self.start
    }

    /// Zoom by `factor` (more than 1 zooms in), keeping the point at `anchor`, a fraction of the
    /// visible part, where it is. It zooms no further in than showing `min_span`.
    fn zoom(&mut self, anchor: f64, factor: f64, min_span: f64) -> bool {
        let fixed = self.whole(anchor);
        let span = (self.span() / factor).clamp(min_span.min(1.0), 1.0);
        self.place(fixed - anchor * span, span)
    }

    /// Move by `delta`, a fraction of the visible part.
    fn pan(&mut self, delta: f64) -> bool {
        self.place(self.start + delta * self.span(), self.span())
    }

    fn reset(&mut self) -> bool {
        self.place(0.0, 1.0)
    }

    fn place(&mut self, start: f64, span: f64) -> bool {
        let start = start.clamp(0.0, 1.0 - span);
        let placed = Self {
            start,
            end: start + span,
        };
        let changed =
            (placed.start - self.start).abs() > 1e-12 || (placed.end - self.end).abs() > 1e-12;
        *self = placed;
        changed
    }

    /// Where a fraction of the visible part is in the whole extent.
    fn whole(self, fraction: f64) -> f64 {
        self.start + fraction * self.span()
    }
}

/// What a pointer event asks of a figure.
#[derive(Debug, Clone, Copy, PartialEq)]
enum Gesture {
    /// Nothing: let the event through, so that scrolling scrolls the output.
    None,
    /// A press, which may become a click or a drag.
    Press,
    /// Zoom by `factor` (more than 1 zooms in) around `at`.
    Zoom { at: Point, factor: f32 },
    /// Move the content by a distance in pixels.
    Pan { delta: Vector, dragging: bool },
    /// Show everything.
    Reset,
    /// A press and release in place.
    Click(Point),
}

/// Pointer state, turning events into gestures.
#[derive(Debug, Default)]
struct Pointer {
    modifiers: keyboard::Modifiers,
    drag: Option<Drag>,
    last_press: Option<(Instant, Point)>,
}

#[derive(Debug, Clone, Copy)]
struct Drag {
    origin: Point,
    last: Point,
    moved: bool,
}

impl Pointer {
    fn gesture(
        &mut self,
        event: &canvas::Event,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Gesture {
        match *event {
            canvas::Event::Keyboard(keyboard::Event::ModifiersChanged(modifiers)) => {
                self.modifiers = modifiers;
                Gesture::None
            }
            canvas::Event::Mouse(mouse::Event::WheelScrolled { delta }) => {
                let Some(at) = cursor.position_in(bounds) else {
                    return Gesture::None;
                };
                let (x, y) = match delta {
                    mouse::ScrollDelta::Lines { x, y } => (x * LINE, y * LINE),
                    mouse::ScrollDelta::Pixels { x, y } => (x, y),
                };
                if self.modifiers.command() {
                    Gesture::Zoom {
                        at,
                        factor: (y * ZOOM_SPEED).exp(),
                    }
                } else if x.abs() > y.abs() {
                    Gesture::Pan {
                        delta: Vector::new(x, 0.0),
                        dragging: false,
                    }
                } else {
                    Gesture::None
                }
            }
            canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)) => {
                let Some(at) = cursor.position_in(bounds) else {
                    return Gesture::None;
                };
                let now = Instant::now();
                let double = self.last_press.is_some_and(|(time, position)| {
                    now - time < DOUBLE_CLICK && position.distance(at) <= CLICK_DISTANCE
                });
                if double {
                    self.last_press = None;
                    self.drag = None;
                    return Gesture::Reset;
                }
                self.last_press = Some((now, at));
                self.drag = Some(Drag {
                    origin: at,
                    last: at,
                    moved: false,
                });
                Gesture::Press
            }
            canvas::Event::Mouse(mouse::Event::CursorMoved { .. }) => {
                let Some(drag) = &mut self.drag else {
                    return Gesture::None;
                };
                // the event is in window coordinates, while the cursor, like the bounds, is
                // translated by the scrolling of the output
                let Some(position) = cursor.position() else {
                    return Gesture::Press;
                };
                let at = position - (bounds.position() - Point::ORIGIN);
                drag.moved |= at.distance(drag.origin) > CLICK_DISTANCE;
                let delta = at - drag.last;
                drag.last = at;
                if drag.moved {
                    Gesture::Pan {
                        delta,
                        dragging: true,
                    }
                } else {
                    Gesture::Press
                }
            }
            canvas::Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)) => {
                match self.drag.take() {
                    Some(drag) if !drag.moved => Gesture::Click(drag.origin),
                    Some(_) => Gesture::Press,
                    None => Gesture::None,
                }
            }
            _ => Gesture::None,
        }
    }

    fn dragging(&self) -> bool {
        self.drag.is_some_and(|drag| drag.moved)
    }
}

/// Whether a gesture that changed the figure by `changed` should stop the event here.
fn status(gesture: Gesture, changed: bool) -> canvas::event::Status {
    let captured = match gesture {
        Gesture::None => false,
        // sideways scrolling passes through when there's nothing to pan
        Gesture::Pan {
            dragging: false, ..
        } => changed,
        _ => true,
    };
    if captured {
        canvas::event::Status::Captured
    } else {
        canvas::event::Status::Ignored
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ticks_use_round_steps() {
        let ticks = Ticks::new(0.0, 119.0, 6, 1.0);
        assert_eq!(ticks.step, 20.0);
        assert_eq!(ticks.values, [0.0, 20.0, 40.0, 60.0, 80.0, 100.0]);

        let ticks = Ticks::new(0.0043, 0.8192, 5, 0.0);
        assert_eq!(ticks.step, 0.2);
        assert_eq!(ticks.values.len(), 4);
        assert_eq!(ticks.format(ticks.values[0]), "0.2");
    }

    #[test]
    fn ticks_respect_the_minimum_step() {
        let ticks = Ticks::new(3.2, 5.6, 20, 1.0);
        assert_eq!(ticks.step, 1.0);
        assert_eq!(ticks.values, [4.0, 5.0]);
        assert_eq!(ticks.format(4.0), "4");
    }

    #[test]
    fn ticks_of_an_empty_range() {
        assert_eq!(Ticks::new(2.0, 2.0, 5, 1.0).values, [2.0]);
    }

    #[test]
    fn tick_labels_have_the_decimals_the_step_needs() {
        let ticks = Ticks::new(-0.1, 0.1, 4, 0.0);
        assert_eq!(ticks.step, 0.05);
        assert_eq!(ticks.format(-0.0), "0.00");
        assert_eq!(ticks.format(0.05), "0.05");
    }

    #[test]
    fn values_print_like_athenacl() {
        assert_eq!(format_value(0.81923), "0.8192");
        assert_eq!(format_value(0.664), "0.664");
        assert_eq!(format_value(120.0), "120");
        assert_eq!(format_value(-0.00001), "0");
    }

    #[test]
    fn zooming_keeps_the_anchor_in_place() {
        let mut window = Window::default();
        assert!(window.zoom(0.25, 2.0, 0.01));
        assert_eq!(window, Window { start: 0.125, end: 0.625 });
        assert_eq!(window.whole(0.25), 0.25);
    }

    #[test]
    fn zooming_stops_at_the_limits() {
        let mut window = Window::default();
        assert!(!window.zoom(0.5, 0.5, 0.01), "already showing everything");
        window.zoom(0.5, 1000.0, 0.1);
        assert!((window.span() - 0.1).abs() < 1e-12);
        assert!(!window.zoom(0.5, 2.0, 0.1));
    }

    #[test]
    fn panning_stays_inside() {
        let mut window = Window {
            start: 0.25,
            end: 0.75,
        };
        assert!(window.pan(1.0));
        assert_eq!(window, Window { start: 0.5, end: 1.0 });
        assert!(!window.pan(0.5));
        assert!(window.reset());
        assert_eq!(window, Window::default());
    }

    fn mouse_event(event: mouse::Event) -> canvas::Event {
        canvas::Event::Mouse(event)
    }

    /// A figure lower in the scrolled output: its bounds and the cursor are in the output's content
    /// coordinates, while pointer events are in window coordinates.
    fn scrolled() -> Rectangle {
        Rectangle::new(Point::new(0.0, 500.0), Size::new(680.0, 100.0))
    }

    #[test]
    fn clicks_inside_the_scrolled_output() {
        let mut pointer = Pointer::default();
        let cursor = mouse::Cursor::Available(Point::new(100.0, 550.0));
        let press = mouse_event(mouse::Event::ButtonPressed(mouse::Button::Left));
        // winit reports where the pointer is before a release, in window coordinates
        let moved = mouse_event(mouse::Event::CursorMoved {
            position: Point::new(100.0, 150.0),
        });
        let release = mouse_event(mouse::Event::ButtonReleased(mouse::Button::Left));
        assert_eq!(pointer.gesture(&press, scrolled(), cursor), Gesture::Press);
        assert_eq!(pointer.gesture(&moved, scrolled(), cursor), Gesture::Press);
        assert_eq!(
            pointer.gesture(&release, scrolled(), cursor),
            Gesture::Click(Point::new(100.0, 50.0))
        );
    }

    #[test]
    fn dragging_pans_by_the_pointer_movement() {
        let mut pointer = Pointer::default();
        let at = |x| mouse::Cursor::Available(Point::new(x, 550.0));
        let moved = mouse_event(mouse::Event::CursorMoved {
            position: Point::new(0.0, 0.0),
        });
        let press = mouse_event(mouse::Event::ButtonPressed(mouse::Button::Left));
        pointer.gesture(&press, scrolled(), at(100.0));
        let pan = |delta| Gesture::Pan {
            delta: Vector::new(delta, 0.0),
            dragging: true,
        };
        assert_eq!(pointer.gesture(&moved, scrolled(), at(110.0)), pan(10.0));
        assert_eq!(pointer.gesture(&moved, scrolled(), at(130.0)), pan(20.0));
        let release = mouse_event(mouse::Event::ButtonReleased(mouse::Button::Left));
        assert_eq!(pointer.gesture(&release, scrolled(), at(130.0)), Gesture::Press);
    }

    #[test]
    fn label_height_is_the_micro_cell() {
        assert_eq!(Font::Micro.cell().1 as f32 * LABEL_SCALE, LABEL_HEIGHT);
    }

    #[test]
    fn anchors_follow_athenacl() {
        // micro text is 7 pixels high: centered, its fourth row is on the anchor
        assert_eq!(Anchor::CenterWest.offset(9, 7), (0.0, -3.0));
        assert_eq!(Anchor::NorthCenter.offset(9, 7), (-3.0, 0.0));
        assert_eq!(Anchor::NorthEast.offset(9, 7), (-9.0, 0.0));
    }
}
