//! Ports of `pysrc/athenaCL/libATH` modules, in Rust.
//!
//! A ported module keeps its Python import path: `athenaCL.libATH.error` is the Rust
//! `src/libath/error.rs`, registered as a native RustPython module where the `.py` file was. The
//! original implementation moves to `pysrc/athenaCL/libATH/_pyref/` as the reference, and
//! `tests/parity.py` calls the port and the reference with the same inputs, so a port cannot change
//! behavior unnoticed.
//!
//! Ports restructure rather than transliterate: the core is idiomatic Rust with natural types —
//! generic iterators, `usize` widths, `f64` values — and the module is a thin boundary that keeps
//! the Python contract: names, arguments, result shapes and ordering. Arithmetic that produces
//! user-visible values is kept operation for operation, so results come out identical; where a
//! Python quirk had no consumer reading it (an int/float typing, an error raised by running off a
//! recursion), the port normalizes it, says so in its docs, and the parity corpus states the
//! narrowing.

pub(crate) mod error;
pub(crate) mod interpolate;
pub(crate) mod permutate;
