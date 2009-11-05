#-----------------------------------------------------------------||||||||||||--
# Name:          TimeSegment.py
# Purpose:       Texture to fill partitioned time ranges generators
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH import pitchTools
from athenaCL.libATH import unit
from athenaCL.libATH import language
lang = language.LangObj()

_MOD = 'TimeSegment.py'


# static: pitchSelectorControl, levelFieldMonophonic, levelOctaveMonophonic

# static: levelEventCount
         # event count per segment, or event count per texture
         # this control will radically change the number of events
         # if event count is per Texture, event count per segment could be
         # by part (all parts have equal numbers of events, 
         # but this is easy to do w/ event count per        
         # segment) or by proportion of dur (this requires generating all segment
         # durs first
         
# static: totalSegmentCount
         # number of segments
         
# dyn: segmentWidthGenerator, width of segments, for as many segments as 
         # specified as static parameter
         # 'width of segments in seconds generated in order'
         # cannot always use unit interval scalar b/c this will make it very            
         # difficult
         # to align density segments b/n textures w/ different durations
         
# dyn: event count generator
         # count can be adjusted to apply to each segment, or to total texture
         # if total texture, number of events is proportional to segment 
         # durations generated above
         
# dyn: fillGenerator, 'event start time within unit interval'
         # apply to each segment unitl event per segment count is reached
         # unit interval is mapped to either segment or to whole texture

# this excludes, for instance, easily saying that you want 8 segments
# although this can be done by simply supplying segment width w/ 
# proper values

# path duration fraction should determine pitch values based on wherever time
# values fall; no other path density concerns; textures segments will
# often be shorter tn path df, though cannot rely on this

# this used to suggest a static: segmentWidthToggle to toggle width 
# generator to give values as proportional (unit interval (0-1)) or in abs time # values? 0-1 values: map to total duration of texture; this would not have 
# required a total segment count, but presumably would have given values until 
# enough (either unit interval or real time) were given; this has weaknesses
# over specifying count and width values, though count is a static value (and
# not the result of a dynamic process); 

# this relates to ac't density-of-start-times and   Density Curve Section


class TimeSegment(baseTexture.Texture):
    def __init__(self, name=None, scObj=None):
        baseTexture.Texture.__init__(self, name, scObj) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'TimeSegment'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['pitchSelectorControl', 'levelFieldMonophonic',    
             'levelOctaveMonophonic', 'levelEventCount', 'totalSegmentCount']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        # define ordered list of dynamic parameters
        # [{name: x, type: x, default: x)]
        self.dynPmtrManifest = [
            {'name':'segmentWidthGenerator', 'type':'genPmtrObjs',  
                      'default': ('bg','rc',(1,2,3)), 'doc': 'segment width weight'},
            {'name':'eventCountGenerator', 
                        'type':'genPmtrObjs',  'default': ('cg', 'ud', 3, 40, 2),                           
                        'doc': 'event count per segment or per Texture'},
            {'name':'fillGenerator', 'type':'genPmtrObjs',  'default': ('ru',0,1),                           
                        'doc': 'event start time'},
            ]
        self._updateDynPmtrInit() # defines textPmtrNo, textLabels
        self.doc = lang.docTmTimeSegment

    def _scoreMain(self):
        """creates score
        note: octave choose for every note
        """
        # texture-wide time elements
        inst = self.getInst()
        
        # needed for preliminary parameter values
        # tStart, tEnd = self.getTimeRange()
        # tCurrent = tStart

        # get field, octave selection method value
        textPitchSelectorControl = self.getTextStatic('psc', 'selectionString') 
        textFieldLevel = self.getTextStatic('lfm', 'level') 
        textOctaveLevel = self.getTextStatic('lom', 'level')        

        # this is level tt event count numbers are applied (not count itself)
        textLevelEventCount = self.getTextStatic('lec', 'level')
        textTotalSegmentCount = self.getTextStatic('tsc', 'count')

        segmentManifest = [] # store [count, segWeight, start, end]
        # process segments first, determine events per segemtn
        tSeg = 0
        if textLevelEventCount == 'segment': # event count per segement
            for q in range(textTotalSegmentCount):
                eventCount = self.getTextDynamic('eventCountGenerator', tSeg)
                segmentManifest.append([int(round(eventCount))]) # store as list
                tSeg = tSeg + 1
        elif textLevelEventCount == 'count': # event count is total
            # get one value and divide
            eventCount = self.getTextDynamic('eventCountGenerator', tSeg)
            segEventCount = int(round((eventCount/textTotalSegmentCount)))
            if segEventCount <= 0: segEventCount = 1 # force minimum per seg
            for q in range(textTotalSegmentCount):
                segmentManifest.append([segEventCount]) # store as list      
        
        #print _MOD, 'levelEventCount', textLevelEventCount
        #print _MOD, 'textTotalSegmentCount', textTotalSegmentCount
        #print _MOD, 'segmentManifest', segmentManifest

        # get total duration
        tStart, tEnd = self.getTimeRange()
        tDurSpan = tEnd - tStart # not final dur, but time start span
        
        # get segment proportions
        tSeg = 0 # segment count as event step size
        segmentWidth = [] # store widths before getting scaled size
        for q in range(textTotalSegmentCount):
            # what if segment widht is zero?
            val = self.getTextDynamic('segmentWidthGenerator', tSeg)
            if val <= 0: pass # continue or warn?
            segmentWidth.append(val)
            tSeg = tSeg + 1
        # transfrom segment width into a collection of boundaries   
        #print _MOD, 'segmentWidth', segmentWidth
        segmentBounds = unit.unitBoundaryProportion(segmentWidth)
        
        for q in range(textTotalSegmentCount):
            s, m, e = segmentBounds[q]
            segmentManifest[q].append(s * tDurSpan)
            segmentManifest[q].append(e * tDurSpan)
            
        #print _MOD, 'segmentWidth', segmentManifest
                
        # get texture start time as init time
        tCurrent = tStart # defined abovie

        # if field/oct vals are taken once per set, pre calculate and store 
        # in a list; access from this list with pathPos index
        fieldValBuf = []
        if textFieldLevel == 'set':
            for q in range(self.getPathLen()):
                s, e = self.clockPoints(q) # use path df start time
                fieldValBuf.append(self.getField(s))
        octValBuf = []
        if textOctaveLevel == 'set':
            for q in range(self.getPathLen()):
                s, e = self.clockPoints(q)
                octValBuf.append(self.getOct(s))

        # iterate through segments in order
        for segPos in range(textTotalSegmentCount):      
            segEventCount = segmentManifest[segPos][0] # count is first in list
            tStartSeg = segmentManifest[segPos][1]
            tEndSeg = segmentManifest[segPos][2]
            # create events for thsi segment
            #print _MOD, 'segPos', segPos
            for i in range(segEventCount): #
                # get generator value w/n unit interval         
                tUnit = unit.limit(self.getTextDynamic('fillGenerator', tCurrent))
                tCurrent = unit.denorm(tUnit, tStartSeg, tEndSeg)
                pathPos = self.clockFindPos(tCurrent) # get pos for current time
                if pathPos == None: 
                    raise ValueError, 'tCurrent out of all time ranges'
    
                #print _MOD, 'pp, tc', pathPos, tCurrent
                #print _MOD, 'tss, tes', tStartSeg, tEndSeg
                         
                # need to determin path position based on time point of event
                chordCurrent = self.getPitchGroup(pathPos)
                multisetCurrent = self.getMultiset(pathPos)
    
                # create a generator to get pitches from chord as index values
                selectorChordPos = basePmtr.Selector(range(0,len(chordCurrent)),
                                                                 textPitchSelectorControl)
    
                # choose pc from chord
                ps = chordCurrent[selectorChordPos()] # get position w/n chord

                # a if the division of path dfs is w/n a single segment
                # either side of the path may occur more than once.
                # perhaps pre calculate and store in a list?

                if textFieldLevel == 'event': # every event
                    transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                elif textFieldLevel == 'set':
                    transCurrent = fieldValBuf[pathPos] # choose PITCHFIELD

                if textOctaveLevel == 'event':
                    octCurrent = self.getOct(tCurrent) # choose OCTAVE
                elif textOctaveLevel == 'set':
                    octCurrent = octValBuf[pathPos] # choose OCTAVE
                    #print _MOD, 'pathPos, oct, t', pathPos, octCurrent, tCurrent

                psReal = pitchTools.psToTempered(ps, octCurrent, 
                                      self.temperamentObj, transCurrent)                                      
                self.stateUpdate(tCurrent, chordCurrent, ps, 
                                      multisetCurrent, None, psReal)

                bpm, pulse, dur, sus, acc = self.getRhythm(tCurrent) 
                if acc == 0 and not self.silenceMode: # this is a rest
                    tCurrent = tCurrent + dur
                    continue

                amp = self.getAmp(tCurrent) * acc # choose amp, pan
                pan = self.getPan(tCurrent)
                auxiliary = self.getAux(tCurrent) # chooose AUX, pack into list
                eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, sus, acc, 
                                                             amp, psReal, pan, auxiliary)
                self.storeEvent(eventDict)
                # tCurrent = tCurrent + dur # move clocks forward by dur unit

            # self.clockForward() # advances path positon
        return 1

        
