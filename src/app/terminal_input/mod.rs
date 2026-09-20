//! Command input with Iced's editing behavior and a terminal block caret.

pub(crate) use input::Input;

mod input;
mod renderer;

#[cfg(test)]
mod tests;
