# -----------------------------------------------------------------||||||||||||--
# Name:          InterpolateFill.py
# Purpose:       non-linear interpolation b/n generated points.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2007-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest


from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH.libPmtr import basePmtr

from athenaCL.libATH import pitchTools
from athenaCL.libATH import language
from athenaCL.libATH import unit

lang = language.LangObj()


# _docInterpolate = """
#
# time points are created non-linearly based on tempo and rhythm values
# a static texture parameter object determines a sampling rate
# the duration between each time-point is calculated
# this width is divided into the necessary samples based on sr
# events are created for each sampple w/n width
# amp values are interpolated between each time point
#
# in this way gendyn like structures can be created:
# assign dynamic parameter to both rhythm (using convert second) and amp
# sieves could be used to calculate durations and amplitudes
#
# static parameter objects

# levelInterpolateFrame = event, frame
#     if frame size is updated for each frame or each event
# parameterInterpolationControl = event, frame
#     how often non duration parameters are updated
# snapSustainTime = on, off
#     whether sustain values snap to frame width
# snapEventTime = on, off
#     determines if time points are snapped to grid over the whole duration
#     providing the most even spacing
#     or if time points are allowed to be out of the sampling rate
#
# when processed as an audioFile, each event becomes a sample
# pitch/path parameters have no effect
# """
#


class InterpolateFill(baseTexture.Texture):
    """linear interpolation between event points

    #>>> a = InterpolateFill('test')
    """

    def __init__(self, name=None):
        baseTexture.Texture.__init__(self, name)  # init base class
        self.author = "athenaCL native"
        self.tmName = "InterpolateFill"
        # will get defaults from object, order determines labels
        self.textPmtrNames = [
            "pitchSelectorControl",
            "levelFieldMonophonic",
            "levelOctaveMonophonic",
            "totalEventCount",
            "levelEventPartition",
            "eventDensityPartition",
            "interpolationMethodControl",
            "levelFrameDuration",
            "parameterInterpolationControl",
            "snapSustainTime",
        ]
        self._updateTextPmtrInit()  # defines textPmtrNo, textLabels

        # frame dur should be updated only for each event,
        # or for each frame
        self.dynPmtrManifest = [
            {
                "name": "fillGenerator",
                "type": "genPmtrObjs",
                "default": ("ru", 0, 1),
                "doc": "event start time",
            },
            {
                "name": "frameDuration",
                "type": "genPmtrObjs",
                "default": ("oo", ("ws", "e", 4, 0, 5, 15)),
                "doc": "duration in seconds of each frame between events",
            },
            {
                "name": "exponent",
                "type": "genPmtrObjs",
                "default": ("c", 1),
                "doc": "exponent used for power segment interpolation",
            },
        ]
        self._updateDynPmtrInit()  # defines textPmtrNo, textLabels

        self.doc = lang.docTmInterpolateFill

    def _scoreMain(self):
        """creates score

        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('InterpolateFill')
        >>> ti.tmName == 'InterpolateFill'
        True
        >>> ti.loadDefault()
        >>> ti.score() == True
        True

        """
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        # get field, octave selection method value
        textFieldLevel = self.getTextStatic("lfm", "level")
        textOctaveLevel = self.getTextStatic("lom", "level")
        textPitchSelectorControl = self.getTextStatic("psc", "selectionString")
        textEventCount = self.getTextStatic("tec", "count")
        textEventPartition = self.getTextStatic("lep", "level")
        textDensityPartition = self.getTextStatic("edp", "level")

        textInterpolationMethodControl = self.getTextStatic("imc", "method")
        textLevelFrameDuration = self.getTextStatic("lfd", "level")
        textParameterInterpolationControl = self.getTextStatic("pic", "onOff")
        textSnapSustainTime = self.getTextStatic("sst", "onOff")

        # cannot snap event time in this context
        # textSnapEventTime = self.getTextStatic('set', 'onOff')

        if textDensityPartition == "set":  # get a list of values
            pLen = self.getPathLen()
            eventPerSet = [int(round(textEventCount / pLen))] * pLen
        else:  # duration fraction
            scalars = self.getPathDurationPercent()
            eventPerSet = [int(round(x * textEventCount)) for x in scalars]
        eventIndex = 0

        # a list of frame data: tStart, dur, eventFlag, interpMethod,interpExponet
        tFrameArray = []

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            # start and end of this set is in real-time, not local to path
            # if not by set, boundaries here are always tt of entire texture
            if textEventPartition == "set":
                tStartSet, tEndSet = self.clockPoints()  # value relative to start
            else:  # its a path based, treat tiem as one set
                tStartSet, tEndSet = self.getTimeRange()  # value relative to start

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
                # silence mode has to be ignored

                amp = self.getAmp(tCurrent) * acc  # choose amp, pan
                pan = self.getPan(tCurrent)
                auxiliary = self.getAux(tCurrent)  # chooose AUX, pack into list
                eventDict = self.makeEvent(
                    tCurrent, bpm, pulse, dur, sus, acc, amp, psReal, pan, auxiliary
                )
                self.storeEvent(eventDict)
                # tCurrent = tCurrent + dur # move clocks forward by dur unit

                # always store event time in array, w/ interp type and exponent
                tFrameArray.append(
                    (
                        tCurrent,
                        dur,
                        1,
                        textInterpolationMethodControl,
                        self.getTextDynamic("exponent", tCurrent),
                    )
                )
                # tFrame = copy.deepcopy(tCurrent)

            self.clockForward()  # advances path positon

        # sort frames and events; should both be the same size and in order
        self.esObj.sort()
        tFrameArray.sort()
        # sort stored events

        # process frame start times
        # store first event, as well as interp exponet if needed
        # tFrame is set to tCurrent
        tFrameArrayPost = []
        for i in range(len(tFrameArray) - 1):  # dont do last event
            eventDict = self.esObj[i]
            tCurrent = eventDict["time"]
            tFrame = copy.deepcopy(tCurrent)
            # get relative duration to next event
            durRel = self.esObj[i + 1]["time"] - eventDict["time"]
            # transfer old tFrame to new
            tFrameArrayPost.append(tFrameArray[i])

            if textLevelFrameDuration == "event":  # one frame dur / event
                frameDur = self.getTextDynamic("frameDuration", tCurrent)
                if frameDur < durRel:
                    # can eval in loop b/c frameDur is constant
                    while (tFrame + frameDur) < (tCurrent + durRel):
                        tFrame = tFrame + frameDur
                        tFrameArrayPost.append((tFrame, frameDur, 0))
            # frame updates / frame
            elif textLevelFrameDuration == "frame":
                while 1:
                    # must calc frameDur to see if it is over e next event
                    frameDur = self.getTextDynamic("frameDuration", tFrame)
                    if (tFrame + frameDur) > (tCurrent + durRel):
                        break  # cannot fit another frame w/o passing next event
                    tFrame = tFrame + frameDur
                    tFrameArrayPost.append((tFrame, frameDur, 0))
            # cannot snap event time here; woudl require repositioning
            # next event
        # restore the last tFrame to the new tFrame
        tFrameArrayPost.append(tFrameArray[-1])

        # configure which parameters, in EventSequence object, are interpolated
        if textParameterInterpolationControl == "on":
            active = ["time", "acc", "bpm", "amp", "ps", "pan", "aux"]  #
        elif textParameterInterpolationControl == "off":
            active = ["time", "bpm"]
        # interpolate events
        self.interpolate(tFrameArrayPost, textSnapSustainTime, active)
        return 1


#         a = bpf.LinearSegment([(0,2),(100,20)])


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
