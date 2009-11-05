#-----------------------------------------------------------------||||||||||||--
# Name:          LiteralVertical.py
# Purpose:       literal vertical presentation.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH import pitchTools
from athenaCL.libATH.libPmtr import parameter   
from athenaCL.libATH import language
lang = language.LangObj()

_MOD = 'LiteralVertical.py'

class LiteralVertical(baseTexture.Texture):
    """simple one dimension line algorithm
    """
    def __init__(self, name=None, scObj=None):
        baseTexture.Texture.__init__(self, name, scObj) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'LiteralVertical'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['loopWithinSet', 'maxTimeOffset',
                                     'levelFieldPolyphonic', 'levelOctavePolyphonic',
                                     'pathDurationFraction']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        self.doc = lang.docTmLiteralVertical

    def _scoreMain(self):
        """creates score
        """
        # texture-wide PATH/PITCH elements
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        #texture-wide TEXTURE (self.textQ amd)options 
        #used for optional parallel voices
        textRepeatToggle    = self.getTextStatic('lws', 'onOff') 
        textMaxTimeOffset    = self.getTextStatic('mto', 'time') 
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfp', 'level') 
        textOctaveLevel = self.getTextStatic('lop', 'level')     

        # when off, the number of sets in the path completely 
        # determines the number of events in the texture
        pathDurationFraction = self.getTextStatic('pdf', 'onOff')   

        # create range of offsets to draw from
        # scale base by distribution from -1 to
        # this gives a range from -1 to 1
        self.gaussPmtrObj = parameter.factory(('randomGauss', .5, .1, -1, 1))
        # used below now
        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            chordLength = len(chordCurrent)
            muteSet = 'off'
            pcTest = 'noNote' # set one note found to filter out rests

            tStartSetReal = copy.deepcopy(tCurrent)
            self.stateUpdate(tCurrent, chordCurrent, None, 
                                  multisetCurrent, None, None)
            
            if textFieldLevel == 'set':
                transCurrent = self.getField(tCurrent) # choose PITCHFIELD
            if textOctaveLevel == 'set':
                octCurrent = self.getOct(tCurrent) # choose OCTAVE

            while 1: # dur of each path
                # to do one chord per event this needs to be controlled
                # not by time per set, but simply by if a single chord
                # has been executed 
                if pathDurationFraction == 'off':
                    if tCurrent > tStartSetReal: break
                else: # sustain entire path over desired dur fraction
                    if tCurrent >= tEndSet: break

                # no ps yet found, give as None, get default
                self.stateUpdate(tCurrent, chordCurrent, None, 
                                      multisetCurrent, None, None)

                if textFieldLevel == 'event':
                    transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                if textOctaveLevel == 'event':
                    octCurrent = self.getOct(tCurrent) # choose OCTAVE

                # choose RHYTHM
                bpm, pulse, dur, sus, acc = self.getRhythm(tCurrent)
                if muteSet == 'on': # make all rests
                    acc = 0 # everything is a rest after chord inex reset
                if acc != 0: # this is a note
                    pcTest = 'noteFound' #only set first time note found
                if acc == 0 and not self.silenceMode: # this is a rest
                    tCurrent = tCurrent + dur
                    continue

                # amp and pan per chord, not voice
                amp = self.getAmp(tCurrent) * acc
                pan = self.getPan(tCurrent)
                tThisChord = copy.deepcopy(tCurrent)
                
                for ps in chordCurrent:
                    self.stateUpdate(tCurrent, chordCurrent, ps, 
                                          multisetCurrent, None, None)
                                          
                    if textFieldLevel == 'voice':
                        transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                    if textOctaveLevel == 'voice':
                        octCurrent = self.getOct(tCurrent) # choose OCTAVE
                    psReal = pitchTools.psToTempered(ps, octCurrent, 
                                          self.temperamentObj, transCurrent)
                    self.stateUpdate(tCurrent, chordCurrent, None, 
                                          multisetCurrent, None, psReal)
                    # aux per voice, post psReal definition
                    auxiliary = self.getAux(tCurrent)

                    # offset value is between -textMaxOffset, 0, and +textMaxOffset
                    offset = self.gaussPmtrObj(0.0) * textMaxTimeOffset
                    tCurrent = tCurrent + offset
                    if tCurrent < 0: # cant start before 0
                        tCurrent = tThisChord # reset

                    eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, sus, 
                                                        acc, amp, psReal, pan, auxiliary)
                    self.storeEvent(eventDict)
                    # restore time to tCurrent before processing offset again
                    tCurrent = tThisChord

                # turn of further notes if all gotten
                if textRepeatToggle == 'off' and pcTest == 'noteFound':
                    muteSet = 'on'
                # move clocks forward by dur unit
                tCurrent = tCurrent + dur

            self.clockForward() # advances path positon
        return 1

        
