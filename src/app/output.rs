//! The view for interpreter's output.

use iced::{
    alignment, font,
    widget::{
        button,
        checkbox,
        column,
        container,
        container::Style as ContainerStyle,
        horizontal_rule,
        horizontal_space,
        row,
        // rule::{self, Appearance as RuleAppearance},
        scrollable,
        text,
        Column,
        Row,
    },
    Border, Font,
};
use uuid::Uuid;

use super::Message;
use crate::interpreter::{LinkOutput, ModuleResult as InterpreterResult, Output};

#[derive(Debug)]
pub(crate) struct OutputViewState {
    id: Uuid,
    width: f32,
    output: Option<InterpreterResult<Vec<Output>>>,
    is_pinned: bool,
    cmd: String,
}

impl Default for OutputViewState {
    fn default() -> Self {
        Self {
            id: Uuid::new_v4(),
            width: 0.0,
            output: None,
            is_pinned: false,
            cmd: String::new(),
        }
    }
}

impl OutputViewState {
    pub(crate) fn id(&self) -> Uuid {
        self.id
    }

    pub(crate) fn with_width(mut self, width: f32) -> Self {
        self.width = width;
        self
    }

    pub(crate) fn set_output(&mut self, output: Option<InterpreterResult<Vec<Output>>>) {
        self.output = output;
    }

    pub(crate) fn set_cmd(&mut self, cmd: &str) {
        self.cmd = cmd.to_owned();
    }

    pub(crate) fn set_pinned(&mut self, is_pinned: bool) {
        self.is_pinned = is_pinned;
    }
}

pub(crate) fn view(state: &OutputViewState) -> iced::Element<Message> {
    if let Some(output) = &state.output {
        return match output {
            Ok(msg) => view_output(state, msg),
            Err(msg) => view_error(state.width, msg.to_string()),
        };
    }

    container("").width(state.width).into()
}

fn view_output<'a>(
    state: &'a OutputViewState,
    outputs: &'a [Output],
) -> iced::Element<'a, Message> {
    let mut elements = vec![view_output_header(state.id, state.is_pinned, &state.cmd)];
    for output in outputs {
        elements.push(render_output(output));
    }

    container(column(elements))
        .width(state.width)
        .padding(20.0)
        .into()
}

fn view_error<'a>(width: f32, msg: String) -> iced::Element<'a, Message> {
    let text = text(msg).font(Font::MONOSPACE).width(width);
    let mut style = ContainerStyle::default();
    style.border = Border {
        color: [1.0, 0.0, 0.0].into(),
        width: 1.0,
        ..Default::default()
    };
    container(text)
        .width(width)
        .style(move |_| style)
        .padding(20.0)
        .into()
}

fn render_output<'a>(output: &'a Output) -> iced::Element<'a, Message> {
    match output {
        Output::Paragraph(value) => view_paragraph(value),
        Output::Header(value) => view_header(value),
        Output::Divider => horizontal_rule(20.0).into(),
        Output::Row(value) => view_row(value),
        Output::Link(value) => view_link(value),
    }
}

fn view_paragraph(value: &str) -> iced::Element<Message> {
    container(text(value).font(Font::MONOSPACE))
        .padding(20.0)
        .into()
}

fn view_header(value: &str) -> iced::Element<Message> {
    let mut style = Font::MONOSPACE;
    style.weight = font::Weight::Bold;
    container(text(value).font(style).size(18.0))
        .padding([20.0, 0.0])
        .into()
}

fn view_row<'a>(list: &'a [Output]) -> iced::Element<'a, Message> {
    let mut row = Row::new().spacing(10.0);
    for output in list.iter() {
        row = row.push(render_output(output));
    }

    row.wrap().into()
}

fn view_link(link: &LinkOutput) -> iced::Element<Message> {
    button(
        text(&link.text)
            .font(Font::MONOSPACE)
            .align_x(alignment::Horizontal::Center),
    )
    .style(iced::widget::button::text)
    .on_press(Message::SendCommand(link.cmd.to_owned()))
    .into()
}

fn view_output_header<'a>(id: Uuid, is_pinned: bool, title: &'a str) -> iced::Element<'a, Message> {
    container(
        row(vec![
            view_header(title),
            horizontal_space().into(),
            container(
                checkbox("pin", is_pinned).on_toggle(move |v| Message::SetPinOutput((id, v))),
            )
            .padding([0.0, 40.0])
            .into(),
        ])
        .align_y(iced::Alignment::Center),
    )
    .style(|_| ContainerStyle {
        background: Some(iced::Color::from_rgba(0.0, 0.0, 0.0, 0.2).into()),
        ..Default::default()
    })
    .into()
}
