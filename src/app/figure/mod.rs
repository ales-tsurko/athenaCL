//! Interactive figures in the output, drawn in athenaCL's style and the app's colors.
//!
//! Figures span the output's width. ⌘-scroll zooms around the pointer, dragging (or scrolling
//! sideways) pans, and a double click shows the whole figure again. Labels are drawn in athenaCL's
//! bitmap font at the same size whatever the zoom, and axes relabel as it changes. A texture's
//! events can also be shown as a score.

mod automaton;
mod ensemble;
mod parameters;
mod score;

use std::{
    cell::Cell,
    time::{Duration, Instant},
};

use iced::{
    keyboard, mouse,
    widget::{
        self,
        canvas::{self, Frame},
    },
    Color, Element, Point, Rectangle, Size, Vector,
};

pub(crate) use self::score::{view as score, Part};
use crate::figure::{
    font::{Bitmap, Font},
    Figure,
};

/// Messages from figures.
#[derive(Debug, Clone, PartialEq)]
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

/// Show a figure `width` wide in `palette`, marking `active_texture` on ensemble timelines.
pub(crate) fn view<'a>(
    figure: &'a Figure,
    width: f32,
    active_texture: &'a str,
    palette: Palette,
) -> Element<'a, Message> {
    match figure {
        Figure::Parameters(parameters) => parameters::view(parameters, palette),
        Figure::Ensemble(ensemble) => ensemble::view(ensemble, active_texture, palette),
        Figure::Automaton(automaton) => automaton::view(automaton, width, palette),
    }
}

/// The colors figures are drawn in: the theme's.
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct Palette {
    /// Around the plates: the page.
    pub(crate) page: Color,
    /// Behind the data.
    pub(crate) plate: Color,
    /// Grid lines on the plate.
    pub(crate) grid: Color,
    /// Labeled grid lines on the plate.
    pub(crate) major: Color,
    /// Data on the plate: values, textures, notes.
    pub(crate) mark: Color,
    /// Secondary data on the plate: clones.
    pub(crate) alt: Color,
    /// What the pointer is over.
    pub(crate) hover: Color,
    /// Labels on the page: values, times, names.
    pub(crate) label: Color,
    /// Titles on the page.
    pub(crate) title: Color,
    /// Staff lines.
    pub(crate) staff: Color,
    /// The track of the bar showing the part in view.
    pub(crate) track: Color,
}

impl Palette {
    /// A shade from the page (0) to the labels' ink (1).
    fn shade(self, amount: f64) -> Color {
        let amount = amount.clamp(0.0, 1.0) as f32;
        let blend = |from: f32, to: f32| from + (to - from) * amount;
        Color::from_rgb(
            blend(self.page.r, self.label.r),
            blend(self.page.g, self.label.g),
            blend(self.page.b, self.label.b),
        )
    }
}

/// Forget what `cache` drew when the colors changed since: the theme was switched.
fn repaint(cache: &canvas::Cache, painted: &Cell<Option<Palette>>, palette: Palette) {
    if painted.replace(Some(palette)) != Some(palette) {
        cache.clear();
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

/// A float as an index: drawn things are placed by non-negative fractions of their whole extent,
/// so any negative value a rounding error could produce counts as zero rather than wrapping.
fn to_index(value: f64) -> usize {
    #[expect(
        clippy::cast_sign_loss,
        reason = "negative values are clamped away before the cast"
    )]
    let index = value.max(0.0) as usize;
    index
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
        // by whole powers: `powf` is only as exact as the platform's libm, and it can make a round
        // step come out as 0.20000000000000007
        let magnitude = power_of_ten(raw.log10().floor());
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
        let decimals = to_index((-self.step.log10().floor()).clamp(0.0, 6.0));
        let value = if value.abs() < self.step * 1e-9 {
            0.0
        } else {
            value
        };
        format!("{value:.decimals$}")
    }
}

/// Ten to a whole `exponent`, as exactly as f64 holds it.
///
/// Powers of ten come out of a multiplication, not the platform's `powf`: a tick step is a round
/// number, and the smallest error in the last bit shows up as `0.20000000000000007` in a label.
fn power_of_ten(exponent: f64) -> f64 {
    let steps = to_index(exponent.abs().min(308.0));
    let magnitude = (0..steps).fold(1.0, |power: f64, _| power * 10.0);
    if exponent < 0.0 {
        1.0 / magnitude
    } else {
        magnitude
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

/// The bar under a figure showing the part of its x axis in view.
const BAR_TRACK: f32 = 1.0;
const BAR_THUMB: f32 = 3.0;
/// How tall the bar's row is: the thumb, and room around it to grab.
const BAR_HEIGHT: f32 = 11.0;
/// The shortest the thumb gets, however far the figure is zoomed in.
const BAR_MIN: f32 = 2.0 * BAR_THUMB;

/// A figure's scrollbar: the bar under it showing the part of its x axis in view. Dragging it, or
/// clicking the track, moves the view.
#[derive(Debug, Default)]
struct Bar {
    /// Where the thumb was grabbed, as a fraction of its width.
    grabbed: Option<f32>,
}

impl Bar {
    /// The bar's row under a figure, across the `span` its axis is drawn over.
    fn area(span: Rectangle, top: f32) -> Rectangle {
        Rectangle::new(Point::new(span.x, top), Size::new(span.width, BAR_HEIGHT))
    }

    /// Where the thumb is in `area`.
    fn thumb(area: Rectangle, window: Window) -> Rectangle {
        let width = (window.span() as f32 * area.width).max(BAR_MIN);
        let left = (area.x + window.start as f32 * area.width).min(area.x + area.width - width);
        Rectangle::new(
            Point::new(left, area.y + (BAR_HEIGHT - BAR_THUMB) / 2.0),
            Size::new(width, BAR_THUMB),
        )
    }

    fn draw(frame: &mut Frame, area: Rectangle, window: Window, palette: Palette) {
        frame.fill_rectangle(
            Point::new(area.x, area.y + (BAR_HEIGHT - BAR_TRACK) / 2.0),
            Size::new(area.width, BAR_TRACK),
            palette.track,
        );
        let thumb = Self::thumb(area, window);
        frame.fill_rectangle(thumb.position(), thumb.size(), palette.label);
    }

    /// Handle an event over the bar, moving `window`: `None` when the event isn't the bar's,
    /// otherwise whether the window moved.
    fn update(
        &mut self,
        event: &canvas::Event,
        bounds: Rectangle,
        area: Rectangle,
        cursor: mouse::Cursor,
        window: &mut Window,
    ) -> Option<bool> {
        match event {
            canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)) => {
                let at = cursor.position_in(bounds)?;
                if !area.contains(at) {
                    return None;
                }
                let thumb = Self::thumb(area, *window);
                self.grabbed = Some(if thumb.contains(at) {
                    (at.x - thumb.x) / thumb.width
                } else {
                    0.5
                });
                let start = self.move_to(at.x, area, *window);
                Some(window.place(start, window.span()))
            }
            canvas::Event::Mouse(mouse::Event::CursorMoved { .. }) => {
                self.grabbed?;
                // the event is in window coordinates, while the bounds are the output's
                let at = cursor.position()? - (bounds.position() - Point::ORIGIN);
                let start = self.move_to(at.x, area, *window);
                Some(window.place(start, window.span()))
            }
            canvas::Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)) => {
                self.grabbed.take().map(|_| false)
            }
            _ => None,
        }
    }

    /// Where the window starts when the thumb is grabbed at `x`.
    fn move_to(&self, x: f32, area: Rectangle, window: Window) -> f64 {
        let grabbed = self.grabbed.unwrap_or(0.5);
        let width = (window.span() as f32 * area.width).max(BAR_MIN);
        let left = x - grabbed * width;
        f64::from((left - area.x) / area.width.max(1.0))
    }

    fn dragging(&self) -> bool {
        self.grabbed.is_some()
    }
}

/// The action for an event the bar took: it never passes through.
fn bar_action<Message>(changed: bool) -> Option<widget::Action<Message>> {
    Some(if changed {
        widget::Action::request_redraw().and_capture()
    } else {
        widget::Action::capture()
    })
}

/// What a pointer event asks of a figure.
#[derive(Debug, Clone, Copy, PartialEq)]
enum Gesture {
    /// Nothing: let the event through, so that scrolling scrolls the output.
    None,
    /// The pointer moved over the figure, which shows what it's over.
    Hover,
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
        match event {
            canvas::Event::Keyboard(keyboard::Event::ModifiersChanged(modifiers)) => {
                self.modifiers = *modifiers;
                Gesture::None
            }
            canvas::Event::Mouse(mouse::Event::WheelScrolled { delta }) => {
                let Some(at) = cursor.position_in(bounds) else {
                    return Gesture::None;
                };
                let (x, y) = match delta {
                    mouse::ScrollDelta::Lines { x, y } => (*x * LINE, *y * LINE),
                    mouse::ScrollDelta::Pixels { x, y } => (*x, *y),
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
                    return if cursor.is_over(bounds) {
                        Gesture::Hover
                    } else {
                        Gesture::None
                    };
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

/// The [`widget::Action`] for a gesture that changed the figure by `changed` and produced
/// `message`: publish the message, redraw the change, and stop the event here when the figure
/// handled it.
fn action<Message>(
    gesture: Gesture,
    changed: bool,
    message: Option<Message>,
) -> Option<widget::Action<Message>> {
    let captured = match gesture {
        Gesture::None | Gesture::Hover => false,
        // sideways scrolling passes through when there's nothing to pan
        Gesture::Pan {
            dragging: false, ..
        } => changed,
        _ => true,
    };
    let action = match message {
        Some(message) => Some(widget::Action::publish(message)),
        None if changed || gesture == Gesture::Hover => Some(widget::Action::request_redraw()),
        None if captured => Some(widget::Action::capture()),
        None => None,
    };

    if captured {
        action.map(widget::Action::and_capture)
    } else {
        action
    }
}

#[cfg(test)]
mod tests {
    #![expect(clippy::float_cmp, reason = "the tests assert exact tick values")]

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
        assert_eq!(
            window,
            Window {
                start: 0.125,
                end: 0.625
            }
        );
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
        assert_eq!(
            window,
            Window {
                start: 0.5,
                end: 1.0
            }
        );
        assert!(!window.pan(0.5));
        assert!(window.reset());
        assert_eq!(window, Window::default());
    }

    fn mouse_event(event: mouse::Event) -> canvas::Event {
        canvas::Event::Mouse(event)
    }

    #[test]
    fn actions_publish_capture_and_redraw() {
        use iced::{event, window};

        // clicks publish their message and capture the event
        let (message, _, status) = action(
            Gesture::Click(Point::ORIGIN),
            false,
            Some(Message::SelectTexture("texture".to_owned())),
        )
        .expect("clicks act")
        .into_inner();
        assert!(matches!(message, Some(Message::SelectTexture(_))));
        assert_eq!(status, event::Status::Captured);

        // interactive gestures that changed the figure capture it and redraw
        for gesture in [
            Gesture::Zoom {
                at: Point::ORIGIN,
                factor: 2.0,
            },
            Gesture::Pan {
                delta: Vector::new(1.0, 0.0),
                dragging: true,
            },
            Gesture::Reset,
        ] {
            let (_, redraw, status) = action::<Message>(gesture, true, None)
                .expect("changes act")
                .into_inner();
            assert_eq!(status, event::Status::Captured);
            assert!(matches!(redraw, window::RedrawRequest::NextFrame));
        }

        // presses capture the event without a message
        let (_, _, status) = action::<Message>(Gesture::Press, false, None)
            .expect("presses act")
            .into_inner();
        assert_eq!(status, event::Status::Captured);

        // sideways scrolling passes through when there is nothing to pan…
        let scrolled = Gesture::Pan {
            delta: Vector::new(1.0, 0.0),
            dragging: false,
        };
        assert!(action::<Message>(scrolled, false, None).is_none());
        // …but captures once it pans
        assert!(action::<Message>(scrolled, true, None).is_some());

        // nothing gestures only redraw changes
        assert!(action::<Message>(Gesture::None, false, None).is_none());
        assert!(action::<Message>(Gesture::None, true, None).is_some());
    }

    #[test]
    fn command_scrolling_zooms() {
        let mut pointer = Pointer::default();
        let at = mouse::Cursor::Available(Point::new(100.0, 550.0));
        let command = canvas::Event::Keyboard(keyboard::Event::ModifiersChanged(
            keyboard::Modifiers::COMMAND,
        ));
        let lines = mouse_event(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Lines { x: 0.0, y: -2.0 },
        });
        let pixels = mouse_event(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Pixels { x: 0.0, y: -80.0 },
        });

        assert_eq!(pointer.gesture(&command, scrolled(), at), Gesture::None);
        assert!(matches!(
            pointer.gesture(&lines, scrolled(), at),
            Gesture::Zoom { .. }
        ));
        assert!(matches!(
            pointer.gesture(&pixels, scrolled(), at),
            Gesture::Zoom { .. }
        ));
    }

    #[test]
    fn sideways_scrolling_pans() {
        let mut pointer = Pointer::default();
        let scroll = mouse_event(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Pixels { x: -40.0, y: 0.0 },
        });
        let at = mouse::Cursor::Available(Point::new(100.0, 550.0));

        assert_eq!(
            pointer.gesture(&scroll, scrolled(), at),
            Gesture::Pan {
                delta: Vector::new(-40.0, 0.0),
                dragging: false,
            }
        );
    }

    #[test]
    fn plain_vertical_scrolling_ignores() {
        let mut pointer = Pointer::default();
        let scroll = mouse_event(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Pixels { x: 0.0, y: -40.0 },
        });

        let outside = mouse::Cursor::Available(Point::new(100.0, 10.0));
        assert_eq!(pointer.gesture(&scroll, scrolled(), outside), Gesture::None);
        let inside = mouse::Cursor::Available(Point::new(100.0, 550.0));
        assert_eq!(pointer.gesture(&scroll, scrolled(), inside), Gesture::None);
    }

    #[test]
    fn moving_without_a_drag_hovers() {
        let mut pointer = Pointer::default();
        let moved = mouse_event(mouse::Event::CursorMoved {
            position: Point::new(100.0, 150.0),
        });
        let at = mouse::Cursor::Available(Point::new(100.0, 550.0));

        assert_eq!(pointer.gesture(&moved, scrolled(), at), Gesture::Hover);
    }

    #[test]
    fn moving_outside_ignores() {
        let mut pointer = Pointer::default();
        let moved = mouse_event(mouse::Event::CursorMoved {
            position: Point::new(100.0, 150.0),
        });
        let outside = mouse::Cursor::Available(Point::new(100.0, 50.0));

        assert_eq!(pointer.gesture(&moved, scrolled(), outside), Gesture::None);
    }

    #[test]
    fn double_clicks_reset() {
        let mut pointer = Pointer::default();
        let at = mouse::Cursor::Available(Point::new(100.0, 550.0));
        let press = mouse_event(mouse::Event::ButtonPressed(mouse::Button::Left));

        assert_eq!(pointer.gesture(&press, scrolled(), at), Gesture::Press);
        assert_eq!(pointer.gesture(&press, scrolled(), at), Gesture::Reset);
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
        assert_eq!(
            pointer.gesture(&release, scrolled(), at(130.0)),
            Gesture::Press
        );
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
