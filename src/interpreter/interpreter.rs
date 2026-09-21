//! athenaCL interpreter.

use std::{
    sync::{Arc, LazyLock},
    thread,
};

use async_channel::{unbounded, Receiver, Sender};
use rustpython_vm as vm;
use thiserror::Error;
use vm::{
    builtins::{PyBaseExceptionRef, PyInt, PyStr, PyTuple},
    Interpreter as PyInterpreter, PyObjectRef, PyResult, VirtualMachine,
};

use super::{athena_obj_ext, dialog_ext, figure_ext, manual_ext, sndhdr, xml_tools_ext};
use crate::figure::Figure;

/// Global interpreter representation.
pub static INTERPRETER_WORKER: LazyLock<InterpreterWorker> = LazyLock::new(InterpreterWorker::run);
pub(crate) type InterpreterResult<T> = Result<T, Error>;

/// A worker which keeps the interpreter on a dedicated thread and provides communication with it
/// via channels.
#[derive(Debug)]
pub struct InterpreterWorker {
    pub interp_sender: Sender<Message>,
    pub gui_sender: Sender<Message>,
    pub gui_receiver: Receiver<Message>,
    /// Response sender/receiver is a special channel dedicated for sending user's answer to
    /// `Message::Ask`.
    pub response_sender: Sender<String>,
    /// Response sender/receiver is a special channel dedicated for sending user's answer to
    /// `Message::Ask`.
    pub response_receiver: Receiver<String>,
}

impl InterpreterWorker {
    /// Run the interpereter loop.
    fn run() -> Self {
        // the tests keep out of the user's preferences; set before the thread reads the environment
        #[cfg(test)]
        init_scratch_prefs();

        let (interp_sender, r) = unbounded::<Message>();
        let (gui_sender, gui_receiver) = unbounded::<Message>();
        let s = gui_sender.clone();

        let _ = thread::spawn(move || {
            #[expect(
                clippy::panic,
                reason = "the app cannot proceed without the interpreter"
            )]
            let interpreter = Interpreter::new().unwrap_or_else(|err| {
                s.send_blocking(Message::PythonError(err.to_string()))
                    .expect("can't send message to channel");
                panic!("error initializating interpreter");
            });

            loop {
                if let Ok(message) = r.recv_blocking() {
                    let msg = match message {
                        Message::SendCmd(cmd) => interpreter.run_cmd(&cmd).map(Message::Post),
                        Message::GetScratchDir => interpreter
                            .pref("athena", "fpScratchDir")
                            .map(Message::ScratchDir),
                        Message::GetAppearance => interpreter
                            .pref("gui", "appearance")
                            .map(Message::Appearance),
                        Message::GetCompletions => {
                            interpreter.command_completions().map(Message::Completions)
                        }
                        // saving needs no reply, unless it fails
                        Message::SetAppearance(appearance) => {
                            match interpreter.write_pref("gui", "appearance", &appearance) {
                                Ok(()) => continue,
                                Err(err) => Err(err),
                            }
                        }
                        _ => continue,
                    }
                    .into();

                    s.send_blocking(msg).expect("cannot send message to gui");
                }
            }
        });

        let (response_sender, response_receiver) = unbounded();

        Self {
            interp_sender,
            gui_sender,
            gui_receiver,
            response_sender,
            response_receiver,
        }
    }
}

#[derive(Debug, Clone)]
pub enum Message {
    /// Output from the interpreter (stdout).
    Post(String),
    /// Request input from the user (stdin).
    Ask {
        prompt: String,
        question: Question,
    },
    /// Send command to the interpreter.
    SendCmd(String),
    /// Error from the interpreter (stderr).
    Error(String),
    /// Python's interpreter- level errors.
    PythonError(String),
    /// Play a MIDI file (in the output area).
    ///
    /// The value is the path to the file.
    LoadMidi(String),
    /// Play an Audio file (in the output area).
    ///
    /// The value is the path to the file.
    LoadAudio(String),
    /// Show a figure (in the output area).
    Figure(Arc<Figure>),
    /// Show a page of the manual (in the output area).
    Manual(crate::manual::Request),
    /// Get scratch dir.
    GetScratchDir,
    /// The result of `Self::GetScratchDir`.
    ScratchDir(String),
    /// Get the GUI's saved look: `light` or `dark`.
    GetAppearance,
    /// The result of `Self::GetAppearance`.
    Appearance(String),
    /// Save the GUI's look.
    SetAppearance(String),
    /// Request the command catalog once, without running a user command.
    GetCompletions,
    /// Names and descriptions from athenaCL's command registry.
    Completions(Vec<CommandCompletion>),
    PathLibUpdated(Vec<String>),
    TextureLibUpdated(Vec<String>),
    // Not system file path, but athenaCL pitch path
    ActivePathSet(String),
    ActiveTextureSet(String),
}

/// A command offered by the interpreter's own registry.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandCompletion {
    /// Canonical command spelling, accepted regardless of ASCII case.
    pub name: String,
    /// A short description from the existing command documentation.
    pub description: String,
}

/// What kind of answer a question wants, so that the gui can offer it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Question {
    /// Anything typed.
    Text,
    /// Yes or no, and which of them the user gets by answering nothing.
    YesNo { default: bool },
    /// Yes, no or cancel, and which of the first two answering nothing gives.
    YesNoCancel { default: bool },
}

impl Question {
    /// The answers it offers, in the order they are shown; none, when it takes any text.
    pub fn answers(self) -> &'static [&'static str] {
        match self {
            Self::Text => &[],
            Self::YesNo { .. } => &["YES", "NO"],
            Self::YesNoCancel { .. } => &["YES", "NO", "CANCEL"],
        }
    }
}

impl From<Error> for Message {
    fn from(value: Error) -> Self {
        match value {
            Error::Command(_, cmd_err) => Message::Error(cmd_err),
            Error::PythonError(err) => Message::PythonError(err),
        }
    }
}

impl From<InterpreterResult<Message>> for Message {
    fn from(value: InterpreterResult<Message>) -> Self {
        match value {
            Ok(msg) => msg,
            Err(e) => Self::from(e),
        }
    }
}

struct Interpreter {
    py_interpreter: PyInterpreter,
    ath_interpreter: PyObjectRef,
    ath_object: PyObjectRef,
}

impl Interpreter {
    fn new() -> InterpreterResult<Self> {
        let py_interpreter = init_py_interpreter();
        let (ath_interpreter, ath_object) = Self::init_ath_interpreter(&py_interpreter)?;
        Ok(Self {
            py_interpreter: init_py_interpreter(),
            ath_interpreter,
            ath_object,
        })
    }

    fn init_ath_interpreter(
        interpreter: &PyInterpreter,
    ) -> InterpreterResult<(PyObjectRef, PyObjectRef)> {
        interpreter.enter(|vm| -> InterpreterResult<(PyObjectRef, PyObjectRef)> {
            let scope = vm.new_scope_with_builtins();
            let import = vm::py_compile!(source = "from athenaCL.libATH import athenaObj");
            let _ = vm
                .run_code_obj(vm.ctx.new_code(import), scope.clone())
                .try_py()?;

            // the version athenaCL reports is the package's, so that it is written down once;
            // the one in athenaObj.py only stands in when the python runs on its own
            scope
                .globals
                .get_item("athenaObj", vm)
                .try_py()?
                .set_attr("athVersion", vm.ctx.new_str(env!("CARGO_PKG_VERSION")), vm)
                .try_py()?;

            let module = vm::py_compile!(
                source = r#"interp = athenaObj.Interpreter()
interp"#
            );
            let _ = vm
                .run_code_obj(vm.ctx.new_code(module), scope.clone())
                .try_py()?;
            let interp = scope.globals.get_item("interp", vm).try_py()?;
            let ath_object = interp.get_attr("ao", vm).try_py()?;

            Ok((interp, ath_object))
        })
    }

    fn run_cmd(&self, cmd: &str) -> InterpreterResult<String> {
        self.py_interpreter.enter(|vm| -> _ {
            let result = vm
                .call_method(&self.ath_interpreter, "cmd", (cmd.to_string(),))
                .try_py()?;
            let (is_ok, msg) = extract_result_tuple(vm, result).try_py()?;

            if is_ok {
                Ok(msg)
            } else {
                Err(Error::Command(cmd.to_owned(), msg))
            }
        })
    }

    fn command_completions(&self) -> InterpreterResult<Vec<CommandCompletion>> {
        self.py_interpreter.enter(|vm| {
            let result = vm
                .call_method(&self.ath_object, "commandCompletions", ())
                .try_py()?;
            vm.extract_elements_with(&result, |entry| {
                let tuple = entry
                    .downcast_ref::<PyTuple>()
                    .ok_or_else(|| vm.new_type_error("Expected a command tuple".to_owned()))?;
                let [name, description] = tuple.as_slice() else {
                    return Err(vm.new_value_error("Expected name and description".to_owned()));
                };
                Ok(CommandCompletion {
                    name: extract_string(vm, name.clone())?,
                    description: extract_string(vm, description.clone())?,
                })
            })
            .try_py()
        })
    }

    /// A preference, from athenaCL's preferences file.
    fn pref(&self, category: &str, key: &str) -> InterpreterResult<String> {
        self.py_interpreter.enter(|vm| -> _ {
            let external = self.external(vm)?;
            let result = vm
                .call_method(&external, "getPref", (category.to_owned(), key.to_owned()))
                .try_py()?;

            extract_string(vm, result).try_py()
        })
    }

    /// Save a preference to athenaCL's preferences file.
    fn write_pref(&self, category: &str, key: &str, value: &str) -> InterpreterResult<()> {
        self.py_interpreter.enter(|vm| -> _ {
            let external = self.external(vm)?;
            let _ = vm
                .call_method(
                    &external,
                    "writePref",
                    (category.to_owned(), key.to_owned(), value.to_owned()),
                )
                .try_py()?;

            Ok(())
        })
    }

    /// The athenaCL object's `external`, which keeps the preferences.
    fn external(&self, vm: &VirtualMachine) -> InterpreterResult<PyObjectRef> {
        let external = vm
            .get_attribute_opt(self.ath_object.clone(), "external")
            .try_py()?
            .expect("external attribute is always available on AthenaObject");

        Ok(external)
    }
}

/// Point athenaCL's preferences and log at a directory of this process' own.
///
/// athenaCL keeps one preference file for every instance, in the home directory, and rewrites it as
/// it runs. The tests call this before starting an interpreter, so that running them leaves the
/// preferences of whoever ran them alone, and so that test processes running at once never write
/// over each other's.
pub fn init_scratch_prefs() {
    // every test process gets its own, all under the one directory to sweep away
    let prefs = std::env::temp_dir()
        .join("athenacl-tests")
        .join(std::process::id().to_string());
    std::fs::create_dir_all(&prefs).expect("the scratch preferences directory should be created");
    std::env::set_var("ATHENACL_PREFS_DIR", prefs);
}

/// Initialize the python interpreter with precompiled stdlib and athenaCL (python modules).
pub fn init_py_interpreter() -> PyInterpreter {
    let mut settings = vm::Settings::default();
    settings.optimize = 2;
    let builder = PyInterpreter::builder(settings);
    let ctx = builder.ctx.clone();
    builder
        .add_native_modules(&rustpython_stdlib::stdlib_module_defs(&ctx))
        .add_native_module(xml_tools_ext::module_def(&ctx))
        .add_native_module(dialog_ext::module_def(&ctx))
        .add_native_module(athena_obj_ext::module_def(&ctx))
        .add_native_module(figure_ext::module_def(&ctx))
        .add_native_module(manual_ext::module_def(&ctx))
        .add_native_module(sndhdr::module_def(&ctx))
        .add_frozen_modules(rustpython_pylib::FROZEN_STDLIB)
        .add_frozen_modules(vm::py_freeze!(dir = "../../pysrc"))
        .build()
}

fn extract_result_tuple(vm: &VirtualMachine, result: PyObjectRef) -> PyResult<(bool, String)> {
    // Ensure the result is a tuple
    if let Some(tuple) = result.downcast_ref::<PyTuple>() {
        // Ensure the tuple has exactly 2 elements (Integer, String)
        if let [int_part, str_part] = tuple.as_slice() {
            // Extract and convert the first element to i32
            let int_part = int_part
                .downcast_ref::<PyInt>()
                .ok_or_else(|| vm.new_type_error("Expected an integer".to_owned()))?
                .as_bigint();

            let bool_part = *int_part != 0.into();

            // Extract and convert the second element to String
            let str_part = str_part
                .downcast_ref::<PyStr>()
                .map(|v| v.to_str().unwrap_or_default().to_owned())
                .unwrap_or_default();

            Ok((bool_part, str_part))
        } else {
            Err(vm.new_value_error("Expected a tuple of length 2".to_owned()))
        }
    } else {
        Err(vm.new_type_error("Expected a tuple".to_owned()))
    }
}

#[cfg(test)]
fn extract_vec_string(vm: &VirtualMachine, result: PyObjectRef) -> PyResult<Vec<String>> {
    result
        .downcast_ref::<vm::builtins::PyList>()
        .ok_or_else(|| vm.new_type_error("Expected a list".to_owned()))
        .map(|list| {
            list.borrow_vec()
                .iter()
                .map(|v| extract_string(vm, v.to_owned()))
                .collect::<PyResult<Vec<String>>>()
        })?
}

fn extract_string(vm: &VirtualMachine, result: PyObjectRef) -> PyResult<String> {
    result
        .downcast_ref::<PyStr>()
        .ok_or_else(|| vm.new_type_error("Expected a string".to_owned()))
        .map(ToString::to_string)
}

trait TryPy {
    type Output;

    fn try_py(self) -> InterpreterResult<Self::Output>;
}

impl<T> TryPy for PyResult<T> {
    type Output = T;

    fn try_py(self) -> InterpreterResult<T> {
        self.map_err(Error::from_py_err)
    }
}

#[derive(Debug, Error, Clone)]
pub enum Error {
    #[error("{0}")]
    PythonError(String),
    #[error("Error running command `{0}`: {1}")]
    Command(String, String),
}

impl Error {
    fn from_py_err(err: PyBaseExceptionRef) -> Self {
        let message = err
            .get_arg(0)
            .as_ref()
            .and_then(|arg| arg.downcast_ref::<PyStr>())
            .map(|s| s.to_str().unwrap_or_default().to_owned())
            .unwrap_or_else(|| "Unknown (silent) error".to_string());

        Self::PythonError(message)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn completions_come_from_the_live_command_registry_with_descriptions() {
        init_scratch_prefs();
        let interpreter = Interpreter::new().expect("interpreter");
        let commands = interpreter.command_completions().expect("command catalog");
        let names = interpreter.py_interpreter.enter(|vm| {
            let names = interpreter
                .ath_object
                .get_attr("cmdRef", vm)
                .expect("registry");
            extract_vec_string(vm, names).expect("command names")
        });
        assert_eq!(
            commands
                .iter()
                .map(|command| &command.name)
                .collect::<Vec<_>>(),
            names.iter().collect::<Vec<_>>()
        );
        assert!(commands
            .iter()
            .any(|command| command.name == "TIn" && command.description == "TextureInstance: new"));
        assert!(commands
            .iter()
            .any(|command| command.name == "help" && !command.description.is_empty()));
        assert!(
            commands.iter().any(|command| command.name == "PIals"),
            "documented hidden commands are available too"
        );
    }

    #[test]
    fn athenacl_reports_the_package_version() {
        init_scratch_prefs();
        let interpreter = init_py_interpreter();
        let (_, ath_object) =
            Interpreter::init_ath_interpreter(&interpreter).expect("the interpreter starts");

        let version = interpreter.enter(|vm| {
            let version = ath_object
                .get_attr("athVersion", vm)
                .expect("the athena object carries a version");
            extract_string(vm, version).expect("the version is a string")
        });

        assert_eq!(version, env!("CARGO_PKG_VERSION"));
    }
}
