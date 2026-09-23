//! Checked floating-point operations shared by the OMDE ports.

use rustpython_vm::{builtins::PyBaseExceptionRef, VirtualMachine};

/// Failures distinguished by RustPython's arithmetic and `math` module.
#[derive(Debug, Clone, Copy, PartialEq)]
pub(super) enum Error {
    ZeroDivision,
    Domain,
    Range,
    NonFinite(f64),
}

impl Error {
    pub(super) fn exception(self, vm: &VirtualMachine) -> PyBaseExceptionRef {
        match self {
            Self::ZeroDivision => vm.new_zero_division_error("division by zero"),
            Self::Domain => vm.new_value_error("math domain error"),
            Self::Range => vm.new_overflow_error("math range error"),
            Self::NonFinite(value) => {
                vm.new_value_error(format!("expected a finite input, got {value}"))
            }
        }
    }
}

impl From<pymath::Error> for Error {
    fn from(error: pymath::Error) -> Self {
        match error {
            pymath::Error::EDOM => Self::Domain,
            pymath::Error::ERANGE => Self::Range,
        }
    }
}

pub(super) fn divide(numerator: f64, denominator: f64) -> Result<f64, Error> {
    if denominator == 0.0 {
        Err(Error::ZeroDivision)
    } else {
        Ok(numerator / denominator)
    }
}

/// Sine and cosine have a more specific domain error than the other math functions.
pub(super) fn trig(value: f64, cosine: bool) -> Result<f64, Error> {
    let operation = if cosine {
        pymath::math::cos
    } else {
        pymath::math::sin
    };
    operation(value).map_err(|error| match error {
        pymath::Error::EDOM => Error::NonFinite(value),
        pymath::Error::ERANGE => Error::Range,
    })
}

pub(super) fn pow(base: f64, exponent: f64) -> Result<f64, Error> {
    pymath::math::pow(base, exponent).map_err(Error::from)
}

pub(super) fn fmod(value: f64, period: f64) -> Result<f64, Error> {
    pymath::math::fmod(value, period).map_err(Error::from)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn checked_operations_keep_python_failures() {
        assert_eq!(divide(1.0, 0.0), Err(Error::ZeroDivision));
        assert_eq!(divide(0.0, -0.0), Err(Error::ZeroDivision));
        assert!(matches!(
            trig(f64::INFINITY, false),
            Err(Error::NonFinite(_))
        ));
        assert!(matches!(
            trig(f64::NEG_INFINITY, true),
            Err(Error::NonFinite(_))
        ));
        assert_eq!(pow(2.0, 1024.0), Err(Error::Range));
        assert_eq!(pow(-0.5, 0.5), Err(Error::Domain));
        assert_eq!(fmod(f64::INFINITY, 1.0), Err(Error::Domain));
        assert_eq!(fmod(0.0, 0.0), Err(Error::Domain));
        assert!(fmod(f64::NAN, 1.0).expect("NaN propagates").is_nan());
        assert!(trig(f64::NAN, false).expect("NaN propagates").is_nan());
    }
}
