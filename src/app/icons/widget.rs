//! Layout and drawing shared by every icon, including its button's foreground color.

use iced::{
    advanced::{
        image,
        layout::{self, Layout},
        mouse, renderer,
        widget::{tree, Tree, Widget},
    },
    widget::{button, container, Button},
    Element, Length, Rectangle, Size, Theme,
};

use crate::app::icons::{cache::Cache, Icon};

impl Icon {
    /// A button with this icon centered in its available space.
    pub(crate) fn button<'a, Message: 'a>(
        self,
        style: impl Fn(&Theme, button::Status) -> button::Style + 'a,
    ) -> Button<'a, Message> {
        button(container(self).center(Length::Fill))
            .padding(0)
            .style(style)
    }

    /// One logical screen pixel per cell; display scaling is handled by the renderer.
    fn extent(self) -> f32 {
        self.rows().len() as f32
    }
}

impl<Message, Theme, Renderer> Widget<Message, Theme, Renderer> for Icon
where
    Renderer: image::Renderer<Handle = image::Handle>,
{
    fn tag(&self) -> tree::Tag {
        tree::Tag::of::<Cache>()
    }

    fn state(&self) -> tree::State {
        tree::State::new(Cache::default())
    }

    fn size(&self) -> Size<Length> {
        Size::new(Length::Fixed(self.extent()), Length::Fixed(self.extent()))
    }

    fn layout(
        &mut self,
        _tree: &mut Tree,
        _renderer: &Renderer,
        limits: &layout::Limits,
    ) -> layout::Node {
        layout::Node::new(limits.resolve(
            Length::Fixed(self.extent()),
            Length::Fixed(self.extent()),
            Size::ZERO,
        ))
    }

    fn draw(
        &self,
        tree: &Tree,
        renderer: &mut Renderer,
        _theme: &Theme,
        style: &renderer::Style,
        layout: Layout<'_>,
        _cursor: mouse::Cursor,
        viewport: &Rectangle,
    ) {
        let bounds = layout.bounds();
        let Some(clip) = bounds.intersection(viewport) else {
            return;
        };

        let handle = tree
            .state
            .downcast_ref::<Cache>()
            .image(*self, style.text_color);
        renderer.draw_image(
            image::Image::new(handle)
                .filter_method(image::FilterMethod::Nearest)
                .snap(true),
            Rectangle {
                width: self.extent(),
                height: self.extent(),
                ..bounds
            },
            clip,
        );
    }
}

impl<'a, Message, Theme, Renderer> From<Icon> for Element<'a, Message, Theme, Renderer>
where
    Renderer: image::Renderer<Handle = image::Handle> + 'a,
{
    fn from(icon: Icon) -> Self {
        Self::new(icon)
    }
}

#[cfg(test)]
mod tests {
    use iced::{
        advanced::renderer::{Headless, Renderer as _},
        Color, Font, Point,
    };

    use super::*;
    use crate::app::theme::Mode;

    #[test]
    fn rebuilding_the_view_retains_the_cached_image() {
        let element: Element<'_, ()> = Icon::Play.into();
        let mut tree = Tree::new(element.as_widget());
        let original = tree
            .state
            .downcast_ref::<Cache>()
            .image(Icon::Play, Color::WHITE)
            .id();
        for _ in 0..120 {
            let rebuilt: Element<'_, ()> = Icon::Play.into();
            tree.diff(rebuilt.as_widget());
            assert_eq!(
                tree.state
                    .downcast_ref::<Cache>()
                    .image(Icon::Play, Color::WHITE)
                    .id(),
                original
            );
        }
    }

    #[test]
    fn gpu_icons_inherit_button_ink_and_stay_sharp_at_display_scales() {
        check_rendering("wgpu");
    }

    #[test]
    fn software_icons_inherit_button_ink_and_stay_sharp_at_display_scales() {
        check_rendering("tiny-skia");
    }

    fn check_rendering(backend: &str) {
        let Some(mut renderer) = iced::futures::executor::block_on(iced::Renderer::new(
            Font::DEFAULT,
            14.into(),
            Some(backend),
        )) else {
            eprintln!("Skipping image rendering check: {backend} is unavailable");
            return;
        };
        let viewport = Rectangle::with_size(Size::new(48.0, 48.0));

        let themes = [
            Mode::Light.theme(),
            Mode::Dark.theme(),
            Theme::custom(
                "Custom coloured palette".to_owned(),
                iced::theme::Palette {
                    background: Color::from_rgb8(39, 25, 59),
                    text: Color::from_rgb8(255, 205, 101),
                    ..Theme::Dark.palette()
                },
            ),
        ];
        for theme in themes {
            let colors = theme.palette();
            for selected in [false, true] {
                let (ink, paper) = if selected {
                    (colors.background, colors.text)
                } else {
                    (colors.text, colors.background)
                };
                for icon in [
                    Icon::Metronome,
                    Icon::Folder,
                    Icon::FolderOpen,
                    Icon::CircleOutline,
                    Icon::CircleFilled,
                    Icon::Play,
                    Icon::Pause,
                    Icon::Speaker,
                    Icon::Muted,
                    Icon::SoundFont,
                    Icon::ChevronUp,
                    Icon::ChevronDown,
                ] {
                    let side = match icon {
                        Icon::ChevronUp | Icon::ChevronDown => 8.0,
                        _ => 16.0,
                    };
                    assert!(icon.rows().iter().all(|row| row.len() == icon.rows().len()));
                    let size = <Icon as Widget<(), Theme, iced::Renderer>>::size(&icon);
                    assert_eq!(size, Size::new(Length::Fixed(side), Length::Fixed(side)));

                    let mut element: Element<'_, ()> = icon
                        .button(move |_, _| button::Style {
                            text_color: ink,
                            ..button::Style::default()
                        })
                        .width(36)
                        .height(36)
                        .on_press(())
                        .into();
                    let mut tree = Tree::new(element.as_widget());
                    let node = element
                        .as_widget_mut()
                        .layout(
                            &mut tree,
                            &renderer,
                            &layout::Limits::new(Size::ZERO, viewport.size()),
                        )
                        .move_to(Point::new(4.25, 4.75));
                    renderer.reset(viewport);
                    element.as_widget().draw(
                        &tree,
                        &mut renderer,
                        &theme,
                        &renderer::Style {
                            text_color: Color::from_rgb(1.0, 0.0, 0.0),
                        },
                        Layout::new(&node),
                        mouse::Cursor::Unavailable,
                        &viewport,
                    );

                    for (scale, size) in [(1.0, 48), (1.25, 60), (1.5, 72), (2.0, 96), (3.0, 144)] {
                        let pixels = renderer.screenshot(Size::new(size, size), scale, paper);
                        let pixels = pixels.as_chunks::<4>().0;
                        let ink = ink.into_rgba8();
                        let paper = paper.into_rgba8();
                        assert!(
                            pixels.contains(&ink),
                            "{icon:?}, {theme:?}, selected={selected}, scale={scale}: missing ink"
                        );
                        assert!(pixels.iter().all(|&pixel| pixel == ink || pixel == paper));
                    }
                }
            }
        }
    }
}
