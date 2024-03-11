// runs tests for python code

use rustpython_vm as vm;
use vm::py_freeze;

#[test]
fn test() {
    let interpreter = athenacl::init_interpreter();

    let result = interpreter.enter(|vm| {
        let scope = vm.new_scope_with_builtins();
        let code = vm::py_compile!(file = "tests/runner.py");
        vm.run_code_obj(vm.ctx.new_code(code), scope)?;

        vm::PyResult::Ok(())
    });

    interpreter.run(|_vm| result);
}
