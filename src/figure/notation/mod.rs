//! Pixel music notation for a texture's events.
//!
//! A [`Score`] engraves events once, in notation pixels, with every horizontal position tied to
//! an event's place on the x axis: its time, or its slot among the events. Drawing it along an
//! [`Axis`] then places everything at any zoom. The notation is athenaCL's: there is no meter, so
//! no time signatures or barlines; notes are beamed by beat, pitches are spelled with sharps and
//! quarter-sharps, and each accidental applies only to its own note.

mod engraving;
mod glyphs;

pub use engraving::{Axis, Note, Run, Score};
