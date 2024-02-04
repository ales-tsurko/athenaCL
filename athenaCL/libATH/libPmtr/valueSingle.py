# -----------------------------------------------------------------||||||||||||--
# Name:          valueSingle.py
# Purpose:       definitions of all paramater objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import random, copy
import unittest, doctest


from athenaCL.libATH import automata
from athenaCL.libATH import chaos
from athenaCL.libATH import dice
from athenaCL.libATH import drawer
from athenaCL.libATH import pitchTools
from athenaCL.libATH import language

lang = language.LangObj()
from athenaCL.libATH import markov
from athenaCL.libATH import feedback
from athenaCL.libATH import grammar
from athenaCL.libATH import quantize
from athenaCL.libATH import sieve
from athenaCL.libATH import table
from athenaCL.libATH import typeset
from athenaCL.libATH import unit
from athenaCL.libATH import error
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.libOrc import orc

_MOD = "valueSingle.py"
from athenaCL.libATH import prefTools

environment = prefTools.Environment(_MOD)

# -----------------------------------------------------------------||||||||||||--
# hidden basePmtr.Parameter objects for controlling instrument and time range


class StaticInst(basePmtr.Parameter):
    """note: this object contains a complete orchestra object inside
    of it; this may be inefficient
    """

    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "staticInst"
        self.doc = lang.docPoSi
        self.argTypes = ["int", "str"]
        self.argNames = ["instrumentNumber", "orchestraName"]
        self.argDefaults = [3, "csoundNative"]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error
        self.hidden = 1  # hidden from user creation
        self.inst = self.args[0]
        self.orcName = self.args[1]
        self.orcObj = orc.factory(self.orcName)

    def checkArgs(self):
        if not self.orcObj.instNoValid(self.inst):
            return 0, "instrument error: no such instrument available."
        return 1, ""

    def repr(self, format=""):
        if format == "argsOnly":  # as string
            return "%i" % self.inst
        name = self.orcObj.getInstName(self.inst)  # this gets name
        # name = self.orcBuilder.getInstName(self.inst)
        return "%s (%s: %s)" % (str(self.inst), self.orcName, name)

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.inst
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
# note that this might be modified to take PulstTriples
# this might be defined as new group of ParameterObjects form which the user
# can select?


class StaticRange(basePmtr.Parameter):
    def __init__(self, args, refDict):
        """
        >>> from athenaCL.libATH.libPmtr import valueSingle
        >>> a = valueSingle.StaticRange([[10,20]], {})
        >>> a()
        [10, 20]
        """
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "staticRange"
        self.doc = lang.docPoSr
        self.argTypes = [
            "list",
        ]
        self.argNames = ["timeRange"]
        self.argDefaults = [(0, 20)]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error
        self.hidden = 1  # hidden from user creation
        self.tRange = self.args[0]
        self.tStart = self.args[0][0]
        self.tEnd = self.args[0][1]

        if not drawer.isNum(self.tStart) or not drawer.isNum(self.tEnd):
            raise error.ParameterObjectSyntaxError("time range values must be numbers.")

    def checkArgs(self):
        if self.tStart == self.tEnd:
            return 0, "range error: start and end times cannot be the same value."
        if self.tStart > self.tEnd:
            return 0, "range error: start time must be before end time."
        if self.tStart < 0 or self.tEnd < 0:
            return 0, "range error: start and end times cannot be negative."
        return 1, ""

    def repr(self, format=""):
        # args only format returns just a list; other wise spaced nicely
        return typeset.timeRangeAsStr((self.tStart, self.tEnd), format)

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.tRange
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--


class CyclicGen(basePmtr.Parameter):
    # note: directions strings used be preceded by 'linear' but
    # this is no longer necessary
    # may want to add support for a dynamic increment value
    # and variable min and max?
    def __init__(self, args, refDict):
        """
        >>> from athenaCL.libATH.libPmtr import valueSingle
        >>> a = valueSingle.CyclicGen(['ud', 0, 10, .2], {})
        >>> a()
        0.20000...
        """
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "cyclicGen"
        self.doc = lang.docPoCg
        self.argTypes = ["str", "num", "num", "num"]
        self.argNames = ["directionString", "min", "max", "increment"]
        self.argDefaults = ["ud", 0, 1, 0.125]
        self.argDemos = [
            ["d", 0, 1, 0.125],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error
        self.directionSrc = self._directionParser(self.args[0])  # amy raise error
        self.direction = copy.copy(self.directionSrc)
        self.min = self.args[1]
        self.max = self.args[2]
        self.inc = self.args[3]
        # this should be adaptive
        self.cycle = self.min

    def checkArgs(self):
        if self.min > self.max:
            return 0, "range error: minimum is larger than maximum."
        if self.inc < 0 or self.inc > abs(self.max - self.min):
            return 0, "increment error: must fit within range."
        return 1, ""

    def repr(self, format=""):
        # as direction changes, show directionSrc not direction
        return "%s, %s, %s, %s, %s" % (
            self.type,
            self.directionSrc,
            typeset.anyDataToStr(self.min),
            typeset.anyDataToStr(self.max),
            typeset.anyDataToStr(self.inc),
        )

    def __call__(self, t=None, refDict=None):
        # direction values are converted on object init
        if self.direction == "upDown":
            self.cycle = self.cycle + self.inc
            if self.cycle > self.max:
                self.direction = "downUp"  # 1
                self.cycle = self.max
            else:
                pass  # do nothing, direction is now down
        elif self.direction == "downUp":
            self.cycle = self.cycle - self.inc
            if self.cycle < self.min:
                self.direction = "upDown"  # 0
                self.cycle = self.min
            else:
                pass  # do nothing, direction is now up
        elif self.direction == "up":
            if (self.cycle + self.inc) > self.max:
                self.direction = "up"  # 2
                self.cycle = self.min
            else:
                self.cycle = self.cycle + self.inc
                self.direction = "up"  # 2
                self.cycle = self.cycle
        elif self.direction == "down":
            if (self.cycle - self.inc) < self.min:
                self.direction = "down"  # 3
                self.cycle = self.max
            else:
                self.cycle = self.cycle - self.inc
                self.direction = "down"  # 3
                self.cycle = self.cycle
        self.currentValue = self.cycle
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class Constant(basePmtr.Parameter):
    def __init__(self, args, refDict):
        """
        >>> from athenaCL.libATH.libPmtr import valueSingle
        >>> a = valueSingle.Constant([3], {})
        >>> a()
        3
        """
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "constant"
        self.doc = lang.docPoC
        self.argTypes = [["str", "num"]]
        self.argNames = ["value"]
        self.argDefaults = [0]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error
        self.value = self.args[0]

    def checkArgs(self):
        return 1, ""

    def repr(self, format=""):
        return "%s, %s" % (self.type, typeset.anyDataToStr(self.value))

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.value
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class BasketGen(basePmtr.Parameter):
    def __init__(self, args, refDict):
        """
        >>> from athenaCL.libATH.libPmtr import valueSingle
        >>> a = valueSingle.BasketGen(['oc', [1,2,3]], {})
        >>> a()
        1
        """
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "basketGen"
        self.doc = lang.docPoBg
        self.argTypes = ["str", ["list", "num"]]
        self.argNames = ["selectionString", "valueList"]
        self.argDefaults = ["rc", [0, 0.25, 0.25, 1]]
        self.argDemos = [
            ["oo", [0, 0.1, 0.2, 0.4, 0.8, 0.6, 0.5, 1]],
            ["rw", [0, 0.1, 0.2, 0.4, 0.8, 0.6, 0.5, 1]],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        if drawer.isList(self.args[1]):
            self.list = list(self.args[1])
        else:
            self.list = [
                self.args[1],
            ]

        self.control = self._selectorParser(self.args[0])  # raises exception
        self.selector = basePmtr.Selector(self.list, self.control)

    def checkArgs(self):
        if len(self.list) == 0:
            return 0, "list must have more than 0 items."
        return 1, ""

    def repr(self, format=""):
        return "%s, %s, %s" % (self.type, self.control, self._scrubList(self.list))

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.selector()
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class BasketFill(basePmtr.Parameter):
    def __init__(self, args, refDict):
        """
        >>> from athenaCL.libATH.libPmtr import valueSingle
        >>> a = valueSingle.BasketFill(['oc', 3, 20], {})
        Traceback (most recent call last):
        ParameterObjectSyntaxError: wrong type of data...

        >>> a = valueSingle.BasketFill(['oc', ['bg', 'oc', [3,100]], 20], {})
        >>> a.repr()
        'basketFill, orderedCyclic, (basketGen, orderedCyclic, (3,100)), 20'
        >>> a()
        3
        """
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "basketFill"
        self.doc = lang.docPoBf
        self.argTypes = ["str", "list", "int"]
        self.argNames = [
            "selectionString",
            "parameterObject: source Generator",
            "valueCount",
        ]
        self.argDefaults = ["oc", ["ru", 0, 1], 10]
        self.argDemos = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.control = self._selectorParser(self.args[0])  # raises exception
        self.fillObj = self._loadSub(self.args[1], "genPmtrObjs")
        self.valueCount = abs(self.args[2])
        if self.valueCount == 0:
            self.valueCount = 1  # correct bad arg
        # do processing on init
        self.basket = []
        for t in range(self.valueCount):
            self.basket.append(self.fillObj(t, refDict))
        # create selector to store and access values
        self.selector = basePmtr.Selector(self.basket, self.control)

    def checkArgs(self):
        if len(self.basket) == 0:
            return 0, "list must have more than 0 items."
        ok, msg = self.fillObj.checkArgs()  # check storead po
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        return "%s, %s, (%s), %s" % (
            self.type,
            self.control,
            self.fillObj.repr(format),
            self.valueCount,
        )

    def reset(self):
        self.selector.reset()
        self.fillObj.reset()  # this is not necesary

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.selector()
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class BasketFillSelect(basePmtr.Parameter):
    # given a list, select w/ unit control
    def __init__(self, args, refDict):
        """
        >>> from athenaCL.libATH.libPmtr import valueSingle
        >>> a = valueSingle.BasketFillSelect([['ru',0,1], 3, ['ru',0,1]], {})
        >>> a.repr()
        'basketFillSelect, (randomUniform, (constant, 0), (constant, 1)), 3, (randomUniform, (constant, 0), (constant, 1))'
        >>> a = valueSingle.BasketFillSelect([['bg','oc',[20,30]], 2, ['bg', 'oc', [.2,.8]]], {})
        >>> a()
        20
        >>> a()
        30
        """
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "basketFillSelect"
        self.doc = lang.docPoBfs
        self.argTypes = ["list", "int", "list"]
        self.argNames = [
            "parameterObject: source Generator",
            "valueCount",
            "parameterObject: selection Generator",
        ]

        self.argDefaults = [["ru", 0, 1], 10, ["rb", 0.2, 0.2, 0, 1]]
        self.argDemos = []

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.fillObj = self._loadSub(self.args[0], "genPmtrObjs")
        self.valueCount = abs(self.args[1])
        if self.valueCount == 0:
            self.valueCount = 1  # correct bad arg
        # do processing on init
        self.basket = []
        for t in range(self.valueCount):
            self.basket.append(self.fillObj(t, refDict))
        # configure selector
        self.unitSelectObj = self._loadSub(self.args[2], "genPmtrObjs")
        self.valueBoundary = unit.unitBoundaryEqual(len(self.basket))
        # environment.printDebug([self.basket, self.valueBoundary])

    def checkArgs(self):
        if len(self.basket) == 0:
            return 0, "list must have more than 0 items."
        ok, msg = self.fillObj.checkArgs()  # check storead po
        if not ok:
            return 0, msg
        ok, msg = self.unitSelectObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        fillObjStr = self.fillObj.repr(format)
        unitSelectStr = self.unitSelectObj.repr(format)
        return "%s, (%s), %s, (%s)" % (
            self.type,
            fillObjStr,
            self.valueCount,
            unitSelectStr,
        )

    def reset(self):
        self.fillObj.reset()
        self.unitSelectObj.reset()

    def __call__(self, t=None, refDict=None):
        # get value w/n unit interval, de-map from arptition
        pos = unit.unitBoundaryPos(
            unit.limit(self.unitSelectObj(t, refDict)), self.valueBoundary
        )
        self.currentValue = self.basket[pos]
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class BasketSelect(basePmtr.Parameter):
    # given a list, select w/ unit control
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "basketSelect"
        self.doc = lang.docPoBs
        self.argTypes = [["list", "num"], "list"]
        self.argNames = ["valueList", "parameterObject: selection Generator"]

        self.argDefaults = [
            (1, 2, 3, 4, 5, 6, 7, 8, 9),
            (
                "rb",
                0.2,
                0.2,
                ("bpl", "e", "s", ((0, 0.4), (120, 0))),
                ("bpl", "e", "s", ((0, 0.6), (120, 1))),
            ),
        ]
        self.argDemos = []

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        if drawer.isList(self.args[0]):
            self.list = list(self.args[0])
        else:
            self.list = [
                self.args[0],
            ]

        self.unitSelectObj = self._loadSub(self.args[1], "genPmtrObjs")
        self.valueBoundary = unit.unitBoundaryEqual(len(self.list))

    def checkArgs(self):
        if len(self.list) == 0:
            return 0, "list must have more than 0 items."
        ok, msg = self.unitSelectObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        unitSelectStr = self.unitSelectObj.repr(format)
        return "%s, %s, (%s)," % (self.type, self._scrubList(self.list), unitSelectStr)

    def reset(self):
        self.unitSelectObj.reset()

    def __call__(self, t=None, refDict=None):
        # get value w/n unit interval, de-map from arptition
        pos = unit.unitBoundaryPos(
            unit.limit(self.unitSelectObj(t, refDict)), self.valueBoundary
        )
        self.currentValue = self.list[pos]
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class SieveList(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "sieveList"
        self.doc = lang.docPoSl
        self.argTypes = ["str", "int", "int", "str", "str"]
        self.argNames = [
            "logicalString",
            "zMin",
            "zMax",
            "format: integer, width, unit, binary",
            "selectionString",
        ]
        self.argDefaults = ["3|4", -12, 12, "int", "oc"]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        try:
            self.sieveObj = sieve.Sieve(self.args[0])
        except AttributeError:
            raise error.ParameterObjectSyntaxError("sieve creation failed")

        a = self.args[1]
        b = self.args[2]
        if a > b:
            self.zMin = b
            self.zMax = a
        elif a < b:
            self.zMin = a
            self.zMax = b
        else:
            raise error.ParameterObjectSyntaxError("zMin must not be equal to zMax")
        self.z = list(range(self.zMin, self.zMax + 1))
        self.length = len(self.z)

        self.format = self._sieveFormatParser(self.args[3])
        self.segment = self.sieveObj(0, self.z, self.format)
        self.control = self._selectorParser(self.args[4])  # raises exception
        self.selector = basePmtr.Selector(self.segment, self.control)

    def checkArgs(self):
        if self.length == 0:
            return 0, "z is empty; choose a larger z range."
        if len(self.segment) == 0:
            return 0, "sieve segment is empty; choose a better logic formula or z."
        return 1, ""

    def repr(self, format=""):
        msg = []
        msg.append(
            "%s, %s, %s, %s, %s, %s"
            % (
                self.type,
                str(self.sieveObj),
                typeset.anyDataToStr(self.zMin),
                typeset.anyDataToStr(self.zMax),
                self.format,
                self.control,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(self.LMARGIN + "%s" % self._scrubList(self.segment))
        return "".join(msg)

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.selector()
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class ValueSieve(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "valueSieve"
        self.doc = lang.docPoVs
        self.argTypes = ["str", "num", ["num", "list"], ["num", "list"], "str"]
        self.argNames = ["logicalString", "length", "min", "max", "selectionString"]
        self.argDefaults = ["3&19|4&13@11", 360, 0, 1, "oo"]
        self.argDemos = [
            ["3&19|4&13@11|5@2&15@2", 120, 0, 1, "rw"],
            [
                "3&19|4&13@11",
                240,
                ("bpp", "e", "s", ((0, 0), (80, 48), (120, 30)), -1.25),
                ("bpp", "e", "s", ((0, 100), (80, 52), (120, 100)), 1.25),
                "oc",
            ],
            [
                "3&19|4&13@11",
                120,
                ("bpp", "e", "s", ((0, 0), (80, 48), (120, 30)), -1.25),
                ("bpp", "e", "s", ((0, 100), (80, 52), (120, 100)), 1.25),
                "rp",
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        try:
            self.sieveObj = sieve.Sieve(self.args[0])
        except AttributeError:
            raise error.ParameterObjectSyntaxError("sieve creation failed")

        self.length = int(self.args[1])
        self.z = list(range(0, abs(self.length)))
        self.normSeries = self.sieveObj(0, self.z, "unit")
        # self.normSeries = unit.unitNormRange(self.sieveSeg)
        if self.args[1] < 0:  # a negative length reverses the series
            self.normSeries.reverse()

        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.control = self._selectorParser(self.args[4])  # raises exception
        self.selector = basePmtr.Selector(self.normSeries, self.control)

    def checkArgs(self):
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg

        if len(self.normSeries) == 0:
            return 0, "sieve segment is empty; choose a longer length."
        if self.length < 1:
            return 0, "argument error: length must be 1 or greater."
        return 1, ""

    def repr(self, format=""):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        msg = []
        msg.append(
            "%s, %s, %s, (%s), (%s), %s"
            % (
                self.type,
                str(self.sieveObj),
                typeset.anyDataToStr(self.length),
                minStr,
                maxStr,
                self.control,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(
            self.LMARGIN
            + "%s" % self._scrubList(self.normSeries, self.minObj(0), self.maxObj(0))
        )
        return "".join(msg)

    def reset(self):
        self.selector.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t=None, refDict=None):
        element = self.selector()
        self.currentValue = unit.denorm(
            element, self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class SieveFunnel(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "sieveFunnel"
        self.doc = lang.docPoSf
        self.argTypes = ["str", "num", ["num", "list"], ["num", "list"], "list"]
        self.argNames = [
            "logicalString",
            "length",
            "min",
            "max",
            "parameterObject: fill value generator",
        ]
        self.argDefaults = [
            "3|4",
            24,
            0,
            1,
            ("ru", 0, 1),
        ]
        self.argDemos = [
            [
                "5|13",
                14,
                ("ws", "e", 60, 0, 0, 0.25),
                ("ws", "e", 60, 0, 0.75, 1),
                ("ru", 0, 1),
            ],
            [
                "13@5|13@7|13@11",
                20,
                ("a", 0, ("ws", "e", 30, 1, -0.75, 1.75)),
                ("bpp", "e", "l", ((0, 100), (160, 20)), 2),
                ("rb", 0.4, 0.3, 0, 1),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        try:
            self.sieveObj = sieve.Sieve(self.args[0])
        except AttributeError:
            raise error.ParameterObjectSyntaxError("sieve creation failed")

        self.length = int(self.args[1])
        self.z = list(range(0, abs(self.length)))
        # NOTE: this needs to be updated to use a unit sieve segment
        self.sieveSeg = self.sieveObj(0, self.z)
        self.normSeries = unit.unitNormRange(self.sieveSeg)
        self.funnel = unit.FunnelUnit(self.sieveSeg)

        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.pmtrObj = self._loadSub(self.args[4], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.pmtrObj.checkArgs()
        if ok != 1:
            return ok, msg
        # check that pmtrObj produce value w/n unit interval
        if len(self.sieveSeg) == 0:
            return 0, "sieve segment is empty; choose a longer length."
        if self.length < 1:
            return 0, "argument error: length must be 1 or greater."
        return 1, ""

    def repr(self, format=""):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        pmtrStr = self.pmtrObj.repr(format)
        msg = []
        msg.append(
            "%s, %s, %s, (%s), (%s), (%s)"
            % (
                self.type,
                str(self.sieveObj),
                typeset.anyDataToStr(self.length),
                minStr,
                maxStr,
                pmtrStr,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(self.LMARGIN + "%s" % self._scrubList(self.sieveSeg))
        return "".join(msg)

    def reset(self):
        self.pmtrObj.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t=None, refDict=None):
        # limit parameter values to 0 and 1
        p = unit.limit(self.pmtrObj(t, refDict))
        unitVal = self.funnel.findNearest(p)
        self.currentValue = unit.denorm(
            unitVal, self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class ListPrime(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "listPrime"
        self.doc = lang.docPoLp
        self.argTypes = ["int", "int", "str", "str"]
        self.argNames = [
            "start",
            "length",
            "format: integer, width, unit, binary",
            "selectionString",
        ]
        self.argDefaults = [2, 50, "int", "oc"]
        self.argDemos = [
            [-100, 100, "wid", "rc"],
            [200, -30, "bin", "rp"],
        ]

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.start = self.args[0]
        self.length = self.args[1]
        self.format = self._sieveFormatParser(self.args[2])

        if self.length > 999999:  # a million values is too many!
            raise error.ParameterObjectSyntaxError(
                "length value exceeds a practical range"
            )

        # process prime segment
        self.obj = sieve.PrimeSegment(self.start, abs(self.length))
        self.segment = self.obj(self.format)

        if self.length < 0:  # a negative length reverses the series
            self.segment.reverse()

        self.control = self._selectorParser(self.args[3])  # raises exception
        self.selector = basePmtr.Selector(self.segment, self.control)

    def checkArgs(self):
        if self.length == 0:
            return 0, "length must not be 0."
        if len(self.segment) == 0:
            return 0, "segment obtained zero values; try a differetn start or length."
        return 1, ""

    def repr(self, format=""):
        msg = []
        msg.append(
            "%s, %s, %s, %s, %s"
            % (
                self.type,
                typeset.anyDataToStr(self.start),
                typeset.anyDataToStr(self.length),
                self.format,
                self.control,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(self.LMARGIN + "%s" % self._scrubList(self.segment))
        return "".join(msg)

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.selector()
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class ValuePrime(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "valuePrime"
        self.doc = lang.docPoVp
        self.argTypes = ["int", "int", ["num", "list"], ["num", "list"], "str"]
        self.argNames = ["start", "length", "min", "max", "selectionString"]
        self.argDefaults = [2, 50, 0, 1, "oo"]
        self.argDemos = [
            [100, 20, ["bphc", "e", "l", [(0, 0.5), (120, 1)]], 1, "rp"],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.start = self.args[0]
        self.length = self.args[1]

        if self.length > 999999:  # a million values is too many!
            raise error.ParameterObjectSyntaxError(
                "length value exceeds a practical range"
            )

        # process prime segment
        self.obj = sieve.PrimeSegment(self.start, abs(self.length))
        self.normSeries = self.obj("unit")  # force a normalized series

        if self.length < 0:  # a negative length reverses the series
            self.normSeries.reverse()

        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.control = self._selectorParser(self.args[4])  # raises exception
        self.selector = basePmtr.Selector(self.normSeries, self.control)

    def checkArgs(self):
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg

        if self.length == 0:
            return 0, "length must be larger than 0."
        if len(self.normSeries) == 0:
            return 0, "segment obtained zero values; try a differetn start or length."
        return 1, ""

    def repr(self, format=""):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        msg = []
        msg.append(
            "%s, %s, %s, (%s), (%s), %s"
            % (
                self.type,
                typeset.anyDataToStr(self.start),
                typeset.anyDataToStr(self.length),
                minStr,
                maxStr,
                self.control,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(
            self.LMARGIN
            + "%s" % self._scrubList(self.normSeries, self.minObj(0), self.maxObj(0))
        )
        return "".join(msg)

    def reset(self):
        self.selector.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t=None, refDict=None):
        element = self.selector()
        self.currentValue = unit.denorm(
            element, self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class CaList(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "caList"
        self.doc = lang.docPoCl
        self.argTypes = ["str", ["num", "list"], ["num", "list"], "str", "str"]
        self.argNames = [
            "caSpec",
            "parameterObject: rule",
            "parameterObject: mutation",
            "tableExtractionString",  # defined in base class
            "selectionString",
        ]
        self.argDefaults = ["f{f}i{c}x{81}y{120}", 0.25, 0.0005, "sc", "oc"]
        self.argDemos = [
            ["f{2}y{120}", ("mv", "a{90}b{182}:{a=29|b=1}", ("c", 0)), 0, "fria", "oc"],
        ]
        # check raw arguments for number, typed
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        rule = self.args[1]
        if drawer.isNum(rule):
            rule = ("c", rule)
        self.rule = self._loadSub(rule, "genPmtrObjs")
        mutation = self.args[2]
        if drawer.isNum(mutation):
            mutation = ("c", mutation)
        self.mutation = self._loadSub(mutation, "genPmtrObjs")

        self.tableFormat = table.monoFormatParser(self.args[3])  # raises exception
        if self.tableFormat == None:
            raise error.ParameterObjectSyntaxError("bad table format")

        # run ca only on init
        ruleStart = self.rule(0, self._refDictSim)
        mutationStart = self.mutation(0, self._refDictSim)

        try:
            self.ca = automata.factory(self.args[0], ruleStart, mutationStart)
        except error.AutomataSpecificationError as e:
            raise error.ParameterObjectSyntaxError("error in CA specification: %s" % e)

        # must supply yTotal here to get generations w/ skip
        for i in range(1, self.ca.spec.get("yTotal")):  # already got zero
            self.ca.gen(
                1, self.rule(i, self._refDictSim), self.mutation(i, self._refDictSim)
            )
        norm = 0  # do not normalize
        self.segment = self.ca.getCells(
            self.tableFormat,
            norm,
            self.ca.spec.get("s"),
            None,
            self.ca.spec.get("c"),
            self.ca.spec.get("w"),
        )

        self.control = self._selectorParser(self.args[4])  # raises exception
        self.selector = basePmtr.Selector(self.segment, self.control)

    def checkArgs(self):
        ok, msg = self.rule.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.mutation.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        rule = self.rule.repr(format)
        mutation = self.mutation.repr(format)
        msg = []
        msg.append(
            "%s, %s, (%s), (%s), %s, %s"
            % (self.type, str(self.ca), rule, mutation, self.tableFormat, self.control)
        )
        if format == "argsOnly":
            return "".join(msg)
        return "".join(msg)

    def reset(self):
        # not sure mutation and rule resets are useful
        self.mutation.reset()
        self.rule.reset()
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.selector()
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class CaValue(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "caValue"
        self.doc = lang.docPoCv
        self.argTypes = [
            "str",
            ["num", "list"],
            ["num", "list"],
            "str",
            ["num", "list"],
            ["num", "list"],
            "str",
        ]
        self.argNames = [
            "caSpec",
            "parameterObject: rule",
            "parameterObject: mutation",
            "tableExtractionString",  # options defined in base class
            "min",
            "max",
            "selectionString",
        ]
        self.argDefaults = ["f{s}", ("c", 110), ("c", 0), "sr", 0, 1, "oc"]
        self.argDemos = [
            [
                "f{s}x{81}y{120}k{2}r{1}i{r}",
                ("bpl", "e", "s", ((0, 30), (119, 34))),
                0.05,
                "sr",
                0,
                1,
                "oc",
            ],
            [
                "f{t}x{81}y{120}k{3}r{1}w{12}",
                1842,
                ("bpl", "e", "l", ((0, 0), (80, 0.02))),
                "sr",
                ("ws", "e", 15, 0, 0, 0.4),
                1,
                "oc",
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        rule = self.args[1]
        if drawer.isNum(rule):
            rule = ("c", rule)
        self.rule = self._loadSub(rule, "genPmtrObjs")
        mutation = self.args[2]
        if drawer.isNum(mutation):
            mutation = ("c", mutation)
        self.mutation = self._loadSub(mutation, "genPmtrObjs")

        self.tableFormat = table.monoFormatParser(self.args[3])  # raises exception
        if self.tableFormat == None:
            raise error.ParameterObjectSyntaxError("bad table format")

        # run ca only on init
        ruleStart = self.rule(0, self._refDictSim)
        mutationStart = self.mutation(0, self._refDictSim)

        try:
            self.ca = automata.factory(self.args[0], ruleStart, mutationStart)
        except error.AutomataSpecificationError as e:
            raise error.ParameterObjectSyntaxError("error in CA specification: %s" % e)

        # must supply yTotal here to get generations w/ skip
        for i in range(1, self.ca.spec.get("yTotal")):  # already got zero
            self.ca.gen(
                1, self.rule(i, self._refDictSim), self.mutation(i, self._refDictSim)
            )
        norm = 1  # normalize
        self.segment = self.ca.getCells(
            self.tableFormat,
            norm,
            self.ca.spec.get("s"),
            None,
            self.ca.spec.get("c"),
            self.ca.spec.get("w"),
        )

        self.minObj, self.maxObj = self._loadMinMax(self.args[4], self.args[5])

        self.control = self._selectorParser(self.args[6])  # raises exception
        self.selector = basePmtr.Selector(self.segment, self.control)

    def checkArgs(self):
        ok, msg = self.rule.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.mutation.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg
        return 1, ""

    def repr(self, format=""):
        rule = self.rule.repr(format)
        mutation = self.mutation.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        msg = []
        msg.append(
            "%s, %s, (%s), (%s), %s, (%s), (%s), %s"
            % (
                self.type,
                str(self.ca),
                rule,
                mutation,
                self.tableFormat,
                minStr,
                maxStr,
                self.control,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        return "".join(msg)

    def reset(self):
        # not sure mutation and rule resets are useful
        self.mutation.reset()
        self.rule.reset()
        self.selector.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = unit.denorm(
            self.selector(), self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--


class PathRead(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "pathRead"
        self.outputFmt = "str"  # declare outputFmt as string?
        self.doc = lang.docPoPr
        self.argTypes = [
            "str",
        ]
        self.argNames = ["pathFormatString"]
        self.argDefaults = ["forte"]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error
        self.formatNames = ["forte", "mason", "fq", "ps", "midi", "pch", "name"]
        # adjust arg names to embed string selection choices
        self.argNames[0] = self.argNames[0] + ":" + ",".join(self.formatNames)
        self.format = self.args[0]

    def checkArgs(self):
        if self.format not in self.formatNames:
            return 0, "format error: bad format name."
        return 1, ""

    def repr(self, format=""):
        msg = []
        msg.append("%s, %s" % (self.type, self.format))
        return "".join(msg)

    def __call__(self, t=None, refDict=None):
        # we will always have a current multiset, so getting chord data is
        multisetObj = refDict["stateCurrentMultiset"]
        # not a problem; in some cases getting particluar pitch information
        # may be hard; psReal may not have been calcualted, or out of date
        # as in the case w/ ornaments.
        # NOTE: this might be more efficient to not use objects, just convert
        if refDict["stateCurrentPitchPost"] != None:  # it has been assigned
            psReal = refDict["stateCurrentPitchPost"]
        else:  # get from ps value; may not be transposed
            psReal = refDict["stateCurrentPitchRaw"]
        # create a new pitch object
        psObj = pitchTools.Pitch(psReal, "psReal")

        if self.format == "mason":
            self.currentValue = multisetObj.get("mason")
        elif self.format == "forte":  # get a forte string
            self.currentValue = '"%s"' % multisetObj.repr("sc")
        elif self.format == "fq":
            self.currentValue = psObj.get("fq")
        elif self.format == "ps":
            self.currentValue = psObj.get("psReal")
        elif self.format == "midi":
            self.currentValue = psObj.get("midi")
        elif self.format == "pch":
            self.currentValue = psObj.get("pch")
        elif self.format == "name":
            self.currentValue = psObj.get("psName")

        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class LogisticMap(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "logisticMap"
        self.doc = lang.docPoLm
        self.argTypes = [
            "num",
            ["str", "list", "num"],
            ["num", "list"],
            ["num", "list"],
        ]
        self.argNames = ["initValue", "parameterObject: p value", "min", "max"]
        self.argDefaults = [0.5, ("wt", "e", 90, 0, 2.75, 4), 0, 1]
        self.argDemos = [
            [0.1, ("bg", "rw", (3, 3, 3, 3.2, 3.2, 3.2, 3.9, 3.9, 3.9)), 0, 1],
            [
                0.5,
                ("ig", ("bg", "rc", (3, 3.2, 3.5699461)), ("bg", "rc", (5, 7, 9))),
                ("bpl", "e", "l", ((0, 0.5), (60, 0), (120, 0.5))),
                ("bpl", "e", "l", ((0, 0.5), (40, 3))),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.xInit = self.args[0]
        self.x = copy.copy(self.args[0])  # init value
        ref = {
            3.2: ["bi", "2"],
            3.44951: ["quad", "4"],
            3.5699461: [
                "chaos",
            ],  # this value does not seem to be cahaotic
            3.57: [
                "periodic01",
            ],
        }
        self.pmtrObj = self._loadAutoConstantStr(self.args[1], ref, "genPmtrObjs")
        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.p = 0  # will be set by ParameterObject

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg
        if self.xInit > 1 or self.xInit <= 0:
            return 0, "incorrect x init value; value must be between 0 and 1."
        return 1, ""

    def repr(self, format=""):
        pmtrStr = self.pmtrObj.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return "%s, %s, (%s), (%s), (%s)" % (
            self.type,
            typeset.anyDataToStr(self.xInit),
            pmtrStr,
            minStr,
            maxStr,
        )

    def reset(self):
        self.pmtrObj.reset()
        self.minObj.reset()
        self.maxObj.reset()
        self.x = copy.copy(self.xInit)  # reset initial value

    def __call__(self, t=None, refDict=None):
        self.p = self.pmtrObj(t, refDict)
        self.x = chaos.verhulst(self.p, self.x)
        self.currentValue = unit.denorm(
            self.x, self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


class HenonBasket(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "henonBasket"
        self.doc = lang.docPoHb
        # a, b, xinit, yinit, min, max, select
        self.argTypes = [
            "num",
            "num",
            ["num", "list"],
            ["num", "list"],
            "int",
            "str",
            ["num", "list"],
            ["num", "list"],
            "str",
        ]
        self.argNames = [
            "xInit",
            "yInit",
            "parameterObject: a value",
            "parameterObject: b value",
            "valueCount",
            "valueSelect: x, y, xy, yx",
            "min",
            "max",
            "selectionString",
        ]

        self.argDefaults = [0.5, 0.5, 1.4, 0.3, 1000, "x", 0, 1, "oc"]
        self.argDemos = [
            [0.5, 0.5, 0.5, 0.8, 1000, "yx"],
            [0.5, 0.5, ("cg", "ud", 0, 0.9, 0.05), 0.3, 1000, "xy"],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.xInit = self.args[0]
        self.yInit = self.args[1]
        # _load methods will raise error if found
        self.a = self._loadAutoConstant(self.args[2], "genPmtrObjs")
        self.b = self._loadAutoConstant(self.args[3], "genPmtrObjs")
        self.valueCount = abs(self.args[4])
        self.valueSelect = self._valueSelectBiParser(self.args[5])
        self.minObj, self.maxObj = self._loadMinMax(self.args[6], self.args[7])
        self.control = self._selectorParser(self.args[8])  # raises exception

        # do processing:
        self.basket = []
        self.henon = chaos.Henon(
            self.a(0, self._refDictSim),
            self.b(0, self._refDictSim),
            self.xInit,
            self.yInit,
        )
        i = 0
        tSim = 0  # simulated time
        while i <= self.valueCount:  # start at 0
            if i == 0:  # dont refresh a and b
                x, y = self.henon()
            else:
                x, y = self.henon(
                    self.a(i, self._refDictSim), self.b(i, self._refDictSim)
                )
            for char in self.valueSelect:
                if char == "x":
                    self.basket.append(x)
                elif char == "y":
                    self.basket.append(y)
                i = i + 1
            tSim = tSim + 1  # increment for each
        self.normSeries = unit.unitNormRange(self.basket)
        self.selector = basePmtr.Selector(self.normSeries, self.control)

    def checkArgs(self):
        ok, msg = self.a.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.b.checkArgs()
        if ok != 1:
            return ok, msg
        if self.valueCount < 1:
            return 0, "incorrect valueCount; value must be greater than zero."
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg
        return 1, ""

    def repr(self, format=""):
        aStr = self.a.repr(format)
        bStr = self.b.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return "%s, %s, %s, (%s), (%s), %s, %s, (%s), (%s), %s" % (
            self.type,
            self.xInit,
            self.yInit,
            aStr,
            bStr,
            typeset.anyDataToStr(self.valueCount),
            self.valueSelect,
            minStr,
            maxStr,
            self.control,
        )

    def reset(self):
        # resuting a and b is not strictly necessary, as values are already
        # calculated
        self.a.reset()
        self.b.reset()
        # mandatory
        self.selector.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = unit.denorm(
            self.selector(), self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


class LorenzBasket(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "lorenzBasket"
        self.doc = lang.docPoLb
        # a, b, xinit, yinit, min, max, select
        self.argTypes = [
            "num",
            "num",
            "num",
            ["num", "list"],
            ["num", "list"],
            ["num", "list"],
            "int",
            "str",
            ["num", "list"],
            ["num", "list"],
            "str",
        ]
        self.argNames = [
            "xInit",
            "yInit",
            "zInit",
            "parameterObject: r value",
            "parameterObject: s value",
            "parameterObject: b value",
            "valueCount",
            "valueSelect: x,y,z,xy,xz,yx,yz,zx,zy,xyz,xzy,yxz,yzx,zxy,zyx",
            "min",
            "max",
            "selectionString",
        ]

        self.argDefaults = [1.0, 1.0, 1.0, 28, 10, 2.66666, 1000, "xyz", 0, 1, "oc"]
        self.argDemos = [
            [0.5, 1.5, 10, ("cg", "d", 1, 80, 1.5), 10, 12.4, 1000, "x", 0, 1, "oc"],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.xInit = self.args[0]
        self.yInit = self.args[1]
        self.zInit = self.args[2]
        # _load methods will raise error if found
        self.r = self._loadAutoConstant(self.args[3], "genPmtrObjs")
        self.s = self._loadAutoConstant(self.args[4], "genPmtrObjs")
        self.b = self._loadAutoConstant(self.args[5], "genPmtrObjs")
        self.valueCount = abs(self.args[6])
        self.valueSelect = self._valueSelectTriParser(self.args[7])
        self.minObj, self.maxObj = self._loadMinMax(self.args[8], self.args[9])
        self.control = self._selectorParser(self.args[10])  # raises exception

        # do processing:
        self.basket = []
        self.lorenz = chaos.Lorenz(
            self.r(0, self._refDictSim),
            self.s(0, self._refDictSim),
            self.b(0, self._refDictSim),
            self.xInit,
            self.yInit,
            self.zInit,
        )
        i = 0
        tSim = 0  # simulated time
        while i <= self.valueCount:  # start at 0
            if i == 0:  # dont refresh values
                x, y, z = self.lorenz()
            else:
                x, y, z = self.lorenz(
                    self.r(tSim, self._refDictSim),
                    self.s(tSim, self._refDictSim),
                    self.b(tSim, self._refDictSim),
                )
            for char in self.valueSelect:
                if char == "x":
                    self.basket.append(x)
                elif char == "y":
                    self.basket.append(y)
                elif char == "z":
                    self.basket.append(z)
                i = i + 1
            tSim = tSim + 1  # increment for each
        self.normSeries = unit.unitNormRange(self.basket)
        self.selector = basePmtr.Selector(self.normSeries, self.control)

    def checkArgs(self):
        ok, msg = self.r.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.s.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.b.checkArgs()
        if ok != 1:
            return ok, msg
        if self.valueCount < 1:
            return 0, "incorrect valueCount; value must be greater than zero."
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg
        return 1, ""

    def repr(self, format=""):
        rStr = self.r.repr(format)
        sStr = self.s.repr(format)
        bStr = self.b.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return "%s, %s, %s, %s, (%s), (%s), (%s), %s, %s, (%s), (%s), %s" % (
            self.type,
            self.xInit,
            self.yInit,
            self.zInit,
            rStr,
            sStr,
            bStr,
            typeset.anyDataToStr(self.valueCount),
            self.valueSelect,
            minStr,
            maxStr,
            self.control,
        )

    def reset(self):
        # resuting a and b is not strictly necessary, as values are already
        # calculated
        self.r.reset()
        self.s.reset()
        self.b.reset()
        # mandatory
        self.selector.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = unit.denorm(
            self.selector(), self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class Noise(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "noise"
        self.doc = lang.docPoN
        self.argTypes = [
            "num",
            ["str", "list", "num"],
            ["num", "list"],
            ["num", "list"],
        ]
        self.argNames = [
            "resolution",
            "parameterObject: gamma value as string or number",
            "min",
            "max",
        ]
        self.argDefaults = [100, "pink", 0, 1]
        self.argDemos = [
            [100, "black", 0, 1],
            [100, ("wt", "e", 120, 0, 1, 3), 0, 1],
            [100, ("bg", "rc", (3, 3, 3, 3, 2, 1)), 0, 1],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        ref = {
            0: ["white", "w"],
            1: ["pink", "p"],
            2: [
                "brown",
            ],
            3: [
                "black",
            ],
        }
        self.pmtrObj = self._loadAutoConstantStr(self.args[1], ref, "genPmtrObjs")
        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.resolution = abs(self.args[0])
        # print _MOD, self.resolution
        # set up the dice
        self.game = dice.GameNoise(self.resolution)

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg
        return 1, ""

    def repr(self, format=""):
        pmtrStr = self.pmtrObj.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        return "%s, %s, (%s), (%s), (%s)" % (
            self.type,
            typeset.anyDataToStr(self.resolution),
            pmtrStr,
            minStr,
            maxStr,
        )

    def reset(self):
        self.game.reset()
        self.pmtrObj.reset()
        self.minObj.reset()
        self.maxObj.reset()

    def __call__(self, t=None, refDict=None):
        self.g = self.pmtrObj(t, refDict)  # get new gamma
        self.game.step(self.g)  # take a step in the game
        self.currentValue = unit.denorm(
            self.game(),  # calling game gets sum
            self.minObj(t, refDict),
            self.maxObj(t, refDict),
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class Accumulator(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "accumulator"
        self.doc = lang.docPoA
        self.argTypes = ["num", "list"]
        self.argNames = ["initValue", "parameterObject: Generator"]
        self.argDefaults = [0, ("bg", "rc", [1, 3, 4, 7, -11])]
        self.argDemos = [
            [0, ("ws", "e", 20, 0, -0.5, 1.5)],  # wavy accumulator
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        # note: the first value will not be the init unless the pmtrObj
        # returns 0 as its first value
        self.init = copy.copy(self.args[0])
        self.value = copy.copy(self.args[0])  # init value
        self.pmtrObj = self._loadSub(self.args[1], "genPmtrObjs")

        self.initState = 1  # if this the first calls

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        pmtrStr = self.pmtrObj.repr(format)
        return "%s, %s, (%s)" % (self.type, typeset.anyDataToStr(self.init), pmtrStr)

    def reset(self):
        # call other resets
        self.pmtrObj.reset()
        self.value = copy.copy(self.init)  # reset initial value
        self.initState = 1

    def __call__(self, t=None, refDict=None):
        # first value must be init alone
        if self.initState:
            self.initState = 0  # turn off init state
            # do not update current value
        else:
            self.value = self.value + self.pmtrObj(t, refDict)
        self.currentValue = self.value
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class TypeFormat(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "typeFormat"
        self.doc = lang.docPoTf
        self.argTypes = ["str", "list"]
        self.argNames = ["typeFormatString", "parameterObject: generator"]
        self.argDefaults = ["sq", ("bg", "rc", [1, 3, 4, 7, -11])]
        self.argDemos = [("s", ("bg", "rc", [1, 3, 4, 7, -11]))]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        # may raise exception
        self.format = self._typeFormatParser(self.args[0])
        self.pmtrObj = self._loadSub(self.args[1], "genPmtrObjs")

        # update output format
        if self.format == "stringQuote":
            self.outputFmt = "str"  # declare outputFmt as string
        elif self.format == "string":
            self.outputFmt = "str"  # declare outputFmt as string
        else:
            raise AttributeError("bad typeFormat given: %s").with_traceback(self.format)

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        pmtrStr = self.pmtrObj.repr(format)
        return "%s, %s, (%s)" % (self.type, self.format, pmtrStr)

    def reset(self):
        # call other resets
        self.pmtrObj.reset()

    def __call__(self, t=None, refDict=None):
        src = self.pmtrObj(t, refDict)
        if self.format == "stringQuote":
            self.currentValue = '"%s"' % src
        elif self.format == "string":
            self.currentValue = "%s" % src
        else:
            raise AttributeError("bad typeFormat given: %s").with_traceback(self.format)

        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class Mask(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "mask"
        self.doc = lang.docPoM
        self.argTypes = ["str", "list", "list", "list"]
        self.argNames = [
            "boundaryString: limit, wrap, reflect",
            "parameterObject: first boundary",
            "parameterObject: second boundary",
            "parameterObject: generator of masked values",
        ]
        self.argDefaults = [
            "l",
            ("ws", "e", 60, 0, 0.5, 0),
            ("wc", "e", 90, 0, 0.5, 1),
            ("ru", 0, 1),
        ]
        self.argDemos = [
            [
                "w",
                ("bpl", "e", "l", ((0, 0), (90, 0.5))),
                ("bpl", "e", "l", ((0, 1), (90, 0.5))),
                ("ws", "e", 30, 0, 0, 1),
            ],
            [
                "r",
                ("ws", "e", 60, 0.25, 0.7, 1),
                ("bpl", "e", "l", ((0, 0.4), (90, 0), (120, 0.4))),
                ("ws", "e", 24, 0, 0, 1),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        # will raise exceptio on error
        self.boundaryMethod = self._boundaryParser(self.args[0])
        self.boundingPmtrObjA = self._loadSub(self.args[1], "genPmtrObjs")
        self.boundingPmtrObjB = self._loadSub(self.args[2], "genPmtrObjs")
        self.fillPmtrObj = self._loadSub(self.args[3], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.boundingPmtrObjA.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.boundingPmtrObjB.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.fillPmtrObj.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        a = self.boundingPmtrObjA.repr(format)
        b = self.boundingPmtrObjB.repr(format)
        f = self.fillPmtrObj.repr(format)
        return "%s, %s, (%s), (%s), (%s)" % (self.type, self.boundaryMethod, a, b, f)

    def reset(self):  # call other resets
        self.boundingPmtrObjA.reset()
        self.boundingPmtrObjB.reset()
        self.fillPmtrObj.reset()

    def __call__(self, t=None, refDict=None):
        a = self.boundingPmtrObjA(t, refDict)
        b = self.boundingPmtrObjB(t, refDict)
        f = self.fillPmtrObj(t, refDict)
        self.currentValue = unit.boundaryFit(a, b, f, self.boundaryMethod)
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class MaskReject(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "maskReject"
        self.doc = lang.docPoMr
        self.argTypes = ["str", "list", "list", "list"]
        self.argNames = [
            "boundaryString: limit, wrap, reflect",
            "parameterObject: first boundary",
            "parameterObject: second boundary",
            "parameterObject: generator of masked values",
        ]
        self.argDefaults = [
            "l",
            ("ws", "e", 60, 0, 0.5, 0),
            ("wc", "e", 90, 0, 0.5, 1),
            ("ru", 0, 1),
        ]
        self.argDemos = [
            [
                "w",
                ("bpl", "e", "l", ((0, 0), (90, 0.5))),
                ("bpl", "e", "l", ((0, 1), (90, 0.5))),
                ("ws", "e", 30, 0, 0, 1),
            ],
            [
                "r",
                ("ws", "e", 60, 0.25, 0.7, 1),
                ("bpl", "e", "l", ((0, 0.4), (90, 0), (120, 0.4))),
                ("ws", "e", 24, 0, 0, 1),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        # will raise exceptio on error
        self.boundaryMethod = self._boundaryParser(self.args[0])
        self.boundingPmtrObjA = self._loadSub(self.args[1], "genPmtrObjs")
        self.boundingPmtrObjB = self._loadSub(self.args[2], "genPmtrObjs")
        self.fillPmtrObj = self._loadSub(self.args[3], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.boundingPmtrObjA.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.boundingPmtrObjB.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.fillPmtrObj.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        a = self.boundingPmtrObjA.repr(format)
        b = self.boundingPmtrObjB.repr(format)
        f = self.fillPmtrObj.repr(format)
        return "%s, %s, (%s), (%s), (%s)" % (self.type, self.boundaryMethod, a, b, f)

    def reset(self):  # call other resets
        self.boundingPmtrObjA.reset()
        self.boundingPmtrObjB.reset()
        self.fillPmtrObj.reset()

    def __call__(self, t=None, refDict=None):
        a = self.boundingPmtrObjA(t, refDict)
        b = self.boundingPmtrObjB(t, refDict)
        f = self.fillPmtrObj(t, refDict)
        self.currentValue = unit.boundaryReject(a, b, f, self.boundaryMethod)
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class MaskScale(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "maskScale"
        self.doc = lang.docPoMs
        self.argTypes = ["list", "int", ["num", "list"], ["num", "list"], "str"]
        self.argNames = [
            "parameterObject: source Generator",
            "valueCount",
            "min",
            "max",
            "selectionString",
        ]
        self.argDefaults = [
            ("lp", 100, 120, "w", "oc"),
            120,
            ("bphc", "e", "l", ((0, 0), (120, -3))),
            3,
            "oc",
        ]
        self.argDemos = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.genObj = self._loadSub(self.args[0], "genPmtrObjs")
        self.valueCount = int(self.args[1])
        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        self.control = self._selectorParser(self.args[4])  # raises exception

        self.series = []
        # fill series collections
        for x in range(self.valueCount):  # use x as time/step indicator
            self.series.append(self.genObj(x, refDict))
        self.normSeries = unit.unitNormRange(self.series)
        self.selector = basePmtr.Selector(self.normSeries, self.control)

    def checkArgs(self):
        ok, msg = self.genObj.checkArgs()
        if not ok:
            return 0, msg

        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg

        if self.valueCount < 1:
            return 0, "argument error: length must be 1 or greater."

        return 1, ""

    def repr(self, format=""):
        genStr = self.genObj.repr(format)
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        msg = []
        msg.append(
            "%s, (%s), %s, (%s), (%s), %s"
            % (
                self.type,
                genStr,
                typeset.anyDataToStr(self.valueCount),
                minStr,
                maxStr,
                self.control,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        return "".join(msg)

    def reset(self):
        self.genObj.reset()
        self.minObj.reset()
        self.maxObj.reset()
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        element = self.selector()
        self.currentValue = unit.denorm(
            element, self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class FunnelBinary(basePmtr.Parameter):

    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "funnelBinary"
        self.doc = lang.docPoFb
        self.argTypes = ["str", "list", "list", "list", "list"]
        self.argNames = [
            "thresholdMatchString: upper, lower, match",
            "parameterObject: threshold",
            "parameterObject: first boundary",
            "parameterObject: second boundary",
            "parameterObject: generator of masked values",
        ]
        self.argDefaults = [
            "u",
            ("bpl", "e", "s", ((0, 0), (120, 1))),
            ("ws", "e", 60, 0, 0.5, 0),
            ("wc", "e", 90, 0, 0.5, 1),
            ("ru", 0, 1),
        ]
        self.argDemos = [
            [
                "m",
                ("c", 0.2),
                ("bpl", "e", "l", ((0, 0), (60, 0.5))),
                ("bpl", "e", "l", ((0, 1), (60, 0.5))),
                ("ws", "e", 20, 0, 0, 1),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        # will raise exceptio on error
        self.thresholdMatch = self._thresholdMatchParser(self.args[0])
        self.thresholdPmtrObj = self._loadSub(self.args[1], "genPmtrObjs")
        self.boundingPmtrObjA = self._loadSub(self.args[2], "genPmtrObjs")
        self.boundingPmtrObjB = self._loadSub(self.args[3], "genPmtrObjs")
        self.fillPmtrObj = self._loadSub(self.args[4], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.thresholdPmtrObj.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.boundingPmtrObjA.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.boundingPmtrObjB.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.fillPmtrObj.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        h = self.thresholdPmtrObj.repr(format)
        a = self.boundingPmtrObjA.repr(format)
        b = self.boundingPmtrObjB.repr(format)
        f = self.fillPmtrObj.repr(format)
        return "%s, %s, (%s), (%s), (%s), (%s)" % (
            self.type,
            self.thresholdMatch,
            h,
            a,
            b,
            f,
        )

    def reset(self):  # call other resets
        self.thresholdPmtrObj.reset()
        self.boundingPmtrObjA.reset()
        self.boundingPmtrObjB.reset()
        self.fillPmtrObj.reset()

    def __call__(self, t=None, refDict=None):
        h = self.thresholdPmtrObj(t, refDict)
        a = self.boundingPmtrObjA(t, refDict)
        b = self.boundingPmtrObjB(t, refDict)
        f = self.fillPmtrObj(t, refDict)
        self.currentValue = quantize.funnelBinary(h, a, b, f, self.thresholdMatch)
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class IterateWindow(basePmtr.Parameter):
    # iterator: selects from multiple parameter objects
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateWindow"
        self.doc = lang.docPoIw
        self.argTypes = ["list", "list", "str"]
        self.argNames = [
            "parameterObjectList: a list of Generators",
            "parameterObject: generate or skip control Generator",
            "selectionString",
        ]

        self.argDefaults = [
            (("ru", 0, 1), ("wt", "e", 30, 0, 0, 1)),
            ("bg", "oc", [8, 4, -2]),
            "oc",
        ]
        self.argDemos = [
            [
                (
                    ("ru", 1, ("a", 0, ("c", -0.2))),
                    ("ws", "e", 15, 0.25, ("a", 1, ("c", 0.4))),
                ),
                ("bg", "oc", [8, 8, -11]),
                "rc",
            ],
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
                pmtrObj = parameter.factory(argList, "genPmtrObjs")
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
            if obj.parent != "parameter":
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
                        self.valueBuffer.append(self.objArray[pos](t, refDict))
                # force the selection of a new value, examine results
                failCount = failCount + 1
                if failCount > self.FAILLIMIT and self.valueBuffer == []:
                    print(lang.WARN, self.type, "no values obtained; supplying value")
                    self.valueBuffer.append(self.objArray[pos](t, refDict))
                # leave loop if values in buffer
                if self.valueBuffer != []:
                    break
        # get value from value buffer
        self.currentValue = self.valueBuffer.pop(0)  # get first and remove
        return self.currentValue


class IterateGroup(basePmtr.Parameter):
    # iterator: groups and skip
    # group or skip values from a single parameter object
    # similar to AC Toolbox 'group'
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateGroup"
        self.doc = lang.docPoIg
        self.argTypes = ["list", "list"]
        self.argNames = [
            "parameterObject: source Generator",
            "parameterObject: group or skip control Generator",
        ]
        self.argDefaults = [("ws", "e", 30, 0, 0, 1), ("bg", "rc", (-3, 1, -1, 5))]
        self.argDemos = [
            [("wc", "e", 30, 0, 0, 1), ("wt", "e", 20, 0, 4, -1)],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.valueBuffer = []  # grouped values that must be used before expelling
        self.genObj = self._loadSub(self.args[0], "genPmtrObjs")
        self.controlObj = self._loadSub(self.args[1], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.genObj.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.controlObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        genStr = self.genObj.repr(format)
        controlStr = self.controlObj.repr(format)
        return "%s, (%s), (%s)" % (self.type, genStr, controlStr)

    def reset(self):
        self.genObj.reset()
        self.controlObj.reset()
        self.valueBuffer = []  # reset initial value

    def __call__(self, t=None, refDict=None):
        if self.valueBuffer == []:  # empty
            failCount = 0
            # note that t and refDict are constant within this loop
            while 1:
                q = self.controlObj(t, refDict)  # this should be a number
                q = drawer.floatToInt(q)
                if q < 0:  # skip values
                    for r in range(-drawer.floatToInt(q)):
                        skip = self.genObj(t, refDict)  # discard value
                elif q > 0:  # repeat values
                    group = self.genObj(t, refDict)
                    for r in range(q):  # pack same value multiple times
                        self.valueBuffer.append(group)
                # force the selection of a new value, examin results
                failCount = failCount + 1
                if failCount > self.FAILLIMIT and self.valueBuffer == []:
                    print(lang.WARN, self.type, "no values obtained; supplying value")
                    self.valueBuffer.append(self.genObj(t, refDict))
                # leave loop of values in buffer
                if self.valueBuffer != []:
                    break
        # get value from value buffer
        self.currentValue = self.valueBuffer.pop(0)  # get first and remove
        return self.currentValue


class IterateHold(basePmtr.Parameter):
    # holds values and selects; variable refresh rates
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateHold"
        self.doc = lang.docPoIh
        self.argTypes = ["list", "list", "list", "str"]
        self.argNames = [
            "parameterObject: source Generator",
            "parameterObject: size Generator",
            "parameterObject: refresh count Generator",
            "selectionString",
        ]

        self.argDefaults = [
            ("ru", 0, 1),
            ("bg", "rc", [2, 3, 4]),
            ("bg", "oc", [12, 24]),
            "oc",
        ]
        self.argDemos = [
            [
                ("ws", "e", 30, 0, 0, 1),
                ("bg", "rc", [3, 4, 5]),
                ("bg", "oc", [6, 12, 18]),
                "oo",
            ],
        ]

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.srcObj = self._loadSub(self.args[0], "genPmtrObjs")
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
            self.valueBuffer.append(self.srcObj(t, refDict))
        self.selector = basePmtr.Selector(self.valueBuffer, self.control)
        self.eventCount = 0

    def __call__(self, t=None, refDict=None):
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
        self.currentValue = self.selector()  # get first and remove
        return self.currentValue


class IterateCross(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateCross"
        self.doc = lang.docPoIc
        self.argTypes = ["list", "list", "list"]
        self.argNames = [
            "parameterObject: first source Generator",
            "parameterObject: second source Generator",
            "parameterObject: interpolation between first and second Generator",
        ]
        self.argDefaults = [
            ("ws", "e", 30, 0, 0, 1),
            ("wp", "e", 30, 0, 0, 1),
            ("bpl", "e", "l", ((0, 0), (120, 1))),
        ]
        self.argDemos = [
            [
                ("ws", "e", 30, 0, 0, 1),
                ("ru", 0, 1),
                ("bpl", "e", "l", ((0, 0), (120, 1))),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.genObjOne = self._loadSub(self.args[0], "genPmtrObjs")
        self.genObjTwo = self._loadSub(self.args[1], "genPmtrObjs")
        self.controlObj = self._loadSub(self.args[2], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.genObjOne.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.genObjTwo.checkArgs()
        if not ok:
            return 0, msg
        ok, msg = self.controlObj.checkArgs()
        if not ok:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        genStrOne = self.genObjOne.repr(format)
        genStrTwo = self.genObjTwo.repr(format)
        controlStr = self.controlObj.repr(format)
        return "%s, (%s), (%s), (%s)" % (self.type, genStrOne, genStrTwo, controlStr)

    def reset(self):
        self.genObjOne.reset()
        self.genObjTwo.reset()
        self.controlObj.reset()

    def __call__(self, t=None, refDict=None):
        q = self.controlObj(t, refDict)  # this should be a number
        q = unit.limit(q)  # limt b/n zero and 1

        a = self.genObjOne(t, refDict)
        b = self.genObjTwo(t, refDict)

        # denorm is may not be the right process here, as this takes the
        # difference of the values specified
        self.currentValue = unit.interpolate(q, a, b)
        return self.currentValue


class IterateSelect(basePmtr.Parameter):
    # fill a list, select w/ unit control
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "iterateSelect"
        self.doc = lang.docPoIs
        self.argTypes = ["list", "list", "list", "list"]
        self.argNames = [
            "parameterObject: source Generator",
            "parameterObject: size Generator",
            "parameterObject: refresh count Generator",
            "parameterObject: selection Generator",
        ]

        self.argDefaults = [
            ("ru", 0, 1),
            ("bg", "rc", [10, 11, 12]),
            ("bg", "oc", [12, 24]),
            ("rb", 0.15, 0.15, 0, 1),
        ]
        self.argDemos = [
            [("lp", 20, 20, "int", "oc"), ("c", 20), ("c", 20), ("rb", 0.2, 0.2, 0, 1)],
        ]

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.srcObj = self._loadSub(self.args[0], "genPmtrObjs")
        self.sizeObj = self._loadSub(self.args[1], "genPmtrObjs")
        self.refreshObj = self._loadSub(self.args[2], "genPmtrObjs")
        self.unitSelectObj = self._loadSub(self.args[3], "genPmtrObjs")
        self.valueBuffer = []  # collection values selected from
        self.valueBufferBoundary = []  # use unit.unitBoundaryEqual
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
        ok, msg = self.unitSelectObj.checkArgs()
        if not ok:
            return 0, msg

        return 1, ""

    def repr(self, format=""):
        srcStr = self.srcObj.repr(format)
        sizeStr = self.sizeObj.repr(format)
        refreshStr = self.refreshObj.repr(format)
        unitSelectStr = self.unitSelectObj.repr(format)
        return "%s, (%s), (%s), (%s), (%s)" % (
            self.type,
            srcStr,
            sizeStr,
            refreshStr,
            unitSelectStr,
        )

    def reset(self):
        # call other resets
        self.srcObj.reset()
        self.sizeObj.reset()
        self.refreshObj.reset()
        self.unitSelectObj.reset()
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
            self.valueBuffer.append(self.srcObj(t, refDict))
        # create boundaries w/n unit interval; equally spaced
        self.valueBufferBoundary = unit.unitBoundaryEqual(len(self.valueBuffer))
        self.eventCount = 0

    def __call__(self, t=None, refDict=None):
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
        # get value w/n unit interval, de-map from arptition
        pos = unit.unitBoundaryPos(
            unit.limit(self.unitSelectObj(t, refDict)), self.valueBufferBoundary
        )
        self.currentValue = self.valueBuffer[pos]
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class SampleAndHold(basePmtr.Parameter):
    # could add an initialization value
    # add comparison: ==, >=, >, <=, < as fourth parameter
    # determine if incoming signal is great than; ignore results after first
    # after below, reset trigger gate

    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "sampleAndHold"
        self.doc = lang.docPoSah
        self.argTypes = ["str", "list", "list", "list"]
        self.argNames = [
            "comparison",
            "parameterObject: source Generator",
            "parameterObject: trigger Generator",
            "parameterObject: trigger threshold Generator",
        ]

        self.argDefaults = ["gt", ("ru", 0, 1), ("wsd", "e", 10, 0, 0, 1), ("c", 0.5)]
        self.argDemos = [
            ["e", ("ru", 0, 1), ("wp", "e", 20, 0, 0, 1), ("c", 1)],
            ["e", ("ru", 0, 1), ("wsd", "e", 5, 0, 0, 1), ("c", 1)],
        ]

        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.valueBuffer = None  # init value
        self.thresholdGate = None  # init value

        self.control = self._comparisonParser(self.args[0])  # raises exception
        self.poSrc = self._loadSub(self.args[1], "genPmtrObjs")
        self.poTrig = self._loadSub(self.args[2], "genPmtrObjs")
        self.poThreshold = self._loadSub(self.args[3], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.poSrc.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.poTrig.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.poThreshold.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        a = self.poSrc.repr(format)
        b = self.poTrig.repr(format)
        c = self.poThreshold.repr(format)
        return "%s, %s, (%s), (%s), (%s)" % (self.type, self.control, a, b, c)

    def reset(self):
        self.valueBuffer == None  # set to None to set new value on call
        self.thresholdGate = None  # init value
        self.poSrc.reset()
        self.poTrig.reset()
        self.poThreshold.reset()

    def __call__(self, t=None, refDict=None):
        trigger = self.poTrig(t, refDict)  # call for every call
        threshold = self.poThreshold(t, refDict)  # call for every call

        # round to force a minimum resolution
        trigger = round(trigger, 10)
        threshold = round(threshold, 10)

        update = 0
        if self.valueBuffer == None:
            update = 1
        elif self.control == "equal":
            if trigger == threshold:
                update = 1
        elif self.control == "greaterThan":  # was negative
            if trigger > threshold and self.thresholdGate in [None, "-"]:
                update = 1
        elif self.control == "greaterThanOrEqual":
            if trigger >= threshold and self.thresholdGate in [None, "-"]:
                update = 1
        elif self.control == "lessThan":
            if trigger < threshold and self.thresholdGate in [None, "+"]:
                update = 1
        elif self.control == "lessThanOrEqual":
            if trigger <= threshold and self.thresholdGate in [None, "+"]:
                update = 1

        # store position of trigger in relation to threshold
        if trigger > threshold:
            self.thresholdGate = "+"  # show above threshold
        elif trigger < threshold:
            self.thresholdGate = "-"  # show above threshold

        if update:
            self.valueBuffer = self.poSrc(t, refDict)
        # convert to float for csound internal processing
        self.currentValue = float(self.valueBuffer)
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--


class Quantize(basePmtr.Parameter):
    # q,(a,0,(c,.01)),(bg,oc,[.5,1.5,2]),5,(c,1),(ru,0,3)
    # q,(c,0),(cg,lud,.5,2,.05),1,(c,1),(ru,0,3) # triangles
    # q,(c,1.5),(cg,lud,.25,1.25,.0125),1,(c,1),(ru,0,3)
    # q,(ws,e,120,0,1.25,1.75),(c,.5),1,(c,1),(ru,0,2) # sine
    # q,(ws,e,120,0,1.25,1.75),(cg,lud,.25,.75,.0025),1,(c,1),(ru,0,1)
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "quantize"
        self.doc = lang.docPoQ
        self.argTypes = ["list", "list", "int", "list", "list"]
        self.argNames = [
            "parameterObject: grid reference value Generator",
            "parameterObject: step width Generator",
            "stepCount",
            "parameterObject: unit interval measure of quantize pull",
            "parameterObject: source Generator",
        ]
        self.argDefaults = [("c", 0), ("c", 0.25), 1, ("c", 1), ("ru", 0, 1)]
        self.argDemos = [
            [
                ("c", 0),
                ("bg", "oc", [0.05, 0.2]),
                2,
                ("bpl", "e", "l", ((0, 1), (120, 0.5))),
                ("wpu", "e", 20, -2, 0, 0, 1),
            ],
            # expanding wave w/ diminishing attraction
            [
                ("ws", "e", 60, 0, 1.25, 1.75),
                ("cg", "lud", 0.3, 0.9, 0.006),
                1,
                ("bpl", "e", "l", ((0, 1), (40, 1), (120, 0.25))),
                ("ru", 0, 1),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.gridRefObj = self._loadSub(self.args[0], "genPmtrObjs")
        self.stepGenObj = self._loadSub(self.args[1], "genPmtrObjs")
        self.stepCount = self.args[2]
        self.pullObj = self._loadSub(self.args[3], "genPmtrObjs")
        self.fillPmtrObj = self._loadSub(self.args[4], "genPmtrObjs")
        self.quantObj = quantize.Quantizer(self.LOOPLIMIT)

    def checkArgs(self):
        if self.stepCount <= 0:
            return 0, "stepCount error: must be greater than zero."
        ok, msg = self.gridRefObj.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.stepGenObj.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.pullObj.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.fillPmtrObj.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        g = self.gridRefObj.repr(format)
        s = self.stepGenObj.repr(format)
        p = self.pullObj.repr(format)
        f = self.fillPmtrObj.repr(format)
        return "%s, (%s), (%s), %s, (%s), (%s)" % (
            self.type,
            g,
            s,
            typeset.anyDataToStr(self.stepCount),
            p,
            f,
        )

    def reset(self):  # call other resets
        self.gridRefObj.reset()
        self.stepGenObj.reset()
        self.pullObj.reset()
        self.fillPmtrObj.reset()

    def _buildGrid(self, t, refDict):
        # this is a grid of interval steps, not absoulte weights
        # only need a few steps; quantizer will take care of rest
        # po is used to build grid has a constant t
        grid = []
        for i in range(self.stepCount):
            # potential problem for time-based parameter objects
            # supply i instead of t, get at least steps
            q = self.stepGenObj(i, refDict)
            if q == 0:
                continue  # no use in a 0 width grid
            grid.append(abs(q))
        # accept redundant values, always take in order
        if grid == []:  # this is a problem
            print(lang.WARN, self.type, "supplying grid with default values")
            grid.append(1)  # give it something
        return grid

    def __call__(self, t=None, refDict=None):
        # grid is built for each evaluation
        self.quantObj.updateGrid(self._buildGrid(t, refDict))
        g = self.gridRefObj(t, refDict)
        f = self.fillPmtrObj(t, refDict)
        p = self.pullObj(t, refDict)
        self.currentValue = self.quantObj.attract(f, p, g)
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class MarkovValue(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "markovValue"
        self.doc = lang.docPoMv
        self.argTypes = ["str", "list"]
        self.argNames = ["transitionString", "parameterObject: order value"]
        self.argDefaults = ["a{.2}b{.5}c{.8}d{0}:{a=5|b=4|c=7|d=1}", ("c", 0)]
        self.argDemos = [
            [
                "a{0}b{.2}c{.4}d{.6}e{.8}f{1}:{a=3|b=6|c=8|d=8|e=5|f=2}a:{b=3}b:{a=2|c=4}c:{b=3|d=5}d:{a=1|c=4|e=3}e:{d=3|f=2}f:{e=2}a:b:{c=3}b:a:{b=2}b:c:{d=4}c:b:{a=2|c=1}c:d:{a=1|c=1|e=3}d:a:{b=1}d:c:{b=3|d=1}d:e:{d=1|f=2}e:d:{c=3}e:f:{e=2}f:e:{d=2}",
                ("bpl", "e", "s", ((0, 0), (119, 2))),
            ],
        ]
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
        self.orderObj = self._loadSub(self.args[1], "genPmtrObjs")
        # need to store accumulated values
        self.accum = []

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
        # assume that unitVal is produced with a uniform distribution
        unitVal = random.random()  # check random instance creation...
        order = self.orderObj(t, refDict)
        self.accum.append(self.markovObj.next(unitVal, self.accum, order))
        q = self.accum[-1]  # need to determine if this is numeric or not
        if len(self.accum) > self.MARKOVLIMIT:
            self.accum.pop(0)  # remove first in list

        qVal = drawer.strToNum(q)
        if qVal != None:  # could not convert to a number
            self.currentValue = qVal  # get last value
        else:  # assume that a string is what is desired
            self.currentValue = q
        return self.currentValue


class MarkovGeneratorAnalysis(basePmtr.Parameter):
    # mga,(bg,oc,(3,3,3,0,9,9,6)),40,2,(mv,a{1}b{0}c{2}:{a=10|b=1|c=2},(c,0))
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "markovGeneratorAnalysis"
        self.doc = lang.docPoMga

        self.argTypes = ["list", "int", "int", "list"]
        self.argNames = [
            "parameterObject: source Generator",
            "valueCount",
            "maxAnalysisOrder",
            "parameterObject: output order value",
        ]
        self.argDefaults = [
            ("ws", "e", 30, 0, 0, 1),
            30,
            2,
            ("mv", "a{1}b{0}c{2}:{a=10|b=1|c=2}", ("c", 0)),
        ]
        self.argDemos = [
            [
                ("bpp", "e", "l", ((0, 0.5), (10, 1), (15, 0)), 2),
                15,
                2,
                ("bg", "rw", (0, 1, 2, 2, 1)),
            ],
            [
                ("bg", "oc", (0.3, 0.3, 0.3, 0, 0.9, 0.9, 0.6)),
                28,
                2,
                ("mv", "a{1}b{0}c{2}:{a=10|b=1|c=2}", ("c", 0)),
            ],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.srcObj = self._loadSub(self.args[0], "genPmtrObjs")
        self.valueCount = self.args[1]
        self.maxAnalysisOrder = self.args[2]
        self.orderObj = self._loadSub(self.args[3], "genPmtrObjs")

        # need to store accumulated values
        self.analysisSeries = []
        self.accum = []
        # analysis is done on init
        self.markovObj = markov.Transition()  # creat obj w/o loading
        # this may raise an exception
        self._updateAnalysis()

    def checkArgs(self):
        if self.valueCount <= 0:
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
                typeset.anyDataToStr(self.valueCount),
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
        self._updateAnalysis()  # srcObj will be reset before this, so may be same

    def _updateAnalysis(self):
        # note: this may raise an error if po is expecting values in the refDict
        self.analysisSeries = []
        for i in range(self.valueCount):
            refDict = {}  # assume we can use an empty dictionary here
            self.analysisSeries.append(self.srcObj(i, refDict))
        # create object with source values
        self.markovObj.loadList(self.analysisSeries, self.maxAnalysisOrder)

    def __call__(self, t=None, refDict=None):
        # assume that unitVal is produced with a uniform distribution
        unitVal = random.random()  # check random instance creation...
        order = self.orderObj(t, refDict)
        # note: we may want to trim accum to save memory space
        # it need not be longer than maximum order (but we dont know what this is)
        self.accum.append(self.markovObj.next(unitVal, self.accum, order))
        if len(self.accum) > self.MARKOVLIMIT:
            self.accum.pop(0)  # remove first in list

        q = self.accum[-1]  # need to determine if this is numeric or not
        qVal = drawer.strToNum(q)
        if qVal != None:  # could not convert to a number
            self.currentValue = qVal  # get last value
        else:  # assume that a string is what is desired
            self.currentValue = q
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class GrammarTerminus(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "grammarTerminus"
        self.doc = lang.docPoGt
        self.argTypes = ["str", "int", "str"]
        self.argNames = ["grammarString", "stepCount", "selectionString"]
        self.argDefaults = ["a{.2}b{.5}c{.8}d{0}@a{ba}b{bc}c{cd}d{ac}@a", 6, "oc"]
        self.argDemos = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.grammarObj = grammar.Grammar()  # creat obj w/o loading
        try:
            self.grammarObj.load(self.args[0])
        except error.TransitionSyntaxError as e:
            raise error.ParameterObjectSyntaxError("Grammar creation failed: %s" % e)

        self.valueCount = int(self.args[1])
        self.control = self._selectorParser(self.args[2])  # raises exception

        # perform generations
        for i in range(self.valueCount):
            next(self.grammarObj)

        self.selector = basePmtr.Selector(
            self.grammarObj.getState(values=True), self.control
        )

    def checkArgs(self):
        return 1, ""

    def repr(self, format=""):
        msg = []
        msg.append(
            "%s, %s, %s, %s"
            % (self.type, str(self.grammarObj), self.valueCount, self.control)
        )
        return "".join(msg)

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        self.currentValue = self.selector()
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class FeedbackModelLibrary(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "feedbackModelLibrary"
        self.doc = lang.docPoFml
        self.argTypes = ["str", "list", "list", ["num", "list"], ["num", "list"]]

        # might add threshold value normalized w/n unit interval
        self.argNames = [
            "feedbackModelName",
            "parameterObject: aging step",
            "parameterObject: threshold",
            "min",
            "max",
        ]
        self.argDefaults = ["cc", ("bg", "rc", (1, 3)), ("c", 0.9), 0, 1]
        self.argDemos = []
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        try:
            self.feedbackType = feedback.libraryParser(self.args[0])
            self.feedbackObj = feedback.factory(self.feedbackType)
            self.feedbackObj.fillSensorProducer()
        except feedback.FeedbackError as e:
            raise error.ParameterObjectSyntaxError(
                "Feedback object creation failed: %s" % e
            )

        self.ageObj = self._loadSub(self.args[1], "genPmtrObjs")
        self.thresholdObj = self._loadSub(self.args[2], "genPmtrObjs")

        self.minObj, self.maxObj = self._loadMinMax(self.args[3], self.args[4])

    def checkArgs(self):
        ok, msg = self.ageObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.thresholdObj.checkArgs()
        if ok != 1:
            return ok, msg

        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg

        return 1, ""

    def repr(self, format=""):
        ageStr = self.ageObj.repr(format)
        thresholdStr = self.thresholdObj.repr(format)

        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)

        msg = []
        msg.append(
            "%s, %s, (%s), (%s), (%s), (%s)"
            % (self.type, self.feedbackType, ageStr, thresholdStr, minStr, maxStr)
        )
        return "".join(msg)

    def reset(self):
        self.minObj.reset()
        self.maxObj.reset()
        self.ageObj.reset()
        self.thresholdObj.reset()

    def __call__(self, t=None, refDict=None):
        # advance based on an age
        self.feedbackObj.advance(self.ageObj(t, refDict))
        self.currentValue = unit.denorm(
            self.feedbackObj.getValue(),
            self.minObj(t, refDict),
            self.maxObj(t, refDict),
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class FibonacciSeries(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "fibonacciSeries"
        self.doc = lang.docPoFs
        self.argTypes = ["num", "num", ["num", "list"], ["num", "list"], "str"]
        self.argNames = ["start", "length", "min", "max", "selectionString"]
        self.argDefaults = [200, 20, 0, 1, "oc"]
        self.argDemos = [
            [40, 20, 0, 1, "rc"],
            [400, 20, ("ws", "e", 35, 0, 0.5, 0), ("cg", "ud", 0.6, 1, 0.025), "oo"],
        ]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.start = int(self.args[0])
        self.length = int(self.args[1])
        self.minObj, self.maxObj = self._loadMinMax(self.args[2], self.args[3])
        # do setup processing
        self.series = chaos.fibonacciSeries(self.start, (self.start + abs(self.length)))
        self.normSeries = unit.unitNormRange(self.series)

        self.control = self._selectorParser(self.args[4])  # raises exception
        self.selector = basePmtr.Selector(self.normSeries, self.control)

        if self.length < 0:  # a negative length reverses the series
            self.normSeries.reverse()
            self.length = abs(self.length)

    def checkArgs(self):
        ok, msg = self.minObj.checkArgs()
        if ok != 1:
            return ok, msg
        ok, msg = self.maxObj.checkArgs()
        if ok != 1:
            return ok, msg

        if self.start < 1:
            return 0, "argument error: start value must be 1 or greater."
        if self.length < 1:
            return 0, "argument error: length must be 1 or greater."
        return 1, ""

    def repr(self, format=""):
        minStr = self.minObj.repr(format)
        maxStr = self.maxObj.repr(format)
        msg = []
        msg.append(
            "%s, %s, %s, (%s), (%s), %s"
            % (
                self.type,
                typeset.anyDataToStr(self.start),
                typeset.anyDataToStr(self.length),
                minStr,
                maxStr,
                self.control,
            )
        )
        if format == "argsOnly":
            return "".join(msg)
        # show sieve if not argsOnly
        msg.append("\n")
        msg.append(
            self.LMARGIN
            + "%s" % self._scrubList(self.normSeries, self.minObj(0), self.maxObj(0))
        )
        return "".join(msg)

    def reset(self):
        self.minObj.reset()
        self.maxObj.reset()
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        element = self.selector()
        self.currentValue = unit.denorm(
            element, self.minObj(t, refDict), self.maxObj(t, refDict)
        )
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class _Operator(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = None
        self.argTypes = ["list", "list"]
        self.argNames = [
            "parameterObject: first value",
            "parameterObject: second value",
        ]
        self.argDefaults = [("ws", "e", 30, 0, 0, 1), ("a", 0.5, ("c", 0.025))]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.pmtrObjA = self._loadSub(self.args[0], "genPmtrObjs")
        self.pmtrObjB = self._loadSub(self.args[1], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.pmtrObjA.checkArgs()
        if ok == 0:
            return 0, msg
        ok, msg = self.pmtrObjB.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        pmtrStrA = self.pmtrObjA.repr(format)
        pmtrStrB = self.pmtrObjB.repr(format)
        return "%s, (%s), (%s)" % (self.type, pmtrStrA, pmtrStrB)

    def reset(self):
        self.pmtrObjA.reset()
        self.pmtrObjB.reset()

    def __call__(self, t=None, refDict=None):
        None  # define in subclcass


# subclass of sampleSelect: just change name
class OperatorAdd(_Operator):
    def __init__(self, args, refDict):
        _Operator.__init__(self, args, refDict)  # call base init
        self.type = "operatorAdd"
        self.doc = lang.docPoOa

    def __call__(self, t=None, refDict=None):
        a = self.pmtrObjA(t, refDict)
        b = self.pmtrObjB(t, refDict)
        self.currentValue = a + b
        return self.currentValue


class OperatorSubtract(_Operator):
    def __init__(self, args, refDict):
        _Operator.__init__(self, args, refDict)  # call base init
        self.type = "operatorSubtract"
        self.doc = lang.docPoOs

    def __call__(self, t=None, refDict=None):
        a = self.pmtrObjA(t, refDict)
        b = self.pmtrObjB(t, refDict)
        self.currentValue = a - b
        return self.currentValue


class OperatorDivide(_Operator):
    def __init__(self, args, refDict):
        _Operator.__init__(self, args, refDict)  # call base init
        self.type = "operatorDivide"
        self.doc = lang.docPoOd

    def __call__(self, t=None, refDict=None):
        a = self.pmtrObjA(t, refDict)
        b = self.pmtrObjB(t, refDict)
        try:
            self.currentValue = a / float(b)
        except ZeroDivisionError:
            self.currentValue = a
        return self.currentValue


class OperatorMultiply(_Operator):
    def __init__(self, args, refDict):
        _Operator.__init__(self, args, refDict)  # call base init
        self.type = "operatorMultiply"
        self.doc = lang.docPoOm

    def __call__(self, t=None, refDict=None):
        a = self.pmtrObjA(t, refDict)
        b = self.pmtrObjB(t, refDict)
        self.currentValue = a * b
        return self.currentValue


class OperatorPower(_Operator):
    def __init__(self, args, refDict):
        _Operator.__init__(self, args, refDict)  # call base init
        self.type = "operatorPower"
        self.doc = lang.docPoOp

    def __call__(self, t=None, refDict=None):
        a = self.pmtrObjA(t, refDict)
        b = self.pmtrObjB(t, refDict)
        self.currentValue = pow(a, b)
        return self.currentValue


class OperatorCongruence(_Operator):
    def __init__(self, args, refDict):
        _Operator.__init__(self, args, refDict)  # call base init
        self.type = "operatorCongruence"
        self.doc = lang.docPoOc

    def __call__(self, t=None, refDict=None):
        a = self.pmtrObjA(t, refDict)
        b = self.pmtrObjB(t, refDict)
        try:
            self.currentValue = a % b  # permit floats or ints
        except ZeroDivisionError:
            self.currentValue = a
        return self.currentValue


# -----------------------------------------------------------------||||||||||||--
class OneOver(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict)  # call base init
        self.type = "oneOver"
        self.doc = lang.docPoOo

        self.argTypes = ["list"]
        self.argNames = ["parameterObject: value"]
        self.argDefaults = [("ws", "e", 30, 0, 0.5, 2)]
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0:
            raise error.ParameterObjectSyntaxError(msg)  # report error

        self.pmtrObj = self._loadSub(self.args[0], "genPmtrObjs")

    def checkArgs(self):
        ok, msg = self.pmtrObj.checkArgs()
        if ok == 0:
            return 0, msg
        return 1, ""

    def repr(self, format=""):
        pmtrStr = self.pmtrObj.repr(format)
        return "%s, (%s)" % (self.type, pmtrStr)

    def reset(self):
        self.pmtrObj.reset()

    def __call__(self, t=None, refDict=None):
        x = self.pmtrObj(t, refDict)
        try:
            self.currentValue = 1.0 / x  # permit floats or ints
        except ZeroDivisionError:
            self.currentValue = 1
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
