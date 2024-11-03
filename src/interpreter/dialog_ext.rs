//! Extensions to the athenacl's dialog module.
//!
//! The dialog module is responsible for communication between the user and athena interpreter.
//! Also, it implements communication between athena interpreter and GUI by sending messages to the
//! [`InterpreterWorker`](crate::interpreter::InterpreterWorker).

use rfd::FileDialog;
use rustpython_vm::{pymodule, VirtualMachine};

use crate::interpreter;

pub(crate) fn make_module(vm: &mut VirtualMachine) {
    vm.add_native_module("dialogExt", Box::new(_inner::make_module));
}

#[pymodule]
pub(super) mod _inner {
    use std::env;
    use std::str;

    use super::*;
    use rustpython_vm::{convert::ToPyObject, PyResult};

    #[pyfunction(name = "promptChooseDir")]
    pub(crate) fn prompt_choose_dir(
        title: String,
        initial_dir: String,
        vm: &VirtualMachine,
    ) -> PyResult {
        prompt_dialog(title, initial_dir, PromptType::ChooseDir, vm)
    }

    #[pyfunction(name = "promptChooseFile")]
    pub(crate) fn prompt_choose_file(
        title: String,
        initial_dir: String,
        vm: &VirtualMachine,
    ) -> PyResult {
        prompt_dialog(title, initial_dir, PromptType::ChooseFile, vm)
    }

    #[pyfunction(name = "promptSaveFile")]
    pub(crate) fn prompt_save_file(
        title: String,
        initial_dir: String,
        vm: &VirtualMachine,
    ) -> PyResult {
        prompt_dialog(title, initial_dir, PromptType::SaveFile, vm)
    }

    fn prompt_dialog(
        title: String,
        initial_dir: String,
        prompt_type: PromptType,
        vm: &VirtualMachine,
    ) -> PyResult {
        let initial_dir = if initial_dir.is_empty() {
            match env::current_dir() {
                Ok(path) => path.to_string_lossy().to_string(),
                Err(e) => {
                    eprint!("{}", e);
                    let res = vec![
                        vm.ctx.new_str("").to_pyobject(vm),
                        vm.ctx.new_int(0).to_pyobject(vm),
                    ];
                    return Ok(vm.ctx.new_tuple(res).into());
                }
            }
        } else {
            initial_dir
        };

        let title = if title.is_empty() {
            "Select directory".to_string()
        } else {
            title
        };

        let fd = FileDialog::new()
            .set_title(title)
            .set_directory(initial_dir)
            .set_can_create_directories(true);

        let res = match prompt_type {
            PromptType::ChooseDir => fd.pick_folder(),
            PromptType::ChooseFile => fd.pick_file(),
            PromptType::SaveFile => fd.save_file(),
        };

        let res = match res {
            Some(path) => vec![
                vm.ctx
                    .new_str(path.to_string_lossy().to_string())
                    .to_pyobject(vm),
                vm.ctx.new_int(1).to_pyobject(vm),
            ],
            None => vec![
                vm.ctx.new_str("").to_pyobject(vm),
                vm.ctx.new_int(0).to_pyobject(vm),
            ],
        };

        Ok(vm.ctx.new_tuple(res).into())
    }

    #[derive(Clone, Copy)]
    enum PromptType {
        ChooseDir,
        ChooseFile,
        SaveFile,
    }

    #[pyfunction(name = "postOut")]
    pub(crate) fn post_out(output: String) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Post(output))
            .expect("cannot send message via channel");
        Ok(())
    }

    #[pyfunction(name = "askInput")]
    pub(crate) fn ask_input(prompt: String, vm: &VirtualMachine) -> PyResult {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Ask(prompt))
            .expect("cannot send message via channel");

        if let Ok(msg) = interpreter::INTERPRETER_WORKER
            .response_receiver
            .recv_blocking()
        {
            return Ok(vm.ctx.new_str(msg).into());
        }

        Ok(vm.ctx.new_str("").into())
    }

    #[pyfunction(name = "playMidi")]
    pub(crate) fn play_midi(path: String) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::LoadMidi(path))
            .expect("cannot send message via channel");

        Ok(())
    }

    #[pyfunction(name = "playAudio")]
    pub(crate) fn play_audio(path: String) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::LoadAudio(path))
            .expect("cannot send message via channel");

        Ok(())
    }
}
