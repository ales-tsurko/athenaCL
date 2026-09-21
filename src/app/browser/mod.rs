//! The scratch folder: a cached tree, background file operations and native change notifications.

pub use state::Message;
pub(crate) use filesystem::Opened;
pub(crate) use state::{Browser, Effect};
#[cfg(test)]
pub(crate) use state::Edit;

mod drag;
mod filesystem;
mod input;
mod resize;
mod selection;
mod state;
#[cfg(test)]
mod tests;
mod view;
mod watch;
