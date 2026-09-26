# -----------------------------------------------------------------||||||||||||--
# Name:          unit.py
# Purpose:       unit interval tools
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest

from athenaCL.libATH import drawer

_MOD = "unit.py"


# -----------------------------------------------------------------||||||||||||--
# unit interval tools


class UnitException(Exception):
    pass


# -----------------------------------------------------------------||||||||||||--
def seriesMinMax(series):
    """given any list of numbers, return e min and e max
    must convert to list to allow sorting of array or other sequence objects

    >>> seriesMinMax([3,4,5])
    (3, 5)
    """
    seriesLen = len(series)
    if seriesLen == 1:
        return series[0], series[0]
    elif seriesLen == 0:
        raise ValueError("series with no values given")
    q = []
    for val in series:
        q.append(val)
    q.sort()
    return q[0], q[-1]


def tableMinMax(table):
    """find min max for embedded lists"""
    q = []
    for row in table:
        q = q + list(seriesMinMax(row))  # collect min max of each row
    q.sort()
    return q[0], q[-1]


# -----------------------------------------------------------------||||||||||||--
def unitNorm(value, valueRange):
    """Normalize value within the unit interval.

    >>> unitNorm(3, (3,10))
    0.0
    >>> unitNorm(1, (3,10)) # values are not limited here
    -0.285714...
    >>> unitNorm(6.5, (3,10))
    0.5
    >>> unitNorm(10, (3,10))
    1.0
    >>> unitNorm(17, (3,10))
    2.0
    """
    min, max = seriesMinMax(valueRange)
    span = max - min

    dif = value - min
    if drawer.isInt(dif):
        dif = float(dif)
    if span != 0:
        return dif / span
    else:  # fill value if span is zero
        return 0


def unitNormRange(series, fixRange=None):
    """read all values from a list
    normalize values within min and maximum of series

    >>> unitNormRange([0,3,4])
    [0.0, 0.75, 1.0]
    """
    if fixRange != None:
        fixRange.sort()
        min = fixRange[0]
        max = fixRange[-1]
    else:  # find max and min from values
        min, max = seriesMinMax(series)
    span = max - min
    unit = []
    if len(series) > 1:
        for val in series:
            dif = val - min
            if drawer.isInt(dif):
                dif = float(dif)
            if span != 0:
                unit.append(dif / span)
            else:  # fill value if span is zero
                unit.append(0)
    else:  # if one element, return 0 (could be 1, or .5)
        unit.append(0)
    return unit


def unitNormRangeTable(table, fixRange=None):
    """read all values from a a list
    normalize values wihtin min and maximum of series

    >>> unitNormRangeTable([[4,-2],[234,0],[3,7]])
    [[0.025423728813559324, 0.0], [1.0, 0.0084745762711864406],
        [0.021186440677966101, 0.038135593220338986]]
    """
    if fixRange != None:
        fixRange.sort()
        min = fixRange[0]
        max = fixRange[-1]
    else:  # find max and min from values
        min, max = tableMinMax(table)
    span = max - min
    unit = []
    i = 0
    for row in table:
        unit.append([])
        for val in row:
            dif = val - min
            if drawer.isInt(dif):
                dif = float(dif)
            if span != 0:
                unit[i].append(dif / span)
            else:  # fill value if span is zero
                unit[i].append(0)
        i = i + 1
    return unit


def unitNormEqual(parts):
    """given a certain number of parts, return a list unit-interval values
    between 0 and 1, w/ as many divisions as parts; 0 and 1 always inclusive
    >>> unitNormEqual(3)
    [0.0, 0.5, 1]
    """
    if parts <= 1:
        return [0]
    elif parts == 2:
        return [0, 1]
    else:
        unit = []
        step = 1.0 / (parts - 1)
        for y in range(0, parts - 1):  # one less value tn needed
            unit.append(y * step)
        unit.append(1)  # make last an integer, add manually
        return unit


def unitNormStep(step, a=0, b=1, normalized=True):
    """given a step size and an a/b min/max range, calculate number of parts
    to fill step through inclusive a,b
    then return a unit interval list of values necessary to cover region

    Note that returned values are by default normalized within the unit interval.

    >>> unitNormStep(.5, 0, 1)
    [0.0, 0.5, 1]

    >>> unitNormStep(.5, -1, 1)
    [0.0, 0.25, 0.5, 0.75, 1]

    >>> unitNormStep(.5, -1, 1, normalized=False)
    [-1, -0.5, 0.0, 0.5, 1.0]

    >>> post = unitNormStep(.25, 0, 20)
    >>> len(post)
    81
    >>> post = unitNormStep(.25, 0, 20, normalized=False)
    >>> len(post)
    81

    """
    if a == b:
        return []  # no range, return boundary
    if a < b:
        min = a
        max = b
    if a > b:
        min = b
        max = a
    # find number of parts necessary
    count = 0  # will count last, so dont count min at begining
    values = []
    x = min
    while x <= max:
        values.append(x)  # do before incrementing
        x += step
        count += 1

    if normalized:
        return unitNormEqual(count)
    else:
        return values


def unitNormProportion(series):
    """normalize values w/n unit interval, where max is determined
    by the sum of the series (proportional section of total)
    this is the same as that used for durFraction in Path

    >>> unitNormProportion([0,3,4])
    [0.0, 0.42857142857142855, 0.5714285714285714]
    >>> unitNormProportion([1,1,1])
    [0.33333333333333331, 0.33333333333333331, 0.33333333333333331]
    """
    # note: negative values should be shifted to positive region first
    sum = 0
    for x in series:
        if x < 0:
            raise ValueError("series members should be positive")
        sum = sum + x
    assert sum != 0
    unit = []  # weights on the unit interval; sum == 1
    for x in series:
        unit.append((x / float(sum)))
    return unit


def unitNormAccumulate(series):
    """give a series of values, all within the unit interval, treate
    each as time (x) values, and create a new unit interval spacing
    that is proportional to the sequence of series durations

    if assume zero is start, means that there will be one more point
    than in source
    0, 0+n1, 0+n2, 0+n3

    >>> unitNormAccumulate([.4,.1,.4,.1])
    [0.0, 0.40000000000000002, 0.5, 0.90000000000000002, 1.0]

    >>> unitNormAccumulate([.8,.2,.5,.1])
    [0.0, 0.5, 0.625, 0.9375, 1.0]

    >>> unitNormAccumulate([.5,.5,.5])
    [0.0, 0.33333333333333331, 0.66666666666666663, 1.0]
    """
    t = 0
    accume = [t]
    for step in series:
        t = t + step
        accume.append(t)
    unit = []
    for pos in accume:
        unit.append(float(pos) / t)  # t is max
    return unit


def denorm(value, a, b):
    """take a normalized value; shift it between min and max
    assumes min and max is relevant

    >>> denorm(.5, 10, 20)
    15.0
    >>> denorm(.5, -20, 20)
    0.0
    >>> denorm(10, -20, 20)
    Traceback (most recent call last):
    UnitException: value (10) must be in unit interval
    """
    if value < 0 or value > 1:  # must be normalized
        raise UnitException("value (%s) must be in unit interval" % value)

    if a == b:
        return a  # no range, return boundary
    if a < b:
        min = a
        max = b
    if a > b:
        min = b
        max = a
    # value times range, plus lower boundary
    scale = (float(value) * (max - min)) + min
    return scale


def denormList(unit, a, b):
    """given a list unit interval values b/n 0 and 1, denorm b/n a and b

    >>> denormList([.2, .5], 10, 20)
    [12.0, 15.0]
    """
    for value in unit:
        if value < 0 or value > 1:  # must be normalized
            raise UnitException("value (%s) must be in unit interval" % value)

    if a == b:
        return a  # no range, return boundary
    if a < b:
        min = a
        max = b
    if a > b:
        min = b
        max = a
    return [((float(value) * (max - min)) + min) for value in unit]


def interpolate(value, a, b):
    """switch between two values based on q value w/n unit interval;
    low q is a, high q is b
    low and high are not relevant

    >>> interpolate(.5, 10, 20)
    15.0
    >>> interpolate(.8, 10, 20)
    18.0
    """
    if value < 0 or value > 1:  # must be normalized
        raise UnitException("value (%s) must be in unit interval" % value)
    if value == 0:
        return a
    if value == 1:
        return b
    # scale each value and sum; min, max, and sign do not matter
    return (a * (1 - value)) + (b * value)


def limit(value, method=None):
    """may need to use w/ denorm and others above tt do not already limit vals"""
    if value > 1:
        return 1
    elif value < 0:
        return 0
    else:
        return value


# -----------------------------------------------------------------||||||||||||--


def unitBoundaryEqual(parts):
    """return a list of min/mean/max values for a unit interval divided
    into user supplied partions
    note: lower and upper boundaries do overlap

    >>> unitBoundaryEqual(3)
    [(0, 0.16666666666666666, 0.33333333333333331), (0.33333333333333331, 0.5,
    0.66666666666666663), (0.66666666666666663, 0.83333333333333326, 1.0)]
    """
    bounds = []
    if parts <= 0:
        raise UnitException("cannot process 0 parts")

    step = 1.0 / parts
    boundL = 0
    boundH = None
    for face in range(0, parts):
        if face != parts - 1:
            boundH = step * (face + 1)
        else:  # last, avoid rounding errors
            boundH = 1.0
        mean = boundL + (step * 0.5)
        bounds.append((boundL, mean, boundH))
        boundL = boundH
    return bounds


def unitBoundaryFree(series):
    """take an arbitrary series, and create unit boundaries
    for n members of a series, there will be n-1 boundaries

    >>> unitBoundaryFree([0,3,4])
    [(0.0, 0.375, 0.75), (0.75, 0.875, 1.0)]
    """
    unit = unitNormRange(series)
    bounds = []
    boundL = None
    boundH = None
    for i in range(0, len(unit)):
        if i != len(unit) - 1:  # not last
            boundL = unit[i]
            boundH = unit[i + 1]
            mean = (boundL + boundH) * 0.5
            bounds.append((boundL, mean, boundH))
        else:  # last, avoid rounding errors
            break
    return bounds


def unitBoundaryProportion(series):
    """take an series of parts of an implied sum, create unit boundaries
    for n members of a series, there will be n boundaries
    note: zero cannot be an entry (not a valid proportion)

    >>> unitBoundaryProportion([1,1,2])
    [(0, 0.125, 0.25), (0.25, 0.375, 0.5), (0.5, 0.75, 1.0)]
    """
    # series cannot have non-specified values, that is, 0
    if 0 in series:
        raise UnitException("cannot process series that contains zero")

    unit = unitNormProportion(series)
    bounds = []
    boundL = None
    boundH = None
    sum = 0
    for i in range(0, len(unit)):
        if i != len(unit) - 1:  # not last
            boundL = sum
            boundH = sum + unit[i]
            sum = sum + unit[i]
            mean = (boundL + boundH) * 0.5
            bounds.append((boundL, mean, boundH))
        else:  # last, avoid rounding errors
            boundL = sum
            boundH = 1.0
            mean = (boundL + boundH) * 0.5
            bounds.append((boundL, mean, boundH))
    return bounds


def unitBoundaryPos(val, bounds):
    """value is between 0 and 1, map to a value within bounds
    there is a slight error in that the last value goes to 1
    bounds must be sorted

    returns position w/n bounds as index value, 0 to n-1

    >>> unitBoundaryPos(.4, [(0, 0.125, 0.25), (0.25, 0.375, 0.5), (0.5, 0.75, 1.0)])
    1
    >>> unitBoundaryPos(.1, [(0, 0.125, 0.25), (0.25, 0.375, 0.5), (0.5, 0.75, 1.0)])
    0

    """
    if val < 0 or val > 1:  # must be normalized
        raise UnitException("value (%s) must be in unit interval" % val)

    # make sure boudns cover complete unit interval
    if bounds[0][0] != 0 or bounds[-1][2] != 1:
        raise UnitException("incomplete bounds")

    if val == 1:  # special case
        return len(bounds) - 1  # last one
    else:
        for i in range(0, len(bounds)):
            a, m, b = bounds[i]
            if val >= a and val < b:  # exception for 1 above
                return i  # return mean


# -----------------------------------------------------------------||||||||||||--


def discreteBinaryPad(series, fixRange=None):
    """take an integer series of values
    fill all spaces with zeros that are not occupied
    the result will always be sorted

    >>> discreteBinaryPad([3,4,5])
    [1, 1, 1]
    >>> discreteBinaryPad([3,20,22])
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1]
    """
    # make sure these are ints
    for x in series:
        if not drawer.isInt(x):
            raise UnitException("non integer value found")

    discrete = []
    if fixRange != None:
        fixRange.sort()  # make sure sorted
        min = fixRange[0]
        max = fixRange[-1]
    else:  # find max and min from values
        seriesAlt = list(copy.deepcopy(series))
        seriesAlt.sort()
        min = seriesAlt[0]
        max = seriesAlt[-1]
    for x in range(min, max + 1):
        if x in series:
            discrete.append(1)
        else:  # not in series
            discrete.append(0)
    return discrete


def discreteCompress(series):
    """takes a series; count the adjacent occurances of the same value
    store as ordered pairs; this is primitive compression

    >>> discreteCompress([3,3,3,2,2,2,8,8,8,8,8,8,8])
    [(3, 3), (2, 3), (8, 7)]

    """
    comp = []
    xLast = None
    xCount = 0
    for i in range(0, len(series)):
        x = series[i]
        if x == xLast or xLast == None:
            xCount += 1
        elif x != xLast:  # new value not the same as last
            comp.append((xLast, xCount))  # store previous series
            xCount = 1  # start at one for this value
        # last value, report
        if i == len(series) - 1:
            comp.append((x, xCount))
        xLast = x
    return comp


# -----------------------------------------------------------------||||||||||||--
def boundaryFit(a, b, f, boundaryMethod):
    """take boundary levels a,b and place f within them
    available methods include wrap, reflect, limit
    used for mask-based parameter objects

    >>> boundaryFit(3, 9, 23, 'limit')
    9
    >>> boundaryFit(3, 9, 10, 'reflect')
    8
    >>> boundaryFit(3, 9, 12, 'wrap')
    6
    >>> boundaryFit(3, 9, 5, 'wrap')
    5
    """
    if a > b:
        min = b
        max = a
    elif a < b:
        min = a
        max = b
    else:  # they are the same
        min = a
        max = a
    period = abs(max - min)
    center = min + (period * 0.5)
    # within boundary
    if f >= min and f <= max:
        return f
    elif f == min or f == max:
        return f
    else:  # out of boundary
        if max == min:
            return center  # if the same, return boundary
        if boundaryMethod == "limit":
            if f > max:
                return max
            elif f < min:
                return min
        elif boundaryMethod == "wrap":
            # shift period to find wihin range
            if f > max:
                while 1:
                    f = f - period
                    if f <= max:
                        break
            elif f < min:
                while 1:
                    f = f + period
                    if f >= min:
                        break
            return f
        elif boundaryMethod == "reflect":
            while f > max or f < min:
                if f > max:
                    f = max - (abs(f - max))
                elif f < min:
                    f = min + (abs(f - min))
                else:
                    break  # f >= min or f <= max
            return f


def boundaryReject(a, b, f, boundaryMethod):
    """place f outside of a and b;

    >>> boundaryReject(3, 9, 23, 'limit')
    23
    >>> boundaryReject(3, 9, 10, 'reflect')
    10
    >>> boundaryReject(3, 9, 12, 'wrap')
    12
    >>> boundaryReject(3, 9, 5, 'wrap')
    -1
    """
    if a > b:
        min = b
        max = a
    elif a < b:
        min = a
        max = b
    else:  # they are the same
        min = a
        max = a
    period = abs(max - min)
    center = min + (period * 0.5)
    # outside of boundary
    if f <= min or f >= max:
        return f
    elif f == min or f == max:
        return f
    else:  # w/n boundary: project outside
        if max == min:
            return center  # if the same, return boundary
        if boundaryMethod == "limit":
            if f < max and f >= center:
                return max  # middle values round up
            elif f > min and f < center:
                return min
        elif boundaryMethod == "wrap":
            # shift period to find wihin range
            if f < max and f >= center:
                while 1:  # add values to bring upward, out of range
                    f = f + period
                    if f >= max:
                        break
            elif f > min and f < center:
                while 1:  # subtract values to bring downward, out of range
                    f = f - period
                    if f <= min:
                        break
            return f
        elif boundaryMethod == "reflect":
            while f < max and f > min:
                if f < max and f >= center:
                    f = max + (abs(f - max))  # add the distance from the value to lim
                elif f > min and f < center:
                    f = min - (abs(f - min))
                else:
                    break  # f >= min or f <= max
            return f


# def boundaryDouble(a, b, c, d, f, boundaryMethod):
#     """place f w/n a and b but not in c and d
#     """
#     if a > b:
#         min = b; max = a
#     elif a < b:
#         min = a; max = b
#     else: # they are the same
#         min = a; max = a
#
#     if c > d:
#         minNot = d; maxNot = c
#     elif c < d:
#         minNot = c; maxNot = d
#     else: # they are the same
#         minNot = c; maxNot = c
#
#     post = boundaryFit(min, max, f, boundaryMethod)


# -----------------------------------------------------------------||||||||||||--
class FunnelUnitException(Exception):
    pass


# -----------------------------------------------------------------||||||||||||--


class FunnelUnit:
    def __init__(self, series):
        """
        >>> a = FunnelUnit([3,4,20])
        """
        self.srcSeries = series
        self.srcSeriesUnit = unitNormRange(series)

        self.binaryMap = discreteBinaryPad(series)
        # create boundary w/n unit interval of binary rep
        self.binaryBound = unitBoundaryEqual(len(self.binaryMap))
        self.discrComp = discreteCompress(self.binaryMap)

        # print 'len series', len(series)
        # print 'len bound', len(self.binaryBound)
        # print self.binaryMap

    def _seriesPosToBinaryPos(self, pos):
        """giving a pos in series (0 start) return bin position
        if"""
        count = 0  # number of 1's in range
        if pos >= len(self.srcSeries):
            raise FunnelUnitException("series position out of range")
        for i in range(0, len(self.binaryMap)):
            if self.binaryMap[i] == 1:
                if count == pos:
                    return i
                count = count + 1

    def _binaryPosToSeriesPos(self, pos):
        if pos >= len(self.binaryMap):
            raise FunnelUnitException("binary position out of range")
        if self.binaryMap[pos] != 1:
            return None
        count = 0  # series position
        for i in range(0, len(self.binaryMap)):
            if self.binaryMap[i] == 1:
                if i == pos:
                    return count
                count = count + 1

    # -----------------------------------------------------------------------||--
    def findReject(self, val):
        """take the binary map, and divide the zero portions appropriate

        >>> a = FunnelUnit([0,1,2,3,4,20])
        >>> a.findReject(0)
        0.0
        >>> a.findReject(.1)
        0.1000...
        """
        if val < 0 or val > 1:
            raise FunnelUnitException("value (%s) must be in unit interval" % val)
        # get position w/n biary bound
        i = unitBoundaryPos(val, self.binaryBound)
        if self.binaryMap[i] == 1:  # if 1, return that position
            pos = self._binaryPosToSeriesPos(i)
            return self.srcSeriesUnit[pos]
        else:  # no series value w/n this boundary
            return None

    def _findAdjacent(self, pos):
        """given a position in the binary array, determine
        lower and upper positions that have a 1

        >>> a = FunnelUnit([0,1,2,3,4,20])
        >>> a._findAdjacent(10)
        (4, 20)
        """
        posLower = None
        posUpper = None
        # get upper
        for i in range(pos + 1, len(self.binaryMap)):
            if self.binaryMap[i] == 1:
                posUpper = i
                break
        # get lower
        posArray = list(range(0, pos))
        posArray.reverse()
        for i in posArray:
            if self.binaryMap[i] == 1:
                posLower = i
                break
        # check for erros
        # print _MOD, 'pos, posLower, posUpper', pos, posLower, posUpper

        if posLower == None or posUpper == None:
            raise FunnelUnitException("neighbor positions cannot be found")

        return posLower, posUpper

    def findNearest(self, val):
        """
        >>> a = FunnelUnit([0,1,2,3,4,20])
        >>> a.findNearest(.5)
        0.2000...
        >>> a.findNearest(.8)
        1.0
        """
        if val < 0 or val > 1:
            raise FunnelUnitException("value (%s) must be in unit interval" % val)
        # get position w/n biary bound
        i = unitBoundaryPos(val, self.binaryBound)
        if self.binaryMap[i] == 1:  # if 1, return that position
            pos = self._binaryPosToSeriesPos(i)
            return self.srcSeriesUnit[pos]
        else:  # no series value w/n this boundary
            absPos = 0
            for j in range(0, len(self.discrComp)):
                x, count = self.discrComp[j]
                # do not need to worry about boudnary conditions, as this
                # value will never be the last
                relPos = 0
                midCount = None
                for k in range(0, count):  # simulate index values
                    if absPos == i:  # the area looking for
                        posLower, posUpper = self._findAdjacent(absPos)
                        midCount = count  # store this compressed
                        break
                    relPos = relPos + 1
                    absPos = absPos + 1
                if midCount != None:  # done, break
                    break
            # determine winner
            if midCount % 2 == 0:  # even
                relMid = midCount / 2  # middle-upper index w/n count
            else:  # odd, there is a middle
                relMid = midCount / 2  # middle index w/n count

            if relPos < relMid:
                pos = self._binaryPosToSeriesPos(posLower)
            else:
                pos = self._binaryPosToSeriesPos(posUpper)
            return self.srcSeriesUnit[pos]


#     def test(self):
#         max = 40
#         print 'findReject'
#         for x in range(0,max+1):
#             print self.findReject(x/float(max))
#         print '\nfindNearest'
#         for x in range(0,max+1):
#             print self.findNearest(x/float(max))


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
