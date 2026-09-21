//! Scratch tree and its context menus, using the same colors, pixel labels and icons as the log.

use std::path::Path;

use iced::{
    alignment::Vertical,
    keyboard::Modifiers,
    mouse::Interaction,
    widget::{
        button, column, container, mouse_area, row, scrollable, space, text, text_input, tooltip,
        Column,
    },
    Color, Element, Length, Padding,
};
use iced_aw::ContextMenu;

use crate::app::{
    app::{segment, switch},
    browser::{
        filesystem::{Entry, Kind},
        input::Input,
        state::{Browser, Edit, Message, NAME_INPUT, TREE},
    },
    icons::Icon,
    pixel, scrollbar,
    theme::Colors,
};

/// The size of names, and of everything else the panel says.
const TEXT: f32 = 12.0;
/// A row's room around its mark and name, and how far each level of the tree is indented.
const ROW: [f32; 2] = [4.0, 6.0];
const INDENT: f32 = 14.0;
/// The width of a row's mark: a folder's icon, or a file's type.
const MARK: f32 = 16.0;
/// How long the pointer rests on a row before its whole name shows.
const NAME_DELAY: std::time::Duration = std::time::Duration::from_millis(800);

/// The keys of the context menu's actions, as the keyboard's modifier is named where it runs.
const COPY_KEYS: &str = if cfg!(target_os = "macos") {
    "Cmd+C"
} else {
    "Ctrl+C"
};
const PASTE_KEYS: &str = if cfg!(target_os = "macos") {
    "Cmd+V"
} else {
    "Ctrl+V"
};
const NEW_FOLDER_KEYS: &str = if cfg!(target_os = "macos") {
    "Shift+Cmd+N"
} else {
    "Shift+Ctrl+N"
};

impl Browser {
    pub(crate) fn divider(&self, colors: Colors) -> Element<'_, Message> {
        self.width.divider(colors)
    }

    pub(crate) fn view(&self, colors: Colors) -> Element<'_, Message> {
        let actions = switch(
            colors,
            [
                tip(
                    container(segment("REFRESH", colors, false, Message::Refresh))
                        .id("browser-refresh"),
                    "Read the folder again",
                    colors,
                ),
                tip(
                    container(segment(
                        "FOLDER...",
                        colors,
                        false,
                        (!self.busy).then_some(Message::ChooseRoot),
                    ))
                    .id("browser-change-folder"),
                    "Choose the scratch folder",
                    colors,
                ),
            ],
        );
        // the label lines up with the tree's marks
        let title = row![
            pixel::label("FILES", colors.dim),
            space::horizontal(),
            actions
        ]
        .align_y(Vertical::Center)
        .padding(Padding::ZERO.left(ROW[1]));

        let mut tree = Column::new().width(Length::Fill);
        tree = tree.push(self.root_row(colors));
        for entry in &self.listing.entries {
            tree = tree.push(self.entry(entry, colors));
        }
        if self.listing.entries.is_empty() {
            let message = if self.root.as_os_str().is_empty() {
                "Choose a scratch folder."
            } else if self.scanning {
                "Reading folder…"
            } else {
                "No readable files."
            };
            tree = tree.push(note(message, colors));
        }
        for error in &self.listing.errors {
            tree = tree.push(note(error, colors));
        }

        let mut panel = column![
            title,
            scrollable(tree)
                .id(TREE)
                .direction(scrollable::Direction::Vertical(scrollbar::vertical()))
                .height(Length::Fill)
                .style(colors.scrollbar()),
        ]
        .spacing(10)
        .padding(Padding::new(12.0).left(0))
        .width(self.width.get())
        .height(Length::Fill);
        if let Some(edit) = &self.edit {
            panel = panel.push(self.form(edit, colors));
        }
        let status = if self.busy {
            Some("Working…".to_owned())
        } else if let Some(status) = &self.status {
            Some(status.clone())
        } else if self.selected.len() > 1 {
            Some(format!("{} selected", self.selected.len()))
        } else {
            None
        };
        if let Some(status) = status {
            panel = panel.push(
                container(text(status).size(TEXT).color(colors.dim))
                    .padding(Padding::ZERO.left(ROW[1])),
            );
        }
        Input::new(panel).dragging(self, colors).into()
    }

    /// The scratch folder itself, at the top of the tree: where things are pasted, made and
    /// dragged to be at its top level.
    fn root_row(&self, colors: Colors) -> Element<'_, Message> {
        let name = self.root.file_name().map_or_else(
            || "Scratch folder".to_owned(),
            |name| name.to_string_lossy().into_owned(),
        );
        let line = container(
            row![
                Icon::FolderOpen,
                text(name).size(TEXT).wrapping(text::Wrapping::None)
            ]
            .spacing(6)
            .align_y(Vertical::Center),
        )
        .padding(indented(0))
        .width(Length::Fill)
        .clip(true)
        .style(move |_| container::Style {
            text_color: Some(colors.ink),
            ..container::Style::default()
        });
        Input::new(ContextMenu::new(line, move || {
            self.menu(&self.root, true, colors)
        }))
        .context(self.root.clone())
        .into()
    }

    fn entry<'a>(&'a self, entry: &'a Entry, colors: Colors) -> Element<'a, Message> {
        let folder = entry.kind == Kind::Folder;
        let selected = self.selected.contains(&entry.path);
        // a selection the keys act on is inked; one they do not is only shaded
        let (fill, ink, dim) = match (selected, self.focused) {
            (true, true) => (Some(colors.ink), colors.paper, colors.paper),
            (true, false) => (Some(colors.rule), colors.ink, colors.dim),
            (false, _) => (None, colors.ink, colors.dim),
        };
        let mark: Element<'_, Message> = if folder {
            Icon::folder(self.expanded.contains(&entry.path)).into()
        } else {
            container(pixel::label(tag(entry.kind), dim))
                .center_x(MARK)
                .into()
        };
        let line = container(
            row![
                mark,
                text(entry.name()).size(TEXT).wrapping(text::Wrapping::None)
            ]
            .spacing(6)
            .align_y(Vertical::Center),
        )
        // under the scratch folder's own row
        .padding(indented(entry.depth.min(8) + 1))
        .width(Length::Fill)
        .clip(true)
        .style(move |_| container::Style {
            text_color: Some(ink),
            background: fill.map(Into::into),
            ..container::Style::default()
        });
        let content = mouse_area(line)
            .interaction(Interaction::Pointer)
            .on_press(Message::Click(
                entry.path.clone(),
                Modifiers::empty(),
                false,
            ))
            .on_double_click(Message::Click(entry.path.clone(), Modifiers::empty(), true));
        let menu = ContextMenu::new(content, move || self.menu(&entry.path, folder, colors));
        tooltip(
            Input::new(menu)
                .context(entry.path.clone())
                .hover(shade(colors)),
            container(text(entry.name()).size(TEXT))
                .padding(6)
                .style(colors.block(true)),
            tooltip::Position::Bottom,
        )
        .delay(NAME_DELAY)
        .into()
    }

    fn menu<'a>(&'a self, path: &'a Path, folder: bool, colors: Colors) -> Element<'a, Message> {
        let directory = self.directory_for(Some(path));
        let action = |label: &'static str, keys: &'static str, message, enabled: bool| {
            let enabled = enabled && !self.busy;
            let ink = if enabled { colors.ink } else { colors.dim };
            button(
                row![
                    text(label).size(TEXT).color(ink),
                    space::horizontal(),
                    text(keys).size(11).color(colors.dim),
                ]
                .spacing(12)
                .align_y(Vertical::Center),
            )
            .padding([6, 10])
            .width(Length::Fill)
            .on_press_maybe(enabled.then_some(message))
            .style(colors.bare())
        };
        let separator = || {
            container(
                container(space())
                    .width(Length::Fill)
                    .height(1)
                    .style(Colors::fill(colors.rule)),
            )
            .padding([4, 0])
        };
        let mut menu = column![];
        if path != self.root {
            menu = menu
                .push(action(
                    if folder { "Expand / collapse" } else { "Open" },
                    "Enter",
                    Message::Open(path.into()),
                    true,
                ))
                .push(separator())
                .push(action("Copy", COPY_KEYS, Message::Copy(path.into()), true))
                .push(action(
                    "Rename…",
                    "F2",
                    Message::Edit(Edit::Rename(path.into())),
                    !self.selected.contains(path) || self.selected.len() == 1,
                ))
                .push(action(
                    "Delete…",
                    "Delete",
                    Message::Edit(Edit::Delete(self.selected.targets(path))),
                    true,
                ))
                .push(separator());
        }
        menu = menu
            .push(action(
                "Paste",
                PASTE_KEYS,
                Message::Paste(directory.clone()),
                !self.clipboard.is_empty(),
            ))
            .push(action(
                "New folder…",
                NEW_FOLDER_KEYS,
                Message::Edit(Edit::CreateFolder(directory)),
                true,
            ));
        Input::new(
            container(menu)
                .padding(4)
                .width(230)
                .style(move |theme| container::Style {
                    background: Some(colors.paper.into()),
                    text_color: Some(colors.ink),
                    ..colors.frame()(theme)
                }),
        )
        .menu()
        .into()
    }

    fn form<'a>(&'a self, edit: &'a Edit, colors: Colors) -> Element<'a, Message> {
        let (title, confirm) = match edit {
            Edit::Rename(_) => ("RENAME", "RENAME"),
            Edit::CreateFolder(_) => ("NEW FOLDER", "CREATE"),
            Edit::Delete(_) => ("DELETE PERMANENTLY?", "DELETE"),
        };
        let mut form = column![pixel::label(title, colors.dim)].spacing(10);
        if let Edit::Delete(paths) = edit {
            let target = if let [path] = paths.as_slice() {
                path.file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into_owned()
            } else {
                format!("{} selected items", paths.len())
            };
            form = form.push(
                text(format!(
                    "{target}\nIncluding folder contents. This cannot be undone."
                ))
                .size(TEXT),
            );
        } else {
            form = form.push(
                container(
                    text_input("Name", &self.name)
                        .id(NAME_INPUT)
                        .on_input_maybe((!self.busy).then_some(Message::Name))
                        .on_submit(Message::Confirm)
                        .style(colors.input())
                        .size(TEXT),
                )
                .padding(6)
                .style(colors.frame()),
            );
        }
        // the action is taken as a question's picked answer is: with return, or its button
        let enabled = !self.busy && (matches!(edit, Edit::Delete(_)) || !self.name.is_empty());
        let buttons = switch(
            colors,
            [
                container(segment(
                    confirm,
                    colors,
                    enabled,
                    enabled.then_some(Message::Confirm),
                ))
                .id("browser-confirm")
                .into(),
                segment(
                    "CANCEL",
                    colors,
                    false,
                    (!self.busy).then_some(Message::Cancel),
                ),
            ],
        );
        container(form.push(row![space::horizontal(), buttons]))
            .id("browser-confirmation")
            .padding(12)
            .width(Length::Fill)
            .style(move |theme| container::Style {
                background: Some(colors.rule.into()),
                text_color: Some(colors.ink),
                ..colors.frame()(theme)
            })
            .into()
    }
}

/// A row's room, `depth` levels into the tree.
fn indented(depth: usize) -> Padding {
    Padding::from(ROW).left(ROW[1] + depth as f32 * INDENT)
}

/// What a file is, as the micro font names it beside it.
fn tag(kind: Kind) -> &'static str {
    match kind {
        Kind::Athena => "AO",
        Kind::Midi => "MI",
        Kind::Audio => "AU",
        Kind::Text | Kind::Folder => "TX",
    }
}

/// A line of the tree that is not an entry: why there are none, or what could not be read.
fn note<'a>(message: &str, colors: Colors) -> Element<'a, Message> {
    container(text(message.to_owned()).size(TEXT).color(colors.dim))
        .padding(indented(1))
        .into()
}

/// What a row is shaded with under the pointer: halfway from the page to the rule.
fn shade(colors: Colors) -> Color {
    let half = |page: f32, rule: f32| (page + rule) / 2.0;
    Color::from_rgb(
        half(colors.paper.r, colors.rule.r),
        half(colors.paper.g, colors.rule.g),
        half(colors.paper.b, colors.rule.b),
    )
}

/// `content`, and what it does in words when the pointer rests on it.
fn tip<'a>(
    content: impl Into<Element<'a, Message>>,
    words: &'a str,
    colors: Colors,
) -> Element<'a, Message> {
    tooltip(
        content,
        container(text(words).size(TEXT))
            .padding(6)
            .style(colors.block(true)),
        tooltip::Position::Bottom,
    )
    .delay(std::time::Duration::from_millis(500))
    .into()
}
