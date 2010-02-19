#-----------------------------------------------------------------||||||||||||--
# Name:          HarmonicShuffle.py
# Purpose:       Texture to provide procedural access to path data
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest

from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.libPmtr import parameter   
from athenaCL.libATH import pitchTools
from athenaCL.libATH import language
from athenaCL.libATH import drawer
lang = language.LangObj()


#-----------------------------------------------------------------||||||||||||--

class HarmonicShuffle(baseTexture.Texture):
    def __init__(self, name=None):
        """
        #>>> a = HarmonicShuffle('test')
        """
        baseTexture.Texture.__init__(self, name) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'HarmonicShuffle'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['multisetSelectorControl', 'pitchSelectorControl',
                                     'maxTimeOffset', 
                                     'levelFieldPolyphonic', 'levelOctavePolyphonic']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        # define ordered list of dynamic parameters
        # [{name: x, type: x, default: x)]
        self.dynPmtrManifest = [
            {'name':'countPerMultiset', 'type':'genPmtrObjs',   
                'default': ('c',2),                          
                'doc': 'number of simultaneities created from the selected Multiset'},
            {'name':'countPerSimultaneity', 'type':'genPmtrObjs',    
                'default': ('c',0),                          
                'doc': 'number of pitches extracted from the selected Multiset, where zero is all pitches'},
            ]
        self._updateDynPmtrInit() # defines textPmtrNo, textLabels
        self.doc = lang.docTmHarmonicShuffle

    def _scoreMain(self):
        """creates score
        note: octave choose for every note

        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('HarmonicShuffle')
        >>> ti.tmName == 'HarmonicShuffle'
        True
        >>> ti.loadDefault()
        >>> ti.score() == True
        True
        """
        # texture-wide time elements
        inst = self.getInst()
        
        # needed for preliminary parameter values
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        # get static texture values
        textMultisetSelectorControl = self.getTextStatic('msc', 'selectionString')       
        textPitchSelectorControl = self.getTextStatic('psc', 'selectionString') 
        textMaxTimeOffset    = self.getTextStatic('mto', 'time') 
        textFieldLevel = self.getTextStatic('lfp', 'level') 
        textOctaveLevel = self.getTextStatic('lop', 'level')     
  
        pLen = self.getPathLen()
        selectorMultisetPos = basePmtr.Selector(range(pLen),
                                                         textMultisetSelectorControl)

        # random generator for creating offset in vetical attacks
        # same technique used in LiteralVertical, DroneArticulate
        self.gaussPmtrObj = parameter.factory(('randomGauss', .5, .1, -1, 1))

        while tCurrent < tEnd:
            pathPos = selectorMultisetPos() # select path position
    
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            # get number of simultaneities from this multiset
            # count is probabilistic, absolute value; cannot be zero
            multisetCount = abs(drawer.floatToInt(
                self.getTextDynamic('countPerMultiset', tCurrent), 'weight'))
            # make zero == 1; alternatively, make zero a skib and continue
            if multisetCount == 0: multisetCount = 1

            if textFieldLevel == 'set':
                transCurrent = self.getField(tCurrent) # choose PITCHFIELD
            if textOctaveLevel == 'set':
                octCurrent = self.getOct(tCurrent) # choose OCTAVE

            # number of times a simultaneity is drawn
            for k in range(multisetCount):
                if tCurrent > tEnd: break

                # create a selector to get pitches from chord as index values
                # only need to create one for each chord
                selectorChordPos = basePmtr.Selector(range(len(chordCurrent)),
                                                                 textPitchSelectorControl)

                # determine how many pitches in this simultaneity
                # abs value, rounded to nearest integer
                simultaneityCount = abs(drawer.floatToInt(
                    self.getTextDynamic('countPerSimultaneity', tCurrent), 'weight'))
                # if zero set to max chord size
                if simultaneityCount == 0: 
                    simultaneityCount = len(chordCurrent)
                elif simultaneityCount > len(chordCurrent):
                    simultaneityCount = len(chordCurrent)

                self.stateUpdate(tCurrent, chordCurrent, None, 
                                      multisetCurrent, None, None)
    
                if textFieldLevel == 'event':
                    transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                if textOctaveLevel == 'event':
                    octCurrent = self.getOct(tCurrent) # choose OCTAVE

                # rhythm, amp, pan, aux: all chosen once per simultaneity
                bpm, pulse, dur, sus, acc = self.getRhythm(tCurrent) 
                if acc == 0 and not self.silenceMode: # this is a rest
                    tCurrent = tCurrent + dur
                    continue

                amp = self.getAmp(tCurrent) * acc # choose amp, pan
                pan = self.getPan(tCurrent)
    
                tThisChord = copy.deepcopy(tCurrent)

                # get each pitch in the simultaneity
                for i in range(simultaneityCount): # pitch in chord

                    ps = chordCurrent[selectorChordPos()] # get position w/n chord
                    self.stateUpdate(tCurrent, chordCurrent, ps, 
                                          multisetCurrent, None, None)
                                          
                    if textFieldLevel == 'voice':
                        transCurrent = self.getField(tCurrent) # choose PITCHFIELD
                    if textOctaveLevel == 'voice':
                        octCurrent = self.getOct(tCurrent) # choose OCTAVE

                    psReal = pitchTools.psToTempered(ps, octCurrent, 
                                          self.temperamentObj, transCurrent)                                      
                    self.stateUpdate(tCurrent, chordCurrent, ps, 
                                          multisetCurrent, None, psReal)

                    # aux values are drawn here once per voice; 
                    # this is common to TMs: DroneArticulate, DroneSustain
                    auxiliary = self.getAux(tCurrent) # chooose AUX, pack into list
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

                # move clocks forward by dur unit
                tCurrent = tCurrent + dur        

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