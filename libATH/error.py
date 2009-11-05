#-----------------------------------------------------------------||||||||||||--
# Name:          error.py
# Purpose:       athenaCL exceptions
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--



# now error.ParameterObjectSyntaxError
class ParameterObjectSyntaxError(SyntaxError):
    def __init__(self, msg=''):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg



# was SyntaxErrorTransition
# now error.TransitionSyntaxError
class TransitionSyntaxError(SyntaxError):
    def __init__(self, msg=''):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg



# was SyntaxErrorAutomataSpecification
# now error.AutomataSpecificationError
class AutomataSpecificationError(SyntaxError):
    def __init__(self, msg=''):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg


# was BadPulseData
# now error.PulseSyntaxError
class PulseSyntaxError(SyntaxError):
    def __init__(self, msg=''):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg


# was BadPitchData
# now error.PitchSyntaxError
class PitchSyntaxError(SyntaxError):
    def __init__(self, msg=''):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg



class ParticleSyntaxError(SyntaxError):
    def __init__(self, msg=''):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg







# was IncompleteArguments
# now error.ArgumentError
class ArgumentError(SyntaxError):
    def __init__(self, msg=''):
        self._msg = msg
        SyntaxError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg




# was CloneError
# now error.CloneError
class CloneError(StandardError):
    def __init__(self, msg=''):
        self._msg = msg
        StandardError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg




# was MultisetInitError, BadSetInput
# now error.MultisetError
class MultisetError(StandardError):
    def __init__(self, msg=''):
        self._msg = msg
        StandardError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg



# was TestBug
# now error.TestError
class TestError(StandardError):
    def __init__(self, msg=''):
        self._msg = msg
        StandardError.__init__(self, "%s" % self._msg)
    
    def __repr__(self):
        return self._msg



