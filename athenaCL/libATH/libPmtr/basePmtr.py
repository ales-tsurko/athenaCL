# -----------------------------------------------------------------||||||||||||--
# Name:          parent.py
# Purpose:       base class of all general and rhythm parameter objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import random, copy
import unittest, doctest

from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import unit
from athenaCL.libATH import error
from athenaCL.libATH import language
from athenaCL.libATH import table
from athenaCL.libATH import argTools

lang = language.LangObj()

_MOD = "basePmtr.py"

# -----------------------------------------------------------------||||||||||||--
# constants string suffix used for naming multiple parameters
AUXQ = "auxQ"
TEXTQ = "textQ"
DYNQ = "dynQ"
CLONEQ = "cloneQ"
# common parameters
tCOMMONQ = (
    "inst",
    "tRange",
    "beatT",
    "rhythmQ",
    "fieldQ",
    "octQ",
    "ampQ",
    "panQ",
    "path",
)
# textures have sustain and accent fields tt textures do not
cCOMMONQ = (
    "time",
    "sus",
    "acc",
    "fieldQ",
    "octQ",
    "ampQ",
    "panQ",
)

REFDICT_SIM = {"bpm": 120, "fpAudioDirs": []}


def _getLabels(no, prefix, index):
    """
    >>> _getLabels(1, 'ampQ', 0)
    ['ampQ0']
    """
    labels = []
    for i in range(0, no):
        if index:  # store two data attributes
            labels.append((i, "%s%s" % (prefix, str(i))))
        else:
            labels.append("%s%s" % (prefix, str(i)))
    return labels


def auxLabel(auxNo, index=0):
    """
    >>> auxLabel(3,0)
    ['auxQ0', 'auxQ1', 'auxQ2']
    """
    return _getLabels(auxNo, AUXQ, index)


def textLabel(textNo, index=0):
    """
    >>> textLabel(3,0)
    ['textQ0', 'textQ1', 'textQ2']
    """
    return _getLabels(textNo, TEXTQ, index)


def cloneLabel(textNo, index=0):
    """
    >>> cloneLabel(3, 0)
    ['cloneQ0', 'cloneQ1', 'cloneQ2']
    """
    return _getLabels(textNo, CLONEQ, index)


def dynLabel(dynNo, index=0):
    """
    >>> dynLabel(3)
    ['dynQ0', 'dynQ1', 'dynQ2']
    """
    return _getLabels(dynNo, DYNQ, index)


# -----------------------------------------------------------------||||||||||||--
class Selector(object):
    """object to handle selecting things from a list
    basic selectors that do not require additional parameters
    can be initialized w/ and empty source, but will raise an index
    error if __call__ is used w/ empty list

    >>> a = Selector([3,4,5], 'randomWalk')
    """

    # selection methods to add:
    # randomFirst ? (favor first, exponential)
    # randomLast ? (favor last, exponential)
    # randomEdges ? (favor edges)
    # randomCenter ? (favor center, gausian distribution)

    def __init__(self, src, control):
        self.src = src
        # control value is not parsed; must be complete string!
        self.control = control
        self.ref = []
        self.status = 0  # check if values are available, updated w/ set list
        self._setList()  # copy rawList to list
        self._resetIndex()

        self.scratch = []  # will be populated if needed
        # this is a list of indexes to move through in order
        self._direction = []  # used in oscillate
        self._updateDirectionIndex()

    def _setList(self):
        self.ref = []
        for i in range(len(self.src)):  # index for custom obj
            entry = self.src[i]
            if hasattr(entry, "copy"):  # copy object tt have copy attribute
                self.ref.append(entry.copy())
            else:
                self.ref.append(copy.deepcopy(entry))
        if len(self.ref) == 0:
            self.status = 0
        else:
            self.status = 1

    def getStatus(self):
        "used to check if values are set or not"
        return self.status

    def _setListScratch(self):
        self.scratch = []
        for i in range(len(self.src)):  # index for custom obj
            entry = self.src[i]
            if hasattr(entry, "copy"):
                self.scratch.append(entry.copy())
            else:
                self.scratch.append(copy.deepcopy(entry))

    def _updateDirectionIndex(self):
        if len(self.ref) == 0:
            self._direction = []
        elif len(self.ref) == 1:
            self._direction = [0]
        elif len(self.ref) == 2:
            self._direction = [0, 1]
        else:
            self._direction = list(range(0, len(self.ref)))  # 0,1,2
            post = list(range(1, (len(self.ref) - 1)))  # 1,
            post.reverse()  # second half of range
            self._direction = self._direction + post

    def _resetIndex(self):
        if self.control == "orderedCyclicRetrograde":
            self._i = len(self.ref) - 1
        else:
            self._i = 0  # current position

    def reset(self):
        self.scratch = []  # will be populated if needed
        self._resetIndex()

    def update(self, src):
        "update the list; if it is a different size, reset index"
        oldSize = len(self.ref)  # store old size
        self.src = src
        self._setList()  # this will clear and set self.ref
        if len(self.ref) != oldSize:
            self.scratch = []
            self._i = 0
            self._updateDirectionIndex()

    def _randomChoice(self):
        "randomly select an item"
        return random.choice(self.ref)

    def _randomWalk(self):
        "one-dimension random walk, with wrapping"
        if len(self.ref) == 1:
            return self.ref[0]
        if random.choice([0, 1]):
            self._i = self._i + 1
        else:
            self._i = self._i - 1
        selectIndex = self._i % len(self.ref)  # use mod for wrapping
        return self.ref[selectIndex]

    def _randomPermutate(self):
        """non redundant selection at random; refils when empty"""
        if len(self.ref) == 1:
            return self.ref[0]
        if len(self.scratch) == 0:
            self._setListScratch()
        select = random.choice(self.scratch)
        del self.scratch[self.scratch.index(select)]
        self._i = self._i + 1
        return select

    def _orderedCyclic(self):
        """move through list of items in order"""
        if len(self.ref) == 1:
            return self.ref[0]
        if self._i == len(self.ref):
            self._i = 0
        select = self.ref[self._i]
        self._i += 1
        return select

    def _orderedCyclicRetrograde(self):
        """move through list of items in reverse order"""
        if len(self.ref) == 1:
            return self.ref[0]
        if self._i < 0:
            self._i = len(self.ref) - 1  # max index
        select = self.ref[self._i]
        self._i -= 1
        return select

    def _orderedOscillate(self):
        """move through list of items by reading the direction list
        direction list has index values to move through
        self._i referes to direction index, not list indices"""
        if len(self.ref) == 1:
            return self.ref[0]
        if self._i == len(self._direction):
            self._i = 0
        select = self.ref[self._direction[self._i]]
        self._i = self._i + 1
        return select

    def __call__(self):
        """
        >>> a = Selector([3,4,5], 'orderedCyclic')
        >>> a()
        3
        >>> a()
        4

        >>> b = Selector([3,4,5], 'randomPermutate')
        >>> post = [b() for x in range(3)]
        >>> post.sort()
        >>> post = [3,4,5]

        >>> c = Selector([3,4,5], 'randomChoice')
        >>> d = Selector([3,4,5], 'randomWalk')
        >>> e = Selector([3,4,5], 'orderedOscillate')

        >>> f = Selector([3,4,5], 'orderedCyclicRetrograde')
        >>> f(), f(), f(), f()
        (5, 4, 3, 5)
        """
        # emergency check
        if len(self.ref) == 0:
            raise IndexError("selector has no values")
        if self.control == "randomChoice":
            return self._randomChoice()
        elif self.control == "randomWalk":
            return self._randomWalk()
        elif self.control == "randomPermutate":
            return self._randomPermutate()
        elif self.control == "orderedCyclic":
            return self._orderedCyclic()
        elif self.control == "orderedCyclicRetrograde":
            return self._orderedCyclicRetrograde()
        elif self.control == "orderedOscillate":
            return self._orderedOscillate()
        else:
            raise ValueError("no control for %s" % self.control)


# -----------------------------------------------------------------||||||||||||--
class Parameter(object):
    """base class for all pmtr objects

    parameter objects are very broady construed; can be any of a number of things
    some parameter objects are 'generators': current times does not make a dif
        orderedCyclic
    some parameter objects are 'functions': current time makes a difference
        waves, bpf

    some attributes are checked for adding, as in some cases it seems
    the base class sets up attributes before calling the parent class init
    """

    def __init__(self, args, refDict=None):
        """
        >>> a = Parameter([])
        """
        self.args = args
        self.currentValue = None
        # retain source of parent class to deferntiate b/n rhythm pmtrs
        self.parent = "parameter"
        # priority determines which pmtr objects can overide others
        self.priority = 0  # zero is nuetral, 9 is max
        # parameters must declare output
        # can be a list of multiple types if necessary
        self.outputFmt = "num"  # declare outputFmt as num by default
        # determine if this parameer is hidden from user creation
        self.hidden = 0

        if not hasattr(self, "refDict"):
            self.refDict = refDict  # dif b/n kept and shown args
        else:  # update dictionary w/ new values
            self.refDict.update(refDict)
        # generator/rhythm parameter objects include name as an argument
        if not hasattr(self, "argCountOffset"):
            self.argCountOffset = 1  # dif b/n kept and shown args
        # self.argTypes = [] # list of types, (can be list of possibilities)
        if not hasattr(self, "argDefaults"):
            self.argDefaults = []  # optional a list of defaults that will be used

        self.argDemos = []  # optional list of lists of demo args
        # data needed by many parameter objects
        self.LMARGIN = " " * lang.LMARGINW  # for spaceing extra info
        # common numerical limits
        self.FAILLIMIT = 99  # number of values tested before supplying
        self.LOOPLIMIT = 999  # number of values tested before supplying
        self.MARKOVLIMIT = 9  # limit order of markov analysis
        # store commonly used argument names and their extra documentation
        # may need to gather lists of options from other modules
        _optListTable = list(table.tableMonoFormatRef.keys())
        _optListTable.sort()

        # note: some of these values should be obtained from the parsers
        # defined below
        self._argNameRef = {
            "selectionString": [
                "randomChoice",
                "randomWalk",
                "randomPermutate",
                "orderedCyclic",
                "orderedCyclicRetrograde",
                "orderedOscillate",
            ],
            "articulationString": ["attack", "sustain"],
            "anchorString": ["lower", "upper", "average", "median"],
            "directionString": ["upDown", "downUp", "up", "down"],
            "onOff": ["on", "off"],
            "typeFormatString": ["string", "stringQuote"],
            "stepString": ["event", "time"],
            "edgeString": ["loop", "single"],  # used for breakPoints
            "scaleString": ["absolute", "proportional"],  # used for envelopes
            "pulseList": ["a list of Pulse notations"],
            "pulse": ["a single Pulse notation"],
            "tableExtractionString": _optListTable,
        }
        # store a dummy ref dict for cases of non-time based pre-bundling
        # of sub parameter objects
        self._refDictSim = REFDICT_SIM

    def checkArgs(self):
        """used to check high-level argument issues that do not happen during
        initialization. these may include issues of value range, or matching
        a string within an appropriate group"""
        pass

    def repr(self, format=""):
        pass

    def __str__(self):
        return self.repr()

    def _reprDemo(self):
        # manually extractin acronym like this may produce
        # acronyms that are different than those defined in parameter.py?
        msg = ["%s" % drawer.acronymExtract(self.type)]
        # goes through each arg in the list of args
        for arg in self.argDefaults:
            raw = typeset.anyDataToStr(arg)
            # strip any extra quotes provided
            raw = raw.replace("'", "")  # will be a single quote
            msg.append(raw)
        return ", ".join(msg)

    def _reprArgs(self, format="min"):
        """pack argument into numbered form with argument options in braces"""
        msg = []
        count = 1
        if format == "min":
            msg.append(self.type)
        else:
            msg.append("(%s) name" % count)
        # add additional args
        if format == "min":
            for argStr in self.argNames:
                if ":" in argStr:  # can pack extra info in there with this
                    argStr, argChoice = argStr.split(":")
                    argStr = argStr.strip()
                msg.append(argStr)
        else:
            for argStr in self.argNames:
                if ":" in argStr:  # can pack extra info in there with this
                    argStr, argChoice = argStr.split(":")
                    argChoice = argChoice.split(",")
                else:
                    argChoice = None  # room for extra documentation
                argSub = []
                count = count + 1
                argSub.append("(%s) %s" % (count, argStr))
                # see if more info is avail for this arg name
                if argStr in list(self._argNameRef.keys()):
                    argChoice = self._argNameRef[argStr]
                if argChoice != None:
                    docSub = []
                    if len(argChoice) == 1:  # its a doc string
                        docSub.append(argChoice[0].strip())
                    else:
                        for arg in argChoice:
                            arg = arg.strip()
                            if arg == "":
                                continue
                            docSub.append("'%s'" % arg)
                    argSub.append(" {%s}" % ", ".join(docSub))

                msg.append("".join(argSub))
        return ", ".join(msg)

    def reprDoc(self, format=""):
        msg = []
        if format in ["full", ""]:
            msg.append(self._reprArgs("min"))
            msg.append("\n")
            msg.append(
                typeset.descriptionAsStr(
                    self.doc, "\n", self._reprArgs("max"), self._reprDemo()
                )
            )
        elif format == "paragraph":
            msg.append(typeset.descriptionAsStr(self.doc, " ", self._reprArgs("max")))
        elif format == "args":
            msg.append(self._reprArgs("min"))
        elif format == "argsMax":
            msg.append(self._reprArgs("max"))
        elif format == "list":  # return a list for column presentation
            msg.append(("Description", self.doc))
            msg.append(("Arguments", self._reprArgs("max")))
            return msg  # do not join
        else:  # should not happen
            raise ValueError
        return "".join(msg)

    def __call__(self, t=None, refDict=None):
        pass

    def reset(self):
        """reset any counters or order managers; always called before scoring"""
        pass

    def postEvent(self, eventDict, refDict):
        """do post event processing on other parameter values
        this allows a pmtr obj to modify other event values
        refDict allows the paramter to look at the current event values
        gathered form TMclass
        """
        return eventDict

    # -----------------------------------------------------------------------||--
    # utility methods
    def _checkRawArgs(self):
        """checks raw arg type and number
        number of args always excludes the first string, the name of the pmtr
        will supply defaults if missing args after a point, and self.argDefaults
            defined
        """
        self.args, ok, msg = argTools.strongType(
            self.args, self.argTypes, self.argDefaults, self.argCountOffset
        )
        # provide arg count offset as 1
        return ok, msg

    # -----------------------------------------------------------------------||--
    def _loadSub(self, arg, lib, idStr=""):
        from athenaCL.libATH.libPmtr import parameter

        try:
            obj = parameter.factory(arg, lib)
        except error.ParameterObjectSyntaxError as msg:
            if idStr == "":
                raise error.ParameterObjectSyntaxError("failed sub-parameter: %s" % msg)
            else:
                raise error.ParameterObjectSyntaxError(
                    "failed %s sub-parameter: %s" % (idStr, msg)
                )
        return obj

    def _loadAutoConstant(self, arg, lib="genPmtrObjs"):
        """take args and if a number, returns as a constant value parameterObj
        otherwise, keep as is

        >>> a = Parameter([])
        >>> post = a._loadAutoConstant(45)
        >>> post.type
        'constant'
        >>> post = a._loadAutoConstant(['ru', 0, 1])
        >>> post.type
        'randomUniform'
        """
        if drawer.isNum(arg):
            pmtrArgs = ("c", arg)  # fit within a constant
        else:  # its a list to create a ParameterObject
            pmtrArgs = arg
        # create a ParameterObject
        from athenaCL.libATH.libPmtr import parameter

        try:
            obj = parameter.factory(pmtrArgs, lib)
        except error.ParameterObjectSyntaxError as msg:
            raise error.ParameterObjectSyntaxError("failed sub-parameter: %s" % msg)
        return obj

    def _loadAutoConstantStr(self, arg, ref, lib="genPmtrObjs"):
        """accept a number, a list parameter object, or a string from
        within a dfeind string group"""
        #         ref = {'0' : ['tn', 't', 't n' '0'],
        #                 }
        if drawer.isNum(arg):
            pmtrArgs = ("c", arg)
        elif drawer.isStr(arg):
            post = drawer.selectionParse(arg, ref, 0)  # autosearch off
            if post == None:
                raise error.ParameterObjectSyntaxError("no such preset name known.")
            pmtrArgs = ("c", post)  # a constant pmtr obj
        else:  # its a list to create a ParameterObject
            pmtrArgs = arg
        # create a ParameterObject
        from athenaCL.libATH.libPmtr import parameter

        try:
            obj = parameter.factory(pmtrArgs, lib)
        except error.ParameterObjectSyntaxError as msg:
            raise error.ParameterObjectSyntaxError("failed sub-parameter: %s" % msg)
        return obj

    def _loadMinMax(self, min, max):
        """
        >>> a = Parameter([])
        >>> post = a._loadMinMax(45, 34)
        >>> post[0].type, post[1].type
        ('constant', 'constant')
        >>> post = a._loadMinMax(45, ['ru', 0, 1])
        >>> post[0].type, post[1].type
        ('constant', 'randomUniform')
        >>> post = a._loadMinMax(['ru', 0, 1], ['ru', 0, 1])
        >>> post[0].type, post[1].type
        ('randomUniform', 'randomUniform')
        """

        if drawer.isNum(min):
            minArgs = ("c", min)
        elif drawer.isList(min):
            minArgs = min
        # check max
        if drawer.isNum(max):
            maxArgs = ("c", max)
        elif drawer.isList(max):
            maxArgs = max
        # create a parameter object
        from athenaCL.libATH.libPmtr import parameter

        try:
            minObj = parameter.factory(minArgs)
        except error.ParameterObjectSyntaxError as msg:
            raise error.ParameterObjectSyntaxError("failed sub-parameter: %s" % msg)
        try:
            maxObj = parameter.factory(maxArgs)
        except error.ParameterObjectSyntaxError as msg:
            raise error.ParameterObjectSyntaxError("failed sub-parameter: %s" % msg)
        return minObj, maxObj

    # -----------------------------------------------------------------------||--
    def _scrubList(self, data, min=None, max=None):
        """for presenting list data
        used to apply scalar to uncalculated values"""
        msg = []
        for element in data:
            if min != None and max != None:
                element = unit.denorm(element, min, max)
            msg.append(typeset.anyDataToStr(element))
        dataStr = ",".join(msg)
        return "(%s)" % dataStr

    # -----------------------------------------------------------------------||--
    # string conversion
    # only place those tt are share by multiple po here
    # most of these should be converted to raise exceptions on error

    def _directionParser(self, usrStr):
        """decode direction strings; this used to have values preceded
        by 'linear; keep for backwards compat

        >>> a = Parameter([])
        >>> a._directionParser('ud')
        'upDown'
        """
        ref = {
            "upDown": ["ud", "lud", "linearupdown", "0"],
            "downUp": ["du", "ldu", "lineardownup", "1"],
            "up": ["u", "lu", "linearup", "2"],
            "down": ["d", "ld", "lineardown", "3"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad direction name: enter %s." % selStr
            )
        return usrStr

    def _selectorParser(self, usrStr):
        """decode control choice strings; exception on error

        >>> a = Parameter([])
        >>> a._selectorParser('rp')
        'randomPermutate'
        """
        ref = {
            "randomChoice": ["rc", "0"],
            "randomWalk": ["rw"],
            "randomPermutate": ["rp"],
            "orderedCyclic": ["oc", "1"],
            "orderedCyclicRetrograde": [
                "ocr",
            ],
            "orderedOscillate": ["oo"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad selectionString: enter %s." % selStr
            )
        return usrStr

    def _loopControlParser(self, usrStr):
        """determine if a value referes to loop (1) or single (0)

        >>> a = Parameter([])
        >>> a._loopControlParser(0)
        'single'
        """
        ref = {
            "loop": ["l", "1"],
            "single": ["s", "0"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "loop control is either %s." % selStr
            )
        return usrStr  # may be None

    def _stepControlParser(self, usrStr):
        """determine if a value refers to step (event) control (1) or
        real-time control (0)

        >>> a = Parameter([])
        >>> a._stepControlParser('e')
        'event'
        """
        ref = {
            "event": ["e", "1"],
            "time": ["t", "0"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad step control. enter %s." % selStr
            )
        return usrStr  # may be None

    def _selectLevelFrameParser(self, usrStr):
        """
        >>> a = Parameter([])
        >>> a._selectLevelFrameParser('f')
        'frame'
        """
        ref = {
            "event": ["e", "1"],
            "frame": ["f", "0"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad frame level control. enter %s." % selStr
            )
        return usrStr  # may be None

    def _boundaryParser(self, usrStr):
        """decode control choice strings

        >>> a = Parameter([])
        >>> a._boundaryParser('w')
        'wrap'
        """
        ref = {
            "limit": ["l"],
            "wrap": ["w"],
            "reflect": ["r"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad boundary method. enter %s." % selStr
            )
        return usrStr  # may be None

    def _onOffParser(self, usrStr):
        """decode control choice strings

        >>> a = Parameter([])
        >>> a._onOffParser(1)
        'on'
        """
        ref = {
            "on": ["1"],
            "off": ["0"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _anchorParser(self, usrStr):
        """
        >>> a = Parameter([])
        >>> a._anchorParser('a')
        'average'
        """
        ref = {
            "lower": ["l"],
            "upper": ["u"],
            "average": ["a"],
            "median": ["m"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _scaleSwitchParser(self, usrStr):
        """determine if a value refers to absolute or proportional values

        >>> a = Parameter([])
        >>> a._scaleSwitchParser('p')
        'proportional'
        """
        ref = {
            "absolute": ["a", "1"],
            "proportional": ["p", "0"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad step control. enter %s." % selStr
            )
        return usrStr  # may be None

    def _thresholdMatchParser(self, usrStr):
        """
        >>> a = Parameter([])
        >>> a._thresholdMatchParser('u')
        'upper'
        """
        ref = {
            "lower": ["l"],
            "upper": ["u"],
            "match": ["m"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _valueSelectBiParser(self, usrStr):
        """xy selection
        >>> a = Parameter([])
        >>> a._valueSelectBiParser('xy')
        'xy'
        """
        ref = {  # automatically uses keys as case insensitive values
            "x": [],
            "y": [],
            "xy": [],
            "yx": [],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _valueSelectTriParser(self, usrStr):
        "xyz selection"
        ref = {  # automatically uses keys as case insensitive values
            "x": [],
            "y": [],
            "z": [],
            "xy": [],
            "xz": [],
            "yx": [],
            "yz": [],
            "zx": [],
            "zy": [],
            "xyz": [],
            "xzy": [],
            "yxz": [],
            "yzx": [],
            "zxy": [],
            "zyx": [],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _articulationParser(self, usrStr):
        """decode control choice strings

        >>> a = Parameter([])
        >>> a._articulationParser('a')
        'attack'
        """
        ref = {
            "attack": ["a"],
            "sustain": ["s"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _typeFormatParser(self, usrStr):
        "decode control choice strings"
        ref = {
            "stringQuote": [
                "sq",
            ],
            "string": ["str", "s"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _sieveFormatParser(self, usrStr):
        "decode control choice strings"
        ref = {
            "integer": ["i", "int"],
            "width": ["w", "wid"],
            "binary": ["b", "bin"],
            "unit": ["u", "uni"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _comparisonParser(self, usrStr):
        """decode control choice strings

        >>> a = Parameter([])
        >>> a._comparisonParser('lt')
        'lessThan'
        """
        ref = {
            "equal": ["e", "="],
            "greaterThan": ["gt", "g", "greater", ">"],
            "greaterThanOrEqual": ["gtoe", ">="],
            "lessThan": ["lt", "l", "less", "<"],
            "lessThanOrEqual": ["ltoe", "<="],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _selectLevelMonophonicParser(self, usrStr):
        "decode control choice strings"
        ref = {
            "event": ["e"],
            "set": ["s"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _selectLevelPolyphonicParser(self, usrStr):
        """decode control choice strings

        >>> a = Parameter([])
        >>> a._selectLevelPolyphonicParser('e')
        'event'
        """
        ref = {
            "event": ["e"],
            "set": ["s"],
            "voice": ["v"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    # filter po converters needed here for backwards compat
    def _selectRetrogradeParser(self, usrStr):
        "decode control choice strings"
        ref = {
            "off": ["off", "0"],
            "timeInverse": ["ti", "tinvers"],
            "eventInverse": ["ei", "retro"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr

    def _selectTimeRefParser(self, usrStr):
        """decode control choice strings

        >>> a = Parameter([])
        >>> a._selectTimeRefParser('tt')
        'textureTime'
        """
        ref = {
            "textureTime": ["tt"],
            "cloneTime": ["ct"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr == None:
            selStr = drawer.selectionParseKeyLabel(ref)
            raise error.ParameterObjectSyntaxError(
                "bad control value: enter %s." % selStr
            )
        return usrStr


# -----------------------------------------------------------------||||||||||||--
# rhythm objects
class RhythmParameter(Parameter):
    """parent class of all rhythm objects; defines util methods
    all rhythm objects store a triple for currentValue
    """

    def __init__(self, args, refDict):
        """
        >>> a = RhythmParameter([], {})
        """
        Parameter.__init__(self, args, refDict)  # call base init
        self.argCountOffset = 1  # dif b/n kept and shown args
        self.parent = "rhythm"  # mark as a special type
        self.currentPulse = None  # init value, used in getCurrentRhythm
        self.outputFmt = "list"  # declare outputFmt as a list of data
        self.bpm = None  # set in subclasses at evaluation time


# no longer needed, as can just acces the .currentPulse attribute directly
#     def getCurrentPulseObj(self):
#         return self.currentPulse


# -----------------------------------------------------------------||||||||||||--
# internal static texture parameters
class StaticParameterTexture(Parameter):
    """texture parameters are simple dictionaries of static values
    values can be switches or other static control information, perferences
    arguments are named and accessed by name"""

    def __init__(self, args, refDict):
        """
        >>> a = StaticParameterTexture([], {})
        """
        # note: look for first arg as type and remove
        if not drawer.isList(args):  # single tuple not evaluated as list
            args = [
                args,
            ]  # add to list
        if args != []:  # if not empty
            if args[0] == self.type:
                args = args[1:]
        Parameter.__init__(self, args, refDict)  # call base init
        self.argCountOffset = 0  # dif b/n kept and shown args
        self.parent = "textureStatic"  # mark as a special type
        self.outputFmt = None  # output values from dictionary
        self._switches = {}  # dictionary that stores switch valuess

    def _updateSwitches(self):
        self._switches = {}  # dictionary that stores switches
        i = 0
        for name in self.argNames:
            # first arg will be name of parameter object
            # but this will be removed when loading
            if ":" in name:
                name, doc = name.split(":")
                name = name.strip()
            self._switches[name] = self.args[i]
            i = i + 1

    def switch(self, name):
        # have to remove extra documentation from name
        if ":" in name:
            name, doc = name.split(":")
            name = name.strip()
        return self._switches[name]

    def repr(self, format=""):
        # why not use baesParameter representation methods here?
        msg = []
        for name in self.argNames:
            if drawer.isList(self.switch(name)):
                msg.append("%s" % self._scrubList(self.switch(name)))
            else:
                msg.append("%s" % typeset.anyDataToStr(self.switch(name)))
        if format in ["argsOnly", ""]:
            msg = [
                self.type,
            ] + msg
            return ", ".join(msg)
        elif format in ["noType"]:
            return ", ".join(msg)

    def getArgs(self):
        """get complete arg list used to build this object"""
        args = []
        for name in self.argNames:
            args.append(self.switch(name))
        # prepend name of arg
        args = [
            self.type,
        ] + args
        return tuple(args)  # tuple is just by convention

    def getArgsLabel(self):
        """returns a string of the pmtr name and arg value names"""
        msg = []
        msg.append(self.type)  # add name string
        msg = msg + self.argNames  # add arg names
        return drawer.listScrub(msg, None, "rmQuote")

    def __call__(self, name):
        """simply treturn the data
        can access as numbered steps in arg list, starting at 0"""
        if drawer.isInt(name):  # if number, make into string name
            name = self.argNames[name]
        return self.switch(name)


# -----------------------------------------------------------------||||||||||||--
# internal statuc clone parameters
class StaticParameterClone(StaticParameterTexture):
    """just like texture static parameter objects, except for clonse"""

    def __init__(self, args, refDict):
        """
        >>> a = StaticParameterClone([], {})
        """
        StaticParameterTexture.__init__(self, args, refDict)  # call base init
        self.parent = "cloneStatic"  # mark as a special type


# -----------------------------------------------------------------||||||||||||--
# internal static texture parameters
class FilterParameter(Parameter):
    """filter parameters operate like filters
    filter parameters operate on an array of values from the eventSequence
    they cannot be run in real-time, as they require all values present
    cloneFilter's also have an input fmt to determine compatibility
    w/ various aux pmtrs that may use strings

    both general purpose and rhythm parameter objects can
    be used (rhythm parameter objects on use the dur value to change
    offsets, while sustain is a separate parameter for clonse)
    """

    def __init__(self, args, refDict):
        """
        >>> a = FilterParameter([], {})
        """
        Parameter.__init__(self, args, refDict)  # call base init
        self.parent = "cloneFilter"  # mark as a special type
        self.outputFmt = None  # output values from dictionary
        self.inputFmt = ("num", "str")  # declare input as num by default
        self.argCountOffset = 1  # dif b/n kept and shown args

    def __call__(self, valueArray, tArray=None, refDictArray=None):
        """refDict here is created in clone score method by taking data
        from the esObj, simulating compatibility w/ general pmtr objects
        """
        pass


# -----------------------------------------------------------------||||||||||||--
# provide utility functions from Parameter class
# only used in ioTools for backwards compat with pickled data structs


def selectorParser(str):
    """
    >>> selectorParser('rw')
    'randomWalk'
    """
    obj = Parameter(None)
    return obj._selectorParser(str)


def directionParser(str):
    """
    >>> directionParser('u')
    'up'
    """
    obj = Parameter(None)
    return obj._directionParser(str)


# used for backwards compat of old clones
def retrogradeParser(str):
    """
    >>> retrogradeParser('o')
    'off'
    """
    obj = Parameter(None)
    try:
        return obj._selectRetrogradeParser(str)
    except error.ParameterObjectSyntaxError:
        return "off"


# -----------------------------------------------------------------||||||||||||--
# test just selector here

# def TestOld():
#     colTest = [[3,2,54], ['test'], ['234', 56, 'dfg', 3], [100,200], range(0,20)]
#     for col in colTest:
#         for control in ['randomChoice', 'randomWalk', 'randomPermutate',
#                              'orderedCyclic', 'orderedOscillate']:
#             print _MOD, 'selector test:', control, col
#             a = Selector(col, control)
#             print [a() for x in range(10)]
#             newCol = random.choice(colTest)
#             a.update(newCol)
#             print _MOD, 'selector test: post update', control, newCol
#             print [a() for x in range(10)]
#             a.reset()
#             print [a() for x in range(10)]
#             print


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
