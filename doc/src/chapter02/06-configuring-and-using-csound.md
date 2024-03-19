## Configuring and Using Csound

Although Csound files were created in the above examples, only the resulting MIDI files were auditioned. To produce audio files with Csound, some additional configuration may be necessary.
      
To create an audio file with Csound, two files are required: a score (.sco) and an orchestra (.orc); alternatively, both files can be combined into a single XML file called (within athenaCL) a csoundData file (.csd). With the csoundNative instruments and EventMode, all necessary Csound files are created by athenaCL. To activate csoundData file production, the EventOutput csoundData must be selected. Alternatively, users can create only a Csound score (with EventModes csoundExternal or csoundSilence), and apply this score to any desired external Csound orchestra.
      
The Csound audio rendering software must be installed separately. Csound is an open source, free, cross platform program available for all major operating systems.
      
Once configured properly, athenaCL provides commands to control Csound rendering. The user may be required to provide the location of (file path to) the Csound program; the location of the Csound program is set with the APea command, or Athena Preferences external applications command. Each platform has a different default Csound application specified. Unix: default position is /usr/local/bin/csound; MacOS X: default Csound is the same as Unix; Windows: users must select the Csound executable, "winsound.exe," with the APea command. The user can select a different Csound with the APea command; this selection is stored in the user preferences and is maintained between athenaCL sessions.
      
Assuming that the necessary Csound files were created with ELn as demonstrated above, the user may view the Csound score file created with the command ELv, or EventList view. Depending on operating system configuration, this command will open the score file with a platform-specific text reader. Alternatively, the .sco file can be manually selected and opened by the user.
Whenever athenaCL creates Csound files under EventMode csoundNative, a script file (.bat) is created to automate rendering of the audio file from the Csound score and orchestra (or .csd file). The script instructs Csound to create an audio file with the same name as the score in the same directory as the score, orchestra, and batch file.
      
Prior to writing files with the ELn command, the desired audio file format can be specified from within athenaCL using the command APa. The user will be prompted to select a file format from the options given. Note: the user must set Csound options before executing ELn; otherwise, they will have no effect until a new EventList is created.
      

**Changing the Csound audio file format with CPff**

```
pi{y0}ti{a2} :: apa
select format, channels, or rate. (f,c,r): f
current audio file format: aif.
select aif, wav, or sd2. (a, w, or s): a
audio format set to 'aif'.
```

Assuming correct Csound installation and configuration within athenaCL, the user can enter ELr to automatically initiate Csound rendering of the last Csound score created with ELn. ELr, using the operating system, calls the athenaCL-created script. For ELr to function, and thus the ELn-created script to function, the Csound score and orchestra files (or .csd file) must remain in their original locations. 
      

**Rendering a Csound score**

```
pi{y0}ti{a2} :: elr
audio rendering initiated: /Volumes/xdisc/_scratch/test02.bat
```

Alternatively, users can render Csound files created in athenaCL within any Csound application, just as they would for any other Csound score and orchestra, manually setting file Paths, file formats, and Csound option flags. See Csound documentation for more information on using Csound.
      
As demonstrated above with MIDI files, the user can open the Csound-rendered audio file with the ELh command. This command opens the audio file with a platform-specific media player.
      

**Opening Csound-generated audio files with ELh**

```
pi{y0}ti{a2} :: elh
EventList hear initiated: /Volumes/xdisc/_scratch/test02.aif
EventList hear initiated: /Volumes/xdisc/_scratch/test02.mid
```

To summarize, there are three athenaCL commands needed to create, render, and hear a Csound score, and they must be executed in order: ELn, ELr, ELh. To link these three commands, the user can set a automation preference with the ELauto command. When this option is toggled, the single command ELn will create an EventList, render it in Csound, and open the Csound-created audio file with a platform-specific media player.
      
