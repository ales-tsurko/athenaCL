#-----------------------------------------------------------------||||||||||||--
# Name:          MonophonicOrnament.py
# Purpose:       simple texture module for creating an ornamented line.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2003-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import random, copy
import unittest, doctest

from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH import ornament
from athenaCL.libATH import pitchTools
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH import language
lang = language.LangObj()

class MonophonicOrnament(baseTexture.Texture):
    """simple one dimension line algorithm

    >>> #a = MonophonicOrnament('test')
    """
    def __init__(self, name=None):
        baseTexture.Texture.__init__(self, name) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'MonophonicOrnament'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['loopWithinSet', 'ornamentLibrarySelect',
                                     'ornamentMaxDensity',
                                     'levelFieldMonophonic', 'levelOctaveMonophonic']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels
        
        # setup ornament, store names in refDict
        self._ornGroup()
        self.refDict = {'ornGroupNames': self._ornGroupNames()}
        self.doc = lang.docTmMonophonicOrnament
        
    def _ornGroup(self):
        # see ornament.py for detailed information
        # name, position, harmonicLang, microtone
        self.ornGroupLib = { 
        'diatonicGroupA' : [('turn.0,1,0,-1.b','attack','path', .5),
                                  ('trill.0,1.b','release','path', .5),
                                  ('rise.-2,-1','attack','path', .5),
                                  ('trill.0,1.a','release','microtone', .125),
                                  ('arc.-1,2,1','attack','path', .5),
                                  ('fall.2,1','attack','path', .5),
                                  ('trill.0,1.a','release','microtone', .092),
                                  ('rise.1,2','release','path', .5),
                                  ('arc.0,1','attack','path', .5),
                                  ('fall.1,0,-1','release','path', .5),],

        'diatonicGroupB' : [('turn.0,1,0,-1.b','attack','path', .5),
                                  ('trill.0,1.b','release','path', .5),
                                  ('fall.2,1','attack','path', .5),
                                  ('arc.0,1','attack','path', .5),],

        'microGroupA'   : [  ('turn.0,1,0,-1.b','attack','microtone', .11),
                                  ('trill.0,1.b','release','microtone', .13),
                                  ('rise.-1','attack','path', .09),
                                  ('rise.-2,-1','attack','path', .05),
                                  ('arc.-1,2,1','attack','microtone', .08),
                                  ('fall.2,1','attack','path', .10),
                                  ('rise.1,2','release','microtone', .02),
                                  ('arc.0,1','attack','microtone', .034543),
                                  ('fall.1,0,-1','release','microtone', .0654),],

        'microGroupB'   : [  ('rise.-1','attack','path', .5),
                                  ('arc.-1,2,1','attack','microtone', .13),
                                  ('fall.2,1','attack','path', .5),
                                  ('rise.-1','attack','microtone', .15),
                                  ('arc.0,1','attack','microtone', .14543),
                                  ('fall.1,0,-1','release','microtone', .07),],
    
        'microGroupC'   : [  ('rise.-1','attack','microtone', .17),
                                  ('arc.-1,2,1','attack','microtone', .065),
                                  ('rise.-1','attack','microtone', .19),
                                  ('arc.0,1','attack','microtone', .17),
                                  ('fall.1,0,-1','release','microtone', .08),
                                  ('fall.2,1','attack','microtone', .06),],

        'chromaticGroupA': [('rise.-1','attack','chromatic', .17),
                                  ('rise.-1','attack','chromatic', .13),
                                  ('arc.0,1','attack','chromatic', .10),
                                  ('fall.1,0,-1','release','chromatic', .08),
                                  ('trill.0,1.a','release','chromatic', .092),
                                  ],
    
        'trillGroupA'    : [ ('rise.-1','attack','path', .17),
                                  ('trill.0,1.a','release','microtone', .21),
                                  ('trill.0,1.a','release','microtone', .15),
                                  ('trill.0,1.b','attack','microtone', .12),
                                  ('trill.0,1.b','release','microtone', .17),
                                  ('turn.0,1,0,-1.a','release','microtone', .27),
                                  ('turn.0,1,0,-1.a','attack','microtone', .05),
                                  ('turn.0,1,0,-1.b','release','path', .18),
                                  ('turn.0,1,0,-1.b','attack','path', .18),]
                                }

    def _ornGroupNames(self):
        ornList = list(self.ornGroupLib.keys()) 
        ornList.append('off') # add off option
        return ornList

    def _ornGroupGet(self, name):
        if name == 'off':
            return None
        else:
            return self.ornGroupLib[name]

    def _scoreMain(self):
        """creates score

        >>> from athenaCL.libATH.libTM import texture
        >>> ti = texture.factory('MonophonicOrnament')
        >>> ti.tmName == 'MonophonicOrnament'
        True
        >>> ti.loadDefault()
        >>> ti.score() == True
        True

        """
        self.ornamentObj = ornament.Ornament(self.pmtrObjDict,
                                                    self.temperamentObj)

        # texture-wide PATH/PITCH elements
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        #texture-wide TEXTURE (self.textQ amd)options 
        #used for optional parallel voices
        textRepeatToggle    = self.getTextStatic('lws', 'onOff') 
        # create a list of chords from the appropriate pitch mode
        ornamentSwitch = self.getTextStatic('ols', 'libraryName') 
        ornamentMaxDensity = self.getTextStatic('omd', 'percent') 
        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfm', 'level') 
        textOctaveLevel = self.getTextStatic('lom', 'level')        
        # create a randomUniform parameter object to control ornament control
        # values between 0 and 1; if pmtr() <= ornamentMaxDensity
        ruPmtrObj = parameter.factory(('randomUniform', 0, 1))
        

        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            chordLength = len(chordCurrent)
            chordIndex = 0
            muteSet = 'off'
            psTest = []
            ornamentIndex = 0

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
                psTest.append(ps) 
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
                                      
                bpm, pulse, dur, sus, acc = self.getRhythm(tCurrent)
                if muteSet == 'on': # make all rests
                    acc = 0 # everything is a rest after chord inex reset
                if acc == 0 and not self.silenceMode: # this is a rest
                    chordIndex = chordIndex - 1 # dont count this note if a rest
                    psTest = psTest[:-1] # drop off last addition
                    tCurrent = tCurrent + dur
                    continue

                # amp, pan, aux choosen per event
                amp = self.getAmp(tCurrent) * acc
                pan = self.getPan(tCurrent)
                auxiliary = self.getAux(tCurrent)

                parentEventDict = self.makeEvent(tCurrent, bpm, pulse, dur, 
                                                 sus, acc, amp, psReal, pan, auxiliary)
                refDict = self.getRefDict(tCurrent)
                if ornamentSwitch != 'off':
                    # check if an ru value is <= ornament density (if 1, always)
                    # time value is not important
                    if ruPmtrObj(tCurrent) <= ornamentMaxDensity:
                        repretory = self._ornGroupGet(ornamentSwitch)
                        #a, b, c, d = repretory[ornamentIndex] # this will do in order
                        a, b, c, d = random.choice(repretory) # choose orn at random
                        subEventArray = self.ornamentObj.create(refDict,a,b,c,d)                         
                        self.storePolyEvent(parentEventDict, subEventArray, 'orn')
                        ornamentIndex = ornamentIndex + 1 # increment for when ordered
                        if ornamentIndex == len(repretory):
                            ornamentIndex = 0
                    else:
                        self.storeEvent(parentEventDict)
                else: # ornament == 'off': # dont do ornaments
                    self.storeEvent(parentEventDict)

                # turn of further notes if all gotten
                if textRepeatToggle == 'off' and len(psTest) >= chordLength:
                    muteSet = 'on'

                # move clocks forward by dur unit
                tCurrent = tCurrent + dur
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