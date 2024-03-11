#![allow(missing_docs)]

// it doesn't use any codegen or build system here, it's just to recompile the project in case some
// python code changed

fn main() {
    println!("cargo:rerun-if-changed=pysrc");
    println!("cargo:rerun-if-changed=tests/*.py");
}
