//! The app's look: black and white type, light or dark.
//!
//! Dark mode inverts light mode, except for the blocks (figure plates, the query panel, the error
//! tag, the play button), which stay dark, a step lighter than the page, and what's lit (played
//! segments, the cursor), which dims to grey.

use iced::{
    border,
    theme::Palette as IcedPalette,
    widget::{button, container, pick_list, scrollable, text_input},
    Background, Border, Color, Shadow, Theme,
};

use super::figure::Palette;

/// The app's two looks.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum Mode {
    /// Ink on paper.
    #[default]
    Light,
    /// Paper-colored ink on a dark page.
    Dark,
}

impl Mode {
    /// The look saved in athenaCL's preferences as `name`: `light` or `dark`.
    pub(crate) fn from_name(name: &str) -> Option<Self> {
        match name.trim() {
            "light" => Some(Self::Light),
            "dark" => Some(Self::Dark),
            _ => None,
        }
    }

    /// The name athenaCL's preferences save the look as.
    pub(crate) fn name(self) -> &'static str {
        match self {
            Self::Light => "light",
            Self::Dark => "dark",
        }
    }

    /// The look's colors.
    pub(crate) fn colors(self) -> Colors {
        match self {
            Self::Light => LIGHT,
            Self::Dark => DARK,
        }
    }

    /// The iced theme, for what widgets draw by default: text, selections, the window.
    pub(crate) fn theme(self) -> Theme {
        let colors = self.colors();
        Theme::custom(
            format!("athenaCL {}", self.name()),
            IcedPalette {
                background: colors.paper,
                text: colors.ink,
                primary: colors.ink,
                success: colors.ink,
                warning: colors.ink,
                danger: colors.ink,
            },
        )
    }
}

/// The colors of a look.
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct Colors {
    /// The page.
    pub(crate) paper: Color,
    /// Text and rules.
    pub(crate) ink: Color,
    /// Secondary text: labels, prompts.
    pub(crate) dim: Color,
    /// Faint rules: the scrollbar's track.
    pub(crate) rule: Color,
    /// What's lit: played segments, the cursor.
    pub(crate) lit: Color,
    /// What isn't lit: unplayed segments.
    pub(crate) unlit: Color,
    /// Blocks: figure plates, the query panel, the error tag, the play button.
    pub(crate) block: Color,
    /// Grid lines on a block.
    pub(crate) block_grid: Color,
    /// Text and marks on a block.
    pub(crate) on_block: Color,
    /// What the pointer is over, in a figure.
    pub(crate) hover: Color,
    /// Staff lines.
    pub(crate) staff: Color,
}

const LIGHT: Colors = Colors {
    paper: Color::from_rgb8(0xfa, 0xfa, 0xf8),
    ink: Color::from_rgb8(0x0a, 0x0a, 0x0a),
    dim: Color::from_rgb8(0x5e, 0x5e, 0x5b),
    rule: Color::from_rgb8(0xd8, 0xd8, 0xd4),
    lit: Color::from_rgb8(0x0a, 0x0a, 0x0a),
    unlit: Color::from_rgb8(0xda, 0xda, 0xd6),
    block: Color::from_rgb8(0x0a, 0x0a, 0x0a),
    block_grid: Color::from_rgb8(0x2b, 0x2b, 0x2b),
    on_block: Color::from_rgb8(0xfa, 0xfa, 0xf8),
    hover: Color::from_rgb8(0x8a, 0x8a, 0x86),
    staff: Color::from_rgb8(0x6a, 0x6a, 0x66),
};

const DARK: Colors = Colors {
    paper: Color::from_rgb8(0x0b, 0x0b, 0x0a),
    ink: Color::from_rgb8(0xec, 0xeb, 0xe6),
    dim: Color::from_rgb8(0x92, 0x92, 0x8e),
    rule: Color::from_rgb8(0x2a, 0x2a, 0x28),
    lit: Color::from_rgb8(0x8a, 0x8a, 0x86),
    unlit: Color::from_rgb8(0x2e, 0x2e, 0x2c),
    block: Color::from_rgb8(0x19, 0x19, 0x18),
    block_grid: Color::from_rgb8(0x33, 0x33, 0x31),
    on_block: Color::from_rgb8(0xec, 0xeb, 0xe6),
    hover: Color::from_rgb8(0x8a, 0x8a, 0x86),
    staff: Color::from_rgb8(0x6a, 0x6a, 0x66),
};

impl Colors {
    /// The colors figures are drawn in.
    pub(crate) fn figure(self) -> Palette {
        Palette {
            page: self.paper,
            plate: self.block,
            grid: self.block_grid,
            major: mix(self.block_grid, self.hover, 0.35),
            mark: self.on_block,
            alt: self.hover,
            hover: self.hover,
            label: self.ink,
            title: self.dim,
            staff: self.staff,
            track: self.rule,
        }
    }

    /// An outlined button: the folder, the pickers' look.
    pub(crate) fn outlined(self) -> impl Fn(&Theme, button::Status) -> button::Style {
        move |_, status| button::Style {
            background: Some(Background::Color(match status {
                button::Status::Hovered | button::Status::Pressed => self.rule,
                button::Status::Active | button::Status::Disabled => self.paper,
            })),
            text_color: self.ink,
            border: self.border(1.0),
            shadow: Shadow::default(),
            snap: true,
        }
    }

    /// A block button: the play button.
    pub(crate) fn block_button(self) -> impl Fn(&Theme, button::Status) -> button::Style {
        move |_, status| button::Style {
            background: Some(Background::Color(match status {
                button::Status::Disabled => self.rule,
                _ => self.block,
            })),
            text_color: self.on_block,
            border: self.border(1.0),
            shadow: Shadow::default(),
            snap: true,
        }
    }

    /// A segment of a switch: filled with ink when it's the one chosen.
    pub(crate) fn segment(self, chosen: bool) -> impl Fn(&Theme, button::Status) -> button::Style {
        move |_, status| {
            let background = match (chosen, status) {
                (true, _) => self.ink,
                (false, button::Status::Hovered | button::Status::Pressed) => self.rule,
                (false, _) => self.paper,
            };
            button::Style {
                background: Some(Background::Color(background)),
                text_color: if chosen { self.paper } else { self.ink },
                border: Border::default(),
                shadow: Shadow::default(),
                snap: true,
            }
        }
    }

    /// A bare button: the tempo's steppers.
    pub(crate) fn bare(self) -> impl Fn(&Theme, button::Status) -> button::Style {
        move |_, status| button::Style {
            background: match status {
                button::Status::Hovered | button::Status::Pressed => {
                    Some(Background::Color(self.rule))
                }
                _ => None,
            },
            text_color: self.ink,
            border: Border::default(),
            shadow: Shadow::default(),
            snap: true,
        }
    }

    /// A 1 pixel ink frame, as around buttons and switches.
    pub(crate) fn frame(self) -> impl Fn(&Theme) -> container::Style {
        move |_| container::Style {
            border: self.border(1.0),
            ..container::Style::default()
        }
    }

    /// A block: the query panel, the error tag.
    pub(crate) fn block(self, framed: bool) -> impl Fn(&Theme) -> container::Style {
        move |_| container::Style {
            text_color: Some(self.on_block),
            background: Some(Background::Color(self.block)),
            border: if framed {
                self.border(1.0)
            } else {
                Border::default()
            },
            ..container::Style::default()
        }
    }

    /// A rule of `color`: a container filled with it.
    pub(crate) fn fill(color: Color) -> impl Fn(&Theme) -> container::Style {
        move |_| container::Style {
            background: Some(Background::Color(color)),
            ..container::Style::default()
        }
    }

    /// The input: no box, only its text.
    pub(crate) fn input(self) -> impl Fn(&Theme, text_input::Status) -> text_input::Style {
        move |_, _| text_input::Style {
            background: Background::Color(Color::TRANSPARENT),
            border: Border::default(),
            icon: self.ink,
            placeholder: self.dim,
            value: self.ink,
            selection: self.rule,
        }
    }

    /// An outlined picker.
    pub(crate) fn picker(self) -> impl Fn(&Theme, pick_list::Status) -> pick_list::Style {
        move |_, status| pick_list::Style {
            text_color: self.ink,
            placeholder_color: self.dim,
            handle_color: self.ink,
            background: Background::Color(match status {
                pick_list::Status::Hovered | pick_list::Status::Opened { .. } => self.rule,
                pick_list::Status::Active => self.paper,
            }),
            border: self.border(1.0),
        }
    }

    /// A picker's menu.
    pub(crate) fn menu(self) -> impl Fn(&Theme) -> iced::overlay::menu::Style {
        move |_| iced::overlay::menu::Style {
            background: Background::Color(self.paper),
            border: self.border(1.0),
            text_color: self.ink,
            selected_text_color: self.paper,
            selected_background: Background::Color(self.ink),
            shadow: Shadow::default(),
        }
    }

    /// The output's scrollbar: a hairline track with a thin ink thumb.
    pub(crate) fn scrollbar(self) -> impl Fn(&Theme, scrollable::Status) -> scrollable::Style {
        move |theme, status| {
            let rail = scrollable::Rail {
                background: Some(Background::Color(self.rule)),
                border: Border::default(),
                scroller: scrollable::Scroller {
                    background: Background::Color(self.ink),
                    border: Border::default(),
                },
            };
            scrollable::Style {
                container: container::Style::default(),
                vertical_rail: rail,
                horizontal_rail: rail,
                gap: None,
                ..scrollable::default(theme, status)
            }
        }
    }

    fn border(self, width: f32) -> Border {
        Border {
            color: self.ink,
            width,
            radius: border::Radius::default(),
        }
    }
}

/// A color `amount` of the way from `from` to `to`.
fn mix(from: Color, to: Color, amount: f32) -> Color {
    let blend = |a: f32, b: f32| a + (b - a) * amount;
    Color::from_rgb(
        blend(from.r, to.r),
        blend(from.g, to.g),
        blend(from.b, to.b),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn looks_are_saved_by_name() {
        for mode in [Mode::Light, Mode::Dark] {
            assert_eq!(Mode::from_name(mode.name()), Some(mode));
        }
        assert_eq!(Mode::from_name(" dark\n"), Some(Mode::Dark));
        assert_eq!(Mode::from_name("sepia"), None);
    }

    #[test]
    fn dark_mode_keeps_blocks_dark() {
        let dark = Mode::Dark.colors();
        assert_eq!(dark.block, Color::from_rgb8(0x19, 0x19, 0x18));
        assert_eq!(dark.on_block, dark.ink);
        let light = Mode::Light.colors();
        assert_eq!(light.block, light.ink);
        assert_eq!(light.on_block, light.paper);
    }

    #[test]
    fn mixing_goes_between_colors() {
        let gray = mix(Color::BLACK, Color::WHITE, 0.5);
        assert!((gray.r - 0.5).abs() < 1e-6 && (gray.b - 0.5).abs() < 1e-6);
    }
}
