#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          baseOrc.py
# Purpose:       base classes for orchestra defs, instriment defs.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--
from athenaCL.libATH import drawer
_MOD = 'baseOrc.py'

class Orchestra:
    """subclass from which all orchestas inherit
    provides representation of an orchestra, including what instruments
    are available, instrument defaults
    
    NOTE: the orchesta encapsulates instrument objects
    no direct access to instrument objects should be give: always go through
    orchestra object
    
    this orchestra, as 'generic', is used by EngineAudioFile to
    limit amp values; assumes native unit interval representation
    """

    def __init__(self):
        self.name = None
        self._instrNumbers = None # access w/ methods, not by looking at this attr
    #-----------------------------------------------------------------------||--
    # public interface methods    
    def instNoValid(self, iNo):
        """test if an instrument number is valid"""
        return drawer.isInt(iNo)
        
    def instNoList(self, format=None):
        """return a list of instrument numbers; if
        a list is not availabe, return None
        if format is specified 'user', return in a  user readable format"""
        return self.instrNumbers
        
    def constructOrc(self, noChannels=2, instList=None):
        """returns string of orchestra, if file based"""
        return None

    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        optional arg for iNo gives data just for on inst
        also return a list of available values"""
        return None, None

    def getInstPreset(self, iNo, auxNo=None):
        """returns a dictionary of default values for one instrument
        convert 'pmtr7' labels to 'auxQ0' labels
        aux values must be labeled starting at auxQ0"""
        return None
        
    def getInstName(self, iNo):
        'returns a string'
        return None

    def getInstAuxNo(self, iNo):
        'return aux no for named instrument'
        return None

    def getInstPmtrInfo(self, iNo, pmtrNo):
        """for specified inst, pmtrNo, return pmtr info"""
        return None
        
    #-----------------------------------------------------------------------||--
    # orcMapMode determines if values are scaled or left alone
    # ('mix' refers to mixing-like values: pan, amp, pitch)
    # assume pan and amp are b/n 0 and 1; pitch is in psReal
    # instruments define a minimum scaling w/ 'force'
    # optional scaling is done w/ mix
    # this may be done on a per-instrument basis, or done just for the complete
    # orchestra
    
    
    # other names: orcMap, postMap
    # perhaps call orcMap to user, postMap w/n objects?
    # for post-event mapping?
    def postMap(self, iNo, pmtr, val, orcMapMode=1):
        """baseClass method used as public interface by all subclasses
        orcMapMode=1 means that mix maps are done
        0 means that only limit methods are called
        psReal values alrea _always_ mapped
        """
        if pmtr == 'amp': # map amp
            val = self._postMapAmp(iNo, val, orcMapMode)
        elif pmtr == 'pan': # map pan
            val = self._postMapPan(iNo, val, orcMapMode) # always limit
        elif pmtr == 'ps': # ALWAYS map psReal values, regardless of orcMapMode
            val = self._postMapPs(iNo, val)
        else: # this shoudl never happen
            raise ValueError, 'bad parameter name in orchestra'
        return val
        
    #-----------------------------------------------------------------------||--
    # mappings of psReal, amp, pan; only applied of mix mode is on
    # mapings done before limits
    def _postMapPs(self, iNo, val):
        return val
        
    def _postMapAmp(self, iNo, val, orcMapMode=1):
        if orcMapMode: # mapping
            if val < 0: val = 0 # limit b/n 0 and 1
            elif val > 1: val = 1
        # limiting
        if val < 0: val = 0 # we can assume tt amps are never negative
        return val
        
    def _postMapPan(self, iNo, val, orcMapMode=1):
        if orcMapMode:
            val = val % 1.0 # modulo around 1
        return val


#-----------------------------------------------------------------||||||||||||--
class Instrument:
    """implementation free instrument model
    handles conversions of parameter labels
    NOTE: insturment objects should always be accessed through an orchestra
    """
    def __init__(self, auxNo=None):
        self.name = 'generic' # name can be specified if subclased
        # to shift from label representation 7, 8, to data rep: 0, 1
        self.pmtrCountDefault = 6 # 6 built in values
        # this value may be overriden by sub-class, or provided as an arg
        self.auxNo = auxNo # number of additional parameters over default
        self.pmtrInfo = {}
        self.pmtrDefault = {}
        # parameters tt store amplitude and paning mix scaling values
        # each instrument may provide a triple of min, max values
        # and data for a non-linear mapping, if need.
        # values provided here are real-values, post conversion, for the inst
        # not all orcs/instruments will use these
        self.postMapPs = None # supplied just for order 
        self.postMapAmp = (0,1, 'linear') 
        self.postMapPan = (0,1, 'linear') 

    def getPresetDict(self):
        """note: auxQs are represented minus 7, so as to appear as needed, 
        starting at auxQ0"""
        presetDict = {} # default values are set in TMclass.loadDefault
        # this corrects the labeling of aux fields to reflext that used later on
        for key in self.pmtrDefault.keys(): # isolate pmtr fields
            if key[:4] == 'pmtr': # rename pmtr keys to a single auxQ
                adjNum = int(key[4:]) - (self.pmtrCountDefault + 1)  # 7 = 0
                newKey  = 'auxQ%i' % adjNum
                presetDict[newKey] = self.pmtrDefault[key]
            else: # standard key
                presetDict[key] = self.pmtrDefault[key]
        return presetDict

    def getPostMapAmpMax(self):
        """utility to get max amplitude as set in postMap
        post-ut needs this information"""
        return self.postMapAmp[1]









