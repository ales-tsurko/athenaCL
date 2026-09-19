//! Extensions to the athenacl's dialog module.
//!
//! The dialog module is responsible for communication between the user and athena interpreter.
//! Also, it implements communication between athena interpreter and GUI by sending messages to the
//! [`InterpreterWorker`](crate::interpreter::InterpreterWorker).

use rfd::FileDialog;
use rustpython_vm::{pymodule, VirtualMachine};

use crate::interpreter;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "dialogExt")]
pub(super) mod _inner {
    use std::{env, path::PathBuf, str};

    use rustpython_vm::{convert::ToPyObject, PyResult};

    use super::*;

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
        let Some(initial_dir) = initial_directory(initial_dir) else {
            return cancelled(vm);
        };
        let title = if title.is_empty() {
            "Select directory".to_string()
        } else {
            title
        };

        let dialog = FileDialog::new()
            .set_title(title)
            .set_directory(initial_dir)
            .set_can_create_directories(true);

        response(prompt_type.pick(dialog), vm)
    }

    #[derive(Clone, Copy)]
    enum PromptType {
        ChooseDir,
        ChooseFile,
        SaveFile,
    }

    impl PromptType {
        /// Pick with `dialog` however this prompt asks.
        fn pick(self, dialog: FileDialog) -> Option<PathBuf> {
            match self {
                PromptType::ChooseDir => dialog.pick_folder(),
                PromptType::ChooseFile => dialog.pick_file(),
                PromptType::SaveFile => dialog.save_file(),
            }
        }
    }

    /// The directory a dialog opens in: the given one, or the working directory.
    pub(super) fn initial_directory(initial_dir: String) -> Option<String> {
        if !initial_dir.is_empty() {
            return Some(initial_dir);
        }

        env::current_dir()
            .map(|path| path.to_string_lossy().to_string())
            .map_err(|err| eprint!("{err}"))
            .ok()
    }

    /// The athenaCL dialog result: the chosen path, or an empty one with a zero.
    pub(super) fn response(picked: Option<PathBuf>, vm: &VirtualMachine) -> PyResult {
        let (path, ok) = match picked {
            Some(path) => (path.to_string_lossy().to_string(), 1),
            None => (String::new(), 0),
        };

        Ok(vm
            .ctx
            .new_tuple(vec![
                vm.ctx.new_str(path).to_pyobject(vm),
                vm.ctx.new_int(ok).to_pyobject(vm),
            ])
            .into())
    }

    /// A dialog result for when it cannot even be shown.
    fn cancelled(vm: &VirtualMachine) -> PyResult {
        response(None, vm)
    }

    #[pyfunction(name = "postOut")]
    pub(crate) fn post_out(output: String, vm: &VirtualMachine) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Post(output))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;
        Ok(())
    }

    #[pyfunction(name = "askInput")]
    pub(crate) fn ask_input(prompt: String, vm: &VirtualMachine) -> PyResult {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Ask(prompt))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        if let Ok(msg) = interpreter::INTERPRETER_WORKER
            .response_receiver
            .recv_blocking()
        {
            return Ok(vm.ctx.new_str(msg).into());
        }

        Ok(vm.ctx.new_str("").into())
    }

    #[pyfunction(name = "playMidi")]
    pub(crate) fn play_midi(path: String, vm: &VirtualMachine) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::LoadMidi(path))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(())
    }

    #[pyfunction(name = "playAudio")]
    pub(crate) fn play_audio(path: String, vm: &VirtualMachine) -> PyResult<()> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::LoadAudio(path))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use rustpython_vm::builtins::{PyInt, PyStr, PyTuple};

    use super::_inner::{initial_directory, response};

    #[test]
    fn the_working_directory_is_the_default_start() {
        assert_eq!(
            initial_directory("given".to_owned()).as_deref(),
            Some("given")
        );
        let cwd = initial_directory(String::new()).expect("the working directory is available");
        assert!(!cwd.is_empty());
    }

    #[test]
    fn responses_carry_the_path_and_flag() {
        let interpreter = crate::init_py_interpreter();
        interpreter.enter(|vm| {
            let picked = response(Some("/tmp/x".into()), vm).expect("a picked path builds");
            assert_eq!(tuple_fields(&picked), ("/tmp/x".to_owned(), 1));

            let cancelled = response(None, vm).expect("a cancelled dialog builds");
            assert_eq!(tuple_fields(&cancelled), (String::new(), 0));
        });
    }

    /// The `(path, ok)` fields of a dialog result.
    fn tuple_fields(result: &rustpython_vm::PyObject) -> (String, i64) {
        let tuple = result
            .downcast_ref::<PyTuple>()
            .expect("the result is a tuple");
        let path = tuple.as_slice()[0]
            .downcast_ref::<PyStr>()
            .expect("the first field is a string")
            .to_str()
            .unwrap_or_default()
            .to_owned();
        let ok = tuple.as_slice()[1]
            .downcast_ref::<PyInt>()
            .expect("the second field is a number")
            .as_bigint()
            .to_string()
            .parse()
            .expect("the flag is a small number");

        (path, ok)
    }
}
