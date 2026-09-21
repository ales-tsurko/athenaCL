//! This module keeps GUI-related stuff.

pub use app::*;

#[expect(
    clippy::module_inception,
    reason = "the module is the `app` module's core"
)]
mod app;
mod browser;
mod completion;
mod figure;
mod history;
mod icons;
mod manual;
mod pixel;
mod playback;
mod player;
mod scrollbar;
mod segments;
#[cfg(test)]
mod snapshot;
mod terminal_input;
pub(crate) mod theme;
