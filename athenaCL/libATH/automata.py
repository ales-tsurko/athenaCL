#-----------------------------------------------------------------||||||||||||--
# Name:          automata.py
# Purpose:       Cellular Automata objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2005-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import os, random, array, copy

from athenaCL.libATH import drawer
from athenaCL.libATH import unit
from athenaCL.libATH import error
from athenaCL.libATH import table
from athenaCL.libATH import typeset
from athenaCL.libATH import permutate

# decimal may be used to get accurate continuous ca
# this increase computation time considerably
try: 
    import decimal # only w/ python 2.4
    DECIMAL = 1
except ImportError:
    DECIMAL = 0

# in some cases turn off to increase performance
# DECIMAL = 0

_MOD = 'automata.py'


#-----------------------------------------------------------------||||||||||||--


# repition: 250
# nesting: 22, 60, 90, 105, 129, 150, 225
# randomness: (10 total) 30, 45, 73
# local structures: 110

# for 1d totalistic rules. 0-2186:
# >>> automata.ruleGen(777, 1, [0,1,2], [0,1,2,3,4,5,6])
# [(0, 0), (1, 1), (2, 2), (3, 1), (4, 0), (5, 0), (6, 1)]

# rules for totalistic:
# 1086, 90 177 912 2040

# long stringy things
# 600 843 870 1086 1167 1329 1572 1815 1842
# :: auca f{t}x{81}y{80}k{3}r{1} 1086 bpl,e,l,((0,0),(80,.02))
# :: auca f{t}x{81}y{80}k{3}r{1} 1167 bpl,e,l,((0,0),(80,.02))

# totalistic rules tt have nested patterns tt go forever
# 219 957 966 1884 237 420 948 1749
# :: auca f{t}x{81}y{80}k{4}r{1} 1884 bpl,e,l,((0,0),(80,.01))
# :: auca f{t}x{81}y{80}k{3}r{1} 1884 bpl,e,l,((0,0),(80,.02))
# :: auca f{t}x{81}y{80}k{3}r{1} 420 bpl,e,l,((0,0),(40,.001),(80,0))

# totalistic rules tt produce randomness:
# 177 912 2040

# tr rules tt produce complex mixed behavior
# 1041 1635 2049 1635

# totalistic w/ 4 values, looking at 3 previous values k4r1
# example of a such a ca on p754 nks
# a = automata.TotalisticQuad(201,1004600,[0]*99+[1,1]+[0]*99)


# :: auca f{t}y{80}x{81}r{1}k{4}i{r}s{0} 1004600 0
# string things; terminates from single start

# :: auca f{t}y{80}x{81}r{1}k{4}i{r}s{0} 195735784 0
# complex, divers colors, dark background

# :: auca f{t}y{80}x{81}r{1}k{4}i{c}s{0} 554761 0
# complex symmetrical

# :: auca f{t}y{80}x{81}r{1}k{4}i{r}s{0} 10000845 0
# mostly simple pattern from single; complx from random

# :: auca f{t}y{80}x{81}r{1}k{4}i{r}s{0} 846484 0
# from center boring, but from random, interesting laced shapes

# :: auca f{t}y{80}x{81}r{2}k{6}i{c} 1806 0
# nested serpinksy
# :: auca f{t}y{80}x{81}r{2}k{6}i{c} 98123 0
# pattern
# :: auca f{t}y{80}x{81}r{2}k{6}i{c} 1983570 0
# complex nested
# :: auca f{t}y{80}x{81}r{2}k{6}i{c} 84251500514 0
# complex but symmetrical
# :: auca f{t}y{80}x{81}r{2}k{6}i{c} 66448723 0
# complex symmetrical

# combined:
# :: auca f{t}y{80}x{81}r{2}k{6}i{r}s{20} mv,a{1806}b{84251500514}c{98123}:{a=8|b=5|c=2},(c,0) 0.01


# s.k2.r1.rule=73.m0.01  -- potentially useful for rhythm generation
# s.k2.r1.rule=109.m0 -- started from random gives cyclic patterns
# s.k2.r1.rule=133.m0.01 - also good for rhythm from random start

# s.k4.r1.rule=136920680033006148807870461902105273178.m0.01 - noise
# s.k4.r1.rule=136920680033006148807870461902105273184.m0 - local struct
# s.k4.r1.rule=136920680033006148807870461902105273244.m0 - mixed
# s.k4.r1.rule=136920680033006148807870461902105273290.m0 - mixed
# s.k4.r1.rule=136920680033006148807870461902105273308.m0 - mixed
# s.k4.r1.rule=136920680033006148807870461902105273322.m.005 - pattern


# s.k2.r2.rule=10134.m0 - interesting edge pattern    
# s.k2.r2.rule=10156.m0 - nested triangles rotated slightly
# s.k2.r2.rule=500144.m0 - nested rotated
# s.k2.r2.rule=500148.m0 - diagonal, possibly nested
# s.k2.r2.rule=3070153.m0 - edge activity
# s.k2.r2.rule=55020952.m0 - mixed
# s.k2.r2.rule=55020953.m0 - mixed, complex, stringy

# standard CA: k=3 r=1 rule=235 mutation=0.1 init=random ; r-angle line paterns


# auca f{t}y{80}x{81}r{2}k{6}i{r} mv,a{1806}b{84251500514}c{98123}:{a=80|b=3|c=1},(c,0) 0.01

# t.k2.r1.rule2.m0.001
# t.k2.r1.rule5.m0.001
#       mutation adds some behavior
# t.k4.r1.rule502.m0.001        
#       double triangle, down; with mutation this is more interesting
# t.k4.r1.rule505.m0.001    
#       simple triangles, mutation does not add taht much
# t.k4.r1.rule509.m0.001
#       traingle, nested
# t.k4.r1.rule514.m0.001
#       triangles, but nested with lines

# t.k6.r1.rule=1083234423495.m0
#       a cmplex, bizarre but symmetrical shape


# con.k2.r1.rule=0.08.m0.001
#       a nice tree-like shape
# con.k2.r1.rule=0.4.m0.001
#       w/o mutation, a plain triangle
# con.k2.r1.rule=0.48  .m0.001
#       nice, interlaced pattern
#       strong difference b/n float and decimal
# con.k2.r1.rule=0.56.m0.001
#       pyramid shape
# con.k2.r1.rule=0.031.m0.001
#       smooth gradiant, slow change
#       cannot quickly distinguish float/decimal
# con.k2.r1.rule=0.0073.m0.001
#       just dispersion w/o noise
# con.k2.r1.rule=0.0657.m0.001
#       tree like over faded background, no imeed float/decima diff

# con.k2.r2.rule=0.248.m0.001
#       linear pattern
# con.k2.r2.rule=0.093.m0.001
#       lacy tree, cannot distinguish float/decimal
# con.k2.r2.rule=0.031.m0.001
#       very smooth gradiant w/ activity, cannot distinguish float/decimal
# con.k2.r2.rule=0.093.m1e-08
#       lacy tree


# con.k2.r2.rule=0.001.m0.1 -- a cloudy, patchy field
# con.k2.r2.rule=0.001.m0.05    -- a cloudy, patchy field
# con.k2.r2.rule=0.005.m0.05    -- a cloudy, patchy field
#       w/o noise thise produce simple fades
# :: auca f{c}x{81}y{80}r{2} .01 bpl,e,l,((0,0),(80,.1))



#-----------------------------------------------------------------||||||||||||--

def caFormatParser(usrStr):
    ref = {
        's' : ['s', 'standard'],
        't' : ['t', 'tot', 'totalistic'],
        'c' : ['c', 'continuous'],
        'f' : ['f', 'float'],
            }
    usrStr = drawer.selectionParse(usrStr, ref)
    return usrStr # may be Non


def caInitParser(usrStr):
    usrNum, junk = drawer.strExtractNum(usrStr)
    if (len(usrNum) == len(usrStr) or drawer.isNum(usrStr) or
        drawer.isList(usrStr)):
        return usrStr # not a string, a data obj
    # only parse if a string
    ref = {
        'center' : ['c', 'center'],
        'random' : ['r', 'random'],
            }
    usrStr = drawer.selectionParse(usrStr, ref)
    return usrStr # may be Non

    
    
class AutomataSpecification:
    """object to mange arguments for automata"""

    def __init__(self, usrStr):
    
        self.OPEN = '{'
        self.CLOSE = '}'
        
        self.src = self._loadDictionary(usrStr)
        self.src = self._updateDefault(self.src)
        self.src = self._updateRational(self.src)
    
    def _keyParser(self, usrStr):
        if drawer.isNum(usrStr) or drawer.isList(usrStr):
            return usrStr # not a string, a data obj
        # only parse if a string
        
        # may need to add: 'd' for dimension
        # 'z' for z axis?
        ref = {
            'f' : ['f', 'format', 'form', 'type'],
            'k' : ['k', 'colors'],
            'r' : ['r', 'radius'],
            'i' : ['i', 'init', 'initial'],
            'x' : ['x', 'size'],
            'y' : ['y', 'steps', 'gen'],
            'w' : ['w', 'width'],
            'c' : ['c', 'center'],
            's' : ['s', 'skip'],

                }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr # may be None

    def get(self, key):
        if key == 'yTotal': # y with skip, for actual generations
            return self.src['y'] + self.src['s']
        elif key in self.src.keys():
            return self.src[key]
        else: raise AttributeError

    def repr(self, fmt='full'):
        if fmt == 'line': # split into multiple lines
            return 'f{%s}k{%s}r{%s}\ni{%s}\nx{%s}y{%s}\nw{%s}c{%s}s{%s}' % (
            self.src['f'], self.src['k'], self.src['r'], self.src['i'],
            self.src['x'], self.src['y'], self.src['w'], self.src['c'],
            self.src['s'])        
        else:
            return 'f{%s}k{%s}r{%s}i{%s}x{%s}y{%s}w{%s}c{%s}s{%s}' % (
            self.src['f'], self.src['k'], self.src['r'], self.src['i'],
            self.src['x'], self.src['y'], self.src['w'], self.src['c'],
            self.src['s'])
        
    def __str__(self):
        return self.repr()
    
    def _loadDictionary(self, usrStr):
        """this model is borrowed from markov.py; could be abstracted to
        a common utility"""
        if usrStr.count(self.OPEN) != usrStr.count(self.CLOSE):
            raise error.AutomataSpecificationError, "all braces not paired"     
        post = {}
        groups = usrStr.split(self.CLOSE)
        for double in groups:
            if self.OPEN not in double: continue
            key, value = double.split(self.OPEN)
            key = self._keyParser(key)
            if key == None: continue
            post[key] = value
        return post
    
    def _updateDefault(self, src):
        """make a ca dictionary
        rule and mutation are left out, as dynamic"""
        xMAX = 1000
        yMAX = 10000
        ref = { # these are the limits
            'f' : ('s',), # must be first element of a list
            'k' : (2, 0, 36), # def, min, max
            'r' : (1, .5, 10),
            'i' : ('center',),
            'x' : (91, 1, xMAX), # should be odd value
            'y' : (135, 1, yMAX),
            'w' : (0, 0, yMAX), # will get value of 
            'c' : (0, -xMAX, xMAX), # center
            's' : (0, 0, yMAX), # skip
                }
        
        # src keys have already been formated to single character refs
        for key in ref.keys():
            if key not in src.keys():
                src[key] = ref[key][0]
            else: # keu exists, eval numbers if necessary
                if drawer.isNum(ref[key][0]): # check numbers                           
                    min = ref[key][1]
                    max = ref[key][2]
                    # permit r values w/ decimal .5
                    if key =='r' and '.' in src[key]:
                        # double, round, and divide; will be either 0 or .5
                        value = drawer.strToNum(src[key], 'float', min, max)
                        value = round(value*2) / 2
                    else:
                        value = drawer.strToNum(src[key], 'int', min, max)
                    if value != None:
                        src[key] = value
                    else: # cant resolve value, provide default
                        src[key] = ref[key][0]
                if drawer.isStr(ref[key][0]): # check strings
                    if key == 'f':
                        value = caFormatParser(src[key])
                    elif key == 'i':
                        value = caInitParser(src[key])
                    if value != None:
                        src[key] = value
                    else:
                        src[key] = ref[key][0]      
        return src       
        

    def _updateRational(self, src):
        # do not add skip here, as this makes parameters args non-reversible!
#         if src['s'] > 0: # add skip to y to maintain size
#             src['y'] = src['y'] + src['s']
        if src['k'] <= 0:
            src['f'] = 'f' # make into a float
        if src['w'] <= 0: # width may be greater than x
            src['w'] = src['x']
        # set k if format continuous
        if src['f'] in ['c', 'f']:
            src['k'] = 0
        return src

#-----------------------------------------------------------------||||||||||||--
# rule translatino schemes
# the order of rules does not matter
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/343386

# http://www.schatten.info/info/ca/ca.html
# total rules == pow(k, pow(k, n))
# k is states, n number of neighbors including core (r*2+1)

# Since each cell ranges from 0 to 2, the total ranges from 0 to 6, or 7 
# possibilities. There are thus 3^7 or 2187 rules of this type

# there are 256 elementary rules for r=1, nks p53
# for k=3 r=1: 7625597484987 rules nks p60

# other ways of thinking about totalistic rule counts
# q is max value to be found in any single cell
# >>> k=2; r=1; q=k-1
# >>> pow(k,((r*2)+1)*q)
# 8
# >>> automata.ruleCount(((r*2)+1),range(k),(((r*2)+1)*(k-1)))
# 8
# >>> k=3; r=2; q=k-1
# >>> pow(k,((r*2)+1)*q)
# 59049
# >>> automata.ruleCount(((r*2)+1),range(k),(((r*2)+1)*(k-1)))
# 59049

#-----------------------------------------------------------------||||||||||||--
def ruleCount(srcSpan, dstValues, srcValues=None):
    # srcSpan == r*2+1, len(dstValues) == k
    # totalistic rule count: k = k, len(dstValues)
    if drawer.isNum(dstValues):
        k = dstValues
        dstValues = range(dstValues)
    else: # assume its a list
        k = len(dstValues)
    if srcValues == None: # not totalistic
        count = pow(k, pow(k, srcSpan))
    else: # totalistic, srcValues are provided
        if drawer.isNum(srcValues):
            q = srcValues
        else: # assume its a list
            q = len(srcValues)      
        count = pow(k, q)
    # print _MOD, 'rule count', count
    return count

def ruleGen(ruleNo, srcSpan=3, dstValues=[0,1], srcValues=None):
    """generate a rule in the form of a list; each entry in the list
    consists of a src list (the ordered values in the previous step to match
    and a destinatino value (the new cell value)
    k == number of cell values (len(dstValues))
    srcSpan is number of previous values considered (3 here is an r of 1)
    srcValues for totalistic rules, where src and dst are not the same
    """
    dstNo = len(dstValues) # number of possible cell values
    if srcValues == None: # non totalistic riles
        # get number of possible outcomes, or arrangemnts of src states
        srcMatches = permutate.selections(dstValues, srcSpan)
    # for totalistic rules, src values not from selections of possibility
    # byt given directly in a list
    else:
        srcValues.sort() # get from low to high, reverse of ws
        srcMatches = srcValues
    # gets next step array of values; note: these are reveresed from ws presentn
    ruleArray = [(ruleNo/pow(dstNo,i)) % dstNo for i in range(len(srcMatches))] 
    # bundle as pairs b/n src and dst
    r = [[srcMatches[x], ruleArray[x]] for x in range(len(srcMatches))]
    return r
    
    


#-----------------------------------------------------------------||||||||||||--
# base class for all discrete
class _Automaton:
    def __init__(self, size, rule=0, init=0, dstValues=None, 
                     srcSpan=3, srcValues=None, mutation=None):
        self.rule = rule # number, or string perhaps
        self.format = None # define in subclass
        self.dimension = None # define in subclass
        
        self.srcSpan = srcSpan # the number of previous values compared
        assert self.srcSpan % 2 == 1 # must be an odd number
        # value used to to determine index shift left of center
        # want floored /2 division here; should work for even number srcSpan
        self.srcSpanRuleShift = 0 - (self.srcSpan / 2)
        self.size = size # number of cells in one step       
        # may need to prase these values
        self.init = caInitParser(init)
        if self.init == None: raise ValueError, 'bad init value'
        if dstValues != None: # can be none for continuous ca
            dstValues.sort()
        self.dstValues = dstValues
        self.dstIndexCenter = -1 # index to be used for center init values
        
        if srcValues != None: # only used for continuous
            srcValues.sort()
        self.srcValues = srcValues

        if self.srcSpan % 2 == 0: # if even
            self.r = (self.srcSpan - 1) / 2.0 # must be a float
        else: # of odd, get an int
            self.r = (self.srcSpan - 1) / 2 
        # self.dstValues == None signifies a continuous
        if self.dstValues != None: self.k = len(self.dstValues)
        else: self.k = 0

        self.mutation = mutation # w/n unit interval
        self.stepHistory = [] # store steps as lists or arrays
        self.stepTemplate = [] # base structure to refresh
                
    def _getTemplate(self):
        return self.stepTemplate[:]
        
    def _fmtStepBi(self, msg):
        msg = msg.replace('0', ' ')
        msg = msg.replace('1', '+')
        return msg
        
    def _fmtStepTri(self, msg):
        msg = msg.replace('0', ' ')
        msg = msg.replace('1', '.')
        msg = msg.replace('2', '*')
        return msg

    def _fmtStepQuad(self, msg):
        msg = msg.replace('0', ' ')
        msg = msg.replace('1', '.')
        msg = msg.replace('2', '*')
        msg = msg.replace('3', '%')
        return msg

    def _fmtStepContinuous(self, msg):
        msg = msg.replace('0', ' ')
        msg = msg.replace('1', '.')
        msg = msg.replace('2', '-')
        msg = msg.replace('3', '~')
        msg = msg.replace('4', '^')
        msg = msg.replace('5', '+')
        msg = msg.replace('6', '*')
        msg = msg.replace('7', '%')
        msg = msg.replace('8', '#')
        msg = msg.replace('9', '@')
        return msg

    def _fmtContinuous(self, stepData):
        filter = array.array('B')
        for i in range(len(stepData)):
            # get past deciaml, shift forward, make into an int
            filter.append(int(round(stepData[i], 1) % 1.0 * 10))
        return filter
                
    def _fmtStep(self, stepData):
        # continuous, w/ decimal objects
        if self.dstValues == None and self.DECIMAL: 
            stepData = self._fmtContinuous(stepData)
            msg = drawer.listScrub(stepData)
        else: # an array
            if self.dstValues == None:
                stepData = self._fmtContinuous(stepData)
            msg = drawer.listScrub(stepData.tolist())         
        msg = msg.replace(',','')
        if self.dstValues == None:
            return self._fmtStepContinuous(msg)
        elif len(self.dstValues) == 2:
            return self._fmtStepBi(msg)
        elif len(self.dstValues) == 3:
            return self._fmtStepTri(msg)
        elif len(self.dstValues) == 4:
            return self._fmtStepQuad(msg)

    def repr(self, style=None):
        if style == 'brief':
            msg = 'f{%s}k{%s}r{%s}' % (self.format[0], self.k, self.r)
        elif style == 'line':
            msg = self.spec.repr(style)
        elif style == 'full':
            msg = '%s rule=%s mutation%s' % (msg, self.rule, self.mutation)
        else:
            if hasattr(self, 'spec'): # get full spec args
                msg = self.spec.repr()
            else:
                msg = 'f{%s}k{%s}r{%s}' % (self.format[0], self.k, self.r)
        # add current rule and mutation if full
        return msg
        
    def __repr__(self):
        return self.repr()




        
#-----------------------------------------------------------------||||||||||||--
# private class for one dimensional
class _AutomatonOneDimension(_Automaton):
    def __init__(self, size, rule=0, init=0, dstValues=[0,1], 
                     srcSpan=3, srcValues=None, mutation=None):
        _Automaton.__init__(self, size, rule, init, dstValues, 
                                             srcSpan, srcValues, mutation)
        self.dimension = 1 
        self.outFmt = ['table','flat', 'sum', 'average', 'product']

    def _refreshTemplate(self):
        # create a blank template based on size
        if self.dstValues != None: # discrete ca
            self.stepTemplate = array.array('B') # B is unsighed char, 0 to 255
            for x in range(self.size):
                self.stepTemplate.append(self.dstValues[0]) # refresh w/ first value
        else: # a continuous ca
            if self.DECIMAL:
                self.stepTemplate = [] # ues an ordinary list
            else:
                self.stepTemplate = array.array('d') # d is a double float
            for x in range(self.size):
                if self.DECIMAL: val = decimal.Decimal(0)
                else: val = 0.0
                self.stepTemplate.append(val) # refresh w/ first value

    def _getCenter(self):
        """get center""" # size here is no of colums
        # index values are one less, so no need to add extra 1 for center
        # // operator, since python 2.2, will fource integer floor ops
        return self.size//2 # let floor

    def clear(self):
        """processes init value and replaces history with first generation
        will always add an init to the history, meaning that there will always
        be one more generation than expected in most cases"""
        stepInit = self._getTemplate()
        if drawer.isStr(self.init):
            numStr, junk = drawer.strExtractNum(self.init)
            if self.init == 'center':
                centerIndex = self._getCenter()
                if self.dstValues == None: # continuous case
                    if self.DECIMAL: val = decimal.Decimal(1)
                    else: val = 1.0
                    # should add one here, but need -1 for list position shift
                    stepInit[self._getCenter()] = val 
                else: # center value is dependent; must provude as variable
                    stepInit[self._getCenter()] = self.dstValues[self.dstIndexCenter] 
            elif self.init == 'random':
                for x in range(self.size):
                    if self.dstValues == None: # continuous case
                        if self.DECIMAL: val = decimal.Decimal(str(random.random()))
                        else: val = random.random() 
                        stepInit[x] = val                
                    else: # discrete
                        stepInit[x] = random.choice(self.dstValues)
            # may be number as a string; treat as a list
            elif len(numStr) == len(self.init):
                for x in range(self.size):
                    # must be integers, use force to limit at min / max
                    if self.dstValues != None:
                        min = self.dstValues[0]
                        max = self.dstValues[-1]
                    else: # continuous, unit interval
                        min = 0
                        max = 1
                    val = drawer.strToNum(self.init[(x % len(self.init))], 'int', 
                                                 min, max, 1)
                    stepInit[x] = val
        elif drawer.isNum(self.init):
            for x in range(self.size):
                stepInit[x] = self.init               
        elif drawer.isList(self.init):
            for x in range(self.size):
                stepInit[x] = self.init[(x % len(self.init))]
        self.stepHistory = [stepInit] # a list of arrays        
        
    def _getSrcLast(self, pos, stepLast):
        """read appropriately size chunks from a src step for
        rule comparison; handle wrapping issues of boundary conditions for
        any size issue, including if rule is greater than then src
        note: this function is called often: optimized"""
        srcLast = [] # return a list
        stepLastLen = len(stepLast)
        for q in range(self.srcSpan): # for len of src rule size
            i = pos + self.srcSpanRuleShift + q
            if i < 0: neg = 1
            else: neg = 0
            i = abs(i) % stepLastLen
            if neg: i = -i
            srcLast.append(stepLast[i])
        return srcLast # keep as list

    def _ruleMatch(self, srcRule, srcLast):
        pass # define in sub class

    def applyRule(self, ruleList):
        """for each position (including wrapping), this test each rule in
        the rule list for a match;
        mutation: will set a percentage of random replacements of dst values
            with anything other-than the selected values
        """
        stepLast = self.stepHistory[-1] # get last
        stepNext = self._getTemplate()
        for pos in range(self.size): # scan each position
            srcLast = self._getSrcLast(pos, stepLast) # returns list
            for src, dst in ruleList: # iterate over each rule until found src
                # if rule condition found for last row
                if self._ruleMatch(src, srcLast):
                    # if mutation is zero, never hapen
                    if random.random() < self.mutation: 
                        option = self.dstValues[:] # remove selected value
                        option.pop(option.index(dst)) # and choose any other
                        dst = random.choice(option)
                    stepNext[pos] = dst
                    break # only need to match one rule for each pos
        self.stepHistory.append(stepNext)
        
    def _ruleFilter(self, rule):
        """self.ruleMax must be defined before calling this
        """
        # ruleMax may be a decimal object, so conver to float before comparing
        # continuous ca have a ruleMax == 1.0
        try:
            if float(self.ruleMax) > 1.0: # not continuous
                return drawer.floatToInt(rule, 'weight') % self.ruleMax
            else: # continuous, leave as float, no weighting
                return rule % self.ruleMax
        except OverflowError: # ruleMax may be very very large, and no float pos
            return drawer.floatToInt(rule, 'weight') % self.ruleMax
        
    def _rToSrcSpan(self, r):
        """r values may be fractional, .5 or .0; must conver to int"""
        return int((r*2) + 1) #3 # this is an r == 1

    def gen(self, steps=1, rule=None, mutation=None):
        """mutation can be between zero and 1; percent of random flips"""
        if rule != None: # update if changed
            self.rule = self._ruleFilter(rule)
        if mutation != None:
            self.mutation = mutation
        ruleList = ruleGen(self.rule, self.srcSpan, # rule list should be a list
                                 self.dstValues, self.srcValues)      
        for x in range(steps):
            self.applyRule(ruleList)
                    
    def display(self, start=None, end=None):     
        """generate, but print each line for display"""       
        if start == None:
            start = 0
        if end == None:
            end = len(self.stepHistory)         
        for step in range(start, end):
            print self._fmtStep(self.stepHistory[step])
            #time.sleep(.001)
        
    def getCells(self, fmt='table', norm=1, stepStart=None, stepEnd=None, 
                     centerOffset=0, width=None):
        """width should not be negative
        norm: turn normalizing on or off; will change into list, even if an array
        """
        # set min value to always be zero; this will be true for all outputs
        # max values wull be calclulated when necessary
        d = table.Table(self.stepHistory, 0)
        return d.extract(fmt, norm, stepStart, stepEnd, centerOffset, width)

        
        
# specialized for continuous use
# override apply rule and gen
class _AutomatonOneDimensionContinuous(_AutomatonOneDimension):
    def __init__(self, size, rule=0, init=0, srcSpan=3, mutation=None):
        srcValues=None 
        dstValues=None # always none for continuous
        _AutomatonOneDimension.__init__(self, size, rule, init, dstValues, 
                                             srcSpan, srcValues, mutation)
    
    def applyRule(self):
        """for each position (including wrapping), apply rule
        continuous values allways b/n 0 and 1
        """
        stepLast = self.stepHistory[-1] # get last
        stepNext = self._getTemplate()

        if self.DECIMAL: sumInit = decimal.Decimal(0)
        else: sumInit = 0.0

        for pos in range(self.size): # scan each position
            # dont need to go throuhg each rule to find a match
            srcLast = self._getSrcLast(pos, stepLast)
            # dont need to match rule
            sum = copy.copy(sumInit)
            for val in srcLast:
                sum = sum + val
            avg = sum / len(srcLast) # if this len is always e same, find ahead
            # rule in a continuous ca is a value that is added to average
            if random.random() < self.mutation: # do mutation
                if self.DECIMAL: dst = decimal.Decimal(str(random.random()))
                else: dst = random.random()
            else: # no mutation
                if self.DECIMAL: 
                    dst = (avg + self.rule) % decimal.Decimal(1)
                else:
                    dst = (avg + self.rule) % 1.0
                
            stepNext[pos] = dst
        self.stepHistory.append(stepNext)
        
    def gen(self, steps=1, rule=None, mutation=None):
        """dont need to apply generator or apply rules here
        ruleFilter is not used here, as floating values are needed"""
        if rule != None:
            if self.DECIMAL: rule = decimal.Decimal(str(rule))
        if mutation != None:
            self.mutation = mutation
            
        for x in range(steps):
            self.applyRule()
            

#-----------------------------------------------------------------||||||||||||--
# public discrete one dimensional

class Standard(_AutomatonOneDimension):
    def __init__(self, usrStr, rule=0, mutation=0):
        self.spec = AutomataSpecification(usrStr)
        k = self.spec.get('k')
        r = self.spec.get('r')
        size = self.spec.get('x')
        init = self.spec.get('i')
        
        dstValues = range(k) #[0,1]
        srcSpan = self._rToSrcSpan(r) 
        srcValues = None # same as dst, based on srcSpan
        self.ruleMax = ruleCount(srcSpan, dstValues) # 256 
        rule = self._ruleFilter(rule)
        self.DECIMAL = DECIMAL # assign un-altered, though not used
        _AutomatonOneDimension.__init__(self, size, rule, init, dstValues, 
                                                 srcSpan, srcValues, mutation)
        self.format = 'standard'
        self._refreshTemplate()
        self.clear() # clear step history and creates init row

    def _ruleMatch(self, srcRule, srcLast):
        if srcRule == srcLast: # both here are lists
            return 1
        else: return 0

                
#-----------------------------------------------------------------||||||||||||--

class Totalistic(_AutomatonOneDimension):
    def __init__(self, usrStr, rule=0, mutation=0):
        self.spec = AutomataSpecification(usrStr)
        k = self.spec.get('k')
        r = self.spec.get('r')
        size = self.spec.get('x')
        init = self.spec.get('i')

        if k <= 1: raise ValueError, 'bad k value'
        if r < 1: raise ValueError, 'bad r value'
        
        dstValues = range(k) # if k ==2, k= [0,1]
        srcSpan = self._rToSrcSpan(r) 
        # max of dstValues * srcSpan is max
        # [0,1,2,3] # all sums of two states---
        # also (3*k)-2
        srcValues = range((dstValues[-1]*srcSpan)+1)     # srcNot e same as dst
        
        self.ruleMax = ruleCount(srcSpan,dstValues,srcValues)
        rule = self._ruleFilter(rule)

        self.DECIMAL = DECIMAL # assign un-altered, though not used
        _AutomatonOneDimension.__init__(self, size, rule, init, dstValues, 
                                                 srcSpan, srcValues, mutation)
        self.format = 'totalistic'
        # center inits for totalistic must be mid-value (not darkest)        
        self.dstIndexCenter = 1
        self._refreshTemplate()
        self.clear() # clear step history and creates init row

    def _ruleMatch(self, srcRule, srcLast):     
        # sum will find the appropriate value b/n 0 and 6
        srcLastSum = 0
        for x in srcLast:
            srcLastSum = srcLastSum + x
        # compare to averaged nearest int
        if srcRule == srcLastSum: # both here are lists
            return 1
        else: return 0
        
        

#-----------------------------------------------------------------||||||||||||--

class Continuous(_AutomatonOneDimensionContinuous):
    def __init__(self, usrStr, rule=0, mutation=0):
        # rules here are constant values tt are added to cels
        # then the float portion is taken as the new value
        # self.dstValues always None for continuous

        self.spec = AutomataSpecification(usrStr)
        r = self.spec.get('r')
        size = self.spec.get('x')
        init = self.spec.get('i')

        self.DECIMAL = DECIMAL # assign un-altered
        if self.DECIMAL:
            rule = decimal.Decimal(str(rule))
            self.ruleMax = decimal.Decimal('1.0')
        else:
            self.ruleMax = 1.0
            
        rule = self._ruleFilter(rule)
        srcSpan = self._rToSrcSpan(r) 
        _AutomatonOneDimensionContinuous.__init__(self, size, rule, init, 
                                                                srcSpan, mutation)
        self.format = 'continuous' 
        self._refreshTemplate()
        self.clear() # clear step history and creates init row


class Float(_AutomatonOneDimensionContinuous):
    def __init__(self, usrStr, rule=0, mutation=0):
        # like a continuous, but uses floats for speed
        
        self.spec = AutomataSpecification(usrStr)
        r = self.spec.get('r')
        size = self.spec.get('x')
        init = self.spec.get('i')

        # this is the only difference to Continuous
        self.DECIMAL = 0 # assign as 0, force float-based production
        self.ruleMax = 1.0
        
        rule = self._ruleFilter(rule)
        srcSpan = self._rToSrcSpan(r) 
        _AutomatonOneDimensionContinuous.__init__(self, size, rule, init, 
                                                                srcSpan, mutation)
        self.format = 'float' 
        self._refreshTemplate()
        self.clear() # clear step history and creates init row
        




#-----------------------------------------------------------------||||||||||||--
class _AutomatonTwoDimension(_Automaton):
    def __init__(self, size, rule=0, init=0):
        _Automaton.__init__(self, size, rule, init)
        self.dimension = 2

        self._refreshTemplate()
        self.clear() # clear step history and creates init row
    
    def _refreshTemplate(self):
        # create a blank template based on size
        self.stepTemplate = []
        for y in range(self.size[1]): # as x, y
            row = array.array('B') # B is unsighed char, values 0 to 255
            for x in range(self.size[0]):
                row.append(0)
            self.stepTemplate.append(row)

    def clear(self):
        """processes init value and replaces history with first generation"""
        stepInit = self._getTemplate()
        if drawer.isNum(self.init):
            for y in range(self.size[1]):
                for x in range(self.size[0]):
                    self.stepTemplate[y][x] = self.init
        elif drawer.isList(self.init): # assume list is same size from
            for row in self.init:
                for col in row:
                    self.stepTemplate[y][x] = col                     
        self.stepHistory = [stepInit] # a list of arrays        

    def display(self, start=None, end=None):     
        """generate, but print each line for display"""       
        if start == None:
            start = 0
        if end == None:
            end = len(self.stepHistory)         
        for step in range(start, end):
            for row in self.stepHistory[step]:
                print self._fmtStep(row)





#-----------------------------------------------------------------||||||||||||--


caMonoClasses = [Standard, Totalistic, Continuous]

def factory(usrStr, rule=0, mutation=0):     
    spec = AutomataSpecification(usrStr)
    # may raise error.AutomataSpecificationError, e:
    if spec.get('f') == 's':
        obj = Standard(usrStr, rule, mutation)
    elif spec.get('f') == 't':
        obj = Totalistic(usrStr, rule, mutation)
    elif spec.get('f') == 'c':
        obj = Continuous(usrStr, rule, mutation)
    elif spec.get('f') == 'f':
        obj = Float(usrStr, rule, mutation)
    return obj
    






#-----------------------------------------------------------------||||||||||||--
class TestOld:
    def __init__(self):
        pass

    def testOneDimensionPerformance(self):        
        from athenaCL.libATH import rhythm
        timerTotal = rhythm.Timer()

        for type in caMonoClasses:
            k = 2
            r = 1
            for ruleNo in range(30,40):
                timer = rhythm.Timer()
                a = type(k, r, 39, ruleNo, 'center')
                a.gen(100)
                #timerTotal.stop()
                timer.stop()
                print a
                print timer('sw')
            print 'total time', timerTotal('sw')


    def testOneDimensionDisplay(self):       
        from athenaCL.libATH import rhythm
        timerTotal = rhythm.Timer()

        for type in caMonoClasses:
            for k in range(2,5):
                spec = 'k{%s}r{1}' % (k)
                for ruleNo in range(0,10):
                    timer = rhythm.Timer()
                    # exception for continuous
                    if type in [Continuous]:
                        ruleNo = ruleNo * .1
                        a = type(spec, ruleNo)
                    else:
                        a = type(spec, ruleNo)
                    a.gen(50)
                    #timerTotal.stop()
                    timer.stop()
            
                    # clear screen for nice presentation
                    os.system('clear')
                    a.display()
                    for norm in range(0,2):
                        for out in a.outFmt:
                            print _MOD, out, norm
                            print a.getCells(out, norm)
                    print a
            print 'total time', timerTotal('sw')




#-----------------------------------------------------------------||||||||||||--

if __name__ == '__main__':
    
    a = TestOld()
    a.testOneDimensionDisplay()

    #a.testOneDimensionPerformance()


