//! Native OMDE oscillators, all inheriting the functional framework's `Function`.
//!
//! The reference is `pysrc/athenaCL/libATH/_pyref/oscillator.py`. Sinusoids retain frequency
//! updates; folded waves retain the period last supplied by `f`. Assignments occur in Python's
//! original order, including when a later operation fails. Arguments remain Python objects until
//! arithmetic needs them: explicit `None`, large integers, and numeric protocols retain their
//! original behavior. No state lock spans a Python callback. Transcendentals use the same checked
//! math implementation as RustPython.
//!
//! Narrowing: the implementation attributes `frequency`, `phase0`, `T`, and `exponent` are not
//! exposed. No athenaCL consumer reads or writes them.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.omde.oscillator")]
pub(super) mod _inner {
    use rustpython_vm::{
        builtins::{PyStr, PyType},
        common::lock::PyRwLock,
        convert::ToPyObject,
        function::{FuncArgs, OptionalArg},
        protocol::PyNumberMethods,
        pyclass,
        types::{AsNumber, Callable, Constructor, Initializer, PyComparisonOp},
        AsObject, FromArgs, Py, PyObjectRef, PyRef, PyResult, Traverse, VirtualMachine,
    };

    use super::super::{
        copy::{self, CopyState},
        functional::{Function, FunctionModel},
        math,
    };

    /// A leaf can be the first OMDE import; initialize its native base before its types.
    pub(crate) fn module_exec(
        vm: &VirtualMachine,
        module: &Py<rustpython_vm::builtins::PyModule>,
    ) -> PyResult<()> {
        vm.import("athenaCL.libATH.omde._functional", 0)?;
        __module_exec(vm, module);
        Ok(())
    }

    #[derive(Debug, Clone, Traverse)]
    struct Wave {
        frequency: PyObjectRef,
        phase0: PyObjectRef,
        period: Option<PyObjectRef>,
        #[pytraverse(skip)]
        exponent: Option<f64>,
    }

    /// Short locks only: Python arithmetic and coercions can call back into a wave.
    #[derive(Debug, Default, Traverse)]
    struct State(PyRwLock<Option<Wave>>);

    impl State {
        fn native_state(&self, vm: &VirtualMachine) -> PyObjectRef {
            let Some(wave) = self.0.read().clone() else {
                return vm.ctx.none();
            };
            vm.ctx
                .new_tuple(vec![
                    wave.frequency,
                    wave.phase0,
                    wave.period.unwrap_or_else(|| vm.ctx.none()),
                    wave.exponent.to_pyobject(vm),
                ])
                .into()
        }

        fn restore(&self, state: PyObjectRef, vm: &VirtualMachine) -> PyResult<()> {
            let wave = if vm.is_none(&state) {
                None
            } else {
                let [frequency, phase0, period, exponent] = copy::unpack(&state, vm)?;
                Some(Wave {
                    frequency,
                    phase0,
                    period: period.try_into_value(vm)?,
                    exponent: exponent.try_into_value(vm)?,
                })
            };
            self.replace(wave);
            Ok(())
        }

        // Read only the current operand: a whole Wave snapshot delays unrelated finalizers.
        fn read<R>(&self, vm: &VirtualMachine, read: impl FnOnce(&Wave) -> R) -> PyResult<R> {
            let state = self.0.read();
            let wave = state
                .as_ref()
                .ok_or_else(|| vm.new_attribute_error("oscillator is not initialized"))?;
            Ok(read(wave))
        }

        fn frequency(&self, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            self.read(vm, |wave| wave.frequency.clone())
        }

        fn phase0(&self, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            self.read(vm, |wave| wave.phase0.clone())
        }

        fn period(&self, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            Ok(self
                .read(vm, |wave| wave.period.clone())?
                .unwrap_or_else(|| vm.ctx.none()))
        }

        fn exponent(&self, vm: &VirtualMachine) -> PyResult<f64> {
            self.read(vm, |wave| wave.exponent)?
                .ok_or_else(|| vm.new_attribute_error("power oscillator has no exponent"))
        }

        // Return replaced references to the caller: their __del__ may reenter this state.
        fn update<R>(
            &self,
            vm: &VirtualMachine,
            update: impl FnOnce(&mut Wave) -> R,
        ) -> PyResult<R> {
            let mut state = self.0.write();
            let state = state
                .as_mut()
                .ok_or_else(|| vm.new_attribute_error("oscillator is not initialized"))?;
            Ok(update(state))
        }

        fn replace(&self, wave: Option<Wave>) {
            let previous = std::mem::replace(&mut *self.0.write(), wave);
            drop(previous);
        }

        fn initialize(&self, wave: Wave, shape: Shape, vm: &VirtualMachine) -> PyResult<()> {
            if self.0.read().is_none() {
                self.replace(Some(wave));
                return Ok(());
            }
            // Match the individual Python assignments, including finalizer reentry.
            self.update(vm, |old| {
                std::mem::replace(&mut old.frequency, wave.frequency)
            })?;
            if !matches!(shape, Shape::Sine | Shape::Cosine) {
                self.update(vm, |old| old.period.take())?;
            }
            self.update(vm, |old| std::mem::replace(&mut old.phase0, wave.phase0))?;
            if matches!(shape, Shape::Sine) {
                self.update(vm, |old| old.period.take())?;
            }
            // Power initializers assign the exponent only after math.pow succeeds.
            Ok(())
        }
    }

    #[derive(Debug, Clone, Copy)]
    enum Shape {
        Sine,
        Cosine,
        Up,
        Down,
        Square,
        Triangle,
        PowerUp,
        PowerDown,
    }

    #[derive(FromArgs)]
    pub(crate) struct PlainArgs {
        #[pyarg(any, optional)]
        frequency: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        phase0: OptionalArg<PyObjectRef>,
    }

    impl PlainArgs {
        fn wave(&self, vm: &VirtualMachine) -> Wave {
            Wave {
                frequency: self
                    .frequency
                    .as_ref()
                    .cloned()
                    .unwrap_or_else(|| vm.ctx.new_float(1.0).into()),
                phase0: self
                    .phase0
                    .as_ref()
                    .cloned()
                    .unwrap_or_else(|| vm.ctx.new_float(0.0).into()),
                period: None,
                exponent: None,
            }
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct PowerArgs {
        #[pyarg(flatten)]
        plain: PlainArgs,
        #[pyarg(any, optional)]
        exponent: OptionalArg<PyObjectRef>,
    }

    /// Both argument sets initialize before the first call; only power waves evaluate an exponent.
    /// Borrow arguments so their finalizers run after the complete initializer returns.
    trait WaveArgs {
        fn initialize(&self, state: &State, shape: Shape, vm: &VirtualMachine) -> PyResult<()>;
    }

    impl WaveArgs for PlainArgs {
        fn initialize(&self, state: &State, shape: Shape, vm: &VirtualMachine) -> PyResult<()> {
            state.initialize(self.wave(vm), shape, vm)
        }
    }

    impl WaveArgs for PowerArgs {
        fn initialize(&self, state: &State, shape: Shape, vm: &VirtualMachine) -> PyResult<()> {
            state.initialize(self.plain.wave(vm), shape, vm)?;
            let exponent = match &self.exponent {
                OptionalArg::Missing => 0.0,
                OptionalArg::Present(value) => value.try_float(vm)?.to_f64(),
            };
            let exponent = math::pow(2.0, exponent).map_err(|error| error.exception(vm))?;
            state.update(vm, |wave| wave.exponent = Some(exponent))
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct CallArgs {
        #[pyarg(any)]
        t: PyObjectRef,
        #[pyarg(any, optional)]
        f: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        phase0: OptionalArg<PyObjectRef>,
    }

    fn supplied(
        value: &OptionalArg<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        match value {
            OptionalArg::Present(value)
                if value.rich_compare_bool(&vm.ctx.none(), PyComparisonOp::Ne, vm)? =>
            {
                Ok(Some(value.clone()))
            }
            _ => Ok(None),
        }
    }

    fn update_phase(
        state: &State,
        phase0: &OptionalArg<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        if let Some(phase0) = supplied(phase0, vm)? {
            state.update(vm, |wave| std::mem::replace(&mut wave.phase0, phase0))?;
        }
        Ok(())
    }

    fn set_period(state: &State, frequency: PyObjectRef, vm: &VirtualMachine) -> PyResult<()> {
        // Compute before assignment: a failed division must leave the old period intact.
        let period = vm._truediv(vm.ctx.new_float(1.0).as_object(), &frequency)?;
        drop(frequency);
        state.update(vm, |wave| wave.period.replace(period))?;
        Ok(())
    }

    fn sinusoid(state: &State, args: CallArgs, cosine: bool, vm: &VirtualMachine) -> PyResult {
        if let Some(frequency) = supplied(&args.f, vm)? {
            state.update(vm, |wave| std::mem::replace(&mut wave.frequency, frequency))?;
        }
        update_phase(state, &args.phase0, vm)?;
        set_period(state, state.frequency(vm)?, vm)?;
        let phase = {
            let time = {
                let shift =
                    vm._mul(state.phase0(vm)?.as_object(), state.period(vm)?.as_object())?;
                vm._add(&shift, &args.t)?
            };
            vm._mul(&time, state.frequency(vm)?.as_object())?
        };
        let value = {
            let radians = vm._mul(
                vm.ctx.new_float(2.0 * std::f64::consts::PI).as_object(),
                &phase,
            )?;
            math::trig(radians.try_float(vm)?.to_f64(), cosine)
                .map_err(|error| error.exception(vm))?
        };
        Ok(vm.ctx.new_float((1.0 + value) / 2.0).into())
    }

    fn folded(state: &State, args: &mut CallArgs, vm: &VirtualMachine) -> PyResult<()> {
        if let Some(frequency) = supplied(&args.f, vm)? {
            set_period(state, frequency, vm)?;
        }
        let missing_period =
            state
                .period(vm)?
                .rich_compare_bool(&vm.ctx.none(), PyComparisonOp::Eq, vm)?;
        if missing_period {
            set_period(state, state.frequency(vm)?, vm)?;
        }
        update_phase(state, &args.phase0, vm)?;
        // Match Python's rebinding of t and release each intermediate at its last use. The other
        // arguments remain alive until sample() returns, as Python locals do.
        args.t = {
            let shift = vm._mul(state.period(vm)?.as_object(), state.phase0(vm)?.as_object())?;
            // RustPython's specialized string += uses ordinary addition's error message.
            if args.t.downcast_ref_if_exact::<PyStr>(vm).is_some() {
                vm._add(&args.t, &shift)?
            } else {
                vm._iadd(&args.t, &shift)?
            }
        };
        let time = {
            let period = state.period(vm)?;
            math::fmod(
                args.t.try_float(vm)?.to_f64(),
                period.try_float(vm)?.to_f64(),
            )
            .map_err(|error| error.exception(vm))?
        };
        args.t = vm.ctx.new_float(time).into();
        if time < 0.0 {
            args.t = vm._iadd(&args.t, state.period(vm)?.as_object())?;
        }
        Ok(())
    }

    fn half_period(state: &State, vm: &VirtualMachine) -> PyResult {
        vm._mul(
            state.period(vm)?.as_object(),
            vm.ctx.new_float(0.5).as_object(),
        )
    }

    fn triangle(time: &PyObjectRef, state: &State, vm: &VirtualMachine) -> PyResult {
        // Each original T * 0.5 is observable: operators can replace the stored period.
        let rising =
            time.rich_compare_bool(half_period(state, vm)?.as_object(), PyComparisonOp::Lt, vm)?;
        if rising {
            vm._truediv(time, half_period(state, vm)?.as_object())
        } else {
            let ratio = {
                let remainder = vm._sub(time, half_period(state, vm)?.as_object())?;
                vm._truediv(&remainder, half_period(state, vm)?.as_object())?
            };
            vm._sub(vm.ctx.new_float(1.0).as_object(), &ratio)
        }
    }

    fn sample(state: &State, mut args: CallArgs, shape: Shape, vm: &VirtualMachine) -> PyResult {
        if matches!(shape, Shape::Sine | Shape::Cosine) {
            return sinusoid(state, args, matches!(shape, Shape::Cosine), vm);
        }
        folded(state, &mut args, vm)?;
        match shape {
            Shape::Square => {
                let high = {
                    let half =
                        vm._truediv(state.period(vm)?.as_object(), vm.ctx.new_int(2).as_object())?;
                    args.t.rich_compare_bool(&half, PyComparisonOp::Lt, vm)?
                };
                Ok(vm.ctx.new_float(if high { 1.0 } else { 0.0 }).into())
            }
            Shape::Triangle => triangle(&args.t, state, vm),
            _ => {
                let value = {
                    let ratio = vm._truediv(&args.t, state.period(vm)?.as_object())?;
                    if matches!(shape, Shape::Down | Shape::PowerDown) {
                        vm._sub(vm.ctx.new_float(1.0).as_object(), &ratio)?
                    } else {
                        ratio
                    }
                };
                if matches!(shape, Shape::PowerUp | Shape::PowerDown) {
                    let exponent = state.exponent(vm)?;
                    let powered = math::pow(value.try_float(vm)?.to_f64(), exponent)
                        .map_err(|error| error.exception(vm))?;
                    Ok(vm.ctx.new_float(powered).into())
                } else {
                    Ok(value)
                }
            }
        }
    }

    #[pyattr]
    #[pyclass(name = "Sine", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Sine {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    #[pyattr]
    #[pyclass(name = "Cosine", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Cosine {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    #[pyattr]
    #[pyclass(name = "SawUp", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct SawUp {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    #[pyattr]
    #[pyclass(name = "SawDown", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct SawDown {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    #[pyattr]
    #[pyclass(name = "Square", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Square {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    #[pyattr]
    #[pyclass(name = "Triangle", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct Triangle {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    #[pyattr]
    #[pyclass(name = "PowerUp", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct PowerUp {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    #[pyattr]
    #[pyclass(name = "PowerDown", base = Function, traverse)]
    #[repr(C)]
    #[derive(Debug)]
    pub(crate) struct PowerDown {
        #[pytraverse(skip)]
        base: Function,
        state: State,
    }

    /// The eight public types differ only in signature and waveform selection.
    macro_rules! wave_impl {
        ($class:ident, $args:ty, $shape:ident) => {
            impl Constructor for $class {
                type Args = FuncArgs;

                fn py_new(
                    _cls: &Py<PyType>,
                    _args: FuncArgs,
                    _vm: &VirtualMachine,
                ) -> PyResult<Self> {
                    Ok(Self {
                        base: Function(FunctionModel),
                        state: State::default(),
                    })
                }
            }
            impl Initializer for $class {
                type Args = $args;

                fn init(zelf: PyRef<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult<()> {
                    args.initialize(&zelf.state, Shape::$shape, vm)
                }
            }
            impl Callable for $class {
                type Args = CallArgs;

                fn call(zelf: &Py<Self>, args: Self::Args, vm: &VirtualMachine) -> PyResult {
                    sample(&zelf.state, args, Shape::$shape, vm)
                }
            }
            // Static native subclasses need the reflected slots registered explicitly.
            impl AsNumber for $class {
                fn as_number() -> &'static PyNumberMethods {
                    Function::as_number()
                }
            }
            impl CopyState for $class {
                fn native_state(&self, vm: &VirtualMachine) -> PyResult {
                    Ok(self.state.native_state(vm))
                }

                fn restore_native_state(
                    &self,
                    state: PyObjectRef,
                    vm: &VirtualMachine,
                ) -> PyResult<()> {
                    self.state.restore(state, vm)
                }
            }
        };
    }
    wave_impl!(Sine, PlainArgs, Sine);
    wave_impl!(Cosine, PlainArgs, Cosine);
    wave_impl!(SawUp, PlainArgs, Up);
    wave_impl!(SawDown, PlainArgs, Down);
    wave_impl!(Square, PlainArgs, Square);
    wave_impl!(Triangle, PlainArgs, Triangle);
    wave_impl!(PowerUp, PowerArgs, PowerUp);
    wave_impl!(PowerDown, PowerArgs, PowerDown);

    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl Sine {}
    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl Cosine {}
    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl SawUp {}
    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl SawDown {}
    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl Square {}
    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl Triangle {}
    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl PowerUp {}
    #[pyclass(
        flags(BASETYPE),
        with(Constructor, Initializer, Callable, AsNumber, CopyState)
    )]
    impl PowerDown {}
}
