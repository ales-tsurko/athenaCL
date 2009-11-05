#-----------------------------------------------------------------||||||||||||--
# Name:          oscillator.py
# Purpose:       oscillator objects
#
# Authors:       Maurizio Umberto Puxeddu
#                    Christopher Ariza
#
# Copyright:     (c) 2001-2007 Christopher Ariza
# Copyright:     (c) 2000-2001 Maurizio Umberto Puxeddu
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


"""
Oscillating function translated and normalized in the [0,1] range
"""


# for all functioins, frequency can be supplied w/ call method to change
# frequency; otherwise, initially supplied fq is used
# an initial fq can be none

from math import pow, fmod, sin, cos, pi
from athenaCL.libATH.omde.functional import Function

class Sine(Function):
    """
    Sinusoid translated in the [0,1] range
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.phase0 = phase0
    
    def __call__(self, t, f=None):
        if f != None: self.frequency = f
    
        phase = self.phase0 + t * self.frequency
        return (1.0 + sin(2.0 * pi * phase)) / 2.0

class Cosine(Function):
    """
    Cosinusoid translated in the [0,1] range
    """
    def __init__(self, frequency=1.0, phase0=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.phase0 = phase0
    
    def __call__(self, t, f=None):
        if f != None: self.frequency = f      

        phase = self.phase0 + t * self.frequency
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
    
    def __call__(self, t, f=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T
        return t / self.T

class SawDown(Function):
    """
    broken
    """
    def __init__(self, frequency=1.0, ph=0.0):
        Function.__init__(self)
        self.frequency = frequency
        self.T = None # require when called
        self.ph = ph
    
    def __call__(self, t, f=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency

        t += self.T * self.ph
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
    
    def __call__(self, t, f=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency

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
    
    def __call__(self, t, f=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency

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
        self.T = None # require when called
        self.phase0 = phase0
    
    def __call__(self, t, f=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency

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
    
    def __call__(self, t, f=None):
        if f != None: self.T = 1.0 / f
        if self.T == None:
            self.T = 1.0 / self.frequency

        t += self.T * self.phase0
        t = fmod(t, self.T)
        if t < 0: t += self.T
        
        if t < (self.T * .5):
            return t / (self.T * .5)
        else:
            return 1.0 - (t - (self.T * .5))/ (self.T * .5)





if __name__ == '__main__':
    f1 = Sine(1.0)
    f2 = Cosine(1.0)
    f3 = SawUp(1.0)
    f4 = SawDown(1.0)
    f5 = PowerUp(1.0, 0, 1.0)
    f6 = PowerUp(1.0, 0, 2.0)
    f7 = PowerUp(1.0, 0, -1.0)
    f8 = PowerDown(1.0, 0, 1.0)
    f9 = PowerDown(1.0, 0, 2.0)
    f10 = PowerDown(1.0, 0, -1.0)
    f11 = Square(1.0)
    f12 = Triangle(1.0)
    f13 = Sine(1.0, 0.3)
    f14 = Cosine(1.0, 0.3)
    f15 = SawUp(1.0, 0.3)
    f16 = PowerUp(1.0, 0.3, 2.0)
    f17 = PowerDown(1.0, 0.3, 2.0)
    f18 = Square(1.0, 0.3)
    f19 = Triangle(1.0, 0.3)
    
    t = -2.0
    step = 0.01
    for i in range(401):
        #print t, f1(t)
        print t, f1(t), f2(t), f3(t), f4(t), f5(t), f6(t), f7(t), f8(t), f9(t), f10(t), f11(t), f12(t), f13(t), f14(t), f15(t), f16(t), f17(t), f18(t), f19(t)
        t += step
        
    
    # end
