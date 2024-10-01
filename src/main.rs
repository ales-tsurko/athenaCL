//! The executable.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")] // hide console window on Windows in release

use athenacl::app;
// use rustpython_vm as vm;

fn main() -> iced::Result {
    iced::application("athenaCL", app::update, app::view)
        .antialiasing(true)
        .centered()
        .settings(iced::settings::Settings {
            id: Some(app::APPLICATION_ID.to_string()),
            default_text_size: 14.into(),
            ..Default::default()
        })
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
