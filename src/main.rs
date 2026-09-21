//! The executable.

use athenacl::app;

fn main() -> iced::Result {
    iced::application(app::boot, app::update, app::view)
        .title("athenaCL")
        .subscription(app::subscription)
        .theme(app::theme)
        .centered()
        // the settings carry the fonts and switch antialiasing off; set once, as setting them
        // replaces whatever was set before
        .settings(app::settings())
        .window(iced::window::Settings {
            size: (1120.0, 760.0).into(),
            min_size: Some((app::MIN_WINDOW_SIZE).into()),
            ..Default::default()
        })
        .run()
}
