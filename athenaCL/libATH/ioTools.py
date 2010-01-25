#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          ioTools.py
# Purpose:       provides XML reading and writing for athenaObjects.
#                    passing a standard dictionary of data between athenaObj
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy, sys
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import argTools
from athenaCL.libATH import language
from athenaCL.libATH import error
lang = language.LangObj()
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH import xmlTools
import xml.dom.minidom

_MOD = 'ioTools.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)

#-----------------------------------------------------------------||||||||||||--
# take an xml doc and convert into structured dictionaries

def extractXML(path):
    """open an xml file and return a dictionary
    dictionary built from attribute key value pairs
    missing attributes are not added (backwards compat done in athenaObj
    """
    # added universal new line support; should provide cross-plat access
    f = open(path, 'rU') 
    doc = xml.dom.minidom.parse(f)
    f.close()
    procData = xmlTools.xmlToPy(doc)
    aData = procData['athenaObject']['athena'] #athena Data
    pData = procData['athenaObject']['paths'] #path Data
    tData = procData['athenaObject']['textures'] #tData
    return aData, pData, tData



#-----------------------------------------------------------------||||||||||||--
# evalues raw string data from xml intp proper lists and python data structures
# strings cannot be evaluated, as this causes a name error
# all other data objects, however, should be evaluated
def _evalRecurse(data):
    """recursively evaluate data in dictionaries; if data is a string, 
    dont evaluate if data is a dict, recurse"""
    keyList = data.keys()
    for key in keyList:
        if drawer.isDict(data[key]):
            _evalRecurse(data[key])
        else: # not a dictionary
            try:
                data[key] = eval(data[key])
            except (NameError, SyntaxError): # its a string
                pass

def evalObjectDictionary(aData, pData, tData):
    """scans all data dicitionaries evaluates data, 
    keeping strings as string"""
    _evalRecurse(aData)
    _evalRecurse(pData)
    _evalRecurse(tData)
    return aData, pData, tData

#-----------------------------------------------------------------||||||||||||--
# provide data dictionaries, write to an xml file
def writeXML(filePath, aData, pData, tData):
    """write athenaObject as xml file
    provide three dictionaries: aData, pathData, textureData
    what is written is controled by how pData is packaged
    this is done internally in athenaObj
    """
    msg = []
    parent = 'athenaObject'
    msg.append(xmlTools.XMLHEAD)
    msg.append('\n<%s>' % parent)
    msg = msg + xmlTools.pyToXml(parent, 'athena', aData, 1, [])
    msg = msg + xmlTools.pyToXml(parent, 'paths', pData, 1, 
                 [None, None, 'pi', None, ('voiceLib', 'pv')])
    msg = msg + xmlTools.pyToXml(parent, 'textures', tData, 1, 
                 [None, None, ('textureLib', 'ti', 'cloneLib', 'tc')])
    msg.append('\n</%s>' % parent)  # close prefs 
    f = open(filePath, 'w')
    f.writelines(msg)
    f.close()





#-----------------------------------------------------------------||||||||||||--
# backwards compat object deals with problems
class BackwardsCompat:
    """process evaluated dictionary of raw athenaobj data, including textures
    and paths.
    this is a destructive backwards compat, in that it changes pmtr values"""
    def __init__(self):
        pass


    #-----------------------------------------------------------------------||--
    # pre 1.4.0
    
    def _waveReplace(self, argSrc):
        """always returns a list, not a tuple"""
        arg = list(argSrc[:])
        if not drawer.isStr(arg[0]):
            return arg # dont alter
        # try to find pmtr Type           
        pmtrType = None
        for lib in ['genPmtrObjs', 'rthmPmtrObjs',]:
            try: pmtrType = parameter.pmtrTypeParser(arg[0], lib)
            except error.ParameterObjectSyntaxError: continue
        if pmtrType == None: # no match found
            return arg
        # insert step string as second argument
        elif pmtrType in ['waveSine', 'waveCosine', 'waveSawDown',
                             'waveSawUp',   'wavePulse', 'waveTriangle', 
                             'wavePowerDown', 'wavePowerUp']:
            # make sure that this is not alreayd fixed:
            if drawer.isStr(arg[1]): # can assume that this is a t/e string
                return arg
            newArgs = [arg[0], 't'] + list(arg[1:])  
            environment.printDebug(['changed args:', arg, 'to:', newArgs])
            return newArgs
        else:
            return arg
        
    def _recursiveUpdate(self, argSrc): 
        # args are already evaluated data and strings
        # argSrc must at a lost of values
        insertFix = self._waveReplace(argSrc) # returns a list
        # check for embedded
        for i in range(len(insertFix)):
            arg = insertFix[i]
            # look for an arg that is a list
            if drawer.isList(arg) and len(arg) > 0:
                argPost = self._recursiveUpdate(arg) # returns a tuple
                insertFix[i] = argPost # assign over old postiion
        return insertFix                 
                    
    def _pre140_pmtrObjUpdates(self):
        """minor fixes to old parameterObjects"""
        t = self.tData
        for tName in t['textureLib'].keys():
            for pmtrKey in t['textureLib'][tName]['pmtrQDict'].keys():
                arg = t['textureLib'][tName]['pmtrQDict'][pmtrKey]   
                newArgs = tuple(self._recursiveUpdate(arg))
                if newArgs != arg: # a change has been made
                    environment.printDebug(['changed args:', arg, 'to:', newArgs])
                    t['textureLib'][tName]['pmtrQDict'][pmtrKey] = newArgs
                # do alterations to textureStatic and cloneStatic names
                # these will always be given with full names
                # these do not need to be recursice
                replacePairs = [('ornamentLibrary', 'ornamentLibrarySelect'), 
                                     ('ornamentDensity', 'ornamentMaxDensity'), 
                                     ('timeReference', 'timeReferenceSource'),
                                     ('retrogradeMethod', 'retrogradeMethodToggle'),
                                    ]
                for src, dst in replacePairs:
                    if arg[0] == src:
                        newArgs = [dst] + list(arg[1:]) # make new list
                        t['textureLib'][tName]['pmtrQDict'][pmtrKey] = tuple(newArgs)
                        environment.printDebug(['replaced:', src, dst])



    #-----------------------------------------------------------------------||--
    def _pre144_pmtrObjUpdates(self):
        """minor fixes to old parameterObjects"""
        t = self.tData
        for tName in t['textureLib'].keys():
            for pmtrKey in t['textureLib'][tName]['pmtrQDict'].keys():
                arg = t['textureLib'][tName]['pmtrQDict'][pmtrKey]   
                # do alterations to textureStatic
                replacePairs = [('nonRedundantSwitch', 'pitchSelectorControl'), 
                                    ]
                for src, dst in replacePairs:
                    # nonRedundantSwitch, if on, is e same as randomPermutate
                    if arg[0] == src:
                        if 'n' in arg[1]: new = 'randomPermutate' 
                        else: new = 'randomChoice' 
                        newArgs = [dst, new] # make new list
                        t['textureLib'][tName]['pmtrQDict'][pmtrKey] = tuple(newArgs)
                        environment.printDebug(['replaced:', src, arg[1], dst, new])

    def _pre145_cleanExtraAux(self):
        """correct a possible error where, when going from a larger to a 
        smaller aux value, extra Q keys exist that should not by the aux count
        this causes errors elsewhere, and his been fixed
        this method looks a the aux and removes any extra aux like things"""
        t = self.tData
        for tName in t['textureLib'].keys():
            auxNo = t['textureLib'][tName]['auxNo']
            # store all valid
            auxLabelValid = basePmtr.auxLabel(auxNo)
            for pmtrKey in t['textureLib'][tName]['pmtrQDict'].keys():           
                if pmtrKey not in auxLabelValid: # not a valid auxq
                    if pmtrKey[:4] == 'auxQ': # if it looks like an auxq
                        del t['textureLib'][tName]['pmtrQDict'][pmtrKey]
                        environment.printDebug(['removed extra auxQ:', pmtrKey])
        # clear extra clone aux as well
        for cName in t['cloneLib'].keys():
            auxNo = t['cloneLib'][cName]['auxNo']
            # store all valid
            auxLabelValid = basePmtr.auxLabel(auxNo)
            for pmtrKey in t['cloneLib'][cName]['pmtrQDict'].keys():              
                if pmtrKey not in auxLabelValid: # not a valid auxq
                    if pmtrKey[:4] == 'auxQ': # if it looks like an auxq
                        del t['cloneLib'][cName]['pmtrQDict'][pmtrKey]
                        environment.printDebug(['removed extra auxQ:', pmtrKey])
                        
                
    def _pre200_basic(self):
        """correct a possible error where, when going from a larger to a 
        smaller aux value, extra Q keys exist that should not by the aux count
        this causes errors elsewhere, and his been fixed
        this method looks a the aux and removes any extra aux like things"""
        if 'nchnls' in self.aData.keys():
            self.aData['audioChannels'] = self.aData['nchnls']
            del self.aData['nchnls']
        if 'audioRate' not in self.aData.keys():
            self.aData['audioRate'] = 44100

    #-----------------------------------------------------------------------||--
    def process(self, aData, pData, tData):
        """main methods for providing backwards compat for global changes
        operates on raw python data lists, not on built objects
        smaller backwards compat may happen in lower level objects"""
        self.aData = aData
        self.pData = pData
        self.tData = tData

        self.fileVersionObj = argTools.Version(self.aData['version'])

        # pre 1.4.0
        boundary = argTools.Version('1.4.0')
        if self.fileVersionObj < boundary:
            environment.printDebug('pre %s update necessary.' % str(boundary))
            self._pre140_pmtrObjUpdates()

        # pre 1.4.5 ; was 1.4.4, but had to increment to catch old errors
        # v. 1.4.5 may not exists
        boundary = argTools.Version('1.4.5')
        if self.fileVersionObj < boundary:
            environment.printDebug('pre %s update necessary.' % str(boundary))
            self._pre144_pmtrObjUpdates()
            self._pre145_cleanExtraAux()

        # pre 2.0
        boundary = argTools.Version('2.0.0')
        if self.fileVersionObj < boundary:
            environment.printDebug('pre %s update necessary.' % str(boundary))
            self._pre200_basic()

        # return data
        return self.aData, self.pData, self.tData






        
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
