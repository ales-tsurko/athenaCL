//! File operations use isolated temporary trees, never the user's scratch folder.

use std::{collections::BTreeSet, fs, path::Path};

use iced::keyboard::Modifiers;

use crate::app::browser::{
    filesystem::{Kind, Listing, Opened, Operation},
    state::{Browser, Edit, Effect, Message},
};

#[test]
fn tree_filters_binary_files_and_only_reads_expanded_folders() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    fs::create_dir(root.join("scores")).expect("subfolder");
    fs::write(root.join("scores/notes.txt"), "hello 音").expect("text");
    fs::write(root.join("notes"), "utf-8 text without an extension").expect("text");
    fs::write(
        root.join("object.xml"),
        b"<?xml version=\"1.0\"?><!--saved--><athenaObject/>",
    )
    .expect("object");
    fs::write(root.join("other.xml"), b"<settings/>").expect("xml");
    fs::write(root.join("events.mid"), b"MThd\0\0\0\x06").expect("midi");
    fs::write(root.join("render.WAV"), b"RIFF\0\0\0\0WAVE").expect("audio");
    fs::write(root.join("piano.SF2"), b"RIFF\0\0\0\0sfbk").expect("sound font");
    fs::write(root.join("binary.dat"), [0, 255, 7]).expect("binary");
    let listing = Listing::read(root, &BTreeSet::new()).expect("listing");
    assert_eq!(listing.entries.len(), 7);
    assert_eq!(listing.entries.first().expect("folder").kind, Kind::Folder);
    for (name, kind) in [
        ("object.xml", Kind::Athena),
        ("other.xml", Kind::Text),
        ("events.mid", Kind::Midi),
        ("render.WAV", Kind::Audio),
        ("piano.SF2", Kind::SoundFont),
        ("notes", Kind::Text),
    ] {
        assert!(listing
            .entries
            .iter()
            .any(|entry| entry.name() == name && entry.kind == kind));
    }
    let expanded = BTreeSet::from([root.join("scores")]);
    let listing = Listing::read(root, &expanded).expect("expanded tree");
    assert!(listing
        .entries
        .iter()
        .any(|entry| entry.name() == "notes.txt" && entry.depth == 1));
    assert!(listing.errors.is_empty());
    assert_eq!(
        Opened::read(root, &root.join("piano.SF2")).expect("open sound font"),
        Opened::SoundFont
    );
    Listing::read(&root.join("missing"), &expanded).expect_err("missing folder");
}

#[test]
fn text_open_preserves_unicode_and_limits_large_previews() {
    let dir = tempfile::tempdir().expect("scratch folder");
    for (name, bytes, expected) in [
        ("empty", Vec::new(), ""),
        (
            "utf8",
            "\u{feff}hello 音\n".as_bytes().to_vec(),
            "hello 音\n",
        ),
        (
            "utf16le",
            [
                vec![0xff, 0xfe],
                "hello 音"
                    .encode_utf16()
                    .flat_map(u16::to_le_bytes)
                    .collect(),
            ]
            .concat(),
            "hello 音",
        ),
        (
            "utf16be",
            [
                vec![0xfe, 0xff],
                "音".encode_utf16().flat_map(u16::to_be_bytes).collect(),
            ]
            .concat(),
            "音",
        ),
    ] {
        let path = dir.path().join(name);
        fs::write(&path, bytes).expect("file");
        assert_eq!(
            Opened::read(dir.path(), &path).expect("text opens"),
            Opened::Text(expected.into())
        );
    }
    let path = dir.path().join("large.txt");
    fs::write(&path, "音".repeat(400_000)).expect("large text");
    let Opened::Text(content) = Opened::read(dir.path(), &path).expect("bounded preview") else {
        panic!("text preview");
    };
    assert!(content.len() < 1024 * 1024 + 100);
    assert!(content.ends_with("[Text truncated after 1 MiB]"));
    fs::write(&path, [0xff, 0xfe, 0, 0xd8]).expect("invalid UTF-16");
    Opened::read(dir.path(), &path).expect_err("invalid UTF-16");
}

#[test]
fn copy_paste_never_overwrites_and_rename_delete_support_spaces_and_unicode() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    let source = root.join("song 音.txt");
    fs::write(&source, "original").expect("file");
    let copy = Operation::Copy {
        source: source.clone(),
        directory: root.into(),
    };
    copy.run(root).expect("first copy");
    copy.run(root).expect("second copy");
    assert_eq!(
        fs::read_to_string(root.join("song 音 copy.txt")).expect("copy"),
        "original"
    );
    assert_eq!(
        fs::read_to_string(root.join("song 音 copy 2.txt")).expect("copy"),
        "original"
    );
    Operation::CreateFolder {
        directory: root.into(),
        name: "scores".into(),
    }
    .run(root)
    .expect("new folder");
    Operation::Copy {
        source: source.clone(),
        directory: root.join("scores"),
    }
    .run(root)
    .expect("paste into folder");
    Operation::Copy {
        source: root.join("scores"),
        directory: root.into(),
    }
    .run(root)
    .expect("recursive copy");
    assert!(root.join("scores copy/song 音.txt").is_file());
    Operation::Rename {
        path: root.join("scores copy"),
        name: "renamed scores".into(),
    }
    .run(root)
    .expect("rename folder");
    Operation::Delete(root.join("renamed scores"))
        .run(root)
        .expect("delete recursively");
    assert!(!root.join("renamed scores").exists());
    Operation::Rename {
        path: source.clone(),
        name: "new name 音.txt".into(),
    }
    .run(root)
    .expect("rename file");
    assert!(!source.exists());
    Operation::Delete(root.join("new name 音.txt"))
        .run(root)
        .expect("delete file");
    assert!(root.join("song 音 copy.txt").exists());
}

#[test]
fn file_actions_reject_collisions_recursion_and_paths_outside_the_root() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    for name in ["first", "second"] {
        fs::write(root.join(name), name).expect("file");
    }
    fs::create_dir(root.join("folder")).expect("folder");
    let rename = |name: &str| Operation::Rename {
        path: root.join("first"),
        name: name.into(),
    };
    assert!(rename("second").run(root).is_err());
    assert_eq!(
        fs::read_to_string(root.join("second")).expect("original"),
        "second"
    );
    for name in ["", ".", "..", "../escape", "a/b", "a\\b", "/escape"] {
        assert!(rename(name).run(root).is_err(), "{name}");
        assert!(Operation::CreateFolder {
            directory: root.into(),
            name: name.into()
        }
        .run(root)
        .is_err());
    }
    assert!(Operation::Delete(root.into()).run(root).is_err());
    assert!(Operation::Rename {
        path: root.into(),
        name: "other".into()
    }
    .run(root)
    .is_err());
    assert!(Operation::Copy {
        source: root.join("folder"),
        directory: root.join("folder")
    }
    .run(root)
    .is_err());
    let outside = tempfile::tempdir().expect("other folder");
    let outside_file = outside.path().join("outside");
    fs::write(&outside_file, "untouched").expect("file");
    assert!(Operation::Delete(outside_file.clone()).run(root).is_err());
    Opened::read(root, &outside_file).expect_err("outside the scratch folder");
    assert_eq!(
        fs::read_to_string(outside_file).expect("outside file"),
        "untouched"
    );
    Opened::read(root, &root.join("missing")).expect_err("missing file");
    Opened::read(root, &root.join("folder")).expect_err("folder is not a file");
}

#[test]
fn moves_preserve_contents_and_refuse_conflicts_cycles_and_outside_paths() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    fs::create_dir_all(root.join("scores/nested")).expect("folders");
    fs::create_dir(root.join("destination")).expect("destination");
    fs::write(root.join("scores/nested/音.txt"), "keep these notes").expect("notes");
    let move_to = |source: &Path, directory: &Path| {
        Operation::Move {
            source: source.into(),
            directory: directory.into(),
        }
        .run(root)
    };
    move_to(&root.join("scores"), &root.join("destination")).expect("move folder");
    assert!(!root.join("scores").exists());
    let moved = root.join("destination/scores/nested/音.txt");
    assert_eq!(
        fs::read_to_string(&moved).expect("moved notes"),
        "keep these notes"
    );
    move_to(&moved, root).expect("move file back to root");
    assert!(!moved.exists());
    let restored = root.join("音.txt");
    move_to(&restored, root).expect("same folder is a no-op");
    fs::write(root.join("destination/音.txt"), "existing notes").expect("collision");
    move_to(&restored, &root.join("destination")).expect_err("never overwrite");
    assert_eq!(
        fs::read_to_string(&restored).expect("source"),
        "keep these notes"
    );
    assert_eq!(
        fs::read_to_string(root.join("destination/音.txt")).expect("destination"),
        "existing notes"
    );
    for directory in [
        root.join("destination"),
        root.join("destination/scores/nested"),
    ] {
        move_to(&root.join("destination"), &directory).expect_err("no directory cycles");
    }
    move_to(root, &root.join("destination")).expect_err("cannot move scratch root");
    let outside = tempfile::tempdir().expect("outside folder");
    move_to(&restored, outside.path()).expect_err("cannot move outside scratch root");
    fs::write(outside.path().join("outside.txt"), "outside").expect("outside file");
    move_to(&outside.path().join("outside.txt"), root).expect_err("outside source");
    assert!(outside.path().join("outside.txt").exists());
}

#[test]
fn native_drags_move_the_selection_into_folders_and_back_to_the_root() {
    use iced::{mouse, Event, Size};
    use iced_test::Simulator;

    use crate::app::theme::Mode;
    for mode in [Mode::Light, Mode::Dark] {
        let dir = tempfile::tempdir().expect("scratch folder");
        let root = dir.path();
        fs::create_dir(root.join("destination")).expect("destination");
        fs::create_dir(root.join("source")).expect("source");
        fs::write(root.join("source/child.txt"), "child").expect("child");
        fs::write(root.join("notes.txt"), "notes").expect("notes");
        let mut browser = ui_browser(root);
        for name in ["source", "notes.txt"] {
            drop(browser.update(Message::Click(root.join(name), Modifiers::COMMAND, false)));
        }
        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(280.0, 500.0),
            browser.view(mode.colors()),
        );
        let start = simulator
            .find("notes.txt")
            .expect("source row")
            .bounds()
            .center();
        let end = simulator
            .find("destination")
            .expect("destination row")
            .bounds()
            .center();
        simulator.point_at(end);
        let _ = simulator.simulate([
            Event::Mouse(mouse::Event::CursorMoved { position: start }),
            Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
            Event::Mouse(mouse::Event::CursorMoved { position: end }),
            Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)),
        ]);
        let messages: Vec<_> = simulator.into_messages().collect();
        assert!(messages.iter().any(|message| matches!(message,
            Message::Move(paths, directory) if paths.len() == 2 && directory == &root.join("destination")
        )), "{messages:?}");
        for message in messages {
            let (task, effect) = browser.update(message);
            if let Some(Effect::Changing(paths)) = effect {
                assert_eq!(paths.len(), 2, "release media before either path is moved");
                assert!(
                    paths.iter().all(|path| path.exists()),
                    "move is still deferred"
                );
            }
            drop(finish(&mut browser, task));
        }
        assert!(root.join("destination/notes.txt").is_file());
        assert!(root.join("destination/source/child.txt").is_file());
        assert!(!root.join("notes.txt").exists() && !root.join("source").exists());
        assert_eq!(browser.selected.len(), 2, "moved items stay selected");
        assert!(browser.expanded.contains(&root.join("destination")));

        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(280.0, 500.0),
            browser.view(mode.colors()),
        );
        let start = simulator
            .find("notes.txt")
            .expect("nested source")
            .bounds()
            .center();
        let root_name = root
            .file_name()
            .expect("named")
            .to_string_lossy()
            .into_owned();
        let end = simulator
            .find(root_name.as_str())
            .expect("root row")
            .bounds()
            .center();
        simulator.point_at(end);
        let _ = simulator.simulate([
            Event::Mouse(mouse::Event::CursorMoved { position: start }),
            Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
            Event::Mouse(mouse::Event::CursorMoved { position: end }),
            Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)),
        ]);
        for message in simulator.into_messages() {
            let (task, _) = browser.update(message);
            drop(finish(&mut browser, task));
        }
        assert!(root.join("notes.txt").is_file());
        assert!(root.join("source/child.txt").is_file());
        assert!(!root.join("destination/notes.txt").exists());
    }
}

#[test]
fn dragging_expands_hovered_folders_and_escape_cancels_without_moving() {
    use iced::{keyboard, mouse, time::Instant, window, Event, Size};
    use iced_test::Simulator;

    use crate::app::theme::Mode;
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    fs::create_dir(root.join("destination")).expect("destination");
    fs::write(root.join("destination/inside.txt"), "inside").expect("nested file");
    fs::write(root.join("notes.txt"), "notes").expect("notes");
    let mut browser = ui_browser(root);
    let mut simulator = Simulator::with_size(
        crate::app::settings(),
        Size::new(280.0, 500.0),
        browser.view(Mode::Dark.colors()),
    );
    let start = simulator
        .find("notes.txt")
        .expect("source row")
        .bounds()
        .center();
    let end = simulator
        .find("destination")
        .expect("folder row")
        .bounds()
        .center();
    simulator.point_at(end);
    let _ = simulator.simulate([
        Event::Mouse(mouse::Event::CursorMoved { position: start }),
        Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
        Event::Mouse(mouse::Event::CursorMoved { position: end }),
        Event::Window(window::Event::RedrawRequested(
            Instant::now() + std::time::Duration::from_secs(1),
        )),
    ]);
    let _ = simulator
        .snapshot(&Mode::Dark.theme())
        .expect("drop target renders");
    let _ = simulator.tap_key(keyboard::key::Named::Escape);
    let _ = simulator.simulate([Event::Mouse(mouse::Event::ButtonReleased(
        mouse::Button::Left,
    ))]);
    let messages: Vec<_> = simulator.into_messages().collect();
    assert!(
        messages.iter().any(|message| matches!(message,
            Message::RevealFolder(path) if path == &root.join("destination")
        )),
        "{messages:?}"
    );
    assert!(!messages
        .iter()
        .any(|message| matches!(message, Message::Move(..))));
    for message in messages {
        let (task, _) = browser.update(message);
        drop(finish(&mut browser, task));
    }
    assert!(browser.expanded.contains(&root.join("destination")));
    assert!(browser
        .listing
        .entries
        .iter()
        .any(|entry| entry.path == root.join("destination/inside.txt")));
    let (task, _) = browser.update(Message::RevealFolder(root.join("destination")));
    drop(finish(&mut browser, task));
    assert!(
        browser.expanded.contains(&root.join("destination")),
        "hovering again must not collapse it"
    );
    assert!(root.join("notes.txt").exists());
}

#[test]
fn drag_scroll_actions_move_only_the_browser_viewport() {
    use iced::{
        advanced::{
            renderer::Headless,
            widget::{operation::Outcome, Operation as _},
        },
        futures::{executor::block_on, StreamExt},
        widget::{row, scrollable, space},
        Font, Length, Size,
    };
    use iced_test::{
        runtime::{task::into_stream, user_interface::Cache, Action, UserInterface},
        selector, Selector,
    };

    use crate::app::{browser::state::TREE, theme::Mode};
    let dir = tempfile::tempdir().expect("scratch folder");
    for index in 0..40 {
        fs::write(dir.path().join(format!("file-{index:02}.txt")), "notes").expect("file");
    }
    let mut browser = ui_browser(dir.path());
    let tasks = [48.0, -24.0].map(|delta| {
        let (task, effect) = browser.update(Message::Scroll(delta));
        assert!(effect.is_none());
        task
    });
    let backend = std::env::var("ICED_TEST_BACKEND").ok();
    let mut renderer = block_on(iced::Renderer::new(
        Font::DEFAULT,
        14.into(),
        backend.as_deref(),
    ))
    .expect("headless renderer");
    let mut ui = UserInterface::build(
        row![
            browser.view(Mode::Light.colors()),
            scrollable(space().height(2000))
                .id("log")
                .width(Length::Fill)
                .height(Length::Fill),
        ],
        Size::new(1040.0, 640.0),
        Cache::default(),
        &mut renderer,
    );
    for (task, offset) in tasks.into_iter().zip([48.0, 24.0]) {
        let actions = block_on(into_stream(task).expect("scroll task").collect::<Vec<_>>());
        for action in actions {
            if let Action::Widget(mut operation) = action {
                ui.operate(&renderer, operation.as_mut());
            }
        }
        for (id, expected) in [(TREE, offset), ("log", 0.0)] {
            let mut find = selector::id(id).find();
            ui.operate(
                &renderer,
                &mut iced::advanced::widget::operation::black_box(&mut find),
            );
            let Outcome::Some(Some(selector::Target::Scrollable { translation, .. })) =
                find.finish()
            else {
                panic!("scrollable {id}");
            };
            assert!(
                (translation.y - expected).abs() < 0.1,
                "{id}: {translation:?}"
            );
            assert!(translation.x.abs() < 0.1);
        }
    }
}

#[test]
fn scrolled_drag_targets_follow_visible_rows_and_edges_request_scrolling() {
    use iced::{keyboard, mouse, time::Instant, window, Event, Point, Size};
    use iced_test::{selector, Simulator};

    use crate::app::{browser::state::TREE, theme::Mode};
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    for index in 0..20 {
        fs::create_dir(root.join(format!("folder-{index:02}"))).expect("folder");
    }
    fs::write(root.join("notes.txt"), "notes").expect("notes");
    let mut browser = ui_browser(root);
    for edge in [true, false] {
        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(280.0, 400.0),
            browser.view(Mode::Light.colors()),
        );
        let viewport = simulator.find(selector::id(TREE)).expect("tree").bounds();
        simulator.point_at(viewport.center());
        let _ = simulator.simulate([Event::Mouse(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Pixels { x: 0.0, y: -2000.0 },
        })]);
        let start = simulator
            .find("notes.txt")
            .expect("source row")
            .visible_bounds()
            .expect("source scrolled into view")
            .center();
        let end = if edge {
            Point::new(viewport.center_x(), viewport.y + 5.0)
        } else {
            simulator
                .find("folder-19")
                .expect("destination row")
                .visible_bounds()
                .expect("visible folder")
                .center()
        };
        simulator.point_at(end);
        let _ = simulator.simulate([
            Event::Mouse(mouse::Event::CursorMoved { position: start }),
            Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
            Event::Mouse(mouse::Event::CursorMoved { position: end }),
        ]);
        if edge {
            let _ = simulator.simulate([Event::Window(window::Event::RedrawRequested(
                Instant::now() + std::time::Duration::from_secs(1),
            ))]);
            let _ = simulator.tap_key(keyboard::key::Named::Escape);
        }
        let _ = simulator.simulate([Event::Mouse(mouse::Event::ButtonReleased(
            mouse::Button::Left,
        ))]);
        let messages: Vec<_> = simulator.into_messages().collect();
        if edge {
            assert!(
                messages
                    .iter()
                    .any(|message| matches!(message, Message::Scroll(y) if *y < 0.0)),
                "{messages:?}"
            );
            assert!(!messages
                .iter()
                .any(|message| matches!(message, Message::Move(..))));
        } else {
            assert!(messages.iter().any(|message| matches!(message,
                Message::Move(paths, directory) if paths == &[root.join("notes.txt")] && directory == &root.join("folder-19")
            )), "{messages:?}");
            for message in messages {
                let (task, _) = browser.update(message);
                drop(finish(&mut browser, task));
            }
            assert!(root.join("folder-19/notes.txt").is_file());
            assert!(!root.join("notes.txt").exists());
        }
    }
}

#[cfg(unix)]
#[test]
fn links_are_hidden_and_recursive_copy_cannot_follow_them() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let outside = tempfile::tempdir().expect("outside folder");
    let root = dir.path();
    fs::create_dir(root.join("source")).expect("folder");
    fs::write(outside.path().join("keep"), "untouched").expect("file");
    std::os::unix::fs::symlink(outside.path(), root.join("link")).expect("link");
    std::os::unix::fs::symlink(outside.path(), root.join("source/link")).expect("nested link");
    let listing = Listing::read(root, &BTreeSet::new()).expect("listing");
    assert!(!listing.entries.iter().any(|entry| entry.name() == "link"));
    assert!(Operation::Copy {
        source: root.join("source"),
        directory: root.into()
    }
    .run(root)
    .is_err());
    assert!(
        !root.join("source copy").exists(),
        "incomplete copy is cleaned up"
    );
    Opened::read(root, &root.join("link/keep")).expect_err("link outside the scratch folder");
    assert!(outside.path().join("keep").exists());
}

#[test]
fn old_scan_results_and_watch_events_cannot_replace_the_current_root() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let mut browser = Browser::default();
    drop(browser.set_root(dir.path().join("old")));
    drop(browser.update(Message::Copy(dir.path().join("old/file"))));
    drop(browser.update(Message::Edit(Edit::Rename(dir.path().join("old/file")))));
    drop(browser.set_root(dir.path().join("new")));
    drop(browser.update(Message::Scanned(1, Err("old scan failed".into()))));
    drop(browser.update(Message::WatchFailed(
        dir.path().join("old"),
        "old watcher".into(),
    )));
    assert!(browser.status.is_none());
    assert!(browser.edit.is_none());
    assert!(browser.clipboard.is_empty());
    let (_, effect) = browser.update(Message::Opened(1, "old/file".into(), Ok(Opened::Audio)));
    assert!(effect.is_none());
    drop(browser.update(Message::Scanned(2, Err("current error".into()))));
    assert_eq!(browser.listing.errors, ["current error"]);
}

#[test]
fn deletion_requires_confirmation_and_failed_operations_preserve_the_form() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let path = dir.path().join("notes.txt");
    fs::write(&path, "notes").expect("file");
    let mut browser = Browser::default();
    drop(browser.set_root(dir.path().into()));
    let (_, effect) = browser.update(Message::Edit(Edit::Delete(vec![path.clone()])));
    assert!(effect.is_none());
    assert!(!browser.busy);
    assert!(path.exists());
    let (_, effect) = browser.update(Message::Confirm);
    assert!(matches!(effect, Some(Effect::Changing(affected)) if affected == [path.clone()]));
    assert!(browser.busy);
    drop(browser.update(Message::Finished(1, Err("locked file".into()))));
    assert!(!browser.busy);
    assert!(browser.edit.is_some());
    assert_eq!(browser.status.as_deref(), Some("locked file"));
    drop(browser.update(Message::Cancel));
    assert!(browser.edit.is_none());
    assert!(path.exists(), "the asynchronous task was never run");
}

fn ui_browser(root: &Path) -> Browser {
    let mut browser = Browser::default();
    drop(browser.set_root(root.into()));
    browser.visible = true;
    browser.listing = Listing::read(root, &BTreeSet::new()).expect("listing");
    browser
}

#[test]
fn tree_opens_on_double_click_and_context_actions_are_clickable_in_both_themes() {
    use iced::{mouse, Event, Size};
    use iced_test::Simulator;

    use crate::app::theme::Mode;
    let dir = tempfile::tempdir().expect("scratch folder");
    let path = dir.path().join("notes.txt");
    fs::write(&path, "notes").expect("file");
    let browser = ui_browser(dir.path());
    for mode in [Mode::Light, Mode::Dark] {
        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(240.0, 500.0),
            browser.view(mode.colors()),
        );
        let _ = simulator.snapshot(&mode.theme()).expect("browser renders");
        let _ = simulator.click("notes.txt").expect("single click");
        let _ = simulator.click("notes.txt").expect("double click");
        let messages: Vec<_> = simulator.into_messages().collect();
        assert!(
            matches!(messages.first(), Some(Message::Click(selected, modifiers, false)) if selected == &path && modifiers.is_empty())
        );
        assert!(messages
            .iter()
            .any(|message| matches!(message, Message::Click(opened, _, true) if opened == &path)));

        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(240.0, 500.0),
            browser.view(mode.colors()),
        );
        let bounds = simulator
            .find("notes.txt")
            .expect("file")
            .visible_bounds()
            .expect("visible");
        simulator.point_at(bounds.center());
        let _ = simulator.simulate([
            Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Right)),
            Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Right)),
        ]);
        let _ = simulator
            .snapshot(&mode.theme())
            .expect("context menu renders");
        let _ = simulator.click("Rename…").expect("context action");
        let messages: Vec<_> = simulator.into_messages().collect();
        assert!(messages
            .iter()
            .any(|message| matches!(message, Message::Context(selected) if selected == &path)));
        assert!(messages.into_iter().any(
            |message| matches!(message, Message::Edit(Edit::Rename(renamed)) if renamed == path)
        ));
    }
}

fn finish(browser: &mut Browser, task: iced::Task<Message>) -> Vec<Effect> {
    use iced::futures::{executor::block_on, StreamExt};
    use iced_test::runtime::{task::into_stream, Action};
    let mut pending = vec![task];
    let mut effects = Vec::new();
    while let Some(task) = pending.pop() {
        if let Some(stream) = into_stream(task) {
            for action in block_on(stream.collect::<Vec<_>>()) {
                if let Action::Output(message) = action {
                    let (task, effect) = browser.update(message);
                    pending.push(task);
                    effects.extend(effect);
                }
            }
        }
    }
    effects
}

#[test]
fn file_action_forms_accept_names_and_require_an_explicit_delete() {
    use iced::{keyboard::key::Named, Size};
    use iced_test::{selector, Simulator};

    use crate::app::{browser::state::NAME_INPUT, theme::Mode};
    let dir = tempfile::tempdir().expect("scratch folder");
    let path = dir.path().join("notes.txt");
    fs::write(&path, "notes").expect("file");
    let mut browser = ui_browser(dir.path());
    for edit in [
        Edit::Rename(path.clone()),
        Edit::CreateFolder(dir.path().into()),
        Edit::Delete(vec![path.clone()]),
    ] {
        drop(browser.update(Message::Edit(edit.clone())));
        let mode = Mode::Dark;
        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(240.0, 550.0),
            browser.view(mode.colors()),
        );
        let _ = simulator
            .snapshot(&mode.theme())
            .expect("file action form renders");
        if matches!(edit, Edit::CreateFolder(_)) {
            let _ = simulator
                .click(selector::id(NAME_INPUT))
                .expect("name input");
            let _ = simulator.typewrite("new folder");
            let _ = simulator.tap_key(Named::Enter);
        } else {
            let _ = simulator
                .click(selector::id("browser-confirm"))
                .expect("confirmation button");
        }
        let messages: Vec<_> = simulator.into_messages().collect();
        assert!(
            messages
                .iter()
                .any(|message| matches!(message, Message::Confirm)),
            "{edit:?}: {messages:?}"
        );
        if matches!(edit, Edit::CreateFolder(_)) {
            assert!(messages
                .iter()
                .any(|message| matches!(message, Message::Name(name) if name == "new folder")));
        }
        // Viewing or typing in a form has not touched the source file.
        assert!(path.exists());
        drop(browser.update(Message::Cancel));
        assert!(browser.edit.is_none());
    }
    drop(browser.update(Message::Click(path.clone(), Modifiers::empty(), false)));
    assert!(browser.selected.contains(&path));
    drop(browser.update(Message::WatchFailed(
        dir.path().into(),
        "temporarily unavailable".into(),
    )));
    assert!(browser.status.is_some());
    let (task, _) = browser.update(Message::Refresh);
    drop(finish(&mut browser, task));
    assert!(browser.status.is_none());
    assert!(matches!(
        browser.update(Message::ChooseRoot).1,
        Some(Effect::ChooseRoot)
    ));
    drop(browser.update(Message::Toggle));
    assert!(!browser.visible);
}

#[test]
fn background_tasks_refresh_open_and_apply_file_actions() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    fs::create_dir(root.join("folder")).expect("folder");
    fs::write(root.join("folder/notes.txt"), "some notes").expect("file");
    let mut browser = Browser::default();
    drop(browser.set_root(root.into()));
    let (scan, _) = browser.update(Message::Toggle);
    drop(browser.update(Message::Expand(root.join("folder"))));
    assert!(finish(&mut browser, scan).is_empty());
    assert_eq!(
        browser.listing.entries.len(),
        2,
        "expansion during a scan schedules a fresh scan"
    );
    let path = root.join("folder/notes.txt");
    let (open, _) = browser.update(Message::Open(path.clone()));
    assert!(
        matches!(finish(&mut browser, open).first(), Some(Effect::Opened(opened, Ok(Opened::Text(text)))) if opened == &path && text == "some notes")
    );
    drop(browser.update(Message::Copy(path)));
    let (paste, _) = browser.update(Message::Paste(root.into()));
    drop(finish(&mut browser, paste));
    assert!(root.join("notes.txt").is_file());
    drop(browser.update(Message::Edit(Edit::Rename(root.join("notes.txt")))));
    drop(browser.update(Message::Name("renamed.txt".into())));
    let (rename, effect) = browser.update(Message::Confirm);
    assert!(matches!(effect, Some(Effect::Changing(_))));
    drop(finish(&mut browser, rename));
    assert!(root.join("renamed.txt").is_file());
    assert!(browser.edit.is_none());
    drop(browser.update(Message::Edit(Edit::CreateFolder(root.into()))));
    drop(browser.update(Message::Name("new folder".into())));
    let (create, _) = browser.update(Message::Confirm);
    drop(finish(&mut browser, create));
    assert!(root.join("new folder").is_dir());
    drop(browser.update(Message::Edit(Edit::Delete(vec![root.join("new folder")]))));
    let (delete, _) = browser.update(Message::Confirm);
    drop(finish(&mut browser, delete));
    assert!(!root.join("new folder").exists());
    assert!(!browser.busy);
    assert!(browser.listing.errors.is_empty());
}

#[test]
fn native_modified_clicks_select_ranges_and_toggle_items_without_opening() {
    use iced::{keyboard, Event, Size};
    use iced_test::Simulator;

    use crate::app::theme::Mode;
    let dir = tempfile::tempdir().expect("scratch folder");
    for name in ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"] {
        fs::write(dir.path().join(name), "notes").expect("file");
    }
    let mut browser = ui_browser(dir.path());
    let mut simulator = Simulator::with_size(
        crate::app::settings(),
        Size::new(280.0, 500.0),
        browser.view(Mode::Light.colors()),
    );
    let _ = simulator.click("a.txt").expect("anchor");
    let _ = simulator.simulate([Event::Keyboard(keyboard::Event::ModifiersChanged(
        Modifiers::SHIFT,
    ))]);
    let _ = simulator.click("d.txt").expect("range end");
    let _ = simulator.click("b.txt").expect("shorter range");
    let _ = simulator.simulate([Event::Keyboard(keyboard::Event::ModifiersChanged(
        Modifiers::COMMAND,
    ))]);
    let _ = simulator.click("e.txt").expect("add to selection");
    let _ = simulator.click("a.txt").expect("remove from selection");
    let _ = simulator.click("a.txt").expect("add back without opening");
    for message in simulator.into_messages() {
        let (task, effect) = browser.update(message);
        assert!(effect.is_none());
        assert!(
            finish(&mut browser, task).is_empty(),
            "modified double click must not open a file"
        );
    }
    assert_eq!(browser.selected.len(), 3);
    for name in ["a.txt", "b.txt", "e.txt"] {
        assert!(browser.selected.contains(&dir.path().join(name)), "{name}");
    }
    drop(browser.update(Message::Context(dir.path().join("b.txt"))));
    assert_eq!(
        browser.selected.len(),
        3,
        "right click preserves an existing selection"
    );
    drop(browser.update(Message::Context(dir.path().join("c.txt"))));
    assert_eq!(browser.selected.len(), 1);
    assert!(browser.selected.contains(&dir.path().join("c.txt")));
    drop(browser.update(Message::Click(
        dir.path().join("e.txt"),
        Modifiers::COMMAND | Modifiers::SHIFT,
        false,
    )));
    assert_eq!(browser.selected.len(), 3, "additive range");
    drop(browser.update(Message::Click(
        dir.path().join("d.txt"),
        Modifiers::empty(),
        false,
    )));
    assert_eq!(
        browser.selected.len(),
        1,
        "ordinary clicks replace the selection"
    );
}

#[test]
fn batch_copy_and_delete_include_selected_folders_only_once() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    let folder = root.join("source");
    let child = folder.join("inside.txt");
    let file = root.join("outside.txt");
    let destination = root.join("destination");
    fs::create_dir(&folder).expect("source");
    fs::create_dir(&destination).expect("destination");
    fs::write(&child, "inside").expect("child");
    fs::write(&file, "outside").expect("file");
    let mut browser = ui_browser(root);
    let (expand, _) = browser.update(Message::Expand(folder.clone()));
    drop(finish(&mut browser, expand));
    for path in [&folder, &child, &file] {
        drop(browser.update(Message::Click(path.clone(), Modifiers::COMMAND, false)));
    }
    assert_eq!(browser.selected.len(), 3);
    drop(browser.update(Message::Copy(child.clone())));
    assert_eq!(browser.clipboard.len(), 2, "parent includes the child");
    let (copy, _) = browser.update(Message::Paste(destination.clone()));
    drop(finish(&mut browser, copy));
    assert!(destination.join("source/inside.txt").is_file());
    assert!(destination.join("outside.txt").is_file());
    assert!(!destination.join("inside.txt").exists());
    let paths = browser.selected.targets(&folder);
    drop(browser.update(Message::Edit(Edit::Delete(paths.clone()))));
    assert!(
        file.exists() && child.exists(),
        "batch deletion also requires confirmation"
    );
    let (delete, effect) = browser.update(Message::Confirm);
    assert!(matches!(effect, Some(Effect::Changing(affected)) if affected == paths));
    drop(finish(&mut browser, delete));
    assert!(!file.exists() && !folder.exists());
    assert!(destination.join("source/inside.txt").is_file());
    assert_eq!(
        browser.selected.len(),
        0,
        "deleted entries cannot stay selected"
    );
}

#[test]
fn partial_batch_failure_is_reported_and_successful_deletions_can_be_retried() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    let path = root.join("file.txt");
    fs::write(&path, "notes").expect("file");
    let operations = [
        Operation::Delete(path.clone()),
        Operation::Delete(root.into()),
    ];
    let error = Operation::run_all(&operations, root).expect_err("root cannot be deleted");
    assert!(error.contains("Some items could not be changed"));
    assert!(!path.exists());
    let retried = Operation::run_all(&operations, root).expect_err("root still cannot be deleted");
    assert!(
        !retried.contains("file.txt"),
        "already completed deletions are not errors"
    );
}

#[test]
fn collapse_removes_hidden_selections_and_shift_can_start_a_new_range() {
    let dir = tempfile::tempdir().expect("scratch folder");
    let folder = dir.path().join("folder");
    let child = folder.join("notes.txt");
    fs::create_dir(&folder).expect("folder");
    fs::write(&child, "notes").expect("file");
    let mut browser = ui_browser(dir.path());
    let (expand, _) = browser.update(Message::Expand(folder.clone()));
    drop(finish(&mut browser, expand));
    drop(browser.update(Message::Click(child, Modifiers::SHIFT, false)));
    assert_eq!(
        browser.selected.len(),
        1,
        "Shift without an anchor selects one item"
    );
    let (collapse, _) = browser.update(Message::Expand(folder.clone()));
    drop(finish(&mut browser, collapse));
    assert_eq!(browser.selected.len(), 0);
    drop(browser.update(Message::Click(folder, Modifiers::SHIFT, false)));
    assert_eq!(browser.selected.len(), 1);
}

#[test]
#[expect(
    clippy::cast_sign_loss,
    reason = "the confirmation panel lies inside the positive window viewport"
)]
fn confirmation_panel_has_a_distinct_surface_and_batch_context_actions() {
    use iced::{mouse, Event, Size};
    use iced_test::{selector, Simulator};

    use crate::app::{
        browser::resize::{MAX_WIDTH, MIN_WIDTH},
        theme::Mode,
    };

    let dir = tempfile::tempdir().expect("scratch folder");
    for name in ["a.txt", "b.txt"] {
        fs::write(dir.path().join(name), "notes").expect("file");
    }
    let mut browser = ui_browser(dir.path());
    for name in ["a.txt", "b.txt"] {
        drop(browser.update(Message::Click(
            dir.path().join(name),
            Modifiers::COMMAND,
            false,
        )));
    }
    for mode in [Mode::Light, Mode::Dark] {
        let colors = mode.colors();
        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(280.0, 500.0),
            browser.view(colors),
        );
        let file = simulator
            .find("a.txt")
            .expect("file")
            .visible_bounds()
            .expect("visible");
        simulator.point_at(file.center());
        let _ = simulator.simulate([Event::Mouse(mouse::Event::ButtonPressed(
            mouse::Button::Right,
        ))]);
        let _ = simulator.click("Rename…").expect("disabled rename");
        let messages: Vec<_> = simulator.into_messages().collect();
        assert!(!messages
            .iter()
            .any(|message| matches!(message, Message::Edit(Edit::Rename(_)))));

        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(280.0, 500.0),
            browser.view(colors),
        );
        simulator.point_at(file.center());
        let _ = simulator.simulate([Event::Mouse(mouse::Event::ButtonPressed(
            mouse::Button::Right,
        ))]);
        let _ = simulator.click("Delete…").expect("delete selected items");
        for message in simulator.into_messages() {
            drop(browser.update(message));
        }
        assert!(matches!(&browser.edit, Some(Edit::Delete(paths)) if paths.len() == 2));
        for width in [MIN_WIDTH, MAX_WIDTH] {
            drop(browser.update(Message::Resize(width)));
            let mut simulator = Simulator::with_size(
                crate::app::settings(),
                Size::new(width, 500.0),
                browser.view(colors),
            );
            let bounds = simulator
                .find(selector::id("browser-confirmation"))
                .expect("confirmation card")
                .visible_bounds()
                .expect("visible confirmation");
            let _ = simulator
                .find("2 selected items\nIncluding folder contents. This cannot be undone.")
                .expect("selection count");
            let snapshot = simulator
                .snapshot(&mode.theme())
                .expect("confirmation renders");
            let pixels = crate::app::snapshot::pixels(&snapshot);
            let scale = pixels.width() as f32 / width;
            assert_eq!(
                pixels
                    .get_pixel(
                        ((bounds.x + 3.0) * scale) as u32,
                        ((bounds.y + 3.0) * scale) as u32
                    )
                    .0,
                colors.rule.into_rgba8()
            );
            assert_ne!(colors.rule, colors.paper);
            if let Ok(directory) = std::env::var("ATHENACL_BROWSER_PREVIEW") {
                pixels
                    .save(
                        Path::new(&directory)
                            .join(format!("confirmation-{}-{width}.png", mode.name())),
                    )
                    .expect("preview");
            }
        }
        drop(browser.update(Message::Cancel));
        drop(browser.update(Message::Resize(280.0)));
    }
}

#[test]
fn keys_move_through_the_tree_and_take_the_menus_actions() {
    use iced::keyboard::{key::Named, Key};

    let dir = tempfile::tempdir().expect("scratch folder");
    let root = dir.path();
    fs::create_dir(root.join("scores")).expect("folder");
    fs::write(root.join("scores/first.mid"), b"MThd").expect("midi");
    fs::write(root.join("notes.txt"), "notes").expect("file");
    fs::write(root.join("render.wav"), b"RIFF").expect("audio");
    let mut browser = ui_browser(root);
    let press = |browser: &mut Browser, key: Key, modifiers: Modifiers| {
        let (task, effect) = browser.update(Message::Key(key, modifiers));
        let mut effects = finish(browser, task);
        effects.extend(effect);
        effects
    };
    let arrow = |named: Named| Key::Named(named);
    let only = |browser: &Browser, name: &str| {
        browser.selected.len() == 1 && browser.selected.contains(&root.join(name))
    };

    // with nothing selected, down takes the first entry; shift takes the next one too
    drop(press(
        &mut browser,
        arrow(Named::ArrowDown),
        Modifiers::empty(),
    ));
    assert!(only(&browser, "scores"));
    drop(press(
        &mut browser,
        arrow(Named::ArrowDown),
        Modifiers::empty(),
    ));
    assert!(only(&browser, "notes.txt"));
    drop(press(
        &mut browser,
        arrow(Named::ArrowDown),
        Modifiers::SHIFT,
    ));
    assert_eq!(browser.selected.len(), 2);
    // up goes on from where the keys last were
    drop(press(
        &mut browser,
        arrow(Named::ArrowUp),
        Modifiers::empty(),
    ));
    assert!(only(&browser, "notes.txt"));
    drop(press(
        &mut browser,
        arrow(Named::ArrowUp),
        Modifiers::empty(),
    ));
    assert!(only(&browser, "scores"));

    // a folder opens to the right; from inside it, left goes back to it and then closes it
    drop(press(
        &mut browser,
        arrow(Named::ArrowRight),
        Modifiers::empty(),
    ));
    assert!(browser.expanded.contains(&root.join("scores")));
    drop(press(
        &mut browser,
        arrow(Named::ArrowDown),
        Modifiers::empty(),
    ));
    assert!(only(&browser, "scores/first.mid"));
    drop(press(
        &mut browser,
        arrow(Named::ArrowLeft),
        Modifiers::empty(),
    ));
    assert!(only(&browser, "scores"));
    drop(press(
        &mut browser,
        arrow(Named::ArrowLeft),
        Modifiers::empty(),
    ));
    assert!(!browser.expanded.contains(&root.join("scores")));

    // return opens a file, as a double click does
    browser.selected.only(root.join("notes.txt"));
    let effects = press(&mut browser, arrow(Named::Enter), Modifiers::empty());
    assert!(effects.iter().any(
        |effect| matches!(effect, Effect::Opened(opened, Ok(_)) if opened == &root.join("notes.txt"))
    ));

    // the context menu's actions, by the keys it shows beside them
    drop(press(&mut browser, arrow(Named::F2), Modifiers::empty()));
    assert!(matches!(&browser.edit, Some(Edit::Rename(path)) if path == &root.join("notes.txt")));
    assert_eq!(browser.name, "notes.txt");
    drop(browser.update(Message::Cancel));
    drop(press(
        &mut browser,
        arrow(Named::Backspace),
        Modifiers::empty(),
    ));
    assert!(
        matches!(&browser.edit, Some(Edit::Delete(paths)) if paths == &vec![root.join("notes.txt")])
    );
    drop(browser.update(Message::Cancel));
    drop(press(
        &mut browser,
        Key::Character("N".into()),
        Modifiers::COMMAND | Modifiers::SHIFT,
    ));
    assert!(matches!(&browser.edit, Some(Edit::CreateFolder(directory)) if directory == root));
    drop(browser.update(Message::Cancel));
    drop(press(
        &mut browser,
        Key::Character("c".into()),
        Modifiers::COMMAND,
    ));
    assert_eq!(browser.clipboard, vec![root.join("notes.txt")]);
    drop(press(
        &mut browser,
        Key::Character("v".into()),
        Modifiers::COMMAND,
    ));
    assert_eq!(
        fs::read_dir(root).expect("root").count(),
        4,
        "pasted beside itself, as a copy"
    );

    drop(press(
        &mut browser,
        Key::Character("a".into()),
        Modifiers::COMMAND,
    ));
    assert_eq!(browser.selected.len(), browser.listing.entries.len());
    browser.focused = true;
    drop(press(
        &mut browser,
        arrow(Named::Escape),
        Modifiers::empty(),
    ));
    assert_eq!(browser.selected.len(), 0);
    assert!(!browser.focused, "escape gives the keys back");
}

#[test]
fn a_click_in_the_tree_gives_it_the_keys_and_one_elsewhere_takes_them_back() {
    use iced::{
        mouse,
        widget::{row, space},
        Event, Point, Size,
    };
    use iced_test::Simulator;

    use crate::app::theme::Mode;
    let dir = tempfile::tempdir().expect("scratch folder");
    fs::write(dir.path().join("notes.txt"), "notes").expect("file");
    let mut browser = ui_browser(dir.path());
    assert!(!browser.focused);
    drop(browser.update(Message::Click(
        dir.path().join("notes.txt"),
        Modifiers::empty(),
        false,
    )));
    assert!(browser.focused);

    let colors = Mode::Light.colors();
    let mut simulator = Simulator::with_size(
        crate::app::settings(),
        Size::new(600.0, 400.0),
        row![browser.view(colors), space::horizontal()],
    );
    simulator.point_at(Point::new(500.0, 200.0));
    let _ = simulator.simulate([
        Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
        Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)),
    ]);
    let messages: Vec<_> = simulator.into_messages().collect();
    assert!(messages
        .iter()
        .any(|message| matches!(message, Message::Blur)));
    for message in messages {
        drop(browser.update(message));
    }
    assert!(!browser.focused);
}

#[test]
fn a_row_is_shaded_under_the_pointer() {
    use iced::{mouse, Color, Event, Size};
    use iced_test::Simulator;

    use crate::app::theme::Mode;
    let dir = tempfile::tempdir().expect("scratch folder");
    fs::write(dir.path().join("notes.txt"), "notes").expect("file");
    let browser = ui_browser(dir.path());
    let colors = Mode::Light.colors();
    let mut simulator = Simulator::with_size(
        crate::app::settings(),
        Size::new(280.0, 300.0),
        browser.view(colors),
    );
    let name = simulator
        .find("notes.txt")
        .expect("row")
        .visible_bounds()
        .expect("visible");
    // the row's pixels left of its mark, at the snapshot's twice the size
    let (top, bottom) = (f64::from(name.y), f64::from(name.y + name.height));
    let pixels = |simulator: &mut Simulator<'_, Message>| {
        crate::app::snapshot::pixels(&simulator.snapshot(&Mode::Light.theme()).expect("renders"))
            .enumerate_pixels()
            .filter(|&(x, y, _)| {
                let (x, y) = (f64::from(x) / 2.0, f64::from(y) / 2.0);
                (1.0..4.0).contains(&x) && (top..bottom).contains(&y)
            })
            .map(|(_, _, pixel)| pixel.0)
            .collect::<Vec<_>>()
    };
    let before = pixels(&mut simulator);
    assert!(!before.is_empty());
    assert!(before
        .iter()
        .all(|pixel| *pixel == colors.paper.into_rgba8()));

    simulator.point_at(name.center());
    let _ = simulator.simulate([Event::Mouse(mouse::Event::CursorMoved {
        position: name.center(),
    })]);
    let half = |page: f32, rule: f32| (page + rule) / 2.0;
    let shade = Color::from_rgb(
        half(colors.paper.r, colors.rule.r),
        half(colors.paper.g, colors.rule.g),
        half(colors.paper.b, colors.rule.b),
    )
    .into_rgba8();
    let shaded = pixels(&mut simulator);
    assert!(
        shaded.iter().all(|pixel| pixel
            .iter()
            .zip(shade)
            .all(|(drawn, expected)| drawn.abs_diff(expected) <= 1)),
        "the row is not shaded {shade:?}"
    );
}
