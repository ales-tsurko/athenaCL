//! The executable.

use athenacl::app;

fn main() -> iced::Result {
    iced::application(app::State::default, app::update, app::view)
        .title("athenaCL")
        .subscription(app::subscription)
        .theme(app::theme)
        // figures are pixel art: without multisampling, their pixels stay sharp at any offset
        .antialiasing(false)
        .centered()
        .settings(iced::Settings {
            id: Some(app::APPLICATION_ID.to_string()),
            default_text_size: 14.into(),
            default_font: iced::Font::with_name("Fira Mono"),
            ..Default::default()
        })
        .window(iced::window::Settings {
            min_size: Some((app::MIN_WINDOW_SIZE).into()),
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
        .font(iced_fonts::NERD_FONT_BYTES)
        .run()
}
