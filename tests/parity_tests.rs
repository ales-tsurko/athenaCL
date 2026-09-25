//! Runs the parity tests of the ported Python modules against their Rust ports.

mod support;

use rustpython_vm as vm;

#[test]
fn parity() {
    // before the interpreter starts, so that its first read of the preferences already sees it
    support::init_scratch_prefs();
    let interpreter = athenacl::init_py_interpreter();

    // The vm is entered rather than run, so it is never finalized: finalizing collects every object
    // the tests made, which takes longer than running them, and the process ends here anyway. The
    // runner prints its report as it goes, so a failure is readable without it.
    let failed = interpreter.enter(|vm| {
        let scope = vm.new_scope_with_builtins();
        let code = vm::py_compile!(file = "parity.py");
        match vm.run_code_obj(vm.ctx.new_code(code), scope) {
            Ok(_) => false,
            Err(exception) => {
                vm.print_exception(exception);
                true
            }
        }
    });

    assert!(!failed, "the parity tests failed: their report is above");
}
