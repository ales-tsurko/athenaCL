//! Wizard is an overlay over normal output views, which supposed to block user's interaction by
//! requesting data (to create new PathInstance, for example).

use iced::widget::{
    button, column, container, container::Style as ContainerStyle, horizontal_rule,
    horizontal_space, opaque, row, text,
};
use iced::Element;

use crate::app::Message;
use crate::interpreter::Input;

#[derive(Debug, Default)]
pub struct State {
    pub title: String,
    pub inputs: Vec<Input>,
}

#[allow(missing_docs)]
pub fn view<'a>() -> Element<'a, Message> {
    opaque(
        container(
            container(
                column![
                    column![super::view_header("PIn"), horizontal_rule(1)],
                    view_form(),
                    row![
                        horizontal_space(),
                        button("send").on_press(Message::SendCommand("help".to_string()))
                    ]
                ]
                .spacing(20.0), // .align_x(iced::Alignment::Center),
            )
            .padding(40.0)
            .style(|theme: &iced::Theme| ContainerStyle {
                background: Some(theme.palette().background.into()),
                ..Default::default()
            }),
        )
        .padding([50.0, 100.0])
        .width(iced::Length::Fill)
        .height(iced::Length::Fill)
        .style(|_| ContainerStyle {
            background: Some(iced::Background::Color([0.0, 0.0, 0.0, 0.99].into())),
            ..Default::default()
        }),
    )
    .into()
}

fn view_form<'a>() -> Element<'a, Message> {
    container(text("form")).width(iced::Length::Fill).into()
}
