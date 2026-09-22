//! The `athenaCL.libATH.error` module: athenaCL's errors, in Rust.
//!
//! The Rust side is [`AthenaError`], one variant per error the Python side raises, so ported code
//! returns `Result<T, AthenaError>` and stays idiomatic. The Python side keeps its exception types
//! — most report bad user input as `SyntaxError` subclasses, the rest are plain `Exception`s — and
//! [`IntoPyException`] turns a variant into an instance of its type, so Python code catches the
//! same errors it always did. The messages are the callers', as the Python constructors took them;
//! the Python classes also kept a private `_msg` attribute and a message-only `__repr__`, which
//! nothing in athenaCL reads and the native types do not carry.

use rustpython_vm::{
    builtins::PyBaseExceptionRef, convert::IntoPyException, pymodule, VirtualMachine,
};
use thiserror::Error;

/// athenaCL's errors, one per error the Python `error` module raises.
///
/// Every variant carries the message the raising code built, as the Python constructors did;
/// [`Display`](std::fmt::Display) is that message alone.
#[cfg_attr(
    not(test),
    expect(
        dead_code,
        reason = "the modules being ported next return these; the tests hold the raising honest"
    )
)]
#[derive(Debug, Error, Clone)]
pub(crate) enum AthenaError {
    /// a ParameterObject argument string could not be parsed.
    #[error("{0}")]
    ParameterObjectSyntax(String),
    /// a transition table could not be parsed.
    #[error("{0}")]
    TransitionSyntax(String),
    /// an automata specification could not be parsed.
    #[error("{0}")]
    AutomataSpecification(String),
    /// pulse data was malformed.
    #[error("{0}")]
    PulseSyntax(String),
    /// pitch data was malformed.
    #[error("{0}")]
    PitchSyntax(String),
    /// particle data was malformed.
    #[error("{0}")]
    ParticleSyntax(String),
    /// an argument was missing or unusable.
    #[error("{0}")]
    Argument(String),
    /// a Clone could not be processed.
    #[error("{0}")]
    CloneError(String),
    /// a multiset could not be built from the given pitch collection.
    #[error("{0}")]
    Multiset(String),
    /// a test misbehaved.
    #[error("{0}")]
    Test(String),
}

#[cfg_attr(
    not(test),
    expect(dead_code, reason = "the modules being ported next call these")
)]
impl AthenaError {
    /// The Python exception type the variant raises as, by its name in the error module.
    fn python_type_name(&self) -> &'static str {
        match self {
            Self::ParameterObjectSyntax(_) => "ParameterObjectSyntaxError",
            Self::TransitionSyntax(_) => "TransitionSyntaxError",
            Self::AutomataSpecification(_) => "AutomataSpecificationError",
            Self::PulseSyntax(_) => "PulseSyntaxError",
            Self::PitchSyntax(_) => "PitchSyntaxError",
            Self::ParticleSyntax(_) => "ParticleSyntaxError",
            Self::Argument(_) => "ArgumentError",
            Self::CloneError(_) => "CloneError",
            Self::Multiset(_) => "MultisetError",
            Self::Test(_) => "TestError",
        }
    }

    /// The variant reports bad user input, as the `SyntaxError` subclasses do.
    fn is_syntax(&self) -> bool {
        !matches!(
            self,
            Self::CloneError(_) | Self::Multiset(_) | Self::Test(_)
        )
    }

    /// The `athenaCL.libATH.error` module. `vm.import` has `__import__` semantics and returns
    /// the top-level package for a dotted name, so the submodules are walked by hand.
    fn python_module(vm: &VirtualMachine) -> Option<rustpython_vm::PyObjectRef> {
        let athena = vm.import("athenaCL.libATH.error", 0).ok()?;
        let libath = athena.get_attr("libATH", vm).ok()?;
        libath.get_attr("error", vm).ok()
    }
}

impl IntoPyException for AthenaError {
    fn into_pyexception(self, vm: &VirtualMachine) -> PyBaseExceptionRef {
        let message = self.to_string();
        let raised = (|| -> Option<PyBaseExceptionRef> {
            use rustpython_vm::convert::TryFromObject;

            // the module is native and registered before any athenaCL code runs, so this lookup
            // only fails when the host is broken; sys.modules caches it after the first
            let module = Self::python_module(vm)?;
            let exception_type = module.get_attr(self.python_type_name(), vm).ok()?;
            let raised = exception_type.call((message.clone(),), vm).ok()?;
            TryFromObject::try_from_object(vm, raised).ok()
        })();
        // keeping the message matters more than the type when even the module is unreachable
        raised.unwrap_or_else(|| {
            let exception_type = if self.is_syntax() {
                vm.ctx.exceptions.syntax_error
            } else {
                vm.ctx.exceptions.exception_type
            };
            vm.new_exception(
                exception_type.to_owned(),
                vec![vm.ctx.new_str(message).into()],
            )
        })
    }
}

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.error")]
pub(super) mod _inner {
    #![expect(
        clippy::unwrap_used,
        reason = "the pymodule macro's generated attribute setters unwrap"
    )]

    use rustpython_vm::{builtins::PyTypeRef, VirtualMachine};

    /// An athenaCL exception type; `SyntaxError` subclasses report bad user input.
    fn athena_error(vm: &VirtualMachine, name: &'static str, syntax: bool) -> PyTypeRef {
        let base = if syntax {
            vm.ctx.exceptions.syntax_error
        } else {
            vm.ctx.exceptions.exception_type
        };
        vm.ctx
            .new_exception_type("athenaCL.libATH.error", name, Some(vec![base.to_owned()]))
    }

    #[pyattr(name = "ParameterObjectSyntaxError")]
    fn parameter_object_syntax_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "ParameterObjectSyntaxError", true)
    }

    #[pyattr(name = "TransitionSyntaxError")]
    fn transition_syntax_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "TransitionSyntaxError", true)
    }

    #[pyattr(name = "AutomataSpecificationError")]
    fn automata_specification_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "AutomataSpecificationError", true)
    }

    #[pyattr(name = "PulseSyntaxError")]
    fn pulse_syntax_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "PulseSyntaxError", true)
    }

    #[pyattr(name = "PitchSyntaxError")]
    fn pitch_syntax_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "PitchSyntaxError", true)
    }

    #[pyattr(name = "ParticleSyntaxError")]
    fn particle_syntax_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "ParticleSyntaxError", true)
    }

    #[pyattr(name = "ArgumentError")]
    fn argument_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "ArgumentError", true)
    }

    #[pyattr(name = "CloneError")]
    fn clone_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "CloneError", false)
    }

    #[pyattr(name = "MultisetError")]
    fn multiset_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "MultisetError", false)
    }

    #[pyattr(name = "TestError")]
    fn test_error(vm: &VirtualMachine) -> PyTypeRef {
        athena_error(vm, "TestError", false)
    }
}

#[cfg(test)]
mod tests {
    use rustpython_vm::{convert::IntoPyException, AsObject};

    use super::AthenaError;

    /// Every variant raises as an instance of its Python type, with the message as `str`.
    #[test]
    fn variants_raise_as_their_python_types() {
        let cases = [
            (
                AthenaError::ParameterObjectSyntax("no such object".into()),
                "ParameterObjectSyntaxError",
                true,
            ),
            (
                AthenaError::TransitionSyntax("bad table".into()),
                "TransitionSyntaxError",
                true,
            ),
            (
                AthenaError::AutomataSpecification("bad rule".into()),
                "AutomataSpecificationError",
                true,
            ),
            (
                AthenaError::PulseSyntax("no pulse".into()),
                "PulseSyntaxError",
                true,
            ),
            (
                AthenaError::PitchSyntax("no pitch".into()),
                "PitchSyntaxError",
                true,
            ),
            (
                AthenaError::ParticleSyntax("no particle".into()),
                "ParticleSyntaxError",
                true,
            ),
            (
                AthenaError::Argument("missing".into()),
                "ArgumentError",
                true,
            ),
            (
                AthenaError::CloneError("bad clone".into()),
                "CloneError",
                false,
            ),
            (
                AthenaError::Multiset("bad set".into()),
                "MultisetError",
                false,
            ),
            (AthenaError::Test("bug".into()), "TestError", false),
        ];

        let interpreter = crate::init_py_interpreter();
        interpreter.enter(|vm| {
            let module = AthenaError::python_module(vm).expect("the error module imports");
            for (error, type_name, syntax) in cases {
                let raised = error.clone().into_pyexception(vm);
                assert_eq!(&*raised.class().name(), type_name, "raises as itself");
                let exception_type = module
                    .get_attr(type_name, vm)
                    .expect("the module has the type");
                assert!(
                    raised.class().fast_issubclass(&exception_type),
                    "the raised type is the module's type"
                );
                let message = raised
                    .get_arg(0)
                    .as_ref()
                    .and_then(|arg| arg.downcast_ref::<rustpython_vm::builtins::PyStr>())
                    .map(|s| s.to_str().unwrap_or_default().to_owned())
                    .expect("the message is the first argument");
                assert_eq!(message, error.to_string());
                assert_eq!(
                    raised.fast_isinstance(vm.ctx.exceptions.syntax_error),
                    syntax,
                    "{type_name} reports bad input as a SyntaxError when it should"
                );
            }
        });
    }

    /// A `Result` turned into a Python result raises the error, as a pymethod return would.
    #[test]
    fn results_raise_through_the_boundary() {
        let interpreter = crate::init_py_interpreter();
        interpreter.enter(|vm| {
            use rustpython_vm::convert::ToPyResult;

            let result: Result<rustpython_vm::PyObjectRef, AthenaError> =
                Err(AthenaError::PulseSyntax("no such pulse".into()));
            let py_result = result.to_pyresult(vm);
            let raised = py_result.expect_err("the error result becomes a raised exception");
            assert_eq!(&*raised.class().name(), "PulseSyntaxError");
        });
    }
}
