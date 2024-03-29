## Editing Rhythm ParameterObjects

Rhythm ParameterObjects are ParameterObjects specialized for generating time and rhythm information. Many Rhythm ParameterObjects use Pulse object notations to define proportional rhythms and reference a Texture's dynamic bpm attribute. Other ParameterObjects are independent of bpm and can use raw timing information provided by one or more Generator ParameterObjects.
      
When using proportional rhythms, athenaCL uses Pulse objects. Pulses represent a ratio of duration in relation to the duration of beat (specified in BPM and obtained from the Texture). For details on Pulse notation, enter "help pulse":
      

**View Pulse and Rhythm help**

```
pi{auto-muteHiConga}ti{b1} :: help pulse
{topic,documentation}
Pulse and Rhythm    Pulses represent a duration value derived from ratio and a
                    beat-duration. Beat duration is always obtained from a
                    Texture. Pulses are noted as a list of three values: a
                    divisor, a multiplier, and an accent. The divisor and
                    multiplier must be positive integers greater than zero.
                    Accent values must be between 0 and 1, where 0 is a measured
                    silence and 1 is a fully sounding event. Accent values my
                    alternatively be notated as + (for 1) and o (for 0). If a
                    beat of a given duration is equal to a quarter note, a Pulse
                    of (1,1,1) is a quarter note, equal in duration to a beat. A
                    Pulse of (2,1,0) is an eighth-note rest: the beat is divided
                    by two and then multiplied by one; the final zero designates
                    a rest. A Pulse of (4,3,1) is a dotted eight note: the beat
                    is divided by four (a sixteenth note) and then multiplied by
                    three; the final one designates a sounding event. A Rhythm
                    is designated as list of Pulses. For example: ((4,2,1),
                    (4,2,1), (4,3,1)).
```

To edit the rhythms used by Texture b1, enter TIe followed by an "r" to access the rhythm attribute. As before, the user is presented with the current value, then prompted for a new value. In the following example, the ParameterObject "loop" is examined first with the TPv, then the active Texture is edited by providing an random walk over an expanded rhythm. Finally, the rhythm attribute of all Textures is viewed with TEv.
      

**Editing Rhythm ParameterObjects with TIe**

```
pi{auto-muteHiConga}ti{b1} :: tpv loop
Rhythm Generator ParameterObject
{name,documentation}
Loop                loop, pulseList, selectionString
                    Description: Deploys a fixed list of rhythms. Pulses are
                    chosen from this list using the selector specified by the
                    selectionString argument. Arguments: (1) name, (2) pulseList
                    {a list of Pulse notations}, (3) selectionString
                    {'randomChoice', 'randomWalk', 'randomPermutate',
                    'orderedCyclic', 'orderedCyclicRetrograde',
                    'orderedOscillate'}

pi{auto-muteHiConga}ti{b1} :: tie
command.py: raw args  
edit TI b1
which parameter? (i,t,b,r,p,f,o,a,n,x,s,d): r
current rhythm: pulseTriple, (constant, 4), (basketGen, randomPermutate,
(1,1,2,3)), (constant, 1), (constant, 0.75)
new value: l, ((4,1,1),(4,1,1),(4,2,1),(4,3,1),(4,5,1),(4,3,1)), rw
TI b1: parameter rhythm updated.

pi{auto-muteHiConga}ti{b1} :: tev r
compare parameters: rhythm
{name,value,}
a1                  pulseTriple, (constant, 4), (basketGen, randomPermutate,
                    (1,1,2,3)), (constant, 1), (constant, 0.75)
b1                  loop, ((4,1,+),(4,1,+),(4,2,+),(4,3,+),(4,5,+),(4,3,+)),
                    randomWalk
```

Notice that, as with all ParameterObjects, abbreviations can be used for argument strings. The user need only enter the string "l" to select the "loop" RhythmObject, and "rw" to select the randomWalk selection method.
      
To edit Texture a1, the user must first make a1 the active texture with TIo. In the following example, the user applies a zero-order Markov chain to generate pulses. The user fist consults the documentation for ParameterObject markovPulse. For more information about Markov transition strings (Ariza 2006 [AN#1343]), enter "help markov". After selecting and editing the Texture, the Rhythms are compared with TEv:
      

**Editing Rhythm ParameterObjects with TIe**

```
pi{auto-muteHiConga}ti{b1} :: tpv markovp
Rhythm Generator ParameterObject
{name,documentation}
markovPulse         markovPulse, transitionString, parameterObject
                    Description: Produces Pulse sequences by means of a Markov
                    transition string specification and a dynamic transition
                    order generator. The Markov transition string must define
                    symbols that specify valid Pulses. Markov transition order
                    is specified by a ParameterObject that produces values
                    between 0 and the maximum order available in the Markov
                    transition string. If generated-orders are greater than
                    those available, the largest available transition order will
                    be used. Floating-point order values are treated as
                    probabilistic weightings: for example, a transition of 1.5
                    offers equal probability of first or second order selection.
                    Arguments: (1) name, (2) transitionString, (3)
                    parameterObject {order value}

pi{auto-muteHiConga}ti{b1} :: tio a1
TI a1 now active.

pi{auto-muteHiConga}ti{a1} :: tie
edit TI a1
which parameter? (i,t,b,r,p,f,o,a,n,x,s,d): r
current rhythm: pulseTriple, (constant, 4), (basketGen, randomPermutate,
(1,1,2,3)), (constant, 1), (constant, 0.75)
new value: mp, a{8,1,1}b{4,3,1}c{4,2,1}d{4,5,1}:{a=1|b=3|c=4|d=7}, (c,0)
TI a1: parameter rhythm updated.

pi{auto-muteHiConga}ti{a1} :: tev r
compare parameters: rhythm
{name,value,}
a1                  markovPulse,
                    a{8,1,1}b{4,3,1}c{4,2,1}d{4,5,1}:{a=1|b=3|c=4|d=7},
                    (constant, 0)
b1                  loop, ((4,1,+),(4,1,+),(4,2,+),(4,3,+),(4,5,+),(4,3,+)),
                    randomWalk
                    
```

In the previous example, the user supplies four Pulses; each pulses is weighted such that the shortest, (8,1,1), is the least frequent (weight of 1), and the longest, (4,5,1), is the most frequent (weight of 7).
      
Using ELn, the current collection of Textures can be used to create an EventList, and ELh may be used to audition the results. (For more information on using ELn, see .) Each time an EventList is created, different sequences of rhythms will be generated: for Texture a1, these rhythms will be the result of a zero-order Markov chain; for Texture b1, these rhythms will be the result of a random walk on an ordered list of Pulses.
      
A final alternation can be made to the metric performance of these Textures. Using the TEe command, both Texture's bpm attribute can be altered to cause a gradual accelerando from 120 BPM to 300 BPM. In the following example, the user applies a wavePowerUp ParameterObject to the bpm attribute of both Textures by using the TEe command with complete command-line arguments:
      

**Editing BPM with TEe**

```
pi{auto-muteHiConga}ti{a1} :: tee b wpu,t,20,0,2,120,300
TI a1: parameter bpm updated.
TI b1: parameter bpm updated.
```

