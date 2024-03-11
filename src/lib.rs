use rustpython_vm as vm;
use vm::Interpreter;

pub fn init_interpreter() -> Interpreter {
    let settings = vm::Settings::default();
    Interpreter::with_init(settings, |vm| {
        vm.add_native_modules(rustpython_stdlib::get_module_inits());
        vm.add_frozen(rustpython_pylib::FROZEN_STDLIB);
        vm.add_frozen(vm::py_freeze!(dir = "pysrc"));
    })
}
