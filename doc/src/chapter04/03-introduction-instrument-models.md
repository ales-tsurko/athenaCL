## Introduction Instrument Models

athenaCL features numerous integrated instrument models. In some cases these instrument models are references to external specifications; in other cases these instrument models contain complete source code necessary for instantiating synthesis systems. Textures are assigned an instrument from an Orchestra upon creation, and are able to control a wide variety of instrument-specific parameters.
      
athenaCL features an integrated library of Csound instruments, providing automated control of both Csound score and orchestra generation and control. For details on installing and using Csound within athenaCL, see . Csound instruments are signal processing and synthesis instructions. These instructions designates a certain number of parameters to expose to the user of the instrument. These parameters allow events in the score to communicate information and settings to the instrument. athenaCL's integrated library of Csound instruments permits dynamically constructed orchestra files to be used with athenaCL-generated Csound scores. Alternatively, users can use external, custom orchestras with athenaCL-written score files. EventModes csoundNative, csoundExternal, and csoundSilence support diverse ways of working with Csound within athenaCL.
      
athenaCL provides instrument collections (Orchestras) for working with other EventOutput formats. For working with MIDI systems, General MIDI (GM) instrument definitions are provided with the generalMidi and generalMidiPercussion EventModes. 
      
Whenever a Texture is created, an instrument must be specified by number. This is necessary because the Texture must be configured with additional ParameterObjects for instrument-specific parameter control. Instruments are always identified by a number, though within athenaCL descriptive names are provided when available.
      
The instruments available during Texture creation are dependent on the active EventMode: that is, for any active EventMode, one Orchestra is available from which a Texture's instrument must be selected. In the following example, the user lists available EventModes to check that csoundNative is active, and then views the available instruments with the EMi command.

**Listing available Instruments with EMi**

```
pi{}ti{} :: emls
EventMode modes available:
{name}
   csoundExternal      
 + csoundNative        
   csoundSilence       
   midi                
   midiPercussion      
   superColliderNative 

pi{}ti{} :: emi
csoundNative instruments:
{number,name}
   3      sineDrone                        
   4      sineUnitEnvelope                 
   5      sawDrone                         
   6      sawUnitEnvelope                  
   11     noiseWhite                       
   12     noisePitched                     
   13     noiseUnitEnvelope                
   14     noiseTambourine                  
   15     noiseUnitEnvelopeBandpass        
   16     noiseSahNoiseUnitEnvelope        
   17     noiseSahNoiseUnitEnvelopeDistort 
   20     fmBasic                          
   21     fmClarinet                       
   22     fmWoodDrum                       
   23     fmString                         
   30     samplerReverb                    
   31     samplerRaw                       
   32     samplerUnitEnvelope              
   33     samplerUnitEnvelopeBandpass      
   34     samplerUnitEnvelopeDistort       
   35     samplerUnitEnvelopeParametric    
   36     samplerSahNoiseUnitEnvelope      
   40     vocodeNoiseSingle                
   41     vocodeNoiseSingleGlissando       
   42     vocodeNoiseQuadRemap             
   43     vocodeNoiseQuadScale             
   44     vocodeNoiseQuadScaleRemap        
   45     vocodeNoiseOctScale              
   46     vocodeNoiseOctScaleRemap         
   47     vocodeNoiseBiOctScale            
   48     vocodeNoiseTriOctScale           
   50     guitarNylonNormal                
   51     guitarNylonLegato                
   52     guitarNylonHarmonic              
   60     additiveBellBright               
   61     additiveBellDark                 
   62     additiveBellClear                
   70     synthRezzy                       
   71     synthWaveformVibrato             
   72     synthVcoAudioEnvelopeSineQuad    
   73     synthVcoAudioEnvelopeSquareQuad  
   74     synthVcoDistort                  
   80     pluckTamHats                     
   81     pluckFormant                     
   82     pluckUnitEnvelope                
   110    noiseAudioEnvelopeSineQuad       
   111    noiseAudioEnvelopeSquareQuad     
   130    samplerAudioEnvelopeSineQuad     
   131    samplerAudioEnvelopeSquareQuad   
   132    samplerAudioFileEnvelopeFilter   
   133    samplerAudioFileEnvelopeFollow   
   140    vocodeSineOctScale               
   141    vocodeSineOctScaleRemap          
   142    vocodeSineBiOctScale             
   143    vocodeSineTriOctScale            
   144    vocodeSineQuadOctScale           
   145    vocodeSinePentOctScale           
   146    vocodeSineHexOctScale            
   230    samplerVarispeed                 
   231    samplerVarispeedAudioSine        
   232    samplerVarispeedReverb           
   233    samplerVarispeedDistort          
   234    samplerVarispeedSahNoiseDistort  
   240    vocodeVcoOctScale                
   241    vocodeVcoOctScaleRemap    
```

Other EventModes provide other Orchestras for use in Textures. In the example below, the user selects the EventMode midiPercussion with the EMo command and examines the available instruments with the EMi command:
      

**Examining additional Instruments with EMi**

```
pi{}ti{} :: emo mp
EventMode mode set to: midiPercussion.

pi{}ti{} :: emi
generalMidiPercussion instruments:
{number,name}
   35     acousticBassDrum 
   36     bassDrum1        
   37     sideStick        
   38     acousticSnare    
   39     handClap         
   40     electricSnare    
   41     lowFloorTom      
   42     closedHiHat      
   43     highFloorTom     
   44     pedalHiHat       
   45     lowTom           
   46     openHiHat        
   47     lowMidTom        
   48     hiMidTom         
   49     crashCymbal1     
   50     highTom          
   51     rideCymbal1      
   52     chineseCymbal    
   53     rideBell         
   54     tambourine       
   55     splashCymbal     
   56     cowBell          
   57     crashCymbal2     
   58     vibraSlap        
   59     rideCymbal2      
   60     hiBongo          
   61     lowBongo         
   62     muteHiConga      
   63     openHiConga      
   64     lowConga         
   65     highTimbale      
   66     lowTimbale       
   67     highAgogo        
   68     lowAgogo         
   69     cabasa           
   70     maracas          
   71     shortWhistle     
   72     longWhistle      
   73     shortGuiro       
   74     longGuiro        
   75     claves           
   76     hiWoodBlock      
   77     lowWoodBlock     
   78     muteCuica        
   79     openCuica        
   80     muteTriangle     
   81     openTriangle    
```

