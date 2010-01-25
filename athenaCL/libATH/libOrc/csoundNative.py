#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          csoundNative.py
# Purpose:       native csound instrument definitions instruments.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import time
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import language
from athenaCL.libATH import pitchTools
lang = language.LangObj()
from athenaCL.libATH.libOrc import baseOrc


class CsoundNative(baseOrc.Orchestra):
    """built-in csound instruments"""
    def __init__(self):
        """
        >>> a = CsoundNative()
        """
        baseOrc.Orchestra.__init__(self)

        self.name = 'csoundNative'
        self.srcStr = None # string representation for writing

        self._headMono = """
sr       = 44100
kr       = 4410
ksmps    = 10
nchnls = 1
"""
        self._headStereo = """
sr       = 44100
kr       = 4410
ksmps    = 10
nchnls = 2
"""
        self._headQuad = """
sr       = 44100
kr       = 4410
ksmps    = 10
nchnls = 4
"""
        # needed in score, not in orchestra

# f syntax

# p1 -- Table number by which the stored function will be known. A negative number requests that the table be destroyed.
# p2 Action time of function generation (or destruction) in beats.
# p3 Size of function table (i.e. number of points) Must be a power of 2, or a power-of-2 plus 1 (see below). Maximum table size is 16777216 (2**24) points.
# p4 Number of the GEN routine to be called A negative value will cause rescaling to be omitted.
# p5 
# p6 Parameters whose meaning is determined by the particular GEN routine.

        
        self._fTables = """
;f-tables--shared
    f 1  0 16384 10  1                                                      ; sine wave
    f 2  0 1025   5  1 1024 .002                                            ; bell
    f 3  0 16384 10  1                                                      ; sine wave
    f 4  0 16384 10  1 .5 .3 .25 .2 .167 .14 .125 .111              ; sawtooth 
    f 5  0 16384 10  1 0     .3  0  .2   0   .14    0    .111               ; square      
    f 6  0 16384 10  1 1 1 1 .7 .5 .3 .1                                ; Pulse
    f 7  0 2048  19  .5 1 270 1                                         ; sigmoid rise
    f 8  0 4097  7    0 100 .1 300 3 600 1 3000 .01 96 0            ; buzz
    f 9  0 256   10  1                                                      ; low rez sine
    f 13 0 1024  8    -.8 42 -.78   400 -.7 140 .7   400 .78 42 .8 ; distortion

    f 14 0 1024  -20 1                      ; hanning window w/ max value of 1
    f 15 0 16384 7    -1 128 0 128 1        ; a simple phasor for driving sahs

;f-tables--i20
    ;exponentially decaying amplitude envelope for carrier signal
    f 201         0      512        5         1 512  .001     
    ;amplitude envelope for frequency modulation        
    f 202         0      512        7         1 64      0     448    0   
    ;waveform of carrier signal 
    f 203         0      512        9         1 1       0                

;f-tables--i21, i23
    f 210 0 512  10 1                                     ; carriers
    f 211 0 1024  5  .0001 200 1 674 1 150 .0001      ; amplitude envelope
    f 212 0 1024  5  1 1024 .0001                         ; index envelope

;f-tables--i22
    f 231 0 512 7    1   64  0  448  0                ; index envelope
    f 251 0 513 5   .8   113 1  10    1 390 .0001     ; amplitude envelope
"""

        # instrument to add:
        # x. a huge bank of filters, each with an oscillating cf and variable bandwidth. subtractive, but possible fm operations at high enough fqs...

        self._instrNumbers = (3,4,5,6,
                         11,12,13,14,15,16,
                            17, # 1.4.3
                         20,21,22,23,
                         30,31,32,33,34, 
                            35, # parametric filter
                            36,
                            #37,    # cross synthesis working yet
                         40,41, # 1.4.2
                         42,43,44,45,46,47,48, # 1.4.3 vocoder
                         50,51,52,
                         60,61,62,
                         70,71,72,73,74,
                         80,81,82,
                         #90 # physical models here do not work yet
                         #100 # pvoc file problems prohibit analysis use
                         110, 111, # 1.4.3
                         130, 131, 132, 133, # 1.4.3
                         140,141,142,143,144,145,146, # 1.4.3 vocoder
                         230, 231, 232, 233, 234, # 1.4.3
                         240, 241, # 1.4.3
                         )
        
        # on initialization, load a dictionary of objects for use
        self._instrObjDict = {}
        globalDict = globals()
        for iNo in self._instrNumbers:
            objAttr = globalDict['Inst%i' % iNo]
            self._instrObjDict[iNo] = objAttr() # instantiate obj
        

    #-----------------------------------------------------------------------||--
    def instNoValid(self, iNo):
        """test if an instrument number is valid

        >>> a = CsoundNative()
        >>> a.instNoValid(3)
        1
        """
        if drawer.isInt(iNo) and iNo in self._instrNumbers:
            return 1
        else:
            return 0

    def instNoList(self, format=None):
        """return a list of instrument numbers; if
        a list is not availabe, return None"""
        if format == 'user':
            return drawer.listToStr(self._instrNumbers)
        return self._instrNumbers

    def _orcTitle(self):
        msg = []
        msg.append(';athenaCL\n')
        msg.append(';%s\n' % lang.msgAthURL)
        msg.append((';%s\n\n' % time.asctime(time.localtime())))
        return ''.join(msg)

    def _getInstObj(self, iNo):
        if iNo in self._instrObjDict.keys(): # already loaded
            return self._instrObjDict[iNo] # call attribute of module to get object
        else:
            raise ValueError, 'bad insturment number given: %s' % iNo
            
    def getScoFtables(self):
        """public method as needed in score
        this may not be necessary but for external processing as needed"""
        return self._fTables

    def constructOrc(self, noChannels=2, instList=None):
        """buildes a string of an entire orchestra
        provides proper header and output sections based on 
        number of channels

        >>> a = CsoundNative()
        >>> a.constructOrc(2, [3,4,5])
        >>> len(a.srcStr)
        4418
        """
        self.noChannels = noChannels
        msg = []
        msg.append(self._orcTitle())
        if self.noChannels  == 1:
            msg.append(self._headMono)
        elif self.noChannels == 2:
            msg.append(self._headStereo)
        elif self.noChannels == 4:
            msg.append(self._headQuad)

        #self.instrObjDict = {}
        if instList == None: # if not given, add all instruments
            instList = self.instNoList()
        for number in instList:
            if not self.instNoValid(number):
                print lang.WARN, 'instrument %i not available.' % number
                continue
            instrObj = self._getInstObj(number)
            msg.append(instrObj.buildInstrDef(noChannels))
        self.srcStr = ''.join(msg)

    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        pmtrFields includes 6 default values

        >>> a = CsoundNative()
        >>> a.getInstInfo(3)
        ({3: ('sineDrone', 6, {})}, [3])
        """
        if iNo == None:
            instrList = self.instNoList() # use method
        else:
            instrList = [iNo,]
        #self.instrObjDict = {} # this used to store inst obj data
        instInfoDict = {}
        for number in instrList:
            instrObj = self._getInstObj(number)
            instInfoDict[number] = (instrObj.name, 
                                            instrObj.pmtrFields,
                                            instrObj.pmtrInfo)
        return instInfoDict, instrList

    def getInstPreset(self, iNo, auxNo=None):
        """returns a dictionary of default values for one instrument
    
        >>> a = CsoundNative()
        >>> a.getInstPreset(6)
        {'auxQ0': ('c', 0.5), 'auxQ1': ('c', 0.5), 'auxQ2': ('c', 10000), 'auxQ3': ('c', 400), 'auxQ4': ('c', 1)}
        """
        instrObj = self._getInstObj(iNo)
        presetDict = instrObj.getPresetDict() # converts to aux0 fist pos
        return presetDict

    def getInstName(self, iNo):
        'returns a string of name'
        instrObj = self._getInstObj(iNo)
        return instrObj.name

    def getInstAuxNo(self, iNo):
        instrObj = self._getInstObj(iNo)
        return instrObj.auxNo

    def getInstPmtrInfo(self, iNo, pmtrNo):
        """for specified inst, pmtrNo, return pmtr info
        parameter numbers start at 0

        >>> a = CsoundNative()
        >>> a.getInstPmtrInfo(6, 3)
        'low-pass filter end cutoff frequency in Hz'
        """
        instrObj = self._getInstObj(iNo)
        # numbers are shifted by pmtrCountDefault
        # this orchestra uses 'pmtr' instead of 'auxQ'
        key = 'pmtr%s' % (pmtrNo + 1 + instrObj.pmtrCountDefault)
        if instrObj.pmtrInfo != {}:
            return instrObj.pmtrInfo[key]
        else:
            return 'no information available'
        
    #-----------------------------------------------------------------------||--
    # mappings of psReal, amp, pan; only applied of mix mode is on
    # mapings done before limits
    
    # dp amp values in csound
    # 60 dB = 1000
    # 66 dB = 1995.262
    # 72 dB = 3891.07
    # 78 dB = 7943.279
    # 84 dB = 15848.926
    # 90 dB = 31622.764 (abs max around 32767)

    def _postMapPs(self, iNo, val):
        """
        >>> a = CsoundNative()
        >>> a._postMapPs(6, 3)
        8.0...
        """
        return pitchTools.psToPch(val)
        
    def _postMapAmp(self, iNo, val, orcMapMode=1):
        """
        >>> a = CsoundNative()
        >>> a._postMapAmp(6, .5)
        45.0
        """
        # get max/min amp value form inst, as well as scale factor
        instrObj = self._getInstObj(iNo)
        ampMax = float(instrObj.postMapAmp[1])
        if orcMapMode: # optional map; allow values greater then 1
            val = val * ampMax # temp: assume max amp of 90
        # always limit
        if val < 0: val = 0 # we can assume tt amps are never negative
        return val
        
    def _postMapPan(self, iNo, val, orcMapMode=1):
        """
        >>> a = CsoundNative()
        >>> a._postMapPan(6, .5)
        0.5
        """
        if orcMapMode: # optional map
            pass # values are expected b/n 0 and 1
        # always limit: modulo 1    
        if val < 0 or val > 1: val = val % 1.0
        return val


        
        
#-----------------------------------------------------------------||||||||||||--
class InstrumentCsound(baseOrc.Instrument):
    # outputs expect and instrument to have a single final signal, calld "aMixSig
    # this bit of codes gets appended to end of inst def
    def __init__(self):
        baseOrc.Instrument.__init__(self)
        self.author = 'athenaCL native' # attribution
        self.scoSample = ''
        self.pmtrCountDefault = 6 # 6 built in values
        self.pmtrFields = self.pmtrCountDefault
        # postMap values for scaling
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.postMapPan = (0,1, 'linear')  # all pan values assume 0-1 maping
        
        self.monoOutput = """
    ; mono panning around 90 degrees
    out              aMixSig
    endin
"""
        self.stereoOutput = """
    ; stereo panning around 90 degrees
    iCirclePan       = 90.0 * iPan            ; scale 90 with values from 0 to 1
    kdegree          line         iCirclePan, p3, iCirclePan
    kdistance        line         1, p3, 1    ; used to distance reverb, need a constant 1
    aSig1, aSig2     locsig   aMixSig, kdegree, kdistance, 0.0
    outs                 aSig1, aSig2
    endin
"""
        self.quadOutput = """
    ; quad panning around 360 degrees
    iCirclePan                       = 360.0 * iPan ; scale 90 b/n 0 to 1
    kdegree                          line         iCirclePan, p3, iCirclePan
    kdistance                        line         1, p3, 1    ; constant
    aSig1, aSig2, aSig3, aSig4   locsig   aMixSig, kdegree, kdistance, 0.0
    outq                                 aSig1, aSig2, aSig3, aSig4
    endin
"""

    def getInstrHeader(self):
        return '\n;--i%i--%s' % (self.instNo, self.name)

    def buildInstrDef(self, noChannels):
        """returns a string of all the code needed for this instrument"""
        orcString = self.getInstrHeader()
        orcString = orcString + self.orcCode
        self.noChannels = noChannels
        if self.noChannels  == 1:
            orcString = orcString + self.monoOutput
        elif self.noChannels == 2:
            orcString = orcString + self.stereoOutput
        elif self.noChannels == 4:
            orcString = orcString + self.quadOutput
        return orcString


# these classes inherit all functions from InstrumentCsound


#-----------------------------------------------------------------||||||||||||--
class Inst3(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 3
        self.name = 'sineDrone'
        self.info = 'A simple sine wave drone.'
        self.auxNo = 0
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrDefault = {} 
        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    
    ;generate aplitude envelope
    ;                 amp     attack             dur      release
    k1    linen  iAmp,  (iDur * .18), iDur,  (iDur*.19)
    
    ;generate vibrato envelope                               
    irel    = 1.00                       ; set vibrato release time
    idel1 = iDur-(.25 * iDur)        ; calculate initial delay (pcent of dur)
    isus    = iDur - (idel1 - irel)  ; calculate remaining duration                             
    idep    = 2                   ; vibrato depth (1-9 are good)
    irat    = 1                   ; vibrato rate    (1-9 are good)
    ;                           
    ;linseg does delay, osicl does vibrato, k4 uses pulse wave                
    k3 linseg  0, idel1, idep, isus, idep, irel, 0  
    k2 oscil      k3, irat, 1
    k4 oscil      k3, (irat * .666), 6
    
    ;generate oscilator using k1, add vibrato w/k2, k4
    ;                amp          freq                      waveshape
    a1    oscil  k1,          (iFreq + k2),                 1        
    a2    oscil (k1 * .8), ((iFreq * .5) + (k4 * .5)), 1
    
    aMixSig          = (a1 + a2)
""" % str(self.instNo)

        self.scoSample = """
;p1 p2       p3   p4     p5  p6
;inst start  dur      amp    PCH    pan
i3      68.00 00.500 95 5.08    .5
i3      68.66 00.500 75 6.11    .5
"""
#-----------------------------------------------------------------||||||||||||--
class Inst4(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 4
        self.name = 'sineUnitEnvelope'
        self.info = 'A sine with a proportional linear envelope.'
        self.auxNo = 2
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          } 
        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    
    iSusPcent        = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
        
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right  
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aSig            oscil         kAmp, iFreq, 1         
    aMixSig     = aSig
    
""" % str(self.instNo)

        self.scoSample = """
;p1 p2       p3   p4     p5  p6
;inst start  dur      amp    PCH    pan
i3      68.00 00.500 95 5.08    .5
i3      68.66 00.500 75 6.11    .5
"""

#-----------------------------------------------------------------||||||||||||--
class Inst5(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 5
        self.name = 'sawDrone'
        self.info = 'A simple saw wave drone.'
        self.auxNo = 0
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrDefault = {} 
        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    
    ;generate aplitude envelope
    ;             amp       attack       dur     release
    k1 linen      iAmp, (iDur * .18), iDur, (iDur *.19)
    
    ;generate vibrato envelope                               
    irel    = 1.00                       ; set vibrato release time
    idel1 = iDur - (.25 * iDur)  ; calculate initial delay (pcent of dur)
    isus    = iDur - (idel1 - irel)  ; calculate remaining duration                             
    idep    = 2                          ; vibrato depth (1-9 are good)
    irat    = 1                          ; vibrato rate  (1-9 are good)
    ;                           
    ;linseg does delay, osicl does vibrato, k4 uses pulse wave                
    k3 linseg  0, idel1, idep, isus, idep, irel, 0  
    k2 oscil      k3, irat,          1
    k4 oscil      k3, (irat*.666), 6
    
    ;generate oscilator using k1, add vibrato w/k2, k4
    ;             amp        freq                           waveshape
    a1 oscil      k1,        (iFreq + k2),                   4        
    a2 oscil     (k1*.8), ((iFreq * .5) + (k4 *.5)), 1

    aMixSig          = (a1+a2)
""" % str(self.instNo)

        self.scoSample = """
;p1  p2  p3   p4      p5         p6
inst    start dur    amp     PCH        pan
i5      12.00 1.000  95  7.09     .5
i5      12.10 1.000  84  8.09     .5
"""
#-----------------------------------------------------------------||||||||||||--
class Inst6(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 6
        self.name = 'sawUnitEnvelope'
        self.info = 'A square wave with a proportional linear envelope and a variable low-pass filter.'
        self.auxNo = 5
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 10000),
          'pmtr10'  : ('c', 400),
          'pmtr11'  : ('c', 1),
          } 
        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    
    iSusPcent        = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    kq = p11
        
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right  
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    kFreq           linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            oscil        kAmp, iFreq, 4 ; ftable for square wave         
    aSig            lowpass2     aSig, kFreq, kq 
    aMixSig     = aSig
    
""" % str(self.instNo)

        self.scoSample = """
;p1 p2       p3   p4     p5  p6
;inst start  dur      amp    PCH    pan
i3      68.00 00.500 95 5.08    .5
i3      68.66 00.500 75 6.11    .5
"""

#-----------------------------------------------------------------||||||||||||--
class Inst11(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 11
        self.name = 'noiseWhite'
        self.info = 'A simple noise instrument.'
        self.auxNo = 0
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrDefault = {} 
        self.orcCode = """
instr %s
    iDur     = p3
    iAmp     = ampdb(p4)
    iwhite = cpspch(p5)
    iPan     = p6
    a1      random  -1, 1
    k1      linen     iAmp, .1, iDur, .1
    aMixSig = (k1 * a1)
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst12(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 12
        self.name = 'noisePitched'
        self.info = 'A noise instrument with a filter.'
        self.auxNo = 2
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'filter center frequency',
          'pmtr8'   : 'filter bandwidth',
            }
        self.pmtrDefault = {
          'pmtr7'   : ('cyclicGen', 'linearUpDown', 400, 800, 20), 
          'pmtr8'   : ('cyclicGen', 'linearUpDown', 1, 5, .2),
          }
        # this instrument is strange...
        self.orcCode = """
instr %s
    ;duration  = p3
    iAmp     = ampdb(p4)
    iFreq    = cpspch(p5)
    iPan     = p6
    ;filter cf  = p7
    ;filter bw  = p8
    
    k1    linen  1,  (p3*.9), p3, (p3*.1)
    
    ;create noise
    ;                amp      freq tt new values are produced
    a1    randi  p4,      p5,                   
    
    ;create band pass filter
    ;                signal, filter cf, filter bw             
    a2    reson  a1, p7, p8

    aMixSig = (k1 * a2)
""" % str(self.instNo)

        self.scoSample = """
;ins     strt    dur     amp    fq      pan  fltr     fltr  
; 56                     0-1                     cf   bw      
i56 00.0     2.0     .9  10000 .2       440   2  
"""

#-----------------------------------------------------------------||||||||||||--
class Inst13(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 13
        self.name = 'noiseUnitEnvelope'
        self.info = 'A noise generator with a proportional linear envelope and a variable low-pass filter'
        self.auxNo = 5
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent        = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iCutoffStart = p9
    iCutoffEnd = p10
    kq = p11
    
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right  
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kFreq           linseg   iCutoffStart, iDur, iCutoffEnd

    ;aSig            noise  1000, 0; or rand 22050
    aSig             random -1, 1
    a1               lowpass2  aSig, kFreq, kq 
    
    aMixSig   = a1 * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst14(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 14
        self.name = 'noiseTambourine'
        self.info = 'A tambourine-like instrument.'
        self.auxNo = 0
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrDefault = {
          'rhythmQ' : ('loop', ((16,1,1), (16,1,1), (16,5,1))) ,
            }
        self.orcCode = """
instr %s
    ;duration  = p3
    iAmp     = ampdb(p4)
    iFreq    = cpspch(p5)
    iPan     = p6

ifrq1     =  7500
iAmp1     =  0.3
ifrq2     =  10500
iAmp2     =  1
ifrq3     =  14000
iAmp3     =  0.3
ifrq4     =  18000
iAmp4     =  1

a1        rnd31 iAmp1, 0, 0
a2        rnd31 iAmp2, 0, 0
a3        rnd31 iAmp3, 0, 0
a4        rnd31 iAmp4, 0, 0

a1        butterbp a1, ifrq1, 1000
a1        butterbp a1, ifrq1, 400
a2        butterbp a2, ifrq2, 1000
a2        butterbp a2, ifrq2, 400
a3        butterbp a3, ifrq3, 1000
a3        butterbp a3, ifrq3, 400
a4        butterbp a4, ifrq4, 1000
a4        butterbp a4, ifrq4, 400

aenv      expon 1, 0.1, 0.1
          aMixSig = (a1 + a2 + a3 + a4) * aenv * iAmp
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst15(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 15
        self.name = 'noiseUnitEnvelopeBandpass'
        self.info = 'A noise generator with a proportional linear envelope and a variable band pass filter.'
        self.auxNo = 6
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'  : 'band pass filter start center frequency in Hz',
          'pmtr10'  : 'band pass filter end center frequency in Hz',
          'pmtr11'  : 'band pass filter start badnwidth in Hz',
          'pmtr12'  : 'band pass filter end badnwidth in Hz',
          
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 800),
          'pmtr10'  : ('c', 2000),
          'pmtr11'  : ('c', 50),
          'pmtr12'  : ('c', 100),

          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent        = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iBandStart = p9
    iBandEnd = p10
    iBandWidthStart = p11
    iBandWidthEnd = p12

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right  
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kband           linseg   iBandStart, iDur, iBandEnd
    kbandWidth  linseg   iBandWidthStart, iDur, iBandWidthEnd

    ;aSig            noise  1000, 0; or rand 22050
    aSig             random -1, 1
    aSig             butterbp  aSig, kband, kbandWidth    
    aMixSig   = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst16(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 16
        self.name = 'noiseSahNoiseUnitEnvelope'
        self.info = 'A noise source with a third order sample and hold filter, a variable high-pass filter, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 12
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'high-pass filter start cutoff frequency in Hz',
          'pmtr13'  : 'high-pass filter end cutoff frequency in Hz',          
          'pmtr14'  : 'first order rate low in Hz',
          'pmtr15'  : 'first order rate high in Hz',
          'pmtr16'  : 'second order rate low in Hz',
          'pmtr17'  : 'second order rate high in Hz',
          'pmtr18'  : 'third order rate in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 20),
          'pmtr13'  : ('c', 30),
          'pmtr14'  : ('c', 1.25),
          'pmtr15'  : ('c', 10),
          'pmtr16'  : ('c', .75),
          'pmtr17'  : ('c', .85),
          'pmtr18'  : ('c', .5),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    
    iHpfStart = p12
    iHpfEnd = p13

    iFirstLow  = p14
    iFirstHigh = p15
    iSecondLow = p16
    iSecondHigh = p17
    iThird = p18

    ; select a table read from for phasing the gate
    iTable = 15

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kfreqLpf        linseg   iCutoffStart, iDur, iCutoffEnd
    kfreqHpf        linseg   iHpfStart, iDur, iHpfEnd

    ; sample signal and noise drivers
    aSigSrc          random   -1, 1
    aNoiseFirst      random   iFirstLow, iFirstHigh
    aNoiseSecond     random   iSecondLow, iSecondHigh

    aGateC       oscil   1, iThird, iTable  ; table is a phasor from - 1 to 1
    aRateB       samphold aNoiseSecond, aGateC
    
    aGateB       oscil   1, aRateB, iTable
    aRateA       samphold aNoiseFirst, aGateB
    
    ; samplehold holds value when gateValue is zero
    aGateA      oscil        1, aRateA, iTable
    aSig            samphold     aSigSrc, aGateA

    ; filters
    aSig            butterhp     aSig, kfreqHpf 
    aSig            lowpass2     aSig, kfreqLpf, iLpfQ 
    
    aMixSig   = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst17(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 17
        self.name = 'noiseSahNoiseUnitEnvelopeDistort'
        self.info = 'A noise source with a third order sample and hold filter, a variable high-pass filter, a proportional linear envelope, a resonant low-pass filter, and a variable low-pass filter.'
        self.auxNo = 18
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          
          'pmtr12'  : 'high-pass filter start cutoff frequency in Hz',
          'pmtr13'  : 'high-pass filter end cutoff frequency in Hz',          
          'pmtr14'  : 'first order rate low in Hz',
          'pmtr15'  : 'first order rate high in Hz',
          'pmtr16'  : 'second order rate low in Hz',
          'pmtr17'  : 'second order rate high in Hz',
          'pmtr18'  : 'third order rate in Hz',
          
          'pmtr19'  : 'resonant filter start cutoff frequency in Hz',
          'pmtr20'  : 'resonant filter end cutoff frequency in Hz',
          'pmtr21'  : 'resonant filter start resonance (0-2)',
          'pmtr22'  : 'resonant filter end resonance (0-2)',
          'pmtr23'  : 'resonant filter start distortion (0-10)',
          'pmtr24'  : 'resonant filter end distortion (0-10)',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 20),
          'pmtr13'  : ('c', 30),
          'pmtr14'  : ('c', 1.25),
          'pmtr15'  : ('c', 40),
          'pmtr16'  : ('c', .75),
          'pmtr17'  : ('c', .85),
          'pmtr18'  : ('c', .5),
          
          'pmtr19'  : ('c', 1000),
          'pmtr20'  : ('c', 6000),
          'pmtr21'  : ('c', .8),
          'pmtr22'  : ('c', .2),
          'pmtr23'  : ('c', 100),
          'pmtr24'  : ('c', 0),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    
    iHpfStart = p12
    iHpfEnd = p13

    iFirstLow  = p14
    iFirstHigh = p15
    iSecondLow = p16
    iSecondHigh = p17
    iThird = p18

    iResonCutoffStart = p19
    iResonCutoffEnd = p20
    iResonStart = p21
    iResonEnd = p22
    iDistortionStart = p23
    iDistortionEnd = p24

    ; select a table read from for phasing the gate
    
    iTable = 15

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kfreqLpf        linseg   iCutoffStart, iDur, iCutoffEnd
    kfreqHpf        linseg   iHpfStart, iDur, iHpfEnd

    ; sample signal and noise drivers
    aSigSrc          random   -1, 1
    aNoiseFirst      random   iFirstLow, iFirstHigh
    aNoiseSecond     random   iSecondLow, iSecondHigh

    aGateC       oscili  1, iThird, iTable  ; table is a phasor from - 1 to 1
    aRateB       samphold aNoiseSecond, aGateC
    
    aGateB       oscili  1, aRateB, iTable
    aRateA       samphold aNoiseFirst, aGateB
    
    ; samplehold holds value when gateValue is zero
    aGateA       oscili   1, aRateA, iTable
    aSig             samphold  aSigSrc, aGateA

    ; filters
        
    aSig            butterhp     aSig, kfreqHpf 
    aSig            lowpass2     aSig, kfreqLpf, iLpfQ 
    
    ; filter through resonant distortion filter
    aSig            = aSig * .99999  ; reduce amp before lpf18 filter
    
    kResonCutoff     linseg   iResonCutoffStart, iDur, iResonCutoffEnd
    kReson           linseg   iResonStart, iDur, iResonEnd
    kDistortion      linseg   iDistortionStart, iDur, iDistortionEnd
    aSig                 lpf18      aSig, kResonCutoff, kReson, kDistortion
        
    aMixSig   = aSig * kAmp
    
""" % str(self.instNo)







#-----------------------------------------------------------------||||||||||||--
class Inst20(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 20
        self.name = 'fmBasic'
        self.info = 'A basic FM instrument.'
        self.auxNo = 2
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'fm factor',
          'pmtr8'   : 'modulation index',
          }
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((7,1,1),(7,5,1))) ,
          #'ampQ'    : ('cyclicGen', 'linearDown', 60.00, 76.00, 2.00) ,
          'pmtr7'   : ('cyclicGen', 'linearUpDown', 0.01, 8.00, 0.10),
          'pmtr8'   : ('cyclicGen', 'linearUpDown', 1.00, 6.00, 0.10),
          }
        self.author = '"basicfm.orc" from Csound Book examples' # attribution
        self.orcCode = """
instr %s
    iPan         =            p6
    iAmp         =            ampdb(p4)
    i1           =            1/p3                    ; ONE CYCLE PER DURATION OF NOTE
    i2           =            cpspch(p5)              ; CONVERTS PCHCLASS NOTATION TO Hz
    
    i3           =            i2 * p7            ; i3 IS THE MODULATING FREQUENCY
    i4           =            i3 * p8            ; i4 IS THE MAXIMUM FREQUENCY DEVIATION
    
    ampenv   oscil    iAmp,i1,201       ; AMPLITUDE ENVELOPE FOR THE CARRIER
    ampdev   oscil    i4,i1,201         ; ENVELOPE APPLIED TO FREQUENCY DEVIATION
    amod         oscili   ampdev,i3,203               ; MODULATING OSCILLATOR
    aSig         oscili   ampenv,i2+amod,203              ; CARRIER OSCILLATOR

    aMixSig  = aSig
""" % str(self.instNo)

        self.scoSample = """
;p1  p2  p3   p4      p5              p6        p7              p8
;inst    start dur   amp      PCH             pan 
;        start dur   amp      carrierFQ             fm_factor   mod_index
;i1     1    5       70   7.06        .5        1               4
;i1     7    5                7.06        .5        1.414    
"""

#-----------------------------------------------------------------||||||||||||--
class Inst21(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 21
        self.name = 'fmClarinet'
        self.info = 'A FM instrument tuned to sound clarinet-like.'
        self.auxNo = 1
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'imax value',
          }
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((7,3,1),(7,5,1)) ),
          #'ampQ'    : ('cyclicGen', 'linearDown', 60.00, 70.00, 1.00) ,
          'pmtr7'   : ('cyclicGen', 'linearUpDown', 1.50, 6.00, 0.20),
          }
        self.author = """
FMclarinet.orc from amsterdam catalog
ACCCI:    20_10_4.ORC
synthesis: FM(20),
              FM with dynamic spectral evolution (10)
              clarinet settings(3)
source:   Chowning (1973)
coded:    jpg 8/92
""" # attribution
        self.orcCode = """
instr %s
    iDur     = p3
    iAmp     = ampdb(p4)
    ifenv    = 211                        ; clarinet settings:
    ifdyn    = 212                        ; amp and index envelope see flow chart
    ifq1     = cpspch(p5)*3          ; N1:N2 is 3:2, imax=5
    if1  = 210                          ; duration ca. .5 sec
    ifq2     = cpspch(p5)*2
    if2  = 210
    imax     = p7
    imin     = 2
    iPan     = p6

    aenv    oscili  iAmp, 1/iDur, ifenv                   ; envelope

    adyn    oscili  ifq2*(imax-imin), 1/iDur, ifdyn   ; index
    adyn    =           (ifq2*imin)+adyn                          ; add minimum value
    amod    oscili  adyn, ifq2, if2                       ; modulator

    a1      oscili  aenv, ifq1+amod, if1                      ; carrier

    aMixSig          = a1
""" % str(self.instNo)

        self.scoSample = """
;p1  p2  p3   p4      p5        p6       p7 
;inst    start dur   amp      PCH       pan 
;                iDur iAmp   pch                 imax
i1      0       .5      75       8.00               4           ; scale by clarinet
i1      +       .       .        8.02               .
i1      .       .       .        8.04               .
"""

#-----------------------------------------------------------------||||||||||||--
class Inst22(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 22
        self.name = 'fmWoodDrum'
        self.info = 'A FM instrument tuned to sound wood-drum-like.'
        self.auxNo = 0
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrDefault = {
          'rhythmQ' : ('loop', ((8,3,1),(8,3,1),(8,3,1),(8,1,0),(4,1,1),
                                        (4,1,1),(8,1,1),(8,1,0))) ,
          #'ampQ'    : ('cyclicGen', 'linearDown', 80.00, 81.00, 1.00) ,
          }
        self.author = """
FMwoodDrum.orc from amsterdam catalog
ACCCI:    20_10_2.ORC
synthesis: FM(20),
              FM with dynamic spectral evolution (10)
              wood-drum settings(2)
source:   Chowning(1973)
coded:    jpg 8/92
""" # attribution
        self.orcCode = """
instr %s
    iDur     = p3
    iAmp     = ampdb(p4)
    ifenv    = 251                        ; wood drum settings:
    ifdyn    = 231                        ; amp and index envelopes see flow chart
    ifq1     = cpspch(p5)*16                ; N1:N2 is 80:55 = 16:11, imax=25
    if1  = 210                          ; duration = .2 sec
    ifq2     = cpspch(p5)*11
    if2  = 210                          ; same gen used by clar
    imax     = 25
    iPan     = p6
    
    aenv    oscili  iAmp, 1/iDur, ifenv               ; envelope
    adyn    oscili  ifq2*imax, 1/iDur, ifdyn          ; dynamic
    amod    oscili  adyn, ifq2, if2                   ; modulator
    a1      oscili  aenv, ifq1+amod, if1                  ; carrier

    aMixSig = a1
""" % str(self.instNo)

        self.scoSample = """
;p1  p2  p3   p4      p5        p6       p7 
;inst    start dur   amp      PCH       pan 
;                iDur    iAmp     pch
;i1  0       .2   76      3.00  .5   ; scale in wood drum...
;i1  +       .       .        3.02   .
"""

#-----------------------------------------------------------------||||||||||||--
class Inst23(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 23
        self.name = 'fmString'
        self.info = 'A FM instrument tuned to sound string-like.'
        self.auxNo = 5
        self.postMapAmp = (0,90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'irise, percentage of rise-time, around .2',
          'pmtr8'   : 'idec, percentage of dec time, around .2',
          'pmtr9'   : 'ivibdel, vibrato delay, around .35', 
          'pmtr10'  : 'ivibwth, vibrato width, around .01', 
          'pmtr11'  : 'ivibrte, vibrato rate, around 2.5', 
          }
        self.pmtrDefault = {
          'rhythmQ' : ('loop', ((8,3,1),(8,3,1),(8,3,1),(8,1,0),
                                        (4,1,1),(4,1,1),(8,1,1),(8,1,0))) ,
          #'ampQ'    : ('cyclicGen', 'linearDown', 80.00, 81.00, 1.00) ,
          'pmtr7'   : ('basketGen', 'randomChoice', (.15, .2, .25)),
          'pmtr8'   : ('basketGen', 'randomChoice', (.15, .2, .25)),
          'pmtr9'   : ('basketGen', 'randomChoice', (.3, .35, .25)), 
          'pmtr10'  : ('basketGen', 'randomChoice', (.01, .0025, .005, .0075)), 
          'pmtr11'  : ('basketGen', 'randomChoice', (2.5, 2.2, 3.1)), 
          }
        self.author = """
FMstring.orc from amsterdam catalog
ACCCI:    20_70_1.ORC
synthesis: FM(20),
              single-carrier, complex wave FM (70)
              string-like(1)
source:   Schottstaedt(1977)
coded:    Russell Pinkston, University of Texas at Austin 
""" # attribution
        self.orcCode = """
instr %s
    iDur      = p3
    iAmp      = ampdb(p4)
    ifqc      = cpspch(p5)        ;S = fc +- ifm1 +- kfm2 +- lfm3
    ifm1      = ifqc
    ifm2      = ifqc*3
    ifm3      = ifqc*4
    indx1     = 7.5/log(ifqc)       ;range from ca 2 to 1
    indx2     = 15/sqrt(ifqc)       ;range from ca 2.6 to .5
    indx3     = 1.25/sqrt(ifqc) ;range from ca .2 to .038

    iPan     = p6
    irise     = p7
    idec      = p8
    inoisdur= .1
    ivibdel = p9 ; was set at contstant 1
    ivibwth = p10
    ivibrte = p11

    kvib      init   0
              timout     0, ivibdel, transient   ; delay vibrato ivibdel sec
    kvbctl  linen    1, .5, iDur-ivibdel, .1  ; vibrato control envelope
    krnd      randi  .0075, 2                   ; random deviation vib width
    kvib      oscili     kvbctl*ivibwth+krnd, ivibrte*kvbctl, 1 ; generator
    
    transient:
              timout     inoisdur,p3,continue  ; execute for .2 secs only
    ktrans  linseg   1,inoisdur,0,1,0         ; transient envelope
    anoise  randi    ktrans*iAmp/4,.2*ifqc ; attack noise...
    attack  oscili   anoise,2000,1            ; ...centered around 2kHz
    
    iTable  = 210
    
    amod1     oscili     ifm1*(indx1+ktrans),ifm1, iTable 
    amod2     oscili     ifm2*(indx2+ktrans),ifm2, iTable
    amod3     oscili     ifm3*(indx3+ktrans),ifm3, iTable
    aSig      oscili     iAmp, (ifqc+amod1+amod2+amod3)*(1+kvib), iTable
    aSig      linen  aSig+attack, irise, iDur, idec
    aMixSig = aSig
""" % str(self.instNo)




#-----------------------------------------------------------------||||||||||||--
class Inst30(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 30
        self.name = 'samplerReverb'
        self.info = 'A simple sampler with reverb. A linear envelope is given in absolute time values.'
        self.auxNo = 6
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'time to read into the file',
          'pmtr8'   : 'absolute atack time',
          'pmtr9'   : 'absolute release time',
          'pmtr10'  : 'reverb time',
          'pmtr11'  : 'reverb gain',
          'pmtr12'  : 'file path to desired sound file',
          }
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((9,6,1),(9,2,1)) ), 
          'pmtr7'   : ('constant', 0),
          'pmtr8'   : ('cyclicGen', 'linearUp', .03, .10, .01),
          'pmtr9'   : ('constant', 0.1),
          'pmtr10'  : ('cyclicGen', 'linearUp', .5, 2.1, .2),
          'pmtr11'  : ('cyclicGen', 'linearUp', .00, .50, .05),
          'pmtr12'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq    = cpspch(p5)
    
    iPitch      = .5
    
    iPan            = p6     
    iSkiptime   = p7
    iAttack     = p8
    iRelease        = p9
    iRvbtime        = p10
    iRvbgain        = p11
    iSamplePath = p12    ; use full pathnames for samples
  
    ;this envelope uses absolute time values
    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    aSig            soundin  iSamplePath, iSkiptime

    arampsig      = kAmp * aSig
    aEffect      reverb aSig, iRvbtime
    arvbreturn = aEffect * iRvbgain

    aMixSig   =  arampsig + arvbreturn
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
class Inst31(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 31
        self.name = 'samplerRaw'
        self.info = 'A simple sampler of single audio files. Audio files are given with a complete file path. Amplitude values are used only to scale amplitude'
        self.auxNo = 1
        self.postMapAmp = (0, 9, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
                      'pmtr7'  : 'file path chooser',
                     } # holds discription, preset for each pmtr in a dictionary
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((9,6,1),(9,2,1)) ), 
          'pmtr7'   : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          }
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq    = cpspch(p5)
    iSkiptime = 0
    iPan         = p6

    ;use full pathnames for samples
    iSamplePath = p7    ; selects which sample
  
    ; envelope uses absolute time values
    kAmp            linen        iAmp, 0, iDur, 0
    aSig            soundin  iSamplePath, iSkiptime
    aMixSig  = kAmp * aSig
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst32(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 32
        self.name = 'samplerUnitEnvelope'
        self.info = 'A simple sampler with a proportional linear envelope and a variable low-pass filter.'
        self.auxNo = 7
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            soundin  iSamplePath, iSkiptime
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 
    
    aMixSig   = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst33(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 33
        self.name = 'samplerUnitEnvelopeBandpass'
        self.info = 'A simple sampler with a proportional linear envelope and a band-pass filter.'
        self.auxNo = 8
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'band pass filter start center frequency in Hz',
          'pmtr10'  : 'band pass filter end center frequency in Hz',
          'pmtr11'  : 'band pass filter start bandwidth in Hz',
          'pmtr12'  : 'band pass filter end bandwidth in Hz',
          'pmtr13'  : 'start time within audio file',
          'pmtr14'  : 'file path to desired sound file',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 2000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 100),
          'pmtr12'  : ('c', 200),
          'pmtr13'  : ('c', 0),
          'pmtr14'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    
    iBandStart = p9
    iBandEnd = p10
    iBandWidthStart = p11
    iBandWidthEnd = p12
    
    iSkiptime = p13
    iSamplePath = p14    ; sample as complete path
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kbandCf     linseg   iBandStart, iDur, iBandEnd
    kbandWidth  linseg   iBandWidthStart, iDur, iBandWidthEnd

    aSig            soundin  iSamplePath, iSkiptime
    aSig            butterbp     aSig, kbandCf, kbandWidth          
    aMixSig  = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst34(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 34
        self.name = 'samplerUnitEnvelopeDistort'
        self.info = 'A sampler with a proportional linear envelope, a distortion processor, and a low-pass filter.'
        self.auxNo = 11
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'distortion input gain; 1 gives a slight distortion',
          'pmtr10'  : 'distortion output gain',
          'pmtr11'  : 'postive wave shaping curve; 0 gives a flat clip',
          'pmtr12'  : 'negative wave shaping curve',             
          'pmtr13'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr14'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr15'  : 'low-pass filter resonance between 1 and 500',
          'pmtr16'  : 'start time within audio file',
          'pmtr17'  : 'file path to desired sound file',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 1),
          'pmtr10'  : ('c', 1),
          'pmtr11'  : ('c', 0),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('c', 4000),
          'pmtr14'  : ('c', 8000),
          'pmtr15'  : ('c', 1),
          'pmtr16'  : ('c', 0),
          'pmtr17'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iDistIn = p9
    iDistOut = p10
    iDistCurvePos = p11
    iDistCurveNeg = p12
    iLpfStart = p13
    iLpfEnd = p14
    iLpfQ = p15
    iSkiptime = p16
    iSamplePath = p17    ; sample as complete path
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kFreq           linseg   iLpfStart, iDur, iLpfEnd

    aSig            soundin  iSamplePath, iSkiptime
    aSig            distort1     aSig, iDistIn, iDistOut, iDistCurvePos, iDistCurveNeg
    a1              lowpass2     aSig, kFreq, iLpfQ 
    aMixSig  = a1 * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst35(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 35
        self.name = 'samplerUnitEnvelopeParametric'
        self.info = 'A simple sampler with a proportional linear envelope and a multi-function parametric filter.'
        self.auxNo = 11
        self.postMapAmp = (0, 5, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'parametric filter start center frequency in Hz',
          'pmtr10'  : 'parametric filter end center frequency in Hz',
          'pmtr11'  : 'parametric filter start Q',
          'pmtr12'  : 'parametric filter end Q',
          'pmtr13'  : 'parametric filter start amp scalar, where 1 is flat',
          'pmtr14'  : 'parametric filter end amp scalar, where 1 is flat',

          'pmtr15'  : 'parametric filter type, where 0 is peaking, 1 is low shelving, 2 is high shelving.',

          'pmtr16'  : 'start time within audio file',
          'pmtr17'  : 'file path to desired sound file',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 400),
          'pmtr10'  : ('c', 2000),
          'pmtr11'  : ('c', 6),
          'pmtr12'  : ('c', 6),

          'pmtr13'  : ('c', 3), # 2 is 6 db, .5 is -6 dB, 
          'pmtr14'  : ('c', 3),

          'pmtr15'  : ('c', 0),
          'pmtr16'  : ('c', 0),
          'pmtr17'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          }
        self.author = 'athenaCL native' # attribution
        # note that rbjeq does not work
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    
    iBandStart = p9
    iBandEnd = p10
    iQStart = p11
    iQEnd = p12
    iGainStart = p13
    iGainEnd = p14

    iFilterType = p15
    
    iSkiptime = p16
    iSamplePath = p17    ; sample as complete path
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kbandCf     linseg   iBandStart, iDur, iBandEnd
    kbandQ      linseg   iQStart, iDur, iQEnd
    kbandGain   linseg   iGainStart, iDur, iGainEnd

    aSig            soundin  iSamplePath, iSkiptime
    aSig            pareq        aSig, kbandCf, kbandGain, kbandQ, iFilterType    
    aMixSig  = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst36(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 36
        self.name = 'samplerSahNoiseUnitEnvelope'
        self.info = 'A simple sampler with third order sample and hold filter, a variable high-pass filter, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 14
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          'pmtr14'  : 'high-pass filter start cutoff frequency in Hz',
          'pmtr15'  : 'high-pass filter end cutoff frequency in Hz',          
          'pmtr16'  : 'first order rate low in Hz',
          'pmtr17'  : 'first order rate high in Hz',
          'pmtr18'  : 'second order rate low in Hz',
          'pmtr19'  : 'second order rate high in Hz',
          'pmtr20'  : 'third order rate in Hz',
          
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('metal01.aif', 'latch01.aif')),
          'pmtr14'  : ('c', 20),
          'pmtr15'  : ('c', 30),
          'pmtr16'  : ('c', 400),
          'pmtr17'  : ('c', 600),
          'pmtr18'  : ('c', 10),
          'pmtr19'  : ('c', 20),
          'pmtr20'  : ('c', .5),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path

    iHpfStart = p14
    iHpfEnd = p15

    iFirstLow = p16
    iFirstHigh = p17
    iSecondLow = p18
    iSecondHigh = p19
    iThird = p20

    ; select a table read from
    iTable = 15

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kfreqLpf        linseg   iCutoffStart, iDur, iCutoffEnd
    kfreqHpf        linseg   iHpfStart, iDur, iHpfEnd

    ; sample signal and noise drivers
    aSigSrc          soundin      iSamplePath, iSkiptime
    aNoiseFirst      random   iFirstLow, iFirstHigh
    aNoiseSecond     random   iSecondLow, iSecondHigh

    aGateC       oscil 1, iThird, iTable    ; table is a phasor from - 1 to 1
    aRateB       samphold aNoiseSecond, aGateC
    
    aGateB       oscil 1, aRateB, iTable
    aRateA       samphold aNoiseFirst, aGateB
    
    ; samplehold holds value when gateValue is zero
    aGateA      oscil 1, aRateA, iTable
    aSig            samphold     aSigSrc, aGateA

    ; filters
    aSig            butterhp     aSig, kfreqHpf 
    aSig            lowpass2     aSig, kfreqLpf, iLpfQ 
    
    aMixSig   = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
class Inst37(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 37
        self.name = 'samplerCrossUnitEnvelope'
        self.info = 'A cross synthesis sampler with a proportional linear envelope and a variable low-pass filter.'
        self.auxNo = 12
        self.postMapAmp = (0, 6, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file A',
          'pmtr13'  : 'file path to desired sound file A, stimulus sound',
          'pmtr14'  : 'start time within audio file B',
          'pmtr15'  : 'file path to desired sound file B, modulating sound',
          'pmtr16'  : 'size of fft, larger the size, better the fq response, worse the time response. 4096 is a good value',
          'pmtr17'  : 'cross synthesis bias start (between 0 and 1)',
          'pmtr18'  : 'cross synthesis bias end (between 0 and 1)',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('metal01.aif', 'metal02.aif')),
          'pmtr14'  : ('c', 0),
          'pmtr15'  : ('sampleSelect', ('drum01.aif', 'grains01.aif')),
          'pmtr16'  : ('c', 256), # 2048, 4096, 1024, 512, 256, 128
          'pmtr17'  : ('c', 1),
          'pmtr18'  : ('c', 1),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptimeA   = p12
    iSamplePathA = p13  ; sample as complete path
    iSkiptimeB   = p14
    iSamplePathB = p15  ; sample as complete path

    ; cross synth parameters
    isize = p16
    ibiasStart = p17
    ibiasEnd = p18
    
    ; fixed cross synth parameters
    ioverlap = 2
    iwin = 14        ; function table number, 14 is a hamming
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kFreq           linseg   iCutoffStart, iDur, iCutoffEnd
    kbias           linseg   ibiasStart, iDur, ibiasEnd

    aSigA           soundin  iSamplePathA, iSkiptimeA
    aSigB           soundin  iSamplePathB, iSkiptimeB
    
    aSig            cross2 aSigA, aSigB, isize, ioverlap, iwin, kbias   
    a1              lowpass2     aSig, kFreq, iLpfQ 
    
    aMixSig   = a1 * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst40(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 40
        self.name = 'vocodeNoiseSingle'
        self.info = 'A one channel vocoder with variable mapping.'
        self.auxNo = 8
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr12'  : 'analysis band-pass bw, from 10 to 500',
          'pmtr13'  : 'analysis 1 band-pass center frequency in Hz',
          'pmtr14'  : 'generator 1 band-pass center frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 40),
          'pmtr12'  : ('c', 50), # band width, 20 is well pitched
          'pmtr13'  : ('c', 400),
          'pmtr14'  : ('c', 1000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    
    iAnalysisCutoff = p11
    iAnalysisQ = p12
  
    iAnalysisCf01 = p13
    iGeneratorCf01 = p14
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            soundin  iSamplePath, iSkiptime
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01

    ; mix all channels
    aSig            = aGen01 

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst41(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 41
        self.name = 'vocodeNoiseSingleGlissando'
        self.info = 'A one channel vocoder with variable mapping between two frequencies'
        self.auxNo = 9
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr12'  : 'analysis band-pass bw, from 10 to 500',
          'pmtr13'  : 'analysis 1 band-pass center frequency in Hz',
          'pmtr14'  : 'generator 1 start band-pass center frequency in Hz',
          'pmtr15'  : 'generator 1 end band-pass center frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 40),
          'pmtr12'  : ('c', 50), # band width, 20 is well pitched
          'pmtr13'  : ('c', 400),
          'pmtr14'  : ('c', 1000),
          'pmtr15'  : ('c', 2000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    
    iAnalysisCutoff = p11
    iAnalysisQ = p12
  
    iAnalysisCf01 = p13
    iGeneratorCfStart01 = p14
    iGeneratorCfEnd01 = p15
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            soundin  iSamplePath, iSkiptime
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    ; create generator filter cf line segment
    kFreqGen01  linseg   iGeneratorCfStart01, iDur, iGeneratorCfEnd01

    ; filter noise at fq, scale by analysis 
    aGen01      butterbp     aNoise, kFreqGen01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01

    ; mix all channels
    aSig            = aGen01 

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
class Inst42(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 42
        self.name = 'vocodeNoiseQuadRemap'
        self.info = 'A four channel vocoder with variable mapping.'
        self.auxNo = 17
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',
          
          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',
          
          'pmtr14'  : 'analysis 1 band-pass center frequency in Hz',
          'pmtr15'  : 'analysis 2 band-pass center frequency in Hz',
          'pmtr16'  : 'analysis 3 band-pass center frequency in Hz',
          'pmtr17'  : 'analysis 4 band-pass center frequency in Hz',
          'pmtr18'  : 'generator 1 band-pass center frequency in Hz',
          'pmtr19'  : 'generator 2 band-pass center frequency in Hz',
          'pmtr20'  : 'generator 3 band-pass center frequency in Hz',
          'pmtr21'  : 'generator 4 band-pass center frequency in Hz',
          
          'pmtr22'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr23'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 50), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 400),
          'pmtr15'  : ('c', 800),
          'pmtr16'  : ('c', 1000),
          'pmtr17'  : ('c', 1200),
          'pmtr18'  : ('c', 400),
          'pmtr19'  : ('c', 800),
          'pmtr20'  : ('c', 200),
          'pmtr21'  : ('c', 1000),

          'pmtr22'  : ('c', 50),
          'pmtr23'  : ('c', 1000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11 ; play back speed
    
    iAnalysisCutoff = p12
    iAnalysisQ = p13
  
    iAnalysisCf01 = p14
    iAnalysisCf02 = p15
    iAnalysisCf03 = p16
    iAnalysisCf04 = p17

    iGeneratorCf01 = p18
    iGeneratorCf02 = p19
    iGeneratorCf03 = p20
    iGeneratorCf04 = p21
  
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p22, iDur, p23

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        = aAmpCh02 * 2                               ; increase signal power
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        = aAmpCh03 * 2                               ; increase signal power
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        = aAmpCh04 * 2                               ; increase signal power
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01
    aGen02      butterbp     aNoise, iGeneratorCf02, iAnalysisQ 
    aGen02      = aGen02 * aAmpCh02
    aGen03      butterbp     aNoise, iGeneratorCf03, iAnalysisQ 
    aGen03      = aGen03 * aAmpCh03
    aGen04      butterbp     aNoise, iGeneratorCf04, iAnalysisQ 
    aGen04      = aGen04 * aAmpCh04

    ; mix all channels
    aSig            = aGen01 + aGen02 + aGen03 + aGen04

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst43(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 43
        self.name = 'vocodeNoiseQuadScale'
        self.info = 'A four channel vocoder with scaled mapping.'
        self.auxNo = 13
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',
          
          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',          
          
          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 50), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 800),
          'pmtr15'  : ('c', 1.3333333333),

          'pmtr16'  : ('c', 400),
          'pmtr17'  : ('c', 1.6666666666),
          
          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 4000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11
    
    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)

    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        = aAmpCh02 * 2                               ; increase signal power
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        = aAmpCh03 * 2                               ; increase signal power
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        = aAmpCh04 * 2                               ; increase signal power
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01
    aGen02      butterbp     aNoise, iGeneratorCf02, iAnalysisQ 
    aGen02      = aGen02 * aAmpCh02
    aGen03      butterbp     aNoise, iGeneratorCf03, iAnalysisQ 
    aGen03      = aGen03 * aAmpCh03
    aGen04      butterbp     aNoise, iGeneratorCf04, iAnalysisQ 
    aGen04      = aGen04 * aAmpCh04

    ; mix all channels
    aSig            = aGen01 + aGen02 + aGen03 + aGen04

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst44(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 44
        self.name = 'vocodeNoiseQuadScaleRemap'
        self.info = 'A four channel vocoder with variable remapping.'
        self.auxNo = 21
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',
          
          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',         

          'pmtr18'  : 'generator 1 channel frequency source (1-4)',
          'pmtr19'  : 'generator 2 channel frequency source (1-4)',           
          'pmtr20'  : 'generator 3 channel frequency source (1-4)',
          'pmtr21'  : 'generator 4 channel frequency source (1-4)',           

          'pmtr22'  : 'generator 1 post scale (0-1)',
          'pmtr23'  : 'generator 2 post scale (0-1)',           
          'pmtr24'  : 'generator 3 post scale (0-1)',
          'pmtr25'  : 'generator 4 post scale (0-1)',    
          
          'pmtr26'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr27'  : 'low-pass filter end cutoff frequency in Hz',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 40), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 800),
          'pmtr15'  : ('c', 1.333333333333),

          'pmtr16'  : ('c', 400),
          'pmtr17'  : ('c', 1.666666666666),
          
          'pmtr18'  : ('c', 1),
          'pmtr19'  : ('c', 2),
          'pmtr20'  : ('c', 3),
          'pmtr21'  : ('c', 4),
          
          'pmtr22'  : ('c', 1),
          'pmtr23'  : ('c', 1),
          'pmtr24'  : ('c', 1),
          'pmtr25'  : ('c', 1),
          
          'pmtr26'  : ('c', 100),
          'pmtr27'  : ('c', 2000),
          }
          
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    
    ; integer values tt determine which channel goes where
    iGeneratorSrcCh01 = p18 - 1  ; values in src channel become exponents
    iGeneratorSrcCh02 = p19 - 1
    iGeneratorSrcCh03 = p20 - 1
    iGeneratorSrcCh04 = p21 - 1

    ; can re-scale generator mapping, produce normal fqs prior to remap
    ; amp will stay the same, based on order number; changes fqs applied
    ; with number
    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh01)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh02)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh03)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh04)

    ; making these k-rate for envelope scaling
    kGeneratorPost01 = p22
    kGeneratorPost02 = p23
    kGeneratorPost03 = p24
    kGeneratorPost04 = p25
     
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p26, iDur, p27

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        = aAmpCh02 * 2                               ; increase signal power
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        = aAmpCh03 * 2                               ; increase signal power
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        = aAmpCh04 * 2                               ; increase signal power
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01 * kGeneratorPost01
    aGen02      butterbp     aNoise, iGeneratorCf02, iAnalysisQ 
    aGen02      = aGen02 * aAmpCh02 * kGeneratorPost02
    aGen03      butterbp     aNoise, iGeneratorCf03, iAnalysisQ 
    aGen03      = aGen03 * aAmpCh03 * kGeneratorPost03
    aGen04      butterbp     aNoise, iGeneratorCf04, iAnalysisQ 
    aGen04      = aGen04 * aAmpCh04 * kGeneratorPost04

    ; mix all channels
    aSig            = aGen01 + aGen02 + aGen03 + aGen04
    
    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)






#-----------------------------------------------------------------||||||||||||--
# 8 ch

# this instrument had an incorrect aux value of 12

class Inst45(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self) 
        self.instNo = 45
        self.name = 'vocodeNoiseOctScale'
        self.info = 'An eight channel vocoder with scaled mapping.'
        self.auxNo = 13
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',
          
          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar', 
          
          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 50), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 500),
          'pmtr15'  : ('c', 1.333333333333),

          'pmtr16'  : ('c', 500),
          'pmtr17'  : ('c', 1.333333333333),
          
          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 8000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)
  
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        = aAmpCh02 * 2                               ; increase signal power
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        = aAmpCh03 * 2                               ; increase signal power
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        = aAmpCh04 * 2                               ; increase signal power
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        = aAmpCh05 * 2                               ; increase signal power
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        = aAmpCh06 * 2                               ; increase signal power
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        = aAmpCh07 * 2                               ; increase signal power
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        = aAmpCh08 * 2                               ; increase signal power
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf

    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01
    aGen02      butterbp     aNoise, iGeneratorCf02, iAnalysisQ 
    aGen02      = aGen02 * aAmpCh02
    aGen03      butterbp     aNoise, iGeneratorCf03, iAnalysisQ 
    aGen03      = aGen03 * aAmpCh03
    aGen04      butterbp     aNoise, iGeneratorCf04, iAnalysisQ 
    aGen04      = aGen04 * aAmpCh04

    aGen05      butterbp     aNoise, iGeneratorCf05, iAnalysisQ 
    aGen05      = aGen05 * aAmpCh05
    aGen06      butterbp     aNoise, iGeneratorCf06, iAnalysisQ 
    aGen06      = aGen06 * aAmpCh06
    aGen07      butterbp     aNoise, iGeneratorCf07, iAnalysisQ 
    aGen07      = aGen07 * aAmpCh07
    aGen08      butterbp     aNoise, iGeneratorCf08, iAnalysisQ 
    aGen08      = aGen08 * aAmpCh08

    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
# 8 ch
class Inst46(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 46
        self.name = 'vocodeNoiseOctScaleRemap'
        self.info = 'An eight channel vocoder with variable remapping.'
        self.auxNo = 29
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',         

          'pmtr18'  : 'generator 1 channel frequency source (1-8)',
          'pmtr19'  : 'generator 2 channel frequency source (1-8)',           
          'pmtr20'  : 'generator 3 channel frequency source (1-8)',
          'pmtr21'  : 'generator 4 channel frequency source (1-8)',           
          'pmtr22'  : 'generator 5 channel frequency source (1-8)',
          'pmtr23'  : 'generator 6 channel frequency source (1-8)',           
          'pmtr24'  : 'generator 7 channel frequency source (1-8)',
          'pmtr25'  : 'generator 8 channel frequency source (1-8)',           

          'pmtr26'  : 'generator 1 post scale (0-1)',
          'pmtr27'  : 'generator 2 post scale (0-1)',           
          'pmtr28'  : 'generator 3 post scale (0-1)',
          'pmtr29'  : 'generator 4 post scale (0-1)',           
          'pmtr30'  : 'generator 5 post scale (0-1)',
          'pmtr31'  : 'generator 6 post scale (0-1)',           
          'pmtr32'  : 'generator 7 post scale (0-1)',
          'pmtr33'  : 'generator 8 post scale (0-1)',           

          'pmtr34'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr35'  : 'low-pass filter end cutoff frequency in Hz',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 40), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 400),
          'pmtr15'  : ('c', 1.33333333333),

          'pmtr16'  : ('c', 100),
          'pmtr17'  : ('c', 1.6666666666),
          
          'pmtr18'  : ('c', 1),
          'pmtr19'  : ('c', 2),
          'pmtr20'  : ('c', 3),
          'pmtr21'  : ('c', 4),
          'pmtr22'  : ('c', 5),
          'pmtr23'  : ('c', 6),
          'pmtr24'  : ('c', 7),
          'pmtr25'  : ('c', 8),
          
          'pmtr26'  : ('c', 1),
          'pmtr27'  : ('c', 1),
          'pmtr28'  : ('c', 1),
          'pmtr29'  : ('c', 1),
          'pmtr30'  : ('c', 1),
          'pmtr31'  : ('c', 1),
          'pmtr32'  : ('c', 1),
          'pmtr33'  : ('c', 1),
          
          'pmtr34'  : ('c', 100),
          'pmtr35'  : ('c', 4000),
          }
          
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)
    
    ; integer values tt determine which channel goes where
    iGeneratorSrcCh01 = p18 - 1  ; values in src channel become exponents
    iGeneratorSrcCh02 = p19 - 1
    iGeneratorSrcCh03 = p20 - 1
    iGeneratorSrcCh04 = p21 - 1
    iGeneratorSrcCh05 = p22 - 1 
    iGeneratorSrcCh06 = p23 - 1
    iGeneratorSrcCh07 = p24 - 1
    iGeneratorSrcCh08 = p25 - 1

    ; can re-scale generator mapping, produce normal fqs prior to remap
    ; amp will stay the same, based on order number; changes fqs applied
    ; with number
    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh01)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh02)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh03)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh04)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh05)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh06)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh07)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh08)

    ; making these k-rate for envelope scaling
    kGeneratorPost01 = p26
    kGeneratorPost02 = p27
    kGeneratorPost03 = p28
    kGeneratorPost04 = p29
    kGeneratorPost05 = p30
    kGeneratorPost06 = p31
    kGeneratorPost07 = p32
    kGeneratorPost08 = p33
  
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p34, iDur, p35
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0

    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        = aAmpCh02 * 2                               ; increase signal power
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        = aAmpCh03 * 2                               ; increase signal power
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        = aAmpCh04 * 2                               ; increase signal power
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        = aAmpCh05 * 2                               ; increase signal power
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        = aAmpCh06 * 2                               ; increase signal power
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        = aAmpCh07 * 2                               ; increase signal power
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        = aAmpCh08 * 2                               ; increase signal power
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf

    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01 * kGeneratorPost01
    aGen02      butterbp     aNoise, iGeneratorCf02, iAnalysisQ 
    aGen02      = aGen02 * aAmpCh02 * kGeneratorPost02
    aGen03      butterbp     aNoise, iGeneratorCf03, iAnalysisQ 
    aGen03      = aGen03 * aAmpCh03 * kGeneratorPost03
    aGen04      butterbp     aNoise, iGeneratorCf04, iAnalysisQ 
    aGen04      = aGen04 * aAmpCh04 * kGeneratorPost04

    aGen05      butterbp     aNoise, iGeneratorCf05, iAnalysisQ 
    aGen05      = aGen05 * aAmpCh05 * kGeneratorPost05
    aGen06      butterbp     aNoise, iGeneratorCf06, iAnalysisQ 
    aGen06      = aGen06 * aAmpCh06 * kGeneratorPost06
    aGen07      butterbp     aNoise, iGeneratorCf07, iAnalysisQ 
    aGen07      = aGen07 * aAmpCh07 * kGeneratorPost07
    aGen08      butterbp     aNoise, iGeneratorCf08, iAnalysisQ 
    aGen08      = aGen08 * aAmpCh08 * kGeneratorPost08

    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
# 16 ch

class Inst47(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 47
        self.name = 'vocodeNoiseBiOctScale'
        self.info = 'An sixteen channel vocoder with scaled mapping.'
        self.auxNo = 13
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',
          
          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 5), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 120),
          'pmtr15'  : ('c', 1.33333333),

          'pmtr16'  : ('c', 120),
          'pmtr17'  : ('c', 1.33333333),
          
          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 4000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iAnalysisCf09 = p14 * (iAnalysisFqScalar ^ 8)
    iAnalysisCf10 = p14 * (iAnalysisFqScalar ^ 9)
    iAnalysisCf11 = p14 * (iAnalysisFqScalar ^ 10)
    iAnalysisCf12 = p14 * (iAnalysisFqScalar ^ 11)
    iAnalysisCf13 = p14 * (iAnalysisFqScalar ^ 12)
    iAnalysisCf14 = p14 * (iAnalysisFqScalar ^ 13)
    iAnalysisCf15 = p14 * (iAnalysisFqScalar ^ 14)
    iAnalysisCf16 = p14 * (iAnalysisFqScalar ^ 15)

    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)
    
    iGeneratorCf09 = p16 * (iGeneratorFqScalar ^ 8)
    iGeneratorCf10 = p16 * (iGeneratorFqScalar ^ 9)
    iGeneratorCf11 = p16 * (iGeneratorFqScalar ^ 10)
    iGeneratorCf12 = p16 * (iGeneratorFqScalar ^ 11)
    iGeneratorCf13 = p16 * (iGeneratorFqScalar ^ 12)
    iGeneratorCf14 = p16 * (iGeneratorFqScalar ^ 13)
    iGeneratorCf15 = p16 * (iGeneratorFqScalar ^ 14)
    iGeneratorCf16 = p16 * (iGeneratorFqScalar ^ 15)
    
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        = aAmpCh02 * 2                               ; increase signal power
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        = aAmpCh03 * 2                               ; increase signal power
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        = aAmpCh04 * 2                               ; increase signal power
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        = aAmpCh05 * 2                               ; increase signal power
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        = aAmpCh06 * 2                               ; increase signal power
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        = aAmpCh07 * 2                               ; increase signal power
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        = aAmpCh08 * 2                               ; increase signal power
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf

    aAmpCh09        butterbp     aSrc, iAnalysisCf09, iAnalysisQ
    aAmpCh09        = abs(aAmpCh09)
    aAmpCh09        butterlp     aAmpCh09, iAnalysisCutoff
    aAmpCh09        = aAmpCh09 * 2                               ; increase signal power
    aAmpCh09        tone         aAmpCh09, iAnalysisCutoff   ; one pole lpf

    aAmpCh10        butterbp     aSrc, iAnalysisCf10, iAnalysisQ
    aAmpCh10        = abs(aAmpCh10)
    aAmpCh10        butterlp     aAmpCh10, iAnalysisCutoff
    aAmpCh10        = aAmpCh10 * 2                               ; increase signal power
    aAmpCh10        tone         aAmpCh10, iAnalysisCutoff   ; one pole lpf

    aAmpCh11        butterbp     aSrc, iAnalysisCf11, iAnalysisQ
    aAmpCh11        = abs(aAmpCh11)
    aAmpCh11        butterlp     aAmpCh11, iAnalysisCutoff
    aAmpCh11        = aAmpCh11 * 2                               ; increase signal power
    aAmpCh11        tone         aAmpCh11, iAnalysisCutoff   ; one pole lpf

    aAmpCh12        butterbp     aSrc, iAnalysisCf12, iAnalysisQ
    aAmpCh12        = abs(aAmpCh12)
    aAmpCh12        butterlp     aAmpCh12, iAnalysisCutoff
    aAmpCh12        = aAmpCh12 * 2                               ; increase signal power
    aAmpCh12        tone         aAmpCh12, iAnalysisCutoff   ; one pole lpf

    aAmpCh13        butterbp     aSrc, iAnalysisCf13, iAnalysisQ
    aAmpCh13        = abs(aAmpCh13)
    aAmpCh13        butterlp     aAmpCh13, iAnalysisCutoff
    aAmpCh13        = aAmpCh13 * 2                               ; increase signal power
    aAmpCh13        tone         aAmpCh13, iAnalysisCutoff   ; one pole lpf

    aAmpCh14        butterbp     aSrc, iAnalysisCf14, iAnalysisQ
    aAmpCh14        = abs(aAmpCh14)
    aAmpCh14        butterlp     aAmpCh14, iAnalysisCutoff
    aAmpCh14        = aAmpCh14 * 2                               ; increase signal power
    aAmpCh14        tone         aAmpCh14, iAnalysisCutoff   ; one pole lpf

    aAmpCh15        butterbp     aSrc, iAnalysisCf15, iAnalysisQ
    aAmpCh15        = abs(aAmpCh15)
    aAmpCh15        butterlp     aAmpCh15, iAnalysisCutoff
    aAmpCh15        = aAmpCh15 * 2                               ; increase signal power
    aAmpCh15        tone         aAmpCh15, iAnalysisCutoff   ; one pole lpf

    aAmpCh16        butterbp     aSrc, iAnalysisCf16, iAnalysisQ
    aAmpCh16        = abs(aAmpCh16)
    aAmpCh16        butterlp     aAmpCh16, iAnalysisCutoff
    aAmpCh16        = aAmpCh16 * 2                               ; increase signal power
    aAmpCh16        tone         aAmpCh16, iAnalysisCutoff   ; one pole lpf

    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01
    aGen02      butterbp     aNoise, iGeneratorCf02, iAnalysisQ 
    aGen02      = aGen02 * aAmpCh02
    aGen03      butterbp     aNoise, iGeneratorCf03, iAnalysisQ 
    aGen03      = aGen03 * aAmpCh03
    aGen04      butterbp     aNoise, iGeneratorCf04, iAnalysisQ 
    aGen04      = aGen04 * aAmpCh04

    aGen05      butterbp     aNoise, iGeneratorCf05, iAnalysisQ 
    aGen05      = aGen05 * aAmpCh05
    aGen06      butterbp     aNoise, iGeneratorCf06, iAnalysisQ 
    aGen06      = aGen06 * aAmpCh06
    aGen07      butterbp     aNoise, iGeneratorCf07, iAnalysisQ 
    aGen07      = aGen07 * aAmpCh07
    aGen08      butterbp     aNoise, iGeneratorCf08, iAnalysisQ 
    aGen08      = aGen08 * aAmpCh08

    aGen09      butterbp     aNoise, iGeneratorCf09, iAnalysisQ 
    aGen09      = aGen09 * aAmpCh09
    aGen10      butterbp     aNoise, iGeneratorCf10, iAnalysisQ 
    aGen10      = aGen10 * aAmpCh10
    aGen11      butterbp     aNoise, iGeneratorCf11, iAnalysisQ 
    aGen11      = aGen11 * aAmpCh11
    aGen12      butterbp     aNoise, iGeneratorCf12, iAnalysisQ 
    aGen12      = aGen12 * aAmpCh12

    aGen13      butterbp     aNoise, iGeneratorCf13, iAnalysisQ 
    aGen13      = aGen13 * aAmpCh13
    aGen14      butterbp     aNoise, iGeneratorCf14, iAnalysisQ 
    aGen14      = aGen14 * aAmpCh14
    aGen15      butterbp     aNoise, iGeneratorCf15, iAnalysisQ 
    aGen15      = aGen15 * aAmpCh15
    aGen16      butterbp     aNoise, iGeneratorCf16, iAnalysisQ 
    aGen16      = aGen16 * aAmpCh16

    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08 + aGen09 + aGen10 + aGen11 + aGen12 + aGen13 + aGen14 + aGen15 + aGen16)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
# 24 ch
class Inst48(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 48
        self.name = 'vocodeNoiseTriOctScale'
        self.info = 'A twenty-four channel vocoder with scaled mapping.'
        self.auxNo = 13
        self.postMapAmp = (0, 40, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',
          
          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 1.0), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 80),
          'pmtr15'  : ('c', 1.25),

          'pmtr16'  : ('c', 80),
          'pmtr17'  : ('c', 1.25),
          
          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 20000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iAnalysisCf09 = p14 * (iAnalysisFqScalar ^ 8)
    iAnalysisCf10 = p14 * (iAnalysisFqScalar ^ 9)
    iAnalysisCf11 = p14 * (iAnalysisFqScalar ^ 10)
    iAnalysisCf12 = p14 * (iAnalysisFqScalar ^ 11)
    iAnalysisCf13 = p14 * (iAnalysisFqScalar ^ 12)
    iAnalysisCf14 = p14 * (iAnalysisFqScalar ^ 13)
    iAnalysisCf15 = p14 * (iAnalysisFqScalar ^ 14)
    iAnalysisCf16 = p14 * (iAnalysisFqScalar ^ 15)

    iAnalysisCf17 = p14 * (iAnalysisFqScalar ^ 16)
    iAnalysisCf18 = p14 * (iAnalysisFqScalar ^ 17)
    iAnalysisCf19 = p14 * (iAnalysisFqScalar ^ 18)
    iAnalysisCf20 = p14 * (iAnalysisFqScalar ^ 19)
    iAnalysisCf21 = p14 * (iAnalysisFqScalar ^ 20)
    iAnalysisCf22 = p14 * (iAnalysisFqScalar ^ 21)
    iAnalysisCf23 = p14 * (iAnalysisFqScalar ^ 22)
    iAnalysisCf24 = p14 * (iAnalysisFqScalar ^ 23)


    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)

    iGeneratorCf09 = p16 * (iGeneratorFqScalar ^ 8)
    iGeneratorCf10 = p16 * (iGeneratorFqScalar ^ 9)
    iGeneratorCf11 = p16 * (iGeneratorFqScalar ^ 10)
    iGeneratorCf12 = p16 * (iGeneratorFqScalar ^ 11)
    iGeneratorCf13 = p16 * (iGeneratorFqScalar ^ 12)
    iGeneratorCf14 = p16 * (iGeneratorFqScalar ^ 13)
    iGeneratorCf15 = p16 * (iGeneratorFqScalar ^ 14)
    iGeneratorCf16 = p16 * (iGeneratorFqScalar ^ 15)

    iGeneratorCf17 = p16 * (iGeneratorFqScalar ^ 16)
    iGeneratorCf18 = p16 * (iGeneratorFqScalar ^ 17)
    iGeneratorCf19 = p16 * (iGeneratorFqScalar ^ 18)
    iGeneratorCf20 = p16 * (iGeneratorFqScalar ^ 19)
    iGeneratorCf21 = p16 * (iGeneratorFqScalar ^ 20)
    iGeneratorCf22 = p16 * (iGeneratorFqScalar ^ 21)
    iGeneratorCf23 = p16 * (iGeneratorFqScalar ^ 22)
    iGeneratorCf24 = p16 * (iGeneratorFqScalar ^ 23)

    
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        = aAmpCh02 * 2                               ; increase signal power
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        = aAmpCh03 * 2                               ; increase signal power
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        = aAmpCh04 * 2                               ; increase signal power
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        = aAmpCh05 * 2                               ; increase signal power
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        = aAmpCh06 * 2                               ; increase signal power
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        = aAmpCh07 * 2                               ; increase signal power
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        = aAmpCh08 * 2                               ; increase signal power
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf


    aAmpCh09        butterbp     aSrc, iAnalysisCf09, iAnalysisQ
    aAmpCh09        = abs(aAmpCh09)
    aAmpCh09        butterlp     aAmpCh09, iAnalysisCutoff
    aAmpCh09        = aAmpCh09 * 2                               ; increase signal power
    aAmpCh09        tone         aAmpCh09, iAnalysisCutoff   ; one pole lpf

    aAmpCh10        butterbp     aSrc, iAnalysisCf10, iAnalysisQ
    aAmpCh10        = abs(aAmpCh10)
    aAmpCh10        butterlp     aAmpCh10, iAnalysisCutoff
    aAmpCh10        = aAmpCh10 * 2                               ; increase signal power
    aAmpCh10        tone         aAmpCh10, iAnalysisCutoff   ; one pole lpf

    aAmpCh11        butterbp     aSrc, iAnalysisCf11, iAnalysisQ
    aAmpCh11        = abs(aAmpCh11)
    aAmpCh11        butterlp     aAmpCh11, iAnalysisCutoff
    aAmpCh11        = aAmpCh11 * 2                               ; increase signal power
    aAmpCh11        tone         aAmpCh11, iAnalysisCutoff   ; one pole lpf

    aAmpCh12        butterbp     aSrc, iAnalysisCf12, iAnalysisQ
    aAmpCh12        = abs(aAmpCh12)
    aAmpCh12        butterlp     aAmpCh12, iAnalysisCutoff
    aAmpCh12        = aAmpCh12 * 2                               ; increase signal power
    aAmpCh12        tone         aAmpCh12, iAnalysisCutoff   ; one pole lpf

    aAmpCh13        butterbp     aSrc, iAnalysisCf13, iAnalysisQ
    aAmpCh13        = abs(aAmpCh13)
    aAmpCh13        butterlp     aAmpCh13, iAnalysisCutoff
    aAmpCh13        = aAmpCh13 * 2                               ; increase signal power
    aAmpCh13        tone         aAmpCh13, iAnalysisCutoff   ; one pole lpf

    aAmpCh14        butterbp     aSrc, iAnalysisCf14, iAnalysisQ
    aAmpCh14        = abs(aAmpCh14)
    aAmpCh14        butterlp     aAmpCh14, iAnalysisCutoff
    aAmpCh14        = aAmpCh14 * 2                               ; increase signal power
    aAmpCh14        tone         aAmpCh14, iAnalysisCutoff   ; one pole lpf

    aAmpCh15        butterbp     aSrc, iAnalysisCf15, iAnalysisQ
    aAmpCh15        = abs(aAmpCh15)
    aAmpCh15        butterlp     aAmpCh15, iAnalysisCutoff
    aAmpCh15        = aAmpCh15 * 2                               ; increase signal power
    aAmpCh15        tone         aAmpCh15, iAnalysisCutoff   ; one pole lpf

    aAmpCh16        butterbp     aSrc, iAnalysisCf16, iAnalysisQ
    aAmpCh16        = abs(aAmpCh16)
    aAmpCh16        butterlp     aAmpCh16, iAnalysisCutoff
    aAmpCh16        = aAmpCh16 * 2                               ; increase signal power
    aAmpCh16        tone         aAmpCh16, iAnalysisCutoff   ; one pole lpf


    aAmpCh17        butterbp     aSrc, iAnalysisCf17, iAnalysisQ
    aAmpCh17        = abs(aAmpCh17)
    aAmpCh17        butterlp     aAmpCh17, iAnalysisCutoff
    aAmpCh17        = aAmpCh17 * 2                               ; increase signal power
    aAmpCh17        tone         aAmpCh17, iAnalysisCutoff   ; one pole lpf

    aAmpCh18        butterbp     aSrc, iAnalysisCf18, iAnalysisQ
    aAmpCh18        = abs(aAmpCh18)
    aAmpCh18        butterlp     aAmpCh18, iAnalysisCutoff
    aAmpCh18        = aAmpCh18 * 2                               ; increase signal power
    aAmpCh18        tone         aAmpCh18, iAnalysisCutoff   ; one pole lpf

    aAmpCh19        butterbp     aSrc, iAnalysisCf19, iAnalysisQ
    aAmpCh19        = abs(aAmpCh19)
    aAmpCh19        butterlp     aAmpCh19, iAnalysisCutoff
    aAmpCh19        = aAmpCh19 * 2                               ; increase signal power
    aAmpCh19        tone         aAmpCh19, iAnalysisCutoff   ; one pole lpf

    aAmpCh20        butterbp     aSrc, iAnalysisCf20, iAnalysisQ
    aAmpCh20        = abs(aAmpCh20)
    aAmpCh20        butterlp     aAmpCh20, iAnalysisCutoff
    aAmpCh20        = aAmpCh20 * 2                               ; increase signal power
    aAmpCh20        tone         aAmpCh20, iAnalysisCutoff   ; one pole lpf

    aAmpCh21        butterbp     aSrc, iAnalysisCf21, iAnalysisQ
    aAmpCh21        = abs(aAmpCh21)
    aAmpCh21        butterlp     aAmpCh21, iAnalysisCutoff
    aAmpCh21        = aAmpCh21 * 2                               ; increase signal power
    aAmpCh21        tone         aAmpCh21, iAnalysisCutoff   ; one pole lpf

    aAmpCh22        butterbp     aSrc, iAnalysisCf22, iAnalysisQ
    aAmpCh22        = abs(aAmpCh22)
    aAmpCh22        butterlp     aAmpCh22, iAnalysisCutoff
    aAmpCh22        = aAmpCh22 * 2                               ; increase signal power
    aAmpCh22        tone         aAmpCh22, iAnalysisCutoff   ; one pole lpf

    aAmpCh23        butterbp     aSrc, iAnalysisCf23, iAnalysisQ
    aAmpCh23        = abs(aAmpCh23)
    aAmpCh23        butterlp     aAmpCh23, iAnalysisCutoff
    aAmpCh23        = aAmpCh23 * 2                               ; increase signal power
    aAmpCh23        tone         aAmpCh23, iAnalysisCutoff   ; one pole lpf

    aAmpCh24        butterbp     aSrc, iAnalysisCf24, iAnalysisQ
    aAmpCh24        = abs(aAmpCh24)
    aAmpCh24        butterlp     aAmpCh24, iAnalysisCutoff
    aAmpCh24        = aAmpCh24 * 2                               ; increase signal power
    aAmpCh24        tone         aAmpCh24, iAnalysisCutoff   ; one pole lpf


    ; filter noise at fq, scale by analysis
    aGen01      butterbp     aNoise, iGeneratorCf01, iAnalysisQ 
    aGen01      = aGen01 * aAmpCh01
    aGen02      butterbp     aNoise, iGeneratorCf02, iAnalysisQ 
    aGen02      = aGen02 * aAmpCh02
    aGen03      butterbp     aNoise, iGeneratorCf03, iAnalysisQ 
    aGen03      = aGen03 * aAmpCh03
    aGen04      butterbp     aNoise, iGeneratorCf04, iAnalysisQ 
    aGen04      = aGen04 * aAmpCh04

    aGen05      butterbp     aNoise, iGeneratorCf05, iAnalysisQ 
    aGen05      = aGen05 * aAmpCh05
    aGen06      butterbp     aNoise, iGeneratorCf06, iAnalysisQ 
    aGen06      = aGen06 * aAmpCh06
    aGen07      butterbp     aNoise, iGeneratorCf07, iAnalysisQ 
    aGen07      = aGen07 * aAmpCh07
    aGen08      butterbp     aNoise, iGeneratorCf08, iAnalysisQ 
    aGen08      = aGen08 * aAmpCh08

    aGen09      butterbp     aNoise, iGeneratorCf09, iAnalysisQ 
    aGen09      = aGen09 * aAmpCh09
    aGen10      butterbp     aNoise, iGeneratorCf10, iAnalysisQ 
    aGen10      = aGen10 * aAmpCh10
    aGen11      butterbp     aNoise, iGeneratorCf11, iAnalysisQ 
    aGen11      = aGen11 * aAmpCh11
    aGen12      butterbp     aNoise, iGeneratorCf12, iAnalysisQ 
    aGen12      = aGen12 * aAmpCh12

    aGen13      butterbp     aNoise, iGeneratorCf13, iAnalysisQ 
    aGen13      = aGen13 * aAmpCh13
    aGen14      butterbp     aNoise, iGeneratorCf14, iAnalysisQ 
    aGen14      = aGen14 * aAmpCh14
    aGen15      butterbp     aNoise, iGeneratorCf15, iAnalysisQ 
    aGen15      = aGen15 * aAmpCh15
    aGen16      butterbp     aNoise, iGeneratorCf16, iAnalysisQ 
    aGen16      = aGen16 * aAmpCh16

    aGen17      butterbp     aNoise, iGeneratorCf17, iAnalysisQ 
    aGen17      = aGen17 * aAmpCh17
    aGen18      butterbp     aNoise, iGeneratorCf18, iAnalysisQ 
    aGen18      = aGen18 * aAmpCh18
    aGen19      butterbp     aNoise, iGeneratorCf19, iAnalysisQ 
    aGen19      = aGen19 * aAmpCh19
    aGen20      butterbp     aNoise, iGeneratorCf20, iAnalysisQ 
    aGen20      = aGen20 * aAmpCh20

    aGen21      butterbp     aNoise, iGeneratorCf21, iAnalysisQ 
    aGen21      = aGen21 * aAmpCh21
    aGen22      butterbp     aNoise, iGeneratorCf22, iAnalysisQ 
    aGen22      = aGen22 * aAmpCh22
    aGen23      butterbp     aNoise, iGeneratorCf23, iAnalysisQ 
    aGen23      = aGen23 * aAmpCh23
    aGen24      butterbp     aNoise, iGeneratorCf24, iAnalysisQ 
    aGen24      = aGen24 * aAmpCh24

    ; mix all channels
    aSubA           = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)
    aSubB           = (aGen09 + aGen10 + aGen11 + aGen12 + aGen13 + aGen14 + aGen15 + aGen16)
    aSubC           = (aGen17 + aGen18 + aGen19 + aGen20 + aGen21 + aGen22 + aGen23 + aGen24)
    aSig            = aSubA + aSubB + aSubC
    
    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)











#-----------------------------------------------------------------||||||||||||--
# this only works if file name is given as a number
# cant get it to accept a complete path

class Inst101(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 101
        self.name = 'phaseVocodeRead'
        self.info = 'A simple phase voice reader instrument.'
        self.auxNo = 5
        # dont know what amp scaling is necessary here
        self.postMapAmp = (0, 74, 'linear') # most amps are in db

        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
                      'pmtr7'   : 'pvc analysis file to use',
                     } # holds discription, preset for each pmtr in a dictionary
        self.pmtrDefault = {
          #'ampQ'    : ('cyclicGen', 'linearDown', 2.00, 9.00, 0.25),
          #'pmtr7'   : ('analysisSelect', ('harmonica.1',)),
          'pmtr7'   : ('constant', 1),
          #'pmtr7'   : ('constant', '"/Volumes/xdisc/_scratch/pvoc.1"'),
          'pmtr8'   : ('sl', '3|5|13|19', 1, 60, 'integer', 'rw'),
          'pmtr9'   : ('constant', 0.5),
          'pmtr10'  : ('constant', .001),
          'pmtr11'  : ('constant', .001),
          }

# ; p4 is max amp (in db)
# ; p7 is file no
# ; p8 is bin
# ; p9 is start time in analysis
# ; p10 is fade in time in sec.
# ; p11 is fade out time in sec.

        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    
    ktime             line   p9, iDur, p9 + iDur 
    kenv              linen  iAmp, p10, iDur, p11
    kFreq, kAmp   pvread     ktime, p7, p8 
    aSig              oscili     kAmp, kFreq, 1
    
    aMixSig =     aSig * kenv
""" % str(self.instNo)






#-----------------------------------------------------------------||||||||||||--
class Inst50(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 50
        self.name = 'guitarNylonNormal'
        self.info = 'A simple nylon-string guitar instrument.'
        self.auxNo = 0
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
                     } # holds discription, preset for each pmtr in a dictionary
        self.pmtrDefault = {
          'rhythmQ' : ('loop', (
                          (6,1,1), (6,1,1), (6,1,1), (6,5,1), (6, 2, 0))), 
          #'ampQ'    : ('cyclicGen', 'linearDown', 80.00, 86.00, 0.25),
          }
        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

;   original evelope, w/ fixed values of attack and release
;   kAmp            linseg  0.0, 0.015, iAmp, p3-0.065, iAmp, 0.050, 0.0

    kAmp linseg 0.0, 0.015, iAmp, ((p3-0.015)*.89), iAmp, ((p3-0.015)*.11), 0.0
    aSig            pluck       kAmp, iFreq, iFreq, 0, 1
    af1         reson       aSig, 110, 80
    af2         reson       aSig, 220, 100
    af3         reson       aSig, 440, 80
    aMixSig     balance 0.6 * af1 + af2 + 0.6 * af3 + 0.4 * aSig, aSig
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst51(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 51
        self.name = 'guitarNylonLegato'
        self.info = 'A simple nylon-string guitar instrument, with hammer-on / pull-off attack'
        self.auxNo = 2
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'pitch of note departing-from, in PCH notation',
          'pmtr8'   : 'percentage of note departing, between 0 and 1',
            }
        self.pmtrDefault = {
          'rhythmQ' : ('loop', 
                          ((6,1,1), (6,1,1), (6,1,1), (6,5,1), (6,2,0))), 
          #'ampQ'    : ('cyclicGen', 'linearDown', 80.00, 86.00, 0.25),
          'pmtr7'   : ('basketGen', 'randomChoice', (6.09, 5.03)),
          'pmtr8'   : ('basketGen', 'randomChoice', (.25, .75)),
          }
        self.orcCode = """
instr %s
    iDur      = p3
    iAmp      = ampdb(p4)
    iFreq     = cpspch(p5)
    iPan      = p6
    ibaseFq = cpspch(p7)

    kAmp         linseg 0.0, 0.015, iAmp, p3-0.065, iAmp, 0.05, 0.0
    kFreq        linseg iFreq, p8*p3, iFreq, 0.005, ibaseFq, (1-p8)*p3-0.005, ibaseFq

    aSig         pluck  kAmp, kFreq, iFreq, 0, 1
    af1      reson  aSig, 110, 80
    af2      reson  aSig, 220, 100
    af3      reson  aSig, 440, 80
    aMixSig  balance 0.6*af1+af2+0.6*af3+0.4*aSig, aSig
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst52(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 52
        self.name = 'guitarNylonHarmonic'
        self.info = 'A simple nylon-string guitar instrument, harmonic attack'
        self.auxNo = 0
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {}
        self.pmtrDefault      = {
          'rhythmQ' : ('loop', 
                          ((6,1,1), (6,1,1), (6,1,1), (6,5,1), (6,2,0))), 
          #'ampQ'    : ('cyclicGen', 'linearDown', 80.00, 86.00, 0.25),
                     }
        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    kAmp            linseg 0.0, 0.015, iAmp, p3-0.035, iAmp, 0.02, 0.0
    aMixSig     pluck kAmp, iFreq, iFreq, 0, 6
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--

class Inst60(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 60
        self.name = 'additiveBellBright'
        self.info = 'A simple bell made with 12 partials, each with their own envelope, then mixed together. Based on design by C. Risset.'
        self.auxNo = 0
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {} # infor for aux perameters (greater than six)
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((16, 1), (16, 3))),
          #'ampQ'    : ('cyclicGen', 'linearUp', 60, 70, 1),
          } 
        self.orcCode = """
    instr %s
        iPan     = p6
        iDur1    = p3
        iAmp1    = ampdb(p4)
        iFreq1 = (cpspch(p5) * .56)
        iDur2    = (p3 * .9)
        iAmp2    = (ampdb(p4) * .67)
        iFreq2 = (cpspch(p5))
        iDur3    = (p3 * .65)
        iAmp3    = (ampdb(p4))
        iFreq3 = (cpspch(p5) * .92)
        iDur4    = (p3 * .55)
        iAmp4    = (ampdb(p4)   * 1.8)
        iFreq4 = (cpspch(p5) * 2.62)            
        iDur5    = (p3 * .35)
        iAmp5    = (ampdb(p4)   * 2.67)
        iFreq5 = (cpspch(p5) * 1.19)
        iDur6    = (p3 * .35)
        iAmp6    = (ampdb(p4)   * 1.67)
        iFreq6 = (cpspch(p5) * 1.7)
        iDur7    = (p3 * .25)
        iAmp7    = (ampdb(p4)   * 1.46)
        iFreq7 = (cpspch(p5) * 2)
        iDur8    = (p3 * .2)
        iAmp8    = (ampdb(p4)   * 1.33)
        iFreq8 = (cpspch(p5) * 2.74)
        iDur9    = (p3 * .15)
        iAmp9    = (ampdb(p4)   * 1.33)
        iFreq9 = (cpspch(p5) * 3)
        iDur10 = (p3 * .1)
        iAmp10 = (ampdb(p4))
        iFreq10= (cpspch(p5) * 3.76)
        iDur11 = (p3 * .075)
        iAmp11 = (ampdb(p4) * 1.33)
        iFreq11= (cpspch(p5) * 4.07)
        
            ;create oscilators for each partial
        koscil1 oscil1i  0, iAmp1, iDur1, 2
        aoscili1 oscili  koscil1, iFreq1, 3
        koscil2 oscil1i  0, iAmp2, iDur2, 2
        aoscili2 oscili  koscil2, iFreq2, 3
        koscil3 oscil1i  0, iAmp3, iDur3, 2
        aoscili3 oscili  koscil3, iFreq3, 3
        koscil4 oscil1i  0, iAmp4, iDur4, 2
        aoscili4 oscili  koscil4, iFreq4, 3
        koscil5 oscil1i  0, iAmp5, iDur5, 2
        aoscili5 oscili  koscil5, iFreq5, 3
        koscil6 oscil1i  0, iAmp6, iDur6, 2
        aoscili6 oscili  koscil6, iFreq6, 3
        koscil7 oscil1i  0, iAmp7, iDur7, 2
        aoscili7 oscili  koscil7, iFreq7, 3
        koscil8 oscil1i  0, iAmp8, iDur8, 2
        aoscili8 oscili  koscil8, iFreq8, 3
        koscil9 oscil1i  0, iAmp9, iDur9, 2
        aoscili9 oscili  koscil9, iFreq9, 3
        koscil10 oscil1i     0, iAmp10, iDur10, 2
        aoscili10 oscili     koscil10, iFreq10, 3
        koscil11 oscil1i     0, iAmp11, iDur11, 2
        aoscili11 oscili     koscil11, iFreq11, 3
    
        ;output assignments
        aMixSig          = (aoscili1 + aoscili2 + aoscili3 + aoscili4 + aoscili5 + aoscili6 + aoscili7 + aoscili8 + aoscili9 + aoscili10 + aoscili11)
    """ % str(self.instNo)

        self.scoSample = """
    ;p1  p2  p3   p4      p5         p6
    ;inst    start dur    amp     PCH        pan
    i2      12.00 1.000  97  7.09     .5
    i2      12.10 1.000  84  8.09     .5
    """


#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
class Inst61(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 61
        self.name = 'additiveBellDark'
        self.info = 'A simple bell made with 12 partials, each with their own envelope, then mixed together. Based on design by C. Risset.'
        self.auxNo = 0
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((4, 5), (4, 5))),
          #'ampQ'    : ('cyclicGen', 'linearUp', 60, 66, .8) ,
          } 
        self.orcCode = """
instr %s
    iPan     = p6
    iDur1    = (p3 * .5)
    iAmp1    = (ampdb(p4)   * .5)
    iFreq1 = (cpspch(p5) * .2)
    iDur2    = (p3 * .5)
    iAmp2    = (ampdb(p4)   * .7)
    iFreq2 = (cpspch(p5) * .5)
    iDur3    = (p3 * .5)
    iAmp3    = (ampdb(p4)   * 1)
    iFreq3 = (cpspch(p5) * .8)
    iDur4    = (p3 * .6)
    iAmp4    = (ampdb(p4)   * 1.2)
    iFreq4 = (cpspch(p5) * 1)
    iDur5    = (p3 * .7)
    iAmp5    = (ampdb(p4)   * 1.5)
    iFreq5 = (cpspch(p5) * 1.2)
    iDur6    = (p3 * 1.2)
    iAmp6    = (ampdb(p4)   * 1.5)
    iFreq6 = (cpspch(p5) * 1.5)
    iDur7    = (p3 * 1.2)
    iAmp7    = (ampdb(p4)   * 1.6)
    iFreq7 = (cpspch(p5) * 2)
    iDur8    = (p3 * 1.2)
    iAmp8    = (ampdb(p4)   * 1.7)
    iFreq8 = (cpspch(p5) * 3)
    iDur9    = (p3 * 1.3)
    iAmp9    = (ampdb(p4)   * 1.8)
    iFreq9 = (cpspch(p5) * 3)
    iDur10 = (p3 * 1.4)
    iAmp10 = (ampdb(p4) * 1.9)
    iFreq10= (cpspch(p5) * 4.5)
    iDur11 = (p3 * 1.5)
    iAmp11 = (ampdb(p4) * 2)
    iFreq11= (cpspch(p5) * 4.8)
    
    koscil1 oscil1i 0, iAmp1, iDur1, 2
    aoscili1 oscili koscil1, iFreq1, 3
    koscil2 oscil1i 0, iAmp2, iDur2, 2
    aoscili2 oscili koscil2, iFreq2, 3
    koscil3 oscil1i 0, iAmp3, iDur3, 2
    aoscili3 oscili koscil3, iFreq3, 3
    koscil4 oscil1i 0, iAmp4, iDur4, 2
    aoscili4 oscili koscil4, iFreq4, 3
    koscil5 oscil1i 0, iAmp5, iDur5, 2
    aoscili5 oscili koscil5, iFreq5, 3
    koscil6 oscil1i 0, iAmp6, iDur6, 2
    aoscili6 oscili koscil6, iFreq6, 3
    koscil7 oscil1i 0, iAmp7, iDur7, 2
    aoscili7 oscili koscil7, iFreq7, 3
    koscil8 oscil1i 0, iAmp8, iDur8, 2
    aoscili8 oscili koscil8, iFreq8, 3
    koscil9 oscil1i 0, iAmp9, iDur9, 2
    aoscili9 oscili koscil9, iFreq9, 3
    koscil10 oscil1i     0, iAmp10, iDur10, 2
    aoscili10 oscili     koscil10, iFreq10, 3
    koscil11 oscil1i     0, iAmp11, iDur11, 2
    aoscili11 oscili     koscil11, iFreq11, 3

    aMixSig          = (aoscili1+aoscili2+aoscili3+aoscili4+aoscili5 + aoscili6+aoscili7+aoscili8+aoscili9+aoscili10+aoscili11)
""" % str(self.instNo)

        self.scoSample = """
;p1  p2  p3   p4      p5         p6
;inst    start dur    amp     PCH        pan
i2      12.00 1.000  97  7.09     .5
i2      12.10 1.000  84  8.09     .5
"""


#-----------------------------------------------------------------||||||||||||--
class Inst62(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 62
        self.name = 'additiveBellClear'
        self.info = 'A simple bell made with 12 partials, each with their own envelope, then mixed together. Based on design by C. Risset.'
        self.auxNo = 0
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrDefault = {
          'rhythmQ' : ('loop', ((2,1,1),(2,3,1),(4,3,0))),       
          #'ampQ'    : ('cyclicGen', 'linearUp', 60, 70, 1),
          } 
        self.orcCode = """
instr %s
    iPan     = p6
    
    iDur1    = p3
    iAmp1    = ampdb(p4)
    iFreq1 = (cpspch(p5) * 1)
    
    iDur2    = (p3 * .9)
    iAmp2    = (ampdb(p4)   * .80)
    iFreq2 = (cpspch(p5) * 1.5)
    
    iDur3    = (p3 * .70)
    iAmp3    = (ampdb(p4)   * .70)
    iFreq3 = (cpspch(p5) * 2)
    
    iDur4    = (p3 * .60)
    iAmp4    = (ampdb(p4)   * .80)
    iFreq4 = (cpspch(p5) * 2.5)       
    
    iDur5    = (p3 * .40)
    iAmp5    = (ampdb(p4)   * .55)
    iFreq5 = (cpspch(p5) * 3)
    
    iDur6    = (p3 * 1.05)
    iAmp6    = (ampdb(p4)   * .48)
    iFreq6 = (cpspch(p5) * 4)
    
    iDur7    = (p3 * .80)
    iAmp7    = (ampdb(p4)   * .40)
    iFreq7 = (cpspch(p5) * 5)
    
    iDur8    = (p3 * .65)
    iAmp8    = (ampdb(p4)   * .35)
    iFreq8 = (cpspch(p5) * 6)
    
    iDur9    = (p3 * .15)
    iAmp9    = (ampdb(p4)   * .30)
    iFreq9 = (cpspch(p5) * 7)
    
    iDur10 = (p3 * .90)
    iAmp10 = (ampdb(p4))
    iFreq10= (cpspch(p5) * 8)
    
    iDur11 = (p3 * .10)
    iAmp11 = (ampdb(p4) * .28)
    iFreq11= (cpspch(p5) * 9)
    
        ;create oscilators for each partial
    koscil1 oscil1i  0, iAmp1, iDur1, 2
    aoscili1 oscili  koscil1, iFreq1, 3
    koscil2 oscil1i  0, iAmp2, iDur2, 2
    aoscili2 oscili  koscil2, iFreq2, 3
    koscil3 oscil1i  0, iAmp3, iDur3, 2
    aoscili3 oscili  koscil3, iFreq3, 3
    koscil4 oscil1i  0, iAmp4, iDur4, 2
    aoscili4 oscili  koscil4, iFreq4, 3
    koscil5 oscil1i  0, iAmp5, iDur5, 2
    aoscili5 oscili  koscil5, iFreq5, 3
    koscil6 oscil1i  0, iAmp6, iDur6, 2
    aoscili6 oscili  koscil6, iFreq6, 3
    koscil7 oscil1i  0, iAmp7, iDur7, 2
    aoscili7 oscili  koscil7, iFreq7, 3
    koscil8 oscil1i  0, iAmp8, iDur8, 2
    aoscili8 oscili  koscil8, iFreq8, 3
    koscil9 oscil1i  0, iAmp9, iDur9, 2
    aoscili9 oscili  koscil9, iFreq9, 3
    koscil10 oscil1i     0, iAmp10, iDur10, 2
    aoscili10 oscili     koscil10, iFreq10, 3
    koscil11 oscil1i     0, iAmp11, iDur11, 2
    aoscili11 oscili     koscil11, iFreq11, 3

    ;output assignments
    aMixSig          = (aoscili1+aoscili2+aoscili3+aoscili4+aoscili5 + aoscili6+aoscili7+aoscili8+aoscili9+aoscili10+aoscili11)
""" % str(self.instNo)

        self.scoSample = """

;p1  p2  p3   p4      p5         p6
;inst    start dur    amp     PCH        pan
i9      12.00 1.000  97  7.09     .5
i9      12.10 1.000  84  8.09     .5
"""



#-----------------------------------------------------------------||||||||||||--
class Inst70(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 70
        self.name = 'synthRezzy'
        self.info = 'A highly resonated synth sound.'
        self.auxNo = 3
        self.postMapAmp = (0, 84, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'fq sweep (ms time or fq?)',
          'pmtr8'   : 'irez',
          'pmtr9'   : 'itabl1 (f-table to choose from)',
          } 
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((12,1,1),(3,1,1))) ,
          'pmtr7'   : ('cyclicGen', 'linearUpDown', 20.00, 8000.00, 40.00),
          'pmtr8'   : ('cyclicGen', 'linearUpDown', 1.00, 20.00, 1.20),
          'pmtr9'   : ('cyclicGen', 'linearUpDown', 4, 5, 1),    
          }
        self.orcCode = """
instr %s
    iDur     = p3
    iAmp     = ampdb(p4)
    ifqc     = cpspch(p5)
    iPan     = p6
    
    ; p7 = fq sweep
    irez     = p8
    itabl1 = p9
    
    ; Amplitude envelope
    kaenv    linseg 0, .01, 1, p3-.02, 1, .01, 0
    
    ; Frequency Sweep
    kfco linseg p7, .5*p3, .2*p7, .5*p3, .1*p7
    
    ; This relationship attempts to separate Freq from Res.
    ka1 = 100/irez/sqrt(kfco)-1
    ka2 = 1000/kfco
    
    ; Initialize Yn-1 & Yn-2 to zero
    aynm1 init 0
    aynm2 init 0
    
    ; Oscillator                last number here is the table number
    axn oscil iAmp, ifqc, itabl1
    
    ; Replace the differential eq. with a difference eq.
    ayn = ((ka1+2*ka2)*aynm1-ka2*aynm2+axn)/(1+ka1+ka2)
    
    atemp tone axn, kfco
    aclip1 = (ayn-atemp)/100000
    aclip tablei aclip1, 13, 1, .5
    aout = aclip*20000+atemp
    
    aynm2 = aynm1
    aynm1 = ayn
    
    aMixSig = (kaenv*aout)
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst71(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 71
        self.name = 'synthWaveformVibrato'
        self.info = 'A waveform derived instrument that has vibrato controls.'
        self.auxNo = 8
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'attack',
          'pmtr8'   : 'release rate',
          'pmtr9'   : 'vibrato depth',
          'pmtr10'  : 'vibrato delay',
          'pmtr11'  : 'vibrato fq',
          'pmtr12'  : 'start',
          'pmtr13'  : 'end',
          'pmtr14'  : 'xtime',
          }
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((9, 6), (9, 2))), 
          #'ampQ'    : ('cyclicGen', 'linearDown', 60, 70, 4),
          'pmtr7'   : ('cyclicGen', 'linearUp', 1, 4, 1),       
          'pmtr8'   : ('cyclicGen', 'linearUp', 2, 3, 1),
          'pmtr9'   : ('cyclicGen', 'linearUp', 2, 4, 1),       
          'pmtr10'  : ('cyclicGen', 'linearUp', 2, 4, 1),         
          'pmtr11'  : ('cyclicGen', 'linearUp', .2, 2, .1), 
          'pmtr12'  : ('cyclicGen', 'linearUp', 1, 6, 1),    
          'pmtr13'  : ('cyclicGen', 'linearUp', 1, 5, 1),    
          'pmtr14'  : ('cyclicGen', 'linearUp', .6, .8, .01),    
          } 
        self.author = '' # attribution
        self.orcCode = """
instr %s
    iPan     = p6
                                  
    ifunc1 = p12                          ; initial waveform
    ifunc2 = p13                          ; crossfade waveform
    ifad1    = p3 - (p14 * p3)        ; calculate initial fade
    ifad2    = p3 - ifad1                 ; calculate remaining dur
    irel     = .1                             ; set vibrato release
    idel1    = p3 - (p11 * p3)        ; calculate initial delay
    isus     = p3 - (idel1- irel)     ; calculate remaining dur
    iAmp     = ampdb(p4)
    iscale = iAmp * .166                                          ; p4=amp
    inote    = cpspch(p5)                                         ; p5=freq
    
    k3   linseg   0, idel1, p10, isus, p10, irel, 0     ; p7=attack time
    k2   oscil    k3, p9, 1                                  ; p7=release time
    k1   linen    iscale, p7, p3, p8                         ; p9=vib rate
    a6   oscil    k1, inote*.5+k2, ifunc2                ; p10=vib depth
    a5   oscil    k1, inote*1.25+k2, ifunc2          ; p11=vib delay (0-1)
    a4   oscil    k1, inote+k2, ifunc2                   ; p12=initial wave
    a3   oscil    k1, inote*.997+k2, ifunc1          ; p13=cross wave
    a2   oscil    k1, inote*1.003+k2, ifunc1             ; p14=fade time (0-1)
    a1   oscil    k1, inote+k2, ifunc1   
                 
    kfade    linseg 1, ifad1, 0, ifad2, 1
    afunc1 = kfade * (a1+a2+a3)
    afunc2 = (1 - kfade) * (a4+a5+a6)

    aMixSig          = (afunc1 + afunc2)
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst72(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 72
        self.name = 'synthVcoAudioEnvelopeSineQuad'
        self.info = 'A vco saw, square, or triangle waveform, a proportional linear envelope, and a variable low-pass filter with an audio rate sine envelope.'
        self.auxNo = 20
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'vco wave form index integer (1-3)',
          'pmtr13'  : 'vco start width (0-2)',
          'pmtr14'  : 'vco end width (0-2)',
          
          'pmtr15'  : 'tremelo sine 1 start frequency in Hz',
          'pmtr16'  : 'tremelo sine 1 end frequency in Hz',
          'pmtr17'  : 'tremelo sine 1 amp (0-1)',
          'pmtr18'  : 'tremelo sine 2 start frequency in Hz',
          'pmtr19'  : 'tremelo sine 2 end frequency in Hz',
          'pmtr20'  : 'tremelo sine 2 amp (0-1)',
          'pmtr21'  : 'tremelo sine 3 start frequency in Hz',
          'pmtr22'  : 'tremelo sine 3 end frequency in Hz',
          'pmtr23'  : 'tremelo sine 3 amp (0-1)',
          'pmtr24'  : 'tremelo sine 4 start frequency in Hz',
          'pmtr25'  : 'tremelo sine 4 end frequency in Hz',
          'pmtr26'  : 'tremelo sine 4 amp (0-1)',            
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('bg', 'rc', (1,2,3)),
          'pmtr13'  : ('c', 0.1),
          'pmtr14'  : ('c', 1.9),

          'pmtr15'  : ('c', 2),
          'pmtr16'  : ('c', 4),
          'pmtr17'  : ('c', .25),
          
          'pmtr18'  : ('c', 2),
          'pmtr19'  : ('c', .125),
          'pmtr20'  : ('c', 0),
          
          'pmtr21'  : ('c', 32),
          'pmtr22'  : ('c', 16),
          'pmtr23'  : ('c', 0),

          'pmtr24'  : ('c', .43),
          'pmtr25'  : ('c', 200),
          'pmtr26'  : ('c', 0),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    
    iVcoWaveForm = p12
    iVcoWidthStart = p13     
    iVcoWidthEnd = p14  

    ; get trem envl times
    iTremRateStart01 = p15
    iTremRateEnd01 = p16
    iTremAmp01  = p17
    
    iTremRateStart02 = p18
    iTremRateEnd02 = p19
    iTremAmp02  = p20
    
    iTremRateStart03 = p21
    iTremRateEnd03 = p22
    iTremAmp03  = p23
    
    iTremRateStart04 = p24
    iTremRateEnd04 = p25
    iTremAmp04  = p26

    ; create fq line segments
    kTremCf01   linseg   iTremRateStart01, iDur, iTremRateEnd01
    kTremCf02   linseg   iTremRateStart02, iDur, iTremRateEnd02
    kTremCf03   linseg   iTremRateStart03, iDur, iTremRateEnd03
    kTremCf04   linseg   iTremRateStart04, iDur, iTremRateEnd04


    ; create audio rate envelopes
    ; norm b/n 0 and 1; scale by amp; sihft by 1 lt amp; if amp 0 out is 1

    iTable      = 1 ; hi rez sine wave   
    aTrem01     poscil 1, kTremCf01, iTable
    aTrem01     = (((aTrem01 + 1) * .5) * iTremAmp01) + (1 - iTremAmp01)
    
    aTrem02     poscil 1, kTremCf02, iTable
    aTrem02     = (((aTrem02 + 1) * .5) * iTremAmp02) + (1 - iTremAmp02)

    aTrem03     poscil 1, kTremCf03, iTable
    aTrem03     = (((aTrem03 + 1) * .5) * iTremAmp03) + (1 - iTremAmp03)

    aTrem04     poscil 1, kTremCf04, iTable
    aTrem04     = (((aTrem04 + 1) * .5) * iTremAmp04) + (1 - iTremAmp04)
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease

    kVcoWidth   linseg   iVcoWidthStart, iDur, iVcoWidthEnd   
    aSig            vco      kAmp, iFreq, iVcoWaveForm, kVcoWidth, iTable
    
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd  
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * aTrem01 * aTrem02 * aTrem03 * aTrem04
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst73(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 73
        self.name = 'synthVcoAudioEnvelopeSquareQuad'
        self.info = 'A vco saw, square, or triangle waveform, a proportional linear envelope, and a variable low-pass filter with an audio rate square envelope.'
        self.auxNo = 20
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'vco wave form index integer (1-3)',
          'pmtr13'  : 'vco start width (0-2)',
          'pmtr14'  : 'vco end width (0-2)',
          
          'pmtr15'  : 'tremelo square 1 start frequency in Hz',
          'pmtr16'  : 'tremelo square 1 end frequency in Hz',
          'pmtr17'  : 'tremelo square 1 amp (0-1)',
          'pmtr18'  : 'tremelo square 2 start frequency in Hz',
          'pmtr19'  : 'tremelo square 2 end frequency in Hz',
          'pmtr20'  : 'tremelo square 2 amp (0-1)',
          'pmtr21'  : 'tremelo square 3 start frequency in Hz',
          'pmtr22'  : 'tremelo square 3 end frequency in Hz',
          'pmtr23'  : 'tremelo square 3 amp (0-1)',
          'pmtr24'  : 'tremelo square 4 start frequency in Hz',
          'pmtr25'  : 'tremelo square 4 end frequency in Hz',
          'pmtr26'  : 'tremelo square 4 amp (0-1)',         
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('bg', 'rc', (1,2,3)),
          'pmtr13'  : ('c', 0.1),
          'pmtr14'  : ('c', 1.9),

          'pmtr15'  : ('c', 2),
          'pmtr16'  : ('c', 4),
          'pmtr17'  : ('c', .25),
          
          'pmtr18'  : ('c', 2),
          'pmtr19'  : ('c', .125),
          'pmtr20'  : ('c', 0),
          
          'pmtr21'  : ('c', 32),
          'pmtr22'  : ('c', 16),
          'pmtr23'  : ('c', 0),

          'pmtr24'  : ('c', .43),
          'pmtr25'  : ('c', 200),
          'pmtr26'  : ('c', 0),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    
    iVcoWaveForm = p12
    iVcoWidthStart = p13     
    iVcoWidthEnd = p14  

    ; get trem envl times
    iTremRateStart01 = p15
    iTremRateEnd01 = p16
    iTremAmp01  = p17
    
    iTremRateStart02 = p18
    iTremRateEnd02 = p19
    iTremAmp02  = p20
    
    iTremRateStart03 = p21
    iTremRateEnd03 = p22
    iTremAmp03  = p23
    
    iTremRateStart04 = p24
    iTremRateEnd04 = p25
    iTremAmp04  = p26

    ; create fq line segments
    kTremCf01   linseg   iTremRateStart01, iDur, iTremRateEnd01
    kTremCf02   linseg   iTremRateStart02, iDur, iTremRateEnd02
    kTremCf03   linseg   iTremRateStart03, iDur, iTremRateEnd03
    kTremCf04   linseg   iTremRateStart04, iDur, iTremRateEnd04

    iTable      = 5 ; hi rez square wave

    ; create audio rate envelopes
    ; norm b/n 0 and 1; scale by amp; sihft by 1 lt amp; if amp 0 out is 1
    
    aTrem01     poscil 1, kTremCf01, iTable
    aTrem01     = (((aTrem01 + 1) * .5) * iTremAmp01) + (1 - iTremAmp01)
    
    aTrem02     poscil 1, kTremCf02, iTable
    aTrem02     = (((aTrem02 + 1) * .5) * iTremAmp02) + (1 - iTremAmp02)

    aTrem03     poscil 1, kTremCf03, iTable
    aTrem03     = (((aTrem03 + 1) * .5) * iTremAmp03) + (1 - iTremAmp03)

    aTrem04     poscil 1, kTremCf04, iTable
    aTrem04     = (((aTrem04 + 1) * .5) * iTremAmp04) + (1 - iTremAmp04)
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease

    kVcoWidth   linseg   iVcoWidthStart, iDur, iVcoWidthEnd   
    aSig            vco      kAmp, iFreq, iVcoWaveForm, kVcoWidth, iTable
    
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd  
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * aTrem01 * aTrem02 * aTrem03 * aTrem04
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst74(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 74
        self.name = 'synthVcoDistort'
        self.info = 'A vco saw, square, or triangle waveform, a proportional linear envelope, and a variable low-pass filter with an lpf distortion unit.'
        self.auxNo = 14
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          
          'pmtr12'  : 'vco wave form index integer (1-3)',
          'pmtr13'  : 'vco start width (0-2)',
          'pmtr14'  : 'vco end width (0-2)',
          
          'pmtr15'  : 'resonant filter start cutoff frequency in Hz',
          'pmtr16'  : 'resonant filter end cutoff frequency in Hz',
          'pmtr17'  : 'resonant filter start resonance (0-2)',
          'pmtr18'  : 'resonant filter end resonance (0-2)',
          'pmtr19'  : 'resonant filter start distortion (0-10)',
          'pmtr20'  : 'resonant filter end distortion (0-10)',        
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('bg', 'rc', (1,2,3)),
          'pmtr13'  : ('c', 0.1),
          'pmtr14'  : ('c', 0.9),

          'pmtr15'  : ('c', 6000),
          'pmtr16'  : ('c', 1000),
          'pmtr17'  : ('c', .8),
          'pmtr18'  : ('c', .1),
          'pmtr19'  : ('c', 1000),
          'pmtr20'  : ('c', 10),

          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    
    iVcoWaveForm = p12
    iVcoWidthStart = p13     
    iVcoWidthEnd = p14  

    iResonCutoffStart = p15
    iResonCutoffEnd = p16
    iResonStart = p17
    iResonEnd = p18
    iDistortionStart = p19
    iDistortionEnd = p20
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease

    ; normalize audio file b/n -1 and 1 for lpf18
    iTable      = 1     ; hi rez sine wave
    kVcoWidth   linseg   iVcoWidthStart, iDur, iVcoWidthEnd   
    aSig            vco      1, iFreq, iVcoWaveForm, kVcoWidth, iTable
    
    ; apply distortion, lpf filter
    
    kResonCutoff     linseg   iResonCutoffStart, iDur, iResonCutoffEnd
    kReson           linseg   iResonStart, iDur, iResonEnd
    kDistortion      linseg   iDistortionStart, iDur, iDistortionEnd
    aSig                 lpf18    aSig, kResonCutoff, kReson, kDistortion

    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd  
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)









#-----------------------------------------------------------------||||||||||||--
class Inst80(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 80
        self.name = 'pluckTamHats'
        self.info = 'Percussive sound somewhere between tam-tam and high-hat.'
        self.auxNo = 2
        self.postMapAmp = (0, 80, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'iparm (0-1)', 
          'pmtr8'   : 'low-pass filter frequency',  
          }
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((16, 1), (4, 2))) ,
          #'ampQ'    : ('cyclicGen', 'linearUp', 60, 70, 4) ,
          'pmtr7'   : ('cyclicGen', 'linearUp', .1, .9, .1), 
          'pmtr8'   : ('cyclicGen', 'linearDown', 800, 16000, 200),   
          } 
        self.orcCode = """
instr %s
    iDur     = p3
    iAmp     = ampdb(p4)
    iFreq     = cpspch(p5)
    iPan     = p6
    iparm    = p7
    ilp_fq = p8
    
    k1      linseg   1, (.1*p3), .7, (.5*p3), .7, (.4*p3), 0
    
    ; kAmp, kcps,    icps, ifn, imeth iparm decay    0-1,
    a1      pluck        iAmp, iFreq,             iFreq,         0, 3,      iparm
    a2      pluck        iAmp, (iFreq * .51),  iFreq*.51, 0,    3,      iparm
    a4      pluck        iAmp, (iFreq * .24),  iFreq*.24, 0,    3,      iparm
    
    ;master mix
    a3          = ((a1 + a2 + a4) * k1)
    a6          tone        a3, ilp_fq
    aMixSig          = (a6 * 2) 
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
class Inst81(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 81
        self.name = 'pluckFormant'
        self.info = 'A pluck that slowly morphs into a vocal, formant derived sound.'
        self.auxNo = 10
        self.postMapAmp = (0, 90, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'ipluckamp, % of total amp, 1=dB amp as in p4',
          'pmtr8'   : 'ipluckdur, % of total dur, 1=entire dur of note',
          'pmtr9'   : 'ifmamp, % of total amp, 1=dB amp as in p4', 
          'pmtr10'  : 'ifmrise, % of total dur, 1=entire dur of note', 
          'pmtr11'  : 'ifmdec, % of total duration', 
          'pmtr12'  : 'index',   
          'pmtr13'  : 'ivibdepth',   
          'pmtr14'  : 'ivibrate',
          'pmtr15'  : 'iformantamp, % of total amp, 1=dB amp as in p4',  
          'pmtr16'  : 'iformantrise, % of total dur, 1=entire dur of note',  
          } 
        self.pmtrDefault = {
          'rhythmQ' : ('binaryAccent', ((2, 3), (2, 9))), 
          #'ampQ'    : ('cyclicGen', 'linearUp', 60, 70, 4),
          'pmtr7'   : ('basketGen', 'randomChoice', (0.80,0.95,0.90)),
          'pmtr8'   : ('basketGen', 'randomChoice', (0.70,0.60,0.80)),
          'pmtr9'   : ('basketGen', 'randomChoice', (0.80,0.90,0.70,0.95)), 
          'pmtr10'  : ('basketGen', 'randomChoice', (0.05,0.10,0.15,0.20)), 
          'pmtr11'  : ('basketGen', 'randomChoice', (0.70,0.85,0.95)), 
          'pmtr12'  : ('cyclicGen', 'linearUpDown', 6.00, 8.00, 1.00),    
          'pmtr13'  : ('cyclicGen', 'linearUpDown', 1.00, 1.00, 0.00),   
          'pmtr14'  : ('cyclicGen', 'linearUp', 4.00, 6.00, 1.00),
          'pmtr15'  : ('basketGen', 'randomChoice', (0.90,0.95)),  
          'pmtr16'  : ('basketGen', 'randomChoice', (0.50,0.30,0.10)),    
          } 
        self.orcCode = """
instr %s                                    
    iAmp             = ampdb(p4) / 2    ; amplitude, scaled for two sources
    iFreq            = cpspch(p5)
    
    iPan             = p6    
    ipluckamp    = p7                    ; pcent total amp, 1=dB amp as in p4
    ipluckdur    = p8 * p3           ; pcent total dur, 1=entire dur of note
    ipluckoff    = p3 - ipluckdur
    
    ifmamp       = p9                     ; pcent total amp, 1=dB amp as in p4
    ifmrise      = p10 * p3           ; pcent total dur, 1=entire dur of note
    ifmdec       = p11 * p3           ; pcent total duration
    ifmoff       = p3 - (ifmrise + ifmdec)
    index            = p12
    ivibdepth    = p13
    ivibrate         = p14
    iformantamp  = p15              ; pcent total amp, 1=dB amp as in p4
    iformantrise = p16 * p3         ; pcent total dur, 1=entire dur of note
    iformantdec  = p3 - iformantrise
    
    kpluck       linseg   ipluckamp, ipluckdur, 0, ipluckoff, 0
    apluck1      pluck    iAmp, iFreq, iFreq, 0, 1
    apluck2      pluck    iAmp, iFreq * 1.003, iFreq * 1.003, 0, 1
    apluck       =            kpluck * (apluck1+apluck2)
    
    kfm          linseg   0, ifmrise, ifmamp, ifmdec, 0, ifmoff, 0
    kndx             =            kfm * index
    afm1             foscil   iAmp, iFreq, 1, 7, kndx, 1
    afm2             foscil   iAmp, iFreq * 1.003, 1.003, 2.003, kndx, 1
    afm          =            kfm * (afm1+afm2)
    
    kfrmnt       linseg   0, iformantrise, iformantamp, iformantdec, 0
    kvib             oscil    ivibdepth, ivibrate, 1
    afrmnt1      fof          iAmp, iFreq + kvib, 650, 0, 40, .003, .017, .007, 4, 1, 7, p3
    afrmnt2      fof          iAmp, (iFreq*1.001)+kvib*.009, 650, 0, 40, .003,.017,.007, 10,1,7,p3
    aformnt      =            kfrmnt * (afrmnt1+afrmnt2)

    aMixSig          = (apluck + afm + aformnt)
""" % str(self.instNo)

        self.scoSample = """
                                     ;values b/n 0 & 1.
                                     ;p6      p7      p8    p9    p10       p11  p12     p13     p14    p15 p16     
;ins st   dr     amp     PCH      pan     plkmp plkdr fmp fmris fmdec indx vbdp vbrt frmp fris
i13 52.11  4     80 7.09    .5       .8 .3    .7     .2 .35  8    1 5    3    .5
i13 53.44  4     80 7.09    .5       .8 .4    .7     .35    .35  7    1 6    3    .7
i13 54.77  6     80 7.09    .5       .8 .3    .7     .2 .4       6    1 4    3    .6
i13 56.00  8     80 7.09    .5       .8 .3    .7     .2 .4       6    1 5    3    .6
"""

#-----------------------------------------------------------------||||||||||||--
class Inst82(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 82
        self.name = 'pluckUnitEnvelope'
        self.info = 'A single pluck with a unit envelope and variable low pass filter.'
        self.auxNo = 9
        self.postMapAmp = (0, 84, 'linear') # amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'pluck function table (integer)', 
          'pmtr8'   : 'pluck method (integers 1 through 6)', 
          'pmtr9'   : 'pluck parameter 1 (0-1)', 
          'pmtr10'  : 'pluck parameter 2 (0-1)', 

          'pmtr11'  : 'sustain percent within unit interval',
          'pmtr12'  : 'sustain center within unit interval',
          'pmtr13'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr14'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr15'  : 'low-pass filter resonance between 1 and 500',
          }
        self.pmtrDefault = {
          'rhythmQ' : ('l', ((4, 1), (4, 2))) ,
          #'ampQ'    : ('cyclicGen', 'linearUp', 60, 70, 4) ,
          'pmtr7'   : ('c', 0), 
          'pmtr8'   : ('c', 3),   
          'pmtr9'   : ('c', .5), 
          'pmtr10'  : ('c', 1),   

          'pmtr11'  : ('c', .7), 
          'pmtr12'  : ('c', .01),    
          'pmtr13'  : ('c', 18000), 
          'pmtr14'  : ('c', 18000), 
          'pmtr15'  : ('c', .8),    
          } 
        self.orcCode = """
instr %s

    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    
    iFunction = p7 ; zero automatically generates random
    iMethod = p8    ; method 3 is simple drum; 4 is stretched; may not use pmtrs
    iParm1  = p9
    iParm2  = p10

    iSusPcent        = p11 ; time of sustain section w/n unit interval
    iSusCenterPcent = p12 ; center of sustain sections w/n unit interval
    iCutoffStart = p13
    iCutoffEnd = p14
    kq = p15
        
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right  
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    kFreq           linseg   iCutoffStart, iDur, iCutoffEnd

    ;ar pluck                kamp, kcps, icps, ifn, imeth, iparm1, iparm2
    ; assume that kcps and icps are the same; this seems correct
    aSig            pluck        iAmp, iFreq, iFreq, iFunction, iMethod, iParm1, iParm2
    aSig            lowpass2     aSig, kFreq, kq 
    aMixSig     = aSig

""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
# physical models here in the 90s; not all work yet
class Inst90(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 90
        self.name = 'modelSekere'
        self.info = 'Physical model of sekere percusion instrument.'
        self.auxNo = 4
        self.postMapAmp = (0, 1, 'linear') # most amps are in db
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
  'pmtr7'  : 'period of time over which all sound is stopped', 
  'pmtr8'  : 'the number of beads, teeth, bells, timbrels, etc',     
  'pmtr9'  : 'the damping factor, between 0 and 1', 
  'pmtr10' : 'amount of energy to add back into the system, between 0 and 1',     

          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .01), 
          'pmtr8'   : ('c', 64),    
          'pmtr9'   : ('c', .5), 
          'pmtr10'  : ('c', .1),    
          } 
          
          
# imaxshake (optional) -- amount of energy to add back into the system. The value should be in range 0 to 1.          
          
        self.orcCode = """
instr %s
    iDur     = p3
    iAmp     = ampdb(p4)
    iFreq     = cpspch(p5)
    iPan     = p6
    
    idettack     = p7
    inum = p8
    idamp = p9
    imaxshake = p10
    
    
    a1        sekere iAmp, idettack, inum, idamp, imaxshake
    
    ;master mix

    aMixSig          = a1
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
# this only works if file name is given as a number
# cant get it to accept a complete path

class Inst100(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 100
        self.name = 'phaseVocodeRead'
        self.info = 'A simple phase voice reader instrument.'
        self.auxNo = 5
        # dont know what amp scaling is necessary here
        self.postMapAmp = (0, 74, 'linear') # most amps are in db

        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
                      'pmtr7'   : 'pvc analysis file to use',
                     } # holds discription, preset for each pmtr in a dictionary
        self.pmtrDefault = {
          #'ampQ'    : ('cyclicGen', 'linearDown', 2.00, 9.00, 0.25),
          #'pmtr7'   : ('analysisSelect', ('harmonica.1',)),
          'pmtr7'   : ('constant', 1),
          #'pmtr7'   : ('constant', '"/Volumes/xdisc/_scratch/pvoc.1"'),
          'pmtr8'   : ('sl', '3|5|13|19', 1, 60, 'integer', 'rw'),
          'pmtr9'   : ('constant', 0.5),
          'pmtr10'  : ('constant', .001),
          'pmtr11'  : ('constant', .001),
          }

# ; p4 is max amp (in db)
# ; p7 is file no
# ; p8 is bin
# ; p9 is start time in analysis
# ; p10 is fade in time in sec.
# ; p11 is fade out time in sec.

        self.orcCode = """
instr %s
    iDur    = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6
    
    ktime             line   p9, iDur, p9 + iDur 
    kenv              linen  iAmp, p10, iDur, p11
    kFreq, kAmp   pvread     ktime, p7, p8 
    aSig              oscili     kAmp, kFreq, 1
    
    aMixSig =     aSig * kenv
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
# 8 ch

class Inst140(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 140
        self.name = 'vocodeSineOctScale'
        self.info = 'An eight channel vocoder with scaled mapping and a sine generator.'
        self.auxNo = 13
        self.postMapAmp = (0, 10, 'linear') # amps from experiment
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',
          
          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',       

          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 50), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 500),
          'pmtr15'  : ('c', 1.333333333333),

          'pmtr16'  : ('c', 500),
          'pmtr17'  : ('c', 1.333333333333),

          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 2000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters; dont need to scale by 2 here
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; filter noise at fq, scale by analysis
    aGen01      poscil  aAmpCh01, iGeneratorCf01, iTable
    aGen02      poscil  aAmpCh02, iGeneratorCf02, iTable
    aGen03      poscil  aAmpCh03, iGeneratorCf03, iTable
    aGen04      poscil  aAmpCh04, iGeneratorCf04, iTable
    aGen05      poscil  aAmpCh05, iGeneratorCf05, iTable
    aGen06      poscil  aAmpCh06, iGeneratorCf06, iTable
    aGen07      poscil  aAmpCh07, iGeneratorCf07, iTable
    aGen08      poscil  aAmpCh08, iGeneratorCf08, iTable

    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  

    ; scale by macro envelope        
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
# 8 ch
class Inst141(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 141
        self.name = 'vocodeSineOctScaleRemap'
        self.info = 'An eight channel vocoder with variable remapping and a sine generator.'
        self.auxNo = 29
        self.postMapAmp = (0, 10, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',         

          'pmtr18'  : 'generator 1 channel frequency source (1-8)',
          'pmtr19'  : 'generator 2 channel frequency source (1-8)',           
          'pmtr20'  : 'generator 3 channel frequency source (1-8)',
          'pmtr21'  : 'generator 4 channel frequency source (1-8)',           
          'pmtr22'  : 'generator 5 channel frequency source (1-8)',
          'pmtr23'  : 'generator 6 channel frequency source (1-8)',           
          'pmtr24'  : 'generator 7 channel frequency source (1-8)',
          'pmtr25'  : 'generator 8 channel frequency source (1-8)',           

          'pmtr26'  : 'generator 1 post scale (0-1)',
          'pmtr27'  : 'generator 2 post scale (0-1)',           
          'pmtr28'  : 'generator 3 post scale (0-1)',
          'pmtr29'  : 'generator 4 post scale (0-1)',           
          'pmtr30'  : 'generator 5 post scale (0-1)',
          'pmtr31'  : 'generator 6 post scale (0-1)',           
          'pmtr32'  : 'generator 7 post scale (0-1)',
          'pmtr33'  : 'generator 8 post scale (0-1)',           

          'pmtr34'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr35'  : 'low-pass filter end cutoff frequency in Hz',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 40), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 400),
          'pmtr15'  : ('c', 1.33333333333),

          'pmtr16'  : ('c', 100),
          'pmtr17'  : ('c', 1.6666666666),
          
          'pmtr18'  : ('c', 1),
          'pmtr19'  : ('c', 2),
          'pmtr20'  : ('c', 3),
          'pmtr21'  : ('c', 4),
          'pmtr22'  : ('c', 5),
          'pmtr23'  : ('c', 6),
          'pmtr24'  : ('c', 7),
          'pmtr25'  : ('c', 8),
          
          'pmtr26'  : ('c', 1),
          'pmtr27'  : ('c', 1),
          'pmtr28'  : ('c', 1),
          'pmtr29'  : ('c', 1),
          'pmtr30'  : ('c', 1),
          'pmtr31'  : ('c', 1),
          'pmtr32'  : ('c', 1),
          'pmtr33'  : ('c', 1),
          
          'pmtr34'  : ('c', 100),
          'pmtr35'  : ('c', 4000),
          }
          
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)
    
    ; integer values tt determine which channel goes where
    iGeneratorSrcCh01 = p18 - 1  ; values in src channel become exponents
    iGeneratorSrcCh02 = p19 - 1
    iGeneratorSrcCh03 = p20 - 1
    iGeneratorSrcCh04 = p21 - 1
    iGeneratorSrcCh05 = p22 - 1 
    iGeneratorSrcCh06 = p23 - 1
    iGeneratorSrcCh07 = p24 - 1
    iGeneratorSrcCh08 = p25 - 1

    ; can re-scale generator mapping, produce normal fqs prior to remap
    ; amp will stay the same, based on order number; changes fqs applied
    ; with number
    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh01)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh02)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh03)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh04)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh05)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh06)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh07)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ iGeneratorSrcCh08)

    ; making these k-rate for envelope scaling
    kGeneratorPost01 = p26
    kGeneratorPost02 = p27
    kGeneratorPost03 = p28
    kGeneratorPost04 = p29
    kGeneratorPost05 = p30
    kGeneratorPost06 = p31
    kGeneratorPost07 = p32
    kGeneratorPost08 = p33
  
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p34, iDur, p35
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create noise source to be filtered
    aNoise      random  -1, 1

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0

    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; filter noise at fq, scale by analysis
    aGen01      poscil      aAmpCh01, iGeneratorCf01, iTable
    aGen01      = aGen01 * kGeneratorPost01
    aGen02      poscil      aAmpCh02, iGeneratorCf02, iTable
    aGen02      = aGen02 * kGeneratorPost02
    aGen03      poscil      aAmpCh03, iGeneratorCf03, iTable
    aGen03      = aGen03 * kGeneratorPost03
    aGen04      poscil      aAmpCh04, iGeneratorCf04, iTable
    aGen04      = aGen04 * kGeneratorPost04
    
    aGen05      poscil      aAmpCh05, iGeneratorCf05, iTable
    aGen05      = aGen05 * kGeneratorPost05
    aGen06      poscil      aAmpCh06, iGeneratorCf06, iTable
    aGen06      = aGen06 * kGeneratorPost06
    aGen07      poscil      aAmpCh07, iGeneratorCf07, iTable
    aGen07      = aGen07 * kGeneratorPost07
    aGen08      poscil      aAmpCh08, iGeneratorCf08, iTable
    aGen08      = aGen08 * kGeneratorPost08

    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
# 16 ch; 141 saved for 8 ch remap sine version

class Inst142(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 142
        self.name = 'vocodeSineBiOctScale'
        self.info = 'A sixteen channel vocoder with scaled mapping and a sine generator.'
        self.auxNo = 13
        self.postMapAmp = (0, 10, 'linear') # amps from experiment
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',       

          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 10), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 200),
          'pmtr15'  : ('c', 1.333333333333),

          'pmtr16'  : ('c', 200),
          'pmtr17'  : ('c', 1.333333333333),

          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 12000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iAnalysisCf09 = p14 * (iAnalysisFqScalar ^ 8)
    iAnalysisCf10 = p14 * (iAnalysisFqScalar ^ 9)
    iAnalysisCf11 = p14 * (iAnalysisFqScalar ^ 10)
    iAnalysisCf12 = p14 * (iAnalysisFqScalar ^ 11)
    iAnalysisCf13 = p14 * (iAnalysisFqScalar ^ 12)
    iAnalysisCf14 = p14 * (iAnalysisFqScalar ^ 13)
    iAnalysisCf15 = p14 * (iAnalysisFqScalar ^ 14)
    iAnalysisCf16 = p14 * (iAnalysisFqScalar ^ 15)

    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)

    iGeneratorCf09 = p16 * (iGeneratorFqScalar ^ 8)
    iGeneratorCf10 = p16 * (iGeneratorFqScalar ^ 9)
    iGeneratorCf11 = p16 * (iGeneratorFqScalar ^ 10)
    iGeneratorCf12 = p16 * (iGeneratorFqScalar ^ 11)
    iGeneratorCf13 = p16 * (iGeneratorFqScalar ^ 12)
    iGeneratorCf14 = p16 * (iGeneratorFqScalar ^ 13)
    iGeneratorCf15 = p16 * (iGeneratorFqScalar ^ 14)
    iGeneratorCf16 = p16 * (iGeneratorFqScalar ^ 15)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters; dont need to scale by 2 here
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf


    aAmpCh09        butterbp     aSrc, iAnalysisCf09, iAnalysisQ
    aAmpCh09        = abs(aAmpCh09)
    aAmpCh09        butterlp     aAmpCh09, iAnalysisCutoff
    aAmpCh09        tone         aAmpCh09, iAnalysisCutoff   ; one pole lpf

    aAmpCh10        butterbp     aSrc, iAnalysisCf10, iAnalysisQ
    aAmpCh10        = abs(aAmpCh10)
    aAmpCh10        butterlp     aAmpCh10, iAnalysisCutoff
    aAmpCh10        tone         aAmpCh10, iAnalysisCutoff   ; one pole lpf

    aAmpCh11        butterbp     aSrc, iAnalysisCf11, iAnalysisQ
    aAmpCh11        = abs(aAmpCh11)
    aAmpCh11        butterlp     aAmpCh11, iAnalysisCutoff
    aAmpCh11        tone         aAmpCh11, iAnalysisCutoff   ; one pole lpf

    aAmpCh12        butterbp     aSrc, iAnalysisCf12, iAnalysisQ
    aAmpCh12        = abs(aAmpCh12)
    aAmpCh12        butterlp     aAmpCh12, iAnalysisCutoff
    aAmpCh12        tone         aAmpCh12, iAnalysisCutoff   ; one pole lpf

    aAmpCh13        butterbp     aSrc, iAnalysisCf13, iAnalysisQ
    aAmpCh13        = abs(aAmpCh13)
    aAmpCh13        butterlp     aAmpCh13, iAnalysisCutoff
    aAmpCh13        tone         aAmpCh13, iAnalysisCutoff   ; one pole lpf

    aAmpCh14        butterbp     aSrc, iAnalysisCf14, iAnalysisQ
    aAmpCh14        = abs(aAmpCh14)
    aAmpCh14        butterlp     aAmpCh14, iAnalysisCutoff
    aAmpCh14        tone         aAmpCh14, iAnalysisCutoff   ; one pole lpf

    aAmpCh15        butterbp     aSrc, iAnalysisCf15, iAnalysisQ
    aAmpCh15        = abs(aAmpCh15)
    aAmpCh15        butterlp     aAmpCh15, iAnalysisCutoff
    aAmpCh15        tone         aAmpCh15, iAnalysisCutoff   ; one pole lpf

    aAmpCh16        butterbp     aSrc, iAnalysisCf16, iAnalysisQ
    aAmpCh16        = abs(aAmpCh16)
    aAmpCh16        butterlp     aAmpCh16, iAnalysisCutoff
    aAmpCh16        tone         aAmpCh16, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; filter noise at fq, scale by analysis
    aGen01      poscil  aAmpCh01, iGeneratorCf01, iTable
    aGen02      poscil  aAmpCh02, iGeneratorCf02, iTable
    aGen03      poscil  aAmpCh03, iGeneratorCf03, iTable
    aGen04      poscil  aAmpCh04, iGeneratorCf04, iTable
    aGen05      poscil  aAmpCh05, iGeneratorCf05, iTable
    aGen06      poscil  aAmpCh06, iGeneratorCf06, iTable
    aGen07      poscil  aAmpCh07, iGeneratorCf07, iTable
    aGen08      poscil  aAmpCh08, iGeneratorCf08, iTable

    aGen09      poscil  aAmpCh09, iGeneratorCf09, iTable
    aGen10      poscil  aAmpCh10, iGeneratorCf10, iTable
    aGen11      poscil  aAmpCh11, iGeneratorCf11, iTable
    aGen12      poscil  aAmpCh12, iGeneratorCf12, iTable
    aGen13      poscil  aAmpCh13, iGeneratorCf13, iTable
    aGen14      poscil  aAmpCh14, iGeneratorCf14, iTable
    aGen15      poscil  aAmpCh15, iGeneratorCf15, iTable
    aGen16      poscil  aAmpCh16, iGeneratorCf16, iTable

    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08 + aGen09 + aGen10 + aGen11 + aGen12 + aGen13 + aGen14 + aGen15 + aGen16)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  

    ; scale by macro envelope        
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
# 24 ch

class Inst143(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 143
        self.name = 'vocodeSineTriOctScale'
        self.info = 'A twenty four channel vocoder with scaled mapping and a sine generator.'
        self.auxNo = 13
        self.postMapAmp = (0, 10, 'linear') # amps from experiment
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',       

          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 10), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 80),
          'pmtr15'  : ('c', 1.2),

          'pmtr16'  : ('c', 80),
          'pmtr17'  : ('c', 1.2),

          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 20000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iAnalysisCf09 = p14 * (iAnalysisFqScalar ^ 8)
    iAnalysisCf10 = p14 * (iAnalysisFqScalar ^ 9)
    iAnalysisCf11 = p14 * (iAnalysisFqScalar ^ 10)
    iAnalysisCf12 = p14 * (iAnalysisFqScalar ^ 11)
    iAnalysisCf13 = p14 * (iAnalysisFqScalar ^ 12)
    iAnalysisCf14 = p14 * (iAnalysisFqScalar ^ 13)
    iAnalysisCf15 = p14 * (iAnalysisFqScalar ^ 14)
    iAnalysisCf16 = p14 * (iAnalysisFqScalar ^ 15)
    
    iAnalysisCf17 = p14 * (iAnalysisFqScalar ^ 16)
    iAnalysisCf18 = p14 * (iAnalysisFqScalar ^ 17)
    iAnalysisCf19 = p14 * (iAnalysisFqScalar ^ 18)
    iAnalysisCf20 = p14 * (iAnalysisFqScalar ^ 19)
    iAnalysisCf21 = p14 * (iAnalysisFqScalar ^ 20)
    iAnalysisCf22 = p14 * (iAnalysisFqScalar ^ 21)
    iAnalysisCf23 = p14 * (iAnalysisFqScalar ^ 22)
    iAnalysisCf24 = p14 * (iAnalysisFqScalar ^ 23)


    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)

    iGeneratorCf09 = p16 * (iGeneratorFqScalar ^ 8)
    iGeneratorCf10 = p16 * (iGeneratorFqScalar ^ 9)
    iGeneratorCf11 = p16 * (iGeneratorFqScalar ^ 10)
    iGeneratorCf12 = p16 * (iGeneratorFqScalar ^ 11)
    iGeneratorCf13 = p16 * (iGeneratorFqScalar ^ 12)
    iGeneratorCf14 = p16 * (iGeneratorFqScalar ^ 13)
    iGeneratorCf15 = p16 * (iGeneratorFqScalar ^ 14)
    iGeneratorCf16 = p16 * (iGeneratorFqScalar ^ 15)

    iGeneratorCf17 = p16 * (iGeneratorFqScalar ^ 16)
    iGeneratorCf18 = p16 * (iGeneratorFqScalar ^ 17)
    iGeneratorCf19 = p16 * (iGeneratorFqScalar ^ 18)
    iGeneratorCf20 = p16 * (iGeneratorFqScalar ^ 19)
    iGeneratorCf21 = p16 * (iGeneratorFqScalar ^ 20)
    iGeneratorCf22 = p16 * (iGeneratorFqScalar ^ 21)
    iGeneratorCf23 = p16 * (iGeneratorFqScalar ^ 22)
    iGeneratorCf24 = p16 * (iGeneratorFqScalar ^ 23)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            soundin  iSamplePath, iSkiptime
    
    ; isolate channels by filters; dont need to scale by 2 here
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf


    aAmpCh09        butterbp     aSrc, iAnalysisCf09, iAnalysisQ
    aAmpCh09        = abs(aAmpCh09)
    aAmpCh09        butterlp     aAmpCh09, iAnalysisCutoff
    aAmpCh09        tone         aAmpCh09, iAnalysisCutoff   ; one pole lpf

    aAmpCh10        butterbp     aSrc, iAnalysisCf10, iAnalysisQ
    aAmpCh10        = abs(aAmpCh10)
    aAmpCh10        butterlp     aAmpCh10, iAnalysisCutoff
    aAmpCh10        tone         aAmpCh10, iAnalysisCutoff   ; one pole lpf

    aAmpCh11        butterbp     aSrc, iAnalysisCf11, iAnalysisQ
    aAmpCh11        = abs(aAmpCh11)
    aAmpCh11        butterlp     aAmpCh11, iAnalysisCutoff
    aAmpCh11        tone         aAmpCh11, iAnalysisCutoff   ; one pole lpf

    aAmpCh12        butterbp     aSrc, iAnalysisCf12, iAnalysisQ
    aAmpCh12        = abs(aAmpCh12)
    aAmpCh12        butterlp     aAmpCh12, iAnalysisCutoff
    aAmpCh12        tone         aAmpCh12, iAnalysisCutoff   ; one pole lpf

    aAmpCh13        butterbp     aSrc, iAnalysisCf13, iAnalysisQ
    aAmpCh13        = abs(aAmpCh13)
    aAmpCh13        butterlp     aAmpCh13, iAnalysisCutoff
    aAmpCh13        tone         aAmpCh13, iAnalysisCutoff   ; one pole lpf

    aAmpCh14        butterbp     aSrc, iAnalysisCf14, iAnalysisQ
    aAmpCh14        = abs(aAmpCh14)
    aAmpCh14        butterlp     aAmpCh14, iAnalysisCutoff
    aAmpCh14        tone         aAmpCh14, iAnalysisCutoff   ; one pole lpf

    aAmpCh15        butterbp     aSrc, iAnalysisCf15, iAnalysisQ
    aAmpCh15        = abs(aAmpCh15)
    aAmpCh15        butterlp     aAmpCh15, iAnalysisCutoff
    aAmpCh15        tone         aAmpCh15, iAnalysisCutoff   ; one pole lpf

    aAmpCh16        butterbp     aSrc, iAnalysisCf16, iAnalysisQ
    aAmpCh16        = abs(aAmpCh16)
    aAmpCh16        butterlp     aAmpCh16, iAnalysisCutoff
    aAmpCh16        tone         aAmpCh16, iAnalysisCutoff   ; one pole lpf


    aAmpCh17        butterbp     aSrc, iAnalysisCf17, iAnalysisQ
    aAmpCh17        = abs(aAmpCh17)
    aAmpCh17        butterlp     aAmpCh17, iAnalysisCutoff
    aAmpCh17        tone         aAmpCh17, iAnalysisCutoff   ; one pole lpf

    aAmpCh18        butterbp     aSrc, iAnalysisCf18, iAnalysisQ
    aAmpCh18        = abs(aAmpCh18)
    aAmpCh18        butterlp     aAmpCh18, iAnalysisCutoff
    aAmpCh18        tone         aAmpCh18, iAnalysisCutoff   ; one pole lpf

    aAmpCh19        butterbp     aSrc, iAnalysisCf19, iAnalysisQ
    aAmpCh19        = abs(aAmpCh19)
    aAmpCh19        butterlp     aAmpCh19, iAnalysisCutoff
    aAmpCh19        tone         aAmpCh19, iAnalysisCutoff   ; one pole lpf

    aAmpCh20        butterbp     aSrc, iAnalysisCf20, iAnalysisQ
    aAmpCh20        = abs(aAmpCh20)
    aAmpCh20        butterlp     aAmpCh20, iAnalysisCutoff
    aAmpCh20        tone         aAmpCh20, iAnalysisCutoff   ; one pole lpf

    aAmpCh21        butterbp     aSrc, iAnalysisCf21, iAnalysisQ
    aAmpCh21        = abs(aAmpCh21)
    aAmpCh21        butterlp     aAmpCh21, iAnalysisCutoff
    aAmpCh21        tone         aAmpCh21, iAnalysisCutoff   ; one pole lpf

    aAmpCh22        butterbp     aSrc, iAnalysisCf22, iAnalysisQ
    aAmpCh22        = abs(aAmpCh22)
    aAmpCh22        butterlp     aAmpCh22, iAnalysisCutoff
    aAmpCh22        tone         aAmpCh22, iAnalysisCutoff   ; one pole lpf

    aAmpCh23        butterbp     aSrc, iAnalysisCf23, iAnalysisQ
    aAmpCh23        = abs(aAmpCh23)
    aAmpCh23        butterlp     aAmpCh23, iAnalysisCutoff
    aAmpCh23        tone         aAmpCh23, iAnalysisCutoff   ; one pole lpf

    aAmpCh24        butterbp     aSrc, iAnalysisCf24, iAnalysisQ
    aAmpCh24        = abs(aAmpCh24)
    aAmpCh24        butterlp     aAmpCh24, iAnalysisCutoff
    aAmpCh24        tone         aAmpCh24, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; filter noise at fq, scale by analysis
    aGen01      poscil  aAmpCh01, iGeneratorCf01, iTable
    aGen02      poscil  aAmpCh02, iGeneratorCf02, iTable
    aGen03      poscil  aAmpCh03, iGeneratorCf03, iTable
    aGen04      poscil  aAmpCh04, iGeneratorCf04, iTable
    aGen05      poscil  aAmpCh05, iGeneratorCf05, iTable
    aGen06      poscil  aAmpCh06, iGeneratorCf06, iTable
    aGen07      poscil  aAmpCh07, iGeneratorCf07, iTable
    aGen08      poscil  aAmpCh08, iGeneratorCf08, iTable

    aGen09      poscil  aAmpCh09, iGeneratorCf09, iTable
    aGen10      poscil  aAmpCh10, iGeneratorCf10, iTable
    aGen11      poscil  aAmpCh11, iGeneratorCf11, iTable
    aGen12      poscil  aAmpCh12, iGeneratorCf12, iTable
    aGen13      poscil  aAmpCh13, iGeneratorCf13, iTable
    aGen14      poscil  aAmpCh14, iGeneratorCf14, iTable
    aGen15      poscil  aAmpCh15, iGeneratorCf15, iTable
    aGen16      poscil  aAmpCh16, iGeneratorCf16, iTable

    aGen17      poscil  aAmpCh17, iGeneratorCf17, iTable
    aGen18      poscil  aAmpCh18, iGeneratorCf18, iTable
    aGen19      poscil  aAmpCh19, iGeneratorCf19, iTable
    aGen20      poscil  aAmpCh20, iGeneratorCf20, iTable
    aGen21      poscil  aAmpCh21, iGeneratorCf21, iTable
    aGen22      poscil  aAmpCh22, iGeneratorCf22, iTable
    aGen23      poscil  aAmpCh23, iGeneratorCf23, iTable
    aGen24      poscil  aAmpCh24, iGeneratorCf24, iTable

    ; mix all channels
    aSubA           = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)
    aSubB           = (aGen09 + aGen10 + aGen11 + aGen12 + aGen13 + aGen14 + aGen15 + aGen16)
    aSubC           = (aGen17 + aGen18 + aGen19 + aGen20 + aGen21 + aGen22 + aGen23 + aGen24)
    aSig            = aSubA + aSubB + aSubC

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  

    ; scale by macro envelope        
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
# 32 ch

class Inst144(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 144
        self.name = 'vocodeSineQuadOctScale'
        self.info = 'A thirty two channel vocoder with scaled mapping and a sine generator.'
        self.auxNo = 13
        self.postMapAmp = (0, 10, 'linear') # amps from experiment
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',       

          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 10), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 40),
          'pmtr15'  : ('c', 1.2),

          'pmtr16'  : ('c', 40),
          'pmtr17'  : ('c', 1.2),

          'pmtr18'  : ('c', 2000),
          'pmtr19'  : ('c', 20000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iAnalysisCf09 = p14 * (iAnalysisFqScalar ^ 8)
    iAnalysisCf10 = p14 * (iAnalysisFqScalar ^ 9)
    iAnalysisCf11 = p14 * (iAnalysisFqScalar ^ 10)
    iAnalysisCf12 = p14 * (iAnalysisFqScalar ^ 11)
    iAnalysisCf13 = p14 * (iAnalysisFqScalar ^ 12)
    iAnalysisCf14 = p14 * (iAnalysisFqScalar ^ 13)
    iAnalysisCf15 = p14 * (iAnalysisFqScalar ^ 14)
    iAnalysisCf16 = p14 * (iAnalysisFqScalar ^ 15)
    
    iAnalysisCf17 = p14 * (iAnalysisFqScalar ^ 16)
    iAnalysisCf18 = p14 * (iAnalysisFqScalar ^ 17)
    iAnalysisCf19 = p14 * (iAnalysisFqScalar ^ 18)
    iAnalysisCf20 = p14 * (iAnalysisFqScalar ^ 19)
    iAnalysisCf21 = p14 * (iAnalysisFqScalar ^ 20)
    iAnalysisCf22 = p14 * (iAnalysisFqScalar ^ 21)
    iAnalysisCf23 = p14 * (iAnalysisFqScalar ^ 22)
    iAnalysisCf24 = p14 * (iAnalysisFqScalar ^ 23)
    
    iAnalysisCf25 = p14 * (iAnalysisFqScalar ^ 24)
    iAnalysisCf26 = p14 * (iAnalysisFqScalar ^ 25)
    iAnalysisCf27 = p14 * (iAnalysisFqScalar ^ 26)
    iAnalysisCf28 = p14 * (iAnalysisFqScalar ^ 27)
    iAnalysisCf29 = p14 * (iAnalysisFqScalar ^ 28)
    iAnalysisCf30 = p14 * (iAnalysisFqScalar ^ 29)
    iAnalysisCf31 = p14 * (iAnalysisFqScalar ^ 30)
    iAnalysisCf32 = p14 * (iAnalysisFqScalar ^ 31)


    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)

    iGeneratorCf09 = p16 * (iGeneratorFqScalar ^ 8)
    iGeneratorCf10 = p16 * (iGeneratorFqScalar ^ 9)
    iGeneratorCf11 = p16 * (iGeneratorFqScalar ^ 10)
    iGeneratorCf12 = p16 * (iGeneratorFqScalar ^ 11)
    iGeneratorCf13 = p16 * (iGeneratorFqScalar ^ 12)
    iGeneratorCf14 = p16 * (iGeneratorFqScalar ^ 13)
    iGeneratorCf15 = p16 * (iGeneratorFqScalar ^ 14)
    iGeneratorCf16 = p16 * (iGeneratorFqScalar ^ 15)

    iGeneratorCf17 = p16 * (iGeneratorFqScalar ^ 16)
    iGeneratorCf18 = p16 * (iGeneratorFqScalar ^ 17)
    iGeneratorCf19 = p16 * (iGeneratorFqScalar ^ 18)
    iGeneratorCf20 = p16 * (iGeneratorFqScalar ^ 19)
    iGeneratorCf21 = p16 * (iGeneratorFqScalar ^ 20)
    iGeneratorCf22 = p16 * (iGeneratorFqScalar ^ 21)
    iGeneratorCf23 = p16 * (iGeneratorFqScalar ^ 22)
    iGeneratorCf24 = p16 * (iGeneratorFqScalar ^ 23)

    iGeneratorCf25 = p16 * (iGeneratorFqScalar ^ 24)
    iGeneratorCf26 = p16 * (iGeneratorFqScalar ^ 25)
    iGeneratorCf27 = p16 * (iGeneratorFqScalar ^ 26)
    iGeneratorCf28 = p16 * (iGeneratorFqScalar ^ 27)
    iGeneratorCf29 = p16 * (iGeneratorFqScalar ^ 28)
    iGeneratorCf30 = p16 * (iGeneratorFqScalar ^ 29)
    iGeneratorCf31 = p16 * (iGeneratorFqScalar ^ 30)
    iGeneratorCf32 = p16 * (iGeneratorFqScalar ^ 31)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters; dont need to scale by 2 here
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf


    aAmpCh09        butterbp     aSrc, iAnalysisCf09, iAnalysisQ
    aAmpCh09        = abs(aAmpCh09)
    aAmpCh09        butterlp     aAmpCh09, iAnalysisCutoff
    aAmpCh09        tone         aAmpCh09, iAnalysisCutoff   ; one pole lpf

    aAmpCh10        butterbp     aSrc, iAnalysisCf10, iAnalysisQ
    aAmpCh10        = abs(aAmpCh10)
    aAmpCh10        butterlp     aAmpCh10, iAnalysisCutoff
    aAmpCh10        tone         aAmpCh10, iAnalysisCutoff   ; one pole lpf

    aAmpCh11        butterbp     aSrc, iAnalysisCf11, iAnalysisQ
    aAmpCh11        = abs(aAmpCh11)
    aAmpCh11        butterlp     aAmpCh11, iAnalysisCutoff
    aAmpCh11        tone         aAmpCh11, iAnalysisCutoff   ; one pole lpf

    aAmpCh12        butterbp     aSrc, iAnalysisCf12, iAnalysisQ
    aAmpCh12        = abs(aAmpCh12)
    aAmpCh12        butterlp     aAmpCh12, iAnalysisCutoff
    aAmpCh12        tone         aAmpCh12, iAnalysisCutoff   ; one pole lpf

    aAmpCh13        butterbp     aSrc, iAnalysisCf13, iAnalysisQ
    aAmpCh13        = abs(aAmpCh13)
    aAmpCh13        butterlp     aAmpCh13, iAnalysisCutoff
    aAmpCh13        tone         aAmpCh13, iAnalysisCutoff   ; one pole lpf

    aAmpCh14        butterbp     aSrc, iAnalysisCf14, iAnalysisQ
    aAmpCh14        = abs(aAmpCh14)
    aAmpCh14        butterlp     aAmpCh14, iAnalysisCutoff
    aAmpCh14        tone         aAmpCh14, iAnalysisCutoff   ; one pole lpf

    aAmpCh15        butterbp     aSrc, iAnalysisCf15, iAnalysisQ
    aAmpCh15        = abs(aAmpCh15)
    aAmpCh15        butterlp     aAmpCh15, iAnalysisCutoff
    aAmpCh15        tone         aAmpCh15, iAnalysisCutoff   ; one pole lpf

    aAmpCh16        butterbp     aSrc, iAnalysisCf16, iAnalysisQ
    aAmpCh16        = abs(aAmpCh16)
    aAmpCh16        butterlp     aAmpCh16, iAnalysisCutoff
    aAmpCh16        tone         aAmpCh16, iAnalysisCutoff   ; one pole lpf


    aAmpCh17        butterbp     aSrc, iAnalysisCf17, iAnalysisQ
    aAmpCh17        = abs(aAmpCh17)
    aAmpCh17        butterlp     aAmpCh17, iAnalysisCutoff
    aAmpCh17        tone         aAmpCh17, iAnalysisCutoff   ; one pole lpf

    aAmpCh18        butterbp     aSrc, iAnalysisCf18, iAnalysisQ
    aAmpCh18        = abs(aAmpCh18)
    aAmpCh18        butterlp     aAmpCh18, iAnalysisCutoff
    aAmpCh18        tone         aAmpCh18, iAnalysisCutoff   ; one pole lpf

    aAmpCh19        butterbp     aSrc, iAnalysisCf19, iAnalysisQ
    aAmpCh19        = abs(aAmpCh19)
    aAmpCh19        butterlp     aAmpCh19, iAnalysisCutoff
    aAmpCh19        tone         aAmpCh19, iAnalysisCutoff   ; one pole lpf

    aAmpCh20        butterbp     aSrc, iAnalysisCf20, iAnalysisQ
    aAmpCh20        = abs(aAmpCh20)
    aAmpCh20        butterlp     aAmpCh20, iAnalysisCutoff
    aAmpCh20        tone         aAmpCh20, iAnalysisCutoff   ; one pole lpf

    aAmpCh21        butterbp     aSrc, iAnalysisCf21, iAnalysisQ
    aAmpCh21        = abs(aAmpCh21)
    aAmpCh21        butterlp     aAmpCh21, iAnalysisCutoff
    aAmpCh21        tone         aAmpCh21, iAnalysisCutoff   ; one pole lpf

    aAmpCh22        butterbp     aSrc, iAnalysisCf22, iAnalysisQ
    aAmpCh22        = abs(aAmpCh22)
    aAmpCh22        butterlp     aAmpCh22, iAnalysisCutoff
    aAmpCh22        tone         aAmpCh22, iAnalysisCutoff   ; one pole lpf

    aAmpCh23        butterbp     aSrc, iAnalysisCf23, iAnalysisQ
    aAmpCh23        = abs(aAmpCh23)
    aAmpCh23        butterlp     aAmpCh23, iAnalysisCutoff
    aAmpCh23        tone         aAmpCh23, iAnalysisCutoff   ; one pole lpf

    aAmpCh24        butterbp     aSrc, iAnalysisCf24, iAnalysisQ
    aAmpCh24        = abs(aAmpCh24)
    aAmpCh24        butterlp     aAmpCh24, iAnalysisCutoff
    aAmpCh24        tone         aAmpCh24, iAnalysisCutoff   ; one pole lpf


    aAmpCh25        butterbp     aSrc, iAnalysisCf25, iAnalysisQ
    aAmpCh25        = abs(aAmpCh25)
    aAmpCh25        butterlp     aAmpCh25, iAnalysisCutoff
    aAmpCh25        tone         aAmpCh25, iAnalysisCutoff   ; one pole lpf

    aAmpCh26        butterbp     aSrc, iAnalysisCf26, iAnalysisQ
    aAmpCh26        = abs(aAmpCh26)
    aAmpCh26        butterlp     aAmpCh26, iAnalysisCutoff
    aAmpCh26        tone         aAmpCh26, iAnalysisCutoff   ; one pole lpf

    aAmpCh27        butterbp     aSrc, iAnalysisCf27, iAnalysisQ
    aAmpCh27        = abs(aAmpCh27)
    aAmpCh27        butterlp     aAmpCh27, iAnalysisCutoff
    aAmpCh27        tone         aAmpCh27, iAnalysisCutoff   ; one pole lpf

    aAmpCh28        butterbp     aSrc, iAnalysisCf28, iAnalysisQ
    aAmpCh28        = abs(aAmpCh28)
    aAmpCh28        butterlp     aAmpCh28, iAnalysisCutoff
    aAmpCh28        tone         aAmpCh28, iAnalysisCutoff   ; one pole lpf

    aAmpCh29        butterbp     aSrc, iAnalysisCf29, iAnalysisQ
    aAmpCh29        = abs(aAmpCh29)
    aAmpCh29        butterlp     aAmpCh29, iAnalysisCutoff
    aAmpCh29        tone         aAmpCh29, iAnalysisCutoff   ; one pole lpf

    aAmpCh30        butterbp     aSrc, iAnalysisCf30, iAnalysisQ
    aAmpCh30        = abs(aAmpCh30)
    aAmpCh30        butterlp     aAmpCh30, iAnalysisCutoff
    aAmpCh30        tone         aAmpCh30, iAnalysisCutoff   ; one pole lpf

    aAmpCh31        butterbp     aSrc, iAnalysisCf31, iAnalysisQ
    aAmpCh31        = abs(aAmpCh31)
    aAmpCh31        butterlp     aAmpCh31, iAnalysisCutoff
    aAmpCh31        tone         aAmpCh31, iAnalysisCutoff   ; one pole lpf

    aAmpCh32        butterbp     aSrc, iAnalysisCf32, iAnalysisQ
    aAmpCh32        = abs(aAmpCh32)
    aAmpCh32        butterlp     aAmpCh32, iAnalysisCutoff
    aAmpCh32        tone         aAmpCh32, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; filter noise at fq, scale by analysis
    aGen01      poscil  aAmpCh01, iGeneratorCf01, iTable
    aGen02      poscil  aAmpCh02, iGeneratorCf02, iTable
    aGen03      poscil  aAmpCh03, iGeneratorCf03, iTable
    aGen04      poscil  aAmpCh04, iGeneratorCf04, iTable
    aGen05      poscil  aAmpCh05, iGeneratorCf05, iTable
    aGen06      poscil  aAmpCh06, iGeneratorCf06, iTable
    aGen07      poscil  aAmpCh07, iGeneratorCf07, iTable
    aGen08      poscil  aAmpCh08, iGeneratorCf08, iTable

    aGen09      poscil  aAmpCh09, iGeneratorCf09, iTable
    aGen10      poscil  aAmpCh10, iGeneratorCf10, iTable
    aGen11      poscil  aAmpCh11, iGeneratorCf11, iTable
    aGen12      poscil  aAmpCh12, iGeneratorCf12, iTable
    aGen13      poscil  aAmpCh13, iGeneratorCf13, iTable
    aGen14      poscil  aAmpCh14, iGeneratorCf14, iTable
    aGen15      poscil  aAmpCh15, iGeneratorCf15, iTable
    aGen16      poscil  aAmpCh16, iGeneratorCf16, iTable

    aGen17      poscil  aAmpCh17, iGeneratorCf17, iTable
    aGen18      poscil  aAmpCh18, iGeneratorCf18, iTable
    aGen19      poscil  aAmpCh19, iGeneratorCf19, iTable
    aGen20      poscil  aAmpCh20, iGeneratorCf20, iTable
    aGen21      poscil  aAmpCh21, iGeneratorCf21, iTable
    aGen22      poscil  aAmpCh22, iGeneratorCf22, iTable
    aGen23      poscil  aAmpCh23, iGeneratorCf23, iTable
    aGen24      poscil  aAmpCh24, iGeneratorCf24, iTable

    aGen25      poscil  aAmpCh25, iGeneratorCf25, iTable
    aGen26      poscil  aAmpCh26, iGeneratorCf26, iTable
    aGen27      poscil  aAmpCh27, iGeneratorCf27, iTable
    aGen28      poscil  aAmpCh28, iGeneratorCf28, iTable
    aGen29      poscil  aAmpCh29, iGeneratorCf29, iTable
    aGen30      poscil  aAmpCh30, iGeneratorCf30, iTable
    aGen31      poscil  aAmpCh31, iGeneratorCf31, iTable
    aGen32      poscil  aAmpCh32, iGeneratorCf32, iTable

    ; mix all channels
    aSubA           = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)
    aSubB           = (aGen09 + aGen10 + aGen11 + aGen12 + aGen13 + aGen14 + aGen15 + aGen16)
    aSubC           = (aGen17 + aGen18 + aGen19 + aGen20 + aGen21 + aGen22 + aGen23 + aGen24)
    aSubD           = (aGen25 + aGen26 + aGen27 + aGen28 + aGen29 + aGen30 + aGen31 + aGen32)

    aSig            = aSubA + aSubB + aSubC + aSubD

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  

    ; scale by macro envelope        
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)

#-----------------------------------------------------------------||||||||||||--
# 40 ch

class Inst145(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 145
        self.name = 'vocodeSinePentOctScale'
        self.info = 'A forty channel vocoder with scaled mapping and a sine generator.'
        self.auxNo = 13
        self.postMapAmp = (0, 10, 'linear') # amps from experiment
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',       

          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 10), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 40),
          'pmtr15'  : ('c', 1.15),

          'pmtr16'  : ('c', 40),
          'pmtr17'  : ('c', 1.15),

          'pmtr18'  : ('c', 100),
          'pmtr19'  : ('c', 20000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iAnalysisCf09 = p14 * (iAnalysisFqScalar ^ 8)
    iAnalysisCf10 = p14 * (iAnalysisFqScalar ^ 9)
    iAnalysisCf11 = p14 * (iAnalysisFqScalar ^ 10)
    iAnalysisCf12 = p14 * (iAnalysisFqScalar ^ 11)
    iAnalysisCf13 = p14 * (iAnalysisFqScalar ^ 12)
    iAnalysisCf14 = p14 * (iAnalysisFqScalar ^ 13)
    iAnalysisCf15 = p14 * (iAnalysisFqScalar ^ 14)
    iAnalysisCf16 = p14 * (iAnalysisFqScalar ^ 15)
    
    iAnalysisCf17 = p14 * (iAnalysisFqScalar ^ 16)
    iAnalysisCf18 = p14 * (iAnalysisFqScalar ^ 17)
    iAnalysisCf19 = p14 * (iAnalysisFqScalar ^ 18)
    iAnalysisCf20 = p14 * (iAnalysisFqScalar ^ 19)
    iAnalysisCf21 = p14 * (iAnalysisFqScalar ^ 20)
    iAnalysisCf22 = p14 * (iAnalysisFqScalar ^ 21)
    iAnalysisCf23 = p14 * (iAnalysisFqScalar ^ 22)
    iAnalysisCf24 = p14 * (iAnalysisFqScalar ^ 23)
    
    iAnalysisCf25 = p14 * (iAnalysisFqScalar ^ 24)
    iAnalysisCf26 = p14 * (iAnalysisFqScalar ^ 25)
    iAnalysisCf27 = p14 * (iAnalysisFqScalar ^ 26)
    iAnalysisCf28 = p14 * (iAnalysisFqScalar ^ 27)
    iAnalysisCf29 = p14 * (iAnalysisFqScalar ^ 28)
    iAnalysisCf30 = p14 * (iAnalysisFqScalar ^ 29)
    iAnalysisCf31 = p14 * (iAnalysisFqScalar ^ 30)
    iAnalysisCf32 = p14 * (iAnalysisFqScalar ^ 31)
    
    iAnalysisCf33 = p14 * (iAnalysisFqScalar ^ 32)
    iAnalysisCf34 = p14 * (iAnalysisFqScalar ^ 33)
    iAnalysisCf35 = p14 * (iAnalysisFqScalar ^ 34)
    iAnalysisCf36 = p14 * (iAnalysisFqScalar ^ 35)
    iAnalysisCf37 = p14 * (iAnalysisFqScalar ^ 36)
    iAnalysisCf38 = p14 * (iAnalysisFqScalar ^ 37)
    iAnalysisCf39 = p14 * (iAnalysisFqScalar ^ 38)
    iAnalysisCf40 = p14 * (iAnalysisFqScalar ^ 39)


    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)

    iGeneratorCf09 = p16 * (iGeneratorFqScalar ^ 8)
    iGeneratorCf10 = p16 * (iGeneratorFqScalar ^ 9)
    iGeneratorCf11 = p16 * (iGeneratorFqScalar ^ 10)
    iGeneratorCf12 = p16 * (iGeneratorFqScalar ^ 11)
    iGeneratorCf13 = p16 * (iGeneratorFqScalar ^ 12)
    iGeneratorCf14 = p16 * (iGeneratorFqScalar ^ 13)
    iGeneratorCf15 = p16 * (iGeneratorFqScalar ^ 14)
    iGeneratorCf16 = p16 * (iGeneratorFqScalar ^ 15)

    iGeneratorCf17 = p16 * (iGeneratorFqScalar ^ 16)
    iGeneratorCf18 = p16 * (iGeneratorFqScalar ^ 17)
    iGeneratorCf19 = p16 * (iGeneratorFqScalar ^ 18)
    iGeneratorCf20 = p16 * (iGeneratorFqScalar ^ 19)
    iGeneratorCf21 = p16 * (iGeneratorFqScalar ^ 20)
    iGeneratorCf22 = p16 * (iGeneratorFqScalar ^ 21)
    iGeneratorCf23 = p16 * (iGeneratorFqScalar ^ 22)
    iGeneratorCf24 = p16 * (iGeneratorFqScalar ^ 23)

    iGeneratorCf25 = p16 * (iGeneratorFqScalar ^ 24)
    iGeneratorCf26 = p16 * (iGeneratorFqScalar ^ 25)
    iGeneratorCf27 = p16 * (iGeneratorFqScalar ^ 26)
    iGeneratorCf28 = p16 * (iGeneratorFqScalar ^ 27)
    iGeneratorCf29 = p16 * (iGeneratorFqScalar ^ 28)
    iGeneratorCf30 = p16 * (iGeneratorFqScalar ^ 29)
    iGeneratorCf31 = p16 * (iGeneratorFqScalar ^ 30)
    iGeneratorCf32 = p16 * (iGeneratorFqScalar ^ 31)

    iGeneratorCf33 = p16 * (iGeneratorFqScalar ^ 32)
    iGeneratorCf34 = p16 * (iGeneratorFqScalar ^ 33)
    iGeneratorCf35 = p16 * (iGeneratorFqScalar ^ 34)
    iGeneratorCf36 = p16 * (iGeneratorFqScalar ^ 35)
    iGeneratorCf37 = p16 * (iGeneratorFqScalar ^ 36)
    iGeneratorCf38 = p16 * (iGeneratorFqScalar ^ 37)
    iGeneratorCf39 = p16 * (iGeneratorFqScalar ^ 38)
    iGeneratorCf40 = p16 * (iGeneratorFqScalar ^ 39)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters; dont need to scale by 2 here
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf


    aAmpCh09        butterbp     aSrc, iAnalysisCf09, iAnalysisQ
    aAmpCh09        = abs(aAmpCh09)
    aAmpCh09        butterlp     aAmpCh09, iAnalysisCutoff
    aAmpCh09        tone         aAmpCh09, iAnalysisCutoff   ; one pole lpf

    aAmpCh10        butterbp     aSrc, iAnalysisCf10, iAnalysisQ
    aAmpCh10        = abs(aAmpCh10)
    aAmpCh10        butterlp     aAmpCh10, iAnalysisCutoff
    aAmpCh10        tone         aAmpCh10, iAnalysisCutoff   ; one pole lpf

    aAmpCh11        butterbp     aSrc, iAnalysisCf11, iAnalysisQ
    aAmpCh11        = abs(aAmpCh11)
    aAmpCh11        butterlp     aAmpCh11, iAnalysisCutoff
    aAmpCh11        tone         aAmpCh11, iAnalysisCutoff   ; one pole lpf

    aAmpCh12        butterbp     aSrc, iAnalysisCf12, iAnalysisQ
    aAmpCh12        = abs(aAmpCh12)
    aAmpCh12        butterlp     aAmpCh12, iAnalysisCutoff
    aAmpCh12        tone         aAmpCh12, iAnalysisCutoff   ; one pole lpf

    aAmpCh13        butterbp     aSrc, iAnalysisCf13, iAnalysisQ
    aAmpCh13        = abs(aAmpCh13)
    aAmpCh13        butterlp     aAmpCh13, iAnalysisCutoff
    aAmpCh13        tone         aAmpCh13, iAnalysisCutoff   ; one pole lpf

    aAmpCh14        butterbp     aSrc, iAnalysisCf14, iAnalysisQ
    aAmpCh14        = abs(aAmpCh14)
    aAmpCh14        butterlp     aAmpCh14, iAnalysisCutoff
    aAmpCh14        tone         aAmpCh14, iAnalysisCutoff   ; one pole lpf

    aAmpCh15        butterbp     aSrc, iAnalysisCf15, iAnalysisQ
    aAmpCh15        = abs(aAmpCh15)
    aAmpCh15        butterlp     aAmpCh15, iAnalysisCutoff
    aAmpCh15        tone         aAmpCh15, iAnalysisCutoff   ; one pole lpf

    aAmpCh16        butterbp     aSrc, iAnalysisCf16, iAnalysisQ
    aAmpCh16        = abs(aAmpCh16)
    aAmpCh16        butterlp     aAmpCh16, iAnalysisCutoff
    aAmpCh16        tone         aAmpCh16, iAnalysisCutoff   ; one pole lpf


    aAmpCh17        butterbp     aSrc, iAnalysisCf17, iAnalysisQ
    aAmpCh17        = abs(aAmpCh17)
    aAmpCh17        butterlp     aAmpCh17, iAnalysisCutoff
    aAmpCh17        tone         aAmpCh17, iAnalysisCutoff   ; one pole lpf

    aAmpCh18        butterbp     aSrc, iAnalysisCf18, iAnalysisQ
    aAmpCh18        = abs(aAmpCh18)
    aAmpCh18        butterlp     aAmpCh18, iAnalysisCutoff
    aAmpCh18        tone         aAmpCh18, iAnalysisCutoff   ; one pole lpf

    aAmpCh19        butterbp     aSrc, iAnalysisCf19, iAnalysisQ
    aAmpCh19        = abs(aAmpCh19)
    aAmpCh19        butterlp     aAmpCh19, iAnalysisCutoff
    aAmpCh19        tone         aAmpCh19, iAnalysisCutoff   ; one pole lpf

    aAmpCh20        butterbp     aSrc, iAnalysisCf20, iAnalysisQ
    aAmpCh20        = abs(aAmpCh20)
    aAmpCh20        butterlp     aAmpCh20, iAnalysisCutoff
    aAmpCh20        tone         aAmpCh20, iAnalysisCutoff   ; one pole lpf

    aAmpCh21        butterbp     aSrc, iAnalysisCf21, iAnalysisQ
    aAmpCh21        = abs(aAmpCh21)
    aAmpCh21        butterlp     aAmpCh21, iAnalysisCutoff
    aAmpCh21        tone         aAmpCh21, iAnalysisCutoff   ; one pole lpf

    aAmpCh22        butterbp     aSrc, iAnalysisCf22, iAnalysisQ
    aAmpCh22        = abs(aAmpCh22)
    aAmpCh22        butterlp     aAmpCh22, iAnalysisCutoff
    aAmpCh22        tone         aAmpCh22, iAnalysisCutoff   ; one pole lpf

    aAmpCh23        butterbp     aSrc, iAnalysisCf23, iAnalysisQ
    aAmpCh23        = abs(aAmpCh23)
    aAmpCh23        butterlp     aAmpCh23, iAnalysisCutoff
    aAmpCh23        tone         aAmpCh23, iAnalysisCutoff   ; one pole lpf

    aAmpCh24        butterbp     aSrc, iAnalysisCf24, iAnalysisQ
    aAmpCh24        = abs(aAmpCh24)
    aAmpCh24        butterlp     aAmpCh24, iAnalysisCutoff
    aAmpCh24        tone         aAmpCh24, iAnalysisCutoff   ; one pole lpf


    aAmpCh25        butterbp     aSrc, iAnalysisCf25, iAnalysisQ
    aAmpCh25        = abs(aAmpCh25)
    aAmpCh25        butterlp     aAmpCh25, iAnalysisCutoff
    aAmpCh25        tone         aAmpCh25, iAnalysisCutoff   ; one pole lpf

    aAmpCh26        butterbp     aSrc, iAnalysisCf26, iAnalysisQ
    aAmpCh26        = abs(aAmpCh26)
    aAmpCh26        butterlp     aAmpCh26, iAnalysisCutoff
    aAmpCh26        tone         aAmpCh26, iAnalysisCutoff   ; one pole lpf

    aAmpCh27        butterbp     aSrc, iAnalysisCf27, iAnalysisQ
    aAmpCh27        = abs(aAmpCh27)
    aAmpCh27        butterlp     aAmpCh27, iAnalysisCutoff
    aAmpCh27        tone         aAmpCh27, iAnalysisCutoff   ; one pole lpf

    aAmpCh28        butterbp     aSrc, iAnalysisCf28, iAnalysisQ
    aAmpCh28        = abs(aAmpCh28)
    aAmpCh28        butterlp     aAmpCh28, iAnalysisCutoff
    aAmpCh28        tone         aAmpCh28, iAnalysisCutoff   ; one pole lpf

    aAmpCh29        butterbp     aSrc, iAnalysisCf29, iAnalysisQ
    aAmpCh29        = abs(aAmpCh29)
    aAmpCh29        butterlp     aAmpCh29, iAnalysisCutoff
    aAmpCh29        tone         aAmpCh29, iAnalysisCutoff   ; one pole lpf

    aAmpCh30        butterbp     aSrc, iAnalysisCf30, iAnalysisQ
    aAmpCh30        = abs(aAmpCh30)
    aAmpCh30        butterlp     aAmpCh30, iAnalysisCutoff
    aAmpCh30        tone         aAmpCh30, iAnalysisCutoff   ; one pole lpf

    aAmpCh31        butterbp     aSrc, iAnalysisCf31, iAnalysisQ
    aAmpCh31        = abs(aAmpCh31)
    aAmpCh31        butterlp     aAmpCh31, iAnalysisCutoff
    aAmpCh31        tone         aAmpCh31, iAnalysisCutoff   ; one pole lpf

    aAmpCh32        butterbp     aSrc, iAnalysisCf32, iAnalysisQ
    aAmpCh32        = abs(aAmpCh32)
    aAmpCh32        butterlp     aAmpCh32, iAnalysisCutoff
    aAmpCh32        tone         aAmpCh32, iAnalysisCutoff   ; one pole lpf


    aAmpCh33        butterbp     aSrc, iAnalysisCf33, iAnalysisQ
    aAmpCh33        = abs(aAmpCh33)
    aAmpCh33        butterlp     aAmpCh33, iAnalysisCutoff
    aAmpCh33        tone         aAmpCh33, iAnalysisCutoff   ; one pole lpf

    aAmpCh34        butterbp     aSrc, iAnalysisCf34, iAnalysisQ
    aAmpCh34        = abs(aAmpCh34)
    aAmpCh34        butterlp     aAmpCh34, iAnalysisCutoff
    aAmpCh34        tone         aAmpCh34, iAnalysisCutoff   ; one pole lpf

    aAmpCh35        butterbp     aSrc, iAnalysisCf35, iAnalysisQ
    aAmpCh35        = abs(aAmpCh35)
    aAmpCh35        butterlp     aAmpCh35, iAnalysisCutoff
    aAmpCh35        tone         aAmpCh35, iAnalysisCutoff   ; one pole lpf

    aAmpCh36        butterbp     aSrc, iAnalysisCf36, iAnalysisQ
    aAmpCh36        = abs(aAmpCh36)
    aAmpCh36        butterlp     aAmpCh36, iAnalysisCutoff
    aAmpCh36        tone         aAmpCh36, iAnalysisCutoff   ; one pole lpf

    aAmpCh37        butterbp     aSrc, iAnalysisCf37, iAnalysisQ
    aAmpCh37        = abs(aAmpCh37)
    aAmpCh37        butterlp     aAmpCh37, iAnalysisCutoff
    aAmpCh37        tone         aAmpCh37, iAnalysisCutoff   ; one pole lpf

    aAmpCh38        butterbp     aSrc, iAnalysisCf38, iAnalysisQ
    aAmpCh38        = abs(aAmpCh38)
    aAmpCh38        butterlp     aAmpCh38, iAnalysisCutoff
    aAmpCh38        tone         aAmpCh38, iAnalysisCutoff   ; one pole lpf

    aAmpCh39        butterbp     aSrc, iAnalysisCf39, iAnalysisQ
    aAmpCh39        = abs(aAmpCh39)
    aAmpCh39        butterlp     aAmpCh39, iAnalysisCutoff
    aAmpCh39        tone         aAmpCh39, iAnalysisCutoff   ; one pole lpf

    aAmpCh40        butterbp     aSrc, iAnalysisCf40, iAnalysisQ
    aAmpCh40        = abs(aAmpCh40)
    aAmpCh40        butterlp     aAmpCh40, iAnalysisCutoff
    aAmpCh40        tone         aAmpCh40, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; filter noise at fq, scale by analysis
    aGen01      poscil  aAmpCh01, iGeneratorCf01, iTable
    aGen02      poscil  aAmpCh02, iGeneratorCf02, iTable
    aGen03      poscil  aAmpCh03, iGeneratorCf03, iTable
    aGen04      poscil  aAmpCh04, iGeneratorCf04, iTable
    aGen05      poscil  aAmpCh05, iGeneratorCf05, iTable
    aGen06      poscil  aAmpCh06, iGeneratorCf06, iTable
    aGen07      poscil  aAmpCh07, iGeneratorCf07, iTable
    aGen08      poscil  aAmpCh08, iGeneratorCf08, iTable

    aGen09      poscil  aAmpCh09, iGeneratorCf09, iTable
    aGen10      poscil  aAmpCh10, iGeneratorCf10, iTable
    aGen11      poscil  aAmpCh11, iGeneratorCf11, iTable
    aGen12      poscil  aAmpCh12, iGeneratorCf12, iTable
    aGen13      poscil  aAmpCh13, iGeneratorCf13, iTable
    aGen14      poscil  aAmpCh14, iGeneratorCf14, iTable
    aGen15      poscil  aAmpCh15, iGeneratorCf15, iTable
    aGen16      poscil  aAmpCh16, iGeneratorCf16, iTable

    aGen17      poscil  aAmpCh17, iGeneratorCf17, iTable
    aGen18      poscil  aAmpCh18, iGeneratorCf18, iTable
    aGen19      poscil  aAmpCh19, iGeneratorCf19, iTable
    aGen20      poscil  aAmpCh20, iGeneratorCf20, iTable
    aGen21      poscil  aAmpCh21, iGeneratorCf21, iTable
    aGen22      poscil  aAmpCh22, iGeneratorCf22, iTable
    aGen23      poscil  aAmpCh23, iGeneratorCf23, iTable
    aGen24      poscil  aAmpCh24, iGeneratorCf24, iTable

    aGen25      poscil  aAmpCh25, iGeneratorCf25, iTable
    aGen26      poscil  aAmpCh26, iGeneratorCf26, iTable
    aGen27      poscil  aAmpCh27, iGeneratorCf27, iTable
    aGen28      poscil  aAmpCh28, iGeneratorCf28, iTable
    aGen29      poscil  aAmpCh29, iGeneratorCf29, iTable
    aGen30      poscil  aAmpCh30, iGeneratorCf30, iTable
    aGen31      poscil  aAmpCh31, iGeneratorCf31, iTable
    aGen32      poscil  aAmpCh32, iGeneratorCf32, iTable

    aGen33      poscil  aAmpCh33, iGeneratorCf33, iTable
    aGen34      poscil  aAmpCh34, iGeneratorCf34, iTable
    aGen35      poscil  aAmpCh35, iGeneratorCf35, iTable
    aGen36      poscil  aAmpCh36, iGeneratorCf36, iTable
    aGen37      poscil  aAmpCh37, iGeneratorCf37, iTable
    aGen38      poscil  aAmpCh38, iGeneratorCf38, iTable
    aGen39      poscil  aAmpCh39, iGeneratorCf39, iTable
    aGen40      poscil  aAmpCh40, iGeneratorCf40, iTable

    ; mix all channels
    aSubA           = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)
    aSubB           = (aGen09 + aGen10 + aGen11 + aGen12 + aGen13 + aGen14 + aGen15 + aGen16)
    aSubC           = (aGen17 + aGen18 + aGen19 + aGen20 + aGen21 + aGen22 + aGen23 + aGen24)
    aSubD           = (aGen25 + aGen26 + aGen27 + aGen28 + aGen29 + aGen30 + aGen31 + aGen32)
    aSubE           = (aGen33 + aGen34 + aGen35 + aGen36 + aGen37 + aGen38 + aGen39 + aGen40)

    aSig            = aSubA + aSubB + aSubC + aSubD + aSubE

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  

    ; scale by macro envelope        
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
# 48 ch

class Inst146(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 146
        self.name = 'vocodeSineHexOctScale'
        self.info = 'A forty eight channel vocoder with scaled mapping and a sine generator.'
        self.auxNo = 13
        self.postMapAmp = (0, 10, 'linear') # amps from experiment
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr13'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr14'  : 'analysis frequency base in Hz',
          'pmtr15'  : 'analysis frequency scalar',        

          'pmtr16'  : 'generator frequency base in Hz',
          'pmtr17'  : 'generator frequency scalar',       

          'pmtr18'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr19'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 40), # analysis cut-off fq
          'pmtr13'  : ('c', 10), # band width, 20 is well pitched
          
          'pmtr14'  : ('c', 40),
          'pmtr15'  : ('c', 1.125),

          'pmtr16'  : ('c', 40),
          'pmtr17'  : ('c', 1.125),

          'pmtr18'  : ('c', 2000),
          'pmtr19'  : ('c', 20000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11

    iAnalysisCutoff = p12
    iAnalysisQ = p13

    iAnalysisFqScalar = p15
    iAnalysisCf01 = p14 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p14 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p14 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p14 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p14 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p14 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p14 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p14 * (iAnalysisFqScalar ^ 7)

    iAnalysisCf09 = p14 * (iAnalysisFqScalar ^ 8)
    iAnalysisCf10 = p14 * (iAnalysisFqScalar ^ 9)
    iAnalysisCf11 = p14 * (iAnalysisFqScalar ^ 10)
    iAnalysisCf12 = p14 * (iAnalysisFqScalar ^ 11)
    iAnalysisCf13 = p14 * (iAnalysisFqScalar ^ 12)
    iAnalysisCf14 = p14 * (iAnalysisFqScalar ^ 13)
    iAnalysisCf15 = p14 * (iAnalysisFqScalar ^ 14)
    iAnalysisCf16 = p14 * (iAnalysisFqScalar ^ 15)
    
    iAnalysisCf17 = p14 * (iAnalysisFqScalar ^ 16)
    iAnalysisCf18 = p14 * (iAnalysisFqScalar ^ 17)
    iAnalysisCf19 = p14 * (iAnalysisFqScalar ^ 18)
    iAnalysisCf20 = p14 * (iAnalysisFqScalar ^ 19)
    iAnalysisCf21 = p14 * (iAnalysisFqScalar ^ 20)
    iAnalysisCf22 = p14 * (iAnalysisFqScalar ^ 21)
    iAnalysisCf23 = p14 * (iAnalysisFqScalar ^ 22)
    iAnalysisCf24 = p14 * (iAnalysisFqScalar ^ 23)
    
    iAnalysisCf25 = p14 * (iAnalysisFqScalar ^ 24)
    iAnalysisCf26 = p14 * (iAnalysisFqScalar ^ 25)
    iAnalysisCf27 = p14 * (iAnalysisFqScalar ^ 26)
    iAnalysisCf28 = p14 * (iAnalysisFqScalar ^ 27)
    iAnalysisCf29 = p14 * (iAnalysisFqScalar ^ 28)
    iAnalysisCf30 = p14 * (iAnalysisFqScalar ^ 29)
    iAnalysisCf31 = p14 * (iAnalysisFqScalar ^ 30)
    iAnalysisCf32 = p14 * (iAnalysisFqScalar ^ 31)
    
    iAnalysisCf33 = p14 * (iAnalysisFqScalar ^ 32)
    iAnalysisCf34 = p14 * (iAnalysisFqScalar ^ 33)
    iAnalysisCf35 = p14 * (iAnalysisFqScalar ^ 34)
    iAnalysisCf36 = p14 * (iAnalysisFqScalar ^ 35)
    iAnalysisCf37 = p14 * (iAnalysisFqScalar ^ 36)
    iAnalysisCf38 = p14 * (iAnalysisFqScalar ^ 37)
    iAnalysisCf39 = p14 * (iAnalysisFqScalar ^ 38)
    iAnalysisCf40 = p14 * (iAnalysisFqScalar ^ 39)
    
    iAnalysisCf41 = p14 * (iAnalysisFqScalar ^ 40)
    iAnalysisCf42 = p14 * (iAnalysisFqScalar ^ 41)
    iAnalysisCf43 = p14 * (iAnalysisFqScalar ^ 42)
    iAnalysisCf44 = p14 * (iAnalysisFqScalar ^ 43)
    iAnalysisCf45 = p14 * (iAnalysisFqScalar ^ 44)
    iAnalysisCf46 = p14 * (iAnalysisFqScalar ^ 45)
    iAnalysisCf47 = p14 * (iAnalysisFqScalar ^ 46)
    iAnalysisCf48 = p14 * (iAnalysisFqScalar ^ 47)


    iGeneratorFqScalar = p17
    iGeneratorCf01 = p16 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p16 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p16 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p16 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p16 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p16 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p16 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p16 * (iGeneratorFqScalar ^ 7)

    iGeneratorCf09 = p16 * (iGeneratorFqScalar ^ 8)
    iGeneratorCf10 = p16 * (iGeneratorFqScalar ^ 9)
    iGeneratorCf11 = p16 * (iGeneratorFqScalar ^ 10)
    iGeneratorCf12 = p16 * (iGeneratorFqScalar ^ 11)
    iGeneratorCf13 = p16 * (iGeneratorFqScalar ^ 12)
    iGeneratorCf14 = p16 * (iGeneratorFqScalar ^ 13)
    iGeneratorCf15 = p16 * (iGeneratorFqScalar ^ 14)
    iGeneratorCf16 = p16 * (iGeneratorFqScalar ^ 15)

    iGeneratorCf17 = p16 * (iGeneratorFqScalar ^ 16)
    iGeneratorCf18 = p16 * (iGeneratorFqScalar ^ 17)
    iGeneratorCf19 = p16 * (iGeneratorFqScalar ^ 18)
    iGeneratorCf20 = p16 * (iGeneratorFqScalar ^ 19)
    iGeneratorCf21 = p16 * (iGeneratorFqScalar ^ 20)
    iGeneratorCf22 = p16 * (iGeneratorFqScalar ^ 21)
    iGeneratorCf23 = p16 * (iGeneratorFqScalar ^ 22)
    iGeneratorCf24 = p16 * (iGeneratorFqScalar ^ 23)

    iGeneratorCf25 = p16 * (iGeneratorFqScalar ^ 24)
    iGeneratorCf26 = p16 * (iGeneratorFqScalar ^ 25)
    iGeneratorCf27 = p16 * (iGeneratorFqScalar ^ 26)
    iGeneratorCf28 = p16 * (iGeneratorFqScalar ^ 27)
    iGeneratorCf29 = p16 * (iGeneratorFqScalar ^ 28)
    iGeneratorCf30 = p16 * (iGeneratorFqScalar ^ 29)
    iGeneratorCf31 = p16 * (iGeneratorFqScalar ^ 30)
    iGeneratorCf32 = p16 * (iGeneratorFqScalar ^ 31)

    iGeneratorCf33 = p16 * (iGeneratorFqScalar ^ 32)
    iGeneratorCf34 = p16 * (iGeneratorFqScalar ^ 33)
    iGeneratorCf35 = p16 * (iGeneratorFqScalar ^ 34)
    iGeneratorCf36 = p16 * (iGeneratorFqScalar ^ 35)
    iGeneratorCf37 = p16 * (iGeneratorFqScalar ^ 36)
    iGeneratorCf38 = p16 * (iGeneratorFqScalar ^ 37)
    iGeneratorCf39 = p16 * (iGeneratorFqScalar ^ 38)
    iGeneratorCf40 = p16 * (iGeneratorFqScalar ^ 39)

    iGeneratorCf41 = p16 * (iGeneratorFqScalar ^ 40)
    iGeneratorCf42 = p16 * (iGeneratorFqScalar ^ 41)
    iGeneratorCf43 = p16 * (iGeneratorFqScalar ^ 42)
    iGeneratorCf44 = p16 * (iGeneratorFqScalar ^ 43)
    iGeneratorCf45 = p16 * (iGeneratorFqScalar ^ 44)
    iGeneratorCf46 = p16 * (iGeneratorFqScalar ^ 45)
    iGeneratorCf47 = p16 * (iGeneratorFqScalar ^ 46)
    iGeneratorCf48 = p16 * (iGeneratorFqScalar ^ 47)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p17, iDur, p18
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters; dont need to scale by 2 here
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf


    aAmpCh09        butterbp     aSrc, iAnalysisCf09, iAnalysisQ
    aAmpCh09        = abs(aAmpCh09)
    aAmpCh09        butterlp     aAmpCh09, iAnalysisCutoff
    aAmpCh09        tone         aAmpCh09, iAnalysisCutoff   ; one pole lpf

    aAmpCh10        butterbp     aSrc, iAnalysisCf10, iAnalysisQ
    aAmpCh10        = abs(aAmpCh10)
    aAmpCh10        butterlp     aAmpCh10, iAnalysisCutoff
    aAmpCh10        tone         aAmpCh10, iAnalysisCutoff   ; one pole lpf

    aAmpCh11        butterbp     aSrc, iAnalysisCf11, iAnalysisQ
    aAmpCh11        = abs(aAmpCh11)
    aAmpCh11        butterlp     aAmpCh11, iAnalysisCutoff
    aAmpCh11        tone         aAmpCh11, iAnalysisCutoff   ; one pole lpf

    aAmpCh12        butterbp     aSrc, iAnalysisCf12, iAnalysisQ
    aAmpCh12        = abs(aAmpCh12)
    aAmpCh12        butterlp     aAmpCh12, iAnalysisCutoff
    aAmpCh12        tone         aAmpCh12, iAnalysisCutoff   ; one pole lpf

    aAmpCh13        butterbp     aSrc, iAnalysisCf13, iAnalysisQ
    aAmpCh13        = abs(aAmpCh13)
    aAmpCh13        butterlp     aAmpCh13, iAnalysisCutoff
    aAmpCh13        tone         aAmpCh13, iAnalysisCutoff   ; one pole lpf

    aAmpCh14        butterbp     aSrc, iAnalysisCf14, iAnalysisQ
    aAmpCh14        = abs(aAmpCh14)
    aAmpCh14        butterlp     aAmpCh14, iAnalysisCutoff
    aAmpCh14        tone         aAmpCh14, iAnalysisCutoff   ; one pole lpf

    aAmpCh15        butterbp     aSrc, iAnalysisCf15, iAnalysisQ
    aAmpCh15        = abs(aAmpCh15)
    aAmpCh15        butterlp     aAmpCh15, iAnalysisCutoff
    aAmpCh15        tone         aAmpCh15, iAnalysisCutoff   ; one pole lpf

    aAmpCh16        butterbp     aSrc, iAnalysisCf16, iAnalysisQ
    aAmpCh16        = abs(aAmpCh16)
    aAmpCh16        butterlp     aAmpCh16, iAnalysisCutoff
    aAmpCh16        tone         aAmpCh16, iAnalysisCutoff   ; one pole lpf


    aAmpCh17        butterbp     aSrc, iAnalysisCf17, iAnalysisQ
    aAmpCh17        = abs(aAmpCh17)
    aAmpCh17        butterlp     aAmpCh17, iAnalysisCutoff
    aAmpCh17        tone         aAmpCh17, iAnalysisCutoff   ; one pole lpf

    aAmpCh18        butterbp     aSrc, iAnalysisCf18, iAnalysisQ
    aAmpCh18        = abs(aAmpCh18)
    aAmpCh18        butterlp     aAmpCh18, iAnalysisCutoff
    aAmpCh18        tone         aAmpCh18, iAnalysisCutoff   ; one pole lpf

    aAmpCh19        butterbp     aSrc, iAnalysisCf19, iAnalysisQ
    aAmpCh19        = abs(aAmpCh19)
    aAmpCh19        butterlp     aAmpCh19, iAnalysisCutoff
    aAmpCh19        tone         aAmpCh19, iAnalysisCutoff   ; one pole lpf

    aAmpCh20        butterbp     aSrc, iAnalysisCf20, iAnalysisQ
    aAmpCh20        = abs(aAmpCh20)
    aAmpCh20        butterlp     aAmpCh20, iAnalysisCutoff
    aAmpCh20        tone         aAmpCh20, iAnalysisCutoff   ; one pole lpf

    aAmpCh21        butterbp     aSrc, iAnalysisCf21, iAnalysisQ
    aAmpCh21        = abs(aAmpCh21)
    aAmpCh21        butterlp     aAmpCh21, iAnalysisCutoff
    aAmpCh21        tone         aAmpCh21, iAnalysisCutoff   ; one pole lpf

    aAmpCh22        butterbp     aSrc, iAnalysisCf22, iAnalysisQ
    aAmpCh22        = abs(aAmpCh22)
    aAmpCh22        butterlp     aAmpCh22, iAnalysisCutoff
    aAmpCh22        tone         aAmpCh22, iAnalysisCutoff   ; one pole lpf

    aAmpCh23        butterbp     aSrc, iAnalysisCf23, iAnalysisQ
    aAmpCh23        = abs(aAmpCh23)
    aAmpCh23        butterlp     aAmpCh23, iAnalysisCutoff
    aAmpCh23        tone         aAmpCh23, iAnalysisCutoff   ; one pole lpf

    aAmpCh24        butterbp     aSrc, iAnalysisCf24, iAnalysisQ
    aAmpCh24        = abs(aAmpCh24)
    aAmpCh24        butterlp     aAmpCh24, iAnalysisCutoff
    aAmpCh24        tone         aAmpCh24, iAnalysisCutoff   ; one pole lpf


    aAmpCh25        butterbp     aSrc, iAnalysisCf25, iAnalysisQ
    aAmpCh25        = abs(aAmpCh25)
    aAmpCh25        butterlp     aAmpCh25, iAnalysisCutoff
    aAmpCh25        tone         aAmpCh25, iAnalysisCutoff   ; one pole lpf

    aAmpCh26        butterbp     aSrc, iAnalysisCf26, iAnalysisQ
    aAmpCh26        = abs(aAmpCh26)
    aAmpCh26        butterlp     aAmpCh26, iAnalysisCutoff
    aAmpCh26        tone         aAmpCh26, iAnalysisCutoff   ; one pole lpf

    aAmpCh27        butterbp     aSrc, iAnalysisCf27, iAnalysisQ
    aAmpCh27        = abs(aAmpCh27)
    aAmpCh27        butterlp     aAmpCh27, iAnalysisCutoff
    aAmpCh27        tone         aAmpCh27, iAnalysisCutoff   ; one pole lpf

    aAmpCh28        butterbp     aSrc, iAnalysisCf28, iAnalysisQ
    aAmpCh28        = abs(aAmpCh28)
    aAmpCh28        butterlp     aAmpCh28, iAnalysisCutoff
    aAmpCh28        tone         aAmpCh28, iAnalysisCutoff   ; one pole lpf

    aAmpCh29        butterbp     aSrc, iAnalysisCf29, iAnalysisQ
    aAmpCh29        = abs(aAmpCh29)
    aAmpCh29        butterlp     aAmpCh29, iAnalysisCutoff
    aAmpCh29        tone         aAmpCh29, iAnalysisCutoff   ; one pole lpf

    aAmpCh30        butterbp     aSrc, iAnalysisCf30, iAnalysisQ
    aAmpCh30        = abs(aAmpCh30)
    aAmpCh30        butterlp     aAmpCh30, iAnalysisCutoff
    aAmpCh30        tone         aAmpCh30, iAnalysisCutoff   ; one pole lpf

    aAmpCh31        butterbp     aSrc, iAnalysisCf31, iAnalysisQ
    aAmpCh31        = abs(aAmpCh31)
    aAmpCh31        butterlp     aAmpCh31, iAnalysisCutoff
    aAmpCh31        tone         aAmpCh31, iAnalysisCutoff   ; one pole lpf

    aAmpCh32        butterbp     aSrc, iAnalysisCf32, iAnalysisQ
    aAmpCh32        = abs(aAmpCh32)
    aAmpCh32        butterlp     aAmpCh32, iAnalysisCutoff
    aAmpCh32        tone         aAmpCh32, iAnalysisCutoff   ; one pole lpf


    aAmpCh33        butterbp     aSrc, iAnalysisCf33, iAnalysisQ
    aAmpCh33        = abs(aAmpCh33)
    aAmpCh33        butterlp     aAmpCh33, iAnalysisCutoff
    aAmpCh33        tone         aAmpCh33, iAnalysisCutoff   ; one pole lpf

    aAmpCh34        butterbp     aSrc, iAnalysisCf34, iAnalysisQ
    aAmpCh34        = abs(aAmpCh34)
    aAmpCh34        butterlp     aAmpCh34, iAnalysisCutoff
    aAmpCh34        tone         aAmpCh34, iAnalysisCutoff   ; one pole lpf

    aAmpCh35        butterbp     aSrc, iAnalysisCf35, iAnalysisQ
    aAmpCh35        = abs(aAmpCh35)
    aAmpCh35        butterlp     aAmpCh35, iAnalysisCutoff
    aAmpCh35        tone         aAmpCh35, iAnalysisCutoff   ; one pole lpf

    aAmpCh36        butterbp     aSrc, iAnalysisCf36, iAnalysisQ
    aAmpCh36        = abs(aAmpCh36)
    aAmpCh36        butterlp     aAmpCh36, iAnalysisCutoff
    aAmpCh36        tone         aAmpCh36, iAnalysisCutoff   ; one pole lpf

    aAmpCh37        butterbp     aSrc, iAnalysisCf37, iAnalysisQ
    aAmpCh37        = abs(aAmpCh37)
    aAmpCh37        butterlp     aAmpCh37, iAnalysisCutoff
    aAmpCh37        tone         aAmpCh37, iAnalysisCutoff   ; one pole lpf

    aAmpCh38        butterbp     aSrc, iAnalysisCf38, iAnalysisQ
    aAmpCh38        = abs(aAmpCh38)
    aAmpCh38        butterlp     aAmpCh38, iAnalysisCutoff
    aAmpCh38        tone         aAmpCh38, iAnalysisCutoff   ; one pole lpf

    aAmpCh39        butterbp     aSrc, iAnalysisCf39, iAnalysisQ
    aAmpCh39        = abs(aAmpCh39)
    aAmpCh39        butterlp     aAmpCh39, iAnalysisCutoff
    aAmpCh39        tone         aAmpCh39, iAnalysisCutoff   ; one pole lpf

    aAmpCh40        butterbp     aSrc, iAnalysisCf40, iAnalysisQ
    aAmpCh40        = abs(aAmpCh40)
    aAmpCh40        butterlp     aAmpCh40, iAnalysisCutoff
    aAmpCh40        tone         aAmpCh40, iAnalysisCutoff   ; one pole lpf


    aAmpCh41        butterbp     aSrc, iAnalysisCf41, iAnalysisQ
    aAmpCh41        = abs(aAmpCh41)
    aAmpCh41        butterlp     aAmpCh41, iAnalysisCutoff
    aAmpCh41        tone         aAmpCh41, iAnalysisCutoff   ; one pole lpf

    aAmpCh42        butterbp     aSrc, iAnalysisCf42, iAnalysisQ
    aAmpCh42        = abs(aAmpCh42)
    aAmpCh42        butterlp     aAmpCh42, iAnalysisCutoff
    aAmpCh42        tone         aAmpCh42, iAnalysisCutoff   ; one pole lpf

    aAmpCh43        butterbp     aSrc, iAnalysisCf43, iAnalysisQ
    aAmpCh43        = abs(aAmpCh43)
    aAmpCh43        butterlp     aAmpCh43, iAnalysisCutoff
    aAmpCh43        tone         aAmpCh43, iAnalysisCutoff   ; one pole lpf

    aAmpCh44        butterbp     aSrc, iAnalysisCf44, iAnalysisQ
    aAmpCh44        = abs(aAmpCh44)
    aAmpCh44        butterlp     aAmpCh44, iAnalysisCutoff
    aAmpCh44        tone         aAmpCh44, iAnalysisCutoff   ; one pole lpf

    aAmpCh45        butterbp     aSrc, iAnalysisCf45, iAnalysisQ
    aAmpCh45        = abs(aAmpCh45)
    aAmpCh45        butterlp     aAmpCh45, iAnalysisCutoff
    aAmpCh45        tone         aAmpCh45, iAnalysisCutoff   ; one pole lpf

    aAmpCh46        butterbp     aSrc, iAnalysisCf46, iAnalysisQ
    aAmpCh46        = abs(aAmpCh46)
    aAmpCh46        butterlp     aAmpCh46, iAnalysisCutoff
    aAmpCh46        tone         aAmpCh46, iAnalysisCutoff   ; one pole lpf

    aAmpCh47        butterbp     aSrc, iAnalysisCf47, iAnalysisQ
    aAmpCh47        = abs(aAmpCh47)
    aAmpCh47        butterlp     aAmpCh47, iAnalysisCutoff
    aAmpCh47        tone         aAmpCh47, iAnalysisCutoff   ; one pole lpf

    aAmpCh48        butterbp     aSrc, iAnalysisCf48, iAnalysisQ
    aAmpCh48        = abs(aAmpCh48)
    aAmpCh48        butterlp     aAmpCh48, iAnalysisCutoff
    aAmpCh48        tone         aAmpCh48, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; filter noise at fq, scale by analysis
    aGen01      poscil  aAmpCh01, iGeneratorCf01, iTable
    aGen02      poscil  aAmpCh02, iGeneratorCf02, iTable
    aGen03      poscil  aAmpCh03, iGeneratorCf03, iTable
    aGen04      poscil  aAmpCh04, iGeneratorCf04, iTable
    aGen05      poscil  aAmpCh05, iGeneratorCf05, iTable
    aGen06      poscil  aAmpCh06, iGeneratorCf06, iTable
    aGen07      poscil  aAmpCh07, iGeneratorCf07, iTable
    aGen08      poscil  aAmpCh08, iGeneratorCf08, iTable

    aGen09      poscil  aAmpCh09, iGeneratorCf09, iTable
    aGen10      poscil  aAmpCh10, iGeneratorCf10, iTable
    aGen11      poscil  aAmpCh11, iGeneratorCf11, iTable
    aGen12      poscil  aAmpCh12, iGeneratorCf12, iTable
    aGen13      poscil  aAmpCh13, iGeneratorCf13, iTable
    aGen14      poscil  aAmpCh14, iGeneratorCf14, iTable
    aGen15      poscil  aAmpCh15, iGeneratorCf15, iTable
    aGen16      poscil  aAmpCh16, iGeneratorCf16, iTable

    aGen17      poscil  aAmpCh17, iGeneratorCf17, iTable
    aGen18      poscil  aAmpCh18, iGeneratorCf18, iTable
    aGen19      poscil  aAmpCh19, iGeneratorCf19, iTable
    aGen20      poscil  aAmpCh20, iGeneratorCf20, iTable
    aGen21      poscil  aAmpCh21, iGeneratorCf21, iTable
    aGen22      poscil  aAmpCh22, iGeneratorCf22, iTable
    aGen23      poscil  aAmpCh23, iGeneratorCf23, iTable
    aGen24      poscil  aAmpCh24, iGeneratorCf24, iTable

    aGen25      poscil  aAmpCh25, iGeneratorCf25, iTable
    aGen26      poscil  aAmpCh26, iGeneratorCf26, iTable
    aGen27      poscil  aAmpCh27, iGeneratorCf27, iTable
    aGen28      poscil  aAmpCh28, iGeneratorCf28, iTable
    aGen29      poscil  aAmpCh29, iGeneratorCf29, iTable
    aGen30      poscil  aAmpCh30, iGeneratorCf30, iTable
    aGen31      poscil  aAmpCh31, iGeneratorCf31, iTable
    aGen32      poscil  aAmpCh32, iGeneratorCf32, iTable

    aGen33      poscil  aAmpCh33, iGeneratorCf33, iTable
    aGen34      poscil  aAmpCh34, iGeneratorCf34, iTable
    aGen35      poscil  aAmpCh35, iGeneratorCf35, iTable
    aGen36      poscil  aAmpCh36, iGeneratorCf36, iTable
    aGen37      poscil  aAmpCh37, iGeneratorCf37, iTable
    aGen38      poscil  aAmpCh38, iGeneratorCf38, iTable
    aGen39      poscil  aAmpCh39, iGeneratorCf39, iTable
    aGen40      poscil  aAmpCh40, iGeneratorCf40, iTable

    aGen41      poscil  aAmpCh41, iGeneratorCf41, iTable
    aGen42      poscil  aAmpCh42, iGeneratorCf42, iTable
    aGen43      poscil  aAmpCh43, iGeneratorCf43, iTable
    aGen44      poscil  aAmpCh44, iGeneratorCf44, iTable
    aGen45      poscil  aAmpCh45, iGeneratorCf45, iTable
    aGen46      poscil  aAmpCh46, iGeneratorCf46, iTable
    aGen47      poscil  aAmpCh47, iGeneratorCf47, iTable
    aGen48      poscil  aAmpCh48, iGeneratorCf48, iTable

    ; mix all channels
    aSubA           = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)
    aSubB           = (aGen09 + aGen10 + aGen11 + aGen12 + aGen13 + aGen14 + aGen15 + aGen16)
    aSubC           = (aGen17 + aGen18 + aGen19 + aGen20 + aGen21 + aGen22 + aGen23 + aGen24)
    aSubD           = (aGen25 + aGen26 + aGen27 + aGen28 + aGen29 + aGen30 + aGen31 + aGen32)
    aSubE           = (aGen33 + aGen34 + aGen35 + aGen36 + aGen37 + aGen38 + aGen39 + aGen40)
    aSubF           = (aGen41 + aGen42 + aGen43 + aGen44 + aGen45 + aGen46 + aGen47 + aGen48)

    aSig            = aSubA + aSubB + aSubC + aSubD + aSubE + aSubF

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  

    ; scale by macro envelope        
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)







#-----------------------------------------------------------------||||||||||||--
class Inst110(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 110
        self.name = 'noiseAudioEnvelopeSineQuad'
        self.info = 'A noise generator with an audio-rate sine envelope, a proportional linear envelope, and a variable low-pass filter'
        self.auxNo = 17
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',

          'pmtr12'  : 'tremelo sine 1 start frequency in Hz',
          'pmtr13'  : 'tremelo sine 1 end frequency in Hz',
          'pmtr14'  : 'tremelo sine 1 amp (0-1)',
          'pmtr15'  : 'tremelo sine 2 start frequency in Hz',
          'pmtr16'  : 'tremelo sine 2 end frequency in Hz',
          'pmtr17'  : 'tremelo sine 2 amp (0-1)',
          'pmtr18'  : 'tremelo sine 3 start frequency in Hz',
          'pmtr19'  : 'tremelo sine 3 end frequency in Hz',
          'pmtr20'  : 'tremelo sine 3 amp (0-1)',
          'pmtr21'  : 'tremelo sine 4 start frequency in Hz',
          'pmtr22'  : 'tremelo sine 4 end frequency in Hz',
          'pmtr23'  : 'tremelo sine 4 amp (0-1)',            
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 14000),
          'pmtr10'  : ('c', 100),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 1),
          'pmtr13'  : ('c', 16),
          'pmtr14'  : ('c', 1),
          
          'pmtr15'  : ('c', 2),
          'pmtr16'  : ('c', .125),
          'pmtr17'  : ('c', .5),
          
          'pmtr18'  : ('c', 32),
          'pmtr19'  : ('c', 16),
          'pmtr20'  : ('c', .9),

          'pmtr21'  : ('c', .43),
          'pmtr22'  : ('c', 200),
          'pmtr23'  : ('c', 0),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent        = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    ; get trem envl times
    iTremRateStart01 = p12
    iTremRateEnd01 = p13
    iTremAmp01  = p14
    
    iTremRateStart02 = p15
    iTremRateEnd02 = p16
    iTremAmp02  = p17
    
    iTremRateStart03 = p18
    iTremRateEnd03 = p19
    iTremAmp03  = p20
    
    iTremRateStart04 = p21
    iTremRateEnd04 = p22
    iTremAmp04  = p23

    ; create fq line segments
    kTremCf01   linseg   iTremRateStart01, iDur, iTremRateEnd01
    kTremCf02   linseg   iTremRateStart02, iDur, iTremRateEnd02
    kTremCf03   linseg   iTremRateStart03, iDur, iTremRateEnd03
    kTremCf04   linseg   iTremRateStart04, iDur, iTremRateEnd04

    ; create audio rate envelopes
    ; norm b/n 0 and 1; scale by amp; sihft by 1 lt amp; if amp 0 out is 1
    aTrem01     poscil 1, kTremCf01, 1
    aTrem01     = (((aTrem01 + 1) * .5) * iTremAmp01) + (1 - iTremAmp01)
    
    aTrem02     poscil 1, kTremCf02, 1
    aTrem02     = (((aTrem02 + 1) * .5) * iTremAmp02) + (1 - iTremAmp02)

    aTrem03     poscil 1, kTremCf03, 1
    aTrem03     = (((aTrem03 + 1) * .5) * iTremAmp03) + (1 - iTremAmp03)

    aTrem04     poscil 1, kTremCf04, 1
    aTrem04     = (((aTrem04 + 1) * .5) * iTremAmp04) + (1 - iTremAmp04)

    iCutoffStart = p9
    iCutoffEnd = p10
    kq = p11
    
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right  
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kFreq           linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            random -1, 1
    aSig            lowpass2     aSig, kFreq, kq 
    aMixSig     = aSig * kAmp * aTrem01 * aTrem02 * aTrem03 * aTrem04
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst111(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 111
        self.name = 'noiseAudioEnvelopeSquareQuad'
        self.info = 'A noise generator with an audio-rate square envelope, a proportional linear envelope, and a variable low-pass filter'
        self.auxNo = 17
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',

          'pmtr12'  : 'tremelo square 1 start frequency in Hz',
          'pmtr13'  : 'tremelo square 1 end frequency in Hz',
          'pmtr14'  : 'tremelo square 1 amp (0-1)',
          'pmtr15'  : 'tremelo square 2 start frequency in Hz',
          'pmtr16'  : 'tremelo square 2 end frequency in Hz',
          'pmtr17'  : 'tremelo square 2 amp (0-1)',
          'pmtr18'  : 'tremelo square 3 start frequency in Hz',
          'pmtr19'  : 'tremelo square 3 end frequency in Hz',
          'pmtr20'  : 'tremelo square 3 amp (0-1)',
          'pmtr21'  : 'tremelo square 4 start frequency in Hz',
          'pmtr22'  : 'tremelo square 4 end frequency in Hz',
          'pmtr23'  : 'tremelo square 4 amp (0-1)',         
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 14000),
          'pmtr10'  : ('c', 100),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 2),
          'pmtr13'  : ('c', 32),
          'pmtr14'  : ('c', 1),
          
          'pmtr15'  : ('c', 2),
          'pmtr16'  : ('c', .125),
          'pmtr17'  : ('c', .5),
          
          'pmtr18'  : ('c', 32),
          'pmtr19'  : ('c', 16),
          'pmtr20'  : ('c', 0),

          'pmtr21'  : ('c', .43),
          'pmtr22'  : ('c', 200),
          'pmtr23'  : ('c', 0),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent        = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    ; get trem envl times
    iTremRateStart01 = p12
    iTremRateEnd01 = p13
    iTremAmp01  = p14
    
    iTremRateStart02 = p15
    iTremRateEnd02 = p16
    iTremAmp02  = p17
    
    iTremRateStart03 = p18
    iTremRateEnd03 = p19
    iTremAmp03  = p20
    
    iTremRateStart04 = p21
    iTremRateEnd04 = p22
    iTremAmp04  = p23

    ; create fq line segments
    kTremCf01   linseg   iTremRateStart01, iDur, iTremRateEnd01
    kTremCf02   linseg   iTremRateStart02, iDur, iTremRateEnd02
    kTremCf03   linseg   iTremRateStart03, iDur, iTremRateEnd03
    kTremCf04   linseg   iTremRateStart04, iDur, iTremRateEnd04
 
    iTable      = 5 ; hi rez square wave
    
    ; create audio rate envelopes
    ; norm b/n 0 and 1; scale by amp; sihft by 1 lt amp; if amp 0 out is 1
    aTrem01     oscili 1, kTremCf01, iTable
    aTrem01     = (((aTrem01 + 1) * .5) * iTremAmp01) + (1 - iTremAmp01)
    
    aTrem02     oscili 1, kTremCf02, iTable
    aTrem02     = (((aTrem02 + 1) * .5) * iTremAmp02) + (1 - iTremAmp02)

    aTrem03     oscili 1, kTremCf03, iTable
    aTrem03     = (((aTrem03 + 1) * .5) * iTremAmp03) + (1 - iTremAmp03)

    aTrem04     oscili 1, kTremCf04, iTable
    aTrem04     = (((aTrem04 + 1) * .5) * iTremAmp04) + (1 - iTremAmp04)

    iCutoffStart = p9
    iCutoffEnd = p10
    kq = p11
    
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right  
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kFreq           linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            random -1, 1
    aSig            lowpass2     aSig, kFreq, kq 
    aMixSig     = aSig * kAmp * aTrem01 * aTrem02 * aTrem03 * aTrem04
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
class Inst130(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 130
        self.name = 'samplerAudioEnvelopeSineQuad'
        self.info = 'A sampler with an audio-rate sine summed envelope, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 19
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          
          'pmtr14'  : 'tremelo sine 1 start frequency in Hz',
          'pmtr15'  : 'tremelo sine 1 end frequency in Hz',
          'pmtr16'  : 'tremelo sine 1 amp (0-1)',
          'pmtr17'  : 'tremelo sine 2 start frequency in Hz',
          'pmtr18'  : 'tremelo sine 2 end frequency in Hz',
          'pmtr19'  : 'tremelo sine 2 amp (0-1)',
          'pmtr20'  : 'tremelo sine 3 start frequency in Hz',
          'pmtr21'  : 'tremelo sine 3 end frequency in Hz',
          'pmtr22'  : 'tremelo sine 3 amp (0-1)',
          'pmtr23'  : 'tremelo sine 4 start frequency in Hz',
          'pmtr24'  : 'tremelo sine 4 end frequency in Hz',
          'pmtr25'  : 'tremelo sine 4 amp (0-1)',            
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),

          'pmtr14'  : ('c', 32),
          'pmtr15'  : ('c', 16),
          'pmtr16'  : ('c', 1),
          
          'pmtr17'  : ('c', 2),
          'pmtr18'  : ('c', .125),
          'pmtr19'  : ('c', .5),
          
          'pmtr20'  : ('c', 32),
          'pmtr21'  : ('c', 16),
          'pmtr22'  : ('c', 0),

          'pmtr23'  : ('c', .43),
          'pmtr24'  : ('c', 200),
          'pmtr25'  : ('c', 0),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path

    ; get trem envl times
    iTremRateStart01 = p14
    iTremRateEnd01 = p15
    iTremAmp01  = p16
    
    iTremRateStart02 = p17
    iTremRateEnd02 = p18
    iTremAmp02  = p19
    
    iTremRateStart03 = p20
    iTremRateEnd03 = p21
    iTremAmp03  = p22
    
    iTremRateStart04 = p23
    iTremRateEnd04 = p24
    iTremAmp04  = p25

    ; create fq line segments
    kTremCf01   linseg   iTremRateStart01, iDur, iTremRateEnd01
    kTremCf02   linseg   iTremRateStart02, iDur, iTremRateEnd02
    kTremCf03   linseg   iTremRateStart03, iDur, iTremRateEnd03
    kTremCf04   linseg   iTremRateStart04, iDur, iTremRateEnd04

    iTable = 1 ; hi rez sine wave

    ; create audio rate envelopes
    ; norm b/n 0 and 1; scale by amp; sihft by 1 lt amp; if amp 0 out is 1
    aTrem01     poscil 1, kTremCf01, iTable
    aTrem01     = (((aTrem01 + 1) * .5) * iTremAmp01) + (1 - iTremAmp01)
    
    aTrem02     poscil 1, kTremCf02, iTable
    aTrem02     = (((aTrem02 + 1) * .5) * iTremAmp02) + (1 - iTremAmp02)

    aTrem03     poscil 1, kTremCf03, iTable
    aTrem03     = (((aTrem03 + 1) * .5) * iTremAmp03) + (1 - iTremAmp03)

    aTrem04     poscil 1, kTremCf04, iTable
    aTrem04     = (((aTrem04 + 1) * .5) * iTremAmp04) + (1 - iTremAmp04)
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            soundin  iSamplePath, iSkiptime   
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * kAmp * aTrem01 * aTrem02 * aTrem03 * aTrem04
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst131(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 131
        self.name = 'samplerAudioEnvelopeSquareQuad'
        self.info = 'A sampler with an audio-rate square envelope, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 19
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          
          'pmtr14'  : 'tremelo sine 1 start frequency in Hz',
          'pmtr15'  : 'tremelo sine 1 end frequency in Hz',
          'pmtr16'  : 'tremelo sine 1 amp (0-1)',
          'pmtr17'  : 'tremelo sine 2 start frequency in Hz',
          'pmtr18'  : 'tremelo sine 2 end frequency in Hz',
          'pmtr19'  : 'tremelo sine 2 amp (0-1)',
          'pmtr20'  : 'tremelo sine 3 start frequency in Hz',
          'pmtr21'  : 'tremelo sine 3 end frequency in Hz',
          'pmtr22'  : 'tremelo sine 3 amp (0-1)',
          'pmtr23'  : 'tremelo sine 4 start frequency in Hz',
          'pmtr24'  : 'tremelo sine 4 end frequency in Hz',
          'pmtr25'  : 'tremelo sine 4 amp (0-1)',            
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),

          'pmtr14'  : ('c', 32),
          'pmtr15'  : ('c', 16),
          'pmtr16'  : ('c', 1),
          
          'pmtr17'  : ('c', 2),
          'pmtr18'  : ('c', .125),
          'pmtr19'  : ('c', .5),
          
          'pmtr20'  : ('c', 32),
          'pmtr21'  : ('c', 16),
          'pmtr22'  : ('c', 0),

          'pmtr23'  : ('c', .43),
          'pmtr24'  : ('c', 200),
          'pmtr25'  : ('c', 0),          
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path

    ; get trem envl times
    iTremRateStart01 = p14
    iTremRateEnd01 = p15
    iTremAmp01  = p16
    
    iTremRateStart02 = p17
    iTremRateEnd02 = p18
    iTremAmp02  = p19
    
    iTremRateStart03 = p20
    iTremRateEnd03 = p21
    iTremAmp03  = p22
    
    iTremRateStart04 = p23
    iTremRateEnd04 = p24
    iTremAmp04  = p25

    ; create fq line segments
    kTremCf01   linseg   iTremRateStart01, iDur, iTremRateEnd01
    kTremCf02   linseg   iTremRateStart02, iDur, iTremRateEnd02
    kTremCf03   linseg   iTremRateStart03, iDur, iTremRateEnd03
    kTremCf04   linseg   iTremRateStart04, iDur, iTremRateEnd04

    iTable  = 5 ; hi rez square wave

    ; create audio rate envelopes
    ; norm b/n 0 and 1; scale by amp; sihft by 1 lt amp; if amp 0 out is 1
    aTrem01     oscili 1, kTremCf01, iTable
    aTrem01     = (((aTrem01 + 1) * .5) * iTremAmp01) + (1 - iTremAmp01)
    
    aTrem02     oscili 1, kTremCf02, iTable
    aTrem02     = (((aTrem02 + 1) * .5) * iTremAmp02) + (1 - iTremAmp02)

    aTrem03     oscili 1, kTremCf03, iTable
    aTrem03     = (((aTrem03 + 1) * .5) * iTremAmp03) + (1 - iTremAmp03)

    aTrem04     oscili 1, kTremCf04, iTable
    aTrem04     = (((aTrem04 + 1) * .5) * iTremAmp04) + (1 - iTremAmp04)
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            soundin  iSamplePath, iSkiptime   
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * kAmp * aTrem01 * aTrem02 * aTrem03 * aTrem04
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
class Inst132(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 132
        self.name = 'samplerAudioFileEnvelopeFilter'
        self.info = 'A sampler with an audio-rate envelope generated by another audio file, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 12
        self.postMapAmp = (0, 12, 'linear') # a bit louder than audio file
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
        
          'pmtr12'  : 'analysis audio file start time',
          'pmtr13'  : 'analysis audio file file path',
          'pmtr14'  : 'analysis audio play back speed',          

          'pmtr15'  : 'analysis low-pass filter cutoff frequency in Hz',            

          'pmtr16'  : 'source audio file start time',
          'pmtr17'  : 'source audio file path',
          'pmtr18'  : 'source audio play back speed',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr14'  : ('c', 2),
          
          'pmtr15'  : ('c', 40),
          
          'pmtr16'  : ('c', 0),
          'pmtr17'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr18'  : ('c', .75),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11

    iAnalysisSkiptime = p12
    iAnalysisSamplePath = p13
    iAnalysisPitch = p14

    iAnalysisCutoff = p15
    
    iSrcSkiptime = p16
    iSrcSamplePath = p17
    iSrcPitch = p18
    
    ; get audio stream for analysis
    aAnalysis  diskin    iAnalysisSamplePath, iAnalysisPitch, iAnalysisSkiptime, 0

    ; normalize audio file b/n -1 and 1, assume 16 bit
    aAnalysis   = aAnalysis * .00003

    ; analysis method done in all vocoders here
    ; must scale signal 
    aAmpCh01        = abs(aAnalysis)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        = aAmpCh01 * 2                               ; increase signal power
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    aSig            diskin  iSrcSamplePath, iSrcPitch, iSrcSkiptime, 0

    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * kAmp * aAmpCh01
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst133(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 133
        self.name = 'samplerAudioFileEnvelopeFollow'
        self.info = 'A sampler with an audio-rate envelope generated by another audio file, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 13
        self.postMapAmp = (0, 22, 'linear') # a bit louder than audio file
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
        
          'pmtr12'  : 'analysis audio file start time',
          'pmtr13'  : 'analysis audio file file path',
          'pmtr14'  : 'analysis audio play back speed',          

          'pmtr15'  : 'analysis follow attack time in seconds',         
          'pmtr16'  : 'analysis follow decay time in seconds',        

          'pmtr17'  : 'source audio file start time',
          'pmtr18'  : 'source audio file path',
          'pmtr19'  : 'source audio play back speed',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr14'  : ('c', 2),
          
          'pmtr15'  : ('c', .1),
          'pmtr16'  : ('c', .1),
          
          'pmtr17'  : ('c', 0),
          'pmtr18'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr19'  : ('c', .75),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11

    iAnalysisSkiptime = p12
    iAnalysisSamplePath = p13
    iAnalysisPitch = p14

    iFollowAttack = p15
    iFollowDecay = p16
    
    iSrcSkiptime = p17
    iSrcSamplePath = p18
    iSrcPitch = p19
    
    ; get audio stream for analysis
    aAnalysis  diskin    iAnalysisSamplePath, iAnalysisPitch, iAnalysisSkiptime, 0

    ; normalize audio file b/n -1 and 1, assume 16 bit
    aAnalysis   = aAnalysis * .00003

    ; analysis method uses follow 2
    aAmpCh01        follow2  aAnalysis, iFollowAttack, iFollowDecay
    
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    aSig            diskin  iSrcSamplePath, iSrcPitch, iSrcSkiptime, 0

    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * kAmp * aAmpCh01
    
""" % str(self.instNo)









#-----------------------------------------------------------------||||||||||||--
# vari speed sampler

class Inst230(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 230
        self.name = 'samplerVarispeed'
        self.info = 'A sampler with a variable playback speed, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 9
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          
          'pmtr14'  : 'file play back start speed (1 is normal)',
          'pmtr15'  : 'file play back end speed (1 is normal)',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),

          'pmtr14'  : ('c', .5),
          'pmtr15'  : ('c', .75),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path
    
    iPitchStart = p14    
    iPitchEnd = p15

    kPitch      linseg   iPitchStart, iDur, iPitchEnd
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            diskin  iSamplePath, kPitch, iSkiptime, 0
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply tremelo, then macro envelope
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst231(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 231
        self.name = 'samplerVarispeedAudioSine'
        self.info = 'A sampler with a sine-controlled playback speed, a proportional linear envelope, and a variable low-pass filter.'
        self.auxNo = 10
        self.postMapAmp = (0, 1, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          
          'pmtr14'  : 'file play back min speed (1 is normal)',
          'pmtr15'  : 'file play back max speed (1 is normal)',
          'pmtr16'  : 'file play back oscillation speed in Hz',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 16000),
          'pmtr10'  : ('c', 2000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),

          'pmtr14'  : ('c', .25),
          'pmtr15'  : ('c', 1.25),
          'pmtr16'  : ('c', 200),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path
    
    iPitchMin = p14  
    iPitchMax = p15
    iPitchRate = p16

    iTable = 1 ; hi rez sine wave
    
    ; norm b/n 0 and 1, scale
    kPitch      poscil   1, iPitchRate, iTable
    kPitch      = (((kPitch  + 1) * .5) * (iPitchMax-iPitchMin)) + iPitchMin
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    aAmp            linen        iAmp, iAttack, iDur, iRelease
    
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd

    aSig            diskin  iSamplePath, kPitch, iSkiptime, 0
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 
    aSig            = aSig * aAmp
    aMixSig     = aSig
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst232(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 232
        self.name = 'samplerVarispeedReverb'
        self.info = 'A sampler with a variable playback speed that generates a wet reverb within a proportional linear envelope and a variable low-pass filter.'
        self.auxNo = 12
        self.postMapAmp = (0, 9, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          
          'pmtr14'  : 'file play back start speed (1 is normal)',
          'pmtr15'  : 'file play back end speed (1 is normal)',

          'pmtr16'  : 'reverb start time in seconds',
          'pmtr17'  : 'reverb end time in seconds',
          'pmtr18'  : 'reverb diffusion (0-1)',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 100),
          'pmtr10'  : ('c', 2000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),

          'pmtr14'  : ('c', 1),
          'pmtr15'  : ('c', .5),

          'pmtr16'  : ('c', 20),
          'pmtr17'  : ('c', .5),
          'pmtr18'  : ('c', 0),  # non zero values seem to add hi fq noise
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path
    
    iPitchStart = p14    
    iPitchEnd = p15

    iReverbTimeStart = p16
    iReverbTimeEnd = p17
    iReverbDif = p18
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    kPitch      linseg   iPitchStart, iDur, iPitchEnd
    aSig            diskin   iSamplePath, kPitch, iSkiptime, 0
    
    ; get all wet signal, scale input signal
    kReverbTime      linseg   iReverbTimeStart, iDur, iReverbTimeEnd
    aSig                 nreverb      aSig*.25, kReverbTime, iReverbDif
    
    ; low pass applied to reverb
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply macro envelope
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)


#-----------------------------------------------------------------||||||||||||--
class Inst233(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 233
        self.name = 'samplerVarispeedDistort'
        self.info = 'A sampler with a variable playback speed distorted by a resonant low-pass filter within a proportional linear envelope and a variable low-pass filter.'
        self.auxNo = 15
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 1
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          
          'pmtr14'  : 'file play back start speed (1 is normal)',
          'pmtr15'  : 'file play back end speed (1 is normal)',

          'pmtr16'  : 'resonant filter start cutoff frequency in Hz',
          'pmtr17'  : 'resonant filter end cutoff frequency in Hz',
          'pmtr18'  : 'resonant filter start resonance (0-2)',
          'pmtr19'  : 'resonant filter end resonance (0-2)',
          'pmtr20'  : 'resonant filter start distortion (0-10)',
          'pmtr21'  : 'resonant filter end distortion (0-10)',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .95),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 10000),
          'pmtr10'  : ('c', 2000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),

          'pmtr14'  : ('c', 1),
          'pmtr15'  : ('c', 1),

          'pmtr16'  : ('c', 1000),
          'pmtr17'  : ('c', 6000),
          'pmtr18'  : ('c', .8),
          'pmtr19'  : ('c', .2),
          'pmtr20'  : ('c', 100),
          'pmtr21'  : ('c', 1),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path
    
    iPitchStart = p14    
    iPitchEnd = p15

    iResonCutoffStart = p16
    iResonCutoffEnd = p17
    iResonStart = p18
    iResonEnd = p19
    iDistortionStart = p20
    iDistortionEnd = p21
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 
    kAmp            linen        iAmp, iAttack, iDur, iRelease
    
    kPitch      linseg   iPitchStart, iDur, iPitchEnd
    aSig            diskin   iSamplePath, kPitch, iSkiptime, 0
    
    ; normalize audio file b/n -1 and 1, assume 16 bit
    aSig            = aSig * .00003
    
    ; paramterers for lpf18
    
    kResonCutoff     linseg   iResonCutoffStart, iDur, iResonCutoffEnd
    kReson           linseg   iResonStart, iDur, iResonEnd
    kDistortion      linseg   iDistortionStart, iDur, iDistortionEnd
    aSig                 lpf18      aSig, kResonCutoff, kReson, kDistortion
    
    ; low pass applied
    kLpfCf      linseg   iCutoffStart, iDur, iCutoffEnd
    aSig            lowpass2     aSig, kLpfCf, iLpfQ 

    ; apply macro envelope
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
class Inst234(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 234
        self.name = 'samplerVarispeedSahNoiseDistort'
        self.info = 'A sampler with third order sample and hold filter, a variable high-pass filter, a proportional linear envelope, a resonant low-pass filter, and a variable low-pass filter.'
        self.auxNo = 22
        self.postMapAmp = (0, 90, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'low-pass filter start cutoff frequency in Hz',
          'pmtr10'  : 'low-pass filter end cutoff frequency in Hz',
          'pmtr11'  : 'low-pass filter resonance between 1 and 500',
          'pmtr12'  : 'start time within audio file',
          'pmtr13'  : 'file path to desired sound file',
          
          'pmtr14'  : 'file play back start speed (1 is normal)',
          'pmtr15'  : 'file play back end speed (1 is normal)',
          
          'pmtr16'  : 'high-pass filter start cutoff frequency in Hz',
          'pmtr17'  : 'high-pass filter end cutoff frequency in Hz',          
          'pmtr18'  : 'first order rate low in Hz',
          'pmtr19'  : 'first order rate high in Hz',
          'pmtr20'  : 'second order rate low in Hz',
          'pmtr21'  : 'second order rate high in Hz',
          'pmtr22'  : 'third order rate in Hz',
          
          'pmtr23'  : 'resonant filter start cutoff frequency in Hz',
          'pmtr24'  : 'resonant filter end cutoff frequency in Hz',
          'pmtr25'  : 'resonant filter start resonance (0-2)',
          'pmtr26'  : 'resonant filter end resonance (0-2)',
          'pmtr27'  : 'resonant filter start distortion (0-10)',
          'pmtr28'  : 'resonant filter end distortion (0-10)',        
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .5),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 18000),
          'pmtr10'  : ('c', 8000),
          'pmtr11'  : ('c', 1),
          'pmtr12'  : ('c', 0),
          'pmtr13'  : ('sampleSelect', ('metal01.aif', 'latch01.aif')),
          
          'pmtr14'  : ('c', .25),
          'pmtr15'  : ('c', 3),
          
          'pmtr16'  : ('c', 20),
          'pmtr17'  : ('c', 30),
          'pmtr18'  : ('c', 400),
          'pmtr19'  : ('c', 600),
          'pmtr20'  : ('c', 10),
          'pmtr21'  : ('c', 20),
          'pmtr22'  : ('c', .5),          
          
          'pmtr23'  : ('c', 1000),
          'pmtr24'  : ('c', 6000),
          'pmtr25'  : ('c', .6),
          'pmtr26'  : ('c', .1),
          'pmtr27'  : ('c', 50),
          'pmtr28'  : ('c', 1),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval
    iCutoffStart = p9
    iCutoffEnd = p10
    iLpfQ = p11
    iSkiptime = p12
    iSamplePath = p13    ; sample as complete path

    iPitchStart = p14    
    iPitchEnd = p15

    iHpfStart = p16
    iHpfEnd = p17

    iFirstLow = p18
    iFirstHigh = p19
    iSecondLow = p20
    iSecondHigh = p21
    iThird = p22

    iResonCutoffStart = p23
    iResonCutoffEnd = p24
    iResonStart = p25
    iResonEnd = p26
    iDistortionStart = p27
    iDistortionEnd = p28

    ; select a table read from
    
    iTable = 15

    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    kAmp            linen        iAmp, iAttack, iDur, iRelease
    kfreqLpf        linseg   iCutoffStart, iDur, iCutoffEnd
    kfreqHpf        linseg   iHpfStart, iDur, iHpfEnd

    ; sample signal and noise drivers
    ; normalize audio file b/n -1 and 1, assume 16 bit, for lpf18

    kPitch      linseg   iPitchStart, iDur, iPitchEnd
    aSig            diskin   iSamplePath, kPitch, iSkiptime, 0
    aSig            = aSig * .00003

    ; sah noise signals
    
    aNoiseFirst      random   iFirstLow, iFirstHigh
    aNoiseSecond     random   iSecondLow, iSecondHigh

    aGateC       oscili 1, iThird, iTable    ; table is a phasor from - 1 to 1
    aRateB       samphold aNoiseSecond, aGateC
    
    aGateB       oscili 1, aRateB, iTable
    aRateA       samphold aNoiseFirst, aGateB
    
    ; samplehold holds value when gateValue is zero
    aGateA      oscili 1, aRateA, iTable
    aSig            samphold     aSig, aGateA

    ; filters
    aSig            butterhp     aSig, kfreqHpf 
    aSig            lowpass2     aSig, kfreqLpf, iLpfQ 
    
    ; paramterers for lpf18
    
    kResonCutoff     linseg   iResonCutoffStart, iDur, iResonCutoffEnd
    kReson           linseg   iResonStart, iDur, iResonEnd
    kDistortion      linseg   iDistortionStart, iDur, iDistortionEnd
    aSig                 lpf18      aSig, kResonCutoff, kReson, kDistortion
    
    aMixSig   = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
class Inst240(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 240
        self.name = 'vocodeVcoOctScale'
        self.info = 'An eight channel vocoder with scaled mapping and a variable waveform generator.'
        self.auxNo = 16
        self.postMapAmp = (0, 20, 'linear') # amps from experiment
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',
          
          'pmtr12'  : 'vco wave form index integer (1-3)',
          'pmtr13'  : 'vco start width (0-2)',
          'pmtr14'  : 'vco end width (0-2)',
          
          'pmtr15'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr16'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr17'  : 'analysis frequency base in Hz',
          'pmtr18'  : 'analysis frequency scalar',        

          'pmtr19'  : 'generator frequency base in Hz',
          'pmtr20'  : 'generator frequency scalar',       

          'pmtr21'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr22'  : 'low-pass filter end cutoff frequency in Hz',
          }
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),
          
          'pmtr12'  : ('c', 1),
          'pmtr13'  : ('c', 0.1),
          'pmtr14'  : ('c', 0.9),

          'pmtr15'  : ('c', 40), # analysis cut-off fq
          'pmtr16'  : ('c', 40), # band width, 20 is well pitched
          
          'pmtr17'  : ('c', 400),
          'pmtr18'  : ('c', 1.333333333333),

          'pmtr19'  : ('c', 100),
          'pmtr20'  : ('c', 1.666666666666),

          'pmtr21'  : ('c', 100),
          'pmtr22'  : ('c', 4000),
          }
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11
    
    iVcoWaveForm = p12
    iVcoWidthStart = p13     
    iVcoWidthEnd = p14  

    iAnalysisCutoff = p15
    iAnalysisQ = p16

    iAnalysisFqScalar = p18
    iAnalysisCf01 = p17 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p17 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p17 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p17 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p17 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p17 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p17 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p17 * (iAnalysisFqScalar ^ 7)

    iGeneratorFqScalar = p20
    iGeneratorCf01 = p19 * (iGeneratorFqScalar ^ 0)
    iGeneratorCf02 = p19 * (iGeneratorFqScalar ^ 1)
    iGeneratorCf03 = p19 * (iGeneratorFqScalar ^ 2)
    iGeneratorCf04 = p19 * (iGeneratorFqScalar ^ 3)
    iGeneratorCf05 = p19 * (iGeneratorFqScalar ^ 4)
    iGeneratorCf06 = p19 * (iGeneratorFqScalar ^ 5)
    iGeneratorCf07 = p19 * (iGeneratorFqScalar ^ 6)
    iGeneratorCf08 = p19 * (iGeneratorFqScalar ^ 7)

    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p18, iDur, p19
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0
    
    ; isolate channels by filters; dont need to scale by 2 here
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; vco signal at fq, scale by analysis
    kVcoWidth   linseg   iVcoWidthStart, iDur, iVcoWidthEnd   
    
    aGen01      vco   aAmpCh01, iGeneratorCf01, iVcoWaveForm, kVcoWidth, iTable
    aGen02      vco   aAmpCh02, iGeneratorCf02, iVcoWaveForm, kVcoWidth, iTable
    aGen03      vco   aAmpCh03, iGeneratorCf03, iVcoWaveForm, kVcoWidth, iTable
    aGen04      vco   aAmpCh04, iGeneratorCf04, iVcoWaveForm, kVcoWidth, iTable
    aGen05      vco   aAmpCh05, iGeneratorCf05, iVcoWaveForm, kVcoWidth, iTable
    aGen06      vco   aAmpCh06, iGeneratorCf06, iVcoWaveForm, kVcoWidth, iTable
    aGen07      vco   aAmpCh07, iGeneratorCf07, iVcoWaveForm, kVcoWidth, iTable
    aGen08      vco   aAmpCh08, iGeneratorCf08, iVcoWaveForm, kVcoWidth, iTable
    
    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)



#-----------------------------------------------------------------||||||||||||--
# 8 ch
class Inst241(InstrumentCsound):
    def __init__(self):
        InstrumentCsound.__init__(self)
        self.instNo = 241
        self.name = 'vocodeVcoOctScaleRemap'
        self.info = 'An eight channel vocoder and a variable waveform generator.'
        self.auxNo = 32
        self.postMapAmp = (0, 20, 'linear') # assume amps not greater tn 10
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrInfo = {
          'pmtr7'   : 'sustain percent within unit interval',
          'pmtr8'   : 'sustain center within unit interval',
          'pmtr9'   : 'analysis audio file start time',
          'pmtr10'  : 'analysis file path to desired sound file',
          'pmtr11'  : 'analysis file play back speed',

          'pmtr12'  : 'vco wave form index integer (1-3)',
          'pmtr13'  : 'vco start width (0-2)',
          'pmtr14'  : 'vco end width (0-2)',

          'pmtr15'  : 'analysis low-pass filter cutoff frequency in Hz',
          'pmtr16'  : 'analysis band-pass bw (not q), from 10 to 500',

          'pmtr17'  : 'analysis frequency base in Hz',
          'pmtr18'  : 'analysis frequency scalar',        

          'pmtr19'  : 'generator frequency base in Hz',
          'pmtr20'  : 'generator frequency scalar',         

          'pmtr21'  : 'generator 1 channel frequency source (1-8)',
          'pmtr22'  : 'generator 2 channel frequency source (1-8)',           
          'pmtr23'  : 'generator 3 channel frequency source (1-8)',
          'pmtr24'  : 'generator 4 channel frequency source (1-8)',           
          'pmtr25'  : 'generator 5 channel frequency source (1-8)',
          'pmtr26'  : 'generator 6 channel frequency source (1-8)',           
          'pmtr27'  : 'generator 7 channel frequency source (1-8)',
          'pmtr28'  : 'generator 8 channel frequency source (1-8)',           

          'pmtr29'  : 'generator 1 post scale (0-1)',
          'pmtr30'  : 'generator 2 post scale (0-1)',           
          'pmtr31'  : 'generator 3 post scale (0-1)',
          'pmtr32'  : 'generator 4 post scale (0-1)',           
          'pmtr33'  : 'generator 5 post scale (0-1)',
          'pmtr34'  : 'generator 6 post scale (0-1)',           
          'pmtr35'  : 'generator 7 post scale (0-1)',
          'pmtr36'  : 'generator 8 post scale (0-1)',           

          'pmtr37'  : 'low-pass filter start cutoff frequency in Hz',
          'pmtr38'  : 'low-pass filter end cutoff frequency in Hz',
          }
          
        self.pmtrDefault = {
          'pmtr7'   : ('c', .9),
          'pmtr8'   : ('c', .5),
          'pmtr9'   : ('c', 0),
          'pmtr10'  : ('sampleSelect', ('drum01.aif', 'latch01.aif')),
          'pmtr11'  : ('c', 1),

          'pmtr12'  : ('c', 1),
          'pmtr13'  : ('c', 0.1),
          'pmtr14'  : ('c', 0.9),
          
          'pmtr15'  : ('c', 40), # analysis cut-off fq
          'pmtr16'  : ('c', 40), # band width, 20 is well pitched
          
          'pmtr17'  : ('c', 400),
          'pmtr18'  : ('c', 1.33333333333),

          'pmtr19'  : ('c', 100),
          'pmtr20'  : ('c', 1.6666666666),
          
          'pmtr21'  : ('c', 1),
          'pmtr22'  : ('c', 2),
          'pmtr23'  : ('c', 3),
          'pmtr24'  : ('c', 4),
          'pmtr25'  : ('c', 5),
          'pmtr26'  : ('c', 6),
          'pmtr27'  : ('c', 7),
          'pmtr28'  : ('c', 8),
          
          'pmtr29'  : ('c', 1),
          'pmtr30'  : ('c', 1),
          'pmtr31'  : ('c', 1),
          'pmtr32'  : ('c', 1),
          'pmtr33'  : ('c', 1),
          'pmtr34'  : ('c', 1),
          'pmtr35'  : ('c', 1),
          'pmtr36'  : ('c', 1),
          
          'pmtr37'  : ('c', 100),
          'pmtr38'  : ('c', 4000),
          }
          
        self.author = 'athenaCL native' # attribution
        self.orcCode = """
instr %s
    iDur = p3
    iAmp    = ampdb(p4)
    iFreq = cpspch(p5)
    iPan    = p6

    iSusPcent = p7 ; time of sustain section w/n unit interval
    iSusCenterPcent = p8 ; center of sustain sections w/n unit interval

    iSkiptime = p9
    iSamplePath = p10    ; sample as complete path
    iPitch = p11
    
    iVcoWaveForm = p12
    iVcoWidthStart = p13     
    iVcoWidthEnd = p14  

    iAnalysisCutoff = p15
    iAnalysisQ = p16

    iAnalysisFqScalar = p18
    iAnalysisCf01 = p17 * (iAnalysisFqScalar ^ 0)
    iAnalysisCf02 = p17 * (iAnalysisFqScalar ^ 1)
    iAnalysisCf03 = p17 * (iAnalysisFqScalar ^ 2)
    iAnalysisCf04 = p17 * (iAnalysisFqScalar ^ 3)
    iAnalysisCf05 = p17 * (iAnalysisFqScalar ^ 4)
    iAnalysisCf06 = p17 * (iAnalysisFqScalar ^ 5)
    iAnalysisCf07 = p17 * (iAnalysisFqScalar ^ 6)
    iAnalysisCf08 = p17 * (iAnalysisFqScalar ^ 7)
    
    ; integer values tt determine which channel goes where
    iGeneratorSrcCh01 = p21 - 1  ; values in src channel become exponents
    iGeneratorSrcCh02 = p22 - 1
    iGeneratorSrcCh03 = p23 - 1
    iGeneratorSrcCh04 = p24 - 1
    iGeneratorSrcCh05 = p25 - 1 
    iGeneratorSrcCh06 = p26 - 1
    iGeneratorSrcCh07 = p27 - 1
    iGeneratorSrcCh08 = p28 - 1

    ; can re-scale generator mapping, produce normal fqs prior to remap
    ; amp will stay the same, based on order number; changes fqs applied
    ; with number
    iGeneratorFqScalar = p20
    iGeneratorCf01 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh01)
    iGeneratorCf02 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh02)
    iGeneratorCf03 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh03)
    iGeneratorCf04 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh04)
    iGeneratorCf05 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh05)
    iGeneratorCf06 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh06)
    iGeneratorCf07 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh07)
    iGeneratorCf08 = p19 * (iGeneratorFqScalar ^ iGeneratorSrcCh08)

    ; making these k-rate for envelope scaling
    kGeneratorPost01 = p29
    kGeneratorPost02 = p30
    kGeneratorPost03 = p31
    kGeneratorPost04 = p32
    kGeneratorPost05 = p33
    kGeneratorPost06 = p34
    kGeneratorPost07 = p35
    kGeneratorPost08 = p36
  
    ; setup variable low pass filter from start to end
    kLpfCf      linseg   p37, iDur, p38
  
    ; envl calculations; take percentage of remaining duration
    ; scale by the center percent for left, 1- center precent for right
    
    iAttack     = ((1 - iSusPcent) * iSusCenterPcent) * iDur 
    iRelease        = ((1 - iSusPcent) * (1-iSusCenterPcent)) * iDur 

    ; create analysis of amp following; double filter 
    aSrc            diskin   iSamplePath, iPitch, iSkiptime, 0

    ; isolate channels by filters
    aAmpCh01        butterbp     aSrc, iAnalysisCf01, iAnalysisQ
    aAmpCh01        = abs(aAmpCh01)
    aAmpCh01        butterlp     aAmpCh01, iAnalysisCutoff
    aAmpCh01        tone         aAmpCh01, iAnalysisCutoff   ; one pole lpf

    aAmpCh02        butterbp     aSrc, iAnalysisCf02, iAnalysisQ
    aAmpCh02        = abs(aAmpCh02)
    aAmpCh02        butterlp     aAmpCh02, iAnalysisCutoff
    aAmpCh02        tone         aAmpCh02, iAnalysisCutoff   ; one pole lpf

    aAmpCh03        butterbp     aSrc, iAnalysisCf03, iAnalysisQ
    aAmpCh03        = abs(aAmpCh03)
    aAmpCh03        butterlp     aAmpCh03, iAnalysisCutoff
    aAmpCh03        tone         aAmpCh03, iAnalysisCutoff   ; one pole lpf

    aAmpCh04        butterbp     aSrc, iAnalysisCf04, iAnalysisQ
    aAmpCh04        = abs(aAmpCh04)
    aAmpCh04        butterlp     aAmpCh04, iAnalysisCutoff
    aAmpCh04        tone         aAmpCh04, iAnalysisCutoff   ; one pole lpf

    aAmpCh05        butterbp     aSrc, iAnalysisCf05, iAnalysisQ
    aAmpCh05        = abs(aAmpCh05)
    aAmpCh05        butterlp     aAmpCh05, iAnalysisCutoff
    aAmpCh05        tone         aAmpCh05, iAnalysisCutoff   ; one pole lpf

    aAmpCh06        butterbp     aSrc, iAnalysisCf06, iAnalysisQ
    aAmpCh06        = abs(aAmpCh06)
    aAmpCh06        butterlp     aAmpCh06, iAnalysisCutoff
    aAmpCh06        tone         aAmpCh06, iAnalysisCutoff   ; one pole lpf

    aAmpCh07        butterbp     aSrc, iAnalysisCf07, iAnalysisQ
    aAmpCh07        = abs(aAmpCh07)
    aAmpCh07        butterlp     aAmpCh07, iAnalysisCutoff
    aAmpCh07        tone         aAmpCh07, iAnalysisCutoff   ; one pole lpf

    aAmpCh08        butterbp     aSrc, iAnalysisCf08, iAnalysisQ
    aAmpCh08        = abs(aAmpCh08)
    aAmpCh08        butterlp     aAmpCh08, iAnalysisCutoff
    aAmpCh08        tone         aAmpCh08, iAnalysisCutoff   ; one pole lpf

    iTable      = 1     ; hi rez sine wave

    ; vco signal at fq, scale by analysis
    kVcoWidth   linseg   iVcoWidthStart, iDur, iVcoWidthEnd   
    
    aGen01      vco   aAmpCh01, iGeneratorCf01, iVcoWaveForm, kVcoWidth, iTable
    aGen01      = aGen01 * kGeneratorPost01
    aGen02      vco   aAmpCh02, iGeneratorCf02, iVcoWaveForm, kVcoWidth, iTable
    aGen02      = aGen02 * kGeneratorPost02
    aGen03      vco   aAmpCh03, iGeneratorCf03, iVcoWaveForm, kVcoWidth, iTable
    aGen03      = aGen03 * kGeneratorPost03
    aGen04      vco   aAmpCh04, iGeneratorCf04, iVcoWaveForm, kVcoWidth, iTable
    aGen04      = aGen04 * kGeneratorPost04
    aGen05      vco   aAmpCh05, iGeneratorCf05, iVcoWaveForm, kVcoWidth, iTable
    aGen05      = aGen05 * kGeneratorPost05
    aGen06      vco   aAmpCh06, iGeneratorCf06, iVcoWaveForm, kVcoWidth, iTable
    aGen06      = aGen06 * kGeneratorPost06
    aGen07      vco   aAmpCh07, iGeneratorCf07, iVcoWaveForm, kVcoWidth, iTable
    aGen07      = aGen07 * kGeneratorPost07
    aGen08      vco   aAmpCh08, iGeneratorCf08, iVcoWaveForm, kVcoWidth, iTable
    aGen08      = aGen08 * kGeneratorPost08

    ; mix all channels
    aSig            = (aGen01 + aGen02 + aGen03 + aGen04 + aGen05 + aGen06 + aGen07 + aGen08)

    ; apply lpf filter
    aSig            butterlp     aSig, kLpfCf

    ; generate outer envelope
    kAmp            linen        iAmp, iAttack, iDur, iRelease  
    aMixSig     = aSig * kAmp
    
""" % str(self.instNo)











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