"""In-place dispatch probes, run against a fresh interpreter.

The interpreter quickens binary operations after they execute with numeric operands a few
times, and its quickened fallback drops the in-place operation — `+=` runs as plain `+`
from then on. A reference module already exercised with numbers therefore stops dispatching
__iadd__/__isub__, while the port keeps the language semantics. These probes run here,
before anything warms the frozen reference: cold, it dispatches the in-place operations the
way Python defines them, and the port must agree with it. The main parity corpus cannot hold
these blocks — its own earlier blocks do the warming.
"""

import importlib

modules = (
    'athenaCL.libATH.omde.miscellaneous',
    'athenaCL.libATH._pyref.miscellaneous',
)
results = []
for path in modules:
    m = importlib.import_module(path)
    found = {}

    # __isub__ returns 0.25, __sub__ returns 0.75 — the quantizer's `value -= offset`
    class F(float):
        def __isub__(self, other):
            return F(float(self) - 0.5)

        def __sub__(self, other):
            return F(float(self) - 0.1)

    quantizer = m.Quantizer(F(0.6), 0.25)
    found['quantizer'] = repr(quantizer(0))

    # __iadd__ returns 0, __add__ returns 2 — the swing's `index += step`
    class Idx:
        def __init__(self, v):
            self.v = v

        def __index__(self):
            return self.v

        def __iadd__(self, step):
            return Idx(self.v)

        def __add__(self, step):
            return Idx(self.v + 2)

    walk = m.List(10, 20, 30, mode='swing')
    walk.index = Idx(0)
    first = walk.next()
    try:
        second = walk.next()
        found['swing'] = (repr(first), repr(second), repr(walk.index.v))
    except Exception as err:  # the probes only compare errors these calls raise
        found['swing'] = (repr(first), type(err).__name__)

    # the plain operator's own error kind and message, cold
    class Bare:
        pass

    try:
        m.Accumulator(Bare())(0)
        found['error'] = 'no error'
    except Exception as err:
        found['error'] = '%s: %s' % (type(err).__name__, err)

    results.append(repr(found))

assert results[0] == results[1], 'the fresh in-place probes disagree: %r' % (results,)
# the agreed values must be the in-place ones: __isub__ and __iadd__ dispatched, the
# in-place operation's own error — a warmed reference would give 0.5, 30, and '+' instead
agreed = eval(results[0])
assert agreed['quantizer'] == '0.0', agreed
assert agreed['swing'] == ('10', '10', '0'), agreed
assert '+=' in agreed['error'], agreed
print('fresh in-place dispatch agrees: %s' % results[0])
