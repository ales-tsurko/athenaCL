#-----------------------------------------------------------------||||||||||||--
# Name:          valueSingleOmde.py
# Purpose:       definitions of all omde-descended parameter objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import copy
import unittest, doctest


from athenaCL.libATH import typeset
from athenaCL.libATH import drawer
from athenaCL.libATH import unit
from athenaCL.libATH import error
from athenaCL.libATH import envelope
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH.omde import oscillator
from athenaCL.libATH.omde import rand
from athenaCL.libATH.omde import bpf

from athenaCL.libATH.libPmtr import basePmtr


_MOD = 'valueSingleOmde.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)


#-----------------------------------------------------------------||||||||||||--

class _Wave(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # assigned in subclass
        self.argTypes = ['str', ['num','list'], 'num', ['num','list'], ['num','list']]
        self.argNames = ['stepString', 'parameterObject: secPerCycle', 'phase', 'min', 'max']
        self.argDefaults = ['e', 30, 0, 0, 1]
        self.argDemos = [['e', ('bpl','e','l',((0,30),(120,15))), 0, 0, 1]]
        
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error
                
        self.step = self._stepControlParser(self.args[0]) # raises exception 
        self.spcObj = self._loadAutoConstant(self.args[1])
        self.phase = self.args[2]
        self.minObj, self.maxObj = self._loadMinMax(self.args[3], self.args[4])
        self.obj = None #assigned in subclass
        self.i = 0 # step position

    def checkArgs(self):
        ok, msg = self.spcObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.minObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1: return ok, msg
        return 1, ''

    def repr(self, format=''):
        spcStr = self.spcObj.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return '%s, %s, (%s), %s, (%s), (%s)' % (self.type, self.step, spcStr, 
                 typeset.anyDataToStr(self.phase), minStr, maxStr)

    def reset(self):
        self.i = 0 # step always starts at 0
        self.spcObj.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t, refDict=None):
        if self.step == 'event': # if use events, not time
            tLocal = self.i # do not pass this time to sub pmtrObjs!
        else: tLocal = t             
        
        spc = self.spcObj(t, refDict)
        try: fq = 1.0 / spc # convert spc to frequency
        except ZeroDivisionError:
            fq = 1 # override
            #raise error.ParameterObjectSyntaxError, 'spc/epc must be greater than zero.'       

        self.currentValue = unit.denorm(self.obj(tLocal, fq), # only use tLocal 
                                  self.minObj(t, refDict), self.maxObj(t, refDict))
        # increment after value returned
        if self.step == 'event': # if use steps, not time
            self.i += 1
        return self.currentValue


# omde waves produce values b/n 0 and 1
class WaveSine(_Wave):
    def __init__(self, args, refDict):
        _Wave.__init__(self, args, refDict) # call base init
        self.type = 'waveSine'
        self.doc = lang.docPoWs
        self.argDemos.append(['e',20,0,0,('ws','e',60,.25,.25,1)])
        self.argDemos.append(['e',('bg','oo',(19,19,20,20,20)),0,0,1])

        self.obj = oscillator.Sine(None, self.phase) #omde object

class WaveCosine(_Wave):
    def __init__(self, args, refDict):
        _Wave.__init__(self, args, refDict) # call base init
        self.type = 'waveCosine'
        self.doc = lang.docPoWc
        self.argDemos.append(['e',40,0,('wp','e',20,0,1,.5),('a',0,('c',.01))])
        self.obj = oscillator.Cosine(None, self.phase) #omde object

class WaveSawUp(_Wave):
    def __init__(self, args, refDict):
        _Wave.__init__(self, args, refDict) # call base init
        self.type = 'waveSawUp'
        self.doc = lang.docPoWsu
        self.argDemos.append(['e',20,0,('wpd','e',40,0,1.5,1,.5),0])
        self.obj = oscillator.SawUp(None, self.phase) #omde object

class WaveSawDown(_Wave):
    def __init__(self, args, refDict):
        _Wave.__init__(self, args, refDict) # call base init
        self.type = 'waveSawDown'
        self.doc = lang.docPoWsd
        self.argDemos.append(['e',20,0,('wpu','e',120,0,1.5,.5,1),
                                            ('wpd','e',40,.25,1.5,.5,0)])
        self.obj = oscillator.SawDown(None, self.phase) #omde object

class WavePulse(_Wave):
    def __init__(self, args, refDict):
        _Wave.__init__(self, args, refDict) # call base init
        self.type = 'wavePulse'
        self.doc = lang.docPoWp
        self.argDemos.append(['e',10,0,('a',0,('ws','e',30,.75,-.01,.03)),.5])
        self.obj = oscillator.Square(None, self.phase) #omde object

class WaveTriangle(_Wave):
    def __init__(self, args, refDict):
        _Wave.__init__(self, args, refDict) # call base init
        self.type = 'waveTriangle'
        self.doc = lang.docPoWt
        self.argDemos.append(['e',30,0,('ru',0,.3),('ru',.7,1)])
        self.obj = oscillator.Triangle(None, self.phase) #omde object



#-----------------------------------------------------------------||||||||||||--
class _WaveHalfPeriod(_Wave):
    def __init__(self, args, refDict):
        _Wave.__init__(self, args, refDict) # call base init
        self.spc = None
        self.timeShift = None
        self.currentTimeRange = None
        self.phaseShift = None

    def __call__(self, t, refDict=None):
        if self.step == 'event': # if use events, not time
            tLocal = self.i # do not pass this time to sub pmtrObjs!
        else: tLocal = t             
        
        if self.currentTimeRange == None or (tLocal < self.currentTimeRange[0] or tLocal >= self.currentTimeRange[1]): 
            # double seconds per cycle so that specified values are the
            # the time of one half period
            self.spc = self.spcObj(t, refDict) * 2
            # shift the phase to the start of this segment
            self.timeShift = -tLocal
            # update at the half period
            self.currentTimeRange = [tLocal, tLocal + (self.spc * .5)]

            # flip flop phase shift to get second half of wave
            if self.phaseShift == None or self.phaseShift == .5:
                self.phaseShift = 0
            else:
                self.phaseShift = .5

        try: fq = 1.0 / self.spc # convert spc to frequency
        except ZeroDivisionError:
            fq = 1 # override
            #raise error.ParameterObjectSyntaxError, 'spc/epc must be greater than zero.'       
 
        rawPosition = self.obj(tLocal+self.timeShift, fq, 
                                phase0=self.phaseShift)
        #environment.printDebug(['current fq', fq, 'raw position', rawPosition])

        self.currentValue = unit.denorm(rawPosition, # only use tLocal 
                           self.minObj(t, refDict), self.maxObj(t, refDict))
        # increment after value returned
        if self.step == 'event': # if use steps, not time
            self.i += 1
        return self.currentValue


class WaveHalfPeriodSine(_WaveHalfPeriod):
    def __init__(self, args, refDict):
        _WaveHalfPeriod.__init__(self, args, refDict) # call base init
        self.type = 'waveHalfPeriodSine'
        self.doc = lang.docPoWhps # TODO: add

        self.argDefaults = ['e', ['bg','rc',[10,20,30]], 0, 0, 1]
        self.argDemos.append(['e',20,0,0,('ws','e',60,.25,.25,1)])
        self.argDemos.append(['e',('bg','oo',(19,19,20,20,20)),0,0,1])
        self.obj = oscillator.Sine(None, self.phase) #omde object

class WaveHalfPeriodCosine(_WaveHalfPeriod):
    def __init__(self, args, refDict):
        _WaveHalfPeriod.__init__(self, args, refDict) # call base init
        self.type = 'waveHalfPeriodCosine'
        self.doc = lang.docPoWhpc # TODO: add
        self.argDefaults = ['e', ['bg','rc',[10,20,30]], 0, 0, 1]
        self.obj = oscillator.Cosine(None, self.phase) #omde object
        
class WaveHalfPeriodPulse(_WaveHalfPeriod):
    def __init__(self, args, refDict):
        _WaveHalfPeriod.__init__(self, args, refDict) # call base init
        self.type = 'waveHalfPeriodPulse'
        self.doc = lang.docPoWhpp # TODO: add

        self.argDefaults = ['e', ['bg','rc',[10,20,30]], 0, 0, 1]
        self.argDemos.append(['e',10,0,('a',0,('ws','e',30,.75,-.01,.03)),.5])
        self.argDemos.append(['e',('bg','rc',(15,10,5,8,2)), 0,0,('ls','e',100,.3,1)])
        self.obj = oscillator.Square(None, self.phase) #omde object

class WaveHalfPeriodTriangle(_WaveHalfPeriod):
    def __init__(self, args, refDict):
        _WaveHalfPeriod.__init__(self, args, refDict) # call base init
        self.type = 'waveHalfPeriodTriangle'
        self.doc = lang.docPoWhpt # TODO: add
        self.argDefaults = ['e', ['bg','rc',[10,20,30]], 0, 0, 1]
        self.obj = oscillator.Triangle(None, self.phase) #omde object




#-----------------------------------------------------------------||||||||||||--
# exonential wave; have an additional argument
class _WaveExponential(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # assigned in subclass
        self.argTypes = ['str', ['num','list'], 'num', 'num', 
                             ['num','list'], ['num','list']]
        self.argNames = ['stepString', 'parameterObject: secPerCycle', 'phase', 
                              'exponent', 'min', 'max']
        self.argDefaults = ['e', 30, 0, 2, 0, 1]         
        self.argDemos = [['e', ('bpl','e','l',((0,30),(120,15))), 0, 2, 0, 1]]

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error
        
        self.step = self._stepControlParser(self.args[0]) # raises except on error
        self.spcObj = self._loadAutoConstant(self.args[1])

#         self.spc = self.args[1] # spc not cps
#         try:
#             self.fq = 1.0 / self.spc # convert spc to frequency
#         except ZeroDivisionError:
#             raise error.ParameterObjectSyntaxError, 'spc/epc must be greater than zero.'

        self.phase = self.args[2]
        self.exp = self.args[3]
        self.minObj, self.maxObj = self._loadMinMax(self.args[4], self.args[5])
        self.obj = None #assigned in subclass
        self.i = 0 # step position

    def checkArgs(self):
        ok, msg = self.spcObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.minObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1: return ok, msg
        return 1, ''

    def repr(self, format=''):
        spcStr = self.spcObj.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return '%s, %s, (%s), %s, %s, (%s), (%s)' % (self.type, self.step, 
            spcStr, typeset.anyDataToStr(self.phase), 
            typeset.anyDataToStr(self.exp), minStr, maxStr)

    def reset(self):
        self.i = 0 # step always starts at 0
        self.spcObj.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t, refDict=None):
        if self.step == 'event': # if use events, not time
            tLocal = self.i # do not pass this time to sub pmtrObjs!
        else: tLocal = t      

        spc = self.spcObj(t, refDict)
        try: fq = 1.0 / spc # convert spc to frequency
        except ZeroDivisionError:
            fq = 1 # override
            #raise error.ParameterObjectSyntaxError, 'spc/epc must be greater than zero.'       

        self.currentValue = unit.denorm(self.obj(tLocal, fq), # only use tLocal 
                                  self.minObj(t, refDict),   self.maxObj(t, refDict))
        # increment after value returned
        if self.step == 'event': # if use steps, not time
            self.i = self.i + 1
        return self.currentValue

class WavePowerUp(_WaveExponential):
    def __init__(self, args, refDict):
        _WaveExponential.__init__(self, args, refDict) # call base init
        self.type = 'wavePowerUp'
        self.doc = lang.docPoWpu
        self.argDemos.append(['e',40,0,2,('ru',0,('a',0,('c',.005))),1])
        self.obj = oscillator.PowerUp(None, self.phase, self.exp) #omde object

class WavePowerDown(_WaveExponential):
    def __init__(self, args, refDict):
        _WaveExponential.__init__(self, args, refDict) # call base init
        self.type = 'wavePowerDown'
        self.doc = lang.docPoWpd
        self.argDemos.append(['e',40,0,-1.5,
                                ('wp','e',30,0,0,.2),
                                ('wp','e',20,.25,1,.8)])
        self.obj = oscillator.PowerDown(None, self.phase, self.exp) 




#-----------------------------------------------------------------||||||||||||--
# exonential wave; have an additional argument
class _Random(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # assigned in subclass
        self.argTypes = [['num','list'], ['num','list'],]
        self.argNames = ['min', 'max']
        self.argDefaults = [0, 1]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error
        self.minObj, self.maxObj = self._loadMinMax(self.args[0], self.args[1])
        self.obj = None #assigned in subclass

    def checkArgs(self):
        return 1, ''

    def repr(self, format=''):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return '%s, (%s), (%s)' % (self.type, minStr, maxStr)

    def reset(self):
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t, refDict=None):
        self.currentValue = unit.denorm(self.obj(), 
                                  self.minObj(t, refDict),   self.maxObj(t, refDict))
        return self.currentValue

class RandomUniform(_Random):
    def __init__(self, args, refDict):
        _Random.__init__(self, args, refDict) # call base init
        self.type = 'randomUniform'
        self.doc = lang.docPoRu
        self.argDemos = [[('ws','e',60,0,.5,0),('ws','e',40,.25,1,.5)],
                             ]
        self.obj = rand.UniformRandom() #omde object

class RandomLinear(_Random):
    def __init__(self, args, refDict):
        _Random.__init__(self, args, refDict) # call base init
        self.type = 'randomLinear'
        self.doc = lang.docPoRl
        self.argDemos = [[('a',.5,('c',-.01)),('a',.5,('c',.01))],
                             ]
        self.obj = rand.LinearRandom() #omde object

class RandomInverseLinear(_Random):
    def __init__(self, args, refDict):
        _Random.__init__(self, args, refDict) # call base init
        self.type = 'randomInverseLinear'
        self.doc = lang.docPoRil
        self.argDemos = [[('a',0,('c',.01)),('a',.2,('c',.025))],
                             ]
        self.obj = rand.InverseLinearRandom() #omde object

class RandomTriangular(_Random):
    def __init__(self, args, refDict):
        _Random.__init__(self, args, refDict) # call base init
        self.type = 'randomTriangular'
        self.doc = lang.docPoRt
        self.argDemos = [[0,('wpd','e',90,0,-1.5,1,0)],
                             ]
        self.obj = rand.TriangularRandom() #omde object

class RandomInverseTriangular(_Random):
    def __init__(self, args, refDict):
        _Random.__init__(self, args, refDict) # call base init
        self.type = 'randomInverseTriangular'
        self.doc = lang.docPoRit
        self.argDemos = [[0,('wpd','e',40,0,2,1,.1)],
                             ]
        self.obj = rand.InverseTriangularRandom() #omde object


#-----------------------------------------------------------------||||||||||||--
# random objects with lambda arg
class _RandomOneArg(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # assigned in subclass
        self.argTypes = ['num', ['num','list'], ['num','list']]
        self.argNames = ['lambda', 'min', 'max']
        self.argDefaults = [.5, 0, 1]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error
        self.lambd = float(self.args[0]) # needs to be a float
        self.minObj, self.maxObj = self._loadMinMax(self.args[1], self.args[2])
        self.obj = None #assigned in subclass

    def checkArgs(self):
        if self.lambd <= 0:
            msg = 'lambda may not be less than or equal to zero.'
            return 0, msg        
        ok, msg = self.minObj.checkArgs()
        if not ok: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if not ok: return ok, msg
        return 1, ''

    def repr(self, format=''):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return '%s, %s, (%s), (%s)' % (self.type, 
            typeset.anyDataToStr(self.lambd), minStr, maxStr)

    def reset(self):
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t, refDict=None): # needs time
        self.currentValue = unit.denorm(self.obj(t), 
                                  self.minObj(t, refDict),   self.maxObj(t, refDict))
        return self.currentValue

class RandomExponential(_RandomOneArg):
    def __init__(self, args, refDict):
        _RandomOneArg.__init__(self, args, refDict) # call base init
        self.type = 'randomExponential'      
        self.doc = lang.docPoRe
        self.argDemos = [[100,0,1],
                              [10,('bpl','e','l',((0,0),(120,.5))),
                                    ('bpl','e','l',((0,.5),(120,1)))],
                             ]
        self.obj = rand.ExponentialRandom(self.lambd) #omde object

class RandomInverseExponential(_RandomOneArg):
    def __init__(self, args, refDict):
        _RandomOneArg.__init__(self, args, refDict) # call base init
        self.type = 'randomInverseExponential'
        self.doc = lang.docPoRie
        self.argDemos = [[100,0,1],
                              [10,('bpl','e','l',((0,.5),(120,0))),
                                    ('bpl','e','l',((0,1),(120,.5)))],
                             ]
        self.obj = rand.InverseExponentialRandom(self.lambd) #omde object

class RandomBilateralExponential(_RandomOneArg):
    def __init__(self, args, refDict):
        _RandomOneArg.__init__(self, args, refDict) # call base init
        self.type = 'randomBilateralExponential'
        self.doc = lang.docPoRbe
        self.argDemos = [[10,0,1],
                              [20,0,('bpp','e','l',((0,1),(40,.6),(80,1)),2)],
                             ]
        self.obj = rand.BilateralExponentialRandom(self.lambd) #omde object

#-----------------------------------------------------------------||||||||||||--
# random objects with lambda arg
class _RandomTwoArg(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # assigned in subclass
        self.argTypes = ['num', 'num', ['num','list'], ['num','list']]
        self.argNames = ['alpha', 'beta', 'min', 'max']
        self.argDefaults = [.5, .5, 0, 1]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error

        self.argA = float(self.args[0]) # needs to be a float
        self.argB = float(self.args[1]) # needs to be a float
        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.obj = None #assigned in subclass

    def checkArgs(self):
        if self.argA <= 0 or self.argB <= 0:
            return 0, 'alpha and beta may not be less than or equal to zero.'
        ok, msg = self.minObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1: return ok, msg
        return 1, ''

    def repr(self, format=''):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return '%s, %s, %s, (%s), (%s)' % (self.type, 
            typeset.anyDataToStr(self.argA), typeset.anyDataToStr(self.argB), 
            minStr, maxStr)

    def __call__(self, t, refDict=None): # needs time
        self.currentValue = unit.denorm(self.obj(t), 
                                  self.minObj(t, refDict),   self.maxObj(t, refDict))
        return self.currentValue

class RandomGauss(_RandomTwoArg):
    def __init__(self, args, refDict):
        _RandomTwoArg.__init__(self, args, refDict) # call base init
        self.type = 'randomGauss'
        self.doc = lang.docPoRg
        self.argNames = ['mu', 'sigma', 'min', 'max']
        self.argDefaults = [.5, .1, 0, 1]
        self.argDemos = [[.5,.5,('ws','e',120,.25,0,.5),
                                        ('ws','e',120,.5,1,.5)],
                             ]
        self.obj = rand.GaussRandom(self.argA, self.argB) #omde object

class RandomCauchy(_RandomTwoArg):
    def __init__(self, args, refDict):
        _RandomTwoArg.__init__(self, args, refDict) # call base init
        self.type = 'randomCauchy'
        self.doc = lang.docPoRc
        self.argNames = ['alpha', 'mu', 'min', 'max']
        self.argDefaults = [.1, .5, 0, 1]
        self.argDemos = [[.1,.1,1,('bpp','e','l',((0,0),(120,.3)),2)],
                              [.1,.9,0,('bpp','e','l',((0,1),(120,.3)),2)],
                             ]
        self.obj = rand.CauchyRandom(self.argA, self.argB) #omde object

class RandomBeta(_RandomTwoArg):
    def __init__(self, args, refDict):
        _RandomTwoArg.__init__(self, args, refDict) # call base init
        self.type = 'randomBeta'
        self.doc = lang.docPoRb
        self.argDemos = [[.2,.2,('ws','e',60,0,0,.5),1],
                             ]
        self.obj = rand.BetaRandom(self.argA, self.argB) #omde object
                             
class RandomWeibull(_RandomTwoArg):
    def __init__(self, args, refDict):
        _RandomTwoArg.__init__(self, args, refDict) # call base init
        self.type = 'randomWeibull'
        self.doc = lang.docPoRw
        self.argDefaults = [.5, 2.0, 0, 1]
        self.argDemos = [[.9,.1,0,1],
                              [.1,.9,('ws','e',240,0,0,.4),1]
                             ]
        if self.argA >= 20 or self.argB >= 20:
            msg = 'alpha and beta should not be greater than 20.'
            raise error      
        self.obj = rand.WeibullRandom(self.argA, self.argB) #omde object



#-----------------------------------------------------------------||||||||||||--
# break point functions from omde
class _BreakPoint(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # assigned in subclass
        # 4th arg here is optional
        self.argTypes = [['int', 'str'], ['int', 'str'], 'list', 'num']
        self.argDefaults = ['e','l',
                                  ((0,1),(6,.3),(12,.3),(18,0),(24,.6)), -1.5]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error

        # raises except on error
        self.step = self._stepControlParser(self.args[0]) 
        self.loop = self._loopControlParser(self.args[1]) 

        self.points = self.args[2]
        ok, msg = self._scrubPoints() # not sure what to do if it fails
        if ok != 1:
            raise error

        self.exp = 1 # only used in power
        if len(self.args) >= 4:
            self.exp = self.args[3]

        self.obj = None #assigned in subclass
        self.i = 0 # step position

    def _scrubPoints(self):
        """fix all ordered point pairs:
        if one point is given, duplicate it at a greater x
        remove duplicate x positions, sort"""
        rawPoints = copy.deepcopy(self.points)
        scrubPoints = []
        xPoints = []
        # of a tuple of two value is given as a single point, need to 
        # add as a list
        if not drawer.isList(rawPoints):
            if not drawer.isNum(rawPoints): # accept a single number
                return 0, 'supply a list of points.'
            else: # its is a number
                rawPoints = [rawPoints] # will be handled below
        if len(rawPoints) == 0:
            return 0, 'add points to create a break point.'
        elif len(rawPoints) == 1: # one value is interpreted as a constant
            if drawer.isNum(rawPoints[0]): # shuld be a list
                rawPoints = [(0, rawPoints[0])] # will be fixed latter
        elif len(rawPoints) >= 2: # a tuple w/0 a comma gets collapsed
            if (drawer.isNum(rawPoints[0]) and 
                drawer.isNum(rawPoints[1])): # shuld be a list
                rawPoints = [(rawPoints[0], rawPoints[1])] # will be fixed latter
        for pair in rawPoints:
            if not drawer.isList(pair):
                return 0, 'each point must be a list of (x, y) pairs.'
            if len(pair) >= 2:
                pair = pair[:2]
            x, y = pair
            if not drawer.isNum(x) or not drawer.isNum(y):
                return 0, 'point pairs must consist only of numbers.'
            if x not in xPoints:
                xPoints.append(x)
                scrubPoints.append((x,y))
            else: # an x for this value has already been found
                pass
        scrubPoints.sort() # put in order
        if len(scrubPoints) == 0:
            return 0, 'no valid point pairs given.'
        elif len(scrubPoints) == 1: # add an extra point one unit away
            scrubPoints.append((scrubPoints[0][0]+1, scrubPoints[0][1]))

        self.points = scrubPoints       
        #environment.printDebug(['_scrubPoints, start, end', rawPoints, self.points])
        return 1, '' # all good 

    def _setObj(self):
        if self.loop == 'loop': # either loop or single
            loopArg = 1
        else:
            loopArg = 0
        if self.type == 'breakPointLinear':
            self.obj = bpf.LinearSegment(self.points, periodic=loopArg)
        elif self.type == 'breakPointPower':
            self.obj = bpf.PowerSegment(self.points, exp=self.exp, 
                                                 periodic=loopArg)
        elif self.type == 'breakPointHalfCosine':
            self.obj = bpf.HalfCosineSegment(self.points, periodic=loopArg)
        elif self.type == 'breakPointFlat':
            self.obj = bpf.NoInterpolationSegment(self.points, periodic=loopArg)

    def checkArgs(self):
        return 1, ''

    def repr(self, format=''):
        # internal points must be formated
        pointStr = typeset.anyDataToStr(self.points) # recursive 
        if self.type == 'breakPointLinear':
            return '%s, %s, %s, %s' % (self.type, self.step, self.loop, pointStr,)
        elif self.type == 'breakPointPower':
            return '%s, %s, %s, %s, %s' % (self.type, self.step, self.loop, 
                                            pointStr, typeset.anyDataToStr(self.exp))
        elif self.type == 'breakPointHalfCosine':
            return '%s, %s, %s, %s' % (self.type, self.step, self.loop, pointStr,)
        elif self.type == 'breakPointFlat':
            return '%s, %s, %s, %s' % (self.type, self.step, self.loop, pointStr,)

    def reset(self):
        self.i = 0 # step always starts at 0

    def __call__(self, t, refDict=None):
        if self.step == 'event': # if use events, not time
            t = self.i
        self.currentValue = self.obj(t) # no ref dict needed; omde object
        # increment after value returned
        if self.step == 'event': # if use steps, not time
            self.i += 1
        return self.currentValue

class BreakPointLinear(_BreakPoint):
    def __init__(self, args, refDict):
        _BreakPoint.__init__(self, args, refDict) # call base init
        self.type = 'breakPointLinear'
        # modify the default args to hide the exponent incongruity
        self.argDefaults = self.argDefaults[:3]
        self.argNames = ['stepString', 'edgeString', 'pointList',]
        self.argDemos = [['e','s',((12,.3),(18,.9),(24,.2),(48,.6))],
                  ['e','l',((0,.3),(10,.3),(11,.8),(25,.75),(26,.5),(45,.5),
                              (37,.35),(42,.7))],
                             ]
        self.doc = lang.docPoBpl
        self._setObj()

class BreakPointPower(_BreakPoint):
    def __init__(self, args, refDict):
        _BreakPoint.__init__(self, args, refDict) # call base init
        self.type = 'breakPointPower'
        self.argNames = ['stepString', 'edgeString', 'pointList', 'exponent']
        self.argDemos = [['e','l',
            ((0,.2),(10,1),(20,.8),(30,.5),(40,.2),(45,1),(50,0),(55,1)),
                        3.5],
                         ['e','s',((12,.3),(18,.9),(24,.8),(48,.2)),-4],
                             ]
        self.doc = lang.docPoBpp
        self._setObj()
        
class BreakPointHalfCosine(_BreakPoint):
    def __init__(self, args, refDict):
        _BreakPoint.__init__(self, args, refDict) # call base init
        self.type = 'breakPointHalfCosine'
        # modify the default args to hide the exponent incongruity
        self.argDefaults = self.argDefaults[:3]
        self.argNames = ['stepString', 'edgeString', 'pointList',]
        self.argDemos = [['e','s',((12,.3),(18,.9),(24,.2),(48,.6))],
                              ['e','l',
                              ((0,.3),(10,.3),(11,.8),(25,.75),(26,.5),(45,.5),
                              (37,.35),(42,.7))],
                             ]
        self.doc = lang.docPoBphc
        self._setObj()

class BreakPointFlat(_BreakPoint):
    """Note that this PO may return non-intuitive results, as it tries
    to create flag segments between two points; if there are only two
    points given, even if different, the result will be a constant value.
    """
    def __init__(self, args, refDict):
        _BreakPoint.__init__(self, args, refDict) # call base init
        self.type = 'breakPointFlat'
        # modify the default args to hide the exponent incongruity
        self.argDefaults = self.argDefaults[:3]
        self.argNames = ['stepString', 'edgeString', 'pointList']
        self.argDemos = [['e','s',((12,.3),(18,.9),(24,.2),(48,.6))],
                              ['e','l',
                              ((0,.3),(10,.3),(11,.8),(25,.75),(26,.5),(45,.5),
                              (37,.35),(42,.7))],
                             ]
        self.doc = lang.docPoBpf
        self._setObj()
        




#-----------------------------------------------------------------||||||||||||--
# dynamic break point functions from omde
class _BreakGraph(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # assigned in subclass
        # 4th arg here is optional
        self.argTypes = [['int', 'str'], ['int', 'str'], 'list', 'list', 
                                                                         'int', 'num']
        self.argDefaults = ['e','l', ['a',0,('bg','rp',[1,3,9])],
                                              ['bg','rc',(0,.25,.5,.75,1)], 60, -1.5]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error

        self.step = self._stepControlParser(self.args[0]) # raises except on error
        self.loop = self._loopControlParser(self.args[1]) # raises except on error

        self.points = None
        self.xPointGen = self._loadSub(self.args[2], 'genPmtrObjs')
        self.yPointGen = self._loadSub(self.args[3], 'genPmtrObjs')

        self.pointCount = self.args[4]

        # gen points, scrub, and sort
        ok, msg = self._genPoints(refDict)
        if ok != 1: raise error
        ok, msg = self._scrubPoints() # not sure what to do if it fails
        if ok != 1: raise error

        self.exp = 1 # only used in power
        if len(self.args) >= 6:
            self.exp = self.args[5]

        self.obj = None #assigned in subclass
        self.i = 0 # step position

    def _genPoints(self, refDict):
        """determine how many points need to generated; collectin in points list"""
        self.points = []
        for i in range(self.pointCount):
            coord = [self.xPointGen(i, refDict), self.yPointGen(i, refDict)]
            # check values to make sure they are numbers
            if not drawer.isNum(coord[0]) or not drawer.isNum(coord[1]):
                return 0, 'all point values must be numbers.'
            self.points.append(coord)
        return 1, '' # all good

    def _scrubPoints(self):
        """fix all ordered point pairs:
        if one point is given, duplicate it at a greater x
        remove duplicate x positions, sort"""
        rawPoints = copy.deepcopy(self.points)
        scrubPoints = []
        xPoints = []

        if len(rawPoints) == 0:
            return 0, 'add points to create a break point.'
        elif len(rawPoints) == 1: # one value is interpreted as a constant
            if drawer.isNum(rawPoints[0]): # shuld be a list
                rawPoints = [(0, rawPoints[0])] # will be fixed latter
        elif len(rawPoints) >= 2: # a tuple w/0 a comma gets collapsed
            if (drawer.isNum(rawPoints[0]) and 
                drawer.isNum(rawPoints[1])): # shuld be a list
                rawPoints = [(rawPoints[0], rawPoints[1])] # will be fixed latter
        for pair in rawPoints:
            x, y = pair
            if not drawer.isNum(x) or not drawer.isNum(y):
                return 0, 'point pairs must consist only of numbers.'
            if x not in xPoints: # cannot define an x value more than once
                xPoints.append(x)
                scrubPoints.append((x,y))
            else: # an x for this value has already been found
                pass
        scrubPoints.sort() # put in order
        if len(scrubPoints) == 0:
            return 0, 'no valid point pairs given.'
        elif len(scrubPoints) == 1: # add an extra point one unit away
            scrubPoints.append((scrubPoints[0][0]+1, scrubPoints[0][1]))
        self.points = scrubPoints
        return 1, '' # all good 

    def _setObj(self):
        if self.loop == 'loop': # either loop or single
            loopArg = 1
        else: loopArg = 0

        if self.type == 'breakGraphLinear':
            self.obj = bpf.LinearSegment(self.points, periodic=loopArg)
        elif self.type == 'breakGraphPower':
            self.obj = bpf.PowerSegment(self.points, exp=self.exp, 
                                                 periodic=loopArg)
        elif self.type == 'breakGraphHalfCosine':
            self.obj = bpf.HalfCosineSegment(self.points, periodic=loopArg)
        elif self.type == 'breakGraphFlat':
            self.obj = bpf.NoInterpolationSegment(self.points, periodic=loopArg)

    def checkArgs(self):
        if self.pointCount <= 0:
            return 0, 'pointCount error: must be greater than zero.'
        ok, msg = self.xPointGen.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.yPointGen.checkArgs()
        if not ok: return 0, msg    
        return 1, ''

    def repr(self, format=''):
        xStr = self.xPointGen.repr(format)
        yStr = self.yPointGen.repr(format)

        if self.type == 'breakGraphLinear':
            return '%s, %s, %s, (%s), (%s), %s' % (self.type, self.step, self.loop, xStr, yStr, self.pointCount)
        elif self.type == 'breakGraphPower':
            return '%s, %s, %s, (%s), (%s), %s, %s' % (self.type, self.step, self.loop, xStr, yStr, self.pointCount, typeset.anyDataToStr(self.exp))
        elif self.type == 'breakGraphHalfCosine':
            return '%s, %s, %s, (%s), (%s), %s' % (self.type, self.step, self.loop, xStr, yStr, self.pointCount)
        elif self.type == 'breakGraphFlat':
            return '%s, %s, %s, (%s), (%s), %s' % (self.type, self.step, self.loop, xStr, yStr, self.pointCount)

    def reset(self):
        self.xPointGen.reset()
        self.yPointGen.reset()
        self.i = 0 # step always starts at 0

    def __call__(self, t, refDict=None):
        if self.step == 'event': # if use events, not time
            t = self.i
        self.currentValue = self.obj(t) # no ref dict needed; omde object
        # increment after value returned
        if self.step == 'event': # if use steps, not time
            self.i = self.i + 1
        return self.currentValue


class BreakGraphLinear(_BreakGraph):
    def __init__(self, args, refDict):
        _BreakGraph.__init__(self, args, refDict) # call base init
        self.type = 'breakGraphLinear'
        # modify the default args to hide the exponent incongruity
        self.argDefaults = self.argDefaults[:5]
        self.argNames = ['stepString', 'edgeString', 
                              'parameterObject: x point Generator', 
                              'parameterObject: y point Generator', 'pointCount']
        self.argDemos = []
        self.doc = lang.docPoBgl
        self._setObj()

class BreakGraphPower(_BreakGraph):
    def __init__(self, args, refDict):
        _BreakGraph.__init__(self, args, refDict) # call base init
        self.type = 'breakGraphPower'
        self.argNames = ['stepString', 'edgeString', 
                              'parameterObject: x point Generator', 
                              'parameterObject: y point Generator', 'pointCount', 'exponent']
        self.argDemos = []
        self.doc = lang.docPoBgp
        self._setObj()
        
class BreakGraphHalfCosine(_BreakGraph):
    def __init__(self, args, refDict):
        _BreakGraph.__init__(self, args, refDict) # call base init
        self.type = 'breakGraphHalfCosine'
        # modify the default args to hide the exponent incongruity
        self.argDefaults = self.argDefaults[:5]
        self.argNames = ['stepString', 'edgeString', 
                              'parameterObject: x point Generator', 
                              'parameterObject: y point Generator', 'pointCount']
        self.argDemos = []
        self.doc = lang.docPoBghc
        self._setObj()

class BreakGraphFlat(_BreakGraph):
    def __init__(self, args, refDict):
        _BreakGraph.__init__(self, args, refDict) # call base init
        self.type = 'breakGraphFlat'
        # modify the default args to hide the exponent incongruity
        self.argDefaults = self.argDefaults[:5]
        self.argNames = ['stepString', 'edgeString', 
                              'parameterObject: x point Generator', 
                              'parameterObject: y point Generator', 'pointCount']
        self.argDemos = []
        self.doc = lang.docPoBgf
        self._setObj()
        







#-----------------------------------------------------------------||||||||||||--
# a dynamic line generator

class LineSegment(basePmtr.Parameter):
    def __init__(self, args, refDict):

        """creates score

        >>> from athenaCL.libATH.libPmtr import parameter
        >>> a = parameter.factory(['ls', 'e', 10, 0, 5])
        """
        basePmtr.Parameter.__init__(self, args, refDict) # call base init

        self.type = 'lineSegment'
        # args are: stepString, 
        self.argTypes = [['int', 'str'], ['num','list'], 
                         ['num','list'], ['num','list']]
        self.argDefaults = ['e', 10, 0, 5]
        self.argNames = ['stepString', 'parameterObject: secPerCycle', 
                         'min', 'max']
        self.argDemos = [
            ['e',('bg','rc',(4,7,18)),('ru',0,20),('ru',30,50)],
            ['e',('ws','e',5,0,2,15),0,('ru',0,100)],
            ]
        self.doc = lang.docPoLs

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error

        # raises except on error
        self.step = self._stepControlParser(self.args[0]) 
        # get seconds per cycle
        self.spcObj = self._loadAutoConstant(self.args[1])
        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.i = 0 # counter 
        self.xStart = None
        self.xEnd = None

    def _genPoints(self, refDict, t):
        """determine how many points need to generated; collecting in points list"""
        i = t
        self.xStart = i # i becomes xStart
        lineSpan = self.spcObj(i, refDict)
        if lineSpan == 0: # try  another point
            lineSpan = self.spcObj(i, refDict)
        if lineSpan == 0:
            raise error

        self.xEnd = self.xStart + lineSpan
        yStart = self.minObj(i, refDict)
        yEnd = self.maxObj(i, refDict)
        # one segment
        points = [(self.xStart, yStart), (self.xEnd, yEnd)]
        # check values to make sure they are numbers
        if not drawer.isNum(points[0][0]) or not drawer.isNum(points[0][1]):
            return 0, 'all point values must be numbers.'
        self.obj = bpf.LinearSegment(points, periodic=1)
        return 1, '' # all good

    def checkArgs(self):
        ok, msg = self.spcObj.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.minObj.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.maxObj.checkArgs()
        if not ok: return 0, msg    
        return 1, ''

    def repr(self, format=''):
        spcStr = self.spcObj.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return '%s, (%s), (%s), (%s)' % (self.type, spcStr, minStr, maxStr)
 
    def reset(self):
        self.spcObj.reset()
        self.minObj.reset()
        self.maxObj.reset()
        self.i = 0 # step always starts at 0

    def __call__(self, t, refDict=None):
        if self.step == 'event': # if use events, not time
            t = self.i

        if self.xStart == None or t >= self.xEnd or t < self.xStart:
            self._genPoints(refDict, t) # refresh points and object

        self.currentValue = self.obj(t) # no ref dict needed; omde object
        # increment after value returned
        if self.step == 'event': # if use steps, not time
            self.i = self.i + 1
        return self.currentValue




#-----------------------------------------------------------------||||||||||||--
# from possible envelope generator subclass

#     def _scrubPoints(self):
#         """fix all ordered point pairs:
#         if one point is given, duplicate it at a greater x
#         remove duplicate x positions, sort"""
#         rawPoints = copy.deepcopy(self.points)
#         scrubPoints = []
#         xPoints = []
#         if len(rawPoints) == 0:
#             return 0, 'add points to create a break point.'
#         for pair in rawPoints:
#             if x not in xPoints:
#                 xPoints.append(x)
#                 scrubPoints.append((x,y))
#             else: # an x for this value has already been found
#                 pass
#         scrubPoints.sort() # put in order
#         if len(scrubPoints) == 0:
#             return 0, 'no valid point pairs given.'
#         self.points = scrubPoints
# 
#         return 1, '' # all good 



class EnvelopeGeneratorTrapezoid(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = 'envelopeGeneratorTrapezoid'

        self.argTypes = [['str'], ['int', 'str'], 'int', 
                                  'list', 'list', 'list', 'list', 'list', 
                                 ['num','list'], ['num','list']]
        self.argNames = ['scaleString', 'edgeString', 'eventCount', 
                              'parameterObject: duration Generator', 
                              'parameterObject: ramp up Generator', 
                              'parameterObject: width max Generator', 
                              'parameterObject: ramp down Generator', 
                              'parameterObject: width min Generator', 
                              'min', 'max']

        self.argDefaults = ['proportional','l', 100,
                                 ['c', 40], # dur
                                 ['c',.5],
                                 ['c',4],
                                 ['c',2],
                                 ['c',4],
                                    0, 1]
        self.argDemos = [
            ['p','l',100,('bg','oc',(60,40,20)),('bg','oc',(1,5,10)),('c',6),('c',8),('c',2)],
            ['a','l',100,('bg','oc',(60,40,20)),('bg','oc',(1,5,10)),('c',6),('c',8),('c',2)],
                             ]
        self.doc = lang.docPoEgt

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error

        # proportional absolute switch
        self.propAbsSwitch = self._scaleSwitchParser(self.args[0]) 
        self.loop = self._loopControlParser(self.args[1]) # raises except on error
        self.eventCount = self.args[2]

        self.durGen = self._loadSub(self.args[3], 'genPmtrObjs')
        self.rampUp = self._loadSub(self.args[4], 'genPmtrObjs')
        self.widthMax = self._loadSub(self.args[5], 'genPmtrObjs')
        self.rampDown = self._loadSub(self.args[6], 'genPmtrObjs')
        self.widthMin = self._loadSub(self.args[7], 'genPmtrObjs')

        self.minObj, self.maxObj = self._loadMinMax(self.args[8], self.args[9])

        self.points = None
        # gen points, scrub, and sort
        ok, msg = self._genPoints(refDict)
        if ok != 1: raise error
        self.obj = None #assigned in subclass
        self._setObj()


    def _genPoints(self, refDict):
        """determine how many points need to generated; collectin in points list"""
        self.points = []
        t = 0 # rel time position
        for i in range(self.eventCount):
            dur = self.durGen(t, refDict)
            rampUp = self.rampUp(t, refDict)
            rampDown = self.rampDown(t, refDict)
            widthMax = self.widthMax(t, refDict)
            widthMin = self.widthMin(t, refDict)
            min = self.minObj(t, refDict)
            max = self.maxObj(t, refDict)

            coord = envelope.durToTrapezoid(t, self.propAbsSwitch, dur, 
                              rampUp, widthMax, rampDown, widthMin, min, max)
            self.points = self.points + coord
            t = t + dur
        return 1, '' # all good


    def _setObj(self):
        if self.loop == 'loop': # either loop or single
            loopArg = 1
        else: loopArg = 0
        self.obj = bpf.LinearSegment(self.points, periodic=loopArg)


    def checkArgs(self):
        if self.eventCount <= 0:
            return 0, 'eventCount error: must be greater than zero.'

        ok, msg = self.durGen.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.rampUp.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.widthMax.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.rampDown.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.widthMin.checkArgs()
        if not ok: return 0, msg    

        ok, msg = self.minObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1: return ok, msg

        return 1, ''


    def repr(self, format=''):
        durGen = self.durGen.repr(format)
        rampUp = self.rampUp.repr(format)
        widthMax = self.widthMax.repr(format)
        rampDown = self.rampDown.repr(format)
        widthMin = self.widthMin.repr(format)
        minObj = self.minObj.repr(format)
        maxObj = self.maxObj.repr(format)

        return '%s, %s, %s, %s, (%s), (%s), (%s), (%s), (%s), (%s), (%s)' % (self.type, self.propAbsSwitch, self.loop, self.eventCount, 
        durGen, rampUp, widthMax, rampDown, widthMin, minObj, maxObj)

    def reset(self):
        self.durGen.reset()
        self.rampUp.reset()
        self.widthMax.reset()
        self.rampDown.reset()
        self.widthMin.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t, refDict=None):
        self.currentValue = self.obj(t) # no ref dict needed; omde object
        return self.currentValue




#-----------------------------------------------------------------||||||||||||--
class EnvelopeGeneratorUnit(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = 'envelopeGeneratorUnit'

        self.argTypes = [['int', 'str'], 'int', 
                                  'list', 'list', 'list', 
                                 ['num','list'], ['num','list']]
        self.argNames = ['edgeString', 'eventCount', 
                              'parameterObject: duration Generator', 
                              'parameterObject: sustain center unit Generator', 
                              'parameterObject: sustain width unit Generator', 
                              'min', 'max']

        self.argDefaults = ['l', 100,
                                 ['c', 40], # dur
                                 ['c',.4],
                                 ['c',.2],
                                    0, 1]
        self.argDemos = [
 ['l',100,('bg','oc',(60,40,20)),('bg','oc',(.1,.4,.6)),('bg','oc',(.1,.5,.8))],

                             ]
        self.doc = lang.docPoEgu

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error

        # proportional absolute switch
        self.loop = self._loopControlParser(self.args[0]) # raises except on error
        self.eventCount = self.args[1]

        self.durGen = self._loadSub(self.args[2], 'genPmtrObjs')
        self.center = self._loadSub(self.args[3], 'genPmtrObjs')
        self.width = self._loadSub(self.args[4], 'genPmtrObjs')

        self.minObj, self.maxObj = self._loadMinMax(self.args[5], self.args[6])

        self.points = None
        # gen points, scrub, and sort
        ok, msg = self._genPoints(refDict)
        if ok != 1: raise error
        self.obj = None #assigned in subclass
        self._setObj()


    def _genPoints(self, refDict):
        """determine how many points need to generated; collectin in points list"""
        self.points = []
        t = 0 # rel time position
        for i in range(self.eventCount):
            dur = self.durGen(t, refDict)
            center = self.center(t, refDict)
            width = self.width(t, refDict)
            min = self.minObj(t, refDict)
            max = self.maxObj(t, refDict)

            coord = envelope.durToUnit(t, dur, center, width, min, max)
            self.points = self.points + coord
            t = t + dur
        return 1, '' # all good


    def _setObj(self):
        if self.loop == 'loop': # either loop or single
            loopArg = 1
        else: loopArg = 0
        self.obj = bpf.LinearSegment(self.points, periodic=loopArg)


    def checkArgs(self):
        if self.eventCount <= 0:
            return 0, 'eventCount error: must be greater than zero.'

        ok, msg = self.durGen.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.center.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.width.checkArgs()
        if not ok: return 0, msg    

        ok, msg = self.minObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1: return ok, msg

        return 1, ''


    def repr(self, format=''):
        durGen = self.durGen.repr(format)
        center = self.center.repr(format)
        width = self.width.repr(format)
        minObj = self.minObj.repr(format)
        maxObj = self.maxObj.repr(format)

        return '%s, %s, %s, (%s), (%s), (%s), (%s), (%s)' % (self.type, self.loop, self.eventCount, durGen, center, width, minObj, maxObj)

    def reset(self):
        self.durGen.reset()
        self.center.reset()
        self.width.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t, refDict=None):
        self.currentValue = self.obj(t) # no ref dict needed; omde object
        return self.currentValue



#-----------------------------------------------------------------||||||||||||--
class EnvelopeGeneratorAdsr(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = 'envelopeGeneratorAdsr'

        self.argTypes = [['str'], ['int', 'str'], 'int', 
                                  'list', 'list', 'list', 'list', 'list', 'list',
                                 ['num','list'], ['num','list']]
        self.argNames = ['scaleString', 'edgeString', 'eventCount', 
                              'parameterObject: duration Generator', 
                              'parameterObject: attack Generator', 
                              'parameterObject: decay Generator', 
                              'parameterObject: sustain Generator', 
                              'parameterObject: release Generator', 
                              'parameterObject: sustain scalar Generator', 
                              'min', 'max']

        self.argDefaults = ['proportional','l', 100,
                                 ['c', 40], # dur
                                 ['c',2],
                                 ['c',4],
                                 ['c',2],
                                 ['c',4],
                                 ['c',.5],
                                    0, 1]
        self.argDemos = [
             ['p','l',100,('bg','oc',(60,40,20)),('bg','oc',(1,5,10)),('bg','oc',(10,5,1)),('c',6),('c',2),('bg','oc',(.2,.5,.7))],
             ['a','l',100,('bg','oc',(60,40,20)),('bg','oc',(1,5,10)),('bg','oc',(10,5,1)),('c',6),('c',2),('bg','oc',(.2,.5,.7))],
                             ]
        self.doc = lang.docPoEga

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error # report error

        # proportional absolute switch
        self.propAbsSwitch = self._scaleSwitchParser(self.args[0]) 
        self.loop = self._loopControlParser(self.args[1]) # raises except on error
        self.eventCount = self.args[2]

        self.durGen = self._loadSub(self.args[3], 'genPmtrObjs')
        self.attack = self._loadSub(self.args[4], 'genPmtrObjs')
        self.decay = self._loadSub(self.args[5], 'genPmtrObjs')
        self.sustain = self._loadSub(self.args[6], 'genPmtrObjs')
        self.release = self._loadSub(self.args[7], 'genPmtrObjs')
        self.susScalar = self._loadSub(self.args[8], 'genPmtrObjs')

        self.minObj, self.maxObj = self._loadMinMax(self.args[9], self.args[10])

        self.points = None
        # gen points, scrub, and sort
        ok, msg = self._genPoints(refDict)
        if ok != 1: raise error
        self.obj = None #assigned in subclass
        self._setObj()


    def _genPoints(self, refDict):
        """determine how many points need to generated; collectin in points list"""
        self.points = []
        t = 0 # rel time position
        for i in range(self.eventCount):
            dur = self.durGen(t, refDict)
            attack = self.attack(t, refDict)
            decay = self.decay(t, refDict)
            sustain = self.sustain(t, refDict)
            release = self.release(t, refDict)
            susScalar = self.susScalar(t, refDict)
            min = self.minObj(t, refDict)
            max = self.maxObj(t, refDict)

            coord = envelope.durToAdsr(t, self.propAbsSwitch, dur, 
                              attack, decay, sustain, release, susScalar, min, max)
            self.points = self.points + coord
            t = t + dur
        return 1, '' # all good


    def _setObj(self):
        if self.loop == 'loop': # either loop or single
            loopArg = 1
        else: loopArg = 0
        self.obj = bpf.LinearSegment(self.points, periodic=loopArg)


    def checkArgs(self):
        if self.eventCount <= 0:
            return 0, 'eventCount error: must be greater than zero.'

        ok, msg = self.durGen.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.attack.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.decay.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.sustain.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.release.checkArgs()
        if not ok: return 0, msg    
        ok, msg = self.susScalar.checkArgs()
        if not ok: return 0, msg    

        ok, msg = self.minObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1: return ok, msg

        return 1, ''


    def repr(self, format=''):
        durGen = self.durGen.repr(format)
        attack = self.attack.repr(format)
        decay = self.decay.repr(format)
        sustain = self.sustain.repr(format)
        release = self.release.repr(format)  
        susScalar = self.susScalar.repr(format)  
        minObj = self.minObj.repr(format)
        maxObj = self.maxObj.repr(format)

        return '%s, %s, %s, %s, (%s), (%s), (%s), (%s), (%s), (%s), (%s), (%s)' % (self.type, self.propAbsSwitch, self.loop, self.eventCount, 
        durGen, attack, decay, sustain, release, susScalar, minObj, maxObj)

    def reset(self):
        self.durGen.reset()
        self.attack.reset()
        self.decay.reset()
        self.sustain.reset()
        self.release.reset()
        self.susScalar.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t, refDict=None):
        self.currentValue = self.obj(t) # no ref dict needed; omde object
        return self.currentValue





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
