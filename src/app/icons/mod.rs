//! Reusable pixel icons, with their only artwork source in `glyphs`.
//!
//! Each widget retains its coloured raster across view rebuilds. Repaints reuse the image
//! handle and Iced's texture cache; only a glyph or foreground colour change rebuilds pixels.
//! Nearest-neighbour sampling keeps the native grid sharp at different display scales.

pub(crate) use glyphs::Icon;

mod cache;
mod glyphs;
mod widget;
