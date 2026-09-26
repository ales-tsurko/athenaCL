//! Native OMDE miscellaneous generators, with the Python reference in
//! `_pyref/miscellaneous.py`.
//!
//! This closes the omde family's Cmask generators: `Range`, `IntRange`, `Accumulator`, `Quantizer`,
//! `Attractor`, `Mask`, `List`, `Choice`, and `StaticChoice`, with their helper classes. Like the
//! rand port, the classes are stateless payloads: parameters, sums, indexes, and mode dispatch live
//! in Python instance dictionaries exactly where the reference stored them — including the
//! bound-method attributes `add` and `next`, which are the reference's dispatch mechanism and stay
//! readable, callable, and reassignable. Arithmetic runs through the VM's own operations, and no
//! Rust state is held across the Python callbacks here.
//!
//! Draws keep their reference routing: `Range` and `IntRange` take `omdeRand.UniformRNG()` — the
//! textures stream — while `List`'s random mode and both `Choice` classes draw through the rand
//! module's `choice`/`random` aliases — the parameters stream.
//!
//! `Accumulator`, `List`, `Attractor`, and `Mask` carry their methods as binding descriptors in the
//! class dictionary: wherever a method is obtained — instance access, `super()`, a property's
//! return, an alias — it binds as a real `method` object over the raw method, exactly the copyable
//! kind the reference's Python-level methods were. Class access yields the binding itself, as the
//! reference's class access yielded the function: callable unbound, still binding as a method under
//! any other name, and shared by copies the way functions are. Instance attributes keep resolving
//! first, their descriptor semantics (`staticmethod` bindings) intact, and the ordinary copy
//! reduction carries dict state, subclass slots, and method rebinding to copies — nested callback
//! lists included. Every attribute is read where the reference read it — before callbacks,
//! comparisons, and between branches — and dispatch methods resolve before their arguments
//! evaluate. The reference's augmented assignments dispatch the in-place operations the language
//! defines — `__iadd__` and `__isub__` with the plain operator as fallback — and the port calls the
//! interpreter's own in-place operations to match. (This interpreter quickens binary operations
//! after numeric warm-up, and its quickened fallback drops the in-place operation; the in-place
//! corpus therefore lives in a fresh-interpreter test, where the frozen reference is still cold.)
//!
//! Preserved quirks: `List.__call__` still calls the builtin `next` over a class without `__next__`
//! and raises; `Attractor` still wraps its points with `make_function`, so `findClosest` iterates
//! the wrapper and only an iterable `Function` reaches the arithmetic — whose `pow(2.0,
//! self.exponent)` still passes the wrapped exponent function; `Accumulator` still validates bounds
//! before mode; `List` still ignores unknown keywords; `Choice` still evaluates every probability
//! twice per call — once for the sum, once for the marks — and draws only after both passes, and
//! its non-tuple pair error still raises through `with_traceback(repr(pair))` exactly as written,
//! unsubstituted message and all. `_MarkAccumulatorEvaluate` floats its factor where
//! `_MarkAccumulator` does not, and `StaticChoice` divides its raw probabilities at init, so a zero
//! sum still raises at construction.
//!
//! The only narrowing: `Choice` and `StaticChoice` raise the interpreter's own errors for the
//! arguments their Python `__init__`s rejected — missing, unexpected, and doubled — and the
//! empty-set fold raises `functools.reduce`'s empty-iterable message.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.omde.miscellaneous")]
pub(super) mod _inner {
    use rustpython_vm::{
        builtins::{PyBaseException, PyModule, PyStr, PyType},
        function::{FuncArgs, OptionalArg},
        protocol::PyNumberMethods,
        pyclass,
        types::{AsNumber, Callable, Constructor, Initializer, PyComparisonOp},
        AsObject, FromArgs, Py, PyObject, PyObjectRef, PyPayload, PyRef, PyResult, VirtualMachine,
    };

    use super::super::functional::{Function, FunctionModel, Generator};

    /// Resolve dotted modules with the VM's top-level `__import__` semantics.
    fn module(path: &'static str, vm: &VirtualMachine) -> PyResult {
        let mut object = vm.import(path, 0)?;
        for part in path.split('.').skip(1) {
            object = object.get_attr(part, vm)?;
        }
        Ok(object)
    }

    fn own_module(vm: &VirtualMachine) -> PyResult {
        module("athenaCL.libATH.omde.miscellaneous", vm)
    }

    fn float(value: f64, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_float(value).into()
    }

    fn integer(value: i64, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_int(value).into()
    }

    /// The reference's `math.pow`, with RustPython's checked semantics and domain errors.
    fn math_pow(base: PyObjectRef, exponent: PyObjectRef, vm: &VirtualMachine) -> PyResult {
        own_module(vm)?
            .get_attr("math", vm)?
            .get_attr("pow", vm)?
            .call((base, exponent), vm)
    }

    fn equals(object: &PyObjectRef, text: &'static str, vm: &VirtualMachine) -> PyResult<bool> {
        object.rich_compare_bool(vm.ctx.new_str(text).as_object(), PyComparisonOp::Eq, vm)
    }

    /// The reference's membership test — `mode in [...]` — as in-order rich equality.
    fn matches(mode: &PyObjectRef, names: &[&'static str], vm: &VirtualMachine) -> PyResult<bool> {
        for name in names {
            if equals(mode, name, vm)? {
                return Ok(true);
            }
        }
        Ok(false)
    }

    /// Python's `str()`, which also parses the exotic; `to_string` alone does not.
    fn text(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<String> {
        let stringified = vm
            .ctx
            .types
            .str_type
            .as_object()
            .call((object.clone(),), vm)?;
        Ok(stringified
            .downcast_ref::<PyStr>()
            .expect("str() returns a str")
            .to_str()
            .unwrap_or_default()
            .to_owned())
    }

    fn compare(
        value: &PyObject,
        bound: f64,
        op: PyComparisonOp,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        value.rich_compare_bool(&float(bound, vm), op, vm)
    }

    /// A bound method of the instance, the reference's dispatch attributes (`add`, `next`) —
    /// resolved through the instance, exactly where the reference's `self.method` looked.
    fn bound(zelf: &PyObject, method: &'static str, vm: &VirtualMachine) -> PyResult {
        zelf.get_attr(method, vm)
    }

    /// `self.field(t)`, reading the attribute and calling it with the time.
    fn call_param(
        zelf: &PyObject,
        field: &'static str,
        t: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        zelf.get_attr(field, vm)?.call((t.clone(),), vm)
    }

    /// `make_function(value)` from the functional shim, then the attribute assignment.
    fn set_parameter(
        zelf: &PyObject,
        field: &'static str,
        value: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let maker = module("athenaCL.libATH.omde.functional", vm)?.get_attr("make_function", vm)?;
        zelf.set_attr(field, maker.call((value,), vm)?, vm)
    }

    /// The rand module as the reference's `omdeRand` alias holds it.
    fn omde_rand(vm: &VirtualMachine) -> PyResult {
        own_module(vm)?.get_attr("omdeRand", vm)
    }

    fn deepcopy(value: PyObjectRef, vm: &VirtualMachine) -> PyResult {
        own_module(vm)?
            .get_attr("copy", vm)?
            .get_attr("deepcopy", vm)?
            .call((value,), vm)
    }

    /// An optional parameter's value, with the float the reference defaulted it to.
    fn supplied(
        value: &OptionalArg<PyObjectRef>,
        default: f64,
        vm: &VirtualMachine,
    ) -> PyObjectRef {
        value
            .as_ref()
            .cloned()
            .unwrap_or_else(|| float(default, vm))
    }

    /// The reference's wrapped parameters, assigned in the order its __init__ assigned them.
    fn set_parameters(
        zelf: &PyObject,
        assignments: [(&'static str, PyObjectRef); 4],
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        for (field, value) in assignments {
            set_parameter(zelf, field, value, vm)?;
        }
        Ok(())
    }

    /// The strength ladder the quantizer and the attractor open with: a full strength lands on the
    /// grid, none passes through, and between interpolates.
    fn strength_factor(strength: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        if compare(strength.as_object(), 1.0, PyComparisonOp::Ge, vm)? {
            Ok(float(0.0, vm))
        } else if compare(strength.as_object(), 0.0, PyComparisonOp::Le, vm)? {
            Ok(float(1.0, vm))
        } else {
            vm._sub(&float(1.0, vm), strength)
        }
    }

    /// The bound methods' shared opening: the bounds in the reference's order, then the sum
    /// extended by the value and stored.
    fn bound_state(
        zelf: &PyObject,
        args: &ValueTimeArgs,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef, PyObjectRef)> {
        let lower = call_param(zelf, "lower", &args.t, vm)?;
        let upper = call_param(zelf, "upper", &args.t, vm)?;
        let sum = zelf.get_attr("sum", vm)?;
        let sum = vm._iadd(&sum, &args.value)?;
        zelf.set_attr("sum", sum.clone(), vm)?;
        Ok((lower, upper, sum))
    }

    /// How a bound method folds its overshoot back inside.
    #[derive(Clone, Copy)]
    enum Fold {
        /// The sum clamps at the bound it crossed.
        Clamp,
        /// The overshoot bounces back from the bound it crossed.
        Reflect,
        /// The overshoot re-enters at the opposite bound.
        Wrap,
    }

    impl Fold {
        /// The fold at the bound the sum crossed — `at` — with the opposite bound beside it for the
        /// wrapping fold, keeping each arm's operand order exactly the reference's.
        fn apply(
            self,
            vm: &VirtualMachine,
            sum: &PyObjectRef,
            at: &PyObjectRef,
            opposite: &PyObjectRef,
            above: bool,
        ) -> PyResult {
            match (self, above) {
                (Fold::Clamp, _) => Ok(at.clone()),
                (Fold::Reflect, true) => {
                    let over = vm._sub(sum, at)?;
                    vm._sub(at, &over)
                }
                (Fold::Reflect, false) => {
                    let under = vm._sub(at, sum)?;
                    vm._add(at, &under)
                }
                (Fold::Wrap, true) => {
                    let over = vm._sub(sum, at)?;
                    vm._add(opposite, &over)
                }
                (Fold::Wrap, false) => {
                    let under = vm._sub(at, sum)?;
                    vm._sub(opposite, &under)
                }
            }
        }
    }

    /// The bound methods' shared shape: the bounds in the reference's order, the sum extended by
    /// the value, then the named fold applied at the bound crossed. Every `self.sum` is read where
    /// the reference read it — the comparisons themselves can replace it.
    fn fold_at(
        zelf: &PyObject,
        args: &ValueTimeArgs,
        fold: Fold,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let (lower, upper, _sum) = bound_state(zelf, args, vm)?;
        if zelf
            .get_attr("sum", vm)?
            .rich_compare_bool(&upper, PyComparisonOp::Gt, vm)?
        {
            let sum = zelf.get_attr("sum", vm)?;
            let folded = fold.apply(vm, &sum, &upper, &lower, true)?;
            zelf.set_attr("sum", folded, vm)?;
        } else if zelf
            .get_attr("sum", vm)?
            .rich_compare_bool(&lower, PyComparisonOp::Lt, vm)?
        {
            let sum = zelf.get_attr("sum", vm)?;
            let folded = fold.apply(vm, &sum, &lower, &upper, false)?;
            zelf.set_attr("sum", folded, vm)?;
        }
        Ok(())
    }

    /// The mark accumulators' shared body: the captured starting value, a probability — evaluated
    /// or raw — divided by the factor read after it, folded in place and stored as the choice's
    /// mark.
    fn accumulate_mark(
        zelf: &PyObject,
        possible_choice: &PyObjectRef,
        captured: PyObjectRef,
        probability: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let factor = zelf.get_attr("factor", vm)?;
        let divided = vm._truediv(&probability, &factor)?;
        let value = vm._iadd(&captured, &divided)?;
        zelf.set_attr("value", value.clone(), vm)?;
        possible_choice.set_attr("mark", value, vm)
    }

    /// The builtin `abs`, with its operator semantics.
    fn absolute(value: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        vm.import("builtins", 0)?
            .get_attr("abs", vm)?
            .call((value.clone(),), vm)
    }

    fn extend_with(
        permutations: &mut Vec<PyObjectRef>,
        list: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        for item in list.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            vm.check_signals()?;
            permutations.push(item?);
        }
        Ok(())
    }

    /// Unpack just two items, with the interpreter's own unpacking errors.
    fn unpack_pair(
        item: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
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
        Ok((x.clone(), y.clone()))
    }

    /// `functools.reduce` over an addition, first element first — and its empty-iterable error.
    fn fold_add(values: Vec<PyObjectRef>, vm: &VirtualMachine) -> PyResult {
        let mut values = values.into_iter();
        let mut accumulated = values.next().ok_or_else(|| {
            vm.new_type_error("reduce() of empty iterable with no initial value".to_owned())
        })?;
        for value in values {
            accumulated = vm._add(&accumulated, &value)?;
        }
        Ok(accumulated)
    }

    /// Capture the same module aliases as the reference, once per interpreter.
    pub(crate) fn module_exec(vm: &VirtualMachine, module: &Py<PyModule>) -> PyResult<()> {
        vm.import("athenaCL.libATH.omde._functional", 0)?;
        __module_exec(vm, module);
        let rand = self::module("athenaCL.libATH.omde.rand", vm)?;
        module.set_attr("omdeRand", rand.clone(), vm)?;
        module.set_attr("rand", rand, vm)?;
        let functional = self::module("athenaCL.libATH.omde.functional", vm)?;
        for name in ["Function", "Generator", "make_function"] {
            module.set_attr(name, functional.get_attr(name, vm)?, vm)?;
        }
        for name in ["math", "copy", "types", "unittest", "doctest"] {
            module.set_attr(name, vm.import(name, 0)?, vm)?;
        }
        let functools = vm.import("functools", 0)?;
        module.set_attr("reduce", functools.get_attr("reduce", vm)?, vm)?;
        // the dispatch methods become binding descriptors: wherever they are obtained —
        // instance access, super(), a property's return — they bind as real method objects,
        // the copyable kind the reference's Python-level methods were
        for (class, methods) in [
            (
                "Accumulator",
                [
                    "noBounds",
                    "limitAtBounds",
                    "reflectAtBounds",
                    "wrapAtBounds",
                ]
                .as_slice(),
            ),
            (
                "List",
                [
                    "cycle_next",
                    "swing_next",
                    "random_next",
                    "computePermutations",
                    "swapAdiacentElements",
                ]
                .as_slice(),
            ),
            ("Attractor", ["findClosest"].as_slice()),
            ("Mask", ["mapAt"].as_slice()),
        ] {
            let class: PyRef<PyType> = module
                .get_attr(class, vm)?
                .downcast()
                .map_err(|_absent| vm.new_type_error("the dispatch classes are not reachable"))?;
            for method in methods.iter().copied() {
                super::super::super::method_binding::bind_method(&class, method, vm)?;
            }
        }
        Ok(())
    }

    /// Constructors allocate stateless payloads; typed initializers own validation and mutation.
    macro_rules! omde_new {
        ($class:ident, $base_value:expr) => {
            impl Constructor for $class {
                type Args = FuncArgs;

                fn py_new(
                    _cls: &Py<PyType>,
                    _args: FuncArgs,
                    _vm: &VirtualMachine,
                ) -> PyResult<Self> {
                    Ok(Self { base: $base_value })
                }
            }
        };
    }

    /// Static native subclasses expose their base's operator slots.
    macro_rules! base_number {
        ($class:ident, $base:ident) => {
            impl AsNumber for $class {
                fn as_number() -> &'static PyNumberMethods {
                    $base::as_number()
                }
            }
        };
    }

    #[derive(FromArgs)]
    pub(crate) struct TimeArgs {
        #[pyarg(any)]
        t: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct ValueTimeArgs {
        #[pyarg(any)]
        value: PyObjectRef,
        #[pyarg(any)]
        t: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct MinMaxArgs {
        #[pyarg(any, name = "min")]
        min: PyObjectRef,
        #[pyarg(any, name = "max")]
        max: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct AccumulatorArgs {
        #[pyarg(any)]
        value_generator: PyObjectRef,
        #[pyarg(any, optional)]
        mode: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        lower: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        upper: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        sum0: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    pub(crate) struct QuantizerArgs {
        #[pyarg(any)]
        generator: PyObjectRef,
        #[pyarg(any)]
        delta: PyObjectRef,
        #[pyarg(any, optional)]
        strength: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        offset: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    pub(crate) struct AttractorArgs {
        #[pyarg(any)]
        generator: PyObjectRef,
        #[pyarg(any)]
        points: PyObjectRef,
        #[pyarg(any, optional)]
        strength: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        exponent: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    pub(crate) struct MaskArgs {
        #[pyarg(any, name = "mainFunction")]
        main_function: PyObjectRef,
        #[pyarg(any, name = "lowerLimit")]
        lower_limit: PyObjectRef,
        #[pyarg(any, name = "upperLimit")]
        upper_limit: PyObjectRef,
        #[pyarg(any, optional)]
        exp: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    pub(crate) struct SwapArgs {
        #[pyarg(any)]
        list: PyObjectRef,
        #[pyarg(any)]
        n: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct ComputeArgs {
        #[pyarg(any)]
        list: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct ObjectProbabilityArgs {
        #[pyarg(any)]
        object: PyObjectRef,
        #[pyarg(any)]
        probability: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct EvaluateArgs {
        #[pyarg(any)]
        t: PyObjectRef,
        #[pyarg(any)]
        factor: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct FactorArgs {
        #[pyarg(any)]
        factor: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct PossibleChoiceArgs {
        #[pyarg(any)]
        possible_choice: PyObjectRef,
    }

    /// `self.offset + self.delta * self.rng.random()`, the attributes in the reference's order.
    fn range_value(zelf: &PyObject, integer: bool, vm: &VirtualMachine) -> PyResult {
        let offset = zelf.get_attr("offset", vm)?;
        let delta = zelf.get_attr("delta", vm)?;
        let draw = zelf
            .get_attr("rng", vm)?
            .get_attr("random", vm)?
            .call((), vm)?;
        let scaled = vm._mul(&delta, &draw)?;
        let value = vm._add(&offset, &scaled)?;
        if integer {
            vm.ctx.types.int_type.as_object().call((value,), vm)
        } else {
            Ok(value)
        }
    }

    #[pyattr]
    #[pyclass(name = "Range", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Range {
        base: Generator,
    }

    omde_new!(Range, Generator);
    base_number!(Range, Generator);

    impl Initializer for Range {
        type Args = MinMaxArgs;

        fn init(zelf: PyRef<Self>, args: MinMaxArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            zelf.set_attr("offset", args.min.clone(), vm)?;
            let delta = vm._sub(&args.max, &args.min)?;
            zelf.set_attr("delta", delta, vm)?;
            let rng = omde_rand(vm)?.get_attr("UniformRNG", vm)?.call((), vm)?;
            zelf.set_attr("rng", rng, vm)?;
            Ok(())
        }
    }

    impl Callable for Range {
        type Args = ();

        fn call(zelf: &Py<Self>, _args: (), vm: &VirtualMachine) -> PyResult {
            range_value(zelf.as_object(), false, vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl Range {}

    #[pyattr]
    #[pyclass(name = "IntRange", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct IntRange {
        base: Generator,
    }

    omde_new!(IntRange, Generator);
    base_number!(IntRange, Generator);

    impl Initializer for IntRange {
        type Args = MinMaxArgs;

        fn init(zelf: PyRef<Self>, args: MinMaxArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            zelf.set_attr("offset", args.min.clone(), vm)?;
            let delta = vm._sub(&args.max, &args.min)?;
            zelf.set_attr("delta", delta, vm)?;
            let rng = omde_rand(vm)?.get_attr("UniformRNG", vm)?.call((), vm)?;
            zelf.set_attr("rng", rng, vm)?;
            Ok(())
        }
    }

    impl Callable for IntRange {
        type Args = ();

        fn call(zelf: &Py<Self>, _args: (), vm: &VirtualMachine) -> PyResult {
            range_value(zelf.as_object(), true, vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl IntRange {}

    #[pyattr]
    #[pyclass(name = "Accumulator", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Accumulator {
        base: Function,
    }

    omde_new!(Accumulator, Function(FunctionModel));
    base_number!(Accumulator, Function);

    impl Initializer for Accumulator {
        type Args = AccumulatorArgs;

        fn init(zelf: PyRef<Self>, args: AccumulatorArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            set_parameter(zelf, "generator", args.value_generator, vm)?;
            let sum0 = args
                .sum0
                .as_ref()
                .cloned()
                .unwrap_or_else(|| integer(0, vm));
            zelf.set_attr("sum", sum0, vm)?;
            let mode = args
                .mode
                .as_ref()
                .cloned()
                .unwrap_or_else(|| vm.ctx.new_str("unbound").into());
            if matches(&mode, &["unbound", "u"], vm)? {
                let add = bound(zelf, "noBounds", vm)?;
                zelf.set_attr("add", add, vm)?;
                return Ok(());
            }
            // the reference validates the bounds before the mode
            let upper = args
                .upper
                .as_ref()
                .cloned()
                .unwrap_or_else(|| vm.ctx.none());
            let lower = args
                .lower
                .as_ref()
                .cloned()
                .unwrap_or_else(|| vm.ctx.none());
            if upper.is(&vm.ctx.none()) || lower.is(&vm.ctx.none()) {
                return Err(vm.new_value_error(
                    "cannot create a bound accumulator with undefined bounds".to_owned(),
                ));
            }
            set_parameter(zelf, "upper", upper, vm)?;
            set_parameter(zelf, "lower", lower, vm)?;
            let add = if matches(&mode, &["limit", "l"], vm)? {
                bound(zelf, "limitAtBounds", vm)?
            } else if matches(&mode, &["reflect", "r", "mirror", "m"], vm)? {
                bound(zelf, "reflectAtBounds", vm)?
            } else if matches(&mode, &["wrap", "w"], vm)? {
                bound(zelf, "wrapAtBounds", vm)?
            } else {
                return Err(vm.new_value_error(format!(
                    "mode can only be 'unbound', 'limit', 'reflect', 'mirror' or 'wrap' (got {})",
                    text(&mode, vm)?
                )));
            };
            zelf.set_attr("add", add, vm)?;
            Ok(())
        }
    }

    impl Callable for Accumulator {
        type Args = TimeArgs;

        fn call(zelf: &Py<Self>, args: TimeArgs, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            // the reference resolves the dispatch before evaluating its argument
            let add = zelf.get_attr("add", vm)?;
            let value = call_param(zelf, "generator", &args.t, vm)?;
            add.call((value, args.t.clone()), vm)?;
            zelf.get_attr("sum", vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl Accumulator {
        #[pymethod(name = "noBounds")]
        fn no_bounds(zelf: &Py<Self>, args: ValueTimeArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            let sum = zelf.get_attr("sum", vm)?;
            let summed = vm._iadd(&sum, &args.value)?;
            zelf.set_attr("sum", summed, vm)?;
            Ok(())
        }

        #[pymethod(name = "limitAtBounds")]
        fn limit_at_bounds(
            zelf: &Py<Self>,
            args: ValueTimeArgs,
            vm: &VirtualMachine,
        ) -> PyResult<()> {
            fold_at(zelf.as_object(), &args, Fold::Clamp, vm)
        }

        #[pymethod(name = "reflectAtBounds")]
        fn reflect_at_bounds(
            zelf: &Py<Self>,
            args: ValueTimeArgs,
            vm: &VirtualMachine,
        ) -> PyResult<()> {
            fold_at(zelf.as_object(), &args, Fold::Reflect, vm)
        }

        #[pymethod(name = "wrapAtBounds")]
        fn wrap_at_bounds(
            zelf: &Py<Self>,
            args: ValueTimeArgs,
            vm: &VirtualMachine,
        ) -> PyResult<()> {
            fold_at(zelf.as_object(), &args, Fold::Wrap, vm)
        }
    }

    /// The quantization, with the reference's evaluation order: generator, delta, strength, then
    /// the offset after the factor.
    fn quantizer_value(zelf: &PyObject, t: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let value = call_param(zelf, "generator", t, vm)?;
        let delta = call_param(zelf, "delta", t, vm)?;
        let strength = call_param(zelf, "strength", t, vm)?;
        let factor = strength_factor(&strength, vm)?;
        let offset = call_param(zelf, "offset", t, vm)?;

        let value = vm._isub(&value, &offset)?;
        let delta_2 = vm._truediv(&delta, &float(2.0, vm))?;

        let quotient = vm._truediv(&value, &delta)?;
        let quantized = vm.ctx.types.int_type.as_object().call((quotient,), vm)?;
        let mut quantized = vm._mul(&quantized, &delta)?;
        let mut difference = vm._sub(&value, &quantized)?;

        if difference.rich_compare_bool(&delta_2, PyComparisonOp::Gt, vm)? {
            quantized = vm._iadd(&quantized, &delta)?;
        }
        let negative_delta_2 = vm._neg(&delta_2)?;
        if difference.rich_compare_bool(&negative_delta_2, PyComparisonOp::Lt, vm)? {
            quantized = vm._isub(&quantized, &delta)?;
        }

        difference = vm._sub(&value, &quantized)?;
        let scaled = vm._mul(&difference, &factor)?;
        let quantized = vm._iadd(&quantized, &scaled)?;
        vm._add(&quantized, &offset)
    }

    #[pyattr]
    #[pyclass(name = "Quantizer", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Quantizer {
        base: Function,
    }

    omde_new!(Quantizer, Function(FunctionModel));
    base_number!(Quantizer, Function);

    /// The four wrapped parameters of the quantizer and attractor families, in the order each
    /// reference `__init__` assigned them.
    trait FourParameters {
        fn assignments(&self, vm: &VirtualMachine) -> [(&'static str, PyObjectRef); 4];
    }

    macro_rules! four_parameter_init {
        ($class:ident, $args:ty) => {
            impl Initializer for $class {
                type Args = $args;

                fn init(zelf: PyRef<Self>, args: $args, vm: &VirtualMachine) -> PyResult<()> {
                    set_parameters(zelf.as_object(), args.assignments(vm), vm)
                }
            }
        };
    }

    impl FourParameters for QuantizerArgs {
        fn assignments(&self, vm: &VirtualMachine) -> [(&'static str, PyObjectRef); 4] {
            [
                ("generator", self.generator.clone()),
                ("delta", self.delta.clone()),
                ("strength", supplied(&self.strength, 1.0, vm)),
                ("offset", supplied(&self.offset, 0.0, vm)),
            ]
        }
    }

    impl FourParameters for AttractorArgs {
        fn assignments(&self, vm: &VirtualMachine) -> [(&'static str, PyObjectRef); 4] {
            [
                ("generator", self.generator.clone()),
                ("points", self.points.clone()),
                ("strength", supplied(&self.strength, 1.0, vm)),
                ("exponent", supplied(&self.exponent, 0.0, vm)),
            ]
        }
    }

    four_parameter_init!(Quantizer, QuantizerArgs);
    four_parameter_init!(Attractor, AttractorArgs);

    impl Callable for Quantizer {
        type Args = TimeArgs;

        fn call(zelf: &Py<Self>, args: TimeArgs, vm: &VirtualMachine) -> PyResult {
            quantizer_value(zelf.as_object(), &args.t, vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl Quantizer {}

    #[pyattr]
    #[pyclass(name = "Attractor", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Attractor {
        base: Function,
    }

    omde_new!(Attractor, Function(FunctionModel));
    base_number!(Attractor, Function);

    /// The attractor's strength ladder — whose middle rung passes the wrapped exponent function to
    /// pow, exactly as the reference does, never its value.
    fn attractor_factor(zelf: &PyObject, strength: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        if compare(strength.as_object(), 1.0, PyComparisonOp::Ge, vm)? {
            Ok(float(0.0, vm))
        } else if compare(strength.as_object(), 0.0, PyComparisonOp::Le, vm)? {
            Ok(float(1.0, vm))
        } else {
            let exponent = zelf.get_attr("exponent", vm)?;
            let power = vm._pow(&float(2.0, vm), &exponent, &vm.ctx.none())?;
            let base = vm._sub(&float(1.0, vm), strength)?;
            vm._pow(&base, &power, &vm.ctx.none())
        }
    }

    impl Callable for Attractor {
        type Args = TimeArgs;

        fn call(zelf: &Py<Self>, args: TimeArgs, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            let value = call_param(zelf, "generator", &args.t, vm)?;
            let strength = call_param(zelf, "strength", &args.t, vm)?;
            let factor = attractor_factor(zelf, &strength, vm)?;

            let found = zelf
                .get_attr("findClosest", vm)?
                .call((value, args.t.clone()), vm)?;
            let (difference, closest_point) = unpack_pair(&found, vm)?;
            let scaled = vm._mul(&difference, &factor)?;
            vm._add(&closest_point, &scaled)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl Attractor {
        #[pymethod(name = "findClosest")]
        fn find_closest(zelf: &Py<Self>, args: ValueTimeArgs, vm: &VirtualMachine) -> PyResult {
            let none = vm.ctx.none();
            let mut minimum: PyObjectRef = none.clone();
            let mut closest: PyObjectRef = none.clone();
            let points = zelf.as_object().get_attr("points", vm)?;
            for point in points.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
                vm.check_signals()?;
                let point = point?;
                let called = point.call((args.t.clone(),), vm)?;
                let distance = vm._sub(&args.value, &called)?;
                let unset = minimum.rich_compare_bool(&none, PyComparisonOp::Eq, vm)?;
                if unset {
                    minimum = distance.clone();
                    closest = point;
                } else {
                    let distance_size = absolute(&distance, vm)?;
                    let minimum_size = absolute(&minimum, vm)?;
                    if distance_size.rich_compare_bool(&minimum_size, PyComparisonOp::Lt, vm)? {
                        minimum = distance.clone();
                        closest = point;
                    }
                }
            }
            Ok(vm.ctx.new_tuple(vec![minimum, closest]).into())
        }
    }

    #[pyattr]
    #[pyclass(name = "Mask", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Mask {
        base: Function,
    }

    omde_new!(Mask, Function(FunctionModel));
    base_number!(Mask, Function);

    impl Initializer for Mask {
        type Args = MaskArgs;

        fn init(zelf: PyRef<Self>, args: MaskArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            set_parameter(zelf, "upperLimit", args.upper_limit, vm)?;
            set_parameter(zelf, "lowerLimit", args.lower_limit, vm)?;
            set_parameter(zelf, "mainFunction", args.main_function, vm)?;
            let exp = args.exp.as_ref().cloned().unwrap_or_else(|| float(0.0, vm));
            let exponent = math_pow(float(2.0, vm), exp, vm)?;
            zelf.set_attr("exponent", exponent, vm)?;
            Ok(())
        }
    }

    impl Callable for Mask {
        type Args = TimeArgs;

        fn call(zelf: &Py<Self>, args: TimeArgs, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            // the reference resolves the dispatch before evaluating its argument
            let map_at = zelf.get_attr("mapAt", vm)?;
            let value = call_param(zelf, "mainFunction", &args.t, vm)?;
            map_at.call((value, args.t.clone()), vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl Mask {
        #[pymethod(name = "mapAt")]
        fn map_at(zelf: &Py<Self>, args: ValueTimeArgs, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            // the upper limit evaluates first, as in the reference — and the bounds subtract before
            // the power reads its exponent
            let maximum = call_param(zelf, "upperLimit", &args.t, vm)?;
            let minimum = call_param(zelf, "lowerLimit", &args.t, vm)?;
            let span = vm._sub(&maximum, &minimum)?;
            let exponent = zelf.get_attr("exponent", vm)?;
            let powered = math_pow(args.value.clone(), exponent, vm)?;
            let scaled = vm._mul(&span, &powered)?;
            vm._add(&minimum, &scaled)
        }
    }

    /// The reference's `list[n : n + 2]` dance: slice out, reverse, slice back in.
    fn swap_adiacent(list: &PyObjectRef, n: &PyObjectRef, vm: &VirtualMachine) -> PyResult<()> {
        let two = integer(2, vm);
        let stop = vm._add(n, &two)?;
        let bounds = vm
            .ctx
            .types
            .slice_type
            .as_object()
            .call((n.clone(), stop), vm)?;
        let pair = list.get_item(bounds.as_object(), vm)?;
        pair.get_attr("reverse", vm)?.call((), vm)?;
        list.set_item(bounds.as_object(), pair, vm)
    }

    #[pyattr]
    #[pyclass(name = "List", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct List {
        base: Generator,
    }

    omde_new!(List, Generator);
    base_number!(List, Generator);

    impl Initializer for List {
        type Args = FuncArgs;

        fn init(zelf: PyRef<Self>, args: FuncArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            // the reference scans its keywords for "mode" and silently ignores the rest
            let mode = args
                .kwargs
                .get("mode")
                .cloned()
                .unwrap_or_else(|| vm.ctx.new_str("cycle").into());
            if args.args.is_empty() {
                return Err(vm.new_value_error("cannot create an empty List".to_owned()));
            }
            let list0: PyObjectRef = vm.ctx.new_list(args.args).into();
            let copied = deepcopy(list0.clone(), vm)?;
            zelf.set_attr("list", copied, vm)?;
            let mode = list_mode(&mode, vm)?;
            apply_list_mode(zelf, mode, &list0, vm)
        }
    }

    /// The list modes, as the reference's names dispatched them.
    #[derive(Clone, Copy)]
    enum ListMode {
        Cycle,
        Swing,
        SwingRepeat,
        Heap,
        Random,
    }

    /// The mode a List was asked for, with the reference's error for the names it never had.
    fn list_mode(mode: &PyObjectRef, vm: &VirtualMachine) -> PyResult<ListMode> {
        if matches(mode, &["cycle", "c"], vm)? {
            Ok(ListMode::Cycle)
        } else if matches(mode, &["swing", "s"], vm)? {
            Ok(ListMode::Swing)
        } else if matches(mode, &["swing-repeat", "w"], vm)? {
            Ok(ListMode::SwingRepeat)
        } else if matches(mode, &["heap", "h"], vm)? {
            Ok(ListMode::Heap)
        } else if matches(mode, &["random", "r"], vm)? {
            Ok(ListMode::Random)
        } else {
            Err(vm.new_value_error(format!(
                "mode can be only 'cycle', 'swing', 'swing-repeat', 'heap' or 'random' (got '{}')",
                text(mode, vm)?
            )))
        }
    }

    /// The modes' own assignments, in the order the reference's branches assigned them.
    fn apply_list_mode(
        zelf: &PyObject,
        mode: ListMode,
        list0: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        match mode {
            ListMode::Cycle => {
                zelf.set_attr("index", integer(0, vm), vm)?;
                let next = bound(zelf, "cycle_next", vm)?;
                zelf.set_attr("next", next, vm)?;
            }
            ListMode::Swing => {
                zelf.set_attr("index", integer(0, vm), vm)?;
                zelf.set_attr("step", integer(1, vm), vm)?;
                let next = bound(zelf, "swing_next", vm)?;
                zelf.set_attr("next", next, vm)?;
            }
            ListMode::SwingRepeat => {
                let reversed = deepcopy(list0.clone(), vm)?;
                reversed.get_attr("reverse", vm)?.call((), vm)?;
                zelf.get_attr("list", vm)?
                    .get_attr("extend", vm)?
                    .call((reversed,), vm)?;
                zelf.set_attr("index", integer(0, vm), vm)?;
                let next = bound(zelf, "cycle_next", vm)?;
                zelf.set_attr("next", next, vm)?;
            }
            ListMode::Heap => {
                zelf.set_attr("index", integer(0, vm), vm)?;
                let next = bound(zelf, "cycle_next", vm)?;
                zelf.set_attr("next", next, vm)?;
                let permutations = zelf
                    .get_attr("computePermutations", vm)?
                    .call((list0.clone(),), vm)?;
                zelf.set_attr("list", permutations, vm)?;
            }
            ListMode::Random => {
                let next = bound(zelf, "random_next", vm)?;
                zelf.set_attr("next", next, vm)?;
            }
        }
        Ok(())
    }

    impl Callable for List {
        type Args = ();

        fn call(zelf: &Py<Self>, _args: (), vm: &VirtualMachine) -> PyResult {
            // the reference returned next(self) over a class with no __next__: the builtin's own
            // TypeError, raised identically here
            let zelf_object: PyObjectRef = zelf.to_owned().into();
            vm.import("builtins", 0)?
                .get_attr("next", vm)?
                .call((zelf_object,), vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl List {
        #[pymethod]
        fn cycle_next(zelf: &Py<Self>, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            let list = zelf.get_attr("list", vm)?;
            let index = zelf.get_attr("index", vm)?;
            let item = list.get_item(index.as_object(), vm)?;
            // every attribute is read again where the reference read it — __getitem__ may have
            // replaced them
            let list = zelf.get_attr("list", vm)?;
            let index = zelf.get_attr("index", vm)?;
            let last = integer(list.length(vm)? as i64 - 1, vm);
            if index.rich_compare_bool(&last, PyComparisonOp::Eq, vm)? {
                zelf.set_attr("index", integer(0, vm), vm)?;
            } else {
                let index = zelf.get_attr("index", vm)?;
                let advanced = vm._add(&index, &integer(1, vm))?;
                zelf.set_attr("index", advanced, vm)?;
            }
            Ok(item)
        }

        #[pymethod]
        fn swing_next(zelf: &Py<Self>, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            let list = zelf.get_attr("list", vm)?;
            let index = zelf.get_attr("index", vm)?;
            let item = list.get_item(index.as_object(), vm)?;
            // every attribute is read again where the reference read it — __getitem__ may have
            // replaced them
            if zelf.get_attr("list", vm)?.length(vm)? == 1 {
                zelf.set_attr("step", integer(0, vm), vm)?;
            }
            // the reference's short-circuit: step checked before the index, branch by branch, each
            // attribute read at its own point
            let one = integer(1, vm);
            let forward =
                zelf.get_attr("step", vm)?
                    .rich_compare_bool(&one, PyComparisonOp::Eq, vm)?;
            let flipped_forward = forward && {
                let index = zelf.get_attr("index", vm)?;
                let list = zelf.get_attr("list", vm)?;
                let last = integer(list.length(vm)? as i64 - 1, vm);
                index.rich_compare_bool(&last, PyComparisonOp::Eq, vm)?
            };
            if flipped_forward {
                zelf.set_attr("step", integer(-1, vm), vm)?;
            } else {
                let backward = zelf.get_attr("step", vm)?.rich_compare_bool(
                    &integer(-1, vm),
                    PyComparisonOp::Eq,
                    vm,
                )?;
                let flipped_backward = backward && {
                    let index = zelf.get_attr("index", vm)?;
                    index.rich_compare_bool(&integer(0, vm), PyComparisonOp::Eq, vm)?
                };
                if flipped_backward {
                    zelf.set_attr("step", one, vm)?;
                }
            }
            let step = zelf.get_attr("step", vm)?;
            let index = zelf.get_attr("index", vm)?;
            let advanced = vm._iadd(&index, &step)?;
            zelf.set_attr("index", advanced, vm)?;
            Ok(item)
        }

        #[pymethod]
        fn random_next(zelf: &Py<Self>, vm: &VirtualMachine) -> PyResult {
            let list = zelf.as_object().get_attr("list", vm)?;
            omde_rand(vm)?.get_attr("choice", vm)?.call((list,), vm)
        }

        #[pymethod(name = "computePermutations")]
        fn compute_permutations(
            zelf: &Py<Self>,
            args: ComputeArgs,
            vm: &VirtualMachine,
        ) -> PyResult {
            let zelf = zelf.as_object();
            let list = args.list;
            let mut permutations: Vec<PyObjectRef> = Vec::new();
            extend_with(&mut permutations, &list, vm)?;
            let len = list.length(vm)? as isize;
            for i in 0..len {
                vm.check_signals()?;
                let now = list.length(vm)? as isize;
                let count = if i < now - 1 { now - 1 } else { now - 2 };
                for j in 0..count.max(0) {
                    // the reference calls its own method, subclass overrides included
                    zelf.get_attr("swapAdiacentElements", vm)?
                        .call((list.clone(), integer(j as i64, vm)), vm)?;
                    extend_with(&mut permutations, &list, vm)?;
                }
            }
            let now = list.length(vm)? as isize;
            zelf.get_attr("swapAdiacentElements", vm)?
                .call((list.clone(), integer((now - 2) as i64, vm)), vm)?;
            Ok(vm.ctx.new_list(permutations).into())
        }

        #[pymethod(name = "swapAdiacentElements")]
        fn swap_adiacent_elements(
            _zelf: &Py<Self>,
            args: SwapArgs,
            vm: &VirtualMachine,
        ) -> PyResult<()> {
            swap_adiacent(&args.list, &args.n, vm)
        }
    }

    #[pyattr]
    #[pyclass(name = "_PossibleChoice")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct PossibleChoice;

    impl Constructor for PossibleChoice {
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: FuncArgs, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self)
        }
    }

    impl Initializer for PossibleChoice {
        type Args = ObjectProbabilityArgs;

        fn init(
            zelf: PyRef<Self>,
            args: ObjectProbabilityArgs,
            vm: &VirtualMachine,
        ) -> PyResult<()> {
            let zelf = zelf.as_object();
            zelf.set_attr("object", args.object, vm)?;
            zelf.set_attr("probability", args.probability, vm)?;
            zelf.set_attr("mark", vm.ctx.none(), vm)?;
            Ok(())
        }
    }

    #[pyclass(flags(BASETYPE, HAS_DICT, HAS_WEAKREF), with(Constructor, Initializer))]
    impl PossibleChoice {}

    #[pyattr]
    #[pyclass(name = "_MarkAccumulatorEvaluate")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct MarkAccumulatorEvaluate;

    impl Constructor for MarkAccumulatorEvaluate {
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: FuncArgs, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self)
        }
    }

    impl Initializer for MarkAccumulatorEvaluate {
        type Args = EvaluateArgs;

        fn init(zelf: PyRef<Self>, args: EvaluateArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            // the reference floats its factor here, where _MarkAccumulator does not
            let floated = vm
                .ctx
                .types
                .float_type
                .as_object()
                .call((args.factor,), vm)?;
            zelf.set_attr("t", args.t, vm)?;
            zelf.set_attr("factor", floated, vm)?;
            zelf.set_attr("value", integer(0, vm), vm)?;
            Ok(())
        }
    }

    impl Callable for MarkAccumulatorEvaluate {
        type Args = PossibleChoiceArgs;

        fn call(zelf: &Py<Self>, args: PossibleChoiceArgs, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            // the starting value is captured before the probability evaluates — the left operand
            // loads first, whatever the assignment's spelling lowers to
            let captured = zelf.get_attr("value", vm)?;
            let t = zelf.get_attr("t", vm)?;
            let probability = args
                .possible_choice
                .get_attr("probability", vm)?
                .call((t,), vm)?;
            accumulate_mark(zelf, &args.possible_choice, captured, probability, vm)?;
            Ok(args.possible_choice)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable)
    )]
    impl MarkAccumulatorEvaluate {}

    #[pyattr]
    #[pyclass(name = "_MarkAccumulator")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct MarkAccumulator;

    impl Constructor for MarkAccumulator {
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: FuncArgs, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self)
        }
    }

    impl Initializer for MarkAccumulator {
        type Args = FactorArgs;

        fn init(zelf: PyRef<Self>, args: FactorArgs, vm: &VirtualMachine) -> PyResult<()> {
            let zelf = zelf.as_object();
            zelf.set_attr("factor", args.factor, vm)?;
            zelf.set_attr("value", integer(0, vm), vm)?;
            Ok(())
        }
    }

    impl Callable for MarkAccumulator {
        type Args = PossibleChoiceArgs;

        fn call(zelf: &Py<Self>, args: PossibleChoiceArgs, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            // the starting value is captured first; the probability divides raw, never called
            let captured = zelf.get_attr("value", vm)?;
            let probability = args.possible_choice.get_attr("probability", vm)?;
            accumulate_mark(zelf, &args.possible_choice, captured, probability, vm)?;
            Ok(args.possible_choice)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable)
    )]
    impl MarkAccumulator {}

    /// The reference's non-tuple pair error: an unsubstituted message whose traceback slot holds
    /// `repr(pair)`.
    fn pair_type_error(
        pair: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> rustpython_vm::builtins::PyBaseExceptionRef {
        let error: PyObjectRef = vm
            .new_value_error("pair (object, probability) expected. got %s".to_owned())
            .into();
        let repr: PyObjectRef = match pair.repr(vm) {
            Ok(repr) => repr.into(),
            // repr itself failed: that error is the one the reference's raise produced
            Err(error) => return error,
        };
        let raised = match error
            .get_attr("with_traceback", vm)
            .and_then(|method| method.call((repr,), vm))
        {
            Ok(raised) => raised,
            Err(error) => return error,
        };
        match raised.downcast::<PyBaseException>() {
            Ok(exception) => exception,
            Err(_not_exception) => {
                vm.new_type_error("with_traceback must return the exception".to_owned())
            }
        }
    }

    /// The reference's positional-or-keyword head argument — `pair0` for Choice, `pair` for
    /// StaticChoice — with Python's own errors for the missing, the extra, and the doubled.
    fn head_and_rest(
        args: &FuncArgs,
        name: &'static str,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, Vec<PyObjectRef>)> {
        for key in args.kwargs.keys() {
            if key != name {
                return Err(vm.new_type_error(format!(
                    "__init__() got an unexpected keyword argument '{}'",
                    key
                )));
            }
        }
        let named = args.kwargs.get(name).cloned();
        let head = match (named, args.args.first().cloned()) {
            (Some(_), Some(_)) => {
                return Err(vm.new_type_error(format!(
                    "__init__() got multiple values for argument '{}'",
                    name
                )));
            }
            (Some(named), None) => named,
            (None, Some(head)) => head,
            (None, None) => {
                return Err(vm.new_type_error(format!(
                    "__init__() missing 1 required positional argument: '{}'",
                    name
                )));
            }
        };
        Ok((head, args.args.iter().skip(1).cloned().collect()))
    }

    fn build_choice_set(
        pairs: Vec<PyObjectRef>,
        wrap_probability: bool,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        let class = own_module(vm)?.get_attr("_PossibleChoice", vm)?;
        let maker = if wrap_probability {
            Some(module("athenaCL.libATH.omde.functional", vm)?.get_attr("make_function", vm)?)
        } else {
            None
        };
        let mut set = Vec::new();
        for item in pairs {
            let (object, probability) = unpack_pair(&item, vm)?;
            let probability = match &maker {
                Some(maker) => maker.call((probability,), vm)?,
                None => probability,
            };
            set.push(class.call((object, probability), vm)?);
        }
        Ok(vm.ctx.new_list(set).into())
    }

    /// The set's probabilities as the reference reads them: called for `Choice`, raw for
    /// `StaticChoice`, folded by addition with `reduce`'s empty-iterable error.
    fn probability_sum(
        set: &PyObjectRef,
        evaluate: bool,
        t: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let mut probabilities = Vec::new();
        for choice in set.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            vm.check_signals()?;
            let choice = choice?;
            let probability = choice.get_attr("probability", vm)?;
            let probability = if evaluate {
                probability.call((t.clone(),), vm)?
            } else {
                probability
            };
            probabilities.push(probability);
        }
        fold_add(probabilities, vm)
    }

    /// The mark pass: `_MarkAccumulatorEvaluate(t, sum)` or `_MarkAccumulator(sum)` over the set,
    /// producing the reference's reassigned `self.set`.
    fn mark_pass(zelf: &PyObject, accumulator: &PyObjectRef, vm: &VirtualMachine) -> PyResult<()> {
        let set = zelf.get_attr("set", vm)?;
        let mut marked = Vec::new();
        for choice in set.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            vm.check_signals()?;
            marked.push(accumulator.call((choice?,), vm)?);
        }
        let marked: PyObjectRef = vm.ctx.new_list(marked).into();
        zelf.set_attr("set", marked, vm)
    }

    /// The scan both choice classes share: the first mark the draw does not exceed.
    fn scan_marks(zelf: &PyObject, draw: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let set = zelf.get_attr("set", vm)?;
        for choice in set.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            vm.check_signals()?;
            let choice = choice?;
            let mark = choice.get_attr("mark", vm)?;
            if draw.rich_compare_bool(&mark, PyComparisonOp::Le, vm)? {
                return choice.get_attr("object", vm);
            }
        }
        Err(vm.new_runtime_error("".to_owned()))
    }

    #[pyattr]
    #[pyclass(name = "Choice", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Choice {
        base: Function,
    }

    omde_new!(Choice, Function(FunctionModel));
    base_number!(Choice, Function);

    impl Initializer for Choice {
        type Args = FuncArgs;

        fn init(zelf: PyRef<Self>, args: FuncArgs, vm: &VirtualMachine) -> PyResult<()> {
            let (pair0, pairs) = head_and_rest(&args, "pair0", vm)?;
            for pair in &pairs {
                if !pair.class().is(vm.ctx.types.tuple_type) {
                    return Err(pair_type_error(pair, vm));
                }
            }
            let set = build_choice_set(std::iter::once(pair0).chain(pairs).collect(), true, vm)?;
            zelf.as_object().set_attr("set", set, vm)?;
            Ok(())
        }
    }

    impl Callable for Choice {
        type Args = TimeArgs;

        fn call(zelf: &Py<Self>, args: TimeArgs, vm: &VirtualMachine) -> PyResult {
            let zelf = zelf.as_object();
            let sum = {
                let set = zelf.get_attr("set", vm)?;
                probability_sum(&set, true, &args.t, vm)?
            };
            let accumulator = own_module(vm)?
                .get_attr("_MarkAccumulatorEvaluate", vm)?
                .call((args.t.clone(), sum), vm)?;
            mark_pass(zelf, &accumulator, vm)?;
            // the draw comes after every evaluation
            let draw = omde_rand(vm)?.get_attr("random", vm)?.call((), vm)?;
            scan_marks(zelf, &draw, vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl Choice {}

    #[pyattr]
    #[pyclass(name = "StaticChoice", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct StaticChoice {
        base: Function,
    }

    omde_new!(StaticChoice, Function(FunctionModel));
    base_number!(StaticChoice, Function);

    impl Initializer for StaticChoice {
        type Args = FuncArgs;

        fn init(zelf: PyRef<Self>, args: FuncArgs, vm: &VirtualMachine) -> PyResult<()> {
            let (pair, pairs) = head_and_rest(&args, "pair", vm)?;
            let set = build_choice_set(std::iter::once(pair).chain(pairs).collect(), false, vm)?;
            let zelf = zelf.as_object();
            zelf.set_attr("set", set, vm)?;
            // the marks are fixed at construction, over the raw probabilities
            let set = zelf.get_attr("set", vm)?;
            let none = vm.ctx.none();
            let sum = probability_sum(&set, false, &none, vm)?;
            let accumulator = own_module(vm)?
                .get_attr("_MarkAccumulator", vm)?
                .call((sum,), vm)?;
            mark_pass(zelf, &accumulator, vm)?;
            Ok(())
        }
    }

    impl Callable for StaticChoice {
        type Args = TimeArgs;

        fn call(zelf: &Py<Self>, _args: TimeArgs, vm: &VirtualMachine) -> PyResult {
            let draw = omde_rand(vm)?.get_attr("random", vm)?.call((), vm)?;
            scan_marks(zelf.as_object(), &draw, vm)
        }
    }

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl StaticChoice {}
}
