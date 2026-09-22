//! Extensions to the athenacl's dialog module.
//!
//! The dialog module is responsible for communication between the user and athena interpreter.
//! Also, it implements communication between athena interpreter and GUI by sending messages to the
//! [`InterpreterWorker`](crate::interpreter::InterpreterWorker).

use rustpython_vm::{pymodule, VirtualMachine};

use crate::interpreter;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaObjExt")]
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

    /// Close the GUI: quitting is settled, and whatever was to be saved has been.
    #[pyfunction(name = "quit")]
    pub(crate) fn quit(vm: &VirtualMachine) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Quit)
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(())
    }
}
