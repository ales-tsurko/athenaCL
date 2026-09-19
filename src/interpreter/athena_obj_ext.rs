//! Extensions to the athenacl's dialog module.
//!
//! The dialog module is responsible for communication between the user and athena interpreter.
//! Also, it implements communication between athena interpreter and GUI by sending messages to the
//! [`InterpreterWorker`](crate::interpreter::InterpreterWorker).

use rustpython_vm::{pymodule, VirtualMachine};

use crate::interpreter;

pub(crate) fn make_module(vm: &mut VirtualMachine) {
    vm.add_native_module("athenaObjExt", Box::new(_inner::make_module));
}

#[pymodule]
pub(super) mod _inner {
    use std::str;

    use rustpython_vm::PyResult;

    use super::*;

    #[pyfunction(name = "pathLibUpdated")]
    pub(crate) fn path_lib_updated(path_lib: Vec<String>, vm: &VirtualMachine) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::PathLibUpdated(path_lib))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(())
    }

    #[pyfunction(name = "textureLibUpdated")]
    pub(crate) fn texture_lib_updated(
        texture_lib: Vec<String>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::TextureLibUpdated(texture_lib))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(())
    }

    #[pyfunction(name = "activePathSet")]
    pub(crate) fn active_path_set(path: String, vm: &VirtualMachine) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::ActivePathSet(path))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(())
    }

    #[pyfunction(name = "activeTextureSet")]
    pub(crate) fn active_texture_set(path: String, vm: &VirtualMachine) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::ActiveTextureSet(path))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(())
    }
}
