//! Quit that closes the window, rather than ending the app.
//!
//! On macOS, winit's app menu binds Quit (Cmd+Q) to `-[NSApplication terminate:]`, which ends the
//! app at once: iced never hears of it, and an app can't first offer to save unsaved work. Pointed
//! at the window's `performClose:`, Quit asks the window to close, as its close button does, and
//! iced reports that as a close request. Quitting from the Dock, or by logging out, still ends the
//! app at once.

pub use route::{route, Error};

#[cfg(target_os = "macos")]
mod app_kit;
mod route;
