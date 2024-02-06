## Editing ParameterObjects

To edit an attribute of Texture, a user enters a new ParameterObject argument list. The command TIe, as before, first prompts the user to select which attribute to edit. Next, the current value of the attribute is displayed, followed by a prompt for the new value. TIv can be used to confirm the changed value. In the following example, the panning of Texture "a1" is assigned a fractional noise (1/f) ParameterObject:
      

**Editing the panning of a TextureInstance**

```
pi{auto-muteHiConga}ti{b1} :: tie
edit TI b1
which parameter? (i,t,b,r,p,f,o,a,n,x,s,d): n
current panning: constant, 0.5
new value: n, 50, (cg, ud, 1, 3, .2), .5, 1
TI b1: parameter panning updated.

pi{auto-muteHiConga}ti{b1} :: tiv
TI: b1, TM: LineGroove, TC: 0, TT: TwelveEqual
pitchMode: pitchSpace, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: o, duration: 005.0--19.97
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
(a)mplitude         randomUniform, (constant, 0.6), (constant, 1)
pan(n)ing           noise, 50, (cyclicGen, upDown, 1, 3, 0.2), (constant, 0.5),
                    (constant, 1)
au(x)iliary         none
texture (s)tatic
      s0            parallelMotionList, (), 0.0
      s1            pitchSelectorControl, randomPermutate
      s2            levelFieldMonophonic, event
      s3            levelOctaveMonophonic, event
texture (d)ynamic   none
```

The noise ParameterObject has been given an embedded ParameterObject to control the gamma argument. Notice that instead of entering "noise", "cyclicGen" or "upDown" the user can enter the acronyms "n", "cg", and "ud". All ParameterObjects support automatic acronym expansion of argument strings. This is an important and time-saving shortcut.
      
The previous example edited the panning of Texture "a1" such that it produces values within the range of .5 to 1. This limits the spatial location of the sound to the upper half of the range (the middle to right stereo position). To limit the spatial location of "b1" in a complementary fashion, the Texture is edited to produce values within the range 0 to .5, corresponding to the lower half of the range (the middle to left stereo position). In the example below, TIo is used to select "b1" before entering the TIe command. TEv is then used to compare panning values for all Textures.
      

**Editing the panning of a TextureInstance**

```
pi{auto-muteHiConga}ti{b1} :: tio b1
TI b1 now active.

pi{auto-muteHiConga}ti{b1} :: tie n wpd,e,15,.25,2.5,0,.5
TI b1: parameter panning updated.

pi{auto-muteHiConga}ti{b1} :: tiv
TI: b1, TM: LineGroove, TC: 0, TT: TwelveEqual
pitchMode: pitchSpace, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: o, duration: 005.0--20.06
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
(a)mplitude         randomUniform, (constant, 0.6), (constant, 1)
pan(n)ing           wavePowerDown, event, (constant, 15), 0.25, 2.5, (constant,
                    0), (constant, 0.5)
au(x)iliary         none
texture (s)tatic
      s0            parallelMotionList, (), 0.0
      s1            pitchSelectorControl, randomPermutate
      s2            levelFieldMonophonic, event
      s3            levelOctaveMonophonic, event
texture (d)ynamic   none

pi{auto-muteHiConga}ti{b1} :: tev n
compare parameters: panning
{name,value,}
a1                  constant, 0.5
b1                  wavePowerDown, event, (constant, 15), 0.25, 2.5, (constant,
                    0), (constant, 0.5)
```

Notice that, in the above example, the user provided complete command-line arguments for the TIe command. When entering a ParameterObject from the command-line, no spaces, and only commas, can be used between ParameterObject arguments. As command-line arguments are space delimited (and ParameterObject arguments are comma delimited), a ParameterObject on the command line must be given without spaces between arguments. When providing a ParameterObject to a TIe prompt, however, spaces may be provided.
      
