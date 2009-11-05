# random.py

# Object-oriented Music Definition Environment
# Copyright (C) 2000-2001 Maurizio Umberto Puxeddu

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

'''
Pseudo random numbers.

The following random number generators are available:

UniformRandom
LinearRandom
InverseLinearRandom
TriangularRandom
InverseTriangularRandom
ExponentialRandom
InverseExponentialRandom
BilateralExponentialRandom
GaussRandom
CauchyRandom
BetaRandom
WeibullRandom

The random number generator exported by this module
are not designed to be correct from a statistic point
of view but useful from a musical point of view.

In particular some of these generators have been
modified to return values in the [0, 1] range
even if they have a tail outside this interval.

Other have been modified to be consistent with
the Cmask original RNGs.
'''

import time, math
import random as randomBuiltin
# used to be this
# _the_same = whrandom.whrandom() # returns an instances
try:
    _the_same = randomBuiltin.WichmannHill() # 2.3 and greater
except (AttributeError, ImportError):
    import whrandom
    _the_same = whrandom.whrandom() # 2.3 and greater
        

def _AlwaysTheSame():
     return _the_same


from athenaCL.libATH.omde.functional import Function, make_function
from athenaCL.libATH.omde.functional import Generator

# note: undefined 'make' replaced with make_function
# Private classes

class _LehmerRNG:
     """
     Linear-Congruential Random Number Generator.

     Settings published in: 
     http://www.taygeta.com/rwalks/node1.html, adapted from:
     Park, S.K. and K.W. Miller, 1988; Random Number Generators: Good Ones 
     are Hard to Find, Comm. of the ACM, V. 31. No. 10, pp 1192-1201.

     Usage:

     x = _LehmerRNG([seed, mod, mul, incr])
     
     this returns a callable object. The optional keyword-arguments set the 
     instance attributes. For seeding in relation to system time, seed may 
     be set to 0 or may be omitted.

     The defaults of the other arguments are 2147483647.0, 16807.0, 0.
     These defaults can be changed only while the instance is created.
     
     'seed' is a number between 1 and 2147483647. 
     """
     def __init__(self, seed=0, mod = 2147483647.0, mul = 16807.0, incr = 0):
          self._mod = mod
          self._mul = mul
          self._incr = incr
          self.seed(seed)

     def random(self):
          """
          Returns a uniform random number between 0 and 1
          """
          self._seed = ( self._mul * self._seed + self._incr ) % self._mod
          return self._seed / self._mod

     def seed(self, seed = 0):
          self._seed = seed
          while self._seed == 0 or self._seed == self._mod:
                time.sleep(.01)
                self._seed = long((time.time() % 1) * self._mod)



#UniformRNG = LehmerRNG
#UniformRNG = whrandom.whrandom
UniformRNG = _AlwaysTheSame # not called, renamed

choice = randomBuiltin.choice
random = randomBuiltin.random

class _ExpovariateRNG:
     def __init__(self):
          self.uniformRNG = UniformRNG()

     def random(self, lambd):
          # lambd: rate lambd = 1/mean
          u = self.uniformRNG.random()
          while u <= 1e-7:
                     u = self.uniformRNG.random()
          return -math.log(u) / lambd

class _GaussRNG:
     def __init__(self):
          self.next = None
          
     def random(self, mu, sigma):
          """
          When x and y are two variables from [0, 1), uniformly
          distributed, then
          
          cos(2*pi*x)*sqrt(-2*log(1-y))
          sin(2*pi*x)*sqrt(-2*log(1-y))
          
          are two *independent* variables with normal distribution
          (mu = 0, sigma = 1).
          """
          z = self.next
          self.next = None
          if z is None:
                     x2pi = random() * math.pi * 2
                     g2rad = math.sqrt(-2.0 * math.log(1.0 - random()))
                     z = math.cos(x2pi) * g2rad
                     self.next = math.sin(x2pi) * g2rad

          return mu + z*sigma

class _BetavariateRNG:
     def __init__(self):
          self.expovariateRNG = _ExpovariateRNG()

     def random(self, alpha, beta):
          y = self.expovariateRNG.random(alpha)
          z = self.expovariateRNG.random(1.0/beta)
          return z/(y+z)

class _WeibullvariateRNG:
     def __init__(self):
          self.uniformRNG = UniformRNG()

     def random(self, alpha, beta):
          u = self.uniformRNG.random()
          return alpha * pow(-math.log(u), 1.0/beta)






# Public classes

class UniformRandom(Generator):
     """
     Random generator with uniform distribution
     """
     def __init__(self):
          Generator.__init__(self)
          self.rng = UniformRNG()

     def __call__(self):
          return self.rng.random()

class LinearRandom(Generator):
     """
     Random generator with linearly decreasing distribution.
     """
     def __init__(self):
          Generator.__init__(self)
          self.rng = UniformRNG()

     def __call__(self):
          a = self.rng.random()
          b = self.rng.random()
          return min(a, b)

class InverseLinearRandom(Generator):
     """
     Random generator with linearly increasing distribution.
     """
     def __init__(self):
          Generator.__init__(self)
          self.rng = UniformRNG()

     def __call__(self):
          a = self.rng.random()
          b = self.rng.random()
          return max(a, b)

class TriangularRandom(Generator):
     """
     Random generator with triangular distribution.
     """
     def __init__(self):
          Generator.__init__(self)
          self.rng = UniformRNG()

     def __call__(self):
          while 1:
                a = self.rng.random()
                b = self.rng.random() / 2
                     
                if (a < 0.5 and a > b) or (a >= 0.5 and (a - 0.5) < b):
                     return a

class InverseTriangularRandom(Generator):
     """
     Random generator with inverse triangular distribution.
     """
     def __init__(self):
          Generator.__init__(self)
          self.rng = UniformRNG()

     def __call__(self):
          while 1:
                a = self.rng.random()
                b = self.rng.random() / 2
                     
                if (a < 0.5 and a < b) or (a >= 0.5 and (a - 0.5) > b):
                     return a
# 1 arg
class ExponentialRandom(Function):
     """
     Random number function with exponential distribution
     """
     def __init__(self, lambd = 1.0):
          Function.__init__(self)
          self.lambd = make_function(lambd)
          self.expovariateRNG = _ExpovariateRNG()

     def __call__(self, t):
          lambd = self.lambd(t)
          while 1:
                r = self.expovariateRNG.random(lambd)
                if r < 1.0: break
          return r
     
class InverseExponentialRandom(Function):
     """
     Random number function with inverse exponential distribution
     """
     def __init__(self, lambd = 1.0):
          Function.__init__(self)
          self.lambd = make_function(lambd)
          self.expovariateRNG = _ExpovariateRNG()

     def __call__(self, t):
          lambd = self.lambd(t)
          while 1:
                r = 1.0 - self.expovariateRNG.random(lambd)
                if r > 0.0: break
          return r

class BilateralExponentialRandom(Function):
     """
     Random number function with bilateral exponential distribution
     """
     def __init__(self, lambd = 1.0):
          Function.__init__(self)
          self.lambd = make_function(lambd)
          self.expovariateRNG = _ExpovariateRNG()
          self.uniformRNG = UniformRNG()

     def __call__(self, t):
          lambd = self.lambd(t)
          while 1:
                r = self.expovariateRNG.random(lambd)
                if r < 1.0: break
          if self.uniformRNG.random() > 0.5:
                return 0.5 + r / 2.0
          else:
                return 0.5 - r / 2.0
# two args
class GaussRandom(Function):
     """
     Random number function with Gauss distribution
     """
     def __init__(self, mu = 0.5, sigma = 0.1):
          Function.__init__(self)
          self.mu = make_function(mu)
          self.sigma = make_function(sigma)
          self.gaussRNG = _GaussRNG()

     def __call__(self, t):
          mu = self.mu(t)
          sigma = self.sigma(t)
          while 1:
                value = self.gaussRNG.random(mu, sigma)
                if value >= 0.0 and value <= 1.0:
                     break
          return value
                
class CauchyRandom(Function):
     """
     Random number function with Cauchy distribution
     """
     def __init__(self, alpha = 0.1, mu = 0.5):
          Function.__init__(self)
          self.alpha = make_function(alpha)
          self.mu = make_function(mu)
          self.uniformRNG = UniformRNG()

     def __call__(self, t):
          mu = self.mu(t)
          alpha = self.alpha(t)
          while 1:
                while 1:
                     x = self.uniformRNG.random()
                     if x != 0.5: break
                value = alpha * math.tan(x * math.pi) + mu
                if value <= 1.0 and value >= 0: break
          return value

class BetaRandom(Function):
     """
     Random number function with beta distribution
     """
     def __init__(self, alpha = 0.1, beta = 0.1):
          Function.__init__(self)
          self.uniformRNG = UniformRNG()
          self.betavariateRNG = _BetavariateRNG()
          
          self.alpha = make_function(alpha)
          self.beta = make_function(beta)

     def __call__(self, t):
          alpha = self.alpha(t)
          beta = self.beta(t)
          if self.uniformRNG.random() > 0.5:
                return 1.0 - self.betavariateRNG.random(alpha, beta)
          else:
                return self.betavariateRNG.random(alpha, beta)
     
class WeibullRandom(Generator):
     """
     Random number function with Weibull distribution
     """
     def __init__(self, alpha = 0.5, beta = 2.0):
          Generator.__init__(self)
          self.alpha = make_function(alpha)
          self.beta = make_function(beta)

          self.weibullvariateRNG = _WeibullvariateRNG()

     def __call__(self, t):
          alpha = self.alpha(t)
          beta = self.beta(t)
          while 1:
                value = self.weibullvariateRNG.random(alpha, beta)
                if value >= 0.0 and value <= 1.0:
                     break
          return value




if __name__ == '__main__':
     def testRandom(rng, begin, end, n, m):
          counter = []
          for i in range(m):
                counter.append(0)

          t = 0.0
          step = (end - begin) / n
          for i in range(n):
                r = rng(t)
                print r
                for j in range(m-1, -1, -1):
                     floor = j / float(m)
                     ceil = (j+1)/float(m)
                     if r >= floor and r < ceil:
                          counter[j] = counter[j] + 1
                          break
                t += step
          #sum = 0
          #for j in range(m):
          #  sum += counter[j]
          #  print (j+1) / float(m), counter[j]/float(n)

     #rng = UniformRandom()
     #testRandom(rng, 10000, 100)

     #rng = LinearRandom()
     #testRandom(rng, 10000, 100)

     #rng = InverseLinearRandom()
     #testRandom(rng, 10000, 100)

     #rng = TriangularRandom()
     #testRandom(rng, 10000, 100)

     #rng = InverseTriangularRandom()
     #testRandom(rng, 10000, 100)

     #rng = ExponentialRandom(1.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = ExponentialRandom(0.7)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = ExponentialRandom(2.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     
     #rng = ReverseExponentialRandom(1.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = ReverseExponentialRandom(0.7)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = ReverseExponentialRandom(2.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)

     #rng = BilateralExponentialRandom(1.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = BilateralExponentialRandom(0.7)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = BilateralExponentialRandom(2.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)

     #rng = GaussRandom(0.5, 0.2)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = GaussRandom(0.5, 0.1)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = GaussRandom(0.2, 0.2)
     #testRandom(rng, 0.0, 20.0, 10000, 100)

     rng = CauchyRandom(0.5, 0.2)
     testRandom(rng, 0.0, 20.0, 10000, 100)
     rng = CauchyRandom(0.5, 0.15)
     testRandom(rng, 0.0, 20.0, 10000, 100)
     rng = CauchyRandom(0.2, 0.2)
     testRandom(rng, 0.0, 20.0, 10000, 100)
     
     #rng = BetaRandom(0.2, 0.2)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = BetaRandom(0.6, 0.6)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = BetaRandom(0.1, 0.3)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     
     #rng = WeibullRandom(0.5, 3.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = WeibullRandom(0.5, 5.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = WeibullRandom(0.5, 1.0)
     #testRandom(rng, 0.0, 20.0, 10000, 100)
     #rng = WeibullRandom(0.5, 0.3)
     #testRandom(rng, 0.0, 20.0, 10000, 100)


# end
