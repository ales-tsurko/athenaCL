//! The in-place dispatch probes for the miscellaneous port, in their own interpreter.
//!
//! The interpreter quickens binary operations once they have executed with numeric operands, and
//! its quickened fallback drops the in-place operation — a frozen reference exercised with numbers
//! first will run its `+=` as plain `+` from then on. These probes therefore run in a fresh
//! interpreter, before anything warms the reference: cold, it dispatches `__iadd__`/`__isub__` as
//! the language defines, and the port's own in-place operations must agree. The main parity corpus
//! cannot hold these blocks — its earlier blocks do the warming.

mod support;

use rustpython_vm as vm;

#[test]
fn miscellaneous_in_place_dispatch() {
    // before the interpreter starts, so that its first read of the preferences already sees it
    support::init_scratch_prefs();
    let interpreter = athenacl::init_py_interpreter();

    let failed = interpreter.enter(|vm| {
        let scope = vm.new_scope_with_builtins();
        let code = vm::py_compile!(file = "fresh_misc.py");
        match vm.run_code_obj(vm.ctx.new_code(code), scope) {
            Ok(_) => false,
            Err(exception) => {
                vm.print_exception(exception);
                true
            }
        }
    });

    assert!(
        !failed,
        "the fresh in-place probes failed: the report is above"
    );
}

#[test]
fn unit_mutating_step_dispatch() {
    support::init_scratch_prefs();
    let interpreter = athenacl::init_py_interpreter();

    let failed = interpreter.enter(|vm| {
        let scope = vm.new_scope_with_builtins();
        let code = vm::py_compile!(file = "fresh_unit.py");
        match vm.run_code_obj(vm.ctx.new_code(code), scope) {
            Ok(_) => false,
            Err(exception) => {
                vm.print_exception(exception);
                true
            }
        }
    });

    assert!(
        !failed,
        "the fresh unit step probe failed: the report is above"
    );
}
