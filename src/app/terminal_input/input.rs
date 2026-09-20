//! Delegate editing, focus, selection, scrolling and blink scheduling to Iced.

use iced::{
    advanced::{
        input_method,
        layout::{self, Layout},
        mouse, renderer,
        text::{self, paragraph, Renderer as TextRenderer},
        widget::{tree, Id, Operation, Tree, Widget},
        Clipboard, Shell,
    },
    alignment::Vertical,
    keyboard::{self, key::Named, Modifiers},
    widget::{text_input, TextInput},
    Element, Event, Length, Padding, Rectangle, Size, Theme,
};

use crate::app::{terminal_input::renderer::BlockRenderer, theme::Colors};

/// A borderless command or answer field with a blinking, reverse-video block caret.
pub(crate) struct Input<'a, Message> {
    inner: TextInput<'a, Edit>,
    value: text_input::Value,
    colors: Colors,
    enabled: bool,
    on_input: Option<EditHandler<'a, Message>>,
    on_submit: Option<Message>,
    on_complete: Option<CompletionHandler<'a, Message>>,
    on_dismiss: Option<Message>,
    observe_cursor: bool,
}

impl<'a, Message: Clone> Input<'a, Message> {
    pub(crate) fn new(placeholder: &str, value: &str, colors: Colors) -> Self {
        Self {
            inner: TextInput::new(placeholder, value),
            value: text_input::Value::new(value),
            colors,
            enabled: false,
            on_input: None,
            on_submit: None,
            on_complete: None,
            on_dismiss: None,
            observe_cursor: false,
        }
    }

    pub(crate) fn id(mut self, id: impl Into<Id>) -> Self {
        self.inner = self.inner.id(id);
        self
    }

    pub(crate) fn on_input(mut self, on_input: impl Fn(String) -> Message + 'a) -> Self {
        self.inner = self.inner.on_input(Edit::Changed);
        self.on_input = Some(Box::new(move |value, _| on_input(value)));
        self.enabled = true;
        self
    }

    pub(crate) fn on_submit(mut self, message: Message) -> Self {
        self.inner = self.inner.on_submit(Edit::Submitted);
        self.on_submit = Some(message);
        self
    }

    /// Report edits and caret moves using UTF-8 byte offsets, suppressing selected or IME text.
    pub(crate) fn on_edit(
        mut self,
        on_edit: impl Fn(String, Option<usize>) -> Message + 'a,
    ) -> Self {
        self.inner = self.inner.on_input(Edit::Changed);
        self.on_input = Some(Box::new(on_edit));
        self.enabled = true;
        self.observe_cursor = true;
        self
    }

    pub(crate) fn on_complete(
        mut self,
        on_complete: impl Fn(bool, String, usize) -> Message + 'a,
    ) -> Self {
        self.on_complete = Some(Box::new(on_complete));
        self
    }

    pub(crate) fn on_dismiss(mut self, message: Option<Message>) -> Self {
        self.on_dismiss = message;
        self
    }

    fn completion_key(&self, event: &Event, state: &State) -> Option<Message> {
        let caret = state.caret(&self.value)?;
        match event {
            Event::Keyboard(keyboard::Event::KeyPressed {
                key: keyboard::Key::Named(Named::Tab),
                modifiers,
                ..
            }) if modifiers.is_empty() || *modifiers == Modifiers::SHIFT => {
                self.on_complete.as_ref().map(|complete| {
                    complete(
                        modifiers.shift(),
                        self.value.to_string(),
                        self.value.until(caret).to_string().len(),
                    )
                })
            }
            Event::Keyboard(keyboard::Event::KeyPressed {
                key: keyboard::Key::Named(Named::Escape),
                modifiers,
                ..
            }) if modifiers.is_empty() => self.on_dismiss.clone(),
            _ => None,
        }
    }
}

impl<Message: Clone> Widget<Message, Theme, iced::Renderer> for Input<'_, Message> {
    fn tag(&self) -> tree::Tag {
        tree::Tag::of::<State>()
    }

    fn state(&self) -> tree::State {
        tree::State::new(State {
            input: Tree::new(&self.inner as &dyn Widget<Edit, Theme, iced::Renderer>),
            space: paragraph::Plain::default(),
            caret: None,
            preediting: false,
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
        let state = tree.state.downcast_mut::<State>();
        if let Some(message) = self.completion_key(event, state) {
            state.caret = state.caret(&self.value);
            shell.publish(message);
            shell.capture_event();
            return;
        }
        state.update_preedit(event);
        let mut edits = Vec::new();
        let mut local = Shell::new(&mut edits);
        self.inner.update(
            &mut state.input,
            event,
            layout,
            cursor,
            renderer,
            clipboard,
            &mut local,
            viewport,
        );
        // Forward native redraw/IME requests even when the event produced no application message.
        forward_requests(&local, shell);
        let mut changed = false;
        for edit in edits {
            let message = match edit {
                Edit::Changed(value) => {
                    self.value = text_input::Value::new(&value);
                    changed = true;
                    self.on_input
                        .as_ref()
                        .expect("enabled input has a callback")(
                        value,
                        state
                            .caret(&self.value)
                            .map(|index| self.value.until(index).to_string().len()),
                    )
                }
                Edit::Submitted => self
                    .on_submit
                    .clone()
                    .expect("submit callback was configured"),
            };
            shell.publish(message);
        }
        let caret = state.caret(&self.value);
        if self.observe_cursor && !changed && caret != state.caret && state.native().is_focused() {
            if let Some(on_input) = &self.on_input {
                shell.publish(on_input(
                    self.value.to_string(),
                    caret.map(|index| self.value.until(index).to_string().len()),
                ));
            }
        }
        state.caret = caret;
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

type EditHandler<'a, Message> = Box<dyn Fn(String, Option<usize>) -> Message + 'a>;
type CompletionHandler<'a, Message> = Box<dyn Fn(bool, String, usize) -> Message + 'a>;

/// Retain the native input state and the space measurement across view rebuilds.
#[derive(Debug)]
pub(super) struct State {
    pub(super) input: Tree,
    pub(super) space: paragraph::Plain<<iced::Renderer as TextRenderer>::Paragraph>,
    caret: Option<usize>,
    preediting: bool,
}

impl State {
    fn native(&self) -> &text_input::State<<iced::Renderer as TextRenderer>::Paragraph> {
        self.input.state.downcast_ref()
    }

    fn caret(&self, value: &text_input::Value) -> Option<usize> {
        if !self.native().is_focused() || self.preediting {
            return None;
        }
        match self.native().cursor().state(value) {
            text_input::cursor::State::Index(index) => Some(index),
            text_input::cursor::State::Selection { .. } => None,
        }
    }

    fn update_preedit(&mut self, event: &Event) {
        match event {
            Event::InputMethod(input_method::Event::Preedit(text, _)) => {
                self.preediting = !text.is_empty();
            }
            Event::InputMethod(input_method::Event::Commit(_) | input_method::Event::Closed)
            | Event::Window(iced::window::Event::Unfocused) => self.preediting = false,
            _ => (),
        }
    }

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

/// Native edits are mapped after Iced has updated its caret, including paste and IME commits.
#[derive(Clone)]
enum Edit {
    Changed(String),
    Submitted,
}

fn forward_requests<Message>(native: &Shell<'_, Edit>, shell: &mut Shell<'_, Message>) {
    shell.request_redraw_at(native.redraw_request());
    shell.request_input_method(native.input_method());
    if native.is_event_captured() {
        shell.capture_event();
    }
    if native.is_layout_invalid() {
        shell.invalidate_layout();
    }
    if native.are_widgets_invalid() {
        shell.invalidate_widgets();
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
