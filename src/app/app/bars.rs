//! The header and footer share dimensions, gutters, spacing and control styling.

use iced::{
    alignment::Vertical,
    widget::{column, container, row, space, text, text_input, tooltip, Row},
    Element, Length,
};

use crate::app::{
    app::{
        framed, picker, rule, rule_across, shorten, stepper, Message, State, BAR_SPACING,
        BOTTOM_BAR_HEIGHT, FRAME_HEIGHT, GROUP_SPACING, HEADER_HEIGHT, PATH_CHARACTERS,
        STEPPER_WIDTH, TEMPO_WIDTH, WINDOW_PADDING,
    },
    browser::Message as BrowserMessage,
    icons::Icon,
    pixel,
    theme::{Colors, Mode},
};

pub(super) enum Bar {
    Header,
    Footer,
}

impl Bar {
    pub(super) fn view(self, state: &State, colors: Colors) -> Element<'_, Message> {
        let (height, content) = match self {
            Self::Header => {
                let folder: Element<'_, Message> = {
                    Icon::folder(state.browser.visible)
                        .button(colors.toggle(state.browser.visible))
                        .width(FRAME_HEIGHT)
                        .height(FRAME_HEIGHT)
                        .on_press(Message::Browser(BrowserMessage::Toggle))
                        .into()
                };
                let appearance: Element<'_, Message> = {
                    let (icon, next_mode) = match state.mode {
                        Mode::Light => (Icon::CircleFilled, Mode::Dark),
                        Mode::Dark => (Icon::CircleOutline, Mode::Light),
                    };
                    tooltip(
                        icon.button(colors.outlined())
                            .width(FRAME_HEIGHT)
                            .height(FRAME_HEIGHT)
                            .on_press(Message::SetMode(next_mode)),
                        container(text(format!("Switch to {} mode", next_mode.name())).size(12))
                            .padding(6)
                            .style(colors.block(true)),
                        tooltip::Position::Bottom,
                    )
                    .delay(std::time::Duration::from_millis(500))
                    .into()
                };
                (
                    HEADER_HEIGHT,
                    row![
                        pixel::wordmark(colors.ink),
                        space::horizontal(),
                        state
                            .playback
                            .sound(
                                state.active_soundfont(),
                                state.player_state.loading_soundfont(),
                                colors
                            )
                            .map(Message::Playback),
                        group(row![
                            pixel::label("SCRATCH", colors.dim),
                            text(shorten(&state.scratch_dir, PATH_CHARACTERS)).size(12),
                            container(folder).id("toggle-file-browser"),
                        ]),
                        container(appearance).id("appearance-control"),
                    ],
                )
            }
            Self::Footer => {
                // The icon's final transparent column completes the same visible gap as
                // label-to-input.
                let tempo_label = row![Icon::Metronome, pixel::label("TEMPO", colors.dim)]
                    .spacing(BAR_SPACING - 1.0)
                    .align_y(Vertical::Center);

                // the tempo is typed, or stepped up and down
                let tempo = framed(
                    colors,
                    row![
                        text_input("", &state.tempo)
                            .on_input(Message::TempoChanged)
                            .style(colors.input())
                            .padding([0, 10])
                            .width(TEMPO_WIDTH)
                            .size(14),
                        rule_across(colors.ink),
                        column![
                            stepper(colors, Icon::ChevronUp, 1),
                            rule(colors.ink, 1.0),
                            stepper(colors, Icon::ChevronDown, -1),
                        ]
                        .width(STEPPER_WIDTH),
                    ],
                );
                (
                    BOTTOM_BAR_HEIGHT,
                    row![
                        group(row![
                            pixel::label("PATH", colors.dim),
                            picker(
                                colors,
                                &state.path_lib,
                                &state.active_path,
                                Message::PiSelected
                            ),
                        ]),
                        group(row![
                            pixel::label("TEXTURE", colors.dim),
                            picker(
                                colors,
                                &state.texture_lib,
                                &state.active_texture,
                                Message::TiSelected
                            ),
                        ]),
                        space::horizontal(),
                        group(row![tempo_label, container(tempo).id("tempo-control")]),
                        state.playback.volume(colors).map(Message::Playback),
                    ],
                )
            }
        };
        container(
            content
                .width(Length::Fill)
                .spacing(GROUP_SPACING)
                .align_y(Vertical::Center),
        )
        .padding([0.0, WINDOW_PADDING])
        .width(Length::Fill)
        .height(height)
        .align_y(Vertical::Center)
        .into()
    }
}

/// A label with its control, and the button that goes with them, spaced as one.
fn group<'a, M: 'a>(items: Row<'a, M>) -> Element<'a, M> {
    items.spacing(BAR_SPACING).align_y(Vertical::Center).into()
}
