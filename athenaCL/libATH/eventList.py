#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          eventList.py
# Purpose:       manages Event object types; EventMode, OutputEngines.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--
import os, time, random, copy, array

from athenaCL.libATH import drawer
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import midiTools
from athenaCL.libATH import pitchTools
from athenaCL.libATH import osTools
from athenaCL.libATH import audioTools
from athenaCL.libATH import outFormat
from athenaCL.libATH.libOrc import orc
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.omde import bpf # needed for interpolation

_MOD = 'eventList.py'

#-----------------------------------------------------------------||||||||||||--
# eventModes have a single, default orc object that they work wiht
# sometimes orc objects need to be created w/o the event list object
# and from the eventList objects name


# eventModes: define a type of scoring, incluring what instruments are 
# represented (orc def)
eventModeNames = {
    'cn'      :'csoundNative' ,
    'ce'      :'csoundExternal' ,
    'cs'      :'csoundSilence' ,
    'm'   :'midi',
    'mp'      :'midiPercussion',
    }

# output engines may handle a single output format, or multiple 
# every event mode has certain engines always associated with it
# when using one even mode, other outputs can be requested
# engines concert singel part (texture, clone) data into a polyphonic
# representation
outputEngineNames = [
    'EngineAudioFile',
    'EngineCsoundNative',  # .csd, .sco, .orc, .bat
    'EngineCsoundSilence', # .sco only 
    'EngineCsoundExternal', # .sco only 
    'EngineMaxColl',
    'EngineAcToolbox',
    'EngineMidiFile',
    'EngineText',
    ]


def eventModeParser(typeName):
    """utility functions for parsing user paramter strings into proper
    parameter names. accepts short names and long names, regardless of case
    does not raise an error if no match: returns string unmodified
    """
    parsed = drawer.acronymExpand(typeName, eventModeNames)
    if parsed == None: pass
    return parsed


#-----------------------------------------------------------------||||||||||||--
    
# each eventMode only uses one type of orchestra
# the same orchestra can be used for in multiple event modes
def selectEventModeOrc(emName):
    """for a given emName, supply the appropriate orchestra name
    most often, these will be the same; but two different eventLists may 
    want to sare the same orhestra"""   
    emName = eventModeParser(emName)
    assert emName in eventModeNames.values() and emName != None
    if emName == 'csoundNative':
        return 'csoundNative'
    elif emName == 'csoundSilence':
        return 'csoundSilence'
    elif emName == 'csoundExternal':
        return 'csoundExternal'
    elif emName == 'midi':
        return 'generalMidi'
    elif emName == 'midiPercussion':
        return 'generalMidiPercussion'

# each outputEngine may use only one orchestra, or variable orchestras
# in some cases the emName will determine the orc used w/ an engine
# in other cases, the emName has nothing to do w/ what orc is used
def selectOutEngineOrc(emName, oeName):
    """for a given eventMode and outputEngine, determine best orchestra"""
    assert emName in eventModeNames.values() and emName != None
    if oeName not in outputEngineNames:
        raise ValueError, 'bad Output name: %s' % oeName    
    if oeName == 'EngineAudioFile':
        return 'generic' # use generic orc only for conversions
    elif oeName == 'EngineCsoundNative':
        return 'csoundNative'
    elif oeName == 'EngineCsoundSilence':
        return 'csoundSilence'   
    elif oeName == 'EngineCsoundExternal':
        return 'csoundExternal'   
    elif oeName == 'EngineMaxColl':
        # macColl assumes midi values for all parameters
        return 'generalMidi'
    # treate acToolbox the same as midiFile
    elif oeName in ['EngineMidiFile', 'EngineAcToolbox']:
        if emName in ['midi', 'midiPercussion']:
            return selectEventModeOrc(emName) # will get gm or gmPercussion
        else: # event mode may be something other than a midi variant
            return 'generalMidi' # use midi in all general cases
    elif oeName == 'EngineText':
        return selectEventModeOrc(emName) # get orc of this event mode
    else:
        raise ValueError, 'no such ouput Engine name'




#-----------------------------------------------------------------||||||||||||--
class EventSequence:
    """data representation of event lists; stores all event data 
    for a single texture or clone; a clone will process this object into
    another object

    designed to deal w/ event dictionaries
    event dictionaries can have the following keys (defined in baseTexture):
        eventDict['inst'] = inst
        eventDict['time'] = tCurrent
        eventDict['sus'] = sus # real sustain value
        eventDict['dur'] = dur # not actually used to calc dur, as next t avail
        eventDict['acc'] = acc # may be 0 if silences retained
        eventDict['bpm'] = bpm  # store bpm
        eventDict['pulse'] = pulse   # store string repr of pulse object
        eventDict['amp'] = amp
        eventDict['ps'] = ps
        eventDict['pan'] = pan
        eventDict['aux'] = auxiliary # a list of data, variable size
        eventDict['comment'] # a list
        
    eventData: stores meta data about event list;
        tAbsStart, tAbsEnd
    """
    def __init__(self):
        self._eventList = [] # a list of event dictionaries, perhaps un sorted
        # can store: tStart, tEnd, ampMax
        self._eventData = {} # dictionary that store attribute data

    #-----------------------------------------------------------------------||--
    # built in methods
    def append(self, eventDict):
        """append an event dictionary"""
        self._eventList.append(eventDict)

    def clear(self):
        self._eventList = []

    def __len__(self):
        return len(self._eventList)
        
    def keys(self):
        # return event inex positions form 0
        return range(0, len(self._eventList))

    def __getitem__(self, key):
        """numbers are index keys, return event dict at this location"""
        return self._eventList[key]

    def __setitem__(self, key, value):
        self._eventList[key] = value

    def __delitem__(self, key):
        del self._eventList[key]

    def copy(self):
        esObj = EventSequence()
        # this will not work w/ arrays
        esObj._eventList = copy.deepcopy(self._eventList)
        esObj._eventData = copy.deepcopy(self._eventData)
        return esObj
        
    def sort(self):
        """sort the event list in place according to time values
        called automatically w/ updatePost; called after texture creation
        do not do this always: may be a significant time suck"""
        alt = []
        tRef = []
        for i in range(self.__len__()):
            # store start time, index in source list
            tRef.append((self._eventList[i]['time'], i))
        tRef.sort() # sort according to time
        for t, i in tRef: # reappend dictionaries
            alt.append(self._eventList[i])
        self._eventList = alt # assign to eventList
        
    #-----------------------------------------------------------------------||--
    # data access and loading

    def list(self):
        """return a reference to the event list
        not a copy; only used for translations"""
        return self._eventList
        
    def meta(self, key):
        """get meta data from an event sequence object"""
        return self._eventData[key]
        
    def getArray(self, name):
        """get a copy of all values from the event list as an array"""
        data = []
        for event in self._eventList:
            data.append(event[name])
        return data

    def setArray(self, name, data):
        """load all values from the event list as an array"""
        assert len(data) == len(self._eventList)
        for i in range(0, len(data)):
            self._eventList[i][name] = data[i] 


    #-----------------------------------------------------------------------||--
    # updates and other management
    def updatePre(self):
        # called in before before scoreing
        # shoudl be used to clear the score?
        pass

    def _updateTimeRangeAbs(self):
        # this assumes that events   are sorted...
        tArray = self.getArray('time')
        susArray = self.getArray('sus')
        if len(tArray) == 0: # uncommon, but happens w/ no events
            min = 0
            max = 0
        else:
            # scroll through all values and find largest combination
            min = tArray[0] # possible values by order, may not be right
            max = tArray[-1] + susArray[-1]
            for x in range(len(tArray)):
                if tArray[x] <= min: min = tArray[x]
                if tArray[x] + susArray[x] >= max:
                    max = tArray[x] + susArray[x]
        self._eventData['tAbsStart'] = min
        self._eventData['tAbsEnd'] = max

    def updatePost(self):
        # called in baseTexture in post score
        #self._updateMaxAmp()
        self._updateTimeRangeAbs()
        # note: events used to be sorted here, now make sorting optional

    def getTimeRangeAbs(self):
        return  self._eventData['tAbsStart'],   self._eventData['tAbsEnd']

    def getTotalDuration(self):
        return  self._eventData['tAbsEnd'] - self._eventData['tAbsStart']
    

    #-----------------------------------------------------------------------||--
    # transformations to the event sequence

    def interpolate(self, tFrameArray, snapSus, 
                         active=['time', 'acc', 'bpm', 'amp', 'ps', 'pan', 'aux']):
        """givena tFrameArray, create interpolated events between existing events
        tFrameArray: tStart, dur, eventFlag, interpMethod, interpExponet
            # event frames are len==5, others do not have interpExponet
        exponet can only be updated for each event"""


        # get a list of index values for events within tFrameArray
        eventFrameIndex = []
        for i in range(len(tFrameArray)):
            if tFrameArray[i][2] == 1: # check event status flag
                eventFrameIndex.append(i)
        
        if self.__len__() != len(eventFrameIndex):
            raise ValueError, 'tFrameArray does not contain all events stored: %s, %s' % (self.__len__(), len(eventFrameIndex))

        # iterate over all indexes less 1, as two are done at a time
        for i in range(self.__len__()-1):
            eStart = self._eventList[i]
            eEnd = self._eventList[i+1]

            # range of frames to create is between event frames start and end
            frameStart = eventFrameIndex[i] + 1
            frameEnd = eventFrameIndex[i+1] - 1

            # prepare list of parameters to clone in a dictionary
            # always include aux list, as some vals may not be numbers
            eventTemplate = {}
            for key in eStart.keys():
                if key not in active or key == 'aux':
                    eventTemplate[key] = copy.deepcopy(eStart[key])
                

            # create a dict of bpl objs to acces when creating frames
            # start and end times should be of events, not frames
            tStart = tFrameArray[eventFrameIndex[i]][0]
            tEnd = tFrameArray[eventFrameIndex[i+1]][0]
            # these values are only found w/ event frames
            interpolationMethod = tFrameArray[eventFrameIndex[i]][3]
            exponent = tFrameArray[eventFrameIndex[i]][4]

            bpArray = {}
            for pmtr in active:
                if pmtr == 'aux': continue

                valStart = eStart[pmtr]
                valEnd = eEnd[pmtr]
                boundaryPair = [(tStart, valStart), (tEnd, valEnd)]
    
                # create segment
                if interpolationMethod == 'linear': 
                    bp = bpf.LinearSegment(boundaryPair)
                elif interpolationMethod == 'halfCosine': 
                    bp = bpf.HalfCosineSegment(boundaryPair)
                elif interpolationMethod == 'power': 
                    bp = bpf.PowerSegment(boundaryPair, exp=exponent)
                bpArray[pmtr] = bp

            # handle aux by creating a list of lists
            if 'aux' in active:
                pmtr = 'aux'    
                valStartArray = eStart[pmtr]
                valEndArray = eEnd[pmtr]
                # create a list w/n bpArray to append w/n
                bpArray[pmtr] = []

                # iterate over every aux slot in the source aux list
                for iAux in range(len(eStart[pmtr])):
                    # some aux values may not be numbers
                    if not drawer.isNum(valStartArray[iAux]):
                        bpArray[pmtr].append(None)
                        continue # use vals in template

                    boundaryPair = [(tStart, valStartArray[iAux]),
                                         (tEnd, valEndArray[iAux])]
        
                    # create segment
                    if interpolationMethod == 'linear': 
                        bp = bpf.LinearSegment(boundaryPair)
                    elif interpolationMethod == 'cosine': 
                        bp = bpf.HalfCosineSegment(boundaryPair)
                    elif interpolationMethod == 'power': 
                        bp = bpf.PowerSegment(boundaryPair, exp=exponent)
                    bpArray[pmtr].append(bp)


            # create frames using eventTemplate and acccessing values from bpArray
            for frameIndex in range(frameStart, frameEnd+1):
                # use template to store all non-interpolated values
                eventDict = copy.deepcopy(eventTemplate)
                tFrameStart = tFrameArray[frameIndex][0]
                tFrameDur = tFrameArray[frameIndex][1]
                for pmtr in active:
                    if pmtr == 'aux': continue
                    eventDict[pmtr] = bpArray[pmtr](tFrameStart)
                if 'aux' in active:
                    pmtr = 'aux'    
                    for iAux in range(len(eStart[pmtr])):
                        # keep value set in template
                        if bpArray[pmtr][iAux] == None: continue
                        eventDict[pmtr][iAux] = bpArray[pmtr][iAux](tFrameStart)

                if snapSus: # will override template value
                    eventDict['sus'] = tFrameDur
                # add eventDictionary to this eventList
                self.append(eventDict)

            # if snap sus, alter sus of start and end events
            if snapSus:
                # get first frames start time, substract from event
                eStart['sus'] = tFrameArray[frameStart][0] - eStart['time']
                # ending event is not adjusted

        # sort after processing
        self.sort()

    
    def retrograde(self, type):
        """perform retrograde transformations directly on an event list
        note: assumes that events are sorted
        
        eventInverse: simply reverse the order of all events, using the
            forward time values w/ the reverse events
            keep reverse sustain values
        timeInverse: reverse all events,
            time values are calculted from difference between forward events 
            bkwards
            sustain values are reversed
        example, time, dur values
        
        eventSequence: eventInverse
        src(t,d) 100 3   post(t,d) 100 7
        src(t,d) 103 13 post(t,d) 103 7
        src(t,d) 116 7   post(t,d) 116 13
        src(t,d) 123 7   post(t,d) 123 7
        src(t,d) 130 13 post(t,d) 130 7
        src(t,d) 143 7   post(t,d) 143 13
        src(t,d) 150 7   post(t,d) 150 3
        
        eventSequence: timeInverse
        src(t,d) 100 1   post(t,d) 100 13
        src(t,d) 101 1   post(t,d) 113 7
        src(t,d) 102 3   post(t,d) 120 13
        src(t,d) 105 13 post(t,d) 133 3
        src(t,d) 118 7   post(t,d) 136 1
        src(t,d) 125 13 post(t,d) 137 1
        src(t,d) 138 3   post(t,d) 138 1
        """
        # creat index arrays
        iForward = range(self.__len__())
        iReverse = copy.deepcopy(iForward)
        iReverse.reverse()

        if type in ['off', None]:
            return None # do nothing
        elif type == 'eventInverse':
            alt = copy.deepcopy(self._eventList) # 1,2,3
            alt.reverse() # reverse events  3,2,1
            for i in iForward: # apply # 1,2,3
                # events are reversed; go throught them in order and apply
                # old time values in order from source
                t = self._eventList[i]['time']
                alt[i]['time'] = t
        elif type == 'timeInverse':
            alt = [] # 1,2,3
            altDur = 0 # time between events
            t = copy.copy(self._eventList[0]['time']) # get first event
            for i in iForward:
                j = iReverse[i]
                
                if i != iForward[-1]: # if not the last
                    # get the duration from the last event to the one before it
                    altDur = abs(self._eventList[j]['time'] - 
                                 self._eventList[j-1]['time'])
                else: # last index
                    altDur = self._eventList[j]['dur']
                # get reverse event
                event = copy.deepcopy(self._eventList[j])
                event['time'] = t # apply current time
                event['dur'] = altDur # apply newly calculated duration
                alt.append(event)
                # increment time
                t = t + altDur

        self._eventList = alt # reassign to eventList
            
    #-----------------------------------------------------------------------||--
    # format conversions
    def fillSplitScore(self, splitScore):
        """a split score stores all data in parallel lists
        note: attribute names in the split score follow internal texture
        naming, not event dict naming"""
        iEvent = 0
        delKey = []
        for event in self._eventList:
            splitScore['event'].append(iEvent)
            splitScore['time'].append(event['time'])
            splitScore['beatT'].append(event['bpm']) # called bpm here
            splitScore['sus'].append(event['sus'])
            splitScore['acc'].append(event['acc'])
            splitScore['ampQ'].append(event['amp'])
            splitScore['panQ'].append(event['pan'])
            splitScore['ps'].append(event['ps'])
            for i in range(0, len(event['aux'])): # may be a string!
                val = event['aux'][i]
                key = 'auxQ%i' % i
                splitScore[key].append(val)
            iEvent = iEvent + 1 # increment event count
        #print _MOD, 'fillSplitScore keys', splitScore.keys()
        return splitScore






#-----------------------------------------------------------------||||||||||||--
class EventSequenceSplit:
    """object for storing data for a texture, clone, or parameter
    in separate channels; output provided for graphing
    used for TImap, TCmap, TPmap

    split score holds data for either pre or post texture pmtr data
        or raw pmtr data provided w/ pmtr objects
    not data values are used all the time

    for textures, designed to work with an eventSequence object to get data
    event is index position (0 start),

    a split score can output with four possibilities
    tmRelation: pre/post     if the data values are pre tm, or post tm
    xRelation: event/time if x axis is either event based or time based
    with a clone, only a postTM relation is possible

    a srcObj may be a list of label, pmtrObj pairs
    
    will always ignore non-numeric data types
    
    arrays used for speed optimation of floating point values
    
    need aoInfo such as ssdr and sadr to get file paths
    this is not normally stored in ao.aoInfo, but packed here in command.py
    """
    def __init__(self, srcObj, srcFmt='t', eventCount=None, refresh=0,\
                     aoInfo=None):
        """srcFmt is either t (texture) or c (clone)
        or pg or pf, parameter generator or parameter filter"""
        self.srcObj = srcObj # a list of lable, pmtrObj apurs
        self.srcFmt = srcFmt
        # can be used to limt number of events shown
        # only implemented for pmtr event sequences (pg, pf, pr)
        #self.eventCount = eventCount 
        self.nEvent = eventCount # written w/ loadScoreList
        self.refresh = refresh
        self.aoInfo = aoInfo # may ne None, only needed to get paths
        # determine if strings skipped
        self.strBypass = 1 # set with load() method, default is to skip

        # get aux no if necessary
        if self.srcFmt in ['pg', 'pf', 'pr']:
            self.auxNo = 0
        elif self.srcFmt in ['t', 'c']:
            self.auxNo = self.srcObj.auxNo # must be clone or texture
            if self.srcFmt == 'c':
                if len(self.srcObj.esObj) == 0:
                    raise ValueError, 'clone with empty esObj cannot be graphed' 

        # all data elements other than aux values could be array objects

        # build template for split scire
        splitScore = {}

        # comm to all formats
        # eventCount can be unsigned longs
        splitScore['time'] = array.array('f')   
        splitScore['event'] = array.array('L') # indicies for each event
        # textures and clones require a complete represenation
        if self.srcFmt in ['t', 'c']: # a complete texture rep
            # data valyes; some not always available
            splitScore['beatT'] = array.array('f') #bpm 
            splitScore['dur'] = array.array('f')  
            splitScore['sus'] = array.array('f')  
            splitScore['acc'] = array.array('f')
            splitScore['ps'] = array.array('f') # ps real value
            splitScore['fieldQ'] = array.array('f')  # not in list score  
            splitScore['octQ'] = array.array('f') # not in list score  
            splitScore['ampQ'] = array.array('f')    
            splitScore['panQ'] = array.array('f')   
            for i in range(0, self.auxNo):
                splitScore['auxQ%i'%i] = [] 
        # raw parameter data only stores two values of any type
        elif self.srcFmt in ['pg', 'pf']:
            for label, lib, obj in self.srcObj:
                splitScore[label] = []
        # rhythms stores a speicial arrangement as well
        elif self.srcFmt in ['pr']: # rhythm returns 3 values
            splitScore['sus'] = array.array('f')
            splitScore['dur'] = array.array('f')
            splitScore['acc'] = array.array('f')

        # store order of presentation
        if self.srcFmt == 't': # texture
            self.pmtrOrder = ['time', 'beatT', 'acc', 'dur', 'sus', 'ps', 'fieldQ',
                                    'octQ', 'ampQ', 'panQ']
            for label in basePmtr.auxLabel(self.auxNo):
                self.pmtrOrder.append(label)
        elif self.srcFmt == 'c': # clone; dont show bpm, dur, frm texture
            self.pmtrOrder = ['time', 'sus', 'acc', 'ps', 'fieldQ',
                                    'octQ', 'ampQ', 'panQ']
            for label in basePmtr.auxLabel(self.auxNo):
                self.pmtrOrder.append(label)
        elif self.srcFmt in ['pg', 'pf']: # parameter generator, filter
            self.pmtrOrder = []
            for label, lib, obj in self.srcObj:
                self.pmtrOrder.append(label)
        elif self.srcFmt in ['pr']: # parameter rhythm
            self.pmtrOrder = ['dur', 'sus', 'acc']
        else:
            raise ValueError, 'bad src format'

        # store labels for each parameter
        self.pmtrArgs = {}
        for pmtr in self.pmtrOrder:
            self.pmtrArgs[pmtr] = ''
        self.splitScore = splitScore

    #-----------------------------------------------------------------------||--
    def _updateEventCount(self):
        self.nEvent = len(self.splitScore['event']) # store total number of events

    def _loadPmtrArgs(self):
        """get parameter data from srcObj
        also check for string types and remove them from pmtrArgs and pmtrOrder
        """
        delKey = []
        if self.srcFmt not in ['pg', 'pf', 'pr']: # parameter texture
            for key in self.srcObj.pmtrObjDict.keys():
                pObj = self.srcObj.pmtrObjDict[key]
                if pObj.outputFmt == 'str' and self.strBypass:
                    delKey.append(key)
                    continue # skip string outputs
                self.pmtrArgs[key] = pObj.repr('argsOnly')
        elif self.srcFmt in ['pg', 'pf']: # filter, generator
            for label, lib, pObj in self.srcObj:
                if pObj.outputFmt == 'str' and self.strBypass:
                    delKey.append(label)
                    continue # skip string outputs
                self.pmtrArgs[label] = pObj.repr('argsOnly')
        elif self.srcFmt in ['pr']: # rhythm
            label, lib, pObj = self.srcObj[0] # first is only significant
            self.pmtrArgs['dur'] = pObj.repr('argsOnly')
            self.pmtrArgs['sus'] = ''
            self.pmtrArgs['acc'] = ''
        # remove bad keys
        for key in delKey:
            self.pmtrOrder.remove(key)

    def _loadPostScore(self):
        """creates a new score w/ srcObj, 
        splits a score into a dictionary of labeled parameters values
        xLabel can be event or time; changes x label from time values to 
        event steps"""
        # use existing score if possible
        if len(self.srcObj.esObj) != 0 and self.refresh != 1:
            esObj = self.srcObj.getScore()
        else: # always do a post process to fill time values and event count
            # if this is a clone, scores needs data from texture
            ok = self.srcObj.score()
            if ok == -1 or self.srcObj.checkScore() == 0:
                raise ValueError, 'bad score generation' # error        
            esObj = self.srcObj.getScore()
        # uses esObj method with input obj of split score to update
        # split score may be empty here
        self.splitScore = esObj.fillSplitScore(self.splitScore)

    def _loadPreScore(self):
        """suply a srcObj instance and load fresh parameter data
        may overwrite some data obtained w/ loadScoreList
        note: preScore cannot be calculated from a clone"""
        for key in self.srcObj.pmtrObjDict.keys():
            if key not in self.pmtrOrder: # only parameters that are here
                continue
            pObj = self.srcObj.pmtrObjDict[key]
            if pObj.outputFmt == 'str': # cant do anything w/ strings
                del self.pmtrOrder[self.pmtrOrder.index(key)]
                continue
            self.splitScore[key] = [] # clear list, replace w/ new values
            pObj.reset() # reset parameter object
            for t in self.splitScore['time']: # run through time list
                self.splitScore[key].append(pObj(t)) # append data values
                
    def _loadRawParameter(self):
        """srcObj is a list of raw parameter objects
        optionally skip string storage with strBypass"""
        # add time values
        refDict = basePmtr.REFDICT_SIM
        # merge with aoInfo if around
        if self.aoInfo != None: # fill blank entries
            refDict['sadr'] = self.aoInfo['sadr'] # a list of paths
            refDict['ssdr'] = self.aoInfo['ssdr']
        
        # these are the same; why have both?
        self.splitScore['time'] = range(0, self.nEvent)
        self.splitScore['event'] = range(0, self.nEvent)

        for label, lib, pObj in self.srcObj:
            # check if strings are to be processed
            if pObj.outputFmt == 'str' and self.strBypass:
                continue
            self.splitScore[label] = [] # clear list, replace w/ new values
            pObj.reset() # reset parameter object
            if lib in ['genPmtrObjs']:
                for t in self.splitScore['time']: # run through time list
                    # append data values
                    self.splitScore[label].append(pObj(t, refDict)) 
            elif lib in ['filterPmtrObjs']:
                # create a dummy ref dict array
                refDictArray = [refDict] * self.nEvent
                # first element in srcObj list must be a general pmtr obj
                valArray = self.splitScore[self.srcObj[0][0]] # this gets label
                tArray = self.splitScore['time']
                self.splitScore[label] = pObj(valArray, tArray, refDictArray)
            elif lib in ['rthmPmtrObjs']:
                for t in self.splitScore['time']: # run through time list
                    dur, sus, acc = pObj(t, refDict)
                    self.splitScore['dur'].append(dur)
                    self.splitScore['sus'].append(sus)
                    self.splitScore['acc'].append(acc)

    #-----------------------------------------------------------------------||--             
    def load(self, tmRelation='pre', strBypass=1):
        self.strBypass = strBypass # will skip all pmtr args w/ string output
        # load all parameter args depending on srcFmt set at init
        self._loadPmtrArgs()
        if self.srcFmt not in ['pg', 'pf', 'pr']: # parameter texture
            self._loadPostScore() # always do first
            if tmRelation == 'pre' and self.srcFmt != 'c': # not clone
                self._loadPreScore()
        else:
            self._loadRawParameter()
        self._updateEventCount()

    def clean(self):
        """scrub the split score for bad data, such as strings"""
        delKeys = []
        for pmtr in self.pmtrOrder:
            if len(self.splitScore[pmtr]) == 0: # no data
                delKeys.append(pmtr)
            elif drawer.isStr(self.splitScore[pmtr][0]):
                delKeys.append(pmtr)
        for pmtr in delKeys:
            del self.splitScore[pmtr]
            del self.pmtrArgs[pmtr]
            self.pmtrOrder.remove(pmtr) # this is just a list
            
    def getTitle(self, pmtrLabel):
        """the title gotten here is used for graphics, and, with args is often too 
        long for a graphical display; thus, now just returning title w/o args"""
        pmtrStr = None # po name if available
        if self.pmtrArgs[pmtrLabel] != '':
            pmtrStr = self.pmtrArgs[pmtrLabel].split(',')[0] # first item is name
            if self.srcObj != None and not drawer.isList(self.srcObj):
                junk, fullPmtr = self.srcObj.decodePmtrName(pmtrLabel, 'usr')
                if fullPmtr != '': # assign fullPmtr name
                    pmtrLabel = fullPmtr
        # create title strings
        if pmtrStr != None: # default, optionally add more info
            title = '%s: %s' % (pmtrLabel, pmtrStr) 
        else:
            title = '%s' % (pmtrLabel) 
        return title

    def getCoord(self, pmtr, xRelation='event'):
        """get a data format as a list of coordinant pairs
        xRelation can be event or time
        """
        if self.splitScore[pmtr] == []: # no data
            return None # no data 
        coord = []
        xStep = self.splitScore[xRelation] # event or time
        i = 0
        for x in xStep: # add data plus xRelation to creat coord pairs
            if xRelation == 'event':
                coord.append((x, self.splitScore[pmtr][i]))
            elif xRelation == 'time':
                # add four data points to coord
                # y values are constant
                # x value is initial x plus sustain
                coord.append((x, self.splitScore[pmtr][i], 
                                  x + self.splitScore['sus'][i], 
                                  self.splitScore[pmtr][i]))
            i = i + 1
        return coord

    def getKeys(self):
        """get keys that have values,ignoring other keys
        some keys may not have values if they are pre
        used in drawin the split score
        """
        filter = [] # filtering not necessary if called after clean() method
        for pmtr in self.pmtrOrder:
            if len(self.splitScore[pmtr]) != 0: # no data
                filter.append(pmtr)
        return filter

    #-----------------------------------------------------------------------||--
    # event engines are polyphonic; these outputs are monophonic, or single
    # generator values; only provided output for one parameter objects
    
    def writeTable(self, filePath, sepStr='\t'):
        """return a tab-delmited table of all data in the split score
        format is a list of lines ready for writing
        this is used by TPexp to export parameter data quickly
        from events generated by an EventSequenceSplit
        """
        msg = []
        for key in self.getKeys(): # this gets pmtr obj groups, or arg slots
            dataLine = [self.getTitle(key)]
            for data in self.splitScore[key]:
                dataLine.append(str(data))
            msg.append(sepStr.join(dataLine))
            msg.append('\n')
        f = open(filePath, 'w')
        f.writelines(msg)
        f.close()

    def writeBuffer(self, filePath):
        """write and audio file from data 
        """
        # args are fp, ch, sr
        self.aObj = audioTools.AudioFile(filePath, 1)
        # this will mix all parameters into one smashed representation
        if self.srcFmt == 'pg':
            for key in self.getKeys():
                if key.lower().startswith('g'):
                    # values may not be normalized
                    self.aObj.insertMix(0, self.splitScore[key])
        elif self.srcFmt == 'pf':
            for key in self.getKeys():
                if key.lower().startswith('f'):
                    # values may not be normalized
                    self.aObj.insertMix(0, self.splitScore[key])              
        else:
            raise ValueError, 'unexpected src fmt'


#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
class Performer:
    """used only by EventMode
    can provide complete scores of all textures as flat data obj
    or can step through a score as a rt performnace
    does contain objects, and thus cannot be store 
        (this is unlike an esObj, which is simple a data structure)"""
    def __init__(self):
        self.polySeq = {} # data representation of calculated score       
        self.scoreCount = 0 # number of textures processed
        # no longer store in performer
        # determined by Engine in compatability check
        #self.instList = [] # list of instruments used

    def reset(self):
        self.polySeq = {}
        self.scoreCount = 0 # number of textures processed

    def sort(self):
        """sort all event lists; only called by EventMode"""
        #print _MOD, 'Performer: sorting all EventSequences' 
        for t in self.polySeq.keys(): # get texture names
            self.polySeq[t]['esObj'].sort()
            for c in self.polySeq[t]['TC'].keys():
                self.polySeq[t]['TC'][c]['esObj'].sort()
        
    def _packTexture(self, tName, t):
        """store texture data, encluding an eventList, in a dictionary
        store relevant data for engine processing"""
        self.polySeq[tName] = {} # a specialized dictionary
        self.polySeq[tName]['esObj'] = t.getScore() # store esObj copy
        self.polySeq[tName]['mute'] = t.mute
        self.polySeq[tName]['className'] = t.__module__
        self.polySeq[tName]['orcObj'] = t.getOrc() # ref to obj
        self.polySeq[tName]['inst'] = t.getInst() # get inst number
        self.polySeq[tName]['midiPgm'] = t.midiPgm
        self.polySeq[tName]['midiCh'] = t.midiCh # this is from 1 to 16
        self.polySeq[tName]['orcMapMode'] = t.orcMapMode # store mix mode
        self.polySeq[tName]['TC'] = {}
        self.scoreCount = self.scoreCount + 1 # only count if score successfull

    def _packClone(self, tName, cName, c):
        """store clone data, encluding an eventList, in a dictionary
        stored as part of clone's parent texture
        """
        self.polySeq[tName]['TC'][cName] = {}
        self.polySeq[tName]['TC'][cName]['esObj'] = c.getScore() # esObj
        self.polySeq[tName]['TC'][cName]['mute'] = c.mute
        self.scoreCount = self.scoreCount + 1 # count clone scores 

    # note: textures and clones already may have scores;
    # refreshing the scores here makes sense, but may not always be necessary
    def flattenSome(self, objList, refresh=1):
        """flatten reads and scores textures into a polySeq data dict
        score a polySeq, but only for objects that are in the list
        objects must be textures; clones cannot be scored this way"""
        self.reset()
        # use number as tName
        for i in range(0, len(objList)):
            tName = str(i)
            t = objList[i]
            #inst = t.getInst()
            #if inst not in self.instList: self.instList.append(inst)
            if refresh:
                ok = t.score() #returns -1 if score fails
                if not ok or t.checkScore() == 0:
                    print _MOD, 'texture failed to score', tName
                    continue
            self._packTexture(tName, t)

    def flattenAll(self, ao, refresh=1):
        """flatten reads and scores textures into a polySeq data dict
        generate a flat score, stored in polySeq, for all textures + clones
        in the athenaObject
        creates self.polySeq, a structured dictionary of score data
        score data is stored as an esObjuence obj
        the same format produced
        w/ each textures .score() method.
        must get scores for all texture and clones, even if muted
            a texture can be muted while a clone is not, so all data must be gen
        """
        textureLib = ao.textureLib
        cloneLib = ao.cloneLib
        self.reset()
        for tName in textureLib.keys():
            t = textureLib[tName]
            #inst = t.getInst()
            #if inst not in self.instList: self.instList.append(inst)
             # must always score, even if muted, so clone can be generated
            if refresh:
                ok = t.score() #returns -1 if score fails
                if not ok or t.checkScore() == 0:
                    print _MOD, 'texture failed to score', tName
                    continue
            self._packTexture(tName, t)
            # get necessary inputs for clones
            refDict = t.getRefClone()
            esObjTexture = self.polySeq[tName]['esObj'] 
            for cName in cloneLib.cNames(tName):
                c = cloneLib.get(tName, cName)
                # create a clone score w/ esObj from texture
                # a copy will be made w/n the cone
                if refresh:
                    ok = c.score(esObjTexture, refDict)
                    if not ok:
                        print _MOD, 'clone failed to score', tName, cName
                        continue
                self._packClone(tName, cName, c)


#-----------------------------------------------------------------||||||||||||--
# engines can be used at any time from the event mode, in any mode
# engines support a certain number of outputs
# and always have a default output
# some engines are the same as an EventMode, but not all 
# engines may write more than one file (csoundNative for instance)

# engines deal with the polyphonic nature of event lists, as represented
# in the poly sequnece; it may need to be converted to tracks, commented
# or other wise separated, etcetera

# there are engines that can work w/ any orchestra (text) and are thus
# independent of orchestas; each engine, however, requires an orchesta be 
# assigend to it at some point. in some cases, one engine may only work
# with one orchestra (csoundNative). in other cases, multiple (midiFile)

# there are engines that work w/ no orchestra: audioFile
# as no 'pitch' or 'pan' values are used, and no inst info is needed

class _OutputEngine:
    def __init__(self, emName, ref):
        """output engines: convert polySeq objects into files or streams?
        output engines are respoonsible for writing certain filestypes
        two engines cannot be used tt write the same filetype (.sco)
        
        each engine will have an internal orchestra
        this orchestra is determined by selectOutEngineOrc(), as well as 
        for converting mix values
        
        emName is the name of the currently active EventMode
        this may or may not effect which orchestra is used inside the engine
        for example, the text engine will always use the orc specified by em
        contrarywise, the csoundNative engine will always use its default orc
        
        ref is a ref dictionary with system value and strings needed in 
        processign; this is necessary to avoid passing an athenaObject to the 
        output object
        ref contains file paths for all necessary format based on str
        changes are made to ref to pass paths back to athenaObject
        
        engines store and modify a copy of a user provided outRequest
        engines may remove values from this list during _writePre
        if an engine is called with and empty outRequest, provide minimum
        
        write method does not deal w/ athenaObj, only with:
        ref (for paths) perfObj (passed with the write() method)          
        """
        self.ref = ref
        self.emName = emName # name of eventMode that is using this engine

        self.orcIncompat = [] # define orc sources tt are incompat w/ this engine
        self.orcObj = None # define name of orc used in converting mix vals
        # output data
        self.outComplete = [] # outpout formats that were written
        self.outRequest = [] # called with write operations
        self.outAvailable = None # provided w/ subclass
        self.outMin = None # provided w/ subclass
        # select which components work with a texutre
        # determined after assugment of perfObj and orcObj
        self.compatNames = [] # names of compat texutres
        self.compatInsts = [] # integer ids of compat insts
        
    def _outRequestCheck(self):
        """check to see tt at one of the engines outputs are specified
        if not, add to self.outRequest
        """
        outMinMatch = [] # scratch list to find outs that are in outavailable 
        if self.outRequest == []:
            self.outRequest = self.outMin
        else: # check to see tt output is one of the outputs available
            found = 0 
            for out in self.outRequest:
                if out in self.outAvailable:
                    found = found + 1
                if out in self.outMin:
                    outMinMatch.append(out)
            # must make sure that all min outs are provided
            if found == 0 or len(outMinMatch) < len(self.outMin):
                # add all minimums # these may not all get made (orc/sco if csd)
                for out in self.outMin:
                    if out not in self.outRequest:
                        self.outRequest.append(out)
        #print _MOD, 'post outRequestCheck', self.outRequest
        
    def _orcSelect(self):
        """determine which orchestra should be used with this engine
        in most cases, if an engine is active, it will only use one orc
        (for example, csoundNative always uses csoundNative orc)
        in other cases, an engine might be able to use multiple orchestras
        (for example, the text engine can process w/ any orchestra)
        in these cases, the engine's orc is specified by the emName
        """
        # base eventMode name, as well as engine's name
        orcName = selectOutEngineOrc(self.emName, self.name)
        return orc.factory(orcName)
    
    def _orcCompatability(self, polySeq):
        """determine which textures are compatabile with orchestra of this engine
        assign self.compatTexture and self.compatInst
        each engine will only use textures that have compataible orcs and insts       
        """     
        # determine which orc to use; emOrcObj (current orc of mode)
        # or orc of texture; prefer orc of mode if compatible w orc of text
        # if not, use orc of texture
        
        self.compatNames = [] # names of compat texutres
        self.compatInsts = [] # integer ids of compat insts
        
        # only need polySequence here; no longer pass perfObj
        # polySeq = perfObj.polySeq
        
        for t in polySeq.keys(): # get texture names
            tOrcObj = polySeq[t]['orcObj']
            inst = polySeq[t]['inst'] # inst number as integer
            if tOrcObj.name == self.orcObj.name: # assume match, full compat
                self.compatNames.append(t)
                if inst not in self.compatInsts: 
                    self.compatInsts.append(inst)
            else: # check if emOrc is compat w/ tOrc
                # see if tOrc is incompatabible w/ this Engine
                # inst may not be valid, but still work (midi files are an ex)
                if tOrcObj.name in self.orcIncompat:
                    print lang.WARN, 'texture %s (instrument %s, orchestra %s) incompatible with OutputEngine orchestra %s; change EventMode or edit instrument.' % (t, inst, tOrcObj.name, self.orcObj.name)
                else: # use this texture anyways                  
                    self.compatNames.append(t)
                    if inst not in self.compatInsts: 
                        self.compatInsts.append(inst)     
            # use this to test inst, but may not be necessary
            #if orcObj.instNoValid(inst): # check if inst no is valid
            # incompatible

    def _writePre(self):
        """look at output request and fix as necessary"""
        pass
        
    def _write(self):
        pass
    
    def _writePost(self):
        """update paths in ref as necessary"""
        pass
        
    def write(self, polySeq, outRequest=[]):
        """
        polySeq contains a dictionary of eventSequence objects
            when writing file, the appropriate outputs can be called from 
            the eventSequence
            from a perfObj has polySeq: flattened score representation
            perfObj not needed here
        the job of the output object is take all the converted eventSequence
            data and process is into the appropriate format, then write
            a file.
        outRequest is just a list of strings; not an array of objects as used
            elsewhere
        output request may or may include items in the output; if not
        default is always used
        """
        self.outRequest = copy.deepcopy(outRequest)
        # will suply minimum output if none in this engine specified
        self._outRequestCheck()
        # assign orc to be used with this engine, base on engine type and em
        
        # assign polySeq object from perfObject to a local varaiable 
        # for convenience
        # all engines use the same polySeq to ensure identical representations
        # do not change the polySeq, as may effect other output engines
        # an analysis of the polySeq should be performed before calling methods
        # below to determine which instrumetns are available:
        # each egine should store a list of valid instrument numbers and texture
        # names; thus each engine may filter the polySeq to only provide the
        # partial output
        self.polySeq = polySeq

        self.orcObj = self._orcSelect()
        # check compatability of this engine w/ its orc and included textures  
        # one orcObj will will be chosen for processing, assigned to self.orcObj
        # emOrcObj not compatabile w/ texture orc
        # also used for converting amp and pan values (mixAbs)      
        self._orcCompatability(self.polySeq)
        # assugn emOrcObj to orcObj for engine processing
        if self.compatNames == []: # no compatible textures
            return None # bail
            
        # self.orcObj = emOrcObj # assign orc of event mode?
            
        # call subclass methods to write output files of this engine
        self._writePre()
        self._write()
        self._writePost()
        
    #-----------------------------------------------------------------------||--
    # string and data processing conversion
    
    def _fmtHeadSco(self, headStr='', prepend=''):
        scoHead = []
        scoHead.append('%sathenaCL %s\n' % (prepend, self.ref['version']))
        scoHead.append('%s%s\n' % (prepend, lang.msgAthURL))
        timeStr = time.asctime(time.localtime())
        scoHead.append('%s%s\n' % (prepend, timeStr))
        scoHead.append('%soutput generator: %s (orchestra: %s)\n\n' % (prepend, 
            self.name, self.orcObj.name))
        if headStr != '':
            scoHead.append(headStr)
            scoHead.append('\n')
        return ''.join(scoHead)
        
    def _fmtComment(self, commentList, delimit=';'):
        commentStr = []
        commentStr.append(' %s' % delimit)
        for cmtPos in range(0, len(commentList)):
            cmtData = commentList[cmtPos]
            if drawer.isNum(cmtData):
                cmtData = round(commentList[cmtPos],4)
            cmtStr = str(cmtData)
            cmtStr = cmtStr.rjust(len(cmtStr)+1)
            commentStr.append(cmtStr)
            if cmtPos != len(commentList) - 1:
                commentStr.append(':')
        commentStr.append('\n')
        return ''.join(commentStr)

    def _fmtHeadTexture(self, className, tName, prepend=''):
        return '%sTM(%s), TI(%s)\n' % (prepend, className, tName)

    def _fmtHeadClone(self, className, tName, cName, prepend=''):
        return '%sTM(%s), TI(%s), TC(%s)\n' % (prepend, className, tName, cName)
        
    def _fmtTitleTexture(self, musicName, tName):
        """used for naming ac toolbox sections"""
        return '%s-%s' % (musicName, tName)
        
    def _fmtTitleClone(self, musicName, tName, cName):
        """used for naming ac toolbox sections"""
        return '%s-%s-%s' % (musicName, tName, cName)       
        
    def _strValue(self, value, ljust=8, sigDig=6, prefix='', postfix=' '):
        """given a value, prepare appropriate string version, 
        w/ default space at end (only needed w/ csound scores)"""
        if drawer.isStr(value):
            return '%s%s%s' % (prefix, value.ljust(ljust), postfix)
        elif drawer.isInt(value):
            return '%s%s%s' % (prefix, str(value).ljust(ljust), postfix)
        else: # assume is is a float
            val = round(value, sigDig)
            if sigDig == 0:
                val = int(val) # convert
            return '%s%s%s' % (prefix, str(val).ljust(ljust),
                                     postfix)

    def _strLabel(self, orderList, delimit=' ', prefix=''):
        """previde an event to sample, and return a key string
        orderList is names of each element; if not in dict key key is used
        aux values can be provided just with numbers; will be converted to
        stings
        """
        name = {'inst': 'instrument', 'time': 'timeStart', 'sus': 'timeSustain',
                  'amp': 'amplitude', 'ps':'pitch', 'fq':'frequency', 
                  'midiNote': 'midiNoteNumber', 'pan': 'panning'
                    }
        if orderList[-1] != 'comment':
            orderList.append('comment') # always last         
        label = []           
        for key in orderList:
            if key in name.keys():
                label.append(name[key])
            elif drawer.isInt(key):
                iStr = str(key).rjust(2)
                iStr = iStr.replace(' ', '0') # zero pad
                label.append('aux%s' % iStr)
            else: # not a number or a key
                label.append(key)
        return '%s%s\n' % (prefix, delimit.join(label))
        
    #-----------------------------------------------------------------------||--
    # covnert single eventList into necessary data structures, lists or strings

            
    def _translateCsoundExternalStr(self, orcMapMode, esObj):
        """exclude built in args for amp, ps, pan
        if a user needs pitch information from path
        can be obtained by using pathRead parameter object on an aux
        orcMapMode not really needed here, as ps/amp/pan not used in 
        external score
        """
        el = esObj.list() # get event list
        orderList = ['inst', 'time', 'sus',]
        for i in range(0, len(el[0]['aux'])): # just get first event
            orderList.append(i)
        label = self._strLabel(orderList, ' ', ';')
        msg = []
        for event in el:
            if event['acc'] == 0: continue # do not write rests         
            msg.append(self._strValue(event['inst'], 4, 1, 'i'))
            msg.append(self._strValue(event['time'], 12, 8))
            msg.append(self._strValue(event['sus'], 12, 8))           
            # skip all default perameters, go straight to aux
            for i in range(0, len(event['aux'])):
                msg.append(self._strValue(event['aux'][i], 10, 6))
            msg.append(self._fmtComment(event['comment']))
        return ''.join(msg), label # returns string

    def _translateCsoundNativeStr(self, orcMapMode, esObj):
        """convert single texture or clone event sequence object
        to the apropriate string"""
        el = esObj.list() # get event list
        orderList = ['inst', 'time', 'sus', 'amp', 'ps', 'pan']
        for i in range(0, len(el[0]['aux'])): # just get first event
            orderList.append(i)
        label = self._strLabel(orderList, ' ', ';')
        inst = el[0]['inst'] # get inst from first event
        msg = []
        for event in el:
            if event['acc'] == 0: continue # do not write rests         
            msg.append(self._strValue(event['inst'], 4, 1, 'i'))
            msg.append(self._strValue(event['time'], 12, 8))
            msg.append(self._strValue(event['sus'], 12, 8))
            
            val = self.orcObj.postMap(inst, 'amp', event['amp'], orcMapMode)
            msg.append(self._strValue(val, 10, 6))
            
            val = self.orcObj.postMap(inst, 'ps', event['ps'], orcMapMode)
            msg.append(self._strValue(val, 10, 6)) 

            val = self.orcObj.postMap(inst, 'pan', event['pan'], orcMapMode)
            msg.append(self._strValue(val, 10, 6))
            
            for i in range(0, len(event['aux'])):
                msg.append(self._strValue(event['aux'][i], 10, 6))
            msg.append(self._fmtComment(event['comment']))
        return ''.join(msg), label # returns string

    def _translateCsoundSilenceStr(self, orcMapMode, esObj):
        """
        p1 instrument / p2 time (seconds) / p3 duration (seconds)
        p4 MIDI key (can be a fraction) / p5 MIDI velocity / p6 phase
        p7 x (pan) / p8 y (depth) / p9 z (height)
        p10 pitch-class set (sum of pitch-classes as powers of 2), optional
        """
        # need to check if pitch and pan are in the appropriate
        # data format
        el = esObj.list() # get event list
        orderList = ['inst', 'time', 'sus', 'midiNote', 'velocity', 'phase',
                        'panX', 'panY', 'panZ', 'mason']
        label = self._strLabel(orderList, ' ', ';')
        inst = el[0]['inst'] # get inst from first event
        msg = []
        for event in el:
            if event['acc'] == 0: continue # do not write rests         
            assert len(event) == 11 # req length for csoundSilence
            i = self._strValue(event['inst'], 4, 1, 'i')
            start = self._strValue(event['time'], 12, 8)
            sus = self._strValue(event['sus'], 12, 8)
            
            val = self.orcObj.postMap(inst, 'amp', event['amp'], orcMapMode)
            amp = self._strValue(val, 8, 6)

            val = self.orcObj.postMap(inst, 'ps', event['ps'], orcMapMode)
            midiNote = self._strValue(val, 8, 6)
            
            val = self.orcObj.postMap(inst, 'pan', event['pan'], orcMapMode)
            panX = self._strValue(val, 8, 6, '', ' ')
            
            # parameters for silence; there must be 4 aux values
            phase = self._strValue(event['aux'][0], 8, 6)
            panY = self._strValue(event['aux'][1], 8, 6)
            panZ = self._strValue(event['aux'][2], 8, 6)
            mason = self._strValue(event['aux'][3], 6, 6)
            cmt = self._fmtComment(event['comment'])
            msg.append(''.join([i, start, sus, midiNote, amp, phase,
                                      panX, panY, panZ, mason, cmt]))
        msg.append('\n')
        return ''.join(msg), label # returns string

    #-----------------------------------------------------------------------||--
    def _translateMidiList(self, orcMapMode, esObj):
        """mid list is a short list of data
        consists only of tStart, sus, midiVel, midiPs, midiPan"""
        el = esObj.list() # get event list
        inst = el[0]['inst'] # get inst from first event
        midiList = []
        for event in el:
            if event['acc'] == 0: continue # do not write rests         
            tStart = event['time']
            sus = event['sus']
            midiVel = self.orcObj.postMap(inst, 'amp', event['amp'], orcMapMode)
            midiPs = self.orcObj.postMap(inst, 'ps', event['ps'], orcMapMode)
            midiPan = self.orcObj.postMap(inst, 'pan', event['pan'], orcMapMode)
            midiList.append((tStart, sus, midiVel, midiPs, midiPan))
        return midiList

    def _translateAcToolbox(self, orcMapMode, esObj, ch=0, pgm=0):
        """channel may be None; must provide default (0)
        build a list of string to avoid un packing later"""
        if ch == None: # most shift and correct channel info
            ch = 0
        else:
            ch = ch - 1
        el = esObj.list() # get event list
        inst = el[0]['inst'] # get inst from first event
        dataList = []
        midiPanLast = None # store last to filter data
        # add program change information, always starting at time 0
        dataStr = '(%s (%s %s))\n' % (self._strValue(0, 6, 0),
                            midiTools.decimalProgramChange(ch), pgm)
        dataList.append(dataStr)
        for event in el:
            if event['acc'] == 0: continue # do not write rests         
            tStart = event['time'] * 1000 # convert to ms
            sus = event['sus'] * 1000 # convert to ms
            midiVel = self.orcObj.postMap(inst, 'amp', event['amp'], orcMapMode)
            # cant use postMap here: no way to specify floating mid values
            # only alternative is build a custom orchestra...
            #midiPs = self.orcObj.postMap(inst, 'ps', event['ps'])
            # pitchTools will cap values b/n 0 and 127, but keep floats
            midiPs = pitchTools.psToMidi(event['ps'], 'nolimit')
            midiPan = self.orcObj.postMap(inst, 'pan', event['pan'], orcMapMode)
            # check if pan is different
            if midiPan != midiPanLast:
                midiPanLast = midiPan # pan is controller 10
                dataStr = '(%s (%s 10 %s))\n' % (self._strValue(tStart, 6, 0),
                                    midiTools.decimalController(ch), midiPan)
                dataList.append(dataStr)
            # only store note-on events now
            dataStr = '(%s (%s %s %s) %s)\n' % (self._strValue(tStart, 6, 0),# int?
                                    midiTools.decimalNoteOn(ch),
                                    self._strValue(midiPs, 8, 4), 
                                    self._strValue(midiVel, 4, 0), # an int 
                                    self._strValue(sus, 6, 0)) # assume this is an int
            dataList.append(dataStr)
        return dataList


    def _translateCollList(self, orcMapMode, esObj):
        """coll data must be integers; uses midi values"""
        el = esObj.list() # get event list
        inst = el[0]['inst'] # get inst from first event
        intList = []
        i = 0
        for event in el:
            if event['acc'] == 0: continue # do not write rests         
            # dur is calculated as distane between start times
            # as max/msp players are monophonic
            if i != len(el) - 1: # not last:
                eventNext = el[i+1]
                tSpan = eventNext['time'] - event['time'] # next minus this
            else: # last event
                tSpan = event['sus'] # no next, use dur
            # convert time to ms ints not s
            tSpan = int(round(tSpan * 1000))
            midiVel = self.orcObj.postMap(inst, 'amp', event['amp'], orcMapMode)
            #midiVel = self._ampToMidiVel(event['amp'], esObj.meta('ampMax'))
            midiPs = self.orcObj.postMap(inst, 'ps', event['ps'], orcMapMode)
            #midiPs = pitchTools.psToMidi(event['ps'], 'limit')
            midiPan = self.orcObj.postMap(inst, 'pan', event['pan'], orcMapMode)
            #midiPan = self._panToMidiPan(event['pan']) 
            # dont sub tuple
            intList.append('%s %s %s ' % (midiPs, midiVel, tSpan))
            i = i + 1
        return intList

    #-----------------------------------------------------------------------||--
    def _translateTextDelimitStr(self, orcMapMode, esObj, delimit='\t'):
        """used for creating both a plain text file and a tab delimitted
        file"""
        el = esObj.list() # get event list
        orderList = ['inst', 'time', 'sus', 'amp', 'midiNote', 'pan']
        for i in range(0, len(el[0]['aux'])): # just get first event
            orderList.append(i)
        label = self._strLabel(orderList, delimit)
        inst = el[0]['inst'] # get inst from first event
        msg = []
        for event in el: # set all ljust to 0
            if event['acc'] == 0: continue # do not write rests         
            msg.append(self._strValue(event['inst'], 0, 1, '', delimit))
            msg.append(self._strValue(event['time'], 0, 8, '', delimit))
            msg.append(self._strValue(event['sus'], 0, 8, '', delimit))
            # amp values will be determined by eventMode orc
            val = self.orcObj.postMap(inst, 'amp', event['amp'], orcMapMode)
            msg.append(self._strValue(val, 0, 6, '', delimit))
            # pitch format will be determined by orc of eventMode
            val = self.orcObj.postMap(inst, 'ps', event['ps'], orcMapMode)
            #psName = pitchTools.psToMidi(event['ps'], 'nolimit') 
            msg.append(self._strValue(val, 0, 6, '', delimit)) 
            
            val = self.orcObj.postMap(inst, 'pan', event['pan'], orcMapMode)
            msg.append(self._strValue(val, 0, 6, '', delimit))
            
            for i in range(0, len(event['aux'])):
                msg.append(self._strValue(event['aux'][i], 0, 6, '', delimit))
            # comment has return carriage
            msg.append(self._fmtComment(event['comment'], 'comment:'))
        return ''.join(msg), label
        
        


#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
class EngineAudioFile(_OutputEngine):
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineAudioFile'
        self.doc = lang.docOeAudioFile
        # compatable with all orchestras
        self.orcIncompat = []
        self.outAvailable = ['audioFile']
        self.outMin = ['audioFile']
        self.unitSynthesizerMethod = 'direct'

    def _translateAudioFile(self, orcMapMode, esObj, audioMixObj, method=None):
        """takes an audioMixObject and adds samples to it;
        progressive mixes layerd textures upon each other 
        
        xList shoudl use an array
        audioFile uses the 'generic' orchestra (base-class) to force
            values (from the event list) to stay between zero and one
        """
        el = esObj.list() # get event list

        # start = el[0]['time'] # get start from first event
        # presently, writes all textures and clones at the same location
        # should find a method to localize position relative to frames
        pos = 0 # insert position at zero for now

        xList = [] # presently have to provide data as a list
        for event in el: # set all ljust to 0
            # must right silent events; this used ot be active
            #if event['acc'] == 0: continue

            # limit values b/n 0 and 1 w/ "generic" orcestra
            val = self.orcObj.postMap(1, 'amp', event['amp'], orcMapMode)
            xList.append(val) # get amp values
        # provide a position, a unit list to mix in, and a method
        # this will replace all datall

        audioMixObj.insertMix(pos, xList, method)
        #audioMixObj.insertMixUnit(framePos, xList, method)
        return audioMixObj
        
    def _translatePoly(self):
        """set self.polySeqStr w/ complet orc from self.polySeq
        """
        try: # aiff tools may not be available on a given platform
            # will raise an import error
            # may need to delete old file here
            self.aObj = audioTools.AudioFile(self.ref['pathAudioSynth'], 1)
        except (ImportError, IOError):
            return 0 # failure

        # need to always clear the audio file; if an existing file is alreayd
        # in place, audio will be mixed into this existing file
        self.aObj.clear()

        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = 1 # tDict['orcMapMode'] # force midMode to normalize
            className = tDict['className']
            esObj = tDict['esObj']
            if not tDict['mute']: # pass object to mix data into
                self.aObj = self._translateAudioFile(orcMapMode, esObj, self.aObj,
                                                                self.unitSynthesizerMethod)
            for cName in tDict['TC'].keys():
                if not tDict['TC'][cName]['mute']:
                    esObj = tDict['TC'][cName]['esObj'] 
                    self.aObj = self._translateAudioFile(orcMapMode, esObj,
                                              self.aObj, self.unitSynthesizerMethod)
        return 1 # sucess
        
    def _write(self):
        """ """
        ok = self._translatePoly() # wil write file
        if ok:
            self.outComplete.append('audioFile')
            self.ref['pathView'] = self.ref['pathAudioSynth']


#-----------------------------------------------------------------||||||||||||--
class EngineCsoundNative(_OutputEngine):
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineCsoundNative'
        self.doc = lang.docOeCsoundNative
        # define orcs that are not compatible w/ this engine
        # this engine can only use its own orc
        self.orcIncompat = ['csoundExternal', 'csoundSilence', 'generalMidi',
                                  'generalMidiPercussion']
        self.outAvailable = ['csoundOrchestra', 'csoundBatch', 
                                        'csoundData', 'csoundScore']
        # min out should be score, orc, bat; csd is an option
        self.outMin = ['csoundOrchestra', 'csoundScore', 'csoundBatch']
        # outComplete, pathComplete defined in parent
        self.polySeqStr = None # score as single, format specific string
                
    def _genCommandStr(self, csd=1):
        """creates a .bat string, and a plain list of render options
        there seems to be an error now in the windows version of this now"""
        if os.name == 'mac':     
            if self.ref['nameCsoundCreator'] == 'VRmi':
                audioDirFlag = '\"-X' + self.ref['pathDirRoot'] + '\" ' 
                audioPathFlag = '\"-o' + self.ref['audioName'] + '\" '
            else: # 'sNoC' for newMacCsound(Ingalls), 
                audioDirFlag = '' 
                # quotes optional
                audioPathFlag = '-o' + self.ref['pathAudio'] + ' '
            batFileHead = 'Csound '
        elif os.name == 'posix':
            audioDirFlag = '' # not used
            # quotes optional
            audioPathFlag = '\"-o' + self.ref['pathAudio'] + '\" ' 
            # could change dir or try to set env variables here...
            batFileHead = '#! /bin/sh \n%s ' % self.ref['pathCsound']
        else: # win or other
            audioDirFlag = '' # not used
            # quotes req on win; not sure if space after 0 is req
            audioPathFlag = '\"-o' + self.ref['pathAudio'] + '\" '  
            batFileHead = '@ECHO off\nc:\ncd %s\n%s ' % (self.ref['pathDirCsound'],
                                                                        self.ref['nameExeCsound'])
        renderOpt = ('-m2 '+ # msg level. Sum 1=amps, 2=out-of-range, 4=warnings
            '-d ' + # suppress all displays (-d) (ascii displays -g)
            self.ref['audioFlag'] +               
            '-b1024 ' + # sample frames (or -kprds) per sound I/O buffer, was 8192
            '-B1024 ' + # samples per hardware sound I/O buffer, was 8192
            audioDirFlag +   # Sound File Directory (mac only)
            audioPathFlag)   # other plats use full path here
        if csd: 
            pathOpt =  '\"' + self.ref['pathCsd'] + '\" '
        else: # no csd, use orc and sco path
            pathOpt = ('\"' + self.ref['pathOrc'] + '\" ' + '\"' + 
                                    self.ref['pathSco'] + '\"\n')
        batStr = (batFileHead + renderOpt + pathOpt)
        return batStr, renderOpt # needed for csd

    def _writeBat(self, csd):
        """writes a bat file"""
        batStr, renderOpt = self._genCommandStr(csd)
        f = open(self.ref['pathBat'] , 'w')     
        f.write(batStr)
        f.close()       
        # sytem dependent post-adjustments to batch file
        if os.name == 'mac': # 'VRmi' (Mills), 'sNoC' (Ingalls)
            osTools.rsrcSetCreator(self.ref['pathBat'], 
                                          self.ref['nameCsoundCreator'], 'TEXT')
        elif os.name == 'posix':        
            os.chmod(self.ref['pathBat'], 0755) #makes executable (744=rwxr--r--) 
        else: # win or other
            pass
        self.outComplete.append('csoundBatch')

    def _writeCsd(self):
        """write a csd file given sco and orc strings
        must be done after calling self.translate()
        and after creating orc srcStr
        uses score in self.polySeqStr
        """
        assert self.orcObj.srcStr != None
        batStr, csdOptions = self._genCommandStr(1) # 1 expects a csd string
        xmlHead = '<?xml version="1.0"?>\n' # add?
        msg = []
        msg.append('<CsoundSynthesizer>\n\n')
        if os.name == 'mac':
            optStr = "%s/n%s/n%s/n/n%s" % ('<MacOptions>', 2, 1, 
                     '-b64 -A -s -m0 -K -B0 -Lstdin </MacOptions>')
        optStr = '<CsOptions>\n' + csdOptions + '\n\n' + '</CsOptions>\n'
        msg.append(optStr)
        msg.append('%s\n%s%s\n\n' % ('<CsInstruments>', self.orcObj.srcStr,
                                              '</CsInstruments>'))
        msg.append('%s\n%s%s\n\n' % ('<CsScore>', self.polySeqStr,
                                              '</CsScore>'))
        msg.append('</CsoundSynthesizer>\n')
        f = open(self.ref['pathCsd'] , 'w')
        f.writelines(msg)
        f.close()    
        # sytem dependent post-adjustments to batch file
        if os.name == 'mac':
            osTools.rsrcSetCreator(self.ref['pathCsd'], 
                                          self.ref['nameCsoundCreator'], 'TEXT')
        elif os.name == 'posix':        
            pass
        else: # win or other
            pass
        self.outComplete.append('csoundData')
        
    #-----------------------------------------------------------------------||--
    def _translatePoly(self):
        """set self.polySeqStr w/ complet orc from self.polySeq
        """
        msg = []
        # may pass instrument list here to get only fTables
        # for specific instruments
        headStr = self.orcObj.getScoFtables()
        msg.append(self._fmtHeadSco(headStr, ';'))
        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = tDict['orcMapMode']
            className = tDict['className']
            if not tDict['mute']:
                msg.append(self._fmtHeadTexture(className, tName, ';'))
                esObj = tDict['esObj']
                data, label = self._translateCsoundNativeStr(orcMapMode, esObj)
                msg.append(label)
                msg.append(data)
            for cName in self.polySeq[tName]['TC']:
                if not tDict['TC'][cName]['mute']:
                    msg.append(self._fmtHeadClone(className, tName, cName, ';'))
                    esObj = tDict['TC'][cName]['esObj']
                    data, label = self._translateCsoundNativeStr(orcMapMode, esObj)
                    msg.append(label)
                    msg.append(data)
        self.polySeqStr = ''.join(msg)

    def _writeSco(self):
        f = open(self.ref['pathSco'], 'w')
        f.write(self.polySeqStr)      
        f.close()   
        self.outComplete.append('csoundScore')

    def _writeOrc(self):
        """write orchestra already constructed in _write Method"""
        assert self.orcObj.srcStr != None
        f = open(self.ref['pathOrc'], 'w')
        f.write(self.orcObj.srcStr)   
        f.close()   
        self.outComplete.append('csoundOrchestra')

    def _writePre(self):
        """if csd specified remove orc and score"""
        # csd only works w/ csound native
        if 'csoundData' in self.outRequest: 
            # check for sco and orc, remove
            for out in ['csoundOrchestra', 'csoundScore']:
                if out in self.outRequest:
                    self.outRequest.remove(out)
            if 'csoundData' not in self.outRequest:
                self.outRequest.append('csoundData')
            
    def _write(self):
        """translate and write all files """
        self._translatePoly()
        # update orcObj.srcStr
        # instList may have instruments not compatiable with this orchestra?
        self.orcObj.constructOrc(self.ref['optionNchnls'], self.compatInsts)
        if 'csoundBatch' in self.outRequest:
            if 'csoundData' in self.outRequest:
                self._writeBat(1)
            else:
                self._writeBat(0)
        # assumes tt redundant outs are not selected: csoundData and csoundScore
        if 'csoundData' in self.outRequest:
            self._writeCsd()
        else: # if csd, dont do score and orc
            if 'csoundScore' in self.outRequest:
                self._writeSco()
                self.ref['pathView'] = self.ref['pathSco']
            if 'csoundOrchestra' in self.outRequest:
                self._writeOrc()

    def _writePost(self):
        """post writing updates as necessary
        self.outComplete set above"""
        if 'csoundData' in self.outComplete:
            self.ref['pathView'] = self.ref['pathCsd']
        else:
            if 'csoundScore' in self.outComplete:
                self.ref['pathView'] = self.ref['pathSco']


#-----------------------------------------------------------------||||||||||||--
class EngineCsoundExternal(_OutputEngine):
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineCsoundExternal'
        self.doc = lang.docOeCsoundExternal
        # compatable with all orchestras
        self.orcIncompat = []
        self.outAvailable = ['csoundScore']
        self.outMin = ['csoundScore']

    def _translatePoly(self):
        """set self.polySeqStr w/ complet orc from self.polySeq
        """
        msg = []
        msg.append(self._fmtHeadSco('', ';'))
        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = tDict['orcMapMode']
            className = tDict['className']
            if not tDict['mute']:
                msg.append(self._fmtHeadTexture(className, tName, ';'))
                esObj = tDict['esObj']
                data, label = self._translateCsoundExternalStr(orcMapMode, esObj)
                msg.append(label)
                msg.append(data)
            for cName in tDict['TC'].keys():
                if not tDict['TC'][cName]['mute']:
                    msg.append(self._fmtHeadClone(className, tName, cName, ';'))
                    esObj = tDict['TC'][cName]['esObj'] 
                    data, label = self._translateCsoundExternalStr(orcMapMode, esObj)
                    msg.append(label)
                    msg.append(data)
        self.polySeqStr = ''.join(msg)

    def _write(self):
        """ """
        self._translatePoly()
        f = open(self.ref['pathSco'], 'w')
        f.write(self.polySeqStr)      
        f.close()   
        self.outComplete.append('csoundScore')
        self.ref['pathView'] = self.ref['pathSco']
                
                
                
#-----------------------------------------------------------------||||||||||||--
class EngineCsoundSilence(_OutputEngine):
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineCsoundSilence'
        self.doc = lang.docOeCsoundSilence      
        # not compatable w/ any other orchestras
        # as 4 aux number are necessary
        self.orcIncompat = ['csoundExternal', 'csoundNative', 'generalMidi',
                                  'generalMidiPercussion']
        self.outAvailable = ['csoundScore']
        self.outMin = ['csoundScore']

    def _translatePoly(self):
        """set self.polySeqStr w/ complet orc from self.polySeq
        """
        msg = []
        msg.append(self._fmtHeadSco('', ';'))
        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = tDict['orcMapMode']
            className = tDict['className']
            if not tDict['mute']:
                msg.append(self._fmtHeadTexture(className, tName, ';'))
                esObj = tDict['esObj']
                data, label = self._translateCsoundSilenceStr(orcMapMode, esObj)
                msg.append(label)
                msg.append(data)
            for cName in tDict['TC'].keys():
                if not tDict['TC'][cName]['mute']:
                    msg.append(self._fmtHeadClone(className, tName, cName, ';'))
                    esObj = tDict['TC'][cName]['esObj'] 
                    data, label = self._translateCsoundSilenceStr(orcMapMode, esObj)
                    msg.append(label)
                    msg.append(data)
        self.polySeqStr = ''.join(msg)

    def _write(self):
        """ """
        self._translatePoly()
        f = open(self.ref['pathSco'], 'w')
        f.write(self.polySeqStr)      
        f.close()   
        self.outComplete.append('csoundScore')
        self.ref['pathView'] = self.ref['pathSco']


#-----------------------------------------------------------------||||||||||||--
class EngineMaxColl(_OutputEngine):
    """used to translate from athenaCL format to midi int score format
    int format is used to get athenaCL data into Max/MSP or similar
    no distinctiong between start time and duration, as notes are triggered
    tracks are assigned a sequential number
    all values are converted to integers (midi pitch, midi vel, ms dur)
    uses midi integer values for pitch and amp
    in order pitch, vel, dur (ms)
    stored as chNum, val val val;
    usefull for importing into a coll in max/msp
    note: always uses a midi orchestra
    """
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineMaxColl'
        self.doc = lang.docOeMaxColl
        self.trackList = []
        # define orcs that are not compatible w/ this engine
        self.orcIncompat = [] # all orchestras compatable
        self.outAvailable = ['maxColl']
        self.outMin = ['maxColl']

    def _translatePoly(self):
        """tramslates a athenaCL score to midi score format as defined                  
        elsewhere
        """
        trackList = []
        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = tDict['orcMapMode']
            ch = tDict['midiCh']
            pgm = tDict['midiPgm']
            if not tDict['mute']:
                esObj = tDict['esObj']
                intSco = self._translateCollList(orcMapMode, esObj)
                trackList.append((tName, pgm, ch, intSco))
            for cName in tDict['TC'].keys():
                if not tDict['TC'][cName]['mute']:
                    esObj = tDict['TC'][cName]['esObj']
                    intSco = self._translateCollList(orcMapMode, esObj)
                    trackList.append(('%s-%s' % (tName, cName), pgm, ch, intSco))
        self.trackList = trackList

    def _write(self):
        """ """
        assert 'maxColl' in self.outRequest 
        self._translatePoly()
        fileLines = []
        partNo = 1 # cant use ch or program, just asign ints
        for part in self.trackList:
            scoStr = ''.join(part[3])
            fileLines.append('%s, %s;\n' % (partNo, scoStr))
            partNo = partNo + 1 # no limit on index no
        f = open(self.ref['pathMaxColl'], 'w')
        f.write(''.join(fileLines))
        f.close()     
        self.outComplete.append('maxColl')
        
    def _writePost(self):
        self.ref['pathView'] = self.ref['pathMaxColl']

#-----------------------------------------------------------------||||||||||||--
class EngineMidiFile(_OutputEngine):
    """writes a midi file"""
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineMidiFile'
        self.doc = lang.docOeMidiFile
        # define orcs that are not compatible w/ this engine
        self.orcIncompat = [] # all orchestras compatable
        self.outAvailable = ['midiFile']
        self.outMin = ['midiFile']
        # store structured data
        self.trackList = []

    def _translatePoly(self):
        """tramslates a athenaCL score to midi score
        """
        trackList = []
        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = tDict['orcMapMode']
            ch = tDict['midiCh'] # need w/ or w/o mute
            pgm = tDict['midiPgm']
            if not tDict['mute']:
                esObj = tDict['esObj']
                midiSco = self._translateMidiList(orcMapMode, esObj)
                trackList.append((tName, pgm, ch, midiSco))
            for cName in tDict['TC'].keys():
                if not tDict['TC'][cName]['mute']:
                    esObj = tDict['TC'][cName]['esObj']
                    midiSco = self._translateMidiList(orcMapMode, esObj)
                    trackList.append(('%s-%s' % (tName, cName), pgm, ch, midiSco))
        self.trackList = trackList

    def _write(self):
        """ """
        assert 'midiFile' in self.outRequest
        self._translatePoly()
        midiObj = midiTools.MidiScore(self.trackList, self.ref['nameMusic'],
                                                self.ref['optionMidiTempo'])
        midiObj.write(self.ref['pathMid'])
        self.outComplete.append('midiFile')
        
    def _writePost(self):
        self.ref['pathView'] = self.ref['pathMid']


#-----------------------------------------------------------------||||||||||||--
class EngineAcToolbox(_OutputEngine):
    """writes a midi file"""
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineAcToolbox'
        self.doc = lang.docOeAcToolbox
        # define orcs that are not compatible w/ this engine
        self.orcIncompat = [] # all orchestras compatable
        self.outAvailable = ['acToolbox']
        self.outMin = ['acToolbox']
        # store structured data
        self.codeList = []
        self.codeCmt = 'created with %s' % lang.msgAth

    def _acSection(self, title, dataList, dur):      
        """must convert dur from s to ms"""
        msg = []
        h = """(define %s (make-instance     'section
    :input '(make-from-midi-file 'section)
    :events '(""" % title
        # comment is last quote
        t = """  ) 
    :duration %s 
    :clock-unit nil)    "%s")""" % (self._strValue(dur * 1000, 6, 0), self.codeCmt) 
        msg.append(h)
        for event in dataList: # events are already strings w/ line cariage
            msg.append(event)
        msg.append(t)
        msg.append('\n')
        return ''.join(msg)

    def _acParallelSection(self, title, sectionList, dur):      
        """must convert dur from s to ms
        dur does not seem to be necesary here; can set to nil"""
        msg = []
        h = """(define %s (make-instance     'section
    :input '(make-parallel-section """ % title
        t = """  ) 
    :duration nil 
    :clock-unit nil)    "%s")
(setf (get-events %s)
    (get-events (make-variant %s)))
    """ % (self.codeCmt, title, title) #self._strValue(dur * 1000, 6, 0) 
        msg.append(h)
        for s in sectionList: # events are already strings w/ line cariage
            msg.append(s)
            msg.append('\n')
        msg.append(t)
        msg.append('\n')
        return ''.join(msg)
  
    def _translatePoly(self):
        self.codeList = []      
        # it is necessary to lead with this to permit a parallel section
        # loading error
        self.codeList.append('(setf *convert-from-old-midi-format* nil)\n')
        sectionList = [] # store section names for parallel section
        completeDur = 0 # does this need to be filled?
        musicName = self.ref['nameMusic']
        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = tDict['orcMapMode']
            ch = tDict['midiCh'] # need w/ or w/o mute
            pgm = tDict['midiPgm']
            if not tDict['mute']:
                esObj = tDict['esObj']
                totalDur = esObj.getTotalDuration()
                dataList = self._translateAcToolbox(orcMapMode, esObj, ch, pgm)
                title = self._fmtTitleTexture(musicName, tName)
                self.codeList.append(self._acSection(title, dataList, totalDur))
                sectionList.append(title)
            for cName in tDict['TC'].keys():
                if not tDict['TC'][cName]['mute']:
                    esObj = tDict['TC'][cName]['esObj']
                    totalDur = esObj.getTotalDuration()
                    dataList = self._translateAcToolbox(orcMapMode, esObj, ch, pgm)
                    title = self._fmtTitleClone(musicName, tName, cName)
                    self.codeList.append(self._acSection(title, dataList, totalDur))
                    sectionList.append(title)
        # write a parallel section of all individual sections
        self.codeList.append(self._acParallelSection(musicName, 
                                                sectionList, completeDur))
        
    def _write(self):
        """ """
        assert 'acToolbox' in self.outRequest
        self._translatePoly()
        f = open(self.ref['pathAct'], 'w')
        f.writelines(self.codeList)
        f.close()
        # sytem dependent post-adjustments to batch file
        if os.name == 'mac': # ('ACTP', 'ACEX')
            osTools.rsrcSetCreator(self.ref['pathAct'], 'ACTP', 'ACEX')
        elif os.name == 'posix':
            if drawer.isDarwin(): # try only if darwin
                try:
                    osTools.rsrcSetCreator(self.ref['pathAct'], 'ACTP', 'ACEX')
                except ImportError: pass # do nothing 
        else: pass # win or other
        self.outComplete.append('acToolbox')
        
    def _writePost(self):
        pass


#-----------------------------------------------------------------||||||||||||--
class EngineText(_OutputEngine):
    def __init__(self, emName, ref):
        _OutputEngine.__init__(self, emName, ref) # provide event name
        self.name = 'EngineText'
        self.doc = lang.docOeText
        self.orcIncompat = [] # compat w/ all orchestras
        self.outAvailable = ['textTab', 'textSpace']
        self.outMin = ['textTab']

    def _translatePoly(self, delimit):
        """set self.polySeqStr w/ complet orc from self.polySeq
        """
        msg = []
        msg.append(self._fmtHeadSco(''))
        for tName in self.compatNames:
            tDict = self.polySeq[tName]
            orcMapMode = tDict['orcMapMode']
            className = tDict['className']
            if not tDict['mute']:
                msg.append(self._fmtHeadTexture(className, tName,))
                esObj = tDict['esObj']
                data, label = self._translateTextDelimitStr(orcMapMode, esObj, 
                                                                          delimit)
                msg.append(label)
                msg.append(data)
            for cName in tDict['TC'].keys():
                if not tDict['TC'][cName]['mute']:
                    msg.append(self._fmtHeadClone(className, tName, cName,))
                    esObj = tDict['TC'][cName]['esObj']  
                    data, label = self._translateTextDelimitStr(orcMapMode, esObj,
                                                                              delimit)
                    msg.append(label)
                    msg.append(data)
        self.polySeqStr = ''.join(msg)

    def _write(self):
        """ """
        #print _MOD, 'calling text engine write method'
        for out in self.outRequest:
            if out in ['textTab', 'textSpace']:
                if out == 'textTab':
                    self._translatePoly('\t')
                    fp = self.ref['pathTxtTab']
                if out == 'textSpace':
                    self._translatePoly(' ')
                    fp = self.ref['pathTxtSpace']
            else:
                continue # cannot process anything else
            f = open(fp, 'w')
            f.write(self.polySeqStr)      
            f.close()   
            self.outComplete.append(out)
            self.ref['pathView'] = fp








#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
class EventMode:
    """this object handles multiple output methods, selecting
    which can output when, reporting the results
    Performance object is created here as well
    
    ao is athenaObject; will be used for processing unless a list of textures
    are supplied w/ process method
    
    name is the declared name of this event mode
    
    for a given event mode, there is only one orchestra available
    if this orchestra does not work with an output, output may still be
    calculated   
    """
    def __init__(self, ao, name):
        self.name = eventModeParser(name) # needed to get default orc update
        if self.name == None: raise ValueError, 'no such EventMode: %s' % name
        self.ao = ao
        # not necessary to store perfObj, as created only w/ process method
        #self.perfObj = None # will be made w/ call
        self.ref = {} # dictionary of path names
        #no longer done at init, but w/ process
        #self._updateOrc()
        self.rootPath = None # assigned w/ method
        
        #keep a local copy of all output format objects, keyed by format name
        self.outFormatRef = outFormat.factory('all')
        
        # all ref keys used by engines to write files on process runs                            
        #self.keyWritePaths = ['pathAudioSynth', 'pathSco', 'pathBat', 'pathOrc',
        #    'pathXml', 'pathMid', 'pathCsd', 'pathMaxColl', 'pathTxtTab',
        #    'pathTxtSpace']
        
    #-----------------------------------------------------------------------||--
    # tools for init processing of paths and other data

    def _getAudioFlags(self):
        """used for csound, as well as common file path naming
        returns extsion as well as csound flag
        converst from athenaCL representation to file extensions
        """
        # leave space after flag
        usrFileFormat = self.ao.external.getPref('external','audioFileFormat')
        if    usrFileFormat == 'aif': return '.aif', '-A ' 
        elif usrFileFormat == 'wav': return '.wav', '-W ' 
        elif usrFileFormat == 'sd2': return '.sd2', ''
        #no longer supported
        #elif usrFileFormat == 'ircam': return '.sf', '-J '
        
    def _initRefNames(self):
        """collect necessary data from athenaObj into a dictionary
        this includes all necessary paths for writing all files
        
        all paths derived from rootPath as a root file. 
        note: a future version might take rootPath as a directory and bundle 
        content
        """
        assert self.rootPath != None
        # name music is just the file name, no path, no extensions
        dir, file = os.path.split(self.rootPath)
        self.ref['nameMusic'], x = osTools.extSplit(file) # lop off .sco
        self.ref['audioExt'], self.ref['audioFlag'] = self._getAudioFlags()
        self.ref['audioName'] = self.ref['nameMusic'] + self.ref['audioExt']
        # csound creator only used for macos resources setting
        self.ref['nameCsoundCreator'] = self.ao.external.getPref('external', 
                                            'csoundCreatorCode') 
        # extra data
        self.ref['version'] = self.ao.aoInfo['version']
        self.ref['optionNchnls'] = self.ao.nchnls
        self.ref['optionMidiTempo'] = self.ao.midiTempo
        
    def _absPath(self, ext):
        "builds the appropriate path from an extension"
        path = os.path.join(self.ref['pathDirRoot'], (self.ref['nameMusic'] +
                                                                     ext))
        return path
                                                                        
    def _initRefPaths(self):
        assert self.rootPath != None
        # get data for convenience
        self.ref['pathUsr'] = self.rootPath # store usr path
        self.ref['pathDirRoot'], fileName = os.path.split(self.rootPath)
        dirRoot = self.ref['pathDirRoot']
        nameMusic = self.ref['nameMusic']
        # update all path names
        # these need to be done here so that output objects do not over-write
        # used for csound output after rendering
        self.ref['pathAudio'] = self._absPath(self.ref['audioExt'])
        # this automatically loads all paths in output formats
        for fmt in self.outFormatRef:
            self.ref[fmt.emKey] = self._absPath(fmt.ext)
        # assigned to after processing
        self.ref['pathView'] = None # set in write() method of subclass
        # needed for csound processing
        self.ref['pathCsound'] = self.ao.external.getPref('external', 'csoundPath')
        dirCsound, exeCsound = os.path.split(self.ref['pathCsound'])
        self.ref['pathDirCsound'] = dirCsound
        # must get from path
        self.ref['nameExeCsound'] = exeCsound



    #-----------------------------------------------------------------------||--
        
    def _engineAllocate(self, outRequest):
        """determine, for this event mode, what engines are necessary
        as well as what outputs to request
        assumes that  outputReqest has already been set
        combiness eventMode w/ output request to only get necessary engines

        this the first layer of compatbility; another layer is performed
        for each engine
        does not check for texture-instrument compatibility w/ vairous engines
        
        if a user has a csound output, and is in gm mode, no csound engines
        if a user has a midi output, and is in cs mode, midi is created
        """
        if drawer.isStr(outRequest):
            if outRequest == 'all':
                outRequest = outFormat.outputFormatNames.values()
        engineRequest = []
        # do exclusive groups first; cant be two kinds of csound
        # get engines for varuous EventMode Names         
        #print _MOD, 'allocating engines for em:', self.name
        # csound engines only added if declared with evenMode
        # can only create 1 .sco at a time
        if self.name == 'csoundNative':
            engineRequest.append('EngineCsoundNative')
        elif self.name == 'csoundSilence':
            engineRequest.append('EngineCsoundSilence')
        elif self.name == 'csoundExternal':
            engineRequest.append('EngineCsoundExternal')
        # last option: a simple output request, regardless of event mode
        elif 'csoundScore' in outRequest:
            engineRequest.append('EngineCsoundExternal')
        # do compatible types, possible with many formats
        # compatible types are not dependent on auxillary numbers
        if self.name in ['midi', 'midiPercussion'] or 'midiFile' in outRequest:
            engineRequest.append('EngineMidiFile')
        # check for output requests that have an engine
        # but are not eventModes
        if 'maxColl' in outRequest:
            engineRequest.append('EngineMaxColl')
        if 'textTab' in outRequest or 'textSpace' in outRequest:
            engineRequest.append('EngineText')
        if 'acToolbox' in outRequest:
            engineRequest.append('EngineAcToolbox')
        if 'audioFile' in outRequest:
            engineRequest.append('EngineAudioFile')
        # instantiate necessary objects
        engineLib = {}
        for engine in engineRequest:
            mod = eval(engine) # all take self.ref on init
            # supply event mode name as well as reference dictionary
            engineLib[engine] = mod(self.name, self.ref)
        return engineLib

    #-----------------------------------------------------------------------||--
    # post processing updates
    def _updateInfo(self, ref):
        """get ref to aoInfo dict, update last paths
        need to reassign to instance variable in order to get updated data
            from external objects (output objects)
        viewPath is the file to view, may be a score, csd, or text file
        """
        # add list to preivous
        self.ref = ref
        # fromat of aoPrefs not the same as ref
        # these are paths used for launching things from w/n athenacl
        self.ao.aoInfo['viewFP'] = self.ref['pathView'] # 
        self.ao.aoInfo['audioFP'] = self.ref['pathAudio']
        self.ao.aoInfo['scoFP'] = self.ref['pathSco'] 
        self.ao.aoInfo['orcFP'] = self.ref['pathOrc']
        self.ao.aoInfo['batFP'] = self.ref['pathBat']
        self.ao.aoInfo['csdFP'] = self.ref['pathCsd']
        self.ao.aoInfo['midFP'] = self.ref['pathMid']
        
    def _outputToPath(self, output):
        """if formats are known, return what paths were written"""
        if output == 'audioFile': path = self.ref['pathAudioSynth']
        elif output == 'midiFile': path = self.ref['pathMid']
        elif output == 'csoundBatch': path = self.ref['pathBat'] #self.batPath
        elif output == 'csoundScore': path = self.ref['pathSco'] #self.scoPath
        elif output == 'csoundOrchestra': path = self.ref['pathOrc'] #self.orcPath
        elif output == 'csoundData': path = self.ref['pathCsd'] #self.csdPath
        elif output == 'maxColl': path = self.ref['pathMaxColl'] #self.txtPath
        elif output == 'textSpace': path = self.ref['pathTxtSpace'] #self.csdPath
        elif output == 'textTab': path = self.ref['pathTxtTab'] #self.txtPath
        elif output == 'acToolbox': path = self.ref['pathAct'] #self.txtPath
        else:
            raise ValueError, 'bad output given: %s' % output 
        return path

    def _getReport(self):
        self.outComplete.sort()
        msg = []
        msg.append('%sEventList %s complete:\n' % (lang.TAB, self.ref['nameMusic']))
        # formats returned will be complete output strings
        for output in self.outComplete:
            msg.append('%s\n' % self._outputToPath(output))
        return ''.join(msg)

    #-----------------------------------------------------------------------||--
    # main operations

    def setRootPath(self, rootPath=None):
        if rootPath == None: rootPath = osTools.tempFile() # gets txt temp file
        self.rootPath = rootPath
        self._initRefNames()
        self._initRefPaths()
    
    def getWritePaths(self, rootPath):
        """generate all the paths of possible outputs
        may eventually want to calclulate actual outputs"""
        self.rootPath = rootPath
        self._initRefNames()
        self._initRefPaths()
        msg = []
        # get all write paths from all possible output formats
        for fmt in self.outFormatRef:
            msg.append(self.ref[fmt.emKey]) # emKey attribute is names used here
        return msg
        
    def _docEngine(self, engine):
        """provide an engine name string"""
        msg = []
        for oe in engine.outAvailable:
            oeObj = outFormat.factory(oe)
            msg.append('%s (%s)' % (oe, oeObj.doc))
        return ', '.join(msg)
        
    def _docUser(self, usrOutRequest):
        """similar but not the same as _docReference; this divided into headlist
        and entryLines"""
        emOrcObj = orc.factory(selectEventModeOrc(self.name))
        engineLib = self._engineAllocate(usrOutRequest)
        headList = []
        headList.append('EventMode: %s; Orchestra: %s\n' % (
                             self.name, emOrcObj.name))
        if len(engineLib) == 1: # adjust for plural
            headList.append('%s active OutputEngine:\n' % len(engineLib))
        else:
            headList.append('%s active OutputEngines:\n' % len(engineLib))
        entryLines = []
        eNames = engineLib.keys()
        eNames.sort()
        for engineName in eNames:
            engine = engineLib[engineName]
            options = self._docEngine(engine)
            docStr = '%s EventOutput formats available: %s' % (engine.doc, options)
            entryLines.append([engine.name, docStr])
        return headList, entryLines
        
    def _docReference(self, usrOutRequest): 
        """difference w/ docUser is in the header and the listed 'active' bit"""
        emOrcObj = orc.factory(selectEventModeOrc(self.name))
        engineLib = self._engineAllocate(usrOutRequest)
        msg = []
        eNames = engineLib.keys()
        eNames.sort()
        for engineName in eNames:
            engine = engineLib[engineName]
            #options = drawer.listScrub(engine.outMin, 'rmSpace', 'rmQuote')
            options = self._docEngine(engine)
            docStr = '%s OutputFormat available: %s' % (engine.doc, options)
            msg.append('%s: %s\n' % (engine.name, docStr))
        return ''.join(msg)
        
    def reprDoc(self, usrOutRequest=[], style=None):
        """return a documentation string"""
        # get the em orc for this em mode
        if style in [None]:
            return self._docUser(usrOutRequest)
        if style in ['ref']:
            return self._docReference(usrOutRequest)
        
        
    def process(self, input=None, usrOutRequest=[], refresh=1):
        """must be called after setRootPath
        if input is None: uses local atheanObj, processes all textures and clones
        if input is a list of texture objects, will process as necessary
        return ok, msg; if polySeq is None, will be generated
        otherwise can share the sasme ply score from elsewhere

        refresh will force the generation of new scores
        texture.score() called on creation, and edit: should be up to date
        clone.score() called on creation and edit; should be up to date
        """
        # get orcObj for this mode, indepedent of any texture
        # this orc is passed to each engine; the engine must use it
        # to try to process textures; may or may not be compatible w/ all t's
        
        self.outComplete = [] # clear
        outRequest = copy.deepcopy(usrOutRequest)
        # important tt only one performance object is created, and passed
        # to each output engine; ensures that same results will 
        # happen w/ multiplw outputs
        # perfObj stores a reference to each textures orcObj
        # no need to store perfObj as instance variable
        perfObj = Performer() # perform textures and clones w/ obj
        if input in [None, 'all']:
            perfObj.flattenAll(self.ao, refresh)
        else: # its a list of textures
            perfObj.flattenSome(input, refresh)
            
        # sort all event lists in this perfObj
        # not sure if sorting is always necessary
        # may be a time lag: sort event seq elswhere?
        perfObj.sort()
        # no need to store engineLib
        engineLib = self._engineAllocate(outRequest)
        # local objects not store in em
        emOrcObj = orc.factory(selectEventModeOrc(self.name))

        ok = 1
        msg = []
        # when calling a engine, pass modeOrcObj, process in addition
        # to local texture based texture orcObj
        for engineName in engineLib.keys():
            try: # will write orchestra if necessary 
                # only pass a ref to the polySeq to the engine
                engineLib[engineName].write(perfObj.polySeq, outRequest) 
                self.outComplete = (self.outComplete + 
                                          engineLib[engineName].outComplete)
            except (IOError, OSError), e:
                ok = 0
                msg.append(e)
            # get ref data from engine
            # this redundant: it does not really need to be done each time
            self._updateInfo(engineLib[engineName].ref) 
        # update paths for athenaobject
        if ok:
            return ok, self._getReport(), self.outComplete
        else:
            return ok, lang.msgFileError, self.outComplete




#-----------------------------------------------------------------||||||||||||--
# publicj factory for create an event object
def factory(eventName, ao):
    eventName = eventModeParser(eventName)
    assert eventName != None
    return EventMode(ao, eventName)



















#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
# run tests
class TestOld:
    def __init__(self):
        # call test methods
        # self.testEventList()
        self.testRetrograde()
        
        
    def testEventList(self):
        from athenaCL.libATH import SC

        multisetFactory = SC.MultisetFactory()
        scObj = SC.SetClass()
        setData = 'c4, d3, a#4', 'd#2, a3', '3-5'
        setList = []
        for set in setData:
            setList.append(multisetFactory(None, set, scObj))
        from athenaCL.libATH import pitchPath
        polyPath = pitchPath.PolyPath('test', scObj)
        polyPath.loadMultisetList(setList)
        from athenaCL.libATH.libTM import texture
        texture_ = texture.factory('LineGroove')

        textureParameters = {}
        textureParameters['inst']    = ('staticInst', 2) 
        textureParameters['ampQ']    = ('constant', 70)
        textureParameters['panQ']    = ('constant', .5)
        textureParameters['octQ']    = ('constant', 0)
        textureParameters['fieldQ'] = ('constant', 0)
        textureParameters['rhythmQ'] = ('loop', ((4,1,1),(4,5,1)))
        textureParameters['tRange'] = ('staticRange', (0, 15)) 
        textureParameters['beatT']   = ('c', 30)
        
        pitchMode = 'ps'
        polyphonyMode = '' 
        temperamentName = '12equal' 
        auxNo = 0
        midiPgm = 0
        midiCh = None
        fpSSDR = ''
        fpSADR = ''
        texture_.load(textureParameters, polyPath, polyphonyMode, temperamentName, 
                     pitchMode, auxNo, fpSSDR, fpSADR, midiPgm, midiCh)
        ok = texture_.score()
        print texture_.elScore

    def testRetrograde(self):
    
        for fmt in ['eventInverse', 'timeInverse']: #, 'timeInverse']:
            a = EventSequence()
            tCur = 100
            for x in range(0, 7):
                d = random.choice([1,3,7,13])
                event = {'time':tCur, 'dur':d}
                a.append(event)
                tCur = tCur + d
            print '\neventSequence: %s' % fmt
            a.sort() # maually sort
            a.retrograde(fmt)

if __name__ == '__main__':
    TestOld()




