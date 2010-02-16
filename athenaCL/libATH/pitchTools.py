#-----------------------------------------------------------------||||||||||||--
# Name:          pitch.py
# Purpose:       utility functions for pitch conversions shared by many modules.
#                    defines Pitch class, usefull for any pitch operation
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza, Jonathan Saggau
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

# this module should not import any lower level athenacl modules
import copy, math
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import error

_MOD = 'pitchTools.py'
# PRIMITIVE conversion utilities
# some similar conversion routines are fon in pitchPath.py
# might need to be consolidated in one place


REFdiaNameToPc = {
                    'a' : 9,
                    'b' : 11,
                    'c' : 0,
                    'd' : 2,
                    'e' : 4,
                    'f' : 5,
                    'g' : 7,
                    }

SYMqTone = '~'
SYMsharp = '#'
SYMflat = '$'

REFpcToName =   {0:'c',
                     1:'c%s' % SYMsharp,
                     2:'d',
                     3:'d%s' % SYMsharp,
                     4:'e',
                     5:'f',
                     6:'f%s' % SYMsharp,
                     7:'g',
                     8:'g%s' % SYMsharp,
                     9:'a',
                    10:'a%s' % SYMsharp,
                    11:'b',}


#-----------------------------------------------------------------||||||||||||--
# functions for processign pch values; requires very special handling

def splitOctPs(pitch):
    """this function is used in SC.py and elsewhere
    if a microtone is present, it will be passd in the ps

    >>> splitOctPs(23)
    (1, 11)
    """
    oct, ps = divmod(pitch, 12)
    oct = int(oct) # oct is always an int
    return oct, ps

# replacement fo splitOctPitch space that includes microtones
def splitPsReal(pitch):
    """micro should never be greater than one
    not sure if oct, pc should be converted to ints
    
    >>> splitPsReal(6.23)
    (0, 6, 0.2300...)
    """
    oct, psReal = divmod(pitch, 12)
    pc, micro = divmod(psReal, 1)
    oct = int(oct)
    pc = int(pc)
    return oct, pc, micro

def joinPsReal(oct, pc, micro):
    """used in clone.py to process octave from ps
    used in psToTempered:
    note: pc can be a full psReal beyond the scope of 0-11 ints

    >>> joinPsReal(4, 3, .018)
    51.018...
    """
    return (oct * 12) + pc + micro 

def _splitPch(pch, sigMicro=6):
    """takes string or float and converts to 3 part tuple
    microntones are given in fractional half steps, .5 being a quarter tone
    """
    oct = int(pch)
    junk, pcmicroFloat = divmod(pch, 1) # valid
    pcFloat = pcmicroFloat * 100 # has pc value in .020345, all but oct
    # necesarry to round here in order to avoid errors
    pcFloat = round(pcFloat, sigMicro) # convert 11.999999 to 12
    pc = int(pcFloat) # get int, do not round
    junk, micro = divmod(pcFloat, 1) # gets int, float part
    return oct, pc, micro

def _joinPch(pchTriple, sigMicro=6):
    """converts a PCH triple into a floating point value
    will round sig microtone values to sig micro digits
    one cent == .01, 4 sig digits is is .0001, cent/100
    """
    oct, pc, micro = pchTriple
    if micro != 0:
        micro = round(micro, sigMicro) # .5 is quarter tone
    pch = oct + ((pc + micro) / 100.0)
    return pch

def _normalizePch(pch):
    "takes a pch and corrects for > 12 errors in pc"
    oct, pc, micro = _splitPch(pch)
    #print 'pch = oct, pc, micro', pch, oct, pc, micro
    octMult, pc = splitOctPs(pc)
    adjOct = oct + octMult # octave of 0 keeps pch flat
    return _joinPch((adjOct, pc, micro))

def _splitTransposition(trans):
    """splits a transposition in half steps (5.0324) to octave, pc, micro 
    tuple
    microtones are given in fractional half steps, .5 being a quarter tone
    also works to split a pc with microtones into the appropriate form
    """
    direction = None
    if trans > 0: direction = '+'
    elif trans < 0: direction = '-'
    else: return (0, 0, 0), direction

    totTrans = abs(trans) # removies sign, keeps decimal
    # total nuymber of steps without micros (5.25 becomes 5) 
    transSteps, transMicro = divmod(totTrans, 1.0)
    transSteps = int(transSteps) # make int 1/2 steps

    transOct, transPc = divmod(transSteps, 12)    #no remainder needed here
    transOct = int(transOct)
    transPc = int(transPc)
    return (transOct, transPc, transMicro), direction

def _tripleCombine(a, b, direction='+', minMicro=.000001):
    "for adding PCH triples, doing mod 12 and carrying"
    octA, pcA, microA = a
    octB, pcB, microB = b
    # add micro, get pc carry
    if microA > minMicro or microB > minMicro:
        if direction == '+':
            microY = microA + microB
        elif direction == '-':
            microY = microA - microB
        pcYcarry, microY = divmod(microY, 1)
        pcYcarry = int(pcYcarry)
    else: # ignore very small micro
        microY = 0.0
        pcYcarry = int(0)
    # add pc, get oct carry after mod 12
    if direction == '+':
        pcY = (pcA + pcB) + pcYcarry
    elif direction == '-':
        pcY = (pcA - pcB) + pcYcarry # pc cary already neg from divmod
    octYcarry, pcY = splitOctPs(pcY)
    # add oct 
    if direction == '+':
        octY = (octA + octB) + octYcarry
    elif direction == '-':
        octY = (octA - octB) + octYcarry     # cary is already neg from divmod
    return (octY, pcY, microY)



# this was used to add an octave value to a psReal
# octave supplied was usually at 8, returned pch value
# def psToPchTempered(psReal, octave, temperamentObj):
#     """converts pitch class and octave to Csound PCH format
#     octave 8.00 = middle c (MIDI 60, C4) 
#     source pc can be a pitch-space value
#     """
#     # source can be in pitch space, negative
#     octMult, ps = splitOctPs(psReal) # pc may have micro
#     adjOct = octave + octMult # octave of 0 keeps pch flat
#     # use temperament object w/attributes instead of dict
#     temperedPC = temperamentObj(ps) # this pc is in the form 3.2
#     return psToPch(temperedPC, adjOct) # handles neg, > 12





#-----------------------------------------------------------------||||||||||||--
# note: all transposers are designe to work w/ psReal values
# for psReal values, divmod returns 0 div for oct mid c
# -1 below, 1 one oct above, etcetera
def pcTransposer(source, trans):
    """basic transposition utility, performs mod 12 as check
    will _strip_ any register (octave info)
    keep any possible microtonal info
    will handle microtonal transpositions
    """
    oct, pc = divmod(source, 12)
    # this is changed for pitchObjs
    #pc = int(pc) # no microtones in pitch class space
    oct, pc = divmod((pc + trans), 12)
    return pc
    
def pcoTransposer(source, trans):
    """ pitch class octave transposer
    will _keep_ any register (octave info)
    but peform tansposition in same octave
    keep any possible microtonal info
    """
    oct, pc = divmod(source, 12)
    octTrans, pc = divmod((pc + trans), 12)
    pc = pc + (oct * 12) # restore original octave
    return pc

def psTransposer(source, trans):
    """basic transposition utility, no mod 12"""
    pc = source + trans # can be a negative transposition
    return pc

def pchTransposer(pchSrc, transposition):
    """transposition utility that includes octaves, up(+) or down(-) as expressed
    in half steps and decimal microtones, only operates on PCH
    """
    pchSrc = _normalizePch(pchSrc) # check for >.12 errors
    srcTriple = _splitPch(pchSrc)
    transTriple, direction = _splitTransposition(transposition)
    minMicro = 0.00001 # smallest microtone that matters, in semitone
    if direction == None: # no change
        return pchSrc
    tTriple = _tripleCombine(srcTriple, transTriple, direction, minMicro)     
    return _joinPch(tTriple)

#-----------------------------------------------------------------||||||||||||--
# inversion utilities

def psInverter(value, axis=0):
    """do a pitch space inversion, where axis is any value, and value
    is returned shifted the same distance below/above
    will work w/ psReals, MIDI values, and microtones
    axis is given as a psReal"""
    if value == axis:
        return value
    elif value > axis:
        return value - (2 * abs(axis - value))
    elif value < axis:
        return value + (2 * abs(axis - value))

def pcInverter(value, index=0):
    """index is the mod12 sum from an inversional opperation
    this produces the mappings outlined on Straus, iptt p46
    value should be a pitch class, returns pc"""
    return (index - value) % 12

def pcoInverter(value, index=0):
    """index is the mod12 sum from an inversional opperation
    this produces the mappings outlined on Straus, iptt p46
    retains octave information"""
    oct, pc = divmod(value, 12)
    pc = pcInverter(pc, index) # mod12 inversions
    pc = pc + (oct * 12) # restore original octave
    return pc

# utilities for finding inversional index
def _InvAxisToIndex(axis):
    """if given an axis pitch, determine the appropriate index
    axis can be fractional, like 1.5, to express an axis b/n c# and d
    axis is the pc that maps upon itself"""
    index, remainder = divmod(axis, .5)
    if remainder != 0: # value ending in .0 or.5 not given
        raise ValueError
    return index % 12

def _InvPcPairToIndex(pcA, pcB):
    """take two pitch classes and return an inversional index
    works for invesion notations Ix,y, where x is super and y is sub script
    pcA and pcB can be any x,y"""
    return (pcA+pcB) % 12

#-----------------------------------------------------------------||||||||||||--

def roundMicro(floatVal):
    """convert float value of pitch to an int
    good for midi and psReal to psInt conversions
    """
    return int(round(floatVal))

def _midiLimit(midiPc, micro=0):
    """limit midi pitch integers between 0 and 127
    this is necessary, as will causes errors when writing a file
    """
    # midi pc should may not alreayd be rounded
    midiPc = roundMicro(midiPc)
    if micro >= .5: # round for larger mivrotsones
        midiPc = midiPc + 1
    # these might better limit at an octave equivalant value...
    if midiPc > 127:
        midiPc = 127
    elif midiPc < 0:
        midiPc  = 0
    return midiPc

def pchToMidi(pch, limit='limit'):
    """ limit rounds microtones and limits between 0,127 
    8.00 is 60 
    """
    oct, pc, micro = _splitPch(pch)
    midiPc = ((oct - 3) * 12) + pc
    # if limited, check range, and add micro if > .5
    if limit == 'limit':
        midiPc = _midiLimit(midiPc, micro)
    else: # no limt, keep microtone value
        midiPc = midiPc + micro
    return midiPc

def pchToPs(pch):
    """pch to psReal"""
    oct, pc, micro = _splitPch(pch)
    psReal = pc + micro
    # octave 8 is 0, 7 should be -1
    psReal = psTransposer(psReal, (oct-8)*12)
    return psReal

#-----------------------------------------------------------------||||||||||||--
def _octNameToPsShift(octName=4):
    """ convert octave to psName octave values
    assumes 0-11 is c4-b4; 
    other values have appropriate scale in integer values"""
    if octName == 4: return 0
    elif octName < 4:
        return (octName - 4) * 12 # need a negative value here
    elif octName > 4:
        return (octName - 4) * 12 # need a positive value here

def psNameToPs(psStr):
    """pitch names to ps numbers
    middle c == c4 == midi 60 == 0
    should support negative octaves, like d-2
    """
    psStr = psStr.lower() # make sure lower case
    pcBase = REFdiaNameToPc[psStr[0]] # get first char
    flatScore = 0
    sharpScore = 0
    qScore = 0
    octaveStr = '' # assume c4 octave
    for char in psStr:
        if char == SYMflat:
          flatScore = flatScore + 1
        if char == SYMsharp: # or char == '+':
            sharpScore = sharpScore + 1
        elif char == SYMqTone:
            qScore = qScore + 1
        # oct may be negative
        elif char.isdigit() or char == '-': # get oct, negative if present
            octaveStr = octaveStr + char             
    octaveInt = drawer.strToNum(octaveStr, 'int') # will return None on error
    if octaveInt == None:
        octaveInt = 4 # octave starting at middle c
    # adjust pitch
    pcBase = pcBase - flatScore
    pcBase = pcBase + sharpScore
    if qScore != 0: # add quarter tones
        pcBase = pcBase + (qScore * .5)
    # add octave:
    pcBase = pcBase + _octNameToPsShift(octaveInt)
    return pcBase

#-----------------------------------------------------------------||||||||||||--

def midiToPs(midiInt):
    """convert from octave normalized at 0=c4
    to midi note number, where 60=c4
    midi could be a float
    """
    return midiInt - 60 

def midiToNoteName(midiInt):
    """
    >>> midiToNoteName(69)
    'A4'
    """
    psReal = midiToPs(midiInt)
    return psToNoteName(psReal)

def midiToFq(midiInt):
    """convert a midiInt to fq; midi values are not floating point
    most of the time

    >>> midiToFq(60)
    261.625565...
    """
    psInt = midiToPs(midiInt)
    fq = psToFq(psInt)
    return fq
    

#-----------------------------------------------------------------||||||||||||--
def psToMidi(psReal, limit='limit'):
    """convert from octave normalized at 0=c4
    to midi note number, where 60=c4
    dont strip any microtonal data and do appropriate rounding
    """
    midiPc = 60 + psReal
    if limit == 'limit':
        midiPc = _midiLimit(midiPc)
    return midiPc
    
def psToNoteName(psReal):
    """Convert pitch space to a note name

    >>> psToNoteName(0.5)
    'C~4'
    >>> psToNoteName(10)
    'A#4'
    """
    oct, pc, micro = splitPsReal(psReal)
    pc = int(pc)
    oct = int(oct)
    #for every .5 micro tone value, add a quarter tone
    # b/n 0-.25; .25-.75; .75-1
    if micro >= 0 and micro < .25:
        qStr = ''
        qOffset = 0
    elif micro >= .25 and micro < .75:
        qStr = SYMqTone
        qOffset = 0
    elif micro >= .75 and micro <= 1:
        qStr = ''
        qOffset = 1 # add an extra half step, round up
    else: raise ValueError, 'micro tone value exceeds range'
    # get oct offset for if wraps to ictace
    if (pc + qOffset) > 11:
        octOffset = 1
    else:
        octOffset = 0
    # add offset for micro rounding
    pcStr = REFpcToName[(pc + qOffset) % 12] # this will have sharps
    # qStr either after char, or after sharp
    nameStr = pcStr + qStr + str(oct + octOffset + 4) # shift for div mod value
    return nameStr.upper() # return in upper case


def psToMusicXml(psReal):
    """return note name, alter, and octave values
    may need to find a way to incorporate information on microtones smaller 
    than quarter tones
    """
    oct, pc, micro = splitPsReal(psReal)
    pc = int(pc)
    oct = int(oct)
    #for every .5 micro tone value, add a quarter tone
    # b/n 0-.25; .25-.75; .75-1
    if micro >= 0 and micro < .25:
        qVal = 0
        qOffset = 0
    elif micro >= .25 and micro < .75:
        qVal = .5 # value here is in half semitones
        qOffset = 0
    elif micro >= .75 and micro <= 1:
        qVal = 0
        qOffset = 1 # add an extra half step, round up
    else: raise ValueError, 'micro tone value exceeds range'
    # get oct offset for if wraps to ictace
    if (pc + qOffset) > 11:
        octOffset = 1
    else:
        octOffset = 0
    # add offset for micro rounding
    pcStr = REFpcToName[(pc + qOffset) % 12] # this will have sharps
    pcRoot = pcStr[0] # w/o accidental
    if len(pcStr) == 2 and pcStr[1] == SYMsharp:
        alter = 1 + qVal
    elif len(pcStr) == 2 and pcStr[1] == SYMflat:
        alter = -1 + qVal
    else:
        alter = 0 + qVal # qVal may be zero

    # returns name (w/o sharp), alter, and octave
    return pcRoot.upper(), str(alter), str(oct + octOffset + 4)



def psToFq(psReal):
    """convert a midiInt to fq; handles floating point microtones

    >>> psToFq(0.0)
    261.6255...
    >>> psToFq(9.0)
    440.0
    """
    # this is an accurate fq basis: 1.0594630943593
    # 440 == psReal 9; when 9 is suplied, numerator must be 0, == 440
    # http://www.music.mcgill.ca/~gary/307/week3/audio.html
    try:
        fq = 440 * pow(2, ((psReal-9)/12.0))
    except OverflowError:
        fq = 0
    return fq

def psToPch(srcPc, srcOct=8):
    """converts pitch class and octave to Csound PCH format
    octave 8.00 = middle c (MIDI 60, C4)
    will work with a pith space int/float
    """
    octMult, pc, micro = splitPsReal(srcPc)
    # octMult will be 0 at srcOct, 8, -/+ in relation to deviation
    # thus if srcOct is 7 and psReal is -1, result will be -13
    oct = int(octMult + srcOct) # always ints
    return _joinPch((oct, pc, micro))

def psToTempered(psReal, octShift, temperamentObj=None, tShift=0):
    """converts psReal to a tempered pitch value
    returns a psReal value:
    oct is in integers; trans is in half-step floats
    
    this keeps microtones in the psReal, and adds the differences
    found w/ the temperament object
    
    transposition used to be (pre1.3) applied after temperament is calculated
    now, transposition and octave are added _before_ temperament
    """
    # source can be in pitch space, negative
    #oct, pc, micro = splitPsReal(psReal) # pc may have micro
    #octAdj = oct + octShift # octave of 0 keeps flat
    # transposition happens after tmperament
    #psReal = joinPsReal(octAdj, pcTempered, micro) + trans
    
    # oct will be 0, +/- for each oct shift
    psReal = (octShift * 12) + tShift + psReal
    # use temperament object
    if temperamentObj != None:
        psReal = temperamentObj(psReal)
    return psReal

#-----------------------------------------------------------------||||||||||||--

def fqToPs(fq):
    """convert fq to ps; handles floating point microtones"""   
    # for midi
    #n = 12 x (log(f / 220.0) / log(2)) + 57     
    # http://www.music.mcgill.ca/~gary/307/week3/audio.html
    return 12 * (math.log(fq / 440.0) / math.log(2)) + 9     
    
def fqToMidi(fq, limit='limit'):
    return psToMidi(fqToPs(fq), limit)
    
def fqToPch(fq):
    return psToPch(fqToPs(fq))

def fqToNoteName(fq):
    return psToNoteName(fqToPs(fq))


def fqHarmonicSeries(base, size):
    """generate a harmonic series based off of the base fq, and for as many
    as specified by the size value

    >>> fqHarmonicSeries(200, 10)
    [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000]
    """
    post = [] # include base (fundamental is first harmonic)
    for x in range(size):
        post.append(base*(x+1))
    return post


#-----------------------------------------------------------------||||||||||||--


def allMidiNoteNames():
    """provide a scale of usable midi note numbers

    >>> allMidiNoteNames()
    ['C0', 'C#0', 'D0', 'D#0', 'E0', 'F0', 'F#0', 'G0', 'G#0', 'A0', 'A#0', 'B0', 'C1', 'C#1', 'D1', 'D#1', 'E1', 'F1', 'F#1', 'G1', 'G#1', 'A1', 'A#1', 'B1', 'C2', 'C#2', 'D2', 'D#2', 'E2', 'F2', 'F#2', 'G2', 'G#2', 'A2', 'A#2', 'B2', 'C3', 'C#3', 'D3', 'D#3', 'E3', 'F3', 'F#3', 'G3', 'G#3', 'A3', 'A#3', 'B3', 'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4', 'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5', 'C6', 'C#6', 'D6', 'D#6', 'E6', 'F6', 'F#6', 'G6', 'G#6', 'A6', 'A#6', 'B6', 'C7', 'C#7', 'D7', 'D#7', 'E7', 'F7', 'F#7', 'G7', 'G#7', 'A7', 'A#7', 'B7', 'C8', 'C#8', 'D8', 'D#8', 'E8', 'F8', 'F#8', 'G8']
    """
    scale = []
    for x in range(12, 116):
        scale.append(midiToNoteName(x))
    return scale





#-----------------------------------------------------------------||||||||||||--


class Pitch:
    """define a pitch space class
    fundamental pitch object
    allows transformatioin between any of a variety of formats
    midi, psReal, psName, pch, fq, pc
    pc is only an output format; always converted to a psReal
    all of these are attributes that are automatic conversions of basic types
    psReal may be a float, including microtonal tuning.
    """

    def __init__(self, srcData, format=None):
        """src data can be an int, float, or str
        strings are evaluated if numbers to the appropriate data

        a = Pitch('m30')
        """
        # all valid data forms as strings
        self.forms = ('midi', 'psReal', 'psName', 'pch', 'fq', 'pc')

        self.srcData = srcData # always store original data entered

        if format == 'pc': # pc types are converted to psReal for storage
            self.format = 'psReal'
        else: # all other types are normald
            self.format = format # format should be given if known

        if self.format == None: # defaults are used
            format = self._guessType()
            if format == None: # there has been an error
                raise error.PitchSyntaxError
            else:
                self.format = format
        self.data = self._processType() # this format data
        if self.data == None: # error
            raise error.PitchSyntaxError
        # always store a psReal as a private attribute that maintains
        # the data at the highest resolution
        self._real = self._convert('psReal')

    def _guessType(self):
        """try to determine what kind of pitch data is being provided
        psReal is default for any integer
        midi values must be marked some other way (w/ an m?)
        """
        data = copy.copy(self.srcData)
        if drawer.isStr(data):
            data = drawer.strScrub(data, 'L')
            if len(data) == 0:
                return None # no data found
            if data[0] in REFdiaNameToPc:
                return 'psName'
            elif data.find('m') >= 0 or data.find('midi') >= 0: 
                # an m designates a midi note number
                return 'midi'
            elif data.find('pch') >= 0: # a pch designates a pch value
                return 'pch'
            elif data.find('hz') >= 0 or data.find('fq') >= 0: 
                return 'fq'
            else: # assume other strings are psInts
                return 'psReal'
        if drawer.isInt(data): # midi int, or ps int
            return 'psReal'
        if drawer.isFloat(data): # assume it is a psReal value
            return 'psReal'
        
    def _processType(self):
        """process raw data into appropriate primative format"""
        data = copy.copy(self.srcData)
        if self.format == 'psName':
            if drawer.isStr(data):
                return data
            else:
                return None
        elif self.format == 'psReal': # psReal values should not be rounded
            if drawer.isStr(data):
                try:
                    return float(data)
                except ValueError:
                    return None
            else:
                return data

        elif self.format == 'midi': #midi values should always be rounded
            if drawer.isStr(data):
                data = drawer.strStripAlpha(data)
                try:
                    return float(data) # dont convert to int
                except ValueError:
                    return None
            elif drawer.isInt(data):
                return data
            else: # its a float, round
                return data

        elif self.format == 'pch': # floating point values
            if drawer.isStr(data):
                data = drawer.strStripAlpha(data)
                try:
                    return _normalizePch(float(data))
                except ValueError:
                    return None
            if drawer.isFloat(data):
                return _normalizePch(data)
            else: # something is wrong
                return None

        elif self.format == 'fq': # floating point values
            if drawer.isStr(data):
                data = drawer.strStripAlpha(data)
                try:
                    return float(data)
                except ValueError:
                    return None
            if drawer.isNum(data):
                return float(data) # convert to float
            else: # something is wrong
                return None

        else: # error
            return None

    def _convert(self, dst, src=None, data=None):
        """single interface for all pitch conversions
        valid format strings:
        midi, psName, psReal, [pch, fq] # pch, fq not yet implemented
        does not change internal data representation
        alows conversion between any types

        >>> a = Pitch(2)
        >>> a.get('midi')
        62
        >>> a.get('pc')
        2
        >>> a.get('fq')
        293.664...
        """
        if src == None:
            src = self.format # the format provided at initialization
        if data == None: # make sure this is a copy of the data
            data = copy.copy(self.data) # the data provided at initialization
        if src == 'midi':
            if dst  == 'psReal': return midiToPs(data)
            elif dst == 'psName': return midiToNoteName(data)
            elif dst == 'fq': return midiToFq(data)
            elif dst == 'pch': return psToPch(midiToPs(data))
            elif dst == 'pc' : return roundMicro(pcTransposer(midiToPs(data),0))
            elif dst == 'midi': return roundMicro(data) # do round here only
        elif src == 'psName':
            if dst  == 'midi': return psToMidi(psNameToPs(data))
            elif dst == 'psReal': return psNameToPs(data)
            elif dst == 'fq': return psToFq(psNameToPs(data))
            elif dst == 'pch': return psToPch(psNameToPs(data))
            elif dst == 'pc' : return roundMicro(
                                     pcTransposer(psNameToPs(data),0))
            elif dst == 'psName': return psToNoteName(self._real) # use real
        elif src == 'psReal':
            if dst  == 'midi': return psToMidi(data)
            elif dst == 'psName': return psToNoteName(data)
            elif dst == 'fq': return psToFq(data)
            elif dst == 'pch': return psToPch(data)
            elif dst == 'pc' : return roundMicro(pcTransposer(data, 0))
            elif dst == 'psReal': return data
        elif src == 'pch':
            if dst  == 'midi': return psToMidi(pchToPs(data))
            elif dst == 'psName': return psToNoteName(pchToPs(data))
            elif dst == 'fq': return psToFq(pchToPs(data))
            elif dst == 'pch': return data
            elif dst == 'pc' : return pcTransposer(roundMicro(pchToPs(data)), 0)
            elif dst == 'psReal': return pchToPs(data)          
        elif src == 'fq':
            if dst  == 'midi': return fqToMidi(data)
            elif dst == 'psName': return fqToNoteName(data)
            elif dst == 'fq': return data
            elif dst == 'pch': return fqToPch(data)
            elif dst == 'pc' : return pcTransposer(roundMicro(fqToPs(data)), 0)
            elif dst == 'psReal': return fqToPs(data)
        return None

#     def __getattr__(self, name):
#         """this method should be phased out and not used"""
#         if name not in self.forms:
#             raise AttributeError
#         return self._convert(name) # convert to appropriate data and return

    def get(self, name):
        """use of the get method should replace all direct attribute
        access. """
        if name not in self.forms:
            raise ValueError, 'bad format name'
        return self._convert(name) # convert to appropriate data and return

    def _procStrFloat(self, realVal, sigDigControl):
        """process a float so that only sig digits are shown in string
        if sigDigControl == 'auto' only show digits if they are not 0
        this is only used for providing string representations
        if sigDig Control is a number, at least his many sig digs will be shown
        (maybe more); zeros, however, will be padded if necessary
        """
        if sigDigControl == 'auto':
            sigDig = typeset.sigDigMeasure(realVal) # will measure smallest value
        else:
            sigDig = sigDigControl # assume its a nymber of digits
        
        if sigDig == 0: # make into into an int
            dataStr = str(int(round(realVal, sigDig)))      
        else:         
            dataStr = str(round(realVal, sigDig))
        # some representations reuqire more zeros, like pch 
        if '.' in dataStr:
            x, y = dataStr.split('.')
            if len(y) < sigDig:
                y = y + '0' * (sigDig - len(y))
            return '.'.join([x, y])
        else:
            return dataStr
        
    def report(self):
        """provide a list of strings for display of all attributes"""
        msg = []
        msg.append(( 'format', self.format ))
        msg.append(( 'name', self.repr('psName') ))
        msg.append(( 'midi', self.repr('midi') ))
        msg.append(( 'pitch-class', self.repr('pc') ))
        msg.append(( 'pch', self.repr('pch') ))
        msg.append(( 'frequency', self.repr('fq') ))
        msg.append(( 'pitch-space', self.repr('psReal') ))
        return msg

    def repr(self, format=None):
        """provode a str representation for each format"""
        if format == None:
            format = self.format # default is src format
        if format == 'midi': # should already be an int
            return '%s' % self._convert(format)
        elif format == 'psName': # should always be a string
            return '%s' % self._convert(format).upper()
        elif format == 'psReal': 
            return self._procStrFloat(self._convert(format), 'auto')
        elif format == 'pch': # min of 4 sig digits (cant round micro)
            return self._procStrFloat(self._convert(format), 4)
        elif format == 'fq': # 6 sig digits
            return self._procStrFloat(self._convert(format), 4)
        elif format == 'pc': # 6 sig digits
            return '%i' % self._convert(format)           
        else:
            raise ValueError, 'no such format string: %s' % format

    def __str__(self):
        return self.repr()

    def t(self, value):
        """transpose in pitch space
        t value can be like any psReal, ie 2 is a whole step transposition
        .25 is a quarter tone transposition

        >>> a = Pitch(4)
        >>> a.t(3)
        >>> a.get('midi')
        67
        """
        self._real = psTransposer(self._real, value)
        # convert _real back to native data format
        # args are dst, src, val
        self.data = self._convert(self.format, 'psReal', self._real)

    def tMod(self, value):
        """does a modulus transposition but retains octave info
        if pitch is in 0-12 oct, looks like pc transposition
        if pitch is < 0 or > 12, pitch remains in the same octave
        """
        self._real = pcoTransposer(self._real, value)
        # convert _real back to native data format
        # args are dst, src, val
        self.data = self._convert(self.format, 'psReal', self._real)

    def i(self, axis=0):
        """inverts a pitch around an axis, where the default is 0
        axis is the pitch class or pitch space element
        axis are given as psReal values
        """
        self._real = psInverter(self._real, axis)
        self.data = self._convert(self.format, 'psReal', self._real)

    def iMod(self, axis=0):
        """axis transposition, but retaining octave positon
        like tMod
        """
        # find desired index
        if drawer.isNum(axis):
            index = _InvAxisToIndex(axis)
        if drawer.isList(axis):
            index = _InvPcPairToIndex(axis[0], axis[1])
        self._real = pcoInverter(self._real, index)
        self.data = self._convert(self.format, 'psReal', self._real)






#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testPitch(self):
        demo = ((0, 'psReal'),(0.5, 'psReal'), (1, 'psReal'), 
                  (69, 'midi'), ('c#3', 'psName'), (3, None), ('m60', None),
                  ('-12.3', None),  ('-12.301', None),   ('8.01pch', None),
                  ('12.12', 'pch'), (12.1225, 'pch'))
        for val, format in demo:
            obj = Pitch(val, format)
            for form in obj.forms:
                attr = eval('obj.get("%s")' % form)
                attrStr = str(attr)

#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)