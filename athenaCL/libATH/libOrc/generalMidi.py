#!/usr/local/bin/python
# -----------------------------------------------------------------||||||||||||--
# Name:          generalMidi.py
# Purpose:       generalMidi instrument definitions.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2005 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

from athenaCL.libATH.libOrc import baseOrc
from athenaCL.libATH import pitchTools
from athenaCL.libATH import drawer

_MOD = "generalMidi.py"

# -----------------------------------------------------------------||||||||||||--

gmProgramNames = {
    "piano1": 0,
    "piano2": 1,
    "piano3": 2,
    "honkyTonkPiano": 3,
    "rhodesPiano": 4,
    "ePiano": 5,
    "harpsichord": 6,
    "clavinet": 7,
    "celesta": 8,
    "glockenspiel": 9,
    "musicBox": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubularBells": 14,
    "santur": 15,
    "organ1": 16,
    "organ2": 17,
    "organ3": 18,
    "churchOrgan": 19,
    "reedOrgan": 20,
    "accordion": 21,
    "harmonica": 22,
    "bandoneon": 23,
    "nylonGuitar": 24,
    "steelGuitar": 25,
    "jazzGuitar": 26,
    "cleanGuitar": 27,
    "mutedGuitar": 28,
    "overDriveGuitar": 29,
    "distortonGuitar": 30,
    "guitarHarmonics": 31,
    "acousticBass": 32,
    "fingeredBass": 33,
    "pickedBass": 34,
    "fretlessBass": 35,
    "slapBass1": 36,
    "slapBass2": 37,
    "synthBass1": 38,
    "synthBass2": 39,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contraBass": 43,
    "tremoloStrings": 44,
    "pizzicatoStrings": 45,
    "orchestralHarp": 46,
    "timpani": 47,
    "strings": 48,
    "slowStrings": 49,
    "synthStrings1": 50,
    "synthStrings2": 51,
    "choirAahs": 52,
    "voiceOohs": 53,
    "synthVox": 54,
    "orchestraHit": 55,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "mutedTrumpet": 59,
    "frenchHorn": 60,
    "brassSection": 61,
    "synthBrass1": 62,
    "synthBrass2": 63,
    "sopranoSax": 64,
    "altoSax": 65,
    "tenorSax": 66,
    "baritoneSax": 67,
    "oboe": 68,
    "englishHorn": 69,
    "bassoon": 70,
    "clarinet": 71,
    "piccolo": 72,
    "flute": 73,
    "recorder": 74,
    "panFlute": 75,
    "bottleBlow": 76,
    "shakuhachi": 77,
    "whistle": 78,
    "ocarina": 79,
    "squareWave": 80,
    "sawWave": 81,
    "synCalliope": 82,
    "chifferLead": 83,
    "charang": 84,
    "soloVoice": 85,
    "5thSawWave": 86,
    "bassAndLead": 87,
    "fantasia": 88,
    "warmPad": 89,
    "polySynth": 90,
    "spaceVoice": 91,
    "bowedGlass": 92,
    "metalPad": 93,
    "haloPad": 94,
    "sweepPad": 95,
    "iceRain": 96,
    "soundTrack": 97,
    "crystal": 98,
    "atmosphere": 99,
    "brightness": 100,
    "goblins": 101,
    "echoDrops": 102,
    "starTheme": 103,
    "sitar": 104,
    "banjo": 105,
    "shamisen": 106,
    "koto": 107,
    "kalimba": 108,
    "bagpipe": 109,
    "fiddle": 110,
    "shanai": 111,
    "tinkleBell": 112,
    "agogoBells": 113,
    "steelDrums": 114,
    "woodBlock": 115,
    "taikoDrum": 116,
    "melodicTom1": 117,
    "synthDrum": 118,
    "reverseCymbal": 119,
    "guitarFretnoise": 120,
    "breathNoise": 121,
    "seaShore": 122,
    "birdTweet": 123,
    "telephoneRing": 124,
    "helicopterBlade": 125,
    "applauseNoise": 126,
    "gunShot": 127,
}

# perc on ch 10; name to midi note number
gmPercussionNames = {
    "acousticBassDrum": 35,
    "bassDrum1": 36,
    "sideStick": 37,
    "acousticSnare": 38,
    "handClap": 39,
    "electricSnare": 40,
    "lowFloorTom": 41,
    "closedHiHat": 42,
    "highFloorTom": 43,
    "pedalHiHat": 44,
    "lowTom": 45,
    "openHiHat": 46,
    "lowMidTom": 47,
    "hiMidTom": 48,
    "crashCymbal1": 49,
    "highTom": 50,
    "rideCymbal1": 51,
    "chineseCymbal": 52,
    "rideBell": 53,
    "tambourine": 54,
    "splashCymbal": 55,
    "cowBell": 56,
    "crashCymbal2": 57,
    "vibraSlap": 58,
    "rideCymbal2": 59,
    "hiBongo": 60,
    "lowBongo": 61,
    "muteHiConga": 62,
    "openHiConga": 63,
    "lowConga": 64,
    "highTimbale": 65,
    "lowTimbale": 66,
    "highAgogo": 67,
    "lowAgogo": 68,
    "cabasa": 69,
    "maracas": 70,
    "shortWhistle": 71,
    "longWhistle": 72,
    "shortGuiro": 73,
    "longGuiro": 74,
    "claves": 75,
    "hiWoodBlock": 76,
    "lowWoodBlock": 77,
    "muteCuica": 78,
    "openCuica": 79,
    "muteTriangle": 80,
    "openTriangle": 81,
}


# -----------------------------------------------------------------||||||||||||--
# access utilities
def getPgmName(pgmNum):
    pgmNum = int(pgmNum)
    if pgmNum < 0:
        pgmNum = 0
    if pgmNum > 127:
        pgmName = "unknown"
    else:
        for name, num in list(gmProgramNames.items()):
            if num == pgmNum:
                pgmName = name
                break
    return pgmName


def getPgmNumber(usrStr):
    if usrStr == "":
        return None
    try:
        numVal = int(usrStr)
    except (ValueError, TypeError):
        numVal = -1
    if numVal >= 0:  # its a number, try to use
        return getPgmName(numVal), numVal
    # its a string
    usrStr = drawer.strScrub(usrStr, "L")
    scoreDict = {}
    for name in list(gmProgramNames.keys()):
        nameTest = name.lower()
        scoreDict[name] = nameTest.count(usrStr)  # counts instances
    best = ("", 0)  # name, score
    # go basck over items; name does have case
    for name, score in list(scoreDict.items()):
        if score > best[1]:
            best = (name, score)
    if best[0] == "":  # nothing found
        return None
    else:
        return best[0], gmProgramNames[best[0]]  # name, pgmNum


def getPercNameFromNoteName(usrStr):
    """get perc name from midi note number
    nameStr can be a string (psName) or number (midiNote number)
    """
    if drawer.isStr(usrStr):
        psInt = pitchTools.psNameToPs(usrStr)
        midiInt = pitchTools.psToMidi(psInt)
    else:
        midiInt = int(usrStr)
    # normalize bad values
    if midiInt < 35:
        midiInt = 35
    if midiInt > 81:
        midiInt = 81
    else:
        for name, num in list(gmPercussionNames.items()):
            if num == midiInt:
                percName = name
                break
    return percName


def getNoteNameFromPercName(percStr):
    "for a given percussion name, find what note name is needed"
    foundName = None
    percStr = drawer.strScrub(percStr, "L")
    for name in list(gmPercussionNames.keys()):
        if percStr == name.lower():
            foundName = name
            break
    if foundName == None:  # check again for partial matches
        for name in list(gmPercussionNames.keys()):
            name = name.lower()
            if name.find(percStr) >= 0:
                foundName = name
                break
    if foundName == None:
        print(_MOD, "cant find:", percStr)
    midiInt = gmPercussionNames[foundName]
    noteName = pitchTools.midiToNoteName(midiInt)
    return noteName  # may be None on error


# -----------------------------------------------------------------||||||||||||--
# -----------------------------------------------------------------||||||||||||--
# object models


class GeneralMidi(baseOrc.Orchestra):
    """gm midi instruments"""

    def __init__(self):
        baseOrc.Orchestra.__init__(self)
        self.name = "generalMidi"
        self._dummyInst = InstrumentMidi()
        self._instrNumbers = list(range(0, 128))  # 127 program numbers

    def instNoValid(self, iNo):
        """test if an instrument number is valid"""
        if drawer.isInt(iNo) and iNo in self._instrNumbers:
            return 1
        else:
            return 0

    def instNoList(self, format=None):
        """return a list of instrument numbers; if
        a list is not availabe, return None"""
        if format == "user":
            return drawer.listToStr(self._instrNumbers)
        return self._instrNumbers

    def constructOrc(self, noCh=None, instList=None):
        """nothing to do here"""
        return None

    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        pmtrFields includes 6 default values
        """
        if iNo == None:
            instrList = self._instrNumbers
        else:
            instrList = [
                iNo,
            ]
        instInfoDict = {}
        for number in instrList:
            instInfoDict[number] = (
                getPgmName(number),
                self._dummyInst.pmtrFields,  # always 6
                self._dummyInst.pmtrInfo,
            )  # always empty
        return instInfoDict, instrList

    def getInstPreset(self, iNo, auxNo=None):
        return self._dummyInst.getPresetDict()  # will returns empty dict

    def getInstName(self, iNo):
        return getPgmName(iNo)

    def getInstAuxNo(self, iNo):
        return self._dummyInst.auxNo

    def getInstPmtrInfo(self, iNo, pmtrNo):
        """for specified inst, pmtrNo, return pmtr info"""
        # midi inst have no additional parameter information
        return "no information available"

    # -----------------------------------------------------------------------||--
    # mappings of psReal, amp, pan; only applied of mix mode is on
    def _postMapPs(self, iNo, val):  # alwasy map pitch
        # pitchtools limit will automatically constrain min/max as well
        # this rounds floating point values to integers
        val = pitchTools.psToMidi(val, "limit")
        # always limit max values
        if val < 0:
            val = 0
        if val > 127:
            val = 127
        return val

    # pre 1.3 csoundNative files will have amps mostly in the range of
    # 0 to 80, so this will work; sample insturuments, however, have
    # much lower amplitudes
    def _postMapAmp(self, iNo, val, orcMapMode=1):  # values between 0 and 1
        if orcMapMode:  # optional map
            # does not seem necessary to use 127; seems to peak
            val = int(round(val * 124.0))
        else:  # take raw value as int
            val = int(round(val))
        # always limit
        if val < 0:
            val = 0
        if val > 127:
            val = 127
        return val

    def _postMapPan(self, iNo, val, orcMapMode=1):
        if orcMapMode:  # optional map
            val = int(round(val * 127.0))
        else:  # must be an int
            val = int(round(val))
        # always limit
        # do modulus rotation on pan values
        if val < 0 or val > 127:
            val = val % 127
        return val


# -----------------------------------------------------------------||||||||||||--
class GeneralMidiPercussion(GeneralMidi):
    """percussion as subclass of gm
    compatible w/ gm; only difference is instruments made available
    this distincition is important when used in an eventMode, to select ints
    not important when used in an engine to process values"""

    def __init__(self):
        GeneralMidi.__init__(self)
        self.name = "generalMidiPercussion"
        self._dummyInst = InstrumentMidi()
        # instrument numbers are the pitch values
        self._instrNumbers = list(range(35, 82))  # 35-81 program numbers

    def getInstName(self, iNo):
        """over-ride from gm, as gotten from different dictionary"""
        return getPercNameFromNoteName(iNo)

    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        pmtrFields includes 6 default values
        """
        if iNo == None:
            instrList = self._instrNumbers
        else:
            instrList = [
                iNo,
            ]
        instInfoDict = {}
        for number in instrList:
            instInfoDict[number] = (
                getPercNameFromNoteName(number),
                self._dummyInst.pmtrFields,  # always 6
                self._dummyInst.pmtrInfo,
            )  # always empty
        return instInfoDict, instrList


# -----------------------------------------------------------------||||||||||||--
# one instrument object for all midi insts, general and perc
class InstrumentMidi(baseOrc.Instrument):
    def __init__(self):
        baseOrc.Instrument.__init__(self)
        self.pmtrDefault = {}  # no default for midi instruments
        self.pmtrInfo = {}
        self.pmtrFields = self.pmtrCountDefault
        self.auxNo = 0
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        # pan and amp ranges are b/n 0 and 127
        # for all instruments
        self.postMapAmp = (0, 127, "linear")
        self.postMapPan = (0, 127, "linear")
