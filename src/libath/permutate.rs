//! The `athenaCL.libATH.permutate` module: permutation utilities, in Rust.
//!
//! Port of `pysrc/athenaCL/libATH/_pyref/permutate.py`, restructured: the algorithms are generic
//! lazy iterators over any cloneable items — plain Rust, testable without a interpreter — and the
//! module is a thin boundary keeping the Python names, result lists, and result ordering. The
//! generator functions return single-pass iterators, as generators are. Python's negative widths,
//! where its recursion ran off the end of the list or the recursion limit, are mapped to the errors
//! it died with.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.permutate")]
pub(super) mod _inner {
    use std::iter;

    use rustpython_vm::{
        common::lock::PyMutex,
        convert::TryFromObject,
        protocol::PyIterReturn,
        pyclass,
        types::{IterNext, Iterable, SelfIter},
        Py, PyObjectRef, PyPayload, PyResult, VirtualMachine,
    };

    /// Ordered selections of `n` items, each used at most once.
    fn combinations<T>(items: Vec<T>, n: usize) -> Box<dyn Iterator<Item = Vec<T>>>
    where
        T: Clone + 'static,
    {
        branched_walk(items, n, without)
    }

    /// Ordered selections of `n` items, each usable any number of times.
    fn selections<T>(items: Vec<T>, n: usize) -> Box<dyn Iterator<Item = Vec<T>>>
    where
        T: Clone + 'static,
    {
        match n {
            0 => Box::new(iter::once(Vec::new())),
            _ => Box::new(items.clone().into_iter().flat_map(move |item| {
                selections(items.clone(), n - 1).map(move |tail| once_then(item.clone(), tail))
            })),
        }
    }

    /// Selections of `n` items in the given order, each used at most once. Python walked a range
    /// bound as an optimization; taking each item with the items after it is the same walk, and
    /// widths that cannot be filled simply yield nothing.
    fn unique_combinations<T>(items: Vec<T>, n: usize) -> Box<dyn Iterator<Item = Vec<T>>>
    where
        T: Clone + 'static,
    {
        branched_walk(items, n, after)
    }

    /// Selections built by walking each item as the first, with the items it leaves for the
    /// tail. The `rest_of` decides which items a first item leaves, which is the whole
    /// difference between selection kinds.
    fn branched_walk<T>(
        items: Vec<T>,
        n: usize,
        rest_of: fn(&[T], usize) -> Vec<T>,
    ) -> Box<dyn Iterator<Item = Vec<T>>>
    where
        T: Clone + 'static,
    {
        match n {
            0 => Box::new(iter::once(Vec::new())),
            _ => {
                // one branch per first item: the first item and the rest to fill from
                let branches: Vec<_> = items
                    .iter()
                    .enumerate()
                    .map(|(i, item)| (item.clone(), rest_of(&items, i)))
                    .collect();
                Box::new(branches.into_iter().flat_map(move |(item, rest)| {
                    branched_walk(rest, n - 1, rest_of)
                        .map(move |tail| once_then(item.clone(), tail))
                }))
            }
        }
    }

    /// The items without the one at the position.
    fn without<T: Clone>(items: &[T], i: usize) -> Vec<T> {
        let mut rest = items.to_vec();
        rest.remove(i);
        rest
    }

    /// The items after the one at the position.
    fn after<T: Clone>(items: &[T], i: usize) -> Vec<T> {
        items.iter().skip(i + 1).cloned().collect()
    }

    /// `item` followed by the tail.
    fn once_then<T>(item: T, mut tail: Vec<T>) -> Vec<T> {
        let mut group = Vec::with_capacity(tail.len() + 1);
        group.push(item);
        group.append(&mut tail);
        group
    }

    /// A single-pass Python iterator over a lazily computed sequence of results.
    #[pyattr]
    #[pyclass(name = "permutate_iterator")]
    #[derive(PyPayload)]
    struct PyPermutateIter {
        results: PyMutex<Box<dyn Iterator<Item = PyObjectRef>>>,
    }

    // an unprintable iterator is inside, and Python never prints this type's debug anyway
    impl std::fmt::Debug for PyPermutateIter {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.write_str("permutate_iterator")
        }
    }

    impl SelfIter for PyPermutateIter {}

    impl IterNext for PyPermutateIter {
        fn next(zelf: &Py<Self>, _vm: &VirtualMachine) -> PyResult<PyIterReturn> {
            Ok(match zelf.results.lock().next() {
                Some(value) => PyIterReturn::Return(value),
                None => PyIterReturn::StopIteration(None),
            })
        }
    }

    #[pyclass(with(IterNext, Iterable), flags(DISALLOW_INSTANTIATION))]
    impl PyPermutateIter {}

    /// The items of any Python iterable, as permutate sees them.
    fn elements(items: PyObjectRef, vm: &VirtualMachine) -> PyResult<Vec<PyObjectRef>> {
        TryFromObject::try_from_object(vm, items)
    }

    /// What a function's Python recursion did with a negative width, which its code did by
    /// accident rather than decision.
    #[derive(Clone, Copy)]
    enum NegativeWidth {
        /// the recursion ran out of items and yielded nothing
        Empty,
        /// the recursion had no bottom and hit the recursion limit
        NoBottom,
        /// the code ran off the end of the list
        OffTheEnd,
    }

    /// A permutate core: a walk over the items, as a lazy sequence of result lists.
    type Core = fn(Vec<PyObjectRef>, usize) -> Box<dyn Iterator<Item = Vec<PyObjectRef>>>;

    /// One of permutate's walks, as the Python module offers it.
    #[derive(Clone, Copy)]
    struct Walk {
        /// the core algorithm
        core: Core,
        /// what the Python recursion did with a negative width
        negative: NegativeWidth,
    }

    /// Each item once per result, in every order.
    const COMBINATIONS: Walk = Walk {
        core: combinations,
        negative: NegativeWidth::Empty,
    };
    /// Any item any number of times, in every order.
    const SELECTIONS: Walk = Walk {
        core: selections,
        negative: NegativeWidth::NoBottom,
    };
    /// Each item once per result, in the given order.
    const UNIQUE_COMBINATIONS: Walk = Walk {
        core: unique_combinations,
        negative: NegativeWidth::OffTheEnd,
    };

    /// The width that uses every item, which is what the permutation walks ask for.
    fn whole_width(items: &[PyObjectRef]) -> isize {
        isize::try_from(items.len()).unwrap_or(isize::MAX)
    }

    /// How a call takes its results: collected into a list, or an iterator over them.
    enum Delivery {
        /// the complete list, as the plain functions return
        List,
        /// a single-pass iterator, as the generator functions return
        Iterator,
    }

    /// The results of a walk, delivered as asked, with negative widths mapped to what the
    /// Python recursion did.
    fn delivered(
        walk: Walk,
        items: Vec<PyObjectRef>,
        n: isize,
        delivery: Delivery,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        let results = match usize::try_from(n) {
            Ok(n) => (walk.core)(items, n),
            Err(_) => match walk.negative {
                NegativeWidth::Empty => Box::new(iter::empty()),
                NegativeWidth::NoBottom => {
                    return Err(vm.new_recursion_error("maximum recursion depth exceeded"))
                }
                NegativeWidth::OffTheEnd => {
                    return Err(vm.new_index_error("list index out of range"))
                }
            },
        };
        Ok(match delivery {
            Delivery::List => nested_list(results.collect(), vm.ctx.as_ref()),
            Delivery::Iterator => nested_iterator(results, vm),
        })
    }

    /// A list of the result lists.
    fn nested_list(groups: Vec<Vec<PyObjectRef>>, ctx: &rustpython_vm::Context) -> PyObjectRef {
        ctx.new_list(
            groups
                .into_iter()
                .map(|group| ctx.new_list(group).into())
                .collect(),
        )
        .into()
    }

    /// An iterator over the results, each a list, built as it is drained.
    fn nested_iterator(
        results: Box<dyn Iterator<Item = Vec<PyObjectRef>>>,
        vm: &VirtualMachine,
    ) -> PyObjectRef {
        let ctx = vm.ctx.clone();
        let results = results.map(move |group| ctx.new_list(group).into());
        PyPermutateIter {
            results: PyMutex::new(Box::new(results)),
        }
        .into_pyobject(vm)
    }

    #[pyfunction(name = "combinations")]
    fn combinations_py(items: PyObjectRef, n: isize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        delivered(COMBINATIONS, elements(items, vm)?, n, Delivery::List, vm)
    }

    #[pyfunction(name = "selections")]
    fn selections_py(items: PyObjectRef, n: isize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        delivered(SELECTIONS, elements(items, vm)?, n, Delivery::List, vm)
    }

    #[pyfunction(name = "uniqueCombinations")]
    fn unique_combinations_py(
        items: PyObjectRef,
        n: isize,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        delivered(
            UNIQUE_COMBINATIONS,
            elements(items, vm)?,
            n,
            Delivery::List,
            vm,
        )
    }

    #[pyfunction(name = "permutations")]
    fn permutations_py(items: PyObjectRef, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let items = elements(items, vm)?;
        let n = whole_width(&items);
        delivered(COMBINATIONS, items, n, Delivery::List, vm)
    }

    #[pyfunction(name = "xcombinations")]
    fn xcombinations_py(
        items: PyObjectRef,
        n: isize,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        delivered(
            COMBINATIONS,
            elements(items, vm)?,
            n,
            Delivery::Iterator,
            vm,
        )
    }

    #[pyfunction(name = "xselections")]
    fn xselections_py(items: PyObjectRef, n: isize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        delivered(SELECTIONS, elements(items, vm)?, n, Delivery::Iterator, vm)
    }

    #[pyfunction(name = "xuniqueCombinations")]
    fn xunique_combinations_py(
        items: PyObjectRef,
        n: isize,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        delivered(
            UNIQUE_COMBINATIONS,
            elements(items, vm)?,
            n,
            Delivery::Iterator,
            vm,
        )
    }

    #[pyfunction(name = "xpermutations")]
    fn xpermutations_py(items: PyObjectRef, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let items = elements(items, vm)?;
        let n = whole_width(&items);
        delivered(COMBINATIONS, items, n, Delivery::Iterator, vm)
    }

    #[cfg(test)]
    mod tests {
        use super::{combinations, selections, unique_combinations};

        /// The orders are the orders the Python code walked, which its doctests pin.
        #[test]
        fn combinations_walk_each_item_first() {
            let got: Vec<Vec<i32>> = combinations(vec![3, 4, 5], 3).collect();
            assert_eq!(
                got,
                [
                    [3, 4, 5],
                    [3, 5, 4],
                    [4, 3, 5],
                    [4, 5, 3],
                    [5, 3, 4],
                    [5, 4, 3]
                ]
            );
            let got: Vec<Vec<i32>> = combinations(vec![3, 4, 5], 2).collect();
            assert_eq!(got, [[3, 4], [3, 5], [4, 3], [4, 5], [5, 3], [5, 4]]);
        }

        #[test]
        fn selections_repeat_every_item() {
            let got: Vec<Vec<i32>> = selections(vec![3, 4, 5], 2).collect();
            assert_eq!(
                got,
                [
                    [3, 3],
                    [3, 4],
                    [3, 5],
                    [4, 3],
                    [4, 4],
                    [4, 5],
                    [5, 3],
                    [5, 4],
                    [5, 5]
                ]
            );
        }

        #[test]
        fn unique_combinations_keep_the_given_order() {
            let got: Vec<Vec<i32>> = unique_combinations(vec![3, 4, 5], 2).collect();
            assert_eq!(got, [[3, 4], [3, 5], [4, 5]]);
        }

        #[test]
        fn widths_beyond_the_items_yield_nothing() {
            assert_eq!(combinations::<i32>(vec![1, 2], 3).count(), 0);
            assert_eq!(unique_combinations::<i32>(vec![1, 2], 3).count(), 0);
            assert_eq!(selections::<i32>(vec![1, 2], 3).count(), 8);
        }

        #[test]
        fn zero_width_yields_one_empty_result() {
            assert_eq!(
                combinations::<i32>(vec![1, 2], 0).collect::<Vec<_>>(),
                [Vec::<i32>::new()]
            );
            assert_eq!(
                combinations::<i32>(Vec::new(), 0).collect::<Vec<_>>(),
                [Vec::<i32>::new()]
            );
            assert_eq!(combinations::<i32>(Vec::new(), 2).count(), 0);
        }
    }
}
