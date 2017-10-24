#-----------------------------------------------------------------||||||||||||--
# Name:          audioTools.py
# Purpose:       General audio processing tools
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


# note: this modules may not be compatible w/ all distributions
# there is a wave module that may provide support for wave output formats
# with the same interface

import random, os, array, copy
import unittest, doctest

try:
    import aifc, audioop
    AIF = 1
except ImportError:
    AIF = 0

from athenaCL.libATH import drawer
from athenaCL.libATH import unit
from athenaCL.libATH import fileTools
from athenaCL.libATH import osTools
_MOD = 'audioTools.py'

#-----------------------------------------------------------------||||||||||||--
audioFormatNames = ['aif', 'wav', 'sd2']

def audioFormatParser(usrStr):
    """provide backward compat to older names"""
    ref = {
        'aif'    : ['aif', 'aiff', 'a'],
        'wav'    : ['wav', 'wave', 'w'],
        'sd2'    : ['sd2', 'sd', 'ircam', 'i'], # assign ircam to sd2
            }
    usrStr = drawer.selectionParse(usrStr, ref)
    return usrStr # may be None
    

#-----------------------------------------------------------------||||||||||||--
# def setMacAudioRsrc(fmt, audioPath, prefDict=None):
#     """for macos 9, necessary to set creator and type
#     of audio files. given a fmt and file path, this function
#     does all necessary processing to audio file"""
#     if fmt == None: # assume it is an aif
#         fmt = 'aif'
#     # get standard type codes
#     if fmt == 'aif': typeCode = 'AIFF'
#     elif fmt == 'wav':  typeCode = 'WAVE'
#     elif fmt in ['sd2', 'ircam']: typeCode = 'Sd2f'       
#     # get creator code, use qt on default
#     if prefDict != None and prefDict.has_key('audioPlayerCreatorCode'): 
#         # may be a complete file path, or a name
#         creatorCode = prefDict['audioPlayerCreatorCode'] 
#     else: #'TVOD' is QuickTime, 'auFM' is Peak  
#         creatorCode = 'TVOD' # quick time       
#     osTools.rsrcSetCreator(audioPath, creatorCode, typeCode)


#-----------------------------------------------------------------||||||||||||--
# common equations

def frameToSec(frames, sr=44100):
    return frames / float(sr)

def secToFrame(sec, sr=44100):
    return int(sec * float(sr))

def byteToInt(bytes):
     # divide by 2, and sub 1, b/c int sign: just want max
    return (pow(2, (bytes * 8)) / 2) - 1

def arrayLenToFrameLen(arrayLen, bytes, ch):
    # in the arrya, each byte gets a unit, and each ch gets the samey bytes
    return arrayLen / (bytes * ch) 
    
#useful values:
#+3dB = 2x the power = 1.44x the SPL
#+6dB = 4x the power = 2x the SPL
#The doubling of SPL represents that the power increases four times.
 

# To describe an absolute value, the reference point must be known. There are different reference points defined. 
# 
# dBV represents the level compared to 1 Volt RMS. 0dBV = 1V. There is no reference to impedance (V = Volt). 
# 
# dBu represents the level compared to 0,775 Volt RMS with an unloaded, open circuit, source (u = 'unloaded' or 'unterminated' -- a voltage that is not related to power by an impedance). 
# 
# dBm represents the power level compared to 1 mWatt. This is a level compared to 0,775 Volt RMS across a 600 Ohm load impedance (m = milli). 
# 
# Dealing with voltage, convert from dBV to dBu: 1dBV equals +2.2dBu. 
# 
# +4dBu equals 1.23 Volt RMS. 
# 
# The reference level of -10dBV is the equivalent to a level of -7.8dBu. 
# 
# !!! +4dBu and -10dBV systems have a level difference of 11.8 dB and not 14 dB. This is almost a voltage ratio of 4:1 !!!
# 



 
#-----------------------------------------------------------------||||||||||||--
# this functions rely on lame and oggenc


def encodeMp3(src, dstDir=None, br=128, title='', 
                    artist='', album='', year='', dstName=None, quality=2):
    """encode an mp3 using lame
    -m s     # stereo mode, not using joint stereo
    -q 2     # quality, 0 creates best quality, 2 is good
    -b 128 # bitrate, 96, 128, 256, 320
    --cbr    # forces constatn bit rate, default
    --disptime n # update more often
    -c       # ha!
    --tt     # title 
    --ta     # artist
    --tl     # album 
    --ty     # year """
    srcDir, srcName = os.path.split(src)
    srcName, ext = osTools.extSplit(srcName)
    
    # optional dstName will be used instead of the srcName mod if provided
    if dstName == None:
        dstName = srcName + '.mp3'
    if dstDir == None or not os.path.isdir(dstDir): #place in same dir
        dst = os.path.join(srcDir, dstName)
    else: # use provided dstdir
        dst = os.path.join(dstDir, dstName)
    tagStr = '--tt "%s" --ta "%s" --tl "%s" --ty "%s" ' % (title, artist, 
                                                           album, year)
    cmd = 'lame -m s -q %s --add-id3v2 --cbr --disptime 1 -b %s -c %s %s %s' % (quality, br, 
                                                            tagStr, src, dst)
    os.system(cmd)
    return dst


def decodeMp3(src, dstDir=None, dstName=None, quality=2):
    """decode an mp3 to wav 
    -m s     # stereo mode, not using joint stereo
    -q 2     # quality, 0 creates best quality, 2 is good
    -b 128 # bitrate, 96, 128, 256, 320
    --cbr    # forces constatn bit rate, default
    --disptime n # update more often
    -c       # ha!
    --tt     # title 
    --ta     # artist
    --tl     # album 
    --ty     # year """
    srcDir, srcName = os.path.split(src)
    srcName, ext = osTools.extSplit(srcName)
    
    # optional dstName will be used instead of the srcName mod if provided
    if dstName == None:
        dstName = srcName + '.wav'
    if dstDir == None or not os.path.isdir(dstDir): #place in same dir
        dst = os.path.join(srcDir, dstName)
    else: # use provided dstdir
        dst = os.path.join(dstDir, dstName)
    cmd = 'lame -m s -q %s --decode --disptime 1 -c %s %s' % (quality, src, dst)
    os.system(cmd)
    return dst

def encodeFlac(src, dstDir=None, dstName=None):
    """To encode:
  flac [INPUTFILE [...]] """
    srcDir, srcName = os.path.split(src)
    srcName, ext = osTools.extSplit(srcName)
    
    # optional dstName will be used instead of the srcName mod if provided
    if dstName == None:
        dstName = srcName + '.flac'
    if dstDir == None or not os.path.isdir(dstDir): #place in same dir
        dst = os.path.join(srcDir, dstName)
    else: # use provided dstdir
        dst = os.path.join(dstDir, dstName)
    cmd = 'flac -o %s %s ' % (dst, src)
    os.system(cmd)
    return dst

def decodeFlac(src, dstDir=None, dstName=None):
    """To decode:
  flac -d [INPUTFILE [...]] """
    srcDir, srcName = os.path.split(src)
    srcName, ext = osTools.extSplit(srcName)
    
    # optional dstName will be used instead of the srcName mod if provided
    if dstName == None:
        dstName = srcName + '.aif'
    if dstDir == None or not os.path.isdir(dstDir): #place in same dir
        dst = os.path.join(srcDir, dstName)
    else: # use provided dstdir
        dst = os.path.join(dstDir, dstName)
    cmd = 'flac -d -o %s %s ' % (dst, src)
    os.system(cmd)
    return dst

def encodeOgg(src, dstDir=None, br=128, title='', 
                         artist='', album='', year=''):
    """ encode using oggenc
    -b   # bitrate,  can use -q 0-10 instead
    -o   # output filename
    -d   # date
    -a   # artist
    -t   # title
    -l   # album"""
    srcDir, srcName = os.path.split(src)
    srcName, ext = osTools.extSplit(srcName)
    dstName = srcName + '.ogg'
    if dstDir == None or not os.path.isdir(dstDir): #place in same dir
        dst = os.path.join(srcDir, dstName)
    else: # use provided dstdir
        dst = os.path.join(dstDir, dstName)
    
    tagStr = '-t "%s" -a "%s" -l "%s" -d %s ' % (title, artist, album, year)
    cmd = 'oggenc -w -b %s %s -o "%s" %s' % (br, tagStr, dst, src)
    os.system(cmd)
    return dst


def encodeAac(src, dstDir=None, br=128, title='', 
                    artist='', album='', year='', dstName=None):
    """encode an ac4 using faac
    note: this does not work w/ aiff files
  --artist X     Set artist to X
  --writer X     Set writer to X
  --title X      Set title to X
  --genre X      Set genre to X
  --album X      Set album to X
  --compilation Set compilation
  --track X      Set track to X (number/total)
  --disc X       Set disc to X (number/total)
  --year X       Set year to X
  --cover-art X Read cover art from file X
  --comment X    Set comment to X
  """
    srcDir, srcName = os.path.split(src)
    srcName, ext = osTools.extSplit(srcName)
    
    # optional dstName will be used instead of the srcName mod if provided
    if dstName == None:
        dstName = srcName + '.m4a'
    if dstDir == None or not os.path.isdir(dstDir): #place in same dir
        dst = os.path.join(srcDir, dstName)
    else: # use provided dstdir
        dst = os.path.join(dstDir, dstName)

    # quality seems to be anywhere from 50 to 150
    tagStr = '--title "%s" --artist "%s" --album "%s" --year "%s" ' % (title, 
                artist, album, year)
    cmd = 'faac -q 100 -b %s %s -o "%s" %s' % (br, tagStr, dst, src)
    os.system(cmd)
    return dst
    

#-----------------------------------------------------------------||||||||||||--
# sox wrappers
# http://sox.sourceforge.net/

# note: should use higher quality resampling here

def soxConvert(src, srcExt, dstExt='.aif', srcSr=44100, dstSr=44100):
    dst = src.replace(srcExt, dstExt)
    cmd = 'sox -r %s %s -r %s %s' % (srcSr, src, dstSr, dst)
    os.system(cmd)
    return dst
    

def soxSplit(src):
    # this does not work for some reason

    #dst = src.replace(srcExt, dstExt)
    dir, name = os.path.split(src)
    nameStub, ext = osTools.extSplit(src)
    ext = '.aif'
    dstLeft = os.path.join(dir, nameStub + '.L' + ext)
    dstRight = os.path.join(dir, nameStub + '.R' + ext)

    # get left
    cmd = 'sox %s -c 1 %s avg -l' % (src, dstLeft)
    os.system(cmd)
    # get right
    cmd = 'sox %s -c 1 %s avg -r' % (src, dstRight)
    os.system(cmd)

    return dstLeft, dstRight
    

def soxFade(src, dst=None, timeIn=.01, timeOut=.01):
    # add a fade in and fade out to sound file
    # need total time 
    # this is destructive if dst id none
    timeTotal = fileDur(src)
    if dst == None: # replace original
        nameStub, ext = osTools.extSplit(src)
        dst = '%s-temp%s' % (nameStub, ext)
    #print 'in, out, total:', timeIn, timeOut, timeTotal
    # t is a linear slope
    cmd = 'sox %s %s fade t %s %s %s' % (src, dst, timeIn, timeTotal, timeOut)
    os.system(cmd)
    if dst == '%s-temp%s' % (nameStub, ext):
        osTools.mv(dst, src)
        #osTools.rm(dst)
    return src

def soxAmp(src, dst=None, amp=.9):
    # this is destructive if dst id none
    if dst == None: # replace original
        nameStub, ext = osTools.extSplit(src)
        dst = '%s-temp%s' % (nameStub, ext)
    #print 'in, out, total:', timeIn, timeOut, timeTotal
    # t is a linear slope
    cmd = 'sox %s %s vol %s amplitude' % (src, dst, amp)
    os.system(cmd)
    if dst == '%s-temp%s' % (nameStub, ext):
        osTools.mv(dst, src)
        #osTools.rm(dst)
    return src


def soxSpeed(src, dst=None, speed=.5):
    # this is destructive if dst id none
    if dst == None: # replace original
        nameStub, ext = osTools.extSplit(src)
        dst = '%s-temp%s' % (nameStub, ext)
    #print 'in, out, total:', timeIn, timeOut, timeTotal
    # t is a linear slope
    cmd = 'sox %s %s speed %s' % (src, dst, speed)
    os.system(cmd)
    if dst == '%s-temp%s' % (nameStub, ext):
        osTools.mv(dst, src)
        #osTools.rm(dst)
    return src


#-----------------------------------------------------------------||||||||||||--
# http://www.python.org/doc/current/lib/module-array.html
# for working with arrays see examples here and elsewhere
# 
# noise = []
# for i in range(8000):
#   noise.append(whrandom.randint(-32767, 32767))
# data = array.array("h", noise).tostring()
# 


class EnvelopeGenerator:
    """return various envelopes
    envelopes are floating point values between 0 and 1
    always returned as lists
    """
    def __init__(self):
        pass

    def _ramp(self, rampLen, direction='in', format='linear'):
        envelope = []
        for i in range(0, rampLen):
            envelope.append(((1.0 / rampLen) * i))
            i = i + 1
        if direction == 'out':
            envelope.reverse()
        return envelope

    def symmetric(self, frames, fadeLen):
        """produce an envelope w/ length equal to aObj
        fadeLen is in farames"""
        #totalLen = obj.getnframes()
        totalLen = frames
        if totalLen < (fadeLen * 2):
            raise ValueError('fades are too long')
        flatLen = totalLen - (fadeLen * 2)

        rampIn  = self._ramp(fadeLen, 'in')
        rampOut = self._ramp(fadeLen, 'out')
        # create envelope for entire data
        envelope = rampIn + ([1] * flatLen) + rampOut
        return envelope


class SampleGenerator:
    """utility to generate sample data
    always returns in format for writting
    data in these arrays conssist of two bytes, and thus lengths
        are always twice as large"""
    def __init__(self, ch=1, sr=44100, bytes=2):
        self.ch = 1
        self.bytes = 2 # 16 bits
        self.sr = 44100
        
    def update(self, ch, sr, bytes):
        # update values in case of changes
        self.ch = ch
        self.sr = sr
        self.bytes = bytes
        self.absMax = byteToInt(self.bytes) # value in integers

    #-----------------------------------------------------------------------||--
    # synthesize for given frames

    def silence(self, frames):
        if frames == 0: return ''
        # h is a signed short
        return array.array("h", [0]*frames*self.ch).tostring()

    def noise(self, frames, amp=1):
        """amp is a scalar between 0 and 1"""
        if frames == 0: return ''
        noise = []
        for i in range(frames*self.ch):
            max = byteToInt(self.bytes)
            noise.append(int(round(random.randint(-max, max) * amp)))
        # 'h' is a signed int here 
        return array.array("h", noise).tostring()



    #-----------------------------------------------------------------------||--
    # funtionst the process string and list data
    def multiply(self, xStr, yList):
        """multiple two data strings, both not supplied as lists
        note: this may not work for stereo
        if float values are provided, not sure that proper rouding is done
        """
        xArray = array.array("h")
        xArray.fromstring(xStr)
        xList = xArray.tolist()
        #print _MOD, 'comparing mult lists', len(xList), len(yList), self.ch          
        zList = []
        i = 0
        q = 0
        while 1:
            if i == len(xList): break
            scalar = yList[q] # only one per frame, not data value
            zList.append(int(round(xList[i] * scalar)))
            i = i + 1
            if i % self.ch == 0:
                q = q + 1 # increment scale index
        return array.array("h", zList).tostring()

    def _frameLimit(self, val):
        if val > self.absMax: return self.absMax
        elif val < -self.absMax: return -self.absMax
        else: return val     
    
    def mix(self, xStr, yStr):
        """mix two equal lengthed data strings;
        """     
        xArray = array.array("h")
        xArray.fromstring(xStr)
        xList = xArray.tolist()
        yArray = array.array("h")
        yArray.fromstring(yStr)
        yList = yArray.tolist()
        #print _MOD, 'comparing mix lists', len(xList), len(yList), self.ch 
        zList = []
        i = 0
        q = 0
        for i in range(len(xList)):
            # this should be limited
            zList.append(self._frameLimit(xList[i] + yList[i]))
        return array.array("h", zList).tostring()
        
        
    def split(self, xStr):
        """split stereo data into two lists of data
        if there is 1000 frames dataLen will be 2000
        each side should have 1000 after complete"""
        splitList = []
        for ch in range(self.ch):
            splitList.append([]) # create a list for each channel
        xArray = array.array("h")
        xArray.fromstring(xStr)
        xList = xArray.tolist() # possible not necessary
        i = 0
        while i < len(xList):
            for ch in range(self.ch):
                splitList[ch].append(xList[i])
                i = i + 1
        # convert back to data string format
        #print _MOD, 'split source, side', len(xList), len(splitList[0]), self.ch
        for ch in range(self.ch):
            splitList[ch] = array.array("h", splitList[ch]).tostring()
        return splitList # list of channel data
        
        
    def interleave(self, xStr, yStr):
        """intereleave two data sets
        channel is not considered"""
        xArray = array.array("h")
        xArray.fromstring(xStr)
        xList = xArray.tolist() # possible not necessary
        
        yArray = array.array("h")
        yArray.fromstring(xStr)
        yList = yArray.tolist() # possible not necessary
        
        zList = []
        for i in range(len(xList)):
            zList.append(xList[i])
            zList.append(yList[i])
        # convert back to data string format
        return array.array("h", zList).tostring()
        
    #-----------------------------------------------------------------------||--
    # tools to load unit interval array as samples
    # concver with various methods
        
    def unitSynthesizer(self, xList, method=None):
        """scale values to the bit depth
        pack into a list, convert to string data
        
        assumes that values are normalized b/n 0 and 1

        direct; scales value in range of 0 to 1 between -max and amx
        """
#         for i in range(len(xList)):
#             xList[i] = unit.limit(xList[i])
            
        zList = []
        max = byteToInt(self.bytes)     
        #print _MOD, max
        if method in [None, 'direct']:
            for x in xList:
                valSigned = int(round(unit.denorm(x, -max, max)))
                # add a value for each channel
                for ch in range(self.ch):
                    zList.append(valSigned)
        # thee use zero crossings to effect sig of the wave form
        elif method in ['reflect']:
            sign = 1 # 1 is positive
            for x in xList:         
                val = unit.denorm(x, 0, max)
                if val == 0: # only change sign at zero crossing
                    if sign == 1: sign = -1
                    else: sign = 1
                valSigned = val*sign
                # add a value for each channel
                for ch in range(self.ch):
                    zList.append(valSigned)
        elif method == 'fold':
            sign = 1 # 1 is positive
            for x in xList:         
                val = abs(unit.denorm(x, -max, max)) # abs of full range
                if val == 0: # only change sign at zero crossing
                    if sign == 1: sign = -1
                    else: sign = 1
                valSigned = val*sign
                # add a value for each channel
                for ch in range(self.ch):
                    zList.append(valSigned)

        #print zList
        return array.array("h", zList).tostring()
        




#-----------------------------------------------------------------||||||||||||--          
class AudioFile:
    """object wrapper for an audio file
    with intuitive, high level controls
    
    """
    
    def __init__(self, absPath, ch=1, sr=44100, bytes=2):
        """specify bit depth with bytes, where 2 bytes == 16 bits
        file exists, channel will be updated to appropriate value
        """
        if not AIF: # check if modules loaded
            raise ImportError('aif modules not available (%s)' % os.name)
        self.absPath = absPath
        # store an envelope generator for convenience
        self.envlGenObj = EnvelopeGenerator()
        self.sampleGenObj = SampleGenerator()
        # store initial settings
        self.ch = ch
        self.sr = sr
        self.bytes = bytes
        # setup the file
        self._FILEOPEN = 0 # store if file is open or not to watch for errors
        self._open(None) # None auto-determines what to do
        self._close()

    #-----------------------------------------------------------------------||--
    # private methods for opening and closing file
    
    def _open(self, mode='r', ch=None):
        """frame values must only be updated on opening a file
        for reading; opeing for writing returns 0
        """
        if self._FILEOPEN == 1: # file is already open:
            self.aObj.close()
            raise IOError('attempt to open open file.')
        if mode == None: # determine by wether file exists or not
            if os.path.exists(self.absPath): mode = 'r'
            else: mode = 'w'
        # mark file as open
        self._FILEOPEN = 1
        if mode == 'r':
            assert os.path.exists(self.absPath) 
            self.aObj = aifc.open(self.absPath, mode)
            # only update when opening for reading, as strange results if 
            # open for writing (0 frame length given)
            self._update()
        elif mode == 'w':
            self.aObj = aifc.open(self.absPath, 'w')
            if ch != None: self.ch = ch # coerce channel if provided
            self.aObj.setnchannels(self.ch)
            self.aObj.setsampwidth(self.bytes)
            self.aObj.setframerate(self.sr)
        
    def _close(self):
        if self._FILEOPEN == 0: # file is already closed
            raise IOError('attempt to close a closed file.')
        self._update()
        #print 'closing file: frames %s, channels %s' % (
        #                            self.frames, self.ch)
        self.aObj.close()
        del self.aObj
        self._FILEOPEN = 0

    def _update(self):
        """always call update when opening/closing file"""
        assert self._FILEOPEN == 1
        self.ch = self.aObj.getnchannels()
        self.sr = self.aObj.getframerate()
        self.bytes = self.aObj.getsampwidth() # 1 is 8, 2 is 16, 
        self.frames = self.aObj.getnframes()
        #print _MOD, 'update: found %s frames' % (self.frames)
        # update values in sample gen obj
        self.sampleGenObj.update(self.ch, self.sr, self.bytes)
        
    #-----------------------------------------------------------------------||--
    # methods that use open/close above to wrap public methods
    
    def getSize(self):
        # update should not be necessary
        #self._open('r')
        #self._close()
        return self.frames
        
    def getDur(self):
        """get duration in seconds"""
        return frameToSec(self.frames, self.sr)
    
    def getData(self, pos=0, frames=None):
        """note: when pos != 0, a frame size of None may not get all remaining
        samples, but request samples that are not there"""
        # read some data
        if frames == None: # get all data
            frames = self.frames
        self._open('r') # open to read data
        self.aObj.setpos(pos)
        data = self.aObj.readframes(frames)
        self._close()            
        return data
        
    def reSize(self, size):
        """resize file to desired frames"""
        if self.frames == size: pass
        elif self.frames < size: # add difference
            frameAdd = size - self.frames
            self._open('r')
            data = self.aObj.readframes(self.frames)
            self._close()
            # this data will be of len 2 times frames (2 bytes per frame)
            newData = data + self.sampleGenObj.silence(frameAdd)
            self._open('w')
            self.aObj.writeframesraw(newData)
            self._close()
        else:
            self._open('r')
            data = self.aObj.readframes(size)
            self._close()
            self._open('w')
            self.aObj.writeframesraw(data)
            self._close()
            
    def reChannel(self, ch, side=0):
        """re channelize a file
        if side ==0, keep left, otherwise, right"""
        if ch == self.ch: pass
        elif self.ch == 2 and ch == 1: # make mono
            self._open('r')
            data = self.aObj.readframes(self.frames) # get all
            split = self.sampleGenObj.split(data) # get each side
            self._close()
            self._open('w', ch) # coerce to 1 channel
            self.aObj.writeframesraw(split[side])
            self._close()
        elif self.ch == 1 and ch == 2: # make stereo
            self._open('r')
            data = self.aObj.readframes(self.frames)
            newData = self.sampleGenObj.interleave(data, data) # get each side
            self._close()
            self._open('w', ch) # coerce to 1 channel
            self.aObj.writeframesraw(newData)
            self._close()
        else:
            raise ValueError('incompatible channel conversioin')
            
    def fillNoise(self):
        """pos is start position w/n file"""
        data = self.sampleGenObj.noise(self.frames)
        self._open('w')
        self.aObj.writeframesraw(data)
        self._close()
            
    def fillSilence(self):
        """pos is start position w/n file"""
        data = self.sampleGenObj.silence(self.frames)
        self._open('w')
        self.aObj.writeframesraw(data)
        self._close()
        
    def fillDataRaw(self, data):
        """file w/ raw data in the store format, signed in strings"""
        self._open('w')
        self.aObj.writeframesraw(data)
        self._close()
        
    def fillDataUnit(self, unitList, method=None):
        """fill file w/ a list of unit interval values
        methods are direct, reflect, and fold
        None defaults to direct
        """
        #print _MOD, 'fillDataUnit got unitList;', unitList[0:10]
        data = self.sampleGenObj.unitSynthesizer(unitList, method)
        self._open('w')
        self.aObj.writeframesraw(data)
        self._close()
        #print _MOD, 'fillDataUnit done'

    def clear(self):
        """erase all sample data w/n the audio file
        write one frame of silence"""
        data = self.sampleGenObj.silence(1)
        self._open('w')
        self.aObj.writeframesraw(data)
        self._close()

    def padSilence(self, frames, position='front'):
        """pos is start position w/n file
        can be front or rear"""
        dataPad = self.sampleGenObj.silence(frames)
        dataOld = self.getData() # default is all data
        if position == 'front':
            data = dataPad + dataOld
        if position == 'rear':
            data = dataOld + dataPad
        self._open('w') # over-write existing data
        self.aObj.writeframesraw(data)
        self._close()
        
        
    def insertNoise(self, pos, frames, amp=1):
        """insert some noise at a given amp into the file at position
        specified in frames. dur specified in frames
        not: dur applied to stereo channel does seem to last for the proper dur"""
        if frames + pos > self.frames: raise ValueError('bad position size')
        noiseData = self.sampleGenObj.noise(frames, amp)
        srcLead = self.getData(0, pos-1) # get data before noise
        srcPost = self.getData(pos+frames, self.getSize()-(pos+frames))
        # insert noise data inbetween lead and post
        data = srcLead + noiseData + srcPost
        self._open('w') # over-write existing data
        self.aObj.writeframesraw(data)
        self._close()
        
        
    def insertMix(self, pos, insertData, method=None):
        """insert the data at specifiec location
        data can be in the form of a unitList (b/n 0 and 1)
        or string data (assuming its in the same channel
        
        it may be good to allow for a negative position:
        insert the necessary frames before x and y
        """
        # zero position measured form x
        xData = self.getData()
        xSize = copy.copy(self.frames)
        
        if drawer.isStr(insertData):
            # divide channel number * byte
            ySize = arrayLenToFrameLen(len(insertData), self.bytes, self.ch)
            yData = insertData
        else: #must be a unit list
            ySize = len(insertData) # channel does not matter in unit list
            yData = self.sampleGenObj.unitSynthesizer(insertData, method)

        #print _MOD, 'x, y size', xSize, ySize
        if pos == 0: # just pad end of shorter
            if ySize == xSize:
                _caseStr = 'a' # this is just for debugging
                xFinal = xData
                yFinal = yData
            elif ySize > xSize : # x needs pad after
                _caseStr = 'b'
                dif = ySize - xSize
                xFinal = xData + self.sampleGenObj.silence(dif)
                yFinal = yData
            elif ySize < xSize : # y needs pad after
                _caseStr = 'c'
                dif = xSize - ySize
                xFinal = xData
                yFinal = yData + self.sampleGenObj.silence(dif)
        else:
            if ySize >= xSize:
                _caseStr = 'd'
                posRemain = (pos + ySize) - xSize
                xFinal = xData + self.sampleGenObj.silence(posRemain)
                yFinal = self.sampleGenObj.silence(pos) + yData
            elif ySize < xSize: # x needs pad after
                if pos + ySize == xSize:
                    _caseStr = 'e'
                    xRemain = pos # postpend to x
                    yRemain = 0
                elif pos + ySize < xSize: # need yRemain
                    _caseStr = 'f'
                    xRemain = 0
                    yRemain = xSize - (pos + ySize)
                elif pos + ySize > xSize: # need yRemain
                    _caseStr = 'g'
                    xRemain = (pos + ySize) - xSize
                    yRemain = 0
                
                xFinal = xData + self.sampleGenObj.silence(xRemain)
                yFinal = (self.sampleGenObj.silence(pos) + yData + 
                             self.sampleGenObj.silence(yRemain))        

        #print _MOD, 'resize case:', _caseStr
                                     
        data = self.sampleGenObj.mix(xFinal, yFinal)
        self._open('w') # over-write existing data
        self.aObj.writeframesraw(data)
        self._close()
        
    def envelopeSymmetric(self, fadeLen):
        self._open('r')
        envelope = self.envlGenObj.symmetric(self.frames, fadeLen)
        data = self.aObj.readframes(self.frames) # get all frames
        self._close()
        self._open('w')
        newData = self.sampleGenObj.multiply(data, envelope)
        self.aObj.writeframesraw(newData)
        self._close()
        
    #-----------------------------------------------------------------------||--
    # methods for producing new files form existing ones
    
    def extract(self, newPath, start, length, fadeLen=None, ch=None):
        """ extract a segment of this file to a new file
        start, length, and fadeLen are all in frames
        channel is ch in destination, forced from stereo if needed
        
        returns the new object
        """
        assert newPath != self.absPath # make sure not the same
      
        self._open('r') # open to read data
        if start + length > self.frames:
            self._close()
            raise ValueError('bad start and frame length')
        self.aObj.setpos(start)
        data = self.aObj.readframes(length)
        self._close()
        
        # get same format as current file
        newObj = AudioFile(newPath, self.ch, self.sr, self.bytes)
        newObj.fillDataRaw(data)
        if ch != None:
            newObj.reChannel(ch)
        if fadeLen != None:
            newObj.envelopeSymmetric(fadeLen)
        return newObj

    #-----------------------------------------------------------------------||--
    # high level methods that do not open/close; only call above methods
    
    def testAmp(self, pos, frames, rmsThresh=.08, maxThresh=.50):
        """look at peak and average values and determine if there is enough
        audio to keep"""
        data = self.getData(pos, frames)
        if len(data) == 0:
            print('no data: %s: %s, %s' % (self.frames, pos, frames)) 
            result = 0 # no data to get
        absMax = byteToInt(self.bytes)
        max = audioop.max(data, self.bytes)
        rms = audioop.rms(data, self.bytes)
        if rms >= (absMax * rmsThresh) or max >= (absMax * maxThresh):
            result = 1
        else:
            rmsPct = round((rms / float(absMax)), 3)
            print(_MOD, 'lowamp: rms %s max %s (rmsPct %.3f)' % (str(rms).ljust(5), 
                                                     str(max).ljust(5), rmsPct))
            result = 0
        return result
        
    def findShard(self, length, maxAttempt=20):
        """find a random section of this file file, of length given in frames
        that passes the amp test"""
        # read data
        frames = self.getSize()
        rangeMax = frames - length
        if rangeMax <= 0: 
            print(_MOD, 'findShard: self.frames, length %s %s' % (
                                                        self.frames, length))
            return None # skip
        frameRange = list(range(0, rangeMax))
        for i in range(0, maxAttempt):
            trialStart = random.choice(frameRange)
            if self.testAmp(trialStart, length): # if passes
                return trialStart
        return None # if nothing found
        
    #-----------------------------------------------------------------------||--
    def play(self):
        osTools.openMedia(self.absPath)
        
      




#-----------------------------------------------------------------||||||||||||--          
class ShardHarvest:

    def __init__(self, srcDir, dstDir, audioLength, fadeLength=None):
        """audio and fade lengths are in secondss
        will get all aiff files in the srcDir"""
        self.srcDir = srcDir
        self.dstDir = dstDir

        if not os.path.exists(self.dstDir):
            osTools.mkdir(self.dstDir)
        
        self.audioFrame = secToFrame(audioLength)
        if fadeLength != None:
            self.fadeFrame = secToFrame(fadeLength)
        else: 
            self.fadeFrame = None # turns off fades

        obj = fileTools.AllFiles(self.srcDir, ['aif', 'aiff'])
        self.srcFiles = obj.report()
        # make a list indices to get src files from; will randomize
        self.srcKeys = list(range(0, len(self.srcFiles)))
        self.dstFiles = []

    def _fileNameStr(self, i):
        if i < 10: # must use double f to get full aiff
            return '00%i.aiff' % i
        elif i < 100:
            return '0%i.aiff' % i
        else: 
            return '%i.aiff' % i
            
    def gather(self, fragments=20, indexStart=0):
        """go through files and find a shard; write the new new file, append
        to dstFiles
        indexStart is used to determine file naming;"""
        srcIndex = 0 # use to get from srcKeys
        random.shuffle(self.srcKeys)
        srcLen = len(self.srcKeys)

        used = {} # dictionary of used file paths, value is number of uses
        
        for i in range(indexStart, (fragments+indexStart)):
            if i % 10 == 0: # report every ten
                print(_MOD, 'current index: %s' % i)

            srcPath = self.srcFiles[self.srcKeys[(srcIndex % srcLen)]]
            srcIndex = srcIndex + 1
            
            aObj = AudioFile(srcPath)
            start = aObj.findShard(self.audioFrame)
            if start == None:
                print('no audio found in %s' % srcPath)
                continue

            dstPath = os.path.join(self.dstDir, self._fileNameStr(i))
            ch = 1 # force mono output
            b = aObj.extract(dstPath, start, self.audioFrame, self.fadeFrame, ch)
            self.dstFiles.append(dstPath)
        return self.dstFiles




#-----------------------------------------------------------------||||||||||||--          
class EncodeChain:

    def __init__(self, src, steps=999, bitRateArray=[64]):
        """encode and re-encode, appending to a file cyclically"""
        self.steps = steps
        self.bitRateArray = bitRateArray
        self.src = src
        self.dir, name = os.path.split(src)
        self.nameStub, ext = osTools.extSplit(name)
        #self.ref = os.path.join(dir, '%s%s' % (nameStub+'-ref', ext))
        #self.storage = os.path.join(dir, '%s%s' % (nameStub+'-storage', ext))


    def run(self):
        srcObj = AudioFile(self.src)
        frames = srcObj.getSize()
        print(_MOD, 'length', frames)
        #refObj = srcObj.extract(self.ref, 0, frames) # store a version 
        #storageObj = srcObj.extract(self.storage, 0, frames)
        #print _MOD, 'duration', storageObj.getDur()
        br = self.bitRateArray[0]

        encodeSrcPath = copy.copy(self.src)

        for i in range(self.steps):

            tempEnc = os.path.join(self.dir, '%s%s' % (self.nameStub+'-enc'+str(i),
                                                                  '.mp3'))
            junk, tempEncName = os.path.split(tempEnc)
            tempDec = os.path.join(self.dir, '%s%s' % (self.nameStub+'-dec'+str(i),
                                                                 '.wav'))
            junk, tempDecName = os.path.split(tempDec)
    
            postMp3 = encodeMp3(encodeSrcPath, None, br, '', '', '', '',
                                      tempEncName, 9) # quality set to 9
            postWav = decodeMp3(postMp3, None, tempDecName, 9)
            postAif = soxConvert(postWav, '.wav', '.aif')
            osTools.rm(postWav)

            encodeSrcPath = postAif # store re-decoded aif path

            # add to existing file
            #encStepObj = AudioFile(postAif)

            # get stored data, and then get new data
            #tempStart = storageObj.getData(0, storageObj.getSize())
            #tempEnd = encStepObj.getData(0, encStepObj.getSize())
            # can remove all objects and files no longer necessary
            #del encStepObj
            #osTools.rm(postMp3)

            # replace all data in storage object
            #storageObj.fillDataRaw(tempStart+tempEnd)
            #print _MOD, 'duration', storageObj.getDur()


#-----------------------------------------------------------------||||||||||||--          

def waterMark(src, spotWidth=70, spotDur=1.05, spotAmp=.20):
        """provide an auido file, add noise to watermark
        spotWidth is the segment widht (in sec) in which a wm may occur
        spotDur in seconds"""
        
        if not os.path.exists(src): raise ValueError('no such file')        
        af = AudioFile(src)
        
        dur = af.getDur() # dur is in seconds
        # find total spots
        totalSpots = int(round(float(dur) / spotWidth))
        if totalSpots == 0: totalSpots = 1
        
        frames = af.getSize()
        fps = af.sr # frames per second
        
        spotFrames = int(round(af.sr * spotDur))
        
        # iterate over fraomes in minutes sized chunks 
        pos = 0
        for q in range(0, totalSpots):
            # pick a random starting point between 10 and 40 percent
            # of spotWidth
            min = int(round((.1*spotWidth)))
            max = int(round((.3*spotWidth)))
            
            secIn = random.choice(list(range(min, max)))
            secOut = spotWidth-secIn
            shift = fps * secIn
            pos = pos + shift
            
            af.insertNoise(pos, spotFrames, spotAmp)
            print(_MOD, af.absPath, '(%s)' % frameToSec(pos))
            # shift to end of second
            pos = pos + (fps * secOut)
            




#-----------------------------------------------------------------||||||||||||--          
# utility functions

def fileDur(srcPath):
    """get an audio file duration"""
    aObj = AudioFile(srcPath)
    return aObj.getDur()


















#-----------------------------------------------------------------||||||||||||--          
def TestOld():
    src = '/Volumes/ydisc/_sync/iport/shardSrc/'
    dst = '/Volumes/ydisc/_sync/iport/shardDst/shardBassB-136/'

    if not os.path.exists(dst):
        osTools.mkdir(dst)
    indexStart = 0
    
    # original tests, base 60bpm
    #a = ShardHarvest(src, dst, .120, .012)
    #a = ShardHarvest(src, dst, .060, .006)
    #a = ShardHarvest(src, dst, .030, .003)
    #a = ShardHarvest(src, dst, .015, .0015)

    # bass 220 bpm
    #a = ShardHarvest(src, dst, 0.0170454545455, .0017045) # 500
    #a = ShardHarvest(src, dst, 0.0340909090909, .0034091)  # 500
    #a = ShardHarvest(src, dst, 0.0681818181818, .0068182) # 300
    a = ShardHarvest(src, dst, 0.1363636363636, .0136364) # 300


    # reccomended numbers between 300 and 500 (more for shorter)
    print(a.gather(300, indexStart))



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

