//! Markdown as the log draws it.
//!
//! A page becomes a list of [`Block`]s of styled [`Span`]s. There is no layout here: the log wraps
//! the spans itself, so the manual takes the width it is given and the app's own font.

use pulldown_cmark::{Event, HeadingLevel, Options, Parser, Tag, TagEnd};

/// A run of text, and how it is drawn.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Span {
    /// The text itself.
    pub text: String,
    /// How it is drawn.
    pub style: Style,
    /// Where it leads: another page of the manual, or a url.
    pub link: Option<String>,
}

impl Span {
    /// Text drawn as it is.
    pub fn plain(text: &str) -> Self {
        Self {
            text: text.to_owned(),
            style: Style::Plain,
            link: None,
        }
    }
}

/// How a run of text is drawn.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Style {
    /// As it is.
    Plain,
    /// Bold.
    Strong,
    /// Emphasised: the font has no italic, so it is set a weight heavier.
    Emphasis,
    /// A command, a file name, anything written as code.
    Code,
}

/// A piece of a page.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Block {
    /// A heading, and how deep it is from one.
    Heading {
        /// Its depth, from one.
        level: u8,
        /// Its text.
        spans: Vec<Span>,
    },
    /// A run of text.
    Paragraph(Vec<Span>),
    /// A list item, indented by its depth from zero.
    Item {
        /// How far it is indented, from zero.
        depth: usize,
        /// Its text.
        spans: Vec<Span>,
    },
    /// A transcript or other preformatted text, drawn line for line as athenaCL printed it.
    Code(String),
    /// A screenshot: its path under the manual, and what it shows, for when it cannot be shown.
    Image {
        /// Its path under the manual.
        path: String,
        /// What it shows, in words.
        alt: String,
    },
    /// A line quoted from somewhere, as a search result shows where it matched.
    Quote(String),
    /// A chapter in the contents: its number, how far it is indented, and where it leads.
    Entry {
        /// Its number in the contents, counting from one.
        number: usize,
        /// How far it is indented under its parent, from zero.
        depth: usize,
        /// Its title, which is what the link reads.
        title: String,
        /// Its page's path under the manual.
        path: String,
    },
}

/// Read `text` as the page at `path`, whose links are relative to it.
pub fn parse(text: &str, path: &str) -> Vec<Block> {
    let mut reader = Reader::new(path);
    for event in Parser::new_ext(text, Options::empty()) {
        reader.read(event);
    }
    reader.finish()
}

/// A page as it is read, event by event.
struct Reader<'a> {
    /// The page's path, which its links are relative to.
    path: &'a str,
    /// The blocks read so far.
    blocks: Vec<Block>,
    /// The text of the block being read.
    spans: Vec<Span>,
    /// How the text being read is drawn, and where it leads.
    style: Style,
    link: Option<String>,
    /// The level of the heading being read.
    heading: Option<u8>,
    /// How deep the lists being read are nested, and whether an item of theirs is.
    depth: usize,
    in_item: bool,
    /// Text read as it is, rather than as spans, until its end.
    raw: Option<Raw>,
}

/// What is read as it is written, until its end.
enum Raw {
    /// A transcript.
    Code(String),
    /// A screenshot: its path, and the words describing it.
    Image { path: String, alt: String },
}

impl<'a> Reader<'a> {
    fn new(path: &'a str) -> Self {
        Self {
            path,
            blocks: Vec::new(),
            spans: Vec::new(),
            style: Style::Plain,
            link: None,
            heading: None,
            depth: 0,
            in_item: false,
            raw: None,
        }
    }

    fn read(&mut self, event: Event<'_>) {
        if self.raw.is_some() {
            self.read_raw(event);
            return;
        }
        match event {
            Event::Start(tag) => self.start(tag),
            Event::End(tag) => self.end(tag),
            Event::Text(text) => self.push(&text, self.style),
            Event::Code(text) => self.push(&text, Style::Code),
            Event::SoftBreak => self.spans.push(Span::plain(" ")),
            Event::HardBreak => self.spans.push(Span::plain("\n")),
            _ => (),
        }
    }

    fn read_raw(&mut self, event: Event<'_>) {
        match (event, &mut self.raw) {
            (Event::End(TagEnd::CodeBlock), Some(Raw::Code(text))) => {
                let text = text.trim_end_matches('\n').to_owned();
                self.blocks.push(Block::Code(text));
                self.raw = None;
            }
            (Event::End(TagEnd::Image), Some(Raw::Image { path, alt })) => {
                let (path, alt) = (std::mem::take(path), std::mem::take(alt));
                self.blocks.push(Block::Image { path, alt });
                self.raw = None;
            }
            (
                Event::Text(text) | Event::Code(text),
                Some(Raw::Code(buffer) | Raw::Image { alt: buffer, .. }),
            ) => buffer.push_str(&text),
            _ => (),
        }
    }

    fn start(&mut self, tag: Tag<'_>) {
        match tag {
            // an image stands on its own, however it was written into a paragraph
            Tag::Image { dest_url, .. } => {
                self.end_paragraph();
                let path = resolve(&dest_url, self.path);
                self.raw = Some(Raw::Image {
                    path,
                    alt: String::new(),
                });
            }
            // nothing written before a transcript belongs to it
            Tag::CodeBlock(_) => {
                self.end_paragraph();
                self.raw = Some(Raw::Code(String::new()));
            }
            Tag::Heading { level, .. } => self.heading = Some(number(level)),
            Tag::List(_) => {
                // what was written before a nested list belongs to the item holding it
                if self.in_item {
                    self.end_item();
                }
                self.depth += 1;
            }
            Tag::Item => self.in_item = true,
            Tag::Strong => self.style = Style::Strong,
            Tag::Emphasis => self.style = Style::Emphasis,
            Tag::Link { dest_url, .. } => self.link = Some(resolve(&dest_url, self.path)),
            _ => (),
        }
    }

    fn end(&mut self, tag: TagEnd) {
        match tag {
            TagEnd::Heading(_) => {
                let level = self.heading.take().unwrap_or(1);
                let spans = std::mem::take(&mut self.spans);
                self.blocks.push(Block::Heading { level, spans });
            }
            TagEnd::Paragraph if self.in_item => self.end_item(),
            TagEnd::Paragraph => self.end_paragraph(),
            TagEnd::List(_) => self.depth = self.depth.saturating_sub(1),
            TagEnd::Item => {
                self.in_item = false;
                self.end_item();
            }
            TagEnd::Strong | TagEnd::Emphasis => self.style = Style::Plain,
            TagEnd::Link => self.link = None,
            _ => (),
        }
    }

    fn push(&mut self, text: &str, style: Style) {
        self.spans.push(Span {
            text: text.to_owned(),
            style,
            link: self.link.clone(),
        });
    }

    /// Make a paragraph of the text read since the last block, if there is any.
    fn end_paragraph(&mut self) {
        if !self.spans.is_empty() {
            self.blocks
                .push(Block::Paragraph(std::mem::take(&mut self.spans)));
        }
    }

    /// Make a list item of the text read since the last block, if there is any.
    fn end_item(&mut self) {
        if !self.spans.is_empty() {
            self.blocks.push(Block::Item {
                depth: self.depth.saturating_sub(1),
                spans: std::mem::take(&mut self.spans),
            });
        }
    }

    fn finish(mut self) -> Vec<Block> {
        self.end_paragraph();
        self.blocks
    }
}

/// A link's target as the manual holds it: a page beside `from`, or a url left as it is.
fn resolve(destination: &str, from: &str) -> String {
    if destination.contains("://") || destination.starts_with("mailto:") {
        return destination.to_owned();
    }
    let Some((directory, _)) = from.rsplit_once('/') else {
        return destination.to_owned();
    };
    let mut parts: Vec<&str> = directory.split('/').collect();
    for piece in destination.split('/') {
        match piece {
            "." => (),
            ".." => {
                parts.pop();
            }
            piece => parts.push(piece),
        }
    }
    parts.join("/")
}

fn number(level: HeadingLevel) -> u8 {
    match level {
        HeadingLevel::H1 => 1,
        HeadingLevel::H2 => 2,
        HeadingLevel::H3 => 3,
        HeadingLevel::H4 => 4,
        HeadingLevel::H5 => 5,
        HeadingLevel::H6 => 6,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn headings_and_paragraphs_keep_their_text() {
        let blocks = parse("# Title\n\nSome words.\n", "chapter01/a.md");
        assert_eq!(
            blocks.first(),
            Some(&Block::Heading {
                level: 1,
                spans: vec![Span::plain("Title")],
            })
        );
        assert_eq!(
            blocks.get(1),
            Some(&Block::Paragraph(vec![Span::plain("Some words.")]))
        );
    }

    #[test]
    fn a_soft_break_becomes_a_space_so_the_log_wraps_it_itself() {
        let blocks = parse("one\ntwo\n", "a.md");
        let Some(Block::Paragraph(spans)) = blocks.first() else {
            panic!("a paragraph");
        };
        let text: String = spans.iter().map(|span| span.text.as_str()).collect();
        assert_eq!(text, "one two");
    }

    #[test]
    fn styles_are_kept() {
        let blocks = parse("a **strong** and `code` word\n", "a.md");
        let Some(Block::Paragraph(spans)) = blocks.first() else {
            panic!("a paragraph");
        };
        assert!(spans
            .iter()
            .any(|span| span.text == "strong" && span.style == Style::Strong));
        assert!(spans
            .iter()
            .any(|span| span.text == "code" && span.style == Style::Code));
    }

    #[test]
    fn a_transcript_is_a_block_of_its_own() {
        let blocks = parse(
            "Before.\n\n```\n:: tin a 0\nTI a created.\n```\nAfter.\n",
            "a.md",
        );
        assert_eq!(
            blocks,
            [
                Block::Paragraph(vec![Span::plain("Before.")]),
                Block::Code(":: tin a 0\nTI a created.".to_owned()),
                Block::Paragraph(vec![Span::plain("After.")]),
            ],
            "it keeps its lines, and the next paragraph stays apart"
        );
    }

    #[test]
    fn an_image_is_a_block_of_its_own_beside_its_page() {
        let blocks = parse(
            "Before.\n\n![a map](../images/temap.png)\n\nAfter.\n",
            "chapter04/08-muting.md",
        );
        assert_eq!(
            blocks,
            [
                Block::Paragraph(vec![Span::plain("Before.")]),
                Block::Image {
                    path: "images/temap.png".to_owned(),
                    alt: "a map".to_owned(),
                },
                Block::Paragraph(vec![Span::plain("After.")]),
            ]
        );
    }

    #[test]
    fn list_items_keep_their_depth() {
        let blocks = parse("- one\n    - nested\n", "a.md");
        let depths: Vec<usize> = blocks
            .iter()
            .filter_map(|block| match block {
                Block::Item { depth, .. } => Some(*depth),
                _ => None,
            })
            .collect();
        assert_eq!(depths, [0, 1]);
    }

    #[test]
    fn links_to_pages_resolve_beside_the_page_they_are_on() {
        let blocks = parse("[there](02-next.md)\n", "chapter01/01-here.md");
        let Some(Block::Paragraph(spans)) = blocks.first() else {
            panic!("a paragraph");
        };
        assert_eq!(
            spans.first().and_then(|span| span.link.as_deref()),
            Some("chapter01/02-next.md")
        );
    }

    #[test]
    fn links_out_of_the_manual_are_left_alone() {
        assert_eq!(
            resolve("https://example.com/a", "chapter01/a.md"),
            "https://example.com/a"
        );
        assert_eq!(resolve("../other/b.md", "chapter01/a.md"), "other/b.md");
    }
}
