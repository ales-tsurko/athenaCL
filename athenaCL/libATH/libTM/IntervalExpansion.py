# -----------------------------------------------------------------||||||||||||--
# Name:          IntervalExpansion.py
# Purpose:       simple texture module for creating an ornamented line.
#
# Authors:       Christopher Ariza
#                Paula Matthusen
#
# Copyright:     (c) 2003, 2006-2010 Christopher Ariza, Paula Matthusen
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import random, copy
import unittest, doctest


from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH import ornament
from athenaCL.libATH import pitchTools
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH import language

lang = language.LangObj()

_MOD = "IntervalExpansion.py"


class IntervalExpansion(baseTexture.Texture):
    """simple one dimension line algorithm

    >>> #a = IntervalExpansion('test')
    """

    def __init__(self, name=None):
        baseTexture.Texture.__init__(self, name)  # init base class
        self.author = "athenaCL native"
        self.tmName = "IntervalExpansion"
        # will get defaults from object, order determines labels
        self.textPmtrNames = [
            "loopWithinSet",
            "ornamentLibrarySelect",
            "ornamentMaxDensity",
            "levelFieldMonophonic",
            "levelOctaveMonophonic",
        ]
        self._updateTextPmtrInit()  # defines textPmtrNo, textLabels
        # define ordered list of dynamic parameters
        # [{name: x, type: x, default: x)]
        self.dynPmtrManifest = [
            {
                "name": "ornamentShift",
                "type": "genPmtrObjs",
                "default": ("bg", "rc", (0, 0, -12, 12)),
                "doc": "ornament pitch shift",
            },
        ]
        self._updateDynPmtrInit()  # defines textPmtrNo, textLabels
        self._ornGroup()
        self.refDict = {"ornGroupNames": self._ornGroupNames()}
        self.doc = lang.docTmIntervalExpansion

    def _ornGroup(self):
        # see ornament.py for detailed information
        # name, position, harmonicLang, microtone
        self.ornGroupLib = {
            "diatonicGroupA": [
                ("turn.0,1,0,-1.b", "attack", "path", 0.5),
                ("trill.0,1.b", "release", "path", 0.5),
                ("rise.-2,-1", "attack", "path", 0.5),
                ("trill.0,1.a", "release", "microtone", 0.125),
                ("arc.-1,2,1", "attack", "path", 0.5),
                ("fall.2,1", "attack", "path", 0.5),
                ("trill.0,1.a", "release", "microtone", 0.092),
                ("rise.1,2", "release", "path", 0.5),
                ("arc.0,1", "attack", "path", 0.5),
                ("fall.1,0,-1", "release", "path", 0.5),
            ],
            "diatonicGroupB": [
                ("turn.0,1,0,-1.b", "attack", "path", 0.5),
                ("trill.0,1.b", "release", "path", 0.5),
                ("fall.2,1", "attack", "path", 0.5),
                ("arc.0,1", "attack", "path", 0.5),
            ],
            "diatonicGroupC": [
                ("octotrill.0,12.b", "attack", "path", 0.5),
                ("octoturn.0,12,0,-12.b", "attack", "path", 0.5),
                ("trill.0,1.b", "release", "path", 0.5),
                ("fall.2,1", "attack", "path", 0.5),
                ("arc.0,1", "attack", "path", 0.5),
            ],
            "microGroupA": [
                ("turn.0,1,0,-1.b", "attack", "microtone", 0.11),
                ("trill.0,1.b", "release", "microtone", 0.13),
                ("rise.-1", "attack", "path", 0.09),
                ("rise.-2,-1", "attack", "path", 0.05),
                ("arc.-1,2,1", "attack", "microtone", 0.08),
                ("fall.2,1", "attack", "path", 0.10),
                ("rise.1,2", "release", "microtone", 0.02),
                ("arc.0,1", "attack", "microtone", 0.034543),
                ("fall.1,0,-1", "release", "microtone", 0.0654),
            ],
            "microGroupB": [
                ("rise.-1", "attack", "path", 0.5),
                ("arc.-1,2,1", "attack", "microtone", 0.13),
                ("fall.2,1", "attack", "path", 0.5),
                ("rise.-1", "attack", "microtone", 0.15),
                ("arc.0,1", "attack", "microtone", 0.14543),
                ("fall.1,0,-1", "release", "microtone", 0.07),
            ],
            "microGroupC": [
                ("rise.-1", "attack", "microtone", 0.17),
                ("arc.-1,2,1", "attack", "microtone", 0.065),
                ("rise.-1", "attack", "microtone", 0.19),
                ("arc.0,1", "attack", "microtone", 0.17),
                ("fall.1,0,-1", "release", "microtone", 0.08),
                ("fall.2,1", "attack", "microtone", 0.06),
            ],
            "chromaticGroupA": [
                ("rise.-1", "attack", "chromatic", 0.17),
                ("rise.-1", "attack", "chromatic", 0.13),
                ("arc.0,1", "attack", "chromatic", 0.10),
                ("fall.1,0,-1", "release", "chromatic", 0.08),
                ("trill.0,1.a", "release", "chromatic", 0.092),
            ],
            "trillGroupA": [
                ("rise.-1", "attack", "path", 0.17),
                ("trill.0,1.a", "release", "microtone", 0.21),
                ("trill.0,1.a", "release", "microtone", 0.15),
                ("trill.0,1.b", "attack", "microtone", 0.12),
                ("trill.0,1.b", "release", "microtone", 0.17),
                ("turn.0,1,0,-1.a", "release", "microtone", 0.27),
                ("turn.0,1,0,-1.a", "attack", "microtone", 0.05),
                ("turn.0,1,0,-1.b", "release", "path", 0.18),
                ("turn.0,1,0,-1.b", "attack", "path", 0.18),
            ],
            "trilloctoGroupA": [
                ("trillocto.0,12.a", "attack", "path", 0.17),
                ("trillocto.0,12.a", "release", "microtone", 0.21),
            ],
            "min3GroupA": [
                ("trillMin3.0,3.a", "attack", "path", 0.17),
                ("trillMin3.0,3.a", "release", "microtone", 0.21),
            ],
            "maj3GroupA": [
                ("trillMaj3.0,4.a", "attack", "path", 0.17),
                ("trillMaj3.0,4.a", "release", "microtone", 0.21),
            ],
            #       'neut3GroupA'    : [ ('trillNeut3.0,35.a','attack','path', .17),
            #                                 ('trillNeut3.0,35.a','release','microtone', .21),]
            "trill3GroupA": [
                ("turn.0,3,0,-3.a", "attack", "path", 0.17),
                ("turn.0,3,0,-3.a", "attack", "path", 0.21),
                ("turn.0,3,0,-3.a", "attack", "microtone", 0.21),
                ("trillMaj3.0,4.a", "release", "microtone", 0.21),
            ],
            "trillP5GroupA": [
                ("trillP5.0,7.a", "attack", "path", 0.17),
                ("trillP5.0,7.a", "release", "microtone", 0.21),
            ],
        }

    def _ornGroupNames(self):
        ornList = list(self.ornGroupLib.keys())
        ornList.append("off")  # add off option
        return ornList

    def _ornGroupGet(self, name):
        if name == "off":
            return None
        else:
            return self.ornGroupLib[name]

    def _scoreMain(self):
        """creates score

        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('IntervalExpansion')
        >>> ti.tmName == 'IntervalExpansion'
        True
        >>> ti.loadDefault()
        >>> ti.score() == True
        True

        """
        self.ornamentObj = ornament.Ornament(self.pmtrObjDict, self.temperamentObj)

        # texture-wide PATH/PITCH elements
        # pitches do not come from here, but from below
        path = self.path.get("scPath")
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        # texture-wide TEXTURE (self.textQ amd)options
        textRepeatToggle = self.getTextStatic("lws", "onOff")
        ornamentSwitch = self.getTextStatic("ols", "libraryName")
        ornamentMaxDensity = self.getTextStatic("omd", "percent")
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic("lfm", "level")
        textOctaveLevel = self.getTextStatic("lom", "level")
        # create a randomUniform parameter object to control ornament control
        # values between 0 and 1; if pmtr() <= ornamentMaxDensity
        ruPmtrObj = parameter.factory(("randomUniform", 0, 1))

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            chordLength = len(chordCurrent)
            chordIndex = 0
            muteSet = "off"
            psTest = []
            ornamentIndex = 0

            tStartSetReal = copy.deepcopy(tCurrent)
            self.stateUpdate(tCurrent, chordCurrent, None, multisetCurrent, None, None)

            if textFieldLevel == "set":
                transCurrent = self.getField(tCurrent)  # choose PITCHFIELD
            if textOctaveLevel == "set":
                octCurrent = self.getOct(tCurrent)  # choose OCTAVE

            while 1:  # PITCH in CHORD
                if tCurrent >= tEndSet:
                    break
                ps = chordCurrent[chordIndex]
                psTest.append(ps)
                chordIndex = chordIndex + 1  # shift to next pitch
                if chordIndex >= chordLength:
                    chordIndex = 0

                self.stateUpdate(
                    tCurrent, chordCurrent, ps, multisetCurrent, None, None
                )

                if textFieldLevel == "event":
                    transCurrent = self.getField(tCurrent)  # choose PITCHFIELD
                if textOctaveLevel == "event":
                    octCurrent = self.getOct(tCurrent)  # choose OCTAVE
                psReal = pitchTools.psToTempered(
                    ps, octCurrent, self.temperamentObj, transCurrent
                )
                self.stateUpdate(
                    tCurrent, chordCurrent, ps, multisetCurrent, None, psReal
                )

                bpm, pulse, dur, sus, acc = self.getRhythm(tCurrent)
                if muteSet == "on":  # make all rests
                    acc = 0  # everything is a rest after chord inex reset
                if acc == 0 and not self.silenceMode:  # this is a rest
                    chordIndex = chordIndex - 1  # dont count this note if a rest
                    psTest = psTest[:-1]  # drop off last addition
                    tCurrent = tCurrent + dur
                    continue

                # choose AMP, PAN
                amp = self.getAmp(tCurrent) * acc
                pan = self.getPan(tCurrent)
                auxiliary = self.getAux(tCurrent)

                parentEventDict = self.makeEvent(
                    tCurrent, bpm, pulse, dur, sus, acc, amp, psReal, pan, auxiliary
                )
                refDict = self.getRefDict(tCurrent)
                # "rhythm" not "dur" (dur includes overlap)
                if ornamentSwitch != "off":
                    # check if an ru value is <= ornament density (if 1, always)
                    # time value is not important
                    if ruPmtrObj(tCurrent) <= ornamentMaxDensity:
                        repretory = self._ornGroupGet(ornamentSwitch)
                        # a, b, c, d = repretory[ornamentIndex] # this will do in order
                        a, b, c, d = random.choice(repretory)  # choose orn at random
                        subEventArray = self.ornamentObj.create(refDict, a, b, c, d)
                        # process sub event array
                        for iSub in range(len(subEventArray)):
                            # get time from subEvent
                            subEvent = subEventArray[iSub]
                            val = self.getTextDynamic("ornamentShift", subEvent["time"])
                            subEvent["ps"] = subEvent["ps"] + val
                        self.storePolyEvent(parentEventDict, subEventArray, "orn")
                        ornamentIndex = ornamentIndex + 1  # increment for when ordered
                        if ornamentIndex == len(repretory):
                            ornamentIndex = 0
                    else:
                        self.storeEvent(parentEventDict)
                else:  # ornament == 'off': # dont do ornaments
                    self.storeEvent(parentEventDict)

                # turn of further notes if all gotten
                if textRepeatToggle == "off" and len(psTest) >= chordLength:
                    muteSet = "on"

                # move clocks forward by rhythm unit
                tCurrent = tCurrent + dur
            self.clockForward()  # advances path positon
        return 1


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
