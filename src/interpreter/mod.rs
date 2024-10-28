//! athenaCL interpreter.

use std::sync::LazyLock;
use std::thread;

use async_channel::{unbounded, Receiver, Sender};
use rustpython_vm as vm;
use thiserror::Error;
use vm::{
    builtins::{PyBaseExceptionRef, PyInt, PyStr, PyTuple},
    Interpreter as PyInterpreter, PyObjectRef, PyResult, VirtualMachine,
};

mod dialog_ext;
mod xml_tools_ext;

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
        let (interp_sender, r) = unbounded::<Message>();
        let (gui_sender, gui_receiver) = unbounded::<Message>();
        let s = gui_sender.clone();

        let _ = thread::spawn(move || {
            let interpreter = Interpreter::new().unwrap_or_else(|err| {
                s.send_blocking(Message::PythonError(err.to_string()))
                    .expect("can't send message to channel");
                panic!("error initializating interpreter");
            });

            loop {
                if let Ok(message) = r.recv_blocking() {
                    let msg = match message {
                        Message::SendCmd(cmd) => interpreter.run_cmd(&cmd).map(Message::Post),
                        Message::GetScratchDir => {
                            interpreter.scratch_dir().map(Message::ScratchDir)
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
    Ask(String),
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
    /// Get scratch dir.
    GetScratchDir,
    /// The result of `Self::GetScratchDir`.
    ScratchDir(String),
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
            let module = vm::py_compile!(
                source = r#"from athenaCL.libATH import athenaObj
interp = athenaObj.Interpreter()
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
        self.py_interpreter
            .enter(|vm| -> InterpreterResult<String> {
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

    fn scratch_dir(&self) -> InterpreterResult<String> {
        self.py_interpreter
            .enter(|vm| -> InterpreterResult<String> {
                let external = vm
                    .get_attribute_opt(self.ath_object.clone(), "external")
                    .try_py()?
                    .expect("external attribute is always available on AthenaObject");
                let result = vm
                    .call_method(&external, "getPref", ("athena", "fpScratchDir"))
                    .try_py()?;

                extract_string(vm, result).try_py()
            })
    }
}

/// Initialize the python interpreter with precompiled stdlib and athenaCL (python modules).
pub fn init_py_interpreter() -> PyInterpreter {
    let mut settings = vm::Settings::default();
    settings.optimize = 2;
    PyInterpreter::with_init(settings, |vm| {
        vm.add_native_modules(rustpython_stdlib::get_module_inits());
        vm.add_frozen(rustpython_pylib::FROZEN_STDLIB);
        vm.add_frozen(vm::py_freeze!(dir = "pysrc"));
        xml_tools_ext::make_module(vm);
        dialog_ext::make_module(vm);
    })
}

fn extract_result_tuple(vm: &VirtualMachine, result: PyObjectRef) -> PyResult<(bool, String)> {
    // Ensure the result is a tuple
    if let Some(tuple) = result.payload::<PyTuple>() {
        let elements = tuple.as_slice();

        // Ensure the tuple has exactly 2 elements (Integer, String)
        if elements.len() == 2 {
            // Extract and convert the first element to i32
            let int_part = elements[0]
                .payload::<PyInt>()
                .ok_or_else(|| vm.new_type_error("Expected an integer".to_owned()))?
                .as_bigint();

            let bool_part = *int_part != 0.into();

            // Extract and convert the second element to String
            let str_part = elements[1]
                .payload::<PyStr>()
                .ok_or_else(|| vm.new_type_error("Expected a string".to_owned()))?
                .as_str()
                .to_owned();

            Ok((bool_part, str_part))
        } else {
            Err(vm.new_value_error("Expected a tuple of length 2".to_owned()))
        }
    } else {
        Err(vm.new_type_error("Expected a tuple".to_owned()))
    }
}

fn extract_string(vm: &VirtualMachine, result: PyObjectRef) -> PyResult<String> {
    result
        .payload::<PyStr>()
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
        self.map_err(|e| Error::from_py_err(e))
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
            .map(|s| s.as_str().to_owned())
            .unwrap_or_else(|| "Unknown (silent) error".to_string());

        Self::PythonError(message)
    }
}
