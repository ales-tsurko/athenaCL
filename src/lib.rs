//! athenaCL is an algorithmic music composition tool.

use rustpython_vm as vm;
use vm::Interpreter as PyInterpreter;
pub use app::App;

mod dialog_ext;
mod interpreter;
mod xml_tools_ext;
mod app;

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
