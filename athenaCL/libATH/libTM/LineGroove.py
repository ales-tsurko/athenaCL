#-----------------------------------------------------------------||||||||||||--
# Name:          LineGroove.py
# Purpose:       simple texture module for creating a linear line.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest

from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH import pitchTools
from athenaCL.libATH import language
lang = language.LangObj()

class LineGroove(baseTexture.Texture):
    """simple one dimension line algorithm

    """
    def __init__(self, name=None):
        baseTexture.Texture.__init__(self, name) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'LineGroove'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['parallelMotionList', 'pitchSelectorControl', 
                                    'levelFieldMonophonic', 'levelOctaveMonophonic']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        self.doc = lang.docTmLineGroove

    def _scoreMain(self):
        """creates score

        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('lg')
        >>> ti.tmName == 'LineGroove'
        True
        >>> ti.loadDefault()
        >>> ti.score() == True
        True
        """
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        #texture-wide (self.textQ amd)options 
        #used for optional parallel voices
        textParallelVoiceList = self.getTextStatic('pml', 'transpositionList') 
        textParallelDelayTime = self.getTextStatic('pml', 'timeDelay')       
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfm', 'level') 
        textOctaveLevel = self.getTextStatic('lom', 'level')        
        textPitchSelectorControl = self.getTextStatic('psc', 'selectionString') 

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            selectorChordPos = basePmtr.Selector(list(range(len(chordCurrent))),
                                                             textPitchSelectorControl)
            tStartSetReal = copy.deepcopy(tCurrent)
            self.stateUpdate(tCurrent, chordCurrent, None, 
                                  multisetCurrent, None, None)

            if textFieldLevel == 'set':
                transCurrent = self.getField(tCurrent) # choose PITCHFIELD
            if textOctaveLevel == 'set':
                octCurrent = self.getOct(tCurrent) # choose OCTAVE

            while 1: # pitch in chord 
                if tCurrent >= tEndSet: break
                # choose pc from chord
                ps = chordCurrent[selectorChordPos()] # get position w/n chord
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
                # Parallel transposition 
                offset = 0
                for parallelVoice in textParallelVoiceList:
                      #offset to avoid amp problems, correct error w/ offset
                    tCurrent = tCurrent + textParallelDelayTime          
                    offset = offset + textParallelDelayTime
                    psText = pitchTools.psTransposer(psReal, parallelVoice)
                    eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, sus, 
                                                             acc, amp, psText, pan, auxiliary)
                    self.storeEvent(eventDict)
                # move clocks forward by dur unit
                tCurrent = (tCurrent + dur) - offset          

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

