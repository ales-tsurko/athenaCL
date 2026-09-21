//! Sound font menu and the master level, expressed with the app's common controls.

use std::{
    path::{Path, PathBuf},
    time::Duration,
};

use iced::{
    alignment::{Horizontal, Vertical},
    widget::{button, canvas::Canvas, column, container, row, space, text, tooltip, Column},
    Element, Length,
};
use iced_aw::{drop_down::Alignment, DropDown};

use crate::app::{
    app::{framed, rule_across, segment, BAR_SPACING, FRAME_HEIGHT},
    icons::Icon,
    pixel,
    playback::{preferences::STEPS, Preferences},
    segments,
    theme::Colors,
};

/// The volume's segments: as long as its frame allows beside the mute, and as high as a player's in
/// the log, so the two read as one kind of bar.
const METER_WIDTH: f32 = 144.0;
const SEGMENT_HEIGHT: f32 = 10.0;
/// The sound font menu's width: room for a name and the folder it is in.
const MENU_WIDTH: f32 = 360.0;

impl Preferences {
    pub(crate) fn volume(&self, colors: Colors) -> Element<'_, Message> {
        let muted = self.settings.muted;
        let meter = Canvas::new(segments::Slider {
            position: f64::from(self.settings.volume) / f64::from(STEPS),
            count: usize::from(STEPS),
            colors: Colors {
                lit: if muted { colors.unlit } else { colors.lit },
                ..colors
            },
            steps: Some(STEPS),
            on_change: Message::Volume,
        })
        .width(METER_WIDTH)
        .height(SEGMENT_HEIGHT);
        let level = tooltip(
            container(meter).padding([0, 10]).center_y(Length::Fill),
            container(
                text(format!(
                    "Volume {}%{}",
                    self.settings.percent(),
                    if muted { " (muted)" } else { "" }
                ))
                .size(12),
            )
            .padding(6)
            .style(colors.block(true)),
            tooltip::Position::Top,
        )
        .delay(Duration::from_millis(200));
        // the level and its mute share a frame, as the tempo and its steppers do
        let control = container(framed(
            colors,
            row![
                level,
                rule_across(colors.ink),
                container(segment("MUTE", colors, muted, Message::Mute)).id("master-mute"),
            ],
        ))
        .id("master-volume");
        // what is heard, shown beside its label as the metronome is beside the tempo's
        let icon = if muted { Icon::Muted } else { Icon::Speaker };
        let label = row![icon, pixel::label("VOLUME", colors.dim)]
            .spacing(BAR_SPACING - 1.0)
            .align_y(Vertical::Center);
        row![label, control]
            .spacing(BAR_SPACING)
            .align_y(Vertical::Center)
            .into()
    }

    pub(crate) fn sound(
        &self,
        active: Option<&Path>,
        loading: bool,
        colors: Colors,
    ) -> Element<'_, Message> {
        let name = if loading {
            "Loading…".into()
        } else {
            font_name(active)
        };
        let label = text(crate::app::app::shorten(&name, 20))
            .size(12)
            .wrapping(text::Wrapping::None);
        let button = container(
            Icon::SoundFont
                .button(colors.toggle(self.menu_open))
                .width(FRAME_HEIGHT)
                .height(FRAME_HEIGHT)
                .on_press(Message::Menu(!self.menu_open)),
        )
        .id("soundfont-button");
        let content = row![pixel::label("SOUND", colors.dim), label, button]
            .spacing(BAR_SPACING)
            .align_y(Vertical::Center);
        // the menu drops centered under what it opens from: as wide as the menu, with the group at
        // its end, that is under the button, reaching back under the label
        let content = container(content)
            .width(MENU_WIDTH)
            .align_x(Horizontal::Right);
        DropDown::new(content, self.menu(active, colors), self.menu_open)
            .width(MENU_WIDTH)
            .alignment(Alignment::Bottom)
            .offset(14.0)
            .on_dismiss(Message::Menu(false))
            .into()
    }

    fn menu(&self, active: Option<&Path>, colors: Colors) -> Element<'_, Message> {
        let mut entries = Column::new().push(self.font_row(None, active.is_none(), colors));
        for path in &self.settings.recent {
            entries =
                entries.push(self.font_row(Some(path), active == Some(path.as_path()), colors));
        }
        let separator = container(container(space()).height(1).width(Length::Fill).style(
            move |_| container::Style {
                background: Some(colors.rule.into()),
                ..Default::default()
            },
        ))
        .padding([4, 0]);
        let load = button(row![
            text("Load sound font…").size(12),
            space::horizontal(),
            text(".sf2").size(11).color(colors.dim)
        ])
        .padding([6, 10])
        .width(Length::Fill)
        .style(colors.bare())
        .on_press(Message::Choose);
        container(column![entries, separator, load])
            .padding(4)
            .width(MENU_WIDTH)
            .style(move |theme| container::Style {
                background: Some(colors.paper.into()),
                text_color: Some(colors.ink),
                ..colors.frame()(theme)
            })
            .into()
    }

    fn font_row(&self, path: Option<&Path>, active: bool, colors: Colors) -> Element<'_, Message> {
        let folder = path.map_or_else(
            || "built in".into(),
            |path| {
                let parent = path.parent().unwrap_or(path);
                let display = std::env::home_dir()
                    .and_then(|home| {
                        parent
                            .strip_prefix(home)
                            .ok()
                            .map(|p| format!("~/{}", p.display()))
                    })
                    .unwrap_or_else(|| parent.display().to_string());
                crate::app::app::shorten(&display, 20)
            },
        );
        let ink = if active { colors.paper } else { colors.ink };
        let dim = if active { colors.paper } else { colors.dim };
        let row = row![
            text(crate::app::app::shorten(&font_name(path), 22))
                .size(12)
                .color(ink),
            space::horizontal(),
            text(folder).size(11).color(dim)
        ]
        .spacing(12);
        button(row)
            .padding([6, 10])
            .width(Length::Fill)
            .style(colors.segment(active))
            .on_press(Message::Select(path.map(Path::to_owned)))
            .into()
    }
}

fn font_name(path: Option<&Path>) -> String {
    path.map_or_else(
        || "Yamaha Grand".into(),
        |path| {
            path.file_stem()
                .unwrap_or_default()
                .to_string_lossy()
                .into_owned()
        },
    )
}

#[derive(Debug, Clone)]
pub enum Message {
    Volume(f64),
    Mute,
    Menu(bool),
    Choose,
    Select(Option<PathBuf>),
    Chosen(Option<PathBuf>),
    Saved(Result<(), String>),
}
