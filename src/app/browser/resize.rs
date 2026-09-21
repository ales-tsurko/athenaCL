//! A pixel-width sidebar and a divider that retains its drag outside the handle.

use iced::{
    advanced::{
        layout, mouse,
        renderer::{self, Renderer as _},
        widget::{tree, Tree, Widget},
        Clipboard, Layout, Shell,
    },
    window, Element, Event, Length, Point, Rectangle, Size, Theme,
};

use crate::app::{browser::Message, theme::Colors};

pub(crate) const MIN_WIDTH: f32 = 220.0;
pub(crate) const MAX_WIDTH: f32 = 480.0;
pub(crate) const HANDLE_WIDTH: f32 = 8.0;

#[derive(Debug, Clone, Copy)]
pub(crate) struct Width(f32);

impl Width {
    pub(crate) fn get(self) -> f32 {
        self.0
    }

    pub(crate) fn set(&mut self, width: f32) {
        if width.is_finite() {
            self.0 = width.round().clamp(MIN_WIDTH, MAX_WIDTH);
        }
    }

    pub(crate) fn divider<'a>(self, colors: Colors) -> Element<'a, Message> {
        Element::new(Divider {
            width: self.0,
            colors,
        })
    }
}

impl Default for Width {
    fn default() -> Self {
        Self(280.0)
    }
}

struct Divider {
    width: f32,
    colors: Colors,
}

impl Widget<Message, Theme, iced::Renderer> for Divider {
    fn tag(&self) -> tree::Tag {
        tree::Tag::of::<Gesture>()
    }

    fn state(&self) -> tree::State {
        tree::State::new(Gesture::default())
    }

    fn size(&self) -> Size<Length> {
        Size::new(Length::Fixed(HANDLE_WIDTH), Length::Fill)
    }

    fn layout(
        &mut self,
        _tree: &mut Tree,
        _renderer: &iced::Renderer,
        limits: &layout::Limits,
    ) -> layout::Node {
        layout::Node::new(limits.resolve(Length::Fixed(HANDLE_WIDTH), Length::Fill, Size::ZERO))
    }

    fn update(
        &mut self,
        tree: &mut Tree,
        event: &Event,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        _renderer: &iced::Renderer,
        _clipboard: &mut dyn Clipboard,
        shell: &mut Shell<'_, Message>,
        _viewport: &Rectangle,
    ) {
        let gesture = tree.state.downcast_mut::<Gesture>();
        match event {
            Event::Mouse(mouse::Event::CursorMoved { position }) => {
                // Iced can deliver a batch with the final cursor position for every event.
                // Remember event positions so a fast drag still starts inside the handle.
                gesture.position = Some(*position);
                if let Some(drag) = &gesture.drag {
                    shell.publish(Message::Resize(drag.width + position.x - drag.start));
                    shell.capture_event();
                }
            }
            Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left))
                if !shell.is_event_captured() =>
            {
                if let Some(position) = gesture
                    .position
                    .or_else(|| cursor.position())
                    .filter(|position| layout.bounds().contains(*position))
                {
                    gesture.drag = Some(Drag {
                        start: position.x,
                        width: self.width,
                    });
                    shell.capture_event();
                    shell.request_redraw();
                }
            }
            Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left))
                if gesture.drag.is_some() =>
            {
                gesture.drag = None;
                shell.capture_event();
                shell.request_redraw();
            }
            Event::Window(window::Event::Unfocused) => *gesture = Gesture::default(),
            Event::Mouse(mouse::Event::CursorLeft) => gesture.position = None,
            _ => (),
        }
    }

    fn mouse_interaction(
        &self,
        tree: &Tree,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        _viewport: &Rectangle,
        _renderer: &iced::Renderer,
    ) -> mouse::Interaction {
        if tree.state.downcast_ref::<Gesture>().drag.is_some() || cursor.is_over(layout.bounds()) {
            mouse::Interaction::ResizingHorizontally
        } else {
            mouse::Interaction::None
        }
    }

    fn draw(
        &self,
        tree: &Tree,
        renderer: &mut iced::Renderer,
        _theme: &Theme,
        _style: &renderer::Style,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        _viewport: &Rectangle,
    ) {
        let active =
            tree.state.downcast_ref::<Gesture>().drag.is_some() || cursor.is_over(layout.bounds());
        let bounds = layout.bounds();
        renderer.fill_quad(
            renderer::Quad {
                bounds: Rectangle {
                    x: bounds.x + 3.0,
                    width: if active { 2.0 } else { 1.0 },
                    ..bounds
                },
                ..Default::default()
            },
            if active {
                self.colors.ink
            } else {
                self.colors.rule
            },
        );
    }
}

#[derive(Debug)]
struct Drag {
    start: f32,
    width: f32,
}

#[derive(Debug, Default)]
struct Gesture {
    position: Option<Point>,
    drag: Option<Drag>,
}

#[cfg(test)]
mod tests {
    use iced::{
        mouse,
        widget::{row, space},
        Event, Point,
    };
    use iced_test::Simulator;

    use super::*;
    use crate::app::{browser::Browser, theme::Mode};

    #[test]
    fn divider_drag_continues_outside_the_handle_and_clamps_to_both_limits() {
        let mut browser = Browser::default();
        for (end, expected) in [(-100.0, MIN_WIDTH), (900.0, MAX_WIDTH), (317.0, 313.0)] {
            let mut simulator = Simulator::with_size(
                crate::app::settings(),
                Size::new(1040.0, 500.0),
                row![
                    space().width(browser.width.get()),
                    browser.divider(Mode::Dark.colors()),
                    space::horizontal()
                ]
                .height(Length::Fill),
            );
            simulator.point_at(Point::new(browser.width.get() + 4.0, 100.0));
            let _ = simulator
                .snapshot(&Mode::Dark.theme())
                .expect("hovered divider");
            let _ = simulator.simulate([Event::Mouse(mouse::Event::ButtonPressed(
                mouse::Button::Left,
            ))]);
            simulator.point_at(Point::new(end, 100.0));
            let _ = simulator.simulate([Event::Mouse(mouse::Event::CursorMoved {
                position: Point::new(end, 100.0),
            })]);
            let _ = simulator
                .snapshot(&Mode::Dark.theme())
                .expect("dragged divider");
            let _ = simulator.simulate([Event::Mouse(mouse::Event::ButtonReleased(
                mouse::Button::Left,
            ))]);
            simulator.point_at(Point::new(700.0, 100.0));
            let _ = simulator.simulate([Event::Mouse(mouse::Event::CursorMoved {
                position: Point::new(700.0, 100.0),
            })]);
            for message in simulator.into_messages() {
                drop(browser.update(message));
            }
            assert!(
                (browser.width.get() - expected).abs() < f32::EPSILON,
                "expected {expected}, got {}",
                browser.width.get()
            );
        }
        drop(browser.update(Message::Resize(f32::NAN)));
        assert!((browser.width.get() - 313.0).abs() < f32::EPSILON);
        drop(browser.update(Message::Toggle));
        drop(browser.update(Message::Toggle));
        assert!(
            (browser.width.get() - 313.0).abs() < f32::EPSILON,
            "width survives hiding the browser"
        );
    }
}
