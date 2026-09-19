//! Generations of a cellular automaton: `AUca`.
//!
//! Zooming keeps the cells square, and hovering shows a cell's generation and value.

use iced::{
    mouse,
    widget::{
        self,
        canvas::{self, Canvas, Frame},
    },
    Element, Length, Point, Rectangle, Renderer, Size, Theme, Vector,
};

use super::{
    action, color, fill, format_value, outline, to_index, Anchor, Gesture, Label, Message, Pointer,
    Window, LABEL_SCALE,
};
use crate::figure::{Automaton, Rgb};

const TOP: f32 = 8.0;
const RIGHT: f32 = 8.0;
const BOTTOM: f32 = 8.0;
/// Where the title starts.
const TITLE_X: f32 = 8.0;
/// Title line spacing: athenaCL's 10 pixels, at label scale.
const LINE: f32 = 10.0 * LABEL_SCALE;
/// The largest cell, and the tallest the cells get before they're drawn smaller.
const MAX_CELL: f32 = 12.0;
const MAX_HEIGHT: f32 = 640.0;
/// The fewest cells to zoom in to.
const MIN_CELLS: f64 = 4.0;

pub(super) fn view(automaton: &Automaton, width: f32) -> Element<'_, Message> {
    let layout = Layout::new(automaton, View::default(), width);
    Canvas::new(Cells(automaton))
        .width(Length::Fill)
        .height(layout.height())
        .into()
}

struct Cells<'a>(&'a Automaton);

/// The visible part of the generations, zoomed alike in both directions.
#[derive(Debug, Clone, Copy, Default, PartialEq)]
struct View {
    cells: Window,
    generations: Window,
}

impl View {
    /// Zoom around `at`, keeping cells square.
    fn zoom(&mut self, at: Point, factor: f32, grid: Rectangle, min_span: f64) -> bool {
        let across = f64::from(((at.x - grid.x) / grid.width).clamp(0.0, 1.0));
        let down = f64::from(((at.y - grid.y) / grid.height).clamp(0.0, 1.0));
        let (factor, min) = (f64::from(factor), min_span);

        self.cells.zoom(across, factor, min) || self.generations.zoom(down, factor, min)
    }

    /// Pan by a distance in pixels.
    fn pan(&mut self, delta: Vector, grid: Rectangle) -> bool {
        let across = f64::from(-delta.x / grid.width);
        let down = f64::from(-delta.y / grid.height);

        self.cells.pan(across) || self.generations.pan(down)
    }

    /// Show everything again.
    fn reset(&mut self) -> bool {
        self.cells.reset() || self.generations.reset()
    }
}

#[derive(Debug, Default)]
struct State {
    pointer: Pointer,
    view: View,
    cache: canvas::Cache,
}

impl canvas::Program<Message> for Cells<'_> {
    type State = State;

    fn update(
        &self,
        state: &mut State,
        event: &canvas::Event,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Option<widget::Action<Message>> {
        let gesture = state.pointer.gesture(event, bounds, cursor);
        let layout = Layout::new(self.0, state.view, bounds.width);
        let changed = match gesture {
            Gesture::Zoom { at, factor } => {
                state.view.zoom(at, factor, layout.grid, layout.min_span())
            }
            Gesture::Pan { delta, .. } => state.view.pan(delta, layout.grid),
            Gesture::Reset => state.view.reset(),
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
        let layout = Layout::new(self.0, state.view, bounds.width);
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
        let layout = Layout::new(self.0, state.view, bounds.width);
        match cursor.position_in(bounds) {
            Some(at) if layout.grid.contains(at) => mouse::Interaction::Crosshair,
            _ => mouse::Interaction::default(),
        }
    }
}

/// Where everything is, for a width and zoom.
struct Layout<'a> {
    automaton: &'a Automaton,
    view: View,
    width: f32,
    /// Cells per generation.
    columns: usize,
    /// Where the cells are drawn.
    grid: Rectangle,
}

impl<'a> Layout<'a> {
    fn new(automaton: &'a Automaton, view: View, width: f32) -> Self {
        let columns = automaton.cells.iter().map(Vec::len).max().unwrap_or(0);
        let rows = automaton.cells.len();
        let title = automaton
            .title
            .iter()
            .map(|line| Label::new(line).width())
            .fold(0.0, f32::max);
        let left = (TITLE_X + title + 16.0).max(96.0);
        let cell = ((width - left - RIGHT) / columns.max(1) as f32)
            .floor()
            .min((MAX_HEIGHT / rows.max(1) as f32).floor())
            .clamp(1.0, MAX_CELL);
        Self {
            automaton,
            view,
            width,
            columns,
            grid: Rectangle::new(
                Point::new(left, TOP),
                Size::new(columns as f32 * cell, rows as f32 * cell),
            ),
        }
    }

    fn height(&self) -> f32 {
        // the title and, under it, the hovered cell's three lines
        let text = (self.automaton.title.len() + 4) as f32 * LINE;
        TOP + self.grid.height.max(text) + BOTTOM
    }

    /// The narrowest visible part, as a fraction of either direction, which keeps cells square.
    fn min_span(&self) -> f64 {
        let rows = self.automaton.cells.len().max(1) as f64;
        (MIN_CELLS / self.columns.max(1) as f64).max(MIN_CELLS / rows)
    }

    /// The size of a cell on screen.
    fn cell(&self) -> f32 {
        self.grid.width / (self.view.cells.span() * self.columns.max(1) as f64) as f32
    }

    /// Where a cell edge, or a generation edge, is on screen.
    fn x(&self, column: f64) -> f32 {
        let first = self.view.cells.start * self.columns as f64;
        (self.grid.x + (column - first) as f32 * self.cell()).round()
    }

    fn y(&self, row: f64) -> f32 {
        let first = self.view.generations.start * self.automaton.cells.len() as f64;
        (self.grid.y + (row - first) as f32 * self.cell()).round()
    }

    /// The generation and cell at `at`.
    fn cell_at(&self, at: Point) -> Option<(usize, usize)> {
        if !self.grid.contains(at) {
            return None;
        }
        let cell = self.cell();
        let column =
            self.view.cells.start * self.columns as f64 + f64::from((at.x - self.grid.x) / cell);
        let row = self.view.generations.start * self.automaton.cells.len() as f64
            + f64::from((at.y - self.grid.y) / cell);
        let row = to_index(row);
        let column = to_index(column);
        (column < self.automaton.cells.get(row)?.len()).then_some((row, column))
    }

    fn draw(&self, frame: &mut Frame) {
        let automaton = self.automaton;
        let palette = automaton.palette;
        frame.fill_rectangle(
            Point::ORIGIN,
            Size::new(self.width, self.height()),
            color(palette.margin),
        );
        for (index, line) in automaton.title.iter().enumerate() {
            Label::new(line).draw(
                frame,
                Point::new(TITLE_X, TOP + index as f32 * LINE),
                Anchor::NorthWest,
                color(palette.title),
            );
        }

        let rows = automaton.cells.len();
        let visible = |window: Window, count: usize| {
            let whole = count as f64;
            let first = to_index((window.start * whole).floor());
            let last = to_index((window.end * whole).ceil()).min(count);
            first..last
        };
        let columns = visible(self.view.cells, self.columns);
        for row in visible(self.view.generations, rows) {
            let Some(cells) = automaton.cells.get(row) else {
                continue;
            };
            let (top, bottom) = (self.y(row as f64), self.y(row as f64 + 1.0));
            // a rectangle for each run of cells of the same shade
            let mut start = columns.start;
            while let Some(rest) = cells.get(start..columns.end.min(cells.len())) {
                let gray = Rgb::gray(automaton.shade(rest.first().copied().unwrap_or_default()));
                let run = rest
                    .iter()
                    .take_while(|&&value| Rgb::gray(automaton.shade(value)) == gray)
                    .count()
                    .max(1);
                let (left, right) = (self.x(start as f64), self.x((start + run) as f64));
                let area =
                    Rectangle::new(Point::new(left, top), Size::new(right - left, bottom - top));
                fill(frame, area, self.grid, color(gray));
                start += run;
            }
        }
    }

    /// Frame the cell under the pointer, and show where it is and its value.
    fn draw_hover(&self, frame: &mut Frame, at: Point) {
        let Some((row, column)) = self.cell_at(at) else {
            return;
        };
        let palette = self.automaton.palette;
        let area = Rectangle::new(
            Point::new(self.x(column as f64), self.y(row as f64)),
            Size::new(
                self.x(column as f64 + 1.0) - self.x(column as f64),
                self.y(row as f64 + 1.0) - self.y(row as f64),
            ),
        );
        outline(frame, area.expand(1.0), self.grid, 1.0, color(palette.unit));

        let value = self
            .automaton
            .cells
            .get(row)
            .and_then(|cells| cells.get(column))
            .copied()
            .unwrap_or_default();
        let lines = [
            format!("gen {row}"),
            format!("cell {column}"),
            format!("value {}", format_value(value)),
        ];
        let first = self.automaton.title.len() + 1;
        for (index, line) in lines.iter().enumerate() {
            Label::new(line).draw(
                frame,
                Point::new(TITLE_X, TOP + (first + index) as f32 * LINE),
                Anchor::NorthWest,
                color(palette.unit),
            );
        }
    }
}

#[cfg(test)]
mod tests {
    #![expect(clippy::float_cmp, reason = "the tests assert exact float values")]

    use iced::keyboard;

    use super::*;
    use crate::figure::Palette;

    fn automaton(columns: usize, rows: usize) -> Automaton {
        let black = Rgb(0, 0, 0);
        Automaton {
            palette: Palette {
                background: black,
                grid: black,
                margin: black,
                main: black,
                main_frame: black,
                alt: black,
                alt_frame: black,
                title: black,
                label: black,
                unit: black,
            },
            title: vec!["f{t}k{3}r{1}".to_owned()],
            cells: vec![vec![0.0; columns]; rows],
            max: Some(2.0),
        }
    }

    #[test]
    fn cells_fit_the_width_in_whole_pixels() {
        let automaton = automaton(81, 40);
        let layout = Layout::new(&automaton, View::default(), 680.0);
        let cell = layout.cell();
        assert_eq!(cell, cell.round());
        assert!(layout.grid.x + layout.grid.width <= 680.0 - RIGHT);
        assert!((680.0 - RIGHT - layout.grid.x) / 81.0 < cell + 1.0);
    }

    #[test]
    fn tall_automata_get_smaller_cells() {
        let automaton = automaton(20, 400);
        let layout = Layout::new(&automaton, View::default(), 680.0);
        assert!(layout.grid.height <= MAX_HEIGHT);
    }

    #[test]
    fn zooming_and_resetting_reach_the_view() {
        let automaton = automaton(10, 10);
        let program = Cells(&automaton);
        let bounds = Rectangle::new(Point::ORIGIN, Size::new(680.0, 300.0));
        let at = mouse::Cursor::Available(Point::new(300.0, 100.0));
        let command = canvas::Event::Keyboard(keyboard::Event::ModifiersChanged(
            keyboard::Modifiers::COMMAND,
        ));
        let zoom = canvas::Event::Mouse(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Pixels { x: 0.0, y: 60.0 },
        });

        let mut state = State::default();
        canvas::Program::update(&program, &mut state, &command, bounds, at);
        let action = canvas::Program::update(&program, &mut state, &zoom, bounds, at);
        assert!(action.is_some(), "zooming acts");
        assert!(state.view.cells.span() < 1.0);

        // a double click shows everything again
        let press = canvas::Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left));
        canvas::Program::update(&program, &mut state, &press, bounds, at);
        let action = canvas::Program::update(&program, &mut state, &press, bounds, at);
        assert!(action.is_some(), "resetting acts");
        assert_eq!(state.view, View::default());
    }

    #[test]
    fn hovering_finds_cells() {
        let automaton = automaton(10, 10);
        let layout = Layout::new(&automaton, View::default(), 680.0);
        let cell = layout.cell();
        let at = Point::new(layout.grid.x + 3.5 * cell, layout.grid.y + 6.5 * cell);
        assert_eq!(layout.cell_at(at), Some((6, 3)));
        assert_eq!(layout.cell_at(Point::new(1.0, 1.0)), None);
    }

    #[test]
    fn zooming_keeps_cells_square() {
        let automaton = automaton(80, 20);
        let mut view = View::default();
        let min = Layout::new(&automaton, view, 680.0).min_span();
        view.cells.zoom(0.5, 1000.0, min);
        view.generations.zoom(0.5, 1000.0, min);
        assert_eq!(view.cells.span(), view.generations.span());
    }
}
