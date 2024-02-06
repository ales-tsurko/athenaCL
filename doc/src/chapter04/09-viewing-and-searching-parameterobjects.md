## Viewing and Searching ParameterObjects

For each dynamic attribute of a TextureInstance, a ParameterObject can be assigned to produce values over the duration of the Texture. Complete documentation for all ParameterObjects can be found in . Texture attributes for bpm, local field, local octave, amplitude, panning, and all auxiliary parameters (if required by the instrument) can have independent ParameterObjects.
      
ParameterObjects are applied to a Texture attribute with an argument list. athenaCL accepts lists in the same comma-separated format of Python list data structures. A list can consist of elements like strings, numbers, and other lists, each separated by a comma. Within athenaCL, text strings need not be in quotes, and sub-lists can be given with either parenthesis or brackets. Each entry in the ParameterObject argument list corresponds, by ordered-position, to an internal setting within the ParameterObject. The first entry in the argument list is always the name of the ParameterObject. ParameterObject names, as well as all ParameterObject configuration strings, can always be accessed with acronyms.
      
To display a list if all available ParameterObjects, enter the command TPls, for TextureParameter list:
      

**Displaying all ParameterObjects with TPls**

```
pi{auto-muteHiConga}ti{b1} :: tpls
Generator ParameterObject
{name}
   accumulator                
   basketFill                 
   basketFillSelect           
   basketGen                  
   basketSelect               
   breakGraphFlat             
   breakGraphHalfCosine       
   breakGraphLinear           
   breakGraphPower            
   breakPointFlat             
   breakPointHalfCosine       
   breakPointLinear           
   breakPointPower            
   caList                     
   caValue                    
   constant                   
   constantFile               
   cyclicGen                  
   directorySelect            
   envelopeGeneratorAdsr      
   envelopeGeneratorTrapezoid 
   envelopeGeneratorUnit      
   feedbackModelLibrary       
   fibonacciSeries            
   funnelBinary               
   grammarTerminus            
   henonBasket                
   iterateCross               
   iterateGroup               
   iterateHold                
   iterateSelect              
   iterateWindow              
   lineSegment                
   listPrime                  
   logisticMap                
   lorenzBasket               
   markovGeneratorAnalysis    
   markovValue                
   mask                       
   maskReject                 
   maskScale                  
   noise                      
   oneOver                    
   operatorAdd                
   operatorCongruence         
   operatorDivide             
   operatorMultiply           
   operatorPower              
   operatorSubtract           
   pathRead                   
   quantize                   
   randomBeta                 
   randomBilateralExponential 
   randomCauchy               
   randomExponential          
   randomGauss                
   randomInverseExponential   
   randomInverseLinear        
   randomInverseTriangular    
   randomLinear               
   randomTriangular           
   randomUniform              
   randomWeibull              
   sampleAndHold              
   sampleSelect               
   sieveFunnel                
   sieveList                  
   staticInst                 
   staticRange                
   typeFormat                 
   valuePrime                 
   valueSieve                 
   waveCosine                 
   waveHalfPeriodCosine       
   waveHalfPeriodPulse        
   waveHalfPeriodSine         
   waveHalfPeriodTriangle     
   wavePowerDown              
   wavePowerUp                
   wavePulse                  
   waveSawDown                
   waveSawUp                  
   waveSine                   
   waveTriangle               

Rhythm Generator ParameterObject
{name}
   binaryAccent         
   convertSecond        
   convertSecondTriple  
   gaRhythm             
   iterateRhythmGroup   
   iterateRhythmHold    
   iterateRhythmWindow  
   loop                 
   markovPulse          
   markovRhythmAnalysis 
   pulseSieve           
   pulseTriple          
   rhythmSieve          

Filter ParameterObject
{name}
   bypass               
   filterAdd            
   filterDivide         
   filterDivideAnchor   
   filterFunnelBinary   
   filterMultiply       
   filterMultiplyAnchor 
   filterPower          
   filterQuantize       
   maskFilter           
   maskScaleFilter      
   orderBackward        
   orderRotate          
   pipeLine             
   replace              
```

To display detailed documentation for a ParameterObject, enter the command TPv, for Texture Parameter view. In the following example the user views the ParameterObjects "wavePowerDown" and "noise" by providing command-line arguments for the desired ParameterObject name:
      

**Viewing ParameterObject reference information**

```
pi{auto-muteHiConga}ti{b1} :: tpv wpd
Generator ParameterObject
{name,documentation}
WavePowerDown       wavePowerDown, stepString, parameterObject, phase, exponent,
                    min, max
                    Description: Provides a power down wave between 0 and 1 at a
                    rate given in either time or events per period. Depending on
                    the stepString argument, the period rate (frequency) may be
                    specified in spc (seconds per cycle) or eps (events per
                    cycle). This value is scaled within the range designated by
                    min and max; min and max may be specified with
                    ParameterObjects. The phase argument is specified as a value
                    between 0 and 1. Note: conventional cycles per second (cps
                    or Hz) are not used for frequency. Arguments: (1) name, (2)
                    stepString {'event', 'time'}, (3) parameterObject
                    {secPerCycle}, (4) phase, (5) exponent, (6) min, (7) max

pi{auto-muteHiConga}ti{b1} :: tpv noise
Generator ParameterObject
{name,documentation}
Noise               noise, resolution, parameterObject, min, max
                    Description: Fractional noise (1/fn) Generator, capable of
                    producing states and transitions between 1/f white, pink,
                    brown, and black noise. Resolution is an integer that
                    describes how many generators are used. The gamma argument
                    determines what type of noise is created. All gamma values
                    are treated as negative. A gamma of 0 is white noise; a
                    gamma of 1 is pink noise; a gamma of 2 is brown noise; and
                    anything greater is black noise. Gamma can be controlled by
                    a dynamic ParameterObject. The value produced by the noise
                    generator is scaled within the unit interval. This
                    normalized value is then scaled within the range designated
                    by min and max; min and max may be specified by
                    ParameterObjects. Arguments: (1) name, (2) resolution, (3)
                    parameterObject {gamma value as string or number}, (4) min,
                    (5) max
```

The command TPmap provides graphical displays of ParameterObject-generated values. (To configure athenaCL graphics output, see .) The user must supply the name of the ParamaterObject library (Generator, Rhythm, or Filter), the number of events to generate, and the ParameterObject argument list.
      

**ParameterObject Map display with TPmap**

```
pi{auto-muteHiConga}ti{b1} :: tpmap
select a library: Generator, Rhythm, or Filter. (g, r, f): g
number of events: 120
enter a Generator ParameterObject argument: wpd, e, 30, 0, 2

wavePowerDown, event, (constant, 30), 0, 2, (constant, 0), (constant, 1)
TPmap display complete.
```

The TPmap, like other athenaCL commands, can be used with command-line arguments. In the following example, the user produces a TPmap display of the noise ParameterObject, generating "brown" fractional noise:
      

**ParameterObject Map display with TPmap**

```
pi{auto-muteHiConga}ti{b1} :: tpmap 120 n,50,(c,2),0,1

noise, 50, (constant, 2), (constant, 0), (constant, 1)
TPmap display complete.
```

