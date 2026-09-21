//! What the headless renderer draws, as pixels to look at.

use std::sync::atomic::{AtomicUsize, Ordering};

/// The pixels of `snapshot`.
///
/// A snapshot hands its pixels over only as a file, named after the renderer that drew them, so
/// each is written into a directory of its own and read back from there.
pub(crate) fn pixels(snapshot: &iced_test::simulator::Snapshot) -> image::RgbaImage {
    static TAKEN: AtomicUsize = AtomicUsize::new(0);
    let dir = std::env::temp_dir()
        .join("athenacl-tests")
        .join(std::process::id().to_string())
        .join(format!(
            "snapshot-{}",
            TAKEN.fetch_add(1, Ordering::Relaxed)
        ));
    if dir.exists() {
        std::fs::remove_dir_all(&dir).expect("an old snapshot is removed");
    }
    std::fs::create_dir_all(&dir).expect("the snapshot's directory is made");
    assert!(snapshot
        .matches_image(dir.join("snapshot.png"))
        .expect("the snapshot is written"));
    let file = std::fs::read_dir(&dir)
        .expect("the snapshot's directory reads")
        .flatten()
        .next()
        .expect("the snapshot is there")
        .path();
    let pixels = image::open(file)
        .expect("the snapshot reads back")
        .to_rgba8();
    std::fs::remove_dir_all(&dir).expect("the snapshot's directory is removed");
    pixels
}
