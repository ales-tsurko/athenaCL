# -----------------------------------------------------------------||||||||||||--
# Name:          TimeFill.py
# Purpose:       Texture to fill time range with a generator
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2006-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest

from athenaCL.libATH import pitchTools
from athenaCL.libATH import unit
from athenaCL.libATH import language

lang = language.LangObj()

from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH.libPmtr import basePmtr


class TimeFill(baseTexture.Texture):
    def __init__(self, name=None):
        """
        >>> # a = TimeFill('test')
        """
        baseTexture.Texture.__init__(self, name)  # init base class
        self.author = "athenaCL native"
        self.tmName = "TimeFill"
        # will get defaults from object, order determines labels
        # static: eventCount, fillLevel
        # dyn: fillGenerator
        self.textPmtrNames = [
            "pitchSelectorControl",
            "levelFieldMonophonic",
            "levelOctaveMonophonic",
            "totalEventCount",
            "levelEventPartition",
            "eventDensityPartition",
        ]
        self._updateTextPmtrInit()  # defines textPmtrNo, textLabels
        # define ordered list of dynamic parameters
        # [{name: x, type: x, default: x)]
        self.dynPmtrManifest = [
            {
                "name": "fillGenerator",
                "type": "genPmtrObjs",
                "default": ("ru", 0, 1),
                "doc": "event start time",
            },
        ]
        self._updateDynPmtrInit()  # defines textPmtrNo, textLabels
        self.doc = lang.docTmTimeFill

    def _scoreMain(self):
        """creates score
        note: octave choose for every note

        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('TimeFill')
        >>> ti.tmName == 'TimeFill'
        True
        >>> ti.loadDefault()
        >>> ti.score() == True
        True

        """
        # texture-wide time elements
        inst = self.getInst()

        # needed for preliminary parameter values
        # tStart, tEnd = self.getTimeRange()
        # tCurrent = tStart

        # get field, octave selection method value
        textFieldLevel = self.getTextStatic("lfm", "level")
        textOctaveLevel = self.getTextStatic("lom", "level")
        textPitchSelectorControl = self.getTextStatic("psc", "selectionString")
        textEventCount = self.getTextStatic("tec", "count")
        textEventPartition = self.getTextStatic("lep", "level")
        textDensityPartition = self.getTextStatic("edp", "level")

        if textDensityPartition == "set":  # get a list of values
            pLen = self.getPathLen()
            eventPerSet = [int(round(textEventCount / pLen))] * pLen
        else:  # duration fraction
            scalars = self.getPathDurationPercent()
            eventPerSet = [int(round(x * textEventCount)) for x in scalars]
        eventIndex = 0

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            # start and end of this set is in real-time, not local to path
            # if not by set, boundaries here are always tt of entire texture
            if textEventPartition == "set":
                tStartSet, tEndSet = self.clockPoints()  # value relative to start
            else:  # its a path based, treat tiem as one set
                tStartSet, tEndSet = self.getTimeRange()  # value relative to path

            # create a generator to get pitches from chord as index values
            selectorChordPos = basePmtr.Selector(
                list(range(len(chordCurrent))), textPitchSelectorControl
            )
            # real set start is always the formal start time here
            tCurrent = copy.deepcopy(tStartSet)
            tStartSetReal = copy.deepcopy(tStartSet)
            self.stateUpdate(tCurrent, chordCurrent, None, multisetCurrent, None, None)

            if textFieldLevel == "set":
                transCurrent = self.getField(tCurrent)  # choose PITCHFIELD
            if textOctaveLevel == "set":
                octCurrent = self.getOct(tCurrent)  # choose OCTAVE

            # get event count from list of eventPerSet list by pathPos
            for i in range(eventPerSet[pathPos]):  # pitch in chord
                eventIndex = eventIndex + 1  # cumulative count
                # even when rounded, dont exceed maximum; last set may have less
                if eventIndex > textEventCount:
                    break
                # tCurrent here is assumed as start of set initiall, although
                # this is not exactly correct
                tUnit = unit.limit(self.getTextDynamic("fillGenerator", tCurrent))
                tCurrent = unit.denorm(tUnit, tStartSet, tEndSet)
                # choose pc from chord
                ps = chordCurrent[selectorChordPos()]  # get position w/n chord
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
                if acc == 0 and not self.silenceMode:  # this is a rest
                    tCurrent = tCurrent + dur
                    continue

                amp = self.getAmp(tCurrent) * acc  # choose amp, pan
                pan = self.getPan(tCurrent)
                auxiliary = self.getAux(tCurrent)  # chooose AUX, pack into list
                eventDict = self.makeEvent(
                    tCurrent, bpm, pulse, dur, sus, acc, amp, psReal, pan, auxiliary
                )
                self.storeEvent(eventDict)
                # tCurrent = tCurrent + dur # move clocks forward by dur unit

            self.clockForward()  # advances path positon
        return 1


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        pass

        # again, get TypeError: unbound method __init__() must be called with Texture instance as first argument
        # a = TimeFill()


# -----------------------------------------------------------------||||||||||||--


if __name__ == "__main__":
    from athenaCL.test import baseTest

    baseTest.main(Test)
