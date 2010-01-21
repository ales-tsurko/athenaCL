#-----------------------------------------------------------------||||||||||||--
# Name:          grammar.py
# Purpose:       Grammar and L-System tools
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2009 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import string, random

from athenaCL.libATH import permutate
from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import unit
from athenaCL.libATH import error


_MOD = 'grammar.py'



# clases for creating grammars
# permit L-systems, context-free, and other grammars
# employ markov style string notation


# divide all groups into pairs of key, {}-enclosed values
# all elements of notation are <key>{<value>} pairs
# this notation has two types: symbol definitions and weight definitions
# symbol defs: keys are alphabetic, values can be anything (incl lists)
#                   name{symbol}
# weight defs: keys are source transitions statments w/ step indicator :
#                   transition{name=weight|name=weight}
# support for limited regular expressions in weight defs
# t:*:t match any one in the second palce; not e same as zero or more
# t:-t:t match anything that is not t
# t:w|q:t match either (alternation)
        


# markov version
# a{.2}b{5}c{8} :{a=1|b=2|c=1}
# a{.2}b{5}c{8} :{a=1|b=2|c=1} a:{c=2|a=1} c:{b=1} a:a:{a=3|b=9} c:b:{a=2|b=7|c=4}
# 
# 
# 
# grammar version
# a{.2}b{5}c{8} a{a:b} c{b} b{b:c=.4|a:c=.6}
# 
# first define variables
# a{.2}b{5}c{8}
# 
# need a delimter between variables and rules
# @ sign might make sense
# a{.2}b{5}c{8} @ a{a:b} c{b} b:c{b:c=.4|a:c=.6}
# % sign possible
# a{.2}b{5}c{8} % a{a:b} c{b} b{b:c=.4|a:c=.6}
# 
# 
# how do we incorporate constants?
# a{F+-}b{F+-}c{F+-}
# perhaps empty brace?
# f{F}r{+}l{-} @ f{f:r:l}
# 
# 
# then rules
# context free: a can go to abc or ac
# a{a:b:c|a:c}
# 
# context free we weighted probabilites for rules
# a{a:b:c=.2|a:c=.8}
# 
# a{a:b:c=4|a:c=43}
# 
# 
# context free with limited regular expression
# here we match a with any other symbols
# a:*{a:c}
# here we can match either or; a or c goes to b
# a|c{b}
# here we match anything that is not a
# -a{b:a}
# 
# 
# can we specify genetic operators
# mutation rules
# need to define this as a mutation operation w/ a special flag
# perhaps *?
# mutation happens on the original production rules but does not continue
# *b{c=.3|a=.6}
# 
# 
# 
# 
# w/ context: ab goes to ac?
# a:b{a:c}
# 







class Grammar:

    def __init__(self):
        self._srcStr = ''
        # a dictionary of alphabetic symbols and their assoicated values
        self._symbols = {}
        # production rules
        self._rules = {} 
        # stores complete representation, w/ fractional weights
        #self._weightPost = {} 
        self.OPEN = '{'
        self.CLOSE = '}'
        self.SPLIT = '@' # used to devide varaible assign from rules

        self.ASSIGN = '='

        # space separates weights; also used as 'or' in weight keys?
        self.ASSIGNDELIMIT = '|' 
        self.STEP = ':'
        # symbols for expression weight key definitions
        self.EXPRESSALL = '*'
        self.EXPRESSNOT = '-'
        self.EXPRESSOR   = '|'
        self.EXPRESS = self.EXPRESSALL, self.EXPRESSNOT, self.EXPRESSOR
        # define valid symbol (name) characters
        # symbols may not include spaces, nor case
        self.SYM = string.lowercase + string.digits



    #------------------------------------------------------------------------||--

        
    def _sortSymbolLabel(self, pair):
        """give a pairs of items (where the first is the label)
        extract label and return a sorted list"""
        label = []
        maxSize = 0
        for s, w in pair:
            if len(s) >= maxSize:
                maxSize = len(s)
            label.append((s,w))
        label.sort()
        post = []
        for i in range(0, maxSize+1):
            for s, w in label:
                if len(s) == i:
                    post.append((s,w))
        return post
  
    #------------------------------------------------------------------------||--
    def _parseValidate(self, usrStr):
        """make sure the the string is well formed"""
        if usrStr.count(self.OPEN) != usrStr.count(self.CLOSE):
          # replace with exception subclass
          raise error.TransitionSyntaxError, "all braces not paired"

    def _parseClean(self, usrStr):
        """remove any unusual characters that might appear"""
        for char in ['"', "'"]:
            usrStr = usrStr.replace(char, '')
        return usrStr


#     def _parseWeightKey(self, key):
#         """ make key into a list of symbol strings
#         store expression weight keys in a tuple, with operator leading, as a sub 
#         tuple. only one operator is allowed, must be tuple b/c will be a dict key
#         >>> a._parseWeightKey('a:b:c')
#         ('a', 'b', 'c')
#         >>> a._parseWeightKey('a:b:c|d')
#         ('a', 'b', ('|', 'c', 'd'))
#         >>> a._parseWeightKey('a:b:c|d|e')
#         ('a', 'b', ('|', 'c', 'd', 'e'))
#         >>> a._parseWeightKey('a:*:c')
#         ('a', ('*',), 'c')
#         >>> a._parseWeightKey('a:*:-c')
#         ('a', ('*',), ('-', 'c'))
#         """
#         # make key into a list of symbol strings
#         # if key is self.STEP, assign as empty tuple
#         if key == self.STEP: return ()
#         key = tuple(key.split(self.STEP)) # always split by step delim
#         # filter empty strings
#         keyPost = [] 
#         for element in key:
#             if element == '': continue
#             keyPost.append(element.strip())
#         key = keyPost
#         # check for expressions in each segment of key
#         keyFinal = []
#         for segment in key:
#             keyPost = []
#             for exp in self.EXPRESS:
#                 if exp in segment:
#                     keyPost.append(exp)
#             if len(keyPost) == 0: # no expressions used, a normal weight key
#                 keyFinal.append(segment) # make it a tuple before return
#             elif len(keyPost) > 1:
#                 msg = "only one operator may be used per weight key segment"
#                 raise error.TransitionSyntaxError, msg
#             # definitial an expression, pack new tuple, leading with expression op
#             # if it is an or sym, need to split by this symbol
#             else:
#                 if self.EXPRESSOR in segment:
#                     opperands = segment.split(self.EXPRESSOR)
#                     segmentPost = [self.EXPRESSOR] + opperands
#                     keyFinal.append(tuple(segmentPost))
#                 else: # key post already has expression operator leading
#                     for val in segment:
#                         if val in self.EXPRESS: continue 
#                         keyPost.append(val)
#                     keyFinal.append(tuple(keyPost))
#         return tuple(keyFinal)
# 

    def _parseRuleValue(self, pairRule):
        """read a preliminary dictionary of rules, and split into a list of rules based on having one or more probabilistic rule options"""
        self._rules = {} 
        for key, value in pairRule.items():
            # make key into a list of symbol strings
            # need to do this still
            #key = self._parseWeightKey(key)

            # make value into a src:dst pairs
            ruleList = []
            weights = value.split(self.ASSIGNDELIMIT) # this is the |

            if len(weights) == 1:
                # if there is only one weight, add an assignment value of 1
                # this is permitted
                if self.ASSIGN not in weights[0]:
                    ruleList.append((weights[0], 1))
                else: # remove weight, as it is not significant
                    w = weights[0].split(self.ASSIGN)[0]
                    ruleList.append((w, 1))
            # if there are no assignments but more than one option
            elif value.count(self.ASSIGN) == 0: 
                for symbol in weights:
                    ruleList.append((symbol, 1))
            else:
                # if providing assignments weight, must provide all
                if value.count(self.ASSIGN) != len(weights): 
                    raise error.TransitionSyntaxError, \
                    "weight specifications, if provided, must be provided for each rule output options"
                for assign in weights:
                    # if assignment are present this means that there is more than          
                    # than one option
                    symbol, w = assign.split(self.ASSIGN)
                    # convert to float or int, may not be less tn zero
                    # will return None on error
                    w = drawer.strToNum(w, 'num', 0, None)
                    if w in (None, 0): # no zero weights, or other errors
                        raise error.TransitionSyntaxError, \
                                "bad weight value given: %s" % assign
                    ruleList.append((symbol, w))
            self._rules[key] = ruleList 


    def _checkSymbolFormDef(self, symStr):
        """makes sure that symbol usage is valid for symbol definitions
        symbols cannot have spaces, case, or strange characters"""
        for char in symStr:
            if char not in self.SYM:
                raise error.TransitionSyntaxError,\
                "symbol definition uses illegal characters (%s)" % char

    def _checkSymbolFormRuleKey(self, symStr):
        """makes sure that symbol usage is valid for weight label keys
        permits step separateors and expression characters"""
        valid = self.SYM + self.STEP + ''.join(self.EXPRESS)
        for char in symStr:
            if char not in valid:
                raise error.TransitionSyntaxError,\
                "rule definition uses illegal characters (%s)" % char
        # there must be at least on symbol on left side of production
        # rule that is just a symbol
        count = 0
        for char in self.SYM:
            if char in symStr:
                count += 1
            if count > 0: break
        if count == 0: # no symbiols were found
            raise error.TransitionSyntaxError,\
            "rule definition does not define source symbol"

    def _checkRuleReference(self):
        """make sure that all rule outputs and inputs refer to defined symbols """
        knownSym = self._symbols.keys()
        for inRule, outRule in self._rules.items():
            # this is not the right way to do this!
            # need to iterate through rule parts first
            match = 0
            for s in knownSym:
                if s in inRule: 
                    match = 1
            if not match:
                raise error.TransitionSyntaxError, "rule component (%s) references an undefined symbol" % inRule
            match = 0
            for s in knownSym:
                for option in outRule: # pairs of value, weight
                    print _MOD, option
                    if s in option[0]:
                        match = 1
            if not match:
                raise error.TransitionSyntaxError, "rule component (%s) references an undefined symbol" % outRule
    

    #------------------------------------------------------------------------||--

    def _parse(self, usrStr):
        # divide all groups into pairs of key, {}-enclosed values
        # all elements of notation are <key>{<value>} pairs
        # this notation has two types: symbol definitions and weight definitions
        # symbol defs: keys are alphabetic, values can be anything (incl lists)
        #                   name{symbol}
        # rule defs: keys are source, value is production rule 
        # support for limited regular expressions in weight defs
        # t:*:t match any one in the second palce; not e same as zero or more
        # t:-t:t match anything that is not t
        # t:w|q:t match either (alternation)
        
        # note: this will remove all spaces in all keys and all values

        self._parseValidate(usrStr)
        usrStr = self._parseClean(usrStr)

        pairSymbol = {}
        pairRule = {}

        if usrStr.count(self.SPLIT) != 1: # must be 1 and only 1
            raise error.TransitionSyntaxError, "must include exactly one split delimiter (%s)" % self.SPLIT
        partSymbol, partRule = usrStr.split(self.SPLIT)
        #print _MOD, partSymbol, partRule

        for subStr, dst in [(partSymbol, 'symbol'), (partRule, 'rule')]:
            groups = subStr.split(self.CLOSE)
            for double in groups:
                if self.OPEN not in double: continue
                try:
                    key, value = double.split(self.OPEN)
                except: # possible syntax error in formationi
                    raise error.TransitionSyntaxError, "badly placed delimiters"
    
                # key is always a symbol def: will change case and remove spaces
                key = drawer.strScrub(key, 'lower', [' ']) # rm spaces from key
    
                # split into 2 dictionaries, one w/ symbol defs, one w/ rules
                # symbol defs must come before 
                if dst == 'symbol':
                    self._checkSymbolFormDef(key) # will raise exception on bad key
                    pairSymbol[key] = drawer.strScrub(value, None, [' ']) 
                elif dst == 'rule':  
                    self._checkSymbolFormRuleKey(key)
                    pairRule[key] = drawer.strScrub(value, 'lower', [' ']) 


        # this initializes symbol table
        if pairSymbol == {}:
            raise error.TransitionSyntaxError, "no symbols defined"
        self._symbols = pairSymbol
        # pass the pair dictionary to weight parser
        if pairRule == {}:
            raise error.TransitionSyntaxError, "no rules defined"
        self._parseRuleValue(pairRule) # assigns to self._rules
        
        # check symbol usage and determine orders
        self._checkRuleReference()
        #self._checkSymbolUsage()
        

    #------------------------------------------------------------------------||--         
    def _valueToSymbol(self, value):
        """for a data value, return the defined symbol label"""
        for s, v in self._symbols.items():
            if value == v: return s
        raise ValueError, 'value not known as symbol'
            
    def _valueListToSymbolList(self, valueList):
        """given a list of values (taken from an previous generated values)
        convert all the values to the proper symbols, and return as a tuple"""
        if len(valueList) == 0:
            return () # return an empty tuple
        msg = []
        for v in valueList:
            msg.append(self._valueToSymbol(v))
        return tuple(msg)
        

    #------------------------------------------------------------------------||--
    def repr(self):
        """provide a complete grammar string"""
        # do symbol list first
#         msg = []
#         syms = self._sortSymbolLabel(self._symbols.items())
#         for s, data in syms:
#             msg.append('%s%s%s%s' % (s, self.OPEN, data, self.CLOSE))
#         # determin where to get weight keys, from src or post
#         # Get a list of all defined keys
#         # sort transition keys, or weight labels
#         trans = self._sortWeightKey(self._weightSrc)
#         for t in trans:
#             wList = self._weightSrc[t]
#             #if wList == None: continue # this should not happen...
#             tStr = self._reprWeightLabelKey(t)
#             msg.append('%s%s%s%s' % (tStr, self.OPEN, self._reprWeightList(wList),
#                                               self.CLOSE))
#         return ''.join(msg)
        return ''

    def __str__(self):
        print self._symbols
        print self._rules
        return self.repr()
        


    #------------------------------------------------------------------------||--
    def load(self, usrStr):
        """load a transition string"""
        self._srcStr = usrStr
        self._parse(self._srcStr)






#-----------------------------------------------------------------||||||||||||--
class TestOld:

    def __init__(self):
        self.testParse()
        #self.testAnalysis()

        
    def testParse(self):

        import rhythm
        timer = rhythm.Timer() # get a timer to test time
    
        testA = "a{x} b{y} c{z} @ a{a:b} c{b:b|a:a}"
        # this defines the same rule more than once; combine?
        testB = "a{x} b{y} c{z} @ a{a:b} c{b:b|a:a} c{a:a:a=3|b:b:b=3}"
        testC = "a{x} b{y} c{z} @ a{a:b=23} c{b:b=3}" # these have redundant assig
        
        for test in [testA, testB, testC]:
            a = Grammar()
            print test
            a.load(test)
            print a._symbols
            print a._rules
            print



        print '\ntotal time %s' % timer('sw')



