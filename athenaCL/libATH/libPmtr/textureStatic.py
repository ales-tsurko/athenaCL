#-----------------------------------------------------------------||||||||||||--
# Name:          textureStatic.py
# Purpose:       parameter objects for internal text options.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import error
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH import language
lang = language.LangObj()

_MOD = 'textureStatic.py'
#-----------------------------------------------------------------||||||||||||--

class ParallelMotionList(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'parallelMotionList'
        self.doc = lang.docPoPml
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) #base init
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['list', 'num']
        self.argNames = ['transpositionList', 'timeDelay']
        self.argDefaults = [[], .0]
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        for item in self.switch('transpositionList'):
            if not drawer.isNum(item):
                return 0, 'elements in transpositionList must be numbers.'
        if self.switch('timeDelay') < 0:
            msg = 'timeDelay must be greater than or equal to zero.'
            return 0, msg
        return 1, ''

    # repr and __call__ defined in parent class

#-----------------------------------------------------------------||||||||||||--

class OrnamentLibrarySelect(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'ornamentLibrarySelect'
        self.doc = lang.docPoOls
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str']
        self.argNames = ['libraryName: chromaticGroupC, diatonicGroupA, diatonicGroupB, microGroupA, microGroupB, microGroupC, trillGroupA, off']
        self.argDefaults = ['diatonicGroupA']
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # update available library names?
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        if self.switch('libraryName') not in self.refDict['ornGroupNames']:
            ornNames = drawer.listScrub(self.refDict['ornGroupNames'], 
                                                 None, 'noQuote')
            msg = 'enter an appropriate ornament library name: %s.' % ornNames
            return 0, msg
        return 1, ''

    # repr and __call__ defined in parent class

#-----------------------------------------------------------------||||||||||||--

class OrnamentMaxDensity(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'ornamentMaxDensity'
        self.doc = lang.docPoOmd
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['num']
        self.argDefaults = [1,]
        self.argNames = ['percent',]
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        # note: user drawer precent utility here to accept macro percent values
        if self.switch('percent') < 0 or self.switch('percent') > 1:
            msg = 'ornamentMaxDensity must be between 0 and 1.'
            return 0, msg
        return 1, ''

    # repr and __call__ defined in parent class

#-----------------------------------------------------------------||||||||||||--
# simple numeric po: just get a single value

class MaxTimeOffset(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'maxTimeOffset'
        self.doc = lang.docPoMto
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) # call base 
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['num']
        self.argNames = ['time',]
        self.argDefaults = [.025]
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        if self.switch('time') < 0:
            msg = 'time must be greater than or equal to zero.'
            return 0, msg
        return 1, ''

    # repr and __call__ defined in parent class

class TotalEventCount(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'totalEventCount'
        self.doc = lang.docPoTec
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) # call base 
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['num']
        self.argNames = ['count']
        self.argDefaults = [20]
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        if self.switch('count') <= 0:
            msg = 'eventCount must be greater than zero.'
            return 0, msg
        return 1, ''

    # repr and __call__ defined in parent class


#-----------------------------------------------------------------||||||||||||--
# select from multiple strings
class _Selector(basePmtr.StaticParameterTexture):
    """a base clase for creating simple selectors"""
    def __init__(self, args, refDict):
        basePmtr.StaticParameterTexture.__init__(self, args, refDict)
        # arg types exclude name of parameter: just data arg
        self.argTypes = [['str'],]
        self.argNames = ['selectionString',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._selectorParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        return 1, ''

class PitchSelectorControl(_Selector):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'pitchSelectorControl'
        self.doc = lang.docPoPsc
        self.argDefaults = ['randomPermutate',]
        _Selector.__init__(self, args, refDict) # call base init

class MultisetSelectorControl(_Selector):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'multisetSelectorControl'
        self.doc = lang.docPoMsc
        self.argDefaults = ['randomPermutate',]
        _Selector.__init__(self, args, refDict) # call base init



#-----------------------------------------------------------------||||||||||||--
# on off pmtr

class _SwitchOnOff(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        basePmtr.StaticParameterTexture.__init__(self, args, refDict)
        # arg types exclude name of parameter: just data arg
        self.argTypes = [['str','int'],]
        self.argNames = ['onOff',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._onOffParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        return 1, ''


class LoopWithinSet(_SwitchOnOff):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'loopWithinSet'
        self.doc = lang.docPoLws
        self.argDefaults = ['on',] # should be on, as may be a single note path
        _SwitchOnOff.__init__(self, args, refDict) # call base init

class PathDurationFraction(_SwitchOnOff):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'pathDurationFraction'
        self.doc = lang.docPoPdf
        self.argDefaults = ['on',] # should be on, as may be a single note path
        _SwitchOnOff.__init__(self, args, refDict) # call base init

class SnapSustainTime(_SwitchOnOff):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'snapSustainTime'
        self.doc = lang.docPoSst
        self.argDefaults = ['on',] 
        _SwitchOnOff.__init__(self, args, refDict) # call base init

class SnapEventTime(_SwitchOnOff):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'snapEventTime'
        self.doc = lang.docPoSet
        self.argDefaults = ['on',] 
        _SwitchOnOff.__init__(self, args, refDict) # call base init

class ParameterInterpolationControl(_SwitchOnOff):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'parameterInterpolationControl'
        self.doc = lang.docPoPic
        self.argDefaults = ['on',] 
        _SwitchOnOff.__init__(self, args, refDict) # call base init


#-----------------------------------------------------------------||||||||||||--
# control switch level for octave and field control

class _SwitchLevelMonophonic(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str',]
        self.argNames = ['level: set, event',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._selectLevelMonophonicParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        return 1, ''

    # repr and __call__ defined in parent class

class LevelFieldMonophonic(_SwitchLevelMonophonic):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'levelFieldMonophonic'
        self.doc = lang.docPoLfm
        self.argDefaults = ['event',]
        _SwitchLevelMonophonic.__init__(self, args, refDict) # call base init

class LevelOctaveMonophonic(_SwitchLevelMonophonic):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'levelOctaveMonophonic'
        self.doc = lang.docPoLom
        self.argDefaults = ['event',] # default for octave is usually event
        _SwitchLevelMonophonic.__init__(self, args, refDict) # call base init


#-----------------------------------------------------------------||||||||||||--
# control switch level for octave and field control

class _SwitchLevelPolyphonic(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) 
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str',]
        self.argNames = ['level: set, event, voice',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._selectLevelPolyphonicParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        return 1, ''

    # repr and __call__ defined in parent class

class LevelFieldPolyphonic(_SwitchLevelPolyphonic):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'levelFieldPolyphonic'
        self.doc = lang.docPoLfp
        self.argDefaults = ['event',]
        _SwitchLevelPolyphonic.__init__(self, args, refDict) # call base init

class LevelOctavePolyphonic(_SwitchLevelPolyphonic):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'levelOctavePolyphonic'
        self.doc = lang.docPoLop
        self.argDefaults = ['event',] # default for octave is usually event
        _SwitchLevelPolyphonic.__init__(self, args, refDict) # call base init


#-----------------------------------------------------------------||||||||||||--
# control switch level for between frames and events

class _SwitchLevelFrame(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) 
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str',]
        self.argNames = ['level: event, frame',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._selectLevelFrameParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        return 1, ''

    # repr and __call__ defined in parent class

class LevelFrameDuration(_SwitchLevelFrame):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'levelFrameDuration'
        self.doc = lang.docPoLfd
        self.argDefaults = ['event',]
        _SwitchLevelFrame.__init__(self, args, refDict) # call base init




#-----------------------------------------------------------------||||||||||||--
class LevelEventPartition(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        self.type = 'levelEventPartition'
        self.doc = lang.docPoLep
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str',]
        self.argNames = ['level: set, path',]
        self.argDefaults = ['path',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._selectLevelPartitionParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def _selectLevelPartitionParser(self, usrStr):
        "decode control choice strings"
        ref = {
            'path' : ['p'],
            'set' : ['s'],
                }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError, 'bad control value: enter %s.' % selStr
        return usrStr

    def checkArgs(self):
        return 1, ''


class EventDensityPartition(basePmtr.StaticParameterTexture):

    def __init__(self, args, refDict):
        # below called before all parent classes
        self.type = 'eventDensityPartition'
        self.doc = lang.docPoEdp        
        basePmtr.StaticParameterTexture.__init__(self, args, refDict)
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str']
        self.argNames = ['level: duration, set',]
        self.argDefaults = ['duration',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._selectDensityPartitionParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def _selectDensityPartitionParser(self, usrStr):
        "decode control choice strings"
        ref = {
            'duration' : ['d', 'dur'],
            'set' : ['s'],
                }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError, 'bad control value: enter %s.' % selStr
        return usrStr

    def checkArgs(self):
        return 1, ''


class LevelEventCount(basePmtr.StaticParameterTexture):
        
    def __init__(self, args, refDict):
        # below called before all parent classes
        self.type = 'levelEventCount'
        self.doc = lang.docPoLec        
        basePmtr.StaticParameterTexture.__init__(self, args, refDict)
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str']
        self.argNames = ['level: segment, texture',]
        self.argDefaults = ['segment',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._selectLevelEventCountParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def _selectLevelEventCountParser(self, usrStr):
        "decode control choice strings"
        ref = {
            'texture' : ['t', 'text', 'texture'],
            'segment' : ['s', 'seg', 'segment'],
                }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError, 'bad control value: enter %s.' % selStr
        return usrStr

    def checkArgs(self):
        return 1, ''


class TotalSegmentCount(basePmtr.StaticParameterTexture):
        
    def __init__(self, args, refDict):
        # below called before all parent classes
        self.type = 'totalSegmentCount'
        self.doc = lang.docPoTsc
        basePmtr.StaticParameterTexture.__init__(self, args, refDict)
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['num']
        self.argNames = ['count']
        self.argDefaults = [10]
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        if self.switch('count') <= 0:
            msg = 'eventCount must be greater than zero.'
            return 0, msg
        return 1, ''



class InterpolationMethodControl(basePmtr.StaticParameterTexture):
    def __init__(self, args, refDict):
        self.type = 'interpolationMethodControl'
        self.doc = lang.docPoImc
        basePmtr.StaticParameterTexture.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str',]
        self.argNames = ['method: linear, halfCosine, power',]
        self.argDefaults = ['linear',]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        # will raise exception on error
        self.args[0] = self._interpolationMethodControlParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def _interpolationMethodControlParser(self, usrStr):
        "decode control choice strings"
        ref = {
            'linear' : ['l'],
            'halfCosine' : ['h', 'c', 'hc'],
            'power' : ['p', 'e', 'exp'],
                }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError, 'bad control value: enter %s.' % selStr
        return usrStr

    def checkArgs(self):
        return 1, ''

















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