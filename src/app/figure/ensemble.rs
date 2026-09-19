//! Textures and their clones over time: `TEmap`.
//!
//! Hovering a lane shows its time range, and clicking it selects the texture or clone.

use iced::mouse;
use iced::widget::canvas::{self, Canvas, Frame};
use iced::{Color, Element, Length, Point, Rectangle, Renderer, Size, Theme};

use super::{
    color, fill, outline, status, Anchor, Gesture, Label, Message, Pointer, Ticks, Window,
    LABEL_HEIGHT, LABEL_SCALE,
};
use crate::figure::{Ensemble, Lane};

/// Space around the time labels, and at the edges.
const GUTTER: f32 = 4.0;
/// The time labels on top.
const TOP: f32 = GUTTER + LABEL_HEIGHT + GUTTER;
const RIGHT: f32 = 8.0;
const BOTTOM: f32 = 8.0;
/// Lane height: twice athenaCL's 8 pixel bars, to fit the output's width.
const LANE: f32 = 16.0;
/// The band on top of a bar, in its frame color.
const HEAD: f32 = 4.0;
/// Space between lanes.
const LANE_GAP: f32 = 6.0;
/// Where names start, and how far clone names are indented.
const NAME_X: f32 = 8.0;
const CLONE_INDENT: f32 = 9.0 * LABEL_SCALE;
/// The mark beside the active texture.
const MARKER: f32 = 3.0;
/// Pixels per time label.
const X_LABEL_SPACING: f32 = 64.0;
/// The shortest time to zoom in to, in seconds.
const MIN_SECONDS: f64 = 0.1;

pub(super) fn view<'a>(ensemble: &'a Ensemble, active: &'a str) -> Element<'a, Message> {
    let lanes = rows(ensemble).len() as f32;
    Canvas::new(Timeline { ensemble, active })
        .width(Length::Fill)
        .height(TOP + lanes * (LANE + LANE_GAP) + LANE_GAP + BOTTOM)
        .into()
}

/// A lane on the timeline, with the texture it belongs to.
struct Row<'a> {
    lane: &'a Lane,
    texture: &'a str,
    is_clone: bool,
}

fn rows(ensemble: &Ensemble) -> Vec<Row<'_>> {
    ensemble
        .textures
        .iter()
        .flat_map(|texture| {
            let name = texture.lane.name.as_str();
            std::iter::once(Row {
                lane: &texture.lane,
                texture: name,
                is_clone: false,
            })
            .chain(texture.clones.iter().map(move |clone| Row {
                lane: clone,
                texture: name,
                is_clone: true,
            }))
        })
        .collect()
}

struct Timeline<'a> {
    ensemble: &'a Ensemble,
    active: &'a str,
}

#[derive(Debug, Default)]
struct State {
    pointer: Pointer,
    window: Window,
    cache: canvas::Cache,
}

impl canvas::Program<Message> for Timeline<'_> {
    type State = State;

    fn update(
        &self,
        state: &mut State,
        event: canvas::Event,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> (canvas::event::Status, Option<Message>) {
        let gesture = state.pointer.gesture(&event, bounds, cursor);
        let layout = Layout::new(self.ensemble, state.window, bounds.width);
        let map = layout.map;
        let mut message = None;
        let changed = match gesture {
            Gesture::Zoom { at, factor } => {
                let anchor = ((at.x - map.x) / map.width).clamp(0.0, 1.0);
                state
                    .window
                    .zoom(f64::from(anchor), f64::from(factor), layout.min_span())
            }
            Gesture::Pan { delta, .. } => state.window.pan(f64::from(-delta.x / map.width)),
            Gesture::Reset => state.window.reset(),
            Gesture::Click(at) => {
                message = layout.row_at(at).map(|row| {
                    if row.is_clone {
                        Message::SelectClone {
                            texture: row.texture.to_owned(),
                            clone: row.lane.name.clone(),
                        }
                    } else {
                        Message::SelectTexture(row.lane.name.clone())
                    }
                });
                false
            }
            Gesture::None | Gesture::Press => false,
        };
        if changed {
            state.cache.clear();
        }
        (status(gesture, changed), message)
    }

    fn draw(
        &self,
        state: &State,
        renderer: &Renderer,
        _theme: &Theme,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Vec<canvas::Geometry> {
        let layout = Layout::new(self.ensemble, state.window, bounds.width);
        let content = state
            .cache
            .draw(renderer, bounds.size(), |frame| layout.draw(frame));
        let mut overlay = Frame::new(renderer, bounds.size());
        layout.draw_active(&mut overlay, self.active);
        if let Some(at) = cursor.position_in(bounds) {
            if !state.pointer.dragging() {
                layout.draw_hover(&mut overlay, at);
            }
        }
        vec![content, overlay.into_geometry()]
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
        let layout = Layout::new(self.ensemble, state.window, bounds.width);
        match cursor.position_in(bounds) {
            Some(at) if layout.row_at(at).is_some() => mouse::Interaction::Pointer,
            _ => mouse::Interaction::default(),
        }
    }
}

/// Where everything is, for a width and zoom.
struct Layout<'a> {
    ensemble: &'a Ensemble,
    rows: Vec<Row<'a>>,
    width: f32,
    /// Where the bars are drawn.
    map: Rectangle,
    /// The whole time, from zero to the last end.
    duration: f64,
    /// The visible part of it.
    visible: (f64, f64),
}

impl<'a> Layout<'a> {
    fn new(ensemble: &'a Ensemble, window: Window, width: f32) -> Self {
        let rows = rows(ensemble);
        let names = rows
            .iter()
            .map(|row| Self::name_x(row) + Label::new(&row.lane.name).width())
            .fold(0.0, f32::max);
        let left = (names + 12.0).clamp(72.0, (width / 2.0).max(72.0));
        let map = Rectangle::new(
            Point::new(left, TOP),
            Size::new(
                (width - left - RIGHT).max(1.0),
                rows.len() as f32 * (LANE + LANE_GAP) + LANE_GAP,
            ),
        );
        let end = rows.iter().map(|row| row.lane.end).fold(0.0, f64::max);
        let duration = if end > 0.0 { end } else { 1.0 };
        Self {
            ensemble,
            rows,
            width,
            map,
            duration,
            visible: (window.start * duration, window.end * duration),
        }
    }

    fn min_span(&self) -> f64 {
        MIN_SECONDS / self.duration
    }

    fn name_x(row: &Row) -> f32 {
        if row.is_clone {
            NAME_X + CLONE_INDENT
        } else {
            NAME_X
        }
    }

    /// The top of the lane at `index`.
    fn lane_y(&self, index: usize) -> f32 {
        self.map.y + LANE_GAP + index as f32 * (LANE + LANE_GAP)
    }

    fn x(&self, time: f64) -> f32 {
        let (start, end) = self.visible;
        self.map.x + ((time - start) / (end - start)) as f32 * self.map.width
    }

    /// A lane's bar, inset a pixel at each end as athenaCL draws them.
    fn bar(&self, index: usize) -> Rectangle {
        let lane = self.rows[index].lane;
        let left = self.x(lane.start).round() + 1.0;
        let right = (self.x(lane.end).round() - 1.0).max(left + 1.0);
        Rectangle::new(
            Point::new(left, self.lane_y(index)),
            Size::new(right - left, LANE),
        )
    }

    /// The index of the lane at `at`, across the whole width, gaps shared with neighbors.
    fn index_at(&self, at: Point) -> Option<usize> {
        let offset = at.y - self.map.y - LANE_GAP / 2.0;
        let index = (offset / (LANE + LANE_GAP)) as usize;
        (offset >= 0.0 && index < self.rows.len()).then_some(index)
    }

    fn row_at(&self, at: Point) -> Option<&Row<'a>> {
        self.index_at(at).map(|index| &self.rows[index])
    }

    fn draw(&self, frame: &mut Frame) {
        let palette = self.ensemble.palette;
        frame.fill_rectangle(
            Point::ORIGIN,
            Size::new(self.width, self.map.y + self.map.height + BOTTOM),
            color(palette.margin),
        );
        frame.fill_rectangle(
            self.map.position(),
            self.map.size(),
            color(palette.background),
        );
        Label::new(&format!("{:.2}", self.duration)).draw(
            frame,
            Point::new(NAME_X, GUTTER),
            Anchor::NorthWest,
            color(palette.unit),
        );

        // time: labeled lines in the margin color, and grid lines halfway between them
        let count = (self.map.width / X_LABEL_SPACING) as usize;
        let ticks = Ticks::new(self.visible.0, self.visible.1, count.max(2), 0.001);
        let line = |frame: &mut Frame, time: f64, color: Color| {
            let x = self.x(time).round();
            let line = Rectangle::new(
                Point::new(x, self.map.y),
                Size::new(1.0, self.map.height),
            );
            fill(frame, line, self.map, color);
        };
        let first = (self.visible.0 / ticks.step).floor() * ticks.step;
        let steps = ((self.visible.1 - first) / ticks.step).ceil() as usize;
        for i in 0..=steps {
            line(
                frame,
                first + (i as f64 + 0.5) * ticks.step,
                color(palette.grid),
            );
        }
        for &time in &ticks.values {
            line(frame, time, color(palette.margin));
            let label = Label::new(&ticks.format(time));
            let at = Point::new(self.x(time).round(), GUTTER);
            let bounds = label.bounds(at, Anchor::NorthCenter);
            if bounds.x >= self.map.x - GUTTER && bounds.x + bounds.width <= self.width {
                label.draw(frame, at, Anchor::NorthCenter, color(palette.unit));
            }
        }

        for (index, row) in self.rows.iter().enumerate() {
            let (body_color, head_color, name_color) = if row.is_clone {
                (palette.alt, palette.alt_frame, palette.label)
            } else {
                (palette.main, palette.main_frame, palette.title)
            };
            let bar = self.bar(index);
            let head = Rectangle::new(bar.position(), Size::new(bar.width, HEAD));
            fill(frame, head, self.map, color(head_color));
            let body = Rectangle::new(
                Point::new(bar.x, bar.y + HEAD),
                Size::new(bar.width, LANE - HEAD),
            );
            if row.lane.muted {
                outline(frame, body, self.map, 2.0, color(body_color));
            } else {
                fill(frame, body, self.map, color(body_color));
            }
            Label::new(&row.lane.name).draw(
                frame,
                Point::new(Self::name_x(row), bar.y + LANE / 2.0),
                Anchor::CenterWest,
                color(name_color),
            );
        }
    }

    /// Mark the active texture beside its name.
    fn draw_active(&self, frame: &mut Frame, active: &str) {
        let index = self
            .rows
            .iter()
            .position(|row| !row.is_clone && row.lane.name == active);
        if let Some(index) = index {
            frame.fill_rectangle(
                Point::new(0.0, self.lane_y(index)),
                Size::new(MARKER, LANE),
                color(self.ensemble.palette.unit),
            );
        }
    }

    /// Frame the lane under the pointer, and show its time range.
    fn draw_hover(&self, frame: &mut Frame, at: Point) {
        let Some(index) = self.index_at(at) else {
            return;
        };
        let palette = self.ensemble.palette;
        let lane = self.rows[index].lane;
        outline(frame, self.bar(index), self.map, 1.0, color(palette.title));
        let muted = if lane.muted { " muted" } else { "" };
        let text = format!("{} {:.2}-{:.2}{muted}", lane.name, lane.start, lane.end);
        Label::new(&text).draw_on(
            frame,
            Point::new(self.width - RIGHT, GUTTER),
            Anchor::NorthEast,
            color(palette.title),
            color(palette.margin),
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::figure::{Palette, Rgb, Texture};

    fn lane(name: &str, start: f64, end: f64) -> Lane {
        Lane {
            name: name.to_owned(),
            start,
            end,
            muted: false,
        }
    }

    fn ensemble() -> Ensemble {
        let black = Rgb(0, 0, 0);
        Ensemble {
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
            textures: vec![
                Texture {
                    lane: lane("a", 0.0, 10.0),
                    clones: vec![lane("x", 2.0, 12.0)],
                },
                Texture {
                    lane: lane("b", 5.0, 20.0),
                    clones: Vec::new(),
                },
            ],
        }
    }

    #[test]
    fn clones_follow_their_texture() {
        let ensemble = ensemble();
        let rows = rows(&ensemble);
        let names: Vec<_> = rows
            .iter()
            .map(|row| (row.lane.name.as_str(), row.texture, row.is_clone))
            .collect();
        assert_eq!(names, [("a", "a", false), ("x", "a", true), ("b", "b", false)]);
    }

    #[test]
    fn time_runs_from_zero_to_the_last_end() {
        let ensemble = ensemble();
        let layout = Layout::new(&ensemble, Window::default(), 680.0);
        assert_eq!(layout.duration, 20.0);
        assert_eq!(layout.x(0.0), layout.map.x);
        assert_eq!(layout.x(20.0), layout.map.x + layout.map.width);
    }

    #[test]
    fn lanes_are_found_by_height() {
        let ensemble = ensemble();
        let layout = Layout::new(&ensemble, Window::default(), 680.0);
        let middle = |index| Point::new(1.0, layout.lane_y(index) + LANE / 2.0);
        assert_eq!(layout.row_at(middle(1)).unwrap().lane.name, "x");
        assert_eq!(layout.row_at(middle(2)).unwrap().lane.name, "b");
        assert!(layout.row_at(Point::new(1.0, 2.0)).is_none());
        assert!(layout.row_at(Point::new(1.0, 1000.0)).is_none());
    }
}
