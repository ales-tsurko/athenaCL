#![allow(missing_docs)]
use std::path::PathBuf;

fn main() {
    if cfg!(debug_assertions) {
        symlink("resources", "target/debug/resources");
    } else {
        symlink("resources", "target/release/resources");
    }
    // recompile in case the puthon code has changed
    println!("cargo:rerun-if-changed=pysrc");
    println!("cargo:rerun-if-changed=tests/*.py");
}

fn symlink(original: &str, link: &str) {
    let path = PathBuf::from(link);
    if !path.is_symlink() && !path.exists() {
        #[cfg(target_family = "unix")]
        {
            std::os::unix::fs::symlink(original, link).unwrap();
        }
        #[cfg(target_family = "windows")]
        {
            std::os::windows::fs::symlink_dir(original, link).unwrap();
        }
    }
}
