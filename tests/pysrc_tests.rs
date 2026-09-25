//! Runs the tests of the Python sources.

mod support;

use rustpython_vm as vm;

#[test]
fn test() {
    // A previous process can have used this PID and left an incomplete preferences file behind.
    let previous = std::env::temp_dir()
        .join("athenacl-tests")
        .join(std::process::id().to_string());
    std::fs::create_dir_all(&previous).expect("old preferences directory");
    let name = if cfg!(windows) {
        ".athenaclrc.xml"
    } else {
        ".athenaclrc"
    };
    std::fs::write(previous.join(name), "<?xml version=\"1.0\"?>")
        .expect("incomplete old preferences file");

    // before the interpreter starts, so that its first read of the preferences already sees it
    support::init_scratch_prefs();
    let interpreter = athenacl::init_py_interpreter();

    // The vm is entered rather than run, so it is never finalized: finalizing collects every object
    // the tests made, which takes longer than running them, and the process ends here anyway. The
    // runner prints its report as it goes, so a failure is readable without it.
    let failed = interpreter.enter(|vm| {
        let scope = vm.new_scope_with_builtins();
        let code = vm::py_compile!(file = "runner.py");
        match vm.run_code_obj(vm.ctx.new_code(code), scope) {
            Ok(_) => false,
            Err(exception) => {
                vm.print_exception(exception);
                true
            }
        }
    });

    assert!(!failed, "the Python tests failed: their report is above");
}
