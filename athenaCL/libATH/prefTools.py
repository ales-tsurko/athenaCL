#-----------------------------------------------------------------||||||||||||--
# Name:          prefTools.py
# Purpose:       XML tools for reading and writing preference file.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2009 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

    
import xml.dom.minidom
import unittest, doctest

from athenaCL.libATH import drawer
from athenaCL.libATH import xmlTools
from athenaCL.libATH import imageTools # for updating old image names

_MOD = 'prefTools.py'
#-----------------------------------------------------------------||||||||||||--



CSDOFF = 'csdOff'
CSDON    = 'csdOn'
CSTOFF = 'cstOff'
CSTON    = 'cstOn'
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
    >>> a['audioFileFormat']
    'wav'
    """
    # common to all, some may be chagned in patform specific below
    if category == 'external':
        catDict = {
                      'autoRenderOption': 'autoOff', # this is a csound opt
                      'csoundPath': '', # should be name csoundCommand...
                      'csoundCreatorCode': '', # for macos9 only 
                      'midiPlayerPath': '',
                      'midiPlayerCreatorCode': '',
                      'audioPlayerPath': '',
                      'audioPlayerCreatorCode': '',
                      'textReaderPath': '',
                      'textReaderCreatorCode': '',
                      'imageViewerPath': '',
                      'imageViewerCreatorCode': '',
                      'psViewerPath': '',
                      'psViewerCreatorCode': '',
                     }
    if category == 'athena':
        catDict = {'fpLastDir': '', 
                      'fpLastDirSco': '',
                      'tLastVersionCheck': '',
                      'scratch': '', # used for writing temporary files
                      'ssdir': '',
                      'sadir': '',   
                      'eventOutput': "('midiFile', 'xmlAthenaObject')",
                      'eventMode':'csoundNative', # startup value
                      'refreshMode': '1', # esObj refreshing
                      'cursorToolLb': '[',  
                      'cursorToolRb': ']',  
                      'cursorToolLp': '(',  
                      'cursorToolRp': ')',  
                      'cursorToolP' : 'PI',  
                      'cursorToolT' : 'TI',  
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
                      #past: 847564 (132,117,100)
                      'COLORtxUnit': '#8A7A6A',  #138,122,106
                     }

    # platform dependent preferences
    if platform == 'mac': # refers mainly to macos9 mac
        if category == 'external':
            catDict['audioFileFormat'] = 'aif' 
            catDict['csoundCreatorCode'] = 'VRmi' 
        if category == 'athena':
            catDict['dlgVisualMethod'] = 'mac'
            catDict['gfxVisualMethod'] = 'tk' # tk on os9?
        if category == 'gui':
            catDict['fontTitle'] = "('helvetica', 9, 'normal')" 
            catDict['fontText'] = "('monaco', 9, 'normal')" 
    elif platform == 'posix':
        if drawer.isDarwin():
            if category == 'external':
                catDict['audioFileFormat'] = 'aif' 
                catDict['csoundPath'] = '/usr/local/bin/csound'
                catDict['midiPlayerPath'] = '/Applications/QuickTime Player.app'
                catDict['audioPlayerPath'] = '/Applications/QuickTime Player.app'
                catDict['textReaderPath'] = '' # will use system default
                catDict['imageViewerPath'] = ''
                catDict['psViewerPath'] = ''
        else:
            if category == 'external':
                catDict['audioFileFormat'] = 'aif' 
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
        if category == 'gui':
            catDict['fontTitle'] = "('lucida', 10, 'normal')" 
            catDict['fontText'] = "('lucidatypewriter', 10, 'normal')" 

    else: # win or other
        if category == 'external':
            catDict['audioFileFormat'] = 'wav' 
        if category == 'athena':
            catDict['dlgVisualMethod'] = 'text' # works w/n idle, console on win
            catDict['gfxVisualMethod'] = 'tk'
        if category == 'gui':
            catDict['fontTitle'] = "('helvetica', 7, 'normal')" 
            catDict['fontText'] = "('courier', 8, 'normal')" 

    return catDict

def getDefaultDict(platform):
    """ gets all catgtegories for a given platform
         when update prefs, checks default and provides missing value

    >>> a = getDefaultDict('win')
    >>> a['external']['audioFileFormat']
    'wav'
    """
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
        fileFormat renamed audioFileFormat
    """
    defaultPrefDict = getDefaultDict(platform)
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
    oldPrefDict['athena']['gfxVisualMethod'] = imageTools.imageFormatParser(x)
# no longer necessary, as pref optio named changed
#     x = oldPrefDict['external']['audioFileFormat']
#     oldPrefDict['external']['audioFileFormat'] = audioTools.audioFormatParser(x)
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

def getXmlPrefDict(prefFilePath):  
    """open an xml pref file and return a dictionary
    """
    doc = None
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
    f.close() 
    if doc != None:
        procData = xmlTools.xmlToPy(doc)
        return procData['preferences']
    else: # cant load this data, get new data
        return {} # will fice an updates of all prefs






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


