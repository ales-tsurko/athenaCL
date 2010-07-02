#-----------------------------------------------------------------||||||||||||--
# Name:          baseTexture.py
# Purpose:       base class for all textures.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest


from athenaCL.libATH import temperament
from athenaCL.libATH import multiset

# from athenaCL.libATH import SC
# scObj = SC.SetClass()
from athenaCL.libATH import language
lang = language.LangObj()

from athenaCL.libATH import pitchPath
from athenaCL.libATH import drawer
from athenaCL.libATH import error
from athenaCL.libATH import typeset
from athenaCL.libATH import eventList # get EventSequence obj
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH.libPmtr import basePmtr # used to string prefixes
from athenaCL.libATH.libOrc import orc
from athenaCL.libATH.libOrc import generalMidi
from athenaCL.libATH.omde import bpf # needed for interpolation

_MOD = 'baseTexture.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)



#-----------------------------------------------------------------||||||||||||--
class ClockRegion:
    def __init__(self, tStart, tEnd):
        """
        >>> a = ClockRegion(0, 20)
        >>> a.repr()
        '0:20 (20)'
        """
        if tStart >= tEnd:
            raise ValueError
        self.tStart = tStart
        self.tEnd = tEnd
        self.dur = self.tEnd - self.tStart

    def repr(self, style=None):
        if style == None:
            return '%s:%s (%s)' % (self.tStart, self.tEnd, self.dur)
        elif style == 'dur': # used in TIv display
            return '%.2f(s)' % self.dur

    def __str__(self):
        return self.repr()


#-----------------------------------------------------------------||||||||||||--
class Texture(object):
    """inherited by all textures: all common variables for all textures
    utility and loading functions    
    a texture has 3 parameter sources: default, aux, and texture
    pmtrActive defines which parameters are available from common
    texuture parameters defined in texture
    aux parameters defined by instrument
    """
    def __init__(self, name=None):
        """init variables used only during score creation
            additional variable added later

        >>> a = Texture()
        """
        self.name = name
        self.doc = None # from subclass
        self.mute = 0

        self.esObj = eventList.EventSequence() # greate a blank seq
        # this method will initialize all state variables and assign to none
        self.stateClear()

        self.timeRangeAbs = None # absolute, calculated time range
        self.clockPath = [] # list of clock objects

        # used to store data pased to parameter objects
        self.refDict = {}
        # name parameter fields that are active
        # aux and text parameters cannot be turned off
        self.pmtrCommon = basePmtr.tCOMMONQ
        self.pmtrActive = self.pmtrCommon # default is all common are active

        self.pmtrQDict = {}
        self.pmtrObjDict = {}

        self.auxNo = 0 # set with load
        
        # these are set w/ _updateTextPmtrInit
        self.textPmtrNames = []
        self.textPmtrNo = 0 # set in subclass 
        self.dynPmtrManifest = [] # primary defining attribute for dyn pmtrs
        self.dynPmtrNo = 0 # set in subclass 

    #-----------------------------------------------------------------------||--

    def _getMuteStr(self):
        """get mute string for named texture"""
        if self.mute: return lang.MUTEON
        else: return lang.MUTEOFF

    def _pmtrNumberToUsr(self, pmtr, shift, style='str'):
        """convert a parameter number string into data 
        numbers are returned as numbers, strings as strings
        str, and cmd produce un-altered numbers
        usr wil shift by appropriate values

        >>> a = Texture()
        >>> a._pmtrNumberToUsr('3', 0)
        '3'
        """

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

        >>> a = Texture()
        >>> a.decodePmtrName('amp')
        ('ampQ', '(a)mplitude')
        >>> a.decodePmtrName('p')
        ('path', '(p)ath')
        """
        if usrStr == None: return None, ''
        p = drawer.strScrub(usrStr, 'lower')
        refNo = None # only used for aux, texture

        if p in ('inst', 'i'):
            attrName = 'inst'
            label = '(i)nstrument'
        elif p in ('p', 'path'):
            attrName = 'path'
            label = '(p)ath'
        elif p in ('t', 't_range', 'trange'):
            attrName = 'tRange'
            label = '(t)ime range'
        elif p in ('b', 'bpm', 'beat', 'beatt'):
            attrName = 'beatT'
            label = '(b)pm'
        elif p in ('r', 'rhythm', 'rhythmq'):
            attrName = 'rhythmQ'
            label = '(r)hythm'
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
        elif p[:1] in ['e', 's'] or p[:4] == 'text':
            strNum, strLet = drawer.strExtractNum(p)
            attrName = 'textQ' + strNum
            label = 'texture (s)tatic'
            refNo = self._pmtrNumberToUsr(strNum, 0, style)
        elif p[:1] == 'd' or     p[:4] == 'dynQ':
            strNum, strLet = drawer.strExtractNum(p)
            attrName = 'dynQ' + strNum
            label = 'texture (d)ynamic'
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

    #-----------------------------------------------------------------------||--
    # tools for textPmtr control and access
    def findTextStaticLabel(self, usrStr):
        """get satic texture option label from a usr string
        will raise ValueError with bad name"""
        if usrStr not in self.textLabels:
            # try to match by parameter obj name
            usrStr = drawer.strScrub(usrStr, 'lower')
            for key in parameter.textPmtrNames.keys():
                if usrStr == key: # get long name
                    usrStr = parameter.textPmtrNames[key]
                    break
            found = 0
            # check for parameter names
            for key in self.textLabels:
                if usrStr.lower() == self.pmtrObjDict[key].type.lower():
                    usrStr = key
                    found = 1
                    break
            if not found:
                raise ValueError, 'unknown label name for static parameter'
        return usrStr

    def findTextDynamicLabel(self, usrStr):
        """get satic texture option label from a usr string
        will raise ValueError with bad name
        need to translate name to index positions
        need to return label like dynQ0
        """
        # if not a proper parameter access key, but the natural language name
        if usrStr not in self.dynLabels:
            # try to match by parameter obj name
            usrStr = drawer.strScrub(usrStr, 'lower')
# additional processing not necessary here
            # get names of dyn pmtrs as defined in texture module
#             for key in self.dynPmtrNames: # keys here are full names
#                 if usrStr == key.lower(): # get long name
#                     usrStr = key # simply correct case errors
#                     break
#           # get parameter name key from position
            for i in range(len(self.dynPmtrManifest)):
                if usrStr.lower() == self.dynPmtrManifest[i]['name'].lower():
                    usrStr = self.dynLabels[i]
                    break
#                 raise ValueError, 'unkown label name for dynamic parameter'
        return usrStr
        

    def _updateTextPmtrInit(self):
        """initialization update for text pmtrs; to be done
        after defining self.textPmtrNames"""
        self.textPmtrNo = len(self.textPmtrNames)
        self.textLabels = basePmtr.textLabel(self.textPmtrNo)
        
    def _updateTextPmtrDefaults(self):
        """this only supplies names, which wil load defaults"""
        for i, textLabel in basePmtr.textLabel(self.textPmtrNo, 1):
            # add arg list default if missing to pmtrQdict
            if not self.pmtrQDict.has_key(textLabel):
                args = [self.textPmtrNames[i],]
                dummyObj = parameter.factory(args, 'textPmtrObjs', self.refDict)
                self.pmtrQDict[textLabel] = dummyObj.getArgs()
                
    def _updateDynPmtrInit(self):             
        """initialization update for dyn pmtrs; to be done
        after defining self.textPmtrManifest"""
        self.dynPmtrNames = []
        for dict in self.dynPmtrManifest:
            self.dynPmtrNames.append(dict['name'])
        self.dynPmtrNo = len(self.dynPmtrNames)
        self.dynLabels = basePmtr.dynLabel(self.dynPmtrNo) # get number lables

    def _updateDynPmtrDefaults(self):
        """must supply complete arguments to create dynamic parameter objects"""
        for i, dynLabel in basePmtr.dynLabel(self.dynPmtrNo, 1):
            if not self.pmtrQDict.has_key(dynLabel):
                args = self.dynPmtrManifest[i]['default']
                self.pmtrQDict[dynLabel] = args
    
    #-----------------------------------------------------------------------||--
    # tCurrent, chordCurrent, pitchRaw, multisetObj, pitchObj, pitchPost
    def stateUpdate(self, tCurrent, chordCurrent, ps, 
                         multisetObj, pitchObj, pitchPost):
        """should be called frequently from within texture module"""
        self.stateCurrentTime = tCurrent
        # data representations
        self.stateCurrentChord = chordCurrent
        if ps != None:
            self.stateCurrentPitchRaw = ps
        else: # provide a default, the first pitch
            self.stateCurrentPitchRaw = self.stateCurrentChord[0]
        # object representations
        self.stateCurrentMultiset = multisetObj # object
        if pitchObj != None:
            self.stateCurrentPitchObj = pitchObj # pitch object
        else: # provide default from multiset; we may not be on the first pitch
            self.stateCurrentPitchObj = self.stateCurrentMultiset[0]
        # pitch final includes transposition and temperament
        # may be none if transposition has not been performed
        self.stateCurrentPitchPost = pitchPost

    def stateClear(self):
        """return to none of score is completed
        clears all local variables, resets clockPath position
        always call at beginnign of texture"""
        self.stateCurrentTime = None
        self.stateSetTime = None
        # pitches, depending pitch mode (set, space)
        self.stateCurrentChord = None 
        self.stateCurrentMultiset = None # object
        self.stateCurrentPitchRaw = None # pitch space, from chord, data
        self.stateCurrentPitchObj = None # pitch object
        self.stateCurrentPitchPost = None # pitch post transposition, temperament
        self._clockReset()
    
#     def _updatePolyMode(self):
#         """always call with update Path info"""
#         if self.path.voiceType != 'part': # cant make part
#             self.polyphonyMode = 'set'
#         else:    # can make vl parts
#             self.polyphonyMode = 'part'

    def updatePathInfo(self):
        #self._updatePolyMode()
        self._clockUpdate()

    def updateTemperament(self, name): # assing particular tuning
        """ gets a new temperament object
        """
        #temperamentObj = temperament.Temperament() # generic
        name = temperament.temperamentNameParser(name) # for backward compat
        if name == None: raise ValueError, 'bad temperament name error'
        self.temperamentName = name
        self.temperamentObj = temperament.factory(self.temperamentName)

    def updateFilePaths(self, fpAudioDirs):
        """when file paths are changed by user, each texture object must have
        its file paths reset; this method provides this functionality
        """
        self.fpAudioDirs = fpAudioDirs # list of paths to samples
        #self.fpAudioAnalysisDirs = fpAudioAnalysisDirs # list of paths to analysis

    #-----------------------------------------------------------------------||--
    def getRefDict(self, t=0):
        """update dictionary with references to texture data
        passed to parameter objects with each call function
        allows pmtr obj to have access to global texture data
        may also provide a means for pmtr obj to communicate
        """
        self.refDict['stateCurrentTime'] = self.stateCurrentTime
        self.refDict['stateCurrentChord'] = self.stateCurrentChord
        self.refDict['stateCurrentPitchRaw'] = self.stateCurrentPitchRaw
        self.refDict['stateCurrentMultiset'] = self.stateCurrentMultiset
        self.refDict['stateCurrentPitchObj'] = self.stateCurrentPitchObj
        self.refDict['stateCurrentPitchPost'] = self.stateCurrentPitchPost
        self.refDict['statePathList'] = self._getPathList()
        if self.pmtrObjDict['beatT'].currentValue == None:
            bpm = self.pmtrObjDict['beatT'](t) # get init value
        else: # get current value
            bpm = self.pmtrObjDict['beatT'].currentValue
        self.refDict['bpm'] = bpm
        self.refDict['fpAudioDirs'] = self.fpAudioDirs
        #self.refDict['sadr'] = self.fpAudioAnalysisDirs
        return self.refDict

    def getRefClone(self): # get reference data for clone creation
        # note: do not store this dict
        refDict = copy.deepcopy(self.getRefDict())
        refDict['auxNo'] = self.auxNo
        refDict['auxFmt'] = self.getAuxOutputFmt()
        return refDict


    #-----------------------------------------------------------------------||--
    def load(self, pmtrQDict, pathObj=None, temperamentName='TwelveEqual', 
                pitchMode='ps', auxNo=0, fpAudioDirs=[], midiPgm=None, 
                midiCh=None, mute=0, 
                silenceMode=0, orcMapMode=1, refresh=1):
        """used for starting a texture from a pmtrQDict
        used when loading an athenaObject XML file
        
        silenceMode determies whether or not restts are calculated and stored
        if 1, all rests are calculated and stored
        """
        if pathObj == None:
            pathObj = pitchPath.PolyPath('auto-internal') # name is auto
            pathObj.autoFill([0]) # create a path with only one ptich

        self.path = pathObj # reference to the path object, not a copy
        self.pmtrObjDict = {}
        self.pmtrQDict = copy.deepcopy(pmtrQDict)
        self.pmtrObjDict['inst'] = parameter.factory(self.pmtrQDict['inst'])
        self.pmtrObjDict['tRange'] = parameter.factory(self.pmtrQDict['tRange'])
        self.pmtrObjDict['beatT'] = parameter.factory(self.pmtrQDict['beatT'])
        # this is either 'sc', 'pcs', or 'ps'
        #self.polyphonyMode = polyphonyMode
        self.temperamentName = temperamentName
        self.pitchMode = pitchMode 
        self.silenceMode = silenceMode
        self.orcMapMode = orcMapMode # on (scale) or off (absolute)
        self.auxNo = auxNo # number of auxiliary parameters

        if midiPgm == None: self.midiPgm = 0 #default, added 1.0.23
        else: self.midiPgm = midiPgm
        if midiCh == None: self.midiCh = None #default, added 1.0.23
        else: self.midiCh = midiCh
        self.mute = mute

        self.updateTemperament(self.temperamentName)
        self.fpAudioDirs = fpAudioDirs # list of paths to samples
        #self.fpAudioAnalysisDirs = fpAudioAnalysisDirs # list of paths to analysis
        # done loading data
        # create internal objects
        self.pmtrObjDict['rhythmQ'] = parameter.factory(
                          self.pmtrQDict['rhythmQ'], 'rthmPmtrObjs') 
        self.pmtrObjDict['fieldQ'] = parameter.factory(self.pmtrQDict['fieldQ'])
        self.pmtrObjDict['octQ'] = parameter.factory(self.pmtrQDict['octQ'])
        self.pmtrObjDict['ampQ'] = parameter.factory(self.pmtrQDict['ampQ'])
        self.pmtrObjDict['panQ'] = parameter.factory(self.pmtrQDict['panQ'])

        for auxLabel in basePmtr.auxLabel(self.auxNo):
            self.pmtrObjDict[auxLabel] = parameter.factory( 
                                                  self.pmtrQDict[auxLabel])
        # additional texture options can be added to a TM
        # not stored in pmtrObjDict, but data stored in pmtrQDict
        self._updateTextPmtrDefaults()
        for textLabel in self.textLabels: # load object into textPmtr object
            args = self.pmtrQDict[textLabel]
            self.pmtrObjDict[textLabel] = parameter.factory(args, 
                                                    'textPmtrObjs', self.refDict)
        # dynamic pmtr default from TM subclass; need to get type
        self._updateDynPmtrDefaults()
        for i, dynLabel in basePmtr.dynLabel(self.dynPmtrNo, 1):
            args = self.pmtrQDict[dynLabel]
            type = self.dynPmtrManifest[i]['type']
            self.pmtrObjDict[dynLabel] = parameter.factory(args, 
                                                  type, self.refDict)
            
        # do any texture wide updates that need it
        self.updatePathInfo() # updates clock
        # optionally score, to test and update timeRangeAbs; do not clear
        if refresh:
            ok = self.score()
            assert ok

    def loadDefault(self, inst=4, pathObj=None, fpAudioDirs=[], 
                            lclTimes=None, orcName='csoundNative', 
                            auxNo=None, refresh=1):
        """used to create a texture instance from default values, ie, when
        the user creates a new ti interactively
        lclRangeBeat is optional; only if textures have already been created
        derived from currently selected texture
        """
        # get a raw pmtrQ dict to load as a defaults
        # auxNo is optional argument
        auxNo, pmtrQDict = self._getInstInfo(inst, orcName, auxNo)
            
        # often defined with orc but not required
        if not pmtrQDict.has_key('ampQ'): # if missing amp
            pmtrQDict['ampQ'] = 'rb,.4,.4,.7,.9'
        if not pmtrQDict.has_key('panQ'): # if missing
            pmtrQDict['panQ'] = ('constant', .5)
        if not pmtrQDict.has_key('octQ'): # if missing
            pmtrQDict['octQ'] = ('constant', 0) # no shift
        if not pmtrQDict.has_key('fieldQ'): # if missing
            pmtrQDict['fieldQ'] = ('constant', 0)
        if not pmtrQDict.has_key('rhythmQ'): # if missing
            pmtrQDict['rhythmQ'] = 'pt,(c,4),(bg,rp,(1,1,2,3)),(c,1),(c,.75)'

        pmtrQDict['inst']     = ('staticInst', inst, orcName) # default value
        if lclTimes == None: # no local time info avail
            pmtrQDict['tRange'] = ('staticRange', (0, 20)) # default value
            pmtrQDict['beatT']  = ('c', 120) # default value
        else: # use value from selected TI
            pmtrQDict['tRange'] = lclTimes['tRange']
            pmtrQDict['beatT']  = lclTimes['beatT'] 

        # standard defaults on all new textures
        #auxNo = instInfo[inst][1] - 6 # remove default 6 pmtrs
        pitchMode = 'ps' # pitch space is default    
        #polyphonyMode  = ''    # 'set' or 'part'; auto updated
        silenceMode = 0 # default not to calculate silences
        orcMapMode = 1 # default on: scale for orc dependent values
        temperamentName = 'TwelveEqual'

        # midiPgm and get defaults based on orch name
        # these might be changed later by the user
        if orcName in ['generalMidi']:
            midiPgm = inst
            midiCh = None
        elif orcName in ['generalMidiPercussion']:
            midiPgm = 0
            midiCh = 10 # gets percussion sounds
        else: # get stnadrad default
            midiPgm = 0
            midiCh = None
            
        mute = 0
        # use main load function to load texture
        self.load(pmtrQDict, pathObj, temperamentName, 
                     pitchMode, auxNo, fpAudioDirs, midiPgm, midiCh, 
                     mute, silenceMode, orcMapMode, refresh)

    #-----------------------------------------------------------------------||--
    def copy(self, name=None):
        """return a copy of this texture"""
        #note: this seems like a circular import, but no exception is raised

        path = self.path # ref, not a copy
        pmtrQDict = copy.deepcopy(self.pmtrQDict)
        #polyphonyMode = copy.deepcopy(self.polyphonyMode)
        temperamentName = copy.deepcopy(self.temperamentName)
        pitchMode = copy.deepcopy(self.pitchMode) 
        silenceMode = copy.deepcopy(self.silenceMode) 
        orcMapMode = copy.deepcopy(self.orcMapMode) 
        auxNo = copy.deepcopy(self.auxNo) # number of auxillary parameters
        midiPgm = copy.deepcopy(self.midiPgm)
        midiCh = copy.deepcopy(self.midiCh)
        mute = copy.deepcopy(self.mute)
        fpAudioDirs = copy.deepcopy(self.fpAudioDirs)
        #fpAudioAnalysisDirs = copy.deepcopy(self.fpAudioAnalysisDirs)

        from athenaCL.libATH.libTM import texture
        if name == None: # if no name givne, use this texture's name
            name = self.name
        obj = texture.factory(self.tmName, name) 
        # use main load function to load texture
        obj.load(pmtrQDict, path, temperamentName, 
                    pitchMode, auxNo, fpAudioDirs, midiPgm, midiCh, 
                    mute, silenceMode, orcMapMode)
        return obj

    #-----------------------------------------------------------------------||--
    # get documentation
    def reprDoc(self, format=''):
        """this for a representation of a basic module
        note: this is for public use, not necessary for an object in use"""
        # update incase object has may not yet been loaded
        if self.pmtrQDict == {}:
            self._updateTextPmtrDefaults()
            self._updateDynPmtrDefaults()
        if self.pmtrObjDict == {}:
            self.updatePmtrObj() # create all objects
            
        msg = []
        if format in ['']: # format used by TIdoc command
            msg.append(self.doc)
            msg.append('\n')
            for textLabel in self.textLabels:
                msg.append('\n')
                msg.append(self.pmtrObjDict[textLabel].reprDoc())
            i = 0
            for dynLabel in self.dynLabels:
                dynDict = self.dynPmtrManifest[i] # ordered list by index
                msg.append('\n')
                msg.append(self.pmtrObjDict[dynLabel].reprDoc())
                i = i + 1
            return ''.join(msg)
        elif format == 'entryLines': # format used by TMv command
            head = ['TextureModule: ']
            head.append(self.tmName)
            head.append('; author: %s\n' % self.author)
            head.append(self.doc)
            head.append('\n')
            msg.append([self.decodePmtrName('s')[1], ''])
            for textLabel in self.textLabels:
                msg.append((self.pmtrObjDict[textLabel].type, 
                                self.pmtrObjDict[textLabel].reprDoc('paragraph')))
            msg.append([self.decodePmtrName('d')[1], ''])
            for dynDict in self.dynPmtrManifest: # list of dictionaries
                docStr = typeset.descriptionAsStr(dynDict['doc'])
                msg.append([dynDict['name'], docStr])
            return head, msg
        else:
            raise ValueError
            
    #-----------------------------------------------------------------------||--
    def _reprDocInst(self):
        """get header information for documentation of instrument"""
        entryLines = []
        if 'inst' not in self.pmtrActive: return entryLines # empty if no inst?
        attr, label = self.decodePmtrName('inst')
        entryLines.append([label, self.pmtrObjDict[attr].repr()])
        return entryLines
    
    def _reprDocAuxNames(self):
        """aux documentation is shared by both textures and clones, a is
        thus provided w/ its on method"""
        entryLines = []
        orcObj = self.getOrc() # get ref from parameter obj
        inst = self.getInst()       
        if self.auxNo == 0:
            entryLines.append([self.decodePmtrName('x')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('x')[1], ''])
            for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
                valueStr = orcObj.getInstPmtrInfo(inst, i)
                entryLines.append([(lang.TAB + 'x%i'% i), valueStr])
        return entryLines

    def _reprDocAuxArgs(self):
        """aux documentation for args"""
        entryLines = []
        if self.auxNo != 0:
            for i, auxLabel in basePmtr.auxLabel(self.auxNo, 1):
                valueStr = self.pmtrObjDict[auxLabel].reprDoc('argsMax')
                #labelStr = '%sx%i'% (lang.TAB, i)
                entryLines.append(['', valueStr])
        return entryLines

    def _reprDoc(self):
        """this for a detailed representation of a texture instance
        note: there is a reprDoc() that is not the same as this"""
        headList = []
        headList.append('TI: %s, TM: %s\n' % (self.name, self.tmName))
        # isnt header first
        entryLines = self._reprDocInst()
        # arg strings form built in parameters
        for p in ('beatT', 'rhythmQ', 'fieldQ', 'octQ', 'ampQ', 'panQ'):
            if p not in self.pmtrActive: continue
            valueStr = self.pmtrObjDict[p].reprDoc('argsMax')
            entryLines.append([self.decodePmtrName(p)[1], valueStr])
        # add inst/aux values   
        # can interleave aux info here
        auxInterleave = drawer.listInterleave(self._reprDocAuxNames(),                              
                                                         self._reprDocAuxArgs(), 1)
        entryLines = entryLines + auxInterleave  
        # get texture static parameters
        if self.textPmtrNo == 0:
            entryLines.append([self.decodePmtrName('e')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('e')[1], ''])
            for i, textLabel in basePmtr.textLabel(self.textPmtrNo, 1):
                valueStr = self.pmtrObjDict[textLabel].reprDoc('argsMax')
                entryLines.append([(lang.TAB + 's%i'% i), valueStr])
        # get texture dynamic parameters
        if self.dynPmtrNo == 0:
            entryLines.append([self.decodePmtrName('d')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('d')[1], ''])
            for i, dynLabel in basePmtr.dynLabel(self.dynPmtrNo, 1):
                valueStr = self.dynPmtrManifest[i]['doc']
                entryLines.append([(lang.TAB + 'd%i'% i), valueStr])
                valueStr = self.pmtrObjDict[dynLabel].reprDoc('argsMax')
                entryLines.append(['', valueStr])
        return headList, entryLines
        
    def _reprView(self, extData):
        """privide standard TIv display
        """
        headList = []
        headList.append('TI: %s, TM: %s, TC: %i, TT: %s\n' % (self.name, 
            self.tmName, extData['cloneNo'], self.temperamentName))
        headList.append('pitchMode: %s, ' % ( # no return 
                         self.getPitchMode()))
        headList.append('silenceMode: %s, postMapMode: %s\n' % ( 
                         typeset.boolAsStr(self.silenceMode),
                         typeset.boolAsStr(self.orcMapMode)))
                         
        headList.append('midiProgram: %s\n' % (self.getMidiPgmName()))
        tStrAbs = typeset.timeRangeAsStr(self.timeRangeAbs)
        headList.append('%s%s: %s, duration: %s\n' % (lang.TAB, lang.MUTELABEL, 
                              self._getMuteStr(), tStrAbs))
        entryLines = []

        for p in ('inst', 'tRange', 'beatT', 'rhythmQ'):
            if p not in self.pmtrActive: continue
            attr, label = self.decodePmtrName(p)
            entryLines.append([label, self.pmtrObjDict[attr].repr()])

        entryLines.append(['(p)ath', self.path.name])
        entryLines.append(['', self.path.repr('psName')])
        #entryLines.append(['', self._getPathList('string')])
        entryLines.append(['', self.clockStr()])
        
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

        if self.textPmtrNo == 0:
            entryLines.append([self.decodePmtrName('e')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('e')[1], ''])
            for i, textLabel in basePmtr.textLabel(self.textPmtrNo, 1):
                valueStr = self.pmtrObjDict[textLabel].repr()
                entryLines.append([(lang.TAB + 's%i'% i), valueStr])

        if self.dynPmtrNo == 0:
            entryLines.append([self.decodePmtrName('d')[1], 'none'])
        else:
            entryLines.append([self.decodePmtrName('d')[1], ''])
            for i, dynLabel in basePmtr.dynLabel(self.dynPmtrNo, 1):
                valueStr = self.pmtrObjDict[dynLabel].repr()
                entryLines.append([(lang.TAB + 'd%i'% i), valueStr])
                
        return headList, entryLines
  
    # string representations
    def repr(self, style=None, extData={}):
        if style == None:
            return '%s: %s' % (self.tmName, self.name)
        elif style == 'full':
            return self._reprView(extData)
        elif style == 'mute':
            return self._getMuteStr()
        elif style == 'doc':
            return self._reprDoc()
        elif style == 'docAuxNames':
            return self._reprDocAuxNames()
        elif style == 'docInst':
            return self._reprDocInst()
            
    def __str__(self):
        return self.repr()

    #-----------------------------------------------------------------------||--
    def getPitchMode(self):
        if self.pitchMode == 'ps':
            return 'pitchSpace'
        elif self.pitchMode == 'sc':
            return 'setClass'
        elif self.pitchMode == 'pcs':
            return 'pitchClass'

    def getMidiPgmName(self):
        return generalMidi.getPgmName(self.midiPgm)

    def asignMidiPgm(self):
        pass
        # try to match midi pgm by num, then by name

    #-----------------------------------------------------------------------||--

    def _getPathList(self, format='list'):
        """returns a list of pitches used based on the pitch mode
        not called directly from score() methods
        """
        pathList = []
        if self.pitchMode == 'sc':
            for scIdTuple in self.path.get('scPath'):
                # convert the sc's into pcs at 0; better way to do this...
                pathList.append(list(multiset.forteToPcs(scIdTuple)))
        elif self.pitchMode == 'pcs':
            for set in self.path.get('pcsPath'):
                pathList.append(list(set))   
        elif self.pitchMode == 'ps':
            for set in self.path.get('psPath'):
                pathList.append(list(set))
        # determine output format 
        if format == 'list':
            return pathList
        elif format == 'string': # needs to be redone w/ path obj
            msg = []
            for entry in pathList:
                msg.append('%s'  % drawer.listToStr(entry))
            return ', '.join(msg)

    def getPitchGroup(self, pos):
        """gets pitch gruop as a data structure, w/n the correct pitch mode
        pitch representation will always be psReal values, likely ints"""
        if self.pitchMode == 'sc':
            return list(multiset.forteToPcs(self.path.get('scPath')[pos]))
        elif self.pitchMode == 'pcs':
            return list(copy.copy(self.path.get('pcsPath')[pos]))    
        elif self.pitchMode == 'ps':
            return list(copy.copy(self.path.get('psPath')[pos]))

    def getMultiset(self, pos):
        """gets a copy of the multiset at a given pos"""
        return self.path.copyMultiset(pos)

    def getPathPos(self):
        """gets a list of path positions, from 0 to len-1"""
        return range(0, len(self.path))

    def getPathLen(self):
        """gets a list of path positions"""
        return len(self.path)
        
    def getPathDurationPercent(self):
        """get weightings for path sets; each weight is a proportion of e unit 
        interval"""
        return self.path.get('durPercent')



    #-----------------------------------------------------------------------||--
    # clocking methods for measuing path time points and boundaries
    # uses ClockRegion objects defined above
    
    def _clockUpdate(self):
        """load time points; must be updates if path, tRange, change
        must do once on load; always call from w/n updatePathInfo
        uses real event time points from start time given in tRange
        doest not reflect absolute duration, time including sustain
        """
        self.clockPos = 0
        tStart, tEnd = self.getTimeRange()
        durEndPoints = tEnd - tStart # duration from starts of first, last event
        sStart = copy.deepcopy(tStart) # set start
        sEnd = 0 # set end
        self.clockPath = []
        for percent in self.path.get('durPercent'):
            sEnd = sStart + (percent * durEndPoints)
            clock = ClockRegion(sStart, sEnd)
            self.clockPath.append(clock)
            sStart = sStart + clock.dur

    def _clockReset(self):
        self.clockPos = 0

    def clockForward(self):
        """advance set positon"""
        self.clockPos = self.clockPos + 1
        if self.clockPos >= self.path.len():
            self.clockPos = 0

    def clockBackward(self):
        """decrease set positon"""
        self.clockPos = self.clockPos - 1
        if self.clockPos < 0:
            self.clockPos = self.path.len() - 1

    def clockPoints(self, indexForce=None):
        """return time in seconds of this set position
        w/o args will use current clockPos in path"""
        if indexForce == None: i = self.clockPos
        else: i = indexForce
        start = self.clockPath[i].tStart
        end = self.clockPath[i].tEnd
        return (start, end) 

    def clockStr(self):
        msg = []
        for clock in self.clockPath:
            msg.append(clock.repr('dur'))
        return ', '.join(msg)

    def clockFindPos(self, t):
        """given a time value, return the path step position
        this is necessary for non-linear texture modules"""
        for i in range(len(self.clockPath)):
            if i != len(self.clockPath) - 1: # not last
                if t >= self.clockPath[i].tStart and t < self.clockPath[i].tEnd:
                    return i
            else: # last, include top
                if t >= self.clockPath[i].tStart and t <= self.clockPath[i].tEnd:
                    return i
        else: return None # error, t not in any time range of this texture              

    #-----------------------------------------------------------------------||--

    def _getInstInfo(self, inst, orcName='csoundNative', auxNo=None):
        """gets instrument info
        only used for loading from default, and updateInstPmtr
        """
        orcObj = orc.factory(orcName)
        if auxNo != None: pass
            #print _MOD, 'forcing auxNo change', auxNo
        else: # get from orchestra
            auxNo = orcObj.getInstAuxNo(inst)
        presetDict = orcObj.getInstPreset(inst, auxNo)
        return auxNo, presetDict

    def updateInstPmtr(self, inst=None, orcName='csoundNative', auxNo=None):
        """updates the parameter dict to that of a new instrument
        does not reload objects; must be done with updatePmtrObj
        used for converting/refreshing instruments
        """
        if inst == None: # assume that inst has already been set
            #inst = self.getInst() #
            inst = self.pmtrQDict['inst'][1] # get from q
            orcName = self.pmtrQDict['inst'][2]

        oldAuxNo = self.auxNo
        self.auxNo, presetDict = self._getInstInfo(inst, orcName, auxNo)         
        #print _MOD, 'oldAuxNo, self.AuxNo', oldAuxNo, self.auxNo
        
        oldPmtrDict = copy.deepcopy(self.pmtrQDict)
        # update aux no
        environment.printDebug([lang.WARN, 
            'new Texture auxiliary value %s' % self.auxNo])

        # remove old aux values 
        for auxLabel in basePmtr.auxLabel(oldAuxNo):
            del self.pmtrQDict[auxLabel]
            if auxLabel in self.pmtrObjDict.keys(): # remove objects if they exist
                del self.pmtrObjDict[auxLabel]

        # insert new aux values, from preset dict
        for auxLabel in basePmtr.auxLabel(self.auxNo):
            self.pmtrQDict[auxLabel] = copy.deepcopy(presetDict[auxLabel])

        # update inst parameter object
        self.pmtrQDict['inst'] = ('staticInst', inst, orcName) 
        if orcName in ['generalMidi']: # a gm midi orc overrides previous setting
            self.midiPgm = inst

    def _evalPmtrObj(self, pmtrName=None):
        """called for editing a single parameter object
        handle all exceptions of parameter creation
        """
        if pmtrName == 'path':
            return 0, '' # nothing to do w/ path
        args = self.pmtrQDict[pmtrName]
        if pmtrName[:5] == 'textQ': # check texture options
            try:
                self.pmtrObjDict[pmtrName] = parameter.factory(args, 
                                                  'textPmtrObjs', self.refDict)
            except error.ParameterObjectSyntaxError, msg: # initialization errors
                return 0, 'incorrect arguments: %s' % msg
        else:
            # get appropriate library
            if pmtrName == 'rhythmQ':
                lib = 'rthmPmtrObjs'
            else:
                lib = 'genPmtrObjs'
            try:
                self.pmtrObjDict[pmtrName] = parameter.factory(args, lib)
            except error.ParameterObjectSyntaxError, msg: # initialization errors
                return 0, 'incorrect arguments: %s' % msg
        # check for errors
        if self.pmtrObjDict[pmtrName] == None: # failure to match object type
            return 0, 'there is no ParameterObject with that name.'
        # check for proper types
        if pmtrName == 'rhythmQ': # check that its the right type of pmtr obj
            if self.pmtrObjDict[pmtrName].parent != 'rhythm':
                return 0, 'only a rhythm ParameterObject can be used here.'
        elif pmtrName[:5] == 'textQ':
            if self.pmtrObjDict[pmtrName].parent != 'textureStatic':
                return 0, 'only a texture ParameterObject can be used here.'
        else:
            if self.pmtrObjDict[pmtrName].parent != 'parameter':
                return 0, 'only a generator ParameterObject can be used here.'
        # everything good, check args
        ok, msg = self.pmtrObjDict[pmtrName].checkArgs()
        return ok, msg

    def updatePmtrObj(self, pmtrName=''):
        """if no pmtr given, reinitializes complete pmtr object
        if pmtr given, reinits just that pmtr
        when called during edit of a texture, self.pmtrQDict has been replaced
        with the new values. if edit returns an error message, self.pmtrQDict 
        is replaced with the original
        """
        # this cand destroy the pmtrQDict
        assert pmtrName != 'pmtrQDict'
        if pmtrName == 'inst':
            self.updateInstPmtr() # inst already set in pmtrQDict
            pmtrName = '' # force reinit of all parameters
        if pmtrName == 'path':
            ok = 1
            msg = ''
        elif pmtrName != '':
            ok, msg = self._evalPmtrObj(pmtrName)
        else: # reinit all paramters, no name given
            for pmtrName in self.pmtrQDict.keys():
                ok, msg = self._evalPmtrObj(pmtrName)
                if ok != 1: break # stop processing on error
        # post update actions
        if pmtrName in ['tRange',]: # path should be here but its not a pmtr obj
            self._clockUpdate()
        elif pmtrName == 'path':
            self.updatePathInfo()
        return ok, msg

    def _editRestore(self, attrName, pmtrName, data):
        setattr(self, attrName, data)
        ok, msg = self.updatePmtrObj(pmtrName)
        # this should never fail
        if not ok: raise ValueError, 'texture edit: original data cannot be restored: %s' % msg

    def editPmtrObj(self, pmtrName, pmtrValue, refresh=1):
        """Edits a Texture's Parameter object

        The `refresh` parameter determines if eventlists are refreshed after each run.

        not clearing the score will allow faster clone values
        self.clearScore() # this is for data efficiency; vals are updated
        """
        p = pmtrName
        newData = pmtrValue
        if (p in self.pmtrCommon and p not in self.pmtrActive):
            return None, 'no %s parameter in TI %s.' % (p, self.name)
        if p == 'path': # path is an object reference, not a string
            attrName = 'path'
            oldData = self.path
            newData = pmtrValue
        elif (p in ('ampQ', 'panQ', 'fieldQ', 'octQ', 'beatT', 'tRange', 'inst',
            'rhythmQ') or p[:4] in ['auxQ', 'dynQ'] or p[:5]=='textQ'):
            if p[:4] == 'auxQ':
                if p not in basePmtr.auxLabel(self.auxNo):
                    return 0, 'no such auxiliary label'
            if p[:5] == 'textQ':
                if p not in basePmtr.textLabel(self.textPmtrNo):
                    return 0, 'no such texture static label'
            if p[:4] == 'dynQ':
                if p not in basePmtr.dynLabel(self.dynPmtrNo):
                    return 0, 'no such texture dynamic label'
            attrName = 'pmtrQDict'
            oldData = self.pmtrQDict # attrReference
            newData = copy.deepcopy(self.pmtrQDict)  # copy old dict
            # if we have a parameter object, we need to store a string
            # representation here
            if isinstance(pmtrValue, basePmtr.Parameter):
                environment.printDebug(['editPmtrObj():', 'storing string representation', repr(str(pmtrValue))])
                newData[p] = str(pmtrValue)
            else:
                newData[p] = pmtrValue
        else:
            return 0, 'incorrect parameter label access.'
        # set attribute
        setattr(self, attrName, newData)

        try: # try to refresh objects
            editPhase = 'object creation:'
            # TODO: here is where we need to pass a reference to the 
            # object, and not create new object
            ok, msg = self.updatePmtrObj(p)
            if not ok:
                self._editRestore(attrName, p, oldData)
                return ok, msg
            if refresh:
                editPhase = 'score creation:'
                ok = self.score()
                if not ok:
                    self._editRestore(attrName, p, oldData)
                    return ok, 'score creation returned an error.'
        except error.ParameterObjectSyntaxError, msg: # standard init errors from pmtr obj
            msg = '%s %s' % (editPhase, msg)
            ok = 0
        except IndexError, msg:
            msg = '%s incorrect number of arguments. %s.' % (editPhase, msg)
            ok = 0
        except TypeError, msg:
            msg = '%s incorrect data-type in arguments. %s' % (editPhase, msg)
            ok = 0 
        except UnboundLocalError, msg:
            msg = '%s incorrect paramater type in arguments. %s' % (editPhase, msg)
            ok = 0
        except ValueError, msg:
            msg = '%s value error: an inappropriate data type used.' % editPhase
            ok = 0
        except ZeroDivisionError:
            msg = '%s zero division error: zero cannot be a divisor.' % editPhase
            ok = 0
        if not ok:
            self._editRestore(attrName, p, oldData)
            return ok, msg
        # post edit update to other ojbects
        if attrName == 'path': # decrement references for this path
            #self.ao.textureLib[tName].path.refDecr()
            oldData.refDecr()
            newData.refIncr()
        return 1, '' # success

    #-----------------------------------------------------------------------||--
    # minor edit methods
    
    def editName(self, name):
        self.name = name

    #-----------------------------------------------------------------------||--
    # methods used within texture module to get a value;
    # provides only minor data filtering at the event instance level

    def getTimeRange(self):
        """this is not the real time range, but the time of the 
        first and last event"""
        return self.pmtrObjDict['tRange']() # returns tStart, tEnd

    def getInst(self, tCurrent=None):
        """instrument is usually a constant
        returns a number"""
        return self.pmtrObjDict['inst']()
                
    def getInstOrcName(self, tCurrent=None):
        return self.pmtrObjDict['inst'].orcName

    def getOrc(self, tCurrent=None):
        """get a reference to an orchestra object"""
        return self.pmtrObjDict['inst'].orcObj
    
    def getField(self, tCurrent):
        """called during score excution. returns value at 
        current texture time"""
        trans = self.pmtrObjDict['fieldQ'](tCurrent, self.getRefDict())
        return trans

    def getOct(self, tCurrent):
        """called during score excution. returns value at 
        current texture time; always rounds to an int"""
        oct = int(round(self.pmtrObjDict['octQ'](tCurrent, self.getRefDict())))
        return oct

    def getPan(self, tCurrent):
        """called during score excution. returns value at 
        current texture time; 
        now in orc mix processing: mod 1 perfoermd on all pan values"""
        pan = self.pmtrObjDict['panQ'](tCurrent, self.getRefDict())
        # removed post 1.3 
        #if pan < 0 or pan > 1:
        #    pan = pan % 1.0
        return pan

    def getAmp(self, tCurrent):
        """called during score excution. returns value at 
        current texture time; vales may be scaled by orc"""
        amp = self.pmtrObjDict['ampQ'](tCurrent, self.getRefDict())
        return amp

    def _getBpm(self, tCurrent):
        """calculate a new bpm value
        note: this method is private b/c it should only be accessed
        by the getRhthm method"""
        bpm = self.pmtrObjDict['beatT'](tCurrent, self.getRefDict())
        return bpm

    def getRhythm(self, tCurrent):
        """called during score excution. returns value at 
        current texture time
        dur = total time of abs rhythm
        sus = total time of note sustained, > or <
        tOverlap = sus-dur, time difference between two
        return pulse, bpm for storage
        """
        # NOTE: it _is_ necessary to call bpm here, is the texture
        # does not call bpm values on its one; bpm is only called from a 
        # Texture through the _getBpm method
        bpm = self._getBpm(tCurrent)
        # update bpm first, called each time a rhythm is called
        dur, sus, acc = self.pmtrObjDict['rhythmQ'](tCurrent, self.getRefDict())
        # get pulse as a string
        pulse = str(self.pmtrObjDict['rhythmQ'].currentPulse)
        return bpm, pulse, dur, sus, acc
        
    def getAux(self, tCurrent):
        """called during score excution. returns value at 
        current texture time for all auxillaries
        no avail pmtr object list b/c aux's are determined by
        csound instrument
        """
        auxiliary  = []
        for auxLabel in basePmtr.auxLabel(self.auxNo):
            auxValue = self.pmtrObjDict[auxLabel](tCurrent, self.getRefDict())
            auxiliary.append(auxValue)
        return auxiliary

    def getAuxOutputFmt(self):
        """return a list of output formats of for all aixilliary paramters
        required by clones at initiazation and instrument changing
        output format may be a list of options"""
        auxiliary  = []
        for auxLabel in basePmtr.auxLabel(self.auxNo):
            auxiliary.append(self.pmtrObjDict[auxLabel].outputFmt)
        return auxiliary

    #-----------------------------------------------------------------------||--
    # get text pmtr data

    def getTextStatic(self, label, data=None):
        """get data from text static parameters
        lable is the name or number; data is the name of the argument
        ValueErrors are handled by caller"""
        label = self.findTextStaticLabel(label) # may raise ValueError
        if data != None:
            return self.pmtrObjDict[label](data)
        else: # return complete arg list
            return self.pmtrObjDict[label].getArgs()

    def getTextStaticName(self, label):
        """ValueErrors are handled by caller"""
        label = self.findTextStaticLabel(label) # may raise ValueError
        return self.pmtrObjDict[label].type

    def getTextStaticArgsLabel(self, label):
        """ValueErrors are handled by caller"""
        label = self.findTextStaticLabel(label) # may raise ValueError
        return self.pmtrObjDict[label].getArgsLabel()

    #-----------------------------------------------------------------------||--
    # get dyn pmtr data
    
    def getTextDynamic(self, label, tCurrent):
        """ValueErrors for bad label are handled by caller
        label is name defined in self.dynpmtrmanifest"""
        label = self.findTextDynamicLabel(label)
        return self.pmtrObjDict[label](tCurrent, self.getRefDict())
        
    def getTextDynamicArgsLabel(self, label):
        """ValueErrors for bad label are handled by caller"""
        label = self.findTextDynamicLabel(label)
        return self.pmtrObjDict[label].getArgsLabel()
        
      
    #-----------------------------------------------------------------------||--
    # event processing methods

    def _sortPmtrObjPriority(self):
        """sort pmtr obj by priority, with highest _last_
        checking for postEvent method is not done
        this is done each time event is run, so pmtr obj can have dyn priority
        """
        nameSort = []
        nameList = []
        highest = 0
        for name in self.pmtrObjDict.keys():
            pri = self.pmtrObjDict[name].priority
            if pri < 0: # turns off post event processing
                continue
            nameSort.append((pri, name))
        nameSort.sort()
        for entry in nameSort:
            pri, name = entry
            nameList.append(name)
        return nameList

    def _makeEventComment(self, strMsg=None):
        "make a comment as a tuple as the first element in a list"
        msg = [self.stateCurrentPitchRaw, ]
        if strMsg != None:
            msg.append(strMsg)
        return msg

    def makeEvent(self, tCurrent, bpm, pulse, dur, sus, acc, 
                            amp, ps, pan, auxiliary, comment=None):
        """ps is a psReal pitch value"""
        eventDict = {}
        eventDict['inst'] = self.getInst()
        eventDict['time'] = tCurrent # start time
        eventDict['bpm'] = bpm # store bpm at this moment for ref
        eventDict['pulse'] = pulse # store str pulse for ref
        eventDict['dur'] = dur
        eventDict['sus'] = sus
        eventDict['acc'] = acc
        eventDict['amp'] = amp
        eventDict['ps'] = ps
        eventDict['pan'] = pan
        eventDict['aux'] = auxiliary # a list
        eventDict['comment'] = self._makeEventComment(comment)
        return eventDict

    def storeEvent(self, eventDict):
        """for writting a single event, one at a time
        all TM call this method to add an event to a score
        do postEvent processign for each event after sorting priority
        """
        # do post processing
        attrSort = self._sortPmtrObjPriority()
        refDict = self.getRefDict() # get once, as all at same time
        for name in attrSort: # call method in each obj from low to high priority
            eventDict = self.pmtrObjDict[name].postEvent(eventDict, refDict)
        self.esObj.append(eventDict)

    def _mergeEventDict(self, parent, child):
        for key in parent.keys():
            if not child.has_key(key): # if child does not have value, copy
                child[key] = copy.deepcopy(parent[key])
        return child

    def storePolyEvent(self, parentEventDict, subEventArray, comment=None):
        """for writting multiple events all with the same aux and comment
        subEventArray is a list of event dictionaries
        strips aux from parent, adds to partial, writes to score
        uses storeEvent
        """
        parentComment = self._makeEventComment(comment)
        for eventDict in subEventArray:
            eventDict = self._mergeEventDict(parentEventDict, eventDict)
            # override parent comment with one provided from args
            eventDict['comment'] = self._makeEventComment(comment)
            self.storeEvent(eventDict)

    def interpolate(self, tFrameArray, snapSus, active):
        """perform interpolation on all events based on the specification
        given in the tFrameArray"""
        self.esObj.interpolate(tFrameArray, snapSus, active)


    #-----------------------------------------------------------------------||--
    # score mehods: generting and returning event data

    def checkScore(self):
        "need to check if note event have been created (can be all rests)"
        if len(self.esObj) == 0: return 0
        else: return 1

    def _scorePre(self): # called w/n score method
        self.stateClear() # resets
        self.esObj.clear() # clear event sequence
        for pmtrName in self.pmtrQDict.keys():
            if pmtrName[:5] != 'textQ': #dont update texture options
                # reset all necessary variables before scoring
                # do update dyn parameters
                self.pmtrObjDict[pmtrName].reset() 
        self.esObj.updatePre()

    def _scoreMain(self):
        pass # main scoring method to be overriddne in TM

    def _scorePost(self): # called w/n score method
        """do post esObj, clear state
        update timeRangeAbs"""
        self.esObj.updatePost()
        self.stateClear() # resets
        # absolute, calculated time range
        self.timeRangeAbs = self.esObj.getTimeRangeAbs() 

    def score(self): # main method called for scoring
        '''
        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('lg')
        >>> ti.loadDefault()
        >>> ti.score()
        1
        '''
        self._scorePre()
        ok = self._scoreMain()
        self._scorePost()
        return ok
        
    def getScore(self):
        """always returna copy of current esObj
        this copy may be manipulated elsewhere, and thus must be unique"""
        return self.esObj.copy() # return copy of object

    def clearScore(self):
        #print _MOD, 'clearing score'
        self.esObj.clear() # clear event sequence

    def scoreTest(self, p, dur=10):
        """test the score by calling score() w/ a shorter time range
        must store current pmtr obj settings, then edit, and then restore
        p is name of parameter; if time range, do a complete run
        not yet used

        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('lg')
        >>> ti.loadDefault()
        >>> ti.scoreTest('tRange')
        1
        """
        if p == 'tRange':
            environment.printDebug(['scoreTest() get tRange parameter'])
        #tRangeAbsSrc = copy.copy(self.timeRangeAbs)
        # dont change pmtrQDict, just pmtrObjDict
        tRangeSrc = self.pmtrObjDict['tRange']        
        tRangeTemp =  parameter.factory(('staticRange', (0, dur)) )
        self.pmtrObjDict['tRange'] = tRangeTemp
        #try:
        ok = self.score()
        #except: # catch all errors?
        #    ok = 0
        # restore previous obj
        self.pmtrObjDict['tRange'] = tRangeSrc
        return ok


        
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
