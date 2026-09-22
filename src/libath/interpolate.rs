//! The `athenaCL.libATH.interpolate` module: one-dimensional linear interpolation, in Rust.
//!
//! Port of `pysrc/athenaCL/libATH/_pyref/interpolate.py`, restructured: values are `f64`
//! throughout, where Python kept its int/float distinction — nothing imports the module, no
//! consumer ever read that typing, and the parity corpus compares values. What is not restructured
//! is the arithmetic: `pos` rounds twice as the Python expression did, rather than fusing, and the
//! unit steps accumulate one addition at a time, so the discrete values come out bit for bit.
//! Rounding follows Python's `round`: correctly rounded at the decimal digit, ties to even, which
//! is what Rust's `{:.digits}` formatting of a float does too.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.interpolate")]
pub(super) mod _inner {
    use std::iter;

    use rustpython_vm::{
        function::{ArgIntoFloat, OptionalArg},
        pyclass,
        types::Constructor,
        Py, PyObjectRef, PyPayload, PyResult, VirtualMachine,
    };

    /// `OneDimensionalLinear(start, end)`: linear interpolation between two values.
    #[pyattr]
    #[pyclass(name = "OneDimensionalLinear")]
    #[derive(Debug, PyPayload)]
    struct OneDimensionalLinear {
        min: f64,
        max: f64,
        span: f64,
        /// the values were given high end first, so discrete results run the other way
        flip: bool,
    }

    impl Constructor for OneDimensionalLinear {
        type Args = (ArgIntoFloat, ArgIntoFloat);

        fn py_new(
            _cls: &Py<rustpython_vm::builtins::PyType>,
            (start, end): Self::Args,
            _vm: &VirtualMachine,
        ) -> PyResult<Self> {
            let (start, end) = (f64::from(start), f64::from(end));
            let (min, max, flip) = if start <= end {
                (start, end, false)
            } else {
                (end, start, true)
            };
            Ok(Self {
                min,
                max,
                span: max - min,
                flip,
            })
        }
    }

    #[pyclass(flags(BASETYPE), with(Constructor))]
    impl OneDimensionalLinear {
        #[pygetset]
        fn min(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.min).into()
        }

        #[pygetset]
        fn max(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.max).into()
        }

        #[pygetset]
        fn span(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_float(self.span).into()
        }

        #[pygetset]
        fn flip(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_int(if self.flip { 1 } else { 0 }).into()
        }

        /// A value within the unit interval of the interpolation.
        #[pymethod]
        fn pos(&self, unit: ArgIntoFloat) -> f64 {
            // two roundings, as the Python expression computed it, not a fused multiply-add
            f64::from(unit) * self.span + self.min
        }

        /// A list of values between the two points.
        #[pymethod]
        fn discrete(
            &self,
            steps: isize,
            digits: OptionalArg<isize>,
            vm: &VirtualMachine,
        ) -> PyResult<PyObjectRef> {
            if steps < 2 {
                return Err(bare_value_error(vm));
            }
            let digits = digits.unwrap_or(2);
            // the unit steps accumulate one addition at a time, as the Python loop did
            let step_count = usize::try_from(steps - 1).unwrap_or(0);
            let inc = 1.0 / step_count as f64;
            let mut values: Vec<f64> = iter::successors(Some(0.0), |&i| Some(i + inc))
                .take(step_count)
                .map(|i| round_float(i * self.span + self.min, digits))
                .collect();
            // the high end is the last value, appended after the walk
            values.push(round_float(self.max, digits));
            if self.flip {
                values.reverse();
            }
            Ok(vm.ctx.new_list(values_to_objects(values, vm)).into())
        }
    }

    /// The floats as Python objects.
    fn values_to_objects(values: Vec<f64>, vm: &VirtualMachine) -> Vec<PyObjectRef> {
        values
            .into_iter()
            .map(|v| vm.ctx.new_float(v).into())
            .collect()
    }

    /// The bare `ValueError` the Python code raises for too few steps, with no message.
    fn bare_value_error(vm: &VirtualMachine) -> rustpython_vm::builtins::PyBaseExceptionRef {
        use rustpython_vm::convert::TryFromObject;

        let value_error: PyObjectRef = vm.ctx.exceptions.value_error.to_owned().into();
        value_error
            .call((), vm)
            .and_then(|obj| TryFromObject::try_from_object(vm, obj))
            .unwrap_or_else(|_| vm.new_value_error(""))
    }

    /// `round(float, digits)`: correctly rounded at the decimal digit, ties to even.
    fn round_float(value: f64, digits: isize) -> f64 {
        // beyond the digits a float can carry, rounding changes nothing
        if digits > 1080 {
            return value;
        }
        if digits >= 0 {
            let digits = usize::try_from(digits).unwrap_or(0);
            format!("{:.*}", digits, value).parse().unwrap_or(value)
        } else if digits < -308 {
            0.0
        } else {
            let scale = 10f64.powi(i32::try_from(-digits).unwrap_or(308));
            let scaled = value / scale;
            let rounded: f64 = format!("{:.0}", scaled).parse().unwrap_or(scaled);
            rounded * scale
        }
    }

    #[cfg(test)]
    mod tests {
        #![expect(
            clippy::float_cmp,
            reason = "the tests assert exact rounded values, not approximations"
        )]

        use super::round_float;

        #[test]
        fn floats_round_at_the_digit_ties_to_even() {
            assert_eq!(round_float(0.5, 0), 0.0);
            assert_eq!(round_float(1.5, 0), 2.0);
            assert_eq!(round_float(2.5, 0), 2.0);
            assert_eq!(round_float(3.5, 0), 4.0);
            assert_eq!(round_float(0.25, 1), 0.2);
            assert_eq!(round_float(0.35, 1), 0.3);
            assert_eq!(round_float(0.125, 2), 0.12);
            assert_eq!(round_float(-2.5, 0), -2.0);
            // 2.675 is 2.67499... in binary, so it rounds down
            assert_eq!(round_float(2.675, 2), 2.67);
        }

        #[test]
        fn floats_round_at_negative_digits() {
            assert_eq!(round_float(14.6, -1), 10.0);
            assert_eq!(round_float(15.0, -1), 20.0);
            assert_eq!(round_float(25.0, -1), 20.0);
            assert_eq!(round_float(149.0, -2), 100.0);
        }
    }
}
