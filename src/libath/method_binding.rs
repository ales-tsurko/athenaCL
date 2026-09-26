//! Bind native methods as Python `method` objects so deepcopy rebinds saved callbacks.

use rustpython_vm::{
    builtins::{PyBoundMethod, PyStr, PyType},
    class::PyClassImpl,
    function::FuncArgs,
    pyclass,
    types::{Callable, GetAttr, GetDescriptor},
    AsObject, FromArgs, Py, PyObjectRef, PyPayload, PyResult, Traverse, VirtualMachine,
};

#[pyclass(module = "athenaCL.libATH", name = "_MethodBinding", traverse)]
#[derive(Debug, PyPayload)]
pub(crate) struct MethodBinding {
    method: PyObjectRef,
}

impl GetDescriptor for MethodBinding {
    fn descr_get(
        zelf: PyObjectRef,
        obj: Option<PyObjectRef>,
        _cls: Option<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult {
        match obj {
            None => Ok(zelf),
            Some(instance) => {
                let binding = zelf.downcast_ref::<Self>().ok_or_else(|| {
                    vm.new_type_error("unexpected payload for __get__".to_owned())
                })?;
                Ok(PyBoundMethod::new(instance, binding.method.clone())
                    .into_ref(&vm.ctx)
                    .into())
            }
        }
    }
}

impl Callable for MethodBinding {
    type Args = FuncArgs;

    fn call(zelf: &Py<Self>, args: FuncArgs, vm: &VirtualMachine) -> PyResult {
        zelf.method.call(args, vm)
    }
}

impl GetAttr for MethodBinding {
    fn getattro(zelf: &Py<Self>, name: &Py<PyStr>, vm: &VirtualMachine) -> PyResult {
        let class_attr = vm
            .ctx
            .interned_str(name)
            .and_then(|attr_name| zelf.get_class_attr(attr_name));
        if let Some(obj) = class_attr {
            return vm.call_if_get_descriptor(&obj, zelf.to_owned().into());
        }
        zelf.method.get_attr(name, vm)
    }
}

#[derive(FromArgs)]
struct MemoArgs {
    #[pyarg(any)]
    _memo: PyObjectRef,
}

#[pyclass(with(GetDescriptor, Callable, GetAttr))]
impl MethodBinding {
    #[pymethod(name = "__copy__")]
    fn copy_shared(zelf: &Py<Self>) -> PyObjectRef {
        zelf.to_owned().into()
    }

    #[pymethod(name = "__deepcopy__")]
    fn deepcopy_shared(zelf: &Py<Self>, _args: MemoArgs) -> PyObjectRef {
        zelf.to_owned().into()
    }
}

pub(crate) fn bind_method(
    class: &Py<PyType>,
    name: &'static str,
    vm: &VirtualMachine,
) -> PyResult<()> {
    // The unit module can bind methods before the miscellaneous module has been imported.
    MethodBinding::make_static_type();
    let entry = class
        .get_attr(vm.ctx.intern_str(name))
        .ok_or_else(|| vm.new_type_error(format!("the {name} method is not reachable")))?;
    class.set_attr(
        vm.ctx.intern_str(name),
        MethodBinding { method: entry }.into_ref(&vm.ctx).into(),
    );
    Ok(())
}
