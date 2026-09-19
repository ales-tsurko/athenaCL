//! Parameter values over events or time: `TPmap`, `TImap` and `TCmap`.
//!
//! Graphs are stacked and share the x axis. Hovering shows the value under the pointer in every
//! graph.

use std::cell::Cell;

use iced::{
    mouse,
    widget::{
        self,
        canvas::{self, Canvas, Frame},
    },
    Element, Length, Point, Rectangle, Renderer, Size, Theme,
};

use super::{
    action, fill, format_value, repaint, to_index, Anchor, Gesture, Label, Message, Palette,
    Pointer, Ticks, Window,
};
use crate::figure::{Domain, Graph, Mark, Parameters};

/// Room for value labels, left of the graphs.
const LEFT: f32 = 60.0;
const RIGHT: f32 = 6.0;
const TOP: f32 = 4.0;
/// Space between a graph and its labels, and below them.
const GUTTER: f32 = 4.0;
/// Space between graphs.
const GAP: f32 = 4.0;
/// Graph height when showing a few parameters in detail (`TPmap`)…
const DETAILED: f32 = 144.0;
/// …and when showing all of a texture's parameters.
const COMPACT: f32 = 48.0;
/// Height of a value's mark.
const MARK: f32 = 2.0;
/// Pixels per x axis label.
const X_LABEL_SPACING: f32 = 64.0;
/// The fewest events, or seconds, to zoom in to.
const MIN_EVENTS: f64 = 4.0;
const MIN_SECONDS: f64 = 0.1;

pub(super) fn view(parameters: &Parameters, palette: Palette) -> Element<'_, Message> {
    Canvas::new(Plot {
        parameters,
        palette,
    })
    .width(Length::Fill)
    .height(height(parameters))
    .into()
}

fn graph_height(parameters: &Parameters) -> f32 {
    if parameters.detailed {
        DETAILED
    } else {
        COMPACT
    }
}

fn block_height(parameters: &Parameters) -> f32 {
    TOP + graph_height(parameters) + GUTTER + 2.0 * Label::height() + GUTTER
}

fn height(parameters: &Parameters) -> f32 {
    let count = parameters.graphs.len() as f32;
    (count * block_height(parameters) + (count - 1.0) * GAP).max(0.0)
}

struct Plot<'a> {
    parameters: &'a Parameters,
    palette: Palette,
}

#[derive(Debug, Default)]
struct State {
    pointer: Pointer,
    window: Window,
    cache: canvas::Cache,
    painted: Cell<Option<Palette>>,
}

impl canvas::Program<Message> for Plot<'_> {
    type State = State;

    fn update(
        &self,
        state: &mut State,
        event: &canvas::Event,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Option<widget::Action<Message>> {
        let gesture = state.pointer.gesture(event, bounds, cursor);
        let layout = Layout::new(self.parameters, self.palette, state.window, bounds.width);
        let plot = layout.plot(0);
        let changed = match gesture {
            Gesture::Zoom { at, factor } => {
                let anchor = ((at.x - plot.x) / plot.width).clamp(0.0, 1.0);
                state
                    .window
                    .zoom(f64::from(anchor), f64::from(factor), layout.min_span())
            }
            Gesture::Pan { delta, .. } => state.window.pan(f64::from(-delta.x / plot.width)),
            Gesture::Reset => state.window.reset(),
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
        let layout = Layout::new(self.parameters, self.palette, state.window, bounds.width);
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
        let layout = Layout::new(self.parameters, self.palette, state.window, bounds.width);
        match cursor.position_in(bounds) {
            Some(at) if layout.over_graphs(at) => mouse::Interaction::Crosshair,
            _ => mouse::Interaction::default(),
        }
    }
}

/// Where everything is, for a width and zoom.
struct Layout<'a> {
    parameters: &'a Parameters,
    palette: Palette,
    width: f32,
    /// The whole x axis.
    extent: (f64, f64),
    /// Its visible part.
    visible: (f64, f64),
}

impl<'a> Layout<'a> {
    fn new(parameters: &'a Parameters, palette: Palette, window: Window, width: f32) -> Self {
        let extent = extent(parameters);
        let span = extent.1 - extent.0;
        Self {
            parameters,
            palette,
            width,
            extent,
            visible: (extent.0 + window.start * span, extent.0 + window.end * span),
        }
    }

    /// The narrowest visible part, as a fraction of the whole axis.
    fn min_span(&self) -> f64 {
        let min = match self.parameters.domain {
            Domain::Events => MIN_EVENTS,
            Domain::Time => MIN_SECONDS,
        };
        min / (self.extent.1 - self.extent.0)
    }

    /// The area of the graph at `index`, with its labels.
    fn block(&self, index: usize) -> Rectangle {
        let height = block_height(self.parameters);
        Rectangle::new(
            Point::new(0.0, index as f32 * (height + GAP)),
            Size::new(self.width, height),
        )
    }

    /// Where the graph at `index` plots values.
    fn plot(&self, index: usize) -> Rectangle {
        let block = self.block(index);
        Rectangle::new(
            Point::new(LEFT, block.y + TOP),
            Size::new(
                (self.width - LEFT - RIGHT).max(1.0),
                graph_height(self.parameters),
            ),
        )
    }

    /// The top of the labels under a plot: the units, then the title.
    fn units_y(plot: Rectangle) -> f32 {
        plot.y + plot.height + GUTTER
    }

    fn caption_y(plot: Rectangle) -> f32 {
        Self::units_y(plot) + Label::height()
    }

    fn over_graphs(&self, at: Point) -> bool {
        let plot = self.plot(0);
        at.x >= plot.x && at.x < plot.x + plot.width
    }

    fn x(&self, value: f64, plot: Rectangle) -> f32 {
        let (start, end) = self.visible;
        plot.x + ((value - start) / (end - start)) as f32 * plot.width
    }

    fn x_value(&self, x: f32, plot: Rectangle) -> f64 {
        let (start, end) = self.visible;
        start + f64::from((x - plot.x) / plot.width) * (end - start)
    }

    /// Where a value is, in a plot showing the values `range`. Marks at the extremes stay
    /// inside the plot.
    fn y(value: f64, (low, high): (f64, f64), plot: Rectangle) -> f32 {
        let fraction = ((value - low) / (high - low)) as f32;
        (plot.y + MARK + (1.0 - fraction) * (plot.height - 2.0 * MARK)).round()
    }

    /// The mark of a value: a dash for an event, as athenaCL draws them, or a bar across its
    /// time span.
    fn mark_area(&self, mark: &Mark, range: (f64, f64), plot: Rectangle) -> Rectangle {
        let y = Self::y(mark.value, range, plot);
        let (left, right) = match self.parameters.domain {
            Domain::Events => {
                let spacing = plot.width / (self.visible.1 - self.visible.0) as f32;
                let width = (spacing * 0.75).floor().max(1.0);
                let left = (self.x(mark.start, plot) - width / 2.0).round();
                (left, left + width)
            }
            Domain::Time => {
                let left = self.x(mark.start, plot).round();
                (left, self.x(mark.end, plot).round().max(left + 1.0))
            }
        };
        Rectangle::new(
            Point::new(left, y - MARK / 2.0),
            Size::new(right - left, MARK),
        )
    }

    fn visible_marks<'g>(&self, graph: &'g Graph) -> impl Iterator<Item = &'g Mark> {
        let (start, end) = self.visible;
        graph
            .marks
            .iter()
            .filter(move |mark| mark.end >= start - 1.0 && mark.start <= end + 1.0)
    }

    /// The range of values to show: that of the visible marks, so zooming in shows detail.
    fn value_range(&self, graph: &Graph) -> (f64, f64) {
        let (start, end) = self.visible;
        let shown = graph
            .marks
            .iter()
            .filter(|mark| mark.end >= start && mark.start <= end);
        let (low, high) = min_max(shown)
            .or_else(|| min_max(graph.marks.iter()))
            .unwrap_or((0.0, 1.0));
        if high > low {
            (low, high)
        } else {
            (low - 1.0, high + 1.0)
        }
    }

    /// The mark under `x`: the nearest event, or the time span around it.
    fn mark_at<'g>(&self, graph: &'g Graph, x: f64) -> Option<&'g Mark> {
        let distance = |mark: &&Mark| {
            if x < mark.start {
                mark.start - x
            } else if x > mark.end {
                x - mark.end
            } else {
                0.0
            }
        };
        graph
            .marks
            .iter()
            .min_by(|a, b| distance(a).total_cmp(&distance(b)))
    }

    fn draw(&self, frame: &mut Frame) {
        let palette = self.palette;
        for (index, graph) in self.parameters.graphs.iter().enumerate() {
            let block = self.block(index);
            frame.fill_rectangle(block.position(), block.size(), palette.page);
            let plot = self.plot(index);
            frame.fill_rectangle(plot.position(), plot.size(), palette.plate);

            let range = self.value_range(graph);
            self.draw_values(frame, plot, range);
            self.draw_times(frame, plot);
            self.draw_marks(graph, frame, plot, range);

            Label::new(&graph.title).draw(
                frame,
                Point::new(block.width - RIGHT, Self::caption_y(plot)),
                Anchor::NorthEast,
                palette.title,
            );
        }
    }

    /// Value grid lines with their labels, left of the plot.
    fn draw_values(&self, frame: &mut Frame, plot: Rectangle, range: (f64, f64)) {
        let palette = self.palette;
        let count = to_index(f64::from(
            (plot.height - 2.0 * MARK) / (Label::height() + 8.0),
        ));
        let ticks = Ticks::new(range.0, range.1, count.max(2), 0.0);
        for &value in &ticks.values {
            let y = Self::y(value, range, plot);
            let line = Rectangle::new(Point::new(plot.x, y), Size::new(plot.width, 1.0));
            fill(frame, line, plot, palette.grid);
            Label::new(&ticks.format(value)).draw(
                frame,
                Point::new(plot.x - GUTTER, y),
                Anchor::CenterEast,
                palette.label,
            );
        }
    }

    /// Time grid lines with their labels, under the plot.
    fn draw_times(&self, frame: &mut Frame, plot: Rectangle) {
        let min_step = match self.parameters.domain {
            Domain::Events => 1.0,
            Domain::Time => 0.001,
        };
        let count = to_index(f64::from(plot.width / X_LABEL_SPACING));
        let ticks = Ticks::new(self.visible.0, self.visible.1, count.max(2), min_step);
        for &value in &ticks.values {
            let x = self.x(value, plot).round();
            let line = Rectangle::new(Point::new(x, plot.y), Size::new(1.0, plot.height));
            fill(frame, line, plot, self.palette.grid);
            self.draw_time_label(frame, value, &ticks, plot);
        }
    }

    /// A time's label, when it fits on screen.
    fn draw_time_label(&self, frame: &mut Frame, value: f64, ticks: &Ticks, plot: Rectangle) {
        let label = Label::new(&ticks.format(value));
        let at = Point::new(self.x(value, plot).round(), Self::units_y(plot));
        let bounds = label.bounds(at, Anchor::NorthCenter);
        if bounds.x >= 0.0 && bounds.x + bounds.width <= self.width {
            label.draw(frame, at, Anchor::NorthCenter, self.palette.label);
        }
    }

    /// The marks of `graph`, as bars across their spans of the x axis.
    fn draw_marks(&self, graph: &Graph, frame: &mut Frame, plot: Rectangle, range: (f64, f64)) {
        for mark in self.visible_marks(graph) {
            let area = self.mark_area(mark, range, plot);
            fill(frame, area, plot, self.palette.mark);
        }
    }

    /// A line through the value under the pointer in every graph, and the value itself.
    fn draw_hover(&self, frame: &mut Frame, at: Point) {
        if !self.over_graphs(at) {
            return;
        }
        let palette = self.palette;
        let x = self.x_value(at.x, self.plot(0));
        for (index, graph) in self.parameters.graphs.iter().enumerate() {
            let Some(mark) = self.mark_at(graph, x) else {
                continue;
            };
            let plot = self.plot(index);
            let range = self.value_range(graph);
            let line_x = match self.parameters.domain {
                Domain::Events => self.x(mark.start, plot).round(),
                Domain::Time => at.x.round(),
            };
            let line = Rectangle::new(Point::new(line_x, plot.y), Size::new(1.0, plot.height));
            fill(frame, line, plot, palette.hover);
            let area = self.mark_area(mark, range, plot).expand(1.0);
            fill(frame, area, plot, palette.mark);

            let text = match self.parameters.domain {
                Domain::Events => format!("{}: {}", mark.start, format_value(mark.value)),
                Domain::Time => format!(
                    "{}-{}: {}",
                    format_value(mark.start),
                    format_value(mark.end),
                    format_value(mark.value)
                ),
            };
            Label::new(&text).draw_on(
                frame,
                Point::new(plot.x, Self::caption_y(plot)),
                Anchor::NorthWest,
                palette.label,
                palette.page,
            );
        }
    }
}

/// The span of the x axis: from the first to the last event, or the whole time.
fn extent(parameters: &Parameters) -> (f64, f64) {
    let marks = parameters.graphs.iter().flat_map(|graph| &graph.marks);
    let (min, max) = marks.fold((f64::INFINITY, f64::NEG_INFINITY), |(min, max), mark| {
        (min.min(mark.start), max.max(mark.end))
    });
    if !(min.is_finite() && max.is_finite()) {
        return (0.0, 1.0);
    }
    match parameters.domain {
        // each event takes a column, centered on its number
        Domain::Events => (min - 0.5, max + 0.5),
        Domain::Time if max > min => (min, max),
        Domain::Time => (min, min + 1.0),
    }
}

fn min_max<'m>(marks: impl Iterator<Item = &'m Mark>) -> Option<(f64, f64)> {
    marks.fold(None, |range, mark| {
        let (low, high) = range.unwrap_or((mark.value, mark.value));
        Some((low.min(mark.value), high.max(mark.value)))
    })
}

#[cfg(test)]
mod tests {
    #![expect(clippy::float_cmp, reason = "the tests assert exact float values")]

    use iced::keyboard;

    use super::*;
    use crate::app::theme::Mode;

    fn palette() -> Palette {
        Mode::Light.colors().figure()
    }

    fn parameters(domain: Domain, marks: Vec<Mark>) -> Parameters {
        Parameters {
            domain,
            detailed: true,
            graphs: vec![Graph {
                title: "amplitude: randomUniform".to_owned(),
                marks,
            }],
            events: Vec::new(),
        }
    }

    fn events(values: &[f64]) -> Vec<Mark> {
        values
            .iter()
            .enumerate()
            .map(|(i, &value)| Mark {
                start: i as f64,
                end: i as f64,
                value,
            })
            .collect()
    }

    #[test]
    fn zooming_and_resetting_reach_the_window() {
        let parameters = parameters(Domain::Time, events(&[0.0, 1.0, 5.0, 2.0, 3.0]));
        let program = Plot {
            parameters: &parameters,
            palette: palette(),
        };
        let bounds = Rectangle::new(Point::ORIGIN, Size::new(680.0, 300.0));
        let at = mouse::Cursor::Available(Point::new(300.0, 150.0));
        let command = canvas::Event::Keyboard(keyboard::Event::ModifiersChanged(
            keyboard::Modifiers::COMMAND,
        ));
        let zoom = canvas::Event::Mouse(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Pixels { x: 0.0, y: 60.0 },
        });
        let press = canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left));

        let mut state = State::default();
        canvas::Program::update(&program, &mut state, &command, bounds, at);
        canvas::Program::update(&program, &mut state, &zoom, bounds, at);
        assert!(state.window.span() < 1.0);

        // a double click shows everything again
        canvas::Program::update(&program, &mut state, &press, bounds, at);
        canvas::Program::update(&program, &mut state, &press, bounds, at);
        assert_eq!(state.window, Window::default());
    }

    #[test]
    fn events_are_centered_in_columns() {
        let parameters = parameters(Domain::Events, events(&[0.0; 10]));
        assert_eq!(extent(&parameters), (-0.5, 9.5));
    }

    #[test]
    fn values_fit_what_is_visible() {
        let parameters = parameters(Domain::Events, events(&[0.0, 1.0, 5.0, 2.0, 3.0]));
        let whole = Layout::new(&parameters, palette(), Window::default(), 680.0);
        assert_eq!(whole.value_range(&parameters.graphs[0]), (0.0, 5.0));

        // the first two events
        let mut window = Window::default();
        window.zoom(0.0, 2.5, 0.0);
        let zoomed = Layout::new(&parameters, palette(), window, 680.0);
        assert_eq!(zoomed.value_range(&parameters.graphs[0]), (0.0, 1.0));
    }

    #[test]
    fn constant_values_get_a_range() {
        let parameters = parameters(Domain::Events, events(&[120.0, 120.0]));
        let layout = Layout::new(&parameters, palette(), Window::default(), 680.0);
        assert_eq!(layout.value_range(&parameters.graphs[0]), (119.0, 121.0));
    }

    #[test]
    fn hovering_finds_the_nearest_event() {
        let parameters = parameters(Domain::Events, events(&[0.0, 1.0, 2.0]));
        let layout = Layout::new(&parameters, palette(), Window::default(), 680.0);
        let graph = &parameters.graphs[0];
        assert_eq!(layout.mark_at(graph, 1.4).unwrap().start, 1.0);
        assert_eq!(layout.mark_at(graph, 7.0).unwrap().start, 2.0);
    }

    #[test]
    fn hovering_finds_the_time_span() {
        let marks = vec![
            Mark {
                start: 0.0,
                end: 0.5,
                value: 1.0,
            },
            Mark {
                start: 1.0,
                end: 2.0,
                value: 2.0,
            },
        ];
        let parameters = parameters(Domain::Time, marks);
        let layout = Layout::new(&parameters, palette(), Window::default(), 680.0);
        let graph = &parameters.graphs[0];
        assert_eq!(layout.mark_at(graph, 1.5).unwrap().value, 2.0);
        assert_eq!(layout.mark_at(graph, 0.6).unwrap().value, 1.0);
    }

    #[test]
    fn marks_stay_inside_the_plot() {
        let parameters = parameters(Domain::Events, events(&[0.0, 1.0]));
        let layout = Layout::new(&parameters, palette(), Window::default(), 680.0);
        let plot = layout.plot(0);
        let range = layout.value_range(&parameters.graphs[0]);
        for mark in &parameters.graphs[0].marks {
            let area = layout.mark_area(mark, range, plot);
            assert!(area.y >= plot.y && area.y + area.height <= plot.y + plot.height);
            assert!(area.x >= plot.x && area.x + area.width <= plot.x + plot.width);
        }
    }
}
