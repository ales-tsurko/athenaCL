# -----------------------------------------------------------------||||||||||||--
# Name:          prefTools.py
# Purpose:       XML tools for reading and writing preference file.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import unittest
import tempfile
import os, sys

# limit imports here to only these two modules
from athenaCL.libATH import drawer
from athenaCL.libATH import xmlTools
from xmlToolsExt import xmlToPy

_MOD = "prefTools.py"
# -----------------------------------------------------------------||||||||||||--


CSDOFF = "csdOff"
CSDON = "csdOn"
CSTOFF = "cstOff"
CSTON = "cstOn"
AIF = "AIF"
WAV = "WAV"
AUTOOFF = "autoOff"
AUTOON = "autoOn"
CURSTOOLON = "cursorToolOn"
CURSTOOLOFF = "cursorToolOff"


def getCategoryDefaultDict(platform, category):
    """default preference dictionaries
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
    >>> a = getCategoryDefaultDict('posix', 'athena')
    >>> a['dlgVisualMethod']
    'text'
    """
    # common to all, some may be chagned in patform specific below
    if category == "external":
        catDict = {
            "audioFormat": "aif",  # this is a csound opt
            "autoRenderOption": "autoOff",  # this is a csound opt
            "csoundPath": "",  # should be name csoundCommand...
            "midiPlayerPath": "",
            "audioPlayerPath": "",
            "textReaderPath": "",
            "imageViewerPath": "",
            "psViewerPath": "",
        }
    if category == "athena":
        catDict = {
            "fpLastDir": "",
            "fpLastDirEventList": "",
            "fpScratchDir": "",  # used for writing temporary files
            "fpAudioDir": "",
            "tLastVersionCheck": "",
            "eventOutput": "('midiFile', 'xmlAthenaObject', 'csoundData')",
            "eventMode": "midi",  # startup value
            "refreshMode": "1",  # esObj refreshing
            "debug": "0",
            "cursorToolLb": "",
            "cursorToolRb": "",
            "cursorToolLp": "{",
            "cursorToolRp": "}",
            "cursorToolP": "pi",
            "cursorToolT": "ti",
            "cursorToolOption": "cursorToolOn",
        }
    if category == "gui":
        catDict = {
            # the gui's look, light or dark; figures follow it
            "appearance": "light",
        }

    if platform == "posix":
        if drawer.isDarwin():
            if category == "external":
                catDict["csoundPath"] = "/usr/local/bin/csound"
                catDict["midiPlayerPath"] = "/Applications/QuickTime Player.app"
                catDict["audioPlayerPath"] = "/Applications/QuickTime Player.app"
                catDict["textReaderPath"] = ""  # will use system default
                catDict["imageViewerPath"] = "/Applications/Preview.app"
                catDict["psViewerPath"] = "/Applications/Preview.app"
        else:
            if category == "external":
                catDict["csoundPath"] = "/usr/local/bin/csound"
                catDict["midiPlayerPath"] = "playmidi"
                catDict["audioPlayerPath"] = "xmms"
                catDict["textReaderPath"] = "more"  # will use system default
                catDict["imageViewerPath"] = "imagemagick"
                catDict["psViewerPath"] = "gs"
        # common for all posix
        if category == "athena":
            catDict["dlgVisualMethod"] = "text"

    else:  # win or other
        if category == "external":
            catDict["audioFormat"] = "wav"
        if category == "athena":
            catDict["dlgVisualMethod"] = "text"  # works w/n idle, console on win

    return catDict


def getDefaultPrefDict(platform=None):
    """gets all catgtegories for a given platform
         when update prefs, checks default and provides missing value

    >>> a = getDefaultPrefDict('win')
    >>> a['external']['audioFormat']
    'wav'
    >>> a = getDefaultPrefDict()
    >>> a['athena']['debug']
    '0'
    """
    if platform == None:
        if os.name == "posix":
            platform = "posix"
        else:
            platform = "win"

    prefDict = {}
    prefDict["external"] = getCategoryDefaultDict(platform, "external")
    prefDict["athena"] = getCategoryDefaultDict(platform, "athena")
    prefDict["gui"] = getCategoryDefaultDict(platform, "gui")
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
    categories = ["external", "athena", "gui"]

    # if missing a category:
    if len(list(oldPrefDict.keys())) != len(list(defaultPrefDict.keys())):
        for category in list(defaultPrefDict.keys()):
            if category not in list(oldPrefDict.keys()):
                oldPrefDict[category] = defaultPrefDict[category]

    for catName in categories:  # check each key
        # provide backwards compat for changed category names
        if catName not in list(oldPrefDict.keys()):
            if catName == "external":
                oldPrefDict[catName] = oldPrefDict["csound"]
                del oldPrefDict["csound"]
        oldCatKeys = list(oldPrefDict[catName].keys())
        oldCatKeys.sort()  # sort keys and compare
        newCatKeys = list(defaultPrefDict[catName].keys())
        newCatKeys.sort()
        if not oldCatKeys == newCatKeys:
            for key in newCatKeys:
                if key not in oldCatKeys:  # key not found
                    oldPrefDict[catName][key] = defaultPrefDict[catName][key]
            for key in oldCatKeys:
                if key not in newCatKeys:  # remove old keys no long used
                    del oldPrefDict[catName][key]

    return oldPrefDict


def writePrefDict(prefFilePath, prefDict):
    """given patha and pref, writes as xml file"""
    msg = []
    parent = "preferences"
    msg.append(xmlTools.XMLHEAD)
    msg = msg + xmlTools.pyToXml(
        parent,
        "preferences",
        prefDict,
        0,
        [
            None,
            "prefGroup",
        ],
    )
    f = open(prefFilePath, "w")
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
        with open(prefFilePath, "r") as f:
            doc = f.read()
    if doc != None:
        procData = xmlToPy(doc)
        return procData["preferences"]
    else:  # cant load this data, get new data
        return getDefaultPrefDict()


class Environment(object):
    """object to store debug stats and print output
    >>> a = Environment()
    """

    def __init__(self, modName=None):
        if modName == None:
            modName = _MOD  # set to this module
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
        # reading is in the catch all too: the file may be another athenaCL's
        # half-written one, and this cannot crash
        try:
            return int(getXmlPrefDict(fp)["athena"]["debug"])
        except:  # catch all: this cannot crash
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
            fpScratch = prefDict["athena"]["fpScratchDir"]
        except:  # catch all
            fpScratch = ""
        if not os.path.exists(fpScratch) or not os.path.isdir(fpScratch):
            self.printWarn(
                "scratch directory preference set to a non-directory: %s" % fpScratch
            )
            fpScratch = ""  # do not pass forward
        # final return
        if fpScratch == "":
            return None
        else:
            return fpScratch

    def _formatMsg(self, msg):
        if not drawer.isList(msg):
            msg = [msg]
        post = []
        post.append("%s:" % self.modName)
        for part in msg:
            partMsg = str(part)
            if drawer.isList(part):
                partMsg = partMsg.replace(" ", "")
            post.append(partMsg)
        post.append("\n")
        return " ".join(post)

    def printWarn(self, msg):
        """always print"""
        sys.stderr.write(self._formatMsg(msg))

    def printDebug(self, msg, *arguments):
        if self.debug <= 0:
            return  # do nothing
        else:
            if not drawer.isList(msg):
                msg = [msg]
            if len(arguments) > 0:
                msg += arguments
            sys.stderr.write(self._formatMsg(msg))

    def getTempFile(self, suffix="", fileNameTimeStamp=True):
        """Return a file path to a temporary file with the specified suffix

        This uses the directory set as a preference if possible.

        Ths always returns as file path, whether or not a pref is set
        """
        fpSrc = self.getScratchDirPath()
        if fpSrc == None:  # if it does not exist or cannot be found
            if os.name == "posix":
                fd, fp = tempfile.mkstemp(suffix=suffix)
                if isinstance(fd, int):
                    pass  # see comment below
                else:
                    fd.close()
            else:  # win
                if sys.hexversion < 0x02030000:
                    raise Exception("cannot create temporary file")
                else:
                    tf = tempfile.NamedTemporaryFile(suffix=suffix)
                    fp = tf.name
                    tf.close()
        else:
            if not os.path.exists(fpSrc):
                # cannot continue at all w/o this directory
                raise Exception(
                    "user-specified scratch directory (%s) does not exists." % fpSrc
                )

            # option to generate file name with a time stamp
            # and place in the scratch dir
            if fileNameTimeStamp == True:
                fp = os.path.join(fpSrc, drawer.tempFileName(suffix))
            else:
                if os.name == "posix":
                    fd, fp = tempfile.mkstemp(dir=fpSrc, suffix=suffix)
                    if isinstance(fd, int):
                        # on MacOS, fd returns an int, like 3, when called
                        pass
                    else:
                        fd.close()
                else:  # win
                    if sys.hexversion < 0x02030000:
                        raise Exception("cannot create temporary file")
                    else:
                        tf = tempfile.NamedTemporaryFile(dir=fpSrc, suffix=suffix)
                        fp = tf.name
                        tf.close()
        self.printDebug(["temporary file:", fp])
        return fp


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)


# -----------------------------------------------------------------||||||||||||--


if __name__ == "__main__":
    from athenaCL.test import baseTest

    baseTest.main(Test)
