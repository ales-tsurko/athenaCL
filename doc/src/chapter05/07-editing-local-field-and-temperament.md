## Editing Local Field and Temperament

Within athenaCL, any pitch can be tuned to microtonal specifications, allowing the user to apply non-equal tempered frequencies to each pitch in either a fixed relationship or a dynamic, algorithmically generated manner. Within athenaCL Textures there are two ways to provide microtonal tunings. First, pitches can be transposed and tuned with any ParameterObject by using the Texture local field attribute. Each integer represents a half-step transposition, and floating point values can provide any detail of microtonal specification. Second, each Texture can have a different Temperament, or tuning system based on either pitch class, pitch space, or algorithmic specification. The command TTls allows the user to list the available TextureTemperaments.
      

**Listing all TextureTemperaments**

```
pi{q1}ti{b2} :: ttls
TextureTemperaments available for TI b2:
{name,tunning}
 + TwelveEqual       
   Pythagorean       
   Just              
   MeanTone          
   Split24Upper      
   Split24Lower      
   Interleave24Even  
   Interleave24Odd   
   NoiseLight        
   NoiseMedium       
   NoiseHeavy        
```

The temperament "TwelveEqual" is the active Temperament for current Texture b2. This temperament produces equal-tempered frequencies. To select a different temperament for the active Texture, enter the command TTo. In the example below the user selects the temperament NoiseLight for Textures b2 and Texture b1, and then selects the temperament NoiseMedium for Texture a1. In the last case, two command are given on the some command line. As is the UNIX convention, the commands and arguments are separated by a semicolon:

**Selecting Texture Temperament with TTo**

```
pi{q1}ti{b2} :: tto
select a TextureTemperament for TI b2: (name or number 1-11): nl
TT NoiseLight now active for TI b2.

pi{q1}ti{b2} :: tio b1
TI b1 now active.

pi{q1}ti{b1} :: tto nl
TT NoiseLight now active for TI b1.

pi{q1}ti{b1} :: tio a1; tto nm
TI a1 now active.

TT NoiseMedium now active for TI a1.
```

Not all EventOutputs can perform microtones. MIDI files, for example, cannot store microtonal specifications of pitch. Though such pitches will be generated within athenaCL, they will be rounded when written to the MIDI file. EventOutputs for Csound, however, can handle microtones.
      
