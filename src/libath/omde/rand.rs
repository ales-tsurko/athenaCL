//! Native OMDE random distributions, with the Python reference in `_pyref/rand.py`.
//!
//! Stage two completes the planned RNG backend migration: `UniformRNG()` now returns the
//! interpreter's shared ChaCha12 `textures` stream, seeded by `TMsd`. This changes sequences for
//! its consumers, including the still-Python `miscellaneous.Range` and `IntRange`. Module-level
//! `random`/`choice` remain aliases of the `parameters` stream seeded by `TPsd`; Gauss's Box-Muller
//! pairs intentionally use that stream. Existing Gauss spares survive either stream's reseeding.
//!
//! The native classes keep their Python instance dictionaries. Distribution parameters, helper
//! objects, and RNG references remain Python objects: numeric protocols, subclass overrides,
//! reentrant callbacks, and assignment order survive without holding Rust locks across Python.
//! Ordinary copy reduction handles subclasses, slots, cycles, and aliases. Deepcopy snapshots a
//! textures stream once per copied graph; shallow copies share it. Gauss copies its cached spare
//! but continues drawing new pairs from the module-level parameters alias, as before.
//!
//! Preserved quirks include Weibull's Generator base with a time-taking call, the exponential
//! rejection at `1e-7`, Cauchy's rejection at `0.5`, and Lehmer's clock/sleep reseeding for zero or
//! its modulus. Helpers and their attributes remain available. The only interface narrowing is
//! `UniformRNG()` returning the bridge stream's methods rather than the full `random.Random` API.
//! No athenaCL consumer requires the omitted methods. Distribution arithmetic and errors retain
//! Python semantics; only the underlying UniformRNG sequence deliberately changes.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.omde.rand")]
pub(super) mod _inner {
    use rustpython_vm::{
        builtins::{PyModule, PyType},
        function::{FuncArgs, IntoFuncArgs, OptionalArg},
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
        module("athenaCL.libATH.omde.rand", vm)
    }

    /// Capture the same bound aliases as the reference, once per interpreter.
    pub(crate) fn module_exec(vm: &VirtualMachine, module: &Py<PyModule>) -> PyResult<()> {
        vm.import("athenaCL.libATH.omde._functional", 0)?;
        __module_exec(vm, module);
        let bridge = self::module("athenaCL.libATH.rngBridge", vm)?;
        module.set_attr("_the_same", bridge.get_attr("textures", vm)?, vm)?;
        let parameters = bridge.get_attr("parameters", vm)?;
        for name in ["random", "choice"] {
            module.set_attr(name, parameters.get_attr(name, vm)?, vm)?;
        }
        module.set_attr("UniformRNG", module.get_attr("_AlwaysTheSame", vm)?, vm)?;
        for name in ["math", "time"] {
            module.set_attr(name, vm.import(name, 0)?, vm)?;
        }
        Ok(())
    }

    #[pyfunction(name = "_AlwaysTheSame")]
    fn always_the_same(vm: &VirtualMachine) -> PyResult {
        own_module(vm)?.get_attr("_the_same", vm)
    }

    fn construct(name: &'static str, vm: &VirtualMachine) -> PyResult {
        own_module(vm)?.get_attr(name, vm)?.call((), vm)
    }

    fn float(value: f64, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_float(value).into()
    }

    /// Math calls use RustPython's checked operations, including log's bigint handling and domain
    /// error messages. Arithmetic outside these calls keeps its original Python operands.
    fn math(name: &'static str, value: PyObjectRef, vm: &VirtualMachine) -> PyResult {
        own_module(vm)?
            .get_attr("math", vm)?
            .get_attr(name, vm)?
            .call((value,), vm)
    }

    fn compare(
        value: &PyObject,
        bound: f64,
        op: PyComparisonOp,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        value.rich_compare_bool(&float(bound, vm), op, vm)
    }

    /// Replace a Python local only after evaluating the next draw. Its previous value can have a
    /// finalizer, so dropping it before the draw changes observable callback order.
    fn resample_until(
        value: &mut PyObjectRef,
        mut draw: impl FnMut() -> PyResult,
        mut accept: impl FnMut(&PyObjectRef) -> PyResult<bool>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        loop {
            vm.check_signals()?;
            *value = draw()?;
            if accept(value)? {
                return Ok(());
            }
        }
    }

    fn sample_until(
        draw: impl FnMut() -> PyResult,
        accept: impl FnMut(&PyObjectRef) -> PyResult<bool>,
        vm: &VirtualMachine,
    ) -> PyResult {
        let mut value = vm.ctx.none();
        resample_until(&mut value, draw, accept, vm)?;
        Ok(value)
    }

    fn draw(
        zelf: &PyObject,
        field: &'static str,
        args: impl IntoFuncArgs,
        vm: &VirtualMachine,
    ) -> PyResult {
        zelf.as_object()
            .get_attr(field, vm)?
            .get_attr("random", vm)?
            .call(args, vm)
    }

    fn parameter(
        zelf: &PyObject,
        field: &'static str,
        t: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        zelf.as_object().get_attr(field, vm)?.call((t.clone(),), vm)
    }

    fn parameter_pair(
        zelf: &PyObject,
        t: &PyObjectRef,
        names: [&'static str; 2],
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
        let [first, second] = names;
        let a = parameter(zelf, first, t, vm)?;
        let b = parameter(zelf, second, t, vm)?;
        Ok((a, b))
    }

    fn upper_half(zelf: &PyObject, vm: &VirtualMachine) -> PyResult<bool> {
        compare(
            draw(zelf, "uniformRNG", (), vm)?.as_object(),
            0.5,
            PyComparisonOp::Gt,
            vm,
        )
    }

    fn set_parameter(
        zelf: &PyObject,
        name: &'static str,
        value: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let maker = module("athenaCL.libATH.omde.functional", vm)?.get_attr("make_function", vm)?;
        zelf.as_object()
            .set_attr(name, maker.call((value,), vm)?, vm)
    }

    fn set_helper(
        zelf: &PyObject,
        field: &'static str,
        class: &'static str,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        zelf.as_object().set_attr(field, construct(class, vm)?, vm)
    }

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

    #[derive(FromArgs)]
    pub(crate) struct TimeArgs {
        #[pyarg(any)]
        t: PyObjectRef,
    }

    #[derive(FromArgs)]
    pub(crate) struct RateArgs {
        #[pyarg(any, optional)]
        lambd: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    pub(crate) struct GaussArgs {
        #[pyarg(any, optional)]
        mu: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        sigma: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    pub(crate) struct CauchyArgs {
        #[pyarg(any, optional)]
        alpha: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        mu: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    pub(crate) struct ShapeArgs {
        #[pyarg(any, optional)]
        alpha: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        beta: OptionalArg<PyObjectRef>,
    }

    /// Constructors allocate stateless payloads; typed initializers own validation and mutation.
    /// Their arguments stay alive until initialization ends, including during callback reentry.
    trait InitArgs {
        fn initialize(&self, zelf: &PyObject, kind: Kind, vm: &VirtualMachine) -> PyResult<()>;
    }

    impl InitArgs for () {
        fn initialize(&self, zelf: &PyObject, _kind: Kind, vm: &VirtualMachine) -> PyResult<()> {
            set_helper(zelf, "rng", "UniformRNG", vm)
        }
    }

    impl InitArgs for RateArgs {
        fn initialize(&self, zelf: &PyObject, kind: Kind, vm: &VirtualMachine) -> PyResult<()> {
            set_parameter(zelf, "lambd", supplied(&self.lambd, 1.0, vm), vm)?;
            set_helper(zelf, "expovariateRNG", "_ExpovariateRNG", vm)?;
            if matches!(kind, Kind::Bilateral) {
                set_helper(zelf, "uniformRNG", "UniformRNG", vm)?;
            }
            Ok(())
        }
    }

    impl InitArgs for GaussArgs {
        fn initialize(&self, zelf: &PyObject, _kind: Kind, vm: &VirtualMachine) -> PyResult<()> {
            set_parameter(zelf, "mu", supplied(&self.mu, 0.5, vm), vm)?;
            set_parameter(zelf, "sigma", supplied(&self.sigma, 0.1, vm), vm)?;
            set_helper(zelf, "gaussRNG", "_GaussRNG", vm)
        }
    }

    impl InitArgs for CauchyArgs {
        fn initialize(&self, zelf: &PyObject, _kind: Kind, vm: &VirtualMachine) -> PyResult<()> {
            set_parameter(zelf, "alpha", supplied(&self.alpha, 0.1, vm), vm)?;
            set_parameter(zelf, "mu", supplied(&self.mu, 0.5, vm), vm)?;
            set_helper(zelf, "uniformRNG", "UniformRNG", vm)
        }
    }

    impl InitArgs for ShapeArgs {
        fn initialize(&self, zelf: &PyObject, kind: Kind, vm: &VirtualMachine) -> PyResult<()> {
            let (alpha, beta) = if matches!(kind, Kind::Beta) {
                set_helper(zelf, "uniformRNG", "UniformRNG", vm)?;
                set_helper(zelf, "betavariateRNG", "_BetavariateRNG", vm)?;
                (0.1, 0.1)
            } else {
                (0.5, 2.0)
            };
            set_parameter(zelf, "alpha", supplied(&self.alpha, alpha, vm), vm)?;
            set_parameter(zelf, "beta", supplied(&self.beta, beta, vm), vm)?;
            if matches!(kind, Kind::Weibull) {
                set_helper(zelf, "weibullvariateRNG", "_WeibullvariateRNG", vm)?;
            }
            Ok(())
        }
    }

    #[derive(Clone, Copy)]
    enum Kind {
        Uniform,
        Linear,
        InverseLinear,
        Triangular,
        InverseTriangular,
        Exponential,
        InverseExponential,
        Bilateral,
        Gauss,
        Cauchy,
        Beta,
        Weibull,
    }

    fn triangular(zelf: &PyObject, inverse: bool, vm: &VirtualMachine) -> PyResult {
        let lower_op = if inverse {
            PyComparisonOp::Lt
        } else {
            PyComparisonOp::Gt
        };
        let upper_op = if inverse {
            PyComparisonOp::Gt
        } else {
            PyComparisonOp::Lt
        };
        let half_draw = || {
            vm._truediv(
                draw(zelf, "rng", (), vm)?.as_object(),
                vm.ctx.new_int(2).as_object(),
            )
        };
        vm.check_signals()?;
        let mut a = draw(zelf, "rng", (), vm)?;
        let mut b = half_draw()?;
        loop {
            if (compare(&a, 0.5, PyComparisonOp::Lt, vm)?
                && a.rich_compare_bool(&b, lower_op, vm)?)
                || (compare(&a, 0.5, PyComparisonOp::Ge, vm)?
                    && vm
                        ._sub(&a, &float(0.5, vm))?
                        .rich_compare_bool(&b, upper_op, vm)?)
            {
                return Ok(a);
            }
            vm.check_signals()?;
            // These are two assignments in Python: release old a before drawing new b.
            a = draw(zelf, "rng", (), vm)?;
            b = half_draw()?;
        }
    }

    fn generator(zelf: &PyObject, kind: Kind, vm: &VirtualMachine) -> PyResult {
        match kind {
            Kind::Triangular | Kind::InverseTriangular => {
                triangular(zelf, matches!(kind, Kind::InverseTriangular), vm)
            }
            Kind::Linear | Kind::InverseLinear => {
                let a = draw(zelf, "rng", (), vm)?;
                let b = draw(zelf, "rng", (), vm)?;
                let op = if matches!(kind, Kind::Linear) {
                    PyComparisonOp::Lt
                } else {
                    PyComparisonOp::Gt
                };
                // min/max retain the first object on ties and unordered comparisons.
                if b.rich_compare_bool(&a, op, vm)? {
                    Ok(b)
                } else {
                    Ok(a)
                }
            }
            _ => draw(zelf, "rng", (), vm),
        }
    }

    fn invert_sample(value: PyObjectRef, invert: bool, vm: &VirtualMachine) -> PyResult {
        if invert {
            vm._sub(&float(1.0, vm), &value)
        } else {
            Ok(value)
        }
    }

    fn exponential(zelf: &PyObject, t: &PyObjectRef, kind: Kind, vm: &VirtualMachine) -> PyResult {
        let rate = parameter(zelf, "lambd", t, vm)?;
        let inverse = matches!(kind, Kind::InverseExponential);
        let value = sample_until(
            || {
                let value = draw(zelf, "expovariateRNG", (rate.clone(),), vm)?;
                invert_sample(value, inverse, vm)
            },
            |value| {
                compare(
                    value,
                    if inverse { 0.0 } else { 1.0 },
                    if inverse {
                        PyComparisonOp::Gt
                    } else {
                        PyComparisonOp::Lt
                    },
                    vm,
                )
            },
            vm,
        )?;
        if matches!(kind, Kind::Bilateral) {
            let upper = upper_half(zelf, vm)?;
            let half = vm._truediv(&value, &float(2.0, vm))?;
            if upper {
                vm._add(&float(0.5, vm), &half)
            } else {
                vm._sub(&float(0.5, vm), &half)
            }
        } else {
            Ok(value)
        }
    }

    fn bounded_pair(zelf: &PyObject, t: &PyObjectRef, kind: Kind, vm: &VirtualMachine) -> PyResult {
        let (first, second, helper) = if matches!(kind, Kind::Gauss) {
            ("mu", "sigma", "gaussRNG")
        } else {
            ("alpha", "beta", "weibullvariateRNG")
        };
        let (a, b) = parameter_pair(zelf, t, [first, second], vm)?;
        sample_until(
            || draw(zelf, helper, (a.clone(), b.clone()), vm),
            |value| {
                Ok(compare(value, 0.0, PyComparisonOp::Ge, vm)?
                    && compare(value, 1.0, PyComparisonOp::Le, vm)?)
            },
            vm,
        )
    }

    fn cauchy(zelf: &PyObject, t: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        // Call order differs from constructor order: mu, then alpha.
        let (mu, alpha) = parameter_pair(zelf, t, ["mu", "alpha"], vm)?;
        // x remains a local across both loops, even when the shaped value is rejected.
        let mut x = vm.ctx.none();
        sample_until(
            || {
                resample_until(
                    &mut x,
                    || draw(zelf, "uniformRNG", (), vm),
                    |x| compare(x, 0.5, PyComparisonOp::Ne, vm),
                    vm,
                )?;
                let tangent = math("tan", vm._mul(&x, &float(std::f64::consts::PI, vm))?, vm)?;
                let value = vm._mul(&alpha, &tangent)?;
                vm._add(&value, &mu)
            },
            |value| {
                Ok(compare(value, 1.0, PyComparisonOp::Le, vm)?
                    && value.rich_compare_bool(
                        vm.ctx.new_int(0).as_object(),
                        PyComparisonOp::Ge,
                        vm,
                    )?)
            },
            vm,
        )
    }

    fn beta(zelf: &PyObject, t: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let (alpha, beta) = parameter_pair(zelf, t, ["alpha", "beta"], vm)?;
        // This sign draw precedes both exponentials; the bilateral distribution does the reverse.
        let invert = upper_half(zelf, vm)?;
        // The parameter locals stay alive through inversion, as in the Python frame.
        let value = draw(zelf, "betavariateRNG", (alpha.clone(), beta.clone()), vm)?;
        invert_sample(value, invert, vm)
    }

    fn function(zelf: &PyObject, args: &TimeArgs, kind: Kind, vm: &VirtualMachine) -> PyResult {
        match kind {
            Kind::Exponential | Kind::InverseExponential | Kind::Bilateral => {
                exponential(zelf, &args.t, kind, vm)
            }
            Kind::Gauss | Kind::Weibull => bounded_pair(zelf, &args.t, kind, vm),
            Kind::Cauchy => cauchy(zelf, &args.t, vm),
            _ => beta(zelf, &args.t, vm),
        }
    }

    macro_rules! distribution_impl {
        ($class:ident, $base:ident, $base_value:expr, $args:ty, $kind:ident) => {
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
            impl Initializer for $class {
                type Args = $args;

                fn init(zelf: PyRef<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult<()> {
                    args.initialize(zelf.as_object(), Kind::$kind, vm)
                }
            }
            impl AsNumber for $class {
                fn as_number() -> &'static PyNumberMethods {
                    $base::as_number()
                }
            }
        };
    }

    macro_rules! generator_call {
        ($class:ident, $kind:ident) => {
            impl Callable for $class {
                type Args = ();

                fn call(zelf: &Py<Self>, _args: (), vm: &VirtualMachine) -> PyResult {
                    generator(zelf.as_object(), Kind::$kind, vm)
                }
            }
        };
    }

    macro_rules! function_call {
        ($class:ident, $kind:ident) => {
            impl Callable for $class {
                type Args = TimeArgs;

                fn call(zelf: &Py<Self>, args: TimeArgs, vm: &VirtualMachine) -> PyResult {
                    function(zelf.as_object(), &args, Kind::$kind, vm)
                }
            }
        };
    }

    #[pyattr]
    #[pyclass(name = "UniformRandom", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct UniformRandom {
        base: Generator,
    }

    distribution_impl!(UniformRandom, Generator, Generator, (), Uniform);
    generator_call!(UniformRandom, Uniform);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl UniformRandom {}

    #[pyattr]
    #[pyclass(name = "LinearRandom", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct LinearRandom {
        base: Generator,
    }

    distribution_impl!(LinearRandom, Generator, Generator, (), Linear);
    generator_call!(LinearRandom, Linear);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl LinearRandom {}

    #[pyattr]
    #[pyclass(name = "InverseLinearRandom", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct InverseLinearRandom {
        base: Generator,
    }

    distribution_impl!(InverseLinearRandom, Generator, Generator, (), InverseLinear);
    generator_call!(InverseLinearRandom, InverseLinear);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl InverseLinearRandom {}

    #[pyattr]
    #[pyclass(name = "TriangularRandom", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct TriangularRandom {
        base: Generator,
    }

    distribution_impl!(TriangularRandom, Generator, Generator, (), Triangular);
    generator_call!(TriangularRandom, Triangular);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl TriangularRandom {}

    #[pyattr]
    #[pyclass(name = "InverseTriangularRandom", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct InverseTriangularRandom {
        base: Generator,
    }

    distribution_impl!(
        InverseTriangularRandom,
        Generator,
        Generator,
        (),
        InverseTriangular
    );
    generator_call!(InverseTriangularRandom, InverseTriangular);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl InverseTriangularRandom {}

    #[pyattr]
    #[pyclass(name = "ExponentialRandom", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct ExponentialRandom {
        base: Function,
    }

    distribution_impl!(
        ExponentialRandom,
        Function,
        Function(FunctionModel),
        RateArgs,
        Exponential
    );
    function_call!(ExponentialRandom, Exponential);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl ExponentialRandom {}

    #[pyattr]
    #[pyclass(name = "InverseExponentialRandom", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct InverseExponentialRandom {
        base: Function,
    }

    distribution_impl!(
        InverseExponentialRandom,
        Function,
        Function(FunctionModel),
        RateArgs,
        InverseExponential
    );
    function_call!(InverseExponentialRandom, InverseExponential);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl InverseExponentialRandom {}

    #[pyattr]
    #[pyclass(name = "BilateralExponentialRandom", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct BilateralExponentialRandom {
        base: Function,
    }

    distribution_impl!(
        BilateralExponentialRandom,
        Function,
        Function(FunctionModel),
        RateArgs,
        Bilateral
    );
    function_call!(BilateralExponentialRandom, Bilateral);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl BilateralExponentialRandom {}

    #[pyattr]
    #[pyclass(name = "GaussRandom", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct GaussRandom {
        base: Function,
    }

    distribution_impl!(
        GaussRandom,
        Function,
        Function(FunctionModel),
        GaussArgs,
        Gauss
    );
    function_call!(GaussRandom, Gauss);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl GaussRandom {}

    #[pyattr]
    #[pyclass(name = "CauchyRandom", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct CauchyRandom {
        base: Function,
    }

    distribution_impl!(
        CauchyRandom,
        Function,
        Function(FunctionModel),
        CauchyArgs,
        Cauchy
    );
    function_call!(CauchyRandom, Cauchy);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl CauchyRandom {}

    #[pyattr]
    #[pyclass(name = "BetaRandom", base = Function)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct BetaRandom {
        base: Function,
    }

    distribution_impl!(
        BetaRandom,
        Function,
        Function(FunctionModel),
        ShapeArgs,
        Beta
    );
    function_call!(BetaRandom, Beta);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl BetaRandom {}

    #[pyattr]
    #[pyclass(name = "WeibullRandom", base = Generator)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct WeibullRandom {
        base: Generator,
    }

    distribution_impl!(WeibullRandom, Generator, Generator, ShapeArgs, Weibull);
    function_call!(WeibullRandom, Weibull);

    #[pyclass(
        flags(BASETYPE, HAS_DICT, HAS_WEAKREF),
        with(Constructor, Initializer, Callable, AsNumber)
    )]
    impl WeibullRandom {}

    /// Helper constructors leave Python subclass signatures to their initializers too.
    macro_rules! helper_new {
        ($class:ident) => {
            impl Constructor for $class {
                type Args = FuncArgs;

                fn py_new(
                    _cls: &Py<PyType>,
                    _args: FuncArgs,
                    _vm: &VirtualMachine,
                ) -> PyResult<Self> {
                    Ok(Self)
                }
            }
        };
    }

    macro_rules! helper_init {
        ($class:ident, $field:literal, $source:literal) => {
            helper_new!($class);
            impl Initializer for $class {
                type Args = ();

                fn init(zelf: PyRef<Self>, _args: (), vm: &VirtualMachine) -> PyResult<()> {
                    set_helper(zelf.as_object(), $field, $source, vm)
                }
            }
        };
    }

    #[derive(FromArgs)]
    struct RateDraw {
        #[pyarg(any)]
        lambd: PyObjectRef,
    }

    #[derive(FromArgs)]
    struct GaussDraw {
        #[pyarg(any)]
        mu: PyObjectRef,
        #[pyarg(any)]
        sigma: PyObjectRef,
    }

    #[derive(FromArgs)]
    struct ShapeDraw {
        #[pyarg(any)]
        alpha: PyObjectRef,
        #[pyarg(any)]
        beta: PyObjectRef,
    }

    #[pyattr]
    #[pyclass(name = "_ExpovariateRNG")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct Expovariate;
    helper_init!(Expovariate, "uniformRNG", "UniformRNG");

    #[pyclass(flags(BASETYPE, HAS_DICT, HAS_WEAKREF), with(Constructor, Initializer))]
    impl Expovariate {
        #[pymethod]
        fn random(zelf: &Py<Self>, args: RateDraw, vm: &VirtualMachine) -> PyResult {
            let u = sample_until(
                || draw(zelf.as_object(), "uniformRNG", (), vm),
                |u| Ok(!compare(u, 1e-7, PyComparisonOp::Le, vm)?),
                vm,
            )?;
            let numerator = vm._neg(math("log", u.clone(), vm)?.as_object())?;
            vm._truediv(&numerator, &args.lambd)
        }
    }

    #[pyattr]
    #[pyclass(name = "_GaussRNG")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct Gauss;
    helper_new!(Gauss);

    impl Initializer for Gauss {
        type Args = ();

        fn init(zelf: PyRef<Self>, _args: (), vm: &VirtualMachine) -> PyResult<()> {
            zelf.as_object().set_attr("next", vm.ctx.none(), vm)
        }
    }

    #[pyclass(flags(BASETYPE, HAS_DICT, HAS_WEAKREF), with(Constructor, Initializer))]
    impl Gauss {
        #[pymethod]
        fn random(zelf: &Py<Self>, args: GaussDraw, vm: &VirtualMachine) -> PyResult {
            let mut z = zelf.as_object().get_attr("next", vm)?;
            zelf.as_object().set_attr("next", vm.ctx.none(), vm)?;
            // Python keeps both pair locals alive through the final mu + z * sigma, including while
            // callbacks can inspect or mutate the cached spare.
            let draw_pair = if vm.is_none(&z) {
                let x2pi = {
                    let x = own_module(vm)?.get_attr("random", vm)?.call((), vm)?;
                    let radians = vm._mul(&x, &float(std::f64::consts::PI, vm))?;
                    vm._mul(&radians, vm.ctx.new_int(2).as_object())?
                };
                let g2rad = {
                    let y = own_module(vm)?.get_attr("random", vm)?.call((), vm)?;
                    let log = math("log", vm._sub(&float(1.0, vm), &y)?, vm)?;
                    math("sqrt", vm._mul(&float(-2.0, vm), &log)?, vm)?
                };
                z = vm._mul(math("cos", x2pi.clone(), vm)?.as_object(), &g2rad)?;
                let spare = vm._mul(math("sin", x2pi.clone(), vm)?.as_object(), &g2rad)?;
                zelf.as_object().set_attr("next", spare, vm)?;
                Some((x2pi, g2rad))
            } else {
                None
            };
            // Store the unscaled spare before arithmetic that can fail or reenter this object.
            let scaled = vm._mul(&z, &args.sigma)?;
            let result = vm._add(&args.mu, &scaled)?;
            drop(draw_pair);
            Ok(result)
        }
    }

    #[pyattr]
    #[pyclass(name = "_BetavariateRNG")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct Betavariate;
    helper_init!(Betavariate, "expovariateRNG", "_ExpovariateRNG");

    #[pyclass(flags(BASETYPE, HAS_DICT, HAS_WEAKREF), with(Constructor, Initializer))]
    impl Betavariate {
        #[pymethod]
        fn random(zelf: &Py<Self>, args: ShapeDraw, vm: &VirtualMachine) -> PyResult {
            let y = draw(
                zelf.as_object(),
                "expovariateRNG",
                (args.alpha.clone(),),
                vm,
            )?;
            // Capture the second method before evaluating its argument, as Python does.
            let second = zelf
                .as_object()
                .get_attr("expovariateRNG", vm)?
                .get_attr("random", vm)?;
            let rate = vm._truediv(&float(1.0, vm), &args.beta)?;
            let z = second.call((rate,), vm)?;
            vm._truediv(&z, vm._add(&y, &z)?.as_object())
        }
    }

    #[pyattr]
    #[pyclass(name = "_WeibullvariateRNG")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct Weibullvariate;
    helper_init!(Weibullvariate, "uniformRNG", "UniformRNG");

    #[pyclass(flags(BASETYPE, HAS_DICT, HAS_WEAKREF), with(Constructor, Initializer))]
    impl Weibullvariate {
        #[pymethod]
        fn random(zelf: &Py<Self>, args: ShapeDraw, vm: &VirtualMachine) -> PyResult {
            let u = draw(zelf.as_object(), "uniformRNG", (), vm)?;
            let base = vm._neg(math("log", u.clone(), vm)?.as_object())?;
            let exponent = vm._truediv(&float(1.0, vm), &args.beta)?;
            let powered = vm._pow(&base, &exponent, &vm.ctx.none())?;
            vm._mul(&args.alpha, &powered)
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct LehmerArgs {
        #[pyarg(any, optional)]
        seed: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional, name = "mod")]
        modulus: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional, name = "mul")]
        multiplier: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        incr: OptionalArg<PyObjectRef>,
    }

    #[derive(FromArgs)]
    struct SeedArgs {
        #[pyarg(any, optional)]
        seed: OptionalArg<PyObjectRef>,
    }

    #[pyattr]
    #[pyclass(name = "_LehmerRNG")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct Lehmer;
    helper_new!(Lehmer);

    impl Initializer for Lehmer {
        type Args = LehmerArgs;

        fn init(zelf: PyRef<Self>, args: LehmerArgs, vm: &VirtualMachine) -> PyResult<()> {
            zelf.as_object()
                .set_attr("_mod", supplied(&args.modulus, 2147483647.0, vm), vm)?;
            zelf.as_object()
                .set_attr("_mul", supplied(&args.multiplier, 16807.0, vm), vm)?;
            zelf.as_object().set_attr(
                "_incr",
                args.incr
                    .as_ref()
                    .cloned()
                    .unwrap_or_else(|| vm.ctx.new_int(0).into()),
                vm,
            )?;
            let seed = args
                .seed
                .as_ref()
                .cloned()
                .unwrap_or_else(|| vm.ctx.new_int(0).into());
            zelf.as_object().get_attr("seed", vm)?.call((seed,), vm)?;
            Ok(())
        }
    }

    #[pyclass(flags(BASETYPE, HAS_DICT, HAS_WEAKREF), with(Constructor, Initializer))]
    impl Lehmer {
        #[pymethod]
        fn random(zelf: &Py<Self>, vm: &VirtualMachine) -> PyResult {
            let multiplied = vm._mul(
                zelf.as_object().get_attr("_mul", vm)?.as_object(),
                zelf.as_object().get_attr("_seed", vm)?.as_object(),
            )?;
            let incremented = vm._add(
                &multiplied,
                zelf.as_object().get_attr("_incr", vm)?.as_object(),
            )?;
            let seed = vm._mod(
                &incremented,
                zelf.as_object().get_attr("_mod", vm)?.as_object(),
            )?;
            zelf.as_object().set_attr("_seed", seed, vm)?;
            vm._truediv(
                zelf.as_object().get_attr("_seed", vm)?.as_object(),
                zelf.as_object().get_attr("_mod", vm)?.as_object(),
            )
        }

        #[pymethod]
        fn seed(zelf: &Py<Self>, args: SeedArgs, vm: &VirtualMachine) -> PyResult<()> {
            zelf.as_object().set_attr(
                "_seed",
                args.seed
                    .as_ref()
                    .cloned()
                    .unwrap_or_else(|| vm.ctx.new_int(0).into()),
                vm,
            )?;
            while zelf.as_object().get_attr("_seed", vm)?.rich_compare_bool(
                vm.ctx.new_int(0).as_object(),
                PyComparisonOp::Eq,
                vm,
            )? || zelf.as_object().get_attr("_seed", vm)?.rich_compare_bool(
                zelf.as_object().get_attr("_mod", vm)?.as_object(),
                PyComparisonOp::Eq,
                vm,
            )? {
                vm.check_signals()?;
                own_module(vm)?
                    .get_attr("time", vm)?
                    .get_attr("sleep", vm)?
                    .call((float(0.01, vm),), vm)?;
                let now = own_module(vm)?
                    .get_attr("time", vm)?
                    .get_attr("time", vm)?
                    .call((), vm)?;
                let fraction = vm._mod(&now, vm.ctx.new_int(1).as_object())?;
                let scaled = vm._mul(
                    &fraction,
                    zelf.as_object().get_attr("_mod", vm)?.as_object(),
                )?;
                let seed = vm.ctx.types.int_type.as_object().call((scaled,), vm)?;
                zelf.as_object().set_attr("_seed", seed, vm)?;
            }
            Ok(())
        }
    }
}
