//! Cached command, session-name and history suggestions for the terminal input.

pub use completion::Action;
pub(crate) use completion::{Sources, Suggestions};

#[expect(clippy::module_inception, reason = "the module's completion state")]
mod completion;
mod view;

#[cfg(test)]
mod tests;
