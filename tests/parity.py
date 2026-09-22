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

for test in (test_error, test_permutate, test_quantize, test_chaos):
    test()

print('%d checks, %d failures' % (checks, len(failures)))
for what in failures:
    print(what)
sys.stdout.flush()
if failures:
    sys.exit(1)
