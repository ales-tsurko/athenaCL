#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          ioTools.py
# Purpose:       provides XML reading and writing for athenaObjects.
#                    passing a standard dictionary of data between athenaObj
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
from athenaCL.libATH import drawer
from athenaCL.libATH import argTools
from athenaCL.libATH import language
from athenaCL.libATH import error
lang = language.LangObj()
from athenaCL.libATH import setMeasure # for updating pe names
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH import xmlTools
import xml.dom.minidom

_MOD = 'ioTools.py'


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
#-----------------------------------------------------------------||||||||||||--
# backwards compat object deals with problems


class BackwardsCompat:
    """process evaluated dictionary of raw athenaobj data, including textures
    and paths.
    this is a destructive backwards compat, in that it changes pmtr values"""
    def __init__(self, debug=0):
        self.debug = debug

    #-----------------------------------------------------------------------||--
    # pre 1.3
    # old problem updates

    def _pre130_setMeasure(self):
        """corrects bad setMeasure names"""
        peName = self.pData['CurrentPathEngine']
        fixName = ''
        # check for bad prefix first
        if peName[:8] == 'PMclass.':
            peName = peName[8:] # short bit, dont need module
        # compare to all names
        for name in setMeasure.engines.keys():
            if peName.lower() == name.lower():
                fixName = name
            else:
                if peName.lower() == setMeasure.engines[name].lower():
                    fixName = name
                    break
        if fixName != '':
            self.pData['CurrentPathEngine'] = fixName
            if self.debug: print _MOD, 'fixed pe name:', peName, fixName

    def _pre130_pmtrPrimitive(self):
        """for old parameter object argument formats, mark and pass on
        only old formats are 'bg', 'cg', and 'ba', 
        all new parameter objects start with a string, always"""
        t = self.tData
        for tName in t['textureLib'].keys():
            for pmtrKey in t['textureLib'][tName]['pmtrQDict'].keys():
                pmtrData = t['textureLib'][tName]['pmtrQDict'][pmtrKey]
                # delete old textQ option; no longer used w/o nymber
                if pmtrKey == 'textQ':
                    if self.debug: print _MOD, 'removing old textQ attribute'
                    del t['textureLib'][tName]['pmtrQDict'][pmtrKey]
                if (pmtrKey in basePmtr.tCOMMONQ or 
                     pmtrKey[:len(basePmtr.AUXQ)] == basePmtr.AUXQ):
                    rawArgs = list(t['textureLib'][tName]['pmtrQDict'][pmtrKey])
                    # all new data lists start w/ strings
                    if not drawer.isStr(rawArgs[0]):
                        if drawer.isStr(rawArgs[1]):
                            shiftArgs = [0,0] # arg order changed
                            shiftArgs[0] = rawArgs[1] # was control
                            shiftArgs[1] = rawArgs[0] # was list
                            newArgs = ['basketGen',] + shiftArgs
                            t['textureLib'][tName]['pmtrQDict'][pmtrKey] = newArgs
                            if self.debug:
                                print _MOD, 'updating old arg:', rawArgs, newArgs
                        elif (drawer.isList(rawArgs[0]) and
                            drawer.isList(rawArgs[1])):  
                            newArgs = ['binaryAccent', rawArgs] # old args as a list
                            t['textureLib'][tName]['pmtrQDict'][pmtrKey] = newArgs
                            if self.debug:
                                print _MOD, 'updating old arg:', rawArgs, newArgs
                        elif drawer.isStr(rawArgs[3]):
                            shiftArgs = [0,0,0,0]# arg order changed
                            shiftArgs[1] = rawArgs[0] # was min
                            shiftArgs[2] = rawArgs[1] # was max
                            shiftArgs[3] = rawArgs[2] # was incr
                            shiftArgs[0] = rawArgs[3] # was direction
                            newArgs = ['cyclicGen',] + shiftArgs
                            t['textureLib'][tName]['pmtrQDict'][pmtrKey] = newArgs
                            if self.debug:
                                print _MOD, 'updating old arg:', rawArgs, newArgs
                        else:
                            if self.debug:
                                print _MOD, 'unknown old arg:', pmtrKey, rawArgs

    #-----------------------------------------------------------------------||--
    # pre 1.3
    # bridge to 1.3 data formats, change octave ref, chagne min/max rep

    def _alterPmtrStatic(self, arg, offset):
        """ only operates on a few pmtr objects
        note: args include parameter name as first arg
        these are all args that have shifts and numeric values
        some args are conceptual difficult to shift, so they are exculded"""
        pmtrType = parameter.pmtrTypeParser(arg[0])
        if pmtrType == 'basketGen':
            temp = []
            if not drawer.isList(arg[2]):# its a raw number
                temp = arg[2] + offset
            else:
                for value in arg[2]:
                    temp.append(value + offset)
            newArgs = (arg[0], arg[1], temp)
        elif pmtrType == 'constant':
            newArgs = (arg[0], arg[1]+offset)
        elif pmtrType == 'cyclicGen':
            newArgs = (arg[0], arg[1], arg[2]+offset, arg[3]+offset, arg[4])
        else:
            newArgs = None
        if newArgs != None:
            if self.debug: print _MOD, 'changed args:\n', arg, '\n', newArgs
        else:
            if self.debug: print _MOD, 'no change:', arg
        return newArgs

    def _scaleShiftToMinMax(self, scale, shift, offset=0):
        min = 0 + shift + offset
        max = scale + shift + offset
        if self.debug:
            print _MOD, 'scalar-shift:', scale, shift, 'min-max:', min, max
        return min, max

    def _alterPmtrMinMax(self, arg, offset=0):
        """replace all 'scale' and 'shift' values with min and max
        recursively check sub parameters if necessary
        all parameter objects use this; but need to only look at 
        rthm and generator parameter objects"""
        pmtrType = None
        for lib in ['rthmPmtrObjs', 'genPmtrObjs']:
            try:
                pmtrType = parameter.pmtrTypeParser(arg[0], lib)
            except error.ParameterObjectSyntaxError:
                continue
        # if nothing found it may not be a rthm or gen pmtr arg
        if pmtrType == None:
            if self.debug: print _MOD, 'cant alter pmtr min and max:', arg
            pmtrType = None
            
        # thes dont have scale or shift
        if pmtrType == 'basketGen':
            newArgs = None
        elif pmtrType == 'constant':
            newArgs = None
        elif pmtrType == 'cyclicGen':
            newArgs = None
        # these have scale and shift
        elif pmtrType == 'fibonacciSeries':
            min, max = self._scaleShiftToMinMax(arg[3], arg[4], offset)
            newArgs = (arg[0], arg[1], arg[2], min, max, arg[5])
        elif pmtrType == 'valueSieve':
            min, max = self._scaleShiftToMinMax(arg[3], arg[4], offset)
            newArgs = (arg[0], arg[1], arg[2], min, max, arg[5])
        elif pmtrType == 'logisticMap':
            min, max = self._scaleShiftToMinMax(arg[3], arg[4], offset)
            if drawer.isList(arg[2]): # parameter object
                argTest = self._alterPmtrMinMax(arg[2], offset) # recursive check
                if argTest != None: argSubPmtr = argTest
                else: argSubPmtr = arg[2]
            newArgs = (arg[0], arg[1], argSubPmtr, min, max)
        elif pmtrType == 'accumulator':
            argTest = self._alterPmtrMinMax(arg[2], offset) # recursive check
            if argTest != None: argSubPmtr = argTest
            else: argSubPmtr = arg[2]
            newArgs = (arg[0], arg[1], argSubPmtr)
        elif pmtrType == 'mask':
            argTestA = self._alterPmtrMinMax(arg[2], offset) # recursive check
            if argTestA != None: argSubPmtrA = argTestA
            else: argSubPmtrA = arg[2]
            argTestB = self._alterPmtrMinMax(arg[3], offset) # recursive check
            if argTestB != None: argSubPmtrB = argTestB
            else: argSubPmtrB = arg[3]
            argTestC = self._alterPmtrMinMax(arg[4], offset) # recursive check
            if argTestC != None: argSubPmtrC = argTestC
            else: argSubPmtrC = arg[4]
            newArgs = (arg[0], arg[1], argSubPmtrA, argSubPmtrB, argSubPmtrC)
        elif pmtrType in ['operatorAdd', 'operatorSubtract', 'operatorDivide', 
                                'operatorMultiply', 'operatorPower']:
            argTestA = self._alterPmtrMinMax(arg[1], offset) # recursive check
            if argTestA != None: argSubPmtrA = argTestA
            else: argSubPmtrA = arg[1]
            argTestB = self._alterPmtrMinMax(arg[2], offset) # recursive check
            if argTestB != None: argSubPmtrB = argTestB
            else: argSubPmtrB = arg[2]
            newArgs = (arg[0], argSubPmtrA, argSubPmtrB)
        elif pmtrType in ['waveSine', 'waveCosine', 'waveSawDown', 'waveSawUp', 
                                'wavePulse', 'waveTriangle']:
            min, max = self._scaleShiftToMinMax(arg[3], arg[4], offset)
            newArgs = (arg[0], arg[1], arg[2], min, max)
        elif pmtrType in ['wavePowerDown', 'wavePowerUp']:
            min, max = self._scaleShiftToMinMax(arg[4], arg[5], offset)
            newArgs = (arg[0], arg[1], arg[2], arg[3], min, max)
        elif pmtrType in ['randomUniform', 'randomLinear', 'randomInverseLinear',
                                'randomTriangular', 'randomInverseTriangular']:
            min, max = self._scaleShiftToMinMax(arg[1], arg[2], offset)
            newArgs = (arg[0], min, max)
        elif pmtrType in ['randomExponential', 'randomInverseExponential', 
                                'randomBilateralExponential']:
            min, max = self._scaleShiftToMinMax(arg[2], arg[3], offset)
            newArgs = (arg[0], arg[1], min, max)
        elif pmtrType in ['randomGauss', 'randomCauchy', 
                                'randomBeta', 'randomWeibull']:
            min, max = self._scaleShiftToMinMax(arg[3], arg[4], offset)
            newArgs = (arg[0], arg[1], arg[2], min, max)
        elif pmtrType == 'convertSecond':
            argTest = self._alterPmtrMinMax(arg[1], offset) # recursive check
            if argTest != None: argSubPmtr = argTest
            else: argSubPmtr = arg[1]
            newArgs = (arg[0], argSubPmtr)
        else: newArgs = None
        
        if newArgs != None:
            if self.debug: print _MOD, 'changed args:\n', arg, '\n', newArgs
        else:
            if self.debug: print _MOD, 'no change:', arg
        return newArgs 

    def _pre130_octaveAndMinMax(self):
        """change all scalar shift values to min max
        also fix bad octave values"""
        t = self.tData
        for tName in t['textureLib'].keys():
            for pmtrKey in t['textureLib'][tName]['pmtrQDict'].keys():
                pmtrData = t['textureLib'][tName]['pmtrQDict'][pmtrKey]
                if pmtrKey == 'octQ':
                    if self.debug: print _MOD, 'OCTAVE Q update'
                    newData = self._alterPmtrStatic(pmtrData, -8)
                    if newData == None: # not a static pmtr object data format
                        newData = self._alterPmtrMinMax(pmtrData, -8)
                    if newData == None:
                        msg = 'local octave may not be compatible; shift values by -8'
                        print lang.WARN, msg
                    else:
                        t['textureLib'][tName]['pmtrQDict'][pmtrKey] = newData
                elif pmtrKey not in ['inst',]:
                    newData = self._alterPmtrMinMax(pmtrData)
                    if newData != None:
                        t['textureLib'][tName]['pmtrQDict'][pmtrKey] = newData
                else:
                    pass

    #-----------------------------------------------------------------------||--
    # pre 1.3.0
    # bridge to 1.3 data formats, change instrument numbers for csound native

    def _pre130_pmtrObjStaticBeat(self):
        """post 1.3 the 'staticBeat' parameter object was removed
        this method will find any uses of it and in the beatT slot (should
        not be anywhere else) and replace it with a constant declaration
        """
        t = self.tData
        for tName in t['textureLib'].keys():
            for pmtrKey in t['textureLib'][tName]['pmtrQDict'].keys():
                if pmtrKey == 'beatT':
                    pmtrData = t['textureLib'][tName]['pmtrQDict'][pmtrKey]
                    if pmtrData[0] == 'staticBeat':
                        if self.debug: print _MOD, 'replacing staticBeat pmtrObj'
                        pmtrData = list(pmtrData)
                        pmtrData[0] = 'constant' # replace 'staticBeat' w/ constant
                        if self.debug: print _MOD, pmtrData
                    t['textureLib'][tName]['pmtrQDict'][pmtrKey]=tuple(pmtrData)
    
    def _pre130_instNumber(self):
        t = self.tData
        for tName in t['textureLib'].keys():
            for pmtrKey in t['textureLib'][tName]['pmtrQDict'].keys():
                pmtrData = t['textureLib'][tName]['pmtrQDict'][pmtrKey]
                if pmtrKey == 'inst':
                    oldNum = pmtrData[1]
                    if oldNum == 2: newNum = 60
                    elif oldNum == 4: newNum = 61
                    elif oldNum == 9: newNum = 62
                    elif oldNum == 13: newNum = 70
                    elif oldNum == 7: newNum = 71
                    elif oldNum == 6: newNum = 81
                    elif oldNum == 10: newNum = 80
                    else: newNum = oldNum
                    if newNum != oldNum:
                        newData = (pmtrData[0], newNum, 'csoundNative')
                        if self.debug: print _MOD, 'INST update', pmtrData, newData
                        t['textureLib'][tName]['pmtrQDict'][pmtrKey] = newData

    def _pre130_temperament(self):
        t = self.tData
        for tName in t['textureLib'].keys():
            for tAttr in t['textureLib'][tName].keys():
                # corrected this spelling mistake
                if tAttr == 'tempermentName':
                    if self.debug: print _MOD, 'replacing', tAttr
                    data = copy.copy(t['textureLib'][tName]['tempermentName'])
                    t['textureLib'][tName]['temperamentName'] = data


    def _pre130_missingAttr(self):
        """look for missing data"""
        # event mode added, and name changed
        if self.aData.has_key('eventModeName'): # temporary name
            self.aData['activeEventMode'] = self.aData['eventModeName']
            if self.debug: print _MOD, 'fixing eventMode name'
        if not self.aData.has_key('activeEventMode'):
            self.aData['activeEventMode'] = 'csoundNative'
            if self.debug: print _MOD, 'adding eventMode attribute'

        # add midi tempo (tData)
        if not self.tData.has_key('midiTempo'):
            self.tData['midiTempo'] = 120 # standard default
            if self.debug: print _MOD, 'adding default midiTempo'
            
        # changed names of pre 1.3 ao attributes
        if self.aData.has_key('TnItoggle'):
            self.aData['tniMode'] = self.aData['TnItoggle']
            if self.debug: print _MOD, 'fixing tniMode name'
            
        # path data names
        if self.pData.has_key('CurrentPE'): # may also be CurrentPathEngine
            self.pData['activeSetMeasure'] = self.pData['CurrentPE']
            if self.debug: print _MOD, 'fixing setMeasure name'
        if self.pData.has_key('CurrentPathEngine'):
            self.pData['activeSetMeasure'] = self.pData['CurrentPathEngine']
            if self.debug: print _MOD, 'fixing setMeasure name'
            
        if self.pData.has_key('PathBin'): # may be pathLib
            self.pData['pathLib'] = self.pData['PathBin']
            if self.debug: print _MOD, 'fixing PathBin name' 
        if self.pData.has_key('pathObjects'): # may be pathLib
            self.pData['pathLib'] = self.pData['pathObjects']
            if self.debug: print _MOD, 'fixing PathBin name' 
            
        if self.pData.has_key('CurrentPath'):
            self.pData['activePath'] = self.pData['CurrentPath']
            if self.debug: print _MOD, 'fixing CurrentPath name'
            
        if self.tData.has_key('CurrentTM'): # activeTextureModule
            self.tData['activeTextureModule'] = self.tData['CurrentTM']
            if self.debug: print _MOD, 'fixing CurrentTM name'            
        if self.tData.has_key('CurrentTextureMod'): # activeTextureModule
            self.tData['activeTextureModule'] = self.tData['CurrentTextureMod']
            if self.debug: print _MOD, 'fixing CurrentTM name'            

        if self.tData.has_key('TextureBin'):
            self.tData['textureLib'] = self.tData['TextureBin']
            if self.debug: print _MOD, 'fixing TextureBin name'
        if self.tData.has_key('textureObjects'):
            self.tData['textureLib'] = self.tData['textureObjects']
            if self.debug: print _MOD, 'fixing TextureBin name'
            
        if self.tData.has_key('CurrentTexture'):
            self.tData['activeTexture'] = self.tData['CurrentTexture']
            if self.debug: print _MOD, 'fixing CurrentTexture name'
            
        if self.tData.has_key('CloneBin'): # cloneLib
            self.tData['cloneLib'] = self.tData['CloneBin']
            if self.debug: print _MOD, 'fixing CloneBin name'
        if self.tData.has_key('textureClones'): # cloneLib
            self.tData['cloneLib'] = self.tData['textureClones']
            if self.debug: print _MOD, 'fixing textureClones name'

        if self.tData.has_key('MuteList'):
            muteList = self.tData['MuteList']
        else: muteList = []
        if self.debug: print _MOD, 'old muteList:', muteList

        for tName in self.tData['textureLib'].keys():
            tDict = self.tData['textureLib'][tName]
            if not tDict.has_key('mute'): 
                if tName in muteList: tDict['mute'] = 1
                else: tDict['mute'] = 0
                if self.debug: print _MOD, 'adding mute attribute:', tDict['mute']
            #   added 1.0.23
            if not tDict.has_key('midiPgm'): 
                tDict['midiPgm'] = None # will be provided
            if not tDict.has_key('midiCh'): 
                tDict['midiCh'] = None # will be provided
            # added for at 1.3 
            if not tDict.has_key('silenceMode'): 
                tDict['silenceMode'] = 0 # default is off
            # added for at 1.3; all previous should be off turned off
            if not tDict.has_key('orcMapMode'): 
                tDict['orcMapMode'] = 0 # default is off
            # rename pitchPath option 'usr' to 'ps' (post 1.3) 
            if tDict['pitchMode'].lower() == 'usr':
                tDict['pitchMode'] = 'ps'
                if self.debug: print _MOD, 'renaming texture pitch mode usr to ps'
            # change textIDXXX to tmName     
            if tDict.has_key('textID'):
                tDict['tmName'] = tDict['textID']                
                if self.debug: print _MOD, 'renaming textID'

    def _pre130_pathAttr(self):
        """ambitus is not yet implemented, but former default was 8
        now needs to be 0, w/ overal octave notation changed post 1.3 to 0
        for middle c (masking pch notation)"""
        for pName in self.pData['pathLib'].keys():
            if self.pData['pathLib'][pName]['ambitus'] == 8:
                self.pData['pathLib'][pName]['ambitus'] = 0
                if self.debug: print _MOD, 'updating path %s ambitus' % pName
            # rename old 'usrPath' to psPath 
            if 'usrPath' in self.pData['pathLib'][pName].keys():
                data = self.pData['pathLib'][pName]['usrPath']
                del self.pData['pathLib'][pName]['usrPath']
                self.pData['pathLib'][pName]['psPath'] = data
                if self.debug: print _MOD, 'renaming path usrPath'
            # rename old CurrentPathVoiceXXX to activeVoice
            if 'CurrentPathVoice' in self.pData['pathLib'][pName].keys():
                data = self.pData['pathLib'][pName]['CurrentPathVoice']
                del self.pData['pathLib'][pName]['CurrentPathVoice']
                self.pData['pathLib'][pName]['activeVoice'] = data
                if self.debug: print _MOD, 'renaming activeVoice'

            # rename pathVoiceSortsXXX to voiceRank
            if 'pathVoiceSorts' in self.pData['pathLib'][pName].keys():
                data = self.pData['pathLib'][pName]['pathVoiceSorts']
                del self.pData['pathLib'][pName]['pathVoiceSorts']
                self.pData['pathLib'][pName]['voiceRank'] = data
                if self.debug: print _MOD, 'renaming voiceRank'

            # rename pathVoicesXXX to voiceLib
            if 'pathVoices' in self.pData['pathLib'][pName].keys():
                data = self.pData['pathLib'][pName]['pathVoices']
                del self.pData['pathLib'][pName]['pathVoices']
                self.pData['pathLib'][pName]['voiceLib'] = data
                if self.debug: print _MOD, 'renaming pathVoices'
                
    #-----------------------------------------------------------------------||--
    # pre 1.3.0 clone fix

    def _basicCloneOption(self, rawVal):
        """generate a parameter object argument"""
        rawVal = basePmtr.retrogradeParser(rawVal)
        return ('retrogradeMethodToggle', rawVal) 

    def _basicCloneShift(self, rawVal):
        """generate a parameter object argument"""
        return ('filterAdd', ('c', rawVal)) 

    def _pre130_clones(self):
        """pre 1.3 clones where just lists of data
        data was stored in double dictionaries of tName, cName
        post 1.3 stored w/ tags that are combined tName,cName"""
        oldClone = {}
        t = self.tData
        for tName in t['cloneLib'].keys():
            for cName in t['cloneLib'][tName].keys():
                tag = '%s,%s' % (tName, cName) # get data list
                oldData = copy.deepcopy(t['cloneLib'][tName][cName])
                oldClone[tag] = oldData
        # clear data
        t['cloneLib'] = {}
        for tag in oldClone.keys():
            tName, cName = tag.split(',')
            cDict = {}
            # get data from texture
            cDict['auxNo'] = copy.deepcopy(t['textureLib'][tName]['auxNo'])
            cDict['mute'] = copy.deepcopy(t['textureLib'][tName]['mute'])
            cDict['pmtrQDict'] = {}
            # 0 was time shift
            cDict['pmtrQDict']['time'] = self._basicCloneShift(oldClone[tag][0])
            # 1 was amp shift 
            cDict['pmtrQDict']['ampQ'] = self._basicCloneShift(oldClone[tag][1])
            # 2 was transposition
            cDict['pmtrQDict']['fieldQ'] = self._basicCloneShift(oldClone[tag][2])
            # 1 is now retrograde 
            cDict['pmtrQDict']['cloneQ1']= self._basicCloneOption(oldClone[tag][3])

            # fill remaining values
            cDict['pmtrQDict']['acc']= ['b'] # bypass
            cDict['pmtrQDict']['sus']= ['b'] # bypass
            cDict['pmtrQDict']['octQ']= ['b'] # bypass
            cDict['pmtrQDict']['panQ']= ['b'] # bypass
            # fill aux pmtrs
            for label in basePmtr.auxLabel(cDict['auxNo']):
                cDict['pmtrQDict'][label]= self._basicCloneShift(0)

            t['cloneLib'][tag] = cDict
            if self.debug:
                print _MOD, 'updating clone:', tag, '\n',oldClone[tag], cDict




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
            if self.debug: print _MOD, 'changed args:\n', arg, '\n', newArgs
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
                    if self.debug: print _MOD, 'changed args:\n', arg, '\n', newArgs
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
                        if self.debug: print _MOD, 'replaced:', src, dst



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
                        if self.debug: print _MOD, 'replaced:', src, arg[1], dst, new

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
                        if self.debug: print _MOD, 'removed extra auxQ:', pmtrKey
        # clear extra clone aux as well
        for cName in t['cloneLib'].keys():
            auxNo = t['cloneLib'][cName]['auxNo']
            # store all valid
            auxLabelValid = basePmtr.auxLabel(auxNo)
            for pmtrKey in t['cloneLib'][cName]['pmtrQDict'].keys():              
                if pmtrKey not in auxLabelValid: # not a valid auxq
                    if pmtrKey[:4] == 'auxQ': # if it looks like an auxq
                        del t['cloneLib'][cName]['pmtrQDict'][pmtrKey]
                        if self.debug: print _MOD, 'removed extra auxQ:', pmtrKey
                        
                
    #-----------------------------------------------------------------------||--

    def process(self, aData, pData, tData):
        """main methods for providing backwards compat for global changes
        operates on raw python data lists, not on built objects
        smaller backwards compat may happen in lower level objects"""
        self.aData = aData
        self.pData = pData
        self.tData = tData

        if self.aData['version'] != 'pickled':
            self.fileVersionObj = argTools.Version(self.aData['version'])
        else: # first version w/ xml loading was 1.0.15
            self.fileVersionObj = argTools.Version('1.0.14') # assume before 1.0.15

        # first boundary: pre 1.3.0
        boundary = argTools.Version('1.3.0')
        if self.fileVersionObj < boundary:
            if self.debug: print _MOD, 'pre %s update necessary.' % str(boundary)
            # these need to be in this order
            self._pre130_missingAttr() # change names used throughout
            self._pre130_pathAttr()
            self._pre130_pmtrPrimitive()
            self._pre130_pmtrObjStaticBeat()
            self._pre130_setMeasure()
            self._pre130_octaveAndMinMax()
            self._pre130_instNumber()
            self._pre130_clones()
            self._pre130_temperament()

        # pre 1.4.0
        boundary = argTools.Version('1.4.0')
        if self.fileVersionObj < boundary:
            if self.debug: print _MOD, 'pre %s update necessary.' % str(boundary)
            self._pre140_pmtrObjUpdates()

        # pre 1.4.5 ; was 1.4.4, but had to increment to catch old errors
        # v. 1.4.5 may not exists
        boundary = argTools.Version('1.4.5')
        if self.fileVersionObj < boundary:
            if self.debug: print _MOD, 'pre %s update necessary.' % str(boundary)
            self._pre144_pmtrObjUpdates()
            self._pre145_cleanExtraAux()
            
        # return data
        return self.aData, self.pData, self.tData






