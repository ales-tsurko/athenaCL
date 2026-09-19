//! The Python `sndhdr` module: recognize sound file headers.
//!
//! The standard library removed it in Python 3.13, but athenaCL's `fileTools` still reads audio
//! file information with it, so it lives here as a native module. WAV and AIFF files are read
//! with symphonia — the decoder the player uses, so the metadata cannot disagree with playback —
//! and the `.snd` header, which symphonia does not know, by hand.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

#[pymodule(name = "sndhdr")]
pub(super) mod _inner {
    use std::{fs::File, io::Read, path::Path};

    use rustpython_vm::{PyObjectRef, PyResult, VirtualMachine};
    use symphonia::core::{io::MediaSourceStream, meta::MetadataOptions, probe::Hint};

    /// `what(filename)`: recognize the sound file's header.
    ///
    /// Returns `(type, sampling_rate, channels, frames, bits_per_sample)`, or `None` when the
    /// file is not recognized. The sampling rate of an AIFF file is a float, as the format
    /// stores it as one.
    #[pyfunction(name = "what")]
    fn what(filename: String, vm: &VirtualMachine) -> PyResult {
        let header = what_file(Path::new(&filename));

        Ok(match header {
            Some(header) => tuple(header, vm),
            None => vm.ctx.none(),
        })
    }

    /// What `what` reports about a sound file.
    #[derive(Debug, PartialEq)]
    struct Header {
        kind: &'static str,
        rate: Option<f64>,
        channels: Option<i64>,
        frames: Option<i64>,
        bits: Option<i64>,
    }

    /// Recognize a sound file: symphonia reads WAV and AIFF files, `.snd` headers by hand.
    fn what_file(path: &Path) -> Option<Header> {
        let data = read_header(path)?;

        match sniff(&data)? {
            Kind::Wav | Kind::Aiff => probe(path),
            Kind::Au => au(&data),
        }
    }

    /// The kind of a sound file, by its header magic.
    #[derive(Debug, Clone, Copy, PartialEq)]
    enum Kind {
        Wav,
        Aiff,
        Au,
    }

    /// Which kind of sound file the header magic names.
    fn sniff(data: &[u8]) -> Option<Kind> {
        if is(data, 0, b"RIFF") && is(data, 8, b"WAVE") {
            return Some(Kind::Wav);
        }
        if is(data, 0, b"FORM") && (is(data, 8, b"AIFF") || is(data, 8, b"AIFC")) {
            return Some(Kind::Aiff);
        }
        if is(data, 0, b".snd") {
            return Some(Kind::Au);
        }

        None
    }

    /// Read a WAV or AIFF file's format with symphonia.
    fn probe(path: &Path) -> Option<Header> {
        let kind = sniff(&read_header(path)?).map(Kind::name)?;
        let source = MediaSourceStream::new(
            Box::new(File::open(path).ok()?) as Box<_>,
            Default::default(),
        );
        let mut hint = Hint::new();
        hint.with_extension(kind);
        let probed = symphonia::default::get_probe()
            .format(
                &hint,
                source,
                &Default::default(),
                &MetadataOptions::default(),
            )
            .ok()?;
        let params = &probed.format.default_track()?.codec_params;

        Some(Header {
            kind,
            rate: params.sample_rate.map(f64::from),
            channels: params
                .channels
                .map(|channels| i64::try_from(channels.count()).ok())?,
            frames: params
                .n_frames
                .and_then(|frames| i64::try_from(frames).ok()),
            bits: params.bits_per_coded_sample.map(i64::from),
        })
    }

    /// An AU header: rate and channels from the header, frames from the data size.
    fn au(data: &[u8]) -> Option<Header> {
        let channels = be_u32(data, 20)?;
        if channels == 0 {
            return None;
        }
        let size = be_u32(data, 8)?;
        let rate = f64::from(be_u32(data, 16)?);
        let frames = if size == 0xFFFF_FFFF {
            0
        } else {
            i64::from(size) / i64::from(channels)
        };

        Some(Header {
            kind: Kind::Au.name(),
            rate: Some(rate),
            channels: Some(channels.into()),
            frames: Some(frames),
            bits: None,
        })
    }

    impl Kind {
        /// The name `what` reports.
        fn name(self) -> &'static str {
            match self {
                Kind::Wav => "wav",
                Kind::Aiff => "aiff",
                Kind::Au => "au",
            }
        }
    }

    /// The `(type, rate, channels, frames, bits)` tuple of a header.
    fn tuple(header: Header, vm: &VirtualMachine) -> PyObjectRef {
        let ctx = &vm.ctx;

        ctx.new_tuple(vec![
            ctx.new_str(header.kind).into(),
            maybe_float(header.rate, ctx),
            maybe_int(header.channels, ctx),
            maybe_int(header.frames, ctx),
            maybe_int(header.bits, ctx),
        ])
        .into()
    }

    /// A number, or `None` when the format leaves it out.
    fn maybe_float(value: Option<f64>, ctx: &rustpython_vm::Context) -> PyObjectRef {
        value.map_or_else(|| ctx.none(), |value| ctx.new_float(value).into())
    }

    /// See [`maybe_float`].
    fn maybe_int(value: Option<i64>, ctx: &rustpython_vm::Context) -> PyObjectRef {
        value.map_or_else(|| ctx.none(), |value| ctx.new_int(value).into())
    }

    /// The first kilobyte of a file, where sound file headers live.
    fn read_header(path: &Path) -> Option<Vec<u8>> {
        let mut file = File::open(path).ok()?;
        let mut data = vec![0; 1024];
        let read = file.read(&mut data).ok()?;

        data.truncate(read);
        Some(data)
    }

    /// Whether `data` has `magic` at `at`.
    fn is(data: &[u8], at: usize, magic: &[u8]) -> bool {
        data.get(at..).is_some_and(|rest| rest.starts_with(magic))
    }

    /// A big-endian `u32` at `at`.
    fn be_u32(data: &[u8], at: usize) -> Option<u32> {
        Some(u32::from_be_bytes(data.get(at..at + 4)?.try_into().ok()?))
    }

    #[cfg(test)]
    mod tests {
        #![expect(clippy::float_cmp, reason = "the tests assert exact sample rates")]

        use rustpython_vm::builtins::{PyFloat, PyStr, PyTuple};

        use super::*;

        fn wav_bytes() -> Vec<u8> {
            let mut data = Vec::new();
            data.extend_from_slice(b"RIFF");
            let size = 36 + 8; // the rest of the file: chunks up to the end of `data`
            data.extend_from_slice(&u32::to_le_bytes(size));
            data.extend_from_slice(b"WAVE");
            data.extend_from_slice(b"fmt ");
            data.extend_from_slice(&16u32.to_le_bytes());
            data.extend_from_slice(&1u16.to_le_bytes()); // pcm
            data.extend_from_slice(&2u16.to_le_bytes()); // channels
            data.extend_from_slice(&44_100u32.to_le_bytes()); // rate
            data.extend_from_slice(&176_400u32.to_le_bytes()); // bytes per second
            data.extend_from_slice(&4u16.to_le_bytes()); // bytes per frame
            data.extend_from_slice(&16u16.to_le_bytes()); // bits per sample
            data.extend_from_slice(b"data");
            data.extend_from_slice(&8u32.to_le_bytes());
            data.extend_from_slice(&[0; 8]); // a frame's worth of silence

            data
        }

        fn aiff_bytes() -> Vec<u8> {
            let mut data = Vec::new();
            data.extend_from_slice(b"FORM");
            data.extend_from_slice(&446u32.to_be_bytes()); // the AIFF tag and both chunks
            data.extend_from_slice(b"AIFF");
            data.extend_from_slice(b"COMM");
            data.extend_from_slice(&18u32.to_be_bytes());
            data.extend_from_slice(&2i16.to_be_bytes()); // channels
            data.extend_from_slice(&100i32.to_be_bytes()); // frames
            data.extend_from_slice(&16i16.to_be_bytes()); // bits
                                                          // the sample rate as an 80-bit extended
                                                          // float: 44100 = 1.3458… × 2^15
            data.extend_from_slice(&0x400Eu16.to_be_bytes()); // exponent: 16383 + 15
            data.extend_from_slice(&[0xAC, 0x44, 0, 0, 0, 0, 0, 0]); // 44100 × 2^48
            data.extend_from_slice(b"SSND");
            data.extend_from_slice(&408u32.to_be_bytes()); // offset, block size and the samples
            data.extend_from_slice(&[0; 8]);
            data.extend_from_slice(&[0; 400]); // 100 frames of stereo silence, 16-bit

            data
        }

        fn au_bytes() -> Vec<u8> {
            let mut data = Vec::new();
            data.extend_from_slice(b".snd");
            data.extend_from_slice(&24u32.to_be_bytes()); // header size
            data.extend_from_slice(&200u32.to_be_bytes()); // data size
            data.extend_from_slice(&3u32.to_be_bytes()); // encoding: 16-bit linear
            data.extend_from_slice(&44_100u32.to_be_bytes()); // rate
            data.extend_from_slice(&2u32.to_be_bytes()); // channels

            data
        }

        /// A file in the cargo temporary directory holding `bytes`.
        fn sound_file(name: &str, bytes: &[u8]) -> std::path::PathBuf {
            let path = std::env::temp_dir().join(name);
            std::fs::write(&path, bytes).expect("writing a test sound file works");

            path
        }

        #[test]
        fn magic_names_the_kind() {
            assert_eq!(sniff(&wav_bytes()), Some(Kind::Wav));
            assert_eq!(sniff(&aiff_bytes()), Some(Kind::Aiff));
            assert_eq!(sniff(&au_bytes()), Some(Kind::Au));

            assert_eq!(sniff(b"not a sound file"), None);
            assert_eq!(sniff(b""), None);

            // a RIFF file that is not a WAVE
            let mut not_wave = wav_bytes();
            not_wave.splice(8..12, b"AVI ".to_vec());
            assert_eq!(sniff(&not_wave), None);
        }

        #[test]
        fn wavs_report_their_format() {
            let path = sound_file("athenacl-test.wav", &wav_bytes());
            let header = what_file(&path).expect("a wav file is recognized");
            drop(path);

            assert_eq!(header.kind, "wav");
            assert_eq!(header.rate, Some(44_100.0));
            assert_eq!(header.channels, Some(2));
            assert_eq!(header.frames, Some(2)); // 8 bytes of data, 4 per frame
            assert_eq!(header.bits, Some(16));
        }

        #[test]
        fn aiffs_report_their_format() {
            let path = sound_file("athenacl-test.aiff", &aiff_bytes());
            let header = what_file(&path).expect("an aiff file is recognized");
            drop(path);

            assert_eq!(header.kind, "aiff");
            assert_eq!(header.rate, Some(44_100.0));
            assert_eq!(header.channels, Some(2));
            // symphonia counts the sound chunk's 8 header bytes as samples: 102, not the 100
            // the common chunk declares
            assert_eq!(header.frames, Some(102));
            assert_eq!(header.bits, Some(16));
        }

        #[test]
        fn aus_report_their_format() {
            let header = au(&au_bytes()).expect("an au header is recognized");
            assert_eq!(header.kind, "au");
            assert_eq!(header.rate, Some(44_100.0));
            assert_eq!(header.channels, Some(2));
            assert_eq!(header.frames, Some(100)); // 200 bytes, 2 channels
            assert_eq!(header.bits, None);
        }

        #[test]
        fn other_files_are_not_sound_files() {
            let path = sound_file("athenacl-test.txt", b"not a sound file");
            assert_eq!(what_file(&path), None);

            // a WAVE whose fmt chunk is gone
            let mut no_fmt = wav_bytes();
            no_fmt.splice(12..16, b"junk".to_vec());
            let path = sound_file("athenacl-test-no-fmt.wav", &no_fmt);
            drop(path);
        }

        #[test]
        fn the_module_reads_files() {
            let path = sound_file("athenacl-test-what.wav", &wav_bytes());

            let interpreter = crate::init_py_interpreter();
            interpreter.enter(|vm| {
                let sndhdr = vm.import("sndhdr", 0).expect("the module imports");
                let what = sndhdr.get_attr("what", vm).expect("the module has what");

                let unknown = what
                    .call(("no-such-file",), vm)
                    .expect("a missing file is not an error");
                assert!(vm.is_none(&unknown));

                let wav = what
                    .call((path.to_string_lossy().to_string(),), vm)
                    .expect("a wav file is not an error");
                let tuple = wav
                    .downcast_ref::<PyTuple>()
                    .expect("the result is a tuple");
                let kind = tuple.as_slice()[0]
                    .downcast_ref::<PyStr>()
                    .expect("the kind is a string")
                    .to_str()
                    .unwrap_or_default();
                let rate = tuple.as_slice()[1]
                    .downcast_ref::<PyFloat>()
                    .expect("the rate is a number")
                    .to_f64();

                assert_eq!(kind, "wav");
                assert!(rate == 44_100.0);
            });
        }
    }
}
