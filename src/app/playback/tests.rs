//! Persistence and the controls' actual pointer interactions.

use std::path::PathBuf;

use iced::{
    futures::{executor::block_on, StreamExt},
    mouse, Event, Point, Size,
};
use iced_test::{
    runtime::{task::into_stream, Action},
    Simulator,
};

use crate::app::{
    playback::{
        preferences::{Preferences, Settings},
        Message,
    },
    theme::Mode,
};

fn finish(preferences: &mut Preferences, task: iced::Task<Message>) {
    let Some(stream) = into_stream(task) else {
        return;
    };
    for action in block_on(stream.collect::<Vec<_>>()) {
        if let Action::Output(Message::Saved(result)) = action {
            result.expect("save preferences");
            let next = preferences.saved();
            finish(preferences, next);
        }
    }
}

#[test]
fn preferences_keep_the_latest_level_mute_and_recent_fonts_across_sessions() {
    let dir = tempfile::tempdir().expect("preferences directory");
    let path = dir.path().join("playback.json");
    let (mut preferences, error) = Preferences::at(path.clone());
    assert!(error.is_none());
    preferences.settings.volume = 8;
    let first = preferences.save();
    preferences.settings.volume = 4;
    preferences.settings.muted = true;
    for name in ["first 音.sf2", "second.sf2", "first 音.sf2"] {
        preferences.settings.select(Some(dir.path().join(name)));
    }
    drop(preferences.save());
    finish(&mut preferences, first);
    let (restored, error) = Preferences::at(path);
    assert!(error.is_none());
    assert_eq!(restored.settings, preferences.settings);
    assert_eq!(restored.settings.percent(), 33);
    assert!(restored.settings.gain().abs() < f32::EPSILON);
    assert_eq!(restored.settings.recent.len(), 2);
    assert_eq!(
        restored.settings.recent.first(),
        restored.settings.soundfont.as_ref()
    );
    let mut unmuted = restored.settings.clone();
    unmuted.muted = false;
    assert!((unmuted.gain() - 1.0 / 3.0).abs() < 1e-6);
}

#[test]
fn quitting_while_a_save_is_pending_keeps_the_final_level() {
    let dir = tempfile::tempdir().expect("preferences directory");
    let path = dir.path().join("playback.json");
    let (mut preferences, _) = Preferences::at(path.clone());
    preferences.settings.set_volume(0.25);
    let first = preferences.save();
    preferences.settings.set_volume(0.75);
    preferences.settings.muted = true;
    drop(preferences.save());
    drop(preferences);
    drop(first);
    let (restored, error) = Preferences::at(path);
    assert!(error.is_none());
    assert_eq!(restored.settings.volume, 9);
    assert!(restored.settings.muted);
}

#[test]
fn malformed_preferences_are_preserved_and_out_of_range_levels_are_clamped() {
    let dir = tempfile::tempdir().expect("preferences directory");
    let path = dir.path().join("playback.json");
    std::fs::write(&path, "broken").expect("invalid preferences");
    let (mut preferences, error) = Preferences::at(path.clone());
    assert!(error.is_some());
    let task = preferences.save();
    finish(&mut preferences, task);
    assert_eq!(
        std::fs::read_to_string(&path).expect("read preserved file"),
        "broken"
    );
    std::fs::write(&path, r#"{"volume":200,"recent":["a.sf2","a.sf2"]}"#).expect("preferences");
    let (preferences, error) = Preferences::at(path);
    assert!(error.is_none());
    assert_eq!(preferences.settings.volume, 12);
    assert_eq!(preferences.settings.recent, vec![PathBuf::from("a.sf2")]);
}

#[test]
fn volume_click_drag_scroll_double_click_and_mute_produce_the_right_actions() {
    let mut preferences = Preferences::default();
    preferences.settings = Settings {
        volume: 8,
        muted: true,
        ..Settings::default()
    };
    let mut simulator = Simulator::with_size(
        crate::app::settings(),
        Size::new(300.0, 60.0),
        preferences.volume(Mode::Light.colors()),
    );
    let bounds = simulator
        .find(iced_test::selector::id("master-volume"))
        .expect("meter")
        .bounds();
    // Ten pixels inside the frame is the start of the segmented track.
    let at = Point::new(bounds.x + 10.0 + 144.0 * 0.5, bounds.center_y());
    simulator.point_at(at);
    let _ = simulator.simulate([
        Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
        Event::Mouse(mouse::Event::CursorMoved {
            position: Point::new(bounds.x + bounds.width + 40.0, at.y),
        }),
        Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)),
    ]);
    simulator.point_at(at);
    let _ = simulator.simulate([
        Event::Mouse(mouse::Event::WheelScrolled {
            delta: mouse::ScrollDelta::Lines { x: 0.0, y: 1.0 },
        }),
        Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)),
        Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)),
    ]);
    let _ = simulator
        .click(iced_test::selector::id("master-mute"))
        .expect("mute button");
    let messages: Vec<_> = simulator.into_messages().collect();
    let levels: Vec<_> = messages
        .iter()
        .filter_map(|message| match message {
            Message::Volume(value) => Some(*value),
            _ => None,
        })
        .collect();
    assert!((levels[0] - 0.5).abs() < 1e-6, "{levels:?}");
    assert!((levels[1] - 1.0).abs() < 1e-6, "drag clamps to full");
    assert!(
        (levels[2] - 0.75).abs() < 1e-6,
        "scroll uses the remembered muted level"
    );
    assert!(
        (levels[3] - 1.0).abs() < 1e-6,
        "double click resets to full"
    );
    assert!(messages
        .iter()
        .any(|message| matches!(message, Message::Mute)));
}

#[test]
fn sound_menu_shows_builtin_recent_folders_and_load_last() {
    let mut preferences = Preferences::default();
    let path = PathBuf::from("Sounds/Grand 音.sf2");
    preferences.settings.select(Some(path.clone()));
    preferences.menu_open = true;
    for mode in [Mode::Light, Mode::Dark] {
        let mut simulator = Simulator::with_size(
            crate::app::settings(),
            Size::new(600.0, 400.0),
            preferences.sound(Some(&path), false, mode.colors()),
        );
        for label in [
            "FluidR3 GM",
            "built in",
            "Grand 音",
            "Sounds",
            "Load sound font…",
            ".sf2",
        ] {
            assert!(simulator.find(label).is_ok(), "{label}");
        }
        let builtin = simulator.find("FluidR3 GM").expect("builtin").bounds();
        let recent = simulator.find("Sounds").expect("recent folder").bounds();
        let load = simulator.find("Load sound font…").expect("load").bounds();
        assert!(builtin.y < recent.y && recent.y < load.y);
        let _ = simulator.click("Load sound font…").expect("choose font");
        assert!(simulator
            .into_messages()
            .any(|message| matches!(message, Message::Choose)));
    }
}
