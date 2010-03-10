#-----------------------------------------------------------------||||||||||||--
# Name:          prefTools.py
# Purpose:       XML tools for reading and writing preference file.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

    
import xml.dom.minidom
import unittest, doctest
import tempfile
import os, sys

# limit imports here to only these two modules
from athenaCL.libATH import drawer
from athenaCL.libATH import xmlTools

_MOD = 'prefTools.py'
#-----------------------------------------------------------------||||||||||||--


CSDOFF = 'csdOff'
CSDON  = 'csdOn'
CSTOFF = 'cstOff'
CSTON  = 'cstOn'
AIF = 'AIF'
WAV = 'WAV'
AUTOOFF = 'autoOff'
AUTOON  = 'autoOn'
CURSTOOLON  = 'cursorToolOn'
CURSTOOLOFF = 'cursorToolOff'


def getCategoryDefaultDict(platform, category):
    """ default preference dictionaries
    loaded whem pref.xml missing or used to update
    old pref file. gets only a single catgegory for platform
    
    note: external prefs are read by osTools.openMedia by key value; 
    it is necessary that keys start with the appropriate format strings

    >>> a = getCategoryDefaultDict('win', 'external')
    >>> a['audioFormat']
    'wav'
    >>> a = getCategoryDefaultDict('win', 'athena')
    >>> a['dlgVisualMethod']
    'text'
    >>> a['gfxVisualMethod']
    'tk'
    >>> a = getCategoryDefaultDict('posix', 'athena')
    >>> a['dlgVisualMethod']
    'text'
    >>> a['gfxVisualMethod']
    'png'
    """
    # common to all, some may be chagned in patform specific below
    if category == 'external':
        catDict = {
                      'audioFormat': 'aif', # this is a csound opt
                      'autoRenderOption': 'autoOff', # this is a csound opt
                      'csoundPath': '', # should be name csoundCommand...
                      'midiPlayerPath': '',
                      'audioPlayerPath': '',
                      'textReaderPath': '',
                      'imageViewerPath': '',
                      'psViewerPath': '',
                     }
    if category == 'athena':
        catDict = {
                      'fpLastDir': '', 
                      'fpLastDirEventList': '',
                      'fpScratchDir': '', # used for writing temporary files
                      'fpAudioDir': '',
                      'tLastVersionCheck': '',
                      'eventOutput': "('midiFile', 'xmlAthenaObject', 'csoundData')",
                      'eventMode':'midi', # startup value
                      'refreshMode': '1', # esObj refreshing
                      'debug': '0', 

                      'cursorToolLb': '',  
                      'cursorToolRb': '',  
                      'cursorToolLp': '{',  
                      'cursorToolRp': '}',  
                      'cursorToolP' : 'pi',  
                      'cursorToolT' : 'ti',  
                      'cursorToolOption': 'cursorToolOn',
                      }
    if category == 'gui':
        catDict = {'COLORfgAbs': '#808080',         #128,128,128
                      'COLORfgMain': '#505050',     #80,80,80
                      'COLORfgMainFrame': '#6E6E6E', #110,110,110
                      'COLORfgAlt': '#3C3C3C',          #60,60,60
                      'COLORfgAltFrame': '#5A5A5A', #90,90,90
                      'COLORbgMargin': '#2A2A2A', #42,42,42
                      'COLORbgGrid': '#202020', #32,32,32
                      'COLORbgAbs': '#000000',      #backmost
                      'COLORtxTitle': '#9F9F9F', #'#9A9A9A', #154,154,154
                      'COLORtxLabel': '#7C7C7C', #124,124,124
                      'COLORtxUnit': '#8A7A6A',  #138,122,106
                     }

    if platform == 'posix':
        if drawer.isDarwin():
            if category == 'external':
                catDict['csoundPath'] = '/usr/local/bin/csound'
                catDict['midiPlayerPath'] = '/Applications/QuickTime Player.app'
                catDict['audioPlayerPath'] = '/Applications/QuickTime Player.app'
                catDict['textReaderPath'] = '' # will use system default
                catDict['imageViewerPath'] = '/Applications/Preview.app'
                catDict['psViewerPath'] = '/Applications/Preview.app'
        else:
            if category == 'external':
                catDict['csoundPath'] = '/usr/local/bin/csound'
                catDict['midiPlayerPath'] = 'playmidi'
                catDict['audioPlayerPath'] = 'xmms'
                catDict['textReaderPath'] = 'more' # will use system default
                catDict['imageViewerPath'] = 'imagemagick'
                catDict['psViewerPath'] = 'gs'
        # common for all posix
        if category == 'athena':
            catDict['dlgVisualMethod'] = 'text'
            catDict['gfxVisualMethod'] = 'png' # return to pil

    else: # win or other
        if category == 'external':
            catDict['audioFormat'] = 'wav' 
        if category == 'athena':
            catDict['dlgVisualMethod'] = 'text' # works w/n idle, console on win
            catDict['gfxVisualMethod'] = 'tk'

    return catDict

def getDefaultPrefDict(platform=None):
    """ gets all catgtegories for a given platform
         when update prefs, checks default and provides missing value

    >>> a = getDefaultPrefDict('win')
    >>> a['external']['audioFormat']
    'wav'
    >>> a = getDefaultPrefDict()
    >>> a['athena']['debug']
    '0'
    """
    if platform == None:
        if os.name == 'posix':
            platform = 'posix'
        else:
            platform = 'win'

    prefDict = {}
    prefDict['external'] = getCategoryDefaultDict(platform, 'external')
    prefDict['athena'] = getCategoryDefaultDict(platform, 'athena')
    prefDict['gui']  = getCategoryDefaultDict(platform, 'gui')
    return prefDict

def updatePrefDict(oldPrefDict, platform):
    """check prefs, adds entries missing in newest defaults
    perform backward compatibility for old pref formats here
    this method is caleld only when starting the system
    
    changes:
        csound group renamed to external group
        fileFormat renamed audioFormat
    """
    defaultPrefDict = getDefaultPrefDict(platform)
    categories = ['external', 'athena', 'gui']

    # if missing a category:
    if len(oldPrefDict.keys()) != len(defaultPrefDict.keys()):
        for category in defaultPrefDict.keys():
            if category not in oldPrefDict.keys():
                oldPrefDict[category] = defaultPrefDict[category]

    for catName in categories: # check each key
        # provide backwards compat for changed category names 
        if catName not in oldPrefDict.keys():
            if catName == 'external': 
                oldPrefDict[catName] = oldPrefDict['csound'] 
                del oldPrefDict['csound']
        oldCatKeys = oldPrefDict[catName].keys()
        oldCatKeys.sort() # sort keys and compare
        newCatKeys = defaultPrefDict[catName].keys()
        newCatKeys.sort()
        if not oldCatKeys == newCatKeys:
            for key in newCatKeys:
                if key not in oldCatKeys: # key not found
                    oldPrefDict[catName][key] = defaultPrefDict[catName][key]
            for key in oldCatKeys: 
                if key not in newCatKeys: # remove old keys no long used
                    del oldPrefDict[catName][key]

    # do specific name replacements and changes for backwards compat
    # options user may have selected
    x = oldPrefDict['athena']['gfxVisualMethod']
    oldPrefDict['athena']['gfxVisualMethod'] = drawer.imageFormatParser(x)

    return oldPrefDict

def writePrefDict(prefFilePath, prefDict):
    """given patha and pref, writes as xml file """
    msg = []
    parent = 'preferences'
    msg.append(xmlTools.XMLHEAD)
    msg = msg + xmlTools.pyToXml(parent, 'preferences', prefDict, 0, 
                          [None, 'prefGroup',])   
    f = open(prefFilePath, 'w')
    f.writelines(msg)
    f.close()

def getXmlPrefDict(prefFilePath=None):  
    """open an xml pref file and return a dictionary
    if prefFilePath == None, return a default

    >>> a = getXmlPrefDict(None)
    >>> a['athena']['debug']
    '0'
    """
    doc = None
    if prefFilePath != None:
        f = open(prefFilePath, 'r') 
        try:
            doc = xml.dom.minidom.parse(f)
        # this may be bad, but there could be many errors:
        # xml.parsers.expat.ExpatError
        # xml.sax._exceptions.SAXParseException
        # not worth the risk; just get new prefs
        except: # catch all exceptions
            # cant parse the preference files
            doc = None
        finally:
            f.close() 
    else:
        doc = None
    if doc != None:
        procData = xmlTools.xmlToPy(doc)
        return procData['preferences']
    else: # cant load this data, get new data
        return getDefaultPrefDict() 




class Environment(object):
    """object to store debug stats and print output
    >>> a = Environment()
    """
    def __init__(self, modName=None):
        if modName == None:
            modName = _MOD # set to this module
        self.modName = modName
        self.debug = self.debugStat()

    def debugStat(self):
        """Get the debug preference if available, otherwise zero
        only do this once

        >>> a = Environment()
        >>> post = a.debugStat()
        """
        fp = drawer.getPrefsPath()
        if not os.path.exists(fp):
            return 0
        prefDict = getXmlPrefDict(fp)
        # if fp is not found, this should return a default
        try:
            return int(prefDict['athena']['debug'])
        except: # catch all: this cannot crash
            return 0
    
    def getScratchDirPath(self):
        """Get the scratch preference if available, otherwise return
        None

        Note: this reads from file on each load; this not be efficient

        >>> a = Environment()
        >>> post = a.getScratchDirPath()
        """
        fp = drawer.getPrefsPath()
        if not os.path.exists(fp):
            return None
        prefDict = getXmlPrefDict(fp)
        try:
            fpScratch = prefDict['athena']['fpScratchDir']
        except: # catch all
            fpScratch = ''
        if not os.path.exists(fpScratch) or not os.path.isdir(fpScratch): 
            self.printWarn('scratch directory preference set to a non-directory: %s' % fpScratch)
            fpScratch = '' # do not pass forward        
        # final return
        if fpScratch == '':
            return None
        else:
            return fpScratch

    def _formatMsg(self, msg):
        if not drawer.isList(msg):
            msg = [msg]
        post = []
        post.append('%s:' % self.modName)
        for part in msg:
            partMsg = str(part)
            if drawer.isList(part):
                partMsg = partMsg.replace(' ', '')
            post.append(partMsg)
        post.append('\n')
        return ' '.join(post)
    
    def printWarn(self, msg):
        """always print
        """
        sys.stderr.write(self._formatMsg(msg))

    def printDebug(self, msg, *arguments):
        if self.debug <= 0:
            return # do nothing    
        else:
            if not drawer.isList(msg):
                msg = [msg]
            if len(arguments) > 0:
                msg += arguments
            sys.stderr.write(self._formatMsg(msg))


    def getTempFile(self, suffix='', fileNameTimeStamp=True):
        '''Return a file path to a temporary file with the specified suffix
    
        This uses the directory set as a preference if possible.

        Ths always returns as file path, whether or not a pref is set
        '''
        fpSrc = self.getScratchDirPath() 
        if fpSrc == None: # if it does not exist or cannot be found
            if os.name == 'posix':
                fd, fp = tempfile.mkstemp(suffix=suffix) 
                if isinstance(fd, int):
                    pass # see comment below
                else:
                    fd.close()
            else: # win
                if sys.hexversion < 0x02030000:
                    raise Exception("cannot create temporary file")
                else:
                    tf = tempfile.NamedTemporaryFile(suffix=suffix)
                    fp = tf.name
                    tf.close()
        else:
            if not os.path.exists(fpSrc):    
                # cannot continue at all w/o this directory
                raise Exception('user-specified scratch directory (%s) does not exists.' % fpSrc)

            # option to generate file name with a time stamp
            # and place in the scratch dir
            if fileNameTimeStamp == True:
                fp = os.path.join(fpSrc, drawer.tempFileName(suffix))
            else:
                if os.name == 'posix':
                    fd, fp = tempfile.mkstemp(dir=fpSrc, suffix=suffix)
                    if isinstance(fd, int):
                        # on MacOS, fd returns an int, like 3, when called
                        pass
                    else:
                        fd.close() 
                else: # win
                    if sys.hexversion < 0x02030000:
                        raise Exception("cannot create temporary file")
                    else:
                        tf = tempfile.NamedTemporaryFile(dir=fpSrc, 
                                    suffix=suffix)
                        fp = tf.name
                        tf.close()
        self.printDebug(['temporary file:', fp])
        return fp







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


