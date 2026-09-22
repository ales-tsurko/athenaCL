"""Differential parity tests for the modules ported from `pysrc` to Rust.

A ported module keeps its import path — `athenaCL.libATH.error` is the Rust `src/libath/error.rs`
— and its original Python implementation moves to `athenaCL.libATH._pyref`. These tests call the
port and the reference with the same inputs and compare the results, so a port cannot change
behavior unnoticed. The ports restructure rather than transliterate, so a corpus states where a
Python quirk was deliberately not carried over: `interpolate` works in floats where Python kept
its int/float typing, and its results compare by value.

Comparisons are by `repr`, which covers values, their types (int against float, list against
tuple), and ordering. Extend the corpus below as more modules are ported.
"""

import importlib
import sys


PORTED = ['error', 'interpolate', 'permutate']

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


def same_call(name, fn, *args):
    """A function of the port and of the reference must agree, errors included."""
    rust, ref = modules(name)
    what = '%s.%s(%s)' % (name, fn, ', '.join(map(repr, args)))
    found, found_error = outcome(getattr(rust, fn), *args)
    expected, expected_error = outcome(getattr(ref, fn), *args)
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


def test_interpolate():
    """Interpolation: the interval attributes, positions, and discrete values.

    The port works in floats where Python kept its int/float typing, so results compare by
    value, exactly — no tolerance.
    """
    rust, ref = modules('interpolate')

    def same_value(found, expected, what):
        global checks
        checks += 1
        if float(found) != float(expected):
            failures.append('%s: %r != %r' % (what, found, expected))

    def same_values(found, expected, what):
        global checks
        checks += 1
        if [float(v) for v in found] != [float(v) for v in expected]:
            failures.append('%s: %r != %r' % (what, found, expected))

    for a, b in ((3, 21), (21, 3), (-5, 5), (0, 0), (2.5, 7.5), (7.5, 2.5),
                 (-1.5, 3.25), (0, 1), (3, 3), (3, 3.0)):
        found, expected = rust.OneDimensionalLinear(a, b), ref.OneDimensionalLinear(a, b)
        what = 'OneDimensionalLinear(%r, %r)' % (a, b)
        for attr in ('min', 'max', 'span'):
            same_value(getattr(found, attr), getattr(expected, attr), '%s.%s' % (what, attr))
        same(getattr(found, 'flip'), getattr(expected, 'flip'), '%s.flip' % what)
        for unit in (-0.5, 0, 0.25, 1 / 3, 0.5, 1, 1.0, 2):
            same_value(found.pos(unit), expected.pos(unit), '%s.pos(%r)' % (what, unit))
        for steps in (2, 3, 5, 10):
            same_values(found.discrete(steps), expected.discrete(steps),
                        '%s.discrete(%r)' % (what, steps))
            for digits in (-1, 0, 1, 2, 4):
                same_values(found.discrete(steps, digits), expected.discrete(steps, digits),
                            '%s.discrete(%r, %r)' % (what, steps, digits))
        for steps in (1, 0, -3):
            found_v, found_e = outcome(found.discrete, steps)
            expected_v, expected_e = outcome(expected.discrete, steps)
            note(found_v == expected_v and found_e == expected_e,
                 '%s.discrete(%r): %r%s != %r%s' % (what, steps, found_v, found_e,
                                                    expected_v, expected_e))


def test_permutate():
    """Permutations: every function over a spread of item lists and widths."""
    for items in ([3, 4, 5], [8, 3, 267], ['a', 'b', 'c'], [], [7], 'abc', (3, 4)):
        for n in range(len(list(items)) + 2):
            for fn in ('combinations', 'selections', 'uniqueCombinations'):
                same_call('permutate', fn, items, n)
                same_iter_call('permutate', 'x' + fn, items, n)
        same_call('permutate', 'permutations', items)
        same_iter_call('permutate', 'xpermutations', items)

    # the iterator functions are lazy: this walk has 479 million results, and taking the
    # first must not compute the rest
    rust, ref = modules('permutate')
    same(next(rust.xpermutations(list(range(12)))),
         next(ref.xpermutations(list(range(12)))),
         'first of xpermutations of 12 items')


# the ported modules must import before anything else runs
for name in PORTED:
    modules(name)

for test in (test_error, test_interpolate, test_permutate):
    test()

print('%d checks, %d failures' % (checks, len(failures)))
for what in failures:
    print(what)
sys.stdout.flush()
if failures:
    sys.exit(1)
