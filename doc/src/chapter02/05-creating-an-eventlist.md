## Creating an EventList

To create an EventList, the command ELn, for EventList new, must be used. This command generates a new EventList for each Texture and Clone, and writes necessary EventOutput formats. Each time the ELn command is called, a new musical variant (depending on Texture, Clone, and ParameterObject specification) is produced. It is possible, even likely, that two EventLists, generated from the same AthenaObject file, will not be identical. EventLists, further, are never stored within an AthenaObject. For this reason, users should be careful to save and preserve produced EventList files.
      
When using the ELn command alone, temporary files are created, either in a system-location, or in the scratch directory selected by the user. The user may also, optionally, name the EventList. The EventList name is given as a file name (or a complete file path) ending with an ".xml" extension. Although the ELn command may produce many files, only one file path needs to be provided: all other EventOutput format file names are derived from this source .xml file path. If EventOutput xmlAthenaObject is active, an XML AthenaObject file will be written along with whatever user-specified or EventMode-mandated EventOutput formats are created.
      
In the example above, the user's EventOutput format specification indicates that midiFile and xmlAthenaObject are active outputs. The current EventMode, however, is set to csoundNative, and the Textures of "demo01.xml", upon examination, were created with csoundNative instruments. For these reasons, the ELn command, in this case, will produce an .xml AthenaObject file, a Csound .csd file, a MIDI file (.mid), and a script file for processing the Csound orchestra and score (.bat). For example:
      

**Creating a new EventList with Eln**

```
pi{y0}ti{a2} :: eln
      EventList ath2010.07.02.13.22.35 complete:
/Volumes/xdisc/_scratch/ath2010.07.02.13.22.35.bat
/Volumes/xdisc/_scratch/ath2010.07.02.13.22.35.csd
/Volumes/xdisc/_scratch/ath2010.07.02.13.22.35.mid
/Volumes/xdisc/_scratch/ath2010.07.02.13.22.35.xml
```

Csound files require additional processing to hear audio from the results: this will be demonstrated below. The MIDI file, however, can be listened to immediately with any MIDI file player, such as QuickTime. To hear the file produced by ELn, enter the command ELh, for EventList hear:
      

**Opening an EventList with Elh**

```
pi{y0}ti{a2} :: elh
EventList hear initiated: /Volumes/xdisc/_scratch/ath2010.07.02.13.22.35.mid
```

Depending on operating system configuration, the ELh command should open the newly-created MIDI file in a MIDI-file player. Alternatively, the MIDI file can be opened in an application that supports MIDI files, such as a notation program or sequencer.
      
The ELn command, as all athenaCL commands, can be used with command-line arguments. To create an EventList in a specific directory, simply provide a complete file path following the the ELn command. (Replace "/Volumes/xdisc/_scratch/" with a complete file path to a suitable directory.)
      

**Creating a new EventList with Eln and command-line arguments**

```
pi{y0}ti{a2} :: eln /Volumes/xdisc/_scratch/test02.xml
      EventList test02 complete:
/Volumes/xdisc/_scratch/test02.bat
/Volumes/xdisc/_scratch/test02.csd
/Volumes/xdisc/_scratch/test02.mid
/Volumes/xdisc/_scratch/test02.xml
```

Using the ELh command to listen to this EventList, the user should identify that although "test01" and "test02" are closely related, each musical fragment, due to algorithmic variation, has differences.
      
