//! The `athenaCL.libATH.quantize` module: funneling and grid quantization, in Rust.
//!
//! Port of `pysrc/athenaCL/libATH/_pyref/quantize.py`, restructured: the grid walk and the funnel
//! are plain functions over [`Number`](crate::libath::number::Number), testable without an
//! interpreter, and the module is a thin boundary keeping the Python names, keyword arguments, and
//! the int/float typing of results, which athenaCL's parameter objects read into user-visible
//! output. The walk sorts its two endpoints stably, as Python's sort did, so an exact boundary
//! keeps the reference's type; equal or unorderable funnel boundaries both collapse to the first
//! one, as the Python `else` did.
//!
//! Narrowings, none read by anything in athenaCL: the walk gives up as `None` where the Python code
//! died on an unbound direction (a NaN fill), it does not print its debug line, and the exposed
//! state — the grid, the loop limit, the map values — is read-only where Python's was writable.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

/// The grid walk and the funnel, over Python-typed numbers.
mod core {
    use std::cmp::Ordering;

    use super::super::number::{Number, Overflow};

    /// Where a value at the threshold funnels to.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub(crate) enum Direction {
        /// the threshold itself
        Match,
        /// the higher boundary
        Upper,
        /// the lower boundary
        Lower,
    }

    /// Take boundary levels `a` and `b` and place `f` in relation to the threshold `h`: a value
    /// below takes the lower boundary, above the higher, and at the threshold the direction
    /// decides. Equal or unorderable boundaries collapse to the first one, and a direction Python
    /// would not recognize — or a value no comparison could place — leaves the value nowhere, as
    /// the Python chain fell through.
    pub(crate) fn funnel(
        h: &Number,
        a: &Number,
        b: &Number,
        f: &Number,
        direction: Option<Direction>,
    ) -> Option<Number> {
        let (low, high) = match a.compare(*b) {
            Some(Ordering::Greater) => (*b, *a),
            Some(Ordering::Less) => (*a, *b),
            // equal, or beyond comparison: both boundaries are the first one
            _ => (*a, *a),
        };
        match f.compare(*h) {
            Some(Ordering::Greater) => Some(high),
            Some(Ordering::Less) => Some(low),
            Some(Ordering::Equal) => match direction {
                Some(Direction::Match) => Some(*h),
                Some(Direction::Upper) => Some(high),
                Some(Direction::Lower) => Some(low),
                None => None,
            },
            None => None,
        }
    }

    /// A grid of interval steps, walked from a reference value in either direction to find the two
    /// consecutive steps that bracket a value.
    #[derive(Debug)]
    pub(crate) struct Grid {
        /// the interval steps, cycled through as the walk goes
        steps: Vec<Number>,
        /// how many steps to try before giving up
        loop_limit: usize,
    }

    impl Grid {
        pub(crate) fn new(steps: Vec<Number>, loop_limit: usize) -> Self {
            Self { steps, loop_limit }
        }

        /// The steps, as the Python grid attribute held them.
        pub(crate) fn steps(&self) -> &[Number] {
            &self.steps
        }

        /// The bracketing pair of walk steps around the value, walking down from a reference at or
        /// above it and up from one below. The up walk starts one step into the cycle and the down
        /// walk at the end, as the Python indices did; the pair keeps the walk's own order when the
        /// two steps compare equal, as Python's stable sort did.
        pub(crate) fn bracket(
            &self,
            value: &Number,
            reference: &Number,
        ) -> Result<Option<(Number, Number)>, Overflow> {
            let down = !value.above(*reference);
            let deltas: Box<dyn Iterator<Item = &Number>> = if down {
                Box::new(self.steps.iter().rev().cycle())
            } else {
                Box::new(self.steps.iter().cycle().skip(1))
            };
            let mut previous = *reference;
            for (i, delta) in deltas.enumerate() {
                let step = if down {
                    previous.sub(*delta)?
                } else {
                    previous.add(*delta)?
                };
                let (low, high) = if step.below(previous) {
                    (step, previous)
                } else {
                    (previous, step)
                };
                if low.at_most(*value) && value.at_most(high) {
                    return Ok(Some((low, high)));
                }
                previous = step;
                // the Python walk gave up once its counter passed the loop limit
                if i + 2 >= self.loop_limit {
                    return Ok(None);
                }
            }
            Ok(None)
        }

        /// The value pulled toward the grid point around it. A pull of 1 lands on the point; any
        /// other pull moves away from it by the un-pulled share of the distance, which a tie
        /// between the two boundaries resolves upward, as the Python comparison did.
        pub(crate) fn attract(
            &self,
            fill: &Number,
            pull: &Number,
            reference: &Number,
        ) -> Result<Option<Number>, Overflow> {
            let Some((lower, upper)) = self.bracket(fill, reference)? else {
                return Ok(None);
            };
            if lower.same_value(upper) {
                return Ok(Some(lower));
            }
            let dif_lower = lower.sub(*fill)?.abs()?;
            let dif_upper = upper.sub(*fill)?.abs()?;
            let (point, upward, measure) = if dif_lower.at_least(dif_upper) {
                (upper, true, dif_upper)
            } else {
                (lower, false, dif_lower)
            };
            if pull.same_value(Number::Int(1)) {
                return Ok(Some(point));
            }
            let deviate = measure.mul(Number::Int(1).sub(*pull)?)?;
            let pulled = if upward {
                point.sub(deviate)?
            } else {
                point.add(deviate)?
            };
            Ok(Some(pulled))
        }
    }
}

#[pymodule(name = "athenaCL.libATH.quantize")]
pub(super) mod _inner {
    use rustpython_vm::{
        builtins::{PyStr, PyType},
        common::lock::PyRwLock,
        function::OptionalArg,
        pyclass,
        types::Constructor,
        FromArgs, Py, PyObjectRef, PyPayload, PyResult, VirtualMachine,
    };

    use super::core::{self, Direction, Grid};
    use crate::libath::number::Number;

    /// `funnelBinary(h, a, b, f, hDirection)`: place `f` between the boundaries `a` and `b` at or
    /// around the threshold `h`. The direction is any object; only the strings Python compared
    /// against are recognized, and anything else leaves a threshold value nowhere.
    #[pyfunction(name = "funnelBinary")]
    fn funnel_binary(args: FunnelArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let FunnelArgs {
            h,
            a,
            b,
            f,
            h_direction,
        } = args;
        let direction = h_direction
            .downcast_ref::<PyStr>()
            .and_then(|name| match name.to_str() {
                Some("match") => Some(Direction::Match),
                Some("upper") => Some(Direction::Upper),
                Some("lower") => Some(Direction::Lower),
                _ => None,
            });
        let funneled = core::funnel(&h, &a, &b, &f, direction);
        Ok(funneled.map_or_else(|| vm.ctx.none(), |value| value.as_object(vm)))
    }

    /// The arguments of `funnelBinary`.
    #[derive(FromArgs)]
    struct FunnelArgs {
        #[pyarg(any)]
        h: Number,
        #[pyarg(any)]
        a: Number,
        #[pyarg(any)]
        b: Number,
        #[pyarg(any)]
        f: Number,
        #[pyarg(any, name = "hDirection")]
        h_direction: PyObjectRef,
    }

    /// `Quantizer(looplimit)`: quantizes values onto a grid of interval steps.
    #[pyattr]
    #[pyclass(name = "Quantizer")]
    #[derive(Debug, PyPayload)]
    struct PyQuantizer {
        /// the grid, absent until `updateGrid` supplies one
        grid: PyRwLock<Option<Grid>>,
        loop_limit: usize,
    }

    /// The arguments of the Quantizer constructor.
    #[derive(FromArgs)]
    struct QuantizerArgs {
        #[pyarg(any, optional)]
        looplimit: OptionalArg<isize>,
    }

    impl Constructor for PyQuantizer {
        type Args = QuantizerArgs;

        fn py_new(_cls: &Py<PyType>, args: Self::Args, _vm: &VirtualMachine) -> PyResult<Self> {
            // a limit at or below zero gives up after the first step, as Python's did
            let loop_limit = usize::try_from(args.looplimit.unwrap_or(999)).unwrap_or(0);
            Ok(Self {
                grid: PyRwLock::new(None),
                loop_limit,
            })
        }
    }

    /// The arguments of `updateGrid`.
    #[derive(FromArgs)]
    struct GridArgs {
        #[pyarg(any)]
        grid: PyObjectRef,
    }

    /// The arguments of `attract`.
    #[derive(FromArgs)]
    struct AttractArgs {
        #[pyarg(any)]
        fill: Number,
        #[pyarg(any, optional)]
        pull: OptionalArg<Number>,
        #[pyarg(any, name = "gridRef", optional)]
        grid_ref: OptionalArg<Number>,
    }

    #[pyclass(flags(BASETYPE), with(Constructor))]
    impl PyQuantizer {
        /// The loop limit, as the Python `LOOPLIMIT` attribute held it.
        #[pygetset(name = "LOOPLIMIT")]
        fn loop_limit(&self, vm: &VirtualMachine) -> PyObjectRef {
            vm.ctx.new_int(self.loop_limit).into()
        }

        /// The grid steps, or `None` before `updateGrid` supplies them.
        #[pygetset]
        fn grid(&self, vm: &VirtualMachine) -> PyObjectRef {
            let grid = self.grid.read();
            match grid.as_ref() {
                None => vm.ctx.none(),
                Some(grid) => vm
                    .ctx
                    .new_list(grid.steps().iter().map(|step| step.as_object(vm)).collect())
                    .into(),
            }
        }

        /// Supply the grid, as interval steps; it can be renewed on every attraction.
        #[pymethod(name = "updateGrid")]
        fn update_grid(&self, args: GridArgs, vm: &VirtualMachine) -> PyResult<()> {
            let steps: Vec<Number> =
                rustpython_vm::convert::TryFromObject::try_from_object(vm, args.grid)?;
            if steps.is_empty() {
                // the Python message, which says "more than 1" but means any
                return Err(vm.new_value_error("grid must have more than 1 value"));
            }
            *self.grid.write() = Some(Grid::new(steps, self.loop_limit));
            Ok(())
        }

        /// Pull `fill` onto the grid around it, `pull` of the way, from a grid shifted to
        /// `gridRef`.
        #[pymethod]
        fn attract(&self, args: AttractArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            let pull = args.pull.unwrap_or(Number::Int(1));
            let grid_ref = args.grid_ref.unwrap_or(Number::Int(0));
            let grid = self.grid.read();
            let Some(grid) = grid.as_ref() else {
                // the Python code asked len() of the grid it did not have
                return Err(vm.new_type_error("object of type 'NoneType' has no len()"));
            };
            let attracted = grid
                .attract(&args.fill, &pull, &grid_ref)
                .map_err(|error| error.into_exception(vm))?;
            Ok(attracted.map_or_else(|| vm.ctx.none(), |value| value.as_object(vm)))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::core::{funnel, Direction, Grid};
    use crate::libath::number::Number;

    #[test]
    fn funnel_places_below_above_and_at_the_threshold() {
        let h = Number::Int(10);
        let (a, b) = (Number::Int(1), Number::Int(20));
        assert!(matches!(
            funnel(&h, &a, &b, &Number::Int(15), Some(Direction::Match)),
            Some(Number::Int(20))
        ));
        assert!(matches!(
            funnel(&h, &a, &b, &Number::Int(5), Some(Direction::Match)),
            Some(Number::Int(1))
        ));
        // at the threshold, the direction decides
        assert!(matches!(
            funnel(&h, &a, &b, &Number::Int(10), Some(Direction::Match)),
            Some(Number::Int(10))
        ));
        assert!(matches!(
            funnel(&h, &a, &b, &Number::Int(10), Some(Direction::Upper)),
            Some(Number::Int(20))
        ));
        assert!(matches!(
            funnel(&h, &a, &b, &Number::Int(10), Some(Direction::Lower)),
            Some(Number::Int(1))
        ));
        // boundaries given high first
        assert!(matches!(
            funnel(
                &h,
                &Number::Int(20),
                &Number::Int(1),
                &Number::Int(10),
                Some(Direction::Lower)
            ),
            Some(Number::Int(1))
        ));
        // a float threshold funnels to itself
        assert!(matches!(
            funnel(
                &Number::Float(10.0),
                &a,
                &b,
                &Number::Int(10),
                Some(Direction::Match)
            ),
            Some(Number::Float(_))
        ));
        // a direction Python would not recognize leaves the value nowhere
        assert!(funnel(&h, &a, &b, &Number::Int(10), None).is_none());
    }

    /// Equal boundaries collapse to the first one, however the equality compares, and unorderable
    /// boundaries do too; a value no comparison could place goes nowhere.
    #[test]
    fn funnel_keeps_the_first_boundary_on_ties() {
        // 1 and 1.0 compare equal: both boundaries are the first, an int
        assert!(matches!(
            funnel(
                &Number::Int(0),
                &Number::Int(1),
                &Number::Float(1.0),
                &Number::Int(-1),
                Some(Direction::Lower)
            ),
            Some(Number::Int(1))
        ));
        assert!(matches!(
            funnel(
                &Number::Int(0),
                &Number::Float(1.0),
                &Number::Int(1),
                &Number::Int(-1),
                Some(Direction::Lower)
            ),
            Some(Number::Float(1.0))
        ));
        // a NaN boundary cannot be ordered against: both are the first, the NaN
        assert!(matches!(
            funnel(&Number::Int(0), &Number::Float(f64::NAN), &Number::Int(1), &Number::Int(1), Some(Direction::Upper)),
            Some(Number::Float(value)) if value.is_nan()
        ));
        // ints that float arithmetic would blur still compare exactly
        assert!(matches!(
            funnel(
                &Number::Float(9007199254740992.0),
                &Number::Int(1),
                &Number::Int(20),
                &Number::Int(9007199254740993),
                Some(Direction::Match)
            ),
            Some(Number::Int(20))
        ));
        // a NaN value goes nowhere, whatever the direction
        assert!(funnel(
            &Number::Int(10),
            &Number::Int(1),
            &Number::Int(20),
            &Number::Float(f64::NAN),
            Some(Direction::Match)
        )
        .is_none());
    }

    /// The goldens are the values the Python reference produces, types included.
    #[test]
    fn grids_attract_to_walked_boundaries() {
        let grid = Grid::new(vec![Number::Int(1), Number::Int(2), Number::Int(3)], 999);
        let attracted = |fill, pull, reference| {
            grid.attract(&fill, &pull, &reference)
                .expect("the walk stays within int range")
                .expect("the walk brackets the value")
        };
        assert!(matches!(
            attracted(Number::Int(5), Number::Int(1), Number::Int(0)),
            Number::Int(5)
        ));
        assert!(matches!(
            attracted(Number::Float(3.5), Number::Int(1), Number::Int(0)),
            Number::Int(5)
        ));
        assert!(matches!(
            attracted(Number::Int(10), Number::Int(1), Number::Int(0)),
            Number::Int(11)
        ));
        assert!(matches!(
            attracted(Number::Int(-4), Number::Int(1), Number::Int(0)),
            Number::Int(-3)
        ));
        assert!(matches!(
            attracted(Number::Int(0), Number::Int(1), Number::Int(0)),
            Number::Int(0)
        ));
        // a pull short of 1 leaves part of the distance, and crosses into float
        assert!(matches!(
            attracted(Number::Float(3.5), Number::Int(0), Number::Int(0)),
            Number::Float(3.5)
        ));
        assert!(matches!(
            attracted(Number::Float(3.5), Number::Float(0.5), Number::Int(0)),
            Number::Float(4.25)
        ));
        assert!(matches!(
            attracted(Number::Float(3.5), Number::Float(1.5), Number::Int(0)),
            Number::Float(5.75)
        ));
        // a shifted reference walks the same grid from elsewhere
        assert!(matches!(
            attracted(Number::Int(5), Number::Int(1), Number::Int(10)),
            Number::Int(5)
        ));
        assert!(matches!(
            attracted(Number::Int(5), Number::Int(1), Number::Int(-10)),
            Number::Int(4)
        ));
    }

    /// A tie between the boundaries resolves upward, as the Python comparison did.
    #[test]
    fn ties_attract_upward() {
        let grid = Grid::new(vec![Number::Float(0.5), Number::Float(1.5)], 999);
        let attracted = |fill| {
            grid.attract(&fill, &Number::Int(1), &Number::Int(0))
                .expect("brackets")
                .expect("in range")
        };
        assert!(matches!(attracted(Number::Float(1.0)), Number::Float(1.5)));
        assert!(matches!(attracted(Number::Float(2.25)), Number::Float(2.0)));
        assert!(matches!(attracted(Number::Float(2.75)), Number::Float(3.5)));
    }

    /// The walk keeps its own endpoint order where the two compare equal, as Python's stable sort
    /// did, so an exact boundary keeps the reference's type.
    #[test]
    fn exact_boundaries_keep_the_walks_type() {
        let grid = Grid::new(vec![Number::Float(0.0)], 999);
        let attracted = grid
            .attract(&Number::Int(0), &Number::Int(1), &Number::Int(0))
            .expect("in range")
            .expect("brackets");
        assert!(matches!(attracted, Number::Int(0)));
    }

    #[test]
    fn walks_give_up_at_the_loop_limit() {
        // a zero step never moves the walk, so nothing is ever bracketed
        let stuck = Grid::new(vec![Number::Int(0)], 4);
        let attracted = stuck
            .attract(&Number::Int(5), &Number::Int(1), &Number::Int(0))
            .expect("in range");
        assert!(attracted.is_none());

        // a single step brackets anything the walk reaches, exactly at a boundary too
        let sevens = Grid::new(vec![Number::Int(7)], 999);
        let attracted = |fill| {
            sevens
                .attract(&fill, &Number::Int(1), &Number::Int(0))
                .expect("in range")
                .expect("brackets")
        };
        assert!(matches!(attracted(Number::Int(20)), Number::Int(21)));
        assert!(matches!(attracted(Number::Int(7)), Number::Int(7)));
    }
}
