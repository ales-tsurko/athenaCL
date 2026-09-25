//! The `athenaCL.libATH.chaos` module: chaotic maps and Fibonacci utilities, in Rust.
//!
//! Port of `pysrc/athenaCL/libATH/_pyref/chaos.py`, restructured: the maps are plain state structs
//! stepping one point at a time, testable without an interpreter, and the module is a thin boundary
//! keeping the Python names, keyword arguments, and `math` errors. The arithmetic is kept
//! expression for expression, so trajectories come out identical — including where a square beyond
//! float range flows into infinities, which it does under RustPython, whose `pow` returns infinity
//! rather than raising the `OverflowError` the Python code caught. `math.floor` returns an `int`,
//! so the Fibonacci functions return `int`s — the module's own doctests, written for Python 2, say
//! `float` and are wrong.
//!
//! Two narrowings, neither read by anything in athenaCL: the maps keep float state, where Python
//! could keep an int through int arguments and return it on the first step; and the map objects
//! cannot be `copy.deepcopy`'d, which athenaCL never does to them. The successor's exact-precision
//! limit sits at the square of its input, not the input or the result: an int square beyond 128
//! bits raises `OverflowError`, where Python rounded its exact square into float arithmetic.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

/// The chaotic maps and the Fibonacci numbers, as plain functions and state structs.
mod core {
    use super::super::number::{Number, Overflow};

    /// The error `math.pow` raises: a domain the function refuses, or a result beyond float
    /// range.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub(crate) enum PowError {
        /// the function refuses the operands
        Domain,
        /// the result is beyond float range
        Range,
    }

    /// `math.pow`, whose errors the reference met through it: the value, or the refusal CPython's
    /// math raises for a negative base to a fractional exponent, zero to a negative one, or a
    /// result beyond float range.
    pub(crate) fn math_pow(x: f64, y: f64) -> Result<f64, PowError> {
        let result = x.powf(y);
        if x.is_finite() && y.is_finite() && !result.is_finite() {
            if result.is_nan() || x == 0.0 {
                Err(PowError::Domain)
            } else {
                Err(PowError::Range)
            }
        } else {
            Ok(result)
        }
    }

    /// The i-th Fibonacci number by Binet's formula, as the formula's float, floored. The floor is
    /// exact in the boundary's big integer, however far the series grows. The index is the float
    /// the Python arithmetic made of it, which a fractional index never broke.
    pub(crate) fn fibonacci_number(
        golden_upper: f64,
        golden_lower: f64,
        i: f64,
    ) -> Result<f64, PowError> {
        let exponent = i + 1.0;
        let power_upper = math_pow(golden_upper, exponent)?;
        let power_lower = math_pow(golden_lower, exponent)?;
        Ok((power_upper - power_lower) / 5.0f64.sqrt())
    }

    /// The term after `n` in the Fibonacci series, as the formula's float, floored. An int squares
    /// exactly before the float takes over, as the Python expression did; a float squares through
    /// pow, as Python's `**` does — which is not always the same product as a float multiply. An
    /// int square beyond 128 bits raises, where Python rounded its exact square into float
    /// arithmetic: the exact-precision limit sits at the square, not at the input or the result.
    pub(crate) fn fibonacci_successor(n: Number) -> Result<f64, Overflow> {
        let five_squares = match n {
            // an int squares exactly before the float takes over, as the Python expression did; a
            // float squares through pow, as Python's `**` does — which is not always the same
            // product as a float multiply
            Number::Int(value) => 5.0 * (value.checked_mul(value).ok_or(Overflow)? as f64),
            Number::Float(value) => 5.0 * value.powf(2.0),
        };
        let grown = n.as_f64() + 1.0 + five_squares.sqrt();
        Ok(grown / 2.0)
    }

    /// The Hénon map: `x' = y + 1 - a·x²`, `y' = b·x`.
    #[derive(Debug, Clone, Copy)]
    pub(crate) struct Henon {
        pub a: f64,
        pub b: f64,
        x: f64,
        y: f64,
    }

    impl Henon {
        pub(crate) fn new(a: f64, b: f64, x: f64, y: f64) -> Self {
            Self { a, b, x, y }
        }

        /// The map with any of its values left to the Python constructor's defaults, which sit at
        /// the recommended start of the strange attractor.
        pub(crate) fn with_defaults(
            a: Option<f64>,
            b: Option<f64>,
            x: Option<f64>,
            y: Option<f64>,
        ) -> Self {
            Self::new(
                a.unwrap_or(1.4),
                b.unwrap_or(0.3),
                x.unwrap_or(0.63135448),
                y.unwrap_or(0.18940634),
            )
        }

        /// One step, with optional live `a` and `b`, returning the new `(x, y)`.
        pub(crate) fn step(&mut self, a: Option<f64>, b: Option<f64>) -> (f64, f64) {
            if let Some(a) = a {
                self.a = a;
            }
            if let Some(b) = b {
                self.b = b;
            }
            let x = 1.0 - self.a * self.x.powf(2.0) + self.y;
            let y = self.b * self.x;
            self.x = x;
            self.y = y;
            (self.x, self.y)
        }

        /// The map's state, as the Python attributes exposed it.
        pub(crate) fn state(&self) -> (f64, f64, f64, f64) {
            (self.a, self.b, self.x, self.y)
        }
    }

    /// The Lorenz attractor, advanced by Euler steps of `0.01`, as the Python code did.
    #[derive(Debug, Clone, Copy)]
    pub(crate) struct Lorenz {
        pub r: f64,
        pub s: f64,
        pub b: f64,
        x: f64,
        y: f64,
        z: f64,
    }

    impl Lorenz {
        pub(crate) fn new(r: f64, s: f64, b: f64, x: f64, y: f64, z: f64) -> Self {
            Self { r, s, b, x, y, z }
        }

        /// The map with any of its values left to the Python constructor's defaults; its `b`
        /// default is the literal it wrote, not 8/3.
        pub(crate) fn with_defaults(
            r: Option<f64>,
            s: Option<f64>,
            b: Option<f64>,
            x: Option<f64>,
            y: Option<f64>,
            z: Option<f64>,
        ) -> Self {
            Self::new(
                r.unwrap_or(28.0),
                s.unwrap_or(10.0),
                b.unwrap_or(2.6666666666),
                x.unwrap_or(1.0),
                y.unwrap_or(1.0),
                z.unwrap_or(1.0),
            )
        }

        /// One step, with optional live `r`, `s`, and `b`, returning the new `(x, y, z)`.
        pub(crate) fn step(
            &mut self,
            r: Option<f64>,
            s: Option<f64>,
            b: Option<f64>,
        ) -> (f64, f64, f64) {
            if let Some(r) = r {
                self.r = r;
            }
            if let Some(s) = s {
                self.s = s;
            }
            if let Some(b) = b {
                self.b = b;
            }
            let d = 0.01;
            let dx = self.s * (self.y - self.x);
            let dy = (self.r * self.x) - self.y - (self.x * self.z);
            let dz = (self.x * self.y) - (self.b * self.z);
            self.x += d * dx;
            self.y += d * dy;
            self.z += d * dz;
            (self.x, self.y, self.z)
        }

        /// The map's state and its step, as the Python attributes exposed them.
        pub(crate) fn state(&self) -> (f64, f64, f64, f64, f64, f64) {
            (self.r, self.s, self.b, self.x, self.y, self.z)
        }

        /// The Euler step the Python code fixed.
        pub(crate) fn step_size(&self) -> f64 {
            0.01
        }
    }

    /// `verhulst(p, x)`: the logistic map, without state.
    pub(crate) fn verhulst(p: Number, x: Number) -> Result<Number, Overflow> {
        p.mul(x)?.mul(Number::Int(1).sub(x)?)
    }
}

#[pymodule(name = "athenaCL.libATH.chaos")]
pub(super) mod _inner {
    use rustpython_vm::{
        builtins::PyType,
        common::lock::PyRwLock,
        function::{ArgIntoFloat, OptionalArg, OptionalOption},
        pyclass,
        types::{Callable, Constructor},
        FromArgs, Py, PyObjectRef, PyPayload, PyResult, VirtualMachine,
    };

    use super::core::{self, Henon, Lorenz, PowError};
    use crate::libath::number::Number;

    /// The error `math.pow` raised, as the message it raised it with.
    fn pow_error(
        error: PowError,
        vm: &VirtualMachine,
    ) -> rustpython_vm::builtins::PyBaseExceptionRef {
        match error {
            PowError::Domain => vm.new_value_error("math domain error"),
            PowError::Range => vm.new_overflow_error("math range error"),
        }
    }

    /// A float floored to a Python `int`, exactly, as `math.floor` does — big when the series grows
    /// past what a machine integer holds.
    fn floored(n: f64, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let floored = rustpython_vm::builtins::try_f64_to_bigint(n.floor(), vm)?;
        Ok(vm.ctx.new_int(floored).into())
    }

    /// `_fibonacciNumber(goldenUpper, goldenLower, i)`: the i-th Fibonacci number by Binet's
    /// formula, floored to an `int`.
    #[pyfunction(name = "_fibonacciNumber")]
    fn fibonacci_number(args: FibonacciNumberArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let number = core::fibonacci_number(
            f64::from(args.golden_upper),
            f64::from(args.golden_lower),
            f64::from(args.i),
        )
        .map_err(|error| pow_error(error, vm))?;
        floored(number, vm)
    }

    /// `fibonacciSeries(j, k)`: Fibonacci terms from `j` to `k - 1`, as `int`s.
    #[pyfunction(name = "fibonacciSeries")]
    fn fibonacci_series(args: FibonacciSeriesArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let terms = (args.j..args.k)
            .map(|i| {
                let number = core::fibonacci_number(
                    (1.0 + 5.0f64.sqrt()) / 2.0,
                    (1.0 - 5.0f64.sqrt()) / 2.0,
                    i as f64,
                )
                .map_err(|error| pow_error(error, vm))?;
                floored(number, vm)
            })
            .collect::<Result<Vec<_>, _>>()?;
        Ok(vm.ctx.new_list(terms).into())
    }

    /// `fibonacciSuccessor(n)`: the term after `n` in the Fibonacci series, as an `int`.
    #[pyfunction(name = "fibonacciSuccessor")]
    fn fibonacci_successor(
        args: FibonacciSuccessorArgs,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        let number = core::fibonacci_successor(args.n).map_err(|error| error.into_exception(vm))?;
        floored(number, vm)
    }

    /// `verhulst(p, x)`: the logistic map, without state.
    #[pyfunction]
    fn verhulst(args: VerhulstArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let grown = core::verhulst(args.p, args.x).map_err(|error| error.into_exception(vm))?;
        Ok(grown.as_object(vm))
    }

    /// The arguments of `_fibonacciNumber`.
    #[derive(FromArgs)]
    struct FibonacciNumberArgs {
        #[pyarg(any, name = "goldenUpper")]
        golden_upper: ArgIntoFloat,
        #[pyarg(any, name = "goldenLower")]
        golden_lower: ArgIntoFloat,
        #[pyarg(any)]
        i: ArgIntoFloat,
    }

    /// The arguments of `fibonacciSeries`.
    #[derive(FromArgs)]
    struct FibonacciSeriesArgs {
        #[pyarg(any)]
        j: isize,
        #[pyarg(any)]
        k: isize,
    }

    /// The arguments of `fibonacciSuccessor`.
    #[derive(FromArgs)]
    struct FibonacciSuccessorArgs {
        #[pyarg(any)]
        n: Number,
    }

    /// The arguments of `verhulst`.
    #[derive(FromArgs)]
    struct VerhulstArgs {
        #[pyarg(any)]
        p: Number,
        #[pyarg(any)]
        x: Number,
    }

    /// A live parameter: present with a value, or absent — passed as `None` or left off, as the
    /// Python code treated both the same.
    fn optional_float(arg: OptionalOption<ArgIntoFloat>) -> Option<f64> {
        match arg {
            OptionalArg::Present(Some(value)) => Some(f64::from(value)),
            _ => None,
        }
    }

    /// A constructor argument's value, absent when left off.
    fn or_none(arg: OptionalArg<ArgIntoFloat>) -> Option<f64> {
        match arg {
            OptionalArg::Present(value) => Some(f64::from(value)),
            OptionalArg::Missing => None,
        }
    }

    /// `Henon(a, b, x, y)`: the Hénon map, stepped by calling it.
    #[pyattr]
    #[pyclass(name = "Henon")]
    #[derive(Debug, PyPayload)]
    struct PyHenon {
        henon: PyRwLock<Henon>,
    }

    /// The arguments of the Hénon constructor.
    #[derive(FromArgs)]
    struct HenonArgs {
        #[pyarg(any, optional)]
        a: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        b: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        x: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        y: OptionalArg<ArgIntoFloat>,
    }

    impl Constructor for PyHenon {
        type Args = HenonArgs;

        fn py_new(_cls: &Py<PyType>, args: Self::Args, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self {
                henon: PyRwLock::new(Henon::with_defaults(
                    or_none(args.a),
                    or_none(args.b),
                    or_none(args.x),
                    or_none(args.y),
                )),
            })
        }
    }

    /// The arguments of a live Hénon step.
    #[derive(FromArgs)]
    struct HenonCallArgs {
        #[pyarg(any, optional)]
        a: OptionalOption<ArgIntoFloat>,
        #[pyarg(any, optional)]
        b: OptionalOption<ArgIntoFloat>,
    }

    impl Callable for PyHenon {
        type Args = HenonCallArgs;

        fn call(zelf: &Py<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult {
            let (x, y) = zelf
                .henon
                .write()
                .step(optional_float(args.a), optional_float(args.b));
            Ok(vm
                .ctx
                .new_tuple(vec![vm.ctx.new_float(x).into(), vm.ctx.new_float(y).into()])
                .into())
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Callable))]
    impl PyHenon {
        #[pygetset]
        fn a(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.henon.read().state().0).into()
        }

        #[pygetset]
        fn b(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.henon.read().state().1).into()
        }

        #[pygetset]
        fn x(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.henon.read().state().2).into()
        }

        #[pygetset]
        fn y(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.henon.read().state().3).into()
        }
    }

    /// `Lorenz(r, s, b, x, y, z)`: the Lorenz attractor, stepped by calling it.
    #[pyattr]
    #[pyclass(name = "Lorenz")]
    #[derive(Debug, PyPayload)]
    struct PyLorenz {
        lorenz: PyRwLock<Lorenz>,
    }

    /// The arguments of the Lorenz constructor.
    #[derive(FromArgs)]
    struct LorenzArgs {
        #[pyarg(any, optional)]
        r: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        s: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        b: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        x: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        y: OptionalArg<ArgIntoFloat>,
        #[pyarg(any, optional)]
        z: OptionalArg<ArgIntoFloat>,
    }

    impl Constructor for PyLorenz {
        type Args = LorenzArgs;

        fn py_new(_cls: &Py<PyType>, args: Self::Args, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self {
                lorenz: PyRwLock::new(Lorenz::with_defaults(
                    or_none(args.r),
                    or_none(args.s),
                    or_none(args.b),
                    or_none(args.x),
                    or_none(args.y),
                    or_none(args.z),
                )),
            })
        }
    }

    /// The arguments of a live Lorenz step.
    #[derive(FromArgs)]
    struct LorenzCallArgs {
        #[pyarg(any, optional)]
        r: OptionalOption<ArgIntoFloat>,
        #[pyarg(any, optional)]
        s: OptionalOption<ArgIntoFloat>,
        #[pyarg(any, optional)]
        b: OptionalOption<ArgIntoFloat>,
    }

    impl Callable for PyLorenz {
        type Args = LorenzCallArgs;

        fn call(zelf: &Py<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult {
            let (x, y, z) = zelf.lorenz.write().step(
                optional_float(args.r),
                optional_float(args.s),
                optional_float(args.b),
            );
            Ok(vm
                .ctx
                .new_tuple(vec![
                    vm.ctx.new_float(x).into(),
                    vm.ctx.new_float(y).into(),
                    vm.ctx.new_float(z).into(),
                ])
                .into())
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Callable))]
    impl PyLorenz {
        #[pygetset]
        fn r(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.lorenz.read().state().0).into()
        }

        #[pygetset]
        fn s(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.lorenz.read().state().1).into()
        }

        #[pygetset]
        fn b(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.lorenz.read().state().2).into()
        }

        #[pygetset]
        fn x(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.lorenz.read().state().3).into()
        }

        #[pygetset]
        fn y(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.lorenz.read().state().4).into()
        }

        #[pygetset]
        fn z(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.lorenz.read().state().5).into()
        }

        #[pygetset]
        fn d(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.lorenz.read().step_size()).into()
        }
    }
}

#[cfg(test)]
mod tests {
    #![expect(
        clippy::float_cmp,
        reason = "the tests assert exact trajectories and successors, not approximations"
    )]

    use super::core::{Henon, Lorenz};
    use crate::libath::number::Number;

    /// The goldens are the values the Python reference produces.
    #[test]
    fn henon_trajectories() {
        let mut henon = Henon::new(1.4, 0.3, 0.63135448, 0.18940634);
        let steps: Vec<_> = (0..6).map(|_| henon.step(None, None)).collect();
        assert_eq!(
            steps,
            [
                (0.6313544688175013, 0.189406344),
                (0.6313544925858391, 0.1894063406452504),
                (0.6313544472135992, 0.18940634777575172),
                (0.6313545345528065, 0.18940633416407976),
                (0.6313543665435324, 0.18940636036584196),
                (0.6313546897508229, 0.1894063099630597),
            ]
        );

        let mut dynamic = Henon::new(1.4, 0.3, 0.63135448, 0.18940634);
        assert_eq!(
            dynamic.step(Some(0.4), None),
            (1.029962948233572, 0.189406344)
        );
        assert_eq!(
            dynamic.step(None, Some(0.3)),
            (0.7650768741064033, 0.30898888447007156)
        );
        assert_eq!(
            dynamic.step(Some(1.5), Some(0.2)),
            (0.43097494953143356, 0.1530153748212807)
        );
    }

    /// A square beyond float range flows into infinities, as it does where the module runs.
    #[test]
    fn henon_overflows_into_infinities() {
        let mut henon = Henon::new(1.4, 0.3, 1e200, 0.18940634);
        assert_eq!(
            henon.step(None, None),
            (f64::NEG_INFINITY, 2.9999999999999997e199)
        );
        assert_eq!(
            henon.step(None, None),
            (f64::NEG_INFINITY, f64::NEG_INFINITY)
        );
        assert_eq!(
            henon.step(None, None),
            (f64::NEG_INFINITY, f64::NEG_INFINITY)
        );
    }

    /// The goldens are the values the Python reference produces.
    #[test]
    fn lorenz_trajectories() {
        let mut lorenz = Lorenz::new(28.0, 10.0, 2.6666666666, 1.0, 1.0, 1.0);
        let steps: Vec<_> = (0..5).map(|_| lorenz.step(None, None, None)).collect();
        assert_eq!(
            steps,
            [
                (1.0, 1.26, 0.983333333334),
                (1.026, 1.51756666666666, 0.9697111111124155),
                (1.075156666666666, 1.77972176399998, 0.9594223821500641),
                (1.1456131763999975, 2.0526531193234683, 0.9529725824871321),
                (1.2363171706923446, 2.3419808980497807, 0.9510754448888658),
            ]
        );

        let mut dynamic = Lorenz::new(28.0, 10.0, 2.6666666666, 1.0, 1.0, 1.0);
        assert_eq!(
            dynamic.step(Some(99.96), None, None),
            (1.0, 1.9796, 0.983333333334)
        );
        assert_eq!(
            dynamic.step(None, Some(2.0), None),
            (1.019592, 2.94957066666666, 0.9769071111124156)
        );
        assert_eq!(
            dynamic.step(None, None, Some(0.375)),
            (1.0581915733333334, 3.9292986564476604, 1.003317295997424)
        );
    }

    /// An int squares exactly before the float takes over; a float squares in float, as the Python
    /// square. expression did. Large float `powf` results vary across platforms and are checked
    /// against the Python reference by the parity corpus instead.
    #[test]
    fn fibonacci_successor_squares_ints_exactly() {
        let successor = |n| super::core::fibonacci_successor(n).expect("the square fits");
        assert_eq!(
            successor(Number::Int(7443506681195961)).floor(),
            12043846805661994.0
        );
        assert_eq!(successor(Number::Int(6765)).floor(), 10946.0);
        assert_eq!(successor(Number::Float(6765.0)).floor(), 10946.0);
    }
}
