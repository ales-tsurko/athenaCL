//! Adapt Iced 0.14's caret drawing without copying its input implementation.

use iced::{
    advanced::{image, renderer, text, text::Paragraph as _},
    Background, Color, Font, Pixels, Point, Rectangle, Transformation,
};

/// Forwards drawing to the real renderer, expanding the caret and reversing its character.
pub(super) struct BlockRenderer<'a> {
    inner: &'a mut iced::Renderer,
    index: Option<usize>,
    clip: Rectangle,
    paper: Color,
    cell_width: f32,
    transformation: Option<Transformation>,
    caret: Option<(Rectangle, Background)>,
}

impl<'a> BlockRenderer<'a> {
    pub(super) fn new(
        inner: &'a mut iced::Renderer,
        index: Option<usize>,
        clip: Rectangle,
        paper: Color,
        cell_width: f32,
    ) -> Self {
        Self {
            inner,
            index,
            clip,
            paper,
            cell_width,
            transformation: None,
            caret: None,
        }
    }
}

impl renderer::Renderer for BlockRenderer<'_> {
    fn start_layer(&mut self, bounds: Rectangle) {
        self.inner.start_layer(bounds);
    }

    fn end_layer(&mut self) {
        self.inner.end_layer();
    }

    fn start_transformation(&mut self, transformation: Transformation) {
        self.transformation = Some(transformation);
        self.inner.start_transformation(transformation);
    }

    fn end_transformation(&mut self) {
        self.transformation = None;
        self.inner.end_transformation();
    }

    fn fill_quad(&mut self, quad: renderer::Quad, background: impl Into<Background>) {
        let background = background.into();
        // Iced 0.14 draws its caret/selection quad inside a scroll translation, followed by the
        // paragraph outside it. A selection is explicitly excluded, even if it is only 1px wide.
        if let (Some(_), Some(transformation)) = (self.index, self.transformation) {
            self.caret = Some((quad.bounds * transformation, background));
        } else {
            self.inner.fill_quad(quad, background);
        }
    }

    fn reset(&mut self, bounds: Rectangle) {
        self.inner.reset(bounds);
    }

    fn allocate_image(
        &mut self,
        handle: &image::Handle,
        callback: impl FnOnce(Result<image::Allocation, image::Error>) + Send + 'static,
    ) {
        self.inner.allocate_image(handle, callback);
    }
}

impl text::Renderer for BlockRenderer<'_> {
    type Editor = <iced::Renderer as text::Renderer>::Editor;
    type Font = Font;
    type Paragraph = <iced::Renderer as text::Renderer>::Paragraph;

    const ARROW_DOWN_ICON: char = <iced::Renderer as text::Renderer>::ARROW_DOWN_ICON;
    const CHECKMARK_ICON: char = <iced::Renderer as text::Renderer>::CHECKMARK_ICON;
    const ICED_LOGO: char = <iced::Renderer as text::Renderer>::ICED_LOGO;
    const ICON_FONT: Font = <iced::Renderer as text::Renderer>::ICON_FONT;
    const SCROLL_DOWN_ICON: char = <iced::Renderer as text::Renderer>::SCROLL_DOWN_ICON;
    const SCROLL_LEFT_ICON: char = <iced::Renderer as text::Renderer>::SCROLL_LEFT_ICON;
    const SCROLL_RIGHT_ICON: char = <iced::Renderer as text::Renderer>::SCROLL_RIGHT_ICON;
    const SCROLL_UP_ICON: char = <iced::Renderer as text::Renderer>::SCROLL_UP_ICON;

    fn default_font(&self) -> Font {
        self.inner.default_font()
    }

    fn default_size(&self) -> Pixels {
        self.inner.default_size()
    }

    fn fill_paragraph(
        &mut self,
        paragraph: &Self::Paragraph,
        position: Point,
        color: Color,
        clip: Rectangle,
    ) {
        use iced::advanced::Renderer as _;

        self.inner.fill_paragraph(paragraph, position, color, clip);
        let (Some(index), Some((mut caret, ink))) = (self.index, self.caret.take()) else {
            return;
        };
        caret.width = paragraph
            .grapheme_position(0, index)
            .zip(paragraph.grapheme_position(0, index + 1))
            .map(|(start, end)| end.x - start.x)
            .filter(|width| *width > 0.0)
            .unwrap_or(self.cell_width);
        if let Some(bounds) = caret.intersection(&self.clip) {
            // A separate layer puts the block above the original paragraph. Iced batches quads
            // before text within a layer; without this, dim placeholder text bleeds through it.
            self.inner.with_layer(self.clip, |renderer| {
                renderer.fill_quad(
                    renderer::Quad {
                        bounds,
                        snap: true,
                        ..renderer::Quad::default()
                    },
                    ink,
                );
                renderer.fill_paragraph(paragraph, position, self.paper, bounds);
            });
        }
    }

    fn fill_editor(
        &mut self,
        editor: &Self::Editor,
        position: Point,
        color: Color,
        clip: Rectangle,
    ) {
        self.inner.fill_editor(editor, position, color, clip);
    }

    fn fill_text(
        &mut self,
        text: text::Text<String>,
        position: Point,
        color: Color,
        clip: Rectangle,
    ) {
        self.inner.fill_text(text, position, color, clip);
    }
}
