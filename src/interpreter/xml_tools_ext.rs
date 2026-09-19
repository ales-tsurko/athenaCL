//! Rust extensions to the athenaCL.libATH.xmlTools

use quick_xml::{events::Event, reader::Reader};
use rustpython_vm::{pymodule, VirtualMachine};

pub(crate) fn make_module(vm: &mut VirtualMachine) {
    vm.add_native_module("xmlToolsExt", Box::new(_inner::make_module));
}

#[pymodule]
pub(super) mod _inner {
    use std::str;

    use ahash::AHashMap;
    use rustpython_vm::{convert::ToPyObject, PyResult};

    use super::*;

    #[pyfunction(name = "xmlToPy")]
    pub(crate) fn xml_to_py(code: String, vm: &VirtualMachine) -> PyResult {
        let mut reader = Reader::from_str(&code);
        reader.trim_text(true);
        let mut buf = Vec::new();
        let mut stack = Vec::new();
        let root = vm.ctx.new_dict();
        let mut attrs_cache = AHashMap::<String, String>::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Err(e) => {
                    let err_msg =
                        format!("Error parsing XML at {}: {:?}", reader.buffer_position(), e);
                    let value_err = vm.new_value_error(err_msg);
                    return Err(value_err);
                }

                Ok(Event::Start(e)) => {
                    let name = match e
                        .attributes()
                        .find(|a| matches!(a.as_ref(), Ok(attr) if attr.key.as_ref() == b"name"))
                    {
                        Some(Ok(attr)) => reader
                            .decoder()
                            .decode(attr.value.as_ref())
                            .map_err(|_err| {
                                vm.new_value_error("cannot decode xml attribute".to_owned())
                            })?
                            .to_string(),
                        _ => reader
                            .decoder()
                            .decode(e.name().as_ref())
                            .map_err(|_err| {
                                vm.new_value_error("cannot decode xml element name".to_owned())
                            })?
                            .to_string(),
                    };

                    let dict = vm.ctx.new_dict();
                    stack.push((name, dict));
                }

                Ok(Event::Empty(e)) => {
                    if let Some((_, dict)) = stack.last() {
                        for a in e.attributes() {
                            let attr = a.map_err(|_err| {
                                vm.new_value_error("cannot get xml attribute".to_owned())
                            })?;
                            let key =
                                reader.decoder().decode(attr.key.as_ref()).map_err(|_err| {
                                    vm.new_value_error("cannot decode xml attribute".to_owned())
                                })?;
                            let value =
                                reader
                                    .decoder()
                                    .decode(attr.value.as_ref())
                                    .map_err(|_err| {
                                        vm.new_value_error("cannot decode xml attribute".to_owned())
                                    })?;

                            attrs_cache.insert(key.to_string(), value.to_string());
                        }

                        let value = vm
                            .ctx
                            .new_str(attrs_cache.remove("value").unwrap_or_default().as_str());

                        dict.set_item(
                            &attrs_cache.remove("key").unwrap_or_default(),
                            value.to_pyobject(vm),
                            vm,
                        )?;
                    }
                }

                Ok(Event::End(_)) => {
                    if let Some((name, dict)) = stack.pop() {
                        let parent = stack.last().map(|(_, p)| p).unwrap_or(&root);
                        parent.set_item(&name, dict.to_pyobject(vm), vm)?;
                    }
                }

                Ok(Event::Eof) => break,

                _ => {}
            }

            buf.clear();
        }

        Ok(root.into())
    }

    #[pyfunction(name = "checkFileFormat")]
    pub(crate) fn check_file_format(content: String, vm: &VirtualMachine) -> PyResult {
        let mut reader = Reader::from_str(&content);
        reader.trim_text(true);
        let mut buf = Vec::new();

        let (mut kind, mut message) = ("xml".to_string(), "ok".to_string());

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    if e.name().as_ref() == b"athenaObject" {
                        break;
                    }
                }

                Ok(Event::Eof) => {
                    kind = "unknown".to_string();
                    message = "error reading the file".to_string();
                    break;
                }

                Err(e) => {
                    kind = "unknown".to_string();
                    message = format!("Error parsing XML at {}: {:?}", reader.buffer_position(), e);
                }

                _ => {}
            }

            buf.clear();
        }

        Ok(vm
            .ctx
            .new_tuple(
                [kind, message]
                    .into_iter()
                    .map(|v| vm.ctx.new_str(v).to_pyobject(vm))
                    .collect(),
            )
            .into())
    }
}
