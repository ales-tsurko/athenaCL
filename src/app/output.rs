//! The view for interpreter's output.

use iced::{
    alignment, font,
    widget::{
        button, column, container, container::Appearance as ContainerAppearance, horizontal_rule,
        scrollable, text, Column, Row,
    },
    Border, Font, Length,
};

use super::Message;
use crate::interpreter::{LinkOutput, ModuleResult as InterpreterResult, Output};

#[derive(Debug, Default)]
pub(crate) struct OutputView {
    width: f32,
    output: Option<InterpreterResult<Vec<Output>>>,
}

impl OutputView {
    pub(crate) fn with_width(mut self, width: f32) -> Self {
        self.width = width;
        self
    }

    pub(crate) fn update(&mut self, output: Option<InterpreterResult<Vec<Output>>>) {
        self.output = output;
    }

    pub(crate) fn view(&self) -> iced::Element<'_, Message> {
        if let Some(output) = &self.output {
            return match output {
                Ok(msg) => self.view_output(msg),
                Err(msg) => self.view_error(msg.to_string()),
            };
        }

        container("").width(self.width).into()
    }

    fn view_output(&self, outputs: &[Output]) -> iced::Element<'_, Message> {
        let mut elements = vec![];
        for output in outputs {
            elements.push(self.parse_output(output));
        }
        scrollable(
            column(elements)
                .width(self.width)
                .padding([20.0, 0.0, 20.0, 0.0]),
        )
        .width(self.width)
        .height(Length::Fill)
        .into()
    }

    fn parse_output(&self, output: &Output) -> iced::Element<'_, Message> {
        match output {
            Output::Paragraph(value) => self.view_paragraph(value),
            Output::Header(value) => self.view_header(value),
            Output::Divider => horizontal_rule(20.0).into(),
            Output::List(value) => self.view_grid(value, 8),
            Output::Link(value) => self.view_link(value),
        }
    }

    fn view_grid(&self, list: &[Output], per_row: usize) -> iced::Element<'_, Message> {
        let mut top_row = Row::new().spacing(10.0);
        let mut column = Column::new()
            .spacing(10.0)
            .width(self.width)
            .align_items(iced::Alignment::Start);

        for (n, output) in list.iter().enumerate() {
            if n % per_row == 0 {
                column = column.push(top_row);
                top_row = Row::new().spacing(10.0);
                continue;
            }

            // top_row = top_row.push(horizontal_space());
            top_row = top_row.push(self.parse_output(output));
        }
        column.push(top_row).into()
    }

    fn view_link(&self, link: &LinkOutput) -> iced::Element<'_, Message> {
        button(
            text(&link.text)
                .font(Font::MONOSPACE)
                .horizontal_alignment(alignment::Horizontal::Center),
        )
        .width(link.width)
        .style(iced::theme::Button::Text)
        .on_press(Message::SendCommand(link.cmd.to_owned()))
        .into()
    }

    fn view_paragraph(&self, value: &str) -> iced::Element<'_, Message> {
        text(value).font(Font::MONOSPACE).into()
    }

    fn view_header(&self, value: &str) -> iced::Element<'_, Message> {
        let mut style = Font::MONOSPACE;
        style.weight = font::Weight::Bold;
        text(value).font(style).into()
    }

    fn view_error(&self, msg: String) -> iced::Element<'_, Message> {
        let text = text(msg).font(Font::MONOSPACE).width(self.width);
        let mut style = ContainerAppearance::default();
        style.border = Border {
            color: [1.0, 0.0, 0.0].into(),
            width: 1.0,
            ..Default::default()
        };
        container(text)
            .width(self.width)
            .style(style)
            .padding(20.0)
            .into()
    }
}
