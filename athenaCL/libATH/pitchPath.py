#-----------------------------------------------------------------||||||||||||--
# Name:          pitchPath.py
# Purpose:       defines path object.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import copy
import unittest, doctest

#from athenaCL.libATH import SC
#from athenaCL.libATH import MC
from athenaCL.libATH import pitchTools
from athenaCL.libATH import drawer
from athenaCL.libATH import multiset

_MOD = 'pitchPath'

class PolyPath:
    def __init__(self, name='test'):
        self.name = name

        #self.voiceType = 'none'
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


    #-----------------------------------------------------------------------||--
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

    #-----------------------------------------------------------------------||--
    # do these edits in place


    def retro(self):
        self.multisetPath.reverse()
        #self._voiceRetro() # reverse the amps
        self._updateMultisetChange() # updates all map sorts, group ranks

    def slice(self, slRange):
        """index positions are proper for list slicing"""
        start, end = slRange
        assert start >= 0 and start < self.len()
        assert end >= 0 and end <= self.len()
        self.multisetPath = self.multisetPath[start:end]
        #self._voiceSlice(slRange) # reverse the amps
        self._updateMultisetChange() # updates all map sorts, group ranks
    
    def rotate(self, newZero):
        """newZero is corrected list index value of new 0 position
        ie, value between 1 and self.len-1
        """
        # see rotate in Multiset for an improved rotation algorithm
        assert newZero >= 1 and newZero < self.len()
        self.multisetPath = (self.multisetPath[newZero:self.len()] + 
                                    self.multisetPath[0:newZero])
        #self._voiceReinit() # erases all maps, sorts: should be replaced w/ rot met
        self._updateNew() # updates all map sorts, group ranks

#     def optimize(self, opt='o'):
#         """optimize the path in place
#         opt can be o for optimize, a for antioptimze"""
#         pass # not yet implemented

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

    #-----------------------------------------------------------------------||--
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


    #-----------------------------------------------------------------------||--
    # semi auto loaders      
    def loadPsList(self, pcsList):
        """adds pcs from a list of pc's, not as a complex set of data"""
        self.multisetPath = [] # clear
        for entry in pcsList:
            pcSet = tuple(entry)
            self.multisetPath.append(multiset.Multiset(pcSet))
        self._updateNew()

    def loadMultisetList(self, objList):
        self.multisetPath = [] # clear
        """load a path as a list of multiset objects"""
        for pitch in objList:
            self.multisetPath.append(pitch)
        self._updateNew()

    #-----------------------------------------------------------------------||--
    def loadDataModel(self, pathData):
        """load data stored in an athenaCL xml file"""
        p = pathData
        # init path, sets cur path voice to auto, inits vars
#         if p['activeVoice']: 
#             self.activeVoice = copy.deepcopy(p['activeVoice'])
        if p['ambitus']: 
            self.ambitus = copy.deepcopy(p['ambitus'])
        # load pitch data
        if p['psPath'] == None: #pre1.0path
            for set in p['scPath']: # must have a set path
                self.multisetPath.append(multiset.Multiset(None, set))
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
                setObj = multiset.Multiset(psPath[i], scPath[i])
                setObj.setT(field[i])
                if p.has_key('durFraction'): 
                    setObj.setDur(durFraction[i])
                self.multisetPath.append(setObj)
                i = i + 1
 
        # updates dur fraction and percent values
        self._updateDurSum() 
        # udpate voiceType for each path
        #self._updatePathSizeType() # this may over-ride a forceNoVL

    def writeDataModel(self):
        """write data in format a dict to store in xml file"""
        p = {}
        #p['activeVoice'] = self.activeVoice # was CurrentPathVoiceXXX
        p['ambitus'] = self.ambitus
        p['psPath'] = self.get('psPath')
        p['pcsPath'] = self.get('pcsPath')
        p['scPath'] = self.get('scPath')
        p['field'] = self.get('field')
        p['durFraction'] = self.get('durFraction')

        return copy.deepcopy(p) # return a copy


    #-----------------------------------------------------------------------||--
    def copy(self, name):
        """output a copy of this object, as new object"""
        pathObj = PolyPath(name)
        # this may not be the best method as it runs update init methods
        newDurPath = []
        for set in self.multisetPath:
            pathObj.multisetPath.append(set.copy())
        #pathObj.voiceLib = copy.deepcopy(self.voiceLib)
        #pathObj.voiceRank = copy.deepcopy(self.voiceRank)
        #pathObj.activeVoice = copy.deepcopy(self.activeVoice)
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

    #-----------------------------------------------------------------------||--

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

    #-----------------------------------------------------------------------||--
    # semi public update methods; use these as much as possible
    def _updateNew(self, forceNoVL=0):
        "all updates when a new path is created"
        self._updateDurSum()
        #self._updatePathSizeType(forceNoVL)
        #self._updateVoiceRank('auto') # updates all, adds auto

    def _updateMultisetChange(self, forceNoVL=0):
        " all updates necessary when a multiset has changed"
        self._updateDurSum() # dur values may have changed
        #self._updatePathSizeType(forceNoVL)
        #self._updateVoiceRank() # updates all groups

    #-----------------------------------------------------------------------||--
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

    #-----------------------------------------------------------------------||--
    # reference counting for use w/ textures

    def refIncr(self):
        "adds one to references"
        self.refCount = self.refCount + 1

    def refDecr(self):
        "removes one from references"
        self.refCount = self.refCount - 1
        if self.refCount < 0:
            self.refCount = 0





#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


    def testPolyPathData(self):
        dummyPath = ((2,5,1),(-4,5,3),(2,6,4))
        objList = []
        for set in dummyPath:
            objList.append(multiset.Multiset(set))
        p = PolyPath()
        p.loadMultisetList(objList)
        for name in p.forms:
            post = name, p.get(name)
        p[2].t(5)
        p.t(3)
        p.i()
        p.retro()
        p.rotate(1)
        p.slice((1,3))



#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)