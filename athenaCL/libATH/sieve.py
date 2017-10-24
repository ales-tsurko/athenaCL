#-----------------------------------------------------------------||||||||||||--
# Name:          sieve.py
# Purpose:       sieve opperations, after Iannis Xenakis.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2003-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

# not sure this import is necessary

# standarind importas
import copy, string, random
import unittest, doctest


# sets was added w/ python 2.3; w/ python 2.4, sets are built-in
# a = set('abracadabra') is all that is needed
# the 'sets' module should be around for a while...


try:
    setConstruct = set # built-in constructor
except NameError:
    try: 
        import sets
        setConstruct = sets.Set
    except ImportError:
        setConstruct = None
        # removes functionality; will cause error when used

from athenaCL.libATH import pitchTools
from athenaCL.libATH import drawer
from athenaCL.libATH import unit
from athenaCL.libATH import rhythm
_MOD = 'sieve.py'

from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)




#-----------------------------------------------------------------||||||||||||--
# from 
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117119
# David Eppstein, UC Irvine, 28 Feb 2002
# Alex Martelli
# other implementations
# http://c2.com/cgi-bin/wiki?SieveOfEratosthenesInManyProgrammingLanguages
# http://www.mycgiserver.com/~gpiancastelli/blog/archives/000042.html
def eratosthenes():
    """Yields the sequence of prime numbers via the Sieve of Eratosthenes.
    rather than creating a fixed list of a range (z) and crossing out
    multiples of sequential candidates, this algorithm stores primes under
    their next possible candidate, thus allowing the generation of primes
    in sequence w/o storing a complete range (z).

    create a dictionary. each entry in the dictionary is a key:item pair of 
    the largest (key) largest multiple of this prime so far found : (item)
    the prime. the dictionary only has as many entries as found primes.

    if a candidate is not a key in the dictionary, it is not a multiple of 
    any already-found prime; it is thus a prime. a new entry is added to the 
    dictionary, with the square of the prime as the key. the square of the prime
    is the next possible multiple to be found.

    to use this generator, create an instance and then call the .next() method
    on the instance

    >>> a = eratosthenes()
    >>> a.next()
    2
    >>> a.next()
    3
    """
    D = {}  # map composite integers to primes witnessing their compositeness
    # D stores largest composite: prime, pairs
    q = 2     # candidate, first integer to test for primality
    while True:
        # get item from dict by key; remove from dict
        # p is the prime, if already found
        # q is the candidate, the running integer list
        p = D.pop(q, None) # returns item for key, None if not in dict
        # if candidate (q) is already in dict, not a prime
        if p != None: # key (prime candidate) in dictionary
            # update dictionary w/ the next multiple of this prime not already
            # in dicitionary
            # print 'p,q', p, q
            nextMult = p + q # prime prime plus the candidate; next multiple
            while nextMult in list(D.keys()): # incr x by p until it is a unique key
                nextMult = nextMult + p
            # re-store the prime under a key of the next multiple
            D[nextMult] = p # x is now the next unique multple to be found
        # candidate (q) not already in dictionary; q is prime
        else: # value not in dictionary
            nextMult = q * q # square is next multiple tt will be found
            D[nextMult] = q 
            yield q # return prime
        q = q + 1 # incr. candidate



def rabinMiller(n):
    """based on an implementatioin found here:
    http://krenzel.info/?p=83
    see also here: http://www.4dsolutions.net/ocn/numeracy2.html

    >>> rabinMiller(234)
    0
    """
    n = abs(n)
    if n in [2,3]: return 1
    m = n % 6 # if n (except 2 and 3) mod 6 is not 1 or 5, then n isn't prime
    if m != 1 and m != 5: return 0
    # first hundred primes, 2, 3 handled by mod 6
    primes = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97] 
    if n <= 100:
        if n in primes: return 1 # must include 2,3
        return 0
    for prime in primes:
        if n % prime == 0: return 0
    s, r = n-1, 1
    while not s & 1:
        s >>= 1
        r = r + 1       
    for i in range(0,10): # random tests
        # calculate a^s mod n, where a is a random number
        y = pow(random.randint(1, n-1), s, n)
        if y == 1: continue # n passed test, is composite
        # try values of j from 1 to r-1
        for j in range(1,r):
            if y == n - 1: break # if y = n-1, n passed the test this time
            y = pow(y,2,n) # a^((2^j)*s) mod n
        else:
             return 0 # y never equaled n-1, then n is composite
    # n passed all of the tests, it is very likely prime
    return 1



class PrimeSegment:
    def __init__(self, start, length):
        """gets a segment of prime numbers
        min and length values are suggested; may not be relevant
        in final presentation
        will accept negative values and wrap

        >>> a = PrimeSegment(3, 20)
        >>> a()
        [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73]
        """
        self.seg = []
        self.start = start
        self.length = length
        # fill the segment
        self._fillRange()


    def _fillRabinMiller(self, start, length, stop=None, direction='up'):
        """scan all number in range and return a list of primess
        provide a max to force stoppage at  certain point before the
        maximum length
        direction determines which way things go"""
        seg = []
        _oddBoundary = 4 # number above which only odd primes are found

        if start % 2 == 0 and start > _oddBoundary: # if even
            if direction == 'up':
                n = start + 1
            else: # if down
                n = start - 1
        else: n = start

        while 1:              
            if rabinMiller(n):
                seg.append(n)
                if len(seg) >= length: break

            if n == stop: break

            if n > _oddBoundary: # after 5, no even primes
                if direction == 'up':
                    n = n + 2 # only test odd numbers
                else: n = n - 2 # 
            else: # n is less than 5, add 1
                if direction == 'up':
                    n = n + 1 # must increment by 1
                else: n = n - 1 # 
        return seg


    def _fillRange(self):
        """fill positive and negative range"""
        if self.start < 0:
            # create the negative portion of the segment
            segNeg = self._fillRabinMiller(abs(self.start), self.length, 0, 'down')
            segNeg = [-x for x in segNeg] # make negative
            if len(segNeg) < self.length:
                segPos = self._fillRabinMiller(0, self.length-len(segNeg), 
                                                         None, 'up')
                self.seg = segNeg + segPos
            else: # add positive values
                self.seg = segNeg

        else: # start from zero alone
            self.seg = self._fillRabinMiller(self.start, self.length, None, 'up')


    def __call__(self, format=None):
        """assumes that min and max values are derived from found primes
        means that primes will always be at boundaries"""
        z = [self.seg[0], self.seg[-1]]

        if format in ['bin', 'binary']:
            return unit.discreteBinaryPad(self.seg, z)
        elif format in ['unit']:
            return unit.unitNormRange(self.seg, z)
        elif format in ['wid', 'width']:
            wid = []
            for i in range(0, len(self.seg)-1):
                wid.append((self.seg[i+1]-self.seg[i]))
            return wid
        else: # int, integer
            return self.seg



#-----------------------------------------------------------------||||||||||||--
# implementation of Xenakis formula to calculate m,n for the intersection
# of any two Residual classes

def _gcd(a, b):
    """find the greatest common divisor of a,b
    i.e., greatest number that is a factor of both numbers
    euclides algorithm

    >>> _gcd(20, 30)
    10
    """
    # alt implementation

    #while b != 0:
    #    a, b = b, a % b
    #return abs(a)

    #if a == 0 and b == 0: return 1
    #if b == 0: return a
    #if a == 0: return b
    #else: return _gcd(b, a%b)

    while b != 0:
        a, b = b, a % b
    return abs(a)

def _lcm(a, b):
    """find lowest common multiple of a,b

    >>> _lcm(30,20)
    60
    """
    # // forcers integer style division (no remainder)
    return abs(a*b) / _gcd(a,b) 

def _lcmRecurse(filter):
    # from
    # http://www.oreillynet.com/cs/user/view/cs_msg/41022
    lcmVal = 1
    # note: timing may not be necessary
    timer = rhythm.Timer()
    timer.start()
    for i in range(len(filter)):
        if timer() >= 60: # 1.5 minute
            print('lcm timed out.')
            lcmVal = None
            break
        lcmVal = _lcm(lcmVal, filter[i])
    return lcmVal

def _lcmBrute(filter):
    """redundancies should already be filtered"""
    # py 2147483647 # max for non-long ints
    MAX = 1000000 # max number to try
    upper = filter[-1]
    lower = filter[:-1]
    lcmVal = 0
    x = 1
    while 1:
        lcmVal = upper * x # get next multiple
        if lcmVal >= MAX:
            print('no lcm up to %s' % MAX)
            return None
        match = 0
        for q in lower:
            if lcmVal % q == 0: # lcm is a multuple of q
                match = match + 1
        if match == len(lower):
            break
        x = x + 1           
    return lcmVal



def _meziriac(c1, c2):
    # bachet de _meziriac (1624)
    # in order for x and y to be two corpimes, it is necessary and suff
    # that there exist two relative whole numbers, e, g such that
    #       1 + (g * x) = e * y  or
    #            y' * x = (e' * y) + 1
    # where e and g come from the recursive equations
    #           (e * c2) % c1 == 1  and
    #           (g'* c1) % c2 == 1  ### this is version used here
    # while letting e, g' run through values 0,1,2,3...
    # except if c1 == 1 and c2 == 1
    g = 0
    if c2 == 1:
        g = 1
    elif c1 == c2:
        g = 0 # if equal, causes infinite loop of 0
    else:
        while g < 10000:
            val = (g * c1) % c2
            if val == 1: break
            g = g + 1
    return g





#-----------------------------------------------------------------||||||||||||--
class Residual:
    """object that represents a modulus and a start point
    each object stores a range of integers (self.z) from which sections are drawn
    this range of integers can be changed whenever the section os drawn
    """
    def __init__(self, m, shift=0, neg=0, z=None):
        """
        >>> a = Residual(3, 2)
        """
        # get a default range, can be changed later
        # is an actual range and not start/end points b/c when producing a not (-)
        # it is easy to remove the mod,n from the range
        if z == None: # supply default if necessary
            z = list(range(0, 100)) 
        self.z = z
        #print 'residual init self.z', self.z
        self.m = m
        if neg not in [0, 1]:
            raise TypeError('negative value must be 0, 1, or a Boolean')
        self.neg = neg # negative, complement boolean
        if self.m == 0: # 0 mode causes ZeroDivisionError
            self.shift = shift
        else:
            self.shift = shift % self.m # do mod on shift
        self.segFmtOption = ['int', 'bin', 'unit', 'wid']
        self.segFmt = 'int'

    #-----------------------------------------------------------------------||--
    # utility functions
    def zAssign(self, z):
        "z is the range of integers to use when generating a list"
        self.z = z

    def zAssignRange(self, min, max):
        """z is the range of integers to use when generating a list
        convenience functiont that fixes max
        """
        self.z = list(range(min, max+1))

    def segFmtSet(self, fmt):
        fmt = drawer.strScrub(fmt, 'l')
        assert fmt in self.segFmtOption
        self.segFmt = fmt

    #-----------------------------------------------------------------------||--
    def segment(self, n=0, z=None, format=None):
        """get a residual subset of this modulus at this n
        within the integer range provided by z
        format can be 'int' or 'bin', for integer or binary


        >>> a = Residual(3, 2)
        >>> a.segment(3)
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59, 62, 65, 68, 71, 74, 77, 80, 83, 86, 89, 92, 95, 98]
        >>> a.segment(3, range(3,15))
        [5, 8, 11, 14]
        """
        #print 'residual arg z', z
        if z == None: # z is temporary; if none
            z = self.z # assign to local
        #print 'residual using z', z
        if format == None:
            format = self.segFmt

        subset = []
        if self.m == 0: return subset # empty
        n = (n + self.shift) % self.m # check for n >= m

        for value in z:
            if n == value % self.m:
                subset.append(value)
        if self.neg: # find opposite
            compset = copy.deepcopy(z)
            for value in subset:
                compset.remove(value)
            seg = compset
        else:
            seg = subset
        
        if format in ['bin', 'binary']:
            return unit.discreteBinaryPad(seg, z)
        elif format in ['unit']:
            return unit.unitNormRange(seg, z)
        elif format in ['wid', 'width']: # difference always equal to m
            wid = [self.m] * (len(seg)-1) # one shorter than segment
            return wid
        elif format in ['int', 'integer']: # int, integer
            return seg
        else:
            raise TypeError('%s not a valid sieve format string.' % format)

    def period(self):
        """period is M; obvious, but nice for completeness

        >>> a = Residual(3, 2)
        >>> a.period()
        3
        """
        return self.m

    #-----------------------------------------------------------------------||--
    def copy(self):
        m = copy.copy(self.m)
        shift = copy.copy(self.shift)
        neg = copy.copy(self.neg)
        # provide ref, not copy, to z
        return Residual(m, shift, neg, self.z)
    
    def __call__(self, n=0, z=None, format=None):
        """calls self.segment(); uses segFmt

        >>> a = Residual(3, 2)
        >>> a()
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59, 62, 65, 68, 71, 74, 77, 80, 83, 86, 89, 92, 95, 98]
        """ # if z is None, uses self.z
        #print 'residual', self.repr()
        return self.segment(n, z, format)

    def repr(self, style=None):
        """does not show any logical operator but unary negation"""
        if style == 'classic': # mathmatical style
            if self.shift != 0:
                str = '%s(%s+%s)' % (self.m, 'n', self.shift)
            else:
                str = '%s(%s)' % (self.m, 'n')
            if self.neg:
                str = '-%s' % str
        else: # do evaluatable stype
            str = '%s@%s' % (self.m, self.shift) # show w/ @
            if self.neg:
                str = '-%s' % str
        return str

    def __str__(self):
        """str representation using M(n+shift) style notation

        >>> a = Residual(3, 2)
        >>> str(a)
        '3@2'
        """
        return self.repr() #default style

    def __eq__(self, other):
        "==, compare residual classes in terms of m and shift"
        if other == None: return 0
        if (self.m == other.m and self.shift == other.shift and 
             self.neg == other.neg):
            return 1
        else: return 0

    def __ne__(self, other):
        "m and shift not equal"
        if other == None: return 1
        if (self.m != other.m or self.shift != other.shift or
             self.neg != other.neg):
            return 1
        else: return 0

    def __cmp__(self, other):
        """allow comparison based on m and shift; if all equal look at neg"""
        #return neg if self < other, zero if self == other, 
        # a positive integer if self > other. 
        if self.m < other.m:
            return -1
        elif self.m > other.m:
            return 1
        # if equal compare shift
        elif self.m == other.m:
            if self.shift < other.shift:
                return -1
            elif self.shift > other.shift:
                return 1
            else: # shifts are equal
                if self.neg != other.neg:
                    if self.neg == 1: # its negative, then less
                        return -1
                    else: return 1
                else: return 0
            

    def __neg__(self):
        """unary neg operators; return neg object"""
        if self.neg: #if 1
            neg = 0
        else: # if 0
            neg = 1
        return Residual(self.m, self.shift, neg, self.z)

    def __and__(self, other):
        """&, produces an intersection of two Residual classes
        returns a new Residual class
        cannot be done if R under complementation

        >>> a = Residual(3, 2)
        >>> b = Residual(5, 1)
        >>> c = a & b
        >>> str(c)
        '15@11'
        """
        if other.neg or self.neg:
            raise TypeError('complented Residual objects cannot be intersected')
        m, n = self._cmpIntersection(self.m, other.m, self.shift, other.shift)
        # get the union of both z
        zSet = setConstruct(self.z) | setConstruct(other.z) 
        z = list(zSet)
        neg = 0 # most not be complemented
        return Residual(m, n, 0, z)

    def __or__(self, other):
        """|, not sure if this can be implemented
        i.e., a union of two Residual classes can not be expressed as a single
        Residual, that is intersections can always be reduced, wheras unions
        cannot be reduced."""
        pass


    #-----------------------------------------------------------------------||--
    def _cmpIntersection(self, m1, m2, n1, n2):
        """compression by intersection
        find m,n such that the intersection of two Residual's can 
        be reduced to one Residual Xenakis p 273"""
        d = _gcd(m1, m2)
        c1 = m1 / d # not sure if we need floats here
        c2 = m2 / d
        n3 = 0
        m3 = 0
        if m1 != 0 and m2 != 0:
            n1 = n1 % m1
            n2 = n2 % m2
        else: # one of the mods is equal to 0
            return n3, m3 # no intersection
        if d != 1 and ((n1-n2) % d != 0):
            return n3, m3 # no intersection
        elif d != 1 and ((n1-n2) % d == 0) and (n1 != n2) and (c1 == c2):
            m3 = d # for real?
            n3 = n1
            return m3, n3
        else: # d == 1, or ...
            m3 = c1 * c2 * d
            g = _meziriac(c1, c2) # c1,c2 must be co-prime may produce a loop
            n3 = (n1 + (g * (n2-n1) * c1)) % m3
            return m3, n3





#-----------------------------------------------------------------||||||||||||--
class CompressionSeg:
    """utility to convert from a point sequence to sieve

    the supplied list of values is only the positive values of a sieve segment
    we do not know what the negative values are; we can assume they are between  
    the min and max of the list, but this may not be true in all cases. a z range 
    can be supplied to explitly provide the complete sieve segment, both positive
    and negative values. all values in the z range not in the segment are    
    interepreted as negative values. thus, there is an essential dependency on 
    the the z range and the realized sieve.

    no matter the size of the z range, there is a modulus at which one point in 
    the segment can be found. as such, any segment can be reduced to, at a 
    mimimum, a residual for each point in the segment, each, for the supplied z,      
    providing a segment with one point.

    the same segment can then have multipled logical string representations,
    depending on the provided z.

    """
    def __init__(self, src, z=None):
        """
        >>> a = CompressionSeg([3,4,5,6,7,8])
        """
        self.src = list(copy.deepcopy(src))
        self.src.sort()
        self.match = [] # already sorted from src
        for num in self.src: # remove redundancies
            if num not in self.match:
                self.match.append(num)
        if len(self.match) <= 1:
            raise ValueError('segment must have more than one element')
        self._zUpdate(z) # sets self.z
        # max mod should always be the max of z; this is b/c at for any segment
        # if the mod == max of seg, at least one point can be found in the segment
        # mod is the step size, so only one step will happen in the sequence
        self.MAXMOD = len(self.z) # set maximum mod tried
        # assign self.residuals and do analysis
        try:
            self._process()
        except AssertionError:
            raise ValueError('no Residual classes found for this z range')

    def _zUpdate(self, z=None):
        # z must at least be a superset of match
        if z != None: # its a list
            if not self._subset(self.match, z):
                raise ValueError('z range must be a superset of desired segment')
            else: # okay, assign
                self.z = z
            zMin, zMax = self.z[0], self.z[-1]
        # z is range from max to min, unless provided at init     
        else: # range from min, max; add 1 for range() to max
            zMin, zMax = self.match[0], self.match[-1] 
            self.z = list(range(zMin, (zMax + 1))) 


    #-----------------------------------------------------------------------||--
    def __call__(self):
        """
        >>> a = CompressionSeg([3,4,5,6,7,8])
        >>> b = a()
        >>> str(b[0])
        '1@0'
        """
        return self.residuals

    def __str__(self):
        resStr = []
        if len(self.residuals) == 1: # single union must have an or
            resStr = '%s' % str(self.residuals[0])
        else:
            for resObj in self.residuals:
                resStr.append(str(resObj))
            resStr = '|'.join(resStr)
        return resStr

    #-----------------------------------------------------------------------||--

    def _subset(self, sub, set):
        """true if sub is part of set; assumes no redundancies in each"""
        common = 0
        for x in sub:
            if x in set:
                common = common + 1
        if common == len(sub):
            return 1
        else: return 0

    def _find(self, n, part, whole):
        """given a point, and seiveSegment, find a modulus and shift that
        match"""
        m = 1 # could start at one, but only pertains to the single case of 1@0
        while 1: # search m for max
            obj = Residual(m, n, 0, self.z)
            seg = obj() # n, z is set already
            # check first to see if it is a member of the part
            if self._subset(seg, part):
                return obj, seg
            elif self._subset(seg, whole):
                return obj, seg
            m = m + 1
            # a mod will always be found, at least 1 point; should never happen
            assert m <= self.MAXMOD
        #print 'error, no mod found', n, part

    def _process(self):
        """take a copy of match; move through each value of this list as if it
        were n; for each n test all modulos (from 1 to len(z)+1) to find a 
        residual. when found (one will be found), keep it; remove the found 
        segments from the match, and repeat"""
        # process residuals
        self.residuals = [] # list of objects
        match = copy.copy(self.match) # scratch to work on
        while 1: # loop over whatever is left in the match copy
            n = match[0] # always get first item 
            obj, seg = self._find(n, match, self.match)
            assert obj != None # no residual found; should never happen
            if obj not in self.residuals: # b/c __eq__ defined
                self.residuals.append(obj)
                for x in seg: # clean found values from match
                    if x in match:
                        match.remove(x)
            if len(match) == 0:
                break
        self.residuals.sort()


#-----------------------------------------------------------------||||||||||||--

# http://docs.python.org/lib/set-objects.html
# set object precedence is places & before |

# >>> a = set([3,4])
# >>> b = set([4,5])
# >>> c = set([3,4,5])
# >>> a & b & c
# Set([4])

# >>> a & b | c
# Set([3, 4, 5])

# >>> a & (b | c)
# Set([3, 4])
# >>> (a & b) | c
# Set([3, 4, 5])

# >>> b = sieve.SieveBound('2&4&8|5')
# <R0>&<R1>&<R2>|<R3>
# >>> str(b)
# '2&4&8|5'
# >>> b(0, range(0,20))
# [0, 5, 8, 10, 15, 16]
# >>> b = sieve.SieveBound('2&4&(8|5)')
# <R0>&<R1>&(<R2>|<R3>)
# >>> b(0, range(0,20))
# [0, 8, 16]
# >>> b = sieve.SieveBound('5|2&4&8')
# <R0>|<R1>&<R2>&<R3>
# >>> b(0, range(0,20))
# [0, 5, 8, 10, 15, 16]
# >>> b = sieve.SieveBound('(5|2)&4&8')
# (<R0>|<R1>)&<R2>&<R3>
# >>> b(0, range(0,20))
# [0, 8, 16]
# >>> 

# precedence is -, &, |

class Sieve:
    """create a sieve segment from a sieve logical string of any complexity
    """
    def __init__(self, usrStr, z=None):
        """
        >>> a = Sieve('3@11')
        >>> b = Sieve('2&4&8|5')
        >>> c = Sieve('(5|2)&4&8')
        """
        self.LGROUP = '{'
        self.RGROUP = '}'
        self.AND = '&'
        self.OR = '|'
        self.XOR = '^'
        self.BOUNDS = [self.LGROUP,self.RGROUP,self.AND,self.OR,self.XOR]
        self.NEG = '-'
        self.RESIDUAL = list(string.digits) + ['@']
                
        # note: this z should only be used if usrStr is a str, and not a list
        if z == None and drawer.isStr(usrStr):
            z = list(range(0, 100))
        elif z == None and drawer.isList(usrStr): # if a list, keep as None
            pass
        self.z = z # may be none; will be handled in self._load
        
        self.state = 'exp' # default start state
        self.expType = None # either 'simple' or 'complex'; set w/ load
        self.segFmt = 'int'
        self.segFmtOption = ['int', 'bin', 'unit', 'wid']

        self.nonCompressible = 0 # if current z provides a nullSeg; no compression
        # varaibles will reinit w/ dedicated methods
        self.resLib = {} # store id and object
        self.resId = 0 # used to calculate residual ids

        # expanded, compressed form
        self.expTree = '' # string that stores representation
        self._expPeriod = None # only set if called
        self.cmpTree = '' # string that stores representation
        self._cmpPeriod = None # only set if called; may not be same as exp
        self.usrStr = usrStr # store user string, may be noen
        if self.usrStr != None:
            self._load()

    #-----------------------------------------------------------------------||--
    def _load(self):
        if drawer.isList(self.usrStr):
            self._resClear()
            self._initLoadSegment(self.usrStr) # z will be provided
            self._initCompression()
        # normal instance, or a manual load
        else: # process usrStr
            self._resClear()
            self._initParse()
            self._initCompression()

    def _initCompression(self):
        # only negative that will show up is binary negative, not unary
        # some internal intersections may have a complemented residual class
        self.expType = 'complex' # assume complex
        if (self.NEG in self.expTree or self.LGROUP in self.expTree or 
             self.RGROUP in self.expTree or self.XOR in self.expTree):
            try:
                self._cmpSegment() # will update self.nonCompressible
            except IndexError: # case of z not providing a sufficent any segment
                self.nonCompressible = 1
        else: # try intersection
            try:
                self._cmpIntersection()
                self.expType = 'simple' # only if sucessful
            except TypeError: # attempted intersection of complemented
                try: 
                    self._cmpSegment()
                except IndexError: # no segments available
                    self.nonCompressible = 1

        if self.nonCompressible:
            method = 'no compression possible'
        elif self.expType == 'complex':
            method = 'segment'
        elif self.expType == 'simple':
            method = 'intersection'


    def _initPeriod(self):
        mListExp = self._resPeriodList('exp')
        mListCmp = self._resPeriodList('cmp')
        #print 'brute', _lcmBrute(mListExp)
        lcmExp = _lcmRecurse(mListExp)
        if mListExp == mListCmp:
            self._expPeriod = lcmExp
            self._cmpPeriod = lcmExp
        else: # calculate separately
            self._expPeriod = lcmExp
            self._cmpPeriod = _lcmRecurse(mListCmp)
 
    #-----------------------------------------------------------------------||--
    def expand(self):
        self.state = 'exp'

    def compress(self, z=None):         
        if z != None and z != self.z: # only process if z has changed
            self.z = z
            self._resClear('cmp') # clear compressed residuals
            self._initCompression() # may update self.nonCompressible
        if self.nonCompressible: # do not changes set
            print('no compression availabile at this z.')
        else:
            self.state = 'cmp'


    #-----------------------------------------------------------------------||--
    def dataLoad(self, data):
        """load reinit an existing object"""
        self.usrStr = data['logStr']
        if 'z' in data:
            self.z = data['z']
        self._load()

    def dataStore(self):
        data = {}
        data['logStr'] = self.repr('exp') # store expanded representation
        if self.z == None: # get from residual classes, always one at 
            data['z'] = self.resLib[self._resKeyStr(0)].z
        else:
            data['z'] = self.z
        return data
        
    #-----------------------------------------------------------------------||--
    # utility functions
    def zAssign(self, z):
        "z is the range of integers to use when generating a list"
        self.z = z

    def zAssignRange(self, min, max):
        """z is the range of integers to use when generating a list
        convenience functiont that fixes max
        """
        self.z = list(range(min, max+1))

    def segFmtSet(self, fmt):
        fmt = drawer.strScrub(fmt, 'l')
        assert fmt in self.segFmtOption
        self.segFmt = fmt

    #-----------------------------------------------------------------------||--
    # operator overloading for sieves
    # problem: redunant parenthesis are not removed

    def __neg__(self):
        """unary neg operators; return neg object"""
        dataSelf = self.dataStore()
        usrStr = '%s%s%s%s' % (self.NEG, self.LGROUP, 
                                     dataSelf['logStr'], self.RGROUP)
        z = dataSelf['z']
        return Sieve(usrStr, z)

    def __and__(self, other):
        """&, produces an intersection of two

        >>> a = Sieve('3@11')
        >>> b = Sieve('2&4&8|5')
        >>> c = Sieve('(5|2)&4&8')
        >>> d = a & b
        >>> str(d)
        '{2@0&4@0&8@0|5@0}&{3@2}'
        """
        dataSelf = self.dataStore()
        dataOther = other.dataStore()
        usrStr = '%s%s%s%s%s%s%s' % (self.LGROUP, dataOther['logStr'],
            self.RGROUP, self.AND, self.LGROUP, dataSelf['logStr'], self.RGROUP)
        # take union of z
        zSet = setConstruct(dataSelf['z']) | setConstruct(dataOther['z'])     
        z = list(zSet)
        return Sieve(usrStr, z)

    def __or__(self, other):
        """|, produces a union 

        >>> a = Sieve('3@11')
        >>> b = Sieve('2&4&8|5')
        >>> c = Sieve('(5|2)&4&8')
        >>> d = a | b
        >>> str(d)
        '{2@0&4@0&8@0|5@0}|{3@2}'
        """
        dataSelf = self.dataStore()
        dataOther = other.dataStore()

        usrStr = '%s%s%s%s%s%s%s' % (self.LGROUP, dataOther['logStr'],           
                self.RGROUP, self.OR, self.LGROUP, dataSelf['logStr'], self.RGROUP)
        # take union of z
        zSet = setConstruct(dataSelf['z']) | setConstruct(dataOther['z'])     
        z = list(zSet)
        return Sieve(usrStr, z)

    def __xor__(self, other):
        """^, produces exclusive disjunction """
        dataSelf = self.dataStore()
        dataOther = other.dataStore()

        usrStr = '%s%s%s%s%s%s%s' % (self.LGROUP, dataOther['logStr'],           
                self.RGROUP, self.XOR, self.LGROUP, dataSelf['logStr'], self.RGROUP)
        # take union of z
        zSet = setConstruct(dataSelf['z']) | setConstruct(dataOther['z'])     
        z = list(zSet)
        return Sieve(usrStr, z)

        
    def copy(self):
        """implement..."""
        pass
        
        
    #-----------------------------------------------------------------------||--
    # string conversions
    def _parseResidual(self, usrStr):
        """process an arg string for proper Residual creation
        valid syntax for Mod, shift pairs:
        all valid: MsubN, M@N, M,N, M
        if M is given alone, shift is assumed to be 0
        this method assumes that all brackets have been replaced with pareths
        returns a dictionary of args suitable for creating a Residual classs
        """
        # if given a number, not a string
        if drawer.isNum(usrStr):
            return {'m':int(usrStr), 'n':0, 'neg':0}
    
        usrStr = usrStr.strip()
        if len(usrStr) == 0: return None
        if usrStr.find('sub') >= 0:
            usrStr = usrStr.replace('sub', ',')
        if usrStr.find('@') >= 0:
            usrStr = usrStr.replace('@', ',')
        # remove any braces remain, remove
        # all parenthesis and brackets are converted to braces
        usrStr = usrStr.replace(self.LGROUP, '')
        usrStr = usrStr.replace(self.RGROUP, '')

        # check for not 
        if usrStr[0] == '-': # negative/complement
            neg = 1
            usrStr = usrStr[1:].strip() # strip to remove any leading white space
        else:
            neg = 0
        if len(usrStr) == 0: return None
    
        try: # assume we have either an int (M), or a tuple (M,N)
            args = eval(usrStr) 
        except (NameError, SyntaxError, TypeError):
            return None
        if drawer.isInt(args):
            m = args # int is mod
            shift = 0    # 0 is given as default shift
        elif drawer.isList(args): # may only be a list of one elemnt
            m = args[0] #first  is mod
            if len(args) > 1:
                shift = args[1] #second is shift
            else: shift = 0
        # return a dictionary of args necessary to create Residual
        return {'m':m, 'shift':shift, 'neg':neg}
        
    def _parseLogic(self, usrStr):
        """provide synonymes for logical symbols
        intersection == and, &, *
        union            == or, |, +
        not          == not, -
        the native format for str representation usese only &, |, -
        this method converts all other string representations

        all brackets and braces are replaced with parenthesis
        parentheses are only used for the internal representation
        on string representation, braces are restored
        """
        # if not a string but a number
        if drawer.isNum(usrStr): # assume its a single modules
            usrStr = '%s@0' % int(usrStr)
    
        if usrStr.find('and') >= 0: # replace with '&'
            usrStr = usrStr.replace('and', self.AND)
        if usrStr.find('*') >= 0: # Xenakis notation'
            usrStr = usrStr.replace('*', self.AND)
        if usrStr.find('or') >= 0:
            usrStr = usrStr.replace('or', self.OR)
        if usrStr.find('+') >= 0:
            usrStr = usrStr.replace('+', self.OR)
        if usrStr.find('xor') >= 0:
            usrStr = usrStr.replace('^', self.OR)
        if usrStr.find('not') >= 0:
            usrStr = usrStr.replace('not', self.NEG)
        # all gruoopings converted to braces
        if usrStr.find('[') >= 0: # replace brackets w/ parenthesis
            usrStr = usrStr.replace('[', self.LGROUP)
        if usrStr.find(']') >= 0:
            usrStr = usrStr.replace(']', self.RGROUP)
        if usrStr.find('(') >= 0: # replace braces as well
            usrStr = usrStr.replace('(', self.LGROUP)
        if usrStr.find(')') >= 0:
            usrStr = usrStr.replace(')', self.RGROUP)
        # remove space
        usrStr = usrStr.replace(' ','')
        return usrStr

    #-----------------------------------------------------------------------||--
    def _setInstantiateStr(self, valList):
        """return string necessary to instantiate a set object"""
        valList = list(valList)
        return 'setConstruct(%s)' % repr(valList).replace(' ', '')

    def _resKeyStr(self, id):
        return '<R%i>' % id

    def _resKeys(self, state):
        """get residual keys based on library"""
        assert state in ['cmp', 'exp']
        if state == 'cmp':
            libKeys = []
            for key in list(self.resLib.keys()):
                if key in self.cmpTree:
                    libKeys.append(key)
            return libKeys
        elif state == 'exp':
            libKeys = []
            for key in list(self.resLib.keys()):
                if key in self.expTree:
                    libKeys.append(key)
            return libKeys

    def _resPeriodList(self, state):
        """the period of residual class is m; can be accessed 
        via period() method"""
        mList = []
        for key in self._resKeys(state):
            p = self.resLib[key].period()
            if p not in mList:
                mList.append(p)
        mList.sort()
        return mList

    def _resCreate(self, id, resStr):
        """create a residual object, store in expResidualLib
        return a string id representation
        this uses self.z at initialization"""
        resDict = self._parseResidual(''.join(resStr))
        if resDict == None:
            msg = 'cannot parse %s' % ''.join(resStr)
            raise SyntaxError('bad residual class notation: (%r)' % msg)
        resObj = Residual(resDict['m'],resDict['shift'],
                    resDict['neg'], self.z)
        #print 'created', resDict, self.z
        self.resLib[self._resKeyStr(id)] = resObj
        return self._resKeyStr(id)

    def _resAssign(self, id, resObj):
        self.resLib[self._resKeyStr(id)] = resObj
        return self._resKeyStr(id)

    def _resToSetStr(self, id, n=0, z=None):
        """this is where residuals are converted to set evaluating strings
        z should not be stored; should be a temporary value
        """
        if z == None: # if none given, give internal
            z = self.z 
        # z is valid, gets default from residual class
        if not drawer.isList(z) and z != None:
            raise TypeError('z must be a list of integers.')
        valList = self.resLib[id](n, z) # call residual object
        return self._setInstantiateStr(valList)

    def _resIdIncr(self):
        """increment the resId"""
        self.resId = self.resId + 1

    def _resResetId(self):
        """reset self.resId to the next available number
        may need to re-label some residual classes if gaps develop
        ids should be coniguous integer sequence"""
        iVals = list(range(0, len(list(self.resLib.keys()))))
        for i in iVals:
            testKey = self._resKeyStr(i)
            if testKey not in self.cmpTree and testKey not in self.expTree:
                raise KeyError('gap in residual keys')
        # set resId to next availabe index, the length of the keys
        self.resId = len(list(self.resLib.keys()))

    def _resClear(self, state=None):
        if state == None: # clear all
            self.resLib = {} # store id and object
            self.resId = 0
        elif state == 'cmp':
            cmpKeys = self._resKeys(state)
            for key in cmpKeys:
                del self.resLib[key]
            # reset id to reflect deleted classes
            self._resResetId()
        elif state == 'exp':
            raise ValueError('expanded residual classes shold never be cleared')

    #-----------------------------------------------------------------------||--
    # expansion methods

    def _initLoadSegment(self, usrData):
        """load from a segments
        reload resId"""
        # clear first
        self.expTree = [] # string that stores representation
        # use dynamically generated z
        segObj = CompressionSeg(usrData, self.z) #  a list of values
        if self.z == None: # non given at init, get from segObj
            self.z = segObj.z
        union = segObj() # convert to residual classes
        for resObj in union:
            # store resKey in dict, store as string
            self.expTree.append(self._resAssign(self.resId, resObj))
            self._resIdIncr()
        self.expTree = self.OR.join(self.expTree)
        #print _MOD, 'expTree', self.expTree


    def _initParse(self, z=None):
        """process usrStr string into proper argument dictionaries for Residual
        """
        # clear first
        self.resLib = {} # store id and object
        self.resId = 0
        self.expTree = [] # string that stores representation
        # will remove all spaces
        logStr = self._parseLogic(copy.deepcopy(self.usrStr)) # logical string
        i = 0
        while 1:
            if i == len(logStr): break
            char = logStr[i] # current char

            if i == 0: charPrevious = None # first
            else: charPrevious = logStr[i-1]
            if i == len(logStr) - 1: charNext = None # last
            else: charNext = logStr[i+1]

            #print char, '(%s,%s)' % (charPrevious, charNext)

            # if a boundary symbol ({}&|) symply add to string
            if char in self.BOUNDS:
                self.expTree.append(char)
                i = i + 1

            # if NEG is last char this is always an error
            elif char == self.NEG and charNext == None:
                msg = 'negation cannot be used without operands'
                raise SyntaxError('badly formed logical string (a): (%s)' % msg)
            # attempting to use negationg as a binary operators
            elif (char == self.NEG and charPrevious != None and 
                charPrevious in self.RESIDUAL): # digit, or @ sign
                msg = 'negation cannot be used as a binary operator'
                raise SyntaxError('badly formed logical string (b): (%s)' % msg)
            # check if self.NEG is not folloed by a digit;
            # special case of self.NEG; need to convert into a binary operator
            elif (char == self.NEG and charNext != None and 
                charNext == self.LGROUP):
                # if not first char, and the prevous char is not an operator or
                # a delimter, this is an error (binary negation)
                if (charPrevious != None and charPrevious not 
                    in [self.LGROUP, self.AND, self.OR, self.XOR]):
                    msg = 'negation must be of a group and isolated by delimiters'
                    raise SyntaxError('badly formed logical string (c): (%s)' % msg)
                # add a set of z, or 1@0
                else: # maintain representation until evaluation
                    self.expTree.append(char)
                    i = i + 1

            # processing a normal residual class; only first 
            # char can be negative
            # self.NEG, if present, will be followed by digits
            elif char in string.digits or char == self.NEG:
                resStr = [] # string just for this residual class
                subStart = copy.copy(i)
                subLen = 0
                # fist check for leading NEG
                if logStr[subStart + subLen] == self.NEG:
                    resStr.append(self.NEG)
                    subLen = subLen + 1
                while 1:
                    # if at the end of the logical string
                    if (subStart + subLen) == len(logStr): break
                    subChar = logStr[subStart + subLen]
                    # neg is boundary, as alrady gathered above
                    if subChar in self.BOUNDS or subChar == self.NEG:
                        break # do not increment
                    else:
                        resStr.append(subChar)
                        subLen = subLen + 1
                #print _MOD, 'found residual:', ''.join(resStr)
                self.expTree.append(self._resCreate(self.resId, ''.join(resStr))) 
                self._resIdIncr()
                i = i + subLen
            else: # some other char is in here
                i = i + 1
        # do some checks 
        if len(self.resLib) == 0:
            raise SyntaxError('no residual classes defined')
        self.expTree = ''.join(self.expTree)


    #-----------------------------------------------------------------------||--
    # compression methods
    def _cmpIntersection(self):
        """an unbound sieve, interesect Residual
        """
        self.cmpTree = []    #clear first
        logStr = copy.copy(self.expTree) # create scratch copy
        # if not a string but a number
        orList = logStr.split(self.OR)
        for orGroup in orList:
            if orGroup == '': continue
            # need deal with mixed not's in an andGroup
            andList = orGroup.split(self.AND)
            # do intersections, reduce, and add
            if len(andList) == 1:
                intersection = self.resLib[andList[0]]
            else:
                for i in range(0, len(andList)-1): # one less than len
                    if i == 0: # first, get first
                        # problem was here w/ and list value not being in resLib
                        a = self.resLib[andList[i]]
                    else:
                        a = intersection
                    b = self.resLib[andList[i+1]] # get second
                    # this may raise an exception if not possible
                    intersection = a & b # operator overloadin
            # store resKey in dict, store as string
            self.cmpTree.append(self._resAssign(self.resId, intersection))
            self._resIdIncr()
        self.cmpTree = self.OR.join(self.cmpTree)
        #print _MOD, 'cmpTree', self.cmpTree

    def _cmpSegment(self):
        """a bound sieve, uss a newly created segment"""
        # clear first
        self.cmpTree = []
        # will use z if set elsewheres
        seg = self.segment('exp')
        if seg == []: # empty set
            raise IndexError('empty segment; segment compression not possible')
        else:
            segObj = CompressionSeg(seg, self.z)
            for resObj in segObj():
                self.cmpTree.append(self._resAssign(self.resId, resObj))
                self._resIdIncr()
            self.cmpTree = self.OR.join(self.cmpTree)
        #print _MOD, 'cmpTree', self.cmpTree



    #-----------------------------------------------------------------------||--

    def segment(self, state=None, n=0, z=None, format=None):
        """
        >>> a = Sieve('3@11')
        >>> b = Sieve('2&4&8|5')
        >>> c = Sieve('(5|2)&4&8')
        >>> a.segment('exp')
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59, 62, 65, 68, 71, 74, 77, 80, 83, 86, 89, 92, 95, 98]
        >>> c.segment('cmp', format='wid')
        [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]
        """

        if state == None:
            state = self.state
        if z == None:
            z = self.z
        if format == None:
            format = self.segFmt

        if state == 'exp':
            evalStr = copy.copy(self.expTree)
        elif state == 'cmp':
            evalStr = copy.copy(self.cmpTree)
        keys = self._resKeys(state)

        # only NEG that remain are those applied to groups
        # replace all remain NEG in the formula w/ "1@1-"
        # as long as binary negation is evaluated before & and |, this will work
        # see http://docs.python.org/ref/summary.html
        # must do this before converting segments (where there willneg numbers)
        resObj = Residual(1,0,0,z) # create a temporary residual 1@!
        setStr = self._setInstantiateStr(resObj()) # get segment
        evalStr = evalStr.replace('-', ('%s-' % setStr))
        # replace residuals (this will add - as -numbers)
        for key in keys:
            evalStr = evalStr.replace(key, self._resToSetStr(key, n, z))
        # convert all braces to parenthesis
        evalStr = evalStr.replace(self.LGROUP,'(')
        evalStr = evalStr.replace(self.RGROUP,')')

        # this may raise an exception if mal-formed
        try:
            seg = eval(evalStr)
        except SyntaxError:
            raise SyntaxError('badly formed logical string (%s)' % evalStr)

        seg = list(seg)
        seg.sort()
        if format in ['bin', 'binary']:
            return unit.discreteBinaryPad(seg, z)
        elif format in ['unit']:
            return unit.unitNormRange(seg, z)
        elif format in ['wid', 'width']:
            wid = []
            for i in range(0, len(seg)-1):
                wid.append((seg[i+1]-seg[i]))
            return wid
        else: # int, integer
            return seg

    def period(self, state=None):
        """two periods are possible; if residuals are the same
        for both exp and cmd, only one is calculated
        period only calculated the fist time this method is called

        >>> a = Sieve('3@11')
        >>> a.period()
        3
        >>> b = Sieve('2&4&8|5')
        >>> b.period()
        40
        >>> c = Sieve('(5|2)&4&8')
        >>> c.period()
        40
        """
        if state == None:
            state = self.state
        # check and see if exp has been set yet
        if self._expPeriod == None:
            self._initPeriod()

        if state == 'exp': return self._expPeriod
        elif state == 'cmp': return self._cmpPeriod

    def __call__(self, n=0, z=None, format=None):
        return self.segment(self.state, n, z, format)


# this method is not used anywhere
#     def _segmentConvert(self, format, seg, z):
#         """convert integer to various formats"""
#         if format in ['bin', 'binary']:
#             return unit.discreteBinaryPad(seg, z)
#         elif format in ['unit']:
#             return unit.unitNormRange(seg, z)
#         elif format in ['wid', 'width']: # difference always equal to m
#             wid = [self.m] * (len(seg)-1) # one shorter than segment
#             return wid
#         elif format in ['int', 'integer']: # int, integer
#             return seg
#         else:
#             raise TypeError, '%s not a valid sieve format string.' % format

    def collect(self, n, zMinimum, length, format, zStep=100):
        """collect a segment to meet a desired length for the segment
        z must be extended automatically to continue to search from zMinimum
        zStep is the size of each z used to cycle through all z

        this seems to only work properly for float and ineger sieves

        >>> a = Sieve('3@11')
        >>> a.collect(10, 100, 10, 'int')
        [102, 105, 108, 111, 114, 117, 120, 123, 126, 129]
        """
        found = []
        p = zMinimum # starting value
        zExtendCount = 0
        while zExtendCount < 10000: # default max to break loops
            zMin = p
            zMax = p + zStep 

            # must collect non width formats as integer values; then convert
            if format in ['wid', 'width']:
                segmentPartial = self.segment(self.state, n, list(range(zMin, zMax)), format)
            else: # if a unit, need to start with integers
                segmentPartial = self.segment(self.state, n, list(range(zMin, zMax)), 'int')

            found = found + segmentPartial[:]
            p = p + zStep # increment start value
            zExtendCount = zExtendCount + 1 # fail safe

            if len(found) >= length:
                break

        # trim any extra
        seg = found[:length] 
        if len(seg) != length:
            raise ValueError('desired length of sieve segment cannot be found')

        # only width format comes out correct after concatenation
        # for unit and binary, derive new z based on min and max
        if format in ['unit']:
            # make z to minimum and max value found
            return unit.unitNormRange(seg, list(range(seg[0], seg[-1]+1)))
        elif format in ['bin', 'binary']:
            # make to minimum and max value found
            return unit.discreteBinaryPad(seg, list(range(seg[0], seg[-1]+1)))
        else:
            return seg


    def repr(self, state=None, style=None):
        """style of None is use for users; adds | to singel residuals
        style abs (absolute) does not add | tos single residual class"""
        if state == None:
            state = self.state
        if state == 'exp':
            msg = copy.copy(self.expTree)
        elif state == 'cmp':
            msg = copy.copy(self.cmpTree)
        # get keys for this library
        keys = self._resKeys(state)
        for key in keys:
            msg = msg.replace(key, self.resLib[key].repr(style))
        return msg

    def __str__(self):
        return self.repr()





#-----------------------------------------------------------------||||||||||||--
# high level utility obj

class SievePitch:
    """may raise the following exceptions:
    SyntaxError, ValueError, TypeError, KeyError, error.PitchSyntaxError
    """
    
    def __init__(self, usrStr):
        """
        >>> a = SievePitch('4@7')
        """
        self.psLower = None #'c3'
        self.psUpper = None #'c5' # default ps Range
        self.psOrigin = None # psLower # default
        self.sieveLogStr = '' # logical sieve string
        # this may raise various exceptions including
        # error.PitchSyntaxError, SyntaxError
        self.sieveObj = None
        self._parseUsrStr(usrStr)


    def _parseUsrStr(self, usrStr):
        """when entering a pitch sieve, the logical argument
        must be separated from the range args by commas, i.e.
        8(n+4)|6(n+5)|4(n+1), c3, c8 # no commas can be used elsewhere
        provide defaults if no range is given
        range can be given w/ letter names, as well as ps class number 0 = c4

        >>> a = SievePitch('4@7')
        >>> a._parseUsrStr('13@3|13@6|13@9, c2, c7')
        
        """
        psLower = None
        psUpper = None
        psOrigin = None
        eld = None

        strList = usrStr.split(',')
        i = 0
        for element in strList:
            element = element.strip()
            if element != '':
                if i == 0: 
                    self.sieveLogStr = element
                if i == 1: 
                    psLower = element
                if i == 2: 
                    psUpper = element
                if i == 3: 
                    psOrigin = element
                if i == 4: 
                    eld = element
            i = i + 1
        if self.sieveLogStr == '': # nothing was assigned to it
            return None
        # parse pitch bounaries; accept either string pcs or 
        if psLower != None:
            self.psLower = pitchTools.Pitch(psLower)
        else:
            self.psLower = pitchTools.Pitch('c3', 'psName')
        if psUpper != None:
            self.psUpper = pitchTools.Pitch(psUpper)
        else:
            self.psUpper = pitchTools.Pitch('c5', 'psName')
        if psOrigin != None:
            self.psOrigin = pitchTools.Pitch(psOrigin)
        else: # use psLower value
            self.psOrigin = pitchTools.Pitch(self.psLower.get('psName'), 'psName')

        # scalable eld not yet implemented
        if eld != None:
            self.eld = drawer.strToNum(eld, 'num', .00001, 100) # min, max
            if self.eld == None: # out fo range
                self.eld = 1
        else: 
            self.eld = 1 # default
        
        # create sieve ovject; this may raise exceptions
        self.sieveObj = Sieve(self.sieveLogStr)
            

    def __call__(self):
        """return a sieve segment mapped to integer range b/n
        psLower and psUpper
        note that @0 becomes psLower

        >>> a = SievePitch('4@7&5@4')
        >>> a()
        [7]

        >>> a = SievePitch('13@3|13@6|13@9, c1, c10, 1')
        >>> a()
        [-35, -32, -29, -22, -19, -16, -9, -6, -3, 4, 7, 10, 17, 20, 23, 30, 33, 36, 43, 46, 49, 56, 59, 62, 69, 72]


        >>> a = SievePitch('3@0, c4, c5, c4, .5')
        >>> a.eld
        0.5
        >>> a()
        [0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 12.0]
        >>> a = SievePitch('3@0, c4, c5, c#4, .5')
        >>> a()
        [0.5, 2.0, 3.5, 5.0, 6.5, 8.0, 9.5, 11.0]
        """
        min = self.psLower.get('psReal')
        max = self.psUpper.get('psReal')
        z = list(range(int(min), int(max+1)))
        n = self.psOrigin.get('psReal') # shift origin

        # get integer range
        if self.eld == 1:
            sieveSeg = self.sieveObj(n, z) # make value negative

        else: # microtonal eld
            # returns all posisble values in this range
            valList = unit.unitNormStep(self.eld, min, max, normalized=False)
            #environment.printDebug(valList)

            # this z will not be shifted
            # need to get list of apropriate size
            z = list(range(0, len(valList))) 
            
            # get a binary segment
            binSeg = self.sieveObj(n, z, 'bin')
            sieveSeg = []
            # when there is activity on the unitSeg, return the value
            for i in range(len(binSeg)):
                if binSeg[i] == 1:
                    sieveSeg.append(valList[i])
            
        return sieveSeg






#-----------------------------------------------------------------||||||||||||--

class TestOld:
    def __init__(self):
        self.testTimePoint()
        self.testIntersection()
        #self.testSieveParse()
        self.testSievePitch()
        self.testSieve()

    #-----------------------------------------------------------------------||--
    # may be usefull for testing
    def complement(self, set, z=None):
        """not, exclusion
        may be notated, for subset F, as F' or F w/ line over top
        """
        if z == None:
            z = list(range(0,100))
        ab = []
        for value in z:
            if value not in set: # dont do anything
                ab.append(value)
        return ab
    
    def intersection(self, a, b):
        """and
        notated with an inverted U"""
        ab = []
        for value in a + b: # look at each value
            if value in a and value in b:
                if value not in ab:
                    ab.append(value)
        return ab


    #-----------------------------------------------------------------------||--
    def _clean(self, l):
        "cleans a list"
        return str(l).replace(' ', '')[1:-1]



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


    def testIntersection(self):
        a = Residual(3)
        testArgs = [(3,6,2,5), (4,6,1,3), (5,4,3,2), ]
        for m1, m2, n1, n2 in testArgs:
            a = Residual(m1, n1)
            b = Residual(m2, n2)
            c = a & b           # do intersection


    def testSieveParse(self):
        testArgs = ['-5 | 4 & 4sub3 & 6 | 4 & 4', 
                 '2 or 4 and 4 & 6 or 4 & 4', 
                 3,
                 '3 and 4 or not 3,1 and 4,1 or not 3 and 4,2 or not 3,2 and 4,3',
                 (2,4,6,8),
                 (1,6,11,16,17),
                    ]
        for arg in testArgs:
            testObj = Sieve(arg)
            post = testObj(0, list(range(0, 30)))


    def testSievePitch(self):
        testObj = SievePitch('-5 | 4 & 4sub3 & 6 , b3, f#4')
        testObj = SievePitch('-5 | 4 & 4sub3 & 6 ')
        post = testObj.psLower, testObj.psUpper
        post = testObj()


    def testTimePoint(self):
        args = [(3,6,12),(0, 6, 12, 15, 18, 24, 30, 36, 42),
                  (4,6,13),
            (2, 3, 4, 5, 8, 9, 10, 11, 14, 17, 19, 20, 23, 24, 26, 29, 31),
              #  (3,23,33,47,63,70,71,93,95,119,123,143,153,167),
                  (0,2,4,5,7,9,11,12,14,16,17,19,21,23,24),
                  (1,2,3,4,5,6,7,8,9,10),
                (-8,-6,-4,-2,0,2,1),
                 ]
        for src in args:
            obj = CompressionSeg(src)
            sObj = Sieve(str(obj))
            post = sObj()


    def testSieve(self):
        z = list(range(0,100))
        usrStr = '3@2 & 4@1 | 2@0 & 3@1 | 3@3 | -4@2'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '3@2&4@1|2@0&3@1|3@0|-4@2')

        usrStr = '-(3@2 & -4@1 & -(12@3 | 12@8) | (-2@0 & 3@1 | (3@3)))'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '-{3@2&-4@1&-{12@3|12@8}|{-2@0&3@1|{3@0}}}')


        # 'example from Flint, on Psapha'
        usrStr = '[(8@0 | 8@1 | 8@7) & (5@1 | 5@3)] |   [(8@0 | 8@1 | 8@2) & 5@0] | [8@3 & (5@0 | 5@1 | 5@2 | 5@3 | 5@4)] | [8@4 & (5@0 | 5@1 | 5@2 | 5@3 | 5@4)] | [(8@5 | 8@6) & (5@2 | 5@3 | 5@4)] | (8@1 & 5@2) | (8@6 & 5@1)'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '{{8@0|8@1|8@7}&{5@1|5@3}}|{{8@0|8@1|8@2}&5@0}|{8@3&{5@0|5@1|5@2|5@3|5@4}}|{8@4&{5@0|5@1|5@2|5@3|5@4}}|{{8@5|8@6}&{5@2|5@3|5@4}}|{8@1&5@2}|{8@6&5@1}')

        # 'major scale from FM, p197'
        usrStr = '(-3@2 & 4) | (-3@1 & 4@1) | (3@2 & 4@2) | (-3 & 4@3)'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '{-3@2&4@0}|{-3@1&4@1}|{3@2&4@2}|{-3@0&4@3}')

        # 'nomos alpha sieve'
        usrStr = '(-(13@3 | 13@5 | 13@7 | 13@9) & 11@2) | (-(11@4 | 11@8) & 13@9) | (13@0 | 13@1 | 13@6)'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '{-{13@3|13@5|13@7|13@9}&11@2}|{-{11@4|11@8}&13@9}|{13@0|13@1|13@6}')



#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)



# sieve that break LCM
# >>> t = sieve.Sieve((3,99,123123,2433,2050))
