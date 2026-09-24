"""Differential parity tests for the modules ported from `pysrc` to Rust.

A ported module keeps its import path — `athenaCL.libATH.error` is the Rust `src/libath/error.rs`
— and its original Python implementation moves to `athenaCL.libATH._pyref`. These tests call the
port and the reference with the same inputs and compare the results, so a port cannot change
behavior unnoticed. Where the Python side was never tested — which is most of it — the corpus
below is the coverage it never had. The ports restructure rather than transliterate, so a corpus
states where a Python quirk was deliberately not carried over.

Comparisons are by `repr`, which covers values, their types (int against float, list against
tuple), and ordering. Extend the corpus below as more modules are ported.
"""

import importlib
import sys


PORTED = ['chaos', 'error', 'permutate', 'quantize']

# the omde leaves port under their omde paths; the references keep the flat ones
OMDE = {
    'functional': ('athenaCL.libATH.omde.functional', 'athenaCL.libATH._pyref.functional'),
    'bpf': ('athenaCL.libATH.omde.bpf', 'athenaCL.libATH._pyref.bpf'),
    'oscillator': (
        'athenaCL.libATH.omde.oscillator',
        'athenaCL.libATH._pyref.oscillator',
    ),
    'rand': ('athenaCL.libATH.omde.rand', 'athenaCL.libATH._pyref.rand'),
}
FUNCTIONAL = OMDE['functional']

failures = []
checks = 0


def modules(name):
    """The Rust port of a module and its Python reference."""
    return (importlib.import_module('athenaCL.libATH.' + name),
            importlib.import_module('athenaCL.libATH._pyref.' + name))


_labels = []


def note(ok, what):
    """Count a check and record it when it fails."""
    global checks
    checks += 1
    if not ok:
        failures.append((_labels[-1] if _labels else '?', what))


def same(found, expected, what):
    note(repr(found) == repr(expected), '%s: %r != %r' % (what, found, expected))


def describe(err):
    """An exception as the corpus compares it: its type and message."""
    return '%s: %s' % (type(err).__name__, err)


def outcome(fn, *args, **kwargs):
    """What calling a function produced: a value, or the described exception."""
    try:
        return repr(fn(*args, **kwargs)), None
    except Exception as err:  # the corpus only compares errors these functions raise
        return None, describe(err)


def same_call(name, fn, *args, **kwargs):
    """A function of the port and of the reference must agree, errors included."""
    rust, ref = modules(name)
    what = '%s.%s(%s)' % (name, fn, ', '.join(map(repr, args)))
    found, found_error = outcome(getattr(rust, fn), *args, **kwargs)
    expected, expected_error = outcome(getattr(ref, fn), *args, **kwargs)
    note(found == expected and found_error == expected_error,
         '%s: %r%s != %r%s' % (what, found, found_error, expected, expected_error))


def same_iter_call(name, fn, *args):
    """An iterator function, compared drained, the way consumers read it."""
    def drained(fn):
        return outcome(lambda: list(fn(*args)))

    what = '%s.%s(%s)' % (name, fn, ', '.join(map(repr, args)))
    rust, ref = modules(name)
    found, found_error = drained(getattr(rust, fn))
    expected, expected_error = drained(getattr(ref, fn))
    note(found == expected and found_error == expected_error,
         '%s: %r%s != %r%s' % (what, found, found_error, expected, expected_error))


def test_error():
    """The exception types: their hierarchies, messages, and catching."""
    syntax = ('ParameterObjectSyntaxError', 'TransitionSyntaxError',
              'AutomataSpecificationError', 'PulseSyntaxError', 'PitchSyntaxError',
              'ParticleSyntaxError', 'ArgumentError')
    plain = ('CloneError', 'MultisetError', 'TestError')
    rust, ref = modules('error')
    for name in syntax + plain:
        base = SyntaxError if name in syntax else Exception
        note(issubclass(getattr(rust, name), base),
             'error.%s must subclass %s' % (name, base.__name__))
        for msg in ('', 'no pulse data found'):
            found, expected = getattr(rust, name)(msg), getattr(ref, name)(msg)
            same(found.args, expected.args, 'args of error.%s(%r)' % (name, msg))
            same(str(found), str(expected), 'str of error.%s(%r)' % (name, msg))
            # a raised instance is caught by its own type and by its base
            for catcher in (getattr(rust, name), base):
                try:
                    raise found
                    note(False, 'error.%s was not raised' % name)
                except catcher:
                    note(True, '')


def same_quantizer(grid, loop_limit, fill, pull=None, grid_ref=None, keywords=False):
    """A Quantizer's answer for a value, compared between the port and the reference."""
    rust, ref = modules('quantize')

    def run(module):
        def go():
            if keywords:
                quantizer = (
                    module.Quantizer() if loop_limit is None
                    else module.Quantizer(looplimit=loop_limit)
                )
            else:
                quantizer = (
                    module.Quantizer() if loop_limit is None else module.Quantizer(loop_limit)
                )
            if grid is not None:
                quantizer.updateGrid(list(grid))
            if pull is None and grid_ref is None:
                return quantizer.attract(fill)
            if grid_ref is None:
                if keywords:
                    return quantizer.attract(fill, pull=pull)
                return quantizer.attract(fill, pull)
            if keywords:
                return quantizer.attract(fill, pull=1 if pull is None else pull,
                                         gridRef=grid_ref)
            return quantizer.attract(fill, 1 if pull is None else pull, grid_ref)

        return outcome(go)

    what = 'Quantizer(%r, %r, %r, %r, keywords=%r)' % (grid, loop_limit, fill, pull, keywords)
    found, found_error = run(rust)
    expected, expected_error = run(ref)
    note(found == expected and found_error == expected_error,
         '%s: %r%s != %r%s' % (what, found, found_error, expected, expected_error))


def test_quantize():
    """Funneling and grid quantization, over the cases the Python tests never held."""
    # the funnel's full truth table: below, above, and at the threshold, directions included
    for h, a, b, f in ((10, 1, 20, 15), (10, 1, 20, 5), (10, 1, 20, 10), (10, 20, 1, 10),
                       (10.0, 1, 20, 10), (10, 1, 1, 10), (10.5, 1.5, 20.5, 10.5),
                       (10, 1, 20, float('nan')), (0, 1, 1.0, -1), (0, 1.0, 1, -1),
                       (0, float('nan'), 1, 1), (float(2**53), 1, 20, 2**53 + 1),
                       (float(2**53), 1, 20, 2**53 - 1), (float(2**53), 1, 20, 2**53),
                       (float(-2**127), 1, 20, -2**127),
                       (float(2**127), 1, 20, 2**127 - 2**74)):
        for direction in ('match', 'upper', 'lower', 'sideways'):
            same_call('quantize', 'funnelBinary', h, a, b, f, direction)
        # a direction Python would not recognize, passed as anything at all
        same_call('quantize', 'funnelBinary', h, a, b, f, None)
        # keyword spellings
        same_call('quantize', 'funnelBinary', h=h, a=a, b=b, f=f, hDirection='match')
    # grids: every walk direction, reference shift, pull, and tie, with their typing
    for grid in ([1, 2, 3], [0.5, 1.5], [7], [1], [1, 2.5], [3, 1, 2], [0.0]):
        for fill in (-4, 0, 3.5, 5, 7, 10, 2.25, 2.75, 20, 0.5):
            for pull in (None, 1, 1.0, 0, 0.5, 1.5):
                for grid_ref in (None, 0, 10, -10, 0.5):
                    same_quantizer(grid, None, fill, pull, grid_ref)
    # the same calls through keyword arguments
    same_quantizer([1, 2, 3], None, 3.5, 0.5, 10, keywords=True)
    same_quantizer([0.5, 1.5], 4, 1.0, 1, 0, keywords=True)
    # a walk that cannot bracket gives up at its loop limit and answers None
    same_quantizer([0], 4, 5)
    same_quantizer([0], None, 5)
    # an empty grid is an error with its message; so is a missing grid
    same_quantizer([], None, 5)
    same_quantizer(None, None, 5)


def same_trajectory(name, cls, constructor_args, calls):
    """A map stepped through a series of calls, each step compared."""
    rust, ref = modules(name)
    found_map = getattr(rust, cls)(*constructor_args)
    expected_map = getattr(ref, cls)(*constructor_args)
    for i, call in enumerate(calls):
        found, found_error = outcome(lambda: found_map(*call))
        expected, expected_error = outcome(lambda: expected_map(*call))
        what = '%s.%s, step %d of %r' % (name, cls, i, call)
        note(found == expected and found_error == expected_error,
             '%s: %r%s != %r%s' % (what, found, found_error, expected, expected_error))


def test_chaos():
    """Chaotic maps and Fibonacci numbers, over the cases the Python tests never held."""
    same_call('chaos', '_fibonacciNumber', 15, 9, 1)
    for j, k in ((0, 8), (10, 20), (2, 8), (5, 5), (8, 2), (-4, 4), (0, 1), (30, 36),
                 # the default Fibonacci parameter: start 200, length 20 — the series the
                 # normalized parameter object actually generates
                 (200, 220), (190, 205)):
        same_call('chaos', 'fibonacciSeries', j, k)
    # a term beyond float range is the error Python's math.pow raised
    same_call('chaos', '_fibonacciNumber', 15, 9, 2000)
    same_call('chaos', 'fibonacciSeries', 2000, 2003)
    # pow's own domain errors, and keywords
    same_call('chaos', '_fibonacciNumber', 0, 1, -2)
    same_call('chaos', '_fibonacciNumber', -1.5, 1, 0.5)
    same_call('chaos', '_fibonacciNumber', goldenUpper=15, goldenLower=9, i=1)
    same_call('chaos', 'fibonacciSeries', j=0, k=2)
    for n in (0, 1, 2, 6765, 8, 13, 1597, 12.5, 6765.0, 7443506681195961,
              5966070196238306.0, 5966070196238306, float('nan'), float('inf')):
        same_call('chaos', 'fibonacciSuccessor', n)
    same_call('chaos', 'fibonacciSuccessor', n=13)
    for p, x in ((2, 0.3), (4, 0.5), (3.5, 0.2), (2, 3), (1, 1), (0, 0.5), (-1.5, 0.7)):
        same_call('chaos', 'verhulst', p, x)
    same_call('chaos', 'verhulst', p=4, x=0.5)
    # maps: default trajectories, live parameters, and the overflow collapse
    same_trajectory('chaos', 'Henon', (), [()] * 6)
    same_trajectory('chaos', 'Henon', (), [(0.4,), (None, 0.3), (1.5, 0.2)])
    same_trajectory('chaos', 'Henon', (1.4, 0.3, 1e200, 0.18940634), [()] * 3)
    same_trajectory('chaos', 'Lorenz', (), [()] * 5)
    same_trajectory('chaos', 'Lorenz', (), [(99.96,), (None, 2.0), (None, None, 0.375)])
    # keyword construction and calls
    rust_h, ref_h = modules('chaos')[0].Henon, modules('chaos')[1].Henon
    same(rust_h(a=0.4)(), ref_h(a=0.4)(), 'Henon(a=0.4) stepped')
    same(rust_h()(), ref_h()(), 'Henon() stepped')
    same(rust_h()(b=0.2), ref_h()(b=0.2), 'Henon() stepped with b')
    same(rust_h(a=1.5, x=0.5)(), ref_h(a=1.5, x=0.5)(), 'Henon(a=1.5, x=0.5) stepped')
    rust_l, ref_l = modules('chaos')[0].Lorenz, modules('chaos')[1].Lorenz
    same(rust_l(r=40)(), ref_l(r=40)(), 'Lorenz(r=40) stepped')
    same(rust_l(s=2, b=0.375)(), ref_l(s=2, b=0.375)(), 'Lorenz(s=2, b=0.375) stepped')
    # the exposed state reads as Python read it
    same(rust_h().x, ref_h().x, 'Henon().x')
    same(rust_l().d, ref_l().d, 'Lorenz().d')


def test_permutate():
    """Permutations: every function over a spread of item lists and widths."""
    for items in ([3, 4, 5], [8, 3, 267], ['a', 'b', 'c'], [], [7], 'abc', (3, 4)):
        for n in range(len(list(items)) + 2):
            for fn in ('combinations', 'selections', 'uniqueCombinations'):
                same_call('permutate', fn, items, n)
                same_iter_call('permutate', 'x' + fn, items, n)
        same_call('permutate', 'permutations', items)
        same_iter_call('permutate', 'xpermutations', items)

    # keyword arguments, Python's negative-width corners, and the pruning case
    same_call('permutate', 'combinations', items=[1, 2], n=1)
    same_call('permutate', 'selections', [], -1)
    same_call('permutate', 'selections', [1], -1)
    same_call('permutate', 'uniqueCombinations', [1], -1)
    same_call('permutate', 'uniqueCombinations', [], -1)
    same_call('permutate', 'combinations', [1, 2], -1)
    # the width-equal walk, which the pruning exists for
    same_call('permutate', 'uniqueCombinations', list(range(18)), 18)
    same_call('permutate', 'uniqueCombinations', list(range(17)), 18)

    # the iterator functions are lazy: this walk has 479 million results, and taking the
    # first must not compute the rest
    rust, ref = modules('permutate')
    same(next(rust.xpermutations(list(range(12)))),
         next(ref.xpermutations(list(range(12)))),
         'first of xpermutations of 12 items')


# the ported modules must import before anything else runs
for name in PORTED:
    modules(name)

class _Missing(object):
    """The marker for a block that never set RESULT."""


MISSING = _Missing()


def same_omde(source, pair, label='?'):
    _labels.append(label)
    """A source over the module namespace `m` — the port or the reference — must agree.
    The block must set RESULT and must not let an exception escape: expected errors are
    caught inside the block and compared as values, so an unintended raise on both sides
    cannot pass as agreement."""
    found = {}
    for path in pair:
        module = importlib.import_module(path)
        namespace = {'m': module, 'RESULT': MISSING}
        try:
            # The app runs with optimize=2; parity blocks must retain their assertions.
            exec(compile(source, '<omde-parity>', 'exec', optimize=0), namespace)
            result = namespace['RESULT']
            if result is MISSING:
                found[path] = (None, 'the block set no RESULT')
            else:
                found[path] = (repr(result), None)
        except Exception as err:
            found[path] = (None, 'the block escaped: %s' % describe(err))
    port, ref = pair
    value, error = found[port]
    expected, expected_error = found[ref]
    ok = value == expected and error == expected_error and error is None
    note(ok,
         '%s %s: %r%s != %r%s' % (pair[0].rsplit('.', 1)[-1],
                                   source.strip().splitlines()[0], value, error,
                                   expected, expected_error))


def same_functional(source):
    """The functional module's own pair."""
    same_omde(source, FUNCTIONAL)


def test_functional():
    """The functional bases, as permanent spike coverage: reflected operators and operand
    order, Function/Generator mixtures, overrides, leaf constructors, coercion, lifespans,
    deepcopy fallbacks, the freezer, and the division quirks."""
    # forward and reflected subtraction, operand order visible in the stored halves
    same_functional("""
f = m.ConstantFunction(10)
forward = f - 5
reflected = 5 - f
RESULT = (type(forward).__name__, forward.a.value, forward.b.value, forward(0),
          type(reflected).__name__, reflected.a.value, reflected.b.value, reflected(0))
""")
    # mixtures: a Function combines a Generator by adapting it; a Generator combines a
    # Function as a Function, and everything else as a Generator — each side's own order
    same_functional("""
f = m.ConstantFunction(3)
g = m.ConstantGenerator(4)
left = f + g
right = g + f
sub_g = g - 5
rsub_g = 5 - g
mul_f = 2 * f
RESULT = (type(left).__name__, type(left.a).__name__, type(left.b).__name__, left(0),
          type(right).__name__, type(right.a).__name__, type(right.b).__name__, right(0),
          type(sub_g).__name__, sub_g.a is g, sub_g.b.value, sub_g(),
          type(rsub_g).__name__, rsub_g.a.value, rsub_g.b is g, rsub_g(),
          type(mul_f).__name__, mul_f.a.value, mul_f.b is f, mul_f(0))
""")
    # a Python subclass's own operators win over the native slots
    same_functional("""
class mine(m.Function):
    def __call__(self, t):
        return 1
    def __add__(self, other):
        return 'my add'
    def __sub__(self, other):
        return 'my sub'
class mygen(m.Generator):
    def __call__(self):
        return 2
    def __mul__(self, other):
        return 'my mul'
x = mine() + 0
y = mine() - 0
z = 3 * mygen()
RESULT = (x, y, type(z).__name__, isinstance(mine(), m.FunctionModel))
""")
    # leaf constructors reach the base initializers, and their own signatures stand
    same_functional("""
class leaf(m.Function):
    def __init__(self, a, b):
        m.Function.__init__(self)
        self.a = a
        self.b = b
    def __call__(self, t):
        return self.a + self.b
class leafgen(m.Generator):
    def __init__(self, v):
        m.Generator.__init__(self)
        self.v = v
    def __call__(self):
        return self.v
x = leaf(3, 4)
y = leafgen(9) + leafgen(1)
RESULT = (x(0), x(1), y(), isinstance(x, m.Function), isinstance(y, m.Generator))
""")
    # coercion: identity for its own kind, adaptation across, constants for everything
    # else — and the check order, Generator before Function before model
    same_functional("""
f = m.ConstantFunction(1)
g = m.ConstantGenerator(2)
class model(m.FunctionModel):
    def instance(self, begin, end):
        return m.ConstantFunction((begin, end))
adapted = m.make_function(g)
constant = m.make_function('x')
instanced = m.make_function(model(), 3, 7)
frozen = m.make_generator(f, 2.5)
same_gen = m.make_generator(g)
const_gen = m.make_generator(4)
RESULT = (m.make_function(f) is f,
          type(adapted).__name__, adapted.tig is g,
          type(constant).__name__, constant.value,
          instanced(0),
          type(frozen).__name__, frozen.f is f, frozen.t.value,
          same_gen is g,
          type(const_gen).__name__, const_gen.value,
          m.make_generator(None))
""")
    # model lifespans: complete, or the two errors for the incomplete shapes
    same_functional("""
class model(m.FunctionModel):
    def instance(self, begin, end):
        return m.ConstantFunction(0)
errors = []
for args in ((model(), 3, None), (model(),), (model(), None, 5)):
    try:
        m.make_function(*args)
        errors.append('no error')
    except Exception as err:
        errors.append('%s: %s' % (type(err).__name__, err))
RESULT = errors
""")
    # the constants deep-copy when they can, and keep the original when they cannot
    same_functional("""
import sys
original = [1, 2]
copied = m.ConstantFunction(original)
kept = m.ConstantFunction(sys)
mutated = original.append(3)
RESULT = (copied.value == [1, 2, 3], copied.value is original,
          kept.value is sys)
""")
    # the freezer takes a Function and a freeze time; anything else is its error, raised
    # exactly as the reference raises it
    same_functional("""
f = m.ConstantFunction(8)
g = m.ConstantGenerator(9)
frozen = m.Freezer(f, 3.0)
errors = []
for bad in (5, g):
    try:
        m.Freezer(bad)
        errors.append('no error')
    except Exception as err:
        errors.append('%s: %s' % (type(err).__name__, err))
RESULT = (frozen(), frozen.t.value, errors)
""")
    # division keeps its Python 2 shape: callable methods, no operator, and the
    # Generator quirk of multiplying when the operand is a Function
    same_functional("""
f = m.ConstantFunction(10)
g = m.ConstantGenerator(4)
div = f.__div__(g)
rdiv = f.__rdiv__(2)
gen_div = g.__div__(f)
gen_const_div = g.__div__(5)
gen_rdiv = g.__rdiv__(2)
kw_div = f.__div__(function=g)
kw_gen_div = g.__div__(object=f)
kw_gen_rdiv = g.__rdiv__(object=2)
operator = None
try:
    f / g
    operator = 'divided'
except TypeError as err:
    operator = type(err).__name__
RESULT = (type(div).__name__, div(0), type(rdiv).__name__, rdiv(0),
          type(gen_div).__name__, gen_div(0), type(gen_const_div).__name__,
          gen_const_div(), type(gen_rdiv).__name__, gen_rdiv(), operator,
          type(kw_div).__name__, kw_div(0),
          type(kw_gen_div).__name__, kw_gen_div(0),
          type(kw_gen_rdiv).__name__, kw_gen_rdiv())
""")
    # the bases themselves: calls raise, instances model as themselves, the inheritance
    # chain reaches FunctionModel, and names are stable
    same_functional("""
f = m.ConstantFunction(1)
class tig(m.Generator):
    def __call__(self):
        return 5
adapted = m.make_function(tig())
calls = []
for make in (lambda: m.Function()(0), lambda: m.Function()(t=0),
             lambda: m.Generator()(),
             lambda: m.FunctionModel().instance(0, 1)):
    try:
        make()
        calls.append('no error')
    except Exception as err:
        calls.append(type(err).__name__)
RESULT = (calls, f.instance(3, 9) is f, f.instance(begin=3, end=9) is f,
          isinstance(f, m.FunctionModel), isinstance(adapted, m.FunctionModel),
          m.FunctionModel.__name__, m.Function.__name__, m.Generator.__name__,
          adapted(0))
""")


def test_bpf():
    """The break-point functions: every interpolation, both periodicities, the
    constructor's errors, and the normalize the docstring mis-describes."""
    same_omde("""
s = m.LinearSegment([(0, 1), (5, 3), (20, 1)])
RESULT = (s.pairs, s(0), s(1), s(2.5), s(5), s(10), s(20), s(25), s(-1))
""", OMDE['bpf'])
    same_omde("""
s = m.LinearSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), (9.0, 8.0)])
RESULT = [round(s(t), 6) for t in (-0.5, 0.0, 2.0, 4.0, 5.5, 7.0, 8.0, 9.0, 12.0)]
""", OMDE['bpf'])
    # the periodic call wraps by period shifts, negative times included
    same_omde("""
s = m.LinearSegment([(0, 0), (4, 10)], periodic=1)
RESULT = [round(s(t), 6) for t in (-3.0, -1.0, 0.0, 2.0, 4.0, 5.0, 7.5, 12.0)]
""", OMDE['bpf'])
    # every interpolation over the same pairs, at the pairs' midpoints and ends
    same_omde("""
pairs = [(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), (9.0, 8.0)]
half = m.HalfCosineSegment(pairs)
step = m.NoInterpolationSegment(pairs)
plain = m.PowerSegment(pairs)
RESULT = ([round(f(t), 9) for f in (half, step, plain) for t in (2.0, 5.5, 8.0)],
          step(0.0), step(8.999))
""", OMDE['bpf'])
    # the power segment's exponent: positive, zero, and negative, defaults and keywords
    same_omde("""
pairs = [(0.0, 0.0), (4.0, 10.0), (7.0, 5.0)]
exponents = (m.PowerSegment(pairs, exp=0.5), m.PowerSegment(pairs, exp=2.0),
             m.PowerSegment(pairs, exp=-0.5), m.PowerSegment(pairs, exp=-2.0),
             m.PowerSegment(pairs, exp=0.0), m.PowerSegment(pairs))
RESULT = [round(f(2.0), 9) for f in exponents]
""", OMDE['bpf'])
    # descending pairs flip the power interpolation's branches
    same_omde("""
falling = m.PowerSegment([(0.0, 10.0), (4.0, 0.0)])
RESULT = (round(falling(2.0), 9), falling.pairs)
""", OMDE['bpf'])
    # the reference's errors: the sequence, the count (its typo standing), the unpack
    same_omde("""
errors = []
for pairs in ([(5, 1), (0, 3)], [(0, 1)]):
    try:
        m.LinearSegment(pairs)
        errors.append('no error')
    except Exception as err:
        errors.append('%s: %s' % (type(err).__name__, err))
RESULT = errors
""", OMDE['bpf'])
    # the base class constructs but its call is unimplemented
    same_omde("""
base = m.BPF([(0, 1), (1, 2)])
try:
    base(0)
    called = 'no error'
except Exception as err:
    called = type(err).__name__
RESULT = (base.pairs, called)
""", OMDE['bpf'])
    # normalize writes the [0, 1] range its docstring does not describe, in place
    same_omde("""
s = m.LinearSegment([(0, 5), (5, 15), (10, 0)])
s.normalize()
RESULT = (s.pairs, s(2.5))
""", OMDE['bpf'])
    # a flat function normalizes by zero, as the reference divides
    same_omde("""
s = m.LinearSegment([(0, 5), (5, 5)])
try:
    s.normalize()
    RESULT = 'no error'
except Exception as err:
    RESULT = '%s: %s' % (type(err).__name__, err)
""", OMDE['bpf'])
    # int pairs float; keyword spellings; the segment kinds accept exp unread
    same_omde("""
s = m.NoInterpolationSegment([(0, 1), (2, 3)], exp=9, periodic=0)
RESULT = (s.pairs, s(1))
""", OMDE['bpf'])


def test_oscillator():
    """The waves: their translated values, the state their calls mutate, the keywords
    their signatures carry, and the None-frequency standing until f arrives."""
    same_omde("""
a = m.Sine(0.5)
RESULT = (a(0), round(a(0.5), 9), a(1.0), round(a(1.5), 9), round(a(2.0), 9))
""", OMDE['oscillator'])
    same_omde("""
a = m.Cosine(0.5)
RESULT = (a(0), a(0.5), a(1.0), round(a(1.5), 9), a(2.0))
""", OMDE['oscillator'])
    # the folded family: midpoints, phases, negative times, and the boundaries
    same_omde("""
up = m.SawUp(2.0)
down = m.SawDown(2.0)
sq = m.Square(2.0)
tri = m.Triangle(2.0)
RESULT = tuple(round(f(t), 9) for f in (up, down, sq, tri) for t in (0.0, 0.125, 0.25, 0.375, 0.625, -0.125))
""", OMDE['oscillator'])
    # the phase shifts the fold; the exponent transforms at construction
    same_omde("""
up = m.SawUp(2.0, 0.25)
pu = m.PowerUp(2.0, 0.25, 2.0)
pd = m.PowerDown(2.0, 0.25, 2.0)
plain = m.PowerUp(2.0)
RESULT = (round(up(0.1), 9), round(pu(0.1), 9), round(pd(0.1), 9),
          round(plain(0.25), 9), round(plain(0.5), 9))
""", OMDE['oscillator'])
    # calls mutate state: f stores frequency, and the saw family's period persists
    same_omde("""
a = m.Sine(2.0)
first = a(0.0)
second = a(0.125, 4.0)
third = a(0.125)
b = m.SawUp(2.0)
saw_first = b(0.0, 4.0)
saw_second = b(0.1)
RESULT = (round(first, 9), round(second, 9), round(third, 9),
          round(saw_first, 9), round(saw_second, 9))
""", OMDE['oscillator'])
    # keyword spellings, and the None frequency standing until f arrives
    same_omde("""
a = m.Sine(None, 0.5)
RESULT = (round(a(0.0, f=2.0), 9),
          round(a(0.125, 2.0, phase0=0.25), 9),
          m.SawUp(frequency=2.0, phase0=0.5)(0.1),
          m.Square(2.0)(0.3))
""", OMDE['oscillator'])
    # calling a None-frequency wave without f divides by None, in Python's words
    same_omde("""
a = m.Sine(None)
try:
    a(0.0)
    RESULT = 'no error'
except Exception as err:
    RESULT = '%s: %s' % (type(err).__name__, err)
""", OMDE['oscillator'])


def test_bpf_regressions():
    same_omde("""# inheritance and functional composition
from athenaCL.libATH.omde.functional import Function, FunctionModel, make_function
RESULT = []
for cls in (m.BPF, m.LinearSegment, m.PowerSegment,
            m.HalfCosineSegment, m.NoInterpolationSegment):
    f = cls([(0, 1), (2, 3)])
    RESULT.append((isinstance(f, m.BPF), isinstance(f, Function),
                   isinstance(f, FunctionModel), f.instance(0, 2) is f,
                   make_function(f) is f, (f + 2)(-1), (5 - f)(-1)))
""", OMDE['bpf'])
    same_omde("""# the abstract base clamps before reaching interpolation
f = m.BPF([(0, 1), (1, 2)])
RESULT = [f(-1), f(1), f(2), f(-(2**2000)), f(2**2000)]
for call in (lambda: f(0), lambda: f(0.5),
             lambda: f.interpolate(None, None, None, None, None)):
    try:
        RESULT.append(call())
    except Exception as err:
        RESULT.append((type(err).__name__, str(err)))
""", OMDE['bpf'])
    same_omde("""# float constructor semantics and streaming unpack errors
class Coordinate:
    def __float__(self):
        return 3.0
f = m.LinearSegment([(b'0', '1'), (bytearray(b'2'), Coordinate())])
RESULT = [f.pairs, f(1)]
for pairs in ([], [(1,)], [()], [(1, 2, 3)], [[1, 2, 3, 4]],
              [{1: 2, 3: 4, 5: 6}], [iter((1, 2, 3))], [1], [None],
              [(1, 2), ('bad', 4)]):
    try:
        m.LinearSegment(pairs)
        RESULT.append('no error')
    except Exception as err:
        RESULT.append((type(err).__name__, str(err)))
""", OMDE['bpf'])
    same_omde("""# keyword pairs and ignored keywords must not coerce exp
RESULT = []
for cls in (m.LinearSegment, m.HalfCosineSegment, m.NoInterpolationSegment):
    f = cls(pairs=[(0, 1), (2, 3)], exp=object(), unused=object())
    RESULT.append(f(t=1))
for call in (lambda: m.LinearSegment(),
             lambda: m.LinearSegment([(0, 1), (2, 3)], 1),
             lambda: m.LinearSegment([(0, 1), (2, 3)], pairs=[])):
    try:
        call()
        RESULT.append('accepted')
    except TypeError:
        RESULT.append('TypeError')
""", OMDE['bpf'])
    same_omde("""# do not round a time across an interval boundary
RESULT = []
for periodic in (False, True):
    f = m.NoInterpolationSegment([(0, 1), (2**53 + 4, 2)], periodic=periodic)
    RESULT.append(f(2**53 + 3))
f = m.NoInterpolationSegment([(0, 1), (1, 2)])
RESULT.extend((f(-(2**2000)), f(2**2000), f(float('nan'))))
""", OMDE['bpf'])
    same_omde("""# exponent validation is delayed and follows the flat-value branch
RESULT = []
for exp in (None, '2', [], float('nan'), 2**2000):
    flat = m.PowerSegment([(0, 3), (1, 3)], exp=exp)
    changing = m.PowerSegment([(0, 0), (1, 1)], exp=exp)
    RESULT.append(flat(0.5))
    try:
        RESULT.append(changing(0.5))
    except Exception as err:
        RESULT.append((type(err).__name__, str(err)))
""", OMDE['bpf'])
    same_omde("""# Python subclass initialization and virtual interpolation, including reentry
class Custom(m.BPF):
    def __init__(self, offset, periodic):
        self.offset = offset
        super().__init__([(0, 2), (1, 4)], periodic)
    def interpolate(self, time, time0, value0, time1, value1):
        self.normalize()
        return (time, value0 + self.offset, value1)
class Derived(m.LinearSegment):
    def __init__(self, label, count, extra):
        self.label = label
        super().__init__([(0, 1), (count, extra)])
    def interpolate(self, *args):
        return super().interpolate(*args) + 10
a = Custom(7, False)
b = Custom(7, True)
c = Derived('mine', 2, 3)
RESULT = (a(0.5), a.pairs, b(1.5), b.pairs, c(1), c.label)
""", OMDE['bpf'])
    same_omde("""# public interpolation uses original operand types and builtin pow
pairs = [(0, 0), (1, 1)]
RESULT = []
for cls in (m.BPF, m.LinearSegment, m.HalfCosineSegment,
            m.NoInterpolationSegment, m.PowerSegment):
    f = cls(pairs, exp=0.5) if cls is not m.BPF else cls(pairs)
    for values in ((-1.0, 0.0, 0.0, 1.0, 1.0),
                   (1, 0, 1, 0, 2), (float('inf'), 0, 0, 1, 1),
                   ('bad', 0, 7, 1, 9), (2**100 + 1, 2**100, 0, 2**100 + 2, 1)):
        try:
            RESULT.append(f.interpolate(*values))
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
f = m.LinearSegment(pairs)
RESULT.append(f.interpolate(time=0.5, time0=0, value0=0, time1=1, value1=1))
""", OMDE['bpf'])
    same_omde("""# custom time comparisons may call back into the same function
f = m.NoInterpolationSegment([(0, 0), (1, 2)])
class Time:
    def __lt__(self, bound):
        f.normalize()
        return 0.5 < bound
RESULT = (f(Time()), f(0.5), f.pairs)
""", OMDE['bpf'])
    same_omde("""# reinitializing the base does not reset a power segment's exponent
f = m.PowerSegment([(0, 0), (1, 1)], exp=3)
m.BPF.__init__(f, [(0, 0), (2, 1)])
RESULT = f(1)
""", OMDE['bpf'])


def test_oscillator_regressions():
    same_omde("""# every wave participates in Function coercion and arithmetic
from athenaCL.libATH.omde.functional import Function, FunctionModel, make_function
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    f = cls()
    RESULT.append((isinstance(f, Function), isinstance(f, FunctionModel),
                   f.instance(0, 1) is f, make_function(f) is f,
                   round((f + 1)(0.125), 12), round((3 - f)(0.125), 12)))
""", OMDE['oscillator'])
    same_omde("""# Python subclasses retain their constructors and inherited operators
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    class Derived(cls):
        def __init__(self, name, a, b, c):
            self.name = name
            super().__init__(frequency=a, phase0=b)
        def __call__(self, t):
            return super().__call__(t) + 7
    f = Derived('mine', 2, 0.25, None)
    RESULT.append((f.name, round(f(0.125), 12), round((f * 2)(0.125), 12)))
""", OMDE['oscillator'])
    same_omde("""# checked division, trig, fmod and power errors, including signed zero
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    for frequency, time in ((0, 0), (-0.0, 0), (1, float('inf')),
                            (1, -float('inf')), (float('inf'), 0),
                            (float('nan'), 0), (1, float('nan')),
                            (None, 0), (2**2000, 0), (2**100, 0.125)):
        try:
            RESULT.append(cls(frequency)(time))
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
for cls in (m.PowerUp, m.PowerDown):
    for exponent in (1024, -1075, None, '2', float('inf'), float('nan')):
        try:
            RESULT.append(cls(exponent=exponent)(0.125))
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
    try:
        RESULT.append(cls(-1, exponent=-1)(0.5))
    except Exception as err:
        RESULT.append((type(err).__name__, str(err)))
""", OMDE['oscillator'])
    same_omde("""# failed time and phase arithmetic must retain earlier assignments
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    for time, phase in (('bad', 0), (0, 'bad'), (0, [])):
        f = cls(1)
        try:
            f(time, f=2, phase0=phase)
            RESULT.append('accepted')
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
        RESULT.append(round(f(0.125, phase0=0), 12))
    f = cls(1, None)
    try:
        f(0)
        RESULT.append('accepted')
    except Exception as err:
        RESULT.append((type(err).__name__, str(err)))
""", OMDE['oscillator'])
    same_omde("""# a rejected frequency preserves the folded period and skips the new phase
RESULT = []
for cls in (m.SawUp, m.SawDown, m.Square, m.Triangle, m.PowerUp, m.PowerDown):
    for invalid in (0, 'bad', 2**2000):
        f = cls(2, 0.125)
        before = f(0.1)
        try:
            f(0.1, f=invalid, phase0=0.75)
            RESULT.append('accepted')
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
        RESULT.append((before, f(0.1)))
""", OMDE['oscillator'])
    same_omde("""# sinusoid frequency updates remain after division fails
RESULT = []
for cls in (m.Sine, m.Cosine):
    f = cls()
    for call in (lambda: f(0, f=0, phase0=0.25), lambda: f(0)):
        try:
            RESULT.append(call())
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
    RESULT.append(f(0, f=2))
""", OMDE['oscillator'])
    same_omde("""# signatures reject duplicate/extra arguments while None defaults remain distinct
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    for call in (lambda: cls(1, frequency=2), lambda: cls(unknown=1),
                 lambda: cls(1, 2, 3, 4), lambda: cls()(0, t=1),
                 lambda: cls()(0, unknown=1)):
        try:
            call()
            RESULT.append('accepted')
        except TypeError:
            RESULT.append('TypeError')
    f = cls(frequency=None, phase0=0.25)
    RESULT.append(round(f(t=0.125, f=2, phase0=None), 12))
""", OMDE['oscillator'])
    same_omde("""# arithmetic callbacks can reenter a wave without a held state lock
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.Triangle):
    f = cls(1)
    class Time:
        def __radd__(self, other):
            f(0.0, f=2)
            return other + 0.125
        def __add__(self, other):
            f(0.0, f=2)
            return 0.125 + other
    RESULT.append((round(f(Time()), 12), round(f(0.125), 12)))
""", OMDE['oscillator'])
    same_omde("""# reinitialization during arithmetic yields Python errors, never a Rust panic
RESULT = []
for cls in (m.Sine, m.SawUp):
    f = cls()
    class Time:
        def __add__(self, other):
            f.__init__(frequency=None)
            return 0.0
        def __radd__(self, other):
            f.__init__(frequency=None)
            return 0.0
    try:
        RESULT.append(f(Time()))
    except Exception as err:
        RESULT.append((type(err).__name__, str(err)))
""", OMDE['oscillator'])


def test_omde_copy():
    same_omde("""# copy all waves after a frequency update, including their cached periods
import copy
from athenaCL.libATH.omde.miscellaneous import List
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    f = cls(2, 0.125)
    f(0.0625, f=4)
    copies = (copy.copy(f), copy.deepcopy(f), List(f).list[0])
    expected = round(f(0.03), 12)
    f(0.03, f=8)
    RESULT.append([(type(c) is cls, c is not f, round(c(0.03), 12) == expected)
                   for c in copies])
assert all(all(all(row) for row in group) for group in RESULT)
""", OMDE['oscillator'])
    same_omde("""# copy BPF payloads independently, without running constructors
import copy
from athenaCL.libATH.omde.miscellaneous import List
RESULT = []
for cls in (m.BPF, m.LinearSegment, m.PowerSegment,
            m.HalfCosineSegment, m.NoInterpolationSegment):
    f = cls([(0, 10), (1, 20)])
    copies = (copy.copy(f), copy.deepcopy(f), List(f).list[0])
    f.normalize()
    RESULT.append([(type(c) is cls, c is not f, c(-1), c.pairs) for c in copies])
f = m.PowerSegment([(0, 10), (1, 20)], periodic=True, exp=3)
f.normalize()
c = copy.deepcopy(f)
RESULT.append((c(1.5), c.pairs))
""", OMDE['bpf'])
    same_omde("""# subclass state, slots, native/attribute aliases and cycles share one memo
import copy
class Frequency:
    def __init__(self): self.value = 2
    def __rtruediv__(self, x): return x / self.value
    def __rmul__(self, x): return x * self.value
class Derived(m.Sine):
    def __init__(self, required):
        self.shared = Frequency()
        self.node = {'owner': self}
        super().__init__(self.shared)
class Slotted(Derived):
    __slots__ = ('slot',)
f = Slotted('required')
f.slot = f.node
c = copy.deepcopy(f)
s = copy.copy(f)
c.shared.value = 4
RESULT = (type(c) is Slotted, c.node['owner'] is c, c.slot is c.node,
          c.shared is not f.shared, c(0.0625), round(f(0.0625), 12),
          s.shared is f.shared, s.node is f.node, s.slot is f.slot)
assert RESULT[:4] == (True, True, True, True)
assert RESULT[4] == 1.0
""", OMDE['oscillator'])
    same_omde("""# deepcopy a BPF with a native exponent aliased by a subclass attribute
import copy
class Exponent:
    value = 2
    def __eq__(self, x): return self.value == x
    def __gt__(self, x): return self.value > x
    def __radd__(self, x): return x + self.value
class Derived(m.PowerSegment):
    def __init__(self, required):
        self.shared = Exponent()
        self.owner = self
        super().__init__([(0, 0), (1, 1)], exp=self.shared)
f = Derived('required')
c = copy.deepcopy(f)
c.shared.value = 3
RESULT = (type(c) is Derived, c.owner is c, c.shared is not f.shared, c(0.5), f(0.5))
assert RESULT == (True, True, True, 0.0625, 0.125)
""", OMDE['bpf'])


def test_omde_finalizers():
    same_omde("""# dropping an old frequency or phase must allow a reentrant call
RESULT = []
for cls in (m.Sine, m.Cosine):
    events = []
    class Frequency:
        def __del__(self):
            events.append(round(wave(0.125, f=1.0), 12))
    wave = cls(Frequency())
    value = wave(0.125, f=2.0)
    RESULT.append((round(value, 12), events))
    assert len(events) == 1
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    events = []
    class Phase:
        def __del__(self):
            events.append(round(wave(0.125), 12))
    wave = cls(2, Phase())
    value = wave(0.125, phase0=0.0)
    RESULT.append((round(value, 12), events))
    assert len(events) == 1
""", OMDE['oscillator'])
    same_omde("""# reinitializing releases old fields outside the lock, in assignment order
RESULT = []
for cls in (m.Sine, m.Cosine, m.SawUp, m.SawDown, m.Square,
            m.Triangle, m.PowerUp, m.PowerDown):
    events = []
    class Frequency:
        def __del__(self):
            events.append(round(wave(0.125), 12))
    wave = cls(Frequency(), 0.25)
    wave.__init__(2, 0.0)
    RESULT.append((events, round(wave(0.125), 12)))
    assert len(events) == 1
""", OMDE['oscillator'])
    same_omde("""# replacing a Python-valued period can run a reentrant finalizer
events = []
class Period(float):
    def __del__(self): events.append(round(wave(0.125, f=1.0), 12))
class Frequency:
    def __rtruediv__(self, x): return Period(0.5)
wave = m.SawUp()
wave(0.0, f=Frequency())
RESULT = (wave(0.125, f=4.0), events)
assert len(events) == 1
""", OMDE['oscillator'])
    same_omde("""# an old exponent finalizer sees the pairs before BPF reinitialization
events = []
class Exponent(float):
    def __del__(self):
        curve.normalize()
        events.append(curve.pairs)
curve = m.PowerSegment([(0, 10), (1, 20)], exp=Exponent(2))
curve.__init__([(0, 30), (1, 50)], exp=1)
RESULT = (events, curve.pairs, curve(0.5))
assert events == [[(0.0, 0.0), (1.0, 1.0)]]
""", OMDE['bpf'])
    same_omde("""# replacing the complete BPF state can finalize a periodic flag
events = []
class Periodic:
    def __del__(self):
        curve.normalize()
        events.append(curve.pairs)
curve = m.LinearSegment([(0, 10), (1, 20)], periodic=Periodic())
curve.__init__([(0, 30), (1, 50)])
RESULT = (events, curve.pairs, curve(0.5))
assert len(events) == 1
""", OMDE['bpf'])


def test_omde_initializer_arguments():
    same_omde("""# the original pairs argument stays alive until the new BPF state is installed
RESULT = []
for cls in (m.BPF, m.LinearSegment, m.PowerSegment,
            m.HalfCosineSegment, m.NoInterpolationSegment):
    for direct_base in (False, True):
        events = []
        class Pairs(list):
            def __del__(self):
                events.append(curve.pairs)
                curve.normalize()
        curve = cls([(0, 10), (1, 20)])
        if direct_base:
            m.BPF.__init__(curve, Pairs([(0, 30), (1, 50)]))
        else:
            curve.__init__(Pairs([(0, 30), (1, 50)]))
        RESULT.append((events, curve.pairs, curve(-1), curve(2)))
        assert events == [[(0.0, 30.0), (1.0, 50.0)]]
        assert curve.pairs == [(0.0, 0.0), (1.0, 1.0)]
        if cls is m.LinearSegment:
            assert curve(0.5) == 0.5
""", OMDE['bpf'])
    same_omde("""# pairs finalizers retain mutations made after BPF initialization
RESULT = []
for cls in (m.BPF, m.LinearSegment, m.PowerSegment,
            m.HalfCosineSegment, m.NoInterpolationSegment):
    events = []
    class Pairs(list):
        def __del__(self):
            events.append(curve.pairs)
            curve.__init__([(0, 70), (2, 90)], periodic=True)
    curve = cls([(0, 10), (1, 20)])
    curve.__init__(Pairs([(0, 30), (1, 50)]))
    RESULT.append((events, curve.pairs))
    assert events == [[(0.0, 30.0), (1.0, 50.0)]]
    assert curve.pairs == [(0.0, 70.0), (2.0, 90.0)]
""", OMDE['bpf'])
    same_omde("""# the original keyword arguments survive reentrant pair conversion
events = []
class Exponent(float):
    def __del__(self):
        events.append(curve.pairs)
        curve.__init__([(0, 70), (1, 90)], exp=3)
class Coordinate:
    def __float__(self):
        curve.__init__([(0, 10), (1, 20)], exp=1)
        return 0.0
curve = m.PowerSegment([(0, 0), (1, 1)])
curve.__init__([(Coordinate(), 30), (1, 50)], exp=Exponent(2))
RESULT = (events, curve.pairs, curve(0.5))
assert RESULT == ([[(0.0, 30.0), (1.0, 50.0)]], [(0.0, 70.0), (1.0, 90.0)], 71.25)
""", OMDE['bpf'])
    same_omde("""# temporary exponent finalizers run after the transformed exponent is assigned
RESULT = []
for cls, base in ((m.PowerUp, 0.25), (m.PowerDown, 0.75)):
    events = []
    class Exponent:
        def __float__(self): return 2.0
        def __del__(self):
            events.append(wave(0.125))
            wave.__init__(frequency=2.0, exponent=3.0)
    wave = cls(2.0, exponent=0.0)
    wave.__init__(frequency=2.0, exponent=Exponent())
    RESULT.append((events, wave(0.125)))
    assert events == [base ** 4] and wave(0.125) == base ** 8
""", OMDE['oscillator'])
    same_omde("""# frequency and phase arguments survive reentrant exponent conversion
RESULT = []
for cls, base in ((m.PowerUp, 0.25), (m.PowerDown, 0.75)):
    for argument in ('frequency', 'phase0'):
        events = []
        class Argument(float):
            def __del__(self):
                events.append(wave(0.125))
                wave.__init__(frequency=2.0, exponent=3.0)
        class Exponent:
            def __float__(self):
                wave.__init__(frequency=2.0, exponent=0.0)
                return 2.0
        wave = cls(2.0)
        if argument == 'frequency':
            wave.__init__(frequency=Argument(2.0), exponent=Exponent())
        else:
            wave.__init__(frequency=2.0, phase0=Argument(0.0), exponent=Exponent())
        RESULT.append((events, wave(0.125)))
        assert events == [base ** 4] and wave(0.125) == base ** 8
""", OMDE['oscillator'])


def test_omde_mutating_callbacks():
    same_omde("""# the loop reads the points after the first comparison callback
curve = m.LinearSegment([(0, 10), (1, 20)])
class Time:
    def __lt__(self, other):
        curve.normalize()
        return 0.5 < other
    def __sub__(self, other): return 0.5 - other
RESULT = (curve(Time()), curve.pairs)
assert RESULT[0] == 0.5
""", OMDE['bpf'])
    same_omde("""# periodic truth and wrapping callbacks can replace points and bounds
RESULT = []
class Periodic:
    def __bool__(self):
        curve.normalize()
        return True
curve = m.LinearSegment([(0, 10), (1, 20)], periodic=Periodic())
RESULT.append(curve(1.5))
curve = m.LinearSegment([(0, 10), (1, 20)], periodic=True)
class Time:
    def __lt__(self, other):
        curve.__init__([(0, 10), (2, 30)], periodic=True)
        return -0.5 < other
    def __add__(self, other): return -0.5 + other
RESULT.append(curve(Time()))
assert RESULT == [0.5, 25.0]
""", OMDE['bpf'])
    same_omde("""# a loop keeps its old iterator but checks the current pairs' length
curve = m.LinearSegment([(0, 10), (1, 20)])
class Time:
    calls = 0
    def __lt__(self, other):
        self.calls += 1
        if self.calls == 2:
            curve.__init__([(0, 30), (1, 40), (2, 50)])
        return 2.0 < other
    def __sub__(self, other): return 2.0 - other
try:
    RESULT = curve(Time())
except Exception as err:
    RESULT = (type(err).__name__, str(err))
assert RESULT[0] == 'ZeroDivisionError'
""", OMDE['bpf'])
    same_omde("""# failed power reinitialization updates plain fields but keeps the old exponent
RESULT = []
for cls in (m.PowerUp, m.PowerDown):
    for invalid in (1024, None, 'bad'):
        wave = cls(1, 0.0, exponent=2)
        wave(0.0, f=8)
        try:
            wave.__init__(frequency=2, phase0=0.25, exponent=invalid)
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
        RESULT.append(wave(0.125))
        assert RESULT[-1] == 0.0625
""", OMDE['oscillator'])


def test_omde_read_boundaries():
    same_omde("""# a replaced phase finalizes before the current folded sample is calculated
RESULT = []
for cls, expected in ((m.SawUp, 0.625), (m.SawDown, 0.375), (m.Square, 0.0),
                      (m.Triangle, 0.75), (m.PowerUp, 0.625), (m.PowerDown, 0.375)):
    events = []
    class Phase:
        def __del__(self):
            events.append(wave(0.0, phase0=0.5))
    wave = cls(1.0, Phase())
    value = wave(0.125, phase0=0.0)
    RESULT.append((value, events, wave(0.125)))
    assert value == expected and len(events) == 1
""", OMDE['oscillator'])
    same_omde("""# each exponent access observes reinitialization by earlier comparisons
RESULT = []
for operation in ('eq', 'gt'):
    for replacement in (3, -3):
        class Exponent(float):
            def __eq__(self, other):
                if operation == 'eq':
                    curve.__init__([(0, 0), (1, 1)], exp=replacement)
                return False
            def __gt__(self, other):
                if operation == 'gt':
                    curve.__init__([(0, 0), (1, 1)], exp=replacement)
                return True
        curve = m.PowerSegment([(0, 0), (1, 1)], exp=Exponent(1))
        RESULT.append(curve(0.5))
assert RESULT[0] == 0.0625
""", OMDE['bpf'])
    same_omde("""# subtraction for a descending power base precedes the exponent read
class Ratio:
    def __rsub__(self, other):
        curve.__init__([(0, 1), (1, 0)], exp=3)
        return 0.5
class Time:
    def __sub__(self, other): return self
    def __truediv__(self, other): return Ratio()
curve = m.PowerSegment([(0, 1), (1, 0)], exp=1)
RESULT = curve.interpolate(Time(), 0, 1, 1, 0)
assert RESULT == 0.0625
""", OMDE['bpf'])


def test_oscillator_callback_regressions():
    same_omde("""# replacing phase during time arithmetic finalizes it before the next operation
RESULT = []
for cls, expected in ((m.Sine, 0.5), (m.Cosine, 0.0), (m.SawUp, 0.5),
                      (m.SawDown, 0.5), (m.Square, 0.0), (m.Triangle, 1.0),
                      (m.PowerUp, 0.5), (m.PowerDown, 0.5)):
    events = []
    class Phase:
        def __mul__(self, value): return 0.0
        def __rmul__(self, value): return 0.0
        def __del__(self):
            events.append(round(wave(0.0, f=4.0), 12))
    class Time:
        def __add__(self, shift):
            wave(0.0, phase0=0.0)
            return 0.375
        def __radd__(self, shift): return self.__add__(shift)
    wave = cls(2.0, Phase())
    value = round(wave(Time()), 12)
    RESULT.append((value, events, round(wave(0.125), 12)))
    assert value == expected and len(events) == 1
""", OMDE['oscillator'])
    same_omde("""# an intermediate shift is released as soon as its addition finishes
RESULT = []
for cls, expected in ((m.Sine, 0.5), (m.Cosine, 0.0), (m.SawUp, 0.5),
                      (m.SawDown, 0.5), (m.Square, 0.0), (m.Triangle, 1.0),
                      (m.PowerUp, 0.5), (m.PowerDown, 0.5)):
    events = []
    class Shift:
        def __add__(self, value): return value
        def __radd__(self, value): return value
        def __del__(self):
            events.append(round(wave(0.0, f=4.0, phase0=0.0), 12))
    class Phase:
        def __mul__(self, value): return Shift()
        def __rmul__(self, value): return Shift()
    wave = cls(2.0, Phase())
    value = round(wave(0.375), 12)
    RESULT.append((value, events))
    assert value == expected and len(events) == 1
""", OMDE['oscillator'])
    same_omde("""# rebinding folded time releases it, but frequency arguments live through sampling
RESULT = []
for cls, expected in ((m.SawUp, 0.5), (m.SawDown, 0.5), (m.Square, 0.0),
                      (m.Triangle, 1.0), (m.PowerUp, 0.5), (m.PowerDown, 0.5)):
    events = []
    class Time:
        def __add__(self, shift): return 0.375
        def __del__(self): events.append(wave(0.0, f=4.0))
    wave = cls(2.0)
    value = wave(Time())
    RESULT.append((value, events))
    assert value == expected and len(events) == 1
events = []
class Frequency:
    def __rtruediv__(self, value): return 0.5
    def __del__(self): events.append(wave(0.0, f=4.0))
wave = m.SawUp()
value = wave(0.125, f=Frequency())
RESULT.append((value, events, wave(0.125)))
assert value == 0.25 and len(events) == 1
""", OMDE['oscillator'])
    same_omde("""# a None or equality-overloaded period falls back to the constructor frequency
RESULT = []
for cls, expected in ((m.SawUp, 0.25), (m.SawDown, 0.75), (m.Square, 1.0),
                      (m.Triangle, 0.5), (m.PowerUp, 0.25), (m.PowerDown, 0.75)):
    for kind in ('none', 'equal', 'reenter'):
        events = []
        class Period(float):
            def __eq__(self, other):
                if other is None:
                    events.append(kind)
                    if kind == 'reenter': wave.__init__(frequency=2.0)
                    return True
                return float.__eq__(self, other)
        class Frequency:
            def __rtruediv__(self, value):
                return None if kind == 'none' else Period(1.0)
        wave = cls(1.0 if kind == 'reenter' else 2.0)
        value = wave(0.125, f=Frequency())
        RESULT.append((value, events, wave(0.125)))
        assert value == expected
        assert events == ([] if kind == 'none' else [kind])
""", OMDE['oscillator'])
    same_omde("""# Triangle repeats overloaded half-period arithmetic on both branches
RESULT = []
for time, expected, count in ((0.125, 0.25, 2), (0.375, 1.25, 3)):
    calls = []
    class Period(float):
        def __mul__(self, value):
            if value == 0.5:
                calls.append(value)
                return 0.25 if len(calls) == 1 else 0.5
            return float(self) * value
    class Frequency:
        def __rtruediv__(self, value): return Period(0.5)
    value = m.Triangle()(time, f=Frequency())
    RESULT.append((value, calls))
    assert value == expected and len(calls) == count
""", OMDE['oscillator'])
    same_omde("""# Triangle rereads the period after each reentrant half-period multiplication
RESULT = []
for time, expected in ((0.125, 0.25), (0.375, 1.25)):
    calls = []
    class Period(float):
        def __mul__(self, value):
            if value == 0.5:
                calls.append(value)
                wave(0.0, f=1.0)
            return float(self) * value
    class Frequency:
        def __rtruediv__(self, value): return Period(0.5)
    wave = m.Triangle()
    value = wave(time, f=Frequency())
    RESULT.append((value, calls, wave(0.125)))
    assert value == expected and len(calls) == 1
""", OMDE['oscillator'])


def test_bpf_failed_initialization():
    same_omde("""# validation errors install pairs, conversion errors leave them unchanged
import copy
def outcome(call):
    try: return call()
    except Exception as err: return (type(err).__name__, str(err))
def broken_pairs():
    yield (0, 99)
    raise ValueError('iteration failed')
RESULT = []
for cls in (m.BPF, m.LinearSegment, m.PowerSegment,
            m.HalfCosineSegment, m.NoInterpolationSegment):
    for pairs in ([], [(0, 99)], [(1, 30), (0, 50)],
                  [(0, 99), ('bad', 50)], [(0, 99), (1,)], broken_pairs()):
        curve = cls([(0, 10), (1, 20)])
        error = outcome(lambda: curve.__init__(pairs))
        RESULT.append((error, curve.pairs, outcome(lambda: curve(-1)),
                       outcome(lambda: curve(0.5)), outcome(lambda: curve(2))))
        for copied in (copy.copy(curve), copy.deepcopy(curve)):
            assert copied.pairs == curve.pairs
            assert outcome(lambda: copied(0.5)) == outcome(lambda: curve(0.5))
curve = m.LinearSegment([(0, 10), (1, 20)])
outcome(lambda: curve.__init__([(0, 99)]))
assert curve.pairs == [(0.0, 99.0)] and curve(-1) == 99.0
""", OMDE['bpf'])
    same_omde("""# invalid reinitialization preserves the previous periodic flag and bounds
import copy
def outcome(call):
    try: return call()
    except Exception as err: return (type(err).__name__, str(err))
RESULT = []
for old_periodic in (False, True):
    for pairs in ([], [(0, 99)], [(2, 30), (0, 50)]):
        curve = m.LinearSegment([(0, 10), (1, 20)], periodic=old_periodic)
        RESULT.append(outcome(lambda: curve.__init__(pairs, periodic=not old_periodic)))
        for current in (curve, copy.deepcopy(curve)):
            RESULT.append((current.pairs, [outcome(lambda: current(t)) for t in (-0.5, 0.5, 1.5)]))
""", OMDE['bpf'])
    same_omde("""# a subclass can retain partially initialized pairs and the power exponent
import copy
RESULT = []
for pairs in ([], [(0, 99)], [(1, 30), (0, 50)]):
    class Partial(m.PowerSegment):
        def __init__(self):
            try: super().__init__(pairs, exp=3)
            except ValueError: pass
    curve = Partial()
    for current in (curve, copy.copy(curve), copy.deepcopy(curve)):
        RESULT.append((current.pairs, current.interpolate(0.5, 0, 0, 1, 1)))
        try:
            current.normalize()
            RESULT.append(current.pairs)
        except Exception as err:
            RESULT.append((type(err).__name__, str(err)))
""", OMDE['bpf'])




# Script both implementations at their common seam; restore even when a block fails.
SCRIPTED = """
class Scripted:
    def __init__(self, draws):
        self.draws = list(draws)
        self.count = 0
    def random(self):
        self.count += 1
        return self.draws.pop(0)

saved = []
def routed(texture_draws, parameter_draws):
    textures, parameters = Scripted(texture_draws), Scripted(parameter_draws)
    saved.append((m._the_same, m.random))
    m._the_same, m.random = textures, parameters.random
    return textures, parameters

def restored():
    m._the_same, m.random = saved.pop()
"""


def scripted(body):
    """Unwind every nested route, including when an unexpected error escapes."""
    import textwrap
    return (SCRIPTED + "\ntry:\n" + textwrap.indent(body, '    ')
            + "\nfinally:\n    while saved: restored()\n")


def test_rand():
    """The random module — stage two, the final planned backend migration: the port's
    draw source is deliberately new, so raw sequences do not compare against the
    reference's MT19937. Instead identical scripted uniforms feed both sides'
    distributions — results and draw consumption compared exactly, the rejection
    boundaries and parameter evaluation order included — beside the class shapes, the
    deepcopy contract, and the seeding seam."""
    import itertools
    _rand_label = itertools.count()

    def rand_omde(source):
        same_omde(source, OMDE['rand'], 'rand block %d' % next(_rand_label))

    # the class shapes: every generator and function in the framework's hierarchy,
    # the composition the operators give, and the call signatures the reference signed
    rand_omde("""from athenaCL.libATH.omde.functional import Generator, Function
generators = (m.UniformRandom(), m.LinearRandom(), m.InverseLinearRandom(),
              m.TriangularRandom(), m.InverseTriangularRandom())
functions = (m.ExponentialRandom(), m.ExponentialRandom(0.7),
             m.InverseExponentialRandom(1.0), m.BilateralExponentialRandom(2.0),
             m.GaussRandom(), m.GaussRandom(0.2, 0.2), m.CauchyRandom(0.5, 0.2),
             m.BetaRandom(0.2, 0.2), m.BetaRandom(0.1, 0.3))
weibull = m.WeibullRandom(0.5, 3.0)
combined = m.ExponentialRandom(1.0) + 1
adapted = m.UniformRandom() + 1
RESULT = ([isinstance(g, Generator) for g in generators],
          [isinstance(f, Function) for f in functions],
          isinstance(weibull, Generator),
          isinstance(combined, Function), 0 <= combined(5.0),
          type(adapted).__name__)
""")
    # the call signatures: generators take nothing, functions and the Weibull generator
    # take the time — error kinds compared, not the machinery's own messages
    rand_omde("""def kind(callable_):
    try:
        callable_()
        return 'no error'
    except TypeError:
        return 'TypeError'
RESULT = (kind(m.UniformRandom()), kind(lambda: m.ExponentialRandom(1.0)()),
          kind(lambda: m.WeibullRandom(0.5, 2.0)()))
""")
    # scripted draws feed both sides' sources: the reference's shared instance and the
    # module alias, the port's bridge streams
    rand_omde(scripted("""
textures, parameters = routed([0.3, 0.6, 0.2, 0.9, 0.4], [])
uniform = m.UniformRandom()()
linear = m.LinearRandom()()
inverse = m.InverseLinearRandom()()
RESULT = (uniform, linear, inverse, textures.count)
"""))
    # the triangular pair walk: a rejected pair, then an accepted one
    rand_omde(scripted("""
textures, parameters = routed([0.2, 0.5, 0.4, 0.1], [])
triangular = m.TriangularRandom()()
first = (triangular, textures.count)

textures, parameters = routed([0.2, 0.5], [])
inverse_triangular = m.InverseTriangularRandom()()
RESULT = (first, inverse_triangular, textures.count)
"""))
    # the exponential boundary: zero and 1e-7 itself are rejected, the next draw taken
    rand_omde(scripted("""
textures, parameters = routed([0, 1e-7, 0.4], [])
value = m.ExponentialRandom(2.0)(5.0)
first = (value, -__import__('math').log(0.4) / 2.0, textures.count)

textures, parameters = routed([0.4], [])
inverse = m.InverseExponentialRandom(2.0)(5.0)
RESULT = (first, inverse, 1.0 - -__import__('math').log(0.4) / 2.0, textures.count)
"""))
    # the bilateral branch: both sides of the half, the exponential's draw before the
    # branch's
    rand_omde(scripted("""
textures, parameters = routed([0.4, 0.6], [])
upper = m.BilateralExponentialRandom(2.0)(5.0)
restored()
textures, parameters = routed([0.4, 0.3], [])
lower = m.BilateralExponentialRandom(2.0)(5.0)
RESULT = (upper, lower, textures.count)
"""))
    # the Cauchy singularity at exactly 0.5, rejected; the tangent within range after
    rand_omde(scripted("""
textures, parameters = routed([0.5, 0.25], [])
value = m.CauchyRandom(0.1, 0.5)(5.0)
RESULT = (value, 0.1 * __import__('math').tan(0.25 * __import__('math').pi) + 0.5,
          textures.count)
"""))
    # the Weibull draw, from its generator-shaped call
    rand_omde(scripted("""
textures, parameters = routed([0.7], [])
value = m.WeibullRandom(0.5, 2.0)(5.0)
RESULT = (value, 0.5 * (-__import__('math').log(0.7)) ** (1.0 / 2.0), textures.count)
"""))
    # the beta branch draw before the two exponential draws, the second rate the
    # reciprocal
    rand_omde(scripted("""
textures, parameters = routed([0.6, 0.4, 0.3], [])
value = m.BetaRandom(2.0, 4.0)(5.0)
y = -__import__('math').log(0.4) / 2.0
z = -__import__('math').log(0.3) / 0.25
RESULT = (value, 1.0 - z / (y + z), textures.count)
"""))
    # the Gauss pair from the parameters stream: the first call draws two, the cached
    # call none, the cached spare scaled by the later call's own mu and sigma
    rand_omde(scripted("""
import math
textures, parameters = routed([], [0.2, 0.9])
rng = m.GaussRandom(0.5, 0.1)
first = rng(1.0)
second = rng(2.0)
x2pi = 0.2 * math.pi * 2
g2rad = math.sqrt(-2.0 * math.log(1.0 - 0.9))
RESULT = (first, 0.5 + math.cos(x2pi) * g2rad * 0.1,
          second, 0.5 + math.sin(2 * math.pi * 0.2) * g2rad * 0.1,
          parameters.count)
"""))
    # the parameters evaluate once per call, in the reference's order, before any draw
    rand_omde(scripted("""
from athenaCL.libATH.omde.functional import Function
log = []
class Logged(Function):
    def __init__(self, name, value):
        self.name, self.value = name, value
    def __call__(self, t):
        log.append(self.name)
        return self.value

textures, parameters = routed([0.5, 0.25], [0.2, 0.9])
cauchy = m.CauchyRandom(Logged('alpha', 0.1), Logged('mu', 0.5))
gauss = m.GaussRandom(Logged('mu', 0.5), Logged('sigma', 0.1))
cauchy(1.0)
gauss(1.0)
gauss(2.0)
RESULT = list(log)
"""))
    # the Gauss pair's arithmetic is bit-identical: the reference's and the port's
    # values agree exactly through the platform's own math
    rand_omde(scripted("""
textures, parameters = routed([], [0.2, 0.9, 0.6, 0.1])
first = m.GaussRandom(0.5, 0.1)(1.0)
fresh = m.GaussRandom(0.3, 0.2)(1.0)
RESULT = (repr(first), repr(fresh))
"""))
    # the deepcopy contract: a copy snapshots the draw source, drawing the same future
    # sequence independently; shared references in one graph stay shared
    rand_omde("""import copy
m.UniformRNG().seed(7)
a = m.UniformRandom()
x = a()
c = copy.deepcopy(a)
y = c()
z = a()
shared = m.LinearRandom()
pair = [shared, shared]
copied = copy.deepcopy(pair)
RESULT = (x != z, y == z, c is not a, copied[0] is copied[1])
""")
    # the Gauss spare travels with a deep copy: the copy's first call consumes nothing
    # and answers with its own parameters
    rand_omde(scripted("""
import copy
textures, parameters = routed([], [0.2, 0.9])
rng = m.GaussRandom(0.5, 0.1)
first = rng(1.0)
copied = copy.deepcopy(rng)
second = copied(3.0)
RESULT = (parameters.count, repr(second))
"""))
    # reseeding leaves a pending Gauss spare standing: the next call answers from the
    # cache, not the reseeded stream, and with the current mu and sigma
    rand_omde(scripted("""
textures, parameters = routed([], [0.2, 0.9])
rng = m.GaussRandom(0.5, 0.1)
first = rng(1.0)
restored()
textures, parameters = routed([], [0.6, 0.1])
second = rng(9.0)
RESULT = (parameters.count, second == first)
"""))
    # the seeding seam: seeding through the shared object twice draws the same
    # sequence, and the Lehmer congruence steps deterministically beside it
    rand_omde("""m.UniformRNG().seed(7)
first = [m.UniformRandom()() for _ in range(3)]
m.UniformRNG().seed(7)
again = [m.UniformRandom()() for _ in range(3)]
lehmer = m._LehmerRNG(1)
steps = [round(lehmer.random(), 9) for _ in range(4)]
lehmer.seed(1)
RESULT = (first == again, first != [], steps == [round(lehmer.random(), 9) for _ in range(4)])
""")


def test_rand_contracts():
    pair = OMDE['rand']
    same_omde(scripted("""# helpers expose the original keyword signatures and consumption
textures, parameters = routed([0.0, 1e-7, 0.5, 0.4, 0.3, 0.7], [0.2, 0.9])
expo = m._ExpovariateRNG().random(lambd=2)
beta = m._BetavariateRNG().random(alpha=2, beta=4)
weibull = m._WeibullvariateRNG().random(alpha=0.5, beta=2)
gauss = m._GaussRNG()
RESULT = (expo, beta, weibull, gauss.random(mu=0.5, sigma=0.1),
          gauss.random(mu=0.3, sigma=0.2), textures.count, parameters.count)
"""), pair)
    same_omde(scripted("""# forced outer rejections and both triangular halves
RESULT = []
cases = [('TriangularRandom', (), [0.1, 0.9, 0.8, 0.1, 0.8, 0.9]),
         ('InverseTriangularRandom', (), [0.4, 0.1, 0.6, 0.9, 0.6, 0.1]),
         ('ExponentialRandom', (1.0,), [0.1, 0.9]),
         ('InverseExponentialRandom', (1.0,), [0.1, 0.9]),
         ('BilateralExponentialRandom', (1.0,), [0.1, 0.9, 0.5]),
         ('CauchyRandom', (0.1, 0.5), [0.5, 0.49, 0.75]),
         ('WeibullRandom', (1.0, 2.0), [0.01, 0.9])]
for name, args, draws in cases:
    textures, parameters = routed(draws + [0.123], [])
    f = getattr(m, name)(*args)
    value = f(t=0) if args else f()
    RESULT.append((name, value, textures.count, textures.random()))
    restored()
"""), pair)
    same_omde(scripted("""# acceptance of exact endpoints and the exp threshold's next float
import math
RESULT = []
for name, args, draws in [('_ExpovariateRNG', (2,), [math.nextafter(1e-7, 0), 1e-7, math.nextafter(1e-7, 1)]),
                         ('_WeibullvariateRNG', (0.5, 2), [1.0]),
                         ('_BetavariateRNG', (2, 4), [1.0, 0.5])]:
    textures, parameters = routed(draws, [])
    RESULT.append((getattr(m, name)().random(*args), textures.count))
    restored()
for mu in (0, 1):
    textures, parameters = routed([], [0, 0])
    RESULT.append((m.GaussRandom(mu, 0)(t=0), parameters.count))
    restored()
"""), pair)
    same_omde(scripted("""# errors preserve draw consumption and exact Python exception messages
RESULT = []
cases = [('m.ExponentialRandom(0)(0)', [0.5], []),
         ('m.InverseExponentialRandom(-0.0)(0)', [0.5], []),
         ('m.BetaRandom(2, 0)(0)', [0.2, 0.5], []),
         ('m._BetavariateRNG().random(2, 4)', [1.0, 1.0], []),
         ('m.WeibullRandom(0.5, 2)(0)', [0.0], []),
         ('m.WeibullRandom(0.5, 0)(0)', [0.5], []),
         ('m.ExponentialRandom(None)(0)', [0.5], []),
         ('m.CauchyRandom(None)(0)', [0.25], []),
         ('m.GaussRandom(None)(0)', [], [0.2, 0.9]),
         ('m._GaussRNG().random(0, 1)', [], [0.2, 1.0])]
for source, td, pd in cases:
    textures, parameters = routed(td, pd)
    try: eval(source)
    except Exception as err:
        RESULT.append((type(err).__name__, str(err), textures.count, parameters.count))
    else: raise AssertionError('expected failure: ' + source)
    restored()
"""), pair)
    same_omde(scripted("""# parameter functions evaluate once despite rejection, in source order
from athenaCL.libATH.omde.functional import Function
log = []
class Parameter(Function):
    def __init__(self, name, value): self.name, self.value = name, value
    def __call__(self, t):
        log.append((self.name, t))
        return self.value
textures, parameters = routed([0.1, 0.9, 0.1, 0.9, 0.5, 0.49, 0.25,
                              0.2, 0.4, 0.3, 0.01, 0.9], [0.125, 0.999, 0, 0])
m.ExponentialRandom(Parameter('lambda', 1))(1)
m.BilateralExponentialRandom(Parameter('lambda', 1))(2)
m.CauchyRandom(Parameter('alpha', 0.1), Parameter('mu', 0.5))(3)
m.BetaRandom(Parameter('alpha', 2), Parameter('beta', 4))(4)
m.WeibullRandom(Parameter('alpha', 1), Parameter('beta', 2))(5)
m.GaussRandom(Parameter('mu', 0.5), Parameter('sigma', 1))(6)
RESULT = (log, textures.count, parameters.count)
"""), pair)
    same_omde(scripted("""# numeric protocols and large ints are evaluated at the arithmetic boundary
from athenaCL.libATH.omde.functional import Function
log = []
class Number:
    def __rtruediv__(self, value):
        log.append(('divide', value))
        return value / 2
class Value(Function):
    def __call__(self, t): return Number()
textures, parameters = routed([0.5, 0.5], [])
RESULT = (m.ExponentialRandom(Value())(0), m.ExponentialRandom(2**100)(0), log,
          textures.count)
"""), pair)
    same_omde("""# constructors reject duplicate, unknown and surplus arguments
RESULT = []
for source in ('m.UniformRandom(1)', 'm.LinearRandom(x=1)',
               'm.ExponentialRandom(2, lambd=3)', 'm.ExponentialRandom(nope=2)',
               'm.ExponentialRandom(1, 2)', 'm.GaussRandom(mu=1, typo=2)',
               'm.BetaRandom(1, 2, 3)', 'm.WeibullRandom(alpha=1, typo=2)',
               'm._ExpovariateRNG(1)', 'm._GaussRNG().random(mu=1)',
               'm._LehmerRNG(1, seed=2)', 'm._LehmerRNG(1).seed(1, 2)'):
    try: eval(source)
    except TypeError: RESULT.append('TypeError')
    else: raise AssertionError(source)
""", pair)
    same_omde(scripted("""# permissive new and typed init allow Python constructors and overrides
from athenaCL.libATH.omde.functional import Function, Generator
textures, parameters = routed([0.3, 0.5, 0.4, 0.7, 0.8], [])
class U(m.UniformRandom):
    def __init__(self, name, extra):
        self.name = name
        super().__init__()
class E(m.ExponentialRandom):
    def __init__(self, name, rate, extra):
        self.name = name
        super().__init__(lambd=rate)
class Custom(m.LinearRandom):
    def __call__(self): return 0.25
u, e = U('u', 9), E('e', 2, 9)
RESULT = (u.name, e.name, (3-u)(), (e*2)(0), Custom()(),
          isinstance(u, Generator), isinstance(e, Function), textures.count)
"""), pair)
    same_omde(scripted("""# a copy graph shares a single snapshot; shallow copies share original helpers
import copy
textures, parameters = routed([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], [])
a, b = m.UniformRandom(), m.LinearRandom()
ca, cb = copy.deepcopy([a, b])
values = (ca(), cb(), a(), b())
shallow = copy.copy(a)
RESULT = (values, ca.rng is cb.rng, ca.rng is not a.rng, shallow.rng is a.rng,
          textures.count)
"""), pair)
    same_omde(scripted("""# deepcopy retains subclass type, slots, cycles and cross-field aliases
import copy
class U(m.UniformRandom):
    __slots__ = ('slot',)
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.slot = self.rng
        self.owner = self
textures, parameters = routed([0.1, 0.2], [])
a = U('saved')
c = copy.deepcopy(a)
RESULT = (type(c) is U, c.name, c.owner is c, c.slot is c.rng,
          c.rng is not a.rng, c(), a(), textures.count)
"""), pair)
    same_omde(scripted("""# Gauss shallow copies share the helper; deep copies preserve its pending spare
import copy
from athenaCL.libATH.omde.functional import Function
class TimeMu(Function):
    def __call__(self, t): return t / 10
textures, parameters = routed([], [0.2, 0.9, 0.6, 0.1])
a = m.GaussRandom(TimeMu(), 0.1)
first = a(5)
b = copy.copy(a)
c = copy.deepcopy(a)
RESULT = (b.gaussRNG is a.gaussRNG, c.gaussRNG is not a.gaussRNG,
          b(3), c(3), parameters.count, a(5), parameters.count)
"""), pair)
    same_omde(scripted("""# an arithmetic failure occurs after the Gauss spare is installed
textures, parameters = routed([], [0.2, 0.9])
g = m._GaussRNG()
try: g.random(None, 0.1)
except TypeError: pass
else: raise AssertionError('invalid mu')
RESULT = (g.random(mu=0.3, sigma=0.2), parameters.count, g.next is None)
"""), pair)
    same_omde("""# Lehmer retains integer/float modulo semantics, including arbitrary-width integers
RESULT = []
for args in [(1,), (-3, 97, 13, 2), (7, -97, 13, 2),
             (2**150, 2**151+7, 2**130+5, 11)]:
    r = m._LehmerRNG(*args)
    RESULT.append([r.random() for _ in range(5)])
    r.seed(seed=args[0])
    RESULT.append(r.random())
try: m._LehmerRNG(1, mod=0).random()
except Exception as err: RESULT.append((type(err).__name__, str(err)))
else: raise AssertionError('zero modulus')
""", pair)
    same_omde("""# clock reseeding covers zero, modulus and repeated zero ticks without sleeping
from types import SimpleNamespace
calls = []
ticks = iter([123.0, 123.5, 123.25])
saved_time = m.time
m.time = SimpleNamespace(time=lambda: next(ticks), sleep=lambda t: calls.append(t))
try:
    r = m._LehmerRNG(0, mod=100, mul=3)
    initial = (r._seed, r.random())
    r.seed(100)
    RESULT = (initial, r._seed, r.random(), calls)
finally:
    m.time = saved_time
""", pair)

    same_omde("""# compare full seeded distributions with both algorithms on the new draw source
from athenaCL.libATH import rngBridge
saved = m._the_same, m.random
m._the_same, m.random = rngBridge.textures, rngBridge.parameters.random
try:
    RESULT = []
    for seed in (0, 7, -12345, 2**200):
        for name in ('UniformRandom', 'LinearRandom', 'InverseLinearRandom',
                     'TriangularRandom', 'InverseTriangularRandom', 'ExponentialRandom',
                     'InverseExponentialRandom', 'BilateralExponentialRandom',
                     'GaussRandom', 'CauchyRandom', 'BetaRandom', 'WeibullRandom'):
            rngBridge.textures.seed(seed)
            rngBridge.parameters.seed(seed)
            f = getattr(m, name)()
            timed = name in ('ExponentialRandom', 'InverseExponentialRandom',
                             'BilateralExponentialRandom', 'GaussRandom', 'CauchyRandom',
                             'BetaRandom', 'WeibullRandom')
            values = [f(t=i) if timed else f() for i in range(12)]
            RESULT.append((name, values, rngBridge.textures.random(),
                           rngBridge.parameters.random()))
finally:
    m._the_same, m.random = saved
""", pair)


def test_rand_lifetimes():
    pair = OMDE['rand']
    same_omde("""# accepted uniforms remain alive during distribution arithmetic
from types import SimpleNamespace
RESULT = []
for name in ('ExponentialRandom', 'WeibullRandom'):
    events = []
    class Uniform(float):
        def __del__(self): events.append('uniform finalized')
    class Rate:
        def __rtruediv__(self, other):
            events.append('parameter division')
            return 0.75 if 'uniform finalized' in events else 0.25
    f = getattr(m, name)()
    source = SimpleNamespace(random=lambda: Uniform(0.5))
    if name == 'ExponentialRandom':
        f.expovariateRNG.uniformRNG = source
        f.lambd = lambda t: Rate()
    else:
        f.weibullvariateRNG.uniformRNG = source
        f.beta = lambda t: Rate()
    value = f(0)
    assert events == ['parameter division', 'uniform finalized']
    RESULT.append((name, value, list(events)))
""", pair)
    same_omde("""# Gaussian angle remains alive through cache storage and final arithmetic
events = []
g = m._GaussRNG()
class Angle(float):
    def __del__(self):
        events.append(('angle finalized', g.next is None))
        g.next = None
class Radians(float):
    def __mul__(self, other): return Angle(float(self) * other)
class Uniform(float):
    def __mul__(self, other): return Radians(float(self) * other)
saved = m.random
m.random = iter([Uniform(0.125), 0.2]).__next__
try:
    value = g.random(0, 1)
    assert events == [('angle finalized', False)] and g.next is None
    RESULT = (value, g.next, events)
finally:
    m.random = saved
""", pair)
    same_omde("""# a rejected sample survives until its replacement draw returns
from types import SimpleNamespace
RESULT = []
for name, field in [('ExponentialRandom', 'expovariateRNG'),
                    ('InverseExponentialRandom', 'expovariateRNG'),
                    ('BilateralExponentialRandom', 'expovariateRNG'),
                    ('GaussRandom', 'gaussRNG'), ('WeibullRandom', 'weibullvariateRNG')]:
    events = []
    class Rejected:
        def __lt__(self, other): return False
        def __gt__(self, other): return False
        def __ge__(self, other): return False
        def __rsub__(self, other): return self
        def __del__(self): events.append('finalize')
    class Helper:
        def __init__(self): self.calls = 0
        def random(self, *args):
            self.calls += 1
            events.append('draw')
            return Rejected() if self.calls == 1 else 0.25
    f = getattr(m, name)()
    setattr(f, field, Helper())
    if name == 'BilateralExponentialRandom':
        f.uniformRNG = SimpleNamespace(random=lambda: 0.25)
    value = f(0)
    assert events == ['draw', 'draw', 'finalize']
    RESULT.append((name, value, list(events)))
""", pair)
    same_omde("""# the exponential helper also retains its rejected uniform draw
class Rejected(float):
    def __del__(self): events.append('finalize')
class Source:
    def __init__(self): self.calls = 0
    def random(self):
        self.calls += 1
        events.append('draw')
        return Rejected(0) if self.calls == 1 else 0.5
events = []
f = m._ExpovariateRNG()
f.uniformRNG = Source()
value = f.random(2)
assert events == ['draw', 'draw', 'finalize']
RESULT = (value, events)
""", pair)
    same_omde("""# triangular retries replace a before drawing b, then replace b
RESULT = []
for name, first, second, final in [('TriangularRandom', 0.2, 0.4, (0.4, 0.2)),
                                  ('InverseTriangularRandom', 0.4, 0.1, (0.2, 0.8))]:
    events = []
    class Sample(float):
        def __new__(cls, value, name):
            obj = float.__new__(cls, value)
            obj.name = name
            return obj
        def __del__(self): events.append('finalize ' + self.name)
    class Halved:
        def __truediv__(self, other): return Sample(second, 'b')
    class Source:
        def __init__(self): self.calls = 0
        def random(self):
            self.calls += 1
            events.append('draw %d' % self.calls)
            if self.calls == 1: return Sample(first, 'a')
            if self.calls == 2: return Halved()
            return final[self.calls - 3]
    f = getattr(m, name)()
    f.rng = Source()
    value = f()
    assert events == ['draw 1', 'draw 2', 'draw 3', 'finalize a', 'draw 4', 'finalize b']
    RESULT.append((name, value, list(events)))
""", pair)
    same_omde("""# Cauchy keeps x across outer retries and value until its replacement exists
from athenaCL.libATH.omde.functional import Function
events = []
class Sample(float):
    def __new__(cls, value, name):
        obj = float.__new__(cls, value)
        obj.name = name
        return obj
    def __del__(self): events.append('finalize ' + self.name)
class Rejected:
    def __le__(self, other): return False
    def __del__(self): events.append('finalize value')
class Product:
    def __init__(self, first): self.first = first
    def __add__(self, other): return Rejected() if self.first else 0.25
class Factor:
    def __init__(self): self.calls = 0
    def __mul__(self, other):
        self.calls += 1
        return Product(self.calls == 1)
class Alpha(Function):
    def __call__(self, t): return Factor()
class Source:
    def __init__(self): self.calls = 0
    def random(self):
        self.calls += 1
        events.append('draw %d' % self.calls)
        if self.calls == 1: return Sample(0.49, 'x')
        if self.calls == 2: return Sample(0.5, 'singularity')
        return 0.25
f = m.CauchyRandom(Alpha())
f.uniformRNG = Source()
value = f(0)
assert events == ['draw 1', 'draw 2', 'finalize x', 'draw 3',
                  'finalize singularity', 'finalize value']
RESULT = (value, events)
""", pair)
    same_omde("""# Beta parameters remain alive while the returned value is inverted
from athenaCL.libATH.omde.functional import Function
events = []
class Rate:
    def __rtruediv__(self, other): return Numerator()
    def __del__(self): events.append('rate finalized')
class Numerator:
    def __add__(self, other): return Denominator()
class Denominator:
    def __rtruediv__(self, other): return Value()
class Value:
    def __rsub__(self, other):
        events.append('inversion')
        return 'rate finalized' in events
class Parameter(Function):
    def __call__(self, t): return Rate()
class Source:
    def random(self): return 0.75
f = m.BetaRandom(Parameter(), 2)
f.uniformRNG = Source()
f.betavariateRNG.expovariateRNG.uniformRNG = Source()
value = f(0)
assert value is False and events == ['inversion', 'rate finalized']
RESULT = (value, events)
""", pair)


for test in (test_error, test_permutate, test_quantize, test_chaos, test_functional,
             test_bpf, test_oscillator, test_bpf_regressions, test_oscillator_regressions,
             test_omde_copy, test_omde_finalizers, test_omde_initializer_arguments,
             test_omde_mutating_callbacks,
             test_omde_read_boundaries, test_oscillator_callback_regressions,
             test_bpf_failed_initialization, test_rand, test_rand_contracts,
             test_rand_lifetimes):
    test()

print('%d checks, %d failures' % (checks, len(failures)))
for what in failures:
    print(what)
sys.stdout.flush()
if failures:
    sys.exit(1)
