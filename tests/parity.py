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

# functional ports under its omde path; the reference keeps the flat one
FUNCTIONAL = ('athenaCL.libATH.omde.functional', 'athenaCL.libATH._pyref.functional')

failures = []
checks = 0


def modules(name):
    """The Rust port of a module and its Python reference."""
    return (importlib.import_module('athenaCL.libATH.' + name),
            importlib.import_module('athenaCL.libATH._pyref.' + name))


def note(ok, what):
    """Count a check and record it when it fails."""
    global checks
    checks += 1
    if not ok:
        failures.append(what)


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


def same_functional(source):
    """A source over the module namespace `m` — the port's shim or the reference — must
    agree. The block must set RESULT and must not let an exception escape: expected
    errors are caught inside the block and compared as values, so an unintended raise
    on both sides cannot pass as agreement."""
    found = {}
    for path in FUNCTIONAL:
        module = importlib.import_module(path)
        namespace = {'m': module, 'RESULT': MISSING}
        try:
            exec(source, namespace)
            result = namespace['RESULT']
            if result is MISSING:
                found[path] = (None, 'the block set no RESULT')
            else:
                found[path] = (repr(result), None)
        except Exception as err:
            found[path] = (None, 'the block escaped: %s' % describe(err))
    port, ref = FUNCTIONAL
    value, error = found[port]
    expected, expected_error = found[ref]
    ok = value == expected and error == expected_error and error is None
    note(ok,
         'functional %s: %r%s != %r%s' % (source.splitlines()[0], value, error,
                                          expected, expected_error))


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


for test in (test_error, test_permutate, test_quantize, test_chaos, test_functional):
    test()

print('%d checks, %d failures' % (checks, len(failures)))
for what in failures:
    print(what)
sys.stdout.flush()
if failures:
    sys.exit(1)
