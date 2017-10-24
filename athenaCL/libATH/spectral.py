#-----------------------------------------------------------------||||||||||||--
# Name:          spectral.py
# Purpose:       General audio spectrum processing tools
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--



import os, math, copy
from athenaCL.libATH import pitchTools
from athenaCL.libATH import drawer
from athenaCL.libATH import unit
from athenaCL.libATH import imageTools
from athenaCL.libATH.libGfx import graphPmtr


_MOD = 'spectral.py'

#-----------------------------------------------------------------||||||||||||--
# a class to read spectrum files
class SpectrumData:
    """a class to read various spectrum data forms and provide the result
    in psReals
    """
    def __init__(self, usrStr):
        """usrStr may have a comma, and thus include data for
        the number of values to read; can also be set below
        w/ getPitch method"""
        if usrStr == None:
            raise ValueError('bad file path given')
        if usrStr.find(',') >= 0:
            filePath, maxCount = usrStr.split(',')[:2]
            maxCount = drawer.strToNum(maxCount, 'int')
            #print _MOD, 'got maxCount of', maxCount
        else:
            filePath = usrStr
            maxCount = None # default
        if maxCount != None:
            self.maxCount = maxCount
        else: self.maxCount = 10
        # file path shuold always exists
        filePath = drawer.pathScrub(filePath)
        if not os.path.exists(filePath) or os.path.isdir(filePath): 
            raise ValueError('bad file path given')
        self.filePath = filePath
        self.forms = ['audacity.spectrum', 'audacity.autocorrelation']
        ok = self._parseFormat()
        if ok == None:
            raise ValueError('bad file path given')
        self.dataEval, self.fmt = ok
    
    def _parseFormat(self):
        if self.filePath.endswith('.txt'):
            f = open(self.filePath)
            fileStr = f.read()
            f.close()
        else: return None # no other file types supported
        dataEval = [] # evaluated data, sorted by val, fq, other
        
        # for some reason radline got strange results on macos x
        # manually reading line types
        if fileStr.find('\r\n') >= 0: SEProw = '\r\n' # win 
        elif '\r' in fileStr: SEProw = '\r' # macos
        elif '\n' in fileStr: SEProw = '\n' # unix
        else: return None # error, bad file
        fileLines = fileStr.split(SEProw)               

        # skip first line, as is key
        for line in fileLines:
            if line == '': continue
            # need to figure seperator
            elif '\t' in line: SEPcol = '\t'
            else: return None # error, bad file
            spectData = line.split(SEPcol)
            #print _MOD, spectData
            # tabbed lists should have either 2 or 3 items
            spectChunk = len(spectData)
            if spectChunk < 2 or spectChunk > 3:
                continue
            if spectChunk == 2: # assume audacity spectrum
                # Frequency (Hz), Level (dB)
                # return amp, fq
                fmt = 'audacity.spectrum'
                fq = drawer.strToNum(spectData[0])
                if fq == None: continue
                amp = drawer.strToNum(spectData[1])
                if amp == None: continue
                dataEval.append((amp, fq))
            elif spectChunk == 3: # assume audacity spectrum
                # Lag (seconds), Frequency (Hz), Level
                fmt = 'audacity.autocorrelation'
                fq = drawer.strToNum(spectData[1])
                if fq == None: continue
                amp = drawer.strToNum(spectData[2])
                if amp == None: continue
                s = drawer.strToNum(spectData[0])
                if s == None: continue
                dataEval.append((amp, fq, s))
        if len(dataEval) == 0: return None
        # sort so amps is ranked first
        dataEval.sort()
        dataEval.reverse() # largest on top
        return dataEval, fmt

    def getPitch(self, format='fq', maxCount=None):
        """read frequencies from the list
        format is standard Pitch object formats
        macCount will be used, if supplied, otherwise use value
        given at init, or from default"""
        if maxCount == None:
            maxCount = self.maxCount # use value set at init
        maxLen = len(self.dataEval)
        if maxCount > 0: # get top portion of sorted list
            if maxCount > maxLen: maxCount = maxLen
            posList = list(range(maxCount))
        elif maxCount < 0: # get bottom portion of sorted list
            if maxCount < -maxLen: maxCount = -maxLen
            posList = list(range(len(self.dataEval) + maxCount, len(self.dataEval)))
        else: return [] # empty range
        pitchList = []
        assert format in ['fq', 'psReal']
        for i in posList:
            # fq is always second
            if i >= len(self.dataEval): break
            fq = self.dataEval[i][1]
            if format == 'fq': # do nothing
                pitchList.append(fq)
            elif format == 'psReal':
                pitchList.append(pitchTools.fqToPs(fq))
        return pitchList











#-----------------------------------------------------------------||||||||||||--          
class PhaseAnalysis:
    """csound pvoc analysis 
    creates a file in the same dir as src file
    having a priblem generating images with csound 5
    see: http://www.csounds.com/manual/html/pvanal.html
    """
    def __init__(self, src):
        # assume an aif file
        if not src.endswith('.aif'): raise ValueError
        if not os.path.exists(src): raise ValueError
    
        dir, fnSrc = os.path.split(src)
    
        fnBin = fnSrc.replace('.aif', '.pvc')
        fnTxt = fnSrc.replace('.aif', '.txt')

        self.frameSize = 1024 # must be power of 2
        self.overlapFactor = 4 # default value of 4 seems good
        
        optStr = '-n %s' % self.frameSize 

        # alternat method from csound command: csound -U pvanal 
        cmd = 'cd %s; pvanal -V %s %s %s %s' % (dir, fnTxt, optStr, fnSrc, fnBin)
    
        os.system(cmd)

        # store this paths for external processing
        self.fpSrc = src
        self.fpTxt = os.path.join(dir, fnTxt)
        self.fpPvc = os.path.join(dir, fnBin)

        self.data = [] # a list of lists
        self.binCount = None
        self.header = [] # first 4 lines

        self._parse() # fill all values, analyse file

    def _parse(self):
        self.data = [] # a list of lists

        f = open(self.fpTxt)
        msg = f.readlines()
        f.close()

        self.header = msg[0:3]

        for line in msg[3:]:
            if line.strip() == '': continue
            # remove frame heade ra t beginng, will leave a number
            line = line.replace('Frame ', '')
            # replace 4 space, and 2 space boundaries w;/ one space
            line = line.replace('    ', ' ')
            line = line.replace('   ', ' ') 
            line = line.replace('  ', ' ') 
            # split into a list, drop first element as it is row id
            line = line.split(' ')[1:]
            post = []
            # bundle as pairs
            i = 0
            while i < len(line)-2:
                # note: reversing values so fq precedes amp
                a = float(line[i])
                f = float(line[i+1])
                i = i + 2 
                post.append((f,a))
            self.data.append(post)
        # number of bins is the length of the first row
        if self.data == []:
            return 0 # failure, empty audio file, etcetera
        else:
            self.binCount = len(self.data[0])
            return 1 # good


    def readAvg(self, bin):
        # for a given bin, get the average of all values for all frmaes
        if bin > self.binCount - 1: raise ValueError('bin out of range')
        a = 0
        f = 0

        for row in self.data:
            f = f + row[bin][0]
            a = a + abs(row[bin][1])
        f = f / len(self.data)
        a = a / len(self.data)
        return f, a

    def readCoord(self, fqRange=(20,20000), norm=1):
        amp = []
        fq = []
        for i in range(self.binCount):
            f, a = self.readAvg(i)
            if f < fqRange[0] or f > fqRange[1]:
                continue
            # take log of a
            if norm:
                f = math.log(f, 10)
            amp.append(a)
            fq.append(f)
        # always add min and max to fq values, w/ zero amp
        # this is necessary before normalization
        # unit interval will then map to min and max
        for val in fqRange:
            fq.append(math.log(val, 10))
            amp.append(0)

        # normalize values
        if norm:
            amp = unit.unitNormRange(amp)
            fq = unit.unitNormRange(fq)
        
        coord = []
        # make pairs
        for i in range(len(amp)):
            coord.append((fq[i], amp[i]))
        return coord








# this is experimental and incomplete
# pabon game
#-----------------------------------------------------------------||||||||||||--

class SpectralComponent:
    def __init__(self, id, rInit, f):
        self.id = id
        self.x = 0
        self.y = 0
        self.rInit = rInit # this is in degrees
        self.r = copy.deepcopy(self.rInit) # phase, in degrees
        self.f = f
        self.history = []

    def reset(self):
        self.x = 0
        self.y = 0
        self.r = copy.deepcopy(self.rInit) # phase, in degrees

    def _degreeToPhase(self, r):
        return (r % 360) / 360.0

    def _phaseToDegree(self, r):
        return (r % 1.0) * 360.0

    def _getSides(self, theta, h):
        """given theta, hypoteneuse determine a, b
        a is always the side opposite the angle"""
        a = math.sin(theta) * h
        b = math.cos(theta) * h
        return a, b

    def _getPosition(self, r, step, x, y):
        """given a direction and current x, y, calc new x, y
        step may be positive or negative
        """
        xShift = 0
        yShift = 0

        self.r = r % 360 # reduce mod
        rAdj = round(self.r, 6)       
        # might need to round
        if rAdj in [0.0, 90.0, 180.0, 270.0]:
            if rAdj == 0.0: # going left
                xShift = -step 
                yShift = 0 
            elif rAdj == 90.0: # going up
                xShift = 0
                yShift = step 
            elif rAdj == 180.0: # going right
                xShift = step
                yShift = 0 
            elif rAdj == 270.0: # going down
                xShift = -step
                yShift = 0 
        # not on axis
        if rAdj > 0.0 and rAdj < 90.0:
            a, b = self._getSides(rAdj, step)
            xShift = -b
            yShift = a
        elif rAdj > 90.0 and rAdj < 180.0:
            a, b = self._getSides(rAdj-90, step)
            xShift = a
            yShift = b
        elif rAdj > 180.0 and rAdj < 270.0:
            a, b = self._getSides(rAdj-180, step)
            xShift = a
            yShift = -b
        elif rAdj > 270.0 and rAdj < 360.0:
            a, b = self._getSides(rAdj-270, step)
            xShift = -b
            yShift = -a

        return xShift, yShift

    def _stop(self, t):
        """update phase position
        this is where the confusion comes... what type of data
        is phase needed"""
        phase = self._degreeToPhase(self.rInit) + (t * self.f)
        # range is -1 to 1, phase is between 0 and 1
        self.r = phase % 360             #self._phaseToDegree(phase)
        # not sure what this value is for
        amp = math.sin(2.0 * math.pi * phase)

    def _step(self, step):
        """update step"""
        # after a given
        x, y = self._getPosition(self.r, step, self.x, self.y)
        self.x = self.x + x
        self.y = self.y + y

    def _amp(self):
        """get distance from origin"""
        a = abs(self.x)
        b = abs(self.y)
        h = pow((pow(a, 2) + pow(b, 2)), .5)
        return h

    def postTime(self, time, step):
        self._stop(time)
        self._step(step)
        self.history.append(self._amp())


    def __str__(self):
        xStr = '%.2f' % (self.x)
        yStr = '%.2f' % (self.y)
        rStr = '%.2f' % (self.r)
        fStr = '%.2f' % (self.f)
        aStr = '%.2f' % (self._amp())
        return "x: %s y: %s r: %s f: %s a: %s" % (xStr.ljust(6), yStr.ljust(6),
                                        rStr.ljust(6), fStr.ljust(6), aStr.ljust(6))


#-----------------------------------------------------------------||||||||||||--

class PabonGame:
    def __init__(self, partitionNo, signal=None):
        if signal == None:
            self.signal = [.5, -.1, .9, .4, -.2, .8]
        else:
            self.signal = signal

        self.partitionNo = partitionNo
        self.partitionFreq = []

        freqMin = 1
        freqMax = 100
        freqStep = (freqMax - freqMin) / self.partitionNo

        f = freqMin
        for i in range(0, self.partitionNo):
            self.partitionFreq.append(f)
            f = f + freqStep

        self.components = []
        rInit = 0
        i = 0 # used for indexing position
        for f in self.partitionFreq:
            self.components.append(SpectralComponent(i, rInit, f))
            i = i + 1


    def run(self):
        t = 0
        for step in self.signal:
            print('step:', step, 'time:', t)
            for part in self.components:
                part.postTime(t, step)

            print(self._repr())
            t = t + 1

    def _repr(self, style=''):
        msg = []
        for part in self.components:
            msg.append(str(part))
            msg.append('\n')
        return ''.join(msg)

    def __str__(self):
        return self._repr()

#-----------------------------------------------------------------||||||||||||--


def testTone(dur, f, phaseInit, sr):
    samples = [0] * dur * sr
    sampleDur =  1. / sr
    t = 0
    for x in range(0, (dur*sr)):
        phase = phaseInit + (t * f)
        samples[x] = math.sin(2.0 * math.pi * phase)
        t = t + sampleDur
    return samples




#-----------------------------------------------------------------||||||||||||--
class Test:
    def __init__(self):
        a = PabonGame(6)
        a.run()


if __name__ == '__main__':
    Test()




#-----------------------------------------------------------------||||||||||||--





# from oscillator.py
# phase is a floating point value b/n 0 and 1
# class Sine(Function):
#       """
#       Sinusoid translated in the [0,1] range
#       """
#       def __init__(self, frequency = 1.0, phase0 = 0.0):
#            Function.__init__(self)
#            self.frequency = frequency
#            self.phase0 = phase0
# 
#       def __call__(self, t):
#            phase = self.phase0 + t * self.frequency
# 
#            # range is -1 to 1, 2 units
#            # need to shift up to 2 to 9, then divide by 2
#            return (1.0 + sin(2.0 * pi * phase)) / 2.0





























