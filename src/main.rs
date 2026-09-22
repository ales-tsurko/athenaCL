//! The executable.

use athenacl::app;

fn main() -> iced::Result {
    iced::application(app::boot, app::update, app::view)
        .title(app::title)
        .subscription(app::subscription)
        .theme(app::theme)
        .centered()
        // the settings carry the fonts and switch antialiasing off; set once, as setting them
        // replaces whatever was set before
        .settings(app::settings())
        .window(iced::window::Settings {
            size: (1120.0, 760.0).into(),
            min_size: Some((app::MIN_WINDOW_SIZE).into()),
            // the app closes it once it's offered to save unsaved work
            exit_on_close_request: false,
            ..Default::default()
        })
        .run()
}
