#-----------------------------------------------------------------||||||||||||--
# Name:          bpf.py
# Purpose:       break point functions
#
# Authors:       Maurizio Umberto Puxeddu
#                    Christopher Ariza
#
# Copyright:     (c) 2007-2010 Christopher Ariza
#                (c) 2000-2001, Maurizio Umberto Puxeddu
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import math
import unittest, doctest


from athenaCL.libATH.omde.functional import Function, FunctionModel


#-----------------------------------------------------------------||||||||||||--
# base class used for all varieties

class BPF(Function):
    """
    BPF(pairs)
    base class for all break-point functions
    """
    def __init__(self, pairs, periodic=0):
        """
        Return a BPF instance.
        
        pair is the list of pairs (time, value).
        At lease the pairs should be passed, otherwise
        a ValueError exception is raised.
        
        if periodic is true the periodic version of
        the call operator is used.
        if periodic is false the aperiodic version of
        the call operator is used.
        
        >>> a = BPF([(0,1), (100, 20)])
        """
        Function.__init__(self)
        self.pairs = [(float(x), float(y)) for x,y in pairs]
        
        self._check_pairs()
        
        if len(self.pairs) < 2:
            raise ValueError, 'Two few pairs (%d)' % len(self.pairs)
        
        self.xStart, junk = self.pairs[0] # x value of first
        self.xEnd, junk = self.pairs[-1] # x value of last
        self.period = self.xEnd - self.xStart 
        
        if periodic:
            self.__call__ = self._evaluate_periodic
        else:
            self.__call__ = self._evaluate_aperiodic
    
    def _evaluate_aperiodic(self, t):
        """
        Aperiodic version of the __call__ operator.
        Values outside the boundaries of the function
        are the same of the boundaries.
        """
        (time0, value0) = self.pairs[0]
        
        # Evaluation before first point
        if t < time0:
            return value0
        
        index = 0 # need to check if after last point
        for (time1, value1) in self.pairs:
            if t < time1: break
            index = index + 1
            time0, value0 = time1, value1
        
        # Evaluation past last point
        if index == len(self.pairs):
            return value0
        
        return self.interpolate(t, time0, value0, time1, value1)
        
    def _evaluate_periodic(self, t):
        """
        Periodic version of the __call__ operator.
        Function repeats outside of the boundaries.

        """
        
        while t < self.xStart: # shift time to a value within the range
            t = t + self.period
        while t >= self.xEnd: 
            t = t - self.period # 
        #            while t < 0: # shift 
        #                 t = t + self.period
        #            # changed to >= rather than >
        #            # > caused divide by 0 error
        #            while t >= self.period: 
        #                 t = t - self.period # 
        
        for (time1, value1) in self.pairs: # find next set of points
            if t < time1: break
            time0, value0 = time1, value1
        
        return self.interpolate(t, time0, value0, time1, value1)
    
    def interpolate(self, time, time0, value0, time1, value1):
      """
      Interpolate the function value between two given points.
      Unimplemented method.
      """
      raise NotImplementedError
    
    def normalize(self):
        """
        Normalize the function in the [-1,1] range.
        """
        max = None
        min = None
        for t, v in self.pairs:
            if max == None or v > max:
                max = v
            if min == None or v < min:
                min = v
                 
        if max == None or min == None:
            return
        
        factor = max - min
        new_pairs = []
        for t, v in self.pairs:
            v = (v - min) / factor
            new_pairs.append((t, v))
        
        self.pairs = new_pairs
        
    def _check_pairs(self):
      time0 = None
      for time1, value1 in self.pairs:
            if time0 is not None and time1 < time0:
                raise ValueError, 'pairs are not in temporal sequence'
            time0 = time1
            

#-----------------------------------------------------------------||||||||||||--
# note: these were all chaged such that pairs are provided as a list of lists
# this allows a list of pairs to be provided as a single object

class PowerSegment(BPF):
    """
    Break-point function with exponential interpolation.
    See the BPF base class for more info.      

    >>> a = PowerSegment([(0, 1), (5, 3), (20, 1)])     
    """
    def __init__(self, pairs, **dict):
        """
        Return a PowerSegment instance.
        Syntax:
        PowerSegment(...points... [, exp=1.0] [, periodic=0])
        Break-points are specified as couples
        (time, value)
        like PowerSegment((0, 1), (5, 3), (20, 1))
        """
        if dict.has_key('exp'):
            self.exponent = dict['exp']
        else: self.exponent = 1.0
        
        if dict.has_key('periodic'):
            periodic = dict['periodic']
        else: periodic = 0
        
        BPF.__init__(self, pairs, periodic)
    
    def interpolate(self, time, time0, value0, time1, value1):
        r = (time - time0)/(time1 - time0)
        
        if value1 == value0:
            return value0
        elif self.exponent == 0.0:
            return value0 + r * (value1 - value0)
        elif self.exponent > 0.0:
            if value1 >= value0:
                return value0 + pow(r, 1.0 + self.exponent) * (value1 - value0)
            else:
                return value1 + (pow(1.0 - r, 1.0 + self.exponent) * 
                                      (value0 - value1))
        else:
            if value1 >= value0:
                return value1 + (pow(1.0 - r, 1.0 - self.exponent) * 
                                      (value0 - value1))
            else:
                return value0 + pow(r, 1.0 - self.exponent) * (value1 - value0)


class LinearSegment(BPF):
    """
    Break-point function with linear interpolation.
    See the BPF base class for more info. 

    >>> a = LinearSegment([(0, 1), (5, 3), (20, 1)])     
    """
    def __init__(self, pairs, **dict):
        """
        Return a LinearSegment instance.
        Syntax:
        LinearSegment(...points... [, exp=1.0] [, periodic=0])
        Break-points are specified as couples
        (time, value)
        like LineSegment((0, 1), (5, 3), (20, 1))
        """
        if dict.has_key('periodic'):
            periodic = dict['periodic']
        else: periodic = 0
        BPF.__init__(self, pairs, periodic)
        
    def interpolate(self, time, time0, value0, time1, value1):
        return value0 + ((time - time0)/(time1 - time0)) * (value1 - value0)
    


class HalfCosineSegment(BPF):
    """
    Break-point function with half-cosine interpolation.
    See the BPF base class for more info. 

    >>> a = HalfCosineSegment([(0, 1), (5, 3), (20, 1)])
    """
    def __init__(self, pairs, **dict):
        if dict.has_key('periodic'):
            periodic = dict['periodic']
        else: periodic = 0
        BPF.__init__(self, pairs, periodic)
      
    def interpolate(self, time, time0, value0, time1, value1):
        x = ((time - time0) / (time1 - time0)) * math.pi + math.pi
        return value0 + ((value1 - value0) * (1 + math.cos(x)) / 2.0)



class NoInterpolationSegment(BPF):
    """
    Break-point function without interpolation.
    See the BPF base class for more info.
    """
    def __init__(self, pairs, **dict):
        """
        Return a NoInterpolationSegment instance.
        Syntax:
        NoInterpolationSegment(...points... [, exp=...])
        Break-point function without interpolation.
        Break-points are specified as couples
        (time, value)
        like NoInterpolationSegment((0, 1), (5, 3), (20, 1))

        >>> a = NoInterpolationSegment([(0, 1), (5, 3), (20, 1)])
        """
        if dict.has_key('periodic'):
            periodic = dict['periodic']
        else: periodic = 0
        BPF.__init__(self, pairs, periodic)
    
    def interpolate(self, time, time0, value0, time1, value1):
        return value0












#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        segment1 = HalfCosineSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), 
                                            (9.0, 8.0)])
        segment2 = NoInterpolationSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), 
                                                    (9.0, 8.0)])
        segment3 = PowerSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), 
                                    (9.0, 8.0)], exp=0.5)
        segment4 = PowerSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), 
                                    (9.0, 8.0)], exp=2.0)
        segment5 = PowerSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), 
                                    (9.0, 8.0)], exp=-0.5)
        segment6 = PowerSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), 
                                    (9.0, 8.0)], exp=-2.0)
        segment7 = LinearSegment([(0.0, 0.0), (4.0, 10.0), (7.0, 5.0), 
                                   (9.0, 8.0)])
        
        t = 0.0
        step = 0.01
        for i in range(1200):
            post = (t, segment1(t), segment2(t), segment3(t), segment4(t),
                    segment5(t), segment6(t), segment7(t))
            t = t + step


#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)


