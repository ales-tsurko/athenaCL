#-----------------------------------------------------------------||||||||||||--
# Name:          SC.py
# Purpose:       utility functions and SC object for all set class operations.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

# master data tables used for all set data access
from athenaCL.libATH import SCdata
from athenaCL.libATH import dialog
from athenaCL.libATH import drawer
from athenaCL.libATH import pitchTools
from athenaCL.libATH import language
from athenaCL.libATH import spectral
from athenaCL.libATH import sieve
from athenaCL.libATH import error
lang = language.LangObj()

SCDICT  = SCdata.SCDICT  # data for all sets, vectors and docs
TNMAX     = SCdata.TNMAX     # dictionary
TNIMAX  = SCdata.TNIMAX  # ref dictionary
TNREF     = SCdata.TNREF     # ref dcitionary
SCREF     = SCdata.SCREF     # ref dcitionary
forte     = SCdata.forte     # classic forte table

#-----------------------------------------------------------------||||||||||||--

import copy

_MOD = 'SC.py'
#-----------------------------------------------------------------||||||||||||--

# these function are depreciated here
# moved to pitchTools.py
# thes are provided for bkward compat
transposer = pitchTools.pcTransposer
pitchSpaceTransposer = pitchTools.psTransposer

#-----------------------------------------------------------------||||||||||||--
# tools for processing sets
# these methods are out of date (post 1.2) and should be phased out of usage

def pcSetTransposer(chord, trans):
    """transposes an entire set by trans. w/ mod12
    will strip oct info, retain micro info
    """
    newSet = []
    for pc in chord:
        newSet.append(pitchTools.pcTransposer(pc, trans))
    return tuple(newSet)
    
def psSetTransposer(chord, trans):
    """transposes an entire set by trans, no mod12
    retains oct info, micro info 
    """
    newSet = []
    for pc in chord:    ## works for negative or positive numbers
        newSet.append(pitchTools.psTransposer(pc, trans))
    return tuple(newSet)
    
def pcInverter(nrmlSet):
    """returns the inversion of a chord (list of pitches in normal form)"""
    tempSet = []
    invertSet = []
    for pitch in nrmlSet:
        tempSet.append((12 - pitch) % 12)
    tempSet.reverse()
    for pitch in tempSet:
        invertSet.append(transposer(pitch, (12 - tempSet[0])))
    return tuple(invertSet)

def psInverter(normalChord): 
    """returns the inversion of a chord (list of pitches in normal form)
    returns inversion with same starting value in pitch space
    must be entered as normal form
    """  
    modInversiontSet = pcInverter(normalChord)
    
    sourceSetAsOctMultipliers = []
    for entry in normalChord:
        octMultiplier, modPC = pitchTools.splitOctPs(entry)
        # gives original order of oct multipliers fo each member of set
        sourceSetAsOctMultipliers.append(octMultiplier)
    
    modInversiontSet = list(modInversiontSet)
    # do mod 12 transposition
    invertedChord = pcSetTransposer(modInversiontSet, normalChord[0])
  
    invertedChord = list(invertedChord)
    #check octaves
    for i in range(0,len(normalChord)) :
        sourceOct = sourceSetAsOctMultipliers[i]
        currentOct, modPC = pitchTools.splitOctPs(invertedChord[i])     
        if sourceOct == currentOct:
            pass
        else: # find difference and make up
          if sourceOct > currentOct:
              direction = 'up'
          else:
              direction = 'down'
          distance = abs(currentOct - sourceOct)
          if direction == 'up':
              invertedChord[i] = invertedChord[i] + (12 * distance)
          else:
              invertedChord[i] = invertedChord[i] - (12 * distance)         
    return tuple(invertedChord)

    
#-----------------------------------------------------------------||||||||||||--
def psSetToMason(chord):
    """named after a music educator named Mason by Michael Gogins
    convert any pitch space / class set to a 'mason' value
    OR-ing, to be precise, mod 4095 (the total number of unordered
    pitch-class sets in 12TET), not adding. In other words, a bit-field of 12
    bits, one bit per pitch-class.
    """
    newSet = []
    for pc in chord:
        pc = pitchTools.pcTransposer(pc, 0) # make mod 12
        if pc not in newSet: # remove redundancies
            newSet.append(pc)
    mason = 0
    for i in newSet:
        mason = mason + pow(2, i)
    return mason % 4095

#-----------------------------------------------------------------||||||||||||--
# utility to calculate normal form
def findNormalT(pcSet, setMatrix=None):
    """finds normal form of any pc set and returns forte number
    as a scTriple data structure, and transposition from normal form
    pcSet may contain psReals, and as such, need to be converted to ints
    """
    if setMatrix == None: # use forte as default
        setMatrix = forte
    MONADscTuple = (1,1,0)

    # check for bad data
    if drawer.isStr(pcSet):
        return None # error, no strings supported here
    if drawer.isList(pcSet):
        for psReal in pcSet:# make sure all values are numbers; no strings allowed
            if drawer.isStr(psReal):
                return None # break, return None as error
    # check for unusual data
    if drawer.isNum(pcSet): # its a single number
        pcVal = pitchTools.roundMicro(pcSet)
        return MONADscTuple, (pcVal % 12) # second number is transposition from 0
    if len(pcSet) == 1:  #filter out monad!
        pcVal = pitchTools.roundMicro(pcSet[0])
        return MONADscTuple, (pcVal % 12)

    # scrub and go
    pcSetClone = []
    for psReal in pcSet: # pcSet may contian psReal, w/ floating values
        pcSetClone.append(pitchTools.roundMicro(psReal))
    #check fr non base 12 numbers, negative numbers, redundancies
    pcSetClone = list(pcSetTransposer(pcSetClone, 0))
    pcSetClone.sort()

    i = 0
    chord = []
    for i in range(0,12):  # remove redundancies
        if i in pcSetClone:
            chord.append(i)
    card = len(chord)    
    if card < 1: # monad has already been filtered out
        return None # 2nd no is transposition from 0
    if card == 1: # this is a set like (3,3,3,3)
        return MONADscTuple, (pcSet[0] % 12) 
    elif card > 12:
        return None # 'irrational cardinality error'

    rotIndices = range(0, card)
    foundIndex = None                #control variable
    for rot in rotIndices:
        r        = rot # dont need to add 1? + 1
        rotSet = chord[r:card] + chord[0:r]
        dif  = rotSet[0]
        pSet     = pcSetTransposer(rotSet, -dif)
        iSet     = tuple(pcInverter(pSet))
        maxRange = len(setMatrix[card])
        # check all sets of given card for match
        for index in range(1, maxRange):     # start with 1, not zero
            # this is a default; may be a symmetrical set and have no inversion
            foundInv = 'A' 
            # test each set in this cardinality; "0" gets pitches
            testSet = tuple(setMatrix[card][index][0])  
            if iSet == testSet:
                foundIndex = index
                foundInv      = 'B'      #nt sure yet if 1 or 0
                break 
            elif pSet == testSet:
                foundIndex = index
                foundInv      = 'A'      #nt sure yet if 1 or 0 
                break
        if foundIndex != None:
            break
    if foundIndex == None:  ## no set found
        return None #'failed!!!'
    
    if foundInv == 'B':
        # has inversion that is non-redundant (variant)
        if setMatrix[card][foundIndex][2][1] == 0 :   
            scInv = -1
        else: scInv = 0
    elif foundInv == 'A':
         # has inversion that is non-redundant (variant)
        if setMatrix[card][foundIndex][2][1] == 0 :
            scInv = 1
        else: scInv = 0
    return (card, foundIndex, scInv), dif


def findNormal(pcSet, setMatrix=None):
    """same as above but w/o returning transposition"""
    scTuple, dif = findNormalT(pcSet, setMatrix)
    return scTuple


#-----------------------------------------------------------------||||||||||||--
# conversion utilities

def forteToSc(card, index, inversion=-2):
    """checks for proper inversion and supplies one (A) if not given
    acts as a general filter for all functions calling old forte numbers or
    possible errors: this function will check and suply an alternitive if 
    there is an error rather than raising an exception. its used heavily 
    and is a source of possible errors
    """
    boundError = 0
    if card > 12 or card < 1:
        boundError = 1
    else: scCard = card          #all other cards are good + used

    # checks cardinality fr a valid index number
    # supplies index 1 fr a valid card that does nt have
    # a valid index. !!!!!!!!!! should return an error!
    
    if card == 1 or card == 11:
        if index <= 0 or index >2:
            boundError = 1
        else: scIndex = index
    if card == 2 or card == 10:
        if index <= 0 or index >6:
            boundError = 1
        else: scIndex = index
    elif card == 3 or card == 9:
        if index <= 0 or index > 12:
            boundError = 1
        else: scIndex = index
    elif card == 4 or card == 8:
        if index <= 0 or index > 29:
            boundError = 1
        else: scIndex = index
    elif card == 5 or card == 7:
        if index <= 0 or index > 38:
            boundError = 1
        else: scIndex = index
    elif card == 6:
        if index <= 0 or index > 50:
            boundError = 1
        else: scIndex = index
    elif card == 12:    ## aggregate!
        if index <= 0 or index > 2:
            boundError = 1
        else: scIndex = index

    if boundError:
        print _MOD, 'SC boundary error', card, index, inversion
        return None
    # check fr proper inversion status useing variance vector
    # if_no inv give fr a set, 0 or 1 is suplied, never -1
    # if_no inversion is supplied, acts as if_in Tn/i classification
             
    if inversion <= -2 or inversion >= 2 or inversion == 0:
        if forte[scCard][scIndex][2][1] == 0 :      
        # has inversion that is non-redundant (variant)
            scInv = 1
        else: scInv = 0
    if inversion == -1:
        if forte[scCard][scIndex][2][1] == 0 :
            scInv = -1
        else: scInv = 0
    if inversion == 1:
        if forte[scCard][scIndex][2][1] == 0 :
            scInv = 1   
        else: scInv = 0

    return scCard, scIndex, scInv

def tupleToSc(rawForte):
    """accepts single tuple as input, then uses forte to sc to 
        to supply necessary inversion, if needed.
    """
    if rawForte[0] == 1:
        return (1,1,0) 
    try:
        inv = rawForte[2]
    except:
        inv = -2     #unknown inversion value: forte to sc will suply
    scTuple = forteToSc(rawForte[0], rawForte[1], inv)
    if scTuple == None:
        raise ValueError
    return scTuple

# scToStr method should be moved inside Multiset
def scToStr(rawForte):
    """raw fortte is a tuple with either 2 or 3 elements, needing to be 
        checked
    """
    if drawer.isInt(rawForte):
        return '1-1' 
    elif rawForte[0] == 1:
        return '1-1'      
    
    scTuple = tupleToSc(rawForte)     
    if len(scTuple) != 3: raise ValueError # should never happen
        
    card = str(scTuple[0])
    indx = str(scTuple[1])
    if scTuple[2] == 0:
        inv = ''
    elif scTuple[2] == 1:
        inv = 'A'
    elif scTuple[2] == -1:
        inv = 'B'
    else: inv = 'error'
    return card + '-' + indx + inv
        







#-----------------------------------------------------------------||||||||||||--

class SetClass:
    """object to provide a unifrom interface to SC data
        this is a library object; it store utility functions and reference data
        object, in general, should be passed; unique objects are not needed
        no permanent data stored in this object
        only use to acces data, not to process or display
    """
          
    def __init__(self):
        # backward compat tables
        self.REFdiaNameToPc = pitchTools.REFdiaNameToPc

        self.analysisDict = {
        'K'   : self.morris_K,            #  (self, forteX, forteY) 
        'pRel'  : self.castren_pRel,          #  (self, forteX, forteY, tni=1, n=2) 
        'R1'      : self.forte_R1,            #  (self, forteX, forteY)
        'R2'      : self.forte_R2,            #(self, forteX, forteY, strict = 1, 
                                                      # min_matches = 4)
        'R0'      : self.forte_R0,            #  (self, forteX, forteY)
        'SI'      : self.teitelbaum_SI,       #  (self, forteX, forteY)
        'SIM'     : self.morris_SIM,              #  (self, forteX, forteY)
        'ASIM'  : self.morris_ASIM,       #(self, forteX, forteY)                     
                                                      #{1    -0(h.sim), avg=.42, d.v.=79}
        'sf'      : self.lord_sf,                 #  (self, forteX, forteY)
        'IcVSIM': self.isaacson_IcVSIM,   #  (self, forteX, forteY)
        'IcVD1' : self.rogers_IcVD1,          #  (self, forteX, forteY)
        'IcVD2' : self.rogers_IcVD2,          #  (self, forteX, forteY)
        'COST'  : self.rogers_COST,       #(self, forteX, forteY)                     
                                                      #{0    -1(h.sim), avg=.81, d.v.=92}
        'Ak'      : self.rahn_Ak,                 #(self, forteX, forteY)                     
                                                      #{0    -1(h.sim), avg=.58, d.v.=78}
        'MEMBn' : self.rahn_MEMBn,            #  (self, forteX, forteY,tni=1,n=2,)
        'TMEMB' : self.rahn_TMEMB,            #  (self, forteX, forteY, tni=1)
        'ATMEMB': self.rahn_ATMEMB,       #(self, forteX, forteY, tni=1)              
                                                      #{0    -1(h.sim), avg=.45, d.v.=101}
        'REL'     : self.lewin_REL,           #(self, forteX, forteY, tni=1)              
                                                      #{0    -1(h.sim), avg=.57, d.v.=91}
        'TpRel' : self.castren_TpREL,         #(self, forteX, forteY, tni=1)              
                                                      #{100-0(h.sim), avg= 63, d.v.=79}
        }

    #-----------------------------------------
    # bacward compat functions
    # will be removed with multiset
    def forteToSc(self, card, index, inversion=-2):
        return forteToSc(card, index, inversion)

    def tupleToSc(self, rawForte):
        return tupleToSc(rawForte)

    def scToStr(self, rawForte):
        return scToStr(rawForte)

    # will be depreciated, as now in pitch tools
    def anySetToPcs(self, set):
        # set can contain any int, positive or neg
        # input must be a list
        pcsSet = []
        for entry in set:
            modulatedEntry = transposer(entry, 0)
            pcsSet.append(modulatedEntry)
        pcsSet = tuple(pcsSet)
        return pcsSet

    #-----------------------------------------
    # data access
    def rawSetData(self, card, index, inv, key):
        'access data as from list coordinants'
        return SCDICT[card][index,inv][key]
        
    def getAllScTriples(self, cardRange='all', tniTog=0):
        """gets all scTriples within a variety of ranges
        card range can be specified as string 'all', 
        as an int (getting just the values of that int
        or as a range from 1 to 12; if range, last values is inclusif"""
        if cardRange == 'all':
            gatherCards = range(1,13)
        elif drawer.isInt(cardRange):
            gatherCards = [cardRange,] # only get one card
        elif drawer.isList(cardRange):
            if cardRange[1] < cardRange[0]:
                raise ValueError, 'bad cardinality range given'
            elif cardRange[0] == cardRange[1]:
                gatherCards = [cardRange[0],] # only get one card
            else:
                gatherCards = range(cardRange[0], cardRange[1]+1)
        found = []
        for scTriple in TNREF.keys():
            card = scTriple[0]
            inv = scTriple[2]
            if card in gatherCards:
                if tniTog and inv == -1: pass # leave out inversions
                else:
                    found.append(scTriple)
        found.sort()
        return found

                    
     #---------------------||||||||||||--                    
    # these functions are used fr calling any data entry frm
    # the SCDICT via a SC class instance (as Sc n Athena)
    # AUTOVALIDATED with sc_to_forte.
    # if_no inversion is supplied, acts as if_in Tn/i classification
     #   -2 is the unknown (test and suply) integer, if nt suplied when called
    
    def pcs(self, rawForte):      
        scTuple = self.tupleToSc(rawForte)
        return SCDICT[scTuple[0]][scTuple[1], scTuple[2]][0]
    def var(self, rawForte):
        scTuple = self.tupleToSc(rawForte)
        return SCDICT[scTuple[0]][scTuple[1], scTuple[2]][1]
    def icv(self, rawForte):
        scTuple = self.tupleToSc(rawForte)
        return SCDICT[scTuple[0]][scTuple[1], scTuple[2]][2]


    def cv(self, rawForte, n):
        """get tni vector for a forte and an n size"""
        if n > 12 or n < 2:
            return 'error in cv n value'
        scTuple = self.tupleToSc(rawForte)
        # translate a 2cv to an icv vector
        if n == 2:
            key = 2
        # find position in SC data tuple
        else:
            card    = scTuple[0]
            if n > card:
                return 'n/a'
            shift = 2 # positional shift nec. to get the right data string
            key = shift + (n-2)
        try:
            value = SCDICT[scTuple[0]][scTuple[1], scTuple[2]][key]
        except:
            value = 'n/a'
        return value


    def xv(self, rawForte, n):
        """get tn vector for a forte and an n size"""
        if n > 12 or n < 2:
            return 'error in xv n value'
        scTuple = self.tupleToSc(rawForte)
        # translate a 2cv to an icv vector
        if n == 2:
            key = 2
        # find position in SC data tuple
        else:
            card    = scTuple[0]
            if n > card:
                return 'n/a'     
            # card-2 is the number of positions to move over ot get xvectors        
            shift = 2 + (card-2) 
            key = shift + (n-2)
        try:
            value = SCDICT[scTuple[0]][scTuple[1], scTuple[2]][key]
        except:
            value = 'n/a'
        return value


    def _findVectorPos(self, rawForte, tniMode=0):
        """for a given set, finds the appropriate vector position
            given the appropriate tni mode """
        scTuple = self.tupleToSc(rawForte)
        card, index, inv = scTuple
        if tniMode == 1: # tni mode
            vectorPos = index - 1 # subtract one to get list position
        else: # tn mode
            vectorPos = TNREF[scTuple] - 1
        return vectorPos

    def _findVectorVal(self, rawForteBase, rawForteSeek, tniMode=0):
        """gets the value from a vector belong to forteBase; value is number
            of subsets like forteSeek
        """
        scTupleBase = self.tupleToSc(rawForteBase)
        scTupleSeek = self.tupleToSc(rawForteSeek)
        cardBase, indexBase, invBase = scTupleBase
        cardSeek, indexSeek, invSeek = scTupleSeek

        if cardSeek > cardBase: # no vectors of greater card than source
            return None

        vPos = self._findVectorPos(rawForteSeek, tniMode)
        if tniMode == 1: #tni mode
            vector = self.cv(scTupleBase, cardSeek)
        else: #tn mode
            vector = self.xv(scTupleBase, cardSeek)
        return vector[vPos]
         

    def zData(self, rawForte):            
        """returns sc tuple of z relation, if it exists
            otherwise, returns none
        """       
        scTuple = self.tupleToSc(rawForte)
        zVal = forte[scTuple[0]][scTuple[1]][3] # gets z relation val
        # z val is index of relative z relation
        if zVal == 0:
            return None
        else:
            # find card complement
            card = scTuple[0]
            return self.tupleToSc((card, zVal))

    def refData(self, rawForte):
        """returns dictionary of references from SCdata"""
        scTuple = self.tupleToSc(rawForte)
        setRef = SCREF[scTuple]
        if setRef == {} or setRef == None:
            return None
        else:
            return setRef


    def findSuperSets(self, rawForte, cardRange='all', tniMode=0):
        """find all sets with equal or greater card that have this
            set as a subset
        """
        scTupleSeek = self.tupleToSc(rawForte)
        card, index, inv = scTupleSeek
        if card >= 1 and card <= 12:
            if cardRange == 'all':
                cardsToSearch = range(card, 13)
            setList = self.getAllScTriples(cardsToSearch, tniMode)

        valueDict = {}
        for set in setList:
            vectorVal = self._findVectorVal(set, scTupleSeek, tniMode)
            if vectorVal != 0:    
                valueDict[set] = vectorVal

        searchResults = []
        rankList = []
        for setTuple in valueDict.keys():
            rankList.append((valueDict[setTuple], setTuple))
        rankList.sort()
        rankList.reverse()
        for rank, setTuple in rankList:
            searchResults.append(setTuple) # ordered by rank
        if searchResults == []:
            return None
        return searchResults, valueDict

    def findAllZ(self, cardRange='all', tniMode=0):
        """return a list of triples for a all sets that have a z relations"""
        searchResults = []
        for setTriple in self.getAllScTriples('all', tniMode):
            if self.zData(setTriple) != None:
                searchResults.append(setTriple)
        return searchResults

    def _strToSearchList(self, str):
        """removes bad characters, returns a list of words"""
        str = str.replace('-',' ')
        str = str.replace(',',' ')
        str = str.replace('/',' ')
        str = str.replace('\ ', ' ')
        strList = str.split() # returns a list
        return strList           

    def findRef(self, searchStr, refType='name', setRange='all', tniMode=0):
        searchWords = self._strToSearchList(searchStr) # returns a list
        scoreDict = {}
        for setTuple in self.getAllScTriples('all', tniMode):
            refDict = self.refData(setTuple)
            scoreDict[setTuple] = 0
            if refDict == None:
                continue
            if refDict.has_key(refType): # name groups
                nameList = refDict[refType]
                nameWords = []
                for nameStrings in nameList: # list of strings
                    nameWords = nameWords + self._strToSearchList(nameStrings)           
                for sw in searchWords:
                    swTemp = sw.lower() # keep case
                    for nw in nameWords:
                        nwTemp = nw.lower() # keep case
                        if nwTemp.find(swTemp) >= 0:
                            scoreDict[setTuple] = scoreDict[setTuple] + 1 # add point
        rankList = []
        for setTuple in scoreDict.keys():
            if scoreDict[setTuple] == 0:
                del scoreDict[setTuple] # remove if 0 score
            else: # add ranks to a list
                rankList.append((scoreDict[setTuple], setTuple))
        rankList.sort()
        rankList.reverse()      
        searchResults = []
        for rank, setTuple in rankList: # ordered
            searchResults.append(setTuple)
        if searchResults == []:
            return None
        else:
            return searchResults # list of triples


    #---------------------||||||||||||-- 
    # sim utilities 

    def _sumVector(self, vector):
        sum = 0
        for reg in vector:
            sum = sum + reg
        return sum

    def _pcentVector(self, vector):
        '%v'
        total = self._sumVector(vector)
        p_v = []
        for reg in vector:
            percent = (reg / float(total)) * 100
            # if rounded here, error emerge in_castren_pRel
            # percent = round(percent)
            # percent = int(percent)
            p_v.append(percent)  
        return p_v
        
    def _difVector(self, vectorX, vectorY):
        """difference vector"""
        # this_vector should be a % vector before processing
        max = len(vectorX)
        difVectorX = []
        difVectorY = []
        for i in range(0, max):
            if vectorX[i] == vectorY[i]:
                difVectorX.append(0)
                difVectorY.append(0)
            elif vectorX[i] > vectorY[i]:
                difVectorX.append(vectorX[i] - vectorY[i])
                difVectorY.append(0)
            elif vectorY[i] > vectorX[i]:
                difVectorX.append(0)
                difVectorY.append(vectorY[i] - vectorX[i])
        difVectorX = tuple(difVectorX)
        difVectorY = tuple(difVectorY)
        return(difVectorX, difVectorY)

    def _scaledDifVector(self, vectorX, vectorY):
        """scaled difference vector"""
        # this_vector should be a % vector before processing
        difVectorX, difVectorY = self._difVector(vectorX, vectorY)
        sd_vector_x = self._pcentVector(difVectorX)
        sd_vector_y = self._pcentVector(difVectorY)
        return (sd_vector_x, sd_vector_y)

    def _scToSdv(self, forteX, forteY, tni=1, n=2):
        """converts 2 set classes to scaled difference vectors"""
        #_if tni == 1,(true_, TnI) uses cvN vectors (smaller)
        #_if tni == 0 (false_,Tn), uses cxN vectors (larger)
        if n > forteX[0] or n > forteY[0]:
            return 'no subset under this cardinality'
        if tni == 1:  #TnI#
            vectorX = self.cv(forteX, n)
            vectorY = self.cv(forteY, n)
        else:             #Tn #
            vectorX = self.xv(forteX, n)
            vectorY = self.xv(forteY, n)              
        p_vector_x                      = self._pcentVector(vectorX)
        p_vector_y                      = self._pcentVector(vectorY)
        sdv_vector_x, sdv_vector_y = self._scaledDifVector(p_vector_x, p_vector_y)
        return tuple(sdv_vector_x), tuple(sdv_vector_y)

    def _vPosToSc(self, vector_position, tni=1, n=2):
        if tni == 1:  #TnI#
            return (n, vector_position + 1)
        else:             #Tn #
            for key, value in TNREF.items():
                if key[0] == n and value == vector_position + 1:
                    return key

    def _vToValueSc(self, sd_vector, tni=1, n=2):
        """process scalled difference vector only"""
        pairs = []
        for i in range(0, len(sd_vector)):
            if sd_vector[i] == 0:
                continue
            set = self._vPosToSc(i, tni, n)
            pairs.append((sd_vector[i], set))
        return pairs

    def _difGroup(self, forteX, forteY, tni=1, n=2):
        """creates weight, sc pair lists"""
        sdv_vector_x, sdv_vector_y = self._scToSdv(forteX, forteY, tni, n)
        pair_x = self._vToValueSc(sdv_vector_x, tni, n)
        pair_y = self._vToValueSc(sdv_vector_y, tni, n)
        return tuple(pair_x), tuple(pair_y)

    def _crossGroup(self, pair_x, pair_y, tni=1, pRel_n=2):
        """process only weight/sc pair lists"""
        group = []
        for weight_x, sc_x in pair_x:
            for weight_y, sc_y in pair_y:
                Wp    = (weight_x * weight_y) / 100.0
                pRel = self.castren_pRel(sc_x, sc_y, tni, pRel_n)
                vW    = (pRel * Wp) / 100.0
                group.append((sc_x, sc_y, vW))
        return group


    #---------------------||||||||||||-- 
    # NOTE these methods use the doc string to store the min
    # max and average value of each of these functions

    def morris_K(self, forteX, forteY, tni=1):  #castren, p37
        '(0, 55, 10, 35)'    #min sim, max sim, avg, values
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY)
        minimum = []
        for i in range(0,6):      #icv vector indices 0-5       
            if icv_x[i] < icv_y[i]:
                minimum.append(icv_x[i])
            else: minimum.append(icv_y[i])
        sum = self._sumVector(minimum)      
        return sum
 
 
    def castren_pRel(self, forteX, forteY, tni=1, n=2):  #castren, p39
        '(100, 0, 30, 85)'  #min sim, max sim, avg, values
        #_if tni == 1,(true_, TnI) uses cvN vectors (smaller)
        #_if tni == 0 (false_,Tn), uses cxN vectors (larger)
        if n > forteX[0] or n > forteY[0]:
            return 'no subset under this cardinality'
        if tni == 1:  #TnI#
            vectorX = self.cv(forteX, n)
            vectorY = self.cv(forteY, n)
            max = TNIMAX[n]
        else:             #Tn #
            vectorX = self.xv(forteX, n)
            vectorY = self.xv(forteY, n)              
            max = TNMAX[n]
        p_v_x = self._pcentVector(vectorX)
        p_v_y = self._pcentVector(vectorY)
        temp = []
        for i in range(0,max):
            dif = abs(p_v_x[i] - p_v_y[i])
            temp.append(dif)
        sum = self._sumVector(temp)
        return round((sum / 2.0), 1)


        


    #---------------------||||||||||||--  
    # sim relations not_producing values
 
    def forte_R1(self, forteX, forteY, tni=1):  #castren, p43
        '0'
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY)
        match_indices = []
        nomat_indices = []
        for i in range(0,6):      #icv vector indices 0-5       
            if icv_x[i] == icv_y[i]:
                match_indices.append(i)
            else:
                nomat_indices.append(i)
        if len(match_indices) != 4:
            return 0
        if (icv_x[nomat_indices[0]] == icv_y[nomat_indices[1]] and 
             icv_x[nomat_indices[1]] == icv_y[nomat_indices[0]]):
            return 1
        else: return 0   
     
    def forte_R2(self, forteX, forteY, tni=1, strict=1, min_matches=4): 
        #castren, p44
        '0'
        # strict is used to follow strict forte rules, that is, the 2 
        # left-over vector registers
        # can not_hold the r1-like cross relation. if_strict == 0 (false_),
        # this_test 
        # only finds the minimum number of matches needed (4 the default_)
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY)      
        match_indices = []
        nomat_indices = []
        for i in range(0,6):      #icv vector indices 0-5       
            if icv_x[i] == icv_y[i]:
                match_indices.append(i)
            else:
                nomat_indices.append(i)
        # THIS IS FORTES EXACT DEFINITION
        if strict == 1:  
            if len(match_indices) != 4:
                return 0
            # this_is R1
            if (icv_x[nomat_indices[0]] == icv_y[nomat_indices[1]] and 
                 icv_x[nomat_indices[1]] == icv_y[nomat_indices[0]]):
                return 0            
            else: return 1           
        # THIS IS A MORE FLEXIBLE TEST
        else:
            if len(match_indices) < min_matches:
                return 0
            else:
                return 1
            

    def forte_R0(self, forteX, forteY, tni=1):  #castren, p46
        '0'
        # find minimum similarity
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY)
        match_indices = []
        for i in range(0,6):      #icv vector indices 0-5       
            if icv_x[i] == icv_y[i]:
                match_indices.append(i)
        if len(match_indices) == 0:
            return 1
        else: return 0          
        
 
 # skipped b/c very very week
 # Alphonce: Difference Value Relation (castren p49)
 # Solomon: R relation (castren p50)
 
     
    #---------------------||||||||||||--  
    # sim relations comparing one subset-class_cardinality at a time
     
     
    def teitelbaum_SI(self, forteX, forteY, tni=1):  #castren, p51
        '(8.49, 1.41, 2.85, 31)'  #min sim, max sim, avg, values
        if forteX[0] != forteY[0]:
            return 'n/a'
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY)    
        temp = []
        for i in range(0,6):      #icv vector indices 0-5       
            value = pow((icv_x[i] - icv_y[i]), 2)
            temp.append(value)
        sum = self._sumVector(temp)
        return pow(sum, .5) #round?
        
    def morris_SIM(self, forteX, forteY, tni=1):     #castren, p54
        '(65, 0, 13, 44)'    #min sim, max sim, avg, values
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY)    
        temp = []
        for i in range(0,6):                             #icv vector indices 0-5      
            value = abs(icv_x[i] - icv_y[i])
            temp.append(value)
        sum = self._sumVector(temp)
        return sum
     
    def morris_ASIM(self, forteX, forteY, tni=1):  #castren, p59
        '(1, 0, .42, 79)'    #min sim, max sim, avg, values
        sim = self.morris_SIM(forteX, forteY)
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY) 
        sum = self._sumVector(icv_x) + self._sumVector(icv_y)    # add '#ICV'
        return sim / float(sum) # may result in divid by zero error

    def lord_sf(self, forteX, forteY, tni=1):    #castren, p61
        '(9, 0, 3, 10)'  #min sim, max sim, avg, values
        if forteX[0] != forteY[0]:
            return 'n/a'    
        sim = self.morris_SIM(forteX, forteY)
        return sim / 2.0
     
    def isaacson_IcVSIM(self, forteX, forteY, tni=1):   #castren, p62
        '(3.64, 0, 1.2, 121)'  #min sim, max sim, avg, values
        # not_perfect correspondance with castren's results
        # see notes on page 65

        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY) 
        IdV = []
        for i in range(0,6):                             #icv vector indices 0-5      
            value = abs(icv_x[i] - icv_y[i])
            IdV.append(value)        
        sum_IdV     = self._sumVector(IdV) 
        average_IdV = sum_IdV / 6.0              #always 6 for_icv's

        sum = 0
        for IdV_reg in IdV:
            sum = sum + pow((IdV_reg - average_IdV), 2)
        return pow((sum / 6.0), .5)  

 
    def rogers_IcVD1(self, forteX, forteY, tni=1):  #castren, p67
        '(2, 0, .59, 140)'  #min sim, max sim, avg, values
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY) 

        sum_x = self._sumVector(icv_x)
        sum_y = self._sumVector(icv_y)

        temp = []
        for i in range(0,6):                             #icv vector indices 0-5      
            value = abs((icv_x[i]/float(sum_x)) - (icv_y[i]/float(sum_y)))
            temp.append(value)    
        return self._sumVector(temp) 

    def rogers_IcVD2(self, forteX, forteY, tni=1):  #castren, p67
        '(1.41, 0, .54, 133)'  #min sim, max sim, avg, values
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY) 

        sum_x = 0
        for elem in icv_x:
            sum_x = sum_x + pow(elem, 2)
        rad_x = pow(sum_x, .5)

        sum_y = 0
        for elem in icv_y:
            sum_y = sum_y + pow(elem, 2)
        rad_y = pow(sum_y, .5)

        temp = []
        for i in range(0,6):             #icv vector indices 0-5      
            value = pow(((icv_x[i]/rad_x) - (icv_y[i]/rad_y)), 2)
            temp.append(value)  
        sum = self._sumVector(temp)

        return pow(sum, .5)



    def rogers_COST(self, forteX, forteY, tni=1):  #castren, p71
        '(0, 1, .81, 92)'    #min sim, max sim, avg, values
        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY) 

        numerator = 0
        for i in range(0,6):
            numerator = numerator + (icv_x[i] * icv_y[i])

        sum_x = 0
        for elem in icv_x:
            sum_x = sum_x + pow(elem, 2)
        rad_x = pow(sum_x, .5)

        sum_y = 0
        for elem in icv_y:
            sum_y = sum_y + pow(elem, 2)
        rad_y = pow(sum_y, .5)

        denominator = rad_x * rad_y
        if denominator == 0:
            print 'divide by zero error'
            result = 0
        result = numerator / denominator
        return result



    def rahn_Ak(self, forteX, forteY, tni=1):    #castren, p73
        '(0, 1, .58, 78)'    #min sim, max sim, avg, values
        # ak(X,Y) = (1-ASIM(X,Y))

        numerator = 2 * self.morris_K(forteX, forteY)

        icv_x = self.icv(forteX)
        icv_y = self.icv(forteY) 
        sum_x = self._sumVector(icv_x)
        sum_y = self._sumVector(icv_y)
        denominator = sum_x + sum_y

        return numerator / float(denominator)


    def rahn_MEMBn(self, forteX, forteY, tni=1, n=2):   #castren, p75
        '(0, 121, 30, 79)'  #min sim, max sim, avg, values
        #_if tni == 1,(true_, TnI) uses cvN vectors (smaller)
        #_if tni == 0 (false_,Tn), uses cxN vectors (larger)
        if n > forteX[0] or n > forteY[0]:
            return 'no subset under this cardinality'
        if tni == 1:  #TnI#
            vectorX = self.cv(forteX, n)
            vectorY = self.cv(forteY, n)
            max = TNIMAX[n]
        else:             #Tn #
            vectorX = self.xv(forteX, n)
            vectorY = self.xv(forteY, n)              
            max = TNMAX[n]

        MEMBn = 0
        for i in range(0, max):
            if vectorX[i] == 0 or vectorY[i] == 0:
                continue
            else:
                MEMBn = MEMBn + (vectorX[i] + vectorY[i])
        return MEMBn

    #---------------------||||||||||||--  
    # total measures

    def rahn_TMEMB(self, forteX, forteY, tni=1):     #castren, p80
        '(0, 6118, 131, 877)'  #min sim, max sim, avg, values
        # not_perfect correspondance with castren's results
        # see notes on page 84 (error of a single digit: 440/441)

        if forteX[0] <= forteY[0]:
            n = forteX[0]
        else: 
            n = forteY[0]
        TMEMB = 0
        for n_subset in range(2, (n + 1)):
            value = self.rahn_MEMBn(forteX, forteY, tni, n_subset)
            TMEMB = TMEMB + value
        return TMEMB


    def rahn_ATMEMB(self, forteX, forteY, tni=1):  #castren, p84
        '(0, 1, .45, 101)'  #min sim, max sim, avg, values
        # all numbers match castren, impying possible errors_in
        # rahn_TMEMB unimportant

        if forteX[0] <= forteY[0]:
            n = forteX[0]
        else: 
            n = forteY[0]
        TMEMB = 0
        for n_subset in range(2, (n + 1)):
            value = self.rahn_MEMBn(forteX, forteY, tni, n_subset)
            TMEMB = TMEMB + value
        denominator = ((pow(2, forteX[0]) + pow(2, forteY[0])) - 
                          (forteX[0] + forteY[0] + 2))
        return TMEMB / float(denominator)


    def lewin_REL(self, forteX, forteY, tni=1): #castren, p89
        '(0, 1, .57, 91)'    #min sim, max sim, avg, values

        # most numbers match castren, with occassional round errors

        #_if tni == 1,(true_, TnI) uses cvN vectors (smaller)
        #_if tni == 0 (false_,Tn), uses cxN vectors (larger)

        if forteX[0] <= forteY[0]:
            n = forteX[0]
        else: 
            n = forteY[0]

        V_tot     = 0
        W_tot_x = 0
        W_tot_y = 0
        for n_subset in range(2, (n + 1)): 
            if tni == 1:  #TnI#
                vectorX = self.cv(forteX, n_subset)
                vectorY = self.cv(forteY, n_subset)
                max = TNIMAX[n_subset]       #number of registers in_vector
            else:             #Tn #
                vectorX = self.xv(forteX, n_subset)
                vectorY = self.xv(forteY, n_subset)             
                max = TNMAX[n_subset] 

            for i in range(0, max):
                V_tot = V_tot + pow((vectorX[i] * vectorY[i]), .5)

            sum_x       = self._sumVector(vectorX)
            W_tot_x = W_tot_x + sum_x
            sum_y       = self._sumVector(vectorY)
            W_tot_y = W_tot_y + sum_y
        try:
            REL = V_tot / pow((W_tot_x * W_tot_y), .5)
        except ZeroDivisionError:
            print "divide by zero error"
            REL = 0
        return REL


    def castren_TpREL(self, forteX, forteY, tni=1):  #castren, p89
        '(100, 0, 63, 79)'  #min sim, max sim, avg, values
        #_if tni == 1,(true_, TnI) uses cvN vectors (smaller)
        #_if tni == 0 (false_,Tn), uses cxN vectors (larger)

        if forteX[0] == forteY[0]:
            n = forteX[0] - 1
        elif forteX[0] < forteY[0]: 
            n = forteX[0]
        else: 
            n = forteY[0]

        numerator = 0
        for n_subset in range(2, (n + 1)): 
            if tni == 1:  #TnI#
                vectorX = self.cv(forteX, n_subset)
                vectorY = self.cv(forteY, n_subset)
                max = TNIMAX[n_subset]       #number of registers in_vector
            else:             #Tn #
                vectorX = self.xv(forteX, n_subset)
                vectorY = self.xv(forteY, n_subset)             
                max = TNMAX[n_subset] 
            pv_x = self._pcentVector(vectorX)
            pv_y = self._pcentVector(vectorY)
            sum = 0
            for i in range(0, max):
                sum = sum + abs(pv_x[i] - pv_y[i])           
            numerator = numerator + (sum / 2.0)
        return numerator / (n - 1)

    #---------------------||||||||||||--  

    def _castrenLevel(self, forteX, forteY, level):
        # branch acts like n on the local level, not_to be confused with a level
        #
        tni = 0 # always use Tn classification for_castren

        # produces weighted difference vectors based on two sets
        # level == cardinality of found subsets
        # listed as: weight, SC

        x, y = self._difGroup(forteX, forteY, tni, level)

        # matches all dif vectors in_each group, calculates weight
        # n must be one less than current level
        # listed as: SCX, SCY, weight
        
        sub_group = self._crossGroup(x, y, 0, level-1)

        # each pair of sets in_new_group needs to calc dif group, and_then 
        # produce a new_group

        return sub_group

    def _castrenBranch(self, forteX, forteY, branch):

        if branch == 4:
            

            level = branch
            key = (level,)
            temp = self._castrenLevel(forteX, forteY, level)

            Dict = {}
            Dict[key] = temp

            level = level - 1
            counter = 0
            for sc_x, sc_y, weight in Dict[key]:
                temp = self._castrenLevel(sc_x, sc_y, level)              
                key = (level, counter)
                Dict[key] = temp
                counter = counter + 1

            # my levels are different than castren's

            lvl_3_keys = [] 
            lvl_4_keys = [] 
            h = Dict.keys()
            h.sort()
            for key in h:
                if key[0] == 3:
                    lvl_3_keys.append(key) 
                elif key[0] == 4:
                    lvl_4_keys.append(key) 
            

            lvl_3_sums = []
            for key in lvl_3_keys:
                temp = 0
                for sc_x, sc_y, vW in Dict[key]:
                    temp = temp + vW
                lvl_3_sums.append(temp)

            lvl_4_sums = []
            for key in lvl_4_keys:
                temp = 0
                index = 0
                for sc_x, sc_y, vW in Dict[key]:
                    temp = (vW * lvl_3_sums[index]) / 100.0
                    lvl_4_sums.append(temp)

            lvl_top = self.castren_pRel((7,35), (4,22,1), 0, branch)
            lvl_4_tot = self._sumVector(lvl_4_sums)

            branch_value = (lvl_top * lvl_4_tot) / 100.0

        return branch_value

    #---------------------||||||||||||--  
    # general interface for analysis measures
    def analysis(self, method, scX, scY, tni):
        """ check if its a scTriple or a set object
        may raise a divide by zero error
        """
        assert method in self.analysisDict.keys()

        if hasattr(scX, 'get') and hasattr(scY, 'get'):
            return self.analysisDict[method](scX.get('sc'), scY.get('sc'), tni)
        elif drawer.isList(scX) and drawer.isList(scY):
            return self.analysisDict[method](scX, scY, tni)
        else:
            raise ValueError, 'incorrect data format for analysis'

    def analysisRange(self, method, data=None):
        """get info on analyis ranges striped from the doc attribute
        if no data requested, info returned as a list
        """
        rl = eval(self.analysisDict[method].__doc__)
        rDict = {}
        if rl == 0 or rl == None:
            rDict['min'] = 0.0 # defaults
            rDict['max'] = 1.0
            rDict['avg'] = None
            rDict['val'] = None # values
        else:
            rDict['min'] = rl[0]
            rDict['max'] = rl[1]
            rDict['avg'] = rl[2]
            rDict['val'] = rl[3]
        return rDict

    def analysisRangeStr(self, method, w=12):
        rDict = self.analysisRange(method)
        sideRange = (w - 2) / 2 
        rString = (str(rDict['min']).rjust(sideRange) + '--' + 
                      str(rDict['max']).ljust(sideRange))
        return rString

    def analysisNames(self):
        return self.analysisDict.keys()

#-----------------------------------------------------------------||||||||||||--

class Multiset:
    """object of a set which may be interpreted as a set
    pcs, ps, or setclass. order and multiplcity may or may not matter
    thus it is called a multiset
    object orientated structure
    """
    
    def __init__(self, psRealSrc=None, scTriple=None, scObj=None):
        """ store scObj for reference
        _psRealSrc is stored as original data entered; not transposed or changed
        and should not be read as data
        scTriple stores forte name as data strcuture
        must be update for all changes
        psList is the internal data representation
        """
        if scObj == None:
            scObj = SetClass()
        self.scObj = scObj
        self.forms = ('midi', 'psReal', 'psName', 'pch', 'fq', 'pc', # pitch obj
                          'sc', 'dur', 'normal', 'mason', 'card') 
                          # sone only found in Multiset
        # it is questionable if the t is still required
        # stores transposition away from normal form, and accumulates other
        # transpositions
        self.tRef = 0
        self.dur     = 1 # a value for durational weighting, default

        if psRealSrc != None and scTriple != None: # both given
            self._psRealSrc = psRealSrc
            self._scTriple = scTriple

        elif psRealSrc != None and scTriple == None: # only ps given
            self._psRealSrc = psRealSrc
            normData = findNormalT(self._psRealSrc)
            if normData == None: # an erro has happend
                #print 'problem w/', _psRealSrc
                raise error.MultisetError # cancel set
            self._scTriple, self.tRef = normData

        elif psRealSrc == None and scTriple != None: # only sc given
            self._scTriple = scTriple
            self._psRealSrc = self.scObj.pcs(self._scTriple)
        else: # if both None
            raise error.MultisetError
            
        self._psList = [] # a list of pitch objects
        for value in self._psRealSrc: # must be psReal values
            self._psList.append(pitchTools.Pitch(value, 'psReal'))
        # store cardinality
        # removed as redundant; use get
        # self.card = self._scTriple[0]

    #------------------------------------------------------------------------||--
    # data representation
    def _reprListData(self, listData, outer=1):
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


    def repr(self, type='psReal', outer=1):
        """displays a Multiset; outer determines if paranethesis are incl
        """
        # first look for representations that are lists of other data
        if type in ('psReal', 'psName', 'pc', 'midi', 'pch', 'fq'):
            msgList = []
            for pitch in self._psList:
                str = pitch.repr(type)
                msgList.append(str)
            return self._reprListData(msgList, outer)
        # representations that are single values
        elif type == 'dur': # not really needed
            return '%s' % self.dur

        elif type == 'sc':
            # scToStr method should be moved inside this class
            return scToStr(self._scTriple)

        elif type == 'normal':
            normalList = self.scObj.pcs(self._scTriple)
            return self._reprListData(normalList, outer)

        elif type == 'prime':
            # strip inversion info from scTriple, default gets prime
            normalList = self.scObj.pcs(self._scTriple[0:2])
            return self._reprListData(normalList, outer)

        elif type == 'icv':
            return self._reprListData(self.icv())

        elif type == 'var':
            return self._reprListData(self.var())

        elif type == 'ref': # returns a list of strings
            refDict = self.refData()
            msgLines = []
            if refDict == None:
                return None
            else:
                for key in refDict.keys():
                    msgLines.append(', '.join(refDict[key]))
                return msgLines
 
        elif type == 'refNames': # return a str of ref names
            refDict = self.refData()
            if refDict == None:
                return None
            else:
                refDict = self.refData()
                if refDict.has_key('name'):
                    return ', '.join(refDict['name'])
                else:
                    return None

        elif type == 'tRef':
            return '%s' % self.tRef

        else:
            raise ValueError, 'bad representation format'

    def __str__(self):
        """default string representation is as 'psReal'"""
        return self.repr()
    
    #------------------------------------------------------------------------||--
    # data entry, updating
    def setDur(self, value):
        self.dur = value

    def setT(self, value):
        """for setting a tRef on load or otherwise"""
        self.tRef = value

    def __setitem__(self, key, value):
        self._psList[key] = value
        self._update()

    def __contains__(self, item):
        """item to test is a set obj"""
        if item in self._psList:
            return 1
        else:
            return 0

    def __delitem__(self, key):
        # key is in the order position
        del self._psList[key]
        self._update()

    def __getitem__(self, key):
        self._update()
        return self._psList[key]

    #------------------------------------------------------------------------||--
    # data access
    def __len__(self):
        return len(self._psList)

    def _access(self, name):
        """output data in the appropriate format
        does not change internal data representation
        """
        if name == 'sc': # not an attribute of pitch objects
            return self._scTriple
        elif name == 'dur': # not an attribute of pitch objects
            return self.dur
        elif name == 'normal': # not an attribute of pitch objects
            return self.scObj.pcs(self._scTriple)
        elif name == 'mason':
            pcList =     []
            for pitch in self._psList:
                pcList.append(pitch.get('pc'))
            return psSetToMason(pcList) # returns an int
        elif name == 'card': # get cardinality
            return self._scTriple[0]
        dataList = []
        for pitch in self._psList:
            dataList.append(pitch.get(name))
        return tuple(dataList)

#     def __getattr__(self, name):
#         """this method of data access should no longer be used"""
#         if name not in self.forms:
#             #print 'Multiset: invalid request for', name
#             raise AttributeError
#         return self._access(name) # convert to appropriate data and return

    def get(self, name):
        if name not in self.forms:
            raise ValueError, 'bad format requested'
        return self._access(name) # convert to appropriate data and return

    # sc analysis measures
    def var(self):
        return self.scObj.var(self._scTriple)
    def icv(self):
        return self.scObj.icv(self._scTriple)
    def cv(self, n):
        return self.scObj.cv(self._scTriple, n)
    def xv(self, n):
        return self.scObj.xv(self._scTriple, n)

    def z(self): # returns none if no data
        return self.scObj.zData(self._scTriple)
    def zObj(self):
        """return a new set object for the z related set"""
        if self.z() != None:
            return Multiset(None, self.z(), self.scObj)
        else:
            return None

    def refData(self):
        return self.scObj.refData(self._scTriple)

    def superSet(self, setRange='all', tniMode=0):
        """returns raw triples w/ searchResults, valueDict
        if match is given, looks for scTriple to match, returns truth
        else returns list of tuples"""
        searchResults, valueDict = self.scObj.findSuperSets(self._scTriple, 
                                                                            'all', tniMode)
        return searchResults, valueDict

    def rawData(self, key):
        """raw data via key"""
        return self.scObj.rawSetData(self._scTriple[0], self._scTriple[1],
                                              self._scTriple[2], key)

    #------------------------------------------------------------------------||--
    # data transformations

    def _update(self):
        """update scTriple in the case that pitches have chaned,
        via inversion or replacement
        """
        normData = findNormalT(self._access('psReal'))
        if normData == None: # an erro has happend
            print 'SC.py: _update: problem w/', self._access('psReal')
            raise error.MultisetError
        self._scTriple, self.tRef = normData
        # this was removed as redundant
        #self.card = self._scTriple[0]

    def t(self, value):
        """transpose each pitch objectin pitch space
        """
        for pitch in self._psList:
            pitch.t(value)
        self.tRef = self.tRef + value # update transpositon counter

    def tMod(self, value):
        """trasnpose w/in modulus, retain octave"""
        for pitch in self._psList:
            pitch.tMod(value)
        self.tRef = self.tRef + value # update transpositon counter

    def i(self, axis=None):
        """ps inversions, value is the axis
        value can be used to shift inversion"""
        if axis == None: # shift around the first note in the series
            axis = self._psList[0].get('psReal')
        for pitch in self._psList:
            pitch.i(axis)
        self._update() # sc may have changed

    def iMod(self, axis=0):
        """inversions, w/in moduls, retain octave
        axis can be a floating point value like 1.5 for certain inversions"""
        for pitch in self._psList:
            pitch.iMod(axis)
        self._update() # sc may have changed

    def retro(self):
        self._psList.reverse()

    def slice(self):
        pass
    
    def rotate(self, newZero):
        """rotate multiset
        note: this is a rotation in place; this does not take register
        into account, only pitch order"""
        if newZero == 0: return 
        
        psLen = len(self._psList)

        if newZero > 0: # map as positive mod
            newZero = newZero % psLen
        if newZero < 0: # map as negative mod
            newZero = newZero % -psLen

        if newZero > 0: # map as positive mod
            self._psList = (self._psList[newZero:psLen] + 
                                    self._psList[0:newZero])
        if newZero < 0: # map as negative mod
            self._psList = (self._psList[psLen+newZero:psLen] + 
                                    self._psList[0:psLen+newZero])


    def rotateOctave(self, newZero):
        """rotate multiset
        assume that new zero is the lowest pitch in the set
        transpose pitches as necessary
        """
        if newZero == 0: return 
        psLen = len(self._psList)
        if psLen == 0: return

        self.rotate(newZero) # do standard rotatioin

        # the first pitch should always be the lowest pitch
        if newZero > 0: # map as positive mod
            for i in range(1, psLen): # must be greater than 1
                while self._psList[i].get('psReal') < self._psList[0].get('psReal'):
                    self._psList[i].t(12) # transpose up one octave
        # take new first pitch down an octave
        # the first pitch should then always be the lowest pitch
        if newZero < 0: # map as positive mod
            self._psList[0].t(-12)
            for i in range(1, psLen): # must be greater than 1
                # continue to check for pitches below the first pitch
                while self._psList[i].get('psReal') < self._psList[0].get('psReal'):
                    self._psList[i].t(12) # transpose up one octave

    def spaceOctave(self, shift=1):
        """simple method of spacing pitches be increasing or decreasing octaves
        does not take into account existing octave positions"""
        if shift == 0: return # no change
        for i in range(len(self._psList)):
            # for each pitch in the set, add an additional octave shift
            # for each new pitch, an additional shift unit of octaves is added
            self._psList[i].t(12 * shift * i) # shift may be negatives


    def copy(self):
        obj = Multiset(self._access('psReal'), self._scTriple, self.scObj)
        obj.dur = copy.deepcopy(self.dur)
        obj.tRef = copy.deepcopy(self.tRef)
        return obj

#-----------------------------------------------------------------||||||||||||--
class MultisetFactory:
    """object to handle getting a set from a user
    sortif a MultiSet factory, for producing objects
    """
    def __init__(self):
        pass
        # scObj provided w/ call

    def _parseSetInputType(self, usrStr, termObj):
        """determine which set input is being provided by user
        termObj may be None; if not interactive, not allow import
        """
        usrStr = drawer.strScrub(usrStr, 'L')
        for char in usrStr:
            if char in ['@','&', '|',]: # removed ,'(',')'
                return 'sieve'
        # if a complete user string, get a file dialog
        if usrStr in ['file', 'import', 'spectrum']:
            if not termObj.interact: return None # cant import w/ not interactive
            return 'import'
        if usrStr.find('.txt') >= 0: # assume its a file path
            return 'txt' # import a spectrum
        if usrStr.find('m') >= 0:
            return 'midi'
        if usrStr.find('hz') >= 0 or usrStr.find('fq') >= 0:
            return 'fq'
        # the first character of a set class must always be a number
        # 10, 11, and 12 should be in this list, but requires two characters
        # there must be a dash (not leading), no comas, no periods, 
        if (usrStr[0] in ['1','2','3','4','5','6','7','8','9',] and
            usrStr.find('-') != -1 and usrStr.find(',') == -1 and
            usrStr.find('.') == -1 and usrStr[0] != '-'):
            # no other characters should be in this
            return 'forte'
        else:
            for char in usrStr.lower(): # check if it has characters
                if char in pitchTools.REFdiaNameToPc.keys():
                    return 'psName'
            return 'psReal' # assume pset numbers

    def _parseForte(self, usrStr):
        """decifer a user-entered forte value"""
        #usrStr = self._scrubUsrStr(usrStr)
        #true if string has dash, no commas, no periods: is forte 
        scFound = None
        if usrStr.find('b') != -1:
            inv = -1
            usrStr = usrStr.replace('b', ' ')
        else:
            inv = 1 #this value may not be correct, is checked later on
            usrStr = usrStr.replace('a', ' ')
        usrStr = usrStr.replace('-', ' , ')     #replace dash with comma
        try:
            rawForte = eval(usrStr)
        except (NameError, SyntaxError):
            raise error.MultisetError
        if rawForte[0] < 1 or rawForte[0] > 12:
            raise error.MultisetError
        elif rawForte[1] > TNIMAX[rawForte[0]]:
            raise error.MultisetError
        else: # successfil asignment
            scFound = self.scObj.forteToSc(rawForte[0], rawForte[1], inv)
        return scFound

    def _parsePsName(self, usrStr):
        """convert a list of pitch names to a ps
        middle c == c4 == midi 60 == 0
        """
        #usrStr = self._scrubUsrStr(usrStr)
        usrList = drawer.strToListFlat(usrStr, 'L')
        psList = []
        for elem in usrList: # may be int or float
            elem = drawer.strScrub(elem)
            if elem == '': continue
            elif elem[0] not in pitchTools.REFdiaNameToPc.keys():
                continue
            else: # this should never raise an error
                psList.append(pitchTools.psNameToPs(elem))
        return psList
        
    def _parseMidi(self, usrStr):
        """conver midi values to psInt values"""
        usrStr = drawer.strStripAlpha(usrStr)
        usrList = drawer.strToListFlat(usrStr, 'L')
        #usrList = usrStr.split(',')
        psList = []
        for elem in usrList: # may be int or float
            elem = drawer.strToNum(elem.strip(), 'num')
            if elem == None: continue
            else: psList.append(pitchTools.midiToPs(elem))
        return psList
        
    def _parseFq(self, usrStr):
        """conver midi values to psInt values"""
        usrStr = drawer.strStripAlpha(usrStr)
        usrList = drawer.strToListFlat(usrStr, 'L')
        #usrList = usrStr.split(',')
        psList = []
        for elem in usrList: # may be int or float
            elem = drawer.strToNum(elem.strip(), 'num')
            if elem == None: continue
            else: psList.append(pitchTools.fqToPs(elem))
        return psList
        
    def _parsePsReal(self, usrStr):
        """process a usr string entered as a list psReals"""
        usrList = drawer.strToListFlat(usrStr, 'L')
        psList = []
        for elem in usrList: # may be int or float
            elem = drawer.strToNum(elem.strip(), 'num')
            if elem == None: continue
            else: psList.append(elem)
        return psList

    def _parseSieve(self, usrStr):
        try:
            sieveObj = sieve.SievePitch(usrStr)
            psSet = sieveObj()
        except (SyntaxError, ValueError, TypeError, 
                  KeyError, error.PitchSyntaxError):
            raise error.MultisetError
        if psSet == []: # no values in this seive segment
            raise error.MultisetError
        return psSet
        
    def _parseTxt(self, usrStr, count=None):
        """convert a text file commulative spectrum"""
        # usrstr is a file path
        try:
            specObj = spectral.SpectrumData(usrStr)
            psSet = specObj.getPitch('psReal', count)
        except (ValueError, IOError):
            raise error.MultisetError
        if psSet == []: # no values in this seive segment
            raise error.MultisetError
        return psSet
        
    def _getCount(self, termObj):
        """get number of pitches to read interactively"""
        query = 'number of pitches?'
        while 1:
            usrStr = dialog.askStr(query, termObj)
            if usrStr == None: return None
            num = drawer.strToNum(usrStr, 'int')
            if num != None and num != 0: return num
            else:
                dialog.msgOut(('%senter a positive or negative integer.\n' % 
                    lang.TAB), termObj)          
        
        
    def _makeObj(self, ao=None, read=None, scObj=None):
        """ returns sc, pcset, trans from 0=C, and inv
        read arg allows non-interactive use: provide data as arg
        can be used to replace calls to getSet
        pass an ao to get references and termObj
        """
        if ao != None:
            termObj = ao.termObj
            dlgVisMet = ao.external.getPref('athena', 'dlgVisualMethod')
            fpLastDir = ao.fpLastDir
        else: # get defaults
            termObj = None
            dlgVisMet = 'txt'
            fpLastDir = ''
        if scObj == None:
            scObj = SetClass()
        self.scObj = scObj
        
        attempts = 0
        usrStrType = None # not yet known what format user provided
        while 1:
            if read != None: # method must return result, not interactive
                if attempts > 0: return None # dont run more than once when reading
                usrStr = read # assign to usrStr for parsing
            else:
                usrStr = dialog.askStr(lang.msgSCgetSet, termObj)
                if usrStr == None: return None
            attempts = attempts + 1
            usrStrType = self._parseSetInputType(usrStr, termObj)
            # may get one or the other of these as input values
            scFound = None
            psSet = None
            try:
                if usrStrType == 'forte':
                    scFound = self._parseForte(usrStr)
                elif usrStrType == 'psName':
                    psSet = self._parsePsName(usrStr)
                elif usrStrType == 'psReal':
                    psSet = self._parsePsReal(usrStr)
                elif usrStrType == 'sieve':
                    psSet = self._parseSieve(usrStr)
                elif usrStrType == 'midi':
                    psSet = self._parseMidi(usrStr)
                elif usrStrType == 'fq':
                    psSet = self._parseFq(usrStr)
                elif usrStrType == 'txt':
                    psSet = self._parseTxt(usrStr)
                # import will get a file dialog
                elif usrStrType == 'import':
                    msg, ok = dialog.promptGetFile(lang.msgSCgetAudacity, 
                                             fpLastDir, 'file', dlgVisMet, termObj)
                    count = self._getCount(termObj) # count may be equal to None
                    # call parse text after getting file path
                    if ok: psSet = self._parseTxt(msg, count)
                    else: return None # cancel
                else: return None
            except error.MultisetError:
                dialog.msgOut(lang.msgSCnoSuchSet, termObj)
                continue
            try:
                obj = Multiset(psSet, scFound, self.scObj)
            except error.MultisetError:
                return None # will be understood as error

            if read == None: # dont check response
                sc = obj.repr('sc')
                ps = obj.repr('psName')
                query = lang.TAB + 'SC %s as %s? ' % (sc, ps)
                ok = dialog.askYesNoCancel(query, 1, termObj)               
                if ok != -1 and ok != 1:  continue  # return to top
                elif ok == -1: return None # destroy obj    
            return obj

    def __call__(self, termObj=None, read=None, scObj=None):
        return self._makeObj(termObj, read, scObj)

    def getRange(self, setRange='all', tni=0, scObj=None):
        """return a list w/ all sets returned as objects
        scObj os required for opperation
        """
        if scObj == None:
            scObj = SetClass()
        self.scObj = scObj

        objList = []
        for scTriple in self.scObj.getAllScTriples(setRange, tni):
            objList.append(Multiset(None, scTriple, self.scObj))
        return objList

    def getAllZ(self, setRange='all', tni=0, scObj=None):
        """return a list of all Z set objects
        scObj required"""
        if scObj == None:
            scObj = SetClass()
        self.scObj = scObj

        objList = []
        for scTriple in self.scObj.findAllZ(setRange, tni):
            objList.append(Multiset(None, scTriple, self.scObj))
        return objList

    def getAllSuperset(self, searchSetObj, setRange='all', tni=0, scObj=None):
        """return a list of all set objects that match search
        scObj required"""
        if scObj == None:
            scObj = SetClass()
        self.scObj = scObj

        searchResults, valueDict = searchSetObj.superSet(setRange, 0)
        objList = [] # transform search results into objects
        for scTriple in searchResults:
            objList.append(Multiset(None, scTriple, self.scObj))
        return objList, valueDict


    def getRef(self, searchStr, refType, setRange='all', tni=0, scObj=None):
        """return a list of all set objects that match search
        scObj required"""
        if scObj == None:
            scObj = SetClass()
        self.scObj = scObj

        objList = []
        resultList = self.scObj.findRef(searchStr, refType, setRange, tni)
        if resultList != None:
            for scTriple in resultList:
                objList.append(Multiset(None, scTriple, self.scObj))
        return objList # ordered list by incidence



#-----------------------------------------------------------------||||||||||||--
# no longer used
# def getSet(termObj=None, read=None, scObj=None):
#     """functional interface for object creation"""
#     # emulates old getSet method of SC
#     interObj = MultisetFactory()
#     obj = interObj(termObj, read, scObj)
#     if obj == None: # error
#         return None
#     else:
#         return obj.get('sc'), obj.get('psReal'), obj.tRef

# no long used, and collides w/ baseTexture method
# def getMultiset(termObj=None, read=None, scObj=None):
#     """functional interface for object creation"""
#     # emulates old getSet method of SC
#     interObj = MultisetFactory()
#     return interObj(termObj, read, scObj) # may be None on error


#-----------------------------------------------------------------||||||||||||--

def getPitch(termObj=None, read=None):
    while 1:
        if read != None:
            usrStr = read
        else:
            usrStr = dialog.askStr("enter a pitch or note name:", termObj)
            if usrStr == None:
                return None
        usrStr = usrStr.lower() # make sure lower case
        try:
            obj = pitchTools.Pitch(usrStr)
        except error.PitchSyntaxError: 
            if read != None:    
                return None # failure
            dialog.msgOut('%sno such pitch exists.\n' % lang.TAB, termObj)
            continue
        return obj

#-----------------------------------------------------------------||||||||||||--



class Test:
    def __init__(self):
        self.testMultisetData()

    def testMultisetData(self):
        demo = ((2,-5,3,5),(3.06,4.25,8.002),(34,),
                    (7,9,4,5,6,4,3,2,4,5,3,3,3))
        for set in demo:
            obj = Multiset(set)
            print '\n', obj, len(obj), obj.get('card')
            for form in obj.forms:
                print form, obj.repr(form)
                print getattr(obj, form)

    def testMultisetTrans(self):
        pass
    
if __name__ == '__main__':
    Test()


