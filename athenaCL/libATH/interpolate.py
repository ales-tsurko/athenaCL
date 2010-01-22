import unittest, doctest


# low level interpolation tools


class OneDimensionalLinear:

    def __init__(self, start, end):
        """interpolate b/n two values
        >>> a = OneDimensionalLinear(3, 21)
        """
        if start <= end:
            self.min = start
            self.max = end
            self.flip = 0
        else:
            self.min = end
            self.max = start
            self.flip = 1
            
        self.span = self.max - self.min

    def pos(self, unit):
        """get a vlue w/n the unit interval"""
        return (unit * self.span) + self.min

    def discrete(self, steps, digits=2):
        """get a list of values b/n e points"""
        if steps < 2: raise ValueError
        inc = 1.0 / (steps-1)
        post = []

        i = 0.0
        for q in range(steps-1):
            post.append(round(self.pos(i), digits))
            i = i + inc
        # manually add last value
        post.append(round(self.max, digits))
        if self.flip:
            post.reverse()
        return post




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