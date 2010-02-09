

import time
from athenaCL.libATH import pitchTools
from athenaCL.libATH import rhythm
from athenaCL.libATH import drawer




#-----------------------------------------------------------------||||||||||||--

class Note:

    def __init__(self, ps, dur, tie=None, dyn=None):
        """pitch format is standard atheanCL ps units, where midi 60 is 0
        duration is given as pulse triple
        may add dynmaics
        if ps == None, this is a rest"""
        # modify to accept objects as well
        self._ps = ps # athenacl pitch space value

        if hasattr(dur, 'triple'): # its a pulse triple
            self._dur = dur
        else:
            self._dur = rhythm.Pulse(dur) # convert to pulse object

        self._tie = tie # a number code for various formats
        self._dyn = dyn # provude a dynamic value

        self._psName = None      
        self._psAlter = None          
        self._psOctave = None       

        if self._ps != None:
            self._psName, self._psAlter, self._psOctave = pitchTools.psToMusicXml(self._ps)

    def getPitch(self):
        msg = []
        if self._ps == None:
            msg.append('\t\t<rest />') # no pitch, its a rest
        else:
            msg.append('\t\t<pitch>')
            msg.append('\t\t\t<step>%s</step>' % self._psName)
            if self._psAlter != '0':
                msg.append('\t\t\t<alter>%s</alter>' % self._psAlter)
            msg.append('\t\t\t<octave>%s</octave>' % self._psOctave)
            msg.append('\t\t</pitch>')
        return '\n'.join(msg)


    def getDur(self, divisions=120):
        """divisions is number of division in each quarter note
        this is set for each measure; default here is 120"""
        # assume that 1,1,1 is a quarter note
        div, mult, acc = self._dur.get() # returns pulse triple
        dur = (divisions // div) * mult # this mus tbe an integer
        msg = []
        msg.append('\t\t<duration>%s</duration>' % dur)
        return ''.join(msg)

    def getAccidental(self):
        """provide accidental note data"""
        # must add redundant accidental indication to show in finale
        # sharp, sharp-sharp, flat-flat, natural-sharp, natural-flat, 
        # quarter-flat, quarter-sharp, three-quarters-flat, and three-quarters-sharp

        # http://www.recordare.com/xml/musicxml-index.html

        msg = []
        # if pitch is defined, and tie is not stopping
        if self._ps != None and self._tie not in [0,2]:
            if self._psAlter == str(0):
                accidental = 'natural'
            elif self._psAlter == str(0.5):
                accidental = 'quarter-sharp'
            elif self._psAlter == str(1):
                accidental = 'sharp'
            elif self._psAlter == str(1.5):
                accidental = 'three-quarters-sharp'
            elif self._psAlter == str(-0.5):
                accidental = 'quarter-flat'
            elif self._psAlter == str(-1):
                accidental = 'flat'
            elif self._psAlter == str(-1.5):
                accidental = 'three-quarters-flat'
            else:
                accidental = None
            if accidental != None:
                msg.append('\t\t<accidental>%s</accidental>' % accidental)
        return '\n'.join(msg)


    def getTie(self):       
        """provide a start or end tie indication
        1 is start, 0 is stop; 2 is stop then start
        None can be provided to bypass
        """
        # http://www.recordare.com/xml/midi-compatible.html
        msg = []
        if self._tie in [0, 2]: # may be None
            msg.append('\t\t<tie type="stop" />')
        elif self._tie in [1, 2]:
            msg.append('\t\t<tie type="start" />')
        return ''.join(msg)

# Alter values of -2 and 2 can be used for double-flat and double-sharp. Decimal values can be used 
# for microtones (e.g., 0.5 for a quarter-tone sharp), but not all programs may convert this into 
# MIDI pitch-bend data. 

# The duration element is an integer that represents a note's duration in terms of divisions per 
# quarter note. Since our example has 12 divisions per quarter note, a quarter note has a duration of 
# 12. The eighth-note triplets have a duration of 4, while the eighth notes have a duration of 6. 


    def __call__(self, divisions):
        msg = []
        msg.append('\t<note>')
        msg.append(self.getPitch())
        msg.append(self.getDur(divisions))
        msg.append(self.getTie())
        msg.append(self.getAccidental()) # accidental has to come after dur
        msg.append('\t</note>')
        return '\n'.join(msg)
    












#-----------------------------------------------------------------||||||||||||--
class Measure:

    def __init__(self):
        self._attributes = {}
        self._attributesLast = {} # store last measure
        self._notes = [] # a list of objects

    def setAttributesArg(self, divisions=120, key=(0,'major'), 
                            time=(4,4), clef=('G', 2)):
        """divisions is number of divisions per quarter note
        can be anything; but makes sense to use a large value divisible
        by 5, 4, 3, and 2
        """
        self._attributes['divisions'] = divisions
        self._attributes['key'] = key
        self._attributes['time'] = time
        self._attributes['clef'] = clef
        
    def setAttributes(self, attributes):
        """alternative method using direct dictionary assignemtn"""
        self._attributes = attributes

    def setAttributesLast(selt, attribute):
        self._attributesLast = attributes

    def getAttributes(self):
        """return current attribute dictionary for comparison later"""
        return self._attributes 

    #-----------------------------------------------------------------------||--
    def addNote(self, ps, dur, dyn=None):
        """add a list of note objects?"""
        obj = Note(ps, dur, dyn)
        self._notes.append(obj)
    
    def setNotesArg(self, notes):
        """provide a list of arguments as dictionaries"""
        for q in notes:
            obj = Note(q['ps'], q['dur'], q['dyn'])
            self._notes.append(obj)

    def setNotes(self, notes):
        """list of note objects"""
        self._notes = notes



    #-----------------------------------------------------------------------||--
    def __call__(self, number):
        """number is measure number"""
        msg = []
        msg.append("""<measure number="%s">""" % number)

        msg.append("""<attributes>""")

        msg.append("""\t<divisions>%s</divisions>""" % self._attributes['divisions'])

        # if different
        if ('key' not in self._attributesLast or 
            self._attributes['key'] != self._attributesLast['key']):
            msg.append("""\t<key>
\t\t<fifths>%s</fifths>
\t\t<mode>%s</mode>
\t</key>""" % (self._attributes['key'][0], self._attributes['key'][1]))

        if ('time' not in self._attributesLast or 
            self._attributes['time'] != self._attributesLast['time']):

            msg.append("""\t<time>
\t\t<beats>%s</beats>
\t\t<beat-type>%s</beat-type>
\t</time>""" % (self._attributes['time'][0], self._attributes['time'][1]))

        if ('clef' not in self._attributesLast or 
            self._attributes['clef'] != self._attributesLast['clef']):
            msg.append("""\t<clef>
\t\t<sign>%s</sign>
\t\t<line>%s</line>
\t</clef>""" % (self._attributes['clef'][0], self._attributes['clef'][1]))

        msg.append("""</attributes>""")

        # call each note object to get note markup
        for obj in self._notes:
            # call note to get note date
            msg.append(obj(self._attributes['divisions'])) 

        msg.append("""</measure>""")
        return '\n'.join(msg)








#-----------------------------------------------------------------||||||||||||--
class Score:

    def __init__(self):

        self._partRef = [] # defin ordered collections of parts as dictionaries
        self._id = {}
        self._measures = [] # a list of lists, each with measure objects


        self.head = """<?xml version="1.0" encoding="UTF-8" standalone="no"?> 
<!DOCTYPE score-partwise PUBLIC 
     "-//Recordare//DTD MusicXML 1.1 Partwise//EN" 
     "http://www.musicxml.org/dtds/partwise.dtd"> 
"""
        self.scoreOpen = '<score-partwise>'
        self.scoreClose = '</score-partwise>'


    def getEncoding(self):
        y = time.localtime()[0]
        m = time.localtime()[1]
        d = time.localtime()[2]
        m = str(m).rjust(2).replace(' ', '0') # zero pad
        d = str(d).rjust(2).replace(' ', '0')
        return """\t<encoding> 
\t\t<encoding-date>%s-%s-%s</encoding-date> 
\t\t<software>athenaCL</software> 
\t</encoding>""" % (y, m, d) 



    def setPartList(self, partRef):
        """a list of dictionaries like this
            {'part-name':'violoncello 1', 'instrument-name':'Cello', 'midi-channel':'1', 'midi-program':'1'},
        part-name is what apprears next to part
        """ 
        self._partRef = partRef # a list of dictionaries        

    def getPartList(self):
        msg = []
        msg.append('<part-list>')
        # could skip part group
        msg.append("""\t<part-group type="start" number="1">
\t\t<group-symbol>bracket</group-symbol>
\t</part-group>""")
        for i in range(len(self._partRef)):
            n = i + 1
            msg.append('\t<score-part id="P%s">' % n)
            msg.append("""\t\t<part-name>%s</part-name>
\t\t<score-instrument id="P%s-I%s">
\t\t\t<instrument-name>%s</instrument-name>
\t\t</score-instrument> """ % (self._partRef[i]['part-name'], 
                                    n, n, 
                                    self._partRef[i]['instrument-name'],))

            msg.append("""\t\t<midi-instrument id="P%s-I%s">
\t\t\t<midi-channel>%s</midi-channel>
\t\t\t<midi-program>%s</midi-program>
\t\t</midi-instrument>"""   % (n, n, 
                                self._partRef[i]['midi-channel'], 
                                self._partRef[i]['midi-program'],))
            msg.append('\t</score-part>')

        msg.append("""\t<part-group type="stop" number="1" />""")
        msg.append('</part-list>')
        return '\n'.join(msg)


    def setWork(self, title=None, number=None):
        self._title = title
        self._number = number

    def getWork(self):
        msg = []
        msg.append('\t<work>')
        if self._title != None:
            msg.append('\t\t<work-title>%s</work-title>' % self._title)
        if self._number != None:
            msg.append('\t\t<work-number>%s</work-number>' % self._number)
        msg.append('\t</work>')
        return '\n'.join(msg)

    def setIdentification(self, id):
        """dictionary defining 'creator', righs; encoding from elsewhere
        """
        self._id = id

    def getIdentification(self):    
        msg = []
        msg.append('<identification>')
        if 'creator' in self._id:
            msg.append('\t<creator>%s</creator>' % self._id['creator'])
        if 'rights' in self._id:
            msg.append('\t<rights>%s</rights>' % self._id['rights'])
        msg.append(self.getEncoding())
        msg.append('</identification>')
        return '\n'.join(msg)


    #-----------------------------------------------------------------------||--
    def addMeasureList(self, measurePart):
        """add a list of measure objects"""
        self._measures.append(measurePart)
    
    def setMeasures(self, measures):
        """set a list of measures for each part
        list of measures objects"""
        self._measures = measures


    #-----------------------------------------------------------------------||--

    def getPart(self, partId):
        msg = []
        msg.append('<part id="P%s">' % (partId+1)) # shift one for id
        measureNumber = 1    # count is measure number
        for measure in self._measures[partId]:
            msg.append(measure(measureNumber))
            measureNumber = measureNumber + 1
        msg.append('</part>')
        return '\n'.join(msg)
        
    
    #-----------------------------------------------------------------------||--
    def write(self, fp):
        msg = []
        msg.append(self.head)
        msg.append(self.scoreOpen) 

        msg.append(self.getWork())
        msg.append(self.getIdentification())
        msg.append(self.getPartList())

        for partId in range(len(self._partRef)):
            msg.append(self.getPart(partId))

        msg.append(self.scoreClose) 


        # write file
        #print '\n'.join(msg)
        f = open(fp, 'w')
        f.write('\n'.join(msg))
        f.close()












class Test:


    def __init__(self):
        from athenaCL.libATH import osTools
        from athenaCL.libATH import rhythm
        import random

        partList = [
            {'part-name':'Violoncello 1', 'instrument-name':'Cello', 'midi-channel':'1', 'midi-program':'1'},
            {'part-name':'Violoncello 2', 'instrument-name':'Cello', 'midi-channel':'2', 'midi-program':'23'},
            ]

        measureList = []
        for partId in range(len(partList)):
            part = []

            mForm = [(1,4)]

            pulseSeq = []
            pitchSeq = []
            for i in range(40):
                ps = random.choice([0,.5,1,1.5,None,13])
                pitchSeq.append(ps)
                r = random.choice([[2,1], [2,3], [4,1], [4,3], [1,3], [1,2]])
                pulseSeq.append(r)

            a = rhythm.RhythmMeasure(pulseSeq, pitchSeq)
            a.setMeasureForm(mForm)
            postPulse, postEvent = a.partition()

            for mNumber in range(len(postPulse)):

                m = Measure()
                m.setAttributesArg() # will provide defaults

                for eNumber in range(len(postPulse[mNumber])):

                    dur, tie = postPulse[mNumber][eNumber]
                    ps = postEvent[mNumber][eNumber]
                    m.addNote(ps, dur, tie)

                part.append(m)

            measureList.append(part)

        id = {'creator': 'Test Author', 'rights': 'Copyright 2008 Test Author'}

        a = Score()
        a.setPartList(partList)
        a.setWork('Test Composition')
        a.setIdentification(id)
        a.setMeasures(measureList)

        fp = drawer.tempFile('.xml')
        print fp
        a.write(fp)
        
        osTools.openMedia(fp)


if __name__ == '__main__':
    t = Test()



# this is a test of newness




















