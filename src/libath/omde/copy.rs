//! Native payloads participate in Python's normal copy reduction. Keeping native and Python state
//! in one reduction lets deepcopy's memo preserve aliases and cycles.

use rustpython_vm::{
    builtins::{PyDict, PyStr, PyTuple},
    pyclass, AsObject, PyObjectRef, PyPayload, PyRef, PyResult, VirtualMachine,
};

pub(super) fn unpack<const N: usize>(
    state: &PyObjectRef,
    vm: &VirtualMachine,
) -> PyResult<[PyObjectRef; N]> {
    state
        .downcast_ref::<PyTuple>()
        .and_then(|tuple| <&[PyObjectRef; N]>::try_from(tuple.as_slice()).ok())
        .cloned()
        .ok_or_else(|| vm.new_type_error(format!("expected a {N}-item state tuple")))
}

#[pyclass]
pub(super) trait CopyState: PyPayload {
    fn native_state(&self, vm: &VirtualMachine) -> PyResult;
    fn restore_native_state(&self, state: PyObjectRef, vm: &VirtualMachine) -> PyResult<()>;

    #[pymethod]
    fn __getstate__(zelf: PyRef<Self>, vm: &VirtualMachine) -> PyResult {
        let native = zelf.native_state(vm)?;
        // object.__getstate__ includes both __dict__ and a subclass's __slots__.
        let attributes = vm
            .ctx
            .types
            .object_type
            .as_object()
            .get_attr("__getstate__", vm)?
            .call((zelf,), vm)?;
        Ok(vm.ctx.new_tuple(vec![native, attributes]).into())
    }

    #[pymethod]
    fn __setstate__(zelf: PyRef<Self>, state: PyObjectRef, vm: &VirtualMachine) -> PyResult<()> {
        let [native, attributes] = unpack(&state, vm)?;
        zelf.restore_native_state(native, vm)?;
        restore_attributes(zelf.as_object(), attributes, vm)
    }
}

fn restore_attributes(
    object: &rustpython_vm::PyObject,
    state: PyObjectRef,
    vm: &VirtualMachine,
) -> PyResult<()> {
    let (dict, slots) = if state.downcast_ref::<PyTuple>().is_some() {
        let [dict, slots] = unpack(&state, vm)?;
        (dict, Some(slots))
    } else {
        (state, None)
    };
    if !vm.is_none(&dict) {
        let target = object
            .dict()
            .ok_or_else(|| vm.new_type_error("object has no __dict__"))?;
        for (key, value) in dict.try_into_value::<PyRef<PyDict>>(vm)?.items_vec() {
            target.set_item(key.as_object(), value, vm)?;
        }
    }
    if let Some(slots) = slots {
        for (key, value) in slots.try_into_value::<PyRef<PyDict>>(vm)?.items_vec() {
            object.set_attr(&key.try_into_value::<PyRef<PyStr>>(vm)?, value, vm)?;
        }
    }
    Ok(())
}
