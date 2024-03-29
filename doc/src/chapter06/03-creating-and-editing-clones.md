## Creating and Editing Clones

First, using EventMode midi and instrument 0, a Texture with a descending melodic arc will be created. The Texture's time range is set from 0 to 6. The Texture's rhythm employs the ParameterObject convertSecond and uses a standard Generator ParameterObject to create raw duration values in seconds. Finally, This Texture, using a Path only as a reference pitch, employs the Texture's local field to provide harmonic shape.
      

**Creating a Texture**

```
pi{}ti{} :: emo m
EventMode mode set to: midi.

pi{}ti{} :: tin a1 0
TI a1 created.

pi{auto}ti{a1} :: tie t 0,6
TI a1: parameter time range updated.

pi{auto}ti{a1} :: tie r cs,(wpd,e,16,2,0,.6,.02)
TI a1: parameter rhythm updated.

pi{auto}ti{a1} :: tie f wpd,e,16,2,0,12,-24
TI a1: parameter local field updated.

pi{auto}ti{a1} :: tiv
TI: a1, TM: LineGroove, TC: 0, TT: TwelveEqual
pitchMode: pitchSpace, silenceMode: off, postMapMode: on
midiProgram: piano1
      status: +, duration: 00.0--6.41
(i)nstrument        0 (generalMidi: piano1)
(t)ime range        0.0--6.0
(b)pm               constant, 120
(r)hythm            convertSecond, (wavePowerDown, event, (constant, 16), 2, 0,
                    (constant, 0.6), (constant, 0.02))
(p)ath              auto
                    (C4)
                    6.00(s)
local (f)ield       wavePowerDown, event, (constant, 16), 2, 0, (constant, 12),
                    (constant, -24)
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

After creating a Texture, a Clone can be created with the command TCn, for TextureClone New. The user is prompted to enter the name of the new Clone. By default, the Filter ParameterObject filterAdd is applied to the start time of all events with a duration equal to one Pulse. A Clone can be displayed with the TCv command. After displaying the Clone, the user examines the documentation for ParameterObject filterAdd:
      

**Creating and Viewing a Clone with TCn and TCv**

```
pi{auto}ti{a1} :: tcn
name this TextureClone: w1
TC w1 created.

pi{auto}ti{a1} :: tcv
TC: w1, TI: a1
      status: +, duration: 00.5--6.91
(t)ime              filterAdd, (loop, ((1,1,+)), orderedCyclic) 
s(u)stain           bypass                                      
a(c)cent            bypass                                      
local (f)ield       bypass                                      
local (o)ctave      bypass                                      
(a)mplitude         bypass                                      
pan(n)ing           bypass                                      
au(x)iliary         none                                        
clone (s)tatic                                                  
      s0            timeReferenceSource, textureTime            
      s1            retrogradeMethodToggle, off 
```

The Filter ParameterObject bypass is the default for most Clone attributes. This ParameterObject simply passes values through to the Clone unaltered.
      
Upon creating a new EventList and auditioning the results (with ELn and ELh, see  for more information), the descending melodic line of a1 can be heard echoed by Clone w1. In the following example, another Clone is created called w2. This Clone is then edited to have a time value that, rather than shifted by a constant, is scaled by a value that oscillates between 1 and 2. The Clone's local field filter is also set to transpose the Texture's pitches seven half-steps down. The procedure for editing Clone ParameterObjects is similar to that for editing Textures, except for that only Filter ParameterObjects can be provided.
      

**Editing a Clone with TCe**

```
pi{auto}ti{a1} :: tcn w2
TC w2 created.

pi{auto}ti{a1} :: tpv fma
Filter ParameterObject
{name,documentation}
FilterMultiplyAnchor filterMultiplyAnchor, anchorString, parameterObject
                     Description: All input values are first shifted so that the
                     position specified by anchor is zero; then each value is
                     multiplied by the value produced by the parameterObject.
                     All values are then re-shifted so that zero returns to its
                     former position. Arguments: (1) name, (2) anchorString
                     {'lower', 'upper', 'average', 'median'}, (3)
                     parameterObject {operator value generator}

pi{auto}ti{a1} :: tce t fma, l, (ws, e, 8, 0, 1, 2)
TC w2: parameter time updated.

pi{auto}ti{a1} :: tce f fa,(c,-7)
TC w2: parameter local field updated.

pi{auto}ti{a1} :: tcv
TC: w2, TI: a1
      status: +, duration: 000.0--11.41
(t)ime              filterMultiplyAnchor, lower, (waveSine, event, (constant,
                    8), 0, (constant, 1), (constant, 2))
s(u)stain           bypass
a(c)cent            bypass
local (f)ield       filterAdd, (constant, -7)
local (o)ctave      bypass
(a)mplitude         bypass
pan(n)ing           bypass
au(x)iliary         none
clone (s)tatic
      s0            timeReferenceSource, textureTime
      s1            retrogradeMethodToggle, off

```

As with Textures and other objects in athenaCL, Clones can be listed with the TCls command, and the active Clone can be selected with the TCo command. Further, upon examining the parent Texture with TIls, notice that two Clones are now displayed under the TC heading:
      

**Listing and Selecting Clones with TCls and TCo**

```
pi{auto}ti{a1} :: tcls
TextureClones of TI a1
{name,status,duration}
   w1               + 00.5--6.91      
 + w2               + 000.0--11.41 

pi{auto}ti{a1} :: tco w1
TC w1 of TI a1 now active.

pi{auto}ti{a1} :: tils
TextureInstances available:
{name,status,TM,PI,instrument,time,TC}
 + a1               + LineGroove  auto        0   0.0--6.0   2
```

Clones features special transformations selected by CloneStatic ParameterObjects. In the following example, a new Clone is created named w3. The CloneStatic ParameterObject retrogradeMethodToggle is set to timeInverse, causing the Clone to create a retrograde presentation of the Texture's events. Additionally, the Clone's time attribute is set with a filterMultuplyAnchor ParameterObject and the Clone's field attributes is set with a filterAdd ParameterObject:
      

**Creating and Editing Clones**

```
pi{auto}ti{a1} :: tpv retrograde
Clone Static ParameterObject
{name,documentation}
retrogradeMethodToggle retrogradeMethodToggle, name
                       Description: Selects type of retrograde transformation
                       applied to Texture events. Arguments: (1) name, (2) name
                       {'timeInverse', 'eventInverse', 'off'}

pi{auto}ti{a1} :: tcn w3
TC w3 created.

pi{auto}ti{a1} :: tce 
edit TC a1
which parameter? (t,u,c,f,o,a,n,x,s): s
select a clone static parameter to edit, from s0 to s1: 1
current value for c1: off
new value: timeinverse
TC w3: parameter clone static updated.

pi{auto}ti{a1} :: tce t fma,l,(c,2.5)
TC w3: parameter time updated.

pi{auto}ti{a1} :: tce f fa,(c,7)
TC w3: parameter local field updated.
```

The TEmap command displays all Textures as well as all Texture Clones. Texture Clones appear under their parent Texture. Textures and Clones, further, can be muted independently.
      

**Viewing Textures and Clones with TEmap**

```
pi{auto}ti{a1} :: temap
TextureEnsemble Map:
15.22s              |      .       |      .       |      .      |       .      |
a1                  _________________________                                   
      w3            ............................................................
      w2               .............................................
      w1                 .........................
```

