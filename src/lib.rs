//! athenaCL is an algorithmic music composition tool.

pub use interpreter::init_py_interpreter;

pub mod app;
mod figure;
mod interpreter;
mod libath;
pub mod manual;

#[cfg(test)]
#[path = "../tests/support/mod.rs"]
mod test_support;
