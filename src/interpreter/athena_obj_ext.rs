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

    use super::*;
    use rustpython_vm::PyResult;

    #[pyfunction(name = "pathLibUpdated")]
    pub(crate) fn path_lib_updated(path_lib: Vec<String>) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::PathLibUpdated(path_lib))
            .expect("cannot send message via channel");

        Ok(())
    }

    #[pyfunction(name = "textureLibUpdated")]
    pub(crate) fn texture_lib_updated(texture_lib: Vec<String>) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::TextureLibUpdated(texture_lib))
            .expect("cannot send message via channel");

        Ok(())
    }

    #[pyfunction(name = "activePathSet")]
    pub(crate) fn active_path_set(path: String) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::ActivePathSet(path))
            .expect("cannot send message via channel");

        Ok(())
    }

    #[pyfunction(name = "activeTextureSet")]
    pub(crate) fn active_texture_set(path: String) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::ActiveTextureSet(path))
            .expect("cannot send message via channel");

        Ok(())
    }
}
