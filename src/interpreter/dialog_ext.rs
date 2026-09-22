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
    use crate::interpreter::Question;

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

    /// Ask where to save a file, starting in `initial_dir` with `file_name` filled in.
    #[pyfunction(name = "promptSaveFile")]
    pub(crate) fn prompt_save_file(
        title: String,
        initial_dir: String,
        file_name: String,
        vm: &VirtualMachine,
    ) -> PyResult {
        prompt_dialog(title, initial_dir, PromptType::SaveFile(file_name), vm)
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

    enum PromptType {
        ChooseDir,
        ChooseFile,
        /// Saving, under a name to start with.
        SaveFile(String),
    }

    impl PromptType {
        /// Pick with `dialog` however this prompt asks.
        fn pick(self, dialog: FileDialog) -> Option<PathBuf> {
            match self {
                PromptType::ChooseDir => dialog.pick_folder(),
                PromptType::ChooseFile => dialog.pick_file(),
                PromptType::SaveFile(name) => dialog.set_file_name(name).save_file(),
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
        let answer = ask(prompt, Question::Text, vm)?;
        Ok(vm.ctx.new_str(answer).into())
    }

    /// Ask for a yes or a no, and return 1 or 0.
    #[pyfunction(name = "askYesNo")]
    pub(crate) fn ask_yes_no(prompt: String, default: bool, vm: &VirtualMachine) -> PyResult {
        let answer = ask(prompt, Question::YesNo { default }, vm)?;
        Ok(vm.ctx.new_int(i32::from(yes(&answer, default))).into())
    }

    /// Ask for a yes, a no or a cancel, and return 1, 0 or -1.
    #[pyfunction(name = "askYesNoCancel")]
    pub(crate) fn ask_yes_no_cancel(
        prompt: String,
        default: bool,
        vm: &VirtualMachine,
    ) -> PyResult {
        let answer = ask(prompt, Question::YesNoCancel { default }, vm)?;
        let status = if is_cancel(&answer) {
            -1
        } else {
            i32::from(yes(&answer, default))
        };
        Ok(vm.ctx.new_int(status).into())
    }

    /// Put `question` to the user and wait for the answer.
    fn ask(prompt: String, question: Question, vm: &VirtualMachine) -> PyResult<String> {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Ask { prompt, question })
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;

        Ok(interpreter::INTERPRETER_WORKER
            .response_receiver
            .recv_blocking()
            .unwrap_or_default())
    }

    /// Whether an answer means yes: an empty one is the default, as is anything unrecognized,
    /// since the gui only ever sends one of the answers the question offered.
    fn yes(answer: &str, default: bool) -> bool {
        match answer.trim().to_lowercase().as_str() {
            "y" | "yes" | "1" | "on" | "true" => true,
            "n" | "no" | "0" | "off" | "false" => false,
            _ => default,
        }
    }

    fn is_cancel(answer: &str) -> bool {
        matches!(answer.trim().to_lowercase().as_str(), "cancel" | "c" | "-1")
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
