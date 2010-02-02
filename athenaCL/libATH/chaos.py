#-----------------------------------------------------------------||||||||||||--
# Name:          chaos.py
# Purpose:       chaotic and fractal utilities.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2005-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--



import math
import unittest, doctest


#-----------------------------------------------------------------||||||||||||--
def _fibonacciNumber(goldenUpper, goldenLower, i):
    """return i-th number in the Fibonacci series

    >>> _fibonacciNumber(15,9,1)
    64.0
    """ 
    i = i + 1
    n = ((math.pow(goldenUpper, i) - math.pow(goldenLower, i)) /
            math.sqrt(5.0))
    return math.floor(n)

def fibonacciSeries(j, k):
    """return a subset of the fibonacci series.
    Syntax:
    fibonacciSeries(n)
    Return Fiboacci terms from 0 to n-1.
    fibonacciSeries(j, k)
    Return Fibonacci terms from j to k-1

    >>> fibonacciSeries(10, 20)
    [89.0, 144.0, 233.0, 377.0, 610.0, 987.0, 1597.0, 2584.0, 4181.0, 6765.0]

    >>> fibonacciSeries(2, 20)
    [2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0, 55.0, 89.0, 144.0, 233.0, 377.0, 610.0, 987.0, 1597.0, 2584.0, 4181.0, 6765.0]
    """
    goldenUpper = (1.0 + math.sqrt(5.0)) / 2.0
    goldenLower = (1.0 - math.sqrt(5)) / 2.0
    return [_fibonacciNumber(goldenUpper, goldenLower, i) for i in range(j, k)] 
    
def fibonacciSuccessor(n):
    """given a number from the Fibonacci series, return its
    sucessor in the same series.
    """
    return math.floor((n + 1.0 + math.sqrt(5.0 * n ** 2)) / 2.0)

#-----------------------------------------------------------------||||||||||||--
def verhulst(p, x):
    """logistic map or verhulst equation, w/o state variables"""
    return p * x * (1 - x)


#-----------------------------------------------------------------||||||||||||--
# note: usful to get values for x, (x, y) alternating, and x, y, z, alternating

# x(n+1)=y(n)+1-ax(n)^2
# y(n+1)=bx(n)
# X and Y are the initial values for the system and should both be a number close to zero. A and B control the behaviour of the system. Both should  be a positive value. The system will be stable if the values for A and B    are set following this general guideline:
#A<=(2.0-B)
# or; A+B <= 2.0
#It is not possible to predict the maximum and minimum of the output     values. To 
     
# test values
# a, b
# 1.4, 0.3: chaotic, b/n -1 and 1.2
# .4, .3: period 2, b/n 0 and 1
# 0, .3: cons, b/n 0 and 1
# .1, .1: cons, b/n 0 and 1
# 1, 1: overflow error
# 2, 2: negative infinity
# .5, .5: periodic 2, b/n -1 and 1
# 1.5, .2: chaotic, b/n -1 and 1
# .2, 1.01: used mathworld example

# reccomended x,y start points for strange attractor
# x = 0.63135448, y = 0.18940634.

class Henon:

    def __init__(self, a=1.4, b=0.3, x=0.63135448, y=0.18940634):
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        
    def __call__(self, a=None, b=None):
        """can provide dynamic a and b values
        values are not scaled or altered from original
        in case of overflow error, will distort to accomodate"""
        if a != None: self.a = float(a)
        if b != None: self.b = float(b)
        try:
            xTemp = 1.0 - (self.a * pow(self.x, 2.0)) + self.y
        except OverflowError:
            xTemp = 0.0
        yTemp = self.b * self.x
        self.x = xTemp
        self.y = yTemp
        return self.x, self.y
        
        

#-----------------------------------------------------------------||||||||||||--


# x'=sigma*(y-x)
# y'=Rx-y-xz
# z'=xy-Bz
# 
# X, Y, and Z set the initial conditions. SIGMA, R, and B control the  behaviour of the system. In general, higher values for R and B increase  the chaos, while the same is true for lower values for SIGMA:
# It is not possible to predict the maximum and minimum of the output  values.

# The Lorenz attractor is an attractor that arises in a simplified system of equations describing the two-dimensional flow   of fluid of uniform depth, with an imposed temperature difference DeltaT, under gravity g, with buoyancy a, thermal diffusivity k, and kinematic viscosity v.
# ... representing one of the earliest discoveries of the so-called butterfly effect.
# where X is proportional to convective intensity, Y to the temperature  difference between descending and ascending currents, and Z to the difference  in vertical temperature profile from linearity.
# where [sigma] is the Prandtl number, Ra is the Rayleigh number, Ra, is the critical Rayleigh number, and b is a geometric factor  (Tabor 1989, p. 206). Lorenz took b=8/3 and [sigma]=10 (2.666).

# stable values for positive r if sigma greater than b + 1
# r = 28 is chaotic, r 99.96 is periodic

# b is often 8/3 (2.6666666666666665): others 3/8 (.375)
# act examples:
# s, r, b
# 10 28 1.0
# 10 28 3/8
# 10 28 5.2
# 2  28 3/8
# 10 40 3/8 

class Lorenz:
    """this does not work: produces values that are too small"""
    def __init__(self, r=28, s=10.0, b=2.6666666666, 
                             x=1.0, y=1.0, z=1.0):   
        self.r = float(r)
        self.s = float(s)
        self.b = float(b)

        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
        # dont know where this value of d is coming from
        # little uses .003
        # others use 1.0/128 (0.0078125)
        # mikelson uses .001
        # berg uses .01
        self.d = 0.01
        
    def __call__(self, r=None, s=None, b=None):
        if r != None: self.r = float(r)
        if s != None: self.s = float(s)
        if b != None: self.b = float(b)
        
        xTemp = self.s * (self.y - self.x)
        yTemp = (self.r * self.x) - self.y - (self.x * self.z)
        zTemp = (self.x * self.y) - (self.b * self.z)
        self.x = self.x + (self.d * xTemp)
        self.y = self.y + (self.d * yTemp)
        self.z = self.z + (self.d * zTemp)
        return self.x, self.y, self.z
    





#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        a = Henon()
        b = Lorenz()
        for obj in [a, b]:
            for i in range(500):
                out = obj()
                if len(out) == 2:
                    x, y = out
                    post = str(x).ljust(20), str(y).ljust(20)
                elif len(out) == 3:      
                    x, y, z = out
                    post = str(x).ljust(20), str(y).ljust(20), str(z).ljust(20)
            


#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)


