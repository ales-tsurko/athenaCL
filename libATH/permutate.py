#-----------------------------------------------------------------||||||||||||--
# Name:          permutate.py
# Purpose:       utilities for permutations.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2005 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--




# based on code by Ulrich Hoffmann
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/190465


from __future__ import generators


#-----------------------------------------------------------------||||||||||||--
# return generators

def xcombinations(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in xcombinations(items[:i]+items[i+1:],n-1):
                yield [items[i]]+cc
    
def xselections(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for ss in xselections(items, n-1):
                yield [items[i]]+ss

def xuniqueCombinations(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)-n+1):
            for cc in xuniqueCombinations(items[i+1:],n-1):
                yield [items[i]]+cc

def xpermutations(items):
    return xcombinations(items, len(items))

#-----------------------------------------------------------------||||||||||||--
# return complete lists

def combinations(items, n):
    return list(xcombinations(items, n))
    
def selections(items, n):
    return list(xselections(items, n))
    
def uniqueCombinations(items, n):
    return list(xuniqueCombinations(items, n))
    
def permutations(items):    
    return list(xcombinations(items, len(items)))
    
    
#-----------------------------------------------------------------||||||||||||--

if __name__ == "__main__":
    print "Permutations of 'abc'"
    for p in xpermutations(['a', 'b', 'c']): 
        print ''.join(p)

    print list(xpermutations(['a', 'b', 'c']))
    
    print map(''.join, list(xpermutations('done')))

