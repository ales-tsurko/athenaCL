//! Matching, replacement and cycling without a renderer or interpreter round trip.

use crate::{
    app::{
        completion::{Sources, Suggestions},
        history::History,
    },
    interpreter::CommandCompletion,
};

fn catalog() -> Vec<CommandCompletion> {
    ["PIo", "TIo", "TIn", "TIls", "help"]
        .into_iter()
        .map(|name| CommandCompletion {
            name: name.to_owned(),
            description: format!("{name} description"),
        })
        .collect()
}

fn sources(history: &History) -> Sources<'_> {
    Sources {
        history,
        paths: &[],
        textures: &[],
    }
}

#[test]
fn tab_and_shift_tab_cycle_the_original_matches_and_edits_start_a_new_search() {
    let history = History::default();
    let sources = sources(&history);
    let mut suggestions = Suggestions::default();
    suggestions.set_commands(catalog(), sources);
    suggestions.edit("ti", Some(2), sources);
    assert_eq!(suggestions.cycle(false, sources), Some(("TIls ".into(), 5)));
    // The input reports the programmatic cursor move; this must not narrow the cycle.
    suggestions.edit("TIls ", Some(5), sources);
    assert_eq!(suggestions.cycle(false, sources), Some(("TIn ".into(), 4)));
    assert_eq!(suggestions.cycle(true, sources), Some(("TIls ".into(), 5)));
    assert_eq!(suggestions.cycle(true, sources), Some(("TIo ".into(), 4)));
    assert_eq!(suggestions.cycle(false, sources), Some(("TIls ".into(), 5)));
    suggestions.edit("he", Some(2), sources);
    assert_eq!(suggestions.cycle(false, sources), Some(("help ".into(), 5)));
    assert!(!suggestions.is_open(), "one match completes the cycle");
}

#[test]
fn completion_respects_caret_suffix_leading_space_and_help_context() {
    let history = History::default();
    let sources = sources(&history);
    let mut suggestions = Suggestions::default();
    suggestions.set_commands(catalog(), sources);
    for (input, caret, expected, position) in [
        ("  ti a 0", 4, "  TIls a 0", 7),
        ("tiBAD a 0", 2, "TIls a 0", 5),
        ("help ti", 7, "help TIls ", 10),
        ("? ti", 4, "? TIls ", 7),
    ] {
        suggestions.edit(input, Some(caret), sources);
        assert_eq!(
            suggestions.cycle(false, sources),
            Some((expected.into(), position))
        );
    }
    suggestions.edit("tin name ti", Some(11), sources);
    assert!(
        !suggestions.is_open(),
        "command names do not leak into arbitrary arguments"
    );
}

#[test]
fn session_names_are_contextual_and_unicode_safe_and_refresh_when_they_change() {
    let history = History::default();
    let paths = ["音階".to_owned(), "e\u{301}cho".to_owned()];
    let textures = ["bass".to_owned(), "bells".to_owned()];
    let sources = Sources {
        history: &history,
        paths: &paths,
        textures: &textures,
    };
    let mut suggestions = Suggestions::default();
    suggestions.edit("pio 音", Some(7), sources);
    assert_eq!(
        suggestions.cycle(false, sources),
        Some(("pio 音階 ".into(), 7))
    );
    suggestions.edit("pio e", Some(5), sources);
    assert_eq!(
        suggestions.cycle(false, sources),
        Some(("pio e\u{301}cho ".into(), 9))
    );
    suggestions.edit("TIo b", Some(5), sources);
    assert_eq!(
        suggestions.cycle(true, sources),
        Some(("TIo bells ".into(), 10))
    );
    suggestions.edit("TIcp bass ", Some(10), sources);
    assert!(!suggestions.is_open(), "the destination is a new name");
    suggestions.edit("TIn b", Some(5), sources);
    assert!(!suggestions.is_open(), "a new texture needs a new name");
    suggestions.edit("TIrm bass b", Some(11), sources);
    assert!(suggestions.is_open());
    suggestions.refresh(Sources {
        textures: &[],
        ..sources
    });
    assert!(!suggestions.is_open(), "deleted names disappear");
    suggestions.edit("pio 音", Some(5), sources);
    assert!(
        !suggestions.is_open(),
        "an invalid UTF-8 boundary is rejected"
    );
}

#[test]
fn history_is_recent_unique_and_does_not_change_recall_drafts() {
    let mut history = History::default();
    for command in ["tin Bass 0", "tin bass 1", "tin Bass 0", "TIls"] {
        history.record(command).expect("record");
    }
    let _ = history
        .recall(rustyline::history::SearchDirection::Reverse, "draft")
        .expect("recall");
    let mut suggestions = Suggestions::default();
    suggestions.set_commands(catalog(), sources(&history));
    suggestions.edit("ti", Some(2), sources(&history));
    assert_eq!(
        suggestions.candidates.len(),
        5,
        "history and catalog deduplicate"
    );
    suggestions.edit("TIN B", Some(5), sources(&history));
    assert_eq!(
        suggestions.cycle(false, sources(&history)),
        Some(("tin Bass 0".into(), 10))
    );
    assert_eq!(
        history
            .recall(rustyline::history::SearchDirection::Forward, "edited")
            .expect("recall"),
        Some("draft".into())
    );
}

#[test]
fn empty_selection_dismissal_and_explicit_tab() {
    let history = History::default();
    let sources = sources(&history);
    let mut suggestions = Suggestions::default();
    suggestions.set_commands(catalog(), sources);
    suggestions.edit("", Some(0), sources);
    assert!(!suggestions.is_open());
    assert_eq!(suggestions.cycle(false, sources), Some(("help ".into(), 5)));
    suggestions.edit("ti", Some(2), sources);
    suggestions.dismiss();
    suggestions.edit("ti", Some(2), sources);
    suggestions.refresh(sources);
    suggestions.set_commands(catalog(), sources);
    assert!(
        !suggestions.is_open(),
        "unchanged caret and catalog updates do not undo Escape"
    );
    assert_eq!(suggestions.cycle(true, sources), Some(("TIo ".into(), 4)));
    suggestions.edit("ti", None, sources);
    assert_eq!(suggestions.cycle(false, sources), None);
    suggestions.clear();
    assert!(!suggestions.is_open());
}
