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
from athenaCL.libATH import pitchTools
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH import language
lang = language.LangObj()


class DroneSustain(baseTexture.Texture):
    """simple one dimension line algorithm

    >>> a = DroneSustain()
    """
    def __init__(self, name=None):
        baseTexture.Texture.__init__(self, name) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'DroneSustain'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['maxTimeOffset',
                                     'levelFieldPolyphonic', 'levelOctavePolyphonic']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        self.doc = lang.docTmDroneSustain

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
        textMaxTimeOffset    = self.getTextStatic('mto', 'time') 
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfp', 'level') 
        textOctaveLevel = self.getTextStatic('lop', 'level')        

        # this gives a range from -1 to 1
        self.gaussPmtrObj = parameter.factory(('randomGauss', .5, .1, -1, 1))

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            chordLength = len(chordCurrent)
            tStartSetReal = copy.deepcopy(tCurrent)
            
            self.stateUpdate(tCurrent, chordCurrent, None, 
                                  multisetCurrent, None, None)
            if textFieldLevel == 'set':
                transCurrent = self.getField(tCurrent) # choose PITCHFIELD
            if textOctaveLevel == 'set':
                octCurrent = self.getOct(tCurrent) # choose OCTAVE

            while 1: # PITCH in CHORD
                if tCurrent >= tEndSet: break
                # no ps yet found, give as None, get default
                self.stateUpdate(tCurrent, chordCurrent, None, 
                                      multisetCurrent, None, None)

                # choose RHYTHM, no parameter used
                dur = tEndSet - tCurrent # total time of set
                sus = dur
                acc = 1 # no rests
                pulse = '(1,1,1)'
                bpm = None
                if acc == 0 and not self.silenceMode: # this is a rest
                    tCurrent = (tCurrent + dur)
                    continue
                
                if textFieldLevel == 'event':
                    transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                if textOctaveLevel == 'event':
                    octCurrent = self.getOct(tCurrent) # choose OCTAVE
                    
                # amp and pan per chord, not voice
                amp = self.getAmp(tCurrent) * acc 
                pan = self.getPan(tCurrent)                 
                    
                tThisChord = copy.deepcopy(tCurrent)
                for ps in chordCurrent:
                    if textFieldLevel == 'voice':
                        transCurrent = self.getField(tThisChord) # choose PITCHFIELD
                    if textOctaveLevel == 'voice':
                        octCurrent = self.getOct(tThisChord) # choose OCTAVE

                    psReal = pitchTools.psToTempered(ps, octCurrent, 
                                          self.temperamentObj, transCurrent)
                    self.stateUpdate(tCurrent, chordCurrent, ps,
                                          multisetCurrent, None, psReal)
                    # calculate for every voice in chord
                    auxiliary  = self.getAux(tCurrent) # chooose AUX, in list
                    # offset value is between 0, and +textMaxOffset (abs used)
                    offset = abs(self.gaussPmtrObj(0.0)) * textMaxTimeOffset
                    tCurrent = tCurrent + offset
                    if tCurrent < 0: # cant start before 0
                        tCurrent = tThisChord # reset

                    eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, sus, 
                                                            acc, amp, psReal, pan, auxiliary)
                    self.storeEvent(eventDict)
                    # all notes start at the begninng of this chord
                    tCurrent = tThisChord
                # move clocks forward by dur unit
                tCurrent = tCurrent + dur     

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