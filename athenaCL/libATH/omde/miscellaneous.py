#-----------------------------------------------------------------||||||||||||--
# Name:          miscellaneous.py
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# Copyright      (c) 2000-2001, Maurizio Umberto Puxeddu
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

# miscellaneous.py
# Object-oriented Music Description Environment
# Copyright (C) 2000-2001, Maurizio Umberto Puxeddu
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Miscellaneous data generators for OMDE/pmask:
# Range, Accumulator, Quantizer, Mask and List are
# the standard Cmask generators.
# Attactor, Choice, StaticChoice are new in pmask.

import math, copy, types
import unittest, doctest


from athenaCL.libATH.omde import rand # used for omdeRand
omdeRand = rand
from athenaCL.libATH.omde.functional import Function, Generator, make_function

class Range(Generator):
     """
     This generator returns a random value uniformly
     distributed between min and max.

     min and max are constant.

     If you want time-dependent boundaries or a different
     probability distribution use the more generic tendency Mask.
     """
     def __init__(self, min, max):
          """
          Return a Range instance.

          min and max are the range boundaries.
          """
          Generator.__init__(self)
          self.offset = min
          self.delta = max - min

          self.rng = omdeRand.UniformRNG()

     def __call__(self):
          """
          Return the next value.
          """
          return self.offset + self.delta * self.rng.random()

class IntRange(Generator):
     """
     This generator returns an integer random value uniformly
     distributed between min and max.

     min and max are constant.

     If you want time-dependent boundaries or a different
     probability distribution use the more generic tendency Mask.
     """
     def __init__(self, min, max):
          """
          Return a IntRange instance.

          min and max are the range boundaries.
          """
          Generator.__init__(self)
          self.offset = min
          self.delta = max - min

          self.rng = omdeRand.UniformRNG()

     def __call__(self):
          """
          Return then next value.
          """
          return int(self.offset + self.delta * self.rng.random())

class Accumulator(Function):
     """
     This generator adds the values of  a value generator at each call
     and returns the partial result.

     Accumulation can be bound or unbound.
     """
     def __init__(self, value_generator, mode = 'unbound', lower = None, upper = None, sum0 = 0):
          """
          Return an Accumulator instance.

          If mode is 'unbound' (default value) the accumulation is not limited.
          
          If mode is 'reflect' or 'r' or 'mirror' or 'm', the Accumulator folds values
          inside the [lower, upper] range. lower and upper must be specified and may be
          functions.

          If mode 'wrap' or 'w', the Accumulator performs a wrap around at the
          lower and upper limits. lower and upper must be specified and may be
          functions.

          An Accumulator can be initialized by passing the sum0 argument.
          """
          Function.__init__(self)

          self.generator = make_function(value_generator)
          self.sum = sum0

          if mode in ['unbound', 'u']:
                self.add = self.noBounds
          else:
                if upper is None or lower is None:
                     raise ValueError, 'cannot create a bound accumulator with undefined bounds'
                
                self.upper = make_function(upper)
                self.lower = make_function(lower)
                if mode in ['limit', 'l']:
                     self.add = self.limitAtBounds
                elif mode in ['reflect', 'r', 'mirror', 'm']:
                     self.add = self.reflectAtBounds
                elif mode in ['wrap', 'w']:
                     self.add = self.wrapAtBounds
                else:
                     raise ValueError, "mode can only be 'unbound', 'limit', 'reflect', 'mirror' or 'wrap' (got %s)" % mode

     def __call__(self, t):
          """
          """
          self.add(self.generator(t), t)
          return self.sum

     def noBounds(self, value, t):
          self.sum += value

     def limitAtBounds(self, value, t):
          lower = self.lower(t)
          upper = self.upper(t)
          self.sum += value
          if self.sum > upper: self.sum = upper
          elif self.sum < lower: self.sum = lower

     def reflectAtBounds(self, value, t):
          lower = self.lower(t)
          upper = self.upper(t)
          self.sum += value
          if self.sum > upper: self.sum = upper - (self.sum - upper)
          elif self.sum < lower: self.sum = lower + (lower - self.sum)

     def wrapAtBounds(self, value, t):
          lower = self.lower(t)
          upper = self.upper(t)
          self.sum += value
          if self.sum > upper: self.sum = lower + (self.sum - upper)
          elif self.sum < lower: self.sum = upper - (lower - self.sum)

class Quantizer(Function):
     """
     """
     def __init__(self, generator, delta, strength = 1.0, offset = 0.0):
          Function.__init__(self)
          self.generator = make_function(generator)
          self.delta = make_function(delta)
          self.strength = make_function(strength)
          self.offset = make_function(offset)

     def __call__(self, t):
          value = self.generator(t)
          delta = self.delta(t)
          strength = self.strength(t)
          if strength >= 1.0: factor = 0.0
          elif strength <= 0.0: factor = 1.0
          else: factor = 1.0 - strength
          offset = self.offset(t)

          value -= offset

          delta_2 = delta / 2.0
          quantized_value = 0

          quantized_value = int(value / delta) * delta
          difference = value - quantized_value
          
          if difference > delta_2: quantized_value += delta
          if difference < -delta_2: quantized_value -= delta

          difference = value - quantized_value
          quantized_value += difference * factor
          return quantized_value + offset

class Attractor(Function):
     """
     """
     def __init__(self, generator, points, strength = 1.0, exponent = 0.0):
          Function.__init__(self)
          self.generator = make_function(generator)
          self.points = make_function(points)
          self.strength = make_function(strength)
          self.exponent = make_function(exponent)

     def findClosest(self, value, t):
          min = None
          closest_point = None
          for point in self.points:
                distance = value - point(t)
                if min == None or abs(distance) < abs(min):
                     min = distance
                     closest_point = point
          return min, closest_point

     def __call__(self, t):
          value = self.generator(t)
          strength = self.strength(t)
          if strength >= 1.0: factor = 0.0
          elif strength <= 0.0: factor = 1.0
          else: factor = pow(1.0 - strength, pow(2.0, self.exponent))

          difference, closest_point = self.findClosest(value, t)

          return closest_point + difference * factor

class Mask(Function):
     """
     Mask(mainFunction, lowerLimit, upperLimit, exp = 0.0)
     
     The Mask generator is a transformer. It maps the values of the main
     generator in the interval [lowerLimit, upperLimit], the extremes of
     the interval being two generators.
     The main generator should be normalized for Mask to work properly.
     Random generator of the pmask.rng module valid main generators for
     pmask.

     exp is the exponent of the mapping function. It defaults to zero
     (linear mapping). As usual in the Cmask language the real exponent
     is 2^exp.
     """
     def __init__(self, mainFunction, lowerLimit, upperLimit, exp = 0.0):
          Function.__init__(self)
          self.upperLimit = make_function(upperLimit)
          self.lowerLimit = make_function(lowerLimit)
          self.mainFunction = make_function(mainFunction)
          self.exponent = math.pow(2.0, exp)

     def mapAt(self, value, t):
          max = self.upperLimit(t)
          min = self.lowerLimit(t)

          return min + (max - min) * math.pow(value, self.exponent)

     def __call__(self, t):
          return self.mapAt(self.mainFunction(t), t)

class List(Generator):
     """
     List(... [, mode=...])

     This a time-independent generator. It stores a set of items
     and return one of them each one it is called.
     The next item returned depends on the mode parameter

     mode = 'cycle'
     the list traversed in its natural order, after the last
     item, the generator begins again from the first

     mode = 'swing'
     the generator goes back and forth, without repetition
     of the last element

     mode = 'swing-repeat'
     the generator goes back and forth, with repetition of
     the last element

     mode = 'heap'
     the generators computes all permutation of the given
     set and traverse them all

     mode = 'random'
     one item is chosen at random (with replacement). The
     item have the same probability (but you can insert
     some of them more than once.
     If you want a more sophisitaced weighted random choice,
     use Choice.

     The items are copied, so you can safely change them
     after you put them in the List.
     List items are _not_ evaluated.
     
     Default mode is 'cycle'.
     """
     def cycle_next(self):
          item = self.list[self.index]
          if self.index == len(self.list) - 1:
                self.index = 0
          else:
                self.index = self.index + 1
          return item

     def swing_next(self):
          item = self.list[self.index]

          if len(self.list) == 1:
                self.step = 0
          if self.step == 1 and self.index == len(self.list) - 1:
                self.step = -1
          elif self.step == -1 and self.index == 0:
                self.step = 1

          self.index += self.step
          
          return item

     def random_next(self):
          return omdeRand.choice(self.list)

     _value_error_message = "mode can be only 'cycle', 'swing', 'swing-repeat', 'heap' or 'random' (got '%s')"
     
     def __init__(self, *list0, **dict):
          Generator.__init__(self)

          mode = 'cycle'

          for key in dict.keys():
                if key == 'mode': mode = dict['mode']
         
          list0 = list(list0)
          if len(list0) == 0:
                raise ValueError, 'cannot create an empty List'
          self.list = copy.deepcopy(list0)

          if mode in ['cycle', 'c']:
                self.index = 0
                self.next = self.cycle_next
          elif mode in ['swing', 's']:
                self.index = 0
                self.step = 1
                self.next = self.swing_next
          elif mode in ['swing-repeat', 'w']:
                reversed = copy.deepcopy(list0)
                reversed.reverse()
                
                self.list.extend(reversed)

                self.index = 0
                self.next = self.cycle_next
          elif mode in ['heap', 'h']:
                self.index = 0
                self.next = self.cycle_next
                self.list = self.computePermutations(list0)
          elif mode in ['random', 'r']:
                self.next = self.random_next
          else:
                raise ValueError, self._value_error_message % mode

     def __call__(self):
          return self.next()

     def computePermutations(self, list):
          permutations = []
          permutations.extend(list)
          for i in range(len(list)):
                if i < len(list) - 1:
                     n = len(list) - 1
                else:
                     n = len(list) - 2
                for j in range(n):
                     self.swapAdiacentElements(list, j)
                     permutations.extend(list)
          self.swapAdiacentElements(list, len(list) - 2)
          return permutations

     def swapAdiacentElements(self, list, n):
          l2 = list[n:n+2]
          l2.reverse()
          list[n:n+2] = l2

class _PossibleChoice:
     """Internal helper class"""
     def __init__(self, object, probability):
          self.object = object
          self.probability = probability
          self.mark = None

class _MarkAccumulatorEvaluate:
     """Internal helper class"""
     def __init__(self, t, factor):
          self.t = t
          self.factor = float(factor)
          self.value = 0

     def __call__(self, possible_choice):
          self.value += possible_choice.probability(self.t) / self.factor
          possible_choice.mark = self.value

          return possible_choice

class _MarkAccumulator:
     """Internal helper class"""
     def __init__(self, factor):
          self.factor = factor 
          self.value = 0

     def __call__(self, possible_choice):
          self.value += possible_choice.probability / self.factor
          possible_choice.mark = self.value

          return possible_choice

class Choice(Function):
     """
     Choice((object1, probability1)...)

     This is a time-independent generator which performs
     a weighted choice from its set of items.

     

     for example the following generator

     Choice((0, 10), (5: 1))

     returns ten times more often 0 than 5.

     Probabilities may be generators: they
     are evaluated and normalized. This way you can
     use time-varying configuration of probability.
     If you don't need this feature use StaticChoice
     instead.
     """
     def __init__(self, pair0, *pairs):
          Function.__init__(self)
          for pair in pairs:
                if type(pair) is not types.TupleType:
                     raise ValueError, 'pair (object, probability) expected. got %s', repr(pair)

          self.set = []
          for o, p in [pair0] + list(pairs):
                self.set.append(_PossibleChoice(o, make_function(p)))

     def __call__(self, t):
          sum = reduce(lambda x,y: x+y, [possible_choice.probability(t) for possible_choice in self.set ])
          self.set = map(_MarkAccumulatorEvaluate(t, sum), self.set)

          n = omdeRand.random()
          for possible_choice in self.set:
                if n <= possible_choice.mark:
                     return possible_choice.object

          raise RuntimeError

class StaticChoice(Function):
     """
     StaticChoice(set)

     StaticChoice is a variant of Choice.
     Please read the Choice documentation.
     The only different is that items probabilities
     are fixed and will not be evaluated.
     """
     def __init__(self, pair, *pairs):
          Function.__init__(self)

          pairs = [pair] + list(pairs)
          
          self.set = []
          for o, p in pairs:
                self.set.append(_PossibleChoice(o, p))

          sum = reduce(lambda x,y: x+y, 
                  [possible_choice.probability for possible_choice in self.set])
          self.set = map(_MarkAccumulator(sum), self.set)

     def __call__(self, t):
          n = omdeRand.random()
          for possible_choice in self.set:
                if n <= possible_choice.mark:
                     return possible_choice.object

          raise RuntimeError




#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


    def test2(self):
        from athenaCL.libATH.omde.miscellaneous import Range
        from athenaCL.libATH.omde.rand import UniformRandom
        from athenaCL.libATH.omde.bpf import LinearSegment
        
        r = Range(-10, 10)
        a = Accumulator(r, 'wrap', -100.0, 100.0)
        
        for i in range(1000):
            post = i, r(), a(i)


#     def test3(self):
#         from athenaCL.libATH.omde.miscellaneous import Range
#         from athenaCL.libATH.omde.rand import UniformRandom
#         from athenaCL.libATH.omde.bpf import LinearSegment
#         
#         rng = UniformRandom()
#         
#         strength = LinearSegment([(0.0, 0.0), (1.0, 1.0), (2.0, 0.5)])
#         
#         upper = LinearSegment([(0.0, 300.0), (1.0, 350.0), (2.0, 200)])
#         
#         m = Mask(rng, 100, upper)
#         q = Quantizer(m, 10.0, strength, 0.0)
#         
#         t = 0.0
#         step = 0.001
#         for i in range(2001):
#             post = t, q(t)
#             t = t + step
#         
#         a = Attractor(Range(100, 1000), [120.0, 160.0, 200.0, 400.0], 0.8, 1.0)
#         t = 2.0
#         step = 0.001
#         for i in range(2001):
#             post = t, a(t)
#             t = t + step



    def test4(self):           
        from athenaCL.libATH.omde.miscellaneous import Range
        from athenaCL.libATH.omde.rand import UniformRandom
        from athenaCL.libATH.omde.bpf import LinearSegment
        
        
        rng = UniformRandom()
        
        m = Mask(rng, 100, 300)
        
        t = 0.0
        step = 0.001
        for i in range(2000):
            post = t, m(t)
            t = t + step
    
#     def test5(self):
#         from athenaCL.libATH.omde.miscellaneous import Range
#         from athenaCL.libATH.omde.rand import UniformRandom
#         from athenaCL.libATH.omde.bpf import LinearSegment
#         
#         
#         s = {10:1.0, 20:2.0, 30:1.0}
#         c = StaticChoice(s)
#         statistics = {}
#         for key in s.keys():
#             statistics[key] = 0
#         for i in range(100):
#             v = c(0)
#             statistics[v] += 1
#         post = statistics


#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)