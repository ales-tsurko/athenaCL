#-----------------------------------------------------------------||||||||||||--
# Name:          cloneFilter.py
# Purpose:       definitions of all paramater objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import copy
import unittest, doctest


from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import quantize
from athenaCL.libATH import unit
from athenaCL.libATH import error
from athenaCL.libATH import typeset

from athenaCL.libATH.libPmtr import basePmtr
_MOD = 'cloneFilter.py'



#-----------------------------------------------------------------||||||||||||--
class Bypass(basePmtr.FilterParameter):
    def __init__(self, args, refDictArray):
        """
        """
        basePmtr.FilterParameter.__init__(self, args, refDictArray) 
        self.type = 'bypass'
        self.doc = lang.docPoB
        self.argTypes = [] # no args to bypass
        self.argNames = []
        self.argDefaults = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = ('num', 'str') # declare outputFmt as num by default
        self.inputFmt = ('num', 'str') # declare outputFmt as num by default

    def checkArgs(self):
        return 1, '' 

    def repr(self, format=''):
        return '%s' % (self.type)

    def __call__(self, valArray, tArray, refDictArray):
        """bypass does not change any values"""
        return valArray


#-----------------------------------------------------------------||||||||||||--
class OrderBackward(basePmtr.FilterParameter):
    def __init__(self, args, refDictArray):
        """
        """
        basePmtr.FilterParameter.__init__(self, args, refDictArray) 
        self.type = 'orderBackward'
        self.doc = lang.docPoOb
        self.argTypes = [] # no args to bypass
        self.argNames = []
        self.argDefaults = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = ('num', 'str') # declare outputFmt as num by default
        self.inputFmt = ('num', 'str') # declare outputFmt as num by default

    def checkArgs(self):
        return 1, '' 

    def repr(self, format=''):
        return '%s' % (self.type)

    def __call__(self, valArray, tArray, refDictArray):
        """reverse values

        for some reason this test does not run when running all tests
        >>> #from athenaCL.libATH.libPmtr import cloneFilter
        >>> #a = cloneFilter.OrderBackward('', {})
        >>> #a([3,4,5], [0,1,2], {})
        [5, 4, 3]
        """
        self.currentValue = copy.copy(valArray)
        self.currentValue.reverse()
        return self.currentValue


#-----------------------------------------------------------------||||||||||||--
class OrderRotate(basePmtr.FilterParameter):
    def __init__(self, args, refDictArray):
        basePmtr.FilterParameter.__init__(self, args, refDictArray) 
        self.type = 'orderRotate'
        self.doc = lang.docPoOr
        self.argTypes = ['int'] # no args to bypass
        self.argNames = ['rotationSize']
        self.argDefaults = [40]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = ('num', 'str') # declare outputFmt as num by default
        self.inputFmt = ('num', 'str') # declare outputFmt as num by default
        self.steps = self.args[0]

    def checkArgs(self):
        if self.steps <= 0:
            return 0, 'number of rotation steps must be greater than 0'
        return 1, '' 

    def repr(self, format=''):
        return '%s, %s' % (self.type, self.steps)

    def __call__(self, valArray, tArray, refDictArray):
        """reverse values"""
        cut = self.steps % len(valArray) 
        self.currentValue = copy.copy(valArray)
        self.currentValue = self.currentValue[cut:] + self.currentValue[:cut] 
        return self.currentValue

#-----------------------------------------------------------------||||||||||||--
class PipeLine(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = 'pipeLine'
        self.doc = lang.docPoPl
        self.argTypes = ['list']
        self.argNames = ['filterParameterObjectList: a list of sequential Filter ParameterObjects']
        self.argDefaults = [[['or', 40], ['ob']]]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = ['num', 'str'] # declare outputFmt as num by default
        from athenaCL.libATH.libPmtr import parameter
        
        self.objArray = []
        for argList in self.args[0]:
            try:
                pmtrObj = parameter.factory(argList, 'filterPmtrObjs')
            except error.ParameterObjectSyntaxError as msg:
                raise error.ParameterObjectSyntaxError('failed sub-parameter: %s' % msg)
            self.objArray.append(pmtrObj)

    def checkArgs(self):
        # make sure all parameter objects are filters
        for obj in self.objArray:
            if obj.parent != 'cloneFilter':
                return 0, 'all sub ParameterObjects must be a filter.'
            ok, msg = obj.checkArgs()
            if not ok: return 0, msg
        return 1, '' 
        
    def repr(self, format=''):
        subPmtr = []
        for obj in self.objArray:
            subPmtr.append('(%s)' % (obj.repr(format)))
        return '%s, (%s)' % (self.type, ', '.join(subPmtr))

    def reset(self):
        for obj in self.objArray:
            obj.reset()

    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        
        valScrub = copy.copy(valArray) # dont use valArray; make a copy
        
        for obj in self.objArray:
            # check that current array is as long as the original
            assert len(valScrub) == len(valArray)
            valAccum = []
            valAccum = obj(valScrub, tArray, refDictArray)
            valScrub = copy.copy(valAccum)          
        self.currentValue = valScrub
        return self.currentValue


#-----------------------------------------------------------------||||||||||||--
class FilterQuantize(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = 'filterQuantize'
        self.doc = lang.docPoFq
        self.argTypes = ['list', 'list', 'int', 'list']
        self.argNames = [
                        'parameterObject: grid reference value Generator', 
                        'parameterObject: step width Generator', 
                        'stepCount',
                        'parameterObject: unit interval measure of quantize pull',]
        self.argDefaults = [('c', 0), ('c', .25), 1, ('c',1)]
        self.argDemos = [
            [('cg','up',0,1,.0025),('bg','oc',(.4,.6)),2,
                ('bpp','e','l',((0,1),(59,0),(119,1)),-3)]
                             ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = ['num'] # declare outputFmt as num by default
        
        # will raise exception on error
        self.gridRefObj = self._loadSub(self.args[0], 'genPmtrObjs')
        self.stepGenObj = self._loadSub(self.args[1], 'genPmtrObjs')
        self.stepCount = self.args[2]
        self.pullObj = self._loadSub(self.args[3], 'genPmtrObjs')
        self.quantObj = quantize.Quantizer(self.LOOPLIMIT)
        
    def checkArgs(self):
        if self.stepCount <= 0:
            return 0, 'stepCount error: must be greater than zero.'
        ok, msg = self.gridRefObj.checkArgs()
        if ok == 0: return 0, msg
        ok, msg = self.stepGenObj.checkArgs()
        if ok == 0: return 0, msg
        ok, msg = self.pullObj.checkArgs()
        if ok == 0: return 0, msg
        return 1, '' 
        
    def repr(self, format=''):
        g = self.gridRefObj.repr(format)
        s = self.stepGenObj.repr(format)
        p = self.pullObj.repr(format)
        return '%s, (%s), (%s), %s, (%s)' % (self.type, g,
                     s, typeset.anyDataToStr(self.stepCount), p)

    def reset(self):
        self.gridRefObj.reset()
        self.stepGenObj.reset()
        self.pullObj.reset()

    def _buildGrid(self, t, refDict):
        # this is a grid of interval steps, not absoulte weights
        # only need a few steps; quantizer will take care of rest
        # po in used to build grid has a constant t
        grid = []
        for i in range(self.stepCount):
            # potential problem for time-based parameter objects
            # supply i instead of t, get at least steps
            q = self.stepGenObj(i, refDict)
            if q == 0: continue # no use in a 0 width grid
            grid.append(abs(q))
        # accept redundant values, always take in order
        if grid == []: # this is a problem
            print(lang.WARN, self.type, 'supplying grid with default values')
            grid.append(1) # give it something
        return grid

    def __call__(self, valArray, tArray, refDictArray):
         # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(len(valArray)):
            val = valArray[i]
            t = tArray[i]
            refDict = refDictArray[i]
            self.quantObj.updateGrid(self._buildGrid(t, refDict)) 
            g = self.gridRefObj(t, refDict)
            p = self.pullObj(t, refDict)
            self.currentValue.append(self.quantObj.attract(val, p, g))               
        return self.currentValue

#-----------------------------------------------------------------||||||||||||--
class FilterFunnelBinary(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = 'filterFunnelBinary'
        self.doc = lang.docPoFfb
        self.argTypes = ['str', 'list', 'list', 'list']
        self.argNames = ['thresholdMatchString: upper, lower, match',
                              'parameterObject: threshold', 
                              'parameterObject: first boundary', 
                              'parameterObject: second boundary']
        self.argDefaults = ['u',('bpl', 'e', 's', ((0,0),(120,1))), 
                           ('ws','e',60,0,.5,0),('wc','e',90,0,.5,1),]
        self.argDemos = [ ['m', ('c', .2), ('bpl','e','l',((0,0),(60,.5))),
                                      ('bpl','e','l',((0,1),(60,.5))),],     
                                ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = ['num'] # declare outputFmt as num by default
        
        # will raise exceptio on error
        self.thresholdMatch = self._thresholdMatchParser(self.args[0]) 
        self.thresholdPmtrObj = self._loadSub(self.args[1], 'genPmtrObjs')
        self.boundingPmtrObjA = self._loadSub(self.args[2], 'genPmtrObjs')
        self.boundingPmtrObjB = self._loadSub(self.args[3], 'genPmtrObjs')

    def checkArgs(self):
        # make sure all parameter objects are filters
        ok, msg = self.thresholdPmtrObj.checkArgs()
        if ok == 0: return 0, msg
        ok, msg = self.boundingPmtrObjA.checkArgs()
        if ok == 0: return 0, msg
        ok, msg = self.boundingPmtrObjB.checkArgs()
        if ok == 0: return 0, msg
        return 1, '' 
        
    def repr(self, format=''):
        h = self.thresholdPmtrObj.repr(format)
        a = self.boundingPmtrObjA.repr(format)
        b = self.boundingPmtrObjB.repr(format)
        return '%s, %s, (%s), (%s), (%s)' % (self.type, 
            self.thresholdMatch, h, a, b)

    def reset(self):
        self.thresholdPmtrObj.reset()
        self.boundingPmtrObjA.reset()
        self.boundingPmtrObjB.reset()

    def __call__(self, valArray, tArray, refDictArray):
         # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(len(valArray)):
            val = valArray[i]
            t = tArray[i]
            refDict = refDictArray[i]
            h = self.thresholdPmtrObj(t, refDict)
            a = self.boundingPmtrObjA(t, refDict)
            b = self.boundingPmtrObjB(t, refDict)
            self.currentValue.append(quantize.funnelBinary(h, a, b, val,
                                      self.thresholdMatch))
        return self.currentValue


#-----------------------------------------------------------------||||||||||||--
class MaskFilter(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = 'maskFilter'
        self.doc = lang.docPoMf
        self.argTypes = ['str', 'list', 'list']
        self.argNames = [
                        'boundaryString: limit, wrap, reflect',
                        'parameterObject: first boundary', 
                        'parameterObject: second boundary', 
                        ]
        self.argDefaults = ['l',('ws','e',60,0,.5,0),('wc','e',90,0,.5,1)]
        self.argDemos = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = ['num'] # declare outputFmt as num by default
        
        # will raise exception on error
        self.boundaryMethod = self._boundaryParser(self.args[0]) 
        self.boundingPmtrObjA = self._loadSub(self.args[1], 'genPmtrObjs')
        self.boundingPmtrObjB = self._loadSub(self.args[2], 'genPmtrObjs')
        
    def checkArgs(self):
        ok, msg = self.boundingPmtrObjA.checkArgs()
        if ok == 0: return 0, msg
        ok, msg = self.boundingPmtrObjB.checkArgs()
        if ok == 0: return 0, msg
        return 1, '' 
        
    def repr(self, format=''):
        a = self.boundingPmtrObjA.repr(format)
        b = self.boundingPmtrObjB.repr(format)
        return '%s, %s, (%s), (%s)' % (self.type, self.boundaryMethod, a, b)

    def reset(self):
        self.boundingPmtrObjA.reset()
        self.boundingPmtrObjB.reset()

    def __call__(self, valArray, tArray, refDictArray):
         # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(len(valArray)):
            val = valArray[i]
            t = tArray[i]
            refDict = refDictArray[i]
            # get parameter obj values
            a = self.boundingPmtrObjA(t, refDict)
            b = self.boundingPmtrObjB(t, refDict)
            self.currentValue.append(unit.boundaryFit(a, b, val, 
                                            self.boundaryMethod))
        # return list of values
        return self.currentValue


#-----------------------------------------------------------------||||||||||||--
class MaskScaleFilter(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = 'maskScaleFilter'
        self.doc = lang.docPoMsf
        self.argTypes = [ ['num','list'],  ['num','list'], 'str']
        self.argNames = [
                        'min',
                        'max', 
                        'selectionString', 
                        ]
        self.argDefaults = [('ws','e',60,0,.5,0),('wc','e',90,0,.5,1),'rc']
        self.argDemos = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = ['num'] # declare outputFmt as num by default
        
        # will raise exception on error
        self.minObj, self.maxObj = self._loadMinMax(self.args[0], self.args[1])
        self.control = self._selectorParser(self.args[2]) # raises exception

    def checkArgs(self):
        ok, msg = self.minObj.checkArgs()
        if ok != 1: return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1: return ok, msg
        return 1, '' 
        
    def repr(self, format=''):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return '%s, (%s), (%s), %s' % (self.type, minStr, maxStr, self.control)

    def reset(self):
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, valArray, tArray, refDictArray):
         # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []

        # normalize all values and add to selector w/ pre-defiend
        normSeries = unit.unitNormRange(valArray)
        selector = basePmtr.Selector(normSeries, self.control)

        for i in range(len(valArray)):
            val = valArray[i] # original value
            t = tArray[i]
            refDict = refDictArray[i]
            # get normalized val from selector, remap b/n min and max
            postVal = unit.denorm(selector(), 
                         self.minObj(t, refDict),   self.maxObj(t, refDict))
            self.currentValue.append(postVal)

        # return list of values
        return self.currentValue


#-----------------------------------------------------------------||||||||||||--
class Replace(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = 'replace'
        self.doc = lang.docPoR
        self.argTypes = ['list']
        self.argNames = ['parameterObject: generator to replace original values']
        self.argDefaults = [('ru', 0, 1)]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = ['num', 'str'] # declare outputFmt as num by default
        from athenaCL.libATH.libPmtr import parameter
        try:
            self.pmtrObj = parameter.factory(self.args[0])
        except error.ParameterObjectSyntaxError as msg:
            raise error.ParameterObjectSyntaxError('failed sub-parameter: %s' % msg)

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if ok == 0: return 0, msg
        return 1, '' 

    def repr(self, format=''):
        pmtrStr = self.pmtrObj.repr(format)
        return '%s, (%s)' % (self.type, pmtrStr)

    def reset(self):
        self.pmtrObj.reset()


    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(len(valArray)):
            # ref dict should always have bpm gotten from src esObj
            if self.pmtrObj.parent == 'rhythm': # 3 values return, use dur
                dur, sus, acc = self.pmtrObj(tArray[i], refDictArray[i])
                x = dur
            else:
                x = self.pmtrObj(tArray[i], refDictArray[i])
            self.currentValue.append(x)
        return self.currentValue



#-----------------------------------------------------------------||||||||||||--
class _FilterOperator(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = None
        self.argTypes = ['list']
        self.argNames = ['parameterObject: operator value generator']
        self.argDefaults = [('ws', 'e', 30, 0, 0, 1)]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = 'num' # declare outputFmt as num by default
        from athenaCL.libATH.libPmtr import parameter
        try: # note: can be eithe gen or filter parameter object
            self.pmtrObj = parameter.factory(self.args[0], 
                                            [ 'genPmtrObjs','rthmPmtrObjs'])
        except error.ParameterObjectSyntaxError as msg:
            raise error.ParameterObjectSyntaxError('failed sub-parameter: %s' % msg)

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if ok == 0: return 0, msg
        return 1, '' 

    def repr(self, format=''):
        pmtrStr = self.pmtrObj.repr(format)
        return '%s, (%s)' % (self.type, pmtrStr)

    def reset(self):
        self.pmtrObj.reset()


class FilterAdd(_FilterOperator):
    def __init__(self, args, refDict):
        _FilterOperator.__init__(self, args, refDict) # call base init
        self.type = 'filterAdd'
        self.doc = lang.docPoFa

    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(0, len(valArray)):
            # ref dict should always have bpm gotten from src esObj
            if self.pmtrObj.parent == 'rhythm': # 3 values return, use dur
                dur, sus, acc = self.pmtrObj(tArray[i], refDictArray[i])
                x = dur
            else:
                x = self.pmtrObj(tArray[i], refDictArray[i])
            self.currentValue.append(valArray[i] + x)
        return self.currentValue

class FilterMultiply(_FilterOperator):
    def __init__(self, args, refDict):
        _FilterOperator.__init__(self, args, refDict) # call base init
        self.type = 'filterMultiply'
        self.doc = lang.docPoFm

    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(0, len(valArray)):
            # ref dict should always have bpm gotten from src esObj
            if self.pmtrObj.parent == 'rhythm': # 3 values return, use dur
                dur, sus, acc = self.pmtrObj(tArray[i], refDictArray[i])
                x = dur
            else:
                x = self.pmtrObj(tArray[i], refDictArray[i])
            self.currentValue.append(valArray[i] * x)
        return self.currentValue

class FilterDivide(_FilterOperator):
    def __init__(self, args, refDict):
        _FilterOperator.__init__(self, args, refDict) # call base init
        self.type = 'filterDivide'
        self.doc = lang.docPoFd

    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(0, len(valArray)):
            # ref dict should always have bpm gotten from src esObj
            if self.pmtrObj.parent == 'rhythm': # 3 values return, use dur
                dur, sus, acc = self.pmtrObj(tArray[i], refDictArray[i])
                x = dur
            else:
                x = self.pmtrObj(tArray[i], refDictArray[i])
            try:
                self.currentValue.append(valArray[i] / float(x))
            except ZeroDivisionError: # bypass on zero div error
                self.currentValue.append(valArray[i])
        return self.currentValue


class FilterPower(_FilterOperator):
    def __init__(self, args, refDict):
        _FilterOperator.__init__(self, args, refDict) # call base init
        self.type = 'filterPower'
        self.doc = lang.docPoFp

    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        # process each value
        self.currentValue = []
        for i in range(0, len(valArray)):
            # ref dict should always have bpm gotten from src esObj
            if self.pmtrObj.parent == 'rhythm': # 3 values return, use dur
                dur, sus, acc = self.pmtrObj(tArray[i], refDictArray[i])
                x = dur
            else:
                x = self.pmtrObj(tArray[i], refDictArray[i])
            self.currentValue.append(pow(valArray[i],x))
        return self.currentValue




#-----------------------------------------------------------------||||||||||||--
class _FilterOperatorAnchor(basePmtr.FilterParameter):
    def __init__(self, args, refDict):
        basePmtr.FilterParameter.__init__(self, args, refDict) # call base init
        self.type = None
        self.argTypes = ['str', 'list']
        self.argNames = ['anchorString', 
                              'parameterObject: operator value generator']
        self.argDefaults = ['lower', ('wc', 'e', 30, 0, 0, 1)]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.outputFmt = 'num' # declare outputFmt as num by default
        self.inputFmt = 'num' # declare outputFmt as num by default

        self.anchor = self._anchorParser(self.args[0])
        #print _MOD, 'anchor set to', self.anchor
        from athenaCL.libATH.libPmtr import parameter
        try:
            self.pmtrObj = parameter.factory(self.args[1], 
                                            ['genPmtrObjs', 'rthmPmtrObjs'])
        except error.ParameterObjectSyntaxError as msg:
            raise error.ParameterObjectSyntaxError('failed sub-parameter: %s' % msg)

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if ok == 0: return 0, msg
        return 1, '' 

    def repr(self, format=''):
        pmtrStr = self.pmtrObj.repr(format)
        return '%s, %s, (%s)' % (self.type, self.anchor, pmtrStr)

    def reset(self):
        self.pmtrObj.reset()

    def _calcAnchor(self, valArray):
        array = copy.copy(valArray)
        if self.anchor == 'lower':
            arraySort = copy.copy(array)
            arraySort.sort() # lowest at bottom
            return arraySort[0]
        elif self.anchor == 'upper':
            arraySort = copy.copy(array)
            arraySort.sort() # lowest at bottom
            return arraySort[-1]
        elif self.anchor == 'average':
            sum = 0.0
            for x in array:
                sum = sum + x
            return sum / float(len(array))
        elif self.anchor == 'median':
            if len(array) % 2 == 0: #even
                a = len(array) / 2
                b = a - 1         
                return (array[a] + array[b]) / 2.0
            else: # odd
                i = (len(array) - 1) / 2
                return array[i]

    def _shiftArray(self, valArray, shift):
        newArray = []
        for val in valArray:
            newArray.append(val + shift)
        return newArray



class FilterMultiplyAnchor(_FilterOperatorAnchor):
    """filterMultiplyAnchor, anchor, parameterObject
Arguments: (1) name,(2) anchor string 'lower', 'upper', 'average', or 'median' (3) parameterObject"""

    def __init__(self, args, refDict):
        _FilterOperatorAnchor.__init__(self, args, refDict) # call base init
        self.type = 'filterMultiplyAnchor'
        self.doc = lang.docPoFma

    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        anchorVal = self._calcAnchor(valArray)
        #print _MOD, 'anchor value set to', anchorVal

        # create a shifted array, use negative anchor value
        shiftArray = self._shiftArray(valArray, -anchorVal)
        # process each value
        for i in range(0, len(shiftArray)):
            # ref dict should always have bpm gotten from src esObj
            if self.pmtrObj.parent == 'rhythm': # 3 values return, use dur
                dur, sus, acc = self.pmtrObj(tArray[i], refDictArray[i])
                x = dur
            else:
                x = self.pmtrObj(tArray[i], refDictArray[i])
            shiftArray[i] = shiftArray[i] * x
        # reshift zero back to where it was
        self.currentValue = self._shiftArray(shiftArray, anchorVal)
        return self.currentValue


class FilterDivideAnchor(_FilterOperatorAnchor):

    def __init__(self, args, refDict):
        _FilterOperatorAnchor.__init__(self, args, refDict) # call base init
        self.type = 'filterDivideAnchor'
        self.doc = lang.docPoFda

    def __call__(self, valArray, tArray, refDictArray):
        # vale and time should always be the same length
        assert (len(valArray) == len(tArray) and 
                  len(tArray) == len(refDictArray))
        anchorVal = self._calcAnchor(valArray)
        #print _MOD, 'anchor value set to', anchorVal

        # create a shifted array, use negative anchor value
        shiftArray = self._shiftArray(valArray, -anchorVal)
        # process each value
        for i in range(0, len(shiftArray)):
            # ref dict should always have bpm gotten from src esObj
            if self.pmtrObj.parent == 'rhythm': # 3 values return, use dur
                dur, sus, acc = self.pmtrObj(tArray[i], refDictArray[i])
                x = dur
            else:
                x = self.pmtrObj(tArray[i], refDictArray[i])
            try:
                shiftArray[i] = shiftArray[i] / float(x)
            except ZeroDivisionError: # bypass on zero div error
                shiftArray[i] = shiftArray[i]
        # reshift zero back to where it was
        self.currentValue = self._shiftArray(shiftArray, anchorVal)
        return self.currentValue







#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    
    def testBasic(self):
        pass
        #a = OrderBackward('', {})
        #self.assertEqual(a([3,4,5], [0,1,2], {}), [5, 4, 3])
        

#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)







