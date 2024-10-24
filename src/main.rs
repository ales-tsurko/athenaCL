//! The executable.

use athenacl::app;

fn main() -> iced::Result {
    iced::application("athenaCL", app::update, app::view)
        .subscription(app::subscription)
        .antialiasing(true)
        .centered()
        .settings(iced::settings::Settings {
            id: Some(app::APPLICATION_ID.to_string()),
            default_text_size: 14.into(),
            default_font: iced::Font::MONOSPACE,
            ..Default::default()
        })
        .window(iced::window::Settings {
            min_size: Some((800.0, 600.0).into()),
            ..Default::default()
        })
        .run()
}
