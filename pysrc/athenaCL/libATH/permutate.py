# -----------------------------------------------------------------||||||||||||--
# Name:          permutate.py
# Purpose:       utilities for permutations.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2005-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import unittest, doctest


# based on code by Ulrich Hoffmann
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/190465


# -----------------------------------------------------------------||||||||||||--
# return generators


def xcombinations(items, n):
    if n == 0:
        yield []
    else:
        for i in range(len(items)):
            for cc in xcombinations(items[:i] + items[i + 1 :], n - 1):
                yield [items[i]] + cc


def xselections(items, n):
    if n == 0:
        yield []
    else:
        for i in range(len(items)):
            for ss in xselections(items, n - 1):
                yield [items[i]] + ss


def xuniqueCombinations(items, n):
    if n == 0:
        yield []
    else:
        for i in range(len(items) - n + 1):
            for cc in xuniqueCombinations(items[i + 1 :], n - 1):
                yield [items[i]] + cc


def xpermutations(items):
    return xcombinations(items, len(items))


# -----------------------------------------------------------------||||||||||||--
# return complete lists


def combinations(items, n):
    """
    >>> combinations([3,4,5], 3)
    [[3, 4, 5], [3, 5, 4], [4, 3, 5], [4, 5, 3], [5, 3, 4], [5, 4, 3]]
    >>> combinations([3,4,5], 2)
    [[3, 4], [3, 5], [4, 3], [4, 5], [5, 3], [5, 4]]
    """
    return list(xcombinations(items, n))


def selections(items, n):
    """
    >>> selections([3,4,5], 2)
    [[3, 3], [3, 4], [3, 5], [4, 3], [4, 4], [4, 5], [5, 3], [5, 4], [5, 5]]
    """
    return list(xselections(items, n))


def uniqueCombinations(items, n):
    """
    >>> uniqueCombinations([3,4,5], 2)
    [[3, 4], [3, 5], [4, 5]]
    """
    return list(xuniqueCombinations(items, n))


def permutations(items):
    """
    >>> permutations([8,3,267])
    [[8, 3, 267], [8, 267, 3], [3, 8, 267], [3, 267, 8], [267, 8, 3], [267, 3, 8]]
    """
    return list(xcombinations(items, len(items)))


# -----------------------------------------------------------------||||||||||||--

# if __name__ == "__main__":
#     print "Permutations of 'abc'"
#     for p in xpermutations(['a', 'b', 'c']):
#         print ''.join(p)
#
#     print list(xpermutations(['a', 'b', 'c']))
#
#     print map(''.join, list(xpermutations('done')))
#


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
