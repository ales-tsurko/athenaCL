# -----------------------------------------------------------------||||||||||||--
# Name:          error.py
# Purpose:       athenaCL exceptions
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2007-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import unittest, doctest


# now error.ParameterObjectSyntaxError
class ParameterObjectSyntaxError(SyntaxError):
    def __init__(self, msg=""):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was SyntaxErrorTransition
# now error.TransitionSyntaxError
class TransitionSyntaxError(SyntaxError):
    def __init__(self, msg=""):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was SyntaxErrorAutomataSpecification
# now error.AutomataSpecificationError
class AutomataSpecificationError(SyntaxError):
    def __init__(self, msg=""):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was BadPulseData
# now error.PulseSyntaxError
class PulseSyntaxError(SyntaxError):
    def __init__(self, msg=""):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was BadPitchData
# now error.PitchSyntaxError
class PitchSyntaxError(SyntaxError):
    def __init__(self, msg=""):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


class ParticleSyntaxError(SyntaxError):
    def __init__(self, msg=""):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was IncompleteArguments
# now error.ArgumentError
class ArgumentError(SyntaxError):
    def __init__(self, msg=""):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was CloneError
# now error.CloneError
class CloneError(Exception):
    def __init__(self, msg=""):
        self._msg = msg
        Exception.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was MultisetInitError, BadSetInput
# now error.MultisetError
class MultisetError(Exception):
    def __init__(self, msg=""):
        self._msg = msg
        Exception.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# was TestBug
# now error.TestError
class TestError(Exception):
    """
    >>> a = TestError()
    """

    def __init__(self, msg=""):
        self._msg = msg
        Exception.__init__(self, "%s" % self._msg)

    def __repr__(self):
        return self._msg


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    from athenaCL.test import baseTest

    baseTest.main(Test)
