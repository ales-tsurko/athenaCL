## Editing Local Octave

With a Texture's local field and local octave controls, ParameterObjects can be used to alter the pitches derived from a Path. In most TextureModules, the transformation offered by field and octave control can be applied either once per Multiset, or once per event. This is set by editing the TextureStatic options levelField and levelOctave.
      
In the following example, the local octave attribute of Texture b1 is edited such that octaves are chosen in order from a list of possibilities, creating a sequence of octave transpositions. An octave value of 0 means no transposition; an octave of -2 means a transposition two octaves down.
      

**Editing Local Octave**

```
pi{q1}ti{b1} :: tie
command.py: raw args  
edit TI b1
which parameter? (i,t,b,r,p,f,o,a,n,x,s,d): o
current local octave: constant, 0
new value: bg, oc, [-3,-2,2,-1]
TI b1: parameter local octave updated.

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
local (o)ctave      basketGen, orderedCyclic, (-3,-2,2,-1)
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

Listening to the results of the previous edit (with ELn and ELh), it should be clear that a new octave is applied to each event of Texture b1, creating an regular oscillation of register independent of Path Multiset.
      
Alternatively, the user may desire local octave and field controls to only be applied once per Multiset. This option can be set for TextureModule LineGroove by editing the TextureStatic parameter "levelOctaveMonophonic." In the following example, the user examines the documentation of ParameterObject levelOctaveMonophonic, and a copy of Texture b1 is created named b2. Next, this Texture's panning is edited, and then the TextureStatic option levelOctaveMonophonic is changed from "event" to "set":
      

**Editing TextureStatic**

```
pi{q1}ti{b1} :: tpv leveloctave
Texture Static ParameterObject
{name,documentation}
levelOctaveMonophonic levelOctaveMonophonic, level
                      Description: Toggle between selection of local octave
                      (transposition) values per set of the Texture Path, or per
                      event. Arguments: (1) name, (2) level {'set', 'event'}
levelOctavePolyphonic levelOctavePolyphonic, level
                      Description: Toggle between selection of local octave
                      (transposition) values per set of the Texture Path, per
                      event, or per polyphonic voice event. Arguments: (1) name,
                      (2) level {'set', 'event', 'voice'}

pi{q1}ti{b1} :: ticp b1 b2
TextureInstance b2 created.

pi{q1}ti{b2} :: tie 
edit TI b2
which parameter? (i,t,b,r,p,f,o,a,n,x,s,d): s
select a texture static parameter to edit, from s0 to s3: 3
current value for s3: event
new value: set
TI b2: parameter texture static updated.

pi{q1}ti{b2} :: tie n c,.1
TI b2: parameter panning updated.
```

Listening to a new EventList created with these three Textures (with ELn and ELh), it should be clear that all pitch information is synchronized by use of a common Path. In the case of Texture a1, the pitches are taken directly from the Path with register. In the case of Texture b1 (right channel), the Path pitches, without register, are transposed into various registers for each event. In the case of Texture b2 (left channel), the Path pitches, also without register, are transposed into various registers only once per Multiset.
      
