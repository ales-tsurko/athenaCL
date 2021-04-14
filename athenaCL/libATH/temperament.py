#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          temperament.py
# Purpose:       object definition for temperament objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2003-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import random
import unittest, doctest

from athenaCL.libATH import drawer
from athenaCL.libATH import pitchTools

_MOD = 'temperament.py'
#-----------------------------------------------------------------||||||||||||--

class Temperament:
    "parent class of all temperament classes"

    def __init__(self):
        """
        >>> a = Temperament()
        """
        self.name = None
        self.doc = None

    def __call__(self, psReal):
        """takes a psReal (post trans, post oct) and returns a psReal
        """
        self._splitPitch(psReal) # this will assign local values
        self._translatePitch() # this will perform an operation on local vals
        return self._joinPitch() # this will return a psReal, delete local

    def _splitPitch(self, psReal):
        oct, pc, micro = pitchTools.splitPsReal(psReal) # pc may have micro
        #self.psReal = psReal
        self.oct = oct
        self.pc = pc
        self.micro = micro
    
    def _joinPitch(self):
        # note: joinPsReal will accept pc values tt are not pc:
        # the may be floats, above and below 0-11 range
        psReal = pitchTools.joinPsReal(self.oct, self.pc, self.micro)
        # deleat temporary variables
        del self.oct
        del self.pc
        del self.micro
        #del self.psReal
        return psReal

#-----------------------------------------------------------------||||||||||||--

class TwelveEqual(Temperament):
    def __init__(self):
        """
        >>> a = TwelveEqual()
        """
        Temperament.__init__(self)
        self.name = 'TwelveEqual'
        self.doc = 'Twelve tone equal temperament'
        
    def _translatePitch(self):
        pass # do nothing

class Pythagorean(Temperament):
    def __init__(self):
        """
        >>> a = Pythagorean()
        """
        Temperament.__init__(self)
        self.name = 'Pythagorean'
        self.doc = 'Static Pythagorean tuning'
        
    # pythagorean, from dodge and jerse p39 -->
    # note: aug4 and dim5 are rounded (588,612) -->
    def _translatePitch(self):
        pc = self.pc
        if    pc == 0: pcPost =   0.00
        elif pc ==  1: pcPost =   0.90
        elif pc ==  2: pcPost =   2.04
        elif pc ==  3: pcPost =   2.94
        elif pc ==  4: pcPost =   4.08
        elif pc ==  5: pcPost =   4.98
        elif pc ==  6: pcPost =   6.00
        elif pc ==  7: pcPost =   7.02
        elif pc ==  8: pcPost =   7.92
        elif pc ==  9: pcPost =   9.06
        elif pc == 10: pcPost =   9.96
        elif pc == 11: pcPost =  11.09
        # assign
        self.pc = pcPost

class Just(Temperament):
    def __init__(self):
        """
        >>> a = Just()
        """
        Temperament.__init__(self)
        self.name = 'Just'
        self.doc = 'Static Just tuning'
    # just, from dodge and jerse p39
    # note: aug unis and min2 (92,112), min2 is used
    # note: aug6 and min7 (996,1018), min7 is used
    def _translatePitch(self):
        pc = self.pc
        if    pc == 0: pcPost =   0.00
        elif pc ==  1: pcPost =   1.12
        elif pc ==  2: pcPost =   2.04
        elif pc ==  3: pcPost =   3.16
        elif pc ==  4: pcPost =   3.86
        elif pc ==  5: pcPost =   4.98
        elif pc ==  6: pcPost =   6.00
        elif pc ==  7: pcPost =   7.02
        elif pc ==  8: pcPost =   8.14
        elif pc ==  9: pcPost =   8.84
        elif pc == 10: pcPost =  10.18
        elif pc == 11: pcPost =  10.88
        # assign
        self.pc = pcPost

class MeanTone(Temperament):
    def __init__(self):
        """
        >>> a = MeanTone()
        """
        Temperament.__init__(self)
        self.name = 'MeanTone'
        self.doc = 'Static Mean Tone tuning'
    # meanTone, from dodge and jerse p39
    # note: aug unis and min2 (76,117), min2 is used
    # note: aug6 and min7 (966,1007), min7 is used -
    def _translatePitch(self):
        pc = self.pc
        if    pc == 0: pcPost =   0.00
        elif pc ==  1: pcPost =   1.17
        elif pc ==  2: pcPost =   1.93
        elif pc ==  3: pcPost =   3.10
        elif pc ==  4: pcPost =   3.86
        elif pc ==  5: pcPost =   5.03
        elif pc ==  6: pcPost =   5.80
        elif pc ==  7: pcPost =   6.97
        elif pc ==  8: pcPost =   8.14
        elif pc ==  9: pcPost =   8.90
        elif pc == 10: pcPost =  10.07
        elif pc == 11: pcPost =  10.83
        # assign
        self.pc = pcPost

class Split24Lower(Temperament):
    def __init__(self):
        """
        >>> a = Split24Lower()
        """
        Temperament.__init__(self)
        self.name = 'Split24Lower'
        self.doc = 'Lower half of a 24 tone equal tempered scale'

    def _translatePitch(self):
        self.pc = self.pc * .5

class Split24Upper(Temperament):
    def __init__(self):
        """
        >>> a = Split24Upper()
        """
        Temperament.__init__(self)
        self.name = 'Split24Upper'
        self.doc = 'Upper half of a 24 tone equal tempered scale'

    def _translatePitch(self):
        self.pc = (self.pc * .5) + 6 # shift 1/4 tone higher, 1/2 octave

class Interleave24Even(Temperament):
    def __init__(self):
        """
        >>> a = Interleave24Even()
        """
        Temperament.__init__(self)
        self.name = 'Interleave24Even'
        self.doc = 'Even steps of a 24 tone equal tempered scale'

    def _translatePitch(self):
        self.pc = self.pc + 0 # do nothing, same as 12te

class Interleave24Odd(Temperament):
    def __init__(self):
        """
        >>> a = Interleave24Odd()
        """
        Temperament.__init__(self)
        self.name = 'Interleave24Odd'
        self.doc = 'Odd steps of a 24 tone equal tempered scale'

    def _translatePitch(self):
        self.pc = self.pc + .5 # add 1/4 tone

class NoiseLight(Temperament):
    def __init__(self):
        """
        >>> a = NoiseLight()
        """
        Temperament.__init__(self)
        self.name = 'NoiseLight'
        self.doc = 'Provide uniform random +/- 5 cent noise on each pitch'
    maxNoise = .05
    def _translatePitch(self):
        shift = (random.random() * (self.maxNoise * 2)) - self.maxNoise
        self.pc = self.pc + shift

class NoiseMedium(Temperament):
    def __init__(self):
        """
        >>> a = NoiseMedium()
        """
        Temperament.__init__(self)
        self.name = 'NoiseMedium'
        self.doc = 'Provide uniform random +/- 10 cent noise on each pitch'
    maxNoise = .10
    def _translatePitch(self):
        shift = (random.random() * (self.maxNoise * 2)) - self.maxNoise
        self.pc = self.pc + shift

class NoiseHeavy(Temperament):
    def __init__(self):
        """
        >>> a = NoiseHeavy()
        """
        Temperament.__init__(self)
        self.name = 'NoiseHeavy'
        self.doc = 'Provide uniform random +/- 15 cent noise on each pitch'
    maxNoise = .15
    def _translatePitch(self):
        shift = (random.random() * (self.maxNoise * 2)) - self.maxNoise
        self.pc = self.pc + shift

class NoiseUser(Temperament):
    def __init__(self):

        Temperament.__init__(self)
        self.name = 'NoiseUser'
        self.doc = 'Provide uniform random +/- 50 cent noise on each pitch'
    maxNoise = 10
    def _translatePitch(self):
        shift = (random.random() * (self.maxNoise * 2)) - self.maxNoise
        self.pc = self.pc + shift


#-----------------------------------------------------------------||||||||||||--


temperamentNames = ['TwelveEqual', 'Pythagorean', 'Just', 'MeanTone', 
                         'Split24Upper', 'Split24Lower', 
                         'Interleave24Even', 'Interleave24Odd', 
                         'NoiseLight', 'NoiseMedium', 'NoiseHeavy', 'NoiseUser']

def temperamentNameParser(usrStr):
    # allows for backward compatibility with old names
    ref = {
        'TwelveEqual' : ['12equal', '12', 'twelveequal', 'te'],
        'Pythagorean' : ['12pythagorean', 'pythagorean', 'p'],
        'Just'  : ['12just', 'just', 'j'],
        'MeanTone'  : ['12meantone', 'meantone', 'mean', 'mt'],
        'Split24Upper'   : ['24toneupper', '24splitupper', 'split24upper', 'su'],
        'Split24Lower'   : ['24tonelower', '24splitlower', 'split24lower', 'sl'],
        'Interleave24Even' : ['24toneupper', '24interleaveeven', 
                                     'interleave24even', 'ie'],
        'Interleave24Odd'    : ['24tonelower', '24interleaveodd', 
                                     'interleave24odd', 'io'],
        'NoiseLight'  : ['12lightnoise', '12noiselight', 'noiselight', 'nl'],
        'NoiseMedium'   : ['12noisemedium', 'noisemedium', 'nm'],
        'NoiseHeavy'  : ['12heavynoise', '12noiseheavy', 'noiseheavy', 'nh'],
        'NoiseUser'  : ['12heavyuser', '12noiseuser', 'noiseuser', 'nu'],
            }
            
    usrStr = drawer.selectionParse(usrStr, ref)
    return usrStr # may be Non
    
    
def factory(rawArgs):
    name = temperamentNameParser(rawArgs)
    if name == None: 
        raise ValueError('bad temperament name given: %s' % rawArgs) # failure
    modAttr = globals()[name]
    return modAttr()
    
    
    
    
    
    
    

#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        for name in temperamentNames:
            a = factory(name)
            post = [a(x) for x in range(0,12)]


#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)
