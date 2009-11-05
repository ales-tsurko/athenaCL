#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          orc.py
# Purpose:       public factory for getting orc objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

from athenaCL.libATH import drawer
from athenaCL.libATH import language
lang = language.LangObj()

from athenaCL.libATH.libOrc import csoundNative
from athenaCL.libATH.libOrc import csoundExternal
from athenaCL.libATH.libOrc import generalMidi
from athenaCL.libATH.libOrc import baseOrc

orcNames = {
    'g'   :'generic' ,
    'ce'      :'csoundExternal' ,
    'cn'      :'csoundNative' ,
    'cs'      :'csoundSilence',
    'gm'      :'generalMidi',
    'gmp'     :'generalMidiPercussion',
    }

# orcIncompat delcared in baseOrc and included as internal attribute
# for each orc


#-----------------------------------------------------------------||||||||||||--
def orcTypeParser(typeName):
    """utility functions for parsing user paramter strings into proper
    parameter names. accepts short names and long names, regardless of case
    does not raise an error if no match: returns string unmodified
    """
    return drawer.acronymExpand(typeName, orcNames) # may be none

def factory(orcName):
    orcName = orcTypeParser(orcName)
    assert orcName != None
    if orcName == 'generic': # only used wtih audioFile format
        return baseOrc.Orchestra() # get the base orchestra
    elif orcName == 'csoundNative':
        return csoundNative.CsoundNative()
    elif orcName == 'generalMidi':
        return generalMidi.GeneralMidi()
    elif orcName == 'generalMidiPercussion':
        return generalMidi.GeneralMidiPercussion()
    elif orcName == 'csoundSilence':
        return csoundExternal.CsoundSilence()
    elif orcName == 'csoundExternal':
        return csoundExternal.CsoundExternal()
    else:
        raise ValueError, 'bad orchestra name: %s' % orcName

#-----------------------------------------------------------------||||||||||||--

# run tests
class Test:
    def __init__(self):
        # call test methods
        for orcName in orcNames.keys():
            a = factory(orcName)
            print
            print a.name
            a.getInstInfo()
    
            if a.instNoList() != None:
                for iNo in a.instNoList():
                    print str(iNo).ljust(4), a.getInstName(iNo)
                    a.getInstPreset(iNo)
    
            a.constructOrc()

if __name__ == '__main__':
    Test()

