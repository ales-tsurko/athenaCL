//! Observe native event order, row selection, and browser drag gestures.

use std::path::PathBuf;

use iced::{
    advanced::{
        layout, mouse, overlay,
        renderer::{self, Renderer as _},
        widget::{tree, Operation, Tree, Widget},
        Clipboard, Layout, Shell,
    },
    keyboard::{self, Modifiers},
    window, Border, Color, Element, Event, Length, Point, Rectangle, Size, Theme, Vector,
};

use crate::app::{
    browser::{
        drag::{Gesture, Targets},
        Browser, Message,
    },
    theme::Colors,
};

pub(crate) struct Input<'a> {
    content: Element<'a, Message>,
    context: Option<PathBuf>,
    browser: Option<(&'a Browser, Colors)>,
    /// What a row is shaded with while the pointer is over it.
    hover: Option<Color>,
    /// Whether this is an open context menu, which iced_aw also operates with its row's layout.
    menu: bool,
}

impl<'a> Input<'a> {
    pub(crate) fn new(content: impl Into<Element<'a, Message>>) -> Self {
        Self {
            content: content.into(),
            context: None,
            browser: None,
            hover: None,
            menu: false,
        }
    }

    /// An open context menu: iced_aw also operates on it with the layout of the row it opened on,
    /// which its widgets cannot follow, so it is only operated on with a layout of its own size.
    pub(crate) fn menu(mut self) -> Self {
        self.menu = true;
        self
    }

    pub(crate) fn hover(mut self, color: Color) -> Self {
        self.hover = Some(color);
        self
    }

    pub(crate) fn context(mut self, path: PathBuf) -> Self {
        self.context = Some(path);
        self
    }

    pub(crate) fn dragging(mut self, browser: &'a Browser, colors: Colors) -> Self {
        self.browser = Some((browser, colors));
        self
    }
}

impl Widget<Message, Theme, iced::Renderer> for Input<'_> {
    fn tag(&self) -> tree::Tag {
        tree::Tag::of::<State>()
    }

    fn state(&self) -> tree::State {
        tree::State::new(State::default())
    }

    fn children(&self) -> Vec<Tree> {
        vec![Tree::new(&self.content)]
    }

    fn diff(&self, tree: &mut Tree) {
        tree.diff_children(std::slice::from_ref(&self.content));
    }

    fn size(&self) -> Size<Length> {
        self.content.as_widget().size()
    }

    fn layout(
        &mut self,
        tree: &mut Tree,
        renderer: &iced::Renderer,
        limits: &layout::Limits,
    ) -> layout::Node {
        let node = self.content.as_widget_mut().layout(
            tree.children.first_mut().expect("one content child"),
            renderer,
            limits,
        );
        tree.state.downcast_mut::<State>().size = node.size();
        node
    }

    fn operate(
        &mut self,
        tree: &mut Tree,
        layout: Layout<'_>,
        renderer: &iced::Renderer,
        operation: &mut dyn Operation,
    ) {
        if self.menu && layout.bounds().size() != tree.state.downcast_ref::<State>().size {
            return;
        }
        if let Some(path) = self.context.as_mut() {
            operation.custom(None, layout.bounds(), path);
        }
        self.content.as_widget_mut().operate(
            tree.children.first_mut().expect("one content child"),
            layout,
            renderer,
            operation,
        );
    }

    fn update(
        &mut self,
        tree: &mut Tree,
        event: &Event,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        renderer: &iced::Renderer,
        clipboard: &mut dyn Clipboard,
        shell: &mut Shell<'_, Message>,
        viewport: &Rectangle,
    ) {
        let state = tree.state.downcast_mut::<State>();
        match event {
            Event::Keyboard(keyboard::Event::ModifiersChanged(value)) => state.modifiers = *value,
            Event::Window(window::Event::Unfocused) => {
                state.modifiers = Modifiers::empty();
                state.position = None;
            }
            Event::Mouse(mouse::Event::CursorMoved { position }) => {
                state.position = Some(*position)
            }
            Event::Mouse(mouse::Event::CursorLeft) => state.position = None,
            _ => (),
        }
        // A batch can give every event the final cursor position. Use the ordered motion events for
        // both row hit testing and the drag, preserving scrollable/overlay cursor transforms.
        let cursor = if self.browser.is_some() && !cursor.is_levitating() {
            if matches!(
                event,
                Event::Mouse(mouse::Event::CursorLeft) | Event::Window(window::Event::Unfocused)
            ) {
                mouse::Cursor::Unavailable
            } else {
                state
                    .position
                    .map(mouse::Cursor::Available)
                    .unwrap_or(cursor)
            }
        } else {
            cursor
        };
        if self.hover.is_some() {
            let hovered = cursor.is_over(layout.bounds()) && cursor.is_over(*viewport);
            if hovered != state.hovered {
                state.hovered = hovered;
                shell.request_redraw();
            }
        }
        if let Some((browser, _)) = self.browser {
            // a click anywhere else takes the keys back from the tree
            if browser.focused
                && !shell.is_event_captured()
                && matches!(event, Event::Mouse(mouse::Event::ButtonPressed(_)))
                && !cursor.is_over(layout.bounds())
            {
                shell.publish(Message::Blur);
            }
            if state.drag.engaged() && !shell.is_event_captured() {
                let mut targets = Targets::new(*viewport);
                self.content.as_widget_mut().operate(
                    tree.children.first_mut().expect("one content child"),
                    layout,
                    renderer,
                    &mut targets,
                );
                if state
                    .drag
                    .update(event, cursor.position(), browser, &targets, shell)
                {
                    shell.capture_event();
                    return;
                }
            }
        }
        if !shell.is_event_captured()
            && matches!(
                event,
                Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Right))
            )
            && cursor.is_over(layout.bounds())
            && cursor.is_over(*viewport)
        {
            if let Some(path) = &self.context {
                shell.publish(Message::Context(path.clone()));
            }
        }
        let mut messages = Vec::new();
        let mut local = Shell::new(&mut messages);
        if shell.is_event_captured() {
            local.capture_event();
        }
        self.content.as_widget_mut().update(
            tree.children.first_mut().expect("one content child"),
            event,
            layout,
            cursor,
            renderer,
            clipboard,
            &mut local,
            viewport,
        );
        // The outer panel observes modifiers even when entries are inserted while Shift is held. No
        // subscription race: the modifiers and click are handled in native event order.
        let drag = std::cell::RefCell::new(&mut state.drag);
        shell.merge(local, |message| match message {
            Message::Click(path, _, double) => match self.browser {
                Some((browser, _)) => drag.borrow_mut().click(
                    path,
                    state.modifiers,
                    double,
                    cursor.position(),
                    browser,
                ),
                None => Message::Click(path, state.modifiers, double),
            },
            other => other,
        });
    }

    fn mouse_interaction(
        &self,
        tree: &Tree,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        viewport: &Rectangle,
        renderer: &iced::Renderer,
    ) -> mouse::Interaction {
        if let Some(interaction) = tree.state.downcast_ref::<State>().drag.interaction() {
            return interaction;
        }
        self.content.as_widget().mouse_interaction(
            tree.children.first().expect("one content child"),
            layout,
            cursor,
            viewport,
            renderer,
        )
    }

    fn draw(
        &self,
        tree: &Tree,
        renderer: &mut iced::Renderer,
        theme: &Theme,
        style: &renderer::Style,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        viewport: &Rectangle,
    ) {
        if let Some(color) = self.hover {
            if tree.state.downcast_ref::<State>().hovered {
                renderer.fill_quad(
                    renderer::Quad {
                        bounds: layout.bounds(),
                        ..Default::default()
                    },
                    color,
                );
            }
        }
        self.content.as_widget().draw(
            tree.children.first().expect("one content child"),
            renderer,
            theme,
            style,
            layout,
            cursor,
            viewport,
        );
        if let Some((_, colors)) = self.browser {
            if let Some(bounds) = tree.state.downcast_ref::<State>().drag.highlight() {
                renderer.fill_quad(
                    renderer::Quad {
                        bounds,
                        border: Border {
                            color: colors.ink,
                            width: 2.0,
                            ..Default::default()
                        },
                        ..Default::default()
                    },
                    Color::TRANSPARENT,
                );
            }
        }
    }

    fn overlay<'b>(
        &'b mut self,
        tree: &'b mut Tree,
        layout: Layout<'b>,
        renderer: &iced::Renderer,
        viewport: &Rectangle,
        translation: Vector,
    ) -> Option<overlay::Element<'b, Message, Theme, iced::Renderer>> {
        self.content.as_widget_mut().overlay(
            tree.children.first_mut()?,
            layout,
            renderer,
            viewport,
            translation,
        )
    }
}

impl<'a> From<Input<'a>> for Element<'a, Message> {
    fn from(input: Input<'a>) -> Self {
        Self::new(input)
    }
}

#[derive(Debug, Default)]
struct State {
    modifiers: Modifiers,
    position: Option<Point>,
    drag: Gesture,
    /// Whether the pointer is over the row, which is then shaded.
    hovered: bool,
    /// The size it was last laid out at.
    size: Size,
}
