//! Arithmetic for ordinary Python ints and floats, independent of the interpreter.
//!
//! The boundary uses this only for exact built-in numbers representable by `Number`. Big integers,
//! subclasses, and user-defined objects retain RustPython dispatch.

use crate::libath::number::Number;

pub(super) fn normalize(value: Number, low: Number, span: Number) -> Option<Number> {
    let difference = value.sub(low).ok()?;
    if span.same_value(Number::Int(0)) {
        Some(Number::Int(0))
    } else {
        Some(Number::Float(difference.as_f64() / span.as_f64()))
    }
}

pub(super) fn denormalize(value: Number, low: Number, span: Number) -> Option<Number> {
    Number::Float(value.as_f64()).mul(span).ok()?.add(low).ok()
}

pub(super) fn interpolate(value: Number, a: Number, b: Number) -> Option<Number> {
    let complement = Number::Int(1).sub(value).ok()?;
    a.mul(complement).ok()?.add(b.mul(value).ok()?).ok()
}

pub(super) fn mean(a: Number, b: Number) -> Option<Number> {
    a.add(b).ok()?.mul(Number::Float(0.5)).ok()
}

pub(super) fn limit(value: Number) -> Option<Number> {
    if value.above(Number::Int(1)) {
        Some(Number::Int(1))
    } else if value.below(Number::Int(0)) {
        Some(Number::Int(0))
    } else {
        None
    }
}

pub(super) fn equal_part(parts: usize, index: usize) -> Number {
    if index + 1 == parts {
        Number::Int(1)
    } else {
        Number::Float(index as f64 * (1.0 / (parts - 1) as f64))
    }
}

pub(super) fn equal_bound(parts: usize, face: usize, low: Number) -> (Number, Number, Number) {
    let step = 1.0 / parts as f64;
    let half = step * 0.5;
    let high = if face + 1 == parts {
        Number::Float(1.0)
    } else {
        Number::Float(step * (face + 1) as f64)
    };
    let middle = Number::Float(low.as_f64() + half);
    (low, middle, high)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ordinary_numeric_results_keep_python_types_and_order() {
        assert!(matches!(
            normalize(Number::Int(5), Number::Int(5), Number::Int(0)),
            Some(Number::Int(0))
        ));
        assert!(matches!(
            normalize(Number::Int(3), Number::Int(3), Number::Int(7)),
            Some(Number::Float(0.0))
        ));
        assert!(matches!(
            interpolate(Number::Float(0.5), Number::Int(10), Number::Int(20)),
            Some(Number::Float(15.0))
        ));
        assert!(matches!(
            denormalize(Number::Float(0.5), Number::Int(10), Number::Int(20)),
            Some(Number::Float(20.0))
        ));
        assert!(matches!(
            mean(Number::Int(0), Number::Int(1)),
            Some(Number::Float(0.5))
        ));
        assert!(matches!(limit(Number::Float(2.0)), Some(Number::Int(1))));
        assert!(limit(Number::Float(f64::NAN)).is_none());
        assert!(interpolate(Number::Int(i128::MAX), Number::Int(2), Number::Int(3)).is_none());
    }

    #[test]
    fn partitions_keep_endpoint_types() {
        let parts: Vec<_> = (0..3).map(|index| equal_part(3, index)).collect();
        assert!(matches!(
            parts.as_slice(),
            [Number::Float(0.0), Number::Float(0.5), Number::Int(1)]
        ));
        let mut low = Number::Int(0);
        let bounds: Vec<_> = (0..3)
            .map(|face| {
                let bound = equal_bound(3, face, low);
                low = bound.2;
                bound
            })
            .collect();
        assert!(matches!(bounds[0].0, Number::Int(0)));
        assert!(matches!(bounds[2].2, Number::Float(1.0)));
    }
}
