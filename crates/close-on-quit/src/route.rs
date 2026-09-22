//! Quit, pointed at the window's close button.

use raw_window_handle::RawWindowHandle;

/// Point Quit at the close button of the window `window` is the handle of.
///
/// Only macOS quits otherwise than by closing the window; elsewhere, there is nothing to do. It
/// must be called on the main thread, as iced runs a window's tasks.
pub fn route(window: RawWindowHandle) -> Result<(), Error> {
    match window {
        #[cfg(target_os = "macos")]
        RawWindowHandle::AppKit(handle) => crate::app_kit::route(handle),
        #[cfg(target_os = "macos")]
        _ => Err(Error::NotAppKit),
        #[cfg(not(target_os = "macos"))]
        _ => Ok(()),
    }
}

/// Why Quit could not be pointed at the window.
#[derive(Debug, PartialEq, Eq, thiserror::Error)]
pub enum Error {
    /// A window on macOS that isn't AppKit's.
    #[error("the window is not an AppKit window")]
    NotAppKit,
    /// AppKit's menus are only for the main thread.
    #[error("the menu can only be changed on the main thread")]
    NotMainThread,
    /// The handle's view is not in a window.
    #[error("the view is not in a window")]
    NoWindow,
    /// No menu item ends the app: there is none, or each has been pointed away already.
    #[error("the app menu has no Quit item")]
    NoQuit,
}

#[cfg(test)]
mod tests {
    use std::num::NonZeroU32;

    use raw_window_handle::XcbWindowHandle;

    use super::*;

    #[test]
    fn only_appkit_windows_have_a_quit_to_point_elsewhere() {
        let window = RawWindowHandle::Xcb(XcbWindowHandle::new(NonZeroU32::MIN));

        let routed = route(window);

        if cfg!(target_os = "macos") {
            assert_eq!(routed, Err(Error::NotAppKit));
        } else {
            assert_eq!(routed, Ok(()));
        }
    }
}
