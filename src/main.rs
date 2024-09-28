//! The executable.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")] // hide console window on Windows in release

use athenacl;
// use rustpython_vm as vm;

fn main() -> iced::Result {
    iced::application("athenacl", athenacl::app::update, athenacl::app::view)
        .antialiasing(true)
        .centered()
        .window(iced::window::Settings {
            min_size: Some((800.0, 600.0).into()),
            ..Default::default()
        })
        .run()
}

// fn main() -> vm::PyResult<()> {
//     let interpreter = athenacl::init_py_interpreter();
//     interpreter.enter(|vm| {
//         let _ = vm.import("athenaCL.athenacl", 0)?;
//         vm::PyResult::Ok(())
//     })
// }
