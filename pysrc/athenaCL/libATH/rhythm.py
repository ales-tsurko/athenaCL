# -----------------------------------------------------------------||||||||||||--
# Name:          rhythm.py
# Purpose:       rhyhtm and time based conversions.
#                    defines Pulse class, for a single duration / accent
#                    defines Rhythm class, as series of Pulses
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

# this module should not import any lower level athenacl modules
import copy, time
import unittest, doctest

from athenaCL.libATH import drawer
from athenaCL.libATH import error

_MOD = "rhythm.py"
# -----------------------------------------------------------------||||||||||||--

REFdurStr = {
    "w": (1, 4),  # whole
    "h": (1, 2),
    "q": (1, 1),  # if bpm referes to quarter
    "e": (2, 1),
    "s": (4, 1),  # sixteenth
    "t": (8, 1),  # thirtysecond
    # triplets
    "tw": (3, 8),  # triplet whole
    "th": (3, 4),
    "tq": (3, 2),  # if bpm referes to quarter
    "te": (3, 1),
    "ts": (6, 1),
    "tt": (12, 1),
    # dotted durations
    "dw": (1, 6),  # dotted whole
    "dh": (1, 3),
    "dq": (2, 3),  # if bpm referes to quarter
    "de": (4, 3),
    "ds": (8, 3),
    "dt": (16, 3),
}

# make this a range, min, max
REFdynStr = {  # gives lower boundary value, 8 equal divisions
    "+": (1, 1),
    "fff": (0.95, 1),  # >= x <
    "ff": (0.9, 0.95),  # < max, not <=
    "f": (0.8, 0.9),
    "mf": (0.6, 0.8),
    "mp": (0.4, 0.6),  # .5 is median
    "p": (0.3, 0.4),
    "pp": (0.15, 0.3),
    "ppp": (0.0001, 0.15),  # min sig digits is 4, see below
    "o": (0, 0),
}


# replace with function from below
def dynStrToAcc(sym):
    """convert dynStr to accent value; ints will be ints, otherwise floats"""
    if sym not in list(REFdynStr.keys()):
        raise ValueError
    # return median of min/max
    if REFdynStr[sym][0] == REFdynStr[sym][1]:
        return REFdynStr[sym][0]  # min or max, 0, 1 values are the same
    else:  # get median value between min and max
        return (REFdynStr[sym][0] + REFdynStr[sym][1]) * 0.5


def accToDynStr(num):
    if num >= 0.9999:
        return "+"
    elif num < 0.0001:
        return "o"
    # no integers beyond this
    num = round(num, 4)  # four sig digits
    for sym in list(REFdynStr.keys()):
        if num >= REFdynStr[sym][0] and num < REFdynStr[sym][1]:
            return sym
    raise ValueError  # should not happen


# humdrum duration notation here
# http://www.music-cog.ohio-state.edu/Humdrum/representations/kern.rep.html


def beatTimeToBpm(timePerBeat):
    """return value in bpm

    >>> beatTimeToBpm(30)
    2.0
    """
    return 60.0 * (1.00 / timePerBeat)


def bpmToBeatTime(bpmValue):
    """return value in seconds

    >>> bpmToBeatTime(120)
    0.5
    """
    return 60.0 / float(bpmValue)


# -----------------------------------------------------------------||||||||||||--


class Pulse:
    """define a fundamental duration / accent / sustain unit
    holds duration and sustain info
    duration is time till next note, or rhythm
    sustain is the time of sounding, which may be > or < than duration
    main data stored in self.triple
    """

    def __init__(self, srcData, type=None):
        """src data can be a tuple/list duple or triple
        if one data elemetn given:
        or can be a duration string like 'q' or otherwise
        can also be an int or float, becoming a single pulse and being dynamic
        if two data elements, assumes div/mod
        three is complete tuple

        >>> a = Pulse('3,1')
        >>> a
        (3,1,+)
        """
        # valid forms as strings and attributes
        self.forms = ("dur", "triple", "acc", "sus")  # 'str' fromat not complete
        self.srcData = srcData  # store original data entered

        if type == None:  # defaults used
            type = self._guessType()
            if type == None:  # this is an error
                raise error.PulseSyntaxError
            else:
                self.format = type
        else:  # type given
            self.format = type
        # data is a triple of div, mult, acc
        self.triple = self._processFormat()  # stores native triple format
        if self.triple == None:  # returns None on error
            raise error.PulseSyntaxError
        self.triple = list(self.triple)  # not sure why this is necssary
        # additional parameters that effect output
        self.bpm = 120.0  # default value, called w/ seconds
        self.sustain = 1.0  # percent b/n 0 and 1 of pulse that 'sounds'

    def _guessType(self):
        """try to determine what kind of duration/dynamic data is given
        can be string or integer tuple/list: (2,1,1) or (3,1)
        can be string char like q, e, t, s, th?
        can be string acc list .5 1 .3 1
        """
        data = copy.copy(self.srcData)
        if drawer.isStr(data):
            data = data.strip()  # temp data
            data = data.lower()
            if len(data) == 0:
                return None  # no data found
            if data[0].islower():  # if has chars
                if data in list(REFdurStr.keys()):
                    return "str"
                elif data in list(REFdynStr.keys()):  # maybe its a dynmaic
                    return "acc"  # acc string value alone
                else:
                    raise error.PulseSyntaxError
            elif data[0] == "[" or data[0] == "(":  # its a list or tuple
                return "triple"
            elif data.find(",") >= 0:  # if there are commas in string
                return "triple"
            else:  # assume its an acc string
                return "acc"
        if drawer.isNum(data):  # acc list
            return "acc"
        if drawer.isList(data):
            return "triple"

    def _processFormat(self):
        """process raw data into a rhythm triples
        stored as a rhythm triple in self.triple
        return None on error
        """
        data = copy.copy(self.srcData)
        if self.format == "str":
            if drawer.isStr(data) and data in list(REFdurStr.keys()):
                data = data.strip()
                data = data.lower()
                return self._expandRawTriple(REFdurStr[data])  # return None on error
            else:
                return None
        elif self.format == "triple":
            if drawer.isStr(data):
                data = self._scrubDynStr(data)  # may raise error.PulseSyntaxError
                try:
                    data = list(eval(data))  # convert to list
                except (ValueError, SyntaxError):
                    return None
                return self._expandRawTriple(data)  # return None on error
            else:  # its a real tuple/list
                return self._expandRawTriple(data)  # return None on error
        elif self.format == "acc":  # a list of amps
            if drawer.isStr(data):
                if data in list(REFdynStr.keys()):  # its a string
                    data = self._dynStrToVal(data)  # convert to number
                else:  # its a string number like '3'
                    try:
                        data = eval(data)  # an int/float
                    except (ValueError, SyntaxError):
                        return None
                return self._expandRawTriple(data)  # return None on error
            else:  # its a real int/float
                return self._expandRawTriple(data)  # return None on error
        else:  # error
            return None

    def _normAcc(self, acc):
        """normalize acc values between 0 and 1"""
        if acc > 1:
            acc = 1
        elif acc < 0:
            acc = 0
        return acc

    def _normDivMult(self, div, mult):
        div = abs(div)  # no nagatives
        mult = abs(mult)  # no nagatives
        if div == 0:
            raise error.PulseSyntaxError
        elif mult == 0:
            raise error.PulseSyntaxError
        return div, mult

    def _expandRawTriple(self, data):
        """take an int, 2, or three element tuple and provide defaults
        returns None if nothing expandable
        if third element in list exists and is a string will be converted
        does checks on div and mult, divide by zero error and all raise exception
        """
        defD = 1  # default values
        defM = 1
        defA = 1
        if drawer.isNum(data):  # assum its an acc
            return (defD, defM, self._normAcc(data))
        elif drawer.isStr(data):  # assum its an acc as string
            return (defD, defM, self._normAcc(self._dynStrToVal(data)))
        elif drawer.isList(data):
            data = list(data)  # convert to list for assignment
            if len(data) == 0:
                return None
            elif len(data) == 1:  # its an acc
                return (defD, defM, self._normAcc(data))
            elif len(data) == 2:
                try:
                    data[0], data[1] = self._normDivMult(data[0], data[1])
                except error.PulseSyntaxError:
                    return None  # error
                return (data[0], data[1], defA)
            else:  # other info in a list will be removed
                try:
                    data[0], data[1] = self._normDivMult(data[0], data[1])
                except error.PulseSyntaxError:
                    return None  # error
                if drawer.isStr(data[2]):
                    acc = self._dynStrToVal(data[2])
                else:  # its a number
                    acc = data[2]
                return (data[0], data[1], self._normAcc(acc))
        else:
            return None  # error

    def _scrubDynStr(self, usrStr):
        """scrub a usrStr (pulse triple, or single value)
        for dynamic markings and replace them with str(float) vals
        this reads a single string and returns a str rep of int or float
        """
        usrStr = usrStr.lower()
        # provide keys to match other possible symbols (just need + really)
        chars = drawer.strExtractAlpha(usrStr, list(REFdynStr.keys()))
        if chars not in usrStr:  # chars are not all contiguous, bad arg
            raise error.PulseSyntaxError
        elif chars == "":  # no chars at all, just numbers, return
            return usrStr

        # now convert a string symbol w/n larger string
        # chagne dyn symbols to floats
        # need to always have longest strings firts
        # to avoid f, vs fff confusions
        sortItems = []
        for sym in list(REFdynStr.keys()):  # will retain class, int or float
            sortItems.append((len(sym), sym, dynStrToAcc(sym)))
        sortItems.sort()
        sortItems.reverse()  # largest lengths first

        match = None
        for l, sym, val in sortItems:
            if chars.find(sym) >= 0:
                count = chars.count(sym)
                if count > 1:
                    continue  # not a match
                elif count == 1:
                    match = sym, val  # single match
                else:
                    continue  # try again
            if match != None:
                break
        # check for partial matches, like pppppppp or mmf
        if match == None:
            for l, sym, val in sortItems:
                if chars.find(sym) >= 0:  # will start w/ longest first, closest
                    count = chars.count(sym)
                    if count > 1:
                        match = sym, val  # accept non-single match
                    else:
                        continue  # try again
                if match != None:
                    break
        if match != None:
            usrStr = usrStr.replace(chars, str(match[1]))  # match stores val, num
        return usrStr

    def _dynStrToVal(self, usrStr):
        """get string representation of accent value, then convert to either
        an int or a float"""
        acc = self._scrubDynStr(usrStr)
        if acc == "1" or acc == "0":  # makle an int
            return int(acc)
        else:
            return float(acc)

    def _reprTripleData(self, listData, outer=1):
        msgList = []
        i = 0
        for data in listData:
            if i == 2:  # last element, acc
                msgList.append(accToDynStr(data))  # get str for data
            else:
                msgList.append(str(data))
            i = i + 1
        msg = ",".join(msgList)  # should be a list of strings
        if outer:
            return "(%s)" % msg
        else:
            return msg

    def repr(self, type=None, bpm=None):
        """get string representations"""
        if type == None:
            type = "triple"  # default
        if type == "dur":  # time in seconds
            dur, sus, acc = self._calculate(bpm)
            return "%.2fs" % dur
        elif type == "sus":  # time in seconds
            dur, sus, acc = self._calculate(bpm)
            return "%.2fs" % sus
        elif type in ("triple", "str"):
            return self._reprTripleData(self.triple)
        elif type == "acc":
            return "%s" % self.triple[2]

    def __str__(self):
        return self.repr()

    def __repr__(self):
        return self.repr()

    def _calculate(self, bpm=None, sustain=None):
        """calculate duration in seconds
        sustain is some fraction of the duration, between 0 and > 1
        if sustain is less than 1, the note is staccato
        if sustain is > than one, the note is legato (sustains past next note)
        dur is the time of the real rhythm, i.e., time till next note
        sus is the time of sounding
        """
        if bpm != None:
            self.bpm = bpm
        if sustain != None:  # set if given
            self.sustain = sustain
        dur = (bpmToBeatTime(self.bpm) / (float(self.triple[0]))) * self.triple[1]
        sus = dur * self.sustain  # dur times ratio +/- 1
        acc = self.triple[2]
        return dur, sus, acc

    def _access(self, format):
        """get data structures by format"""
        if format == "dur":  # seconds
            dur, sus, acc = self._calculate()
            return dur
        if format == "sus":  # seconds
            dur, sus, acc = self._calculate()
            return sus
        elif format == "triple":  # default data ref
            return self.triple
        # elif format == 'str': # get str val
        #    return None # not yet implemented
        elif format == "acc":  # get acc val
            return self.triple[2]

    def get(self, format="triple"):
        if format not in self.forms:
            raise ValueError("bad format requested: %s" % format)
        return self._access(format)

    def __eq__(self, other):
        if self.triple == other.triple and self.format == self.format:
            return 1
        else:
            return 0

    def __len__(self):
        return 3  # always 3

    def __call__(self, bpm=None, sustain=None):
        "returns dur, sus, acc triple"
        return self._calculate(bpm, sustain)  # sets attributes

    def setSus(self, sustain):
        """set the sustain scalar value
        should it check if value is >= zero?"""
        self.sustain = sustain

    def setBpm(self, bpm):
        """set the sustain multiplier value"""
        self.bpm = bpm

    def setAcc(self, acc):
        """set the acc multiplier value"""
        self.triple[2] = self._normAcc(acc)

    def copy(self):
        """return a new object that is a copy of this one"""
        triple = copy.deepcopy(self.triple)
        pulseObj = Pulse(triple, "triple")
        pulseObj.setSus(self.sustain)
        pulseObj.setBpm(self.bpm)
        return pulseObj

    def scale(self, value):
        """scale the multiplier by an integer
        this can be used to increase or decrease duration;
        divisor is not altered
        """
        if not drawer.isInt(value):
            raise ValueError("value must be an integer")
        self.triple[1] = self.triple[1] * value

    # -----------------------------------------------------------------------||--
    def ratioRaise(self, value):
        """increasing divider and multipler; opposite of reducing
        raising ot a higher terms
        duratin remains the same"""
        if not drawer.isInt(value):
            raise ValueError("value must be an integer")
        self.triple[0] = self.triple[0] * value
        self.triple[1] = self.triple[1] * value

    def ratioTarget(self, div):
        """given a goal divisor, provide appropriate multiples to
        div and mult
        must be sure that value is alreaduy a proper multiple"""
        if not drawer.isInt(div):
            raise ValueError("value must be an integer")
        if float(div) / self.triple[0] != float(div) // self.triple[0]:
            raise ValueError(
                "target divisor does not divide evenly into pulse triple divisor"
            )
        # divide goal divisor by current divisor to get necessary mutltiple
        m = div // self.triple[0]
        self.ratioRaise(m)

    def fracture(self, numerator, denominator):
        """denominatoride a pulse into two pulses that sum to the same dur
        provide a fraction that is returned as first half of a pulse triple
        if 4, 5 is provided, denominatorided into 4/5 adn 1/5, return 4/5 first"""

        if not drawer.isInt(numerator):
            raise ValueError("numerator must be an integer")
        if not drawer.isInt(denominator):
            raise ValueError("denominator must be an integer")
        if numerator > denominator:
            raise ValueError("fraction must be less than 1")

        a = self.copy()
        b = self.copy()

        # scale denominatorisor by uniform amount
        dSource = self.triple[0]
        a.triple[0] = dSource * denominator
        b.triple[0] = dSource * denominator

        mSource = self.triple[1]
        a.triple[1] = mSource * numerator
        b.triple[1] = mSource * (denominator - numerator)

        return a, b

    def cut(self, multiplier):
        """given a value for a multipler, return to pulses
        where the multipliers sum to the current multiplier"""

        if not drawer.isInt(multiplier):
            raise ValueError("multiplier must be an integer")
        if multiplier > self.triple[1]:
            raise ValueError("new multiplier must be less than current")

        a = self.copy()
        b = self.copy()

        mSource = self.triple[1]
        a.triple[1] = multiplier
        b.triple[1] = mSource - multiplier

        return a, b


# -----------------------------------------------------------------||||||||||||--

# info on openmusic rhythm trees
# http://www.ircam.fr/equipes/repmus/OpenMusic/Documentation/OMUserDocumentation/DocFiles/Reference/Rhythmtrees/Index.html


# -----------------------------------------------------------------||||||||||||--


class Rhythm:
    """class of a rhythm, stores multiple pulses
    will accept data list or list of strings as srcData
    normal list data processed as pulse list
    if single tuple is string or float, will processed as acc driven pulse list
    """

    def __init__(self, srcData):
        """srcList can be a list of pulseObjects
        or list of rhythm tuples, or a string to be evaluated into pulses"""
        self.srcData = srcData  # store original data
        self.forms = ("dur", "sus", "triple", "acc")
        # may raise error.PulseSyntaxError
        self.pulseList = self._loadPulse()

    def _tripleMonadTest(self, srcData):
        """determine if a rhythm is a single rhythm triple, or rather
        a pulse list
        (1,1,1) will be interpreterd as pulse list
        (1,)
        (3,1) will be rhythm triple
        (1,2) will be rhythm triple
        """
        if len(srcData) == 2 or len(srcData) == 3:
            d = srcData[0]
            m = srcData[1]
            if drawer.isNum(d):
                if d >= 2 or m >= 2:  # one value needs to be greater than 1
                    if d != 0 and m != 0:  # neither can be zerp
                        return 1  # rhythm triple
        return 0  # it is a pulse list

    def _loadPulse(self):
        objList = []
        if drawer.isStr(self.srcData):
            # if whole argument is a string; not yet implemented
            # this is not going to work, cannot devide a compelete string w/ ,
            strList = self.srcData.split(",")  # split
            for element in strList:
                obj = Pulse(element)  # will raise exception on load error
                objList.append(obj)
        elif drawer.isNum(self.srcData):
            obj = Pulse(self.srcData)  # will raise exception on load error
            objList.append(obj)
        elif drawer.isList(self.srcData):
            if self._tripleMonadTest(self.srcData):  #    a single triple
                obj = Pulse(self.srcData)
                objList.append(obj)
            else:  # get individual chunks; a pulse list
                for element in self.srcData:
                    obj = Pulse(element)  # will raise exception on load error
                    objList.append(obj)
        else:
            raise error.PulseSyntaxError
        return objList

    # -----------------------------------------------------------------------||--
    # presentation
    def _reprListData(self, listData, outer=1):
        msgList = []
        for data in listData:
            if not drawer.isStr(data):
                msgList.append(str(data))
            else:
                msgList.append(data)
        msg = ",".join(msgList)  # should be a list of strings
        if outer:
            return "(%s)" % msg
        else:
            return msg

    def repr(self, type="triple", bpm=None, outer=1):
        if type in ("dur", "sus", "triple", "acc"):  # native to set
            msgList = []
            for pulse in self.pulseList:
                msgList.append(pulse.repr(type, bpm))
            return self._reprListData(msgList, outer)

    def __str__(self):
        return self.repr()  # default

    def __repr__(self):
        return self.repr()

    # data access and manipulation
    # -----------------------------------------------------------------------||--
    def setSus(self, sustain):
        "set sustain for all pulse objects with the same value"
        for pulse in self.pulseList:
            pulse.setSus(sustain)

    def setAcc(self, acc):
        "set acc for all pulse objects with the same value"
        for pulse in self.pulseList:
            pulse.setAcc(acc)

    def setBpm(self, bpm):
        "set bpm for all pulse objects with the same value"
        for pulse in self.pulseList:
            pulse.setBpm(bpm)

    # -----------------------------------------------------------------------||--
    def copy(self):
        obj = Rhythm(copy.deepcopy(self.srcData))
        # copy pulse list manually to ensure identity
        pulseList = []
        for i in range(len(self.pulseList)):
            pulseList.append(self.pulseList[i].copy())
        obj.pulseList = pulseList
        return obj

    # -----------------------------------------------------------------------||--
    def ratioRaise(self, value):
        "set sustain for all pulse objects with the same value"
        for pulse in self.pulseList:
            pulse.ratioRaise(value)

    def ratioTarget(self, div):
        "set sustain for all pulse objects with the same value"
        for pulse in self.pulseList:
            pulse.ratioTarget(div)

    # -----------------------------------------------------------------------||--
    def __len__(self):
        return len(self.pulseList)

    def _access(self, type):
        if type in ("dur", "sus", "triple", "acc"):  # native to set
            dataList = []
            for pulse in self.pulseList:
                dataList.append(pulse.get(type))
            return dataList

    #     def __getattr__(self, name):
    #         """phase out use of this method for get() below"""
    #         if name not in self.forms:
    #             raise AttributeError
    #         return self._access(name)

    def get(self, name):
        if name not in self.forms:
            raise ValueError("bad format requested: %s" % name)
        return self._access(name)

    def __contains__(self, item):
        if item in self.pulseList:
            return 1
        else:
            return 0

    def __getitem__(self, key):
        return self.pulseList[key]

    def __delitem__(self, key):
        del self.pulseList[key]

    def __setitem__(self, key, value):
        self.pulseList[key] = value

    #     def __call__(self, index=None, bpm=None, sustain=None):
    #         pass

    def __coerce__(self):
        return None  # not possible


# -----------------------------------------------------------------||||||||||||--


class RhythmMeasure:
    """given a list of rhythm durations, divide into blocks based
    on a measure unit
    ignore bpm values for all pulses

    """

    # >>> from athenaCL.libATH import rhythm
    # >>> a = rhythm.RhythmMeasure([(1,1),(1,5),(2,5),(1,3),(4,1),(1,7)])
    # >>> a.setMeasureForm([(1,4)])
    # >>> a.partition()

    def __init__(self, srcRhythm, srcEvent=[None]):

        self.srcEventData = srcEvent  # a list of lists; meta data for each rhythm
        self.dstEventData = None  # process w/ normalize method

        self.srcRhythm = Rhythm(srcRhythm)
        self.dstRhythm = None
        self.srcMeasureForm = []  # store measure form as a rhythm
        self.dstMeasureForm = None
        self.baseDivisor = None  # common divisor shared by all pulses after norm

    def setMeasureForm(self, form):
        """measure is a list of durations (as rhythms) that will be used
        to partition rhythms"""
        self.srcMeasureForm = Rhythm(form)

    def _normalizeEventData(self):
        """make sure that self.evenData has the same number of
        entities as srcRhythm; use None if necessary"""
        if len(self.srcRhythm) == len(self.srcEventData):
            self.dstEventData = self.srcEventData
        elif len(self.srcRhythm) < len(self.srcEventData):
            self.dstEventData = self.srcEventData[: len(self.srcRhythm)]
        # if src data is elss,
        elif len(self.srcRhythm) > len(self.srcEventData):
            self.dstEventData = []
            for i in range(len(self.srcRhythm)):
                self.dstEventData.append(self.srcEventData[i % len(self.srcEventData)])

    def _normalizeRatio(self):
        """
        finds a common multiple for both the measure and all rhythms
        shifts all values of all rhythms
        does not have to be least common multiple; just a common multiple
        after found, can raise all pulses by this value"""
        unique = []
        for p in self.srcRhythm:
            if p.triple[0] not in unique:
                unique.append(p.triple[0])  # store
        for p in self.srcMeasureForm:
            if p.triple[0] not in unique:
                unique.append(p.triple[0])
        # get product simply by multiple; this is not a lcm
        self.baseDivisor = 1
        for val in unique:
            self.baseDivisor = self.baseDivisor * val

        self.dstRhythm = self.srcRhythm.copy()
        self.dstRhythm.ratioTarget(self.baseDivisor)
        self.dstMeasureForm = self.srcMeasureForm.copy()
        self.dstMeasureForm.ratioTarget(self.baseDivisor)

    def _diagnostic(self, post):
        print()
        print(_MOD, "measure partition diagnostic")
        print("dst rhtyhm:", self.dstRhythm)
        sumTotal = 0
        mCount = 1
        for measure in post:
            print("measure %s" % mCount)
            print(measure)
            sum = 0
            for pulse, tie in measure:
                sum = sum + pulse.triple[1]
            sumTotal = sumTotal + sum
            print("sum", sum)
            mCount = mCount + 1
        print()
        print("sum measure", sumTotal)

        sumDst = 0
        for pulse in self.dstRhythm:
            sumDst = sumDst + pulse.triple[1]
        print("sum dst rhythm", sumDst)

    def partition(self):
        """take dstRhythm and dstMeasure and partition into measures
        return pairs of Pulse objects and tie status
        tie status is None, 1 (start), 0 (end), or 2 (continue)"""
        self._normalizeRatio()
        self._normalizeEventData()

        post = []  # create a list of lists of pulse objects, tie status
        postData = []  # a list of lists of src data, matched and repeated as tied

        mCount = 0  # count of measures
        pPos = 0  # pulse position
        mSum = 0  # measure sum
        pRemainder = None  # pulse left over after cut

        # print _MOD, 'base divisor', self.baseDivisor

        while 1:
            # take modulus to cycle through measure forms
            pMeasure = self.dstMeasureForm[mCount % len(self.srcMeasureForm)]
            target = pMeasure.triple[1]  # get multiplier
            # print _MOD, 'measure target', target
            measure = []
            measureData = []

            mSum = 0  # reset measure sum
            while 1:  # ending this loop means measure is full
                if pRemainder != None:  # there is a remainder to partition
                    pActive = pRemainder
                else:
                    pActive = self.dstRhythm[pPos]
                dur = pActive.triple[1]
                acc = pActive.triple[2]
                eActive = self.dstEventData[pPos]

                # mSum should always be less than the target before adding dur
                if mSum >= target:
                    raise ValueError("mSum has exceeded target before check")
                # find out how much space is left
                mEmpty = target - mSum
                # this sum is conditional; it may exceed measure after this point
                mSum = mSum + dur
                if mSum == target:
                    if pRemainder != None:
                        tie = 0  # close open tie
                    else:
                        tie = None  # no tie
                    if acc == 0:
                        tie = None  # case of a rest: no tie
                    measure.append([pActive.copy(), tie])
                    measureData.append(eActive)
                    pPos = pPos + 1
                    pRemainder = None  # clear any remainder
                    break
                elif mSum < target:  # this dur still fits within this measure
                    if pRemainder != None:
                        tie = 0  # close open tie
                    else:
                        tie = None  # no tie
                    if acc == 0:
                        tie = None  # case of a rest: no tie
                    measure.append([pActive.copy(), tie])  # no tie
                    measureData.append(eActive)
                    pPos = pPos + 1
                    pRemainder = None  # clear any remainder
                    # dont break
                elif mSum > target:
                    # if pActive is a remainder, it will be cut again
                    if pRemainder != None:
                        tie = 2  # continue open tie
                    else:
                        tie = 1  # open a new tie
                    if acc == 0:
                        tie = None  # case of a rest: no tie
                    pCut, pRemainder = pActive.cut(mEmpty)  # returns two pulse objs
                    measure.append([pCut, tie])  # tie to next
                    measureData.append(eActive)
                    # dont increument pPos
                    break
                # always check if pPos has expanded beyond all rhythms
                # in some cases last measure may not be complete
                if pPos >= len(self.dstRhythm):
                    break

            post.append(measure)
            postData.append(measureData)

            # print _MOD, post
            if pPos >= len(self.dstRhythm):
                break

            mCount = mCount + 1  # increment measure count
            # print _MOD, 'measure count', mCount
            if mCount > 9999999:
                break  # safety

        # self._diagnostic(post)

        return post, postData

    def aggregate(self, rhythmData, eventData, newBar=4):
        """given data partitioned under one organization, combine a specified number of measures into new measures
        this permits doing segmentation at the beat level, and then re-organizing at the bar level
        """

        # >>> from athenaCL.libATH import rhythm
        # >>> a = rhythm.RhythmMeasure([(4,5),(4,1),(4,7),(4,3),(4,1)])
        # >>> a.setMeasureForm([(1,1)])
        # >>> a.partition()

        assert len(rhythmData) == len(eventData)
        rhythmDataBar = []
        eventDataBar = []
        offset = 0
        newCount = 0

        barRhythm = []
        barEvent = []
        for i in range(len(rhythmData)):  # move through each existing bar
            barRhythm = barRhythm + rhythmData[i]
            barEvent = barEvent + eventData[i]
            # that many bars have been added, or last available bar
            if i % newBar == newBar - 1 or i == len(rhythmData) - 1:
                rhythmDataBar.append(barRhythm[:])
                eventDataBar.append(barEvent[:])
                barRhythm = []
                barEvent = []
        return rhythmDataBar, eventDataBar


# -----------------------------------------------------------------||||||||||||--
class TimeValue:
    """object to read and write time values"""

    sPerMin = 60
    sPerHour = sPerMin * 60
    mPerHour = 60
    hPerDay = 24
    sPerDay = sPerHour * hPerDay
    mPerDay = mPerHour * hPerDay
    sPerWeek = sPerDay * 7
    sPerYear = sPerDay * 365

    def __init__(self, data):
        # ds is decimal seconds, or values less than 1, as a decimal
        # ds is not converted to ms or any other unit
        self.time = {"f": 0, "s": 0, "m": 0, "h": 0, "d": 0}
        self.sec = 0
        self.srcData = data
        self.timeLabels = ["d", "h", "m", "s", "f"]  # must be in order

        if drawer.isStr(data):
            self._humanToSec(data)  # load to self.time
        elif drawer.isNum(data):  # assume seconds
            self.time["s"] = data  # keep floating point values
        else:
            raise ValueError("unsupported data type")
        self._updateTime()  # update and shifts all values

    def _humanStrPrep(self, usrStr):
        """determine which format the string is in"""
        usrStr = usrStr.lower()
        usrStr = usrStr.strip()
        for label in self.timeLabels:
            if usrStr.find(label) >= 0:  # found
                # if labels are found, assume the dominant, remove colons
                usrStr = usrStr.replace(":", "")  # remove colons
                return usrStr, "label"
        # assume its a colon separated list
        # remove labels if found
        return usrStr, "colon"

    def _humanToSec(self, usrStr):
        """allow 2 types of time notation:
        2:2:02 where hour, min, seconds are given
        2h 2m 2s with labels, spaces not required
        return value in seconds"""
        usrStr, format = self._humanStrPrep(usrStr)
        # order matters for colon separated lists
        if format == "colon":  # using colon notation
            usrList = usrStr.split(":")
            usrLen = len(usrList)
            if usrLen == 1:  # assume seconds given
                self.time["s"] = float(usrList[0])
            elif usrLen == 2:  # assume m:s
                self.time["s"] = float(usrList[1])
                self.time["m"] = int(usrList[0])
            elif usrLen == 3:  # assume h:m:s
                self.time["s"] = float(usrList[2])
                self.time["m"] = int(usrList[1])
                self.time["h"] = int(usrList[0])
            elif usrLen == 4:  # assume d:h:m:s
                self.time["s"] = float(usrList[3])
                self.time["m"] = int(usrList[2])
                self.time["h"] = int(usrList[1])
                self.time["d"] = int(usrList[0])
            else:
                raise ValueError("unsupported time string")
        # order does not matter for labeled data
        # label must follow value
        elif format == "label":
            # parse as char separated
            charList = list(copy.copy(usrStr))
            labelList = []  # in order found in usrStr
            valStr = copy.copy(usrStr)
            for char in charList:
                if char in self.timeLabels:
                    labelList.append(char)  # in order found
            for label in labelList:
                # replace all labels /w commas, make into a list
                valStr = valStr.replace(label, ",")
            valList = valStr.split(",")
            if valList[-1] == "":  # last label, no comma, causes last val to be ''
                del valList[-1]
            if len(labelList) != len(valList):
                raise ValueError("bad time string labels")
            for i in range(0, len(labelList)):
                val = valList[i]
                label = labelList[i]
                if label not in ["f", "s"]:  # not a float
                    self.time[label] = int(val)
                else:
                    self.time[label] = float(val)

    def _strNum(self, num):
        """take a num and return a sting
        pad extra zero if num is less than 10
        if num is > 60 leave alone"""
        if num == 0 or num < 0.0001:  # min resolution
            return "00"
        elif num > 60:
            return str(num)
        elif num < 0.01:  # show 4 decimals
            return "0%.4f" % (round(num, 4))
        elif num < 1:  # show 2 decimals
            return "0%.2f" % (round(num, 2))
        elif num < 10:
            return "0%i" % (int(round(num)))
        else:
            return "%s" % (int(round(num)))

    def repr(self, type="label"):
        if type == "label":
            return "%sd %sh %sm %ss" % (
                self._strNum(self.time["d"]),
                self._strNum(self.time["h"]),
                self._strNum(self.time["m"]),
                self._strNum(self.time["s"] + self.time["f"]),
            )
        elif type == "watch":
            if self.time["d"] != 0:  # show all
                return "%s:%s:%s:%s" % (
                    self._strNum(self.time["d"]),
                    self._strNum(self.time["h"]),
                    self._strNum(self.time["m"]),
                    self._strNum(self.time["s"] + self.time["f"]),
                )
            elif self.time["h"] != 0:  # show up to hour
                return "%s:%s:%s" % (
                    self._strNum(self.time["h"]),
                    self._strNum(self.time["m"]),
                    self._strNum(self.time["s"] + self.time["f"]),
                )
            else:  # s, fractions if necessary
                return "%s:%s" % (
                    self._strNum(self.time["m"]),
                    self._strNum(self.time["s"] + self.time["f"]),
                )
        elif type == "s" or type == "seconds":
            pass

    def __str__(self):
        return self.repr()

    def __repr__(self):
        return self.repr()

    def __getattr__(self, name):
        if name not in self.timeLabels:
            print("missing", name)
            raise AttributeError
        s = self._seconds()  # geet seconds
        if name == "s" or name == "f":
            return s
        elif name == "m":
            return s / float(self.sPerMin)
        elif name == "h":
            return s / float(self.sPerHour)
        elif name == "d":
            return s / float(self.sPerDay)

    def _updateTime(self):
        """conver the time in seconds to the self.time dictionary"""
        # convert seconds to int and split fraction
        sAdj = 0
        if self.time["f"] != 0:  # split float
            sAdj, f = divmod(self.time["f"], 1)
            self.time["f"] = f
        # check for floats in second's vales
        self.time["s"] = self.time["s"] + sAdj
        if self.time["s"] != 0:
            sAdj = 0
            s, f = divmod(self.time["s"], 1)
            if f != 0:  # there is a fraction in the seconds
                self.time["f"] = self.time["f"] + f
                # check floats again
                sAdj, fAdj = divmod(self.time["f"], 1)  # check if fract is > 1
                if sAdj != 0:  # f, s, needs to be adjusted
                    self.time["f"] = fAdj
            self.time["s"] = int(s + sAdj)  # final s as int
        # s is now and int; split seconds
        mAdj = 0
        if self.time["s"] != 0:
            mAdj, s = divmod(self.time["s"], self.sPerMin)
            if mAdj != 0:  # s, m need to be adjusted
                self.time["s"] = s
        self.time["m"] = self.time["m"] + mAdj
        # check minutes
        hAdj = 0
        if self.time["m"] != 0:
            hAdj, m = divmod(self.time["m"], self.mPerHour)
            if hAdj != 0:  # m,h need to be adjusted
                self.time["m"] = m
        self.time["h"] = self.time["h"] + hAdj
        # check hours
        dAdj = 0
        if self.time["h"] != 0:
            dAdj, h = divmod(self.time["h"], self.hPerDay)
            if dAdj != 0:  # d, h need to be adjusted
                self.time["h"] = h
        self.time["d"] = self.time["d"] + dAdj
        # check days

    def _seconds(self):
        """sum total seconds"""
        s = 0
        s = s + self.time["f"]  # add float
        s = s + self.time["s"]  # add sec
        s = s + (self.time["m"] * self.sPerMin)
        s = s + (self.time["h"] * self.sPerHour)
        s = s + (self.time["d"] * self.sPerDay)
        return s


# -----------------------------------------------------------------||||||||||||--
class Timer:
    """object to hande timing things and printing durations"""

    def __init__(self):
        # start on init
        self.tStart = time.time()
        self.tDif = 0
        self.tStop = None

    def start(self):
        """explicit start method; will clear previous values"""
        self.tStart = time.time()
        self.tStop = None  # show that a new run has started so __call__ works
        self.tDif = 0

    def stop(self):
        self.tStop = time.time()
        self.tDif = self.tStop - self.tStart

    def clear(self):
        self.tStop = None
        self.tDif = 0
        self.tStart = None

    def __call__(self, format=None):
        """reports curretntime or stopped time
        if stopped, gets tDif; if not stopped, gets current time
        can get string or numerical representations"""
        if self.tStop == None:  # if not stoped yet
            t = time.time() - self.tStart
        else:
            t = self.tDif

        if format == None:
            return t  # get numerical
        elif format == "sw":
            tObj = TimeValue(t)
            return tObj.repr("watch")  # self.stopwatchStr(t)

    def __str__(self):
        if self.tStop == None:  # if not stoped yet
            t = time.time() - self.tStart
        else:
            t = self.tDif
        tObj = TimeValue(t)
        return tObj.repr("watch")
        # return self.stopwatchStr(self.tDif)


# -----------------------------------------------------------------||||||||||||--
class TestOld:
    def __init__(self):
        # self.testPulse()
        self.testPulseSplit()
        # self.testConversions()
        # self.testRhythm()
        # self.testTimer()
        # self.testTimeValue()

    def testPulseSplit(self):
        for triple in ([4, 1], [3, 1], [1, 1], [5, 3]):
            a = Pulse(triple)
            for fraction in ([1, 4], [3, 4], [5, 8], [2, 3], [6, 21]):
                print("source:", a, a())
                print("fraction:", str(fraction))
                # split into a quarter and three quarters
                x, y = a.fracture(fraction[0], fraction[1])
                print("result:", x, x(), y, y())
                print("sum:", x()[0] + y()[0])
                print()

    def testRhythm(self):
        testVals = (
            ((2, 1), (3, 1), (5, 1, 0)),
            ("(3,2,1)", "(1,1,mf)", "(3,1)"),
            (2, 1, 1),
            "mf,p,f",
            (1),
            (1, 1),
            (1, 0),
            (0, 1, 0),
            (0.2, 0.4, 1),
        )
        # note that the singel tuple gets converted to one pulse, wheras
        # the list of chars / floats gets converted to 3 pulses
        for val in testVals:
            a = Rhythm(val)
            print("\ninput", val, len(a))
            for type in a.forms:
                print(a.repr(type), a.get(type))

    def testTimer(self):
        obj = Timer()
        print("print:", obj)
        time.sleep(2.2)
        print("print:", obj)
        time.sleep(2.8)
        print("call:", obj())
        time.sleep(3.1)
        print("call:", obj())
        time.sleep(1.1)
        obj.stop()
        print(obj)
        print()

    def testTimeValue(self):
        for testStr in [
            "3:2",
            "25h.2s",
            "1d 4h 64m 2.4s",
            "3:2:4.3",
            1201,
            30.2,
            234234,
        ]:
            print(testStr)
            tObj = TimeValue(testStr)
            print(tObj.repr("label"))
            print(tObj.repr("watch"))
            for label in tObj.timeLabels:
                print("%s:" % label, getattr(tObj, label))
            print()


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)

    def testPulse(self):
        testVals = (
            1,
            0.5,
            "q",
            "s",
            "4,3,2",
            (1, 4, 0.5),
            (2, 4),
            (1, 2, "+"),
            "(3,8,+)",
            (2, 3, "fff"),
            "3,3,ff",
            "mf",
        )
        for test in testVals:
            pulse = Pulse(test)
            for type in pulse.forms:
                post = type, pulse.repr(type), pulse.get(type)
            post = pulse(30)
            post = pulse(60, 1.6)  # call w/ bpm and sustain ratio
            post = pulse(60, 0.3)

    def testConversions(self):
        post = accToDynStr(1)
        post = accToDynStr(0.9)
        post = accToDynStr(0.8)
        post = accToDynStr(0.4)
        post = accToDynStr(0.3)
        post = accToDynStr(0.1)
        post = accToDynStr(0)

        pulse = Pulse(0.5)
        post = pulse._scrubDynStr("(3,2,mf)")
        post = pulse._scrubDynStr("(3,2,o)")
        post = pulse._scrubDynStr("(3,2,+)")
        post = pulse._scrubDynStr("(3,2,mp)")
        post = pulse._scrubDynStr("(3,2,f)")
        post = pulse._scrubDynStr("(3,2,fff)")
        post = pulse._scrubDynStr("(3,2,p)")
        post = pulse._scrubDynStr("(3,2,pp)")
        post = pulse._scrubDynStr("(3,2,.4)")
        post = pulse._scrubDynStr("fff")
        post = pulse._scrubDynStr("+")


# -----------------------------------------------------------------||||||||||||--


if __name__ == "__main__":
    from athenaCL.test import baseTest

    baseTest.main(Test)
