## Selecting and Viewing TextureModules

A Texture is an instance of a TextureModule. Every time a Texture is created, athenaCL creates an independent instance of the active TextureModule. To display a complete list of all available TextureModules, enter the command TMls:
      

**Listing TextureModules with TMls**

```
pi{}ti{} :: tmls
TextureModules available:
{name,TIreferences}
   DroneArticulate    0
   DroneSustain       0
   HarmonicAssembly   0
   HarmonicShuffle    0
   InterpolateFill    0
   InterpolateLine    0
   IntervalExpansion  0
   LineCluster        0
 + LineGroove         0
   LiteralHorizontal  0
   LiteralVertical    0
   MonophonicOrnament 0
   TimeFill           0
   TimeSegment        0
```

As in other athenaCL displays, the first line of the display is a key, telling the user that the list consists of a name followed by the number of TI references. This number displays the count of TextureInstances referenced from a parent TextureModule. The "+" designates the active TextureModule. When creating a new TextureInstance, athenaCL uses the active TextureModule.
      
To select a different TextureModule, the user enters TMo. The user is prompted to enter the name or number (as represented in the list order) of the desired TextureModule. The TMls command can be used to confirm the change.
      

**Selecting the active TextureModule with TMo**

```
pi{}ti{} :: tmo 
which TextureModule to activate? (name or number 1-14): da
TextureModule DroneArticulate now active.

pi{}ti{} :: tmls
TextureModules available:
{name,TIreferences}
 + DroneArticulate    0
   DroneSustain       0
   HarmonicAssembly   0
   HarmonicShuffle    0
   InterpolateFill    0
   InterpolateLine    0
   IntervalExpansion  0
   LineCluster        0
   LineGroove         0
   LiteralHorizontal  0
   LiteralVertical    0
   MonophonicOrnament 0
   TimeFill           0
   TimeSegment        0
```

Here the user has entered "da", to select the TextureModule DroneArticulate. Whenever selecting objects in athenaCL the user may enter the acronym (formed from the leading character and all following capitals), the literal name ("dronearticulate"), or the ordinal number as displayed in the corresponding list display.
      
To learn what a particular TextureModule does, as well what types of Texture options are available, enter the command TMv, for TextureModule View. In this example, the user, with TIo, selects the TextureModule "LineGroove" (with a command-line argument) before entering the TMv command.
      

**Viewing details of the active TextureModule**

```
pi{}ti{} :: tmo linegroove
TextureModule LineGroove now active.

pi{}ti{} :: tmv
TextureModule: LineGroove; author: athenaCL native
This TextureModule performs each set of a Path as a simple monophonic line;
pitches are chosen from sets in the Path based on the pitch selector control.
texture (s)tatic
parallelMotionList    Description: List is a collection of transpositions
                      created above every Texture-generated base note. The
                      timeDelay value determines the amount of time in seconds
                      between each successive transposition in the
                      transpositionList. Arguments: (1) name, (2)
                      transpositionList, (3) timeDelay
pitchSelectorControl  Description: Define the selector method of Path pitch
                      selection used by a Texture. Arguments: (1) name, (2)
                      selectionString {'randomChoice', 'randomWalk',
                      'randomPermutate', 'orderedCyclic',
                      'orderedCyclicRetrograde', 'orderedOscillate'}
levelFieldMonophonic  Description: Toggle between selection of local field
                      (transposition) values per set of the Texture Path, or per
                      event. Arguments: (1) name, (2) level {'set', 'event'}
levelOctaveMonophonic Description: Toggle between selection of local octave
                      (transposition) values per set of the Texture Path, or per
                      event. Arguments: (1) name, (2) level {'set', 'event'}
texture (d)ynamic
```

The TMv command displays the name of the TextureModule along with the author of its code. Following the author designation is a description of how the module performs. Following this is documentation for all TextureStatic parameter objects, or Texture-specific options and user-configurable settings pertinent to the particular TextureModule's algorithmic design.
      
