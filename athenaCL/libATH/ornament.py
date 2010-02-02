#-----------------------------------------------------------------||||||||||||--
# Name:          ornament.py
# Purpose:       object to work with texture modules to create ornaments.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2003-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import language
lang = language.LangObj() 
from athenaCL.libATH.libPmtr import parameter   
from athenaCL.libATH import pitchTools

_MOD = 'ornament.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)

#-----------------------------------------------------------------||||||||||||--

def extractNeighbors(pitchGroup, baseNote, scales=None):
    """takes a set, or a whole path, and derives a pc scale, 
    a pitch space scale, and provides the upper and lower note to 
    baseNote
    
    baseNote should be represented in the pitch group
    we need to know our current reference position in the pitchGroup
    pitchGroup has pitch pre-temperament; thus baseNote should be
    pre-temperament
    may be a psReal
    
    pitchGroup: from a refDict, containing stateCurrentChord, or statePathList
    will be a list of raw psReal values: could be floats, and could have micro
    specification
    """
    # if scales given and no pitchGroup is given
    if scales != None and pitchGroup == None:
        colPitchSpace = scales[0]
        colPitchClass = scales[1]
    else: # given a set or path as pitchGroup
        if drawer.isNum(pitchGroup[0]):
            pitchGroup = [pitchGroup, ] # make all look like paths
        colPitchSpace = []
        colPitchClass = []
        for set in pitchGroup:
            for entry in set:
                if entry not in colPitchSpace:
                    colPitchSpace.append(entry)
                # round; zero trans gets mod12
                entryPC = pitchTools.pcTransposer(entry, 0) 
                if entryPC not in colPitchClass:
                    colPitchClass.append(entryPC)
        colPitchSpace.sort()
        colPitchClass.sort()
        scales = colPitchSpace, colPitchClass

    # use pitch class space to get neighbors
    # can use pitch space in the future? wrap around is strange
    octaveAdjust = 0
    baseOctMult, basePC = pitchTools.splitOctPs(baseNote)
    
    # although baseNote may be a float (already tempered)
    # basePC seems to    need to be an int, as it is used to find
    # a position in the scale; for this reason it seems like
    # the path positions value, and not the tempered pitch
    # should be coming in as the baseNote: tmerperament could cause
    # a rounding error and pass a pitch that is not in the scale at all
    
    #print _MOD, basePC, colPitchClass
    idx = None
    try:
        idx = colPitchClass.index(basePC)
    except ValueError: # not in the collected pitches; try rounding
        for i in range(len(colPitchClass)):
            # compare rounded versions, as floats may not match
            if round(colPitchClass[i], 2) == round(basePC, 2):
                idx = i
                # print _MOD, 'found rounded match'
        if idx == None:
            idx = 0
            environment.printDebug('no match between base pitch and collected pitches')
        
    idxL = idx - 1 # lower neighbor
    if idxL == -1: # wrap index around 
        idxL = len(colPitchClass) - 1
        octaveAdjust = -1
    idxU = idx + 1 # upper neighbor
    if idxU == len(colPitchClass):
        idxU = 0
        octaveAdjust = 1

    neighborL = colPitchClass[idxL]
    if octaveAdjust == -1:
        neighborL = pitchTools.psTransposer(neighborL, -12)

    neighborU = colPitchClass[idxU]
    if octaveAdjust == 1:
        neighborU = pitchTools.psTransposer(neighborU, 12)

    # do octave adjust ment relative to baseNote in pitch space
    neighborL = pitchTools.psTransposer(neighborL, (12 * baseOctMult))
    neighborU = pitchTools.psTransposer(neighborU, (12 * baseOctMult))
    lowerUpper = neighborL, neighborU
        
    return scales, lowerUpper
    

def mapNeighbors(scales, baseNote, contourForm):
    """take abstract scale positions above/below base and translate
    to scale pc space int values, for use in 'diatonic' scale positions
    0 is always the baseNote
    integers above and below translate into scale steps, using pcSpcae Ints
    """
    # baseNote should probably be an int
    # as we are going to look for it in an int ps scale
    
    # not sure this is necessary: paths can be microtonal
    #assert drawer.isInt(baseNote)
    
    # find max value of scale form
    maxInt = 0
    for entry in contourForm:
        if abs(entry) > maxInt:
            maxInt = abs(entry)

    # create pitch dicitonary for entire range
    pcContourDict = {}
    pcContourDict[0] = baseNote
    #keyRange = range(-maxInt, maxInt+1)
    
    # going up
    lastNote = pcContourDict[0]
    keyInt = 1
    while 1: # move up from 0 till maxInt found
        # supplying pitchGroup, baseNote, scales
        scales, (lower,upper) = extractNeighbors(None, lastNote, scales)
        pcContourDict[keyInt] = upper
        lastNote = upper
        keyInt = keyInt + 1
        if keyInt > maxInt:
            break
    # going down
    lastNote = pcContourDict[0]
    keyInt = -1
    while 1: # move up from 0 till maxInt found
        scales, (lower,upper) = extractNeighbors(None, lastNote, scales)
        pcContourDict[keyInt] = lower
        lastNote = lower
        keyInt = keyInt - 1
        if keyInt < -maxInt:
            break
    return pcContourDict









#-----------------------------------------------------------------||||||||||||--



class Ornament:
    """create an ornament object for each texture instance that needs one
        provide references to all local TM attriubtes that this class needs
        output in form congruent with event additions
    """
    def __init__(self, pmtrObjDict, temperamentObj):
        self.pmtrObjDict = pmtrObjDict # reference
        self.temperamentObj = temperamentObj # reference
        self._ornLibrary() # updates self.ornLib w/ new values
        self.ornKeys = self.ornLib.keys()

        # mu, sigma, min, max; want a range from -1 to 1
        self.gaussPmtrObj = parameter.factory(('randomGauss', .5, .1, -1, 1))

    def _ornLibrary(self):
        """
        contourForm 
            [1,0]         upward trill
            [-1,0]    downlard trill
            [0,]            tremolando
            [1,0,-1,0] turn
        pitchLang 
            'chromatic' scale steos are half steps
            'set'    scale steps are diatonic steps from scale derived from set
            'path' scale steps are diatonic steps from scale derived from path
            'microtone' scale steos are microtonal interval
        ornStyle 
            'single' # does ornament once, scales time percent to fit
            'loop' # loops ornament over time percent
            'scale' # scale notes to fit over time duration
        ornPos  
            'attack'
            'release' if comes at beginning or end of note
            'anticipate'  negative time, before note start time
        ornNotePcent = .5 # actual value calculated from durations
            % of note duration that is ornament; this is not the actual value
        durOrnGoal      = [.102]
            this is the duration of the ornamental notes in second
        durInstPcentOffset = .06
            vary duration by max 9% for each trill note
        microTone = .25 # this is relative to pc, so this is .005 in PCH
            microtone size in fraction of half-steps
        ampScalerMedian          = .900 # .875 # scale of base note
        ampInstPcentOffset = .025 # vary amp by max 10% for each trill note
            values per trill note
        """
        # these are low level ornament primitives and do not have complete data
        # position, pitchlanguage, and microtone must be provided
        self.ornLib = {
             'trill.0,1.a' :{'contourForm' : [0,1],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .55,
                                    'durOrnGoal' : [.095,.101,.095,.099,],
                         'durInstPcentOffset' : .034,
                             'ampScalerMedian' : .920, # scale of base note
                         'ampInstPcentOffset' : .012},

            'trill.0,1.b':   {'contourForm' : [0,1],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .60,
                                    'durOrnGoal' : [.115,.110,.107,.101,],
                         'durInstPcentOffset' : .042,
                             'ampScalerMedian' : .930, # scale of base note
                         'ampInstPcentOffset' : .010},
                         
     'trillocto.0,12.a':     {'contourForm' : [0,12],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .60,
                                    'durOrnGoal' : [.115,.110,.107,.101,],
                         'durInstPcentOffset' : .042,
                             'ampScalerMedian' : .930, # scale of base note
                         'ampInstPcentOffset' : .010},

     'trillMin3.0,3.a': {'contourForm' : [0,3],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .60,
                                    'durOrnGoal' : [.115,.110,.107,.101,],
                         'durInstPcentOffset' : .042,
                             'ampScalerMedian' : .930, # scale of base note
                         'ampInstPcentOffset' : .010},

     'trillMaj3.0,4.a': {'contourForm' : [0,4],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .60,
                                    'durOrnGoal' : [.115,.110,.107,.101,],
                         'durInstPcentOffset' : .042,
                             'ampScalerMedian' : .930, # scale of base note
                         'ampInstPcentOffset' : .010},

#     'trillNeut3.0,35.a':  {'contourForm' : [0,3.5],
#                                       'ornStyle' : 'loop',
#                                 'ornNotePcent' : .60,
#                                    'durOrnGoal' : [.115,.110,.107,.101,],
#                         'durInstPcentOffset' : .042,
#                             'ampScalerMedian' : .930, # scale of base note
#                         'ampInstPcentOffset' : .010},

         'trillP5.0,7.a':    {'contourForm' : [0,5],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .60,
                                    'durOrnGoal' : [.115,.110,.101,],
                         'durInstPcentOffset' : .042,
                             'ampScalerMedian' : .930, # scale of base note
                         'ampInstPcentOffset' : .015},
     

      'turn.0,1,0,-1.a':     {'contourForm' : [0,1,0,-1],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .47,
                                    'durOrnGoal' : [.90,.088,.96,.086],
                         'durInstPcentOffset' : .023,
                             'ampScalerMedian' : .940, # scale of base note
                         'ampInstPcentOffset' : .025},

      'turn.0,1,0,-1.b':     {'contourForm' : [0,1,0,-1],
                                      'ornStyle' : 'single',
                                 'ornNotePcent' : .50,
                                    'durOrnGoal' : [.110,.088,.105,.091],
                         'durInstPcentOffset' : .023,
                             'ampScalerMedian' : .940, # scale of base note
                         'ampInstPcentOffset' : .025},
                         
      'turn.0,3,0,-3.a':     {'contourForm' : [0,1,0,-1],
                                      'ornStyle' : 'loop',
                                 'ornNotePcent' : .47,
                                    'durOrnGoal' : [.90,.088,.96,.086],
                         'durInstPcentOffset' : .023,
                             'ampScalerMedian' : .940, # scale of base note
                         'ampInstPcentOffset' : .025},
                        

              'rise.-2,-1': {'contourForm' : [-2, -1],
                                      'ornStyle' : 'single',
                                 'ornNotePcent' : .45,
                                    'durOrnGoal' : [.094,],
                         'durInstPcentOffset' : .020,
                             'ampScalerMedian' : .940, # scale of base note
                         'ampInstPcentOffset' : .012},

                'rise.1,2':  {'contourForm' : [1, 2],   # "lift"
                                      'ornStyle' : 'scale',
                                 'ornNotePcent' : .50,
                                    'durOrnGoal' : [.099,.105],
                         'durInstPcentOffset' : .032,
                             'ampScalerMedian' : .960, # scale of base note
                         'ampInstPcentOffset' : .025},

                 'rise.-1':  {'contourForm' : [-1,],  # "lift"
                                      'ornStyle' : 'scale',
                                 'ornNotePcent' : .30,
                                    'durOrnGoal' : [.099,.105],
                         'durInstPcentOffset' : .022,
                             'ampScalerMedian' : .960, # scale of base note
                         'ampInstPcentOffset' : .025},

                'fall.2,1':  {'contourForm' : [2, 1],
                                      'ornStyle' : 'single',
                                 'ornNotePcent' : .50,
                                    'durOrnGoal' : [.099,.110],
                         'durInstPcentOffset' : .034,
                             'ampScalerMedian' : .950, # scale of base note
                         'ampInstPcentOffset' : .008},

            'fall.1,0,-1':   {'contourForm' : [1,0,-1],
                                      'ornStyle' : 'single',
                                 'ornNotePcent' : .50,
                                    'durOrnGoal' : [.092,.094,.099],
                         'durInstPcentOffset' : .025,
                             'ampScalerMedian' : .950, # scale of base note
                         'ampInstPcentOffset' : .020},

            'arc.-1,2,1':    {'contourForm' : [-1, 2, 1],
                                      'ornStyle' : 'scale',
                                 'ornNotePcent' : .50,
                                    'durOrnGoal' : [.100,.105,.110],
                         'durInstPcentOffset' : .032,
                             'ampScalerMedian' : .940, # .875 # scale of base note
                         'ampInstPcentOffset' : .023},

                 'arc.0,1':  {'contourForm' : [0,1],
                                      'ornStyle' : 'single',
                                 'ornNotePcent' : .50,
                                    'durOrnGoal' : [.099,.097],
                         'durInstPcentOffset' : .037,
                             'ampScalerMedian' : .950, # scale of base note
                         'ampInstPcentOffset' : .018},

      'fall.extended.a' : {'contourForm' : [2,0,-1,-2,2,0,-1,-2,0,-1, 
                                                        -2,0,-1,-2,-1,-2,-1,-2],
                                      'ornStyle' : 'scale',
                                 'ornNotePcent' : .70,
                                    'durOrnGoal' : [.088,.094,.086,.094,.090],
                         'durInstPcentOffset' : .022,
                             'ampScalerMedian' : .950, # scale of base note
                         'ampInstPcentOffset' : .010},
                         }

    #-----------------------------------------------------------------------||--
    def _getOrnLibrary(self, name=None, ornPos='release', 
                             pitchLang='path', microTone=.5):
        """finds the name, builds a complete preset dict by adding usr info
            provides an interface for accessing the ornament library
        """
        # add additional parameters
        if name not in self.ornKeys:
            raise AttributeError, 'no such ornament named %s' % name

        ornDict = self.ornLib[name]
        ornDict['ornPos'] = ornPos
        ornDict['pitchLang'] = pitchLang
        ornDict['microTone'] = microTone
        return ornDict


    def psScale(self, pitchFormat, contourForm, psBase, microTone=.5):
        """translates a scale form in notation [0,-1,0,1] into various pitch
        representations. integers in the scale form are interpreted in three
        ways: as chromatic 1/2 steps, as diatonic scale pitches (either from
        the local
        set or the entire path), or as units of some microtonal size
        this returns a list representing the scale steps in relation to             
        psBase
        
        psBase needs to be found in terms of the path, 
        which may not consist only of ints
        
        returns a psCountourReference, which is alway tempered pitch values
        """
        # not sure this needs to be an int
        #assert drawer.isInt(psBase)
        
        octCurrent   = self.pmtrObjDict['octQ'].currentValue
        transCurrent = self.pmtrObjDict['fieldQ'].currentValue
        #currentChord = self.stateCurrentChord

        # not needed for all forms, but myst always get
        if pitchFormat == 'set':
            pitchGroup = self.refDict['stateCurrentChord']
        elif pitchFormat == 'path':
            pitchGroup = self.refDict['statePathList']
        else: # non given, but note used
            pitchGroup = self.refDict['stateCurrentChord']


        refScales, lowerUpper = extractNeighbors(pitchGroup, psBase)
        pcContourDict = mapNeighbors(refScales, psBase, contourForm)
        #print pcContourDict
        # get pitch scale
        # this has the mapping with the appropriate pitches
        # N.B: danger here of getting mistransposed values
        # previously was an error and corrected in _splitPch
        psContourRef = [] 
        if pitchFormat == 'chromatic':
            for entry in contourForm:
                # transpose before getting temperament
                pcSpace = pitchTools.psTransposer(psBase, entry) 
                psReal = pitchTools.psToTempered(pcSpace, octCurrent, 
                                      self.temperamentObj, transCurrent)

                psContourRef.append(psReal) # transpose by half steps
        #   sets: derive scale from set
        elif pitchFormat == 'set' or pitchFormat == 'path': 
            for entry in contourForm:
                pcSpace = pcContourDict[entry] # scale step is a key, gets pcSpace
                psReal = pitchTools.psToTempered(pcSpace, octCurrent, 
                                      self.temperamentObj, transCurrent)

                psContourRef.append(psReal) # transpose by half steps
        elif pitchFormat == 'microtone': # microtonal
            for entry in contourForm: # treat scale step as microtone scaler
                # must do transposition after converting to PCH
                if entry * microTone > entry * 2:
                    environment.printWarn([lang.WARN, 'microtone large (%s)' % (entry * microTone)])
                trans = (transCurrent + (entry * microTone))
                psReal = pitchTools.psToTempered(psBase, octCurrent, 
                                      self.temperamentObj, trans)

                psContourRef.append(psReal) # transpose by half steps
        else:
            raise ValueError, 'no such pitchFormat'
        # this now returns psReals, not pch values
        return psContourRef, refScales

    def _makeEventDict(self, tCurrent, sus, amp, ps, pan):
        """creates a SubEvent, used in PolyEvent of textures
        ornament event dict does not contain aux and comment fields
        any additioinal fields will be provided by texture
        here sus may be refered to as dur; distinction not importatn
        for ornaments."""
        eventDict = {}
        eventDict['time'] = tCurrent
        eventDict['sus'] = sus
        eventDict['amp'] = amp
        eventDict['ps'] = ps
        eventDict['pan'] = pan
        return eventDict

    def _addDurNoise(self, durInst, durInstPcentOffset):
        durInstShiftMax  = durInst * durInstPcentOffset
        randVal = self.gaussPmtrObj(0.0) # val b/n -1 and 1
        final = durInst + (randVal * durInstShiftMax)
        #durInstShiftList = getOffsetScalers(durInstShiftMax) 
        #finalDur = durInst + random.choice(durInstShiftList)
        return final

    def _addAmpNoise(self, ampInst, anpInstPcentOffset):
        ampInstShiftMax  = ampInst * anpInstPcentOffset
        randVal = self.gaussPmtrObj(0.0) # val b/n -1 and 1
        final = ampInst + (randVal * ampInstShiftMax)
        return final

    def _setOrnPos(self, ornPos, rhythmBase, tCurrent, totOrnDur):
        """based on ornament position, gets start and end times for base note
        and ornament; tCurrent is the real current time, so negative values
        are irrational.
        """
        if totOrnDur > rhythmBase:
            environment.printDebug(['ERROR: pos: %s, baseT: %s, ornT: %s' % (ornPos, rhythmBase, totOrnDur)])
            # ornament can never be longer than the rhythm base
            raise ValueError, 'ornament time is longer than base note'

        if tCurrent - totOrnDur < 0 and ornPos == 'anticipate':
            environment.printDebug(['anticipate ornament starts at negative time, mangling to attack'])
            ornPos = 'attack'

        if ornPos == 'release':
            durBase   = rhythmBase - totOrnDur
            tBaseStart = tCurrent
            tBaseEnd      = tCurrent + durBase
            tOrnStart  = tCurrent + durBase
            tOrnEnd   = tCurrent + rhythmBase # duration of whole event group
        if ornPos == 'anticipate': 
            durBase   = rhythmBase # ornament prceedes notes duration
            tBaseStart = tCurrent # original start time
            tBaseEnd      = tCurrent + rhythmBase
            tOrnStart  = tCurrent - totOrnDur
            tOrnEnd   = tCurrent # original start time
        if ornPos == 'attack':
            durBase   = rhythmBase - totOrnDur
            tBaseStart = tCurrent + totOrnDur
            tBaseEnd      = tCurrent + rhythmBase
            tOrnStart  = tCurrent
            tOrnEnd   = tCurrent + totOrnDur

        # problems happening when duration of the base note is very
        # short; need to check here for a short base note, if too 
        # short, raise an exception
        if durBase < .0001:
            raise ValueError, 'ornament basDur is very very short'
        return durBase, tBaseStart, tBaseEnd, tOrnStart, tOrnEnd


    def _getOrnDurStyle(self, presetDict, estOrnDurFraction):
        """find size and durations of an ornaments
        estOrnDurFraction is time of ornament in ms
        return totOrnament duration, which is the _actual_ duration to be used
        single and loop use actual durations, and can thus fail to fit
        if they fail to fit, the are scaled
        """

        contourForm = presetDict['contourForm']
        ornStyle     = presetDict['ornStyle']
        durOrnGoal   = presetDict['durOrnGoal']
        durInstPcentOffset = presetDict['durInstPcentOffset']
        # estOrnDurFraction: actual time in ms of ornament

        # ornStyle is 'scale', 'loop'
        # durOrnGoal is a list of possible duration fractions
        # find number of notes
        durList = []
        durIndex = 0
        durCount = 0
        totOrnDur = 0

        # check scaling issues
        durOrnGoalSlc = [] # temporary slice of durOrnGoal
        # get elements relavent to scale length
        if len(durOrnGoal) >= len(contourForm): # if more durs than ornaments
            durOrnGoalSlc = durOrnGoal[0:len(contourForm)] # slice take needed
        else: # loop what is given to fit orn in contour
            i = 0
            while 1:
                durOrnGoalSlc.append(durOrnGoal[i])
                if len(durOrnGoalSlc) == len(contourForm):
                    break # only need length of scale form
                i = i + 1
                if i == len(durOrnGoal):
                    i = 0 # loop around regions that are shorter
        durModelTotal = 0.0 # duration of unscaled ornament
        for durTemp in durOrnGoalSlc: # get each duration fraction
            durModelTotal = durModelTotal + durTemp # total of fractions
        
        if ornStyle == 'scale': # rhythm of note conforms to duration of orn
            for durTemp in durOrnGoalSlc:
                # find proportional fraction of entire segment
                perCentDur = durTemp / float(durModelTotal)
                # pcnt times estame actual duration in ms
                durInst = perCentDur * estOrnDurFraction 
                finalDur = self._addDurNoise(durInst, durInstPcentOffset)
                durList.append(finalDur) # add to list
                totOrnDur = totOrnDur + finalDur # add to total

        elif ornStyle == 'single': # rhythm of note matters, duration may change
            # find time of ornaments not stretched, if the dont fit, then 
            if durModelTotal > estOrnDurFraction: # doesnt fit
                trueSingle = 0 # must scale
            else:
                trueSingle = 1 # dont need to scale, can be a true single

            for durInst in durOrnGoal: # get times in ms
                # add noise to duration
                if trueSingle:
                    pass #keep durInst
                else: # scale
                    perCentDur = durInst / float(durModelTotal)
                    # pcnt times estame actual duration in ms
                    durInst = perCentDur * estOrnDurFraction 

                finalDur = self._addDurNoise(durInst, durInstPcentOffset)
                durList.append(finalDur) # add to list
                totOrnDur = totOrnDur + finalDur # add to total
                durCount = durCount + 1 # add to number of durations collected
                if durCount == len(contourForm):
                    break # dont add any more

        elif ornStyle == 'loop': # rhythm of note matters, duration may change
            # find time of ornaments not stretched, if the dont fit, then 
            if durModelTotal > estOrnDurFraction: # doesnt fit
                trueLoop = 0 # must scale
            else:
                trueLoop = 1 # dont need to scale, can be a true single
            while 1:
                durInst = durOrnGoal[durIndex] # get from list of durs
                durIndex = durIndex + 1
                if durIndex >= len(durOrnGoal):
                    durIndex = 0 # loop around if needed
                if trueLoop:
                    # leave durInst alone
                    nextDurInstance = durOrnGoal[durIndex]
                    # add noise to duration
                else: # scale
                    # find proportional fraction of entire segment
                    perCentDur = durInst / float(durModelTotal)
                    # pcnt times estame actual duration in ms
                    durInst = perCentDur * estOrnDurFraction 
                    perCentDurNext = durOrnGoal[durIndex] / float(durModelTotal)
                    nextDurInstance = perCentDurNext * estOrnDurFraction 

                finalDur = self._addDurNoise(durInst, durInstPcentOffset)
                durList.append(finalDur) # add to list
                totOrnDur = totOrnDur + finalDur # add to total
                durCount = durCount + 1 # add to number of durations collected
                if (totOrnDur > (estOrnDurFraction - nextDurInstance) or 
                     totOrnDur >= estOrnDurFraction):
                    break # dotn add any more durations

        if totOrnDur > estOrnDurFraction * 1.25:
            environment.printWarn([lang.WARN, 'ornament duration is very long'])
            environment.printDebug(['totOrnDur: %s, estOrnDurFraction: %s' % (totOrnDur, estOrnDurFraction)])
        return totOrnDur, durList

    #-----------------------------------------------------------------------||--

    def create(self, refDict, presetName='trill', ornPos='release', 
                  pitchLang='path', microTone=.5):
        """
        psBase is a pitch space integer, or not, depending on path form
        """

        self.refDict = refDict
        tCurrent = refDict['stateCurrentTime']
        psBaseRaw = refDict['stateCurrentPitchRaw'] # this is psBaseInt, no temper

        presetDict = self._getOrnLibrary(presetName, ornPos, 
                                                  pitchLang, microTone)
        # load parameters
        contourForm = presetDict['contourForm']
        ornStyle     = presetDict['ornStyle']
        ornPos   = presetDict['ornPos']
        pitchLang = presetDict['pitchLang']
        ornNotePcent = presetDict['ornNotePcent']
        durOrnGoal   = presetDict['durOrnGoal']
        durInstPcentOffset = presetDict['durInstPcentOffset']
        microTone = presetDict['microTone']
        ampScalerMedian  = presetDict['ampScalerMedian']
        ampInstPcentOffset = presetDict['ampInstPcentOffset']
        
        # from parameter objects
        inst = self.pmtrObjDict['inst'].currentValue
        pan  = self.pmtrObjDict['panQ'].currentValue
        amp  = self.pmtrObjDict['ampQ'].currentValue
        octCurrent   = self.pmtrObjDict['octQ'].currentValue
        transCurrent = self.pmtrObjDict['fieldQ'].currentValue

        pulseObj = self.pmtrObjDict['rhythmQ'].currentPulse
        baseRhythmTuple = pulseObj.get('triple')
        currentBeatTime = self.pmtrObjDict['rhythmQ'].bpm
        # duration of base rhyth, first of triple
        rhythmBase = self.pmtrObjDict['rhythmQ'].currentValue[0] # gets time in ms

        # calculat a tempered, transposed position
        # this value may be a float
        psBase = pitchTools.psToTempered(psBaseRaw, octCurrent,
                                    self.temperamentObj, transCurrent)
        # translate contourForm into PCH list of appropriate pitches
        #print _MOD, pitchLang, contourForm, psBase, microTone
        
        # psBase here needs to an int, in pitch space, that is somewhere on
        # the path. psCountourReference
        psContourReference, refScales = self.psScale(pitchLang, contourForm, 
                                                    psBaseRaw, microTone)
                                                    
        # estimated, this will chang once rhythms meausred
        estOrnDurFraction = rhythmBase * ornNotePcent 
        # find number of notes, and actual duartion of all oraments
        totOrnDur, durList = self._getOrnDurStyle(presetDict, estOrnDurFraction)
        # time of ornament, time of base
        # get timings
        posTimes = self._setOrnPos(ornPos, rhythmBase, tCurrent, totOrnDur)      
        durBase, tBaseStart, tBaseEnd, tOrnStart, tOrnEnd = posTimes
        
        # make notes
        tLocalCurrent = copy.deepcopy(tCurrent)
        ampOrnament = amp * ampScalerMedian # get amp base value
        eventList = [] # event list does not store compelete events
        
        # make base note:
        if durBase > .0001:# if very short, ommit this note (value in seconds)
            abortOrnament = 0
        else:
            abortOrnament = 1
        if not abortOrnament: 
            baseNoteEvent = self._makeEventDict(tBaseStart, durBase, amp, 
                                                            psBase, pan)
        else: # abort ornament, user tempered pitch
            print lang.WARN, "ornamants aborted" 
            baseNoteEvent = self._makeEventDict(tCurrent, rhythmBase, amp, 
                                                            psBase, pan)
            eventList.append(baseNoteEvent)
            return eventList

        # build ornament from ornament start time
        tLocalCurrent = tOrnStart # clock may move backwards
        scalePosition = 0 # index ot contourForm and durList
        durPosition = 0
        durBufferSpace = .003 # 3 ms gap to avoid clips
        while 1:
            #print scalePosition, tLocalCurrent, durList[durPosition], tOrnEnd
            ampInstance = self._addAmpNoise(ampOrnament, ampInstPcentOffset)
            # indices hold ps, tempered version of of contourForm
            psCurrent = psContourReference[scalePosition] 
            durInst = durList[durPosition]
            durFake = durInst - durBufferSpace # create shorter dur for b/n notes
            eventDict = self._makeEventDict(tLocalCurrent, durFake, ampInstance, 
                                                      psCurrent, pan) # not complete event
            eventList.append(eventDict) 
            tLocalCurrent = tLocalCurrent + durInst # append actual
            # iterators
            scalePosition = scalePosition + 1
            if scalePosition == len(psContourReference):
                scalePosition = 0
            durPosition = durPosition + 1
            if durPosition == len(durList):
                durPosition = 0
            # exits
            if ornStyle == 'loop':
                if tLocalCurrent >= tOrnEnd: break
                if tLocalCurrent + durList[durPosition] >= tOrnEnd:
                    break # dont want trill that spills over
            else: # ornaments that are 'single' or 'scale'
                if durPosition == 0: # its gone through once already
                    break # only have enough durs for each ornament

        # resort notes so this looks better
        if ornPos == 'release':
            eventList.insert(0, baseNoteEvent) # insert at beginning
        else: # place base note after ornament
            eventList.append(baseNoteEvent) # add at end
        return eventList








#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testDistributions(self):
        self.ornObj = Ornament({},{})
        for dur in [.1, 10, 100, 1000, 100000]:
            for x in range(0, 4):
                post = self.ornObj._addDurNoise(dur, .03)

    def testTimeEngine(self):
        self.ornObj = Ornament({},{})
        ornNotePcent = .5
        testCount = 0
        durations = [2.3, 20, 400, .01, .0005]
        for tCurrent in [0, 100, 1000]:
            for name in self.ornObj.ornKeys:
                for ornPos in ['attack', 'release', 'anticipate']:
                    for rhythmBase in durations:
                        estOrnDurFraction = rhythmBase * ornNotePcent 
                        presetDict = self.ornObj._getOrnLibrary(name, ornPos, 'path')
                        totOrnDur, durList = self.ornObj._getOrnDurStyle(
                                presetDict, estOrnDurFraction)
                        posTimes = self.ornObj._setOrnPos(ornPos, rhythmBase, 
                                            tCurrent, totOrnDur)       
                        durBase, tBaseStart, tBaseEnd, tOrnStart, tOrnEnd = posTimes
                        testCount += 1

#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)


