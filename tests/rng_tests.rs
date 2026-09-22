//! Runs the rng stream integration tests: the redirected `random` module, the bridge's streams, and
//! their contracts, asserted rather than smoked.

#![expect(
    clippy::panic,
    reason = "a failing source should stop its test with the source named"
)]

use rustpython_vm as vm;

fn with_interpreter(f: impl FnOnce(&vm::VirtualMachine)) {
    athenacl::init_scratch_prefs();
    let interpreter = athenacl::init_py_interpreter();
    interpreter.enter(f);
}

/// Python source whose last statement is `RESULT = ...`, evaluated for its `repr`.
fn evaluate(vm: &vm::VirtualMachine, source: &str) -> String {
    let scope = vm.new_scope_with_builtins();
    let code = vm
        .compile_with_opts(
            source,
            vm::compiler::Mode::Exec,
            "rng-test".to_owned(),
            vm.compile_opts(),
        )
        .map_err(|err| vm.new_syntax_error(&err, Some(source)))
        .expect("the source compiles");
    vm.run_code_obj(code, scope.clone())
        .unwrap_or_else(|exception| {
            vm.print_exception(exception);
            panic!("the source runs: {source}");
        });
    let result = vm
        .compile_with_opts(
            "RESULT",
            vm::compiler::Mode::Eval,
            "rng-test".to_owned(),
            vm.compile_opts(),
        )
        .expect("RESULT evaluates");
    let value = vm.run_code_obj(result, scope).unwrap_or_else(|exception| {
        vm.print_exception(exception);
        panic!("RESULT evaluates: {source}");
    });
    let repr = value.repr(vm).expect("the value has a repr");
    repr.to_str().expect("the repr is text").to_owned()
}

/// Python and the bridge advance one stream together: interleaved draws, one of them taken by Rust
/// directly, resume each other.
#[test]
#[expect(clippy::float_cmp, reason = "the draws are pinned exactly")]
fn python_and_rust_draw_the_same_stream() {
    with_interpreter(|vm| {
        let drawn = evaluate(
            vm,
            r#"
import random
from athenaCL.libATH import rngBridge

random.seed(42)
random.random()  # the first draw, through Python
RESULT = rngBridge.parameters.random()  # the second, through the bridge
"#,
        );
        // the third, taken by Rust calling the stream method itself
        let stream = vm
            .import("athenaCL.libATH.rngBridge", 0)
            .expect("athenaCL imports")
            .get_attr("libATH", vm)
            .expect("libATH")
            .get_attr("rngBridge", vm)
            .expect("the bridge module")
            .get_attr("parameters", vm)
            .expect("the parameters stream");
        let random = stream.get_attr("random", vm).expect("the draw method");
        let rust_draw = random.call((), vm).expect("Rust draws through the stream");
        let rust_draw = rust_draw
            .downcast_ref::<rustpython_vm::builtins::PyFloat>()
            .expect("a float")
            .to_f64();

        let reference = evaluate(
            vm,
            r#"
import random

random.seed(42)
RESULT = repr([random.random() for _ in range(3)])
"#,
        );
        let expected: Vec<f64> = reference
            .trim_matches('\'')
            .trim_start_matches('[')
            .trim_end_matches(']')
            .split(", ")
            .map(|value| value.parse().expect("a float"))
            .collect();
        let second: f64 = drawn.trim_matches('\'').parse().expect("a float");
        assert_eq!(
            second, expected[1],
            "the bridge's draw is the second of the stream"
        );
        assert_eq!(
            rust_draw, expected[2],
            "Rust's draw is the third of the stream"
        );
    });
}

/// A seed's first uniforms through Python's `random`, frozen against the Rust goldens.
#[test]
fn seed_uniforms_through_python_are_frozen() {
    with_interpreter(|vm| {
        let drawn = evaluate(
            vm,
            r#"
import random

random.seed(42)
RESULT = repr([random.random() for _ in range(3)])
"#,
        );
        assert_eq!(
            drawn,
            "'[0.010420726227266863, 0.6838216199428104, 0.42172164704826665]'"
        );
    });
}

/// Every seed encoding's first draws through the bridge, frozen: int (zero, negative, beyond 128
/// bits, beyond 64 bits), unicode str, float, and bytes — the huge integers included, which no
/// machine width holds.
#[test]
fn all_seed_encodings_are_frozen_through_the_bridge() {
    with_interpreter(|vm| {
        let drawn = evaluate(
            vm,
            r#"
from athenaCL.libATH import rngBridge

def draws(seed):
    rngBridge.parameters.seed(seed)
    return [rngBridge.parameters.random() for _ in range(2)]

RESULT = repr([
    draws(0), draws(-12345), draws(2 ** 100 + 12345), draws(2 ** 200), draws(-(2 ** 200)),
    draws('ünïcødé 🎵'), draws(-0.0), draws(b'\x00\xff'),
])
"#,
        );
        assert_eq!(
            drawn,
            concat!(
                "'[[0.8140322782963471, 0.9879443697944874], ",
                "[0.790695075264827, 0.9950673537316433], ",
                "[0.9419837696961295, 0.8451631658294405], ",
                "[0.0973780815481956, 0.7706176727402214], ",
                "[0.67522654352289, 0.5695104007457215], ",
                "[0.6203725344350238, 0.47535106019728124], ",
                "[0.1705578037033001, 0.7361657245824361], ",
                "[0.2644852260555608, 0.8907850160355159]]'"
            )
        );
    });
}

/// The full-word bound draws the raw words, frozen from the Rust goldens.
#[test]
fn full_word_draws_through_python_are_frozen() {
    with_interpreter(|vm| {
        let drawn = evaluate(
            vm,
            r#"
from athenaCL.libATH import rngBridge

rngBridge.parameters.seed(-12345)
RESULT = [rngBridge.parameters.below(2 ** 64) for _ in range(3)]
"#,
        );
        assert_eq!(
            drawn,
            "[14585749693752774906, 18355752810391038032, 5797352014731876786]"
        );
    });
}

/// Separate interpreters keep separate streams: one's draws never move the other's.
#[test]
fn interpreters_keep_separate_streams() {
    athenacl::init_scratch_prefs();
    let first = athenacl::init_py_interpreter();
    let second = athenacl::init_py_interpreter();

    let run = |interpreter: &vm::Interpreter, source: &str| -> String {
        interpreter.enter(|vm| {
            let scope = vm.new_scope_with_builtins();
            let code = vm
                .compile_with_opts(
                    source,
                    vm::compiler::Mode::Exec,
                    "rng-test".to_owned(),
                    vm.compile_opts(),
                )
                .expect("the source compiles");
            vm.run_code_obj(code, scope.clone())
                .expect("the source runs");
            let result = vm
                .compile_with_opts(
                    "RESULT",
                    vm::compiler::Mode::Eval,
                    "rng-test".to_owned(),
                    vm.compile_opts(),
                )
                .expect("RESULT evaluates");
            vm.run_code_obj(result, scope)
                .expect("RESULT runs")
                .repr(vm)
                .expect("the value has a repr")
                .to_str()
                .expect("the repr is text")
                .to_owned()
        })
    };

    // A seeds and draws once
    let a_first = run(
        &first,
        r#"
from athenaCL.libATH import rngBridge
rngBridge.parameters.seed(7)
RESULT = rngBridge.parameters.random()
"#,
    );
    // B seeds the same and draws twice: shared state would have restarted A's stream here
    let b_draws = run(
        &second,
        r#"
from athenaCL.libATH import rngBridge
rngBridge.parameters.seed(7)
RESULT = [rngBridge.parameters.random() for _ in range(2)]
"#,
    );
    // A draws again, without reseeding: its own second draw
    let a_second = run(
        &first,
        r#"
from athenaCL.libATH import rngBridge
RESULT = rngBridge.parameters.random()
"#,
    );

    let b: Vec<&str> = b_draws
        .trim_start_matches('[')
        .trim_end_matches(']')
        .split(", ")
        .collect();
    assert_eq!(a_first, b[0], "one seed, one sequence");
    assert_eq!(
        a_second, b[1],
        "another interpreter's seeding and drawing leaves this stream where it was"
    );
}

/// The parameters and textures streams are seeded and drawn as units: `TPsd`'s own call —
/// `random.seed()` — leaves the textures stream and the legacy `TMsd` generator where they were.
#[test]
fn parameters_and_textures_are_separate_streams() {
    with_interpreter(|vm| {
        let drawn = evaluate(
            vm,
            r#"
import random
from athenaCL.libATH import rngBridge
from athenaCL.libATH.omde import rand

# TPsd's call, on the parameters stream
random.seed(5)
parameters_before = random.random()

# the textures stream, seeded, holds its position across TPsd
rngBridge.textures.seed(9)
textures_before = rngBridge.textures.random()
rngBridge.textures.seed(9)
random.seed(5)
parameters_again = random.random()
textures_after = rngBridge.textures.random()

# the legacy TMsd generator draws its own sequence, unmoved by TPsd: TMsd seeds it,
# then it draws. Its continuation is captured first, then checked without reseeding —
# a reset would hide any disturbance.
legacy = rand.UniformRNG()
legacy.seed(7)
first_six = [legacy.random() for _ in range(6)]
legacy.seed(7)
legacy_before = [legacy.random() for _ in range(3)]
random.seed(99)
random.random()
legacy_after = [legacy.random() for _ in range(3)]

RESULT = repr((
    parameters_before == parameters_again,
    textures_before == textures_after,
    legacy_before == first_six[:3],
    legacy_after == first_six[3:],
))
"#,
        );
        assert_eq!(drawn, "'(True, True, True, True)'");
    });
}

/// The aliases `omde.rand` caches at import capture the redirected functions, and drawing through
/// them advances the seeded stream.
#[test]
fn cached_aliases_draw_the_redirected_stream() {
    with_interpreter(|vm| {
        let drawn = evaluate(
            vm,
            r#"
import random
from athenaCL.libATH import rngBridge
from athenaCL.libATH.omde import rand

items = [10, 20, 30, 40, 50, 60]

random.seed(123)
through_alias = [rand.random() for _ in range(2)]
random.seed(123)
through_bridge = [rngBridge.parameters.random() for _ in range(2)]

# the cached choice draws from the stream: its pick consumes a position, and the draw
# after it continues the shared stream — the same walk taken through the bridge
random.seed(777)
alias_choice = [rand.choice(items), random.random()]
random.seed(777)
bridge_choice = [rngBridge.parameters.choice(items), random.random()]

RESULT = (through_alias == through_bridge and alias_choice == bridge_choice
          and alias_choice[0] in items)
"#,
        );
        assert_eq!(drawn, "True");
    });
}

/// The redirected wrappers keep Python's contracts — parameter names, versions, errors — and
/// `below` states its own.
#[test]
fn wrappers_hold_their_contracts() {
    with_interpreter(|vm| {
        let drawn = evaluate(
            vm,
            r#"
import random
from athenaCL.libATH import rngBridge

random.seed(0)
singleton = random.randint(5, 5)
sixes = [random.randint(0, 5) for _ in range(2)]
values = [random.randint(-2, 3) for _ in range(2)]
choice = random.choice([7])

# keyword arguments, in the replaced functions' own parameter names
random.seed(a=0)
kw_seed = random.random()
random.seed(0)
pos_seed = random.random()
kw_randint = random.randint(a=0, b=5)
kw_choice = random.choice(seq=[7])
kw_shuffle = random.shuffle(x=[3, 1, 2])
items = list(range(6))
shuffled = random.shuffle(items)

# the version is the stream's single policy
seed_v2 = (random.seed(5, version=2) is None)
try:
    random.seed(5, version=1)
    version_error = 'no error'
except ValueError as err:
    version_error = '%s: %s' % (type(err).__name__, err)

# seeds beyond any machine width, and a string that cannot encode
huge = []
for seed in (2 ** 200, -(2 ** 200)):
    random.seed(seed)
    huge.append(0 <= random.random() < 1)
try:
    random.seed('abc\ud800def')
    surrogate_error = 'no error'
except UnicodeEncodeError as err:
    surrogate_error = type(err).__name__

# below's own bounds: every non-positive bound is a value error, however wide; past the
# raw word, an overflow
below_errors = []
for bound in (0, -5, -(2 ** 200)):
    try:
        rngBridge.parameters.below(bound)
        below_errors.append('no error')
    except Exception as err:
        below_errors.append('%s: %s' % (type(err).__name__, err))
try:
    rngBridge.parameters.below(2 ** 64 + 1)
    below_errors.append('no error')
except Exception as err:
    below_errors.append('%s: %s' % (type(err).__name__, err))

# the other wrappers' errors
wrapper_errors = []
for call in ('random.randint(2, 1)', 'random.choice([])',
             'random.randint(2 ** 63, 2 ** 63)'):
    try:
        eval(call)
        wrapper_errors.append('no error')
    except Exception as err:
        wrapper_errors.append('%s: %s' % (type(err).__name__, err))

RESULT = repr((
    singleton, sixes, values, choice, kw_seed == pos_seed, kw_randint in range(6),
    kw_choice, kw_shuffle, shuffled, items, seed_v2, version_error, huge,
    surrogate_error, below_errors, wrapper_errors,
))
"#,
        );
        let expected = concat!(
            "\"(5, [4, 4], [3, 3], 7, True, True, 7, None, None, [0, 3, 2, 4, 5, 1], True, ",
            "'ValueError: random.seed: version 1 is not carried; the stream seeds one way', ",
            "[True, True], 'UnicodeEncodeError', ",
            "['ValueError: random.below: bound must be positive, got 0', ",
            "'ValueError: random.below: bound must be positive, got -5', ",
            "'ValueError: random.below: bound must be positive, got \
             -1606938044258990275541962092341162602522202993782792835301376', ",
            "'OverflowError: random.below: bound 18446744073709551617 is beyond the 64-bit draws \
             the stream makes'], ",
            "['ValueError: random.randint: empty range for randint()', ",
            "'IndexError: Cannot choose from an empty sequence', ",
            "'OverflowError: random.randint: endpoints must fit the 64-bit draws the stream \
             makes'])\""
        );
        assert_eq!(drawn, expected);
    });
}
