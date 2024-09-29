//! athenaCL interpreter.

use rustpython_vm as vm;
use serde::{Deserialize, Serialize};
use thiserror::Error;
use vm::{
    builtins::{PyBaseExceptionRef, PyInt, PyStr, PyTuple},
    convert::ToPyObject,
    Interpreter as PyInterpreter, PyObjectRef, PyResult, VirtualMachine,
};

use crate::init_py_interpreter;

pub(crate) type ModuleResult<T> = Result<T, Error>;

pub(crate) struct Interpreter {
    py_interpreter: PyInterpreter,
    ath_interpreter: PyObjectRef,
}

impl Interpreter {
    pub(crate) fn new() -> ModuleResult<Self> {
        let py_interpreter = init_py_interpreter();
        let ath_interpreter = Self::init_ath_interpreter(&py_interpreter)?;
        Ok(Self {
            py_interpreter: init_py_interpreter(),
            ath_interpreter,
        })
    }

    fn init_ath_interpreter(interpreter: &PyInterpreter) -> ModuleResult<PyObjectRef> {
        interpreter.enter(|vm| -> ModuleResult<PyObjectRef> {
            let scope = vm.new_scope_with_builtins();
            let module = vm::py_compile!(
                source = r#"from athenaCL.libATH import athenaObj
interp = athenaObj.Interpreter()
interp"#
            );
            let _ = vm
                .run_code_obj(vm.ctx.new_code(module), scope.clone())
                .try_py(vm)?;
            scope.globals.get_item("interp", vm).try_py(vm)
        })
    }

    pub(crate) fn run_cmd(&self, cmd: &str) -> ModuleResult<Vec<Output>> {
        self.py_interpreter
            .enter(|vm| -> ModuleResult<Vec<Output>> {
                let result = vm
                    .call_method(&self.ath_interpreter, "cmd", (cmd.to_string(),))
                    .try_py(vm)?;
                let (is_ok, msg) = extract_tuple(vm, result).try_py(vm)?;

                if is_ok {
                    Ok(serde_json::from_str(&msg)?)
                } else {
                    Err(Error::Command(cmd.to_owned(), msg))
                }
            })
    }
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

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type", content = "params")]
pub(crate) enum Output {
    Header(String),
    Divider,
    Paragraph(String),
    Row(Vec<Self>),
    Link(LinkOutput),
}

#[derive(Debug, Serialize, Deserialize)]
pub(crate) struct LinkOutput {
    pub(crate) text: String,
    pub(crate) cmd: String,
}

pub(crate) trait TryPy {
    type Output;

    fn try_py(self, vm: &VirtualMachine) -> ModuleResult<Self::Output>;
}

impl<T> TryPy for PyResult<T> {
    type Output = T;

    fn try_py(self, vm: &VirtualMachine) -> ModuleResult<T> {
        self.map_err(|e| Error::from_py_err(e, vm))
    }
}

#[derive(Debug, Error)]
pub(crate) enum Error {
    #[error("{0}")]
    PythonError(String),
    #[error("Error running command `{0}`: {1}")]
    Command(String, String),
    #[error("Error deserializing interpreter output: {0}")]
    DeserializeOutput(#[from] serde_json::Error),
}

impl Error {
    fn from_py_err(err: PyBaseExceptionRef, vm: &VirtualMachine) -> Self {
        Self::PythonError(
            err.to_pyobject(vm)
                .repr(vm)
                .expect("can't get pyobject representation")
                .to_string(),
        )
    }
}
