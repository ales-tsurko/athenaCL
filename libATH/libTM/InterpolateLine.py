#-----------------------------------------------------------------||||||||||||--
# Name:          InterpolateLinear.py
# Purpose:       linear interpolation b/n generated points.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
from athenaCL.libATH.libTM import baseTexture
from athenaCL.libATH.libPmtr import basePmtr

from athenaCL.libATH import pitchTools
from athenaCL.libATH import language

lang = language.LangObj()


# _docInterpolate = """
# 
# time points are created linearly based on tempo and rhythm values
# a static texture parameter object determines a sampling rate
# the duration between each time-point is calculated
# this width is divided into the necessary samples based on sr
# events are created for each sampple w/n width
# amp values are interpolated between each time point
# 
# in this way gendyn like structures can be created:
# assign dynamic parameter to both rhythm (using convert second) and amp
# sieves could be used to calculate durations and amplitudes
# 
# static parameter objects

# levelInterpolateFrame = event, frame
#     if frame size is updated for each frame or each event
# parameterInterpolationControl = event, frame
#     how often non duration parameters are updated
# snapSustainTime = on, off
#     whether sustain values snap to frame width
# snapEventTime = on, off
#     determines if time points are snapped to grid over the whole duration
#     providing the most even spacing
#     or if time points are allowed to be out of the sampling rate
#     
# when processed as an audioFile, each event becomes a sample
# pitch/path parameters have no effect
# """
# 

class InterpolateLine(baseTexture.Texture):
    """linear interpolation between event points
    """
    def __init__(self, name=None, scObj=None):
        baseTexture.Texture.__init__(self, name, scObj) # init base class
        self.author = 'athenaCL native'
        self.tmName = 'InterpolateLine'
        # will get defaults from object, order determines labels
        self.textPmtrNames = ['pitchSelectorControl', 
                                    'levelFieldMonophonic', 'levelOctaveMonophonic',
                        'interpolationMethodControl',
                      'levelFrameDuration', 'parameterInterpolationControl',
                                 'snapSustainTime', 'snapEventTime']
        self._updateTextPmtrInit() # defines textPmtrNo, textLabels

        # frame dur should be updated only for each event,
        # or for each frame
        self.dynPmtrManifest = [
            {'name':'frameDuration', 'type':'genPmtrObjs',  
                'default': ('oo', ('c', 30)),                             
                'doc': 'duration in seconds of each frame between events'},
            {'name':'exponent', 'type':'genPmtrObjs',    
                'default': ('c', 1),                              
                'doc': 'exponent used for power segment interpolation'},
            ]
        self._updateDynPmtrInit() # defines textPmtrNo, textLabels

        self.doc = lang.docTmInterpolateLine

    def _scoreMain(self):
        """creates score
        """
        # texture-wide time elements
        inst = self.getInst()
        tStart, tEnd = self.getTimeRange()
        tCurrent = tStart

        # get field, octave selection method value
        textFieldLevel = self.getTextStatic('lfm', 'level') 
        textOctaveLevel = self.getTextStatic('lom', 'level')        
        textPitchSelectorControl = self.getTextStatic('psc', 'selectionString') 
        textInterpolationMethodControl = self.getTextStatic('imc', 'method') 
        textLevelFrameDuration = self.getTextStatic('lfd', 'level') 
        textParameterInterpolationControl = self.getTextStatic('pic', 'onOff') 
        textSnapSustainTime = self.getTextStatic('sst', 'onOff') 
        textSnapEventTime = self.getTextStatic('set', 'onOff') 

        # a list of frame data: tStart, dur, eventFlag, interpMethod,interpExponet
        tFrameArray = [] 

        # create a list of chords from the appropriate pitch mode
        for pathPos in self.getPathPos():
            chordCurrent = self.getPitchGroup(pathPos)
            multisetCurrent = self.getMultiset(pathPos)

            tStartSet, tEndSet = self.clockPoints()
            selectorChordPos = basePmtr.Selector(range(len(chordCurrent)),
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
                # silence mode has to be ignored

                amp = self.getAmp(tCurrent) * acc # choose amp, pan
                pan = self.getPan(tCurrent)
                auxiliary = self.getAux(tCurrent) # chooose AUX, pack into list
                eventDict = self.makeEvent(tCurrent, bpm, pulse, dur, sus, acc, 
                                                             amp, psReal, pan, auxiliary)
                # need to store events in order to do proper post-event processing
                self.storeEvent(eventDict)

                # always store event time in array, w/ interp type and exponent
                tFrameArray.append((tCurrent, dur, 1, 
                    textInterpolationMethodControl, 
                    self.getTextDynamic('exponent', tCurrent))) 
                tFrame = copy.deepcopy(tCurrent)

                # check if this is the last event of entire texture
                # if so, do not calculate frames
                if tCurrent + dur > tEnd: 
                    tCurrent = tCurrent + dur
                    break
                
                # process frame start times
                # store first event, as well as interp exponet if needed
                # tFrame is set to tCurrent
                else:     
                    if textLevelFrameDuration == 'event': # one frame dur / event
                        frameDur = self.getTextDynamic('frameDuration', tCurrent)
                        if frameDur < dur:
                            # can eval in loop b/c frameDur is constant
                            while (tFrame + frameDur) < (tCurrent + dur):
                                tFrame = tFrame + frameDur
                                tFrameArray.append((tFrame, frameDur, 0)) 
                     # frame updates / frame
                    elif textLevelFrameDuration == 'frame':
                        while 1:
                            # must calc frameDur to see if it is over e next event
                            frameDur = self.getTextDynamic('frameDuration', tFrame)
                            if (tFrame + frameDur) > (tCurrent + dur):
                                break # cannot fit another frame w/o passing next event
                            tFrame = tFrame + frameDur
                            tFrameArray.append((tFrame, frameDur, 0)) 
                    # update current time after fram processing
                    if textSnapEventTime == 'on':
                        # always use existing frame dur for both event and frame proc
                        # add to last set frame time
                        tCurrent = tFrame + frameDur 
                    else:
                        tCurrent = tCurrent + dur

            # advances path positon
            self.clockForward() 


        # configure which parameters, in EventSequence object, are interpolated
        if textParameterInterpolationControl == 'on':
            active = ['time', 'acc', 'bpm', 'amp', 'ps', 'pan', 'aux'] # 
        elif textParameterInterpolationControl == 'off':
            active = ['time', 'bpm']
        # interpolate events
        self.interpolate(tFrameArray, textSnapSustainTime, active)
        return 1


#         a = bpf.LinearSegment([(0,2),(100,20)])



        
