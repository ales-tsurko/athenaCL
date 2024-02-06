## Creating, Selecting, and Viewing TextureInstances

A TextureInstance is always linked to a Path. If no Paths exists when the Texture is created, a default Path is automatically created consisting of a single Multiset with a single pitch (middle C, or C4). If Paths exists when the Texture is created, the active PathInstance is assigned to the Texture. A TextureInstance's Path can be later edited. For a complete introduction to Paths see .
      
A new TextureInstance is always created from the active TextureModule; the user must then always select the desired TextureModule before creating a Texture of the desired type. A TextureInstance's type, or TextureModule, cannot be changed after the Texture is created.
      
A new Texture is created with the TIn command, for TextureInstance New. The user is prompted to name the new Texture and select an instrument by number. If the number of the desired instrument is not known, a "?" can be entered to display a list of instruments. In the example below the user selects TextureMode LineGroove, EventMode midiPercussion, and then creates a texture named "a1" with instrument 64 ("lowConga").
      

**Creating a new TextureInstance with TIn**

```
pi{}ti{} :: tmo linegroove
TextureModule LineGroove now active.

pi{}ti{} :: emo mp
EventMode mode set to: midiPercussion.

pi{}ti{} :: tin
name this texture: a1
enter instrument number:
(35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,6
1,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81)
or "?" for instrument help: 64
TI a1 created.
```

To hear the resulting musical structure, enter the command ELn. (For more information on using ELn, see . The resulting MIDI file may be opened with the ELh command.
      

**Creating a new EventList with ELn**

```
pi{auto-lowConga}ti{a1} :: eln
command.py: temporary file: /Volumes/xdisc/_scratch/ath2010.07.02.17.51.42.xml 
      EventList ath2010.07.02.17.51.42 complete:
/Volumes/xdisc/_scratch/ath2010.07.02.17.51.42.mid
/Volumes/xdisc/_scratch/ath2010.07.02.17.51.42.xml
```

After creating a Texture, the TIv command can be used to view the active Texture:
      

**Viewing a TextureInstance**

```
pi{auto-lowConga}ti{a1} :: tiv
TI: a1, TM: LineGroove, TC: 0, TT: TwelveEqual
pitchMode: pitchSpace, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: +, duration: 000.0--20.06
(i)nstrument        64 (generalMidiPercussion: lowConga)
(t)ime range        00.0--20.0
(b)pm               constant, 120
(r)hythm            pulseTriple, (constant, 4), (basketGen, randomPermutate,
                    (1,1,2,3)), (constant, 1), (constant, 0.75)
(p)ath              auto-lowConga
                    (E4)
                    20.00(s)
local (f)ield       constant, 0
local (o)ctave      constant, 0
(a)mplitude         randomBeta, 0.4, 0.4, (constant, 0.7), (constant, 0.9)
pan(n)ing           constant, 0.5
au(x)iliary         none
texture (s)tatic
      s0            parallelMotionList, (), 0.0
      s1            pitchSelectorControl, randomPermutate
      s2            levelFieldMonophonic, event
      s3            levelOctaveMonophonic, event
texture (d)ynamic   none
```

The TIv command displays all essential attributes of a Texture. Each label in the display corresponds to an attribute in the TextureInstance. The TIv display is in two-blocks. The first block gives parameters that are constant. The first line displays the name of the TextureInstance (a1), the name of the parent TextureModule (LineGroove), the number of TextureClones (0), and the active TextureTemperament (TwelveEqual). The second line displays the PitchMode (pitchSpace), the silenceMode (off), and the postMapMode (on). The third line provides the GM MIDI program name (piano1). The fourth, indented line displays the TextureInstance's mute status (where a "o" is muted and a "+" is non-muted) and the absolute duration the Texture's events.
      
The second block lists the primary algorithmic controls of the Texture. The names of these attributes use parenthesis to designate a single-letter abbreviation. The instrument attribute is displayed first, with the value following the label: instrument number (64), the name of the orchestra (generalMidiPercussion) and the name of the instrument (lowConga). The next attribute is time-range, the start and end time in seconds from the beginning of the EventList. A new Texture is given a default time-range of twenty seconds (00.0--20.0). New Textures, when created, get their time-range from the active Texture.
      
The bpm attribute is the tempo in beats per minute. The value is set with the ParameterObject "constant" to produce a tempo of 120 BPM. In most cases, the bpm control is used to calculate the duration of rhythms and pulses used in a Texture.
      
The rhythm attribute designates a Rhythm ParameterObject to control the generation of event durations. Rhythm ParameterObjects often notate rhythms as lists of Pulses. A Pulse is designated as a list of three elements: (divisor, multiplier, accent). The duration of a rhythm is calculated by dividing the time of a beat (from the bpm parameter) by the Pulse divisor, then multiplying the result by the Pulse multiplier. The value of the "accent" determines if a duration is a note or a rest, where 1 or a "+" designates a note, 0 or a "o" designates a rest. Thus an eighth note is given as (2,1,1), a dotted-quarter note as (2,3,1), and dotted-eighth rest as (4,3,0). In the example above, the ParameterObject "loop" is used with three Pulses: two sixteenth notes (4,1,1) and a duration equal to a quarter-note tied to a sixteenth note (4,5,1).
      
The Path attribute gives the name of the PathInstance used by this Texture, followed on the next line by the Multiset pitches that will be used. PathInstances are linked to the Texture. Thus, if a change is made to a Path (with PIe, for example), all Textures that use that Path will reflect the change. Each TextureInstance, however, can control the interpretation of a Path in numerous ways. The Texture PitchMode setting, for example, determines if pitches are derived from a Path in pitchSpace, pitchClassSpace, or as a setClass. The local field and local octave attributes permit each Texture to transpose pitches from the Path independently.
      
The attribute "local field" stores a ParameterObject that controls local transposition of Path pitches. Values are given in semitones, and can include microtonal transpositions as floating-point values following the semitone integer. Thus, a transposition of five half-steps and a quarter-tone would be equal to 5.5. A transposition of a major tenth would be 16. In the example above the attribute value instructs the Texture to use a ParameterObject called "constant." Note: some EventOutput formats do not support microtonal pitch specification. In such cases microtones are rounded to the nearest semitone. The attribute "local octave," similar to local field, controls the octave position of Path pitches. Each integer represents an octave shift, where 0 is no octave shift, each Path pitch retaining its original octave register.
      
The amplitude attribute designates a ParameterObject to control the amplitude of the Texture, measured in a symbolic range from 0 to 1. The panning  attribute designates the ParameterObject used to control spatial location in stereo or quadraphonic space. Values are along the unit interval, from 0 to 1.
      
The attributes that make up the "auxiliary" listing provide any number of additional ParameterObjects to control instrument specific parameter fields. The number of parameter fields is determined by the instrument definition.
      
The last attributes, "texture static" and "texture dynamic," designate controls specific to particular TextureModules. The values here can be edited like other attributes.
      
A second Texture will be created with TIn named "b1" and using instrument 62. The Texture, after creation, is displayed with the TIv command.
      

**Creating and viewing a TextureInstance**

```
pi{auto-lowConga}ti{a1} :: tin
name this texture: b1
enter instrument number:
(35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,6
1,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81)
or "?" for instrument help: 62
TI b1 created.

pi{auto-muteHiConga}ti{b1} :: tiv
TI: b1, TM: LineGroove, TC: 0, TT: TwelveEqual
pitchMode: pitchSpace, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: +, duration: 000.0--20.06
(i)nstrument        62 (generalMidiPercussion: muteHiConga)
(t)ime range        00.0--20.0
(b)pm               constant, 120
(r)hythm            pulseTriple, (constant, 4), (basketGen, randomPermutate,
                    (1,1,2,3)), (constant, 1), (constant, 0.75)
(p)ath              auto-muteHiConga
                    (D4)
                    20.00(s)
local (f)ield       constant, 0
local (o)ctave      constant, 0
(a)mplitude         randomBeta, 0.4, 0.4, (constant, 0.7), (constant, 0.9)
pan(n)ing           constant, 0.5
au(x)iliary         none
texture (s)tatic
      s0            parallelMotionList, (), 0.0
      s1            pitchSelectorControl, randomPermutate
      s2            levelFieldMonophonic, event
      s3            levelOctaveMonophonic, event
texture (d)ynamic   none
```

This new Texture, though created with the same TextureModule, is a completely autonomous object. No changes to "a1" will have any effect on "b1".
      
During an athenaCL session a user can create any number of TextureInstances and save this collection in an AthenaObject file for latter use. For more information on saving, loading, and merging AthenaObjects see . To view a list of all current Textures, enter the command TIls, for TextureInstance List.
      

**Listing all TextureInstances**

```
pi{auto-muteHiConga}ti{b1} :: tils
TextureInstances available:
{name,status,TM,PI,instrument,time,TC}
   a1               + LineGroove  auto-lowConga    64  00.0--20.0   0
 + b1               + LineGroove  auto-muteHiConga 62  00.0--20.0   0
```

This display shows a list of all Textures, each Texture on a single line. The information given, in order from left to right, is the name, the mute-status, the parent TM, the PathInstance, the instrument number, the time-range, and the number of TextureClones. Notice the "+" in front of Texture "b1": this designates that this Texture is active. To change the active Texture, enter the command TIo either with a command-line argument or alone:
      

**Selecting the active TextureInstance**

```
pi{auto-muteHiConga}ti{b1} :: tio a1
TI a1 now active.

pi{auto-muteHiConga}ti{a1} :: 
```

In order to compare a single attribute of all Textures, the user can enter the command TEv, for TextureEnsemble View. TextureEnsemble refers to the collection of all Textures, and all TE commands process all Textures simultaneously. The user will be prompted to enter an abbreviation for the desired attribute. Attribute abbreviations are notated in the TIv display labels. Thus the attribute abbreviation for "(a)mplitude" is "a"; the attribute abbreviation for "pan(n)ing" is "n." As with other commands, use of command-line arguments provides flexible control:
      

**Viewing parameter values for all Textures**

```
pi{auto-muteHiConga}ti{a1} :: tev
compare texture parameters: which parameter? a
compare parameters: amplitude
{name,value,}
a1                  randomBeta, 0.4, 0.4, (constant, 0.7), (constant, 0.9)  
b1                  randomBeta, 0.4, 0.4, (constant, 0.7), (constant, 0.9) 

pi{auto-muteHiConga}ti{a1} :: tev i
compare parameters: instrument
{name,value,}
a1                  64 (generalMidiPercussion: lowConga)     
b1                  62 (generalMidiPercussion: muteHiConga)  
```

