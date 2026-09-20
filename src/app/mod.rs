//! This module keeps GUI-related stuff.

pub use app::*;

#[expect(
    clippy::module_inception,
    reason = "the module is the `app` module's core"
)]
mod app;
mod completion;
mod figure;
mod history;
mod icons;
mod pixel;
mod player;
mod terminal_input;
pub(crate) mod theme;
