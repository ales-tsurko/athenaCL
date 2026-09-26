//! Unit-interval tools, ported from `_pyref/unit.py`.
//!
//! Ordinary, exact built-in ints and floats use a typed Rust core. Big integers, numeric
//! subclasses, and user-defined objects keep RustPython's operation dispatch and ordering; iterable
//! inputs are consumed at the same points as the reference. The reference's dummy `Test` class is
//! omitted. A non-advancing built-in numeric `unitNormStep` raises `ValueError`, and built-in
//! numeric boundary walks stop when arithmetic cannot advance. User-defined numeric operations keep
//! the reference's dispatch behavior. `FunnelUnit` assumes its exposed derived arrays remain
//! mutually consistent after construction.

pub(crate) use self::python::module_def;

mod core;
mod python;
