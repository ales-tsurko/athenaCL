#-----------------------------------------------------------------||||||||||||--
# Name:          cloneStatic.py
# Purpose:       parameter objects for internal clone options.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import unittest, doctest


from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH import language
from athenaCL.libATH import error
lang = language.LangObj()

_MOD = 'cloneStatic.py'
#-----------------------------------------------------------------||||||||||||--


#-----------------------------------------------------------------||||||||||||--

class TimeReferenceSource(basePmtr.StaticParameterClone):
    def __init__(self, args, refDict):
        """
        """
        # note: define type first for first arg check arg checking
        self.type = 'timeReferenceSource'
        self.doc = lang.docPoTrs
        basePmtr.StaticParameterClone.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str']
        self.argDefaults = ['textureTime']
        # the name of this argument (name) should be changed if possible
        self.argNames = ['name: cloneTime, textureTime']
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        self.args[0] = self._selectTimeRefParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        return 1, ''

    # repr and __call__ defined in parent class

class RetrogradeMethodToggle(basePmtr.StaticParameterClone):
    def __init__(self, args, refDict):
        # note: define type first for first arg check arg checking
        self.type = 'retrogradeMethodToggle'
        self.doc = lang.docPoRmt
        basePmtr.StaticParameterClone.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = ['str']
        self.argDefaults = ['off']
        self.argNames = ['name: timeInverse, eventInverse, off',]
        # check raw arguments for number, typtimeDelaye
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError(msg) # report error
        self.args[0] = self._selectRetrogradeParser(self.args[0])
        # must call update switches to fill internal dictionary
        self._updateSwitches()

    def checkArgs(self):
        return 1, ''

    # repr and __call__ defined in parent class





#-----------------------------------------------------------------||||||||||||--
# on off pmtr, not yet used for clones

class _SwitchOnOff(basePmtr.StaticParameterClone):
    def __init__(self, args, refDict):
        basePmtr.StaticParameterClone.__init__(self, args, refDict) # call base
        # arg types exclude name of parameter: just data arg
        self.argTypes = [['str','int'],]
        self.argDefaults = ['off']
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

    # repr and __call__ defined in parent class









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







