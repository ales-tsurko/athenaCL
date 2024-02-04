# -----------------------------------------------------------------||||||||||||--
# Name:          rhythmSingle.py
# Purpose:       definitions of all paramater objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import random
import unittest, doctest

from athenaCL.libATH import genetic  # gaRhythmMod # mod confl w/ class below
from athenaCL.libATH import typeset
from athenaCL.libATH import rhythm
from athenaCL.libATH import sieve
from athenaCL.libATH import markov
from athenaCL.libATH import drawer
from athenaCL.libATH import error
from athenaCL.libATH import language

lang = language.LangObj()

from athenaCL.libATH.libPmtr import basePmtr


_MOD = "rhythmSingle.py"


# -----------------------------------------------------------------||||||||||||--
class BinaryAccent(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "binaryAccent"
        self.doc = lang.docPoBa
        self.argTypes = [
            "list",
        ]
        self.argNames = ["pulseList"]
        self.argDefaults = [
            [(3, 1, 1), (3, 2, 1)],
        ]

        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.currentPulse = None  # init value, used in getCurrentRhythm
        try:
            self.rObj = rhythm.Rhythm(self.args[0])  # first arg list of rhtyhms
        except error.PulseSyntaxError:
            raise error.ParameterObjectSyntaxError("enter a list of two pulse objects.")
        # self.rObj = self._expandRhythm(self.rObj)
        if len(self.rObj) != 2:
            raise error.ParameterObjectSyntaxError("enter a list of two pulse objects.")
        # set sustain mults for each pulse
        self.rObj[0].setSus(1.4)
        self.rObj[1].setSus(1.6)

    def checkArgs(self):
        return 1, ""  # success

    def repr(self, format=""):
        msg = "%s, %s" % (self.type, self.rObj.repr("triple"))
        if format == "argsOnly":
            return msg  # chop off return carriage
        return msg

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.bpm in the 'call' method
        in order to account for changes in tempo
        """
        # calc new durations base don new tempo
        self.bpm = refDict["bpm"]
        if refDict["stateCurrentPitchRaw"] == refDict["stateCurrentChord"][0]:
            self.currentValue = self.rObj[1](self.bpm)  # dur, sus, acc
            self.currentPulse = self.rObj[1]
        else:  # override acc value
            self.currentValue = self.rObj[0](self.bpm)  # dur, sus, acc
            self.currentPulse = self.rObj[0]
        return self.currentValue

    def postEvent(self, eventDict, refDict):
        "binary accent provides an amp accent if pc == chordCurrent[0]"
        if refDict["stateCurrentPitchRaw"] == refDict["stateCurrentChord"][0]:
            eventDict["amp"] = eventDict["amp"] * 1.08  # scale value
        return eventDict


# -----------------------------------------------------------------||||||||||||--


class GaRhythm(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "gaRhythm"
        self.doc = lang.docPoGr
        self.argTypes = ["list", "num", "num", "num", "str", "num"]
        self.argNames = [
            "pulseList",
            "crossover",
            "mutation",
            "elitism",
            "selectionString",
            "populationSize",
        ]
        self.argDefaults = [
            [(3, 1, 1), (3, 1, 1), (6, 1, 1), (6, 3, 1), (3, 1, 0)],
            0.70,
            0.060,
            0.01,
            "oc",
            20,
        ]
        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        # args = [rObj, crossoverRate, mutationRate, percentElite]
        self.currentPulse = None  # init value, used in getCurrentRhythm

        self.rObj = rhythm.Rhythm(self.args[0])
        # must check rhythm before instantiating genome
        if len(self.rObj) <= 2:
            msg = "pulse list error: supply a rhythm of 3 or more pulses"
            raise error.ParameterObjectSyntaxError(msg)  # report error

        # exapnd rhythms without rests
        # self.rObj = self._expandRhythm(self.rObj)
        self.bpm = 120  # used for initial dur calculations
        self.crossoverRate = self.args[1]
        self.mutationRate = self.args[2]
        self.percentElite = self.args[3]

        # get populationi size as last arg
        self.popSize = self.args[5]
        if self.popSize < 2:
            msg = "population size must be 2 or greater"
            raise error.ParameterObjectSyntaxError(msg)  # report error

        try:
            self.genome = genetic.Genome(
                self.popSize,
                self.rObj.get("triple"),
                rhythm.bpmToBeatTime(self.bpm),
                self.crossoverRate,
                self.mutationRate,
                self.percentElite,
            )
        except ValueError:
            self.genome = None  # this will return error when args checked
        if self.genome == None:
            raise error.ParameterObjectSyntaxError("genome failed to be populated.")

        self.rObjBundle = []  # stores list of rhythms, by family
        self.pulseBundle = []  # stores all pulses as one list

        self.rawRhythmBundle = self.genome.gen(40, 1)  # 2nd arg makes silent
        for rawList in self.rawRhythmBundle:
            rObj = rhythm.Rhythm(rawList)
            rObj.setSus(0.94)  # create equal sustain
            self.rObjBundle.append(rObj)  # list of rhythms
            for i in range(0, len(rObj)):
                self.pulseBundle.append(rObj[i])  # flat list of pulse objects

        # set pulseBundle as list from which selector draws
        self.control = self._selectorParser(self.args[4])  # raises exception
        self.selector = basePmtr.Selector(self.pulseBundle, self.control)

    def checkArgs(self):
        if self.crossoverRate < 0 or self.crossoverRate > 1:
            return 0, "range error: crossover rate must be between 0 and 1."
        if self.mutationRate < 0 or self.mutationRate > 1:
            return 0, "range error: mutation rate must be between 0 and 1."
        if self.percentElite < 0 or self.percentElite > 1:
            return 0, "range error: percent elite must be between 0 and 1."
        return 1, ""

    def repr(self, format=""):
        msg = []
        msg.append(
            "%s, %s, %s, %s, %s, %s, %s"
            % (
                self.type,
                self.rObj.repr("triple"),
                typeset.anyDataToStr(self.crossoverRate),
                typeset.anyDataToStr(self.mutationRate),
                typeset.anyDataToStr(self.percentElite),
                self.control,
                typeset.anyDataToStr(self.popSize),
            )
        )
        if format == "argsOnly":  # if not off, doesnt add list of rhythms
            return "".join(msg)
        msg.append("\n")
        for rObj in self.rObjBundle:  # use rObj bundle to get lists of variations
            msg.append(self.LMARGIN + "%s" % rObj.repr("triple"))
            msg.append("\n")
        msg = msg[:-1]  # chop off last return carriage
        return "".join(msg)

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.bpm in the 'call' method
        in order to account for changes in tempo
        self.beatT should be updated in TMclass.getRhythm method
        """
        self.bpm = refDict["bpm"]
        self.currentPulse = self.selector()
        self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--


class Loop(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "loop"
        self.doc = lang.docPoL
        self.argTypes = ["list", "str"]
        self.argNames = ["pulseList", "selectionString"]
        self.argDefaults = [
            ((3, 1, 1), (3, 1, 1), (8, 1, 1), (8, 1, 1), (8, 3, 1), (3, 2, 0)),
            "oc",
        ]
        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.currentPulse = None  # init value, used in getCurrentRhythm
        try:
            self.rObj = rhythm.Rhythm(self.args[0])
        except error.PulseSyntaxError:
            raise error.ParameterObjectSyntaxError("enter a list of pulse objects.")
        for r in range(0, len(self.rObj)):
            self.rObj[r].setSus(0.94)  # set constant sustain, was 98, but still cut

        self.control = self._selectorParser(self.args[1])  # raises exception
        self.selector = basePmtr.Selector(self.rObj, self.control)

    def checkArgs(self):
        if len(self.rObj) < 1:
            return 0, "list error: there must be rhythms in this list."
        return 1, ""

    def repr(self, format=""):
        msg = "%s, %s, %s" % (self.type, self.rObj.repr("triple"), self.control)
        if format == "argsOnly":
            return msg
        return msg

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.beatT in the 'call' method
        in order to account for changes in tempo
        get next rhythm in the list
        if the last rhyth, reset position to 0
        """
        self.bpm = refDict["bpm"]
        self.currentPulse = self.selector()
        self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class ConvertSecond(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "convertSecond"
        self.doc = lang.docPoCs
        self.argTypes = [
            "list",
        ]
        self.argNames = [
            "parameterObject: duration values in seconds",
        ]
        self.argDefaults = [
            ("ru", 0.25, 2.5),
        ]

        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.currentPulse = None  # init value, used in getCurrentRhythm
        # might be good to calculate a proper rhyhm object with given tempo
        self.rObj = rhythm.Rhythm((1, 1))  # just a place holder
        self.pmtrObj = self._loadSub(args[0], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        return "%s, (%s)" % (self.type, self.pmtrObj.repr(format))

    def reset(self):
        self.pmtrObj.reset()

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.beatT in the 'call' method
        in order to account for changes in tempo
        """
        self.bpm = refDict["bpm"]  # bpm is not used to calc values
        # these are calculated values, not raw pulse values
        dur = self.pmtrObj(t, refDict)
        sus = 0.999 * dur
        acc = 1
        # creat object for reference
        self.currentPulse = None  # cannot create pulse, as no bpm is envolved
        self.currentValue = dur, sus, acc  # no rests are possible
        return self.currentValue


class ConvertSecondTriple(basePmtr.RhythmParameter):
    # cst, (ws, e, 20, 0, .25, 1.25), (ws, e, 20, .5, .25, 1.25), (c, 1)
    # dur is the time of the real rhythm, i.e., time till next note
    # sus is the time of sounding
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "convertSecondTriple"
        self.doc = lang.docPoCst
        self.argTypes = ["list", "list", "list"]
        self.argNames = [
            "parameterObject: duration values in seconds",
            "parameterObject: sustain values in seconds",
            "parameterObject: accent values between 0 and 1",
        ]

        self.argDefaults = [
            ("ws", "e", 30, 0, 0.25, 2.5),
            ("ws", "e", 60, 0.25, 0.25, 2.5),
            ("bg", "rc", [0, 1, 1, 1]),
        ]

        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if not ok:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.currentPulse = None  # init value, used in getCurrentRhythm
        # might be good to calculate a proper rhyhm object with given tempo
        self.rObj = rhythm.Rhythm((1, 1))  # just a place holder
        self.durObj = self._loadSub(args[0], "genPmtrObjs", "duration")
        self.susObj = self._loadSub(args[1], "genPmtrObjs", "sustain")
        self.accObj = self._loadSub(args[2], "genPmtrObjs", "accent")

    def checkArgs(self):
        ok, msg = self.durObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.susObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.accObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        d = self.durObj.repr(format)
        s = self.susObj.repr(format)
        a = self.accObj.repr(format)
        return "%s, (%s), (%s), (%s)" % (self.type, d, s, a)

    def reset(self):
        self.durObj.reset()
        self.susObj.reset()
        self.accObj.reset()

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.beatT in the 'call' method
        in order to account for changes in tempo
        """
        self.bpm = refDict["bpm"]  # bpm is not used to calc values
        # these are calculated values, not raw pulse values
        dur = abs(self.durObj(t, refDict))
        sus = abs(self.susObj(t, refDict))
        acc = abs(self.accObj(t, refDict))
        # this is interesting, but violates the intended use
        # of accent as an amp scalar
        # acc = drawer.floatToInt(self.accObj(t, refDict), 'weight')
        if acc <= 0:
            acc = 0
        elif acc >= 1:
            acc = 1
        # creat object for reference
        self.currentPulse = None  # cannot create pulse, as no bpm is envolved
        self.currentValue = dur, sus, acc  # no rests are possible
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class PulseTriple(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "pulseTriple"
        self.doc = lang.docPoPt
        self.argTypes = ["list", "list", "list", "list"]
        self.argNames = [
            "parameterObject: pulse divisor",
            "parameterObject: pulse multiplier",
            "parameterObject: accent value between 0 and 1",
            "parameterObject: sustain scalar greater than 0",
        ]

        self.argDefaults = [
            ("bg", "rc", (6, 5, 4, 3)),
            ("bg", "rc", (1, 2, 3)),
            ("bg", "rc", (1, 1, 1, 0)),
            ("ru", 0.5, 1.5),
        ]
        self.argDemos = [
            [
                ("c", 4),
                ("cl", "f{s}x{81}y{120}k{2}r{1}w{6}c{-2}", 109, 0.01, "sr", "oc"),
                ("cv", "f{s}x{81}y{120}k{2}r{1}w{3}c{8}", 109, 0.003, "sr", 0, 1, "oc"),
                ("c", 1),
            ],
        ]
        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if not ok:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.currentPulse = None  # init value, used in getCurrentRhythm
        # will raise error
        self.divObj = self._loadSub(args[0], "genPmtrObjs", "divisor")
        self.multObj = self._loadSub(args[1], "genPmtrObjs", "multiplier")
        self.accObj = self._loadSub(args[2], "genPmtrObjs", "accent")
        self.susObj = self._loadSub(args[3], "genPmtrObjs", "sustain")

    def checkArgs(self):
        ok, msg = self.divObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.multObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.accObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.susObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        d = self.divObj.repr(format)
        m = self.multObj.repr(format)
        a = self.accObj.repr(format)
        s = self.susObj.repr(format)
        return "%s, (%s), (%s), (%s), (%s)" % (self.type, d, m, a, s)

    def reset(self):
        self.divObj.reset()
        self.multObj.reset()
        self.accObj.reset()
        self.susObj.reset()

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.beatT in the 'call' method
        in order to account for changes in tempo
        """
        self.bpm = refDict["bpm"]  # bpm is not used to calc values
        # these are calculated values, not raw pulse values
        d = abs(drawer.floatToInt(self.divObj(t, refDict), "weight"))
        if d == 0:
            d = 1
        m = abs(drawer.floatToInt(self.multObj(t, refDict), "weight"))
        if m == 0:
            m = 1
        # used to be round; this is no longer done, as acc are implemented
        acc = abs(self.accObj(t, refDict))
        if acc <= 0:
            acc = 0  # must limit b/n 0 and 1
        elif acc >= 1:
            acc = 1
        sus = abs(self.susObj(t, refDict))  # dont round or weight
        if sus == 0:
            sus = 1  # sus of 0 is an error
        # create pulse object
        self.currentPulse = rhythm.Pulse((d, m, acc), "triple")
        self.currentPulse.setSus(sus)
        self.currentValue = self.currentPulse(self.bpm)  # call w/ bpm
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--


class PulseSieve(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "pulseSieve"
        self.doc = lang.docPoPs
        self.argTypes = [["str", "num", "list"], "num", "list", "str", "str"]

        self.argNames = [
            "logicalString",
            "sieveLength",
            "pulse",
            "selectionString",
            "articulationString",
        ]
        self.argDefaults = ["3|4|5@2", 60, (3, 1, 1), "oc", "a"]
        self.argDemos = [
            ["3|4|5@2", 60, (4, 1, 1), "rc", "s"],
        ]

        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.currentPulse = None  # init value, used in getCurrentRhythm
        self.length = abs(int(round(self.args[1])))
        self.z = list(range(0, self.length))
        try:
            self.sieveObj = sieve.Sieve(self.args[0], self.z)
        except AttributeError:
            raise error.ParameterObjectSyntaxError("incorrect sieve syntax.")

        try:
            self.pulseObj = rhythm.Pulse(self.args[2])
        except error.PulseSyntaxError:
            raise error.ParameterObjectSyntaxError("incorrect sieve syntax.")
        self.pulseObj.setSus(0.94)  # no sustain

        self.pulseOn = self.pulseObj.copy()
        self.pulseOn.setAcc(1)  # force on
        self.pulseOff = self.pulseObj.copy()
        self.pulseOff.setAcc(0)  # force off
        # gets a list if numbers, like 0,3,4,6,9,10
        # interpret as equal dur time points

        # get format based on ariticulation
        self.articulation = self._articulationParser(self.args[4])
        if self.articulation == "sustain":
            fmt = "wid"
        elif self.articulation == "attack":
            fmt = "bin"
        self.sieveObj.segFmtSet(fmt)
        self.sieveSeg = self.sieveObj(0, self.z)
        # set z as list from which selector draws
        self.control = self._selectorParser(self.args[3])  # raises exception
        self.selector = basePmtr.Selector(self.sieveSeg, self.control)

    def checkArgs(self):
        if len(self.sieveSeg) == 0:
            return 0, "sieve segment is empty; choose a longer length."
        return 1, ""

    def repr(self, format=""):
        msg = []
        msg.append(
            "%s, %s, %s, %s, %s, %s"
            % (
                self.type,
                str(self.sieveObj),
                typeset.anyDataToStr(self.length),
                self.pulseObj.repr("triple"),
                self.control,
                self.articulation,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(self.LMARGIN + "%s" % self._scrubList(self.sieveSeg))
        return "".join(msg)

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.beatT in the 'call' method
        in order to account for changes in tempo
        if its an attack, use binary segment to select on /off
        if its a sustain, use binary on and scale
        """
        self.bpm = refDict["bpm"]
        if self.articulation == "attack":
            bin = self.selector()  # get integer from self.z
            if bin:  # if at this step in sieve seg
                self.currentPulse = self.pulseOn
            else:  # supply a rest
                self.currentPulse = self.pulseOff
        else:
            wid = self.selector()  # wid will be 1 or greater
            self.currentPulse = self.pulseOn.copy()  # always on, get a copy
            self.currentPulse.scale(wid)  # scale by width

        self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--


class RhythmSieve(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "rhythmSieve"
        self.doc = lang.docPoRs
        self.argTypes = [
            ["str", "num", "list"],
            "num",
            "str",
            "list",
        ]
        self.argNames = [
            "logicalString",
            "sieveLength",
            "selectionString",
            "parameterObject: Rhythm Generator",
        ]
        self.argDefaults = [
            "3|4|5",
            60,
            "rw",
            ("l", ((3, 1, 1), (3, 1, 1), (3, 5, 1))),
        ]

        self.priority = 9  # rhythm gets top priority
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.currentPulse = None  # init value, used in getCurrentRhythm
        self.length = abs(int(round(self.args[1])))
        self.z = list(range(0, self.length))
        try:
            self.sieveObj = sieve.Sieve(self.args[0], self.z)
        except AttributeError:
            raise error.ParameterObjectSyntaxError("incorrect sieve syntax.")

        # NOTE: update this to use binary segment
        # gets a binary representawtion
        self.sieveSeg = self.sieveObj(0, self.z, "bin")
        # set z as list from which selector draws
        self.control = self._selectorParser(self.args[2])  # raises exception
        # select 1/0 from ginary sieve seg
        self.selector = basePmtr.Selector(self.sieveSeg, self.control)
        # create a parameter object
        self.rthmObj = self._loadSub(self.args[3], "rthmPmtrObjs")

    def checkArgs(self):
        ok, msg = self.rthmObj.checkArgs()
        if ok != 1:
            return ok, msg
        if len(self.sieveSeg) == 0:
            return 0, "sieve segment is empty; choose a longer length."
        if self.length < 1:
            return 0, "argument error: length must be 1 or greater."
        return 1, ""

    def repr(self, format=""):
        msg = []
        msg.append(
            "%s, %s, %s, %s, (%s)"
            % (
                self.type,
                str(self.sieveObj),
                typeset.anyDataToStr(self.length),
                self.control,
                self.rthmObj.repr(format),
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(self.LMARGIN + "%s" % self._scrubList(self.sieveSeg))
        return "".join(msg)

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        """all rhythm objects must use self.beatT in the 'call' method
        in order to account for changes in tempo
        """
        self.bpm = refDict["bpm"]
        # call to process
        junk = self.rthmObj(t, refDict)
        pulseObj = self.rthmObj.currentPulse  # get pulse object

        pulseOn = pulseObj.copy()
        pulseOn.setAcc(1)  # force on
        pulseOff = pulseObj.copy()
        pulseOff.setAcc(0)  # force off

        bin = self.selector()  # get integer from self.z
        if bin:  # if 1
            self.currentPulse = pulseOn
        else:  # # a slot
            self.currentPulse = pulseOff
        self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class MarkovPulse(basePmtr.RhythmParameter):
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "markovPulse"
        self.doc = lang.docPoMp
        self.argTypes = ["str", "list"]
        self.argNames = ["transitionString", "parameterObject: order value"]
        # note: restringulator can hand commas in braces...

        # TODO: accept single value for order value!

        self.argDefaults = ["a{3,1,1}b{2,1,1}c{3,2,0}:{a=3|b=4|c=1}", ("c", 0)]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.markovObj = markov.Transition()  # creat obj w/o loading
        try:
            self.markovObj.loadTransition(self.args[0])
        except error.TransitionSyntaxError as e:
            raise error.ParameterObjectSyntaxError(
                "Markov transition creation failed: %s" % e
            )
        # will raise error
        self.orderObj = self._loadSub(self.args[1], "genPmtrObjs")
        # need to store accumulated values
        self.accum = []
        # create a dictionary to store pulse objects, w/ string
        self.pulseRef = {}
        # we only need unique signified; even if more than one symbol refers
        # to the same signified, this does not matter
        for key in self.markovObj.getSignified():
            try:
                pulseObj = rhythm.Pulse(key)  # let guess pulse type
            except error.PulseSyntaxError as e:
                raise error.ParameterObjectSyntaxError(
                    "failed pulse object definition: %s" % e
                )
            self.pulseRef[key] = pulseObj  # store objs

    def checkArgs(self):
        ok, msg = self.orderObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        orderStr = self.orderObj.repr(format)
        msg = []
        msg.append("%s, %s, (%s)" % (self.type, str(self.markovObj), orderStr))
        return "".join(msg)

    def reset(self):
        self.orderObj.reset()
        self.accum = []

    def __call__(self, t=None, refDict=None):
        self.bpm = refDict["bpm"]
        # assume that unitVal is produced with a uniform distribution
        unitVal = random.random()  # check random instance creation...
        order = self.orderObj(t, refDict)
        self.accum.append(self.markovObj.next(unitVal, self.accum, order))
        if len(self.accum) > self.MARKOVLIMIT:
            self.accum.pop(0)  # remove first in list
        # the value returned from next will be a signified, not a symbol
        self.currentPulse = self.pulseRef[self.accum[-1]]  # get pulse object
        self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        return self.currentValue


class MarkovRhythmAnalysis(basePmtr.RhythmParameter):

    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "markovRhythmAnalysis"
        self.doc = lang.docPoMra

        self.argTypes = ["list", "int", "int", "list"]
        self.argNames = [
            "parameterObject: source Rhythm Generator",
            "pulseCount",
            "maxAnalysisOrder",
            "parameterObject: output order value",
        ]
        self.argDefaults = [
            (
                "l",
                ((4, 3, 1), (4, 3, 1), (4, 2, 0), (8, 1, 1), (4, 2, 1), (4, 2, 1)),
                "oc",
            ),
            12,
            2,
            ("cg", "u", 0, 2, 0.25),
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.srcObj = self._loadSub(self.args[0], "rthmPmtrObjs")
        self.pulseCount = self.args[1]
        self.maxAnalysisOrder = self.args[2]
        self.orderObj = self._loadSub(self.args[3], "genPmtrObjs")

        # need to store accumulated values
        self.analysisSeries = []
        self.accum = []
        # create a dictionary to store pulse objects, w/ string
        self.pulseRef = {}
        # analysis is done on init
        self.markovObj = markov.Transition()  # creat obj w/o loading
        # this may raise an exception
        self._updateAnalysis()

    def checkArgs(self):
        if self.pulseCount <= 0:
            return 0, "valueCount error: must be greater than zero."
        if self.maxAnalysisOrder <= 0:
            return 0, "maxAnalysisOrder error: must be greater than zero."
        if self.maxAnalysisOrder > self.MARKOVLIMIT:
            return (
                0,
                "maxAnalysisOrder error: analysis order cannot exceed %s."
                % self.MARKOVLIMIT,
            )
        ok, msg = self.srcObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.orderObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        s = self.srcObj.repr(format)
        o = self.orderObj.repr(format)
        msg = []
        msg.append(
            "%s, (%s), %s, %s, (%s)"
            % (
                self.type,
                s,
                typeset.anyDataToStr(self.pulseCount),
                typeset.anyDataToStr(self.maxAnalysisOrder),
                o,
            )
        )
        # if format == 'argsOnly': # as string
        return "".join(msg)
        # show markov if not argsOnly
        # this will be a problem if depth is significant
        # msg.append('\n')
        # msg.append(self.LMARGIN + '%s' % str(self.markovObj))
        # return ''.join(msg)

    def reset(self):
        self.srcObj.reset()
        self.orderObj.reset()
        self.accum = []
        self.pulseRef = {}
        self._updateAnalysis()  # srcObj will be reset before this, so may be same

    def _updateAnalysis(self):
        # note: this may raise an error if po is expecting values in the refDict
        self.analysisSeries = []
        for i in range(self.pulseCount):
            refDict = {"bpm": 60}  # this bpm value is not relevant, but needed
            q = self.srcObj(i, refDict)  # call object to get next value
            self.analysisSeries.append(str(self.srcObj.currentPulse))
        # create object with source values
        self.markovObj.loadList(self.analysisSeries, self.maxAnalysisOrder)
        for key in self.markovObj.getSignified():  # get pulse strings
            # this should never raise an error, as generate by rhythm pmtr obj
            self.pulseRef[key] = rhythm.Pulse(key, "triple")  # store objs

    def __call__(self, t=None, refDict=None):
        self.bpm = refDict["bpm"]
        # assume that unitVal is produced with a uniform distribution
        unitVal = random.random()  # check random instance creation...
        order = self.orderObj(t, refDict)
        self.accum.append(self.markovObj.next(unitVal, self.accum, order))
        if len(self.accum) > self.MARKOVLIMIT:
            self.accum.pop(0)  # remove first in list

        self.currentPulse = self.pulseRef[self.accum[-1]]  # get pulse object
        self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class IterateRhythmGroup(basePmtr.RhythmParameter):
    # this follows closel
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateRhythmGroup"
        self.doc = lang.docPoIrg

        self.argTypes = ["list", "list"]
        self.argNames = [
            "parameterObject: source Rhythm Generator",
            "parameterObject: group or skip control Generator",
        ]
        self.argDefaults = [
            (
                "l",
                ((4, 3, 1), (4, 3, 1), (4, 2, 0), (8, 1, 1), (4, 2, 1), (4, 2, 1)),
                "oc",
            ),
            ("bg", "rc", (-3, 1, -1, 5)),
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.valueBuffer = []  # grouped values that must be used before expelling
        self.rthmObj = self._loadSub(self.args[0], "rthmPmtrObjs")
        self.controlObj = self._loadSub(self.args[1], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.rthmObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.controlObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        genStr = self.rthmObj.repr(format)
        controlStr = self.controlObj.repr(format)
        return "%s, (%s), (%s)" % (self.type, genStr, controlStr)

    def reset(self):
        self.rthmObj.reset()
        self.controlObj.reset()
        self.valueBuffer = []  # reset initial value

    def __call__(self, t=None, refDict=None):
        self.bpm = refDict["bpm"]
        if self.valueBuffer == []:  # empty
            failCount = 0
            # note that t and refDict are constant within this loop
            while 1:
                q = self.controlObj(t, refDict)  # this should be a number
                q = drawer.floatToInt(q)
                if q < 0:  # skip values
                    for r in range(-drawer.floatToInt(q)):
                        skip = self.rthmObj(t, refDict)  # discard value
                elif q > 0:  # repeat values
                    # drop list reprsentation,get object
                    valTriple = self.rthmObj(t, refDict)
                    valObj = self.rthmObj.currentPulse  # get pulse object
                    for r in range(q):  # pack same value multiple times
                        self.valueBuffer.append((valTriple, valObj))
                # force the selection of a new value, examin results
                failCount = failCount + 1
                if failCount > self.FAILLIMIT and self.valueBuffer == []:
                    print(lang.WARN, self.type, "no values obtained; supplying value")
                    valTriple = self.rthmObj(t, refDict)
                    valObj = self.rthmObj.currentPulse
                    self.valueBuffer.append((valTriple, valObj))
                # leave loop of values in buffer
                if self.valueBuffer != []:
                    break
        # get value from value buffer
        valTriple, self.currentPulse = self.valueBuffer.pop(0)  # get and remove
        if self.currentPulse != None:  # use bpm if possible
            self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        else:
            self.currentValue = valTriple
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class IterateRhythmWindow(basePmtr.RhythmParameter):
    # this follows closel
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateRhythmWindow"
        self.doc = lang.docPoIrw

        self.argTypes = ["list", "list", "str"]
        self.argNames = [
            "parameterObjectList: a list of Rhythm Generators",
            "parameterObject: generate or skip control Generator",
            "selectionString",
        ]

        self.argDefaults = [
            (
                (
                    "l",
                    ((4, 3, 1), (4, 3, 1), (4, 2, 0), (8, 1, 1), (4, 2, 1), (4, 2, 1)),
                    "oc",
                ),
                ("cs", ("ru", 1.5, 4)),
            ),
            ("bg", "rc", (-3, 6, -1, 15)),
            "oc",
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.valueBuffer = []  # values g selected

        from athenaCL.libATH.libPmtr import parameter

        self.objArray = []
        for argList in self.args[0]:
            try:
                pmtrObj = parameter.factory(argList, "rthmPmtrObjs")
            except error.ParameterObjectSyntaxError as msg:
                raise error.ParameterObjectSyntaxError("failed sub-parameter: %s" % msg)
            self.objArray.append(pmtrObj)

        self.countObj = self._loadSub(self.args[1], "genPmtrObjs")
        # check control string
        self.control = self._selectorParser(self.args[2])
        # create a selector that returns indix values for objArray
        self.selector = basePmtr.Selector(list(range(len(self.objArray))), self.control)

    def checkArgs(self):
        ok, msg = self.countObj.checkArgs()
        if not ok:
            return 0, msg
        for obj in self.objArray:
            if obj.parent != "rhythm":
                return 0, "all sub ParameterObjects must be a Generator."
            ok, msg = obj.checkArgs()
            if not ok:
                return 0, msg
        return 1, ""

    def repr(self, format=""):
        countStr = self.countObj.repr(format)
        subPmtr = []
        for obj in self.objArray:
            subPmtr.append("(%s)" % (obj.repr(format)))
        return "%s, (%s), (%s), %s" % (
            self.type,
            ", ".join(subPmtr),
            countStr,
            self.control,
        )

    def reset(self):
        # call other resets
        self.countObj.reset()
        for obj in self.objArray:
            obj.reset()
        self.valueBuffer = []  # reset initial value
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        self.bpm = refDict["bpm"]

        if self.valueBuffer == []:  # empty
            failCount = 0
            # note that t and refDict are static while updating
            while 1:
                pos = self.selector()  # get position in obj arary
                q = self.countObj(t, refDict)  # this should be a number
                q = drawer.floatToInt(q)
                if q < 0:  # skip values
                    for r in range(q):
                        skip = self.genObj(t, refDict)  # discard value
                elif q > 0:  # gen values
                    for r in range(q):
                        # there is a potential problem here if t is not changed
                        # some parameter objects will return the same value
                        valTriple = self.objArray[pos](t, refDict)
                        valObj = self.objArray[pos].currentPulse
                        # must store obj and triple, incase no obj exists
                        self.valueBuffer.append((valTriple, valObj))
                # force the selection of a new value, examine results
                failCount = failCount + 1
                if failCount > self.FAILLIMIT and self.valueBuffer == []:
                    print(lang.WARN, self.type, "no values obtained; supplying value")
                    valTriple = self.objArray[pos](t, refDict)
                    valObj = self.objArray[pos].currentPulse
                    self.valueBuffer.append((valTriple, valObj))
                # leave loop if values in buffer
                if self.valueBuffer != []:
                    break
        # get value from value buffer
        valTriple, self.currentPulse = self.valueBuffer.pop(0)  # get and remove
        if self.currentPulse != None:  # use bpm if possible
            self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        else:
            self.currentValue = valTriple
        return self.currentValue


class IterateRhythmHold(basePmtr.RhythmParameter):
    # holds values and selects; variable refresh rates
    def __init__(self, args, refDict):
        basePmtr.RhythmParameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateRhythmHold"
        self.doc = lang.docPoIrh
        self.argTypes = ["list", "list", "list", "str"]
        self.argNames = [
            "parameterObject: source Rhythm Generator",
            "parameterObject: size Generator",
            "parameterObject: refresh count Generator",
            "selectionString",
        ]

        self.argDefaults = [
            (
                "pt",
                ("bg", "rc", (4, 2)),
                ("bg", "oc", (5, 4, 3, 2, 1)),
                ("c", 1),
                ("ru", 0.75, 1.25),
            ),
            ("bg", "rc", [2, 3, 4]),
            ("bg", "oc", [4, 5, 6]),
            "oc",
        ]

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.srcObj = self._loadSub(self.args[0], "rthmPmtrObjs")
        self.sizeObj = self._loadSub(self.args[1], "genPmtrObjs")
        self.refreshObj = self._loadSub(self.args[2], "genPmtrObjs")
        self.control = self._selectorParser(self.args[3])  # check control string
        self.valueBuffer = []  # collection values selected from
        self.eventCount = 0
        self.eventCountTotal = 0
        self.refreshValue = None

    def checkArgs(self):
        ok, msg = self.srcObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.sizeObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.refreshObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        srcStr = self.srcObj.repr(format)
        sizeStr = self.sizeObj.repr(format)
        refreshStr = self.refreshObj.repr(format)
        return "%s, (%s), (%s), (%s), %s" % (
            self.type,
            srcStr,
            sizeStr,
            refreshStr,
            self.control,
        )

    def reset(self):
        # call other resets
        self.srcObj.reset()
        self.sizeObj.reset()
        self.refreshObj.reset()
        self.eventCountTotal = 0  # only reset when all reset

    def _refresh(self, count, t, refDict):
        """refresh values stored in the col attribute; this is done during a run
        and is not the same as a reset"""
        count = int(round(count))
        if count == 0 and self.valueBuffer != []:
            return  # do nothing if filled, continue to use values
        elif count == 0 and self.valueBuffer == []:
            count = self.FAILLIMIT  # force some values to be added
        else:
            pass  # keep count as is

        self.valueBuffer = []  # clear list
        # get total event count values when refreshing
        for t in range(self.eventCountTotal, self.eventCountTotal + count):
            valTriple = self.srcObj(t, refDict)
            valObj = self.srcObj.currentPulse
            self.valueBuffer.append((valTriple, valObj))
        self.selector = basePmtr.Selector(self.valueBuffer, self.control)
        self.eventCount = 0

    def __call__(self, t=None, refDict=None):
        self.bpm = refDict["bpm"]
        if (
            self.eventCount >= self.refreshValue and self.refreshValue != 0
        ) or self.eventCountTotal == 0:  # last for first event, where refresh None
            self._refresh(self.sizeObj(t, refDict), t, refDict)
        # need to get a new refresh value
        if self.eventCount == 0 or self.eventCountTotal == 0:
            self.refreshValue = abs(int(round(self.refreshObj(t, refDict))))
        # if tt many events have happend, refresh, otherwise or if 0, dont
        self.eventCount = self.eventCount + 1
        self.eventCountTotal = self.eventCountTotal + 1

        # get value from value buffer
        valTriple, self.currentPulse = self.selector()  # get first and remove
        if self.currentPulse != None:  # use bpm if possible
            self.currentValue = self.currentPulse(self.bpm)  # dur, sus, acc
        else:
            self.currentValue = valTriple
        return self.currentValue


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
