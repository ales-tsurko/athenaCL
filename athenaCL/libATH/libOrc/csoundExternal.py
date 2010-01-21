#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          csoundExternal.py
# Purpose:       external csound instrument definitions instruments.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

from athenaCL.libATH import drawer
from athenaCL.libATH import pitchTools
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH.libOrc import baseOrc


#-----------------------------------------------------------------||||||||||||--
class CsoundExternal(baseOrc.Orchestra):
    """a generic csound instrument with variable aux numbers
    """
    def __init__(self):
        baseOrc.Orchestra.__init__(self)
        self.name = 'csoundExternal'
        # not sure what this value should be...
        # six is the default for csoundNative
        self.pmtrCountDefault = 6         
        self._instrNumbers = None # any integer is acceptable
        # set a default aux as 1
        self._dummyInst = InstrumentCsoundExternal(1)

    def instNoValid(self, iNo):
        """test if an instrument number is valid"""
        return drawer.isInt(iNo)
        
    def instNoList(self, format=None):
        """return a list of instrument numbers; if
        a list is not availabe, return None"""
        if format == 'user':
            return None # None is correct as no inst specified
        return self._instrNumbers
        

    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        pmtrFields includes 6 default values
        """
        # always return the same data, as all instruments are the same
        if iNo == None:
            instrList = [1] # just provide one defaultw
        else:
            instrList = [iNo,]
        instInfoDict = {}
        for number in instrList:
            instInfoDict[number] = (self._dummyInst.name, 
                                            self._dummyInst.pmtrFields,
                                            self._dummyInst.pmtrInfo) 
        return instInfoDict, instrList

    def getInstPreset(self, iNo, auxNo=None):
        """"""
        assert auxNo != None # must be provided
        # provide auxNo as aregument, setting internal to appropriate aux value
        self._dummyInst = InstrumentCsoundExternal(auxNo)
        return self._dummyInst.getPresetDict() # will returns empty dict

    def getInstName(self, iNo):
        return self._dummyInst.name

    def getInstAuxNo(self, iNo):
        return self._dummyInst.auxNo
        
    def getInstPmtrInfo(self, iNo, pmtrNo):
        """for specified inst, pmtrNo, return pmtr info"""
        # do not distingusih by iNo, pmtrNo
        # there should always be an auxQ0
        return self._dummyInst.pmtrInfo['auxQ0']

    # no postMap functions here:
    # built-in amp/pan/pitch values are not placed into a csound external score
    # nothign to do with postMap values


#-----------------------------------------------------------------||||||||||||--
class InstrumentCsoundExternal(baseOrc.Instrument):
    def __init__(self, auxNo=1): # supply auxNo
        baseOrc.Instrument.__init__(self, auxNo)
        # not sure what this value should be...
        # six is the default for csoundNative
        self.pmtrCountDefault = 6         
        self.auxNo = auxNo
        
        self.pmtrInfo = {}
        self.pmtrDefault = {}
        defaultStr = 'unknown parameter'
        defaultPmtr = ('constant', 1)
        
        # for as many aux values, provide values
        for i in range(0, self.auxNo):
            key = 'auxQ%s' % i
            self.pmtrDefault[key] = defaultPmtr
            self.pmtrInfo[key] = defaultStr
            
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        






#-----------------------------------------------------------------||||||||||||--
class CsoundSilence(baseOrc.Orchestra):
    """using goggins silence w/ athenaCL csound instruments
    """
    def __init__(self):
        baseOrc.Orchestra.__init__(self)
        self.name = 'csoundSilence'
        self._instrNumbers = None # any integer is acceptable
        self._dummyInst = InstrumentCsoundSilence()

    def instNoValid(self, iNo):
        """test if an instrument number is valid"""
        return drawer.isInt(iNo)
        
    def instNoList(self, format=None):
        """return a list of instrument numbers; if
        a list is not availabe, return None"""
        if format == 'user':
            return None # None is correct as no list possible
        return self._instrNumbers
        
    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        pmtrFields includes 6 default values
        """
        if iNo == None:
            instrList = [1,] # only return 1 if nothing supplied
        else:
            instrList = [iNo,]
        instInfoDict = {}
        for number in instrList:
            instInfoDict[number] = (self._dummyInst.name, 
                                            self._dummyInst.pmtrFields,
                                            self._dummyInst.pmtrInfo) 
        return instInfoDict, instrList

    def getInstPreset(self, iNo, auxNo=None):
        return self._dummyInst.getPresetDict() # will returns empty dict

    def getInstName(self, iNo):
        return self._dummyInst.name

    def getInstAuxNo(self, iNo):
        return self._dummyInst.auxNo
        
    def getInstPmtrInfo(self, iNo, pmtrNo):
        """for specified inst, pmtrNo, return pmtr info"""
        # do not distingusih by iNo
        key = 'auxQ%s' % pmtrNo
        return self._dummyInst.pmtrInfo[key]
        
        
    # assume amp is midiAmps
    # assume pan is floating point 0 to 1
    #-----------------------------------------------------------------------||--
    # mappings of psReal, amp, pan; only applied of mix mode is on
    def _postMapPs(self, iNo, val):
        val = pitchTools.psToMidi(val, 'noLimit')
        return val

    # use floating point midi amp values
    def _postMapAmp(self, iNo, val, orcMapMode=1):
        val = val * 127.0
        if val < 0: val = 0 # we can assume tt amps are never negative
        return val

    def _postMapPan(self, iNo, val, orcMapMode=1):  # assume b/n 0 and 1
        if val < 0 or val > 1: val = val % 1.0
        return val
        
#-----------------------------------------------------------------||||||||||||--
class InstrumentCsoundSilence(baseOrc.Instrument):
    def __init__(self, auxNo=4): # aux value from here
        baseOrc.Instrument.__init__(self, auxNo)
        self.pmtrInfo = {
                          'auxQ0'   : 'phase', 
                          'auxQ1'   : 'y pan depth',     
                          'auxQ2'  : 'z pan depth', 
                          'auxQ3'  : 'mason index, pitch class set',      
                         } # holds discription, preset for each pmtr in a dictionary
        self.pmtrDefault = {
                          'auxQ0'   : ('constant', 1), 
                          'auxQ1'   : ('constant', .5),
                          'auxQ2'   : ('constant', .5),  
                          'auxQ3'   : ('pathRead', 'mason'),        
                         } 
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        

#-----------------------------------------------------------------||||||||||||--
