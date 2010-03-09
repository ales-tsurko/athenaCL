#-----------------------------------------------------------------||||||||||||--
# Name:          oscillator.py
# Purpose:       oscillator objects
#
# Authors:       Maurizio Umberto Puxeddu
#                    Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# Copyright:     (c) 2000-2001 Maurizio Umberto Puxeddu
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


"""
Oscillating function translated and normalized in the [0,1] range
"""


# for all functioins, frequency can be supplied w/ call method to change
# frequency; otherwise, initially supplied fq is used
# an initial fq can be none


import copy
import unittest, doctest
from math import pow, fmod, sin, cos, pi
from athenaCL.libATH.omde.functional import Function

_MOD = 'valueSingleOmde.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)


class Sine(Function):
    """
    Sinusoid translated in the [0,1] range.
    This means that at t=0 the value is .5

    >>> a = Sine(.5)
    >>> a(0)
    0.5
    >>> a(.5)
    1.0
    >>> a(1.0)
    0.5000...
    >>> a(1.5)
    0.0
    >>> a(2.0)
    0.4999...
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.phase0 = phase0
        self.T = None # require when called
    
    def __call__(self, t, f=None, phase0=None):
        if f != None: 
            self.frequency = f
        if phase0 != None:
            self.phase0 = phase0

        self.T = 1.0 / self.frequency

        phase = ((self.phase0*self.T) + t) * self.frequency
        #environment.printDebug(['phase0:', self.phase0, 'phaseFinal', phase])

        return (1.0 + sin(2.0 * pi * phase)) / 2.0

class Cosine(Function):
    """
    Cosinusoid translated in the [0,1] range

    >>> a = Cosine(.5)
    >>> a(0)
    1.0
    >>> a(.5)
    0.5
    >>> a(1.0)
    0.0
    >>> a(1.5)
    0.499...
    >>> a(2.0)
    1.0
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.phase0 = phase0
    
    def __call__(self, t, f=None, phase0=None):
        if f != None: 
            self.frequency = f      
        if phase0 != None:
            self.phase0 = phase0

        self.T = 1.0 / self.frequency

        phase = ((self.phase0*self.T) + t) * self.frequency
        return (1.0 + cos(2.0 * pi * phase)) / 2.0

class SawUp(Function):
    """
    Saw-up wave translated in the [0,1] range
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.T = None # require when called
        self.phase0 = phase0
    
    def __call__(self, t, f=None, phase0=None):
        if f != None: 
            self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency
        if phase0 != None:
            self.phase0 = phase0

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T
        return t / self.T

class SawDown(Function):
    """
    broken
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.T = None # require when called
        self.phase0 = phase0
    
    def __call__(self, t, f=None, phase0=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency
        if phase0 != None:
            self.phase0 = phase0

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T
        return 1.0 - t / self.T

class PowerUp(Function):
    """
    Power-up wave translated in the [0, 1] range
    """
    def __init__(self, frequency=1.0, phase0=0.0, exponent=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.T = None # require when called
        self.phase0 = phase0
        self.exponent = pow(2.0, exponent)
    
    def __call__(self, t, f=None, phase0=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency
        if phase0 != None:
            self.phase0 = phase0

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T       
        return pow(t / self.T, self.exponent)
          
class PowerDown(Function):
    """
    Power-down wave translated in the [0,1] range
    """
    def __init__(self, frequency=1.0, phase0=0.0, exponent=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.T = None # require when called
        self.phase0 = phase0
        self.exponent = pow(2.0, exponent)
    
    def __call__(self, t, f=None, phase0=None):
        if f != None: 
            self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency
        if phase0 != None:
            self.phase0 = phase0

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T
        return pow(1.0 - t / self.T, self.exponent)

class Square(Function):
    """
    Square wave translated in the [0, 1] range
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        # this is time per period
        self.T = None # require when called
        self.phase0 = phase0
    
    def __call__(self, t, f=None, phase0=None):
        if f != None:
            self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency
        if phase0 != None:
            self.phase0 = phase0

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T
        if t < self.T/2:
            return 1.0
        else:
            return 0.0

class Triangle(Function):
    """
    Trangle oscillator translated in the [0,1] range
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.T = None # require when called
        self.phase0 = phase0

        #self.T = 1.0 / frequency
        #self.T_2 = self.T / 2.0
    
    def __call__(self, t, f=None, phase0=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency
        if phase0 != None:
            self.phase0 = phase0

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T
        
        if t < (self.T * .5):
            return t / (self.T * .5)
        else:
            return 1.0 - (t - (self.T * .5))/ (self.T * .5)


#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)