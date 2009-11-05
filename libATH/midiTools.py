#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          midiTools.py
# Purpose:       general classes for writting a midi file from a note list.
#                    based in part on python code in Musical MIDI Accompaniment (MMA)
#                    developed by Bob van der Poel.
#
# Authors:       Christopher Ariza
#                    Bob van der Poel
#
# Copyright:     (c) 2003-2006 Christopher Ariza
#                    (c) 2002-2003 Bob van der Poel
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
_MOD = 'midiTools.py'


#-----------------------------------------------------------------||||||||||||--
# midi decimal conversion routines
# used for acToolbox output format

def decimalNoteOn(ch=0):
    assert ch >= 0 and ch <=15 #
    return ch + 144

def decimalController(ch=0):
    assert ch >= 0 and ch <=15 #
    return ch + 176

def decimalProgramChange(ch=0):
    assert ch >= 0 and ch <=15 #
    return ch + 192


#-----------------------------------------------------------------||||||||||||--
# midi number packing routines.
def intToWord(x):
    """ Convert a 2 byte MSB LSB value. """
    x = int(x)
    return  chr(x>>8 & 0xff) + chr(x & 0xff)

def intToLong(x):
    """ Convert an int to a 4 byte MSB...LSB value. """
    return intToWord(x>>16) + intToWord(x)

def intTo3Byte(x):
    """ Convert an int to a 3 byte MSB...LSB value.
    only used for self.addTempo, may not be necessary"""
    return intToLong(x)[1:]

def intToVarNumber(x): 
    """ Convert an int to a variable length midi value. """
    lst = chr(x & 0x7f)
    while    1:
        x = x >> 7
        if x:
            lst = chr((x & 0x7f) | 0x80) + lst
        else:
            return lst


#-----------------------------------------------------------------||||||||||||--
class MidiPart:
    """defines an instrument, based on' mma's pattern thingys
    most opperations don on a global self.mtrks dictionary
    including even creating MidiTrack instances
    """

    def __init__(self, name, pgm, mtrks, tickPerBeat, tempo):
        self.name = name
        self.channel = 1 # must be between 1 and 16; 0 is a mute, asigned later
        self.pgm = pgm # program number to use initially
        self.mtrks = mtrks # this is a reference to the mtrks dictionary
                         # need to do operations on this dictionary, dont make a copy
        self.initOffset = 0 # used as base starting positon, in ticks
        self.tickPerBeat = tickPerBeat
        self.tempo = tempo
        self.defaultChVol = 127 # default channel volume
        self.chShare = 0 # if more than one inst useing a channel, need to 
                                    # do per-note program changes

    # this sets name, channel, and volume
    def setChannel(self, c):
        """performs basic setup for a track, including channel, title, volume
            Set the midi-channel number for a track. 
            Checks for channel duplication, Sets default channel volume.
        """
        self.channel = int(c)
        if self.mtrks.has_key(self.channel): # if another inst is using channel
            # find that inst, set it to share, set this inst to share
            pass
        else: # create new instance for this channel
             # create MidiTrack instance
            self.mtrks[self.channel] = MidiTrack(self.channel)
            self.mtrks[self.channel].addTrkName(0, self.name)
            self.mtrks[self.channel].addChannelVol(0, self.defaultChVol)

    def getNoteLen(self, n):
        """Convert a Note to a midi tick length. 
            n is a duration in seconds
        """
        beatPerS = self.tempo / 60.0
        tickPerS = beatPerS * float(self.tickPerBeat)
        durTicks = int(round((tickPerS * n), 0))
        return durTicks

    def score(self, noteList): #, ctable):
        """ write music data to mtracks. """
        # one program change per score only if not > 1 track using this ch
        if not self.chShare: # if not shareing, do pgm change now
            self.mtrks[self.channel].addProgChange(self.initOffset, self.pgm)

        #list form: startT, noteDur, notVol, notNum, 
        for line in noteList:
            # offset is the event start time, converted to ticks
            offset = self.getNoteLen(line[0]) # convert seconds to ticks
            offset = offset + self.initOffset # add inti offset to all t values

            dur = self.getNoteLen(line[1]) # convert seconds to ticks
            vol = line[2] # velocity
            mpc = line[3] # note number
            pan = line[4] # pan val, 0 to 127

            if vol == 0: continue # dont add 0 velocities
            # subtract on tick from pgm offset to give change time
            if self.chShare: # if true, other insts are using this channel
                self.mtrks[self.channel].addProgChange(offset, self.pgm)
            self.mtrks[self.channel].addPan(offset, pan) # add pan
            self.mtrks[self.channel].addPairToTrack(offset, dur, mpc, vol)


#-----------------------------------------------------------------||||||||||||--
# Midi track class. All the midi creation is done here.
# create an instance for each track. 
class MidiTrack:
    def __init__(self, channel):
        # this dictionary stores dictionary pairs of time offsets and events
        # processed with writeMidiTrack
        self.miditrk={}
        self.channel = channel - 1 # off by one correction
        self.trkName = '' # name is given by first inst to use this ch.

    #ADD an evnt to a track!
    def addToTrack(self, offset, event):
        """ Add an event to a track.
            NOTE on track composition: 
                each miditrk is a dictionary
                keys == midi timing offset
                data == list of events
            So, we end up with:
                miditrk[123] = [event1, event2, ...]
            Each event can be any number of bytes in length.
            Events are stored in creation order.
        """
        if offset < 0: offset = 0
        if self.miditrk.has_key(offset):
            self.miditrk[offset].append(event)
        else:
            self.miditrk[offset]=[event]

    def addTimeSig(self, offset,    nn, dd, cc, bb):
        """ Create a midi time signature.
            delta - midi delta offset
            nn = sig numerator, beats per measure
            dd - sig denominator, 2=quarter note, 3=eighth, 
            cc - midi clocks/tick
            bb - # of 32nd notes in quarter (normally 8)      
            returns - packed string 
        """
        self.addToTrack(offset, chr(0xff) + chr(0x58) + chr(0x04) + chr(nn) +
            chr(dd) + chr(cc) + chr(bb) )

    def addText(self, offset, msg):
        """ Create a midi TextEvent."""
        self.addToTrack( offset,
            chr(0xff) + chr(0x01) + intToVarNumber(len(msg)) + msg )

    def addTrkName(self, offset, msg):
        """ Creates a midi track name event. """
        self.addToTrack(offset,
            chr(0xff) + chr(0x03) + intToVarNumber(len(msg)) + msg )
    
    def addProgChange(self, offset, program):
        """ Create a midi program change.
            program - midi program
            Returns - packed string
        """
        self.addToTrack(offset,
            chr(0xc0 | self.channel) + chr(program) )

    def addGlis(self, offset, v):
        """ Set the portamento. LowLevel MIDI.
            This does 2 thing, turns portamento on/off,
            then sets the LSN rate.
        """
        if v == 0:
            self.addToTrack(offset, 
                chr(0xb0 | self.channel) + chr(0x41) + chr(0x00) )
        else:
            self.addToTrack(offset,
                chr(0xb0 | self.channel) + chr(0x41) + chr(0x7f) )
            self.addToTrack(offset,
                chr(0xb0 | self.channel) + chr(0x05) + chr(v) )

    def addPan(self, offset, v):
        """ Set the lsb of the pan setting
        controller 10"""
        #v = int(v) # make sure pan is an int
        self.addToTrack(offset,
            chr(0xb0 | self.channel) + chr(0x0a) + chr(v) )

    # this should be the master volume for the channel
    def addChannelVol(self, offset, v):
        """ Set the midi channel volume.
        controller 7"""
        #v = int(v) # make sure int
        self.addToTrack(offset,
            chr(0xb0 | self.channel) + chr(0x07) + chr(v) )

    def addTempo(self, offset, beats):
        """ Create a midi tempo meta event.
        beats - beats per second
        Return - packed midi string
        """
        self.addToTrack(offset,
            chr(0xff) + chr(0x51) +chr(0x03) + intTo3Byte(60000000/beats))

    def addPairToTrack(self, offset, duration, note, v):
        """ Add a note on/off pair to a track.
        """
        #note = int(note) # double check these are integers
        #v = int(v)
        # a ValueError will be rause if note is beyond chr's ability
        st = chr(0x90 | self.channel) + chr(note)
        self.addToTrack(offset, st + chr(v))
        self.addToTrack(offset + duration, st + chr(0))
    
    def writeMidiTrack(self, out):
        # Create the track. We convert timing offsets to midi-deltas.
        # This is done in-memory so we can determine the size which
        # is put in before the data.
        out.write("MTrk")
        sizePt = out.tell()
        out.write( intToLong(0) )   # dummy, redo at end
        
        dataPt = out.tell()
        trkKeys = self.miditrk.keys() # the keys are the midi timing offset
        trkKeys.sort()

        last = 0
        for tOffset in trkKeys:
            delta = tOffset - last
            if delta < 0:
                delta = 0
            # get all event data from this point
            for eventData in self.miditrk[tOffset]:
                out.write(intToVarNumber(delta) )
                out.write(eventData)
                delta = 0
            last = copy.copy(tOffset)

        # Add an EOF to the track
        out.write(intToVarNumber(0))
        out.write(chr(0xff) + chr(0x2f) + chr(0x00) )
        
        totsize = out.tell() - dataPt
        out.seek(sizePt)

        out.write(intToLong(totsize))
        out.seek(0, 2)      

#-----------------------------------------------------------------||||||||||||--
# self.mtrks is storage for the MIDI data as it is created. It is a dict of
# class instances. Each instance is a MidiTrack(). Keys are the midi channel
# numbers. Ie, self.mtrks[2] is for channel 2, etc.
# self.mtrks[0] is for the meta stuff.

class MidiScore:
    def __init__(self, trackList=None, fileName='athenaCL midi', tempo=120):
        "auto assign channels if none are given"
        self.trackList = trackList
        self.maxCh = 16 # maximum channel assignment allowed
        self.mtrks = {} # dict lives here, pased it inst class for writting

        self.tickPerBeat = 960 # midi ticks per quarter note, PPQN # og was 192
        self.tickOffsetBase = int(round(self.tickPerBeat * .005))
        self.tempo = tempo
        self.fileName = fileName

        self.tnames = {} 
        chList = range(1, (self.maxCh + 1)) # 1-16
        chList.remove(10) # 10 is reserved for drum kit on gm
        chIndex = 0 # position in list
        for name, pgm, ch, score in self.trackList: # passing a ref to dict
            if ch in [0, None]: # auto assign channels if not assigned
                ch = chList[chIndex]
                chIndex = chIndex + 1
                if chIndex >= (self.maxCh - 1): # reset when index == 15
                    chIndex = 0
            else:
                pass # leave channel number alone
            self.tnames[name] = MidiPart(name, pgm, self.mtrks, 
                                                     self.tickPerBeat,
                                                     self.tempo) 
            self.tnames[name].setChannel(ch) # creates mtrack instance 
            self.tnames[name].score(score) # creates mtrack instance 

    def _setChShareFlags(self):
        """runs through all channels and counts tally of use per ch
        then runs through all insts, check channel, and see if being used 
        more than once. if so, set chShare flag to true so a program change
        will be sent with each note event
        """
        instPerCh = {}
        for ch in range(1, (self.maxCh+1)): # dotn include 0 meta track
            count = 0
            for name in self.tnames.keys():
                if self.tnames[name].channel == ch:
                    count = count + 1
            instPerCh[ch] = count

        shiftPos = 0 # start at zero, mult offset base
        # used to randomly shift tracks latter if using the same channel
        for name in self.tnames.keys():
            instSharingThisCh = instPerCh[self.tnames[name].channel]
            if instSharingThisCh > 1: # if more than 1 inst on this ch
                self.tnames[name].chShare = 1 # need to share, to pgm changes
                # give a global offset to avoid collisions in this ch
                self.tnames[name].initOffset = (self.tickOffsetBase * shiftPos)
                shiftPos = shiftPos + 1
            else: # 1 or 0 insts are using this channel
                self.tnames[name].chShare = 0 # false
                self.tnames[name].initOffset = 0 # no offset necesssary

    def _setHeader(self):
        # Set up initial meta track stuff. Track 0 == meta
        self.mtrks[0] = MidiTrack(0)
        self.mtrks[0].addTrkName(0, self.fileName) # leadings zero is start time
        self.mtrks[0].addTempo(0, self.tempo) 
        #self.mtrks[0].addTimeSig(0, 4, 2, 48, 8) 
        # 4, 2 is 4/4 meter; 
        # 96 sets beat as whole note
        # 24 sets beat as quarter
        self.mtrks[0].addTimeSig(0, 4, 2, 24, 8) 
        self.mtrks[0].addText(0, 'created with athenaCL') 
                
    def write(self, filePath):
        "writes the midi to a file"
        self._setHeader() # set header information
        self._setChShareFlags() # if more than on trk per channel try to fix
        # this may raise an exception, OSError or IOError
        f = open(filePath, 'wb') # get file obj named f
        # count tracks; needed for header       
        mtrkKeys = self.mtrks.keys()
        mtrkKeys.sort()
        trackCount = 1    # account for meta track
        for n in mtrkKeys[1:]:    # check all but 0 (meta)
            if len(self.mtrks[n].miditrk) > 1:
                trackCount = trackCount + 1
        # Write Midi file header.
        f.write("MThd" + intToLong(6) + intToWord(1) +
                  intToWord(trackCount) + intToWord(self.tickPerBeat))
        # Write meta track
        self.mtrks[0].writeMidiTrack(f)
        # Write the remaining tracks
        for n in mtrkKeys[1:]:
            if len(self.mtrks[n].miditrk) > 1:
                self.mtrks[n].writeMidiTrack(f) 
        f.close() # close file
        

#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.libATH import osTools
    # score format: sTime, dur, vel, mPcs, pan
    scoreC =     ((0,     .5,    90,    60, 60),
                  (.6,  .5,  90,    51, 60),
                  (1,     .5,    120, 62, 60),
                  (1.6, .5,  90,    69, 60),
                  (2.5, .5,  90,    51, 60),
                  (3.1, .5,  120, 62, 60),
                  (3.5, .5,  90,    69, 60),
                  )
    scoreB =     ((0,        .75,    90,    80, 120),
                  (.75,  .75,    90,    20, 120),
                  (1.25,     .75,    120, 30, 120),
                  (2,        .75,    90,    32, 120),
                  (2.5,  .25,    90,    50, 120),
                  (2.75,     .25,    120, 51, 120),
                  (3,        .25,    90,    52, 120),
                  (3.25,     .25, 126,  52, 120),
                  (3.50,     .25,    10,    52, 120),
                  (3.75,     .25,    20,    52, 110),
                  (4,        .25,    30,    52, 80),
                  (4.25,     .25,    50,    52, 60),
                  (4.50,     .25,    60,    52, 40),
                  (4.75,     .25,    80,    52, 20),
                  (5,        2,  90,    52, 0),
                  )
    # trackName, pgmNumber, ch(optional), scoreEventMode
    trackList = (('testA', 0, None, scoreC),
                     ('testD', 0, None, scoreB),)
    a = MidiScore(trackList)
    testPath = osTools.tempFile('.mid')
    print testPath
    a.write(testPath) # writes in cwd




