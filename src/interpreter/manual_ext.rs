//! `manualExt`: what `AUdoc` calls to put the manual in the log.
//!
//! Python only passes on what was typed after the command; reading the manual, searching it and
//! deciding what to show are all on this side.

use rustpython_vm::pymodule;

use crate::manual;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "manualExt")]
pub(super) mod _inner {
    use rustpython_vm::{PyResult, VirtualMachine};

    use super::told;
    use crate::{interpreter, manual};

    /// Show what `arguments` ask for, and return the line the command prints.
    #[pyfunction(name = "show")]
    pub(crate) fn show(arguments: String, vm: &VirtualMachine) -> PyResult<String> {
        let request = manual::Request::parse(&arguments);
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Manual(request.clone()))
            .map_err(|_err| vm.new_runtime_error("cannot send message to the GUI".to_owned()))?;
        Ok(told(&request))
    }
}

/// What the command says it did, under the page itself.
fn told(request: &manual::Request) -> String {
    match request {
        manual::Request::Contents => {
            "enter AUdoc with a chapter number to read it, or with words to search\n".to_owned()
        }
        manual::Request::Chapter(_) => "AUdoc display complete.\n".to_owned(),
        manual::Request::Search(words) => {
            format!("searched the manual for {}\n", words.join(" "))
        }
        manual::Request::Web => "on-line documentation opened.\n".to_owned(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_request_is_told_on_a_line_of_its_own() {
        for request in [
            manual::Request::Contents,
            manual::Request::Chapter(1),
            manual::Request::Search(vec!["texture".to_owned()]),
            manual::Request::Web,
        ] {
            let line = told(&request);
            assert!(
                line.ends_with('\n') && line.trim().len() > 1,
                "{request:?}: {line:?}"
            );
        }
    }
}
