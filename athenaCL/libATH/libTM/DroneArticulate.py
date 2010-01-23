#-----------------------------------------------------------------||||||||||||--
# Name:          DroneArticulate.py
# Purpose:       vertical, articulate cloud of path sets.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest

from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH import pitchTools
from athenaCL.libATH.libPmtr import parameter   
from athenaCL.libATH import language
lang = language.LangObj()

class DroneArticulate(baseTexture.Texture):
    """polyphonic vertical drone
    """
    def __init__(self, name=None):
        baseTexture.Texture.__init__(self, name) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'DroneArticulate'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['maxTimeOffset',
                                     'levelFieldMonophonic', 'levelOctaveMonophonic']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        self.doc = lang.docTmDroneArticulate

    def _scoreMain(self):
        """creates score
        """
        # texture-wide PATH/PITCH elements
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart
        tCumulative = copy.deepcopy(tStart) # store fake time for pmtr gen

        #texture-wide TEXTURE (self.textQ amd)options 
        #used for optional parallel voices
        textMaxTimeOffset    = self.getTextStatic('mto', 'time') 
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfm', 'level') 
        textOctaveLevel = self.getTextStatic('lom', 'level')

        # create range of offsets to dray from
        # scale base by distribution from -1 to
        # this gives a range from -1 to 1
        self.gaussPmtrObj = parameter.factory(('randomGauss', .5, .1, -1, 1))

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            chordLength = len(chordCurrent)
            muteSet = 'off'
            #not sure what this was used for
            #pcTest = 'noNote' # set one note found to filter out rests
            tStartSetReal = copy.deepcopy(tCurrent)
            
            self.stateUpdate(tCurrent, chordCurrent, None, 
                                  multisetCurrent, None, None)

            if textFieldLevel == 'set':
                transCurrent = self.getField(tCurrent) # choose PITCHFIELD
            if textOctaveLevel == 'set':
                octCurrent = self.getOct(tCurrent) # choose OCTAVE

            # create a clock for each voice
            tVoice = []
            for x in range(0,len(chordCurrent)):
                tVoice.append(copy.deepcopy(tCurrent))

            i = 0 # voice count
            for ps in chordCurrent: # psReal values in chord
                self.stateUpdate(tVoice[i], chordCurrent, ps, 
                                      multisetCurrent, None, None)
                                      
                while tVoice[i] < tEndSet:
                    self.stateUpdate(tVoice[i], chordCurrent, ps, 
                                          multisetCurrent, None, None)

                    bpm, pulse, dur, sus, acc = self.getRhythm(tCumulative)
                    if acc == 0 and not self.silenceMode: # this is a rest
                        tVoice[i] = tVoice[i] + dur
                        tCumulative = tCumulative + dur
                        continue

                    if textFieldLevel == 'event':
                        transCurrent = self.getField(tCumulative) # choose PITCHFIELD
                    if textOctaveLevel == 'event':
                        octCurrent = self.getOct(tCumulative) # choose OCTAVE
                    psReal = pitchTools.psToTempered(ps, octCurrent, 
                                          self.temperamentObj, transCurrent)
                    self.stateUpdate(tVoice[i], chordCurrent, ps, 
                                          multisetCurrent, None, psReal)

                    amp = self.getAmp(tCumulative) * acc
                    pan = self.getPan(tCumulative)
                    auxiliary = self.getAux(tCumulative)

                    # offset value is b/n -textMaxOffset, 0, and +textMaxOffset
                    offset = self.gaussPmtrObj(0.0) * textMaxTimeOffset
             
                    tVoice[i] = tVoice[i] + offset
                    tCumulative = tCumulative + offset
                    if tVoice[i] < 0: # cant start before 0
                        tVoice[i] = tStartSetReal # reset

                    eventDict = self.makeEvent(tVoice[i], bpm, pulse, dur, sus, 
                                                          acc, amp, psReal, pan, auxiliary)
                    self.storeEvent(eventDict)

                    tVoice[i] = tVoice[i] + dur
                    tCumulative = tCumulative + dur
                i = i + 1 # increment voice count

            # find longest voice
            tMaxVoice = 0
            for i in range(0,len(chordCurrent)):
                if tVoice[i] >= tMaxVoice:
                    tMaxVoice = tVoice[i]
            # move clocks forward by dur unit
            tCurrent = tMaxVoice     # new current is at max length
            # do not chang tCumulative, is is already expanding
            self.clockForward() # advances path positon

        return 1

        

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

