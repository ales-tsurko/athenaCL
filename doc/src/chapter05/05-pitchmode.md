## PitchMode

PitchMode is a Texture attribute that controls the interpretation of the Path from inside a TextureInstance.
      
PitchMode determines if a Path is represented to the Texture as a pitch space set, a pitch class set, or set class. As a pitch space set, a Texture performs register information included in a Path. The set (1,11,24), performed as a pitch space set, would consist of a C-sharp, a B-natural a minor seventh above the lowest pitch, and C-natural an octave and major-seventh above the lowest pitch. The set (1,11,24) performed as a pitch-class set, would be interpreted as the set (1,11,0): register information is removed, while pitch class is retained. The set (1,11,24), performed as a set-class, would be interpreted as the set (0,1,2): register and pitch-class are removed, while the normal-form of the set-class is retained.
      
In the following example, a new Texture is created from TextureModule LineGroove. First, the TM must be selected with the TMo command. Next, a new Texture named b1 is created with the TIn command. The TImode command can be used to edit many Texture options. In this example, pitchMode is selected and "pcs," for pitch class space, is selected. Finally, the Texture is given a more interesting rhythm, by use of the Rhythm ParameterObject markovPulse, and is panned to the right with a constant value:
      

**Editing PitchMode of a TextureInstance**

```
pi{q1}ti{a1} :: tmo lg
TextureModule LineGroove now active.

pi{q1}ti{a1} :: tin b1 0
TI b1 created.

pi{q1}ti{b1} :: timode
edit TI b1: Pitch, Polyphony, Silence, or PostMap Mode? (p, y, s, m): p
      current Pitch Mode: pitchSpace. enter new mode (sc, pcs, ps): pcs
Pitch Mode changed to pitchClass

pi{q1}ti{b1} :: tie
edit TI b1
which parameter? (i,t,b,r,p,f,o,a,n,x,s,d): r
current rhythm: pulseTriple, (constant, 4), (basketGen, randomPermutate,
(1,1,2,3)), (constant, 1), (constant, 0.75)
new value: mp, a{6,1,1}b{3,2,0}c{3,5,1}:{a=5|b=3|c=2}, (c,0)
TI b1: parameter rhythm updated.

pi{q1}ti{b1} :: tie n c,.9
TI b1: parameter panning updated.

pi{q1}ti{b1} :: tiv
TI: b1, TM: LineGroove, TC: 0, TT: TwelveEqual
pitchMode: pitchClass, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: +, duration: 000.0--19.83
(i)nstrument        0 (generalMidi: piano1)
(t)ime range        00.0--20.0
(b)pm               constant, 120
(r)hythm            markovPulse, a{6,1,1}b{3,2,0}c{3,5,1}:{a=5|b=3|c=2},
                    (constant, 0)
(p)ath              q1
                    (D2,G#3,A3,D3,E2,B2,A2),(C4,C#4,F#3,G4,A3),(G#5,A4,D#4,E5)
                    10.00(s), 6.25(s), 3.75(s)
local (f)ield       constant, 0
local (o)ctave      constant, 0
(a)mplitude         randomBeta, 0.4, 0.4, (constant, 0.7), (constant, 0.9)
pan(n)ing           constant, 0.9
au(x)iliary         none
texture (s)tatic
      s0            parallelMotionList, (), 0.0
      s1            pitchSelectorControl, randomPermutate
      s2            levelFieldMonophonic, event
      s3            levelOctaveMonophonic, event
texture (d)ynamic   none
```

Because Path q1 is still active, this new Texture is assigned the same Path as Texture a1. After setting the Texture's pitchMode to pitchClassSpace, however, Texture b1 will receive only pitch class values from Path q1: all register information, as performed in Texture a1, is stripped. By creating a new EventList with ELn and auditioning the results, it should be clear that both Textures share the same pitch information and duration weighting. Notice that the faster-moving single-note line Texture b1, however, stays within a single register. When a Texture is in pitchClassSpace Pitch mode, all pitches from a Path are interpreted within the octave from C4 to C5. 
      
