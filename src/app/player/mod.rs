//! Playback controls and a shared, replaceable system audio output.

pub use player::{Message, PlayerId};
pub(crate) use player::{subscription, update, view, GlobalState, Track};

mod events;
mod gain;
mod output;
#[expect(
    clippy::module_inception,
    reason = "the module holds the player state and controls"
)]
mod player;
