#-----------------------------------------------------------------||||||||||||--
# Name:          quantize.py
# Purpose:       store tools for quantizing and funneling.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2006-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest

_MOD = 'quantize.py'


def funnelBinary(h, a, b, f, hDirection):
    """take boundary levels a,b and place f in relation depending on h
    h is threshold, hDirection determine what happens when at threshond"""
    if a > b:
        min = b
        max = a
    elif a < b:
        min = a
        max = b
    else: # they are the same
        min = a
        max = a
    if f > h: return max
    elif f < h: return min
    elif f == h: # match conditioni
        if hDirection == 'match': return h
        elif hDirection == 'upper': return max
        elif hDirection == 'lower': return min


#-----------------------------------------------------------------||||||||||||--
class Quantizer:

    def __init__(self, looplimit=999):
        """grid is a finite list of values in a list; this values
        will be continued in either direction if necessary

        >>> a = Quantizer()
        """
        self.LOOPLIMIT = looplimit
        self.grid = None
        self.gridRetro = None
        
    def _findLowerUpper(self, value, gridRef):
        """gridRef is the reference value to which the grid is shifted
        given a reference value, add or subtract values from the grid
        to find a lower and upper boundary
        """
        init = copy.copy(gridRef) # get lowest value
        if init >= value: move = 'down'
        elif init < value: move = 'up'
        
        n = 1
        cycle = 0
        stepLast = [copy.copy(init)] # order does not matter
        while 1:
            if move == 'down': # dont add one, as starts in reverse
                step = self.gridRetro[(n-1)%len(self.grid)]
                step = stepLast[0] - step
            else: # add one to account for first step
                step = self.grid[n%len(self.grid)]
                step = stepLast[0] + step
            #print _MOD, 'got step', step
            n = n + 1 # module does not require check of value
            if n % len(self.grid) == 0:
                cycle = cycle + 1
            
            stepLast.append(step) # two values, order does not matter 
            stepLast.sort() # min, max
            #print _MOD, 'stepLast sorted', stepLast                 
            if value >= stepLast[0] and value <= stepLast[1]:
                return stepLast[0], stepLast[1]
            stepLast = [] # clear
            stepLast.append(copy.copy(step)) # add previous step
        
            if n >= self.LOOPLIMIT: # around 1000 
                print(_MOD, 'failed to find boundray neighbors')
                return None, None
        
    def updateGrid(self, grid):
        """can be called each time attract is called for dynamic grid
        can be called once for static grid"""
        if len(grid) <= 0: # need more values
            raise ValueError('grid must have more than 1 value')
        self.grid = grid
        self.gridRetro = grid[:]
        self.gridRetro.reverse()
        
    def attract(self, fill, pull=1, gridRef=0):
        """gridRef is the referecne value to which the grid is shift
        use the grid to fill value
        pull is a range of variation allowed"""
        # within boundary
        lower, upper = self._findLowerUpper(fill, gridRef)
        if lower == upper: return lower
        difLower = abs(lower - fill)
        difUpper = abs(upper - fill)
        if difLower >= difUpper: # gt or equal to round up
            difMeasure = difUpper # lower is larger
            gridPoint = upper # upper is smaller
            dir = 'up' # which direction id boundary
        else: 
            difMeasure = difLower
            gridPoint = lower 
            dir = 'down'
        if pull == 1: # no attraction, get grid point
            return gridPoint
        else: # get a random uniform value as scale of dif Measure
            # gridMeasure is always positive
            # if pull is 1, deviate is 0, out is grid
            # if pull is 0, deviate returns point to iriginal value
            deviate = difMeasure * (1-pull)
            if dir == 'up': # grid point is above, bring down
                return gridPoint - deviate
            else: # grid point is below, bring up
                return gridPoint + deviate


#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)



