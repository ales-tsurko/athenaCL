//! Interaction and rendering regressions for the block caret.

use iced::{
    advanced::{
        clipboard,
        layout::{self, Layout},
        mouse, renderer,
        renderer::{Headless as _, Renderer as _},
        text::{self, Paragraph as _, Renderer as TextRenderer},
        widget::{operation, Tree},
        Shell,
    },
    alignment::Vertical,
    keyboard::key::Named,
    widget::text_input,
    window, Color, Element, Event, Font, Point, Rectangle, Size,
};

use crate::app::{
    terminal_input::{input::State, Input},
    theme::{Colors, Mode},
};

type InputState = text_input::State<<iced::Renderer as TextRenderer>::Paragraph>;
const WIDTH: u32 = 240;
const HEIGHT: u32 = 32;

/// The actual input, font and renderer; no mock of Iced's drawing behavior.
struct InputHarness {
    input: Element<'static, String>,
    tree: Tree,
    node: layout::Node,
    renderer: iced::Renderer,
    colors: Colors,
}

impl InputHarness {
    fn new(placeholder: &str, value: &str, colors: Colors, backend: &str) -> Option<Self> {
        iced::advanced::graphics::text::font_system()
            .write()
            .expect("font system")
            .load_font(
                include_bytes!("../../../resources/fonts/Fira_Mono/FiraMono-Regular.ttf")
                    .as_slice()
                    .into(),
            );
        let renderer = iced::futures::executor::block_on(iced::Renderer::new(
            Font::with_name("Fira Mono"),
            14.into(),
            Some(backend),
        ))?;
        let input: Element<'_, String> = Input::new(placeholder, value, colors)
            .id("command")
            .on_input(std::convert::identity)
            .on_submit("submit".to_owned())
            .into();
        let tree = Tree::new(input.as_widget());
        let mut harness = Self {
            input,
            tree,
            node: layout::Node::default(),
            renderer,
            colors,
        };
        harness.layout();
        Some(harness)
    }

    fn layout(&mut self) {
        self.node = self
            .input
            .as_widget_mut()
            .layout(
                &mut self.tree,
                &self.renderer,
                &layout::Limits::new(
                    Size::ZERO,
                    Size::new((WIDTH - 8) as f32, (HEIGHT - 8) as f32),
                ),
            )
            .move_to(Point::new(4.0, 4.0));
    }

    fn focus(&mut self, position: usize) {
        self.input.as_widget_mut().operate(
            &mut self.tree,
            Layout::new(&self.node),
            &self.renderer,
            &mut operation::focusable::focus("command".into()),
        );
        self.input.as_widget_mut().operate(
            &mut self.tree,
            Layout::new(&self.node),
            &self.renderer,
            &mut operation::text_input::move_cursor_to("command".into(), position),
        );
        assert!(self
            .tree
            .state
            .downcast_ref::<State>()
            .input
            .state
            .downcast_ref::<InputState>()
            .is_focused());
    }

    fn event(&mut self, event: Event) -> Vec<String> {
        let mut messages = Vec::new();
        self.input.as_widget_mut().update(
            &mut self.tree,
            &event,
            Layout::new(&self.node),
            mouse::Cursor::Unavailable,
            &self.renderer,
            &mut clipboard::Null,
            &mut Shell::new(&mut messages),
            &Rectangle::with_size(Size::new(WIDTH as f32, HEIGHT as f32)),
        );
        messages
    }

    fn render(&mut self, scale: u32) -> Vec<[u8; 4]> {
        let viewport = Rectangle::with_size(Size::new(WIDTH as f32, HEIGHT as f32));
        self.renderer.reset(viewport);
        self.input.as_widget().draw(
            &self.tree,
            &mut self.renderer,
            &Mode::Light.theme(),
            &renderer::Style::default(),
            Layout::new(&self.node),
            mouse::Cursor::Unavailable,
            &viewport,
        );
        self.renderer
            .screenshot(
                Size::new(WIDTH * scale, HEIGHT * scale),
                scale as f32,
                self.colors.paper,
            )
            .as_chunks::<4>()
            .0
            .to_vec()
    }
}

#[test]
fn the_block_inverts_its_character_and_respects_blink_focus_selection_and_scale() {
    for backend in ["wgpu", "tiny-skia"] {
        for colors in [
            Mode::Light.colors(),
            Mode::Dark.colors(),
            Colors {
                ink: Color::from_rgb8(255, 205, 101),
                paper: Color::from_rgb8(39, 25, 59),
                ..Mode::Dark.colors()
            },
        ] {
            let Some(mut input) = InputHarness::new("", "help", colors, backend) else {
                eprintln!("Skipping {backend}: unavailable");
                continue;
            };
            let idle = input.render(1);
            input.focus(0);
            let visible = input.render(1);
            assert!(
                row(&visible, 5, 1)
                    .iter()
                    .filter(|&&pixel| pixel == colors.ink.into_rgba8())
                    .count()
                    >= 8,
                "the caret fills a character cell, {backend}"
            );
            assert!(
                idle.iter()
                    .zip(&visible)
                    .any(|(before, after)| *before == colors.ink.into_rgba8()
                        && *after == colors.paper.into_rgba8()),
                "the covered letter is reversed, {backend}"
            );
            let retina = input.render(2);
            assert!(
                row(&retina, 10, 2)
                    .iter()
                    .filter(|&&pixel| pixel == colors.ink.into_rgba8())
                    .count()
                    >= 16
            );

            let mut placeholder = InputHarness::new("help", "", colors, backend).expect("renderer");
            placeholder.focus(0);
            let empty = placeholder.render(1);
            for y in 4..22 {
                assert_eq!(
                    row(&empty, y, 1).get(4..12),
                    row(&visible, y, 1).get(4..12),
                    "placeholder text reverses cleanly too, {backend}",
                );
            }

            input.focus(0);
            let _ = input.event(Event::Window(window::Event::RedrawRequested(
                iced::time::Instant::now() + std::time::Duration::from_millis(750),
            )));
            assert_eq!(
                input.render(1),
                idle,
                "native blink hides the block, {backend}"
            );
            input.focus(0);
            let _ = input.event(Event::Window(window::Event::Unfocused));
            assert_eq!(
                input.render(1),
                idle,
                "an inactive window has no caret, {backend}"
            );

            input.focus(0);
            input
                .tree
                .state
                .downcast_mut::<State>()
                .input
                .state
                .downcast_mut::<InputState>()
                .select_range(0, 1);
            let selection = input.render(1);
            assert!(row(&selection, 5, 1).contains(&colors.rule.into_rgba8()));
            assert!(
                !row(&selection, 5, 1).contains(&colors.ink.into_rgba8()),
                "selection is not a block caret"
            );
        }
    }
}

#[test]
fn a_scrolled_line_keeps_the_whole_end_caret_inside_the_input() {
    for backend in ["wgpu", "tiny-skia"] {
        let colors = Mode::Dark.colors();
        let Some(mut input) = InputHarness::new("", &"long command ".repeat(20), colors, backend)
        else {
            continue;
        };
        input.focus(usize::MAX);
        let pixels = input.render(1);
        let cells: Vec<_> = row(&pixels, 5, 1)
            .iter()
            .enumerate()
            .filter_map(|(x, &pixel)| (pixel != colors.paper.into_rgba8()).then_some(x))
            .collect();
        assert!(
            cells.len() >= 8 && cells.len() <= 10,
            "full block at the end: {cells:?}, {backend}"
        );
        assert!(cells.iter().all(|&x| x > 200 && x < (WIDTH - 4) as usize));
    }
}

#[test]
fn focus_cursor_operations_and_editing_remain_native() {
    let Some(mut input) = InputHarness::new("", "help", Mode::Light.colors(), "tiny-skia") else {
        return;
    };
    input.focus(1);
    let messages: Vec<_> = iced_test::simulator::typewrite("X")
        .flat_map(|event| input.event(event))
        .collect();
    assert_eq!(messages, ["hXelp"]);
    let messages: Vec<_> = iced_test::simulator::tap_key(Named::Enter, None)
        .flat_map(|event| input.event(event))
        .collect();
    assert_eq!(messages, ["submit"]);
}

#[test]
fn font_and_size_changes_update_the_empty_caret_and_scroll_padding() {
    let colors = Mode::Light.colors();
    let Some(mut input) = InputHarness::new("", "", colors, "tiny-skia") else {
        return;
    };
    input.focus(0);
    for font in [
        Font::with_name("Fira Mono"),
        Font {
            family: iced::font::Family::Serif,
            ..Font::DEFAULT
        },
    ] {
        for size in [14.0, 20.0] {
            input.renderer = iced::futures::executor::block_on(iced::Renderer::new(
                font,
                size.into(),
                Some("tiny-skia"),
            ))
            .expect("renderer");
            // Rebuild the view while preserving its state, as typing or theme changes do.
            let rebuilt = Input::new("", "", colors)
                .id("command")
                .on_input(std::convert::identity);
            input.input = rebuilt.into();
            input.tree.diff(input.input.as_widget());
            input.layout();

            let measured = <iced::Renderer as TextRenderer>::Paragraph::with_text(text::Text {
                content: "  ",
                font,
                size: size.into(),
                line_height: text::LineHeight::default(),
                bounds: Size::INFINITE,
                align_x: text::Alignment::Default,
                align_y: Vertical::Center,
                shaping: text::Shaping::Advanced,
                wrapping: text::Wrapping::None,
            });
            let advance = measured.grapheme_position(0, 1).expect("space advance").x;
            assert!(advance > 0.0);
            let cached = input.tree.state.downcast_ref::<State>();
            assert_eq!(cached.space.raw().font(), font);
            assert!((cached.space.raw().size().0 - size).abs() < f32::EPSILON);
            let text_bounds = input.node.children().first().expect("text layout").bounds();
            assert!((input.node.size().width - text_bounds.width - 2.0 * advance).abs() < 0.001);

            let pixels = input.render(2);
            let block_width = row(&pixels, 10, 2)
                .iter()
                .filter(|&&pixel| pixel != colors.paper.into_rgba8())
                .count();
            assert!(
                (block_width as f32 - 2.0 * advance).abs() < 1.1,
                "cursor follows the font's space advance: {font:?}, size={size}"
            );
        }
    }
}

fn row(pixels: &[[u8; 4]], y: usize, scale: usize) -> &[[u8; 4]] {
    pixels
        .chunks_exact(WIDTH as usize * scale)
        .nth(y)
        .expect("pixel row")
}
