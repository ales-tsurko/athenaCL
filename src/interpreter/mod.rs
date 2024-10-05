//! athenaCL interpreter.

use std::sync::LazyLock;
use std::thread::{self, JoinHandle};

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

/// A worker which keeps the interpreter on a dedicated thread and provides communication with it
/// via channels.
#[derive(Debug)]
pub struct InterpreterWorker {
    interpreter_handle: JoinHandle<()>,
    pub sender: Sender<Message>,
    pub receiver: Receiver<Message>,
}

impl InterpreterWorker {
    /// Run the interpereter loop.
    fn run() -> Self {
        let (sender, receiver) = unbounded::<Message>();
        let s = sender.clone();
        let r = receiver.clone();

        let interpreter_handle = thread::spawn(move || {
            let interpreter = Interpreter::new().unwrap_or_else(|err| {
                s.send_blocking(Message::PythonError(err.to_string()))
                    .expect("can't send message to channel");
                panic!("error initializating interpreter");
            });

            loop {
                if let Ok(message) = r.recv_blocking() {
                    if let Message::SendCmd(cmd) = message {
                        match interpreter.run_cmd(&cmd) {
                            Ok(msg) => s
                                .send_blocking(Message::Post(msg))
                                .expect("cannot send message via channel"),
                            Err(Error::Command(_, cmd_err)) => s
                                .send_blocking(Message::Error(cmd_err))
                                .expect("cannot send message via channel"),
                            Err(Error::PythonError(err)) => s
                                .send_blocking(Message::PythonError(err))
                                .expect("cannot send message via channel"),
                        }
                    }
                }
            }
        });

        Self {
            interpreter_handle,
            sender,
            receiver,
        }
    }
}

#[derive(Debug, Clone)]
pub enum Message {
    /// Output from the interpreter (stdout).
    Post(String),
    /// Requested input (stdin).
    Ask(String),
    /// Send command to the interpreter.
    SendCmd(String),
    /// Error from the interpreter (stderr).
    Error(String),
    /// Python's interpreter- level errors.
    PythonError(String),
}

pub(crate) type InterpreterResult<T> = Result<T, Error>;

struct Interpreter {
    py_interpreter: PyInterpreter,
    ath_interpreter: PyObjectRef,
}

impl Interpreter {
    fn new() -> InterpreterResult<Self> {
        let py_interpreter = init_py_interpreter();
        let ath_interpreter = Self::init_ath_interpreter(&py_interpreter)?;
        Ok(Self {
            py_interpreter: init_py_interpreter(),
            ath_interpreter,
        })
    }

    fn init_ath_interpreter(interpreter: &PyInterpreter) -> InterpreterResult<PyObjectRef> {
        interpreter.enter(|vm| -> InterpreterResult<PyObjectRef> {
            let scope = vm.new_scope_with_builtins();
            let module = vm::py_compile!(
                source = r#"from athenaCL.libATH import athenaObj
interp = athenaObj.Interpreter()
interp"#
            );
            let _ = vm
                .run_code_obj(vm.ctx.new_code(module), scope.clone())
                .try_py()?;
            scope.globals.get_item("interp", vm).try_py()
        })
    }

    fn run_cmd(&self, cmd: &str) -> InterpreterResult<String> {
        self.py_interpreter
            .enter(|vm| -> InterpreterResult<String> {
                let result = vm
                    .call_method(&self.ath_interpreter, "cmd", (cmd.to_string(),))
                    .try_py()?;
                let (is_ok, msg) = extract_tuple(vm, result).try_py()?;

                if is_ok {
                    Ok(msg)
                } else {
                    Err(Error::Command(cmd.to_owned(), msg))
                }
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

fn extract_tuple(vm: &VirtualMachine, result: PyObjectRef) -> PyResult<(bool, String)> {
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
