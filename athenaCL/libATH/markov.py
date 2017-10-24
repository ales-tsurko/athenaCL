#-----------------------------------------------------------------||||||||||||--
# Name:          markov.py
# Purpose:       markov tools
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2005-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import string, random
import unittest, doctest

from athenaCL.libATH import permutate
from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import unit
from athenaCL.libATH import error

_MOD = 'markov.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)


# string just for string.ascii_lowercase

# Markov chains:
#     probabilities of events;
#     0-order: dont look at any previous values
#     1-order: one previous values looked at
#     
# difference beween transition table and markov
#     more than first order may not be a markov chain
# transition networks; probability tables
# some grammars are first order markov tables
#     which chomsky grammar; 2?
# 
# unconditional probabilities
# zero order markov: zero pervious values
#     designed: specify
#     or from analysis
# act: 'make unconditional table'
#     (this .4) (that .6)
#     can also give a large list of vlaues
# stpewise sum probability:
#     roulette wheel selection
#     divide a line segment into proportion; then select w/ unifrom distribution
# conditional proabilities; based on one or more coniditional probablities
#     a{x} b{y} c{z} :{a=3 b=.03 c=5}
#     a{a=1 b=5 c=4} b{a=2 b=2 c=6} c{a=3 b=1 c=9}
#     a:b{a=3 b=2} a:c:b{a=1}
    
# see markov in help.py for complete details on notation
    
#-----------------------------------------------------------------||||||||||||--


class Transition:

    def __init__(self):
        """
        >>> a = Transition()
        """
        self._srcStr = ''
        # a dictionary of alphabetic symbols and their assoicated values
        self._symbols = {}
        self._ordersSrc = [] # a list of all orders represented, as ints
        # a dict of alphabetic symbols and a weight
        # symbols are in a list according to transition
        # order ['a'] or ['a', 'b']
        # stores incomplete representation, w/ user provided weights
        # may be empty if weights achieved by analysis
        self._weightSrc = {} 

        self.OPEN = '{'
        self.CLOSE = '}'
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

    #-----------------------------------------------------------------------||--
    def _sortWeightKey(self, dict):
        """sort transition keys by size first"""
        keys = list(dict.keys())
        keys.sort()
        # sort keys by length
        ord = []
        for i in range(0, self._ordersSrc[-1]+1):
            for key in keys:
                if len(key) == i:
                    ord.append(key)
        return ord
        
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
  
    #-----------------------------------------------------------------------||--
    def _parseValidate(self, usrStr):
        """make sure the the string appears correct"""
        if usrStr.count(self.OPEN) != usrStr.count(self.CLOSE):
            raise error.TransitionSyntaxError("all braces not paired")

    def _parseWeightKey(self, key):
        """ make key into a list of symbol strings
        store expression weight keys in a tuple, with operator leading, as a sub 
        tuple. only one operator is allowed, must be tuple b/c will be a dict key

        >>> a = Transition()
        >>> a._parseWeightKey('a:b:c')
        ('a', 'b', 'c')
        >>> a._parseWeightKey('a:b:c|d')
        ('a', 'b', ('|', 'c', 'd'))
        >>> a._parseWeightKey('a:b:c|d|e')
        ('a', 'b', ('|', 'c', 'd', 'e'))
        >>> a._parseWeightKey('a:*:c')
        ('a', ('*',), 'c')
        >>> a._parseWeightKey('a:*:-c')
        ('a', ('*',), ('-', 'c'))
        """

        # make key into a list of symbol strings
        # if key is self.STEP, assign as empty tuple
        if key == self.STEP: return ()
        key = tuple(key.split(self.STEP)) # always split by step delim
        # filter empty strings
        keyPost = [] 
        for element in key:
            if element == '': continue
            keyPost.append(element.strip())
        key = keyPost
        # check for expressions in each segment of key
        keyFinal = []
        for segment in key:
            keyPost = []
            for exp in self.EXPRESS:
                if exp in segment:
                    keyPost.append(exp)
            if len(keyPost) == 0: # no expressions used, a normal weight key
                keyFinal.append(segment) # make it a tuple before return
            elif len(keyPost) > 1:
                msg = "only one operator may be used per weight key segment"
                raise error.TransitionSyntaxError(msg)
            # definitial an expression, pack new tuple, leading with expression op
            # if it is an or sym, need to split by this symbol
            else:
                if self.EXPRESSOR in segment:
                    opperands = segment.split(self.EXPRESSOR)
                    segmentPost = [self.EXPRESSOR] + opperands
                    keyFinal.append(tuple(segmentPost))
                else: # key post already has expression operator leading
                    for val in segment:
                        if val in self.EXPRESS: continue 
                        keyPost.append(val)
                    keyFinal.append(tuple(keyPost))
        return tuple(keyFinal)

    def _parseWeightValue(self, pairWeight):
        """read a complete dictionary of transition keys and weights, 
        and load weights as a list"""
        self._weightSrc = {} 
        for key, value in list(pairWeight.items()):
            # make key into a list of symbol strings
            key = self._parseWeightKey(key)
            # make value into a list of pairs
            weights = value.split(self.ASSIGNDELIMIT)
            weightList = []
            for assign in weights:
                if self.ASSIGN not in assign: continue
                if assign.count(self.ASSIGN) > 1: # bad syntax or other error
                    raise error.TransitionSyntaxError("incorrect weight specification: %s" % assign)
                symbol, w = assign.split(self.ASSIGN)
                # convert to float or int, may not be less tn zero
                # will return None on error
                w = drawer.strToNum(w, 'num', 0, None)
                # it woudl be nice to accept zero weights but this causes many
                # side-effects; need to test in whole
                # not defining all weights is permitted
                if w in (None, 0): # no zero weights, or other errors
                    raise error.TransitionSyntaxError("bad weight value given: %s" % assign)
                weightList.append((symbol, w))
            # assign to weight src
            self._weightSrc[key] = weightList 

    def _checkSymbolUsage(self):
        """check to see if all symbols used in weight keys are in symbol list
        also update orders; this fills _ordersSrc"""
        symbols = list(self._symbols.keys())
        for key in list(self._weightSrc.keys()):
            ord = len(key) # a zero key will be an empty tuple
            if ord not in self._ordersSrc: 
                self._ordersSrc.append(ord) # len of weight label is order
            # check symbols used in each weight
            weights = self._weightSrc[key]
            for w in weights:
                # weights are always symbol, number pairs
                if w[0] not in symbols:
                    raise error.TransitionSyntaxError("weight specified for undefined symbol: %s" % w[0])
        # sort order list             
        self._ordersSrc.sort()
                
    def _checkSymbolFormDef(self, symStr):
        """makes sure that symbol usage is valid for symbol definitions
        symbols cannot have spaces, case, or strange characters"""
        for char in symStr:
            if char not in self.SYM:
                raise error.TransitionSyntaxError("symbol definition uses illegal characters (%s)" % char)

    def _checkSymbolFormWeightKey(self, symStr):
        """makes sure that symbol usage is valid for weight label keys
        permits expression characters"""
        valid = self.SYM + self.STEP + ''.join(self.EXPRESS)
        for char in symStr:
            if char not in valid:
                raise error.TransitionSyntaxError("symbol definition uses illegal characters (%s)" % char)
                
    def _parseClean(self, usrStr):
        """remove any unusual characters that migth appear"""
        # may be quoted as a string
        for char in ['"', "'"]:
            usrStr = usrStr.replace(char, '')
        return usrStr
    
    def _parse(self, usrStr):
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
        
        # note: this will remove all spaces in all keys and all values

        self._parseValidate(usrStr)
        usrStr = self._parseClean(usrStr)
        
        pairSymbol = {}
        pairWeight = {}
        groups = usrStr.split(self.CLOSE)
        for double in groups:
            if self.OPEN not in double: continue
            try:
                key, value = double.split(self.OPEN)
            except: # possible syntax error in formationi
                raise error.TransitionSyntaxError("badly placed delimiters")
            # key is always a symbol def: will change case and remove spaces
            key = drawer.strScrub(key, 'lower', [' ']) # rm spaces from key
            # split into 2 dictionaries, one w/ symbol defs, one w/ weights
            # if it is or has a step indicator (:), it is not a def
            if self.STEP in key or self.ASSIGN in value: # it is a weight
                # store weights values in lower
                self._checkSymbolFormWeightKey(key)
                pairWeight[key] = drawer.strScrub(value, 'lower', [' ']) 
            else: # must be a symbol def
                self._checkSymbolFormDef(key) # will raise exception on bad key
                pairSymbol[key] = drawer.strScrub(value, None, [' ']) 
        # this initializes symbol table
        if pairSymbol == {}:
            raise error.TransitionSyntaxError("no symbols defined")
        self._symbols = pairSymbol
        # pass the pair dictionary to weight parser
        if pairWeight == {}:
            raise error.TransitionSyntaxError("no weights defined")
        self._parseWeightValue(pairWeight)
        # check symbol usage and determine orders
        self._checkSymbolUsage()
        

    #-----------------------------------------------------------------------||--         
    def _valueToSymbol(self, value):
        """for a data value, return the defined symbol label"""
        for s, v in list(self._symbols.items()):
            if value == v: return s
        raise ValueError('value not known as Transition symbol')
            
    def _valueListToSymbolList(self, valueList):
        """given a list of values (taken from an previous generated values)
        convert all the values to the proper symbols, and return as a tuple"""
        if len(valueList) == 0:
            return () # return an empty tuple
        msg = []
        for v in valueList:
            msg.append(self._valueToSymbol(v))
        return tuple(msg)
        
    #-----------------------------------------------------------------------||--         
    # methods for analysis
    
    def _analyzeZero(self, data):
        """assumes symbols are defined"""
        self._weightSrc[()] = [] # key is empty tuple
        for sym in list(self._symbols.keys()):
            value = self._symbols[sym]
            self._weightSrc[()].append((sym, data.count(value)))
            
    def _updateWeightList(self, wList, dstSym, count=1):
        """used to update a src wList; dstSym is symbol to be used
        should update weight list in place"""
        found = 0
        for i in range(len(wList)):
            s, w = wList[i]
            if s == dstSym:
                w = w + count # increment the weight
                wList[i] = (s, w) # restore the modified value
                found = 1
        # if not already present, add an entry to list
        if not found:
            wList.append((dstSym, count))
        #return wList
        
    def _analyzeNth(self, srcData, order, wrap=0):
        """do 1 or more order analysis on data list
        optional wrapping determines if wrap start value from end
        not sure what to do if no connections are found: is this a dead end, 
        or should it be treated as an equal distribution (this is the default
        behaviour here..."""
        # get all symbol key combinations
        assert order >= 1
        
        data = srcData[:] # make a copy to work on 
        # if wrap is selected, append order# of begining to end
        if wrap:
            data = data + data[:order]            
            
        symbols = list(self._symbols.keys())
        trans = permutate.selections(symbols, order)              
        # go through all transition possibilities for this order          
        for t in trans: 
            # must convert to tuple
            #print _MOD, 'searching transition', t
            t = tuple(t)
            # every transition key has a list of weights defined initially
            # this will be removed below if no matches found
            self._weightSrc[t] = []
            # decode the transition key into the desired real sequence
            # this will be done for each possible transition
            subList = []
            for s in t: # for each symbol label specified in the transition
                subList.append(self._symbols[s])
            # for each transition possible, 
            # go through all adjacent segments of source data and compare
            for i in range(0, len(data)):
                # need one more than order, as that is what we compare to
                if i + order >= len(data): break
                dataSeg = data[i:i+order]
                assert len(dataSeg) == len(subList) # shuold always be the same
                if dataSeg == subList: # match a segment, must update weights
                    dst = data[i+order] # next value after segment
                    # get sym label for teh dst data value
                    dstSym = self._valueToSymbol(dst)
                    #print _MOD, 'matched, dst', dataSeg, dst
                    self._updateWeightList(self._weightSrc[t], dstSym)
                    #self._weightSrc[t] = wList
            # check for an empty weight string
            if len(self._weightSrc[t]) == 0:
                # not sure what to do: delete it?
                # this is a dead end and cannot be used to generate...
                del self._weightSrc[t]

    def _analyze(self, data, order):
        """given an ordered list, do analysis
        will do all orders from zero up to the order specified
        will always do a zero order analsys"""
        # order should not be greater than the length of the data
        if order >= len(data):
            order = len(data) - 1
        # first find all unique symbols
        symList = []
        for q in data:
            if q not in symList:
                symList.append(q)
        # get labels alpha labels
        labelList = drawer.genAlphaLabel(len(symList))
        # generate proper symbol table
        self._symbols = {}
        for i in range(len(symList)):
            self._symbols[labelList[i]] = symList[i]
        # do zero order
        self._analyzeZero(data)
        # do nth
        for i in range(1, order+1):
            # args are data, order and wrap
            self._analyzeNth(data, i, 1)
        
    def _analyzeStr(self, data, order=0, delimit='', omit=[], include=[]):
        """given data as a string; will break into units
        by delimiter. omit is a list of characters that will be removed
        from consideration; order is max order to look at
        this will destructively fill symbol data; not to be used w/ parse
        include will remove and function as independent elements
        """
        series = []
        # always omit the delimiters from strings
        for extra in [self.OPEN, self.CLOSE]:
            if extra not in omit:
                omit.append(extra)
                
        for char in omit: # replace w/ delimit
            data = data.replace(char, delimit) 
        for char in include:
            if char in data: # replace w/ delimited pad
                data = data.replace(char, '%s%s%s' % (delimit, char, delimit))
        preSeries = data.split(delimit)
        # remove empty elements
        for q in preSeries:
            if q == '': continue
            series.append(q)

        #will fill _weightSrc; can use auto methods to balance
        self._analyze(series, order)
        self._checkSymbolUsage()

    def _analyzeList(self, data, order):
        self._analyze(data, order)
        self._checkSymbolUsage()


    #-----------------------------------------------------------------------||--         
    def _reprWeightList(self, wList):
        """format a weight list for presentation"""
        # wList can be none:
        if wList == None: return None
        wStr = []
        wList = self._sortSymbolLabel(wList)
        for s, w in wList:
            if w == 0: continue # skip zero weights
            wStr.append('%s%s%s' % (s, self.ASSIGN, typeset.anyDataToStr(w)))
        return self.ASSIGNDELIMIT.join(wStr)
        
    def _reprWeightLabelKey(self, raw):
        """provide a string representation of a weight label
        expressionis may be used and must be handled separately"""
        msg = []
        for element in raw:
            if drawer.isList(element): # its an expression
                if element[0] == self.EXPRESSOR:
                    elementStr = self.EXPRESSOR.join(element[1:])
                elif element[0] == self.EXPRESSNOT:
                    elementStr = '%s%s' % (self.EXPRESSNOT, element[1])
                else: # must be self.EXPRESSALL
                    elementStr = self.EXPRESSALL
                msg.append(elementStr)
            else:
                msg.append(element)
        # join w/ step symbol
        msg = self.STEP.join(msg)
        # always add one at end
        return '%s%s' % (msg, self.STEP)
        
    def _reprTransitionStr(self):
        """provide a complete transition string"""
        # do symbol list first
        msg = []
        syms = self._sortSymbolLabel(list(self._symbols.items()))
        for s, data in syms:
            msg.append('%s%s%s%s' % (s, self.OPEN, data, self.CLOSE))
        # determin where to get weight keys, from src or post
        # Get a list of all defined keys
        # sort transition keys, or weight labels
        trans = self._sortWeightKey(self._weightSrc)
        for t in trans:
            wList = self._weightSrc[t]
            #if wList == None: continue # this should not happen...
            tStr = self._reprWeightLabelKey(t)
            msg.append('%s%s%s%s' % (tStr, self.OPEN, self._reprWeightList(wList),
                                             self.CLOSE))
        return ''.join(msg)
        
    def repr(self, format=None):
        return self._reprTransitionStr()

    def __str__(self):
        return self.repr()
        
            
        
    #-----------------------------------------------------------------------||--
    def loadTransition(self, usrStr):
        """load a transition string

        >>> a = Transition()
        >>> a.loadTransition('a{234} b{12} :: {a=3|b=3}')
        """
        self._srcStr = usrStr
        self._parse(self._srcStr)
        
    def loadString(self, data, order):   
        """take a list of symbols and produce an analysis
        symbols cannot contain braces or equals signs

        >>> a = Transition()
        >>> a.loadString('abaaaccdaacaca', 2)
        """
        self._analyzeStr(data, order, ' ', ['\n', '-'])

    def loadFileText(self, filePath):
        f = open(filePath)
        data = f.read()
        f.close
        self._analyzeStr(data, order, ' ', ['\n', '-'])       

    def loadList(self, data, order):
        """will analuyze from 0 to order provided"""
        self._analyzeList(data, order)
        
    #-----------------------------------------------------------------------||--
    def getSignified(self):
        """return symbol values as a list; useful for checking type and quality
        of possible outptus"""
        return list(self._symbols.values())

    def getItems(self):
        """get key, value pairs from sybol dict"""
        return list(self._symbols.items())

    def getOrderMax(self):
        """get highest specified order values"""
        return self._ordersSrc[-1]
        

    #-----------------------------------------------------------------------||--

    def _findWeights(self, srcSeq):
        """given a src sequence, find a weight label that matches
        if not match is available, then return None (will result in 
        and qual distribution when srubbed)"""
        # for expression compat, need a method here to search weights
        # and determine of there is a direct match, or an expression match
        if srcSeq in self._weightSrc: # direct match
            return self._weightSrc[srcSeq]
        # if no key defined, search for matching expressions
        srcLen = len(srcSeq)
        for label in list(self._weightSrc.keys()):
            if len(label) != srcLen: continue # a def for a different order
            matchCount = 0
            for i in range(srcLen):
                # if both are symbol strings, will match
                if label[i] == srcSeq[i]:
                    matchCount = matchCount + 1
                elif drawer.isList(label[i]): # its an expression
                    if label[i][0] == self.EXPRESSALL: # match anything
                        matchCount = matchCount + 1
                    elif label[i][0] == self.EXPRESSNOT: 
                        if label[i][1] != srcSeq[i]: # not supplied operand
                            matchCount = matchCount + 1
                    elif label[i][0] == self.EXPRESSOR: 
                        if srcSeq[i] in label[i][1:]: # match any operands
                            matchCount = matchCount + 1
            if matchCount == srcLen:
                environment.printDebug(['exp match; label:', label, 'src:', srcSeq])
                return self._weightSrc[label]
        # return None if nothing found
        return None

    def _scrubWeights(self, wList):
        """given a list of weights, or none
        return two lists, ordered, for weight vals and symbol vals
        """
        # if an empty weight list is given, use an equal distribution
        # based onall known symbols
        if wList == None:         
            symbols = list(self._symbols.keys()) # order does not matter
            wPost = [1] * len(symbols)
            sDeclared = symbols[:]
        else:
            # wList.sort() # sorting not necessary here, as long as pair are orderd
            wPost = []
            sDeclared = []
            for sym, w in wList:
                sDeclared.append(sym)
                wPost.append(w)
        return wPost, sDeclared
        

    def next(self, unitVal, previous, order, slide=1):
        """generate the next value of the a new chain
        unitVal is floating point number b/n 0 and 1; can be generated
        by any distribution. this value determines the selection of values
        previous is a list of values that will be analaized
        if the list is insufficiant for the order, if slide, will use 
        next available order, otherwise, will use zero order
        order may be a float; if so it will use weighting from drawer
        """
        symbols = list(self._symbols.keys())
        # get appropriate order: if a float, will be dynamically allocated
        order = drawer.floatToInt(order, 'weight')
        if order not in list(range(0, self._ordersSrc[-1]+1)):
            order = self._ordersSrc[-1] # use highest defined
        #print _MOD, 'using order', order
        # get appropriate key of given length of previous
        prevLen = len(previous)
        if prevLen <= order: # if less then specified by order
            if slide: # use length as order
                srcSeq = self._valueListToSymbolList(previous)
            else: srcSeq = () # jump to zeroth
        else: # if values are greater in length than order
            if order == 0: srcSeq = ()
            else:                 
                srcSeq = self._valueListToSymbolList(previous[-order:])      
        # determine of there is a direct match, or an expression match
        wList = self._findWeights(srcSeq) # may return None
        # if none, will create equal distribution of all symbols
        # return parallel lists of weights, symbols, both in same order
        wPost, sDeclared = self._scrubWeights(wList)
        #print _MOD, 'order, wPost, sDeclared', order, wPost, sDeclared
        boundary = unit.unitBoundaryProportion(wPost)
        i = unit.unitBoundaryPos(unitVal, boundary)
        # get symbol, then de-signify symbols into the store value
        return self._symbols[sDeclared[i]]
        







#-----------------------------------------------------------------||||||||||||--

class TestOld:

    def __init__(self):
        self.testParse()
        #self.testAnalysis()
        
    def testParse(self):

        from . import rhythm
        timer = rhythm.Timer() # get a timer to test time
    
        testA = "a{x} b{y} c{z} :{a=3|b=.03|c=5} a:{a=1|b=5|c=4} b{a=2|b=2|c=6} c{a=3|b=1|c=9} a::b::{a=3|b=2} a:c:b{a=1}"
    
        testB = "a{234} b{12} :: {a=3|b=3}" # this is a syntax error, but accepted
    
        testC = "a{this} b{is} c{a string} d {short} :{a=3|b=3|c=3} a:b{c=2}"
    
        testD = "a{(9,3,1)}b{(3,1,1)}c{(3,2,1)}:{a=3|b=1|c=7|g}"

        testE = "a{234} b{12} :{a=3|b=3} a:*:{a=3|b=3}"

        testF = "a{a} b{b} c{c} :{a=3|b=3} a:a|b|c:{c=1}"

        testG = "a{a} b{b} c{c} :{a=3|b=3} *:-c:{c=1}"

        testH = "a{a} b{b} c{c} -a:{a=1} -b:{b=1} -c:{c=1}"

        testI = "a{a} b{b} c{c} a:*{a=1|c=1} b:*{b=1|c=1} c:c{a=1|b=1}"

        testJ = "a{a} b{b} c{c} a:c|b:a{c=1} b:c|a:b{a=1} c:-c:c{b=1}"
    
        for test in [testA, testB, testC, testD, testE, testF, testG, testH, 
                         testI, testJ]:
            a = Transition()
            a.loadTransition(test)
            print(a)
            for order in range(0,4):
                print('requested order:', order)
                msg = []
                for x in range(30):
                    val = random.random()
                    msg.append(a.next(val, msg, order))
                print(' '.join(msg))
            print()

        print('\ntotal time %s' % timer('sw'))



    def testAnalysis():

        from . import rhythm
        timer = rhythm.Timer() # get a timer to test time
            
        msgA = 'that this is a this that is a a this is that but not this that is a is a that this this that but that but this but is but not'      
            
        msgB = """
    Beautiful is better than ugly.
    Explicit is better than implicit.
    Simple is better than complex.
    Complex is better than complicated.
    Flat is better than nested.
    Sparse is better than dense.
    Readability counts.
    Special cases aren't special enough to break the rules.
    Although practicality beats purity.
    Errors should never pass silently.
    Unless explicitly silenced.
    In the face of ambiguity, refuse the temptation to guess.
    There should be one-- and preferably only one --obvious way to do it.
    Although that way may not be obvious at first unless you're Dutch.
    Now is better than never.
    Although never is often better than *right* now.
    If the implementation is hard to explain, it's a bad idea.
    If the implementation is easy to explain, it may be a good idea.
    Namespaces are one honking great idea -- let's do more of those!     
        """
            
        msgC = """To be, or not to be- that is the question:
         Whether 'tis nobler in the mind to suffer
         The slings and arrows of outrageous fortune
         Or to take arms against a sea of troubles,
         And by opposing end them. To die- to sleep-
         No more; and by a sleep to say we end
         The heartache, and the thousand natural shocks
         That flesh is heir to. 'Tis a consummation 
         Devoutly to be wish'd. To die- to sleep.
         To sleep- perchance to dream: ay, there's the rub!
         For in that sleep of death what dreams may come
         When we have shuffled off this mortal coil,
         Must give us pause. There's the respect
         That makes calamity of so long life.
         For who would bear the whips and scorns of time,
         Th' oppressor's wrong, the proud man's contumely,
         The pangs of despis'd love, the law's delay,
         The insolence of office, and the spurns
         That patient merit of th' unworthy takes,
         When he himself might his quietus make
         With a bare bodkin? Who would these fardels bear,
         To grunt and sweat under a weary life,
         But that the dread of something after death-
         The undiscover'd country, from whose bourn
         No traveller returns- puzzles the will,
         And makes us rather bear those ills we have
         Than fly to others that we know not of?
         Thus conscience does make cowards of us all,  
         And thus the native hue of resolution
         Is sicklied o'er with the pale cast of thought,
         And enterprises of great pith and moment
         With this regard their currents turn awry
         And lose the name of action.- Soft you now!
         The fair Ophelia!- Nymph, in thy orisons
         Be all my sins rememb'red."""
        
        
        for test in [msgA, msgB, msgC]:
            a = Transition()
            max = 2
            a.loadString(test, max)
            print(a)
            for order in range(0,max+1):
                print('requested order: (w/ random upward variation)', order)
                msg = []
                for x in range(120):
                    postOrder = order + random.random()
                    val = random.random()
                    msg.append(a.next(val, msg, postOrder))
                print(' '.join(msg))
                print()
            
            
        print('\ntotal time %s' % timer('sw'))



#-----------------------------------------------------------------||||||||||||--


class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


    def testParse(self):
        '''Note testing output; just looking for potential errors
        '''
    
        testA = "a{x} b{y} c{z} :{a=3|b=.03|c=5} a:{a=1|b=5|c=4} b{a=2|b=2|c=6} c{a=3|b=1|c=9} a::b::{a=3|b=2} a:c:b{a=1}"
    
        testB = "a{234} b{12} :: {a=3|b=3}" # this is a syntax error, but accepted
    
        testC = "a{this} b{is} c{a string} d {short} :{a=3|b=3|c=3} a:b{c=2}"
    
        testD = "a{(9,3,1)}b{(3,1,1)}c{(3,2,1)}:{a=3|b=1|c=7|g}"

        testE = "a{234} b{12} :{a=3|b=3} a:*:{a=3|b=3}"

        testF = "a{a} b{b} c{c} :{a=3|b=3} a:a|b|c:{c=1}"

        testG = "a{a} b{b} c{c} :{a=3|b=3} *:-c:{c=1}"

        testH = "a{a} b{b} c{c} -a:{a=1} -b:{b=1} -c:{c=1}"

        testI = "a{a} b{b} c{c} a:*{a=1|c=1} b:*{b=1|c=1} c:c{a=1|b=1}"

        testJ = "a{a} b{b} c{c} a:c|b:a{c=1} b:c|a:b{a=1} c:-c:c{b=1}"
    
        for test in [testA, testB, testC, testD, testE, testF, testG, testH, 
                         testI, testJ]:
            a = Transition()
            a.loadTransition(test)
            for order in range(0,4):
                msg = []
                for x in range(30):
                    val = random.random()
                    a.next(val, msg, order)




#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)

