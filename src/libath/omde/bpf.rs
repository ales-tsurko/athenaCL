//! Native break-point functions, preserving `Function -> BPF -> segment` inheritance.
//!
//! The reference is `pysrc/athenaCL/libATH/_pyref/bpf.py`. Coordinates use Python's `float()`
//! constructor; evaluation compares the original time before doing float arithmetic. Periodic
//! evaluation retains the reference's successive period shifts. Interpolation dispatches through
//! the instance so Python overrides still work.
//!
//! Preserved quirks include the "Two few pairs" typo, normalization into `[0, 1]`, ignored segment
//! keywords, and delayed validation of the power exponent. Power segments use builtin `pow`, which
//! differs from `math.pow` in RustPython. Failed validation retains the newly converted pairs and
//! the previous bounds/flag; failed conversion leaves the pairs unchanged. Copies preserve this
//! partial state. Narrowings: `pairs` returns a snapshot and is not writable; the other
//! implementation attributes (`xStart`, `xEnd`, `period`, `_is_periodic`, `exponent`) are not
//! exposed. No athenaCL consumer reads or writes those attributes.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

/// Numeric storage can be shared across a call without holding a lock during Python code.
mod core {
    use std::sync::Arc;

    use super::super::math;

    #[derive(Debug, Clone)]
    pub(super) struct Points {
        pub pairs: Arc<[(f64, f64)]>,
    }

    /// Cached only after validation succeeds, independently of the current pairs.
    #[derive(Debug, Clone, Copy)]
    pub(super) struct Bounds {
        pub start: f64,
        pub end: f64,
    }

    #[derive(Debug, PartialEq, Eq)]
    pub(super) enum InvalidPairs {
        OutOfOrder,
        TooFew(usize),
    }

    impl Points {
        pub fn new(pairs: Vec<(f64, f64)>) -> Self {
            Self {
                pairs: pairs.into(),
            }
        }

        pub fn validate(&self) -> Result<Bounds, InvalidPairs> {
            if self
                .pairs
                .windows(2)
                .any(|pair| matches!(pair, [first, second] if second.0 < first.0))
            {
                return Err(InvalidPairs::OutOfOrder);
            }
            match self.pairs.as_ref() {
                [first, .., last] => Ok(Bounds {
                    start: first.0,
                    end: last.0,
                }),
                _ => Err(InvalidPairs::TooFew(self.pairs.len())),
            }
        }

        /// Build the replacement first: a failed normalization leaves the old pairs intact.
        pub fn normalize(&mut self) -> Result<(), math::Error> {
            let Some(&(_, first)) = self.pairs.first() else {
                return Ok(());
            };
            let (mut min, mut max) = (first, first);
            for &(_, value) in self.pairs.iter() {
                if value > max {
                    max = value;
                }
                if value < min {
                    min = value;
                }
            }
            let factor = max - min;
            let pairs: Result<Vec<_>, _> = self
                .pairs
                .iter()
                .map(|&(t, value)| math::divide(value - min, factor).map(|value| (t, value)))
                .collect();
            self.pairs = pairs?.into();
            Ok(())
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[test]
        fn pair_validation_and_atomic_normalization() {
            assert!(matches!(
                Points::new(vec![(2.0, 0.0), (1.0, 1.0)]).validate(),
                Err(InvalidPairs::OutOfOrder)
            ));
            assert!(matches!(
                Points::new(vec![(0.0, 1.0)]).validate(),
                Err(InvalidPairs::TooFew(1))
            ));
            let mut points = Points::new(vec![(0.0, 5.0), (1.0, 15.0), (2.0, -5.0)]);
            points.normalize().expect("nonzero range");
            assert_eq!(points.pairs.as_ref(), &[(0.0, 0.5), (1.0, 1.0), (2.0, 0.0)]);
            let mut flat = Points::new(vec![(0.0, 5.0), (1.0, 5.0)]);
            let before = flat.pairs.clone();
            assert_eq!(flat.normalize(), Err(math::Error::ZeroDivision));
            assert!(Arc::ptr_eq(&before, &flat.pairs));
        }
    }
}

#[pymodule(name = "athenaCL.libATH.omde.bpf")]
pub(super) mod _inner {
    use rustpython_vm::{
        builtins::{PyDict, PyFloat, PyType},
        common::lock::PyRwLock,
        function::{FuncArgs, KwArgs, OptionalArg},
        protocol::PyNumberMethods,
        pyclass,
        types::{AsNumber, Callable, Constructor, Initializer, PyComparisonOp},
        AsObject, FromArgs, Py, PyObjectRef, PyRef, PyResult, Traverse, VirtualMachine,
    };

    use super::{
        super::{
            copy::{self, CopyState},
            functional::{Function, FunctionModel},
            math,
        },
        core::{Bounds, InvalidPairs, Points},
    };

    /// Native base types must exist before RustPython constructs this module's subclasses.
    pub(crate) fn module_exec(
        vm: &VirtualMachine,
        module: &Py<rustpython_vm::builtins::PyModule>,
    ) -> PyResult<()> {
        vm.import("athenaCL.libATH.omde._functional", 0)?;
        __module_exec(vm, module);
        Ok(())
    }

    #[derive(Debug, Clone, Default, Traverse)]
    struct State {
        #[pytraverse(skip)]
        points: Option<Points>,
        #[pytraverse(skip)]
        bounds: Option<Bounds>,
        periodic: Option<PyObjectRef>,
        exponent: Option<PyObjectRef>,
    }

    /// Python's `float()` also parses text/bytes; `try_float()` alone does not.
    fn coordinate(value: PyObjectRef, vm: &VirtualMachine) -> PyResult<f64> {
        let float_type: PyObjectRef = vm.ctx.types.float_type.to_owned().into();
        let value = float_type.call((value,), vm)?;
        Ok(value
            .downcast_ref::<PyFloat>()
            .expect("float() returns a float")
            .to_f64())
    }

    fn points(pairs: &PyObjectRef, vm: &VirtualMachine) -> PyResult<Points> {
        let mut floated = Vec::new();
        for item in pairs.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let item = item?;
            // Unpack just three items: even an infinite malformed pair raises promptly.
            let not_iterable = item.class().slots.iter.load().is_none()
                && item
                    .get_class_attr(vm.ctx.intern_str("__getitem__"))
                    .is_none();
            let iterator = item.get_iter(vm).map_err(|error| {
                if not_iterable && error.class().is(vm.ctx.exceptions.type_error) {
                    vm.new_type_error(format!(
                        "cannot unpack non-iterable {} object",
                        item.class().name()
                    ))
                } else {
                    error
                }
            })?;
            let mut pair = iterator.iter_without_hint::<PyObjectRef>(vm)?;
            let x = pair.next().transpose()?;
            let y = pair.next().transpose()?;
            let (Some(x), Some(y)) = (x.as_ref(), y.as_ref()) else {
                let count = usize::from(x.is_some());
                return Err(vm.new_value_error(format!(
                    "not enough values to unpack (expected 2, got {count})"
                )));
            };
            if pair.next().transpose()?.is_some() {
                let cls = item.class();
                let message = if cls.is(vm.ctx.types.tuple_type)
                    || cls.is(vm.ctx.types.list_type)
                    || cls.is(vm.ctx.types.dict_type)
                {
                    format!(
                        "too many values to unpack (expected 2, got {})",
                        item.length(vm)?
                    )
                } else {
                    "too many values to unpack (expected 2)".to_owned()
                };
                return Err(vm.new_value_error(message));
            }
            floated.push((coordinate(x.clone(), vm)?, coordinate(y.clone(), vm)?));
        }
        Ok(Points::new(floated))
    }

    #[pyattr(name = "BPF")]
    #[pyclass(name = "BPF", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct PyBpf {
        #[pytraverse(skip)]
        base: Function,
        state: PyRwLock<State>,
    }

    impl PyBpf {
        fn empty() -> Self {
            Self {
                base: Function(FunctionModel),
                state: PyRwLock::new(State::default()),
            }
        }

        fn read<R>(
            &self,
            vm: &VirtualMachine,
            read: impl FnOnce(&State) -> Option<R>,
        ) -> PyResult<R> {
            read(&self.state.read()).ok_or_else(|| vm.new_attribute_error("BPF is not initialized"))
        }

        fn points(&self, vm: &VirtualMachine) -> PyResult<Points> {
            self.read(vm, |state| state.points.clone())
        }

        fn bounds(&self, vm: &VirtualMachine) -> PyResult<Bounds> {
            self.read(vm, |state| state.bounds)
        }

        fn periodic(&self, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            self.read(vm, |state| state.periodic.clone())
        }

        fn exponent(&self, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            self.read(vm, |state| state.exponent.clone())
        }

        fn replace(&self, state: State) {
            // Releasing Python objects can run __del__, which may reenter this BPF.
            let previous = std::mem::replace(&mut *self.state.write(), state);
            drop(previous);
        }

        fn set_exponent(&self, exponent: PyObjectRef) {
            let previous = self.state.write().exponent.replace(exponent);
            drop(previous);
        }

        fn initialize(
            &self,
            pairs: &PyObjectRef,
            periodic: PyObjectRef,
            vm: &VirtualMachine,
        ) -> PyResult<()> {
            let points = points(pairs, vm)?;
            // Python finishes the list comprehension, assigns pairs, then validates.
            self.state.write().points = Some(points.clone());
            let bounds = points.validate().map_err(|error| {
                vm.new_value_error(match error {
                    InvalidPairs::OutOfOrder => "pairs are not in temporal sequence".to_owned(),
                    InvalidPairs::TooFew(count) => format!("Two few pairs ({count})"),
                })
            })?;
            self.state.write().bounds = Some(bounds);
            let previous = self.state.write().periodic.replace(periodic);
            drop(previous);
            Ok(())
        }
    }

    impl Constructor for PyBpf {
        // Initialization belongs to __init__, including a Python subclass's own signature.
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: FuncArgs, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self::empty())
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct BpfArgs {
        #[pyarg(any)]
        pairs: PyObjectRef,
        #[pyarg(any, optional)]
        periodic: OptionalArg<PyObjectRef>,
    }

    impl Initializer for PyBpf {
        type Args = BpfArgs;

        fn init(zelf: PyRef<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult<()> {
            zelf.initialize(
                &args.pairs,
                args.periodic
                    .as_ref()
                    .cloned()
                    .unwrap_or_else(|| vm.ctx.new_int(0).into()),
                vm,
            )
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct InterpolateArgs {
        #[pyarg(any)]
        time: PyObjectRef,
        #[pyarg(any)]
        time0: PyObjectRef,
        #[pyarg(any)]
        value0: PyObjectRef,
        #[pyarg(any)]
        time1: PyObjectRef,
        #[pyarg(any)]
        value1: PyObjectRef,
    }

    impl InterpolateArgs {
        fn ratio(&self, vm: &VirtualMachine) -> PyResult {
            let elapsed = vm._sub(&self.time, &self.time0)?;
            let span = vm._sub(&self.time1, &self.time0)?;
            vm._truediv(&elapsed, &span)
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct CallArgs {
        #[pyarg(any)]
        t: PyObjectRef,
    }

    // RustPython does not inherit the reflected slots of static native types.
    impl AsNumber for PyBpf {
        fn as_number() -> &'static PyNumberMethods {
            Function::as_number()
        }
    }

    impl CopyState for PyBpf {
        fn native_state(&self, vm: &VirtualMachine) -> PyResult {
            let state = self.state.read().clone();
            let result = vm.ctx.new_dict();
            if let Some(points) = state.points {
                result.set_item("pairs", pairs_object(&points, vm), vm)?;
            }
            if let Some(bounds) = state.bounds {
                result.set_item(
                    "bounds",
                    vm.ctx
                        .new_tuple(vec![
                            vm.ctx.new_float(bounds.start).into(),
                            vm.ctx.new_float(bounds.end).into(),
                        ])
                        .into(),
                    vm,
                )?;
            }
            if let Some(periodic) = state.periodic {
                result.set_item("periodic", periodic, vm)?;
            }
            if let Some(exponent) = state.exponent {
                result.set_item("exponent", exponent, vm)?;
            }
            Ok(result.into())
        }

        fn restore_native_state(&self, state: PyObjectRef, vm: &VirtualMachine) -> PyResult<()> {
            let state = state.try_into_value::<PyRef<PyDict>>(vm)?;
            let points = state
                .get_item_opt("pairs", vm)?
                .map(|pairs| points(&pairs, vm))
                .transpose()?;
            let bounds = state
                .get_item_opt("bounds", vm)?
                .map(|bounds| {
                    let [start, end] = copy::unpack(&bounds, vm)?;
                    Ok(Bounds {
                        start: start.try_into_value(vm)?,
                        end: end.try_into_value(vm)?,
                    })
                })
                .transpose()?;
            self.replace(State {
                points,
                bounds,
                periodic: state.get_item_opt("periodic", vm)?,
                exponent: state.get_item_opt("exponent", vm)?,
            });
            Ok(())
        }
    }

    fn pairs_object(points: &Points, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx
            .new_list(
                points
                    .pairs
                    .iter()
                    .map(|&(x, y)| {
                        vm.ctx
                            .new_tuple(vec![vm.ctx.new_float(x).into(), vm.ctx.new_float(y).into()])
                            .into()
                    })
                    .collect(),
            )
            .into()
    }

    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl PyBpf {
        #[pygetset]
        fn pairs(&self, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            Ok(pairs_object(&self.points(vm)?, vm))
        }

        #[pymethod]
        fn normalize(&self, vm: &VirtualMachine) -> PyResult<()> {
            let mut state = self.state.write();
            let points = state
                .points
                .as_mut()
                .ok_or_else(|| vm.new_attribute_error("BPF is not initialized"))?;
            points.normalize().map_err(|error| error.exception(vm))
        }

        #[pymethod]
        fn interpolate(&self, _args: InterpolateArgs, vm: &VirtualMachine) -> PyResult {
            Err(vm.new_not_implemented_error(""))
        }
    }

    impl Callable for PyBpf {
        type Args = CallArgs;

        fn call(zelf: &Py<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult {
            let periodic = zelf.periodic(vm)?.try_to_bool(vm)?;
            evaluate(zelf, args.t, periodic, vm)
        }
    }

    fn wrap_time(zelf: &PyBpf, mut t: PyObjectRef, vm: &VirtualMachine) -> PyResult {
        // Each comparison/addition reloads the attribute where Python does: callbacks
        // can reinitialize the curve, changing both its bounds and its period.
        while t.rich_compare_bool(
            vm.ctx.new_float(zelf.bounds(vm)?.start).as_object(),
            PyComparisonOp::Lt,
            vm,
        )? {
            let bounds = zelf.bounds(vm)?;
            t = vm._add(&t, vm.ctx.new_float(bounds.end - bounds.start).as_object())?;
        }
        while t.rich_compare_bool(
            vm.ctx.new_float(zelf.bounds(vm)?.end).as_object(),
            PyComparisonOp::Ge,
            vm,
        )? {
            let bounds = zelf.bounds(vm)?;
            t = vm._sub(&t, vm.ctx.new_float(bounds.end - bounds.start).as_object())?;
        }
        Ok(t)
    }

    fn evaluate(
        zelf: &Py<PyBpf>,
        mut t: PyObjectRef,
        periodic: bool,
        vm: &VirtualMachine,
    ) -> PyResult {
        let mut previous = if periodic {
            t = wrap_time(zelf, t, vm)?;
            None
        } else {
            let first = zelf
                .points(vm)?
                .pairs
                .first()
                .copied()
                .ok_or_else(|| vm.new_index_error("list index out of range"))?;
            if t.rich_compare_bool(
                vm.ctx.new_float(first.0).as_object(),
                PyComparisonOp::Lt,
                vm,
            )? {
                return Ok(vm.ctx.new_float(first.1).into());
            }
            Some(first)
        };
        // The for-loop owns the current list, even if a later comparison replaces it.
        let points = zelf.points(vm)?;
        let mut next = None;
        let mut index = 0;
        for &pair in points.pairs.iter() {
            next = Some(pair);
            if t.rich_compare_bool(vm.ctx.new_float(pair.0).as_object(), PyComparisonOp::Lt, vm)? {
                break;
            }
            index += 1;
            previous = Some(pair);
        }
        let previous = previous.ok_or_else(|| unbound("time0", vm))?;
        if !periodic && index == zelf.points(vm)?.pairs.len() {
            return Ok(vm.ctx.new_float(previous.1).into());
        }
        interpolate(
            zelf,
            t,
            previous,
            next.ok_or_else(|| unbound("time1", vm))?,
            vm,
        )
    }

    fn unbound(name: &str, vm: &VirtualMachine) -> rustpython_vm::builtins::PyBaseExceptionRef {
        vm.new_exception_msg(
            vm.ctx.exceptions.unbound_local_error.to_owned(),
            format!("local variable '{name}' referenced before assignment").into(),
        )
    }

    fn interpolate(
        zelf: &Py<PyBpf>,
        t: PyObjectRef,
        previous: (f64, f64),
        next: (f64, f64),
        vm: &VirtualMachine,
    ) -> PyResult {
        let object: PyObjectRef = zelf.to_owned().into();
        object
            .get_attr("interpolate", vm)?
            .call((t, previous.0, previous.1, next.0, next.1), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct SegmentArgs {
        #[pyarg(any)]
        pairs: PyObjectRef,
        #[pyarg(flatten)]
        keywords: KwArgs,
    }

    impl SegmentArgs {
        fn initialize(&self, base: &PyBpf, power: bool, vm: &VirtualMachine) -> PyResult<()> {
            // Keep the original arguments alive through the outer __init__, even if a
            // conversion callback replaces values that have already entered the state.
            let mut keywords = self.keywords.clone();
            if keywords.pop_kwarg("pairs").is_some() {
                return Err(
                    vm.new_type_error("__init__() got multiple values for argument 'pairs'")
                );
            }
            if power {
                // PowerSegment assigns this before BPF.__init__, so a finalizer sees
                // the previous pairs and any failed pair validation keeps the new exponent.
                base.set_exponent(
                    keywords
                        .pop_kwarg("exp")
                        .unwrap_or_else(|| vm.ctx.new_float(1.0).into()),
                );
            }
            let periodic = keywords
                .pop_kwarg("periodic")
                .unwrap_or_else(|| vm.ctx.new_int(0).into());
            base.initialize(&self.pairs, periodic, vm)
        }
    }

    // Identical payload layout lets inherited BPF bindings access each segment's state.
    #[pyattr]
    #[pyclass(name = "PowerSegment", base = PyBpf, traverse)]
    #[repr(transparent)]
    #[derive(Debug)]
    pub(crate) struct PowerSegment(pub PyBpf);

    #[pyattr]
    #[pyclass(name = "LinearSegment", base = PyBpf, traverse)]
    #[repr(transparent)]
    #[derive(Debug)]
    pub(crate) struct LinearSegment(pub PyBpf);

    #[pyattr]
    #[pyclass(name = "HalfCosineSegment", base = PyBpf, traverse)]
    #[repr(transparent)]
    #[derive(Debug)]
    pub(crate) struct HalfCosineSegment(pub PyBpf);

    #[pyattr]
    #[pyclass(name = "NoInterpolationSegment", base = PyBpf, traverse)]
    #[repr(transparent)]
    #[derive(Debug)]
    pub(crate) struct NoInterpolationSegment(pub PyBpf);

    macro_rules! segment_init {
        ($class:ident, $power:literal) => {
            impl From<PyBpf> for $class {
                fn from(base: PyBpf) -> Self {
                    Self(base)
                }
            }
            impl Constructor for $class {
                type Args = FuncArgs;

                fn py_new(
                    _cls: &Py<PyType>,
                    _args: FuncArgs,
                    _vm: &VirtualMachine,
                ) -> PyResult<Self> {
                    Ok(Self(PyBpf::empty()))
                }
            }
            impl Initializer for $class {
                type Args = SegmentArgs;

                fn init(zelf: PyRef<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult<()> {
                    args.initialize(&zelf.0, $power, vm)
                }
            }
            impl AsNumber for $class {
                fn as_number() -> &'static PyNumberMethods {
                    Function::as_number()
                }
            }
        };
    }
    segment_init!(PowerSegment, true);
    segment_init!(LinearSegment, false);
    segment_init!(HalfCosineSegment, false);
    segment_init!(NoInterpolationSegment, false);

    fn linear(args: &InterpolateArgs, ratio: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let difference = vm._sub(&args.value1, &args.value0)?;
        let scaled = vm._mul(ratio, &difference)?;
        vm._add(&args.value0, &scaled)
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Initializer, AsNumber))]
    impl LinearSegment {
        #[pymethod]
        fn interpolate(&self, args: InterpolateArgs, vm: &VirtualMachine) -> PyResult {
            linear(&args, &args.ratio(vm)?, vm)
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Initializer, AsNumber))]
    impl NoInterpolationSegment {
        #[pymethod]
        fn interpolate(&self, args: InterpolateArgs) -> PyObjectRef {
            args.value0
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Initializer, AsNumber))]
    impl HalfCosineSegment {
        #[pymethod]
        fn interpolate(&self, args: InterpolateArgs, vm: &VirtualMachine) -> PyResult {
            let pi: PyObjectRef = vm.ctx.new_float(std::f64::consts::PI).into();
            let ratio = args.ratio(vm)?;
            let radians = vm._mul(&ratio, &pi)?;
            let x = vm._add(&radians, &pi)?;
            let cosine =
                math::trig(x.try_float(vm)?.to_f64(), true).map_err(|error| error.exception(vm))?;
            let difference = vm._sub(&args.value1, &args.value0)?;
            let scaled = vm._mul(&difference, vm.ctx.new_float(1.0 + cosine).as_object())?;
            let halved = vm._truediv(&scaled, vm.ctx.new_float(2.0).as_object())?;
            vm._add(&args.value0, &halved)
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Initializer, AsNumber))]
    impl PowerSegment {
        #[pymethod]
        fn interpolate(&self, args: InterpolateArgs, vm: &VirtualMachine) -> PyResult {
            let ratio = args.ratio(vm)?;
            if vm.bool_eq(&args.value1, &args.value0)? {
                return Ok(args.value0);
            }
            let zero: PyObjectRef = vm.ctx.new_float(0.0).into();
            if vm.bool_eq(self.0.exponent(vm)?.as_object(), &zero)? {
                return linear(&args, &ratio, vm);
            }
            let positive = self
                .0
                .exponent(vm)?
                .rich_compare_bool(&zero, PyComparisonOp::Gt, vm)?;
            let ascending = args
                .value1
                .rich_compare_bool(&args.value0, PyComparisonOp::Ge, vm)?;
            let one: PyObjectRef = vm.ctx.new_float(1.0).into();
            let (base, start, end) = if positive == ascending {
                (ratio, args.value0, args.value1)
            } else {
                (vm._sub(&one, &ratio)?, args.value1, args.value0)
            };
            // Python evaluates the power base first, then rereads self.exponent.
            let exponent = if positive {
                vm._add(&one, self.0.exponent(vm)?.as_object())?
            } else {
                vm._sub(&one, self.0.exponent(vm)?.as_object())?
            };
            let powered = vm._pow(&base, &exponent, &vm.ctx.none())?;
            let difference = vm._sub(&end, &start)?;
            let scaled = vm._mul(&powered, &difference)?;
            vm._add(&start, &scaled)
        }
    }
}
