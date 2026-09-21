//! The manual in the log.
//!
//! A page is drawn as the commands' output is: the app's own monospaced text, wrapped to the width
//! of the log, under its title in the pixel font, as the labels elsewhere are. It is a reader:
//! its links, and the turns at its end, turn it to another page where it is, or open the web.

use std::{
    collections::HashMap,
    path::{Path, PathBuf},
    sync::{LazyLock, Mutex},
};

use iced::{
    font,
    widget::{column, container, image, row, space, span, text, Column},
    Element, Font, Length,
};

use crate::{
    app::{
        app::{segment, switch},
        pixel,
        theme::{Colors, Mode},
    },
    manual::{self, Block, Nav, Page, Span, Style},
};

/// What a page sends: where the link or the turn clicked on it leads.
pub(crate) type Link = String;

/// Space between a page's blocks.
const GAP: f32 = 8.0;
/// How far a list item or a nested chapter is indented, per level.
const INDENT: &str = "    ";
/// A transcript's text, a step under the prose's.
const CODE_SIZE: f32 = 13.0;
/// The room around what is on a panel: a transcript, a screenshot.
const PANEL_PADDING: [u16; 2] = [8, 12];
/// The bullet a list item gets.
const BULLET: &str = "- ";
/// How many of a screenshot's pixels there are to each of the log's: they are taken for screens
/// of twice the density.
const SHOT_SCALE: f32 = 2.0;

/// Draw `page` for a log `width` wide, in `mode`.
pub(crate) fn view(page: &Page, width: f32, mode: Mode) -> Element<'_, Link> {
    let colors = mode.colors();
    let mut blocks = Column::new().spacing(GAP);
    blocks = blocks.push(pixel::label(&page.title.to_uppercase(), colors.dim));
    for block in &page.blocks {
        // the page is already labelled with its title, which is its top heading
        if matches!(block, Block::Heading { level: 1, .. }) {
            continue;
        }
        blocks = blocks.push(view_block(block, width, mode, colors));
    }
    blocks.push(view_nav(&page.nav, colors, width)).into()
}

/// Where the page leads from its end, set as the figures' switch is under them.
fn view_nav<'a>(nav: &Nav, colors: Colors, width: f32) -> Element<'a, Link> {
    let turns = [
        ("CONTENTS", &nav.contents),
        ("PREVIOUS", &nav.previous),
        ("NEXT", &nav.next),
    ]
    .into_iter()
    .filter_map(|(label, path)| Some(segment(label, colors, false, path.clone()?)));
    row![space::horizontal(), switch(colors, turns)]
        .width(width)
        .into()
}

fn view_block(block: &Block, width: f32, mode: Mode, colors: Colors) -> Element<'_, Link> {
    match block {
        Block::Heading { spans, .. } => {
            let text: String = spans.iter().map(|span| span.text.as_str()).collect();
            view_spans(
                &[Span {
                    text,
                    style: Style::Strong,
                    link: None,
                }],
                colors,
            )
        }
        Block::Paragraph(spans) => view_spans(spans, colors),
        Block::Item { depth, spans } => {
            let mut item = vec![Span::plain(&format!("{}{BULLET}", INDENT.repeat(*depth)))];
            item.extend(spans.iter().cloned());
            view_spans(&item, colors)
        }
        Block::Code(code) => view_code(code, colors),
        Block::Image { path, alt } => view_image(path, alt, width, mode, colors),
        Block::Quote(line) => iced_selection::text(format!("{INDENT}{line}"))
            .size(13)
            .style(Colors::selectable(colors.dim, colors.rule))
            .into(),
        Block::Entry {
            number,
            depth,
            title,
            path,
        } => view_entry(*number, *depth, title, path, colors),
    }
}

/// A transcript, as athenaCL printed it: line for line, on a panel of its own so that it does not
/// run into the prose around it.
fn view_code<'a>(code: &str, colors: Colors) -> Element<'a, Link> {
    let code = iced_selection::text(code.to_owned())
        .size(CODE_SIZE)
        .style(Colors::selectable(colors.ink, colors.paper));
    panel(code, colors)
}

/// What stands apart from the prose around it, on a panel of the rule: a transcript, a screenshot.
fn panel<'a>(content: impl Into<Element<'a, Link>>, colors: Colors) -> Element<'a, Link> {
    container(content)
        .padding(PANEL_PADDING)
        .width(Length::Fill)
        .style(Colors::fill(colors.rule))
        .into()
}

/// How wide a picture is drawn on a panel in a log `width` wide: the width screenshots are taken
/// at.
pub(crate) fn picture_width(width: f32) -> f32 {
    width - 2.0 * f32::from(PANEL_PADDING[1])
}

/// A screenshot, with what it shows under it, on a panel as a transcript is: it is not to pass for
/// the app's own controls. It is in the look the app is in: the page names the light one, and the
/// dark one sits beside it with `-dark` before its extension. One taken at the panel's width falls
/// pixel for pixel on the screen; a wider one is drawn smaller, to fit.
fn view_image<'a>(
    path: &str,
    alt: &str,
    width: f32,
    mode: Mode,
    colors: Colors,
) -> Element<'a, Link> {
    let light = manual::root().join(path);
    let dark = light.with_file_name(format!(
        "{}-dark.png",
        light.file_stem().unwrap_or_default().to_string_lossy()
    ));
    let file = match mode {
        Mode::Dark if pixels(&dark).is_some() => dark,
        Mode::Dark | Mode::Light => light,
    };
    let Some((wide, high)) = pixels(&file) else {
        return text(format!("[{alt}]")).color(colors.dim).into();
    };
    let scale = (picture_width(width) / wide as f32 * SHOT_SCALE).min(1.0) / SHOT_SCALE;
    let picture = image(image::Handle::from_path(file))
        .width(wide as f32 * scale)
        .height(high as f32 * scale);
    let caption = iced_selection::text(alt.to_owned())
        .size(CODE_SIZE)
        .style(Colors::selectable(colors.dim, colors.paper));
    panel(column![picture, caption].spacing(GAP), colors)
}

/// Images' sizes in pixels by their files, or nothing for one that cannot be read.
type Sizes = HashMap<PathBuf, Option<(u32, u32)>>;

/// How many pixels wide and high the image in `file` is, read once from its header.
///
/// iced reads an image on a thread of its own and has no size for it until it is done: sized
/// beforehand, a screenshot takes its place from the first frame, instead of pushing the page down
/// when it arrives.
fn pixels(file: &Path) -> Option<(u32, u32)> {
    static PIXELS: LazyLock<Mutex<Sizes>> = LazyLock::new(Mutex::default);
    let mut pixels = PIXELS.lock().ok()?;
    *pixels
        .entry(file.to_owned())
        .or_insert_with(|| ::image::image_dimensions(file).ok())
}

/// A chapter in the contents: its number, and its title as a link to it.
fn view_entry<'a>(
    number: usize,
    depth: usize,
    title: &str,
    path: &str,
    colors: Colors,
) -> Element<'a, Link> {
    row![
        text(format!("{}{number:>3}. ", INDENT.repeat(depth))).color(colors.dim),
        iced_selection::rich_text([span(title.to_owned())
            .color(colors.ink)
            .underline(true)
            .link(path.to_owned())])
        .on_link_click(std::convert::identity)
        .style(Colors::selectable(colors.ink, colors.rule)),
    ]
    .into()
}

/// A run of styled text, wrapped by the log to its own width, which can be selected to copy.
fn view_spans<'a>(spans: &[Span], colors: Colors) -> Element<'a, Link> {
    let spans: Vec<_> = spans
        .iter()
        .map(|it| {
            let mut drawn = span(it.text.clone()).color(colors.ink);
            // a command reads as it does when it is entered, which the log sets in bold
            match it.style {
                Style::Strong | Style::Code => drawn = drawn.font(bold()),
                Style::Emphasis => drawn = drawn.font(medium()),
                Style::Plain => (),
            }
            if let Some(link) = &it.link {
                drawn = drawn.link(link.clone()).underline(true);
            }
            drawn
        })
        .collect();
    iced_selection::rich_text(spans)
        .on_link_click(std::convert::identity)
        .style(Colors::selectable(colors.ink, colors.rule))
        .into()
}

/// Emphasis, a weight between the text's and bold: the font has no italic.
fn medium() -> Font {
    let mut medium = Font::with_name("Fira Mono");
    medium.weight = font::Weight::Medium;
    medium
}

fn bold() -> Font {
    let mut bold = Font::with_name("Fira Mono");
    bold.weight = font::Weight::Bold;
    bold
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_kind_of_block_draws() {
        let page = Page {
            title: "a page".to_owned(),
            blocks: vec![
                Block::Heading {
                    level: 1,
                    spans: vec![Span::plain("Title")],
                },
                Block::Heading {
                    level: 2,
                    spans: vec![Span::plain("Section")],
                },
                Block::Paragraph(vec![Span::plain("words")]),
                Block::Item {
                    depth: 1,
                    spans: vec![Span::plain("an item")],
                },
                Block::Quote("a line".to_owned()),
                Block::Code("pi{}ti{} :: cmd".to_owned()),
                Block::Image {
                    path: "images/window.png".to_owned(),
                    alt: "a screenshot".to_owned(),
                },
                Block::Image {
                    path: "images/missing.png".to_owned(),
                    alt: "a missing one".to_owned(),
                },
                Block::Entry {
                    number: 3,
                    depth: 0,
                    title: "Chapter".to_owned(),
                    path: "chapter01/a.md".to_owned(),
                },
            ],
            nav: Nav {
                contents: Some("SUMMARY.md".to_owned()),
                previous: Some("chapter01/a.md".to_owned()),
                next: Some("chapter01/b.md".to_owned()),
            },
        };
        for mode in [Mode::Light, Mode::Dark] {
            let _ = view(&page, 600.0, mode);
        }
    }

    #[test]
    fn a_transcript_is_selected_by_dragging_across_it_and_shows_the_page_through() {
        use iced::{mouse, Event, Point};

        let code = "pi{}ti{} :: tin a 0\nTI a created.";
        let page = Page {
            title: "a page".to_owned(),
            blocks: vec![Block::Code(code.to_owned())],
            nav: Nav::default(),
        };
        let colors = Mode::Light.colors();
        let mut simulator = iced_test::Simulator::with_size(
            crate::app::settings(),
            iced::Size::new(400.0, 120.0),
            view(&page, 400.0, Mode::Light),
        );
        let bounds = simulator
            .find(code)
            .expect("the transcript is drawn")
            .visible_bounds()
            .expect("the transcript is in view");
        // the page's pixels inside the transcript, on its panel of the rule, at twice the size
        let inside = |x: u32, y: u32| {
            let (x, y) = (f64::from(x) / 2.0, f64::from(y) / 2.0);
            (f64::from(bounds.x)..f64::from(bounds.x + bounds.width)).contains(&x)
                && (f64::from(bounds.y)..f64::from(bounds.y + bounds.height)).contains(&y)
        };
        let marked = |simulator: &mut iced_test::Simulator<'_, Link>| {
            let pixels = crate::app::snapshot::pixels(
                &simulator
                    .snapshot(&Mode::Light.theme())
                    .expect("the page renders"),
            );
            let paper = colors.paper.into_rgba8();
            pixels
                .enumerate_pixels()
                .filter(|&(x, y, pixel)| inside(x, y) && pixel.0 == paper)
                .count()
        };
        assert_eq!(marked(&mut simulator), 0, "nothing is selected yet");

        let (from, to) = (
            bounds.position() + iced::Vector::new(1.0, 1.0),
            Point::new(
                bounds.x + bounds.width - 1.0,
                bounds.y + bounds.height - 1.0,
            ),
        );
        simulator.point_at(from);
        let _ = simulator.simulate([Event::Mouse(mouse::Event::ButtonPressed(
            mouse::Button::Left,
        ))]);
        simulator.point_at(to);
        let _ = simulator.simulate([
            Event::Mouse(mouse::Event::CursorMoved { position: to }),
            Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)),
        ]);
        assert!(marked(&mut simulator) > 0, "the selection shows the page");
    }
}
