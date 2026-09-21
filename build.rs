#![allow(missing_docs, reason = "We don't need module docs in the build script")]
#![allow(clippy::indexing_slicing, reason = "Panics during build are fine")]
#![allow(clippy::expect_used, reason = "Panics during build are fine")]

use std::{
    env, fs, io,
    path::{Path, PathBuf},
    process::Command,
};

fn main() {
    link_resources();
    link_manual();
    // recompile in case the puthon code has changed
    println!("cargo:rerun-if-changed=pysrc");
    // rerun-if-changed doesn't support globs, so tests/*.py are listed one by one
    for entry in fs::read_dir("tests").into_iter().flatten().flatten() {
        let path = entry.path();
        if path.extension() == Some("py".as_ref()) {
            println!("cargo:rerun-if-changed={}", path.display());
        }
    }
}

/// Links the manual next to the executable, where the app reads it as it does in a bundle.
///
/// The manual stays where the repository keeps it, in `doc/src`, which the published book is built
/// from too; only the link is beside the executable.
fn link_manual() {
    let manual = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("Expected during build"))
        .join("doc")
        .join("src");
    let Some(link) = exe_dir().map(|dir| dir.join("manual")) else {
        println!("cargo:warning=cannot find the executable directory, the manual is not linked");
        return;
    };
    if let Err(err) = symlink_dir(&manual, &link) {
        println!(
            "cargo:warning=failed to link {} to {}: {err}",
            link.display(),
            manual.display()
        );
        return;
    }
    // re-run when the link is removed or broken, watched through a page as `resources` is through
    // its files; the pages themselves are read when the app runs, so editing one needs no rebuild
    println!(
        "cargo:rerun-if-changed={}",
        link.join("SUMMARY.md").display()
    );
}

/// Links `resources` next to the executable, where the app looks for the soundfont.
fn link_resources() {
    let resources =
        PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("Expected during build"))
            .join("resources");
    let Some(link) = exe_dir().map(|dir| dir.join("resources")) else {
        println!("cargo:warning=cannot find the executable directory, resources are not linked");
        return;
    };
    if let Err(err) = symlink_dir(&resources, &link) {
        println!(
            "cargo:warning=failed to link {} to {}: {err}",
            link.display(),
            resources.display()
        );
        return;
    }
    // re-run when the link is removed or broken; the files are watched through the link rather than
    // the link itself, because cargo also compares the link's own mtime, which is newer than the
    // start of the build that created it
    for entry in fs::read_dir(&resources).into_iter().flatten().flatten() {
        let name = entry.file_name();
        let is_file = entry.file_type().is_ok_and(|file_type| file_type.is_file());
        // hidden files like .DS_Store are modified by the system
        if is_file && !name.to_string_lossy().starts_with('.') {
            println!("cargo:rerun-if-changed={}", link.join(name).display());
        }
    }
}

/// Directory where cargo places the executable.
fn exe_dir() -> Option<PathBuf> {
    // OUT_DIR is <build dir>/<profile dir>/build/<package>-<hash>/out and the executable is placed
    // into <target dir>/<profile dir>, where <profile dir> is [<target triple>/]<profile>
    let out_dir = PathBuf::from(env::var_os("OUT_DIR")?);
    let build = out_dir.ancestors().nth(2)?;
    if build.file_name() != Some("build".as_ref()) {
        return None;
    }
    let dir = build.parent()?;
    if let Some((target_dir, build_dir)) = target_and_build_dirs() {
        if let Ok(profile_dir) = dir.strip_prefix(build_dir) {
            return Some(target_dir.join(profile_dir));
        }
    }
    // the build dir is somewhere else when --target-dir is passed to cargo, since it isn't
    // visible to `cargo metadata`, and in that case it's also the target dir
    Some(dir.to_owned())
}

/// Target and build directories from the cargo configuration (they differ when `build.build-dir` is
/// set).
fn target_and_build_dirs() -> Option<(PathBuf, PathBuf)> {
    let output = Command::new(env::var_os("CARGO")?)
        .args(["metadata", "--format-version=1", "--no-deps", "--offline"])
        .output()
        .ok()?;
    let metadata: serde_json::Value = serde_json::from_slice(&output.stdout).ok()?;
    let target_dir = metadata["target_directory"].as_str()?;
    let build_dir = metadata["build_directory"].as_str().unwrap_or(target_dir);
    Some((target_dir.into(), build_dir.into()))
}

fn symlink_dir(original: &Path, link: &Path) -> io::Result<()> {
    if let Ok(metadata) = fs::symlink_metadata(link) {
        if !metadata.file_type().is_symlink() {
            return Err(io::Error::new(
                io::ErrorKind::AlreadyExists,
                "it already exists and is not a symlink",
            ));
        }
        if fs::read_link(link)? == original {
            return Ok(());
        }
        // a stale or broken link (e.g. a self-referencing one created by older versions);
        // directory links are removed with remove_dir on Windows
        fs::remove_file(link).or_else(|_| fs::remove_dir(link))?;
    }
    #[cfg(target_family = "unix")]
    {
        std::os::unix::fs::symlink(original, link)
    }
    #[cfg(target_family = "windows")]
    {
        std::os::windows::fs::symlink_dir(original, link)
    }
}
