#-----------------------------------------------------------------||||||||||||--
# Name:          pitchPath.py
# Purpose:       defines path object.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import copy
from athenaCL.libATH import SC
from athenaCL.libATH import MC
from athenaCL.libATH import pitchTools
from athenaCL.libATH import drawer

_MOD = 'pitchPath'

class PolyPath:
    def __init__(self, name='test', scObj=None, mcObj=None):
        self.name = name
        # if not given create
        if scObj == None: self.scObj = SC.SetClass()
        else: self.scObj = scObj
        if mcObj == None: self.mcObj = MC.MapClass()
        else: self.mcObj = mcObj

        self.voiceType = 'none'
        # voice types:
        # 'none' the size of any pcs is > 6
        # 'map' has at least one set of maps, all sixes == or < 6
        # 'part' has at least one set of maps, all sixes are == (vlparts 
        # extractiable)

        # a global pitch referecne for a path object
        # not yet implemented, may not be in the future
        self.ambitus = 0      
        self.multisetPath = []   # hold Multiset objects
        # each form is list of cold data, length always the same
        # sc and scPath are the same; field is no longer used
        self.forms = ('psPath','pcsPath','scPath', 'sc', 'field',
                          'durFraction', 'durPercent')
        # attributes that are stored as lists
        # durFraction = list of int/float values that are treated as dur weights

        # attriubtes that are dynamic
        self.durSum = None # must be calculated after creation
        self.refCount = 0       # keeps track of how many TIs are using this 
                                            # Path. cannot delete until this is == to 0

        # src, dst are index values
        # voiceLib['maps'] dictionary is a dictionary with 
        # (src, dst) : mapTupleID
        # voiceLib['ranks'] dictionary holds
        # (src, dst) : (SMTHrank, UNIFrank, BALrank)      
        self.voiceLib    = {'auto' : {'maps': {},   
                                                'ranks': {}   },
                                 } 
        #all are only valid for the current selection of maps
        # note: event paths with voiceType of 'none' have 'auto' defined

        # each dictionary has a list for each map in this group
        # lists are sorted complete map IDs for the named analysis
        # the format of the dictionary is  
        # (source, dest) : [ordered map ids by analysis]

        # this stores the rankings for each measure for each map
        # thus rankings are calculated once, and dont need to be recalculated
        # unless the set changes

        self.voiceRank = { 'SMTH': {},  
                                'UNIF': {},  
                                'BAL': {}
                             }
        self.activeVoice = 'auto'



    #------------------------------------------------------------------------||--
    #data modifucation an editting

    def insert(self, multiSet, i=None):
        """inserts one vertical position to path at given index number
        does updates, for the situation that you make one change
        """
        if i == None: #append to end
            self.multisetPath.append(multiSet)
        else:
            self.multisetPath[i] = multiSet
        self._updateMultisetChange() 

    def __setitem__(self, key, value):
        self.multisetPath[key] = value
        self._updateMultisetChange() 

    def __contains__(self, item):
        """item to test is a set obj"""
        if item in self.multisetPath:
            return 1
        else:
            return 0

    def __delitem__(self, key):
        # key is in the order position
        del self.multisetPath[key]
        self._updateMultisetChange()

    def __getitem__(self, key):
        return self.multisetPath[key]

    #------------------------------------------------------------------------||--
    # do these edits in place


    def retro(self):
        self.multisetPath.reverse()
        self._voiceRetro() # reverse the amps
        self._updateMultisetChange() # updates all map sorts, group ranks

    def slice(self, slRange):
        """index positions are proper for list slicing"""
        start, end = slRange
        assert start >= 0 and start < self.len()
        assert end >= 0 and end <= self.len()
        self.multisetPath = self.multisetPath[start:end]
        self._voiceSlice(slRange) # reverse the amps
        self._updateMultisetChange() # updates all map sorts, group ranks
    
    def rotate(self, newZero):
        """newZero is corrected list index value of new 0 position
        ie, value between 1 and self.len-1
        """
        # see rotate in Multiset for an improved rotation algorithm
        assert newZero >= 1 and newZero < self.len()
        self.multisetPath = (self.multisetPath[newZero:self.len()] + 
                                    self.multisetPath[0:newZero])
        self._voiceReinit() # erases all maps, sorts: should be replaced w/ rot met
        self._updateNew() # updates all map sorts, group ranks

    def optimize(self, opt='o'):
        """optimize the path in place
        opt can be o for optimize, a for antioptimze"""
        pass # not yet implemented

    def t(self, value, key=None):
        """if key == None, all sets are are transposed"""
        if key == None: # if none, do all
            indexList = range(0,self.len())
        else:
            indexList = []
            indexList.append(key)
        for i in indexList: # get each set
            self.multisetPath[i].t(value)
        self._updateMultisetChange()

    def i(self, key=None):
        """if key == None, all sets are are inverted"""
        if key == None: # if none, do all
            indexList = range(0,self.len())
        else:
            indexList = []
            indexList.append(key)
        for i in indexList: # get each set
            self.multisetPath[i].i()
        self._updateMultisetChange()

    #------------------------------------------------------------------------||--
    # display methods

    def _pssToNoteName(self, set):
        strSet = ''
        for psInt in set:
            nameStr = pitchTools.psToNoteName(psInt)
            strSet = strSet + nameStr + ','
        return strSet[0:-1] # remove last comma

    def _reprListData(self, listData, outer=0):
        msgList = []
        for data in listData:
            if not drawer.isStr(data):
                msgList.append(str(data))
            else:
                msgList.append(data)
        msg = ','.join(msgList) # should be a list of strings
        if outer:
            return '(%s)' % msg
        else:
            return msg


    def reprList(self, type):
        """represet path as various forms of data
        return a list if strings
        """
        if self.len() == 0:
            return 'empty PolyPath'
        strList = []
        if type == 'dur': # returns a list
            i = 0
            for part in self._access('durFraction'):
                pcntValue = int(round((self.get('durPercent')[i]*100)))
                msg = ('%s(%s' % (part, pcntValue)) + '%)'
                strList.append(msg)
                i = i + 1
        elif type == 'psPath' or type == 'psPath': # returns a list
            for set in self.multisetPath:
                strList.append(set.repr('psReal', 0))
        elif type == 'pcsPath': # returns a list
            for set in self.multisetPath:
                strList.append(set.repr('pc', 0))
        elif type == 'psName': # returns a list
            for set in self.multisetPath:
                strList.append(set.repr('psName', 0))
        elif type == 'scPath' or type == 'sc': # sc name list
            for set in self.multisetPath:
                strList.append(set.repr('sc', 0))
        return strList

    def repr(self, type, data=None):
        """represet path as various forms of data
        return a single string
        """
        if self.len() == 0:
            return 'empty PolyPath'
        strList = []

        if type == 'dur': # returns a list
            i = 0
            for part in self._access('durFraction'):
                pcntValue = int(round((self.get('durPercent')[i]*100)))
                msg = ('%s(%s' % (part, pcntValue)) + '%)'
                strList.append(msg)
                i = i + 1
            return strList
        elif type == 'psName': # returns a list
            for set in self.multisetPath:
                strList.append(set.repr('psName', 1))
            return self._reprListData(strList)
        elif type == 'psReal': # returns a list
            for set in self.multisetPath:
                strList.append(set.repr('psReal', 1))
            return self._reprListData(strList)
        elif type == 'scPath' or type == 'sc': # sc name list
            for set in self.multisetPath:
                strList.append(set.repr('sc', 1))
            return self._reprListData(strList)

    def __str__(self):
        return self.repr('scPath')


    #------------------------------------------------------------------------||--
    # semi auto loaders      
    def loadPsList(self, pcsList):
        """adds pcs from a list of pc's, not as a complex set of data"""
        self.multisetPath = [] # clear
        for entry in pcsList:
            pcSet = tuple(entry)
            self.multisetPath.append(SC.Multiset(pcSet))
        self._updateNew()

    def loadMultisetList(self, objList):
        self.multisetPath = [] # clear
        """load a path as a list of multiset objects"""
        for pitch in objList:
            self.multisetPath.append(pitch)
        self._updateNew()

    #------------------------------------------------------------------------||--
    def loadDataModel(self, pathData):
        """load data stored in an athenaCL xml file"""
        p = pathData
        # init path, sets cur path voice to auto, inits vars
        if p['activeVoice']: 
            self.activeVoice = copy.deepcopy(p['activeVoice'])
        if p['ambitus']: 
            self.ambitus = copy.deepcopy(p['ambitus'])
        # load pitch data
        if p['psPath'] == None: #pre1.0path
            for set in p['scPath']: # must have a set path
                self.multisetPath.append(SC.Multiset(None, set, self.scObj))
        else: # use all data
            psPath = copy.deepcopy(p['psPath'])
            pcsPath = copy.deepcopy(p['pcsPath'])
            scPath = copy.deepcopy(p['scPath'])
            field = copy.deepcopy(p['field'])
            # dur fractions added for 1.0.21 
            # if exists, replace: will be updated otherwise
            if p.has_key('durFraction'): 
                durFraction = copy.deepcopy(p['durFraction'])
            i = 0
            for set in psPath:
                setObj = SC.Multiset(psPath[i], scPath[i], self.scObj)
                setObj.setT(field[i])
                if p.has_key('durFraction'): 
                    setObj.setDur(durFraction[i])
                self.multisetPath.append(setObj)
                i = i + 1
 
        # updates dur fraction and percent values
        self._updateDurSum() 
        # udpate voiceType for each path
        self._updatePathSizeType() # this may over-ride a forceNoVL
        if self.voiceType != 'none': # only after assigning self.PathType!
            if not p.has_key('voiceLib'): # occasional error from bad obj
                provideAuto = 1
            elif len(p['voiceLib'].keys()) == 0:# create auto group
                provideAuto = 1
            else: provideAuto = 0 # no auto necessary.
            if provideAuto:
                self.voiceAutoFill('auto')
                self.voiceFillRank()
                self.voiceUpdateMapRank('auto')
            else: # load old pvs
                if p.has_key('voiceRank'):
                    pvRanksUpdate = 'false'
                    data = copy.deepcopy(p['voiceRank']['SMTH'])
                    self.voiceRank['SMTH'] = data
                    data = copy.deepcopy(p['voiceRank']['BAL'])
                    self.voiceRank['BAL'] = data 
                    data = copy.deepcopy(p['voiceRank']['UNIF'])
                    self.voiceRank['UNIF'] = data 
                else: # for all pre 1.0.16 athena objects
                    pvRanksUpdate = 'true'
                    self.voiceFillRank()
                for pvName in p['voiceLib'].keys():# create group
                    self.voiceLib[pvName] = {} 
                    data = copy.deepcopy(p['voiceLib'][pvName]['maps'])
                    self.voiceLib[pvName]['maps']=data
                    if pvRanksUpdate == 'false':
                        data = copy.deepcopy(p['voiceLib'][pvName]['ranks'])
                        self.voiceLib[pvName]['ranks'] = data
                    else: # recalculate
                        self.voiceUpdateMapRank(pvName)

    def writeDataModel(self):
        """write data in format a dict to store in xml file"""
        p = {}
        p['activeVoice'] = self.activeVoice # was CurrentPathVoiceXXX
        p['ambitus'] = self.ambitus
        p['psPath'] = self.get('psPath')
        p['pcsPath'] = self.get('pcsPath')
        p['scPath'] = self.get('scPath')
        p['field'] = self.get('field')
        p['durFraction'] = self.get('durFraction')
        if self.voiceType != 'none': # with voices
            p['voiceRank'] = {}
            p['voiceRank']['SMTH'] = self.voiceRank['SMTH']
            p['voiceRank']['BAL'] = self.voiceRank['BAL']
            p['voiceRank']['UNIF'] = self.voiceRank['UNIF']
            p['voiceLib'] = {}
            for pvName in self.voiceLib.keys():
                p['voiceLib'][pvName] = {}
                data = self.voiceLib[pvName]['maps']
                p['voiceLib'][pvName]['maps'] = data
                data = self.voiceLib[pvName]['ranks']
                p['voiceLib'][pvName]['ranks'] = data
        return copy.deepcopy(p) # return a copy


    #------------------------------------------------------------------------||--
    def copy(self, name):
        """output a copy of this object, as new object"""
        pathObj = PolyPath(name, self.scObj)
        # this may not be the best method as it runs update init methods
        newDurPath = []
        for set in self.multisetPath:
            pathObj.multisetPath.append(set.copy())
        pathObj.voiceLib = copy.deepcopy(self.voiceLib)
        pathObj.voiceRank = copy.deepcopy(self.voiceRank)
        pathObj.activeVoice = copy.deepcopy(self.activeVoice)
        pathObj.durSum = copy.deepcopy(self.durSum)
        pathObj.ambitus = copy.deepcopy(self.ambitus)
        return pathObj

    def copyMultiset(self, pos):
        """get a copy of the multiset obj"""
        return self.multisetPath[pos].copy()

    def autoFill(self, psList=(0,)):
        """auto generate a new path values for use as an auto path
        can supply a list of psReal values
        """
        self.loadPsList([psList,] ) # does updates an inits

    #------------------------------------------------------------------------||--

    def len(self):
        return len(self.multisetPath)

    def __len__(self):
        return self.len()

    def _access(self, form):
        """return data as list"""
        dataList = []
        # append sets w/ the appropriate data
        for set in self.multisetPath:
            if form == 'psPath':
                dataList.append(set.get('psReal'))
            elif form == 'pcsPath':
                dataList.append(set.get('pc'))
            elif form == 'scPath' or form == 'sc':
                dataList.append(set.get('sc'))
            elif form == 'field': # actual attribute
                dataList.append(set.tRef) 
            elif form == 'durFraction': # raw dur values per Multiset
                dataList.append(set.dur)
            elif form == 'durPercent': # unit interval proportions
                dataList.append(self._durPercent(set.dur))
            else:
                raise AttributeError
        return dataList

        
    def get(self, name):
        if name not in self.forms:
            raise ValueError, 'bad format name: %s' % name
        return self._access(name)

    #------------------------------------------------------------------------||--
    # semi public update methods; use these as much as possible
    def _updateNew(self, forceNoVL=0):
        "all updates when a new path is created"
        self._updateDurSum()
        self._updatePathSizeType(forceNoVL)
        self._updateVoiceRank('auto') # updates all, adds auto

    def _updateMultisetChange(self, forceNoVL=0):
        " all updates necessary when a multiset has changed"
        self._updateDurSum() # dur values may have changed
        self._updatePathSizeType(forceNoVL)
        self._updateVoiceRank() # updates all groups

    #------------------------------------------------------------------------||--
    # low level updates
    def _updateDurSum(self):
        """ this updates durSum durPrecent with a whatever values are
             in durFraction """
        self.durSum = 0
        for part in self._access('durFraction'):
            if part <= 0: return None # error
            self.durSum = self.durSum + part

    def _durPercent(self, dur):
        """given a dur, calculate percent of total"""
        return float(dur) / self.durSum

    def loadDur(self, durList):
        """this loads a dur fraction for entire path
        enter as a list of dirs
        """
        if len(durList) != self.len():
            raise ValueError
        i = 0
        for part in durList:
            if part <= 0:
                raise ValueError
            self.multisetPath[i].setDur(part)
            i = i + 1
        self._updateDurSum() # updates all relavent values

    #------------------------------------------------------------------------||--
    # reference counting for use w/ textures

    def refIncr(self):
        "adds one to references"
        self.refCount = self.refCount + 1

    def refDecr(self):
        "removes one from references"
        self.refCount = self.refCount - 1
        if self.refCount < 0:
            self.refCount = 0


    #------------------------------------------------------------------------||--
    # map and voice utility functions

    def voiceNames(self):
        """return a list of voice names; if voiceType is none, return
        an empty list"""
        if self.voiceType == 'none': return [] 
        # get voiceLib keys
        foundKeys = self.voiceLib.keys()
        foundKeys.sort()
        return foundKeys

    def mapKeysFromVoice(self, name='auto'):
        """returns all position keys, like (0,1) from a group"""
        assert name in self.voiceNames()
        foundKeys = self.voiceLib[name]['maps'].keys()
        foundKeys.sort() # sorting puts in order from low to highs
        return foundKeys


    def voiceMapGet(self, group, key):
        """return the map id for given groyp and position key"""
        return self.voiceLib[group]['maps'][key]

    def voiceRepr(self, name='auto'):
        if name in self.voiceNames():
            foundKeys = self.voiceLib[name]['maps'].keys()
            foundKeys.sort()
            mapStringList = []
            for key in foundKeys:
                mapStringList.append(self.mcObj.mapIdTupleToString(
                                            self.voiceLib[name]['maps'][key]))
            return ','.join(mapStringList)
        else:
            raise ValueError

    def voiceMapAdd(self, name, (srcPos, destPos), mapTupleId):
        if name in self.voiceNames():
            self.voiceLib[name]['maps'][(srcPos, destPos)] = mapTupleId
        else:
            self.voiceLib[name] = {}        # great new group first
            self.voiceLib[name]['maps'] = {} 
            # creat 'map' group to enter mpas in
            self.voiceLib[name]['maps'][(srcPos, destPos)] = mapTupleId

    def voiceMapDelete(self, name, (srcPos, destPos)):
        if name in self.voiceNames():
            del self.voiceLib[name]['maps'][(srcPos, destPos)]
        else:
            raise ValueError

    def voiceDelete(self, name):
        """delete an entire group"""
        del self.voiceLib[name]

    def _voiceReinit(self):
        """clear all groups, maps, and sorts"""
        self.voiceLib = {'auto' : {'maps':  {},  
                                            'ranks': {}},
                              } 
        self.voiceRank = {'SMTH': {}, 'UNIF': {}, 'BAL': {} }
        self.activeVoice = 'auto'

    #------------------------------------------------------------------------||--
    # utility functions

    def _updateVoiceRank(self, group='all'):
        """master public update function for map routines
        updates voiceType, maps if necessart
        only use when creating a new path, or when path has changed
        """
        if self.voiceType != 'none':
            groupList = []
            if group == 'all': # update all
                groupList = self.voiceNames()
                # special case (after a path slice) where we dont know if we need to
                # update all, or rather just fill an auto
                if len(groupList) == 1 and groupList[0] == 'auto':
                    group = 'auto'
            else:
                groupList.append(group)
            # only do this after checking and assigning self.PathType!
            if group == 'auto':
                # when a new path is created, a 'auto' pv group is added 
                #automatically
                self.voiceAutoFill(group)    
            # only need when path changes, done once per group
            self.voiceFillRank()
            for group in groupList:
                self.voiceUpdateMapRank(group)

    def _updatePathSizeType(self, forceNoVL=0):
        """checks the size of each path and determines which of three size types 
          is current; can optionally force none for efficiency"""
        uniformGroup = []
        end = 0
        for entry in self.get('pcsPath'):
            size = len(entry)
            uniformGroup.append(size)
            if size > 6:
                self.voiceType = 'none'  # can only do vls with 6 or fewer voices
                end = 1
                break
        # if length less than 1, or forceNoVL
        if self.len() <= 1 or forceNoVL:
            self.voiceType = 'none'
            end = 1
        if end != 1: # none greater than 6, no force, length greater than 1
            # if len of group is == number of contents, all are the same size
            if len(uniformGroup) == uniformGroup.count(uniformGroup[0]):  
                # if all the same size, vl parts can be extracted
                self.voiceType = 'part'  
            else:
                self.voiceType = 'map'


    def voiceAutoFill(self, groupName='auto'):
        """ automatically adds parallel maps to a given group
        used for creating an 'auto' map, using the first (simplest) voice 
        leadings available
        """
        positionRange = range(0, self.len())
        for i in positionRange:
            if (i+1) == self.len():
                break
            srcPos = i
            dstPos = i + 1
            srcSize = len(self.multisetPath[srcPos])
            dstSize = len(self.multisetPath[dstPos])
            # supply the first map of the needed size
            # individual map indexes start with 1, not 0;
            mapTupleId = (srcSize, dstSize, 1)  # simplest is always the first
            self.voiceMapAdd(groupName, (srcPos, dstPos), mapTupleId)  

    def _voiceExpandIdList(self, listOfPartialIds, srcSize, dstSize):
        """take a list of partial ids that all have the same src, dst
        convert them into complete ids that have three values
        """
        convertedList = []
        for i in range(0, len(listOfPartialIds)):
            convertedList.append((srcSize, dstSize, listOfPartialIds[i]))
        return convertedList

    def voiceFillRank(self):
        """fills analysis dictionaris with ordered key list of Position key : 
        ordered list of mapTupleIFs
        only needs to be done for each path, not for each group
        major performance suck
        """
        positionRange = range(0, self.len())
        self.voiceRank['SMTH'] = {} # initialize dictionary
        self.voiceRank['UNIF'] = {} # initialize dictionary
        self.voiceRank['BAL']  = {} # initialize dictionary
        for i in positionRange:
            if (i+1) == self.len():
                break
            srcPos      = i
            dstPos      = i + 1
            srcSet      = self.multisetPath[srcPos].get('pc')
            dstSet      = self.multisetPath[dstPos].get('pc')
            srcSize     = len(srcSet)
            dstSize     = len(dstSet)
            # get pcs from group
            #thisMapTupleId = self.voiceLib[groupName]['maps'][(srcPos, dstPos)]
            #thisPartialId = thisMapTupleId[2]  # the third register in this 
            # tuple has the partial id: (srcSize, dstSize, partialId)
            # this key list has full tuple IDs
            SMTH_dict, orderKeyList = self.mcObj.sortSMTH(srcSet, dstSet)
            convertedList = self._voiceExpandIdList(orderKeyList, srcSize, dstSize)
            self.voiceRank['SMTH'][(srcPos, dstPos)] = convertedList 

            a = self.mcObj.sortUNIF(srcSet, dstSet)
            UNIF_dict = a[0]
            orderKeyList = a[1]
            orderMaxList = a[2]
            orderSpanList = a[3]
            orderOffsetList = a[4]

            convertedList = self._voiceExpandIdList(orderKeyList, srcSize, dstSize)
            self.voiceRank['UNIF'][(srcPos, dstPos)] = convertedList 

            b = self.mcObj.sortBAL(srcSet, dstSet)
            BAL_dict = b[0]
            orderKeyList = b[1]
            orderMaxList = b[2]
            orderSpanList = b[3]
            orderOffsetList = b[4]

            convertedList = self._voiceExpandIdList(orderKeyList, srcSize, dstSize)
            self.voiceRank['BAL'][(srcPos, dstPos)] = convertedList 
            i = i + 1

    def voiceUpdateMapRank(self, groupName):
        """for a given group, this fills the current rankings of the present maps 
        with rank positions for the three analysis positioins
        fills the rank dictionary with position key : current S rank, U rank, 
        B ranks 
        """
        positionRange = range(0, self.len())
        self.voiceLib[groupName]['ranks']  = {} # initialize dictionary
        for i in positionRange:
            if (i+1) == self.len():
                break
            srcPos = i
            dstPos = i + 1
            srcSet = self.get('pcsPath')[srcPos]
            dstSet = self.get('pcsPath')[dstPos]
            srcSize = len(srcSet)
            dstSize = len(dstSet)
            # (srcSize, dstSize, partialId)
            thisMapTupleId = self.voiceLib[groupName]['maps'][(srcPos, dstPos)] 
            smthList = self.voiceRank['SMTH'][(srcPos, dstPos)]
            unifList = self.voiceRank['UNIF'][(srcPos, dstPos)]
            balList = self.voiceRank['BAL'][(srcPos, dstPos)]
            # add one to make first rank == 1, not index pos 0
            smthRank = smthList.index(thisMapTupleId) + 1  
            unifRank = unifList.index(thisMapTupleId) + 1
            balRank = balList.index(thisMapTupleId) + 1
            self.voiceLib[groupName]['ranks'][(srcPos, dstPos)] = (smthRank,
                                                                                 unifRank, balRank) 
            i = i + 1

    def voiceMapRank(self, name, srcPos, dstPos):
        ranks = self.voiceLib[name]['ranks'][(srcPos,dstPos)]     
        size    = len(self.voiceRank['SMTH'][(srcPos, dstPos)])
        return ranks, size      

# not used
#     def getMapIdFromGroupPos(self, name, srcPos, dstPos):
#         mapId = self.voiceLib[name]['maps'][(srcPos, dstPos)]  
#         return mapId   


    def _mapTupleRetro(self, mapId):
        """reverse a map id by switching first and second values"""
        return (mapId[1], mapId[0], mapId[2])

    def _voiceRetro(self):
        """do retrograde for all map groups
        requires going to each map tuple id in each group and reversing values
        update required
        """
        for group in self.voiceNames():
            newKeyList = self.mapKeysFromVoice(group) # gets sorted keys
            newKeyList.reverse() # reverse the keys to go through them backeards
            newMapData = []
            i = 0
            for key in newKeyList:
                # key here is a (src, dst) pairs
                if i + 1 == self.len(): break # needs to be one early
                srcPos = i
                dstPos = i + 1
                newMapId = self._mapTupleRetro(self.voiceMapGet(group, key))
                newKey = srcPos, dstPos
                newMapData.append((group, newKey, newMapId))
                i = i + 1
            self.voiceDelete(group) # del old group
            for name, key, mapId in newMapData:
                self.voiceMapAdd(name, key, mapId)
        # dont need to add ranks, as they will be recalculated
        # updates are called elsewhere

    def _voiceRotate(self, newZero):
        pass # not yet implemented
        # should rotate maps, add boundary map

    def _voiceSlice(self, slRange):
        """do slice on all map groups"""
        min, max = slRange # corrected indices for slice ops
        for group in self.voiceNames():
            oldKeyList    = self.mapKeysFromVoice(group)
            slicedKeyList = oldKeyList[min:max-1] # always one less amp
            newMapData = []
            i = 0
            # will get the old keys out in the new, sliced prder
            for oldKey in slicedKeyList: 
                if (i+1) == self.len(): break
                srcPos = i
                dstPos = i + 1      
                newMapId = self.voiceMapGet(group, oldKey)
                newKey = (srcPos, dstPos)
                newMapData.append((group, newKey, newMapId))
                i = i + 1
            self.voiceDelete(group) # del old group
            for name, key, mapId in newMapData:
                self.voiceMapAdd(name, key, mapId)

    def voiceCopy(self, srcName, dstName):
        """cp a group to a new location"""
        assert srcName in self.voiceNames()
        mapDict = copy.deepcopy(self.voiceLib[srcName]['maps'])
        for key in mapDict.keys():
            mapId = mapDict[key]
            self.voiceMapAdd(dstName, key, mapId)
        self.voiceUpdateMapRank(dstName)
        self.activeVoice = dstName






#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--

class TestOld:
    def __init__(self):
        self.testPolyPathData()

    def testPolyPathData(self):
        dummyPath = ((2,5,1),(-4,5,3),(2,6,4))
        objList = []
        for set in dummyPath:
            objList.append(SC.Multiset(set))

        p = PolyPath()
        p.loadMultisetList(objList)
        print p
        for name in p.forms:
            print name, p.get(name)
        print p[2]
        p[2].t(5)
        print p[2]
        print p.repr('psName')
        p.t(3)
        print p.repr('psName')
        p.i()
        print p.repr('psName')

        print p.voiceLib
        print p.voiceRank
        print p
        p.retro()
        print p
        p.rotate(1)
        print p
        p.slice((1,3))
        print p

if __name__ == '__main__':
    TestOld()




