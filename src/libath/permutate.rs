//! The `athenaCL.libATH.permutate` module: permutation utilities, in Rust.
//!
//! Port of `pysrc/athenaCL/libATH/_pyref/permutate.py`, restructured: the algorithms are generic
//! lazy iterators over any cloneable items — plain Rust, testable without an interpreter — and the
//! module is a thin boundary keeping the Python names, keyword arguments, result lists, and result
//! ordering. The generator functions return single-pass iterators, as generators are. Unique
//! combinations only walk first items that still leave enough items to fill the width — Python's
//! `range(len(items) - n + 1)` — which prunes the impossible branches the plain combinations walk
//! explores by design.
//!
//! Narrowings: the items are read when the call happens, not when the walk advances, so mutating
//! the input list in between is not seen (Python's generators deferred the read); and Python's
//! negative widths, where its recursion ran dry, ran off its end, or hit its recursion limit, are
//! mapped to the empty result or the error it died with.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

/// The walks, as generic lazy iterators over any cloneable items.
mod core {
    use std::iter;

    /// Ordered selections of `n` items, each used at most once. Every item can start a
    /// selection, as the Python loop over all of them did.
    pub(crate) fn combinations<T>(items: Vec<T>, n: usize) -> Box<dyn Iterator<Item = Vec<T>>>
    where
        T: Clone + 'static,
    {
        branched_walk(items, n, without, every_item)
    }

    /// Ordered selections of `n` items, each usable any number of times.
    pub(crate) fn selections<T>(items: Vec<T>, n: usize) -> Box<dyn Iterator<Item = Vec<T>>>
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

    /// Selections of `n` items in the given order, each used at most once. Only items with enough
    /// items after them to fill the rest can start a selection — Python's range bound — so walks of
    /// impossible widths end before they begin.
    pub(crate) fn unique_combinations<T>(
        items: Vec<T>,
        n: usize,
    ) -> Box<dyn Iterator<Item = Vec<T>>>
    where
        T: Clone + 'static,
    {
        branched_walk(items, n, after, fillable_items)
    }

    /// Selections built by walking each item as the first, with the items it leaves for the tail.
    /// The `rest_of` decides which items a first item leaves; the `first_items` says how many items
    /// can start a selection of width `n` from a list of this length.
    fn branched_walk<T>(
        items: Vec<T>,
        n: usize,
        rest_of: fn(&[T], usize) -> Vec<T>,
        first_items: fn(usize, usize) -> usize,
    ) -> Box<dyn Iterator<Item = Vec<T>>>
    where
        T: Clone + 'static,
    {
        match n {
            0 => Box::new(iter::once(Vec::new())),
            _ => {
                // one branch per first item: the first item and the rest to fill from
                let starts = first_items(items.len(), n);
                let branches: Vec<_> = items
                    .iter()
                    .enumerate()
                    .take(starts)
                    .map(|(i, item)| (item.clone(), rest_of(&items, i)))
                    .collect();
                Box::new(branches.into_iter().flat_map(move |(item, rest)| {
                    branched_walk(rest, n - 1, rest_of, first_items)
                        .map(move |tail| once_then(item.clone(), tail))
                }))
            }
        }
    }

    /// Every item can start a selection.
    fn every_item(len: usize, _n: usize) -> usize {
        len
    }

    /// Only items leaving at least `n - 1` after them can start a selection of width `n`,
    /// which is `len - n + 1` items, and none at all when the width cannot be filled: an
    /// impossible width prunes before a single branch is built.
    fn fillable_items(len: usize, n: usize) -> usize {
        len.checked_sub(n).map_or(0, |remaining| remaining + 1)
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
        FromArgs, Py, PyObjectRef, PyPayload, PyResult, VirtualMachine,
    };

    use super::core::{combinations, selections, unique_combinations};

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

    /// A walk core: the results as a lazy sequence of result lists.
    type Core = fn(Vec<PyObjectRef>, usize) -> Box<dyn Iterator<Item = Vec<PyObjectRef>>>;

    /// What a function's Python recursion did with a negative width, which its code did by accident
    /// rather than decision.
    enum NegativeWidth {
        /// the recursion ran out of items and yielded nothing
        Empty,
        /// the recursion ran out of items and yielded nothing — or had no bottom left to run when
        /// items remained
        EmptyOrNoBottom,
        /// the recursion always found another level and hit the recursion limit
        NoBottom,
    }

    /// The results a call walks, with negative widths mapped to what the Python recursion
    /// did with them.
    fn walked(
        items: Vec<PyObjectRef>,
        n: isize,
        negative: NegativeWidth,
        core: Core,
        vm: &VirtualMachine,
    ) -> PyResult<Box<dyn Iterator<Item = Vec<PyObjectRef>>>> {
        match usize::try_from(n) {
            Ok(n) => Ok(core(items, n)),
            Err(_) => match negative {
                NegativeWidth::Empty => Ok(Box::new(iter::empty())),
                NegativeWidth::EmptyOrNoBottom if items.is_empty() => Ok(Box::new(iter::empty())),
                NegativeWidth::EmptyOrNoBottom | NegativeWidth::NoBottom => {
                    // the interpreter's own recursion message, space and all
                    Err(vm.new_recursion_error("maximum recursion depth exceeded "))
                }
            },
        }
    }

    /// The arguments of the width-taking functions.
    #[derive(FromArgs)]
    struct WidthArgs {
        #[pyarg(any)]
        items: PyObjectRef,
        #[pyarg(any)]
        n: isize,
    }

    /// The arguments of the whole-list functions.
    #[derive(FromArgs)]
    struct ItemsArgs {
        #[pyarg(any)]
        items: PyObjectRef,
    }

    /// How a call takes its results: collected into a list, or an iterator over them.
    enum Delivery {
        /// the complete list, as the plain functions return
        List,
        /// a single-pass iterator, as the generator functions return
        Iterator,
    }

    /// The results of a walk, delivered as asked, with negative widths mapped to what the Python
    /// recursion did.
    fn delivered(
        results: PyResult<Box<dyn Iterator<Item = Vec<PyObjectRef>>>>,
        delivery: Delivery,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        let results = results?;
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
    fn combinations_py(args: WidthArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let results = walked(
            elements(args.items, vm)?,
            args.n,
            NegativeWidth::Empty,
            combinations,
            vm,
        );
        delivered(results, Delivery::List, vm)
    }

    #[pyfunction(name = "selections")]
    fn selections_py(args: WidthArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let results = walked(
            elements(args.items, vm)?,
            args.n,
            NegativeWidth::EmptyOrNoBottom,
            selections,
            vm,
        );
        delivered(results, Delivery::List, vm)
    }

    #[pyfunction(name = "uniqueCombinations")]
    fn unique_combinations_py(args: WidthArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let results = walked(
            elements(args.items, vm)?,
            args.n,
            NegativeWidth::NoBottom,
            unique_combinations,
            vm,
        );
        delivered(results, Delivery::List, vm)
    }

    #[pyfunction(name = "permutations")]
    fn permutations_py(args: ItemsArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let items = elements(args.items, vm)?;
        let width = items.len();
        let results = Ok(combinations(items, width));
        delivered(results, Delivery::List, vm)
    }

    #[pyfunction(name = "xcombinations")]
    fn xcombinations_py(args: WidthArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let results = walked(
            elements(args.items, vm)?,
            args.n,
            NegativeWidth::Empty,
            combinations,
            vm,
        );
        delivered(results, Delivery::Iterator, vm)
    }

    #[pyfunction(name = "xselections")]
    fn xselections_py(args: WidthArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let results = walked(
            elements(args.items, vm)?,
            args.n,
            NegativeWidth::EmptyOrNoBottom,
            selections,
            vm,
        );
        delivered(results, Delivery::Iterator, vm)
    }

    #[pyfunction(name = "xuniqueCombinations")]
    fn xunique_combinations_py(args: WidthArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let results = walked(
            elements(args.items, vm)?,
            args.n,
            NegativeWidth::NoBottom,
            unique_combinations,
            vm,
        );
        delivered(results, Delivery::Iterator, vm)
    }

    #[pyfunction(name = "xpermutations")]
    fn xpermutations_py(args: ItemsArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let items = elements(args.items, vm)?;
        let width = items.len();
        let results = Ok(combinations(items, width));
        delivered(results, Delivery::Iterator, vm)
    }
}

#[cfg(test)]
mod tests {
    use super::core::{combinations, selections, unique_combinations};

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

    /// The width-equal walk is the one the pruning exists for: it yields the one result without
    /// exploring the impossible branches after it, which took the unpruned walk a thousand times
    /// longer.
    #[test]
    fn unique_combinations_prune_impossible_branches() {
        let wide: Vec<i32> = (0..18).collect();
        let whole = unique_combinations(wide.clone(), 18);
        assert_eq!(whole.count(), 1);
        assert_eq!(
            unique_combinations(wide.clone(), 18).collect::<Vec<_>>(),
            [wide]
        );
        // a width one past fillable yields nothing at all, without a single branch
        let none = unique_combinations((0..17).collect::<Vec<i32>>(), 18);
        assert_eq!(none.count(), 0);
    }

    /// An impossible width does no recursive work: not one item is cloned, where the unpruned walk
    /// cloned thousands building branches it abandoned.
    #[test]
    fn impossible_widths_do_no_work() {
        use std::sync::atomic::{AtomicUsize, Ordering};

        #[derive(Debug)]
        struct CloneCounter(std::sync::Arc<AtomicUsize>);
        impl Clone for CloneCounter {
            fn clone(&self) -> Self {
                self.0.fetch_add(1, Ordering::Relaxed);
                Self(std::sync::Arc::clone(&self.0))
            }
        }

        let counter = CloneCounter(std::sync::Arc::new(AtomicUsize::new(0)));
        let items: Vec<_> = std::iter::repeat_n(counter.clone(), 200).collect();
        let before = counter.0.load(Ordering::Relaxed);
        let none = unique_combinations(items, 201);
        assert_eq!(none.count(), 0);
        assert_eq!(
            counter.0.load(Ordering::Relaxed),
            before,
            "an impossible width clones nothing"
        );
    }
}
