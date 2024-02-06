## Setting EventMode and Creating a Texture

As explained in , the athenaCL EventMode determines what instruments are available for Texture creation. In the following example, the EventMode is set to midi, the TextureModule LiteralVertical is selected, a new Texture is created with instrument 0, and the Texture is displayed with TIv.
      

**Creating a Texture with TM LiteralVertical**

```
pi{q1}ti{} :: emo midi
EventMode mode set to: midi.

pi{q1}ti{} :: tmls
TextureModules available:
{name,TIreferences}
   DroneArticulate    0
   DroneSustain       0
   HarmonicAssembly   0
   HarmonicShuffle    0
   InterpolateFill    0
   InterpolateLine    0
   IntervalExpansion  0
   LineCluster        0
 + LineGroove         0
   LiteralHorizontal  0
   LiteralVertical    0
   MonophonicOrnament 0
   TimeFill           0
   TimeSegment        0

pi{q1}ti{} :: tmo lv
TextureModule LiteralVertical now active.

pi{q1}ti{} :: tin a1 0
TI a1 created.

pi{q1}ti{a1} :: tiv
TI: a1, TM: LiteralVertical, TC: 0, TT: TwelveEqual
pitchMode: pitchSpace, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: +, duration: 000.0--19.94
(i)nstrument        0 (generalMidi: piano1)
(t)ime range        00.0--20.0
(b)pm               constant, 120
(r)hythm            pulseTriple, (constant, 4), (basketGen, randomPermutate,
                    (1,1,2,3)), (constant, 1), (constant, 0.75)
(p)ath              q1
                    (D2,G#3,A3,D3,E2,B2,A2),(C4,C#4,F#3,G4,A3),(G#5,A4,D#4,E5)
                    10.00(s), 6.25(s), 3.75(s)
local (f)ield       constant, 0
local (o)ctave      constant, 0
(a)mplitude         randomBeta, 0.4, 0.4, (constant, 0.7), (constant, 0.9)
pan(n)ing           constant, 0.5
au(x)iliary         none
texture (s)tatic
      s0            loopWithinSet, on
      s1            maxTimeOffset, 0.03
      s2            levelFieldPolyphonic, event
      s3            levelOctavePolyphonic, event
      s4            pathDurationFraction, on
texture (d)ynamic   none     
```

Notice that the Texture's Path attribute is set to q1. In all cases, a Texture, when created, links to the active Path. The Path a Texture links to can be edited later if necessary. Notice also that the Path listing in the TIv display shows the pitches of the Path, as well as timings for each set: 10, 6.25, and 3.74 seconds respectively. These times are the result of the duration fraction applied to the Texture's duration.
      
To hear this Texture, create an EventList as explained in . After using the ELn command, the ELh command can be used to open the MIDI file. Notice that each chord lasts the appropriate duration fraction of the total twenty-second duration of the Texture.
      
A few small edits to this Texture will make it more interesting. In the following example, both the rhythm and amplitude are edited: the rhythm is given more Pulses and made to oscillate back and forth along the specified series; the amplitude randomly selects from a list of four amplitudes.
      

**Editing a Texture**

```
pi{q1}ti{a1} :: tie r l, ((4,1,1), (4,1,1), (4,3,0), (2,3,1), (3,2,1), (3,2,1)), oo
TI a1: parameter rhythm updated.

pi{q1}ti{a1} :: tie a bg, rc, (.5,.6,.8,1) 
TI a1: parameter amplitude updated.
```

Again, ELn and ELh can be used to create and audition the resulting musical structure.
      
