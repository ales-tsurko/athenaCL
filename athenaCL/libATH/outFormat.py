#-----------------------------------------------------------------||||||||||||--
# Name:          outputFormat.py
# Purpose:       simple objects to represent output formats (EventOutputs).
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2005 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import unittest, doctest



from athenaCL.libATH import drawer
from athenaCL.libATH import language
lang = language.LangObj()


# output formats are selected from the EvenOutput commands
# all output formats; not all are available on allplatforms
# independent of orchestra selection methods
# outputs are not the same as outputEngines (some engines handle multiple
# outputs)
outputFormatNames = {
    'af'      :'audioFile',
    'co'      :'csoundOrchestra',
    'cs'      :'csoundScore',
    'cd'      :'csoundData', # csd file; cant select, determined by csound prefs
    'cb'      :'csoundBatch',# batch file for csound processing
    'sct'     :'superColliderTask',
    'mf'      :'midiFile',
    'ts'      :'textSpace',
    'tt'      :'textTab',
#    'mc'      :'maxColl',
    'xao'     :'xmlAthenaObject',
    'at'      :'acToolbox', # textures and clones as sections
    }


def outputFormatParser(typeName):
    """
    does not raise an error if no match: returns string as none

    >>> outputFormatParser('mf')
    'midiFile'
    >>> outputFormatParser('af')
    'audioFile'
    """
    parsed = drawer.acronymExpand(typeName, outputFormatNames)
    if parsed == None: pass
    return parsed

outputExportFormatNames = {
    'af'      :'audioFile',
    'ts'      :'textSpace',
    'tt'      :'textTab',
#    'mc'      :'maxColl',
    }

def outputExportFormatParser(typeName):
    """
    does not raise an error if no match: returns string as none

    >>> outputExportFormatParser('af')
    'audioFile'
    >>> outputExportFormatParser('ts')
    'textSpace'
    """
    parsed = drawer.acronymExpand(typeName, outputExportFormatNames)
    if parsed == None: pass
    return parsed



    
#-----------------------------------------------------------------||||||||||||--

class _OutputFormat(object):

    def __init__(self):
        self.doc = None # raw doc strings appear in command EMv displays
        
    def reprDoc(self):
        msg = []
        msg.append('%s: %s. (%s)' % (self.name, 
                                                      self.doc, self.ext))
        return ''.join(msg)  

        
#-----------------------------------------------------------------||||||||||||--
class FormatAudioFile(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatAudioFile()
        """
        _OutputFormat.__init__(self)
        self.name = 'audioFile'
        self.emKey = 'pathAudioSynth' 
        self.doc = 'Pulse Code Modulation (PCM) file'
        #uses a synth extension to avoid collision w/ csound out
        self.ext = '.synth.aif' 
        
#-----------------------------------------------------------------||||||||||||--
class FormatCsoundOrchestra(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatCsoundOrchestra()
        """
        _OutputFormat.__init__(self)
        self.name = 'csoundOrchestra'
        self.emKey = 'pathOrc'
        self.doc = 'Csound orchestra file'
        self.ext = '.orc'
        
#-----------------------------------------------------------------||||||||||||--
class FormatCsoundScore(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatCsoundScore()
        """
        _OutputFormat.__init__(self)
        self.name = 'csoundScore'
        self.emKey = 'pathSco'
        self.doc = 'Csound score file'
        self.ext = '.sco'
        
#-----------------------------------------------------------------||||||||||||--
class FormatCsoundData(_OutputFormat):
    def __init__(self):
        _OutputFormat.__init__(self)
        """
        >>> a = FormatCsoundData()
        """
        self.name = 'csoundData'
        self.emKey = 'pathCsd'
        self.doc = 'Csound XML unified file format'
        self.ext = '.csd'
        
#-----------------------------------------------------------------||||||||||||--
class FormatCsoundBatch(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatCsoundBatch()
        """
        _OutputFormat.__init__(self)
        self.name = 'csoundBatch'
        self.emKey = 'pathBat'
        self.doc = 'Platform specific script or batch file'
        self.ext = '.bat'
        

#-----------------------------------------------------------------||||||||||||--
class FormatSuperColliderTask(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatSuperColliderTask()
        """
        _OutputFormat.__init__(self)
        self.name = 'scScd'
        self.emKey = 'pathScScd'
        self.doc = 'SuperCollider task data format'
        self.ext = '.scd'


#-----------------------------------------------------------------||||||||||||--
class FormatMidiFile(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatMidiFile()
        """
        _OutputFormat.__init__(self)
        self.name = 'midiFile'
        self.emKey = 'pathMid'
        self.doc = 'Standard MIDI file'
        self.ext = '.mid'
        
#-----------------------------------------------------------------||||||||||||--
class FormatTextSpace(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatTextSpace()
        """
        _OutputFormat.__init__(self)
        self.name = 'textSpace'
        self.emKey = 'pathTxtSpace'
        self.doc = 'Space delimited event list'
        self.ext = '.space.txt'

#-----------------------------------------------------------------||||||||||||--
class FormatTextTab(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatTextTab()
        """
        _OutputFormat.__init__(self)
        self.name = 'textTab'
        self.emKey = 'pathTxtTab'
        self.doc = 'Tab delimited event list'
        self.ext = '.tab.txt'
        
#-----------------------------------------------------------------||||||||||||--
# class FormatMaxColl(_OutputFormat):
#     def __init__(self):
#         """
#         >>> a = FormatMaxColl()
#         """
#         _OutputFormat.__init__(self)
#         self.name = 'maxColl'
#         self.emKey = 'pathMaxColl'
#         self.doc = 'Max coll object data format'
#         self.ext = '.max.txt'

#-----------------------------------------------------------------||||||||||||--
class FormatAcToolbox(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatAcToolbox()
        """
        _OutputFormat.__init__(self)
        self.name = 'acToolbox'
        self.emKey = 'pathAct'
        self.doc = 'AC Toolbox Environment file'
        self.ext = '.act'
                
#-----------------------------------------------------------------||||||||||||--
class FormatXmlAthenaObject(_OutputFormat):
    def __init__(self):
        """
        >>> a = FormatXmlAthenaObject()
        """
        _OutputFormat.__init__(self)
        self.name = 'xmlAthenaObject'
        self.emKey = 'pathXml'
        self.doc = 'athenaCL native XML format'
        self.ext = '.xml'
        








#-----------------------------------------------------------------||||||||||||--
def factory(request):

    # all will get all ouput formats
    if drawer.isStr(request):
        request = drawer.strScrub(request, 'L')
        if request == 'all':
            request = outputFormatNames.values()
        # if other string given, add to a list
        else:
            request = [request]

    # load objects
    reqArray = []
    for name in request:
        name = outputFormatParser(name)
        if name == None: continue
        # user strings have lower case first char w/ format prefix
        className = 'Format' + name[0].upper() + name[1:]
        # get module attribute for class
        modAttr = globals()[className]
        reqArray.append(modAttr())
        
    if len(reqArray) == 1:
        return reqArray[0]
    else:
        return reqArray



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

