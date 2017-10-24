#-----------------------------------------------------------------||||||||||||--
# Name:          functional.py
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# Copyright:     (c) 2000-2001, Maurizio Umberto Puxeddu
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

# functional.py

# Object-oriented Music Definition Environment
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


import unittest, doctest
import copy



class FunctionModel:
     """
     Base class for function models.
     """
     def __init__(self):
          """
          Return a FunctionalModel instance

          It is an incomplete instance.
          """
          pass
     
     def instance(self, begin, end):
          """
          Return an instance for this FunctionModel as
          a real Function.

          Function is defined in the [begin, end] range.

          Pure virtual method.
          """
          raise NotImplementedError

class Function(FunctionModel):
     """
     Abstract base class for functional scoring

     A subclass of Function must define the __call__(self, t) method,
     where t is the evaluation time.

     A Function is also a FunctionModel (of itself).

     You can also use arithmetic operators
     (+, -, *, /) between generators and get the result generator.
     """
     def __init__(self):
          """
          Return a function instance.
          """
          FunctionModel.__init__(self)

     def __call__(self, t):
          """
          Return the function value at time t.

          Pure virtual method.
          """
          raise NotImplementedError

     def __add__(self, function):
          """
          + operator implementation.
          """
          return AddFunction(self, function)
     
     def __sub__(self, function):
          """
          - operator implementation.
          """
          return SubFunction(self, function)

     def __mul__(self, function):
          """
          * operator implementation.
          """
          return MulFunction(self, function)

     def __div__(self, function):
          """
          / operator implementation.
          """
          return DivFunction(self, function)

     def __radd__(self, function):
          """
          + operator implementation (object is on the right)).
          """
          return AddFunction(function, self)
     
     def __rsub__(self, function):
          """
          - operator implementation (object is on the right)).
          """
          return SubFunction(function, self)

     def __rmul__(self, function):
          """
          * operator implementation (object is on the right)).
          """
          return MulFunction(function, self)

     def __rdiv__(self, function):
          """
          / operator implementation (object is on the right)).
          """
          return DivFunction(function, self)

     def instance(self, begin, end):
          """
          Return self as instance of this Function.
          """
          return self

class TimeDependenceAdaptor(Function):
     """
     This function turns allows you to use a generator
     where a function is needed.
     """
     def __init__(self, tig):
          """
          Return a TimeDependenceAdaptor instance.

          tig is a time independent Generator.
          """
          self.tig = tig

     def __call__(self, t):
          """
          Return the function value at time t.

          Beware: the next value of the generator is returned at each
          call. So evaluating this object twice at the same instant
          could return two different values.
          """
          return self.tig()

class AddFunction(Function):
     """
     Add function

     Given two Functions a and b, this function returns a + b
     """
     def __init__(self, a, b):
          """
          Return an AddFunction instance for two given
          Functions a and b.

          a and b are made Function if necessary and possible.
          """
          self.a = make_function(a)
          self.b = make_function(b)

     def __call__(self, t):
          """
          Return the sum of the values of the two
          functions at time t.
          """
          return self.a(t) + self.b(t)

class SubFunction(Function):
     """
     Sub function

     Given two functions a and b, this function returns a - b
     """
     def __init__(self, a, b):
          """
          Return an SubFunction instance for two given
          Functions a and b.

          a and b are made Function if necessary and possible.
          """
          self.a = make_function(a)
          self.b = make_function(b)

     def __call__(self, t):
          """
          Return the difference of the values of the two
          functions at time t.
          """
          return self.a(t) - self.b(t)

class MulFunction(Function):
     """
     Mul function

     Given two functions a and b, this function returns a * b
     """
     def __init__(self, a, b):
          """
          Return a MulFunction instance for two given
          Functions a and b.

          a and b are made Function if necessary and possible.
          """
          self.a = make_function(a)
          self.b = make_function(b)

     def __call__(self, t):
          """
          Return the product of the values of the two
          functions at time t.
          """
          return self.a(t) * self.b(t)

class DivFunction(Function):
     """
     Div function

     Given two functions a and b, this function returns a / b
     """
     def __init__(self, a, b):
          """
          Return a DivFunction instance for two given
          Functions a and b.

          a and b are made Function if necessary and possible.
          """
          self.a = make_function(a)
          self.b = make_function(b)

     def __call__(self, t):
          """
          Return the quotient of the values of the two
          functions at time t.
          """
          return self.a(t) / self.b(t)

class ConstantFunction(Function):
     """
     Constant function

     it returns the same value at any time.
     """
     def __init__(self, value):
          """
          Return a ConstantFunction instance.
          
          The original value object is deep-copied, if possible.
          """
          try:
                self.value = copy.deepcopy(value)
          except:
                self.value = value

     def __call__(self, t):
          """
          Return the constant value at any time.
          """
          return self.value

class Generator:
     """
     Time-independent data generator base class.

     The call method takes no arguments.

     You can also use arithmetic operators (+, -, *, /) between
     generators and get the result generator.
     """
     def __init__(self):
          pass
     
     def __call__(self):
          raise NotImplementedError

     def __add__(self, object):
          """
          + operator implementation.
          """
          if isinstance(object, Function):
                return AddFunction(make_function(self), object)
          else:
                return AddGenerator(self, object)
     
     def __sub__(self, object):
          """
          - operator implementation.
          """
          if isinstance(object, Function):
                return SubFunction(make_function(self), object)
          else:
                return SubGenerator(self, object)

     def __mul__(self, object):
          """
          * operator implementation.
          """
          if isinstance(object, Function):
                return MulFunction(make_function(self), object)
          else:
                return MulGenerator(self, object)

     def __div__(self, object):
          """
          / operator implementation.
          """
          if isinstance(object, Function):
                return MulFunction(make_function(self), object)
          else:
                return DivGenerator(self, object)

     def __radd__(self, object):
          """
          + operator implementation (object is on the right)).
          """
          return AddGenerator(object, self)
     
     def __rsub__(self, object):
          """
          - operator implementation (object is on the right)).
          """
          return SubGenerator(object, self)

     def __rmul__(self, object):
          """
          * operator implementation (object is on the right)).
          """
          return MulGenerator(object, self)

     def __rdiv__(self, object):
          """
          / operator implementation (object is on the right)).
          """
          return DivGenerator(object, self)

class AddGenerator(Generator):
     """
     Add generator

     Given two generators a and b, this generator returns a + b
     """
     def __init__(self, a, b):
          """
          Return an AddGenerator instance for two given
          Generators a and b.

          a and b are made Generator if necessary and possible.
          """
          self.a = make_generator(a)
          self.b = make_generator(b)

     def __call__(self):
          """
          Return the sum of the next values of the two
          generators.
          """
          return self.a() + self.b()

class SubGenerator(Generator):
     """
     Sub generator

     Given two generators a and b, this generator returns a - b
     """
     def __init__(self, a, b):
          """
          Return a SubGenerator instance for two given
          Generators a and b.

          a and b are made Generator if necessary and possible.
          """
          self.a = make_generator(a)
          self.b = make_generator(b)

     def __call__(self):
          """
          Return the difference of the next values of the two
          generators.
          """
          return self.a() - self.b()

class MulGenerator(Generator):
     """
     Mul generator

     Given two generators a and b, this generator returns a * b
     """
     def __init__(self, a, b):
          """
          Return a MulGenerator instance for two given
          Generators a and b.

          a and b are made Generator if necessary and possible.
          """
          self.a = make_generator(a)
          self.b = make_generator(b)

     def __call__(self):
          """
          Return the product of the next values of the two
          generators.
          """
          return self.a() * self.b()

class DivGenerator(Generator):
     """
     Div generator

     Given two generators a and b, this generator returns a / b
     """
     def __init__(self, a, b):
          """
          Return a DivGenerator instance for two given
          Generators a and b.

          a and b are made Generator if necessary and possible.
          """
          self.a = make_generator(a)
          self.b = make_generator(b)

     def __call__(self):
          """
          Return the quotient of the next values of the two
          generators.
          """
          return self.a() / self.b()

class ConstantGenerator(Generator):
     """
     Constant generator.

     The original object is deep-copied, if possible.
     """
     def __init__(self, value):
          try:
                self.value = copy.deepcopy(value)
          except:
                self.value = value

     def __call__(self):
          return self.value

class Freezer(Generator):
     """
     Convert a Function into a Generator.
     """
     def __init__(self, f, t=0.0):
          """
          Return a Freezer instance.

          f is the freezed function.
          t is the freeze time (default is 0.0).
          """
          if not isinstance(f, Function):
                raise ValueError("Function expected. got '%s'").with_traceback(type(f))
          
          self.f = f
          self.t = make_generator(t)

     def __call__(self):
          return self.f(self.t())

def make_function(object, begin = None, end = None):
     """
     Convert an object to a function.

     If object is a function, make_function() returns object.

     If object is a Generator make_function() performs adaptation
     and return the resulting Function.

     If object is a FunctionModel it is instanced and make_function()
     returns the resulting function.
     But if both begin and end are None, make_function() expects only
     ready-to-use generators and not models.

     Everything else is turned into a ConstantFunction.
     """
     if isinstance(object, Generator):
          return TimeDependenceAdaptor(object)

     if isinstance(object, Function):
          return object
     
     if isinstance(object, FunctionModel):
          if begin is not None and end is not None:
                return object.instance(begin, end)
          elif begin is not None and end is None:
                raise ValueError('generator model not allowed without complete life span')
          else:
                raise ValueError('generator model without life span')
     
     return ConstantFunction(object)

def make_generator(object, t0=0.0):
     """
     Convert an object to a generator.

     If object is a Generator, make_generator() returns object.
     A Function be converted to a Generator by freezing it at t0.
     Everything else is turned into a ConstantGenerator.
     """
     if object == None:
          return None
     
     if isinstance(object, Function):
          return Freezer(object, t0)
     
     if isinstance(object, Generator):
          return object
     
     return ConstantGenerator(object)



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


