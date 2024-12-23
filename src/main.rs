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
            default_font: iced::Font::with_name("Fira Mono"),
            ..Default::default()
        })
        .window(iced::window::Settings {
            min_size: Some((800.0, 600.0).into()),
            max_size: Some((800.0, f32::MAX).into()),
            ..Default::default()
        })
        .font(include_bytes!(
            "../resources/fonts/Fira_Mono/FiraMono-Bold.ttf"
        ))
        .font(include_bytes!(
            "../resources/fonts/Fira_Mono/FiraMono-Medium.ttf"
        ))
        .font(include_bytes!(
            "../resources/fonts/Fira_Mono/FiraMono-Regular.ttf"
        ))
        .font(iced_fonts::REQUIRED_FONT_BYTES)
        .font(iced_fonts::NERD_FONT_BYTES)
        .run()
}
