use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "athenaCL.libATH.unit")]
mod _inner {
    #![expect(
        clippy::unwrap_used,
        reason = "the pymodule macro's generated attribute setters unwrap"
    )]
    use rustpython_vm::{
        builtins::{PyBaseExceptionRef, PyModule, PyType},
        function::{FuncArgs, OptionalArg},
        pyclass,
        types::{Constructor, Initializer, PyComparisonOp},
        AsObject, FromArgs, Py, PyObject, PyObjectRef, PyPayload, PyRef, PyResult, VirtualMachine,
    };

    use crate::libath::number::Number;

    fn plain_number(obj: &PyObjectRef, vm: &VirtualMachine) -> Option<Number> {
        if is_builtin_number(obj, vm) {
            Number::from_object(obj, vm).ok()
        } else {
            None
        }
    }
    fn is_builtin_number(obj: &PyObjectRef, vm: &VirtualMachine) -> bool {
        obj.class().is(vm.ctx.types.int_type) || obj.class().is(vm.ctx.types.float_type)
    }

    fn int(n: i64, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_int(n).into()
    }
    fn float(n: f64, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_float(n).into()
    }
    fn list(values: Vec<PyObjectRef>, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_list(values).into()
    }
    fn tuple(values: Vec<PyObjectRef>, vm: &VirtualMachine) -> PyObjectRef {
        vm.ctx.new_tuple(values).into()
    }
    fn eq(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, PyComparisonOp::Eq, vm)
    }
    fn ne(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, PyComparisonOp::Ne, vm)
    }
    fn lt(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, PyComparisonOp::Lt, vm)
    }
    fn le(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, PyComparisonOp::Le, vm)
    }
    fn gt(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, PyComparisonOp::Gt, vm)
    }
    fn ge(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        a.rich_compare_bool(b, PyComparisonOp::Ge, vm)
    }
    fn values(obj: &PyObjectRef, vm: &VirtualMachine) -> PyResult<Vec<PyObjectRef>> {
        let mut values = Vec::new();
        for value in obj.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let value = value?;
            vm.check_signals()?;
            values.push(value);
        }
        Ok(values)
    }
    fn item(obj: &PyObjectRef, index: i64, vm: &VirtualMachine) -> PyResult {
        obj.get_item(int(index, vm).as_object(), vm)
    }
    fn call(
        obj: &PyObjectRef,
        name: &'static str,
        args: impl rustpython_vm::function::IntoFuncArgs,
        vm: &VirtualMachine,
    ) -> PyResult {
        obj.get_attr(name, vm)?.call(args, vm)
    }
    fn builtin(name: &'static str, vm: &VirtualMachine) -> PyResult {
        vm.import("builtins", 0)?.get_attr(name, vm)
    }
    fn as_float(obj: PyObjectRef, vm: &VirtualMachine) -> PyResult {
        builtin("float", vm)?.call((obj,), vm)
    }
    fn is_int(obj: &PyObjectRef, vm: &VirtualMachine) -> PyResult<bool> {
        obj.is_instance(vm.ctx.types.int_type.as_object(), vm)
    }
    fn sorted_copy(obj: &PyObjectRef, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let copy = list(values(obj, vm)?, vm);
        call(&copy, "sort", (), vm)?;
        Ok(copy)
    }
    fn min_max(obj: &PyObjectRef, vm: &VirtualMachine) -> PyResult<(PyObjectRef, PyObjectRef)> {
        match obj.length(vm)? {
            0 => Err(vm.new_value_error("series with no values given".to_owned())),
            1 => Ok((item(obj, 0, vm)?, item(obj, 0, vm)?)),
            _ => {
                let copy = sorted_copy(obj, vm)?;
                Ok((item(&copy, 0, vm)?, item(&copy, -1, vm)?))
            }
        }
    }
    fn table_min_max(
        obj: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
        let mut all = Vec::new();
        for row in obj.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let row = row?;
            vm.check_signals()?;
            let (a, b) = min_max(&row, vm)?;
            all.push(a);
            all.push(b);
        }
        let copy = sorted_copy(&list(all, vm), vm)?;
        Ok((item(&copy, 0, vm)?, item(&copy, -1, vm)?))
    }
    fn range_bounds(
        fixed: Option<PyObjectRef>,
        source: &PyObjectRef,
        table: bool,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
        if let Some(fixed) = fixed {
            if ne(&fixed, &vm.ctx.none(), vm)? {
                call(&fixed, "sort", (), vm)?;
                return Ok((item(&fixed, 0, vm)?, item(&fixed, -1, vm)?));
            }
        }
        if table {
            table_min_max(source, vm)
        } else {
            min_max(source, vm)
        }
    }
    fn normalized(
        value: &PyObjectRef,
        low: &PyObjectRef,
        span: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        if let (Some(value), Some(low), Some(span)) = (
            plain_number(value, vm),
            plain_number(low, vm),
            plain_number(span, vm),
        ) {
            if let Some(result) = crate::libath::unit::core::normalize(value, low, span) {
                return Ok(result.as_object(vm));
            }
        }
        let mut difference = vm._sub(value, low)?;
        if is_int(&difference, vm)? {
            difference = as_float(difference, vm)?;
        }
        if ne(span, &int(0, vm), vm)? {
            vm._truediv(&difference, span)
        } else {
            Ok(int(0, vm))
        }
    }
    fn module(vm: &VirtualMachine) -> PyResult {
        let root = vm.import("athenaCL.libATH.unit", 0)?;
        root.get_attr("libATH", vm)?.get_attr("unit", vm)
    }
    fn unit_error(message: String, funnel: bool, vm: &VirtualMachine) -> PyBaseExceptionRef {
        let raised = module(vm)
            .and_then(|m| {
                m.get_attr(
                    if funnel {
                        "FunnelUnitException"
                    } else {
                        "UnitException"
                    },
                    vm,
                )
            })
            .and_then(|ty| ty.call((message.clone(),), vm));
        match raised.and_then(|obj| rustpython_vm::convert::TryFromObject::try_from_object(vm, obj))
        {
            Ok(err) => err,
            Err(_) => vm.new_exception(
                vm.ctx.exceptions.exception_type.to_owned(),
                vec![vm.ctx.new_str(message).into()],
            ),
        }
    }
    fn validate_unit(value: &PyObjectRef, funnel: bool, vm: &VirtualMachine) -> PyResult<()> {
        if lt(value, &int(0, vm), vm)? || gt(value, &int(1, vm), vm)? {
            let value = value.str(vm)?.to_string();
            return Err(unit_error(
                format!("value ({value}) must be in unit interval"),
                funnel,
                vm,
            ));
        }
        Ok(())
    }
    fn triple(a: PyObjectRef, b: PyObjectRef, c: PyObjectRef, vm: &VirtualMachine) -> PyObjectRef {
        tuple(vec![a, b, c], vm)
    }
    fn mean(a: &PyObjectRef, b: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        if let (Some(a), Some(b)) = (plain_number(a, vm), plain_number(b, vm)) {
            if let Some(result) = crate::libath::unit::core::mean(a, b) {
                return Ok(result.as_object(vm));
            }
        }
        let sum = vm._add(a, b)?;
        vm._mul(&sum, &float(0.5, vm))
    }
    fn fixed(opt: OptionalArg<PyObjectRef>) -> Option<PyObjectRef> {
        opt.as_ref().cloned().into()
    }

    #[pyattr(name = "UnitException")]
    fn unit_exception(vm: &VirtualMachine) -> rustpython_vm::builtins::PyTypeRef {
        vm.ctx.new_exception_type(
            "athenaCL.libATH.unit",
            "UnitException",
            Some(vec![vm.ctx.exceptions.exception_type.to_owned()]),
        )
    }
    #[pyattr(name = "FunnelUnitException")]
    fn funnel_unit_exception(vm: &VirtualMachine) -> rustpython_vm::builtins::PyTypeRef {
        vm.ctx.new_exception_type(
            "athenaCL.libATH.unit",
            "FunnelUnitException",
            Some(vec![vm.ctx.exceptions.exception_type.to_owned()]),
        )
    }
    pub(crate) fn module_exec(vm: &VirtualMachine, module: &Py<PyModule>) -> PyResult<()> {
        __module_exec(vm, module);
        module.set_attr("_MOD", vm.ctx.new_str("unit.py"), vm)?;
        for name in ["copy", "unittest", "doctest"] {
            module.set_attr(name, vm.import(name, 0)?, vm)?;
        }
        let athena = vm.import("athenaCL.libATH.drawer", 0)?;
        module.set_attr(
            "drawer",
            athena.get_attr("libATH", vm)?.get_attr("drawer", vm)?,
            vm,
        )?;
        let funnel: PyRef<PyType> = module
            .get_attr("FunnelUnit", vm)?
            .downcast()
            .map_err(|_absent| vm.new_type_error("FunnelUnit class is unavailable"))?;
        for name in [
            "_seriesPosToBinaryPos",
            "_binaryPosToSeriesPos",
            "_findAdjacent",
            "findReject",
            "findNearest",
        ] {
            crate::libath::method_binding::bind_method(&funnel, name, vm)?;
        }
        Ok(())
    }

    #[derive(FromArgs)]
    pub(crate) struct SeriesArgs {
        #[pyarg(any)]
        series: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct TableArgs {
        #[pyarg(any)]
        table: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct ValueRangeArgs {
        #[pyarg(any)]
        value: PyObjectRef,
        #[pyarg(any, name = "valueRange")]
        value_range: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct SeriesRangeArgs {
        #[pyarg(any)]
        series: PyObjectRef,
        #[pyarg(any, optional, name = "fixRange")]
        fix_range: OptionalArg<PyObjectRef>,
    }
    #[derive(FromArgs)]
    pub(crate) struct TableRangeArgs {
        #[pyarg(any)]
        table: PyObjectRef,
        #[pyarg(any, optional, name = "fixRange")]
        fix_range: OptionalArg<PyObjectRef>,
    }
    #[derive(FromArgs)]
    pub(crate) struct PartsArgs {
        #[pyarg(any)]
        parts: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct StepArgs {
        #[pyarg(any)]
        step: PyObjectRef,
        #[pyarg(any, optional)]
        a: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        b: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        normalized: OptionalArg<PyObjectRef>,
    }
    #[derive(FromArgs)]
    pub(crate) struct ValueABArgs {
        #[pyarg(any)]
        value: PyObjectRef,
        #[pyarg(any)]
        a: PyObjectRef,
        #[pyarg(any)]
        b: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct DenormListArgs {
        #[pyarg(any)]
        unit: PyObjectRef,
        #[pyarg(any)]
        a: PyObjectRef,
        #[pyarg(any)]
        b: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct LimitArgs {
        #[pyarg(any)]
        value: PyObjectRef,
        #[pyarg(any, optional)]
        method: OptionalArg<PyObjectRef>,
    }
    #[derive(FromArgs)]
    pub(crate) struct BoundaryPosArgs {
        #[pyarg(any)]
        val: PyObjectRef,
        #[pyarg(any)]
        bounds: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct BoundaryArgs {
        #[pyarg(any)]
        a: PyObjectRef,
        #[pyarg(any)]
        b: PyObjectRef,
        #[pyarg(any)]
        f: PyObjectRef,
        #[pyarg(any, name = "boundaryMethod")]
        boundary_method: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct PosArgs {
        #[pyarg(any)]
        pos: PyObjectRef,
    }
    #[derive(FromArgs)]
    pub(crate) struct ValArgs {
        #[pyarg(any)]
        val: PyObjectRef,
    }

    #[pyfunction(name = "seriesMinMax")]
    fn series_min_max(args: SeriesArgs, vm: &VirtualMachine) -> PyResult {
        let (a, b) = min_max(&args.series, vm)?;
        Ok(tuple(vec![a, b], vm))
    }
    #[pyfunction(name = "tableMinMax")]
    fn table_min_max_py(args: TableArgs, vm: &VirtualMachine) -> PyResult {
        let (a, b) = table_min_max(&args.table, vm)?;
        Ok(tuple(vec![a, b], vm))
    }
    #[pyfunction(name = "unitNorm")]
    fn unit_norm(args: ValueRangeArgs, vm: &VirtualMachine) -> PyResult {
        let (low, high) = min_max(&args.value_range, vm)?;
        normalized(&args.value, &low, &vm._sub(&high, &low)?, vm)
    }
    #[pyfunction(name = "unitNormRange")]
    fn unit_norm_range(args: SeriesRangeArgs, vm: &VirtualMachine) -> PyResult {
        norm_range(&args.series, fixed(args.fix_range), vm)
    }
    fn norm_range(
        series: &PyObjectRef,
        fix_range: Option<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult {
        let (low, high) = range_bounds(fix_range, series, false, vm)?;
        let span = vm._sub(&high, &low)?;
        if series.length(vm)? <= 1 {
            return Ok(list(vec![int(0, vm)], vm));
        }
        let mut out = Vec::new();
        for val in series.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let val = val?;
            vm.check_signals()?;
            out.push(normalized(&val, &low, &span, vm)?);
        }
        Ok(list(out, vm))
    }
    #[pyfunction(name = "unitNormRangeTable")]
    fn unit_norm_range_table(args: TableRangeArgs, vm: &VirtualMachine) -> PyResult {
        let (low, high) = range_bounds(fixed(args.fix_range), &args.table, true, vm)?;
        let span = vm._sub(&high, &low)?;
        let mut out = Vec::new();
        for row in args
            .table
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let row = row?;
            vm.check_signals()?;
            let mut normalized_row = Vec::new();
            for val in row.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
                let val = val?;
                vm.check_signals()?;
                normalized_row.push(normalized(&val, &low, &span, vm)?);
            }
            out.push(list(normalized_row, vm));
        }
        Ok(list(out, vm))
    }
    #[pyfunction(name = "unitNormEqual")]
    fn unit_norm_equal(args: PartsArgs, vm: &VirtualMachine) -> PyResult {
        norm_equal(&args.parts, vm)
    }
    fn norm_equal(parts: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        if le(parts, &int(1, vm), vm)? {
            return Ok(list(vec![int(0, vm)], vm));
        }
        if eq(parts, &int(2, vm), vm)? {
            return Ok(list(vec![int(0, vm), int(1, vm)], vm));
        }
        if let Some(Number::Int(count)) = plain_number(parts, vm) {
            if let Ok(count) = usize::try_from(count) {
                let mut values = Vec::new();
                for index in 0..count {
                    vm.check_signals()?;
                    values.push(crate::libath::unit::core::equal_part(count, index).as_object(vm));
                }
                return Ok(list(values, vm));
            }
        }
        let step_denominator = vm._sub(parts, &int(1, vm))?;
        let step = vm._truediv(&float(1.0, vm), &step_denominator)?;
        let range_fn = builtin("range", vm)?;
        let range_end = vm._sub(parts, &int(1, vm))?;
        let range = range_fn.call((int(0, vm), range_end), vm)?;
        let mut out = Vec::new();
        for y in range.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let y = y?;
            vm.check_signals()?;
            out.push(vm._mul(&y, &step)?);
        }
        out.push(int(1, vm));
        Ok(list(out, vm))
    }
    #[pyfunction(name = "unitNormStep")]
    fn unit_norm_step(args: StepArgs, vm: &VirtualMachine) -> PyResult {
        let a = args.a.as_ref().cloned().unwrap_or_else(|| int(0, vm));
        let b = args.b.as_ref().cloned().unwrap_or_else(|| int(1, vm));
        let normalized = args
            .normalized
            .as_ref()
            .cloned()
            .unwrap_or_else(|| vm.ctx.new_bool(true).into());
        if eq(&a, &b, vm)? {
            return Ok(list(Vec::new(), vm));
        }
        let less = lt(&a, &b, vm)?;
        let greater = gt(&a, &b, vm)?;
        let (low, high) = if greater {
            (b, a)
        } else if less {
            (a, b)
        } else {
            return Err(vm.new_exception(
                vm.ctx.exceptions.unbound_local_error.to_owned(),
                vec![vm
                    .ctx
                    .new_str("local variable 'min' referenced before assignment")
                    .into()],
            ));
        };
        let mut x = low;
        let mut out = Vec::new();
        // The reference loops forever for non-progressing steps. Guard only that pathological case.
        while le(&x, &high, vm)? {
            vm.check_signals()?;
            out.push(x.clone());
            let next = vm._iadd(&x, &args.step)?;
            // Restrict the guard to immutable built-ins so it does not add user-defined callbacks.
            if is_builtin_number(&x, vm) && is_builtin_number(&next, vm) && le(&next, &x, vm)? {
                return Err(vm.new_value_error("step does not advance".to_owned()));
            }
            x = next;
        }
        if normalized.try_to_bool(vm)? {
            norm_equal(&int(i64::try_from(out.len()).unwrap_or(i64::MAX), vm), vm)
        } else {
            Ok(list(out, vm))
        }
    }
    #[pyfunction(name = "unitNormProportion")]
    fn unit_norm_proportion(args: SeriesArgs, vm: &VirtualMachine) -> PyResult {
        norm_proportion(&args.series, vm)
    }
    fn norm_proportion(series: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let mut sum = int(0, vm);
        for x in series.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let x = x?;
            vm.check_signals()?;
            if lt(&x, &int(0, vm), vm)? {
                return Err(vm.new_value_error("series members should be positive".to_owned()));
            }
            sum = vm._add(&sum, &x)?;
        }
        if !ne(&sum, &int(0, vm), vm)? {
            return Err(vm.new_exception(vm.ctx.exceptions.assertion_error.to_owned(), vec![]));
        }
        let mut out = Vec::new();
        for x in series.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let x = x?;
            vm.check_signals()?;
            let denominator = as_float(sum.clone(), vm)?;
            out.push(vm._truediv(&x, &denominator)?);
        }
        Ok(list(out, vm))
    }
    #[pyfunction(name = "unitNormAccumulate")]
    fn unit_norm_accumulate(args: SeriesArgs, vm: &VirtualMachine) -> PyResult {
        let mut total = int(0, vm);
        let mut accum = vec![total.clone()];
        for step in args
            .series
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let step = step?;
            vm.check_signals()?;
            total = vm._add(&total, &step)?;
            accum.push(total.clone());
        }
        let mut out = Vec::new();
        for pos in accum {
            vm.check_signals()?;
            let pos = as_float(pos, vm)?;
            out.push(vm._truediv(&pos, &total)?);
        }
        Ok(list(out, vm))
    }
    fn denorm_bounds(
        a: PyObjectRef,
        b: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<Option<(PyObjectRef, PyObjectRef)>> {
        let less = lt(&a, &b, vm)?;
        let greater = gt(&a, &b, vm)?;
        if greater {
            Ok(Some((b, a)))
        } else if less {
            Ok(Some((a, b)))
        } else {
            Ok(None)
        }
    }
    fn unbound_denorm_bound(vm: &VirtualMachine) -> PyBaseExceptionRef {
        vm.new_exception(
            vm.ctx.exceptions.unbound_local_error.to_owned(),
            vec![vm
                .ctx
                .new_str("local variable 'max' referenced before assignment")
                .into()],
        )
    }
    fn boundary_bounds(
        a: PyObjectRef,
        b: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
        if gt(&a, &b, vm)? {
            Ok((b, a))
        } else if lt(&a, &b, vm)? {
            Ok((a, b))
        } else {
            Ok((a.clone(), a))
        }
    }
    fn denorm_one(
        converted: &PyObjectRef,
        low: &PyObjectRef,
        high: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult {
        let span = vm._sub(high, low)?;
        if let (Some(value), Some(low), Some(span)) = (
            plain_number(converted, vm),
            plain_number(low, vm),
            plain_number(&span, vm),
        ) {
            if let Some(result) = crate::libath::unit::core::denormalize(value, low, span) {
                return Ok(result.as_object(vm));
            }
        }
        let scaled = vm._mul(converted, &span)?;
        vm._add(&scaled, low)
    }
    #[pyfunction(name = "denorm")]
    fn denorm(args: ValueABArgs, vm: &VirtualMachine) -> PyResult {
        validate_unit(&args.value, false, vm)?;
        if eq(&args.a, &args.b, vm)? {
            return Ok(args.a);
        }
        let bounds = denorm_bounds(args.a, args.b, vm)?;
        let converted = as_float(args.value, vm)?;
        let (low, high) = bounds.ok_or_else(|| unbound_denorm_bound(vm))?;
        denorm_one(&converted, &low, &high, vm)
    }
    #[pyfunction(name = "denormList")]
    fn denorm_list(args: DenormListArgs, vm: &VirtualMachine) -> PyResult {
        for value in args
            .unit
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let value = value?;
            vm.check_signals()?;
            validate_unit(&value, false, vm)?;
        }
        if eq(&args.a, &args.b, vm)? {
            return Ok(args.a);
        }
        let less = lt(&args.a, &args.b, vm)?;
        let greater = gt(&args.a, &args.b, vm)?;
        let bounds = if greater {
            Some((args.b, args.a))
        } else if less {
            Some((args.a, args.b))
        } else {
            None
        };
        let mut out = Vec::new();
        for value in args
            .unit
            .get_iter(vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
        {
            let value = value?;
            vm.check_signals()?;
            let converted = as_float(value, vm)?;
            let (low, high) = bounds.as_ref().ok_or_else(|| unbound_denorm_bound(vm))?;
            out.push(denorm_one(&converted, low, high, vm)?);
        }
        Ok(list(out, vm))
    }
    #[pyfunction(name = "interpolate")]
    fn interpolate(args: ValueABArgs, vm: &VirtualMachine) -> PyResult {
        validate_unit(&args.value, false, vm)?;
        if eq(&args.value, &int(0, vm), vm)? {
            return Ok(args.a);
        }
        if eq(&args.value, &int(1, vm), vm)? {
            return Ok(args.b);
        }
        if let (Some(value), Some(a), Some(b)) = (
            plain_number(&args.value, vm),
            plain_number(&args.a, vm),
            plain_number(&args.b, vm),
        ) {
            if let Some(result) = crate::libath::unit::core::interpolate(value, a, b) {
                return Ok(result.as_object(vm));
            }
        }
        let complement = vm._sub(&int(1, vm), &args.value)?;
        let left = vm._mul(&args.a, &complement)?;
        let right = vm._mul(&args.b, &args.value)?;
        vm._add(&left, &right)
    }
    #[pyfunction(name = "limit")]
    fn limit(args: LimitArgs, vm: &VirtualMachine) -> PyResult {
        let _ = args.method;
        if let Some(value) = plain_number(&args.value, vm) {
            return Ok(crate::libath::unit::core::limit(value)
                .map_or(args.value, |value| value.as_object(vm)));
        }
        if gt(&args.value, &int(1, vm), vm)? {
            Ok(int(1, vm))
        } else if lt(&args.value, &int(0, vm), vm)? {
            Ok(int(0, vm))
        } else {
            Ok(args.value)
        }
    }
    #[pyfunction(name = "unitBoundaryEqual")]
    fn unit_boundary_equal(args: PartsArgs, vm: &VirtualMachine) -> PyResult {
        boundary_equal(&args.parts, vm)
    }
    fn boundary_equal(parts: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        if le(parts, &int(0, vm), vm)? {
            return Err(unit_error("cannot process 0 parts".to_owned(), false, vm));
        }
        if let Some(Number::Int(count)) = plain_number(parts, vm) {
            if let Ok(count) = usize::try_from(count) {
                return numeric_equal_bounds(count, vm);
            }
        }
        dynamic_equal_bounds(parts, vm)
    }
    fn numeric_equal_bounds(parts: usize, vm: &VirtualMachine) -> PyResult {
        let mut bounds = Vec::new();
        let mut low = Number::Int(0);
        for face in 0..parts {
            vm.check_signals()?;
            let (next_low, middle, high) = crate::libath::unit::core::equal_bound(parts, face, low);
            bounds.push(triple(
                next_low.as_object(vm),
                middle.as_object(vm),
                high.as_object(vm),
                vm,
            ));
            low = high;
        }
        Ok(list(bounds, vm))
    }
    fn dynamic_equal_bounds(parts: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let step = vm._truediv(&float(1.0, vm), parts)?;
        let range = builtin("range", vm)?.call((int(0, vm), parts.clone()), vm)?;
        let mut low = int(0, vm);
        let mut out = Vec::new();
        for face in range.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let face = face?;
            vm.check_signals()?;
            let (middle, high) = dynamic_equal_face(&face, parts, &step, &low, vm)?;
            out.push(triple(low, middle, high.clone(), vm));
            low = high;
        }
        Ok(list(out, vm))
    }
    fn dynamic_equal_face(
        face: &PyObjectRef,
        parts: &PyObjectRef,
        step: &PyObjectRef,
        low: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
        let high = if ne(face, &vm._sub(parts, &int(1, vm))?, vm)? {
            let next = vm._add(face, &int(1, vm))?;
            vm._mul(step, &next)?
        } else {
            float(1.0, vm)
        };
        let half = vm._mul(step, &float(0.5, vm))?;
        Ok((vm._add(low, &half)?, high))
    }
    #[pyfunction(name = "unitBoundaryFree")]
    fn unit_boundary_free(args: SeriesArgs, vm: &VirtualMachine) -> PyResult {
        let unit = norm_range(&args.series, None, vm)?;
        let points = values(&unit, vm)?;
        let mut out = Vec::new();
        for pair in points.windows(2) {
            vm.check_signals()?;
            let [low, high] = pair else { continue };
            let low = low.clone();
            let high = high.clone();
            out.push(triple(low.clone(), mean(&low, &high, vm)?, high, vm));
        }
        Ok(list(out, vm))
    }
    #[pyfunction(name = "unitBoundaryProportion")]
    fn unit_boundary_proportion(args: SeriesArgs, vm: &VirtualMachine) -> PyResult {
        let zero = int(0, vm);
        if vm._contains(&args.series, &zero)? {
            return Err(unit_error(
                "cannot process series that contains zero".to_owned(),
                false,
                vm,
            ));
        }
        let unit = values(&norm_proportion(&args.series, vm)?, vm)?;
        let mut sum = zero;
        let mut out = Vec::new();
        for (i, value) in unit.iter().enumerate() {
            vm.check_signals()?;
            let low = sum.clone();
            let high = if i + 1 == unit.len() {
                float(1.0, vm)
            } else {
                vm._add(&sum, value)?
            };
            if i + 1 != unit.len() {
                sum = vm._add(&sum, value)?;
            }
            out.push(triple(low.clone(), mean(&low, &high, vm)?, high, vm));
        }
        Ok(list(out, vm))
    }
    #[pyfunction(name = "unitBoundaryPos")]
    fn unit_boundary_pos(args: BoundaryPosArgs, vm: &VirtualMachine) -> PyResult {
        boundary_pos(&args.val, &args.bounds, vm)
    }
    fn boundary_pos(value: &PyObjectRef, bounds: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        validate_unit(value, false, vm)?;
        let first = item(bounds, 0, vm)?;
        if ne(&item(&first, 0, vm)?, &int(0, vm), vm)?
            || ne(&item(&item(bounds, -1, vm)?, 2, vm)?, &int(1, vm), vm)?
        {
            return Err(unit_error("incomplete bounds".to_owned(), false, vm));
        }
        if eq(value, &int(1, vm), vm)? {
            return Ok(int(
                i64::try_from(bounds.length(vm)?).unwrap_or(i64::MAX) - 1,
                vm,
            ));
        }
        for i in 0..bounds.length(vm)? {
            vm.check_signals()?;
            let entry = item(bounds, i64::try_from(i).unwrap_or(i64::MAX), vm)?;
            let (a, b) = unpack_boundary(&entry, vm)?;
            let inside = if let (Some(value), Some(a), Some(b)) = (
                plain_number(value, vm),
                plain_number(&a, vm),
                plain_number(&b, vm),
            ) {
                value.at_least(a) && value.below(b)
            } else {
                ge(value, &a, vm)? && lt(value, &b, vm)?
            };
            if inside {
                return Ok(int(i64::try_from(i).unwrap_or(i64::MAX), vm));
            }
        }
        Ok(vm.ctx.none())
    }
    fn unpack_boundary(
        entry: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
        // Python's three-target unpack reads one extra item, not the entire iterator.
        let parts: Vec<_> = unpack_iterator(entry, vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
            .take(4)
            .collect::<PyResult<_>>()?;
        if let [a, _, b] = parts.as_slice() {
            return Ok((a.clone(), b.clone()));
        }
        let message = if parts.len() < 3 {
            format!(
                "not enough values to unpack (expected 3, got {})",
                parts.len()
            )
        } else if entry.class().is(vm.ctx.types.list_type)
            || entry.class().is(vm.ctx.types.tuple_type)
            || entry.class().is(vm.ctx.types.dict_type)
        {
            format!(
                "too many values to unpack (expected 3, got {})",
                entry.length(vm)?
            )
        } else {
            "too many values to unpack (expected 3)".to_owned()
        };
        Err(vm.new_value_error(message))
    }
    fn unpack_iterator(
        entry: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<rustpython_vm::protocol::PyIter> {
        let not_iterable = entry.class().slots.iter.load().is_none()
            && entry
                .get_class_attr(vm.ctx.intern_str("__getitem__"))
                .is_none();
        entry.get_iter(vm).map_err(|error| {
            if not_iterable && error.class().is(vm.ctx.exceptions.type_error) {
                vm.new_type_error(format!(
                    "cannot unpack non-iterable {} object",
                    entry.class().name()
                ))
            } else {
                error
            }
        })
    }
    fn unpack_adjacent(
        entry: &PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<(PyObjectRef, PyObjectRef)> {
        let parts: Vec<_> = unpack_iterator(entry, vm)?
            .iter_without_hint::<PyObjectRef>(vm)?
            .take(3)
            .collect::<PyResult<_>>()?;
        match parts.as_slice() {
            [lower, upper] => Ok((lower.clone(), upper.clone())),
            [.., _, _, _] => {
                let class = entry.class();
                let message = if class.is(vm.ctx.types.list_type)
                    || class.is(vm.ctx.types.tuple_type)
                    || class.is(vm.ctx.types.dict_type)
                {
                    format!(
                        "too many values to unpack (expected 2, got {})",
                        entry.length(vm)?
                    )
                } else {
                    "too many values to unpack (expected 2)".to_owned()
                };
                Err(vm.new_value_error(message))
            }
            _ => Err(vm.new_value_error(format!(
                "not enough values to unpack (expected 2, got {})",
                parts.len()
            ))),
        }
    }
    #[pyfunction(name = "discreteBinaryPad")]
    fn discrete_binary_pad(args: SeriesRangeArgs, vm: &VirtualMachine) -> PyResult {
        binary_pad(&args.series, fixed(args.fix_range), vm)
    }
    fn binary_pad(
        series: &PyObjectRef,
        fixed: Option<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult {
        for value in series.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let value = value?;
            vm.check_signals()?;
            if !is_int(&value, vm)? {
                return Err(unit_error("non integer value found".to_owned(), false, vm));
            }
        }
        let sorted = binary_range(series, fixed, vm)?;
        let low = item(&sorted, 0, vm)?;
        let high = item(&sorted, -1, vm)?;
        let end = vm._add(&high, &int(1, vm))?;
        let range = builtin("range", vm)?.call((low, end), vm)?;
        let mut out = Vec::new();
        for x in range.get_iter(vm)?.iter_without_hint::<PyObjectRef>(vm)? {
            let x = x?;
            vm.check_signals()?;
            out.push(int(i64::from(vm._contains(series, &x)?), vm));
        }
        Ok(list(out, vm))
    }
    fn binary_range(
        series: &PyObjectRef,
        fixed: Option<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult {
        if let Some(fixed) = fixed {
            if ne(&fixed, &vm.ctx.none(), vm)? {
                call(&fixed, "sort", (), vm)?;
                return Ok(fixed);
            }
        }
        let copy = vm
            .import("copy", 0)?
            .get_attr("deepcopy", vm)?
            .call((series.clone(),), vm)?;
        sorted_copy(&copy, vm)
    }
    #[pyfunction(name = "discreteCompress")]
    fn discrete_compress(args: SeriesArgs, vm: &VirtualMachine) -> PyResult {
        let mut last = vm.ctx.none();
        let mut count = 0;
        let mut out = Vec::new();
        let length = args.series.length(vm)?;
        for i in 0..length {
            vm.check_signals()?;
            let x = item(&args.series, i64::try_from(i).unwrap_or(i64::MAX), vm)?;
            if eq(&x, &last, vm)? || eq(&last, &vm.ctx.none(), vm)? {
                count += 1;
            } else if ne(&x, &last, vm)? {
                out.push(tuple(vec![last, int(count, vm)], vm));
                count = 1;
            }
            if i + 1 == args.series.length(vm)? {
                out.push(tuple(vec![x.clone(), int(count, vm)], vm));
            }
            last = x;
        }
        Ok(list(out, vm))
    }
    #[pyfunction(name = "boundaryFit")]
    fn boundary_fit(args: BoundaryArgs, vm: &VirtualMachine) -> PyResult {
        boundary(args, false, vm)
    }
    #[pyfunction(name = "boundaryReject")]
    fn boundary_reject(args: BoundaryArgs, vm: &VirtualMachine) -> PyResult {
        boundary(args, true, vm)
    }
    struct BoundaryState {
        low: PyObjectRef,
        high: PyObjectRef,
        period: PyObjectRef,
        center: PyObjectRef,
    }

    impl BoundaryState {
        fn new(a: PyObjectRef, b: PyObjectRef, vm: &VirtualMachine) -> PyResult<Self> {
            let (low, high) = boundary_bounds(a, b, vm)?;
            let period = builtin("abs", vm)?.call((vm._sub(&high, &low)?,), vm)?;
            let half = vm._mul(&period, &float(0.5, vm))?;
            let center = vm._add(&low, &half)?;
            Ok(Self {
                low,
                high,
                period,
                center,
            })
        }
    }

    enum BoundarySide {
        Upper,
        Lower,
        Neither,
    }

    fn boundary_side(
        f: &PyObjectRef,
        bounds: &BoundaryState,
        reject: bool,
        vm: &VirtualMachine,
    ) -> PyResult<BoundarySide> {
        if reject {
            if lt(f, &bounds.high, vm)? && ge(f, &bounds.center, vm)? {
                return Ok(BoundarySide::Upper);
            }
            if gt(f, &bounds.low, vm)? && lt(f, &bounds.center, vm)? {
                return Ok(BoundarySide::Lower);
            }
        } else {
            if gt(f, &bounds.high, vm)? {
                return Ok(BoundarySide::Upper);
            }
            if lt(f, &bounds.low, vm)? {
                return Ok(BoundarySide::Lower);
            }
        }
        Ok(BoundarySide::Neither)
    }

    fn shift_until(
        mut f: PyObjectRef,
        bounds: &BoundaryState,
        upward: bool,
        reject: bool,
        vm: &VirtualMachine,
    ) -> PyResult {
        loop {
            vm.check_signals()?;
            let next = if upward {
                vm._add(&f, &bounds.period)?
            } else {
                vm._sub(&f, &bounds.period)?
            };
            if is_builtin_number(&f, vm) && is_builtin_number(&next, vm) && eq(&next, &f, vm)? {
                return Ok(f);
            }
            f = next;
            let threshold = if upward {
                if reject {
                    &bounds.high
                } else {
                    &bounds.low
                }
            } else if reject {
                &bounds.low
            } else {
                &bounds.high
            };
            if if upward {
                ge(&f, threshold, vm)?
            } else {
                le(&f, threshold, vm)?
            } {
                return Ok(f);
            }
        }
    }

    fn reflect_step(
        f: &PyObjectRef,
        bounds: &BoundaryState,
        reject: bool,
        vm: &VirtualMachine,
    ) -> PyResult<Option<PyObjectRef>> {
        let (pivot, upward) = match boundary_side(f, bounds, reject, vm)? {
            BoundarySide::Upper => (&bounds.high, reject),
            BoundarySide::Lower => (&bounds.low, !reject),
            BoundarySide::Neither => return Ok(None),
        };
        let delta = builtin("abs", vm)?.call((vm._sub(f, pivot)?,), vm)?;
        if upward {
            vm._add(pivot, &delta).map(Some)
        } else {
            vm._sub(pivot, &delta).map(Some)
        }
    }

    fn boundary_reflect(
        mut f: PyObjectRef,
        bounds: BoundaryState,
        reject: bool,
        vm: &VirtualMachine,
    ) -> PyResult {
        loop {
            vm.check_signals()?;
            let active = if reject {
                lt(&f, &bounds.high, vm)? && gt(&f, &bounds.low, vm)?
            } else {
                gt(&f, &bounds.high, vm)? || lt(&f, &bounds.low, vm)?
            };
            if !active {
                return Ok(f);
            }
            let Some(next) = reflect_step(&f, &bounds, reject, vm)? else {
                return Ok(f);
            };
            if is_builtin_number(&f, vm) && is_builtin_number(&next, vm) && eq(&next, &f, vm)? {
                return Ok(f);
            }
            f = next;
        }
    }

    fn already_placed(
        f: &PyObjectRef,
        bounds: &BoundaryState,
        reject: bool,
        vm: &VirtualMachine,
    ) -> PyResult<bool> {
        if reject {
            Ok(le(f, &bounds.low, vm)? || ge(f, &bounds.high, vm)?)
        } else {
            Ok(ge(f, &bounds.low, vm)? && le(f, &bounds.high, vm)?)
        }
    }

    fn boundary(args: BoundaryArgs, reject: bool, vm: &VirtualMachine) -> PyResult {
        let BoundaryArgs {
            a,
            b,
            f,
            boundary_method,
        } = args;
        let bounds = BoundaryState::new(a, b, vm)?;
        if already_placed(&f, &bounds, reject, vm)? {
            return Ok(f);
        }
        if eq(&f, &bounds.low, vm)? || eq(&f, &bounds.high, vm)? {
            return Ok(f);
        }
        if eq(&bounds.high, &bounds.low, vm)? {
            return Ok(bounds.center);
        }
        if eq(&boundary_method, &vm.ctx.new_str("limit").into(), vm)? {
            match boundary_side(&f, &bounds, reject, vm)? {
                BoundarySide::Upper => Ok(bounds.high),
                BoundarySide::Lower => Ok(bounds.low),
                BoundarySide::Neither => Ok(vm.ctx.none()),
            }
        } else if eq(&boundary_method, &vm.ctx.new_str("wrap").into(), vm)? {
            match boundary_side(&f, &bounds, reject, vm)? {
                BoundarySide::Upper => shift_until(f, &bounds, reject, reject, vm),
                BoundarySide::Lower => shift_until(f, &bounds, !reject, reject, vm),
                BoundarySide::Neither => Ok(f),
            }
        } else if eq(&boundary_method, &vm.ctx.new_str("reflect").into(), vm)? {
            boundary_reflect(f, bounds, reject, vm)
        } else {
            Ok(vm.ctx.none())
        }
    }

    #[pyattr]
    #[pyclass(name = "FunnelUnit")]
    #[derive(Debug, PyPayload)]
    struct FunnelUnit;
    impl Constructor for FunnelUnit {
        type Args = FuncArgs;

        fn py_new(_cls: &Py<PyType>, _args: FuncArgs, _vm: &VirtualMachine) -> PyResult<Self> {
            Ok(Self)
        }
    }
    impl Initializer for FunnelUnit {
        type Args = SeriesArgs;

        fn init(zelf: PyRef<Self>, args: SeriesArgs, vm: &VirtualMachine) -> PyResult<()> {
            let object = zelf.as_object();
            object.set_attr("srcSeries", args.series.clone(), vm)?;
            let normalized = norm_range(&args.series, None, vm)?;
            object.set_attr("srcSeriesUnit", normalized, vm)?;
            let binary = binary_pad(&args.series, None, vm)?;
            object.set_attr("binaryMap", binary.clone(), vm)?;
            object.set_attr(
                "binaryBound",
                boundary_equal(
                    &int(i64::try_from(binary.length(vm)?).unwrap_or(i64::MAX), vm),
                    vm,
                )?,
                vm,
            )?;
            object.set_attr(
                "discrComp",
                discrete_compress(SeriesArgs { series: binary }, vm)?,
                vm,
            )?;
            Ok(())
        }
    }
    fn index(obj: PyObjectRef, vm: &VirtualMachine) -> PyResult<i64> {
        rustpython_vm::convert::TryFromObject::try_from_object(vm, obj)
    }
    fn marked_position(
        binary: &PyObjectRef,
        matches: impl Fn(i64, i64) -> PyResult<bool>,
        vm: &VirtualMachine,
    ) -> PyResult<Option<(i64, i64)>> {
        let mut count = 0;
        for position in 0..binary.length(vm)? {
            vm.check_signals()?;
            let bit = item(binary, i64::try_from(position).unwrap_or(i64::MAX), vm)?;
            if eq(&bit, &int(1, vm), vm)? {
                let position = i64::try_from(position).unwrap_or(i64::MAX);
                if matches(position, count)? {
                    return Ok(Some((position, count)));
                }
                count += 1;
            }
        }
        Ok(None)
    }
    fn ensure_position(
        pos: &PyObjectRef,
        sequence: &PyObjectRef,
        message: &'static str,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let length = int(i64::try_from(sequence.length(vm)?).unwrap_or(i64::MAX), vm);
        if ge(pos, &length, vm)? {
            Err(unit_error(message.to_owned(), true, vm))
        } else {
            Ok(())
        }
    }
    fn series_pos_to_binary(zelf: &PyObject, pos: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let series = zelf.get_attr("srcSeries", vm)?;
        ensure_position(pos, &series, "series position out of range", vm)?;
        let binary = zelf.get_attr("binaryMap", vm)?;
        Ok(
            marked_position(&binary, |_, count| eq(&int(count, vm), pos, vm), vm)?
                .map_or_else(|| vm.ctx.none(), |(position, _)| int(position, vm)),
        )
    }
    fn binary_pos_to_series(zelf: &PyObject, pos: &PyObjectRef, vm: &VirtualMachine) -> PyResult {
        let binary = zelf.get_attr("binaryMap", vm)?;
        ensure_position(pos, &binary, "binary position out of range", vm)?;
        if ne(&binary.get_item(pos.as_object(), vm)?, &int(1, vm), vm)? {
            return Ok(vm.ctx.none());
        }
        Ok(
            marked_position(&binary, |position, _| eq(&int(position, vm), pos, vm), vm)?
                .map_or_else(|| vm.ctx.none(), |(_, count)| int(count, vm)),
        )
    }
    fn adjacent(zelf: &PyObject, pos: i64, vm: &VirtualMachine) -> PyResult<(i64, i64)> {
        let binary = zelf.get_attr("binaryMap", vm)?;
        let length = binary.length(vm)?;
        let mut upper = None;
        for i in (pos + 1)..i64::try_from(length).unwrap_or(i64::MAX) {
            vm.check_signals()?;
            if eq(&item(&binary, i, vm)?, &int(1, vm), vm)? {
                upper = Some(i);
                break;
            }
        }
        let mut lower = None;
        for i in (0..pos).rev() {
            vm.check_signals()?;
            if eq(&item(&binary, i, vm)?, &int(1, vm), vm)? {
                lower = Some(i);
                break;
            }
        }
        match (lower, upper) {
            (Some(a), Some(b)) => Ok((a, b)),
            _ => Err(unit_error(
                "neighbor positions cannot be found".to_owned(),
                true,
                vm,
            )),
        }
    }
    #[pyclass(flags(BASETYPE, HAS_DICT, HAS_WEAKREF), with(Constructor, Initializer))]
    impl FunnelUnit {
        #[pymethod(name = "_seriesPosToBinaryPos")]
        fn series_pos(zelf: &Py<Self>, args: PosArgs, vm: &VirtualMachine) -> PyResult {
            series_pos_to_binary(zelf.as_object(), &args.pos, vm)
        }

        #[pymethod(name = "_binaryPosToSeriesPos")]
        fn binary_pos(zelf: &Py<Self>, args: PosArgs, vm: &VirtualMachine) -> PyResult {
            binary_pos_to_series(zelf.as_object(), &args.pos, vm)
        }

        #[pymethod(name = "_findAdjacent")]
        fn find_adjacent(zelf: &Py<Self>, args: PosArgs, vm: &VirtualMachine) -> PyResult {
            let (a, b) = adjacent(zelf.as_object(), index(args.pos, vm)?, vm)?;
            Ok(tuple(vec![int(a, vm), int(b, vm)], vm))
        }

        #[pymethod(name = "findReject")]
        fn find_reject(zelf: &Py<Self>, args: ValArgs, vm: &VirtualMachine) -> PyResult {
            validate_unit(&args.val, true, vm)?;
            let object = zelf.as_object();
            let pos = boundary_pos(&args.val, &object.get_attr("binaryBound", vm)?, vm)?;
            let map = object.get_attr("binaryMap", vm)?;
            if eq(&map.get_item(pos.as_object(), vm)?, &int(1, vm), vm)? {
                let series_pos = object
                    .get_attr("_binaryPosToSeriesPos", vm)?
                    .call((pos,), vm)?;
                object
                    .get_attr("srcSeriesUnit", vm)?
                    .get_item(series_pos.as_object(), vm)
            } else {
                Ok(vm.ctx.none())
            }
        }

        #[pymethod(name = "findNearest")]
        fn find_nearest(zelf: &Py<Self>, args: ValArgs, vm: &VirtualMachine) -> PyResult {
            validate_unit(&args.val, true, vm)?;
            let object = zelf.as_object();
            let pos = boundary_pos(&args.val, &object.get_attr("binaryBound", vm)?, vm)?;
            let map = object.get_attr("binaryMap", vm)?;
            if eq(&map.get_item(pos.as_object(), vm)?, &int(1, vm), vm)? {
                let series_pos = object
                    .get_attr("_binaryPosToSeriesPos", vm)?
                    .call((pos,), vm)?;
                return object
                    .get_attr("srcSeriesUnit", vm)?
                    .get_item(series_pos.as_object(), vm);
            }
            let position = index(pos, vm)?;
            let mut start = 0;
            let mut chosen = None;
            let comp = object.get_attr("discrComp", vm)?;
            for j in 0..comp.length(vm)? {
                vm.check_signals()?;
                let pair = item(&comp, i64::try_from(j).unwrap_or(i64::MAX), vm)?;
                let (_, count) = unpack_adjacent(&pair, vm)?;
                let count = index(count, vm)?;
                if position >= start && position < start + count {
                    let neighbor = object
                        .get_attr("_findAdjacent", vm)?
                        .call((int(position, vm),), vm)?;
                    let (lower, upper) = unpack_adjacent(&neighbor, vm)?;
                    chosen = Some(if ((position - start) as f64) < (count as f64) / 2.0 {
                        lower
                    } else {
                        upper
                    });
                    break;
                }
                start += count;
            }
            let Some(chosen) = chosen else {
                return Ok(vm.ctx.none());
            };
            let series_pos = object
                .get_attr("_binaryPosToSeriesPos", vm)?
                .call((chosen,), vm)?;
            object
                .get_attr("srcSeriesUnit", vm)?
                .get_item(series_pos.as_object(), vm)
        }
    }
}
