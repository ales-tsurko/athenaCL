//! Preference isolation shared by library unit tests and integration test binaries.

use std::{path::PathBuf, sync::LazyLock};

/// Point athenaCL's preferences and log at a fresh directory for this test process.
///
/// Each process keeps one directory for its interpreters. The random name prevents a later run from
/// reading a partial preferences file left by a process whose ID has been reused.
pub fn init_scratch_prefs() {
    static PREFS_DIR: LazyLock<PathBuf> = LazyLock::new(|| {
        let parent = std::env::temp_dir().join("athenacl-tests");
        std::fs::create_dir_all(&parent)
            .expect("the scratch preferences parent directory should be created");
        tempfile::Builder::new()
            .prefix("prefs-")
            .tempdir_in(parent)
            .expect("the scratch preferences directory should be created")
            .keep()
    });
    std::env::set_var("ATHENACL_PREFS_DIR", PREFS_DIR.as_os_str());
}
