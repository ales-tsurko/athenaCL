#-----------------------------------------------------------------||||||||||||--
# Name:          envelop.py
# Purpose:       creator of breal-point envelope archetypes
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2008-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import random, copy
import unittest, doctest


from athenaCL.libATH import unit
from athenaCL.libATH import error

OFFSET = 0.000000001 # value in seconds used for minimum spacing


#-----------------------------------------------------------------||||||||||||--
def _stepFilter(shift):
    """scalar is used to shift all values to always allow for the offset;
    the scalar value must be calculated elsewhere
    if shift is zero process
    if shfit is negative raise error
    if shift is positive do nothign
    """

    if shift <= 0:
        shift = OFFSET
    return shift


#-----------------------------------------------------------------||||||||||||--

def durToTrapezoid(tStart, propAbsSwitch, dur, rampUp, widthMax, rampDown,
                         widthMin, min=0, max=1):
    """assume dir of peal is widthOn
    will automatically convert to proportion if abs sum extends past dur
    this is an trapezoid with only one ramp; may not have complete duration time; always leads on

    >>> durToTrapezoid(0, 'absolute', 10, 3, 3, 3, .5)
    [[0, 0.0], [3, 1.0], [6, 1.0], [9, 0.0], [9.999..., 0.0]]
    """

    # will automatically sort min, max
    peak = unit.denorm(1, min, max)
    nadir = unit.denorm(0, min, max)

    if propAbsSwitch not in ['absolute', 'proportional']:
        raise error.ParameterObjectSyntaxError, 'incorrect switch'

    if propAbsSwitch == 'absolute':
        timeUnitDenorm = [rampUp, widthMax, rampDown, widthMin]
        if sum(timeUnitDenorm) > dur: # force proportional
            propAbsSwitch = 'proportional' 

    if propAbsSwitch == 'proportional':
        timeUnit = unit.unitNormProportion([rampUp, widthMax, rampDown, widthMin])
        timeUnitDenorm = [x*dur for x in timeUnit]

    tEnd = tStart + dur
    t = tStart 

    envelope = []
    envelope.append([t, nadir])

    t = t + _stepFilter(timeUnitDenorm[0]) # ramp
    envelope.append([t, peak])

    t = t + _stepFilter(timeUnitDenorm[1]) # width
    envelope.append([t, peak])

    t = t + _stepFilter(timeUnitDenorm[2]) # ramp
    envelope.append([t, nadir])

    t = tEnd - OFFSET # always measure to end
    envelope.append([t, nadir])

    return envelope



def durToAdsr(tStart, propAbsSwitch, dur, attack, decay, 
                         sustain, release, susScalar, min=0, max=1):
    """create an adsr envelope
    sustain scalar is a value, w/n the unit interval, of the difference between
    min and max

    >>> durToAdsr(0, 'absolute', 10, 2, 1, 2, 2, .5)
    [[0, 0.0], [2, 1.0], [3, 0.5], [5, 0.5], [7, 0.0], [9.999..., 0.0]]

    """
    # will automatically sort min, max
    peak = unit.denorm(1, min, max)
    nadir = unit.denorm(0, min, max)
    susLevel = (peak-nadir) * unit.limit(susScalar)

    if propAbsSwitch not in ['absolute', 'proportional']:
        raise error.ParameterObjectSyntaxError, 'incorrect switch'

    if propAbsSwitch == 'absolute':
        timeUnitDenorm = [attack, decay, sustain, release]
        if sum(timeUnitDenorm) > dur: # force proportional
            propAbsSwitch = 'proportional' 

    if propAbsSwitch == 'proportional':
        timeUnit = unit.unitNormProportion([attack, decay, sustain, release])
        timeUnitDenorm = [x*dur for x in timeUnit]

    tEnd = tStart + dur
    t = tStart 

    envelope = []
    envelope.append([t, nadir])

    t = t + _stepFilter(timeUnitDenorm[0]) # attack
    envelope.append([t, peak])

    t = t + _stepFilter(timeUnitDenorm[1]) # decay
    envelope.append([t, susLevel])

    t = t + _stepFilter(timeUnitDenorm[2]) # sustain
    envelope.append([t, susLevel])

    if propAbsSwitch == 'proportional':
        t = tEnd - OFFSET # always measure to end
        envelope.append([t, nadir])
    else: # absolute
        t = t + _stepFilter(timeUnitDenorm[3]) # sustain
        envelope.append([t, nadir])
        t = tEnd - OFFSET # always measure to end
        envelope.append([t, nadir])


    return envelope




def durToUnit(tStart, dur, center, width, min=0, max=1):
    """
    this unit envelope is based on a csound model here
     iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
     iRelease    = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
     kAmp        linen     iAmp, iAttack, iDur, iRelease

    >>> durToUnit(0, 10, .5, .5)
    [[0, 0.0], [2.5, 1.0], [7.5, 1.0], [9.999..., 0.0]]

"""
    # will automatically sort min, max
    peak = unit.denorm(1, min, max)
    nadir = unit.denorm(0, min, max)

    # normalize w/n unit interval
    center = unit.limit(center)
    width = unit.limit(width)

    # must be greater or smaller than 0/1 to avoid double points at same x
    # or, worse, the alst event not being the last
    if center >= 1:
        center = center - OFFSET
    if center <= 0:
        center = center + OFFSET
    if width >= 1:
        width = width - OFFSET
    if width <= 0:
        width = width + OFFSET

    rampUp = ((1 - width) * center) * dur
    rampDown = ((1 - width) * (1 - center)) * dur
    center = width * dur

    timeUnitDenorm = [rampUp, center, rampDown]

    tEnd = tStart + dur
    t = tStart 

    envelope = []
    envelope.append([t, nadir])

    t = t + timeUnitDenorm[0] # ramp
    envelope.append([t, peak])

    t = t + timeUnitDenorm[1] # width
    envelope.append([t, peak])

    t = tEnd - OFFSET # always measure to end
    envelope.append([t, nadir])

    return envelope










#-----------------------------------------------------------------||||||||||||--

# class TestOld:
# 
#     """note that there is a potential error in cases where the time interval values fall to or below zero.
# 
#     zero values in some positions could cause the last point to come before the penultimate point. htis error will not be caught
# 
#     the _stepFilter function attempt to catch many possible simple errors
#     """
# 
#     def __init__(self):
#         pass
# 
#     def testBasic(self):
#         print 'durToTrapezoid'
#         post = durToTrapezoid(0, 'proportional', 300, 10,10,10,10,0,1)
#         print post
# 
#         post = durToTrapezoid(120, 'proportional', 300, 10,20000,10,10,-2,10)
#         print post
# 
# 
#         print 'durToAdsr'
#         post = durToAdsr(0, 'proportional', 300, 10,10,10,10,.5, 0,1)
#         print post
# 
#         post = durToAdsr(120, 'proportional', 300, 10,200,100,50, .5, -2,10)
#         print post
# 
# 
#         print 'durToUnit'
#         post = durToUnit(0, 300, .8, .4, 0,1)
#         print post
# 
#         post = durToUnit(120, 300, .01, .01, -2,10)
#         print post
# 



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        post = durToTrapezoid(0, 'proportional', 300, 10,10,10,10,0,1)
        post = durToTrapezoid(120, 'proportional', 300, 10,20000,10,10,-2,10)
        post = durToAdsr(0, 'proportional', 300, 10,10,10,10,.5, 0,1)
        post = durToAdsr(120, 'proportional', 300, 10,200,100,50, .5, -2,10)
        post = durToUnit(0, 300, .8, .4, 0,1)
        post = durToUnit(120, 300, .01, .01, -2,10)


#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)











