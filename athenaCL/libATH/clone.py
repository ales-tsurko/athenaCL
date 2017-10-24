#-----------------------------------------------------------------||||||||||||--
# Name:          clone.py
# Purpose:       class for holding access data from clone objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import copy, random
import unittest, doctest



from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import error
from athenaCL.libATH import pitchTools
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH import language
lang = language.LangObj()

_MOD = 'clone.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)

#-----------------------------------------------------------------||||||||||||--



class Clone:
    """object of a clone; similar to a texture, but processes
    score data; does not actually generate data, but modifies
    in many ways like texture object, but without diverse modules:
    one module to filter any event data

    clones are a non-real time entity: as the process the complete output
    of texture, and they are capable of reversing, there is no reason to
    treat them as real-time.

    clone's need to know the number of aux values, and list of aux pmtr 
    output formats when initiating and changing instrument
    
    note: if a clone processes its interanl esObj more than once, it will
    no longer reflect values from texture, but from sequential processing
    of the same values. for this reason, the esObj must always be refreshed
    before processing
    """

    def __init__(self, name=None, nameParent=None):
        self.name = name
        # get data from texture
        self.nameParent = nameParent # may be none

        self.pmtrQDict = {}
        self.pmtrObjDict = {}
        self.mute = 0 # mute boolean
        # this is now down with a cloneStatic parameterObject
        #self.timeRef = 'tt' # time reference, either texture or clone
        self.timeRangeAbs = None # absolute, calculated time rangec

        # used to store data pased to parameter objects
        self.refDict = {} # not yet used
        self.pmtrCommon = basePmtr.cCOMMONQ
        self.pmtrActive = self.pmtrCommon # default is all common are active

        # as textures, thes are defined in each module
        self.clonePmtrNames = ['timeReferenceSource', 'retrogradeMethodToggle']
        self.clonePmtrNo = len(self.clonePmtrNames)
        self.cloneLabels = basePmtr.cloneLabel(self.clonePmtrNo)

        self.auxNo = 0 # set w/ load method
        self.auxFmt = None # set w/ load method

    #-----------------------------------------------------------------------||--

    def _getMuteStr(self):
        """get mute string for named texture"""
        if self.mute: return lang.MUTEON
        else: return lang.MUTEOFF

    def _pmtrNumberToUsr(self, pmtr, shift, style='str'):
        """convert a parameter number string into data 
        numbers are returned as numbers, strings as strings
        str, and cmd produce un-altered numbers
        usr wil shift by appropriate values"""
        if drawer.isNum(pmtr):
            if style in ['str', 'cmd']:
                return pmtr
            elif style == 'usr':
                return pmtr + shift
        if drawer.isStr(pmtr):
            if style in ['str', 'cmd']:
                return pmtr
            elif style == 'usr':
                pmtr = drawer.strScrub(pmtr, 'lower')
                pmtr = pmtr.replace('q', '')
                return str(int(pmtr) + shift)

    def decodePmtrName(self, usrStr, style='cmd'):
        """translates user string to proper parameter key
        style = cmd uses parenthesis to show command name
            str provides simples string
            usr provides aux/text numbers w/ aprop shift

        >>> a = Clone()
        >>> a.decodePmtrName('c')
        ('acc', 'a(c)cent')
        """
        if usrStr == None: return None, ''
        p = drawer.strScrub(usrStr, 'lower')
        refNo = None # only used for aux, texture
        if p in ('t', 'time',):
            attrName = 'time'
            label = '(t)ime'
        elif p in ('u', 'sustain', 'sus'):
            attrName = 'sus'
            label = 's(u)stain'
        elif p in ('c', 'accent', 'acc'):
            attrName = 'acc'
            label = 'a(c)cent'
        elif p in ('f', 'field', 'fieldq'):
            attrName = 'fieldQ'
            label = 'local (f)ield'
        elif p in ('o', 'oct', 'octq'):
            attrName = 'octQ'
            label = 'local (o)ctave'
        elif p in ('a', 'amp', 'ampq'):
            attrName = 'ampQ'
            label = '(a)mplitude'
        elif p in ('n', 'pan', 'panq'):
            attrName = 'panQ'
            label = 'pan(n)ing'
        elif p[:1] == 'x' or p[:3] == 'aux':
            strNum, strLet = drawer.strExtractNum(p)
            attrName = 'auxQ' + strNum
            label = 'au(x)iliary'
            refNo = self._pmtrNumberToUsr(strNum, 0, style)
        elif p[:1] == 's' or p[:1] == 'c' or p[:5] == 'clone':
            strNum, strLet = drawer.strExtractNum(p)
            attrName = 'cloneQ' + p[1:]
            label = 'clone (s)tatic'
            refNo = self._pmtrNumberToUsr(strNum, 0, style)
        else:
            attrName = None
            label = ''

        if style == 'cmd': # leave parenthesis in names
            pass
        elif style in ['str', 'usr']: # remove parenthesis
            label = label.replace('(','')
            label = label.replace(')', '')
            if style == 'usr' and refNo != None:
                label = '%s %s' % (label, refNo)         
        return attrName, label


    def findCloneStaticLabel(self, usrStr):
        """find proper label for clone static options

        >>> a = Clone()

        """
        if usrStr not in self.cloneLabels:
            # try to match by parameter obj name
            usrStr = drawer.strScrub(usrStr, 'lower')
            for key in list(parameter.clonePmtrNames.keys()): # keys are short
                if usrStr == key: # get long name
                    usrStr = parameter.clonePmtrNames[key]
                    break
            found = 0
            # check for parameter names
            for key in self.cloneLabels:
                if usrStr.lower() == self.pmtrObjDict[key].type.lower():
                    usrStr = key
                    found = 1
                    break
            if not found:
                raise ValueError('bad label name for clone pmtr data: %s' % usrStr)
        return usrStr


    def _reprView(self, extData={}):
        """privide standard TIv display"""
        headList = []
        headList.append('TC: %s, TI: %s\n' % (self.name, 
                             self.nameParent))
        tStrAbs = typeset.timeRangeAsStr(self.timeRangeAbs)
        headList.append('%s%s: %s, duration: %s\n' % (lang.TAB, lang.MUTELABEL, 
                     self._getMuteStr(), tStrAbs))
        entryLines = []

        for p in ('time', 'sus', 'acc'):
            if p not in self.pmtrActive: continue
            attr, label = self.decodePmtrName(p)
            entryLines.append([label, self.pmtrObjDict[attr].repr()])
        for p in ('fieldQ', 'octQ', 'ampQ', 'panQ'):
            if p not in self.pmtrActive: continue
            attr, label = self.decodePmtrName(p)
            entryLines.append([label, self.pmtrObjDict[attr].repr()])

        if self.auxNo == 0:
            entryLines.append([self.decodePmtrName('x')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('x')[1], ''])
            for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
                valueStr = self.pmtrObjDict[auxLabel].repr()
                entryLines.append([(lang.TAB + 'x%i'% i), valueStr])

        if self.clonePmtrNo == 0:
            entryLines.append([self.decodePmtrName('s')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('s')[1], ''])
            for i, textLabel in basePmtr.cloneLabel(self.clonePmtrNo, 1):
                valueStr = self.pmtrObjDict[textLabel].repr()
                entryLines.append([(lang.TAB + 's%i'% i), valueStr])
        return headList, entryLines

    def _reprDocAuxArgs(self):
        """documentation for aix args; does not include title in the list"""
        entryLines = []
        if self.auxNo != 0:
            for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
                valueStr = self.pmtrObjDict[auxLabel].reprDoc('argsMax')
                #labelStr = '%sx%i'% (lang.TAB, i)
                entryLines.append(['', valueStr])
        return entryLines

    def _reprDocStandard(self, extData={}):
        """return documentation for standard parameters"""
        headList = []
        headList.append('TC: %s, TI: %s\n' % (self.name, 
                             self.nameParent))
        entryLines = []     
        for p in ('time', 'sus', 'acc', 'fieldQ', 'octQ', 'ampQ', 'panQ'):
            if p not in self.pmtrActive: continue
            valueStr = self.pmtrObjDict[p].reprDoc('argsMax')
            entryLines.append([self.decodePmtrName(p)[1], valueStr])
        return headList, entryLines


    def _reprDocStatic(self, extData={}):
        """privide a partial documentation view for TIdoc display
        aux doc string will come form the texture
        place before entrLines from here
        """                                  
        entryLines = []     
        if self.clonePmtrNo == 0:
            entryLines.append([self.decodePmtrName('s')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('s')[1], ''])
            for i, textLabel in basePmtr.cloneLabel(self.clonePmtrNo, 1):
                valueStr = self.pmtrObjDict[textLabel].reprDoc('argsMax')
                #valueStr = self.getCloneStaticArgsLabel(textLabel)
                entryLines.append([(lang.TAB + 's%i'% i), valueStr])
        return entryLines
        
    def _reprList(self, refDict):
        activeStr = refDict['activeStr']
        tStr = typeset.timeRangeAsStr(self.timeRangeAbs)
        return [activeStr, self.name, self._getMuteStr(), tStr]

    def repr(self, style=None, refDict={}):
        if style == None:
            return '%s: %s' % (self.nameParent, self.name)
        elif style == 'full':
            return self._reprView(refDict)
        elif style == 'list':
            return self._reprList(refDict)
        elif style == 'docStandard':
            return self._reprDocStandard(refDict)
        elif style == 'docStatic':
            return self._reprDocStatic(refDict)
        elif style == 'docAuxArgs':
            return self._reprDocAuxArgs()
        elif style == 'mute':
            return self._getMuteStr()

    def __str__(self):
        return self.repr()


    #-----------------------------------------------------------------------||--

    def load(self, pmtrQDict, auxNo, auxFmt, mute=0):
        """load clone data
        tRef is time reference, either clone or texture time
        load, unlike texture, does not automatically score"""
        self.mute = mute
        self.auxNo = auxNo
        self.auxFmt = auxFmt
        #as cloneStatic parameterObject
        #self.timeRef = timeRef 

        self.pmtrObjDict = {}
        self.pmtrQDict = copy.deepcopy(pmtrQDict)

        self.pmtrObjDict['time'] = parameter.factory(self.pmtrQDict['time'],
                                                      'filterPmtrObjs')
        self.pmtrObjDict['sus'] = parameter.factory(self.pmtrQDict['sus'],
                                                      'filterPmtrObjs')
        self.pmtrObjDict['acc'] = parameter.factory(self.pmtrQDict['acc'],
                                                         'filterPmtrObjs')
        self.pmtrObjDict['fieldQ'] = parameter.factory(self.pmtrQDict['fieldQ'],
                                                        'filterPmtrObjs')
        self.pmtrObjDict['octQ'] = parameter.factory(self.pmtrQDict['octQ'],
                                                          'filterPmtrObjs')
        self.pmtrObjDict['ampQ'] = parameter.factory(self.pmtrQDict['ampQ'],
                                                         'filterPmtrObjs')
        self.pmtrObjDict['panQ'] = parameter.factory(self.pmtrQDict['panQ'],
                                                     'filterPmtrObjs')

        for auxLabel in basePmtr.auxLabel(self.auxNo):
            self.pmtrObjDict[auxLabel] = parameter.factory( 
                                     self.pmtrQDict[auxLabel], 'filterPmtrObjs')

        self._updateClonePmtrDefaults()
        for cloneLabel in self.cloneLabels: # load object into textPmtr object
            args = self.pmtrQDict[cloneLabel]
            self.pmtrObjDict[cloneLabel] = parameter.factory(args, 
                                      'clonePmtrObjs', self.refDict)

    def _defaultPmtrArg(self):
        """get basic pmtr used as default"""
        return ('bypass',)

    def loadDefault(self, auxNo, auxFmt):
        """create an empty clone dict
        note: no refershing of event is done here; just loads parameters obs

        >>> a = Clone()
        >>> a.loadDefault(3, 'num')
        """
        # defaults do not come from anywhere else...
        self.auxNo = auxNo
        pmtrQDict = {}
        pmtrQDict['time'] = ('filterAdd', ('l',(1,) ))
        pmtrQDict['sus'] = self._defaultPmtrArg()
        pmtrQDict['acc'] = self._defaultPmtrArg()
        pmtrQDict['ampQ'] = self._defaultPmtrArg()
        pmtrQDict['panQ'] = self._defaultPmtrArg()
        pmtrQDict['octQ'] = self._defaultPmtrArg()
        pmtrQDict['fieldQ'] = self._defaultPmtrArg()
        for auxLabel in basePmtr.auxLabel(self.auxNo):
            pmtrQDict[auxLabel] = self._defaultPmtrArg()
        self.load(pmtrQDict, auxNo, auxFmt)


    #-----------------------------------------------------------------------||--
    def copy(self, name=None, nameParent=None):
        """return a copy of this clone
        optionally, can chnage name and name of Parent at creation"""
        #note: this seems like a circular import, but no exception is raised

        pmtrQDict = copy.deepcopy(self.pmtrQDict)
        auxNo = copy.deepcopy(self.auxNo) # number of auxiliary parameters
        auxFmt = copy.deepcopy(self.auxFmt) # output format of parent aux values
        mute = copy.deepcopy(self.mute)
        # timeRef = copy.deepcopy(self.timeRef)

        from athenaCL.libATH import clone
        # will assume that parent stays the same unless named
        if nameParent == None:
            nameParent = self.nameParent
        obj = clone.Clone(name, nameParent) 
        # use main load function to load texture
        obj.load(pmtrQDict, auxNo, auxFmt, mute)
        return obj


    #-----------------------------------------------------------------------||--
    def _updateInstPmtr(self, refDict):
        """when a texture's instrument is changed, aux numbers may change
        this change must be represented in the clone
        updates the parameter dict to that of a new instrument
        does not reload objects; must be done with updatePmtrObj
        used for converting/refreshing instruments      
        """
        oldAuxNo = self.auxNo # store old
        self.auxNo = refDict['auxNo'] # aux no passed in ref dict
        self.auxFmt = refDict['auxFmt'] # aux no passed in ref dict
        oldPmtrDict = copy.deepcopy(self.pmtrQDict)
        
        #print _MOD, 'clone: oldAuxNo, self.AuxNo', oldAuxNo, self.auxNo
        print(lang.WARN, 'new Clone auxiliary value %s' % self.auxNo)

        # remove old aux values 
        for auxLabel in basePmtr.auxLabel(oldAuxNo):
            del self.pmtrQDict[auxLabel]
            if auxLabel in list(self.pmtrObjDict.keys()): # remove objects if they exist
                del self.pmtrObjDict[auxLabel]
        
        # insert new values from defaults
        for auxLabel in basePmtr.auxLabel(self.auxNo):
            self.pmtrQDict[auxLabel] = self._defaultPmtrArg()

    def _updateClonePmtrDefaults(self):
        """this only supplies names, which wil load defaults"""
        for i, cloneLabel in basePmtr.cloneLabel(self.clonePmtrNo, 1):
            # add arg list default if missing to pmtrQdict
            if not cloneLabel in list(self.pmtrQDict.keys()):
                args = [self.clonePmtrNames[i],]
                dummyObj = parameter.factory(args, 'clonePmtrObjs', self.refDict)
                self.pmtrQDict[cloneLabel] = dummyObj.getArgs()

    def _evalPmtrObj(self, pmtrName, refDict):
        """called for editing a single parameter object
        handle all exceptions of parameter creation
        """
        args = self.pmtrQDict[pmtrName]
        if pmtrName[:6] == 'cloneQ': # check texture options
            try:
                self.pmtrObjDict[pmtrName] = parameter.factory(args, 
                                                  'clonePmtrObjs', refDict)
            except error.ParameterObjectSyntaxError as msg: 
                # initialization errors
                return 0, 'incorrect arguments: %s' % msg
        else:
            try:
                self.pmtrObjDict[pmtrName] = parameter.factory(args,
                                           'filterPmtrObjs', refDict)
            except error.ParameterObjectSyntaxError as msg: 
                # initialization errors
                return 0, 'incorrect arguments: %s' % msg
        # check for errors
        if self.pmtrObjDict[pmtrName] == None: # failure to match object type
            return 0, 'there is no parameterObject with that name.'
        # check for proper types
        elif pmtrName[:6] == 'cloneQ':
            if self.pmtrObjDict[pmtrName].parent != 'cloneStatic':
                return 0, 'only a clone parameterObject can be used here.'
        else:
            #print _MOD, 'parent', self.pmtrObjDict[pmtrName].parent
            if self.pmtrObjDict[pmtrName].parent != 'cloneFilter':
                return 0, 'a clone filter parameterObject must be used here.'
        # everything good, check args
        ok, msg = self.pmtrObjDict[pmtrName].checkArgs()
        return ok, msg

    def updatePmtrObj(self, pmtrName='', refDict={}):
        """if no pmtr given, reinitializes complete pmtr object
        if pmtr given, reinits just that pmtr
        when called during edit of a texture, self.pmtrQDict has been replaced
        cannot change inst from here; must be done from ww/n texture
        """
        # this cand destroy the pmtrQDict
        assert pmtrName != 'pmtrQDict'
        if pmtrName == 'inst':
            self._updateInstPmtr(refDict) # inst already set in pmtrQDict
            pmtrName = '' # force reinit of all parameters
        if pmtrName != '':
            ok, msg = self._evalPmtrObj(pmtrName, refDict)
        else: # reinit all paramters, no name given
            for pmtrName in list(self.pmtrQDict.keys()):
                ok, msg = self._evalPmtrObj(pmtrName, refDict)
                if ok != 1: break # stop processing on error
        # post update actions:
        return ok, msg

    def _editRestore(self, attrName, pmtrName, data, refDict):
        setattr(self, attrName, data)
        ok, msg = self.updatePmtrObj(pmtrName, refDict)
        # this should never fail
        if not ok: raise ValueError('clone edit: original data cannot be restored: %s' % msg)
        
    def editPmtrObj(self, pmtrName, pmtrValue, refDict, esObj=None, refresh=1):
        """refresh: turn off score generation
        clearing a clone may be good; texture should not be cleared
        clearing the esObj of a clone causes a problem when trying to 
        using the TCmap comamnd; for now, do not clear score
        self.clearScore() # dont store all this data, but pmtrs updated
        """
        p = pmtrName
        newData = pmtrValue
        if (p in self.pmtrCommon and p not in self.pmtrActive):
            return None, 'no %s parameter in TC %s.' % (p, self.name)
        elif (p in ('time', 'sus', 'acc', 'ampQ', 'panQ', 'fieldQ', 'octQ',) or
                        p[:4]=='auxQ' or p[:6]=='cloneQ'):
            if p[:4] == 'auxQ':
                if p not in basePmtr.auxLabel(self.auxNo):
                    return 0, 'no such auxiliary label'
            if p[:6] == 'cloneQ':
                if p not in basePmtr.cloneLabel(self.clonePmtrNo):
                    return 0, 'no such clone label'
            attrName = 'pmtrQDict'
            oldData = self.pmtrQDict # attrReference
            newData = copy.deepcopy(self.pmtrQDict)  # copy old dict
            newData[p] = pmtrValue
        else:
            return 0, 'incorrect parameter label access.'
        setattr(self, attrName, newData) # make change
        try: # try to refresh objects
            editPhase = 'object creation:'
            ok, msg = self.updatePmtrObj(p, refDict)
            if not ok:
                self._editRestore(attrName, p, oldData, refDict)
                return ok, msg
            if refresh and esObj != None: # test w/ an esObj
                editPhase = 'score creation:'
                ok = self.score(esObj, refDict)
                if not ok:
                    self._editRestore(attrName, p, oldData, refDict)
                    return ok, 'score creation returned an error.'
        except error.ParameterObjectSyntaxError as msg: # standard init errors from pmtr obj
            msg = '%s %s' % (editPhase, msg)
            ok = 0
        except IndexError as msg:
            msg = '%s incorrect number of arguments. %s.' % (editPhase, msg)
            ok = 0
        except TypeError as msg:
            msg = '%s incorrect data-type in arguments. %s' % (editPhase, msg)
            ok = 0 
        except UnboundLocalError as msg:
            msg = '%s incorrect paramater type in arguments. %s' % (editPhase, msg)
            ok = 0
        except ValueError as msg:
            msg = '%s value error: an inappropriate data type used.' % editPhase
            ok = 0
        except ZeroDivisionError:
            msg = '%s zero division error: zero cannot be a divisor.' % editPhase
            ok = 0
        if not ok:
            self._editRestore(attrName, p, oldData, refDict)
            return ok, msg
        return 1, '' # success


    #-----------------------------------------------------------------------||--
    # these all expect array arguments: lists of data for each event
    # refDict is a refDictArray, a list of refDict's

    def getTime(self, valArray, tEvalArray, refDict):
        """get time value for a given ref time value
        values must be shifted to 0 and then repositioned later
        so all scaling is fine, positive or negative"""
        return self.pmtrObjDict['time'](valArray, tEvalArray, refDict)

    def getSus(self, valArray, tEvalArray, refDict):
        return self.pmtrObjDict['sus'](valArray, tEvalArray, refDict)

    def getAcc(self, valArray, tEvalArray, refDict):
        return self.pmtrObjDict['acc'](valArray, tEvalArray, refDict)

    def getAmp(self, valArray, tEvalArray, refDict):
        return self.pmtrObjDict['ampQ'](valArray, tEvalArray, refDict)

    def getPan(self, valArray, tEvalArray, refDict):
        """pan values are limted to 0 to 1; preform a mod 1"""
        pan = self.pmtrObjDict['panQ'](valArray, tEvalArray, refDict)
        for i in range(0, len(pan)): # do mod 1
            if pan[i] < 0 or pan[i] > 1:
                pan[i] = pan[i] % 1.0
        return pan
    
    def getField(self, valArray, tEvalArray, refDict):
        return self.pmtrObjDict['fieldQ'](valArray, tEvalArray, refDict)

    def getOct(self, valArray, tEvalArray, refDict):
        """value input is a ps value, need to extract
        octave information and only process this, then restore
        it to pitch space"""
        octArray = []
        pcArray = []
        # get octave data form ps; micro will not be lost
        for val in valArray: 
            oct, pc = pitchTools.splitOctPs(val)
            octArray.append(oct)
            pcArray.append(pc)
        # process oct data
        octArray = self.pmtrObjDict['octQ'](octArray, tEvalArray, refDict) 
        # micro in pc will not be lost
        valArray = []
        for i in range(0, len(octArray)): # restpr w/ pc
            oct = octArray[i]
            pc = pcArray[i]
            valArray.append(pitchTools.joinPsReal(oct, pc, 0))
        return valArray

    def getAux(self, valueArrayList, tEvalArray, refDict):
        """ get the value list from texture aux parameter
        valueArrayList is a list of aux values for each event
        this needs to be converted into a list of values for each aux       
        then converted back 
        """
        auxEventList = [] # seperate val for each aux
        for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
            auxEventList.append([]) # add a list for each aux
        # go through values and split each aux into separate list, chanelize
        for event in valueArrayList:
            assert len(event) == self.auxNo
            for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
                auxEventList[i].append(event[i])
        # process dataArray in each aux independently
        for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
            valArray = auxEventList[i] # dataArray for one aux value
            auxArray = self.pmtrObjDict[auxLabel](valArray, tEvalArray, refDict)
            auxEventList[i] = auxArray

        # restore to format where each event has all array values
        auxiliary  = []
        for e in range(0,len(valueArrayList)): # go through each event
            eventData = []
            # get data for each aux in this event, put into one list
            for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
                eventData.append(auxEventList[i][e])
            auxiliary.append(eventData)
        return auxiliary

    #-----------------------------------------------------------------------||--
    # since all clones have the same clone options, can list each by name
    # cant do this w/ textures objs; better to keep parallel itnerface

    def getCloneStatic(self, label, data=None):
        """get data from text static parameters
        lable is the name or number; data is the name of the argument"""
        label = self.findCloneStaticLabel(label)
        if data != None:
            return self.pmtrObjDict[label](data)
        else: # return complete arg list
            return self.pmtrObjDict[label].getArgs()

    def getCloneStaticName(self, label):
        label = self.findCloneStaticLabel(label)
        return self.pmtrObjDict[label].type

    def getCloneStaticArgsLabel(self, label):
        label = self.findCloneStaticLabel(label)
        return self.pmtrObjDict[label].getArgsLabel()

    #-----------------------------------------------------------------------||--


    def _scorePre(self, esObj, refDictTexture): # called w/n score method
        """take a texure-style refDict and convert it into a refDictArray
        a new esObj must be supplied; cannot process internal esObj
        more than once

        Note that refDict array has at a minimum a specification for 
        the BPM of each note.
        """
        # should check that it has events
        self.esObj = esObj.copy() # dont assume this is a copy
        if len(self.esObj) == 0:
            raise Exception('no events in EventSequence object')

        for pmtrName in list(self.pmtrQDict.keys()):
            if pmtrName[:6] != 'cloneQ': # check texture options
                # reset all necessary variables before scoring
                self.pmtrObjDict[pmtrName].reset() 
        bpmArray = self.esObj.getArray('bpm')

        self.refDictArray = []
        for val in bpmArray: # use refDict from texture to create a new refArray
            eventDict = copy.deepcopy(refDictTexture)
            eventDict['bpm'] = val
            self.refDictArray.append(eventDict)

        # update event object
        self.esObj.updatePre()

    def _scoreMain(self):
        """ref dict is used to pass necessary values to sub-parameter objects
        such sadr, ssdr, and bpm
        there must be a refDict of each event, as that is where a pmtr looks
        to find rhythm values"""
        
        # get retrgrade type
        retroType = self.getCloneStatic('retrogradeMethodToggle', 'name') 
        self.esObj.retrograde(retroType)

        # do step transformations 
        tPreArray = self.esObj.getArray('time')
        # do time transformation first
        valArray = self.getTime(tPreArray, tPreArray, self.refDictArray)
        self.esObj.setArray('time', valArray)

        # update time reference
        self.timeRef = self.getCloneStatic('timeReferenceSource', 'name') 

        # get new time values after possible shift
        # may need to evaluate with this (ct) or origina (tt)
        tPostArray = self.esObj.getArray('time')
        if self.timeRef == 'tt': # texture time
            tArray = tPreArray
        else: # 'ct', clone time
            tArray = tPostArray

        # process values for each parameter
        valArray = self.esObj.getArray('sus')
        valArray = self.getSus(valArray, tArray, self.refDictArray)
        self.esObj.setArray('sus', valArray)

        valArray = self.esObj.getArray('acc')
        valArray = self.getAcc(valArray, tArray, self.refDictArray)
        self.esObj.setArray('acc', valArray)

        valArray = self.esObj.getArray('amp')
        valArray = self.getAmp(valArray, tArray, self.refDictArray)
        self.esObj.setArray('amp', valArray)

        valArray = self.esObj.getArray('pan')
        valArray = self.getPan(valArray, tArray, self.refDictArray)
        self.esObj.setArray('pan', valArray)

        # pitch takes 2 steps
        valArray = self.esObj.getArray('ps')
        valArray = self.getField(valArray, tArray, self.refDictArray)
        valArray = self.getOct(valArray, tArray, self.refDictArray)
        self.esObj.setArray('ps', valArray)

        # aux is a list of auxArrays
        # for each event, will get a list of values for all aux pmtrs
        valArrayList = self.esObj.getArray('aux') # a list of lists
        valArrayList = self.getAux(valArrayList, tArray, self.refDictArray)
        self.esObj.setArray('aux', valArrayList)
        return 1 # return 1 on success

    def _scorePost(self): # called w/n score method
        # no longer need refDictArray; delete:
        del self.refDictArray 
        self.esObj.updatePost()
        self.timeRangeAbs = self.esObj.getTimeRangeAbs()

    def score(self, esObj, refDictTexture): # main method called for scoring
        """provide an esObj; transform it into a new a esObj (score_
        refDictTexture is a single, standard refDict from a texture
        will be mangled into what is needed for clone: a refDictArray
        """
        #print _MOD, 'clone score method called.'
        self._scorePre(esObj, refDictTexture)
        ok = self._scoreMain()
        self._scorePost()
        return ok

    def getScore(self):
        assert len(self.esObj) != 0
        return self.esObj.copy() # return copy of object

    def clearScore(self):
        #print _MOD, 'clearing score'
        self.esObj.clear() # clear event sequence












#-----------------------------------------------------------------||||||||||||--

class CloneManager:
    """object to store colones by texture name"""
    def __init__(self):
        self._tRef = {} # stores dictionaries of clone object by t name
        self._tRefCurrent = {} # store name of current selected

    def tNames(self):
        """return names of textures that have keys"""
        return list(self._tRef.keys())
    
    def cNames(self, tName):
        """return the names of the clone for a named textuire
        if texture does not have clones, returns None"""
        if tName not in self.tNames(): return []
        names = list(self._tRef[tName].keys())
        names.sort()
        return names

    def cExists(self, tName, name):
        if name in self.cNames(tName): return 1
        else: return 0

    def number(self, tName):
        if tName not in self.tNames(): return 0
        return len(self._tRef[tName])

    #-----------------------------------------------------------------------||--
    # easy acces routines for getting data form clone objects
    # since all clone objects are the same, this is okay
    # will fail if no clones exist: might need to create temporary objects

    def decodePmtrName(self, usrStr, style='cmd'):
        """access this method from elsewhere"""
        tName = random.choice(self.tNames())
        cName = self._tRefCurrent[tName]
        return self._tRef[tName][cName].decodePmtrName(usrStr, style)

    def clonePmtrNo(self):
        """always the same for all clones; get value"""
        tName = random.choice(self.tNames())
        cName = self._tRefCurrent[tName]
        return self._tRef[tName][cName].clonePmtrNo

    #-----------------------------------------------------------------------||--
    def load(self, tName, cName, pmtrQDict, auxNo, auxFmt, mute=0):
        """initialize a clone object inside the appropriate texture label"""
        if not tName in list(self._tRef.keys()):
            self._tRef[tName] = {}
        if cName in list(self._tRef[tName].keys()):
            raise error.CloneError('clone name already exists')
        self._tRef[tName][cName] = Clone(cName, tName)
        self._tRef[tName][cName].load(pmtrQDict, auxNo, auxFmt, mute)
        self._tRefCurrent[tName] = cName

    def loadDefault(self, tName, cName, auxNo, auxFmt):
        """initialize a clone object inside the appropriate texture label"""
        if not tName in list(self._tRef.keys()):
            self._tRef[tName] = {}
        if cName in list(self._tRef[tName].keys()):
            raise error.CloneError('clone name already exists')
        self._tRef[tName][cName] = Clone(cName, tName)
        self._tRef[tName][cName].loadDefault(auxNo, auxFmt)
        self._tRefCurrent[tName] = cName

# this method is not correct; not in use either
#     def edit(self, tName, cName, pmtrName, pmtrValue, esObj=None, refresh=1):
#         return self._tRef[tName][cName].editPmtrObj(pmtrName, pmtrValue, 
#                                                                    esObj, refresh)

    def mute(self, tName, cName, force=None):
        """mute a clone; can force on or off"""
        if force != None:
            self._tRef[tName][cName].mute = force
        elif self._tRef[tName][cName].mute: # already muted
            self._tRef[tName][cName].mute = 0
        else: # mute
            self._tRef[tName][cName].mute = 1

    def muteStatus(self, tName, cName):
        return self._tRef[tName][cName].mute

    def delete(self, tName, cName=None):
        if cName == None: # delete all of a texture's clones
            if tName in list(self._tRef.keys()):
                del self._tRef[tName]
                del self._tRefCurrent[tName]
            else: # this should not happen
                environLocal.printDebug['attempting to remove clone from texture %s not stored in tRef' % tName]
        else:
            if tName in list(self._tRef.keys()):
                del self._tRef[tName][cName]
            else: # this should not happen
                environLocal.printDebug['attempting to remove clone from texture %s not stored in tRef' % tName]

            if self._tRefCurrent[tName] == cName:
                self._tRefCurrent[tName] = '' # nothing selected

    def tMove(self, tOld, tNew):
        """change the name of a texture"""
        if tNew in self.tNames():
            raise error.CloneError('texture name already exists')         
        self._tRef[tNew] = self._tRef[tOld]
        del self._tRef[tOld]
        self._tRefCurrent[tNew] = self._tRefCurrent[tOld]
        del self._tRefCurrent[tOld]

    def cMove(self, tName, cOld, cNew):
        """change the name of a clone"""
        if cNew in self.cNames(tName):
            raise error.CloneError('clone name already exists')
        self._tRef[tName][cNew] = self._tRef[tName][cOld]
        del self._tRef[tName][cOld]
        if self._tRefCurrent[tName] == cOld: # selected
            self._tRefCurrent[tName] = cNew

    def cCopy(self, tName, cOld, cNew):
        """copy a clone within the same texture"""
        if cNew in self.cNames(tName):
            raise error.CloneError('clone name already exists')
        self._tRef[tName][cNew] = self._tRef[tName][cOld].copy(cNew, tName)
        if self._tRefCurrent[tName] == cOld: # selected
            self._tRefCurrent[tName] = cNew
            
    def tCopy(self, tOld, tNew):
        """when a texture is copied, copy all clones within the same texture
        this does not copy the texture; just sets up the necessary clones
        note: not all textures are gotten with self.tNames; only textures tt
        have clones
        """
        if tNew in self.tNames():
            raise error.CloneError('bad source or destination texture naming')
        if tOld not in self.tNames(): # cant do anything with this; no clones
            return None
        self._tRef[tNew] = {}
        for name in self.cNames(tOld):
            self._tRef[tNew][name] = self._tRef[tOld][name].copy(name, tNew)
            if self._tRefCurrent[tOld] == name: # update selected
                self._tRefCurrent[tNew] = name
        
    def get(self, tName, cName):
        """get a reference to a real clone obj"""
        return self._tRef[tName][cName]


    #-----------------------------------------------------------------------||--
    # tools for storing current clone name
    # there can be a current clone for each ti name

    def select(self, tName, cName):
        if cName in self.cNames(tName):
            self._tRefCurrent[tName] = cName

    def current(self, tName):
        if self._tRefCurrent[tName] == '':
            if self.number > 0: # select one
                cName = random.choice(self.cNames(tName))
                self._tRefCurrent[tName] = cName
                return cName
            else:
                return None
        else:
            return self._tRefCurrent[tName]



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        a = Clone('test', 'parentTest')
        a.loadDefault(3, 'num')
        post = a.repr('full')

        b = a.copy()
        b.updatePmtrObj()
        post = b.editPmtrObj('time', ('filterAdd', ('c', 120)), {})


    def testCloneParameterObjects(self):
        from athenaCL.libATH.libPmtr import cloneFilter
        #a = cloneFilter.Bypass('', [])

        # TODO: getting this error when trying to run this test
        # TypeError: unbound method __init__() must be called with FilterParameter instance as first argument (got Bypass instance instead)



#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)