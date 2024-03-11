//! The executable.

use std::process::ExitCode;

use rustpython_vm as vm;
use vm::Interpreter;
use athenacl;

fn main() -> ExitCode {
    let interpreter = athenacl::init_interpreter();
    let result = py_main(&interpreter);
    ExitCode::from(interpreter.run(|_vm| result))
}

fn py_main(interp: &Interpreter) -> vm::PyResult<()> {
    interp.enter(|vm| {
        let _ = vm.import("athenaCL.athenacl", None, 0)?;
        vm::PyResult::Ok(())
    })
}
