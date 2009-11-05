#-----------------------------------------------------------------||||||||||||--
# Name:          parameter.py
# Purpose:       public interface to all textures.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

from athenaCL.libATH import drawer
from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH.libTM import DroneArticulate
from athenaCL.libATH.libTM import DroneSustain
from athenaCL.libATH.libTM import IntervalExpansion
from athenaCL.libATH.libTM import LineCluster
from athenaCL.libATH.libTM import LineGroove
from athenaCL.libATH.libTM import LiteralHorizontal
from athenaCL.libATH.libTM import LiteralVertical
from athenaCL.libATH.libTM import MonophonicOrnament
from athenaCL.libATH.libTM import TimeFill
from athenaCL.libATH.libTM import TimeSegment
from athenaCL.libATH.libTM import HarmonicShuffle
from athenaCL.libATH.libTM import HarmonicAssembly
from athenaCL.libATH.libTM import InterpolateLine
from athenaCL.libATH.libTM import InterpolateFill

# modules where parameters can be found
textureModules = (DroneArticulate, DroneSustain, 
                        IntervalExpansion, 
                        LineCluster, LineGroove, 
                        LiteralHorizontal, LiteralVertical, 
                        MonophonicOrnament,
                        TimeFill, TimeSegment, HarmonicShuffle, HarmonicAssembly,
                        InterpolateLine, InterpolateFill
                      )

tmNames = {
    'da' : 'DroneArticulate',
    'ds' : 'DroneSustain',
    'ie' : 'IntervalExpansion',
    'lc' : 'LineCluster',
    'lg' : 'LineGroove',
    'lh' : 'LiteralHorizontal',
    'lv' : 'LiteralVertical',
    'mo' : 'MonophonicOrnament',
    'tf' : 'TimeFill',
    'ts' : 'TimeSegment', 
    'hs' : 'HarmonicShuffle', 
    'ha' : 'HarmonicAssembly', 
    'il' : 'InterpolateLine', 
    'if' : 'InterpolateFill', 
    }

tmObjs = tmNames.values()



#-----------------------------------------------------------------||||||||||||--
def tmTypeParser(typeName):
    """utility functions for parsing user strings of texture namess
    """
    parsed = drawer.acronymExpand(typeName, tmNames)
    if parsed == None:
        pass 
    return parsed
    # if not mattched, return None

def locator(usrStr):
    objType = tmTypeParser(usrStr) #check type string
    modFound = None
    for mod in textureModules: # look through all mods for
        reload(mod)
        classList = dir(mod)
        if objType in classList:
            modFound = mod
            break
    if modFound == None:
        raise ValueError, 'parameter type error: %s' % usrStr # failure
    return modFound, objType


def factory(tmName, name=None, scObj=None):
    """this is used only for loading adn returning an object
    can return obj or parsed args
    first thing in list must be a string, type def
    """
    reload(baseTexture) # reload base classs
    mod, objType = locator(tmName) #check type string
    if objType == None:
        raise ValueError, 'texture module type error' # failure
    if objType not in tmObjs:
        raise ValueError, 'texture module type error' # failure

    tmObjAttr = getattr(mod, objType)
    tmObj = tmObjAttr(name, scObj)
    return tmObj


def doc(rawName):
    """just get the doc string of a parameter object"""
    mod, objType = locator(rawName) #check type string
    objRef = getattr(mod, objType) # gets ref, not obh
    obj = objRef()
    #docStr = getattr(objRef, '__doc__')
    #return docStr
    return obj.doc
