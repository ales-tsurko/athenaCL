//! The app menu's Quit, pointed at a window through AppKit.

use objc2::{rc::Retained, runtime::AnyObject, sel, MainThreadMarker};
use objc2_app_kit::{NSApplication, NSMenuItem, NSView, NSWindow};
use raw_window_handle::AppKitWindowHandle;

use crate::Error;

/// Point the app menu's Quit at the close button of the window `handle`'s view is in.
pub(crate) fn route(handle: AppKitWindowHandle) -> Result<(), Error> {
    let mtm = MainThreadMarker::new().ok_or(Error::NotMainThread)?;
    let window = window_of(handle, mtm)?;
    let items = quit_items(&NSApplication::sharedApplication(mtm));
    if items.is_empty() {
        return Err(Error::NoQuit);
    }
    for item in &items {
        close_on(item, &window);
    }
    Ok(())
}

/// The window `handle`'s view is in.
fn window_of(
    handle: AppKitWindowHandle,
    _mtm: MainThreadMarker,
) -> Result<Retained<NSWindow>, Error> {
    // SAFETY: an AppKit handle's view is an NSView, which its window keeps alive while iced runs
    // the window's tasks, on the main thread, as the marker shows this is
    let view = unsafe { Retained::retain(handle.ns_view.as_ptr().cast::<NSView>()) }
        .ok_or(Error::NoWindow)?;
    view.window().ok_or(Error::NoWindow)
}

/// The menu items that end the app: Quit, and Quit and Keep Windows, which macOS adds to a bundled
/// app's menu for Option-Cmd-Q.
fn quit_items(app: &NSApplication) -> Vec<Retained<NSMenuItem>> {
    let Some(menu) = app.mainMenu() else {
        return Vec::new();
    };
    menu.itemArray()
        .to_vec()
        .into_iter()
        .filter_map(|menu| menu.submenu())
        .flat_map(|menu| menu.itemArray().to_vec())
        .filter(|item| item.action() == Some(sel!(terminate:)))
        .collect()
}

/// Make `item` close `window`, as the window's close button does.
fn close_on(item: &NSMenuItem, window: &NSWindow) {
    let target: &AnyObject = window;
    // SAFETY: the item holds its target weakly, so it never points at a window that has gone
    unsafe { item.setTarget(Some(target)) };
    // SAFETY: every window responds to performClose:, which takes the sender, as actions do
    unsafe { item.setAction(Some(sel!(performClose:))) };
}

#[cfg(test)]
mod tests {
    use std::ptr::NonNull;

    use super::*;

    #[test]
    fn app_kit_is_only_changed_on_the_main_thread() {
        // a thread of its own is never the main one, so the handle, which points nowhere, is
        // never followed
        let routed = std::thread::spawn(|| route(AppKitWindowHandle::new(NonNull::dangling())))
            .join()
            .expect("the thread ends");

        assert_eq!(routed, Err(Error::NotMainThread));
    }
}
