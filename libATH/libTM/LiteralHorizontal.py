#-----------------------------------------------------------------||||||||||||--
# Name:          LiteralHorizontal.py
# Purpose:       literal horizontal presentation of texture.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH import pitchTools
from athenaCL.libATH import language
lang = language.LangObj()


class LiteralHorizontal(baseTexture.Texture):
    """simple one dimension line algorithm
    """
    def __init__(self, name=None, scObj=None):
        baseTexture.Texture.__init__(self, name, scObj) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'LiteralHorizontal'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['loopWithinSet',
                                    'levelFieldMonophonic', 'levelOctaveMonophonic']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels

        self.doc = lang.docTmLiteralHorizontal

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
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfm', 'level') 
        textOctaveLevel = self.getTextStatic('lom', 'level')        

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            chordLength = len(chordCurrent)
            chordIndex = 0
            muteSet = 'off'
            pcTest = []

            tStartSetReal = copy.deepcopy(tCurrent)
            self.stateUpdate(tCurrent, chordCurrent, None, 
                                  multisetCurrent, None, None)

            if textFieldLevel == 'set':
                transCurrent = self.getField(tCurrent) # choose PITCHFIELD
            if textOctaveLevel == 'set':
                octCurrent = self.getOct(tCurrent) # choose OCTAVE

            while 1: # PITCH in CHORD
                if tCurrent >= tEndSet: break

                ps = chordCurrent[chordIndex] # choose PC from CHORD
                pcTest.append(ps)
                chordIndex = chordIndex + 1 # shift to next pitch
                if chordIndex >= chordLength:
                    chordIndex = 0
                self.stateUpdate(tCurrent, chordCurrent, ps, 
                                      multisetCurrent, None, None)

                if textFieldLevel == 'event':
                    transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                if textOctaveLevel == 'event':
                    octCurrent = self.getOct(tCurrent) # choose OCTAVE
                psReal = pitchTools.psToTempered(ps, octCurrent, 
                                      self.temperamentObj, transCurrent)         
                self.stateUpdate(tCurrent, chordCurrent, ps, 
                                      multisetCurrent, None, psReal)

                bpm, pulse, dur, sus, acc = self.getRhythm(tCurrent) # choose RHYTHM
                if muteSet == 'on': # make all rests
                    acc = 0 # everything is a rest after chord inex reset
                if acc == 0 and not self.silenceMode: # this is a rest
                    chordIndex = chordIndex - 1 # dont count this note if a rest
                    pcTest = pcTest[:-1] # drop off last addition
                    tCurrent = tCurrent + dur
                    continue

                amp = self.getAmp(tCurrent) * acc # choose AMP, PAN
                pan = self.getPan(tCurrent)
                auxiliary = self.getAux(tCurrent) # chooose AUX, pack into list

                eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, sus, acc, 
                                                    amp, psReal, pan, auxiliary)
                self.storeEvent(eventDict)
                # turn of further notes if all gotten
                if textRepeatToggle == 'off' and len(pcTest) >= chordLength:
                    muteSet = 'on'

                # move clocks forward by dur unit
                tCurrent = tCurrent + dur           
            # return value to check for errors   
            self.clockForward() # advances path positon
        return 1

        
