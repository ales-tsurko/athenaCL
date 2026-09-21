//! athenaCL is an algorithmic music composition tool.

pub use interpreter::{init_py_interpreter, init_scratch_prefs};

pub mod app;
mod figure;
mod interpreter;
pub mod manual;
