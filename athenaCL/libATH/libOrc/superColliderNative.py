#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          superColliderNative.py
# Purpose:       native csound instrument definitions instruments.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import time
import unittest, doctest

from athenaCL.libATH import drawer
from athenaCL.libATH import language
from athenaCL.libATH import pitchTools
lang = language.LangObj()
from athenaCL.libATH.libOrc import baseOrc


class SuperColliderNative(baseOrc.Orchestra):
    """built-in csound instruments"""
    def __init__(self):
        baseOrc.Orchestra.__init__(self)

        self.name = 'superColliderNative'
        self.srcStr = None # string representation for writing

        self._instrNumbers = [0]
        
        # on initialization, load a dictionary of objects for use
        self._instrObjDict = {}
        globalDict = globals()
        for iNo in self._instrNumbers:
            objAttr = globalDict['Inst%i' % iNo]
            self._instrObjDict[iNo] = objAttr() # instantiate obj
        

    #-----------------------------------------------------------------------||--
    def instNoValid(self, iNo):
        """test if an instrument number is valid"""
        if drawer.isInt(iNo) and iNo in self._instrNumbers:
            return 1
        else:
            return 0

    def instNoList(self, format=None):
        """return a list of instrument numbers; if
        a list is not availabe, return None"""
        if format == 'user':
            return drawer.listToStr(self._instrNumbers)
        return self._instrNumbers

    def _orcTitle(self):
        msg = []
        msg.append(';athenaCL\n')
        msg.append(';%s\n' % lang.msgAthURL)
        msg.append((';%s\n\n' % time.asctime(time.localtime())))
        return ''.join(msg)

    def _getInstObj(self, iNo):
        if iNo in self._instrObjDict.keys(): # already loaded
            return self._instrObjDict[iNo] # call attribute of module to get object
        else:
            raise ValueError, 'bad insturment number given: %s' % iNo
            

    def constructOrc(self, noChannels=2, instList=None):
        """buildes a string of an entire orchestra
        provides proper header and output sections based on 
        number of channels
        """
        self.noChannels = noChannels
        msg = []
        msg.append(self._orcTitle())

        #self.instrObjDict = {}
        if instList == None: # if not given, add all instruments
            instList = self.instNoList()
        for number in instList:
            if not self.instNoValid(number):
                print lang.WARN, 'instrument %i not available.' % number
                continue
            instrObj = self._getInstObj(number)
            msg.append(instrObj.buildInstrDef(noChannels))
        self.srcStr = ''.join(msg)

    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        pmtrFields includes 6 default values
        """
        if iNo == None:
            instrList = self.instNoList() # use method
        else:
            instrList = [iNo,]
        #self.instrObjDict = {} # this used to store inst obj data
        instInfoDict = {}
        for number in instrList:
            instrObj = self._getInstObj(number)
            instInfoDict[number] = (instrObj.name, 
                                            instrObj.pmtrFields,
                                            instrObj.pmtrInfo)
        return instInfoDict, instrList

    def getInstPreset(self, iNo, auxNo=None):
        """returns a dictionary of default values for one instrument"""
        instrObj = self._getInstObj(iNo)
        presetDict = instrObj.getPresetDict() # converts to aux0 fist pos
        return presetDict

    def getInstName(self, iNo):
        'returns a string of name'
        instrObj = self._getInstObj(iNo)
        return instrObj.name

    def getInstAuxNo(self, iNo):
        instrObj = self._getInstObj(iNo)
        return instrObj.auxNo

    def getInstPmtrInfo(self, iNo, pmtrNo):
        """for specified inst, pmtrNo, return pmtr info
        parameter numbers start at 0"""
        instrObj = self._getInstObj(iNo)
        # numbers are shifted by pmtrCountDefault
        # this orchestra uses 'pmtr' instead of 'auxQ'
        key = 'pmtr%s' % (pmtrNo + 1 + instrObj.pmtrCountDefault)
        if instrObj.pmtrInfo != {}:
            return instrObj.pmtrInfo[key]
        else:
            return 'no information available'
        
    #-----------------------------------------------------------------------||--
    def _postMapPs(self, iNo, val):
        return pitchTools.psToPch(val)
        
    def _postMapAmp(self, iNo, val, orcMapMode=1):
        # get max/min amp value form inst, as well as scale factor
        instrObj = self._getInstObj(iNo)
        ampMax = float(instrObj.postMapAmp[1])
        if orcMapMode: # optional map; allow values greater then 1
            val = val * ampMax # temp: assume max amp of 90
        # always limit
        if val < 0: val = 0 # we can assume tt amps are never negative
        return val
        
    def _postMapPan(self, iNo, val, orcMapMode=1):
        if orcMapMode: # optional map
            pass # values are expected b/n 0 and 1
        # always limit: modulo 1    
        if val < 0 or val > 1: val = val % 1.0
        return val


        
        
#-----------------------------------------------------------------||||||||||||--
class InstrumentSuperCollider(baseOrc.Instrument):
    # outputs expect and instrument to have a single final signal, calld "aMixSig
    # this bit of codes gets appended to end of inst def
    def __init__(self):
        """
        >>> a = InstrumentSuperCollider()
        """
        baseOrc.Instrument.__init__(self)
        self.author = 'athenaCL native' # attribution

        self.pmtrCountDefault = 6 # 6 built in values
        self.pmtrFields = self.pmtrCountDefault
        # postMap values for scaling
        self.postMapAmp = (0,1, 'linear') # most amps are in db
        self.postMapPan = (0,1, 'linear')  # all pan values assume 0-1 maping
        
        self.instNo = None
        self.name = None

        # TODO!
        self.monoOutput = """
   Out.ar(0, Pan2.ar(sigPrePan, panPos));
"""
        self.stereoOutput = """
   Out.ar(0, Pan2.ar(sigPrePan, panPos));
"""
        self.quadOutput = """
   Out.ar(0, Pan2.ar(sigPrePan, panPos));
"""

    def getInstFooter(self):
        msg = """ }).writeDefFile;
s.sendSynthDef("%s");
""" % self.name
        return msg

    def buildInstrDef(self, noChannels):
        """returns a string of all the code needed for this instrument

        >>> a = Inst0()
        >>> post = a.buildInstrDef(2)
        >>> "SynthDef" in post
        True
        >>> a.stereoOutput in post
        True
        """
        self.noChannels = noChannels

        msg = []
        msg.append(self.orcCode)
        if self.noChannels == 1:
            msg.append(self.monoOutput)
        elif self.noChannels == 2:
            msg.append(self.stereoOutput)
        elif self.noChannels == 4:
            msg.append(self.quadOutput)
        msg.append(self.getInstFooter())
        return ''.join(msg)



#-----------------------------------------------------------------||||||||||||--
class Inst0(InstrumentSuperCollider):
    def __init__(self):
        """
        >>> a = Inst0()
        """
        InstrumentSuperCollider.__init__(self)

        self.instNo = 0
        self.name = 'noiseBasic'
        self.info = 'A simple noise instrument.'
        self.auxNo = 3
        self.postMapAmp = (0, 1, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 100),
          }
        self.author = 'athenaCL native' # attribution

        self.orcCode = """
SynthDef("%s", {arg dur, ampMax, pan, attackPercent; 
   var env, amp, gate, panPos, sigPrePan;
   panPos = (pan*2)-1; // convert from 0 to 1 to -1 to 1
   gate = Line.ar(1, 0, dur, doneAction: 2);
   env = Env.perc(attackPercent, dur*attackPercent, ampMax, -4);
   amp = EnvGen.kr(env, gate);
   sigPrePan = WhiteNoise.ar(amp);
""" % self.name




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