//! Persistent playback preferences and their header/footer controls.

pub(crate) use preferences::Preferences;
pub use view::Message;

mod preferences;
mod view;

#[cfg(test)]
mod tests;
