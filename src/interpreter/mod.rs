//! athenaCL interpreter.
pub use interpreter::*;

mod athena_obj_ext;
mod dialog_ext;
mod figure_ext;
#[expect(
    clippy::module_inception,
    reason = "the module is the `interpreter` module's core"
)]
mod interpreter;
mod sndhdr;
mod xml_tools_ext;
