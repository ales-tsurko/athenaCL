"""Check mutating in-place steps before RustPython quickens the Python reference."""

import importlib


class Mutable:
    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        return self.value < other

    def __gt__(self, other):
        return self.value > other

    def __le__(self, other):
        return self.value <= other

    def __iadd__(self, step):
        self.value += step
        return self

    def __repr__(self):
        return 'Mutable(%s)' % self.value


def run(path):
    unit = importlib.import_module(path)
    return repr(unit.unitNormStep(2, Mutable(0), 1, normalized=False))


native = run('athenaCL.libATH.unit')
reference = run('athenaCL.libATH._pyref.unit')
assert native == reference == '[Mutable(2)]', (native, reference)
