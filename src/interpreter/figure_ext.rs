//! Python bindings for figures.
//!
//! Graphics commands pass what they show (parameter values, texture time ranges, cellular automaton
//! cells) to these functions, which send it to the GUI as a [`Figure`](crate::figure::Figure).

use rustpython_vm::{pymodule, VirtualMachine};

use crate::interpreter;

pub(crate) fn make_module(vm: &mut VirtualMachine) {
    vm.add_native_module("figureExt", Box::new(_inner::make_module));
}

#[pymodule]
pub(super) mod _inner {
    use std::sync::Arc;

    use rustpython_vm::{
        builtins::{PyDictRef, PyStrRef},
        function::{ArgIntoBool, ArgIntoFloat},
        PyObject, PyObjectRef, PyResult,
    };

    use super::*;
    use crate::figure::{
        Automaton, Domain, Ensemble, Figure, Graph, Lane, Mark, Palette, Parameters, Rgb, Texture,
    };

    /// `parameterMap(palette, domain, detailed, graphs)`: parameter values, for `TPmap`,
    /// `TImap` and `TCmap`.
    ///
    /// `domain` is `"event"` or `"time"`, and `graphs` a list of `(title, coordinates)`. For
    /// events, coordinates are `(event, value)`; for time, `(start, value, end, value)`.
    #[pyfunction(name = "parameterMap")]
    fn parameter_map(
        palette: PyDictRef,
        domain: PyStrRef,
        detailed: ArgIntoBool,
        graphs: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let domain = match domain.as_str() {
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
        show(Figure::Parameters(Parameters {
            palette: palette_from(&palette, vm)?,
            domain,
            detailed: detailed.into(),
            graphs,
        }));
        Ok(())
    }

    /// `ensembleMap(palette, textures)`: textures and clones over time, for `TEmap`.
    ///
    /// `textures` is a list of `(name, start, end, muted, clones)`, where `clones` is a list of
    /// `(name, start, end, muted)`.
    #[pyfunction(name = "ensembleMap")]
    fn ensemble_map(
        palette: PyDictRef,
        textures: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
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
            let [name, start, end, muted, clones] = items(&texture, vm)?;
            Ok(Texture {
                lane: lane([name, start, end, muted])?,
                clones: map(&clones, vm, |clone| lane(items(&clone, vm)?))?,
            })
        })?;
        show(Figure::Ensemble(Ensemble {
            palette: palette_from(&palette, vm)?,
            textures,
        }));
        Ok(())
    }

    /// `automatonMap(palette, title, cells, max)`: generations of a cellular automaton, for
    /// `AUca`.
    ///
    /// `cells` is a list of generations, each a list of values. `max` is the largest value of a
    /// discrete automaton, or `None` for a continuous one.
    #[pyfunction(name = "automatonMap")]
    fn automaton_map(
        palette: PyDictRef,
        title: PyStrRef,
        cells: PyObjectRef,
        max: Option<ArgIntoFloat>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let cells = map(&cells, vm, |row| map(&row, vm, |value| float(value, vm)))?;
        show(Figure::Automaton(Automaton {
            palette: palette_from(&palette, vm)?,
            title: title.as_str().lines().map(str::to_owned).collect(),
            cells,
            max: max.map(Into::into),
        }));
        Ok(())
    }

    fn show(figure: Figure) {
        interpreter::INTERPRETER_WORKER
            .gui_sender
            .send_blocking(interpreter::Message::Figure(Arc::new(figure)))
            .expect("cannot send message via channel");
    }

    /// Read the colors from a dict of `#rrggbb` strings.
    fn palette_from(palette: &PyDictRef, vm: &VirtualMachine) -> PyResult<Palette> {
        let color = |key: &str| -> PyResult<Rgb> {
            let value = string(palette.get_item(key, vm)?, vm)?;
            Rgb::parse(&value)
                .ok_or_else(|| vm.new_value_error(format!("invalid {key} color: {value}")))
        };
        Ok(Palette {
            background: color("background")?,
            grid: color("grid")?,
            margin: color("margin")?,
            main: color("main")?,
            main_frame: color("mainFrame")?,
            alt: color("alt")?,
            alt_frame: color("altFrame")?,
            title: color("title")?,
            label: color("label")?,
            unit: color("unit")?,
        })
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
            .map(|value| value.as_str().to_owned())
    }
}
