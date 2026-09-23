//! The `athenaCL.libATH.omde._functional` module: the omde functional-scoring bases, in
//! Rust.
//!
//! Port of the three base classes of `pysrc/athenaCL/libATH/_pyref/functional.py`; the combination
//! classes, constants, freezer, and coercions stay in that module's Python shim —
//! `athenaCL.libATH.omde.functional` — which imports these bases, and whose classes the operators
//! below construct by lookup. The bases are stateless: state lives in the Python subclasses, whose
//! `__init__` signatures the permissive constructors leave alone.
//!
//! Division keeps its Python 2 shape: `__div__` and `__rdiv__` are plain callable methods, never
//! true-division slots, so `/` on these classes raises as it does in the reference; and
//! `Generator.__div__` with a `Function` operand constructs `MulFunction`, exactly the reference's
//! quirk.
//!
//! One narrowing: instantiating the bases directly accepts any arguments, where the reference's
//! no-argument `__init__` rejected extras — the instances are unusable either way, their call
//! raising `NotImplementedError`. A second, inherent to nativeness: the arithmetic wrappers the
//! operator slots expose (`f.__add__(2)`, `g.__rsub__(5)`) accept positional arguments only, where
//! the reference's Python-level `__add__(self, function)` accepted its keyword names — the slot
//! protocol carries no keywords, and CPython's own native types expose the same positional-only
//! wrappers. The `+`, `-`, `*` operators and the `__call__`, `__div__`, `__rdiv__`, and `instance`
//! methods keep their names.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

/// The base payloads, for the sibling omde ports to embed as their classes' bases.
pub(crate) use _inner::{Function, FunctionModel};

#[pymodule(name = "athenaCL.libATH.omde._functional")]
pub(crate) mod _inner {
    use rustpython_vm::{
        builtins::{PyType, PyTypeRef},
        function::FuncArgs,
        protocol::PyNumberMethods,
        pyclass,
        types::{AsNumber, Callable, Constructor},
        FromArgs, Py, PyObjectRef, PyPayload, PyResult, VirtualMachine,
    };

    /// The shim module holding the combination classes the operators construct. `vm.import` has
    /// `__import__` semantics and returns the top-level package for a dotted name, so the
    /// submodules are walked by hand.
    fn shim_module(vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let athena = vm.import("athenaCL.libATH.omde.functional", 0)?;
        let libath = athena.get_attr("libATH", vm)?;
        let omde = libath.get_attr("omde", vm)?;
        omde.get_attr("functional", vm)
    }

    /// A class from the shim by name, for an operator to construct.
    fn shim_class(vm: &VirtualMachine, name: &'static str) -> PyResult<PyObjectRef> {
        let module = shim_module(vm)?;
        module
            .get_attr(name, vm)
            .map_err(|_absent| vm.new_type_error(format!("the {name} class is not reachable")))
    }

    /// Construct a combination class from the shim over two operands.
    fn combine(
        vm: &VirtualMachine,
        name: &'static str,
        a: PyObjectRef,
        b: PyObjectRef,
    ) -> PyResult {
        let class = shim_class(vm, name)?;
        class.call((a, b), vm)
    }

    /// The `Function` class, for the operand checks the Generator operators make.
    fn function_class(vm: &VirtualMachine) -> PyResult<PyTypeRef> {
        let athena = vm.import("athenaCL.libATH.omde._functional", 0)?;
        let module = athena
            .get_attr("libATH", vm)?
            .get_attr("omde", vm)?
            .get_attr("_functional", vm)?;
        let class = module.get_attr("Function", vm)?;
        rustpython_vm::convert::TryFromObject::try_from_object(vm, class)
    }

    /// `make_function` from the shim, for the Generator operators' Function branches.
    fn make_function(vm: &VirtualMachine, value: PyObjectRef) -> PyResult {
        let module = shim_module(vm)?;
        let maker = module
            .get_attr("make_function", vm)
            .map_err(|_absent| vm.new_type_error("make_function is not reachable"))?;
        maker.call((value,), vm)
    }

    /// The arguments of a Function's call, in the reference's parameter name.
    #[derive(FromArgs)]
    pub(crate) struct CallArgs {
        #[pyarg(any, name = "t")]
        _t: PyObjectRef,
    }

    /// The arguments of `instance`, in the reference's parameter names. The values are the
    /// subclass's to read; the bases only receive them.
    #[derive(FromArgs)]
    struct InstanceArgs {
        #[pyarg(any, name = "begin")]
        _begin: PyObjectRef,
        #[pyarg(any, name = "end")]
        _end: PyObjectRef,
    }

    /// The arguments of the Function division methods.
    #[derive(FromArgs)]
    struct FunctionDivArgs {
        #[pyarg(any)]
        function: PyObjectRef,
    }

    /// The arguments of the Generator division methods.
    #[derive(FromArgs)]
    struct ObjectDivArgs {
        #[pyarg(any)]
        object: PyObjectRef,
    }

    /// A Generator operator's left side: a Function operand combines as a Function; a constant or
    /// another Generator combines as a Generator.
    fn generator_left(
        vm: &VirtualMachine,
        function_name: &'static str,
        generator_name: &'static str,
        a: PyObjectRef,
        b: PyObjectRef,
    ) -> PyResult {
        let function_type = function_class(vm)?;
        if b.class().fast_issubclass(&function_type) {
            let adapted = make_function(vm, a)?;
            return combine(vm, function_name, adapted, b);
        }
        combine(vm, generator_name, a, b)
    }

    /// `FunctionModel`: the base of the bases, instanced into a function by a lifespan.
    #[pyattr]
    #[pyclass(name = "FunctionModel")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct FunctionModel;

    impl Constructor for FunctionModel {
        // permissive: the arguments belong to a subclass's own __init__
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: Self::Args, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self)
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor))]
    impl FunctionModel {
        /// Instance this model as a ready function over its lifespan.
        #[pymethod]
        fn instance(&self, _args: InstanceArgs, vm: &VirtualMachine) -> PyResult {
            Err(vm.new_not_implemented_error(""))
        }
    }

    /// `Function`: time-dependent scoring, defined by the call `f(t)` its subclasses give.
    #[pyattr]
    #[pyclass(name = "Function", base = FunctionModel)]
    #[derive(Debug)]
    pub(crate) struct Function(pub FunctionModel);

    impl From<FunctionModel> for Function {
        fn from(base: FunctionModel) -> Self {
            Self(base)
        }
    }

    impl Constructor for Function {
        // permissive: the arguments belong to a subclass's own __init__
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: Self::Args, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self(FunctionModel))
        }
    }

    impl Callable for Function {
        /// The call's parameter keeps the reference's name, so `f(t=0)` reaches the same
        /// `NotImplementedError` the reference's `__call__(self, t)` raised.
        type Args = CallArgs;

        fn call(_zelf: &Py<Self>, _args: Self::Args, vm: &VirtualMachine) -> PyResult {
            Err(vm.new_not_implemented_error(""))
        }
    }

    /// The combination class an operand pair builds, looked up in the shim: forward and reflected
    /// calls alike construct over the operands in their original order, exactly as the reference's
    /// `__op__` and `__rop__` pairs do.
    impl AsNumber for Function {
        fn as_number() -> &'static PyNumberMethods {
            static AS_NUMBER: PyNumberMethods = PyNumberMethods {
                // one closure serves both directions: the reference's __rop__ pairs construct over
                // the operands in this same order
                add: Some(|a, b, vm| combine(vm, "AddFunction", a.to_owned(), b.to_owned())),
                subtract: Some(|a, b, vm| combine(vm, "SubFunction", a.to_owned(), b.to_owned())),
                multiply: Some(|a, b, vm| combine(vm, "MulFunction", a.to_owned(), b.to_owned())),
                ..PyNumberMethods::NOT_IMPLEMENTED
            };
            &AS_NUMBER
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Callable, AsNumber))]
    impl Function {
        /// A ready-to-use function instances to itself.
        #[pymethod]
        fn instance(zelf: &Py<Self>, _args: InstanceArgs) -> PyObjectRef {
            zelf.to_owned().into()
        }

        /// Division, in the Python 2 shape the reference defined: a plain method, never the `/`
        /// operator.
        #[pymethod(name = "__div__")]
        fn div(zelf: &Py<Self>, args: FunctionDivArgs, vm: &VirtualMachine) -> PyResult {
            combine(vm, "DivFunction", zelf.to_owned().into(), args.function)
        }

        /// Division reflected, as a plain method.
        #[pymethod(name = "__rdiv__")]
        fn rdiv(zelf: &Py<Self>, args: FunctionDivArgs, vm: &VirtualMachine) -> PyResult {
            combine(vm, "DivFunction", args.function, zelf.to_owned().into())
        }
    }

    /// `Generator`: time-independent scoring, defined by the call `g()` its subclasses give.
    #[pyattr]
    #[pyclass(name = "Generator")]
    #[derive(Debug, PyPayload)]
    pub(crate) struct Generator;

    impl Constructor for Generator {
        // permissive: the arguments belong to a subclass's own __init__
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: Self::Args, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self)
        }
    }

    impl Callable for Generator {
        type Args = ();

        fn call(_zelf: &Py<Self>, _args: Self::Args, vm: &VirtualMachine) -> PyResult {
            Err(vm.new_not_implemented_error(""))
        }
    }

    impl AsNumber for Generator {
        fn as_number() -> &'static PyNumberMethods {
            static AS_NUMBER: PyNumberMethods = PyNumberMethods {
                // one closure serves both directions: reflected calls land with the other operand
                // first, where the constant branch builds the same Generator combination the
                // reference's __rop__ pairs do
                add: Some(|a, b, vm| {
                    generator_left(
                        vm,
                        "AddFunction",
                        "AddGenerator",
                        a.to_owned(),
                        b.to_owned(),
                    )
                }),
                subtract: Some(|a, b, vm| {
                    generator_left(
                        vm,
                        "SubFunction",
                        "SubGenerator",
                        a.to_owned(),
                        b.to_owned(),
                    )
                }),
                multiply: Some(|a, b, vm| {
                    generator_left(
                        vm,
                        "MulFunction",
                        "MulGenerator",
                        a.to_owned(),
                        b.to_owned(),
                    )
                }),
                ..PyNumberMethods::NOT_IMPLEMENTED
            };
            &AS_NUMBER
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor, Callable, AsNumber))]
    impl Generator {
        /// Division, in the Python 2 shape the reference defined — and with the reference's quirk:
        /// a Function operand multiplies rather than divides.
        #[pymethod(name = "__div__")]
        fn div(zelf: &Py<Self>, args: ObjectDivArgs, vm: &VirtualMachine) -> PyResult {
            let function_type = function_class(vm)?;
            if args.object.class().fast_issubclass(&function_type) {
                let adapted = make_function(vm, zelf.to_owned().into())?;
                return combine(vm, "MulFunction", adapted, args.object);
            }
            combine(vm, "DivGenerator", zelf.to_owned().into(), args.object)
        }

        /// Division reflected, as a plain method.
        #[pymethod(name = "__rdiv__")]
        fn rdiv(zelf: &Py<Self>, args: ObjectDivArgs, vm: &VirtualMachine) -> PyResult {
            combine(vm, "DivGenerator", args.object, zelf.to_owned().into())
        }
    }
}
