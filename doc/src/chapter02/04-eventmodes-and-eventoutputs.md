## EventModes and EventOutputs

After loading a demonstration file containing TextureInstances, athenaCL can be used to create an EventList. As a poly-paradigm system with integrated instrument models, athenaCL supports numerous formats of EventLists and can work with a wide variety of sound sources, including Csound and MIDI. What types of EventLists are created depends on two settings within athenaCL: the EventMode and the EventOutput.
      
The EventModes configure athenaCL for working with a particular sound source and Orchestra model, such as the internal Csound orchestra (csoundNative), external Csound orchestras (csoundExternal), various types of MIDI files (generalMidi an generalMidiPercussion), and others. The EventMode determines what instruments are available for Texture creation (see , as well as the operation of some EventList commands. In some cases, the EventMode forces certain EventOutput formats to be written as well.
      
The EventOutputs select what file formats will be created when a new EventList is generated. athenaCL permits the user to create an EventList in numerous formats simultaneously. For example, a Csound score and orchestra, a MIDI file, and tab-delimited table can all be produced from one call to the EventList new command. Some EventOutput formats are created only if the AthenaObject contains Textures created in the appropriate EventMode. Other EventOutput formats can be created with any Texture in any EventMode. Such conflicts, however, are never a problem: athenaCL simply creates whatever EventOutput formats are appropriate based on the user-specified request.
      
To view the current EventMode, enter EMls. To view the current list of selected EventOutputs, enter EOls. The following example demonstrates these commands:
      

**Viewing EventMode and EventOutputs**

```
pi{y0}ti{a2} :: emls
EventMode modes available:
{name}
   csoundExternal      
 + csoundNative        
   csoundSilence       
   midi                
   midiPercussion      
   superColliderNative 

pi{y0}ti{a2} :: eols
EventOutput active:
{name}
   acToolbox         
   audioFile         
   csoundBatch       
 + csoundData        
   csoundOrchestra   
   csoundScore       
 + midiFile          
   pureDataArray     
   superColliderTask 
   textSpace         
   textTab           
 + xmlAthenaObject  
```

To select an additional EventOutput to be requested when a new EventList is created, enter the command EOo, for EventOutput select. To remove an EventOutput, enter the command EOrm, for EventOutput remove. In the following example, the user adds a tab-delimited table output ("textTab") and a specialized output file for the AC Toolbox ("acToolbox"). After viewing the EventOutput list, these EventOutputs are removed. Note: EventOutputs, like many selection in athenaCL, can be designated using automatic acronym expansion (AAE), the user providing only the leading character and capitals. 
      

**Adding and Removing EventOutputs**

```
pi{y0}ti{a2} :: eoo tt at
EventOutput formats: midiFile, xmlAthenaObject, csoundData, textTab, acToolbox.

pi{y0}ti{a2} :: eols
EventOutput active:
{name}
 + acToolbox         
   audioFile         
   csoundBatch       
 + csoundData        
   csoundOrchestra   
   csoundScore       
 + midiFile          
   pureDataArray     
   superColliderTask 
   textSpace         
 + textTab           
 + xmlAthenaObject  

pi{y0}ti{a2} :: eorm tt at
EventOutput formats: midiFile, xmlAthenaObject, csoundData.
```

