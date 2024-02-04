# -----------------------------------------------------------------||||||||||||--
# Name:          grammar.py
# Purpose:       Grammar and L-System tools
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2009-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import string, random
import unittest, doctest
import uuid

from athenaCL.libATH import permutate
from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import unit
from athenaCL.libATH import error


_MOD = "grammar.py"
from athenaCL.libATH import prefTools

environment = prefTools.Environment(_MOD)


# clases for creating grammars
# permit L-systems, context-free, and other grammars
# employ markov style string notation


# markov version used : to delimit chars/symbols
# a{.2}b{5}c{8} :{a=1|b=2|c=1}
# a{.2}b{5}c{8} :{a=1|b=2|c=1} a:{c=2|a=1} c:{b=1} a:a:{a=3|b=9} c:b:{a=2|b=7|c=4}


# grammar version does not use : to delimt, as not necessary for second
# or higher order
# a{.2}b{5}c{8} a{a:b} c{b} b{b:c=.4|a:c=.6}
#
# first define variables
# a{.2}b{5}c{8}
#

# can we specify genetic operators
# mutation rules
# need to define this as a mutation operation w/ a special flag
# perhaps *?
# mutation happens on the original production rules but does not continue
# *b{c=.3|a=.6}

#
# w/ context ab goes to ac?
# ab{ac}
# *ba{a}
# b*a{c}
#


# ---------------------------------------------------------------------------||--
class Grammar:

    def __init__(self):
        self._srcStr = ""
        # a dictionary of alphabetic symbols and their assoicated values
        self._symbols = {}
        self._rules = {}  # production rules
        self._axiom = None  # initial state, chosen at random if not provided
        # store a string array of current state
        # init should be axiom
        self._state = None

        # store max size of all output rules
        self._maxRuleOutputSize = 0

        self.OPEN = "{"
        self.CLOSE = "}"
        # could also be % symbol
        self.SPLIT = "@"  # used to devide varaible assign from rules
        self.ASSIGN = "="

        # space separates weights; also used as 'or' in weight keys?
        self.ASSIGNDELIMIT = "|"
        self.STEP = ":"
        # symbols for expression weight key definitions
        self.EXPRESSALL = "*"
        # self.EXPRESSNOT = '-'
        self.EXPRESSOR = "|"
        self.EXPRESS = self.EXPRESSALL, self.EXPRESSOR  # self.EXPRESSNOT,
        # define valid symbol (name) characters
        # symbols may not include spaces, nor case
        self.SYM = string.ascii_lowercase + string.digits

    def _sortSymbolLabel(self, pair):
        """give pairs of items (where the first is the label)
        extract label and return a sorted list

        >>> g = Grammar()
        >>> g._sortSymbolLabel([['a', 234.5], ['b', 234]])
        [('a', 234.5), ('b', 234)]

        >>> g._sortSymbolLabel([['c', 234.5], ['a', 234]])
        [('a', 234), ('c', 234.5)]
        """
        label = []
        maxSize = 0
        for s, w in pair:
            if len(s) >= maxSize:
                maxSize = len(s)
            label.append((s, w))
        label.sort()
        post = []
        for i in range(maxSize + 1):
            for s, w in label:
                if len(s) == i:
                    post.append((s, w))
        return post

    # -----------------------------------------------------------------------||--
    def _parseValidate(self, usrStr):
        """make sure the the string is well formed

        >>> g = Grammar()
        >>> g._parseValidate('sdf{3}')
        >>> g._parseValidate('sdf{3}}')
        Traceback (most recent call last):
        TransitionSyntaxError: all braces not paired
        """
        if usrStr.count(self.OPEN) != usrStr.count(self.CLOSE):
            # replace with exception subclass
            raise error.TransitionSyntaxError("all braces not paired")

    def _parseClean(self, usrStr):
        """remove any unusual characters that might appear
        >>> g = Grammar()
        >>> g._parseClean('sdf{3}')
        'sdf{3}'
        >>> g._parseClean('sdf{"green"}')
        'sdf{green}'
        """
        for char in ['"', "'"]:
            usrStr = usrStr.replace(char, "")
        return usrStr

    def _parseRuleValue(self, pairRule):
        """Read a preliminary dictionary of rules, and split into a list of rules based on having one or more probabilistic rule options

        >>> g = Grammar()
        >>> g._parseRuleValue({'a': 'ab'})
        >>> g._rules
        {'a': [('ab', 1)]}

        >>> g._parseRuleValue({'a': 'ab|ac'})
        >>> g._rules
        {'a': [('ab', 1), ('ac', 1)]}

        >>> g._parseRuleValue({'a': 'ab|ac|aa=3'})
        >>> g._rules
        {'a': [('ab', 1), ('ac', 1), ('aa', 3)]}


        >>> g._parseRuleValue({'a': 'ab=3|c=12|aa=3'})
        >>> g._rules
        {'a': [('ab', 3), ('c', 12), ('aa', 3)]}

        >>> g._parseRuleValue({'a': 'ab=3|c=12|aa=3', 'c': 'b=3|c=5|a'})
        >>> g._rules
        {'a': [('ab', 3), ('c', 12), ('aa', 3)], 'c': [('b', 3), ('c', 5), ('a', 1)]}

        >>> g._parseRuleValue({'a': 'ab=3|c=12|aa=0'})
        Traceback (most recent call last):
        TransitionSyntaxError: bad weight value given: aa=0

        >>> g._parseRuleValue({'a': ''})
        >>> g._rules
        {'a': [('', 1)]}

        >>> g._parseRuleValue({'a': 'ab=3|c=12|'})
        >>> g._rules
        {'a': [('ab', 3), ('c', 12), ('', 1)]}

        >>> g._parseRuleValue({'*a': 'ab=3|c=12|a=3'})
        >>> g._rules
        {'*a': [('ab', 3), ('c', 12), ('a', 3)]}

        """
        self._rules = {}  # this always clears the last rules
        for key, value in list(pairRule.items()):
            # make value into a src:dst pairs
            ruleList = []
            weights = value.split(self.ASSIGNDELIMIT)  # this is the |

            if len(weights) == 1:
                # if there is only one weight, add an assignment value of 1
                # this is permitted
                if self.ASSIGN not in weights[0]:
                    ruleList.append((weights[0], 1))
                else:  # remove weight, as it is not significant
                    w = weights[0].split(self.ASSIGN)[0]
                    ruleList.append((w, 1))
            # if there are no assignments but more than one option
            # that is, no = sign assignments
            elif value.count(self.ASSIGN) == 0:
                for symbol in weights:
                    ruleList.append((symbol, 1))
            else:
                # environment.printDebug(['obtained weights', weights, value.count(self.ASSIGN)])

                for assign in weights:
                    # if not assignment, provide one as a string
                    if self.ASSIGN not in assign:
                        assign += "=1"  # assume 1

                    symbol, w = assign.split(self.ASSIGN)
                    # convert to float or int, may not be less tn zero
                    # will return None on error
                    w = drawer.strToNum(w, "num", 0, None)
                    if w in [None, 0]:  # no zero weights, or other errors
                        raise error.TransitionSyntaxError(
                            "bad weight value given: %s" % assign
                        )
                    ruleList.append((symbol, w))
            self._rules[key] = ruleList

    def _parseAxiom(self, axiomSrc=None):
        """Call this after all symbols have been found"""
        knownSym = list(self._symbols.keys())
        if axiomSrc != None:
            # NOTE: assumes no delimiters between symbols
            axiomSrc = axiomSrc.strip()
            for char in axiomSrc:
                if char not in knownSym:
                    raise error.TransitionSyntaxError(
                        "bad axiom value given: %s" % char
                    )
            self._axiom = axiomSrc
        else:  # get a random start
            self._axiom = random.choice(knownSym)
        # always update state to axiom
        self._state = self._axiom

    def _checkSymbolFormDef(self, symStr):
        """makes sure that symbol usage is valid for symbol definitions
        symbols cannot have spaces, case, or strange characters

        >>> g = Grammar()
        >>> g._checkSymbolFormDef('wer')
        >>> g._checkSymbolFormDef('w:er')
        Traceback (most recent call last):
        TransitionSyntaxError: symbol definition uses illegal characters (:)

        >>> g._checkSymbolFormDef('wer@#$')
        Traceback (most recent call last):
        TransitionSyntaxError: symbol definition uses illegal characters (@)

        """
        for char in symStr:
            if char not in self.SYM:
                raise error.TransitionSyntaxError(
                    "symbol definition uses illegal characters (%s)" % char
                )

    def _checkSymbolFormRuleKey(self, symStr):
        """makes sure that symbol usage is valid for weight label keys
        permits step separators and expression characters

        >>> g = Grammar()
        >>> g._checkSymbolFormRuleKey('wer')

        """
        if symStr == "":  # permit the empty string
            return

        valid = self.SYM + self.STEP + "".join(self.EXPRESS)
        for char in symStr:
            if char not in valid:
                raise error.TransitionSyntaxError(
                    "rule definition uses illegal characters (%s)" % char
                )
        # there must be at least one symbol on left side of production
        # rule that is just a symbol
        count = 0
        # can be a defined symbol or an all expression
        for char in self.SYM + self.EXPRESSALL:
            if char in symStr:
                count += 1
            if count > 0:
                break
        if count == 0:  # no symbols were found
            raise error.TransitionSyntaxError(
                "rule definition does not define source symbol"
            )

    def _checkRuleReference(self):
        """Make sure that all rule outputs and inputs refer to defined symbols. Rule inputs can use EXPRESSALL for matching

        This method is called in _parse().

        """
        self._maxRuleOutputSize = 0

        knownSym = list(self._symbols.keys())
        for inRule, outRule in list(self._rules.items()):
            # environment.printDebug(['in rule, out rule', inRule, outRule])
            environment.printDebug(["in rule", repr(inRule), "out rule", outRule])

            # need to iterate through rule parts first
            match = True
            # permit empty string as input: this is not yet fully implemented
            if inRule == "":
                pass
            else:
                for r in inRule:
                    if r not in knownSym + [self.EXPRESSALL]:
                        match = False
            if not match:
                raise error.TransitionSyntaxError(
                    "source rule component (%s) references an undefined symbol" % inRule
                )

            # check out rules, of which there is 1 or more
            # NOTE: this assumes there are not delimiters used
            match = False
            for option, weight in outRule:  # pairs of value, weight

                # environment.printDebug(['_checkRuleReference(): option', repr(option)])

                if len(option) > self._maxRuleOutputSize:
                    self._maxRuleOutputSize = len(option)

                if option == "":  # accept empty output option
                    match = True

                # if out rules point to more then value, need to split here
                for char in option:
                    #                     if char == '': # permit empty string
                    #                         match = True
                    if char not in knownSym:
                        match = False
                        break
                    else:
                        match = True
                if not match:
                    break
            if not match:
                raise error.TransitionSyntaxError(
                    "destination rule component (%s) references an undefined symbol"
                    % outRule
                )

    # -----------------------------------------------------------------------||--

    def _parse(self, usrStr):
        """
        >>> g = Grammar()
        >>> g._parse('a{3}b{4} @ a{b}b{a|b}')
        >>> g._parse('a{3}b{4} @ a{b}b{a|b|c}')
        Traceback (most recent call last):
        TransitionSyntaxError: destination rule component ([('a', 1), ('b', 1), ('c', 1)]) references an undefined symbol

        >>> g._parse('a{3}b{4}c{3} @ a{b}b{a|b|c}')

        >>> g._parse('a{3}b{4}c{3} @ a{b}d{a|b|c}')
        Traceback (most recent call last):
        TransitionSyntaxError: source rule component (d) references an undefined symbol

        >>> g._symbols
        {'a': '3', 'c': '3', 'b': '4'}

        >>> g._parse('a{3}b{4}c{3} @ a{bb}b{aa|b|c}')
        >>> g._symbols
        {'a': '3', 'c': '3', 'b': '4'}
        >>> g._rules
        {'a': [('bb', 1)], 'b': [('aa', 1), ('b', 1), ('c', 1)]}

        >>> g._parse('a{3}b{4} @ a{b}b{a|b} @ b')
        >>> g._axiom
        'b'
        >>> g._parse('a{3}b{4} @ a{b}b{a|b} @ baab')
        >>> g._axiom
        'baab'

        >>> g._parse('a{3}b{4} @ a{b}ac{a|b} @ baab')
        Traceback (most recent call last):
        TransitionSyntaxError: source rule component (ac) references an undefined symbol

        >>> g._parse('a{3}b{4} @ *{b} @ baab') # * can be source, not dst
        >>> g._parse('a{3}b{4} @ a{*} @ baab') # * cannot be destination
        Traceback (most recent call last):
        TransitionSyntaxError: destination rule component ([('*', 1)]) references an undefined symbol

        """
        # divide all groups into pairs of key, {}-enclosed values
        # all elements of notation are <key>{<value>} pairs

        self._parseValidate(usrStr)
        usrStr = self._parseClean(usrStr)

        pairSymbol = {}
        pairRule = {}

        if usrStr.count(self.SPLIT) not in [1, 2]:  # must be 1 or 2
            raise error.TransitionSyntaxError(
                "must include exactly one split delimiter (%s)" % self.SPLIT
            )
        if usrStr.count(self.SPLIT) == 1:
            partSymbol, partRule = usrStr.split(self.SPLIT)
            partAxiom = None
        elif usrStr.count(self.SPLIT) == 2:  # split into three
            partSymbol, partRule, partAxiom = usrStr.split(self.SPLIT)

        for subStr, dst in [(partSymbol, "symbol"), (partRule, "rule")]:
            groups = subStr.split(self.CLOSE)
            for double in groups:
                if self.OPEN not in double:
                    continue
                try:
                    key, value = double.split(self.OPEN)
                except:  # possible syntax error in formationi
                    raise error.TransitionSyntaxError("badly placed delimiters")

                # key is always a symbol def: will change case and remove spaces
                key = drawer.strScrub(key, "lower", [" "])  # rm spaces from key

                # split into 2 dictionaries, one w/ symbol defs, one w/ rules
                # symbol defs must come before
                if dst == "symbol":
                    self._checkSymbolFormDef(key)  # will raise exception on bad key
                    pairSymbol[key] = drawer.strScrub(value, None, [" "])
                elif dst == "rule":
                    self._checkSymbolFormRuleKey(key)
                    pairRule[key] = drawer.strScrub(value, "lower", [" "])

        # this initializes symbol table
        if pairSymbol == {}:
            raise error.TransitionSyntaxError("no symbols defined")
        self._symbols = pairSymbol
        # pass the pair dictionary to weight parser
        if pairRule == {}:
            raise error.TransitionSyntaxError("no rules defined")
        self._parseRuleValue(pairRule)  # assigns to self._rules

        # check symbol usage and determine orders
        self._checkRuleReference()
        # assigns axiom value
        self._parseAxiom(partAxiom)

    # -----------------------------------------------------------------------||--
    def _valueToSymbol(self, value):
        """for a data value, return the defined symbol label

        >>> g = Grammar()
        >>> g._parse('a{3}b{4} @ a{b}b{a|b}')
        >>> g._valueToSymbol('4') # everything is a string
        'b'
        """
        for s, v in list(self._symbols.items()):
            if str(value) == v:
                return s
        raise ValueError("value (%s) not known as a symbol" % value)

    def _valueListToSymbolList(self, valueList):
        """given a list of values (taken from an previous generated values)
        convert all the values to the proper symbols, and return as a tuple

        >>> g = Grammar()
        >>> g._parse('a{3}b{4} @ a{b}b{a|b}')
        >>> g._valueListToSymbolList(['3', '4', '3', '4'])
        ('a', 'b', 'a', 'b')

        """
        if len(valueList) == 0:
            return ()  # return an empty tuple
        msg = []
        for v in valueList:
            msg.append(self._valueToSymbol(v))
        return tuple(msg)

    def _symbolToValue(self, value):
        """for a data value, return the defined symbol label

        >>> g = Grammar()
        >>> g._parse('a{3}b{4} @ a{b}b{a|b}')
        >>> g._symbolToValue('a') # everything is a string
        3.0
        """
        for s, v in list(self._symbols.items()):
            if value == s:
                if drawer.isCharNum(v):
                    return float(v)
                else:
                    return v
        raise ValueError("symbol (%s) not known as a value" % value)

    def _symbolListToValueList(self, symbolList):
        """given a list of values (taken from an previous generated values)
        convert all the values to the proper symbols, and return as a tuple

        >>> g = Grammar()
        >>> g._parse('a{3}b{4} @ a{b}b{a|b}')
        >>> g._symbolListToValueList(('a', 'b', 'a', 'b'))
        [3.0, 4.0, 3.0, 4.0]

        """
        if len(symbolList) == 0:
            return []  # return an empty tuple
        msg = []
        for s in symbolList:
            msg.append(self._symbolToValue(s))
        return msg

    def _symbolStrToValueList(self, symbolStr):
        """
        >>> g = Grammar()
        >>> g._parse('a{3}b{4} @ a{b}b{a|b}')
        >>> g._symbolStrToValueList('aaabbaaaba')
        [3.0, 3.0, 3.0, 4.0, 4.0, 3.0, 3.0, 3.0, 4.0, 3.0]

        """
        # divide into list
        symbolList = []
        for char in symbolStr:
            symbolList.append(char)
        return self._symbolListToValueList(symbolList)

    # -----------------------------------------------------------------------||--
    def repr(self):
        """provide a complete grammar string
        >>> g = Grammar()
        >>> g._parse('a{3}b{4} @ a{b}b{a|b} @ a')
        >>> g.repr()
        'a{3}b{4}@a{b}b{a=1|b=1}@a'

        >>> g._parse('a{3}b{4} @ a{bba}b{a|b} @ a')
        >>> g.repr()
        'a{3}b{4}@a{bba}b{a=1|b=1}@a'

        >>> g._parse('a{3}b{4} @ a{bba}b{a=3|b=10} @ a')
        >>> g.repr()
        'a{3}b{4}@a{bba}b{a=3|b=10}@a'

        """
        # do symbol list first
        msg = []
        syms = self._sortSymbolLabel(list(self._symbols.items()))
        for s, data in syms:
            msg.append("%s%s%s%s" % (s, self.OPEN, data, self.CLOSE))
        msg.append(self.SPLIT)
        for src, dst in list(self._rules.items()):
            sub = []
            if len(dst) > 1:
                for part, weight in dst:
                    sub.append("%s=%s" % (part, weight))
            else:  # leave out weight, just get first part
                sub.append(dst[0][0])
            msg.append("%s%s%s%s" % (src, self.OPEN, "|".join(sub), self.CLOSE))
        msg.append(self.SPLIT)
        msg.append(self._axiom)
        return "".join(msg)

    def __str__(self):
        """provide a complete grammar string
        >>> g = Grammar()
        >>> g.load('a{3}b{4} @ a{b}b{a|b} @ a')
        >>> str(g)
        'a{3}b{4}@a{b}b{a=1|b=1}@a'
        """
        return self.repr()

    # -----------------------------------------------------------------------||--
    def load(self, usrStr):
        """load a transition string"""
        self._srcStr = usrStr
        self._parse(self._srcStr)

    def _tagIn(self, input):
        """Must wrap numbers so that 1 does not match 11; instaed <1> and <11> are different matches"""
        return "<%s>" % input

    def __next__(self):
        """Apply all rules and produce a new self._state

        >>> g = Grammar()
        >>> g.load('a{3}b{4} @ a{bab}b{aab} @ abaa')
        >>> str(g)
        'a{3}b{4}@a{bab}b{aab}@abaa'
        >>> g.next()
        >>> g.getState()
        'babaabbabbab'
        >>> g.next()
        >>> g.getState()
        'aabbabaabbabbabaabaabbabaabaabbabaab'
        >>> g.getState(values=True)
        [3.0, 3.0, 4.0, 4.0, 3.0, 4.0, 3.0, 3.0, 4.0, 4.0, 3.0, 4.0, 4.0, 3.0, 4.0, 3.0, 3.0, 4.0, 3.0, 3.0, 4.0, 4.0, 3.0, 4.0, 3.0, 3.0, 4.0, 3.0, 3.0, 4.0, 4.0, 3.0, 4.0, 3.0, 3.0, 4.0]

        >>> g = Grammar()
        >>> g.load('a{3}b{4}c{20}d{2} @ a{bab}b{acb}c{ac}d{cd} @ abd')
        >>> str(g)
        'a{3}b{4}c{20}d{2}@a{bab}c{ac}b{acb}d{cd}@abd'
        >>> g.next()
        >>> g.getState()
        'babacbcd'
        >>> g.next()
        >>> g.getState()
        'acbbabacbbabacacbaccd'


        >>> g = Grammar()
        >>> g.load('a{a}b{b} @ a{ab}b{a} @ b')
        >>> g.getState()
        'b'
        >>> g.next()
        >>> g.getState()
        'a'
        >>> g.next()
        >>> g.getState()
        'ab'
        >>> g.next()
        >>> g.getState()
        'aba'
        >>> g.next()
        >>> g.getState()
        'abaab'
        >>> g.next()
        >>> g.getState()
        'abaababa'

        """
        if self._state == None or self._state == "":
            self._state = self._axiom  # a copy in principle

        stateNew = self._state  # copy
        matchTag = []  # matched start indices
        replacementCount = 0

        # make groups of index values, src groups to match
        # need to find largest rule in size
        indexCharPairs = []
        # self._maxRuleOutputSize

        # environment.printDebug(['next(): self._state', self._state])

        for size in range(1, self._maxRuleOutputSize + 1):
            # for size in range(1, 2):
            for i in range(0, len(self._state), size):
                pair = (i, self._state[i : i + size])
                if pair not in indexCharPairs:
                    indexCharPairs.append(pair)

        for inRule, outRule in list(self._rules.items()):

            environment.printDebug(["next(): in/out rule", repr(inRule), outRule])
            # grammar.py: next(): in/out rule '*' [('ab',1)]

            # environment.printDebug(['next(): index char pairs', indexCharPairs])

            # char here may be 1 or more characters, up to max rule size
            for i, char in indexCharPairs:
                # for i, char in enumerate(self._state):

                # comparison to rule
                match = False
                # test single character, exact match
                if inRule == self.EXPRESSALL or inRule == char:
                    match = True
                # if mutliple characters, and one is expressall, and lenght
                # is the same
                elif (
                    len(inRule) > 1
                    and len(inRule) == len(char)
                    and self.EXPRESSALL in inRule
                ):
                    matchChar = 0
                    for j in range(len(inRule)):
                        if inRule[j] == char[j] or inRule[j] == self.EXPRESSALL:
                            matchChar += 1
                    if matchChar == len(inRule):
                        match = True

                if not match:
                    continue

                # need to find cases of two or more char matches

                # store a string of index in the temp to mark positions
                # can find first instance of symbol; will not
                # be past symbols b/c we are replacing with the old index nums
                iNew = stateNew.find(char)
                pre = stateNew[:iNew]
                # skip location
                post = stateNew[iNew + len(char) :]
                # insert marker as a random cod
                tag = self._tagIn(replacementCount)
                replacementCount += 1
                stateNew = pre + tag + post

                # environment.printDebug(['next(): stateNew', stateNew, repr(pre), repr(tag), repr(post)])
                # make a rule section

                # if only one rule, simply provide it
                if len(outRule) == 1:
                    # a list of value, weight pairSymbol
                    replacement = outRule[0][0]
                # if more than one rule, do a weighted selection
                else:
                    options = []
                    weights = []
                    for o, w in outRule:
                        options.append(o)
                        weights.append(w)
                    # create unit boundaries from ordered weights
                    boundary = unit.unitBoundaryProportion(weights)
                    i = unit.unitBoundaryPos(random.random(), boundary)
                    replacement = options[i]  # index is in position

                # a lost of all replacements to make, between the tag and the
                # replacement
                matchTag.append([tag, replacement])

        # do all replacements
        # environment.printDebug(['stateNew: prereplace', stateNew])
        for tag, replacement in matchTag:
            # these are not actual indices but tags to points in the scratch
            iNew = stateNew.find(tag)
            pre = stateNew[:iNew]
            # skip location
            post = stateNew[iNew + len(tag) :]
            # insert final value
            stateNew = pre + replacement + post

        # environment.printDebug(['stateNew: post', stateNew])

        # replace old
        self._state = stateNew

    def getState(self, values=False):
        if not values:
            return self._state
        else:
            return self._symbolStrToValueList(self._state)

    def reset(self):
        """Reset the state."""
        # state will be set to axiom on next call
        self._state = None

    def setAxiom(self, src):
        """Reset the axiom and the initial state."""
        self._parseAxiom(src)


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):

        g = Grammar()
        g.load("a{3}b{4} @ a{bab}b{aab} @ a")
        next(g)
        self.assertEqual(g.getState(), "bab")
        g.reset()
        next(g)
        self.assertEqual(g.getState(), "bab")
        g.setAxiom("b")
        self.assertEqual(g.getState(), "b")
        next(g)
        self.assertEqual(g.getState(), "aab")

        g.setAxiom("ab")
        self.assertEqual(g.getState(), "ab")
        next(g)
        self.assertEqual(g.getState(), "babaab")
        next(g)
        self.assertEqual(g.getState(), "aabbabaabbabbabaab")

        # simple oscillation
        g = Grammar()
        g.load("a{3}b{4} @ a{b}b{a} @ a")
        next(g)
        self.assertEqual(g.getState(), "b")
        next(g)
        self.assertEqual(g.getState(), "a")
        next(g)
        self.assertEqual(g.getState(), "b")
        next(g)
        self.assertEqual(g.getState(), "a")

        # simple oscillation
        g = Grammar()
        g.load("a{3}b{4} @ a{b}b{a} @ a")
        next(g)
        self.assertEqual(g.getState(), "b")
        next(g)
        self.assertEqual(g.getState(), "a")
        next(g)
        self.assertEqual(g.getState(), "b")
        next(g)
        self.assertEqual(g.getState(), "a")

        # decomposition: can we decompose
        g = Grammar()
        g.load("a{3}b{4} @ a{b}b{}{a} @ a")
        next(g)
        self.assertEqual(g.getState(), "b")
        next(g)
        self.assertEqual(g.getState(), "")
        next(g)
        # for now, this replaces with the axiom
        self.assertEqual(g.getState(), "b")

        g = Grammar()
        g.load("a{3}b{4} @ a{bab}b{} @ bbabbabb")
        next(g)
        self.assertEqual(g.getState(), "babbab")
        next(g)
        self.assertEqual(g.getState(), "babbab")

        # try context matches: can match one to many
        g = Grammar()
        g.load("a{3}b{4} @ aa{bb}bb{aaaa} @ bb")
        next(g)
        self.assertEqual(g.getState(), "aaaa")
        next(g)
        self.assertEqual(g.getState(), "bbbb")
        next(g)
        self.assertEqual(g.getState(), "aaaaaaaa")
        next(g)
        self.assertEqual(g.getState(), "bbbbbbbb")
        next(g)
        self.assertEqual(g.getState(), "aaaaaaaaaaaaaaaa")

        g = Grammar()
        g.load("a{3}b{4} @ aaa{aba}aba{bbb}bbb{aaa} @ bbb")
        next(g)
        self.assertEqual(g.getState(), "aaa")
        next(g)
        self.assertEqual(g.getState(), "aba")
        next(g)
        self.assertEqual(g.getState(), "bbb")
        next(g)
        self.assertEqual(g.getState(), "aaa")
        next(g)

        g = Grammar()
        g.load("a{3}b{4} @ aaa{aba}aba{bbb}bbb{aaa} @ bbbbbb")
        next(g)
        self.assertEqual(g.getState(), "aaaaaa")
        next(g)
        self.assertEqual(g.getState(), "abaaba")
        next(g)
        self.assertEqual(g.getState(), "bbbbbb")
        next(g)
        self.assertEqual(g.getState(), "aaaaaa")
        next(g)

    def testWeighted(self):

        # can use pipe to define equal probabilistic options
        g = Grammar()
        g.load("a{3}b{4} @ a{b|a}b{a|b} @ a")
        next(g)
        self.assertEqual(g.getState() in ["a", "b"], True)
        next(g)
        self.assertEqual(g.getState() in ["a", "b"], True)
        next(g)
        self.assertEqual(g.getState() in ["a", "b"], True)

        g = Grammar()
        g.load("a{3}b{4} @ a{b=5|a} b{a|b=5} @ a")
        post = []
        for x in range(100):
            post.append(g.getState())
            next(g)
        # probabilistic weighting favoring b
        self.assertEqual(post.count("b") > 70, True)

        g = Grammar()
        g.load("a{.2}b{5}c{8} @ a{ab} c{b} b{bc=.4|ac=.6}")

    def testRegularExpression(self):

        g = Grammar()
        g.load("a{1}b{5}c{10} @ *{ab} @ a")

        next(g)
        self.assertEqual(g.getState(), "ab")

        # partial matches with *
        g = Grammar()
        g.load("a{1}b{5}c{10} @ a*{ab} @ aa")
        next(g)
        self.assertEqual(g.getState(), "ab")

        g = Grammar()
        g.load("a{1}b{5}c{10} @ **{ab} @ aa")
        next(g)
        self.assertEqual(g.getState(), "ab")

        g = Grammar()
        g.load("a{1}b{5}c{10} @ b*{ab} @ ba")
        next(g)
        self.assertEqual(g.getState(), "ab")

        g = Grammar()
        g.load("a{1}b{5}c{10} @ *a{cc} @ ba")
        next(g)
        self.assertEqual(g.getState(), "cc")

        g = Grammar()
        g.load("a{1}b{5}c{10} @ *a{cc} c*{aa} @ cc")
        next(g)
        self.assertEqual(g.getState(), "aa")
        next(g)
        self.assertEqual(g.getState(), "cc")
        next(g)
        self.assertEqual(g.getState(), "aa")
        next(g)
        self.assertEqual(g.getState(), "cc")

        g = Grammar()
        g.load("a{1}b{5}c{10} @ a*c{ccc} *c*{abc} @ abc")
        next(g)
        self.assertEqual(g.getState(), "ccc")
        next(g)
        self.assertEqual(g.getState(), "abc")
        next(g)
        self.assertEqual(g.getState(), "ccc")
        next(g)
        self.assertEqual(g.getState(), "abc")


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    import sys
    from athenaCL.test import baseTest

    if len(sys.argv) >= 2:
        t = Test()
        t.testRegularExpression()
    else:
        baseTest.main(Test)
