//! A small, theme-colored list below the prompt; Tab pages through every match.

use iced::{
    widget::{button, column, container, row, text, Column},
    Element, Length,
};

use crate::app::{completion::Suggestions, theme::Colors};

const PAGE_SIZE: usize = 4;

impl Suggestions {
    pub(crate) fn view<'a, Message: Clone + 'a>(
        &'a self,
        colors: Colors,
        on_select: impl Fn(usize) -> Message,
    ) -> Option<Element<'a, Message>> {
        if !self.is_open() {
            return None;
        }
        let selected = self.selected.unwrap_or(0);
        let start = selected / PAGE_SIZE * PAGE_SIZE;
        let rows = self
            .candidates
            .iter()
            .enumerate()
            .skip(start)
            .take(PAGE_SIZE)
            .map(|(index, candidate)| {
                let chosen = index == selected;
                let ink = if chosen { colors.paper } else { colors.ink };
                let dim = if chosen { colors.paper } else { colors.dim };
                button(
                    row![
                        text(shorten(&candidate.label, 29)).color(ink).width(250),
                        text(shorten(&candidate.description, 49))
                            .color(dim)
                            .size(12),
                    ]
                    .spacing(12)
                    .align_y(iced::alignment::Vertical::Center),
                )
                .padding([4, 8])
                .width(Length::Fill)
                .style(colors.segment(chosen))
                .on_press(on_select(index))
                .into()
            });
        let hint = format!(
            "Tab complete · Shift+Tab previous · Esc dismiss    {}–{} / {}",
            start + 1,
            (start + PAGE_SIZE).min(self.candidates.len()),
            self.candidates.len(),
        );
        Some(
            column![
                container(Column::with_children(rows))
                    .padding(1)
                    .style(colors.frame()),
                text(hint).size(12).color(colors.dim),
            ]
            .spacing(6)
            .into(),
        )
    }
}

fn shorten(value: &str, limit: usize) -> String {
    if value.chars().count() <= limit {
        value.to_owned()
    } else {
        format!("{}…", value.chars().take(limit - 1).collect::<String>())
    }
}
