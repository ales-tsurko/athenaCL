//! The manual, as the app reads it.
//!
//! The pages are the mdbook sources the repository keeps under `doc/src`, read as the app runs from
//! a `manual` directory beside the executable: a bundle carries them there, and a development build
//! links them there. `SUMMARY.md` gives the contents; every other page is a chapter, parsed from
//! markdown into [`Block`]s that the log knows how to draw.

mod markdown;

use std::path::PathBuf;

pub use markdown::{Block, Span, Style};

/// The manual's summary file, which lists its chapters.
const SUMMARY: &str = "SUMMARY.md";

/// What `AUdoc` was asked for.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Request {
    /// The contents.
    Contents,
    /// A chapter by its number in the contents, counting from one.
    Chapter(usize),
    /// The chapters whose text holds every one of these words.
    Search(Vec<String>),
    /// The manual on the web, in a browser.
    Web,
}

impl Request {
    /// Read `arguments` as they were typed after `AUdoc`.
    pub fn parse(arguments: &str) -> Self {
        let arguments = arguments.trim();
        if arguments.is_empty() {
            return Self::Contents;
        }
        if arguments.eq_ignore_ascii_case("www") {
            return Self::Web;
        }
        if let Ok(number) = arguments.parse::<usize>() {
            return Self::Chapter(number);
        }
        Self::Search(
            arguments
                .split_whitespace()
                .map(str::to_lowercase)
                .collect(),
        )
    }
}

/// What `AUdoc` shows: a page of the manual, or the list of what there is to read.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Page {
    /// What to call it at the top of the output.
    pub title: String,
    /// Its text, ready to draw.
    pub blocks: Vec<Block>,
    /// Where it leads from its end.
    pub nav: Nav,
}

/// Where a page leads from its end, by the paths of those pages under the manual: back to the
/// contents, and on to the chapters before and after it.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Nav {
    /// The contents, from anywhere but the contents themselves.
    pub contents: Option<String>,
    /// The chapter before.
    pub previous: Option<String>,
    /// The chapter after; from the contents, the first.
    pub next: Option<String>,
}

/// A chapter, as the contents lists it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Entry {
    /// Its number in the contents, counting from one.
    pub number: usize,
    /// Its title.
    pub title: String,
    /// Its page's path under the manual.
    pub path: String,
    /// How far it is indented under its parent, from zero.
    pub depth: usize,
    /// The part of the manual it opens, when it is the first chapter of one.
    pub part: Option<String>,
}

/// Answer a request, or say why it cannot be answered.
pub fn read(request: &Request) -> Result<Page, String> {
    if page(SUMMARY).is_none() {
        return Err(format!(
            "the manual is missing: it should be in {}",
            root().display()
        ));
    }
    match request {
        Request::Contents | Request::Web => Ok(contents_page()),
        Request::Chapter(number) => chapter(*number),
        Request::Search(words) => Ok(search_page(words)),
    }
}

/// Every chapter the summary lists, in order.
pub fn contents() -> Vec<Entry> {
    let summary = page(SUMMARY).unwrap_or_default();
    let summary = summary.as_str();
    let mut entries = Vec::new();
    let mut part = None;
    for line in summary.lines() {
        if let Some(heading) = line.strip_prefix("# ") {
            part = Some(heading.trim().to_owned());
            continue;
        }
        let indent = line.len() - line.trim_start().len();
        let Some(item) = line.trim_start().strip_prefix("- ") else {
            continue;
        };
        let Some((title, path)) = link(item) else {
            continue;
        };
        entries.push(Entry {
            number: entries.len() + 1,
            title,
            path,
            // the summary indents nested chapters by four spaces
            depth: indent / 4,
            part: part.take(),
        });
    }
    entries
}

/// A markdown link, as `[title](path)`.
fn link(item: &str) -> Option<(String, String)> {
    let item = item.trim();
    let (title, rest) = item.strip_prefix('[')?.split_once("](")?;
    let path = rest.strip_suffix(')')?;
    Some((title.to_owned(), path.to_owned()))
}

/// Where the manual is: beside the executable, as a bundle and a development build both put it.
///
/// The tests run from elsewhere, so they read it where the repository keeps it.
pub fn root() -> PathBuf {
    if cfg!(test) {
        return PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("doc")
            .join("src");
    }
    std::env::current_exe()
        .ok()
        .and_then(|exe| Some(exe.parent()?.join("manual")))
        .unwrap_or_default()
}

/// A page's text, by its path under the manual.
pub fn page(path: &str) -> Option<String> {
    std::fs::read_to_string(root().join(path)).ok()
}

/// The entry a path belongs to, so that a link can say where it leads.
pub fn entry_of(path: &str) -> Option<Entry> {
    contents().into_iter().find(|entry| entry.path == path)
}

/// What a link to `path` under the manual asks for: the contents, or a chapter.
pub fn request_of(path: &str) -> Option<Request> {
    if path == SUMMARY {
        return Some(Request::Contents);
    }
    entry_of(path).map(|entry| Request::Chapter(entry.number))
}

/// The contents, as a page of links to every chapter.
fn contents_page() -> Page {
    let entries = contents();
    let nav = Nav {
        next: entries.first().map(|entry| entry.path.clone()),
        ..Nav::default()
    };
    let mut blocks = Vec::new();
    for entry in entries {
        if let Some(part) = &entry.part {
            blocks.push(Block::Heading {
                level: 2,
                spans: vec![Span::plain(part)],
            });
        }
        blocks.push(Block::Entry {
            number: entry.number,
            depth: entry.depth,
            title: entry.title,
            path: entry.path,
        });
    }
    Page {
        title: "athenaCL manual".to_owned(),
        blocks,
        nav,
    }
}

/// A chapter by its number in the contents.
fn chapter(number: usize) -> Result<Page, String> {
    let entries = contents();
    let entry = entries
        .iter()
        .find(|entry| entry.number == number)
        .ok_or_else(|| {
            format!(
                "the manual has chapters 1 to {}; enter AUdoc for the contents",
                entries.len()
            )
        })?;
    let text = page(&entry.path).ok_or_else(|| format!("{} is missing", entry.path))?;
    // chapters count from one, so the one after this is at its number in the list
    let path_at = |index: Option<usize>| Some(entries.get(index?)?.path.clone());
    Ok(Page {
        title: entry.title.clone(),
        blocks: markdown::parse(&text, &entry.path),
        nav: Nav {
            contents: Some(SUMMARY.to_owned()),
            previous: path_at(number.checked_sub(2)),
            next: path_at(Some(number)),
        },
    })
}

/// The chapters holding every one of `words`, with the line each was found on.
fn search_page(words: &[String]) -> Page {
    let mut blocks = vec![Block::Paragraph(vec![Span::plain(&format!(
        "chapters holding {}:",
        words.join(" ")
    ))])];
    let mut found = 0;
    for entry in contents() {
        let Some(text) = page(&entry.path) else {
            continue;
        };
        let lowercase = text.to_lowercase();
        if !words.iter().all(|word| lowercase.contains(word)) {
            continue;
        }
        found += 1;
        blocks.push(Block::Entry {
            number: entry.number,
            depth: 0,
            title: entry.title.clone(),
            path: entry.path.clone(),
        });
        if let Some(line) = first_mention(&text, words) {
            blocks.push(Block::Quote(line));
        }
    }
    if found == 0 {
        blocks.push(Block::Paragraph(vec![Span::plain("nothing found")]));
    }
    Page {
        title: "manual search".to_owned(),
        blocks,
        nav: Nav {
            contents: Some(SUMMARY.to_owned()),
            ..Nav::default()
        },
    }
}

/// A line of `text` showing why it matched, trimmed to a readable length.
///
/// Headings are skipped: a chapter's heading is its title, which is already on the line above. A
/// line holding every word says more than one holding a single word, so it is preferred.
fn first_mention(text: &str, words: &[String]) -> Option<String> {
    let mut lines = text.lines().filter(|line| {
        let line = line.trim();
        !line.is_empty() && !line.starts_with('#')
    });
    let holds = |line: &str, all: bool| {
        let lowercase = line.to_lowercase();
        if all {
            words.iter().all(|word| lowercase.contains(word))
        } else {
            words.iter().any(|word| lowercase.contains(word))
        }
    };
    let lines: Vec<&str> = lines.by_ref().collect();
    let line = lines
        .iter()
        .find(|line| holds(line, true))
        .or_else(|| lines.iter().find(|line| holds(line, false)))?;
    let line = line.trim();
    if line.chars().count() <= MENTION {
        return Some(line.to_owned());
    }
    let short: String = line.chars().take(MENTION).collect();
    Some(format!("{short}…"))
}

/// How much of a found line to show.
const MENTION: usize = 90;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_manual_reads_its_pages() {
        assert!(page(SUMMARY).is_some(), "the summary is there");
        assert!(page("no-such-page.md").is_none());
    }

    #[test]
    fn the_contents_number_every_chapter_in_order() {
        let entries = contents();
        assert!(entries.len() > 20);
        for (index, entry) in entries.iter().enumerate() {
            assert_eq!(entry.number, index + 1);
            assert!(!entry.title.is_empty(), "{entry:?} has a title");
            assert!(page(&entry.path).is_some(), "{} is a page", entry.path);
        }
        assert!(
            entries.iter().any(|entry| entry.depth > 0),
            "nested chapters keep their depth"
        );
        assert!(
            entries.iter().filter(|entry| entry.part.is_some()).count() > 1,
            "the parts are kept, each on its first chapter"
        );
    }

    #[test]
    fn arguments_say_what_to_read() {
        assert_eq!(Request::parse(""), Request::Contents);
        assert_eq!(Request::parse("  "), Request::Contents);
        assert_eq!(Request::parse("3"), Request::Chapter(3));
        assert_eq!(Request::parse("www"), Request::Web);
        assert_eq!(Request::parse("WWW"), Request::Web);
        assert_eq!(
            Request::parse("Texture  Path"),
            Request::Search(vec!["texture".to_owned(), "path".to_owned()])
        );
    }

    #[test]
    fn a_chapter_reads_by_its_number() {
        let page = read(&Request::Chapter(1)).expect("the first chapter reads");
        assert!(!page.title.is_empty());
        assert!(!page.blocks.is_empty());
    }

    #[test]
    fn a_number_past_the_end_says_what_there_is() {
        let error = read(&Request::Chapter(9999)).expect_err("there is no such chapter");
        assert!(error.contains("AUdoc"), "it says how to find out: {error}");
    }

    #[test]
    fn searching_finds_the_chapters_holding_every_word() {
        let page = read(&Request::Search(vec!["texture".to_owned()])).expect("search reads");
        let found = page
            .blocks
            .iter()
            .filter(|block| matches!(block, Block::Entry { .. }))
            .count();
        assert!(found > 1, "several chapters mention textures");

        let page = read(&Request::Search(vec!["zzzznotaword".to_owned()])).expect("search reads");
        assert!(page
            .blocks
            .iter()
            .any(|block| matches!(block, Block::Paragraph(spans) if spans
                .iter()
                .any(|span| span.text == "nothing found"))));
    }

    #[test]
    fn the_contents_link_to_every_chapter() {
        let page = read(&Request::Contents).expect("the contents read");
        let links = page
            .blocks
            .iter()
            .filter(|block| matches!(block, Block::Entry { .. }))
            .count();
        assert_eq!(links, contents().len());
    }

    #[test]
    fn a_page_leads_to_the_contents_and_the_chapters_beside_it() {
        let entries = contents();
        let path = |number: usize| Some(entries[number - 1].path.clone());
        let nav = |request| read(&request).expect("the page reads").nav;

        let contents_nav = nav(Request::Contents);
        assert_eq!(contents_nav.contents, None);
        assert_eq!(contents_nav.previous, None);
        assert_eq!(
            contents_nav.next,
            path(1),
            "the contents lead to the first chapter"
        );

        let first = nav(Request::Chapter(1));
        assert_eq!(first.contents.as_deref(), Some(SUMMARY));
        assert_eq!((first.previous, first.next), (None, path(2)));

        let middle = nav(Request::Chapter(2));
        assert_eq!((middle.previous, middle.next), (path(1), path(3)));

        let last = nav(Request::Chapter(entries.len()));
        assert_eq!(last.next, None);

        let search = nav(Request::Search(vec!["texture".to_owned()]));
        assert_eq!(search.contents.as_deref(), Some(SUMMARY));
        assert_eq!((search.previous, search.next), (None, None));
    }

    #[test]
    fn a_link_asks_for_the_contents_or_a_chapter() {
        let entries = contents();
        assert_eq!(request_of(SUMMARY), Some(Request::Contents));
        assert_eq!(request_of(&entries[2].path), Some(Request::Chapter(3)));
        assert_eq!(request_of("chapter99/nothing.md"), None);
    }

    #[test]
    fn every_link_and_image_between_pages_leads_to_one() {
        let missing = |path: &str| {
            let file = path.split('#').next().unwrap_or(path);
            !root().join(file).exists()
        };
        for entry in contents() {
            let text = page(&entry.path).expect("every chapter is there");
            for block in markdown::parse(&text, &entry.path) {
                let spans = match &block {
                    Block::Heading { spans, .. }
                    | Block::Paragraph(spans)
                    | Block::Item { spans, .. } => spans.as_slice(),
                    Block::Image { path, .. } => {
                        assert!(!missing(path), "{}: no image {path}", entry.path);
                        continue;
                    }
                    Block::Code(_) | Block::Quote(_) | Block::Entry { .. } => continue,
                };
                // a reference to a link that is not defined stays in the text as written
                let text: String = spans.iter().map(|span| span.text.as_str()).collect();
                assert!(
                    !text.contains("]["),
                    "{}: a link without its definition",
                    entry.path
                );
                for link in spans.iter().filter_map(|span| span.link.as_deref()) {
                    if !link.contains("://") && !link.starts_with("mailto:") {
                        assert!(!missing(link), "{}: no page {link}", entry.path);
                    }
                }
            }
        }
    }
}
