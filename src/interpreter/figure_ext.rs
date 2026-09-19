//! Python bindings for figures.
//!
//! Graphics commands pass what they show (parameter values, texture events and time ranges,
//! cellular automaton cells) to these functions, which send it to the GUI as a
//! [`Figure`](crate::figure::Figure). The GUI draws them in its theme's colors.

use rustpython_vm::{pymodule, VirtualMachine};

use crate::interpreter;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "figureExt")]
pub(super) mod _inner {
    use std::sync::Arc;

    use rustpython_vm::{
        builtins::PyStrRef,
        function::{ArgIntoBool, ArgIntoFloat},
        PyObject, PyObjectRef, PyResult,
    };

    use super::*;
    use crate::figure::{
        Automaton, Domain, Ensemble, Event, Figure, Graph, Lane, Mark, Parameters, Texture,
    };

    /// `parameterMap(domain, detailed, graphs, events)`: parameter values, for `TPmap`,
    /// `TImap` and `TCmap`.
    ///
    /// `domain` is `"event"` or `"time"`, and `graphs` a list of `(title, coordinates)`. For
    /// events, coordinates are `(event, value)`; for time, `(start, value, end, value)`.
    ///
    /// `events` are the events the graphs describe, which the GUI can also show as a score:
    /// `(time, duration, sustain, accent, pitch, amplitude, tempo)`, with times in seconds, pitch
    /// in athenaCL's pitch space and tempo in beats per minute. It is empty for parameters
    /// alone.
    #[pyfunction(name = "parameterMap")]
    fn parameter_map(
        domain: PyStrRef,
        detailed: ArgIntoBool,
        graphs: PyObjectRef,
        events: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let domain = match domain.to_str().unwrap_or_default() {
            "event" => Domain::Events,
            "time" => Domain::Time,
            other => return Err(vm.new_value_error(format!("unknown domain: {other}"))),
        };
        let graphs = map(&graphs, vm, |graph| {
            let [title, coordinates] = items(&graph, vm)?;
            let marks = if vm.is_none(&coordinates) {
                Vec::new()
            } else {
                map(&coordinates, vm, |coordinate| {
                    let values = map(&coordinate, vm, |value| float(value, vm))?;
                    match values[..] {
                        [event, value] => Ok(Mark {
                            start: event,
                            end: event,
                            value,
                        }),
                        [start, value, end, _] => Ok(Mark { start, end, value }),
                        _ => Err(vm.new_value_error(format!(
                            "expected 2 or 4 coordinate values, got {}",
                            values.len()
                        ))),
                    }
                })?
            };
            Ok(Graph {
                title: string(title, vm)?,
                marks,
            })
        })?;
        let events = events_from(&events, vm)?;
        show(Figure::Parameters(Parameters {
            domain,
            detailed: detailed.into(),
            graphs,
            events,
        }));
        Ok(())
    }

    /// `ensembleMap(textures)`: textures and clones over time, for `TEmap`.
    ///
    /// `textures` is a list of `(name, start, end, muted, clones, events)`, where `clones` is a
    /// list of `(name, start, end, muted)` and `events` are the texture's, as `parameterMap`
    /// takes them.
    #[pyfunction(name = "ensembleMap")]
    fn ensemble_map(textures: PyObjectRef, vm: &VirtualMachine) -> PyResult<()> {
        let lane = |fields: [PyObjectRef; 4]| -> PyResult<Lane> {
            let [name, start, end, muted] = fields;
            Ok(Lane {
                name: string(name, vm)?,
                start: float(start, vm)?,
                end: float(end, vm)?,
                muted: muted.try_to_bool(vm)?,
            })
        };
        let textures = map(&textures, vm, |texture| {
            let [name, start, end, muted, clones, events] = items(&texture, vm)?;
            Ok(Texture {
                lane: lane([name, start, end, muted])?,
                clones: map(&clones, vm, |clone| lane(items(&clone, vm)?))?,
                events: events_from(&events, vm)?,
            })
        })?;
        show(Figure::Ensemble(Ensemble { textures }));
        Ok(())
    }

    /// `automatonMap(title, cells, max)`: generations of a cellular automaton, for `AUca`.
    ///
    /// `cells` is a list of generations, each a list of values. `max` is the largest value of a
    /// discrete automaton, or `None` for a continuous one.
    #[pyfunction(name = "automatonMap")]
    fn automaton_map(
        title: PyStrRef,
        cells: PyObjectRef,
        max: Option<ArgIntoFloat>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let cells = map(&cells, vm, |row| map(&row, vm, |value| float(value, vm)))?;
        show(Figure::Automaton(Automaton {
            title: title
                .to_str()
                .unwrap_or_default()
                .lines()
                .map(str::to_owned)
                .collect(),
            cells,
            max: max.map(Into::into),
        }));
        Ok(())
    }

    /// Read events as `(time, duration, sustain, accent, pitch, amplitude, tempo)`.
    fn events_from(events: &PyObject, vm: &VirtualMachine) -> PyResult<Vec<Event>> {
        map(events, vm, |event| {
            let [time, duration, sustain, accent, pitch, amplitude, tempo] = items(&event, vm)?;
            Ok(Event {
                time: float(time, vm)?,
                duration: float(duration, vm)?,
                sustain: float(sustain, vm)?,
                sounds: float(accent, vm)? > 0.0,
                pitch: float(pitch, vm)?,
                amplitude: float(amplitude, vm)?,
                tempo: float(tempo, vm)?,
            })
        })
    }

    fn show(figure: Figure) {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Figure(Arc::new(figure)))
            .expect("cannot send message via channel");
    }

    /// Convert each element of a Python sequence.
    fn map<T>(
        sequence: &PyObject,
        vm: &VirtualMachine,
        convert: impl FnMut(PyObjectRef) -> PyResult<T>,
    ) -> PyResult<Vec<T>> {
        vm.extract_elements_with(sequence, Ok)?
            .into_iter()
            .map(convert)
            .collect()
    }

    /// The elements of a sequence of exactly `N` items, such as a tuple of fields.
    fn items<const N: usize>(
        sequence: &PyObject,
        vm: &VirtualMachine,
    ) -> PyResult<[PyObjectRef; N]> {
        let items = vm.extract_elements_with(sequence, Ok)?;
        let count = items.len();
        items
            .try_into()
            .map_err(|_items| vm.new_value_error(format!("expected {N} items, got {count}")))
    }

    fn float(value: PyObjectRef, vm: &VirtualMachine) -> PyResult<f64> {
        value.try_into_value::<ArgIntoFloat>(vm).map(Into::into)
    }

    fn string(value: PyObjectRef, vm: &VirtualMachine) -> PyResult<String> {
        value
            .try_into_value::<PyStrRef>(vm)
            .map(|value| value.to_str().unwrap_or_default().to_owned())
    }
}
