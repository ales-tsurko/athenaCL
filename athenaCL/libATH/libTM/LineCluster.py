#-----------------------------------------------------------------||||||||||||--
# Name:          LineCluster.py
# Purpose:       simple texture module for creating cluster chords.
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

_MOD = 'LineCluster.py'

class LineCluster(baseTexture.Texture):
    """simple one dimension chord algorithm

    #>>> a = LineCluster('test')
    """
    def __init__(self, name=None):
        baseTexture.Texture.__init__(self, name) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'LineCluster'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['parallelMotionList', 'pitchSelectorControl',
                                     'levelFieldPolyphonic', 'levelOctavePolyphonic']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        self.doc = lang.docTmLineCluster


    def _scoreMain(self):
        """creates score
        """
        # texture-wide PATH/PITCH elements
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        # texture-wide TEXTURE (self.textQ amd)options
        #used for optional parallel voices
        textParallelVoiceList = self.getTextStatic('pml', 'transpositionList') 
        textParallelDelayTime = self.getTextStatic('pml', 'timeDelay')       
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfp', 'level') 
        textOctaveLevel = self.getTextStatic('lop', 'level')        
        textPitchSelectorControl = self.getTextStatic('psc', 'selectionString') 
        #textNonRedundantSwitch = self.getTextStatic('nrs', 'onOff') 

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints() 
#             if textNonRedundantSwitch == 'on': selectorControl = 'randomPermutate'
#             else: selectorControl = 'randomChoice'
            selectorChordPos = basePmtr.Selector(range(len(chordCurrent)),
                                                             textPitchSelectorControl)
            tStartSetReal = copy.deepcopy(tCurrent)
            self.stateUpdate(tCurrent, chordCurrent, None, 
                                  multisetCurrent, None, None)

            if textFieldLevel == 'set':
                transCurrent = self.getField(tCurrent) # choose PITCHFIELD
            if textOctaveLevel == 'set':
                octCurrent = self.getOct(tCurrent) # choose OCTAVE

            while 1: # PITCH in CHORD 
                if tCurrent >= tEndSet: break

                bpm, pulse, dur, sus, acc = self.getRhythm(tCurrent) # choose RHYTHM
                if acc == 0 and not self.silenceMode: # this is a rest
                    tCurrent = tCurrent + dur
                    continue

                # this ps should be used as ROOT;
                # this is _not_ implemented yet, however 
                # choose PC from CHORD 
                ps = chordCurrent[selectorChordPos()]   
                self.stateUpdate(tCurrent, chordCurrent, ps, 
                                      multisetCurrent, None, None)
                    
                if textFieldLevel == 'event':
                    transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                if textOctaveLevel == 'event':
                    octCurrent = self.getOct(tCurrent) # choose OCTAVE
                    
                #subprocess psChord is a list of PCH's needed to make chord, 
                psChord = []
                for pitchSpace in chordCurrent:
                    if textFieldLevel == 'voice':
                        transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                    if textOctaveLevel == 'voice':
                        octCurrent = self.getOct(tCurrent) # choose OCTAVE
                    psReal = pitchTools.psToTempered(pitchSpace, octCurrent, 
                                          self.temperamentObj, transCurrent)
                    psChord.append(psReal)
                    
                # amp and pan done for each chord, not voice
                amp = self.getAmp(tCurrent) * acc
                pan = self.getPan(tCurrent)

                #do this for each PCH in psChord, already transposed
                for psReal in psChord:
                    self.stateUpdate(tCurrent, chordCurrent, pitchSpace,
                                          multisetCurrent, None, psReal)
                    # choose aux for each voice
                    auxiliary = self.getAux(tCurrent)  
                    eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, sus, 
                                                        acc, amp, psReal, pan, auxiliary)
                    self.storeEvent(eventDict)
                    # parellel transposition 
                    offset = 0
                    for parallelVoice in textParallelVoiceList:
                        #offset to avoid amp problems, correct error w/ offset
                        tCurrent = tCurrent + textParallelDelayTime          
                        offset = offset + textParallelDelayTime
                        psText = pitchTools.psTransposer(psReal, parallelVoice)
                        eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, 
                                                     sus, acc, amp, psText, pan, auxiliary)
                        self.storeEvent(eventDict)

                #----------------------------
                # move clocks forward by dur unit
                tCurrent = (tCurrent + dur) - offset         

            self.clockForward() # advances path positon 
        # return value to check for errors   
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

