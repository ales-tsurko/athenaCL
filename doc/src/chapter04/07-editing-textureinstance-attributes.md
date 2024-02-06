## Editing TextureInstance Attributes

Each attribute of a Texture can be edited to specialize its performance. Some attributes such as instrument, time-range, and Path are static: they do not change over the duration of a Texture. Other attributes are dynamic, such as bpm, rhythm, local field, local octave, amplitude and panning, and can be configured with a wide range of ParameterObjects.
      
Texture attributes are edited with the TIe command. The command first prompts the user to select which attribute to edit. Attributes are named by a single-letter abbreviation, as notated in the TIv display with parenthesis. Next, the current value of the attribute is displayed, followed by a prompt for the new value. In the following example the time range of Texture "a1" is edited:
      

**Editing a TextureInstance**

```
pi{auto-muteHiConga}ti{b1} :: tie
edit TI b1
which parameter? (i,t,b,r,p,f,o,a,n,x,s,d): t
current time range: 0.0, 20.0
new value: 5, 20
TI b1: parameter time range updated.

pi{auto-muteHiConga}ti{b1} :: tiv
TI: b1, TM: LineGroove, TC: 0, TT: TwelveEqual
pitchMode: pitchSpace, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: +, duration: 005.0--19.97
(i)nstrument        62 (generalMidiPercussion: muteHiConga)
(t)ime range        05.0--20.0
(b)pm               constant, 120
(r)hythm            pulseTriple, (constant, 4), (basketGen, randomPermutate,
                    (1,1,2,3)), (constant, 1), (constant, 0.75)
(p)ath              auto-muteHiConga
                    (D4)
                    15.00(s)
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

In the example above the user select "t" to edit the active Texture's time-range attribute. In general, new values for attributes must be entered with the same syntax with which they are displayed. In this example, time-range values are given as two numbers separated by a comma. Deviation from this syntax will return an error. The user enters 5, 20 to set the time-range attribute to the duration from 5 to 20 seconds.
      
The command TEe, for TextureEnsemble Edit can be used to edit the entire collection of Textures with one command. In the following example the user selects the amplitude attribute with "a" and then enters a new ParameterObject: randomUniform. The randomUniform parameterObject produces random values with a uniform distribution between the required arguments for minimum and maximum. After this edit, TEv, with the command-line argument "a", can be used to view the amplitude for all Textures and confirm the edit.
      

**Editing a single parameter of all Textures with TEe**

```

pi{auto-muteHiConga}ti{b1} :: tee
edit all TextureInstances
which parameter? (i,t,b,r,p,f,o,a,n,x): a
sample amplitude: randomBeta, 0.4, 0.4, (constant, 0.7), (constant, 0.9)
new value: ru, .6, 1
TI a1: parameter amplitude updated.
TI b1: parameter amplitude updated.

pi{auto-muteHiConga}ti{b1} :: tev a
compare parameters: amplitude
{name,value,}
a1                  randomUniform, (constant, 0.6), (constant, 1)  
b1                  randomUniform, (constant, 0.6), (constant, 1)
```

Using ELn, the current collection of Textures can be used to create an EventList, and ELh may be used to audition the results. (For more information on using ELn, see .) The random fluctuation of amplitude values should provide a variety of accent patterns to the fixed rhythmic loop.
      
The collection of Textures can be displayed in a graphical and textual diagram produced by the TEmap command. This command lists each Texture and Clone within the current AthenaObject and provides a proportional representation of their respective start and end times.
      

**Generating a graphical display of Texture position with TEmap**

```
pi{auto-muteHiConga}ti{b1} :: temap
TextureEnsemble Map:
19.97s              |      .       |      .       |      .      |       .      |
a1                  ____________________________________________________________
b1                                 _____________________________________________
```

