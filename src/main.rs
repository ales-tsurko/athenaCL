//! The executable.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")] // hide console window on Windows in release

use athenacl;
use iced::Sandbox;
use rustpython_vm as vm;

fn main() -> iced::Result {
    athenacl::App::run(athenacl::App::settings())
}

// fn main() -> vm::PyResult<()> {
//     let interpreter = athenacl::init_py_interpreter();
//     interpreter.enter(|vm| {
//         let _ = vm.import("athenaCL.athenacl", None, 0)?;
//         vm::PyResult::Ok(())
//     })
// }
