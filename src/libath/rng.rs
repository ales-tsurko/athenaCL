//! athenaCL's random streams, in Rust: the single home of the seeded chance the modules draw.
//!
//! Two streams are kept per interpreter, seeded and drawn as units: `parameters`, which the `TPsd`
//! command seeds and the parameter objects draw from, and `textures`, which the `TMsd` command
//! seeds through OMDE's shared `UniformRNG()`. Gauss keeps drawing from `parameters`. Each is a
//! `ChaCha12Rng` with `SHA-256`-folded
//! seeds — both named and stable, so a seed's draw sequence stays reproducible across builds. The
//! streams live as instances on this module, which RustPython creates per interpreter, so separate
//! interpreters never share state.
//!
//! The interpreter's `random` module is redirected onto the `parameters` stream at initialization,
//! before any athenaCL code imports — so `TPsd`'s existing `random.seed()` call lands here, and
//! every module-level `random.*` draw, from Python or from ported Rust, advances the same stream.
//!
//! The migration is staged by backend, each stage its own released sequence change: stage one
//! replaced module-level `random` draws — the `TPsd`-seeded parameter objects, and the
//! TextureModules that draw global random directly (`MonophonicOrnament`, `IntervalExpansion`);
//! stage two, with the omde family, replaces the legacy `UniformRNG` draws that `TMsd` seeds.
//! Pieces saved before a stage re-render differently after it.

use rustpython_vm::pymodule;

pub(crate) fn module_def(
    ctx: &rustpython_vm::Context,
) -> &'static rustpython_vm::builtins::PyModuleDef {
    _inner::module_def(ctx)
}

/// The seed values' canonical bytes and the stream draws, as plain functions.
mod core {
    use rand::{Rng, RngCore, SeedableRng};
    use rand_chacha::ChaCha12Rng;
    use sha2::{Digest, Sha256};

    /// A seed value's canonical bytes, type-tagged so equal bytes of different types never meet in
    /// the same digest. Integers carry a sign byte and their big-endian minimal magnitude — zero's
    /// magnitude is a single zero byte, with a positive sign — floats carry their IEEE-754 bits
    /// big-endian, strings their UTF-8, and bytes themselves.
    pub(crate) enum Seed {
        /// draw from a canonical encoding
        Bytes(Vec<u8>),
        /// draw from operating-system entropy
        Entropy,
    }

    /// The canonical encoding of an integer seed, the one type with structure: the big-endian
    /// minimal magnitude bytes, unbounded in width, zero's being a single zero byte.
    pub(crate) fn integer_bytes(negative: bool, magnitude: Vec<u8>) -> Vec<u8> {
        let mut bytes = vec![b'I', if negative { b'-' } else { b'+' }];
        if magnitude.is_empty() {
            bytes.push(0);
        } else {
            bytes.extend_from_slice(&magnitude);
        }
        bytes
    }

    /// The 32-byte seed the digest of a canonical encoding yields.
    pub(crate) fn seed_bytes(bytes: &[u8]) -> [u8; 32] {
        let digest = Sha256::digest(bytes);
        let mut seed = [0; 32];
        seed.copy_from_slice(&digest);
        seed
    }

    /// The stream seeded from a seed value.
    pub(crate) fn stream(seed: Seed) -> ChaCha12Rng {
        match seed {
            Seed::Bytes(bytes) => ChaCha12Rng::from_seed(seed_bytes(&bytes)),
            Seed::Entropy => ChaCha12Rng::from_entropy(),
        }
    }

    /// An unbiased draw below `n`, for the bounds `1 <= n <= 2^64`; the bound at `2^64` itself
    /// returns the raw word, which no exclusive range can express.
    pub(crate) fn below<R: RngCore>(rng: &mut R, n: u128) -> Option<u128> {
        const U64_MAX: u128 = u64::MAX as u128;
        const WORD: u128 = U64_MAX + 1;
        match n {
            1..=U64_MAX => Some(rng.gen_range(0..n as u64) as u128),
            WORD => Some(u128::from(rng.next_u64())),
            _ => None,
        }
    }

    /// An inclusive draw between two `i64` endpoints, without consuming a draw for a range of one.
    /// `None` when the span exceeds the raw word, or the endpoints are reversed.
    pub(crate) fn between<R: RngCore>(rng: &mut R, a: i64, b: i64) -> Option<i64> {
        if a == b {
            return Some(a);
        }
        if a > b {
            return None;
        }
        let span = (b as i128 - a as i128 + 1).cast_unsigned();
        let width = u128::from(u64::MAX) + 1;
        if span > width {
            return None;
        }
        let offset = below(rng, span)?;
        Some((a as i128 + offset as i128) as i64)
    }

    #[cfg(test)]
    mod tests {
        use rand::{Rng, RngCore};
        use sha2::{Digest, Sha256};

        use super::{below, between, integer_bytes, seed_bytes, stream, Seed};

        /// Integer seeds carry a sign byte and their big-endian minimal magnitude; zero's magnitude
        /// is one zero byte, with a positive sign.
        #[test]
        fn integer_seeds_encode_canonically() {
            assert_eq!(integer_bytes(false, Vec::new()), b"I+\x00");
            assert_eq!(integer_bytes(false, vec![0x30, 0x39]), b"I+09");
            assert_eq!(integer_bytes(true, vec![0x30, 0x39]), b"I-\x30\x39");
            // 2^100 + 12345 carries 13 bytes, and the width is unbounded: 2^200 carries 26
            let mut expected = vec![b'I', b'+', 0x10];
            expected.extend(std::iter::repeat_n(0, 10));
            expected.extend_from_slice(&[0x30, 0x39]);
            assert_eq!(integer_bytes(false, expected[2..].to_vec()), expected);
            let mut wide = vec![b'I', b'+', 0x01];
            wide.extend(std::iter::repeat_n(0, 25));
            assert_eq!(integer_bytes(false, wide[2..].to_vec()), wide);
        }

        /// The digests of the canonical seed encodings, frozen: a change to the encoding or the
        /// hash moves every seed's stream.
        #[test]
        fn seed_digests_are_frozen() {
            fn digest(bytes: &[u8]) -> Vec<u8> {
                Sha256::digest(bytes).to_vec()
            }
            fn hex(want: &str) -> Vec<u8> {
                want.as_bytes()
                    .chunks(2)
                    .map(|pair| {
                        let pair = std::str::from_utf8(pair).expect("hex digits");
                        u8::from_str_radix(pair, 16).expect("hex digits")
                    })
                    .collect()
            }
            assert_eq!(
                digest(b"I+\x00"),
                hex("cead6af3bafe51a2b4036dd80524e2cbeb6220a7beeeca77f882603348cdfd8a")
            );
            assert_eq!(
                digest(b"I-\x30\x39"),
                hex("6ede1eb8cc295bc5fa13840aa189862d7e2ee65614cb7381a491bfbdbd6ad71e")
            );
            let mut big = vec![b'I', b'+', 0x10];
            big.extend(std::iter::repeat_n(0, 10));
            big.extend_from_slice(&[0x30, 0x39]);
            assert_eq!(
                digest(&big),
                hex("62282bae075414a308402279efb702646da9734233437528ade132128e6be421")
            );
            let mut text = vec![b'S'];
            text.extend_from_slice("ünïcødé 🎵".as_bytes());
            assert_eq!(
                digest(&text),
                hex("19f26aac83ae12251e3a2ec319c633a9a535189555f0e8a89b0399402c5c7786")
            );
            let mut float = vec![b'F'];
            float.extend_from_slice(&(-0.0f64).to_bits().to_be_bytes());
            assert_eq!(
                digest(&float),
                hex("77d087042710da042d6e4a19b913fc5d32d521ed19141e990b62933120feb1c8")
            );
            assert_eq!(
                digest(b"B\x00\xff"),
                hex("68d794c79809afcbc35881222edfb46aca578826ee00fbfe49a30cd4bd00d6b8")
            );
            // 2^200 and its negative: beyond i128, encodable all the same
            let mut wide = vec![b'I', b'+', 0x01];
            wide.extend(std::iter::repeat_n(0, 25));
            assert_eq!(
                digest(&wide),
                hex("8dbcef2740b8ee2540f49c3cbc5412633e3bcb99e9c1a28c43768a996e50a0e7")
            );
            wide[1] = b'-';
            assert_eq!(
                digest(&wide),
                hex("fa98ecfb4cfd208e26ead1157bfada54e106574d5f62d0b07fa721c1c092e136")
            );
            // the frozen digests are what the streams seed from
            assert_eq!(
                seed_bytes(&integer_bytes(false, Vec::new())),
                digest(b"I+\x00")[..]
            );
        }

        /// A seed's first draws, frozen: the sequence a seed begins defines every render made from
        /// it.
        #[test]
        fn draw_sequences_are_frozen() {
            // uniforms from seed 0
            let mut zero = stream(Seed::Bytes(integer_bytes(false, Vec::new())));
            let uniforms: Vec<f64> = (0..3).map(|_| zero.gen()).collect();
            assert_eq!(
                uniforms,
                [0.8140322782963471, 0.9879443697944874, 0.7735099004168228]
            );

            // small ranges from seed 0, and their placement between endpoints
            let mut zero = stream(Seed::Bytes(integer_bytes(false, Vec::new())));
            let sixes: Vec<u128> = (0..6)
                .map(|_| below(&mut zero, 6).expect("the bound is within the word"))
                .collect();
            assert_eq!(sixes, [4, 4, 5, 5, 2, 5]);
            let mut zero = stream(Seed::Bytes(integer_bytes(false, Vec::new())));
            let placed: Vec<i64> = (0..5)
                .map(|_| between(&mut zero, -2, 3).expect("the span is within the word"))
                .collect();
            assert_eq!(placed, [2, 2, 3, 3, 0]);

            // raw words — the bound at 2^64 exactly — from seed -12345
            let mut negative = stream(Seed::Bytes(integer_bytes(true, vec![0x30, 0x39])));
            let words: Vec<u128> = (0..3)
                .map(|_| {
                    below(&mut negative, u128::from(u64::MAX) + 1)
                        .expect("the full word bound is drawn raw")
                })
                .collect();
            assert_eq!(
                words,
                [
                    14585749693752774906,
                    18355752810391038032,
                    5797352014731876786
                ]
            );
        }

        /// A range of one returns its endpoint without consuming a draw, and the widest range the
        /// word covers draws a single raw word.
        #[test]
        fn range_widths_draw_exactly() {
            let mut zero = stream(Seed::Bytes(integer_bytes(false, Vec::new())));
            assert_eq!(between(&mut zero, 5, 5), Some(5));
            // the singleton above consumed nothing: the six-draw sequence stands
            let sixes: Vec<u128> = (0..2)
                .map(|_| below(&mut zero, 6).expect("bound within word"))
                .collect();
            assert_eq!(sixes, [4, 4]);

            // the full i64 span consumes the raw word the below bound at 2^64 does
            let mut whole = stream(Seed::Bytes(integer_bytes(false, Vec::new())));
            let mut raw = whole.clone();
            let drawn = between(&mut whole, i64::MIN, i64::MAX).expect("the widest span");
            let word = u128::from(raw.next_u64());
            assert_eq!(drawn as i128, i128::from(i64::MIN) + word as i128);
        }

        /// Bounds outside the contract refuse rather than draw.
        #[test]
        fn impossible_bounds_refuse() {
            let mut zero = stream(Seed::Bytes(integer_bytes(false, Vec::new())));
            assert_eq!(below(&mut zero, 0), None);
            assert_eq!(below(&mut zero, u128::from(u64::MAX) + 2), None);
            assert_eq!(between(&mut zero, 3, 2), None);
        }
    }
}

#[pymodule(name = "athenaCL.libATH.rngBridge")]
pub(super) mod _inner {
    #![expect(
        clippy::unwrap_used,
        reason = "the pymodule macro's generated attribute setters unwrap"
    )]

    use rand::Rng;
    use rand_chacha::ChaCha12Rng;
    use rustpython_vm::{
        builtins::{PyByteArray, PyBytes, PyFloat, PyInt, PyStr},
        common::lock::PyMutex,
        function::OptionalArg,
        pyclass, FromArgs, PyObjectRef, PyPayload, PyResult, VirtualMachine,
    };

    use super::core::{self, Seed};

    /// One of athenaCL's random streams: a seeded ChaCha12 sequence drawn as a unit.
    #[pyattr]
    #[pyclass(name = "RngStream")]
    #[derive(Debug, PyPayload)]
    struct PyRngStream {
        rng: PyMutex<ChaCha12Rng>,
    }

    /// The module's two streams, entropy-seeded until a seed command reaches them.
    #[pyattr]
    fn parameters(_vm: &VirtualMachine) -> PyRngStream {
        PyRngStream {
            rng: PyMutex::new(core::stream(Seed::Entropy)),
        }
    }

    #[pyattr]
    fn textures(_vm: &VirtualMachine) -> PyRngStream {
        PyRngStream {
            rng: PyMutex::new(core::stream(Seed::Entropy)),
        }
    }

    /// A seed value's canonical encoding, or entropy for `None` — the types Python's own seed
    /// accepted, which the seed commands can pass through.
    fn seed_of(seed: OptionalArg<PyObjectRef>, vm: &VirtualMachine) -> PyResult<Seed> {
        match seed {
            OptionalArg::Missing => Ok(Seed::Entropy),
            OptionalArg::Present(seed) if vm.is_none(&seed) => Ok(Seed::Entropy),
            OptionalArg::Present(seed) => {
                if let Some(int) = seed.downcast_ref::<PyInt>() {
                    let big = int.as_bigint();
                    // the signed big-endian form carries the sign in its first byte's high bit, so
                    // the sign reads without naming the big integer's own type; the magnitude is
                    // unbounded, as Python's seeds are
                    let negative = big
                        .to_signed_bytes_be()
                        .first()
                        .is_some_and(|&byte| byte >= 0x80);
                    return Ok(Seed::Bytes(core::integer_bytes(
                        negative,
                        big.to_bytes_be().1,
                    )));
                }
                if let Some(float) = seed.downcast_ref::<PyFloat>() {
                    let mut bytes = vec![b'F'];
                    bytes.extend_from_slice(&float.to_f64().to_bits().to_be_bytes());
                    return Ok(Seed::Bytes(bytes));
                }
                if let Some(text) = seed.downcast_ref::<PyStr>() {
                    // a str holding lone surrogates has no UTF-8: the encoding fails, as Python's
                    // own does, rather than seeding with nothing
                    let text = text.to_owned().try_into_utf8(vm)?;
                    let mut bytes = vec![b'S'];
                    bytes.extend_from_slice(text.as_str().as_bytes());
                    return Ok(Seed::Bytes(bytes));
                }
                if let Some(bytes) = seed.downcast_ref::<PyBytes>() {
                    let mut tagged = vec![b'B'];
                    tagged.extend_from_slice(bytes.as_bytes());
                    return Ok(Seed::Bytes(tagged));
                }
                if let Some(bytes) = seed.downcast_ref::<PyByteArray>() {
                    let mut tagged = vec![b'B'];
                    tagged.extend_from_slice(&bytes.borrow_buf());
                    return Ok(Seed::Bytes(tagged));
                }
                Err(vm.new_type_error(
                    "a seed must be None, an int, a float, a str, bytes, or a bytearray",
                ))
            }
        }
    }

    #[pyclass(flags(DISALLOW_INSTANTIATION))]
    impl PyRngStream {
        /// Reseed the stream from a seed value, as Python's `random.seed` accepted them. The
        /// version is the stream's single seed policy: 2, the only one carried.
        #[pymethod]
        fn seed(&self, args: SeedArgs, vm: &VirtualMachine) -> PyResult<()> {
            if let OptionalArg::Present(version) = args.version {
                if version != 2 {
                    return Err(vm.new_value_error(format!(
                        "random.seed: version {version} is not carried; the stream seeds one way"
                    )));
                }
            }
            *self.rng.lock() = core::stream(seed_of(args.a, vm)?);
            Ok(())
        }

        /// A uniform value in `[0, 1)`.
        #[pymethod]
        fn random(&self) -> f64 {
            self.rng.lock().gen::<f64>()
        }

        /// Copying a stream snapshots its position without advancing the original.
        #[pymethod]
        fn __copy__(&self) -> Self {
            Self {
                rng: PyMutex::new(self.rng.lock().clone()),
            }
        }

        /// There are no child objects to copy. Python's deepcopy records this result in its memo,
        /// so distinct generators sharing one stream also share one copied stream.
        #[pymethod]
        fn __deepcopy__(&self, _memo: PyObjectRef) -> Self {
            self.__copy__()
        }

        /// An unbiased draw below `n`, for `1 <= n <= 2**64`.
        #[pymethod]
        fn below(&self, args: BelowArgs, vm: &VirtualMachine) -> PyResult<i128> {
            let int = args
                .n
                .downcast_ref::<PyInt>()
                .ok_or_else(|| vm.new_type_error("an integer is required"))?;
            let big = int.as_bigint();
            let magnitude = big.to_bytes_be().1;
            // the sign reads from the big integer before any narrowing: every bound at or below
            // zero is a value error, however wide
            let negative = big
                .to_signed_bytes_be()
                .first()
                .is_some_and(|&byte| byte >= 0x80);
            if magnitude.is_empty() || negative {
                return Err(
                    vm.new_value_error(format!("random.below: bound must be positive, got {big}"))
                );
            }
            if magnitude.len() > 16 {
                return Err(vm.new_overflow_error(format!(
                    "random.below: bound {big} is beyond the 64-bit draws the stream makes"
                )));
            }
            // widened from the big-endian magnitude; beyond the raw word, below refuses
            let mut bound = [0u8; 16];
            let tail = 16 - magnitude.len();
            if let Some(slot) = bound.get_mut(tail..) {
                slot.copy_from_slice(&magnitude);
            }
            let bound = u128::from_be_bytes(bound);
            let mut rng = self.rng.lock();
            core::below(&mut *rng, bound)
                .map(|draw| draw as i128)
                .ok_or_else(|| {
                    vm.new_overflow_error(format!(
                        "random.below: bound {big} is beyond the 64-bit draws the stream makes"
                    ))
                })
        }

        /// An inclusive draw between two endpoints, of a span the raw word can cover.
        #[pymethod]
        fn randint(&self, args: RandintArgs, vm: &VirtualMachine) -> PyResult<i64> {
            let (a, b) = (
                integer_argument(&args.a, vm)?,
                integer_argument(&args.b, vm)?,
            );
            let small = i64::try_from(a);
            let large = i64::try_from(b);
            if let (Ok(a), Ok(b)) = (small, large) {
                let mut rng = self.rng.lock();
                return match core::between(&mut *rng, a, b) {
                    Some(draw) => Ok(draw),
                    None if a > b => Err(
                        vm.new_value_error("random.randint: empty range for randint()".to_owned())
                    ),
                    None => Err(vm.new_overflow_error(
                        "random.randint: range is beyond the 64-bit draws the stream makes"
                            .to_owned(),
                    )),
                };
            }
            Err(vm.new_overflow_error(
                "random.randint: endpoints must fit the 64-bit draws the stream makes",
            ))
        }

        /// An element of a non-empty sequence, drawn by position.
        #[pymethod]
        fn choice(&self, args: ChoiceArgs, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
            let seq = args.seq;
            let len = seq.length(vm)?;
            if len == 0 {
                return Err(vm.new_index_error("Cannot choose from an empty sequence"));
            }
            let mut rng = self.rng.lock();
            let index =
                core::below(&mut *rng, len as u128).expect("a length is a drawable bound") as usize;
            drop(rng);
            seq.get_item(&index, vm)
        }

        /// A sequence shuffled in place, by a Fisher-Yates walk of the stream.
        #[pymethod]
        fn shuffle(&self, args: ShuffleArgs, vm: &VirtualMachine) -> PyResult<()> {
            let seq = args.x;
            let len = seq.length(vm)?;
            for i in (1..len).rev() {
                let mut rng = self.rng.lock();
                let j = core::below(&mut *rng, i as u128 + 1)
                    .expect("a position is a drawable bound") as usize;
                drop(rng);
                let from = seq.get_item(&j, vm)?;
                let to = seq.get_item(&i, vm)?;
                seq.set_item(&i, from, vm)?;
                seq.set_item(&j, to, vm)?;
            }
            Ok(())
        }
    }

    /// The arguments of `seed`, keeping the replaced function's parameter names.
    #[derive(FromArgs)]
    struct SeedArgs {
        #[pyarg(any, optional)]
        a: OptionalArg<PyObjectRef>,
        #[pyarg(any, optional)]
        version: OptionalArg<isize>,
    }

    /// The arguments of `below`.
    #[derive(FromArgs)]
    struct BelowArgs {
        #[pyarg(any)]
        n: PyObjectRef,
    }

    /// The arguments of `randint`.
    #[derive(FromArgs)]
    struct RandintArgs {
        #[pyarg(any)]
        a: PyObjectRef,
        #[pyarg(any)]
        b: PyObjectRef,
    }

    /// The arguments of `choice`.
    #[derive(FromArgs)]
    struct ChoiceArgs {
        #[pyarg(any)]
        seq: PyObjectRef,
    }

    /// The arguments of `shuffle`.
    #[derive(FromArgs)]
    struct ShuffleArgs {
        #[pyarg(any)]
        x: PyObjectRef,
    }

    /// An integer argument at the width the stream can draw within.
    fn integer_argument(value: &PyObjectRef, vm: &VirtualMachine) -> PyResult<i128> {
        let int = value
            .downcast_ref::<PyInt>()
            .ok_or_else(|| vm.new_type_error("an integer is required"))?;
        int.try_to_primitive::<i128>(vm)
    }
}
