//! Python's int/float distinction as a value type, for the ports whose consumers read it.
//!
//! athenaCL's parameter values flow into user-visible output, where Python writes an `int`
//! differently from a `float`, so ports on that path — `quantize`, `chaos` — keep the typing
//! instead of collapsing to `f64`. Integers wider than 128 bits overflow, where Python would keep
//! going with its big integers.

use std::cmp::Ordering;

use rustpython_vm::{
    builtins::{PyFloat, PyInt},
    convert::TryFromObject,
    PyObjectRef, PyResult, VirtualMachine,
};
use thiserror::Error;

/// An integer operation the Python side could not fail with its big integers.
#[derive(Debug, Error)]
#[error("int arithmetic overflowed the 128 bits the port carries")]
pub(crate) struct Overflow;

impl Overflow {
    /// The error as the `OverflowError` the boundary raises.
    pub(crate) fn into_exception(
        self,
        vm: &rustpython_vm::VirtualMachine,
    ) -> rustpython_vm::builtins::PyBaseExceptionRef {
        vm.new_overflow_error(self.to_string())
    }
}

/// A number that keeps Python's distinction between `int` and `float` results.
#[derive(Debug, Clone, Copy)]
pub(crate) enum Number {
    Int(i128),
    Float(f64),
}

impl TryFromObject for Number {
    fn try_from_object(vm: &VirtualMachine, obj: PyObjectRef) -> PyResult<Self> {
        Self::from_object(&obj, vm)
    }
}

impl Number {
    /// The `int` or `float` an argument carried, or a `TypeError` for anything else.
    pub(crate) fn from_object(obj: &PyObjectRef, vm: &VirtualMachine) -> PyResult<Self> {
        if let Some(int) = obj.downcast_ref::<PyInt>() {
            Ok(Self::Int(int.try_to_primitive::<i128>(vm)?))
        } else if let Some(float) = obj.downcast_ref::<PyFloat>() {
            Ok(Self::Float(float.to_f64()))
        } else {
            Err(vm.new_type_error("an int or float is required"))
        }
    }

    /// The number as Python sees it: an `int` object or a `float` object.
    pub(crate) fn as_object(self, vm: &VirtualMachine) -> PyObjectRef {
        match self {
            Self::Int(value) => vm.ctx.new_int(value).into(),
            Self::Float(value) => vm.ctx.new_float(value).into(),
        }
    }

    pub(crate) fn as_f64(self) -> f64 {
        match self {
            Self::Int(value) => value as f64,
            Self::Float(value) => value,
        }
    }

    /// The ordering Python finds between the two, which for mixed numbers is exact rather than
    /// float arithmetic — or `None`, when no comparison could place them, as a NaN places nothing.
    pub(crate) fn compare(self, other: Self) -> Option<Ordering> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => Some(a.cmp(&b)),
            (Self::Int(a), Self::Float(b)) => compare_int_float(a, b),
            (Self::Float(a), Self::Int(b)) => compare_int_float(b, a).map(Ordering::reverse),
            (Self::Float(a), Self::Float(b)) => a.partial_cmp(&b),
        }
    }

    /// `self < other`.
    pub(crate) fn below(self, other: Self) -> bool {
        matches!(self.compare(other), Some(Ordering::Less))
    }

    /// `self > other`.
    pub(crate) fn above(self, other: Self) -> bool {
        matches!(self.compare(other), Some(Ordering::Greater))
    }

    /// `self <= other`, as the Python comparison orders mixed numbers exactly.
    pub(crate) fn at_most(self, other: Self) -> bool {
        matches!(self.compare(other), Some(Ordering::Less | Ordering::Equal))
    }

    /// `self >= other`.
    pub(crate) fn at_least(self, other: Self) -> bool {
        other.at_most(self)
    }

    /// `self == other`, as Python finds mixed numbers equal when the values match.
    pub(crate) fn same_value(self, other: Self) -> bool {
        matches!(self.compare(other), Some(Ordering::Equal))
    }

    /// `self - other`, as Python types it: int minus int stays int.
    pub(crate) fn sub(self, other: Self) -> Result<Self, Overflow> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => a.checked_sub(b).map(Self::Int).ok_or(Overflow),
            (a, b) => Ok(Self::Float(a.as_f64() - b.as_f64())),
        }
    }

    /// `self + other`, as Python types it: int plus int stays int.
    pub(crate) fn add(self, other: Self) -> Result<Self, Overflow> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => a.checked_add(b).map(Self::Int).ok_or(Overflow),
            (a, b) => Ok(Self::Float(a.as_f64() + b.as_f64())),
        }
    }

    /// `self * other`, as Python types it: int times int stays int.
    pub(crate) fn mul(self, other: Self) -> Result<Self, Overflow> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => a.checked_mul(b).map(Self::Int).ok_or(Overflow),
            (a, b) => Ok(Self::Float(a.as_f64() * b.as_f64())),
        }
    }

    /// `abs(self)`, as Python types it; the one negative a 128-bit int cannot take upright.
    pub(crate) fn abs(self) -> Result<Self, Overflow> {
        match self {
            Self::Int(value) => value.checked_abs().map(Self::Int).ok_or(Overflow),
            Self::Float(value) => Ok(Self::Float(value.abs())),
        }
    }
}

/// The exact ordering between a 128-bit int and a float, where Python compares the int's full
/// precision against the float rather than rounding the int into float arithmetic.
fn compare_int_float(int: i128, float: f64) -> Option<Ordering> {
    if float.is_nan() {
        return None;
    }
    if float.is_infinite() {
        return Some(if float > 0.0 {
            Ordering::Less
        } else {
            Ordering::Greater
        });
    }
    // the first magnitude a 128-bit int cannot hold
    const TWO_TO_127: f64 = (1u128 << 127) as f64;
    let truncated = float.trunc();
    if truncated >= TWO_TO_127 {
        return Some(Ordering::Less);
    }
    // -2**127 is the exact i128::MIN and compares exactly; only beyond it is out of range
    if truncated < -TWO_TO_127 {
        return Some(Ordering::Greater);
    }
    // within the range, a truncated float is an exact integer
    let as_int = truncated as i128;
    Some(match int.cmp(&as_int) {
        Ordering::Equal if matches!(float.partial_cmp(&truncated), Some(Ordering::Equal)) => {
            Ordering::Equal
        }
        // the fraction decides, and it carries the float away from its truncation
        Ordering::Equal => {
            if float > truncated {
                Ordering::Less
            } else {
                Ordering::Greater
            }
        }
        order => order,
    })
}

#[cfg(test)]
mod tests {
    use std::cmp::Ordering;

    use super::{compare_int_float, Number};

    /// The ints that lose their identity in float arithmetic still compare exactly.
    #[test]
    fn mixed_comparisons_keep_int_precision() {
        // 2**53 + 1 rounds to 2**53 as a float, but is one greater
        assert_eq!(
            compare_int_float((1 << 53) + 1, 2f64.powi(53)),
            Some(Ordering::Greater)
        );
        assert_eq!(
            compare_int_float(1 << 53, 2f64.powi(53)),
            Some(Ordering::Equal)
        );
        assert_eq!(
            compare_int_float((1 << 53) - 1, 2f64.powi(53)),
            Some(Ordering::Less)
        );
        // fractions order against the integers around them
        assert_eq!(compare_int_float(3, 2.5), Some(Ordering::Greater));
        assert_eq!(compare_int_float(-3, -2.5), Some(Ordering::Less));
        assert_eq!(compare_int_float(2, 2.5), Some(Ordering::Less));
        // beyond the 128-bit range, magnitude decides
        assert_eq!(compare_int_float(i128::MAX, 1e40), Some(Ordering::Less));
        assert_eq!(compare_int_float(i128::MIN, -1e40), Some(Ordering::Greater));
        // the limits themselves compare exactly: i128::MIN is -2**127, and the largest
        // float i128::MAX can meet is one step of 2**74 below 2**127
        assert_eq!(
            compare_int_float(i128::MIN, -(2.0f64.powi(127))),
            Some(Ordering::Equal)
        );
        assert_eq!(
            compare_int_float(i128::MAX, 2.0f64.powi(127) - 2.0f64.powi(74)),
            Some(Ordering::Greater)
        );
        // one float step past the negative limit is beyond the range — a step there is 2**75, the
        // binade's spacing, so it is taken with next_down rather than added
        assert_eq!(
            compare_int_float(i128::MIN, (-2.0f64.powi(127)).next_down()),
            Some(Ordering::Greater)
        );
        assert_eq!(
            compare_int_float(i128::MIN, 2.0f64.powi(127).next_up()),
            Some(Ordering::Less)
        );
        // a NaN places nothing
        assert_eq!(compare_int_float(0, f64::NAN), None);
    }

    /// The public relations carry the exact ordering, NaN included.
    #[test]
    fn relations_agree_with_python() {
        let big = Number::Int((1 << 53) + 1);
        let exact = Number::Float(2f64.powi(53));
        assert!(big.at_least(exact));
        assert!(!big.same_value(exact));
        let nan = Number::Float(f64::NAN);
        assert!(!nan.same_value(nan));
        assert!(!nan.at_most(Number::Int(0)));
        assert!(!nan.at_least(Number::Int(0)));
    }
}
