//! Shared scrollbar geometry for the log and file browser; colors come from the theme.

use iced::widget::scrollable::Scrollbar;

const TRACK: f32 = 1.0;
const THUMB: f32 = 3.0;
const MARGIN: f32 = 4.0;
const SPACING: f32 = 13.0;

/// Width reserved beside scrollable content, including the grab area and spacing.
pub(crate) const RESERVED_WIDTH: f32 = TRACK.max(THUMB) + 2.0 * MARGIN + SPACING;

/// A vertical rail with space between it and the content.
pub(crate) fn vertical() -> Scrollbar {
    horizontal().spacing(SPACING)
}

/// A hairline track with a thin thumb and a wider grab area.
pub(crate) fn horizontal() -> Scrollbar {
    Scrollbar::new()
        .width(TRACK)
        .scroller_width(THUMB)
        .margin(MARGIN)
}
