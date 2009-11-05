#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          MC.py
# Purpose:       map class object used for all map processing.
#                    gets data from MCdata.py
#                    based on modle by Joseph N. Straus
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

                      
#smoothness
#smoothness vector: 7 registers
#uniformity
#uniformity vector: UV: 12 registers
#balance
#balance vector: 12 registers

#-----------------------------------------------------------------||||||||||||-- 
#-----------------------------------------------------------------||||||||||||-- 
import copy
from athenaCL.libATH import dialog
from athenaCL.libATH import drawer
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import SC
from athenaCL.libATH import pitchTools
from athenaCL.libATH import MCdata

vlMapDict = MCdata.vlMapDict    # table of all voice maping

_MOD = 'MC.py'

#-----------------------------------------------------------------||||||||||||-- 

# formats used here
# 




class MapClass:
    """utility functions for map class operations
    """
    def flipMap(self, sourceMap):
        """reverses the direction of a map, from Large-to-small, to small-to-large
        length of map is number of positions in the source
        """
        sourcePos = len(sourceMap)   

        noDifVal         = 0                
        difValBasket = []
        for entry in sourceMap:
            if drawer.isList(entry):  # not an int
                for sub_entry in entry:
                     if sub_entry in difValBasket:
                         pass
                     else:
                         difValBasket.append(sub_entry)
            else:
                if entry in difValBasket:
                    pass
                else:
                    difValBasket.append(entry)
        difValBasket.sort()
        # number of different values is the number of positions in the destination
        destinationPos = len(difValBasket) 

        if sourcePos == destinationPos:
            # if these are equal no flip necessary
            return sourceMap         
        elif sourcePos > destinationPos:
            flipedMap = []
            # this is case where going from larger to smaller set. 
            #this is the form that the map dictionary uses for reference
            for val in difValBasket:
                # find register positions for each value in the basket. 
                # there will be more than one
                tempImbedList = []
                #if sp is > destP we do not need to check for imbedded tuples
                indexCount = 0
                for entry in sourceMap: 
                    if entry == val:
                        tempImbedList.append(indexCount)
                    indexCount = indexCount + 1
                if len(tempImbedList) > 1:
                    newMapEntry = tuple(tempImbedList)
                else:
                    newMapEntry = tempImbedList[0]
                flipedMap.append(newMapEntry)
        else: # destination Pos > source Position
            flipedMap = []
            # construct an empty map
            newMapNoRegisters = destinationPos
            for entry in difValBasket:
                flipedMap.append(0)
            indexCount = 0
            for entry in sourceMap:
                if drawer.isList(entry):  # not an int
                    for sub_entry in entry:
                        flipedMap[sub_entry] = indexCount
                else:
                    flipedMap[entry] = indexCount
                indexCount = indexCount + 1

        flipedMap = tuple(flipedMap)
        return flipedMap

    #------------------------------------------------------------------------||--
    # data access
    def _getMapSrcDstSize(self, sourceMap):
        #length of map is number of positions in the source
        sourcePos = len(sourceMap)   

        noDifVal         = 0                
        difValBasket = []
        for entry in sourceMap:
            if drawer.isList(entry):  # not an int
                for sub_entry in entry:
                     if sub_entry in difValBasket:
                         pass
                     else:
                         difValBasket.append(sub_entry)
            else:
                if entry in difValBasket:
                    pass
                else:
                    difValBasket.append(entry)
        difValBasket.sort()
        # number of different values is the number of positions in the destination
        destinationPos = len(difValBasket)
        return sourcePos, destinationPos


    def getMapDict(self, srcSize, dstSize):
        """returns a dictionary of index numbers : map pairs for the given sizes. 
            these are not sorted, and index numbers are only for permanent 
            reference to source
        """
        if (srcSize > 6 or srcSize < 1 or 
            dstSize > 6 or srcSize < 1):
            return None # returns None as error code
        # no change nec, this is the format of the map dictionary
        if srcSize >= dstSize: 
            return vlMapDict[(srcSize, dstSize)]
        else:    # need to flip all the maps in the reverse dictionary
            # must reverse these to get a dict to then reverse the mappings of
            sourceDict = vlMapDict[(dstSize, srcSize)]  
            newDict   = {}
            for key in sourceDict.keys():
                map = sourceDict[key]
                newMap = self.flipMap(map)
                newDict[key] = newMap
            return newDict

    def getNoMaps(self, srcSize, dstSize):
        """return possible maps between any two sizes"""
        map = self.getMapDict(srcSize, dstSize)
        if map == None: return None
        else:
            return len(map.keys())


    def getSingleMap(self, srcSize, dstSize, mapIndexNo):
        # a single map corrolating to the index and size args
        # map index numbers stat at 1, not at 0
        if (srcSize > 6 or srcSize < 1 or 
            dstSize > 6 or srcSize < 1):
            return -1
        # no change nec, this is the format of the map dictionary
        if srcSize >= dstSize: 
            try:
                map = vlMapDict[(srcSize, dstSize)][mapIndexNo]
            except:
                return -1
        else:    # need to flip all the maps in the reverse dictionary
            try:
                # must reverse these to get a dict to then reverse the mappings
                sourceMap = vlMapDict[(dstSize, srcSize)][mapIndexNo]
            except:
                return -1
            map = self.flipMap(sourceMap)
        return map

    def fetchMap(self, mapIdTuple):
        srcSize = mapIdTuple[0]
        dstSize = mapIdTuple[1]
        mapIndexNo = mapIdTuple[2]
        return self.getSingleMap(srcSize, dstSize, mapIndexNo)

    #------------------------------------------------------------------------||--

    def mapIdTupleToString(self, mapIdTuple):
        srcSize = mapIdTuple[0]
        dstSize = mapIdTuple[1]
        mapIndexNo = mapIdTuple[2]
        return '%i:%i-%i' % (srcSize,dstSize,mapIndexNo)


    def rawMapToString(self, rawMap):
        ### returns map as string with letters
        translationDict = {0 : 'a',
                                 1 : 'b',
                                 2 : 'c',
                                 3 : 'd',
                                 4 : 'e',
                                 5 : 'f' }
        msg = '('
        # length of map is number of positions in the source
        sourcePos = len(rawMap)
        for entry in rawMap:
            if drawer.isList(entry):  # not an int
                msg = msg + '('
                for sub_entry in entry:
                     msg = msg + translationDict[sub_entry]
                msg = msg + ')'
            else:
                msg = msg + translationDict[entry]
        msg = msg + ')'
        return msg

    def stringToMap(self, stringMap):
        """assumes that strings is a comma separated list of maps"""
        goodMap = 0
        goodKey = 0
        # takes a string and returns a mapTuple Id, if the map exists
        translationDict = {'a' : '0',
                                 'b' : '1',
                                 'c' : '2',
                                 'd' : '3',
                                 'e' : '4',
                                 'f' : '5' }
        for letter in translationDict.keys():
            stringMap = stringMap.replace(letter, translationDict[letter])
        try:
            newMap = eval(stringMap)
        except:
            return None
        srcSize, dstSize = self._getMapSrcDstSize(newMap)
        mapDict = self.getMapDict(srcSize, dstSize)
        if mapDict == None: return None
        for key in mapDict.keys():
            if mapDict[key] == newMap:
                goodMap = 1
                goodKey = key
        if goodMap != 1: return None
        ### map is good, return it
        return (srcSize, dstSize, goodKey) 


    #------------------------------------------------------------------------||--
    def genVlPairs(self, pcsX, pcsY, map):
        # generates one vl pair set for single map (takes rawmap, not mapTupleId)
        # this method does not check for the appropriate map; should be 
        # checked elsewhere
        srcSize = len(pcsX)
        #length of map is number of positions in the source, i.e. size
        sourcePos = len(map) 
        
        srcPosCount = 0
        vlTuples = []
        for mapEntry in map:
            if drawer.isList(mapEntry):
                for sub_entry in mapEntry:
                    sourcePC = pcsX[srcPosCount]
                    destinationPC = pcsY[sub_entry]
                    vlTuples.append((sourcePC, destinationPC))                  
            else:
                sourcePC = pcsX[srcPosCount]
                destinationPC = pcsY[mapEntry]
                vlTuples.append((sourcePC, destinationPC))
            srcPosCount = srcPosCount + 1
        return tuple(vlTuples)


    def genSingleVlDiagram(self, pcsX, map):
        # map here is a raw map, not an idTuple
        # returns a dictionary of numbered rows, with pcsX and its next 
        # movement as strings
        translationDict = {0 : 'a',
                                 1 : 'b',
                                 2 : 'c',
                                 3 : 'd',
                                 4 : 'e',
                                 5 : 'f' }
        rowDict = {0 : [],
                      1 : [],
                      2 : [],
                      3 : [],
                      4 : [],
                      5 : [] }

        srcPosCount = 0
        for mapEntry in map:
            if drawer.isList(mapEntry):
                mapTranslated = []
                for sub_entry in mapEntry:
                    mapTranslated.append(translationDict[sub_entry])
                stringMap = ''
                for letter in mapTranslated:
                    stringMap = stringMap + '%s' % letter
                mapTranslated =  stringMap #+ ')'
                rowDict[srcPosCount].append(pcsX[srcPosCount])
                rowDict[srcPosCount].append(mapTranslated)
             
            else:
                mapTranslated = translationDict[mapEntry]
                rowDict[srcPosCount].append(pcsX[srcPosCount])
                rowDict[srcPosCount].append(mapTranslated)

            srcPosCount = srcPosCount + 1
        
        keyList = rowDict.keys()
        keyList.sort()
        for key in keyList:
            if len(rowDict[key]) == 0:
                rowDict[key] = ' ' * 9  # 9 spaces for spacer
            else:
                sourcePCS, mapToPosition = rowDict[key]
                stringEntry = '%s %s' % (str(sourcePCS).rjust(2),
                                                     mapToPosition.ljust(6))
                rowDict[key] = stringEntry
        return rowDict


    def genDoubleVlDiagram(self, pcsX, pcsY, map):
        """ returns a dictionary of numbered rows, 
             with pcsX and its next movement as strings
        """
        rowDict = self.genSingleVlDiagram(pcsX, map)
        rowKeys = rowDict.keys()
        
        for i in range(0,len(pcsY)):
            if len(rowDict[i]) == 0:
                pass
            else:
                rowDict[i] = rowDict[i] + '%s' % str(pcsY[i]).rjust(2)
        return rowDict      

    #------------------------------------------------------------------------||--
    def getAllVl(self, pcsX, pcsY):
        """returns a dictionary of key : ((), ()) vl tuple paris,  pcsX and pcsY 
        can be of any size =< 6; the key is the same as the mapDict key
        """
        if len(pcsX) > 6 or len(pcsX) < 1 or len(pcsY) > 6 or len(pcsY) < 1:
            return 'pcs of this size are not supported'

        vlDict = {}
        srcSize = len(pcsX)
        dstSize = len(pcsY)
        mapDict = self.getMapDict(srcSize, dstSize)

        for key in mapDict.keys():
            map = mapDict[key]
            vlPairs = self.genVlPairs(pcsX, pcsY, map)
            vlDict[key] = vlPairs
        return vlDict


    def genMapFromVlPairs(self, rawVlPairs, pcsX, pcsY):
        """analizes vl pairs with appropriate pcsX and y and finds correct map
        pcs should be a tuple and not a list
        """
        # returns -1 on error
        # NOTE! in some cases of dif sized boundaries this function will not 
        # identify a vlPair b/c of a slitting or merging pair being in the 
        # wrong internal (embedded) order. this hould be fixed in the future
        foundPcsX = []
        foundPcsY = []
        # test pcsY is sorted so as to comparte to the extracted pcsY and test 
        # for eq dont know referential ordering of pcsY, so must sort and then 
        # comparte to prove eq
        
        # added to anticipate strange error found from bug report
        #if None in rawVlPairs: return -1 # something went wrong
        
        pcsXconstituents = []
        pcsYconstituents = []
        for entry in pcsX:
            if entry in pcsXconstituents:
                pass
            else:
                pcsXconstituents.append(entry)
        for entry in pcsY:
            if entry in pcsYconstituents:
                pass
            else:
                pcsYconstituents.append(entry)
        pcsXconstituents.sort()
        pcsYconstituents.sort()
        testPcsY = copy.copy(pcsY)
        testPcsY = list(testPcsY)
        testPcsY.sort()

        # rawVlPairs should alwas been in the order of pcsX, from top to bottom
        for pair in rawVlPairs:
            foundPcsX.append(pair[0])
            foundPcsY.append(pair[1])
        foundPcsX = tuple(foundPcsX)
        testFoundPcsY = copy.copy(foundPcsY)
        testFoundPcsY.sort()
        foundPcsY = tuple(foundPcsY)
        
        foundPcsXconstituents = []
        foundPcsYconstituents = []
        for entry in foundPcsX:
            if entry in foundPcsXconstituents:
                pass
            else:
                foundPcsXconstituents.append(entry)
        for entry in foundPcsY:
            if entry in foundPcsYconstituents:
                pass
            else:
                foundPcsYconstituents.append(entry)
        foundPcsXconstituents.sort()
        foundPcsYconstituents.sort()

        # every elemen in the pcs must be represented in the found; qunatity, 
        # thought, does not matter
        if pcsXconstituents != foundPcsXconstituents: return -1
        if pcsYconstituents != foundPcsYconstituents: return -1

        srcSize = len(pcsX)
        dstSize = len(pcsY)
        foundMap = []
        # fill with 0s for source positions

        if srcSize == dstSize:
            if foundPcsX != pcsX: return -1
            if testFoundPcsY != testPcsY: return -1
        elif srcSize < dstSize:
            # if destination os larger, foundPCS will only match for Y
            if testFoundPcsY != testPcsY: return -1
        elif srcSize > dstSize:
            # if source is larger, foundPCS will only match for X
            if foundPcsX != pcsX: return -1

        rawVlPairs = tuple(rawVlPairs)
        vlPairDict = self.getAllVl(pcsX, pcsY)
        foundMapKey = 0
        for key in vlPairDict.keys():
            if vlPairDict[key] == rawVlPairs:
                foundMapKey = key
                break
        # search for single mistake made in rawVL if source<DEST
        if foundMapKey == 0:
            # if it does not eidentify a pair, it may still be there but entered 
            # in the wrong order
            if srcSize < dstSize:
                tempRawVlPairs = copy.copy(rawVlPairs)
                tempRawVlPairs = list(tempRawVlPairs) # user may have entered tuple
                for counter in range(0, len(tempRawVlPairs)):
                    if counter + 1 == len(tempRawVlPairs):
                        break
                    #check first postiion in this pair and next
                    if tempRawVlPairs[counter][0] == tempRawVlPairs[counter+1][0]: 
                        a = tempRawVlPairs[counter]
                        b = tempRawVlPairs[counter+1]
                        tempRawVlPairs = list(tempRawVlPairs)
                        tempRawVlPairs[counter]     = b
                        tempRawVlPairs[counter+1]   = a
                        tempRawVlPairs = tuple(tempRawVlPairs)
                        for key in vlPairDict.keys():
                            if vlPairDict[key] == tempRawVlPairs:
                                foundMapKey = key
                                break
                    if foundMapKey != 0:
                        # replace the original vlPairs with the new, corrected ones
                        rawVlPairs = tempRawVlPairs
                        break
                    else:
                        # restore original if no match made. 
                        #this will only correct 1 mistake, not two
                        tempRawVlPairs = copy.copy(rawVlPairs)
                        tempRawVlPairs = list(tempRawVlPairs)
            else: return -1  ## failed search
        # search for multiple mistakes in rawVL if source<DEST
        if foundMapKey == 0:
            # if it does not eidentify a pair, it may still be there but entered 
            # in the wrong order
            if srcSize < dstSize:
                tempRawVlPairs = copy.copy(rawVlPairs)
                # user may have entered tuple
                tempRawVlPairs = list(tempRawVlPairs) 
                for counter in range(0, len(tempRawVlPairs)):
                    if counter + 1 == len(tempRawVlPairs):
                        break
                    #check first postiion in this pair and next
                    if tempRawVlPairs[counter][0] == tempRawVlPairs[counter+1][0]:
                        a = tempRawVlPairs[counter]
                        b = tempRawVlPairs[counter+1]
                        tempRawVlPairs = list(tempRawVlPairs)
                        tempRawVlPairs[counter]     = b
                        tempRawVlPairs[counter+1]   = a
                        tempRawVlPairs = tuple(tempRawVlPairs)
                        for key in vlPairDict.keys():
                            if vlPairDict[key] == tempRawVlPairs:
                                foundMapKey = key
                                break
                    if foundMapKey != 0:
                        #   replace the original vlPairs with the new, corrected ones
                        rawVlPairs = tempRawVlPairs 
                        break
                    else:
                        # DONOT restore original if no match made. this will only 
                        # correct > 1 mistake, not 1
                        pass #tempRawVlPairs = copy.copy(rawVlPairs)     
            else: 
                return -1  ## failed search
        if foundMapKey == 0:
            return -1
        # returns a standard map partial ID for the given source dest. size
        # returns vl pairs because they may have been auto corrected
        # (srcSize, dstSize, foundMapKey)
        return (foundMapKey, rawVlPairs)

    #------------------------------------------------------------------------||--
    def displacement(self, srcSet, dstSet, posToTransform):
        """finds value of displacement between two sets
        position to transform is either 1 or 0, for second or first
        finds a new set that has maximal displacement
        """
        srcSize = len(srcSet)
        dstSize = len(dstSet)
        # dont care if inversion is the same, which it may be
        if posToTransform == 0:  # first set changes
            setToChangeP = srcSet
            setToChangeI = SC.psInverter(srcSet)
            setConstant  = dstSet
        # this is a PitchSpace inversion
        else:    # second set changes
            setToChangeP = dstSet
            setToChangeI = SC.psInverter(dstSet)
            setConstant  = srcSet

        setsToCompare = []
        for transInt in range(0,12):    ## all values 0 to 11
            pcsetTP = SC.pcSetTransposer(setToChangeP, transInt)
            pcsetTI = SC.pcSetTransposer(setToChangeI, transInt)    
            if pcsetTP == pcsetTI: # symmetrical set; dont need inversion
                setsToCompare.append((pcsetTP,transInt)) 
            else:
                setsToCompare.append((pcsetTP,transInt))
                setsToCompare.append((pcsetTI,transInt))
                
        minDispl = 9999  # init value very large
        maxDispl = 0  # init value very small
        allResults = []

        for setEntry in setsToCompare:
            tSet, transInt = setEntry # this set is setToCahnge
            if posToTransform == 0:  # first set changes
                SMTHdict, SMTHorderKey = self.sortSMTH(tSet, setConstant)
            else: # last set changes
                SMTHdict, SMTHorderKey = self.sortSMTH(setConstant, tSet)
            # get most smooth
            SMTHvector, SMTHdispl = SMTHdict[SMTHorderKey[0]]
            mapTupleId = (srcSize, dstSize, SMTHorderKey[0])
            scTupleID, dif = SC.findNormalT(tSet)                

            if SMTHdispl <= minDispl:
                minDispl = SMTHdispl             
            else:
                if SMTHdispl >= maxDispl:
                    maxDispl = SMTHdispl

            allResults.append((SMTHdispl, tSet, scTupleID, 
                                         transInt, mapTupleId))

        allResults.sort()     
        # list of four things: (1) smoothness displacement, (2) the pcs set (y) 
        # that was compared to x, (3) the set class of this set (3-11 obviously, 
        # but -1 is the inversion), (4) the transposition that was used, and (5) 
        # the map that was found as most smooth for that comparison

        #for line in allResults:
        #    print _MOD, line
        # does not matter what 'foundForm' is; could be the inverse of a 
        # forte inverse, which is a forte prime
        return minDispl, maxDispl, allResults, len(setsToCompare)

    #------------------------------------------------------------------------||--
    def getSetSizeBounds(self, query=None, termObj=None):
        """utility interactive command to get src, dest pair from the user
            if no query provided, one supplied
            if minimum can be set to 2 or 1"""

        if query == None:
            query = lang.msgMCenterVoiceRange
        while 1:
            sizeInput = dialog.askStr(query, termObj)
            if sizeInput == None or sizeInput == '':
                return None
            if sizeInput.find(':') != -1: # it has a ':'
                sizeInput = sizeInput.replace(':', ',')
            try:
                voiceSizes = eval(sizeInput)
                srcSize = voiceSizes[0]
                dstSize = voiceSizes[1]
            except:
                dialog.msgOut(lang.msgMCbadVoiceRange, termObj)     
                continue
            if (srcSize >= 1 and srcSize <= 6 and 
                dstSize >= 1 and dstSize <= 6 and 
                len(voiceSizes) == 2):
                break
            else:
                dialog.msgOut(lang.msgMCbadVoiceValue, termObj)     
                continue
        return srcSize, dstSize



    def _parseMapInputTupe(self, usrStr):
        """"determine type of map input
        possible: completeMap, rawMap, rawVlPairs, partialMap"""
        inputType = None
        # scan for types of input
        if usrStr.find('-') != -1 and usrStr.find(':') != -1:
            inputType = 'completeMap'
        # if the user has entered an incorrect format for a map class 
        # (only one -, or one :)
        elif usrStr.find('-') != -1 or usrStr.find(':') != -1: 
            # this means that we already have proper source and dest sizes
            return None # case 2
        elif usrStr.find(',') != -1 or usrStr.find('.') != -1:
            if (usrStr.find('a') != -1 or usrStr.find('b') != -1 or 
                 usrStr.find('c') != -1 or usrStr.find('d') != -1 or 
                 usrStr.find('e') != -1 or usrStr.find('f') != -1):
                # raw maps are notated with letters, like (a,b,c)
                inputType = 'rawMap'        
            else: 
                # raw vl pairs are notated with the ints of a pc class
                inputType = 'rawVlPairs'
        else: # case 3
            usrStr = drawer.strToNum(usrStr, 'int')
            if usrStr != None: # an integer
                inputType = 'partialMap'
            else:
                return None
        return inputType


    def _evaluateCompleteMap(self, usrStr, updateSrcDst, 
                                     srcSize, dstSize, termObj):
        """convert usrStrings that encode complete mapClass specificiations
        in the form 3:2-3 or the like
        if updateSrcDst, will read srcDst value form map notation
        otherwise, compares with supplied src/dst sizes"""
        usrStr = usrStr.replace(':', ',')
        usrStr = usrStr.replace('-', ',')
        # value should be a three element list of integers after evaluation
        tempMapTuple = drawer.strToSequence(usrStr, 3, ['int'])
        if tempMapTuple == None: return None # forces value to be len of 3
        # first two values must be between 1 and 6 (1:6, for ex)
        if (tempMapTuple[0] >= 1 and tempMapTuple[0] <= 6 and 
             tempMapTuple[1] >= 1 and tempMapTuple[1] <= 6):
            # check tt start and end size == src and dst
            if updateSrcDst: # need to get new values
                srcSize = tempMapTuple[0]
                dstSize = tempMapTuple[1]
            # update w/ new sizes 
            maxMapKey = self.getNoMaps(srcSize, dstSize)
            # check values agains src/dst
            if tempMapTuple[0] != srcSize or tempMapTuple[1] != dstSize:
                query = lang.msgMCbadMapChoice % (srcSize, dstSize, maxMapKey)
                dialog.msgOut(query, termObj)
                return None
        # length is not == 3, or values are greater/less than they should be
        else: # this is an error
            dialog.msgOut(lang.msgMCnoSuchMap, termObj)              
            return None
        # only need last value from temp typle
        map = self.getSingleMap(srcSize, dstSize, tempMapTuple[2])
        if map == -1 or map == None:    # returns -1 on error
            dialog.msgOut(lang.msgMCnoSuchMap, termObj)     
            return None
        else:
            mapIdTuple = (srcSize, dstSize, tempMapTuple[2])
        return map, mapIdTuple      


    def _evaluatePartialMap(self, usrStr, updateSrcDst, 
                                    srcSize, dstSize, termObj):
        """partial map is simply an integer; if src and dst sizes are known
        then must be w/n range; otherwise, get from user w/ interactive
        """
        usrData = drawer.strToNum(usrStr, 'int')
        if usrData == None: return None # should not happen, as should be intable
      
        if updateSrcDst:
            post = self.getSetSizeBounds() # interactiv ecommand
            if post == None: # bad sizes gotten from user
                dialog.msgOut(lang.msgMCbadVoiceValue, termObj)
                return None
            else: 
                srcSize, dstSize = post # assign to src/dst              
                
        maxMapKey = self.getNoMaps(srcSize, dstSize)
        # usrData must be less tn max and greater = to 1
        if not (usrData <= maxMapKey and usrData >= 1):
            query = lang.msgMCbadMapChoice % (srcSize, dstSize, maxMapKey)
            dialog.msgOut(query, termObj)            
            return None
        
        map = self.getSingleMap(srcSize, dstSize, usrData)
        if map == -1 or map == None:    # returns -1 on error
            dialog.msgOut(lang.msgMCbadRawMapFormat, termObj)       
            return None
        else:
            mapIdTuple = (srcSize, dstSize, usrData)
        return map, mapIdTuple      
            

    def _evaluateRawMap(self, usrStr, updateSrcDst, 
                              srcSize, dstSize, termObj):
        """raw map is an alphabetic string notation tt may include
        parenthesis"""
        mapIdTuple = self.stringToMap(usrStr)
        if mapIdTuple == None:
            dialog.msgOut(lang.msgMCbadRawMapFormat, termObj)       
            return None
        map = self.fetchMap(mapIdTuple)
        if map == -1 or map == None:
            dialog.msgOut(lang.msgMCbadRawMapFormat, termObj)   
            return None
        usrSrcSize, usrDstSize = self._getMapSrcDstSize(map)
        if not updateSrcDst: # provided src/dst
            # if usrStr does not match src/dst sizes
            if (usrSrcSize != srcSize or usrDstSize != dstSize):
                query = lang.msgMCbadMapChoice % (srcSize, 
                          dstSize, self.getNoMaps(srcSize, dstSize))
                dialog.msgOut(query, termObj)
                return None                       
        return map, mapIdTuple      


    def _evaluateRawVlPairs(self, usrStr, updateSrcDst, 
                                    srcSet, dstSet, termObj):
        """raw vl pairs are a notation that uses a list of pairs
        the pairs are separated by commas or double dashes?
        note: this takes srcSet, dstSet, not sizees
        """         
        # updateSrcNecsesary
        try:
            rawVlPairs = eval(usrStr)
            rawVlPairs = tuple(rawVlPairs)
        except:
            dialog.msgOut(lang.msgMCgetBadVlParse, termObj)          
            return None
            
        # need to check if if rawVlPairs has the right data
        # generate sample sets from size
        if len(rawVlPairs) < 1 or len(rawVlPairs) > 6 or None in rawVlPairs:
            dialog.msgOut(lang.msgMCgetBadVlParse, termObj)
            return None
        # examine that this is a list of lists, each w/ 2 values
        for pair in rawVlPairs:
            if not drawer.isList(pair) or len(pair) != 2:
                dialog.msgOut(lang.msgMCgetBadVlParse, termObj)
                return None
            
        # must get user boundarys sizes, b/c in vl-pairs there is no way 
        # of telling if a duplication is a real or phanton redundancy
        if not updateSrcDst: # if not, will be updated below
            srcSize = len(srcSet)
            dstSize = len(dstSet)       
        if updateSrcDst:
            post = self.getSetSizeBounds() # interacitve command
            if post == None:
                dialog.msgOut(lang.msgMCbadVoiceValue, termObj)
                return None
            else: srcSize, dstSize = post
            # need to search and extract voice leading from provided data
            foundPcsX = []
            foundPcsY = []
            # rawVlPairs should alwas been in the order of pcsX, 
            # from top to bottom
            for pair in rawVlPairs:
                foundPcsX.append(pair[0])
                foundPcsY.append(pair[1])
            foundPcsX = tuple(foundPcsX)
            foundPcsY = tuple(foundPcsY)
            foundPcsYsorted = copy.copy(foundPcsY)
            foundPcsYsorted.sort()
    
            # if sizes are equal, strip of actual pcs from the user entered 
            # vl-parts. otherwise generate demos
            if (len(foundPcsX) == srcSize and len(foundPcsY) == dstSize):
                while 1:
                    usrStr = dialog.askStr(lang.msgMCgetRefOrder % 
                              repr(foundPcsY).replace(' ',''), termObj)
                    if usrStr == None: return None
                    try: # what is this?
                        orderedPcsY = eval(usrStr)
                    except:
                        dialog.msgOut(lang.msgConfusedInput, termObj)
                        continue
                    testOrderedPcsY = copy.copy(orderedPcsY)
                    testOrderedPcsY = list(testOrderedPcsY)
                    testOrderedPcsY.sort()
                    # if these are not the same, the user has entered a bad 
                    # referential ordering
                    if foundPcsYsorted != testOrderedPcsY:
                        dialog.msgOut(lang.msgMCgetRefOrderBad, termObj)          
                        continue
                    else: break
                srcSet = foundPcsX # was same as demoPcsX
                dstSet = orderedPcsY # was same as demoPcsY
            else: 
                dialog.msgOut(lang.msgMCgetBadVlPairs, termObj)
                return None
        
        # can apply to acquisition methods 
        mapSearchResult = self.genMapFromVlPairs(rawVlPairs, srcSet, dstSet)
        if mapSearchResult == -1 or mapSearchResult == None:
            dialog.msgOut(lang.msgMCgetBadVlParse, termObj)
            return None
        else:
            partialMapId = mapSearchResult[0]
            correctedVlPairs = mapSearchResult[1]
            
        map = self.getSingleMap(srcSize, dstSize, partialMapId)
        if map == -1 or map == None:    # returns -1 on error
            maxMapKey = self.getNoMaps(srcSize, dstSize)
            query = lang.msgMCbadMapChoice % (srcSize, dstSize, maxMapKey)
            dialog.msgOut(query, termObj)        
            return None           

        mapIdTuple = (srcSize, dstSize, partialMapId)
        return map, mapIdTuple      
                    
                    
    def getUserMap(self, pcsX=(), pcsY=(), termObj=None, read=None):
        """gets map from user, returns -1 on cancel
        if read == string will try to match this string to a map
        returns None on error
        problem is that map can be specified w/o a src or dst
        """
        updateSrcDst = 1     # change to 0 if pcs args are passed in
        mapGotten = ()
        mapIdTuple = ()
        # case where no pcs are supplied, user must enter
        # will have to create dest set after getting boundary lengths
        if len(pcsX) == 0 or len(pcsY) == 0:
            updateSrcDst = 1
            # set to empty values
            srcSize = 0
            dstSize = 0
            srcSet = []
            dstSet = []
        else:
            srcSize = len(pcsX)
            dstSize = len(pcsY)
            if (srcSize >= 1 and srcSize <= 6 and dstSize >= 1 and dstSize <= 6):
                srcSet = tuple(pcsX)
                dstSet = tuple(pcsY)
                # stop sets from being recalculated based on length
                updateSrcDst = 0
             # source inputs are out of range for number of voices
            else: return None, None
            
        attempts = 0
        while 1:
            inputType = ''
            if read != None:
                # dont try more than once when reading
                if attempts > 0: return None, None 
                usrStr = read
                readMode = 1
            else:
                usrStr = dialog.askStr(lang.msgMCgetMapMenu, termObj)
                if usrStr == None: return None, None
                readMode = 0
            attempts = attempts + 1
            # get usrStr type
            inputType = self._parseMapInputTupe(usrStr)
            if inputType == None:
                if not updateSrcDst: # if not updating src and dst sizes
                    msg = lang.msgMCbadMapChoice % (srcSize, dstSize, 
                                            self.getNoMaps(srcSize, dstSize))
                    dialog.msgOut(msg, termObj)  
                else: # dont know src or dst, but still got an error
                    dialog.msgOut(lang.msgMCnoSuchMap, termObj)  
                continue # get data again from user
            
            # complete map is given as 3:2-1 or variant
            # only need index value; strip src and st size
            if inputType == 'completeMap':
                post = self._evaluateCompleteMap(usrStr, updateSrcDst, 
                                                            srcSize, dstSize, termObj)
                if post == None: continue
                mapGotten, mapIdTuple = post # assign values
            # user enters single number but has not entered boundary sizes
            elif inputType == 'partialMap':
                post = self._evaluatePartialMap(usrStr, updateSrcDst, 
                                                          srcSize, dstSize, termObj)
                if post == None: continue
                mapGotten, mapIdTuple = post # assign values
            # rawMaps are alphabetic strings
            elif inputType == 'rawMap': # no boundary entered
                post = self._evaluateRawMap(usrStr, updateSrcDst, 
                                                     srcSize, dstSize, termObj)
                if post == None: continue
                mapGotten, mapIdTuple = post # assign values
            # note: this takes srcSet, dstSet, not sizes
            elif inputType == 'rawVlPairs': # no boundary entered
                post = self._evaluateRawVlPairs(usrStr, updateSrcDst, 
                                                          srcSet, dstSet, termObj)
                if post == None: continue
                mapGotten, mapIdTuple = post # assign values
                                    
            # this should not happen, but errors creep in here:
            if mapIdTuple == None or len(mapIdTuple) == 0:
                return None, None # two None args necessary
            # provide display and ask user if this is what they want
            if readMode: # if reading just return
                return mapIdTuple, mapGotten

            # provide dummy sets if only size provided
            if updateSrcDst: # src/dst dize in 0,1 of mapIdTuple
                srcSet = tuple(range(mapIdTuple[0]))
                dstSet = tuple(range(mapIdTuple[1]))

            rowDict = self.genDoubleVlDiagram(srcSet, dstSet, mapGotten)
            printKeyList = rowDict.keys()
            printKeyList.sort()
            for key in printKeyList:
                tempRow = rowDict[key].strip()
                if tempRow == '': continue
                else: dialog.msgOut('%s%s\n' % (lang.TAB, rowDict[key]))
            
            # final confirmation
            query = lang.msgMCthisAsthat % (self.mapIdTupleToString(mapIdTuple),
                                                      self.rawMapToString(mapGotten))
            askUsr = dialog.askYesNoCancel(query, 1, termObj)                
            if askUsr != -1 and askUsr != 1:
                continue                      # return to top of loop if rejected
            elif askUsr == -1: return None, None
            elif askUsr == 1: break
        return mapIdTuple, mapGotten


    #------------------------------------------------------------------------||--
    def getUserMapFromRank(self, sourceSet, destinationSet, orderKey, 
                                  methodTypeString, termObj=None):
        srcSize = len(sourceSet)
        dstSize = len(destinationSet)
        'gets map from user, returns -1 on cancel'
        # type string is used in prompt
        while 1:
            query = lang.msgMCchooseRank % (methodTypeString, len(orderKey))
            choice = dialog.askStr(query, termObj)
            if choice == None:
                return None
            try:
                choicePos = eval(choice)
                choicePos = choicePos - 1   # human offset correction
            except:
                dialog.msgOut(lang.msgMCnoSuchRank, termObj)
                continue
            if choicePos in range(0, len(orderKey)):#success
                mapIdTuple = (srcSize, dstSize, orderKey[choicePos])
                ### createa  display
                rowDict = self.genDoubleVlDiagram(sourceSet, destinationSet, 
                             self.fetchMap(mapIdTuple))
                printKeyList = rowDict.keys()
                printKeyList.sort()
                for key in printKeyList:
                    tempRow = rowDict[key].strip()
                    if tempRow == '':
                        continue
                    else:
                        dialog.msgOut(lang.TAB + ('%s\n' % rowDict[key]), termObj)
                query = lang.msgMCthisAsthat % (self.mapIdTupleToString(mapIdTuple), 
                                     self.rawMapToString(self.fetchMap(mapIdTuple)))
                askUsr = dialog.askYesNoCancel(query, 1, termObj)       
                if askUsr != -1 and askUsr != 1:
                    continue                      # return to top of loop if rejected 
                elif askUsr == -1:
                    return None
                elif askUsr == 1:
                    return mapIdTuple
            else:
                dialog.msgOut(lang.msgMCnoSuchRank, termObj)
                continue

    #------------------------------------------------------------------------||--
    def SMTH(self, pcsX, pcsY, map):
        # this is the measure of smoothness
        # pcs must be of same size before entering this_function, map is a 
        # rawMap, not mapTUpleId
        if len(pcsX) > 6 or len(pcsX) < 1 or len(pcsY) > 6 or len(pcsY) < 1:
            return 'pcs of this size are not supported'

        vlPairs = self.genVlPairs(pcsX, pcsY, map)
        vectorS = [0,0,0,0,0,0,0]
        for pcs_voice in vlPairs:
            x = pcs_voice[0]
            y = pcs_voice[1]
            dist = abs(x-y)
            dist = pitchTools.pcTransposer(dist, 0)  #trans by 0 to perf mod 12
            if dist > 6:
                dist = 12 - dist
            vectorS[dist] = vectorS[dist] + 1
        reg_i = 0
        totalS = 0
        for reg in vectorS:
            totalS = totalS + (reg * reg_i)
            reg_i = reg_i + 1
        return vectorS, totalS

    def sortSMTH(self, pcsX, pcsY):
        # returns a dictionary and a list
        # the dictionary containts refNo for map : values
        # list contains ordered refNo according to sorting principles 
        if len(pcsX) > 6 or len(pcsX) < 1 or len(pcsY) > 6 or len(pcsY) < 1:
            return None # error, bad size
        mapDict = self.getMapDict(len(pcsX), len(pcsY))
        keyList = mapDict.keys()
        keyList.sort()
        dictS = {}
        for key in keyList:
            vectorS, totalS = self.SMTH(pcsX, pcsY, mapDict[key])
            dictS[key] = vectorS, totalS

        # list of keys in sorted order
        # the order of the pcs entered _does_ matter, b/c references are made only
        # to map index numbers, not fleshed out vl-pair tuples.
        # sorts smallest to largest in a list
        orderKey = []
        for key in keyList:
            vectorS, totalS = dictS[key]
            if orderKey == []:
                orderKey.append(key)
                continue
            index = 0
            for entry in orderKey:
                # !!! want smallest first!!!
                # if current total is > than this total | DO nothing
                if totalS > dictS[entry][1]:    #entry is a key, 1, gets the total
                    index = index + 1
                    if index == len(orderKey):
                    # if greater, and this is the last entry, put at end 
                    # (its the largest)
                        orderKey.append(key)
                        break
                # if current total is < than this total | DO insert
                elif totalS < dictS[entry][1]:  #entry is a key, 1, gets the total
                # when less than or equal to in orderKey, insert at that index
                    orderKey.insert(index, key)
                    break
                # if current total is == than this total | DO more analysis
                elif totalS == dictS[entry][1]: #entry is a key, 1, gets the total
                    # if current vector reg 6 is    < than this vector 6 | DO insert
                    if dictS[key][0][6] < dictS[entry][0][6]: 
                        orderKey.insert(index, key)
                        break
                    elif dictS[key][0][6] > dictS[entry][0][6]: # if >, do nothing 
                        index = index + 1
                        if index == len(orderKey):
                            orderKey.append(key)
                            break 
                    else:
                        if dictS[key][0][5] < dictS[entry][0][5]: 
                            orderKey.insert(index, key)
                            break
                        elif dictS[key][0][5] > dictS[entry][0][5]: # if >, do nothing 
                            index = index + 1
                            if index == len(orderKey):
                                orderKey.append(key)
                                break 
                        else:
                            if dictS[key][0][4] < dictS[entry][0][4]: 
                                orderKey.insert(index, key)
                                break
                            elif dictS[key][0][4] > dictS[entry][0][4]:#if >,do nothing 
                                index = index + 1
                                if index == len(orderKey):
                                    orderKey.append(key)
                                    break 
                            else:
                                if dictS[key][0][3] < dictS[entry][0][3]: 
                                    orderKey.insert(index, key)
                                    break
                                elif dictS[key][0][3] > dictS[entry][0][3]:
                                    #if Greater, do nothing 
                                    index = index + 1
                                    if index == len(orderKey):
                                        orderKey.append(key)
                                        break 
                                else:
                                    if dictS[key][0][2] < dictS[entry][0][2]: 
                                        orderKey.insert(index, key)
                                        break
                                    elif dictS[key][0][2] > dictS[entry][0][2]: 
                                    # if greater, do nothing 
                                        index = index + 1
                                        if index == len(orderKey):
                                            orderKey.append(key)
                                            break 
                                    else:
                                        if dictS[key][0][1] < dictS[entry][0][1]: 
                                            orderKey.insert(index, key)
                                            break
                                        elif (dictS[key][0][1] > 
                                                dictS[entry][0][1]):     
                                            # if greater, do nothing 
                                            index = index + 1
                                            if index == len(orderKey):
                                                orderKey.append(key)
                                                break 
                                        else:
                                            if (dictS[key][0][0] < 
                                                dictS[entry][0][0]): 
                                                orderKey.insert(index, key)
                                                break
                                            elif (dictS[key][0][0] > 
                                                    dictS[entry][0][0]):     
                                                    # if greater, do nothing 
                                                index = index + 1
                                                if index == len(orderKey):
                                                    orderKey.append(key)
                                                    break 
                                            else: # do nothing
                                                index = index + 1
                                                if index == len(orderKey):
          # if greater, and this is the last entry, put at end (its the largest)
                                                    orderKey.append(key)
                                                    break                                             
                else:
                    index = index + 1
                    # if greater, and this is the last entry, 
                    # put at end (its the largest)
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
        return dictS, orderKey

    def printSortSMTH(self, pcsX, pcsY):
        dictS, orderKey = self.sortSMTH(pcsX, pcsY)
        msg = 'final sort    %s\n' % (repr(orderKey).replace(' ', ''))
        msg = msg + '[vector]:[displacement]:\n'
        for key in orderKey:
            line = ''
            map = self.getSingleMap(len(pcsX), len(pcsY), key)
            for entry in dictS[key]:
                line = line + repr(entry).replace(' ', '') + ':'
            mapString = self.rawMapToString(map)
            msg = msg + '%sMC %i, map %s\n' % (line.ljust(55), key, mapString)
        print msg



    #------------------------------------------------------------------------||--
    def UNIF(self, pcsX, pcsY, map):
        vlPairs = self.genVlPairs(pcsX, pcsY, map)
        vectorU = [0,0,0,0,0,0,0,0,0,0,0,0]
        for pcs_voice in vlPairs:
            x = pcs_voice[0]
            y = pcs_voice[1]
            dist = y-x
            if dist < 0 or dist > 11:
                dist = pitchTools.pcTransposer(dist, 0)  #trans by 0 to perf mod 12
            vectorU[dist] = vectorU[dist] + 1

        valuesU = []
        for reg in vectorU:
            valuesU.append(reg)
        valuesU.sort()
        valuesU.reverse() #in order form largest to smallest, with duplicates

        orderedIcPeaksU = []     # contains ordered index positions, not values
        dummy_vector = copy.copy(vectorU)    
        for value in valuesU:  # has all values for every reg, incl 0s
            if value != 0:
                i = dummy_vector.index(value) #get value's index numver
                orderedIcPeaksU.append(i)
            dummy_vector[i] = -1     # knock out so that will not get chosen again
        ### use to finde span
        double_range = range(0,12) + range(0,12)
        start     = 0 
        count     = 0
        max   = 0
        for i in double_range:
            count = count + 1
            if vectorU[i] == 0 and start == 0:
                start = 1
                count = 1
            elif vectorU[i] == 0 and start == 1:
                continue
            elif vectorU[i] != 0 and start == 1:
                start = 0
                if (count - 1) >= max:
                    max = count - 1
            elif vectorU[i] != 0 and start == 0:
                continue
        spanU = 12 - max

        ### find offset
        UNIFoffsetCandidates = []           
        ## print 'unif ordered ic peaks %r' % orderedIcPeaksU
        for peaksIndex in orderedIcPeaksU:
        # ordered peaks contains the register position of non-zero entries
            mvt_from_list = []  
            # for the current peakIndex, this is the remaining index positions 
            # that need to be tested to
            for i in range(0,12):
                # dont want 0s or the value equal to peaks index 
                if vectorU[i] == 0 or i == peaksIndex:
                    continue
                else:
                    mvt_from_list.append(i)
            # find all possible mod 12 locations for the destination
            destination   = peaksIndex
            destNegative  = peaksIndex - 12
            destPositive  = peaksIndex + 12
            temp_distance = 0    ### the accumulator of the distances in the mvt list
            for currentOriginPeak in mvt_from_list:
                startIndex = currentOriginPeak
                a = abs(destination - startIndex)
                # find all possible dstinances to the mod12 destinations,
                # and choose the shortest
                b = abs(destNegative - startIndex)
                c = abs(destPositive - startIndex)
                posibleDistanceList = [a,b,c]
                shortestDistance = min(posibleDistanceList)
                temp_distance = temp_distance + (shortestDistance * 
                                                    vectorU[currentOriginPeak])
            # print 'mvt from originPeak %r to peaksIndex %r, dis fnd %i, wghtd as 
            # %i' % (currentOriginPeak, peaksIndex, shortestDistance, 
            # (shortestDistance * vectorU[currentOriginPeak]))
            #print 'Unif candidiate total distance   %r' % (temp_distance)
            UNIFoffsetCandidates.append((temp_distance, peaksIndex))

        offsetU = 99999
        for (offset, peaksIndex) in UNIFoffsetCandidates:
            if offset <= offsetU:
                offsetU = offset
        offsetIcPeakU = []
        for (offset, peaksIndex) in UNIFoffsetCandidates:
            if offset == offsetU:
                offsetIcPeakU.append(peaksIndex)
        maxU = 0
        for entry in vectorU:
            if entry >= maxU:
                maxU = entry
        # vector, index of nonzero entries, ties for shortest Offset, span, offset
        return vectorU, orderedIcPeaksU, offsetIcPeakU, maxU, spanU, offsetU

    def sortUNIF(self, pcsX, pcsY):
        # returns a dictionary and a list
        # the dictionary containts refNo for map : values
        # list contains ordered refNo according to sorting principles 
        if len(pcsX) > 6 or len(pcsX) < 1 or len(pcsY) > 6 or len(pcsY) < 1:
            return None
        mapDict = self.getMapDict(len(pcsX), len(pcsY))
        keyList = mapDict.keys()
        keyList.sort()
        dictU = {}
        for key in keyList:
            n = self.UNIF(pcsX, pcsY, mapDict[key])
            vectorU, orderedIcPeaksU, offsetIcPeakU, maxU, spanU, offsetU = n
            dictU[key] = (vectorU, orderedIcPeaksU, offsetIcPeakU, 
                              maxU, spanU, offsetU)

        # list of keys in sorted order
        # the order of the pcs entered _does_ matter, b/c references are made only
        # to map index numbers, not fleshed out vl-pair tuples.

        # sorts smallest to largest in a list (we want largest, 
        # to smallest, so reverse at end)
        orderMax = []   # sort list according to 
        for key in keyList:
            maxU = dictU[key][3] # 3 gets the max vale for any vector register
            if orderMax == []:
                orderMax.append(key)
                continue
            index = 0
            for entry in orderMax:
                if maxU > dictU[entry][3]:   #entry is a key, 3, gets the MAX
                    index = index + 1
                    if index == len(orderMax):
                        orderMax.append(key)
                        break
                elif maxU <= dictU[entry][3]:    #entry is a key, 1, gets the max
                    orderMax.insert(index, key)
                    break
                else:
                    index = index + 1 
                    # was orderKey, not orderMax
                    if index == len(orderMax):
                        orderMax.append(key)
                        # orderKey.append(key) # was incorrect?
                        break
        # 5 gets the offset vale for any vector register# this is a list of 
        # indexNos that give the order of Max values, from the highest 
        # to the lowest.
        orderMax.reverse()

        # this sort is necessary
        # sorts smallest to largest in a list
        orderSpan = []   ## sort list according to 
        for key in keyList:
            spanU = dictU[key][4]  ## 4 gets the span vale for any vector register
            if orderSpan == []:
                orderSpan.append(key)
                continue
            index = 0
            for entry in orderSpan:
                if spanU > dictU[entry][4]:  #entry is a key, 4, gets the span
                    index = index + 1
                    if index == len(orderSpan):
                        orderSpan.append(key)
                        break
                elif spanU <= dictU[entry][4]:  #entry is a key, 4, gets the span
                    orderSpan.insert(index, key)
                    break
                else:
                    index = index + 1 
                    # orderSpan here was given as orderKey
                    if index == len(orderSpan):
                        orderSpan.append(key)
                        break

        # sorts smallest to largest in a list
        orderOffset = []    # sort list according to 
        for key in keyList:
            # 5 gets the offset vale for any vector register
            offsetU = dictU[key][5]
            if orderOffset == []:
                orderOffset.append(key)
                continue
            index = 0
            for entry in orderOffset:
                # entry is a key, 5, gets the offset
                if offsetU > dictU[entry][5]:
                    index = index + 1
                    if index == len(orderOffset):
                        orderOffset.append(key)
                        break
                # entry is a key, 5, gets the offset
                elif offsetU <= dictU[entry][5]:     
                    orderOffset.insert(index, key)
                    break
                else:
                    index = index + 1 
                    # orderOffset here was orderKeu
                    if index == len(orderOffset):
                        orderOffset.append(key)
                        break

        # sort by offset, max, then span: orderOffset, orderMax, orderSpan
        # conversion max >>> offset     # span >>> max        # offset >>> span
        orderKey = []   # sort list according to 
        for key in orderOffset:  # take offset list as initial sort
            UNIF_max        = dictU[key][3]  ## 3 gets the max
            spanU     = dictU[key][4] # 4 gets the span
            offsetU = dictU[key][5] # 5 gets the offset
            if orderKey == []:
                orderKey.append(key)
                continue
            index = 0
            for entry in orderKey: ## this is the list of keys already sorted
                # if current offset is > than this offset | DO nothing
                if offsetU > dictU[entry][5]: 
                    index = index + 1 # index keeps tracks of position in orderKey`
                    if index == len(orderKey):
                        orderKey.append(key)
                        break     
                # if current offset is < than this offset | 
                # current max is > this max | DO insert
                elif offsetU < dictU[entry][5] and UNIF_max > dictU[entry][3]: 
                    orderKey.insert(index, key)
                    break
                # if current offset is < than this offset | 
                # current max is < this max | DO nothing
                elif offsetU < dictU[entry][5] and UNIF_max < dictU[entry][3]: 
                    index = index + 1 # index keeps tracks of position in orderKey`
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
                # if current offset is == than this offset | 
                # current max is > this max | DO insert
                elif offsetU == dictU[entry][5] and UNIF_max > dictU[entry][3]: 
                    orderKey.insert(index, key)
                    break
                # if current offset is == than this offset | 
                # current max is < this max | DO nothing
                elif offsetU == dictU[entry][5] and UNIF_max < dictU[entry][3]: 
                    index = index + 1 # index keeps track of position in orderKey`
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
                # if current offset is == than this offset | 
                # current max is == this max | current span is <= this span | 
                # DO inset
                elif (offsetU == dictU[entry][5] and UNIF_max == dictU[entry][3] and
                    spanU <= dictU[entry][4]): 
                    orderKey.insert(index, key)
                    break
                # if current offset is == than this offset | 
                #current max is == this max | 
                #current span is > this span | DO nothing
                elif (offsetU == dictU[entry][5] and UNIF_max == dictU[entry][3] and
                    spanU <= dictU[entry][4]): 
                    # index keeps tracks of position in orderKey`
                    index = index + 1                     
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
                else:
                    index = index + 1 
                    if index == len(orderKey):
                        orderKey.append(key)
                        break

        return dictU, orderKey, orderMax, orderSpan, orderOffset

    def printSortUNIF(self, pcsX, pcsY):
        a = self.sortUNIF(pcsX, pcsY)
        dictU, orderKey, orderMax, orderSpan, orderOffset = a
        msg = 'final sort    %s\nmax sort     %s\nspan sort %s\noffset sort %s\n' % (repr(orderKey).replace(' ', ''), 
            repr(orderMax).replace(' ', ''), repr(orderSpan).replace(' ', ''), repr(orderOffset).replace(' ', ''))
        msg = msg + '[vector]:[peaks]:[offset-peaks]:max:span:offset:\n'
        for key in orderKey:
            line = ''
            map = self.getSingleMap(len(pcsX), len(pcsY), key)
            for entry in dictU[key]:
                line = line + repr(entry).replace(' ', '') + ':'
            mapString = self.rawMapToString(map)
            msg = msg + '%sMC %i, map %s\n' % (line.ljust(55), key, mapString)
        print msg

    #------------------------------------------------------------------------||--
    def BAL(self, pcsX, pcsY, map):
        vlPairs = self.genVlPairs(pcsX, pcsY, map)
        vectorB = [0,0,0,0,0,0,0,0,0,0,0,0]
        for pcs_voice in vlPairs:
            x = pcs_voice[0]
            y = pcs_voice[1]
            dist = x + y
            dist = pitchTools.pcTransposer(dist, 0)  #trans by 0 to perf mod 12
            vectorB[dist] = vectorB[dist] + 1

        valuesB = []
        for reg in vectorB:
            valuesB.append(reg)
        valuesB.sort()
        valuesB.reverse() # now in order form largest to smallest

        orderedIcPeaksB = []     
        dummy_vector = copy.copy(vectorB)    
        for value in valuesB:
            i = dummy_vector.index(value)
            if value != 0:
                orderedIcPeaksB.append(i)
            dummy_vector[i] = -1     # knock out so that will not get chosen again

        double_range = range(0,12) + range(0,12)
        start     = 0 
        count     = 0
        max   = 0
        for i in double_range:
            count = count + 1
            if vectorB[i] == 0 and start == 0:
                start = 1
                count = 1
            elif vectorB[i] == 0 and start == 1:
                continue
            elif vectorB[i] != 0 and start == 1:
                start = 0
                if (count - 1) >= max:
                    max = count - 1
            elif vectorB[i] != 0 and start == 0:
                continue
        spanB = 12 - max

        # find offset
        BALoffsetCandidates = []          
        # print 'bal ordered ic peaks %r' % orderedIcPeaksB
        # ordered peaks contains the register position of non-zero entries
        for peaksIndex in orderedIcPeaksB:
            mvt_from_list = []
            # for the current peakIndex, this is the remaining index positions 
            # that need to be tested to
            for i in range(0,12):
                # dont want 0s or the value equal to peaks index 
                if vectorB[i] == 0 or i == peaksIndex:
                    continue
                else:
                    mvt_from_list.append(i)
            # find all possible mod 12 locations for the destination
            destination   = peaksIndex
            destNegative  = peaksIndex - 12
            destPositive  = peaksIndex + 12
            temp_distance = 0    ### the accumulator of the distances in the mvt list
            for currentOriginPeak in mvt_from_list:
                startIndex = currentOriginPeak
                # find all possible dstinances to the mod12 destinations, 
                # and choose the shortest
                a = abs(destination - startIndex) 
                b = abs(destNegative - startIndex)
                c = abs(destPositive - startIndex)
                posibleDistanceList = [a,b,c]
                shortestDistance = min(posibleDistanceList)
                temp_distance = temp_distance + (shortestDistance * vectorB[currentOriginPeak])
                # print 'mvt from originPeak %r to peaksIndex %r, dis fnd %i, wghtd as %i' % (currentOriginPeak, peaksIndex, shortestDistance, (shortestDistance * vectorB[currentOriginPeak]))
            #print 'Bal candidiate total distance   %r' % (temp_distance)
            BALoffsetCandidates.append((temp_distance, peaksIndex))

        offsetB = 99999
        for (offset, peaksIndex) in BALoffsetCandidates:
            if offset <= offsetB:
                offsetB = offset
        BALoffset_icPeak = []
        for (offset, peaksIndex) in BALoffsetCandidates:
            if offset == offsetB:
                BALoffset_icPeak.append(peaksIndex)
        BALmax = 0
        for entry in vectorB:
            if entry >= BALmax:
                BALmax = entry
        # vector, index of nonzero entries, ties for shortest Offset, span, offset
        return vectorB, orderedIcPeaksB, BALoffset_icPeak, BALmax, spanB,    offsetB


    def sortBAL(self, pcsX, pcsY):
        # returns a dictionary and a list
        # the dictionary containts refNo for map : values
        # list contains ordered refNo according to sorting principles 
        if len(pcsX) > 6 or len(pcsX) < 1 or len(pcsY) > 6 or len(pcsY) < 1:
            return None
        mapDict = self.getMapDict(len(pcsX), len(pcsY))
        keyList = mapDict.keys()
        keyList.sort()
        dictB = {}
        for key in keyList:
            a = self.BAL(pcsX, pcsY, mapDict[key])
            vectorB, orderedIcPeaksB, BALoffset_icPeak, BALmax, spanB, offsetB = a
            dictB[key] = (vectorB, orderedIcPeaksB, BALoffset_icPeak, 
                              BALmax, spanB, offsetB)

        # list of keys in sorted order
        # the order of the pcs entered _does_ matter, b/c references are made only
        # to map index numbers, not fleshed out vl-pair tuples.

        # sorts smallest to largest in a list 
        # (we want largest, to smallest, so reverse at end)
        orderMax = []   ## sort list according to 
        for key in keyList:
            BALmax = dictB[key][3]  # 3 gets the max vale for any vector register
            if orderMax == []:
                orderMax.append(key)
                continue
            index = 0
            for entry in orderMax:
                if BALmax > dictB[entry][3]:    #entry is a key, 3, gets the MAX
                    index = index + 1
                    if index == len(orderMax):
                        orderMax.append(key)
                        break
                elif BALmax <= dictB[entry][3]: #entry is a key, 1, gets the max
                    orderMax.insert(index, key)
                    break
                else:
                    index = index + 1 
                    # was orderKey, not orderMax
                    if index == len(orderMax):
                        orderMax.append(key)
                        break
        orderMax.reverse()      
        # this is a list of indexNos that give the order of Max values, 
        # from the highest to the lowest.

        # this sort is necessary
        # sorts smallest to largest in a list
        orderSpan = []   ## sort list according to 
        for key in keyList:
            spanB = dictB[key][4]# 4 gets the span vale for any vector register
            if orderSpan == []:
                orderSpan.append(key)
                continue
            index = 0
            for entry in orderSpan:
                #entry is a key, 4, gets the span
                if spanB > dictB[entry][4]: 
                    index = index + 1
                    if index == len(orderSpan):
                        orderSpan.append(key)
                        break
                #entry is a key, 4, gets the span
                elif spanB <= dictB[entry][4]:  
                    orderSpan.insert(index, key)
                    break
                else:
                    index = index + 1 
                    # was orderKey, not orderSpan
                    if index == len(orderSpan):
                        orderSpan.append(key)
                        break

        # this sort is not nec, keep for testing
        # sorts smallest to largest in a list
        orderOffset = []    ## sort list according to 
        for key in keyList:
            # 5 gets the offset vale for any vector register
            offsetB = dictB[key][5]
            if orderOffset == []:
                orderOffset.append(key)
                continue
            index = 0
            for entry in orderOffset:
                #entry is a key, 5, gets the offset
                if offsetB > dictB[entry][5]:    
                    index = index + 1
                    if index == len(orderOffset):
                        orderOffset.append(key)
                        break
                #entry is a key, 5, gets the offset
                elif offsetB <= dictB[entry][5]:     
                    orderOffset.insert(index, key)
                    break
                else:
                    index = index + 1 
                    # was orderKey, not orderOffset
                    if index == len(orderOffset):
                        orderOffset.append(key)
                        break


        ## sort by offset, max, then span: orderOffset, orderMax, orderSpan
        ## conversion max >>> offset         # span >>> max     # offset >>> span
        orderKey = []   ## sort list according to 
        for key in orderOffset:  # take offset list as initial sort
            maxB      = dictB[key][3]    ## 3 gets the max
            spanB     = dictB[key][4]    ## 4 gets the span
            offsetB = dictB[key][5]  ## 5 gets the offset
            if orderKey == []:
                orderKey.append(key)
                continue
            index = 0
            for entry in orderKey: ## this is the list of keys already sorted
                # if current offset is > than this offset | DO nothing
                if offsetB > dictB[entry][5]: 
                    index = index + 1                        
                    # index keeps tracks of position in orderKey`
                    if index == len(orderKey):
                        orderKey.append(key)
                        break     
                # if current offset is < than this offset | 
                # current max is > this max | DO insert
                elif offsetB < dictB[entry][5] and maxB > dictB[entry][3]: 
                    orderKey.insert(index, key)
                    break
                # if current offset is < than this offset | 
                # current max is < this max | DO nothing
                elif offsetB < dictB[entry][5] and maxB < dictB[entry][3]: 
                    index = index + 1                       
                    # index keeps tracks of position in orderKey`
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
                # if current offset is == than this offset | 
                #current max is > this max | DO insert
                elif offsetB == dictB[entry][5] and maxB > dictB[entry][3]: 
                    orderKey.insert(index, key)
                    break
                # if current offset is == than this offset | 
                # current max is < this max | DO nothing
                elif (offsetB == dictB[entry][5] and maxB < dictB[entry][3]): 
                    index = index + 1                        
                    # index keeps tracks of position in orderKey`
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
                # if current offset is == than this offset | 
                # current max is == this max | current span is <= this span | 
                # DO inset
                elif (offsetB == dictB[entry][5] and maxB == dictB[entry][3] 
                    and spanB <= dictB[entry][4]): 
                    orderKey.insert(index, key)
                    break
                # if current offset is == than this offset | 
                # current max is == this max | current span is > this span | 
                # DO nothing
                elif (offsetB == dictB[entry][5] and maxB == dictB[entry][3] 
                    and spanB <= dictB[entry][4]): 
                     # index keeps tracks of position in orderKey`
                    index = index + 1                       
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
                else:
                    index = index + 1 
                    if index == len(orderKey):
                        orderKey.append(key)
                        break
        return dictB, orderKey, orderMax, orderSpan, orderOffset

    def printSortBAL(self, pcsX, pcsY):
        a = self.sortBAL(pcsX, pcsY)
        dictB, orderKey, orderMax, orderSpan, orderOffset = a
        msg = 'final sort    %s\nmax sort     %s\nspan sort %s\noffset sort %s\n' % (repr(orderKey).replace(' ', ''), 
            repr(orderMax).replace(' ', ''), repr(orderSpan).replace(' ', ''), repr(orderOffset).replace(' ', ''))
        msg = msg + '[vector]:[peaks]:[offset-peaks]:max:span:offset:\n'
        for key in orderKey:
            line = ''
            map = self.getSingleMap(len(pcsX), len(pcsY), key)
            for entry in dictB[key]:
                line = line + repr(entry).replace(' ', '') + ':'
            mapString = self.rawMapToString(map)
            msg = msg + '%sMC %i, map %s\n' % (line.ljust(55), key, mapString)
        print msg


