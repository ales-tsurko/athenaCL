//! The `athenaCL.libATH.drawer` module: the shared utilities, in Rust, with the Python
//! reference in `_pyref/drawer.py`.
//!
//! One public module in three groups, as the reference filed them: the type predicates and
//! conversions, the text and collection utilities, and the environment helpers (clocks, temporary
//! paths, platform probes, preference paths). Every function works through the Python object
//! protocol — the reference's own operations, not Rust-native rewrites — so subclasses, big
//! integers, Unicode, and dunder dispatch survive:
//!
//! The predicates are `isinstance` checks against the interpreter's own types — `isInt` accepts any
//! integer of any size, booleans, and subclasses, exactly as the reference's checks did; no numeric
//! conversion happens. `strToNum` and `strToSequence` evaluate through the builtin `eval` —
//! expressions included, with the drawer module's globals — and convert exactly the reference's
//! exception kinds to `None`. `floatToInt`'s weighted rounding draws through the `random` module's
//! `random` alias, the parameters stream the interpreter redirected. The clock, filesystem, and
//! preference helpers read the `time`, `os`, `tempfile`, and `subprocess` modules at call time, so
//! routed and real behavior both track the reference, and `getPrefsDir` honors
//! `ATHENACL_PREFS_DIR`.
//!
//! The reference's Python 3 arithmetic is kept as it runs, doctests notwithstanding: `intHalf(3)`
//! yields `(1.5, 2.5)`, true division as written.
//!
//! One narrowing, inherent to nativeness: the module's own functions are native, so `isFunc`
//! answers False for them where the reference's Python-level functions answered True — user-defined
//! Python functions still answer True. No athenaCL consumer applies `isFunc` to the module's own
//! utilities.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.drawer")]
pub(super) mod _inner {
    use rustpython_vm::{
        builtins::{PyBaseExceptionRef, PyList, PyModule, PyTuple, PyType},
        function::OptionalArg,
        AsObject, FromArgs, Py, PyObjectRef, PyResult, VirtualMachine,
    };

    /// Resolve dotted modules with the VM's top-level `__import__` semantics.
    fn module(path: &'static str, vm: &VirtualMachine) -> PyResult {
        let mut object = vm.import(path, 0)?;
        for part in path.split('.').skip(1) {
            object = object.get_attr(part, vm)?;
        }
        Ok(object)
    }

    fn own_module(vm: &VirtualMachine) -> PyResult {
        module("athenaCL.libATH.drawer", vm)
    }

    fn boolean(value: bool, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_bool(value).into()
    }

    fn integer(value: i64, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_int(value).into()
    }

    fn text(value: &str, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_str(value).into()
    }

    fn none(vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.none()
    }

    /// Use Python's `isinstance`, which also consults an object's `__class__` property.
    fn is_instance(
        object: &PyObjectRef,
        class: &Py<PyType>,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        object.is_instance(class.as_object(), vm)
    }

    /// An attribute of an object, read fresh.
    fn attr(object: &PyObjectRef, name: &'static str, vm: &VirtualMachine) -> PyResult {
        object.get_attr(name, vm)
    }

    /// A method of an object called with arguments.
    fn method(
        object: &PyObjectRef,
        name: &'static str,
        args: impl rustpython_vm::function::IntoFuncArgs,
        vm: &VirtualMachine,
    ) -> PyResult {
        object.get_attr(name, vm)?.call(args, vm)
    }

    fn eq(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, rustpython_vm::types::PyComparisonOp::Eq, vm)
    }

    fn ne(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, rustpython_vm::types::PyComparisonOp::Ne, vm)
    }

    fn lt(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, rustpython_vm::types::PyComparisonOp::Lt, vm)
    }

    fn gt(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, rustpython_vm::types::PyComparisonOp::Gt, vm)
    }

    fn le(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, rustpython_vm::types::PyComparisonOp::Le, vm)
    }

    fn ge(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, rustpython_vm::types::PyComparisonOp::Ge, vm)
    }

    /// The object's truth, as a conditional reads it.
    fn truthy(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        object.to_owned().try_to_bool(vm)
    }

    /// The `in` operator, including its special-method lookup and iteration fallback.
    fn contains(
        container: &PyObjectRef,
        value: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        vm._contains(container, value)
    }

    /// The reference's `%` formatting: a lone operand is passed as-is, while multiple operands are
    /// bundled into a tuple.
    fn formatted(format: &PyObjectRef, values: Vec<PyObjectRef>, vm: &VirtualMachine) -> PyResult {
        if let [value] = values.as_slice() {
            return method(format, "__mod__", (value.clone(),), vm);
        }
        let bundle: PyObjectRef = vm.ctx.new_tuple(values).into();
        method(format, "__mod__", (bundle,), vm)
    }

    /// An object's length, as `len()` measures it.
    fn length(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<usize> {
        object.length(vm)
    }

    /// A builtin, by name.
    fn builtin(name: &'static str, vm: &VirtualMachine) -> PyResult {
        vm.import("builtins", 0)?.get_attr(name, vm)
    }

    /// A type, by name, applied to arguments — the interpreter's own conversions.
    fn constructed(
        class: &'static str,
        args: impl rustpython_vm::function::IntoFuncArgs,
        vm: &VirtualMachine,
    ) -> PyResult {
        builtin(class, vm)?.call(args, vm)
    }

    /// A fresh list from collected items.
    fn list_of(items: Vec<PyObjectRef>, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_list(items).into()
    }

    /// Unpack exactly two values, including custom iterable `__divmod__` results.
    fn pair_of(divided: &PyObjectRef, vm: &VirtualMachine) -> PyResult<(PyObjectRef, PyObjectRef)> {
        let exact_tuple = divided.class().is(vm.ctx.types.tuple_type);
        let exact_list = divided.class().is(vm.ctx.types.list_type);
        let pieces = if exact_tuple {
            divided
                .downcast_ref::<PyTuple>()
                .ok_or_else(|| vm.new_type_error("divmod result was not a tuple".to_owned()))?
                .as_slice()
                .to_vec()
        } else if exact_list {
            divided
                .downcast_ref::<PyList>()
                .ok_or_else(|| vm.new_type_error("divmod result was not a list".to_owned()))?
                .borrow_vec()
                .to_vec()
        } else {
            let mut values = Vec::new();
            let not_iterable = divided.class().slots.iter.load().is_none()
                && divided
                    .get_class_attr(vm.ctx.intern_str("__getitem__"))
                    .is_none();
            let python_iter = divided.get_iter(vm).map_err(|error| {
                if not_iterable && error.class().is(vm.ctx.exceptions.type_error) {
                    vm.new_type_error(format!(
                        "cannot unpack non-iterable {} object",
                        divided.class().name()
                    ))
                } else {
                    error
                }
            })?;
            let mut iter = python_iter.iter_without_hint::<PyObjectRef>(vm)?;
            for _ in 0..3 {
                match iter.next() {
                    Some(value) => values.push(value?),
                    None => break,
                }
            }
            values
        };
        match pieces.as_slice() {
            [whole, fraction] => Ok((whole.clone(), fraction.clone())),
            [_, _, ..] => {
                let exact_dict = divided.class().is(vm.ctx.types.dict_type);
                let message = if exact_tuple || exact_list || exact_dict {
                    let got = if exact_dict {
                        length(divided, vm)?
                    } else {
                        pieces.len()
                    };
                    format!("too many values to unpack (expected 2, got {})", got)
                } else {
                    "too many values to unpack (expected 2)".to_owned()
                };
                Err(vm.new_value_error(message))
            }
            _ => Err(vm.new_value_error(format!(
                "not enough values to unpack (expected 2, got {})",
                pieces.len()
            ))),
        }
    }

    /// A two-tuple, as the reference's pairs returned.
    fn pair(a: PyObjectRef, b: PyObjectRef, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_tuple(vec![a, b]).into()
    }

    /// Evaluate with the module's globals and one invocation's mutable locals.
    fn evaluated_in_scope(
        source: &PyObjectRef,
        locals: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let evaluate = builtin("eval", vm)?;
        let globals = own_module(vm)?.get_attr("__dict__", vm)?;
        evaluate.call((source.clone(), globals, locals.clone()), vm)
    }

    /// The reference calls `eval` inside a Python function, where its current locals are visible
    /// and assignment expressions do not write into the module.
    fn evaluated(
        source: &PyObjectRef,
        local_values: &[(&str, PyObjectRef)],
        vm: &VirtualMachine,
    ) -> PyResult {
        let locals: PyObjectRef = vm.ctx.new_dict().into();
        for (name, value) in local_values {
            locals.set_item(*name, value.clone(), vm)?;
        }
        evaluated_in_scope(source, &locals, vm)
    }

    /// Whether a raised exception is one of the reference's converted kinds.
    fn converted(error: &PyBaseExceptionRef, vm: &VirtualMachine) -> bool {
        let exceptions = &vm.ctx.exceptions;
        error.class().fast_issubclass(exceptions.syntax_error)
            || error.class().fast_issubclass(exceptions.name_error)
            || error.class().fast_issubclass(exceptions.value_error)
            || error.class().fast_issubclass(exceptions.type_error)
            || error
                .class()
                .fast_issubclass(exceptions.zero_division_error)
    }

    /// A bare exception of a type, no message.
    fn bare(class: &PyObjectRef, vm: &VirtualMachine) -> PyBaseExceptionRef {
        class
            .call((), vm)
            .and_then(|raised| {
                raised
                    .downcast::<rustpython_vm::builtins::PyBaseException>()
                    .map_err(|_not_exception| {
                        vm.new_type_error("an exception type is expected".to_owned())
                    })
            })
            .expect("an exception type constructs its own kind")
    }

    // -- predicates ----------------------------------------------------------
    // every check is an isinstance against the interpreter's own type

    fn is_list_value(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        Ok(is_instance(object, vm.ctx.types.list_type, vm)?
            || is_instance(object, vm.ctx.types.tuple_type, vm)?)
    }

    fn is_num_value(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        Ok(is_instance(object, vm.ctx.types.float_type, vm)?
            || is_instance(object, vm.ctx.types.int_type, vm)?)
    }

    fn is_str_value(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        is_instance(object, vm.ctx.types.str_type, vm)
    }

    fn is_dict_value(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        is_instance(object, vm.ctx.types.dict_type, vm)
    }

    fn is_int_value(object: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        is_instance(object, vm.ctx.types.int_type, vm)
    }

    /// `_labelOrdered`: the recursive spine of `genAlphaLabel`, in list pieces.
    fn label_ordered(
        n: &PyObjectRef,
        symbols: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Vec<PyObjectRef>> {
        let divided = vm._divmod(n, &integer(length(symbols, vm)? as i64, vm))?;
        let (x, y) = pair_of(&divided, vm)?;
        let one = integer(1, vm);
        let x_post = vm._sub(&x, &one)?;
        let mut msg = Vec::new();
        let count = integer(length(symbols, vm)? as i64, vm);
        let x_nonzero = ne(&x, &integer(0, vm), vm)?;
        let post_within = lt(&x_post, &count, vm)?;
        let post_beyond = ge(&x_post, &count, vm)?;
        if x_nonzero && post_within {
            msg.push(attr(symbols, "__getitem__", vm)?.call((x_post,), vm)?);
            msg.push(attr(symbols, "__getitem__", vm)?.call((y,), vm)?);
        } else if x_nonzero && post_beyond {
            msg = label_ordered(&x_post, symbols, vm)?;
            msg.push(attr(symbols, "__getitem__", vm)?.call((y,), vm)?);
        } else if eq(&x, &integer(0, vm), vm)? {
            msg.push(attr(symbols, "__getitem__", vm)?.call((y,), vm)?);
        }
        Ok(msg)
    }

    #[derive(FromArgs)]
    pub(crate) struct LabelOrderedArgs {
        #[pyarg(any, name = "msg")]
        _msg: PyObjectRef,
        #[pyarg(any)]
        n: PyObjectRef,
        #[pyarg(any)]
        symbols: PyObjectRef,
    }

    #[pyfunction(name = "_labelOrdered")]
    pub(crate) fn label_ordered_python(args: LabelOrderedArgs, vm: &VirtualMachine) -> PyResult {
        Ok(list_of(label_ordered(&args.n, &args.symbols, vm)?, vm))
    }

    /// Capture the same module aliases as the reference, once per interpreter.
    pub(crate) fn module_exec(vm: &VirtualMachine, module: &Py<PyModule>) -> PyResult<()> {
        __module_exec(vm, module);
        module.set_attr("_MOD", text("drawer.py", vm), vm)?;
        for name in [
            "sys", "os", "string", "types", "random", "time", "unittest", "tempfile",
        ] {
            module.set_attr(name, vm.import(name, 0)?, vm)?;
        }
        Ok(())
    }

    // -- group one: predicates and conversions -------------------------------

    #[derive(FromArgs)]
    pub(crate) struct DataArgs {
        #[pyarg(any, name = "usrData")]
        usr_data: PyObjectRef,
    }

    #[pyfunction(name = "isList")]
    pub(crate) fn is_list(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(is_list_value(&args.usr_data, vm)?, vm))
    }

    #[pyfunction(name = "isNum")]
    pub(crate) fn is_num(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(is_num_value(&args.usr_data, vm)?, vm))
    }

    #[pyfunction(name = "isBool")]
    pub(crate) fn is_bool(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(
            is_instance(&args.usr_data, vm.ctx.types.bool_type, vm)?,
            vm,
        ))
    }

    #[pyfunction(name = "isFloat")]
    pub(crate) fn is_float(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(
            is_instance(&args.usr_data, vm.ctx.types.float_type, vm)?,
            vm,
        ))
    }

    #[pyfunction(name = "isInt")]
    pub(crate) fn is_int(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(is_int_value(&args.usr_data, vm)?, vm))
    }

    #[pyfunction(name = "isStr")]
    pub(crate) fn is_str(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(is_str_value(&args.usr_data, vm)?, vm))
    }

    #[pyfunction(name = "isDict")]
    pub(crate) fn is_dict(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(is_dict_value(&args.usr_data, vm)?, vm))
    }

    #[pyfunction(name = "isMod")]
    pub(crate) fn is_mod(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(
            is_instance(&args.usr_data, vm.ctx.types.module_type, vm)?,
            vm,
        ))
    }

    #[pyfunction(name = "isFunc")]
    pub(crate) fn is_func(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(
            is_instance(&args.usr_data, vm.ctx.types.function_type, vm)?,
            vm,
        ))
    }

    #[derive(FromArgs)]
    pub(crate) struct AlmostEqualsArgs {
        #[pyarg(any)]
        x: PyObjectRef,
        #[pyarg(any, optional)]
        y: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        grain: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "almostEquals")]
    pub(crate) fn almost_equals(args: AlmostEqualsArgs, vm: &VirtualMachine) -> PyResult {
        let y = args.y.unwrap_or_else(|| vm.ctx.new_float(0.0).into());
        let grain = args.grain.unwrap_or_else(|| vm.ctx.new_float(1e-7).into());
        let difference = builtin("abs", vm)?.call((vm._sub(&args.x, &y)?,), vm)?;
        let within = lt(&difference, &grain, vm)?;
        Ok(boolean(within, vm))
    }

    fn is_char_num_value(usr_data: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        let total = integer(length(usr_data, vm)? as i64, vm);
        let mut count = integer(0, vm);
        let accepted = list_of(
            [".", "-", " ", "+"]
                .iter()
                .map(|char| text(char, vm))
                .collect(),
            vm,
        );
        for char in usr_data
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let char = char?;
            let digit = method(&char, "isdigit", (), vm)?.try_to_bool(vm)?;
            if digit || contains(&accepted, &char, vm)? {
                count = vm._add(&count, &integer(1, vm))?;
            }
        }
        eq(&count, &total, vm)
    }

    #[pyfunction(name = "isCharNum")]
    pub(crate) fn is_char_num(args: DataArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(is_char_num_value(&args.usr_data, vm)?, vm))
    }

    fn type_as_str_value(type_str: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        for (name, friendly) in [
            ("list", "list"),
            ("num", "number"),
            ("bool", "yes or no"),
            ("float", "floating point number"),
            ("int", "integer number"),
            ("str", "string"),
            ("dict", "dictionary"),
        ] {
            if eq(type_str, &text(name, vm), vm)? {
                return Ok(text(friendly, vm));
            }
        }
        formatted(&text("unknown (%s)", vm), vec![type_str.clone()], vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct TypeAsStrArgs {
        #[pyarg(any, name = "typeStr")]
        type_str: PyObjectRef,
    }

    #[pyfunction(name = "typeAsStr")]
    pub(crate) fn type_as_str(args: TypeAsStrArgs, vm: &VirtualMachine) -> PyResult {
        type_as_str_value(&args.type_str, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct IsTypeArgs {
        #[pyarg(any, name = "usrData")]
        usr_data: PyObjectRef,
        #[pyarg(any)]
        r#type: PyObjectRef,
    }

    fn is_type_value(
        usr_data: &PyObjectRef,
        type_name: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        for name in ["list", "num", "bool", "float", "int", "str", "dict"] {
            if eq(type_name, &text(name, vm), vm)? {
                return match name {
                    "list" => is_list_value(usr_data, vm),
                    "num" => is_num_value(usr_data, vm),
                    "bool" => is_instance(usr_data, vm.ctx.types.bool_type, vm),
                    "float" => is_instance(usr_data, vm.ctx.types.float_type, vm),
                    "int" => is_int_value(usr_data, vm),
                    "str" => is_str_value(usr_data, vm),
                    "dict" => is_dict_value(usr_data, vm),
                    _ => Err(vm.new_value_error("bad data type given".to_owned())),
                };
            }
        }
        Err(vm.new_value_error("bad data type given".to_owned()))
    }

    #[pyfunction(name = "isType")]
    pub(crate) fn is_type(args: IsTypeArgs, vm: &VirtualMachine) -> PyResult {
        Ok(boolean(
            is_type_value(&args.usr_data, &args.r#type, vm)?,
            vm,
        ))
    }

    // -- group two: text and collection utilities ----------------------------

    #[derive(FromArgs)]
    pub(crate) struct InListArgs {
        #[pyarg(any)]
        value: PyObjectRef,
        #[pyarg(any, name = "valueList")]
        value_list: PyObjectRef,
        #[pyarg(any, optional, name = "caseSens")]
        case_sens: OptionalArg<PyObjectRef>,
    }

    /// Walk a list's choices, returning the first a predicate accepts.
    fn find_choice(
        value_list: &PyObjectRef,
        accepts: impl Fn(&PyObjectRef) -> PyResult<bool>,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        for choice in value_list
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let choice = choice?;
            if accepts(&choice)? {
                return Ok(Some(choice));
            }
        }
        Ok(None)
    }

    fn string_prefix(
        choice: &PyObjectRef,
        value: &PyObjectRef,
        lower_choice: bool,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        if !(is_str_value(choice, vm)? && is_str_value(value, vm)?) {
            return Ok(false);
        }
        let candidate = if lower_choice {
            method(choice, "lower", (), vm)?
        } else {
            choice.clone()
        };
        method(&candidate, "startswith", (value.clone(),), vm)?.try_to_bool(vm)
    }

    /// The case-sensitive walk: membership, then partial matches by prefix.
    fn in_list_case(
        value: &PyObjectRef,
        value_list: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        if contains(value_list, value, vm)? {
            return Ok(Some(value.clone()));
        }
        find_choice(
            value_list,
            |choice| string_prefix(choice, value, false, vm),
            vm,
        )
    }

    /// The case-insensitive walks: exact lowered matches first, then partial prefixes.
    fn in_list_nocase(
        value: &PyObjectRef,
        value_list: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        let both = |choice: &PyObjectRef| -> PyResult<bool> {
            Ok(is_str_value(choice, vm)? && is_str_value(value, vm)?)
        };
        let exact = find_choice(
            value_list,
            |choice| {
                if !both(choice)? {
                    return Ok(false);
                }
                let lowered = method(choice, "lower", (), vm)?;
                let value_lowered = method(value, "lower", (), vm)?;
                eq(&value_lowered, &lowered, vm)
            },
            vm,
        )?;
        if exact.is_some() {
            return Ok(exact);
        }
        find_choice(
            value_list,
            |choice| string_prefix(choice, value, true, vm),
            vm,
        )
    }

    #[pyfunction(name = "inList")]
    pub(crate) fn in_list(args: InListArgs, vm: &VirtualMachine) -> PyResult {
        let case_sens = args.case_sens.unwrap_or_else(|| text("case", vm));
        if eq(&args.value, &none(vm), vm)? {
            return Ok(none(vm));
        }
        let found = if eq(&case_sens, &text("case", vm), vm)? {
            in_list_case(&args.value, &args.value_list, vm)?
        } else if eq(&case_sens, &text("noCase", vm), vm)? {
            in_list_nocase(&args.value, &args.value_list, vm)?
        } else {
            return Ok(none(vm));
        };
        Ok(found.unwrap_or_else(|| none(vm)))
    }

    #[derive(FromArgs)]
    pub(crate) struct InListSearchArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, name = "choiceList")]
        choice_list: PyObjectRef,
    }

    #[pyfunction(name = "inListSearch")]
    pub(crate) fn in_list_search(args: InListSearchArgs, vm: &VirtualMachine) -> PyResult {
        let usr_str = method(&args.usr_str, "strip", (), vm)?;
        let usr_str = method(&usr_str, "lower", (), vm)?;
        if eq(&usr_str, &text("", vm), vm)? {
            return Ok(none(vm));
        }
        let mut filter_list = Vec::new();
        let mut exact_list = Vec::new();
        for topic in args
            .choice_list
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let topic = topic?;
            let topic_lowered = method(&topic, "lower", (), vm)?;
            if eq(&topic_lowered, &usr_str, vm)? {
                exact_list.push(topic.clone());
            }
            let found = method(&topic_lowered, "find", (usr_str.clone(),), vm)?;
            if ge(&found, &integer(0, vm), vm)? {
                filter_list.push(topic);
            }
        }
        let empty = list_of(Vec::new(), vm);
        if eq(&list_of(filter_list.clone(), vm), &empty, vm)? {
            Ok(none(vm))
        } else if ne(&list_of(exact_list.clone(), vm), &empty, vm)? {
            Ok(list_of(exact_list, vm))
        } else {
            Ok(list_of(filter_list, vm))
        }
    }

    fn list_to_str_value(
        set: &PyObjectRef,
        remove_space: &PyObjectRef,
        remove_outer: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let set = if is_num_value(set, vm)? {
            list_of(vec![set.clone()], vm)
        } else {
            set.clone()
        };
        let mut set_repr = Vec::new();
        for part in set.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let part = part?;
            set_repr.push(constructed("str", (part,), vm)?);
        }
        let joined = method(&text(",", vm), "join", (list_of(set_repr, vm),), vm)?;
        let mut repr = formatted(&text("(%s)", vm), vec![joined], vm)?;
        if truthy(remove_space, vm)? {
            repr = method(&repr, "replace", (text(" ", vm), text("", vm)), vm)?;
        }
        if truthy(remove_outer, vm)? {
            repr = repr.get_item(
                vm.ctx
                    .types
                    .slice_type
                    .as_object()
                    .call((integer(1, vm), integer(-1, vm)), vm)?
                    .as_object(),
                vm,
            )?;
        }
        Ok(repr)
    }

    #[derive(FromArgs)]
    pub(crate) struct ListToStrArgs {
        #[pyarg(any)]
        set: PyObjectRef,
        #[pyarg(any, optional, name = "removeSpace")]
        remove_space: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional, name = "removeOuter")]
        remove_outer: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "listToStr")]
    pub(crate) fn list_to_str(args: ListToStrArgs, vm: &VirtualMachine) -> PyResult {
        let remove_space = args.remove_space.unwrap_or_else(|| boolean(true, vm));
        let remove_outer = args.remove_outer.unwrap_or_else(|| boolean(false, vm));
        list_to_str_value(&args.set, &remove_space, &remove_outer, vm)
    }

    fn list_to_str_grammar_value(
        items: &PyObjectRef,
        final_separator: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let count = integer(length(items, vm)? as i64, vm);
        if eq(&count, &integer(1, vm), vm)? {
            return items.get_item(integer(0, vm).as_object(), vm);
        }
        if eq(&count, &integer(2, vm), vm)? {
            if ne(final_separator, &none(vm), vm)? {
                return formatted(
                    &text("%s %s %s", vm),
                    vec![
                        items.get_item(integer(0, vm).as_object(), vm)?,
                        final_separator.clone(),
                        items.get_item(integer(1, vm).as_object(), vm)?,
                    ],
                    vm,
                );
            }
            return method(&text(", ", vm), "join", (items.clone(),), vm);
        }
        grammar_tail(items, final_separator, vm)
    }

    /// The tail of a three-or-more list: separators between, the final one before the last.
    fn grammar_tail(
        items: &PyObjectRef,
        final_separator: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let mut msg = Vec::new();
        let two = integer(2, vm);
        let count = integer(length(items, vm)? as i64, vm);
        for i in builtin("range", vm)?
            .call((count,), vm)?
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let i = i?;
            let length = integer(length(items, vm)? as i64, vm);
            let second_last = vm._sub(&length, &two)?;
            if lt(&i, &second_last, vm)? {
                msg.push(items.get_item(i.as_object(), vm)?);
                msg.push(text(", ", vm));
            } else if eq(&i, &second_last, vm)? {
                msg.push(items.get_item(i.as_object(), vm)?);
                if ne(final_separator, &none(vm), vm)? {
                    msg.push(formatted(
                        &text(", %s ", vm),
                        vec![final_separator.clone()],
                        vm,
                    )?);
                } else {
                    msg.push(text(", ", vm));
                }
            } else if eq(&i, &vm._sub(&length, &integer(1, vm))?, vm)? {
                msg.push(items.get_item(i.as_object(), vm)?);
            }
        }
        method(&text("", vm), "join", (list_of(msg, vm),), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct ListToStrGrammarArgs {
        #[pyarg(any)]
        items: PyObjectRef,
        #[pyarg(any, optional, name = "finalSeparator")]
        final_separator: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "listToStrGrammar")]
    pub(crate) fn list_to_str_grammar(args: ListToStrGrammarArgs, vm: &VirtualMachine) -> PyResult {
        let final_separator = args.final_separator.unwrap_or_else(|| none(vm));
        list_to_str_grammar_value(&args.items, &final_separator, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct TypeListAsStrArgs {
        #[pyarg(any, name = "typeList")]
        type_list: PyObjectRef,
        #[pyarg(any, optional, name = "finalSeparator")]
        final_separator: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "typeListAsStr")]
    pub(crate) fn type_list_as_str(args: TypeListAsStrArgs, vm: &VirtualMachine) -> PyResult {
        let final_separator = args.final_separator.unwrap_or_else(|| none(vm));
        let mut items = Vec::new();
        for type_str in args
            .type_list
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let type_str = type_str?;
            let friendly = type_as_str_value(&type_str, vm)?;
            items.push(formatted(&text("%s", vm), vec![friendly], vm)?);
        }
        list_to_str_grammar_value(&list_of(items, vm), &final_separator, vm)
    }

    fn list_scrub_value(
        set: &PyObjectRef,
        space: &PyObjectRef,
        quote: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let set = if is_num_value(set, vm)? {
            list_of(vec![set.clone()], vm)
        } else {
            set.clone()
        };
        if eq(&integer(length(&set, vm)? as i64, vm), &integer(0, vm), vm)? {
            return Ok(text("none", vm));
        }
        let mut repr = list_to_str_value(&set, space, &boolean(false, vm), vm)?;
        let empty = text("", vm);
        repr = strip_brackets(&repr, "(", ")", vm)?;
        repr = strip_brackets(&repr, "[", "]", vm)?;
        if eq(
            &repr.get_item(integer(-1, vm).as_object(), vm)?,
            &text(",", vm),
            vm,
        )? {
            repr = slice_of(&repr, none(vm), integer(-1, vm), vm)?;
        }
        if ne(quote, &none(vm), vm)? {
            repr = method(&repr, "replace", (text("\"", vm), empty.clone()), vm)?;
            repr = method(&repr, "replace", (text("'", vm), empty), vm)?;
        }
        Ok(repr)
    }

    /// A slice of an object, from a start and stop the reference computed.
    fn slice_of(
        object: &PyObjectRef,
        start: PyObjectRef,
        stop: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let bounds = vm
            .ctx
            .types
            .slice_type
            .as_object()
            .call((start, stop), vm)?;
        object.get_item(bounds.as_object(), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct ListScrubArgs {
        #[pyarg(any)]
        set: PyObjectRef,
        #[pyarg(any, optional)]
        space: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        quote: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "listScrub")]
    pub(crate) fn list_scrub(args: ListScrubArgs, vm: &VirtualMachine) -> PyResult {
        let space = args.space.unwrap_or_else(|| text("rmSpace", vm));
        let quote = args.quote.unwrap_or_else(|| none(vm));
        list_scrub_value(&args.set, &space, &quote, vm)
    }

    /// Outer matching brackets removed, when both ends carry them.
    fn strip_brackets(
        repr: &PyObjectRef,
        open: &'static str,
        close: &'static str,
        vm: &VirtualMachine,
    ) -> PyResult {
        let first = repr.get_item(integer(0, vm).as_object(), vm)?;
        let last = repr.get_item(integer(-1, vm).as_object(), vm)?;
        if eq(&first, &text(open, vm), vm)? && eq(&last, &text(close, vm), vm)? {
            return slice_of(repr, integer(1, vm), integer(-1, vm), vm);
        }
        Ok(repr.clone())
    }

    #[derive(FromArgs)]
    pub(crate) struct ListInterleaveArgs {
        #[pyarg(any)]
        a: PyObjectRef,
        #[pyarg(any)]
        b: PyObjectRef,
        #[pyarg(any, optional)]
        offset: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "listInterleave")]
    pub(crate) fn list_interleave(args: ListInterleaveArgs, vm: &VirtualMachine) -> PyResult {
        let offset = args.offset.unwrap_or_else(|| integer(0, vm));
        let mut post = Vec::new();
        for x in builtin("range", vm)?
            .call((integer(0, vm), offset.clone()), vm)?
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let x = x?;
            post.push(args.a.get_item(x.as_object(), vm)?);
        }
        let a_length = integer(length(&args.a, vm)? as i64, vm);
        for x in builtin("range", vm)?
            .call(
                (integer(0, vm), integer(length(&args.b, vm)? as i64, vm)),
                vm,
            )?
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let x = x?;
            let reached = vm._add(&offset, &x)?;
            if !ge(&reached, &a_length, vm)? {
                post.push(args.a.get_item(reached.as_object(), vm)?);
            }
            post.push(args.b.get_item(x.as_object(), vm)?);
        }
        Ok(list_of(post, vm))
    }

    #[derive(FromArgs)]
    pub(crate) struct ListSliceWrapArgs {
        #[pyarg(any)]
        src: PyObjectRef,
        #[pyarg(any)]
        a: PyObjectRef,
        #[pyarg(any)]
        b: PyObjectRef,
        #[pyarg(any, optional)]
        fmt: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "listSliceWrap")]
    pub(crate) fn list_slice_wrap(args: ListSliceWrapArgs, vm: &VirtualMachine) -> PyResult {
        let fmt = method(
            &args.fmt.unwrap_or_else(|| text("value", vm)),
            "lower",
            (),
            vm,
        )?;
        if eq(&args.a, &args.b, vm)? {
            return Ok(list_of(Vec::new(), vm));
        }
        let (minimum, maximum) = if lt(&args.a, &args.b, vm)? {
            (args.a.clone(), args.b.clone())
        } else {
            (args.b.clone(), args.a.clone())
        };
        let start = constructed("int", (minimum,), vm)?;
        let stop = constructed("int", (maximum,), vm)?;
        let mut post = Vec::new();
        let zero = integer(0, vm);
        for i in builtin("range", vm)?
            .call((start, stop), vm)?
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let i = i?;
            let src_length = integer(length(&args.src, vm)? as i64, vm);
            let q = vm._mod(&i, &src_length)?;
            if let Some(item) = wrapped_item(&args.src, &q, &fmt, &zero, vm)? {
                post.push(item);
            }
        }
        Ok(list_of(post, vm))
    }

    /// One wrapped slice item in the requested format; the active formats may skip, and an unknown
    /// format raises the reference's bare ValueError.
    fn wrapped_item(
        src: &PyObjectRef,
        q: &PyObjectRef,
        fmt: &PyObjectRef,
        zero: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        for (name, kind) in [
            ("value", 0),
            ("index", 1),
            ("valueactive", 2),
            ("valuepassive", 3),
            ("indexactive", 4),
            ("indexpassive", 5),
            ("pair", 6),
        ] {
            if !eq(fmt, &text(name, vm), vm)? {
                continue;
            }
            let value = || src.get_item(q.as_object(), vm);
            return match kind {
                0 => value().map(Some),
                1 => Ok(Some(q.clone())),
                2 => {
                    if gt(&value()?, zero, vm)? {
                        value().map(Some)
                    } else {
                        Ok(None)
                    }
                }
                3 => {
                    if eq(&value()?, zero, vm)? {
                        value().map(Some)
                    } else {
                        Ok(None)
                    }
                }
                4 => Ok(gt(&value()?, zero, vm)?.then(|| q.clone())),
                5 => Ok(eq(&value()?, zero, vm)?.then(|| q.clone())),
                6 => Ok(Some(pair(q.clone(), value()?, vm))),
                _ => Ok(None),
            };
        }
        let class: PyObjectRef = vm.ctx.exceptions.value_error.to_owned().into();
        Err(bare(&class, vm))
    }

    fn str_scrub_value(
        usr_str: &PyObjectRef,
        case: &PyObjectRef,
        rm: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let mut usr_str = if !is_str_value(usr_str, vm)? {
            constructed("str", (usr_str.clone(),), vm)?
        } else {
            usr_str.clone()
        };
        if ne(case, &none(vm), vm)? {
            let case = method(case, "lower", (), vm)?;
            let upper_at = method(&case, "find", (text("u", vm),), vm)?;
            if ge(&upper_at, &integer(0, vm), vm)? {
                usr_str = method(&usr_str, "upper", (), vm)?;
            } else {
                let lower_at = method(&case, "find", (text("l", vm),), vm)?;
                if ge(&lower_at, &integer(0, vm), vm)? {
                    usr_str = method(&usr_str, "lower", (), vm)?;
                } else {
                    return Err(vm.new_value_error("bad case type given".to_owned()));
                }
            }
        }
        usr_str = method(&usr_str, "strip", (), vm)?;
        for char in rm.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let char = char?;
            usr_str = method(&usr_str, "replace", (char, text("", vm)), vm)?;
        }
        Ok(usr_str)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrScrubArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional)]
        case: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        rm: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "strScrub")]
    pub(crate) fn str_scrub(args: StrScrubArgs, vm: &VirtualMachine) -> PyResult {
        let case = args.case.unwrap_or_else(|| none(vm));
        let rm = args.rm.unwrap_or_else(|| list_of(Vec::new(), vm));
        str_scrub_value(&args.usr_str, &case, &rm, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrStripAlphaArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
    }

    #[pyfunction(name = "strStripAlpha")]
    pub(crate) fn str_strip_alpha(args: StrStripAlphaArgs, vm: &VirtualMachine) -> PyResult {
        if eq(&args.usr_str, &text("", vm), vm)? {
            return Ok(text("", vm));
        }
        let mut kept = Vec::new();
        for char in args
            .usr_str
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let char = char?;
            let alpha = method(&char, "isalpha", (), vm)?.try_to_bool(vm)?;
            if !alpha {
                kept.push(char);
            }
        }
        method(&text("", vm), "join", (list_of(kept, vm),), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrExtractAlphaArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional)]
        opt: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "strExtractAlpha")]
    pub(crate) fn str_extract_alpha(args: StrExtractAlphaArgs, vm: &VirtualMachine) -> PyResult {
        if eq(&args.usr_str, &text("", vm), vm)? {
            return Ok(text("", vm));
        }
        let opt = args.opt.unwrap_or_else(|| list_of(Vec::new(), vm));
        let mut kept = Vec::new();
        for char in args
            .usr_str
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let char = char?;
            let alpha = method(&char, "isalpha", (), vm)?.try_to_bool(vm)?;
            if alpha || contains(&opt, &char, vm)? {
                kept.push(char);
            }
        }
        method(&text("", vm), "join", (list_of(kept, vm),), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrExtractNumArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional, name = "optAccept")]
        opt_accept: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "strExtractNum")]
    pub(crate) fn str_extract_num(args: StrExtractNumArgs, vm: &VirtualMachine) -> PyResult {
        let opt_accept = args.opt_accept.unwrap_or_else(|| text("", vm));
        let digits = constructed("list", (module("string", vm)?.get_attr("digits", vm)?,), vm)?;
        let extras = constructed("list", (opt_accept,), vm)?;
        let numbers = vm._add(&digits, &extras)?;
        let usr_str = str_scrub_value(&args.usr_str, &none(vm), &list_of(Vec::new(), vm), vm)?;
        let mut found = Vec::new();
        let mut remained = Vec::new();
        for char in usr_str.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let char = char?;
            if contains(&numbers, &char, vm)? {
                found.push(char.clone());
            } else {
                remained.push(char);
            }
        }
        let found = method(&text("", vm), "join", (list_of(found, vm),), vm)?;
        let remained = method(&text("", vm), "join", (list_of(remained, vm),), vm)?;
        Ok(pair(found, remained, vm))
    }

    #[derive(FromArgs)]
    pub(crate) struct StrCompactSpaceArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
    }

    #[pyfunction(name = "strCompactSpace")]
    pub(crate) fn str_compact_space(args: StrCompactSpaceArgs, vm: &VirtualMachine) -> PyResult {
        let mut new_str = Vec::new();
        let mut count = 0;
        let usr_str = method(&args.usr_str, "strip", (), vm)?;
        for char in usr_str.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let char = char?;
            let space = method(&char, "isspace", (), vm)?.try_to_bool(vm)?;
            if !space {
                if count != 0 {
                    new_str.push(text(" ", vm));
                }
                new_str.push(char);
                count = 0;
            } else {
                count += 1;
            }
        }
        method(&text("", vm), "join", (list_of(new_str, vm),), vm)
    }

    fn str_to_num_value(
        usr_str: &PyObjectRef,
        num_type: &PyObjectRef,
        min: &PyObjectRef,
        max: &PyObjectRef,
        force: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        if eq(usr_str, &none(vm), vm)? {
            return Ok(none(vm));
        }
        let bad_format = |vm: &VirtualMachine| -> PyResult<PyBaseExceptionRef> {
            let message = formatted(
                &text("bad number format: %s", vm),
                vec![num_type.clone()],
                vm,
            )?;
            Ok(vm.new_exception(vm.ctx.exceptions.value_error.to_owned(), vec![message]))
        };
        let evaluation: PyResult<PyObjectRef> = (|| {
            if eq(num_type, &text("float", vm), vm)? {
                constructed("float", (usr_str.clone(),), vm)
            } else if eq(num_type, &text("int", vm), vm)? {
                constructed("int", (usr_str.clone(),), vm)
            } else if eq(num_type, &text("num", vm), vm)? {
                // reserved strings evaluate too: 'open' becomes a builtin, then fails isNum
                let value = evaluated(
                    usr_str,
                    &[
                        ("usrStr", usr_str.clone()),
                        ("numType", num_type.clone()),
                        ("min", min.clone()),
                        ("max", max.clone()),
                        ("force", force.clone()),
                    ],
                    vm,
                )?;
                if !is_num_value(&value, vm)? {
                    return Err(bad_format(vm)?);
                }
                Ok(value)
            } else {
                Err(bad_format(vm)?)
            }
        })();
        let num_eval = match evaluation {
            Ok(value) => value,
            Err(error) => {
                if converted(&error, vm) {
                    return Ok(none(vm));
                }
                return Err(error);
            }
        };
        if ne(min, &none(vm), vm)? && lt(&num_eval, min, vm)? {
            if truthy(force, vm)? {
                return Ok(min.clone());
            }
            return Ok(none(vm));
        }
        if ne(max, &none(vm), vm)? && gt(&num_eval, max, vm)? {
            if truthy(force, vm)? {
                return Ok(max.clone());
            }
            return Ok(none(vm));
        }
        Ok(num_eval)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrToNumArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional, name = "numType")]
        num_type: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        min: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        max: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        force: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "strToNum")]
    pub(crate) fn str_to_num(args: StrToNumArgs, vm: &VirtualMachine) -> PyResult {
        let num_type = args.num_type.unwrap_or_else(|| text("num", vm));
        let min = args.min.unwrap_or_else(|| none(vm));
        let max = args.max.unwrap_or_else(|| none(vm));
        let force = args.force.unwrap_or_else(|| integer(0, vm));
        str_to_num_value(&args.usr_str, &num_type, &min, &max, &force, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrToPercentArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional)]
        fmt: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "strToPercent")]
    pub(crate) fn str_to_percent(args: StrToPercentArgs, vm: &VirtualMachine) -> PyResult {
        let mut fmt = args.fmt.unwrap_or_else(|| none(vm));
        let usr_str = str_scrub_value(&args.usr_str, &none(vm), &list_of(Vec::new(), vm), vm)?;
        if eq(&usr_str, &none(vm), vm)? {
            return Ok(none(vm));
        }
        let usr_str = if ge(
            &method(&usr_str, "find", (text("%", vm),), vm)?,
            &integer(0, vm),
            vm,
        )? {
            fmt = text("macro", vm);
            method(&usr_str, "replace", (text("%", vm), text("", vm)), vm)?
        } else {
            usr_str
        };
        let num = str_to_num_value(
            &usr_str,
            &text("float", vm),
            &integer(0, vm),
            &integer(100, vm),
            &integer(0, vm),
            vm,
        )?;
        if eq(&num, &none(vm), vm)? {
            return Ok(none(vm));
        }
        if eq(&fmt, &none(vm), vm)? && gt(&num, &integer(1, vm), vm)? {
            fmt = text("macro", vm);
        }
        if eq(&fmt, &text("macro", vm), vm)? {
            let hundred: PyObjectRef = vm.ctx.new_float(100.0).into();
            return vm._truediv(&num, &hundred);
        }
        Ok(num)
    }

    fn str_to_list_value(
        usr_str: &PyObjectRef,
        delimit: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let usr_str = method(usr_str, "replace", (delimit.clone(), text(",", vm)), vm)?;
        let usr_str = str_scrub_value(&usr_str, &none(vm), &list_of(Vec::new(), vm), vm)?;
        method(&usr_str, "split", (text(",", vm),), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrToListArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional)]
        delimit: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "strToList")]
    pub(crate) fn str_to_list(args: StrToListArgs, vm: &VirtualMachine) -> PyResult {
        let delimit = args.delimit.unwrap_or_else(|| text(",", vm));
        str_to_list_value(&args.usr_str, &delimit, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrToListFlatArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional)]
        case: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        delimit: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "strToListFlat")]
    pub(crate) fn str_to_list_flat(args: StrToListFlatArgs, vm: &VirtualMachine) -> PyResult {
        let case = args.case.unwrap_or_else(|| none(vm));
        let delimit = args.delimit.unwrap_or_else(|| text(",", vm));
        let mut usr_str = method(&args.usr_str, "replace", (delimit, text(",", vm)), vm)?;
        let doubled = ge(
            &method(&usr_str, "find", (text(",,", vm),), vm)?,
            &integer(0, vm),
            vm,
        )?;
        if doubled {
            usr_str = method(&usr_str, "replace", (text(",,", vm), text(",", vm)), vm)?;
        }
        for (old, new) in [(")", ""), ("(", ""), ("]", ""), ("[", "")] {
            usr_str = method(&usr_str, "replace", (text(old, vm), text(new, vm)), vm)?;
        }
        let usr_str = str_scrub_value(&usr_str, &case, &list_of(Vec::new(), vm), vm)?;
        method(&usr_str, "split", (text(",", vm),), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct StrToSequenceArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, optional, name = "dataLen")]
        data_len: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional, name = "dataTypeList")]
        data_type_list: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        delimit: OptionalArg<PyObjectRef>,
    }

    fn update_sequence_locals(
        locals: &PyObjectRef,
        base: &[(&'static str, PyObjectRef)],
        i: &PyObjectRef,
        previous_data: &Option<PyObjectRef>,
        previous_type: &Option<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        for (name, value) in base {
            locals.set_item(*name, value.clone(), vm)?;
        }
        locals.set_item("i", i.clone(), vm)?;
        if let Some(data) = previous_data {
            locals.set_item("data", data.clone(), vm)?;
        }
        if let Some(type_str) = previous_type {
            locals.set_item("typeStr", type_str.clone(), vm)?;
        }
        Ok(())
    }

    #[pyfunction(name = "strToSequence")]
    pub(crate) fn str_to_sequence(args: StrToSequenceArgs, vm: &VirtualMachine) -> PyResult {
        let data_len = args.data_len.unwrap_or_else(|| none(vm));
        let data_type_list = args.data_type_list.unwrap_or_else(|| none(vm));
        let delimit = args.delimit.unwrap_or_else(|| text(",", vm));
        let usr_list = str_to_list_value(&args.usr_str, &delimit, vm)?;
        if eq(&usr_list, &list_of(Vec::new(), vm), vm)? {
            return Ok(none(vm));
        }
        if ne(&data_len, &none(vm), vm)?
            && ne(&integer(length(&usr_list, vm)? as i64, vm), &data_len, vm)?
        {
            return Ok(none(vm));
        }
        let new_list = list_of(Vec::new(), vm);
        let locals: PyObjectRef = vm.ctx.new_dict().into();
        let mut previous_data: Option<PyObjectRef> = None;
        let mut previous_type: Option<PyObjectRef> = None;
        let base_locals = vec![
            ("usrStr", args.usr_str.clone()),
            ("dataLen", data_len.clone()),
            ("dataTypeList", data_type_list.clone()),
            ("delimit", delimit.clone()),
            ("usrList", usr_list.clone()),
            ("newList", new_list.clone()),
        ];
        for i in builtin("range", vm)?
            .call((integer(length(&usr_list, vm)? as i64, vm),), vm)?
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let i = i?;
            let element = usr_list.get_item(i.as_object(), vm)?;
            update_sequence_locals(
                &locals,
                &base_locals,
                &i,
                &previous_data,
                &previous_type,
                vm,
            )?;
            let data = match evaluated_in_scope(&element, &locals, vm) {
                Ok(data) => data,
                Err(error) => {
                    if converted(&error, vm) {
                        return Ok(none(vm));
                    }
                    return Err(error);
                }
            };
            if ne(&data_type_list, &none(vm), vm)? {
                let index = vm._mod(&i, &integer(length(&data_type_list, vm)? as i64, vm))?;
                let type_str = data_type_list.get_item(index.as_object(), vm)?;
                if !is_type_value(&data, &type_str, vm)? {
                    return Ok(none(vm));
                }
                previous_type = Some(type_str);
            }
            previous_data = Some(data.clone());
            method(&new_list, "append", (data,), vm)?;
        }
        Ok(new_list)
    }

    #[derive(FromArgs)]
    pub(crate) struct UrlStrBreakArgs {
        #[pyarg(any)]
        url: PyObjectRef,
    }

    #[pyfunction(name = "urlStrBreak")]
    pub(crate) fn url_str_break(args: UrlStrBreakArgs, vm: &VirtualMachine) -> PyResult {
        let http = text("http://", vm);
        let bounds = |vm: &VirtualMachine| {
            vm.ctx
                .types
                .slice_type
                .as_object()
                .call((none(vm), integer(7, vm)), vm)
        };
        let leading = args.url.get_item(bounds(vm)?.as_object(), vm)?;
        let (head, tail) = if eq(&leading, &http, vm)? {
            (
                leading,
                args.url.get_item(
                    vm.ctx
                        .types
                        .slice_type
                        .as_object()
                        .call((integer(7, vm), none(vm)), vm)?
                        .as_object(),
                    vm,
                )?,
            )
        } else {
            (text("", vm), args.url.clone())
        };
        let tail = method(&tail, "replace", (text("/", vm), text("/ ", vm)), vm)?;
        let tail = method(&tail, "replace", (text(";", vm), text("; ", vm)), vm)?;
        let tail = method(&tail, "replace", (text("=", vm), text("= ", vm)), vm)?;
        vm._add(&head, &tail)
    }

    #[derive(FromArgs)]
    pub(crate) struct UrlPrepArgs {
        #[pyarg(any)]
        url: PyObjectRef,
        #[pyarg(any, optional)]
        fmt: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "urlPrep")]
    pub(crate) fn url_prep(args: UrlPrepArgs, vm: &VirtualMachine) -> PyResult {
        let http_stub = text("http://", vm);
        let file_stub = text("file://", vm);
        let fmt = match args.fmt {
            OptionalArg::Missing => http_stub.clone(),
            OptionalArg::Present(fmt) => {
                if eq(&fmt, &none(vm), vm)? || eq(&fmt, &text("http", vm), vm)? {
                    http_stub.clone()
                } else if eq(&fmt, &text("file", vm), vm)? {
                    file_stub
                } else {
                    fmt
                }
            }
        };
        let bound = integer(length(&fmt, vm)? as i64, vm);
        let leading = args.url.get_item(
            vm.ctx
                .types
                .slice_type
                .as_object()
                .call((none(vm), bound), vm)?
                .as_object(),
            vm,
        )?;
        if ne(&leading, &fmt, vm)? {
            formatted(&text("%s%s", vm), vec![fmt, args.url], vm)
        } else {
            Ok(args.url)
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct PathStrBreakArgs {
        #[pyarg(any)]
        path: PyObjectRef,
    }

    #[pyfunction(name = "pathStrBreak")]
    pub(crate) fn path_str_break(args: PathStrBreakArgs, vm: &VirtualMachine) -> PyResult {
        method(&args.path, "replace", (text("/", vm), text("/ ", vm)), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct IntToStrArgs {
        #[pyarg(any)]
        num: PyObjectRef,
        #[pyarg(any, optional, name = "zeroBuff")]
        zero_buff: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "intToStr")]
    pub(crate) fn int_to_str(args: IntToStrArgs, vm: &VirtualMachine) -> PyResult {
        let mut msg = constructed("str", (args.num,), vm)?;
        let zero_buff = match args.zero_buff {
            OptionalArg::Missing => return Ok(msg),
            OptionalArg::Present(buff) => buff,
        };
        if eq(&zero_buff, &none(vm), vm)? {
            return Ok(msg);
        }
        let msg_length = integer(length(&msg, vm)? as i64, vm);
        if gt(&zero_buff, &msg_length, vm)? {
            let filler = vm._sub(&zero_buff, &msg_length)?;
            for _x in builtin("range", vm)?
                .call((filler,), vm)?
                .get_iter(vm)?
                .iter_without_hint::<PyObjectRef>(vm)?
            {
                _x?;
                msg = vm._add(&text("0", vm), &msg)?;
            }
        }
        Ok(msg)
    }

    #[derive(FromArgs)]
    pub(crate) struct IntHalfArgs {
        #[pyarg(any)]
        num: PyObjectRef,
    }

    #[pyfunction(name = "intHalf")]
    pub(crate) fn int_half(args: IntHalfArgs, vm: &VirtualMachine) -> PyResult {
        let remainder = vm._mod(&args.num, &integer(2, vm))?;
        let left = vm._truediv(&args.num, &integer(2, vm))?;
        if eq(&remainder, &integer(0, vm), vm)? {
            Ok(pair(left.clone(), left, vm))
        } else {
            let right = vm._add(&left, &integer(1, vm))?;
            Ok(pair(left, right, vm))
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct FloatToIntArgs {
        #[pyarg(any)]
        x: PyObjectRef,
        #[pyarg(any, optional)]
        method: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "floatToInt")]
    pub(crate) fn float_to_int(args: FloatToIntArgs, vm: &VirtualMachine) -> PyResult {
        let method = args.method.unwrap_or_else(|| text("round", vm));
        if is_int_value(&args.x, vm)? {
            return Ok(args.x);
        }
        if eq(&method, &text("round", vm), vm)? {
            let rounded = builtin("round", vm)?.call((args.x.clone(),), vm)?;
            return constructed("int", (rounded,), vm);
        }
        if eq(&method, &text("floor", vm), vm)? {
            let divided = vm._divmod(&args.x, &integer(1, vm))?;
            let (whole, _fraction) = pair_of(&divided, vm)?;
            return constructed("int", (whole,), vm);
        }
        if eq(&method, &text("ceiling", vm), vm)? {
            let divided = vm._divmod(&args.x, &integer(1, vm))?;
            let (whole, fraction) = pair_of(&divided, vm)?;
            return ceiling_of(&whole, &fraction, vm);
        }
        if eq(&method, &text("weight", vm), vm)? {
            let q = own_module(vm)?
                .get_attr("random", vm)?
                .get_attr("random", vm)?
                .call((), vm)?;
            let divided = vm._divmod(&args.x, &integer(1, vm))?;
            let (whole, fraction) = pair_of(&divided, vm)?;
            return weighted_int(&whole, &fraction, &q, vm);
        }
        Ok(none(vm))
    }

    /// The ceiling: one whole more whenever a fraction remains.
    fn ceiling_of(whole: &PyObjectRef, fraction: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let mut shift = integer(0, vm);
        if gt(fraction, &integer(0, vm), vm)? {
            shift = integer(1, vm);
        }
        let whole = constructed("int", (whole.clone(),), vm)?;
        vm._add(&whole, &shift)
    }

    /// The weighted rounding: a draw from the random module's alias — the parameters stream —
    /// decides which side of the fraction the result falls on.
    fn weighted_int(
        whole: &PyObjectRef,
        fraction: &PyObjectRef,
        q: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let half: PyObjectRef = vm.ctx.new_float(0.5).into();
        let weight = if eq(fraction, &half, vm)? {
            if ge(q, &half, vm)? {
                integer(1, vm)
            } else {
                integer(0, vm)
            }
        } else if gt(fraction, &half, vm)? {
            if le(q, fraction, vm)? {
                integer(1, vm)
            } else {
                integer(0, vm)
            }
        } else if lt(fraction, &half, vm)? {
            if ge(q, fraction, vm)? {
                integer(0, vm)
            } else {
                integer(1, vm)
            }
        } else {
            return Err(vm.new_exception_msg(
                vm.ctx.exceptions.unbound_local_error.to_owned(),
                "local variable 'weight' referenced before assignment".into(),
            ));
        };
        let weighted = vm._add(whole, &weight)?;
        constructed("int", (weighted,), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct GenAlphaLabelArgs {
        #[pyarg(any)]
        number: PyObjectRef,
    }

    #[pyfunction(name = "genAlphaLabel")]
    pub(crate) fn gen_alpha_label(args: GenAlphaLabelArgs, vm: &VirtualMachine) -> PyResult {
        let symbols = module("string", vm)?.get_attr("ascii_lowercase", vm)?;
        let mut labels = Vec::new();
        for n in builtin("range", vm)?
            .call((args.number,), vm)?
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let n = n?;
            let pieces = label_ordered(&n, &symbols, vm)?;
            let label = method(&text("", vm), "join", (list_of(pieces, vm),), vm)?;
            labels.push(label);
        }
        Ok(list_of(labels, vm))
    }

    #[derive(FromArgs)]
    pub(crate) struct AcronymLibToStrArgs {
        #[pyarg(any, name = "refDict")]
        ref_dict: PyObjectRef,
    }

    #[pyfunction(name = "acronymLibToStr")]
    pub(crate) fn acronym_lib_to_str(args: AcronymLibToStrArgs, vm: &VirtualMachine) -> PyResult {
        let mut short = Vec::new();
        let mut vlong = Vec::new();
        let keys = constructed("list", (method(&args.ref_dict, "keys", (), vm)?,), vm)?;
        method(&keys, "sort", (), vm)?;
        for key in keys.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let key = key?;
            short.push(key.clone());
            vlong.push(args.ref_dict.get_item(key.as_object(), vm)?);
        }
        let joined_short = method(&text(", ", vm), "join", (list_of(short, vm),), vm)?;
        let joined_long = method(&text(", ", vm), "join", (list_of(vlong, vm),), vm)?;
        Ok(pair(joined_long, joined_short, vm))
    }

    fn acronym_extract_value(usr_str: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let upper = module("string", vm)?.get_attr("ascii_uppercase", vm)?;
        let mut auto_str = Vec::new();
        let count = integer(length(usr_str, vm)? as i64, vm);
        for i in builtin("range", vm)?
            .call((count,), vm)?
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let i = i?;
            let char = usr_str.get_item(i.as_object(), vm)?;
            if eq(&i, &integer(0, vm), vm)? {
                auto_str.push(char.clone());
            } else if contains(&upper, &char, vm)? {
                auto_str.push(char);
            }
        }
        let joined = method(&text("", vm), "join", (list_of(auto_str, vm),), vm)?;
        str_scrub_value(&joined, &text("lower", vm), &list_of(Vec::new(), vm), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct AcronymExtractArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
    }

    #[pyfunction(name = "acronymExtract")]
    pub(crate) fn acronym_extract(args: AcronymExtractArgs, vm: &VirtualMachine) -> PyResult {
        acronym_extract_value(&args.usr_str, vm)
    }

    fn option_unique_value(ref_dict: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        let mut first_char: Vec<PyObjectRef> = Vec::new();
        let keys = constructed("list", (method(ref_dict, "keys", (), vm)?,), vm)?;
        for label in keys.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let label = method(&label?, "lower", (), vm)?;
            let char = label.get_item(integer(0, vm).as_object(), vm)?;
            let mut repeated = false;
            for seen in &first_char {
                if eq(seen, &char, vm)? {
                    repeated = true;
                    break;
                }
            }
            if repeated {
                return Ok(false);
            }
            first_char.push(char);
        }
        Ok(true)
    }

    #[derive(FromArgs)]
    pub(crate) struct OptionUniqueKeyLeadCharArgs {
        #[pyarg(any, name = "refDict")]
        ref_dict: PyObjectRef,
    }

    #[pyfunction(name = "optionUniqueKeyLeadChar")]
    pub(crate) fn option_unique_key_lead_char(
        args: OptionUniqueKeyLeadCharArgs,
        vm: &VirtualMachine,
    ) -> PyResult {
        Ok(boolean(option_unique_value(&args.ref_dict, vm)?, vm))
    }

    #[derive(FromArgs)]
    pub(crate) struct AcronymExpandArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, name = "refDict")]
        ref_dict: PyObjectRef,
        #[pyarg(any, optional, name = "autoSearch")]
        auto_search: OptionalArg<PyObjectRef>,
    }

    fn auto_search_value(
        given: OptionalArg<PyObjectRef>,
        ref_dict: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let value = given.unwrap_or_else(|| none(vm));
        if eq(&value, &none(vm), vm)? {
            Ok(boolean(option_unique_value(ref_dict, vm)?, vm))
        } else {
            Ok(value)
        }
    }

    #[pyfunction(name = "acronymExpand")]
    pub(crate) fn acronym_expand(args: AcronymExpandArgs, vm: &VirtualMachine) -> PyResult {
        if eq(&args.usr_str, &none(vm), vm)? {
            return Ok(none(vm));
        }
        if !(is_str_value(&args.usr_str, vm)? && is_dict_value(&args.ref_dict, vm)?) {
            let class: PyObjectRef = vm.ctx.exceptions.assertion_error.to_owned().into();
            return Err(bare(&class, vm));
        }
        if eq(&args.usr_str, &text("", vm), vm)? {
            return Ok(none(vm));
        }
        let auto_search = auto_search_value(args.auto_search, &args.ref_dict, vm)?;
        let auto_str = acronym_extract_value(&args.usr_str, vm)?;
        let usr_str = str_scrub_value(
            &args.usr_str,
            &text("lower", vm),
            &list_of(Vec::new(), vm),
            vm,
        )?;
        let keys = constructed("list", (method(&args.ref_dict, "keys", (), vm)?,), vm)?;
        if let Some(found) = acronym_direct(&usr_str, &keys, &args.ref_dict, vm)? {
            return Ok(found);
        }
        if truthy(&auto_search, vm)? {
            if let Some(found) = acronym_auto(&auto_str, &keys, &args.ref_dict, vm)? {
                return Ok(found);
            }
        }
        Ok(none(vm))
    }

    /// Walk a reference dictionary's keys, returning the first key's value a matcher accepts.
    fn key_match(
        keys: &PyObjectRef,
        ref_dict: &PyObjectRef,
        matches: impl Fn(&PyObjectRef, &PyObjectRef) -> PyResult<bool>,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        for key in keys.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let key = key?;
            let lowered = method(&key, "lower", (), vm)?;
            let value = ref_dict.get_item(key.as_object(), vm)?;
            if matches(&lowered, &value)? {
                return Ok(Some(value));
            }
        }
        Ok(None)
    }

    /// The direct search: the scrubbed string against lowered keys and values alike.
    fn acronym_direct(
        usr_str: &PyObjectRef,
        keys: &PyObjectRef,
        ref_dict: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        key_match(
            keys,
            ref_dict,
            |lowered_key, value| {
                if eq(usr_str, lowered_key, vm)? {
                    return Ok(true);
                }
                let value_lowered = method(value, "lower", (), vm)?;
                eq(usr_str, &value_lowered, vm)
            },
            vm,
        )
    }

    /// The auto search: the extracted acronym against lowered keys.
    fn acronym_auto(
        auto_str: &PyObjectRef,
        keys: &PyObjectRef,
        ref_dict: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        key_match(
            keys,
            ref_dict,
            |lowered_key, _value| eq(auto_str, lowered_key, vm),
            vm,
        )
    }

    #[derive(FromArgs)]
    pub(crate) struct SelectionParseArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
        #[pyarg(any, name = "refDict")]
        ref_dict: PyObjectRef,
        #[pyarg(any, optional, name = "autoSearch")]
        auto_search: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "selectionParse")]
    pub(crate) fn selection_parse(args: SelectionParseArgs, vm: &VirtualMachine) -> PyResult {
        let prepared = selection_prepare(&args.usr_str, &args.ref_dict, vm)?;
        let (usr_str, auto_str) = match prepared {
            Some(prepared) => prepared,
            None => return Ok(none(vm)),
        };
        let auto_search = auto_search_value(args.auto_search, &args.ref_dict, vm)?;
        let keys = constructed("list", (method(&args.ref_dict, "keys", (), vm)?,), vm)?;
        for key in keys.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let key = key?;
            if selection_key_matches(&usr_str, &key, &args.ref_dict, vm)? {
                return Ok(key);
            }
        }
        if truthy(&auto_search, vm)? {
            for key in keys.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
                let key = key?;
                let auto_key = acronym_extract_value(&key, vm)?;
                if eq(&auto_str, &auto_key, vm)? {
                    return Ok(key);
                }
            }
        }
        Ok(none(vm))
    }

    /// The selection prologue: numbers become strings, empty selections end the search, and the
    /// scrubbed string and its acronym come back together.
    fn selection_prepare(
        usr_str: &PyObjectRef,
        ref_dict: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<(PyObjectRef, PyObjectRef)>> {
        if eq(usr_str, &none(vm), vm)? {
            return Ok(None);
        }
        if !(is_dict_value(ref_dict, vm)?
            && (is_str_value(usr_str, vm)? || is_num_value(usr_str, vm)?))
        {
            let class: PyObjectRef = vm.ctx.exceptions.assertion_error.to_owned().into();
            return Err(bare(&class, vm));
        }
        let usr_str = if is_num_value(usr_str, vm)? {
            constructed("str", (usr_str.clone(),), vm)?
        } else {
            usr_str.clone()
        };
        if eq(&usr_str, &text("", vm), vm)? {
            return Ok(None);
        }
        let auto_str = acronym_extract_value(&usr_str, vm)?;
        let usr_str = str_scrub_value(&usr_str, &text("lower", vm), &list_of(Vec::new(), vm), vm)?;
        Ok(Some((usr_str, auto_str)))
    }

    /// Whether one selection key matches: its own name, lowered or stringed, or any of its synonym
    /// values, lowered.
    fn selection_key_matches(
        usr_str: &PyObjectRef,
        key: &PyObjectRef,
        ref_dict: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        let named = if is_str_value(key, vm)? {
            let lowered = method(key, "lower", (), vm)?;
            eq(&lowered, usr_str, vm)?
        } else {
            let stringed = constructed("str", (key.clone(),), vm)?;
            eq(&stringed, usr_str, vm)?
        };
        if named {
            return Ok(true);
        }
        let options = ref_dict.get_item(key.as_object(), vm)?;
        for val in options.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let val = val?;
            let val = if !is_str_value(&val, vm)? {
                constructed("str", (val,), vm)?
            } else {
                val
            };
            let lowered = method(&val, "lower", (), vm)?;
            if eq(&lowered, usr_str, vm)? {
                return Ok(true);
            }
        }
        Ok(false)
    }

    #[derive(FromArgs)]
    pub(crate) struct SelectionParseKeyLabelArgs {
        #[pyarg(any)]
        r#ref: PyObjectRef,
        #[pyarg(any, optional, name = "finalStr")]
        final_str: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "selectionParseKeyLabel")]
    pub(crate) fn selection_parse_key_label(
        args: SelectionParseKeyLabelArgs,
        vm: &VirtualMachine,
    ) -> PyResult {
        let final_str = args.final_str.unwrap_or_else(|| text("or", vm));
        let names = constructed("list", (method(&args.r#ref, "keys", (), vm)?,), vm)?;
        if eq(
            &integer(length(&names, vm)? as i64, vm),
            &integer(1, vm),
            vm,
        )? {
            return names.get_item(integer(0, vm).as_object(), vm);
        }
        method(&names, "sort", (), vm)?;
        let last = names.get_item(integer(-1, vm).as_object(), vm)?;
        let labeled = formatted(&text("%s %s", vm), vec![final_str, last], vm)?;
        names.set_item(integer(-1, vm).as_object(), labeled, vm)?;
        if le(
            &integer(length(&names, vm)? as i64, vm),
            &integer(2, vm),
            vm,
        )? {
            method(&text(" ", vm), "join", (names,), vm)
        } else {
            method(&text(", ", vm), "join", (names,), vm)
        }
    }

    fn restring_comma_value(
        direction: &PyObjectRef,
        usr_str: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let sym = text("???????", vm);
        let comma = text(",", vm);
        if eq(direction, &text("out", vm), vm)? {
            return method(usr_str, "replace", (sym, comma), vm);
        }
        let mut current = slice_of(usr_str, none(vm), none(vm), vm)?;
        for (open, close) in [("'", "'"), ("\"", "\""), ("{", "}")] {
            let open = text(open, vm);
            let close = text(close, vm);
            let mut status = 0;
            let mut built = Vec::new();
            for char in current.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
                let char = char?;
                if eq(&char, &open, vm)? {
                    status = 1;
                }
                if eq(&char, &close, vm)? {
                    status = 0;
                }
                if ne(&char, &comma, vm)? {
                    built.push(char);
                } else if status != 0 {
                    built.push(sym.clone());
                } else {
                    built.push(comma.clone());
                }
            }
            current = method(&text("", vm), "join", (list_of(built, vm),), vm)?;
        }
        Ok(current)
    }

    #[derive(FromArgs)]
    pub(crate) struct RestringCommaArgs {
        #[pyarg(any)]
        direction: PyObjectRef,
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
    }

    #[pyfunction(name = "_restringComma")]
    pub(crate) fn restring_comma(args: RestringCommaArgs, vm: &VirtualMachine) -> PyResult {
        restring_comma_value(&args.direction, &args.usr_str, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct RestringulatorArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
    }

    #[pyfunction(name = "restringulator")]
    pub(crate) fn restringulator(args: RestringulatorArgs, vm: &VirtualMachine) -> PyResult {
        if eq(&args.usr_str, &text("", vm), vm)? {
            return Ok(args.usr_str);
        }
        let comma = text(",", vm);
        let encoded = restring_comma_value(&text("in", vm), &args.usr_str, vm)?;
        let divided = method(&encoded, "split", (comma.clone(),), vm)?;
        let mut new_str = Vec::new();
        for part in divided.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let part = method(&part?, "strip", (), vm)?;
            let part = method(&part, "replace", (text("[", vm), text("(", vm)), vm)?;
            let part = method(&part, "replace", (text("]", vm), text(")", vm)), vm)?;
            let part_clean = slice_of(&part, none(vm), none(vm), vm)?;
            let part_clean = method(&part_clean, "replace", (text("(", vm), text("", vm)), vm)?;
            let part_clean = method(&part_clean, "replace", (text(")", vm), text("", vm)), vm)?;
            if let Some(part) = quoted_part(&part, &part_clean, vm)? {
                new_str.push(part);
                continue;
            }
            new_str.extend(alpha_parts(&part, &part_clean, vm)?);
        }
        let joined = method(&comma, "join", (list_of(new_str, vm),), vm)?;
        let bracketed = method(&joined, "replace", (text("(", vm), text("[", vm)), vm)?;
        let bracketed = method(&bracketed, "replace", (text(")", vm), text("]", vm)), vm)?;
        restring_comma_value(&text("out", vm), &bracketed, vm)
    }

    /// The alpha decision and the quoting restringulator applies to one comma-divided part: either
    /// the part as it stands, or its paren-stripped core wrapped in the part's own parentheses as a
    /// quoted string.
    ///
    /// A part already carrying an even count of one quote kind and none of the other stays as it
    /// stands; badly matched quotes are stripped and the part continues to the alpha inspection.
    fn quoted_part(
        part: &PyObjectRef,
        part_clean: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        let double_quote = text("\"", vm);
        let single_quote = text("'", vm);
        let has_double = ge(
            &method(part, "find", (double_quote.clone(),), vm)?,
            &integer(0, vm),
            vm,
        )?;
        let has_single = ge(
            &method(part, "find", (single_quote.clone(),), vm)?,
            &integer(0, vm),
            vm,
        )?;
        if !has_double && !has_single {
            return Ok(None);
        }
        let doubles = method(part, "count", (double_quote.clone(),), vm)?;
        let singles = method(part, "count", (single_quote.clone(),), vm)?;
        let even_doubles = eq(&vm._mod(&doubles, &integer(2, vm))?, &integer(0, vm), vm)?;
        let even_singles = eq(&vm._mod(&singles, &integer(2, vm))?, &integer(0, vm), vm)?;
        if (even_doubles && eq(&singles, &integer(0, vm), vm)?)
            || (even_singles && eq(&doubles, &integer(0, vm), vm)?)
        {
            return Ok(Some(part.clone()));
        }
        let stripped = method(part, "replace", (double_quote, text("", vm)), vm)?;
        let stripped = method(&stripped, "replace", (single_quote, text("", vm)), vm)?;
        Ok(alpha_parts(&stripped, part_clean, vm)?.pop())
    }

    fn alpha_parts(
        part: &PyObjectRef,
        part_clean: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Vec<PyObjectRef>> {
        if !is_alpha_part(part, part_clean, vm)? {
            return Ok(vec![part.clone()]);
        }
        Ok(vec![quoted_piece(part, vm)?])
    }

    /// Whether a comma-divided part reads as a string: an early decisive character, a non-number
    /// core, or one of the logical, sieve, and markov symbols.
    fn is_alpha_part(
        part: &PyObjectRef,
        part_clean: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        let mut alpha = false;
        let special = list_of(["/", "+", "_"].iter().map(|c| text(c, vm)).collect(), vm);
        for char in part.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let char = char?;
            if eq(&char, &text("(", vm), vm)? || eq(&char, &text(" ", vm), vm)? {
                continue;
            }
            let is_alpha = method(&char, "isalpha", (), vm)?.try_to_bool(vm)?;
            alpha = if is_alpha {
                true
            } else {
                contains(&special, &char, vm)?
            };
            break;
        }
        if !is_char_num_value(part_clean, vm)? {
            alpha = true;
        }
        for sym in ["|", "&", "@", "{", "}", "="] {
            let found = method(part, "__contains__", (text(sym, vm),), vm)?;
            if found.try_to_bool(vm)? {
                alpha = true;
                break;
            }
        }
        Ok(alpha)
    }

    /// The quoted piece: the part's parentheses wrapped around its stripped core, the core rendered
    /// through %r.
    fn quoted_piece(part: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let mut paren_open = Vec::new();
        let mut paren_close = Vec::new();
        let mut part_str = Vec::new();
        for char in part.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let char = char?;
            if eq(&char, &text("(", vm), vm)? {
                paren_open.push(char);
            } else if eq(&char, &text(")", vm), vm)? {
                paren_close.push(char);
            } else {
                part_str.push(char);
            }
        }
        let opened = method(&text("", vm), "join", (list_of(paren_open, vm),), vm)?;
        let core = method(&text("", vm), "join", (list_of(part_str, vm),), vm)?;
        let core = method(&core, "strip", (), vm)?;
        let closed = method(&text("", vm), "join", (list_of(paren_close, vm),), vm)?;
        formatted(&text("%s%r%s", vm), vec![opened, core, closed], vm)
    }

    // -- group three: environment helpers -------------------------------------

    /// The clock strings share one shape: a zone's clock, its asctime split apart, the year read
    /// from the tuple itself, and the zone's own label.
    fn clock_str(zone: &'static str, label: &'static str, vm: &VirtualMachine) -> PyResult {
        let time = vm.import("time", 0)?;
        let raw = time.get_attr(zone, vm)?.call((), vm)?;
        let asc = time.get_attr("asctime", vm)?.call((raw.clone(),), vm)?;
        let asc = method(&asc, "replace", (text(" ", vm), text(" ", vm)), vm)?;
        let parts = method(&asc, "split", (text(" ", vm),), vm)?;
        let message = formatted(
            &text("%s, %s %s %s %s ", vm),
            vec![
                parts.get_item(integer(0, vm).as_object(), vm)?,
                raw.get_item(integer(2, vm).as_object(), vm)?,
                parts.get_item(integer(1, vm).as_object(), vm)?,
                raw.get_item(integer(0, vm).as_object(), vm)?,
                parts.get_item(integer(3, vm).as_object(), vm)?,
            ],
            vm,
        )?;
        vm._add(&message, &text(label, vm))
    }

    #[pyfunction(name = "gmtimeStr")]
    pub(crate) fn gmtime_str(vm: &VirtualMachine) -> PyResult {
        clock_str("gmtime", "GMT", vm)
    }

    #[pyfunction(name = "localtimeStr")]
    pub(crate) fn localtime_str(vm: &VirtualMachine) -> PyResult {
        clock_str("localtime", "EST", vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct GmtimeStampArgs {
        #[pyarg(any, optional, name = "sigDig")]
        sig_dig: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        zone: OptionalArg<PyObjectRef>,
    }

    fn gmtime_stamp_value(
        sig_dig: &PyObjectRef,
        zone: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let time = vm.import("time", 0)?;
        let zone_call = if eq(zone, &text("gmt", vm), vm)? {
            "gmtime"
        } else {
            "localtime"
        };
        let tuple = constructed("list", (time.get_attr(zone_call, vm)?.call((), vm)?,), vm)?;
        let zero = integer(0, vm);
        let six = integer(6, vm);
        let tuple = if gt(sig_dig, &zero, vm)? {
            slice_of(&tuple, zero, sig_dig.clone(), vm)?
        } else {
            let from = builtin("abs", vm)?.call((sig_dig.clone(),), vm)?;
            slice_of(&tuple, from, six, vm)?
        };
        let mut str_name = text("", vm);
        for entry in tuple.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let entry = entry?;
            if le(&entry, &integer(9, vm), vm)? {
                let stringed = constructed("str", (entry,), vm)?;
                let piece = formatted(&text(".0%s", vm), vec![stringed], vm)?;
                str_name = vm._add(&str_name, &piece)?;
            } else {
                let stringed = constructed("str", (entry,), vm)?;
                let piece = formatted(&text(".%s", vm), vec![stringed], vm)?;
                str_name = vm._add(&str_name, &piece)?;
            }
        }
        slice_of(&str_name, integer(1, vm), none(vm), vm)
    }

    #[pyfunction(name = "gmtimeStamp")]
    pub(crate) fn gmtime_stamp(args: GmtimeStampArgs, vm: &VirtualMachine) -> PyResult {
        let sig_dig = args.sig_dig.unwrap_or_else(|| integer(6, vm));
        let zone = args.zone.unwrap_or_else(|| text("gmt", vm));
        gmtime_stamp_value(&sig_dig, &zone, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct LocaltimeStampArgs {
        #[pyarg(any, optional, name = "sigDig")]
        sig_dig: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "localtimeStamp")]
    pub(crate) fn localtime_stamp(args: LocaltimeStampArgs, vm: &VirtualMachine) -> PyResult {
        let sig_dig = args.sig_dig.unwrap_or_else(|| integer(6, vm));
        gmtime_stamp_value(&sig_dig, &text("local", vm), vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct TempDirArgs {
        #[pyarg(any, optional, name = "tempPath")]
        temp_path: OptionalArg<PyObjectRef>,
    }

    fn temp_dir_value(temp_path: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let os_path = module("athenaCL.libATH.drawer", vm)?
            .get_attr("os", vm)?
            .get_attr("path", vm)?;
        let exists = os_path
            .get_attr("exists", vm)?
            .call((temp_path.clone(),), vm)?;
        if truthy(&exists, vm)? {
            Ok(temp_path.clone())
        } else {
            let tempfile = vm.import("tempfile", 0)?;
            tempfile.get_attr("mkdtemp", vm)?.call((), vm)
        }
    }

    #[pyfunction(name = "tempDir")]
    pub(crate) fn temp_dir(args: TempDirArgs, vm: &VirtualMachine) -> PyResult {
        let temp_path = args
            .temp_path
            .unwrap_or_else(|| text("/Volumes/xdisc/_scratch", vm));
        temp_dir_value(&temp_path, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct TempFileNameArgs {
        #[pyarg(any)]
        ext: PyObjectRef,
    }

    #[pyfunction(name = "tempFileName")]
    pub(crate) fn temp_file_name(args: TempFileNameArgs, vm: &VirtualMachine) -> PyResult {
        let stamp = gmtime_stamp_value(&integer(6, vm), &text("local", vm), vm)?;
        let head = vm._add(&text("ath", vm), &stamp)?;
        vm._add(&head, &args.ext)
    }

    #[derive(FromArgs)]
    pub(crate) struct TempFileArgs {
        #[pyarg(any, optional)]
        ext: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional, name = "fpDir")]
        fp_dir: OptionalArg<PyObjectRef>,
    }

    #[pyfunction(name = "tempFile")]
    pub(crate) fn temp_file(args: TempFileArgs, vm: &VirtualMachine) -> PyResult {
        let ext = args.ext.unwrap_or_else(|| text(".txt", vm));
        let fp_dir = args.fp_dir.unwrap_or_else(|| text("", vm));
        let fp_dir = temp_dir_value(&fp_dir, vm)?;
        let os_path = own_module(vm)?.get_attr("os", vm)?.get_attr("path", vm)?;
        let exists = os_path
            .get_attr("exists", vm)?
            .call((fp_dir.clone(),), vm)?;
        if !truthy(&exists, vm)? {
            let tempfile = vm.import("tempfile", 0)?;
            tempfile.get_attr("mktemp", vm)?.call((ext,), vm)
        } else {
            let stamp = gmtime_stamp_value(&integer(6, vm), &text("gmt", vm), vm)?;
            let name = vm._add(&stamp, &ext)?;
            os_path.get_attr("join", vm)?.call((fp_dir, name), vm)
        }
    }

    #[pyfunction(name = "isCarbon")]
    pub(crate) fn is_carbon(vm: &VirtualMachine) -> PyResult {
        match vm.import("Carbon.File", 0) {
            Ok(_carbon) => Ok(integer(1, vm)),
            Err(carbon_error) => {
                if !carbon_error
                    .class()
                    .fast_issubclass(vm.ctx.exceptions.import_error)
                {
                    return Err(carbon_error);
                }
                match vm.import("macfs", 0) {
                    Ok(_macfs) => Ok(integer(0, vm)),
                    Err(macfs_error) => {
                        if !macfs_error
                            .class()
                            .fast_issubclass(vm.ctx.exceptions.import_error)
                        {
                            return Err(macfs_error);
                        }
                        // neither exists here, as neither did in the reference's python 3
                        Ok(integer(-1, vm))
                    }
                }
            }
        }
    }

    fn is_darwin_value(vm: &VirtualMachine) -> PyResult<bool> {
        let os = own_module(vm)?.get_attr("os", vm)?;
        let uname = os.get_attr("uname", vm)?.call((), vm)?;
        let name = uname.get_item(integer(0, vm).as_object(), vm)?;
        let lowered = method(&name, "lower", (), vm)?;
        let starts = method(&lowered, "startswith", (text("darwin", vm),), vm)?;
        starts.try_to_bool(vm)
    }

    #[pyfunction(name = "isDarwin")]
    pub(crate) fn is_darwin(vm: &VirtualMachine) -> PyResult {
        Ok(integer(i64::from(is_darwin_value(vm)?), vm))
    }

    #[pyfunction(name = "isIdle")]
    pub(crate) fn is_idle(vm: &VirtualMachine) -> PyResult {
        let sys = own_module(vm)?.get_attr("sys", vm)?;
        let stdin = sys.get_attr("stdin", vm)?;
        let class = stdin.get_attr("__class__", vm)?;
        let stringed = constructed("str", (class,), vm)?;
        let lowered = method(&stringed, "lower", (), vm)?;
        let found = method(&lowered, "find", (text("idle", vm),), vm)?;
        if ge(&found, &integer(0, vm), vm)? {
            Ok(integer(1, vm))
        } else {
            Ok(integer(0, vm))
        }
    }

    #[pyfunction(name = "isPy24Better")]
    pub(crate) fn is_py24_better(vm: &VirtualMachine) -> PyResult {
        let sys = own_module(vm)?.get_attr("sys", vm)?;
        let version = sys.get_attr("version", vm)?;
        let head = slice_of(&version, none(vm), integer(3, vm), vm)?;
        let old = list_of(
            ["1.5", "1.6", "2.0", "2.1", "2.2", "2.3"]
                .iter()
                .map(|v| text(v, vm))
                .collect(),
            vm,
        );
        if contains(&old, &head, vm)? {
            Ok(integer(0, vm))
        } else {
            Ok(integer(1, vm))
        }
    }

    #[pyfunction(name = "isSudo")]
    pub(crate) fn is_sudo(vm: &VirtualMachine) -> PyResult {
        let os = own_module(vm)?.get_attr("os", vm)?;
        let name = os.get_attr("name", vm)?;
        if ne(&name, &text("posix", vm), vm)? {
            return Ok(integer(0, vm));
        }
        let subprocess = vm.import("subprocess", 0)?;
        let result = subprocess
            .get_attr("getstatusoutput", vm)?
            .call((text("sudo -V", vm),), vm)?;
        let status = result.get_item(integer(0, vm).as_object(), vm)?;
        if eq(&status, &integer(0, vm), vm)? {
            Ok(integer(1, vm))
        } else {
            Ok(integer(0, vm))
        }
    }

    fn is_app_value(fp: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let os = own_module(vm)?.get_attr("os", vm)?;
        let os_path = os.get_attr("path", vm)?;
        if eq(fp, &none(vm), vm)? {
            return Ok(integer(0, vm));
        }
        let exists = os_path.get_attr("exists", vm)?.call((fp.clone(),), vm)?;
        if !truthy(&exists, vm)? {
            return Ok(integer(0, vm));
        }
        let name = os.get_attr("name", vm)?;
        if eq(&name, &text("posix", vm), vm)? {
            return posix_app(&os_path, fp, vm);
        }
        windows_app(fp, vm)
    }

    /// A posix application: on darwin a .app suffix, elsewhere any file that is not a directory.
    fn posix_app(os_path: &PyObjectRef, fp: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        if is_darwin_value(vm)? {
            let is_app = method(fp, "endswith", (text(".app", vm),), vm)?;
            if is_app.try_to_bool(vm)? {
                return Ok(integer(1, vm));
            }
        }
        let is_dir = os_path.get_attr("isdir", vm)?.call((fp.clone(),), vm)?;
        if truthy(&is_dir, vm)? {
            Ok(integer(0, vm))
        } else {
            Ok(integer(1, vm))
        }
    }

    /// A windows application: an .exe suffix.
    fn windows_app(fp: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let is_exe = method(fp, "endswith", (text(".exe", vm),), vm)?;
        if is_exe.try_to_bool(vm)? {
            Ok(integer(1, vm))
        } else {
            Ok(integer(0, vm))
        }
    }

    #[derive(FromArgs)]
    pub(crate) struct IsAppArgs {
        #[pyarg(any)]
        fp: PyObjectRef,
    }

    #[pyfunction(name = "isApp")]
    pub(crate) fn is_app(args: IsAppArgs, vm: &VirtualMachine) -> PyResult {
        is_app_value(&args.fp, vm)
    }

    #[derive(FromArgs)]
    pub(crate) struct AppPathFilterArgs {
        #[pyarg(any)]
        fp: PyObjectRef,
    }

    #[pyfunction(name = "appPathFilter")]
    pub(crate) fn app_path_filter(args: AppPathFilterArgs, vm: &VirtualMachine) -> PyResult {
        let fp = args.fp;
        let os = own_module(vm)?.get_attr("os", vm)?;
        let os_path = os.get_attr("path", vm)?;
        if eq(&fp, &none(vm), vm)? || eq(&fp, &text("", vm), vm)? {
            return Ok(fp);
        }
        let name = os.get_attr("name", vm)?;
        let suffix = if eq(&name, &text("posix", vm), vm)? {
            if is_darwin_value(vm)? {
                ".app"
            } else {
                return Ok(fp);
            }
        } else {
            ".exe"
        };
        let modified = vm._add(&fp, &text(suffix, vm))?;
        let fp_exists = os_path.get_attr("exists", vm)?.call((fp.clone(),), vm)?;
        let modified_exists = os_path
            .get_attr("exists", vm)?
            .call((modified.clone(),), vm)?;
        if !truthy(&fp_exists, vm)? && truthy(&modified_exists, vm)? {
            return Ok(modified);
        }
        Ok(fp)
    }

    #[derive(FromArgs)]
    pub(crate) struct PathScrubArgs {
        #[pyarg(any, name = "usrStr")]
        usr_str: PyObjectRef,
    }

    #[pyfunction(name = "pathScrub")]
    pub(crate) fn path_scrub(args: PathScrubArgs, vm: &VirtualMachine) -> PyResult {
        if !is_str_value(&args.usr_str, vm)? {
            let message = formatted(
                &text("non-string submitted as a path string: %r", vm),
                vec![args.usr_str.clone()],
                vm,
            )?;
            return Err(vm.new_exception(vm.ctx.exceptions.value_error.to_owned(), vec![message]));
        }
        let os = own_module(vm)?.get_attr("os", vm)?;
        let os_path = os.get_attr("path", vm)?;
        let mut usr_str = args.usr_str.clone();
        let name = os.get_attr("name", vm)?;
        if eq(&name, &text("posix", vm), vm)? {
            usr_str = expand_home_path(&os_path, &usr_str, vm)?;
        }
        usr_str = strip_trailing_double_sep(&usr_str, &os, vm)?;
        usr_str = os_path.get_attr("normpath", vm)?.call((usr_str,), vm)?;
        os_path.get_attr("expandvars", vm)?.call((usr_str,), vm)
    }

    /// The posix home expansion: expanduser, then realpath when a separator appears, OSError
    /// passing without changes.
    fn expand_home_path(
        os_path: &PyObjectRef,
        usr_str: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let expanded = os_path
            .get_attr("expanduser", vm)?
            .call((usr_str.clone(),), vm)?;
        let sep = module("athenaCL.libATH.drawer", vm)?
            .get_attr("os", vm)?
            .get_attr("sep", vm)?;
        let found = method(&expanded, "find", (sep,), vm)?;
        if !ge(&found, &integer(0, vm), vm)? {
            return Ok(expanded);
        }
        match os_path
            .get_attr("realpath", vm)?
            .call((expanded.clone(),), vm)
        {
            Ok(real) => Ok(real),
            Err(error) => {
                if error.class().fast_issubclass(vm.ctx.exceptions.os_error) {
                    Ok(expanded)
                } else {
                    Err(error)
                }
            }
        }
    }

    /// A trailing double separator is removed, as the macos 9 leftovers required.
    fn strip_trailing_double_sep(
        usr_str: &PyObjectRef,
        os: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let sep = os.get_attr("sep", vm)?;
        let double = vm._add(&sep, &sep)?;
        let double_length = integer(length(&double, vm)? as i64, vm);
        let tail = slice_of(usr_str, vm._neg(&double_length)?, none(vm), vm)?;
        if eq(&tail, &double, vm)? {
            return slice_of(usr_str, none(vm), vm._neg(&double_length)?, vm);
        }
        Ok(usr_str.clone())
    }

    #[derive(FromArgs)]
    pub(crate) struct PathExistsArgs {
        #[pyarg(any, name = "usrData")]
        usr_data: PyObjectRef,
    }

    #[pyfunction(name = "pathExists")]
    pub(crate) fn path_exists(args: PathExistsArgs, vm: &VirtualMachine) -> PyResult {
        let os_path = own_module(vm)?.get_attr("os", vm)?.get_attr("path", vm)?;
        let path_list = if !is_list_value(&args.usr_data, vm)? {
            list_of(vec![args.usr_data.clone()], vm)
        } else {
            args.usr_data.clone()
        };
        for path in path_list
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let exists = os_path.get_attr("exists", vm)?.call((path?,), vm)?;
            if truthy(&exists, vm)? {
                return Ok(integer(1, vm));
            }
        }
        Ok(integer(0, vm))
    }

    #[pyfunction(name = "getcwd")]
    pub(crate) fn get_cwd(vm: &VirtualMachine) -> PyResult {
        let os = own_module(vm)?.get_attr("os", vm)?;
        match os.get_attr("getcwd", vm)?.call((), vm) {
            Ok(path) => Ok(path),
            Err(error) => {
                if error.class().fast_issubclass(vm.ctx.exceptions.os_error) {
                    Ok(none(vm))
                } else {
                    Err(error)
                }
            }
        }
    }

    #[pyfunction(name = "getud")]
    pub(crate) fn get_ud(vm: &VirtualMachine) -> PyResult {
        let os = own_module(vm)?.get_attr("os", vm)?;
        let os_path = os.get_attr("path", vm)?;
        let name = os.get_attr("name", vm)?;
        if eq(&name, &text("mac", vm), vm)? {
            return Ok(none(vm));
        }
        if eq(&name, &text("posix", vm), vm)? {
            return os_path
                .get_attr("expanduser", vm)?
                .call((text("~", vm),), vm);
        }
        let environ = os.get_attr("environ", vm)?;
        let mut dir = none(vm);
        if let Some(profile) = environ_value(&environ, "USERPROFILE", vm)? {
            let is_dir = os_path
                .get_attr("isdir", vm)?
                .call((profile.clone(),), vm)?;
            if truthy(&is_dir, vm)? {
                dir = profile;
            }
        }
        if eq(&dir, &none(vm), vm)? {
            let home = os_path
                .get_attr("expanduser", vm)?
                .call((text("~", vm),), vm)?;
            let is_dir = os_path.get_attr("isdir", vm)?.call((home.clone(),), vm)?;
            if !truthy(&is_dir, vm)? {
                return Ok(none(vm));
            }
            return Ok(home);
        }
        Ok(dir)
    }

    #[pyfunction(name = "getPrefsName")]
    pub(crate) fn get_prefs_name(vm: &VirtualMachine) -> PyResult {
        let os = own_module(vm)?.get_attr("os", vm)?;
        let name = os.get_attr("name", vm)?;
        if eq(&name, &text("posix", vm), vm)? {
            Ok(text(".athenaclrc", vm))
        } else {
            Ok(text(".athenaclrc.xml", vm))
        }
    }

    fn get_prefs_dir_value(vm: &VirtualMachine) -> PyResult {
        let os = own_module(vm)?.get_attr("os", vm)?;
        let environ = os.get_attr("environ", vm)?;
        let override_name = text("ATHENACL_PREFS_DIR", vm);
        if contains(&environ, &override_name, vm)? {
            return environ.get_item(override_name.as_object(), vm);
        }
        let name = os.get_attr("name", vm)?;
        if eq(&name, &text("posix", vm), vm)? {
            return environ.get_item(text("HOME", vm).as_object(), vm);
        }
        windows_prefs_dir(&os, &environ, vm)
    }

    /// The windows preference directory: APPDATA, else a profile's Application Data, else the
    /// expanded home.
    fn windows_prefs_dir(os: &PyObjectRef, environ: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let os_path = os.get_attr("path", vm)?;
        if let Some(app_data) = environ_value(environ, "APPDATA", vm)? {
            return Ok(app_data);
        }
        if let Some(profile) = environ_value(environ, "USERPROFILE", vm)? {
            let joined = os_path
                .get_attr("join", vm)?
                .call((profile, text("Application Data", vm)), vm)?;
            let exists = os_path
                .get_attr("exists", vm)?
                .call((joined.clone(),), vm)?;
            if truthy(&exists, vm)? {
                return Ok(joined);
            }
        }
        os_path
            .get_attr("expanduser", vm)?
            .call((text("~", vm),), vm)
    }

    /// An environment value, when its key is present.
    fn environ_value(
        environ: &PyObjectRef,
        key: &'static str,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        if contains(environ, &text(key, vm), vm)? {
            return Ok(Some(environ.get_item(text(key, vm).as_object(), vm)?));
        }
        Ok(None)
    }

    #[pyfunction(name = "getPrefsDir")]
    pub(crate) fn get_prefs_dir(vm: &VirtualMachine) -> PyResult {
        get_prefs_dir_value(vm)
    }

    #[pyfunction(name = "getPrefsPath")]
    pub(crate) fn get_prefs_path(vm: &VirtualMachine) -> PyResult {
        let dir = get_prefs_dir_value(vm)?;
        let name = get_prefs_name(vm)?;
        let os_path = own_module(vm)?.get_attr("os", vm)?.get_attr("path", vm)?;
        let exists = os_path.get_attr("exists", vm)?.call((dir.clone(),), vm)?;
        if !truthy(&exists, vm)? {
            let message = formatted(
                &text("cannot write preference file to %s", vm),
                vec![dir],
                vm,
            )?;
            let class: PyObjectRef = vm.ctx.exceptions.exception_type.to_owned().into();
            let error = class
                .call((message,), vm)?
                .downcast::<rustpython_vm::builtins::PyBaseException>()
                .map_err(|_not_exception| {
                    vm.new_type_error("an exception type is expected".to_owned())
                })?;
            return Err(error);
        }
        os_path.get_attr("join", vm)?.call((dir, name), vm)
    }
}
