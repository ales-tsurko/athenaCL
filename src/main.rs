use std::process::ExitCode;

use rustpython_vm as vm;
use vm::Interpreter;

fn main() -> ExitCode {
    let settings = vm::Settings::default();
    let interp = vm::Interpreter::with_init(settings, |vm| {
        vm.add_native_modules(rustpython_stdlib::get_module_inits());
        vm.add_frozen(rustpython_pylib::FROZEN_STDLIB);
        vm.add_frozen(vm::py_freeze!(dir = "pysrc"));
    });
    let result = py_main(&interp);
    ExitCode::from(interp.run(|_vm| result))
}

fn py_main(interp: &Interpreter) -> vm::PyResult<()> {
    interp.enter(|vm| {
        let _ = vm.import("athenaCL.athenacl", None, 0)?;
        vm::PyResult::Ok(())
    })
}
