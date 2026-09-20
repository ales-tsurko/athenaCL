//! Delegate editing, focus, selection, scrolling and blink scheduling to Iced.

use iced::{
    advanced::{
        layout::{self, Layout},
        mouse, renderer,
        text::{self, paragraph, Renderer as TextRenderer},
        widget::{tree, Id, Operation, Tree, Widget},
        Clipboard, Shell,
    },
    alignment::Vertical,
    widget::{text_input, TextInput},
    Element, Event, Length, Padding, Rectangle, Size, Theme,
};

use crate::app::{terminal_input::renderer::BlockRenderer, theme::Colors};

/// A borderless command or answer field with a blinking, reverse-video block caret.
pub(crate) struct Input<'a, Message> {
    inner: TextInput<'a, Message>,
    value: text_input::Value,
    colors: Colors,
    enabled: bool,
}

impl<'a, Message: Clone> Input<'a, Message> {
    pub(crate) fn new(placeholder: &str, value: &str, colors: Colors) -> Self {
        Self {
            inner: TextInput::new(placeholder, value),
            value: text_input::Value::new(value),
            colors,
            enabled: false,
        }
    }

    pub(crate) fn id(mut self, id: impl Into<Id>) -> Self {
        self.inner = self.inner.id(id);
        self
    }

    pub(crate) fn on_input(mut self, on_input: impl Fn(String) -> Message + 'a) -> Self {
        self.inner = self.inner.on_input(on_input);
        self.enabled = true;
        self
    }

    pub(crate) fn on_submit(mut self, message: Message) -> Self {
        self.inner = self.inner.on_submit(message);
        self
    }
}

impl<Message: Clone> Widget<Message, Theme, iced::Renderer> for Input<'_, Message> {
    fn tag(&self) -> tree::Tag {
        tree::Tag::of::<State>()
    }

    fn state(&self) -> tree::State {
        tree::State::new(State {
            input: Tree::new(&self.inner as &dyn Widget<Message, Theme, iced::Renderer>),
            space: paragraph::Plain::default(),
        })
    }

    fn diff(&self, tree: &mut Tree) {
        self.inner
            .diff(&mut tree.state.downcast_mut::<State>().input);
    }

    fn size(&self) -> Size<Length> {
        Widget::size(&self.inner)
    }

    fn layout(
        &mut self,
        tree: &mut Tree,
        renderer: &iced::Renderer,
        limits: &layout::Limits,
    ) -> layout::Node {
        let state = tree.state.downcast_mut::<State>();
        let cell_width = state.measure_space(renderer);
        // Iced reserves only 5 pixels when scrolling to the caret. Leave room for a whole cell
        // (or a double-width fallback glyph) beyond its text clip. Its padding setter takes self.
        let input = std::mem::replace(&mut self.inner, TextInput::new("", ""));
        self.inner = input.padding(Padding::ZERO.right(2.0 * cell_width));
        self.inner.layout(&mut state.input, renderer, limits, None)
    }

    fn operate(
        &mut self,
        tree: &mut Tree,
        layout: Layout<'_>,
        renderer: &iced::Renderer,
        operation: &mut dyn Operation,
    ) {
        self.inner.operate(
            &mut tree.state.downcast_mut::<State>().input,
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
        self.inner.update(
            &mut tree.state.downcast_mut::<State>().input,
            event,
            layout,
            cursor,
            renderer,
            clipboard,
            shell,
            viewport,
        );
    }

    fn mouse_interaction(
        &self,
        tree: &Tree,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        viewport: &Rectangle,
        renderer: &iced::Renderer,
    ) -> mouse::Interaction {
        self.inner.mouse_interaction(
            &tree.state.downcast_ref::<State>().input,
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
        _style: &renderer::Style,
        layout: Layout<'_>,
        cursor: mouse::Cursor,
        viewport: &Rectangle,
    ) {
        let Some(clip) = layout.bounds().intersection(viewport) else {
            return;
        };
        let cached = tree.state.downcast_ref::<State>();
        let state = cached
            .input
            .state
            .downcast_ref::<text_input::State<<iced::Renderer as TextRenderer>::Paragraph>>();
        let index = match state.cursor().state(&self.value) {
            text_input::cursor::State::Index(index) => Some(index),
            text_input::cursor::State::Selection { .. } => None,
        };
        let status = if !self.enabled {
            text_input::Status::Disabled
        } else if state.is_focused() {
            text_input::Status::Focused {
                is_hovered: cursor.is_over(layout.bounds()),
            }
        } else if cursor.is_over(layout.bounds()) {
            text_input::Status::Hovered
        } else {
            text_input::Status::Active
        };
        let appearance = Appearance(self.colors.input()(theme, status));
        let mut renderer = BlockRenderer::new(
            renderer,
            index,
            clip,
            self.colors.paper,
            cached.space.min_width(),
        );

        // This drawing-only input shares the original input's cached paragraphs and focus state.
        // Empty constructor strings avoid reshaping or copying its contents. Its renderer changes
        // only a caret Iced actually draws, retaining native blink, window-focus and IME behavior.
        TextInput::<(), Appearance, BlockRenderer<'_>>::new("", "")
            .on_input_maybe(self.enabled.then_some(|_| ()))
            .draw(
                &cached.input,
                &mut renderer,
                &appearance,
                layout,
                cursor,
                Some(&self.value),
                viewport,
            );
    }
}

impl<'a, Message: Clone + 'a> From<Input<'a, Message>> for Element<'a, Message> {
    fn from(input: Input<'a, Message>) -> Self {
        Self::new(input)
    }
}

/// Retain the native input state and the space measurement across view rebuilds.
#[derive(Debug)]
pub(super) struct State {
    pub(super) input: Tree,
    pub(super) space: paragraph::Plain<<iced::Renderer as TextRenderer>::Paragraph>,
}

impl State {
    fn measure_space(&mut self, renderer: &iced::Renderer) -> f32 {
        let size = renderer.default_size();
        let line_height = text::LineHeight::default();
        // Match TextInput's shaping settings. Plain reuses its paragraph until the font, size or
        // font database changes, including fonts loaded after the first view was constructed.
        let _ = self.space.update(text::Text {
            content: " ",
            font: renderer.default_font(),
            size,
            line_height,
            bounds: Size::new(f32::INFINITY, line_height.to_absolute(size).0),
            align_x: text::Alignment::Default,
            align_y: Vertical::Center,
            shaping: text::Shaping::Advanced,
            wrapping: text::Wrapping::default(),
        });
        self.space.min_width()
    }
}

/// Use exactly the input's appearance without allocating another style closure while drawing.
struct Appearance(text_input::Style);

impl text_input::Catalog for Appearance {
    type Class<'a> = ();

    fn default<'a>() -> Self::Class<'a> {}

    fn style(&self, _class: &(), _status: text_input::Status) -> text_input::Style {
        self.0
    }
}
