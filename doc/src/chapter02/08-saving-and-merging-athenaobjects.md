## Saving and Merging AthenaObjects

Loading a new AthenaObject will completely replace the current AthenaObject contents. For this reason, users should always save their work before loading a new AthenaObject. The user can, alternatively, merge AthenaObjects. Merging is a powerful tool: the user can combine many AthenaObjects that have been saved separately, or combine an AthenaObject numerous times with itself. In the example below, the user merges "demo01.xml", loaded above, with another of the same AthenaObject "demo01.xml". The file paths for athenaCL demonstration files are known to athenaCL, and thus the user can simply provide the name of the demonstration file as a command-line argument.
      

**Merging AthenaObjects with AOmg**

```
pi{y0}ti{a2} :: aomg demo01.xml
      1.3.1 xml AthenaObject merged (00:01):
/Volumes/xdisc/_sync/_x/src/athenacl/athenaCL/demo/legacy/demo01.xml

pi{y0}ti{a2} :: 
```

The command TIls can be used to confirm that the AthenaObjects have been merged. The AOmg command, in the case that two Paths or Textures have the same name, automatically alters the name by appending an underscore ("_"). In the case where an AthenaObject is merged with itself as in this example, each Texture and Path is duplicated.
      

**Listing TextureInstances**

```
pi{y0}ti{a2} :: tils
TextureInstances available:
{name,status,TM,PI,instrument,time,TC}
   _space           + MonophonicOrnament x0          62  39.0--40.0   0
   _space_          + MonophonicOrnament x0_         62  39.0--40.0   0
   a0               + MonophonicOrnament y0          50  01.0--41.0   0
   a0_              + MonophonicOrnament y0_         50  01.0--41.0   0
   a1               + MonophonicOrnament y0          50  01.0--41.0   0
   a1_              + MonophonicOrnament y0_         50  01.0--41.0   0
 + a2               + MonophonicOrnament y0          50  01.0--41.0   0
   a2_              + MonophonicOrnament y0_         50  01.0--41.0   0

```

As shown above, the user may create a new MIDI or Csound EventList of this new AthenaObject and audition the results. As should be clear, the resulting musical structure will sound more dense due to the additional Textures. Due to algorithmic variation, each Texture will remain relatively independent.
      
To save the current AthenaObject, the user may create an XML AthenaObject file. Although AthenaObject files may be created with the proper EventOutput selection and by use of the ELn command, in same cases the user my want to create the XML AthenaObject file alone. The command AOw, for AthenaObject Write, provides this functionality. The user must name the AthenaObject with a ".xml" extension. In the example below the user saves the merged files as a new AthenaObject named "merged.xml" using a command-line argument. If desired, the AOw command can be used without command-line arguments to select the location of the file with an interactive file dialog. (Replace "/Volumes/xdisc/_scratch/" with a complete file path to a suitable directory.)
      

**Creating a new AthenaObject with AOw**

```
pi{y0}ti{a2} :: aow /Volumes/xdisc/_scratch/merged.xml
      AthenaObject saved:
/Volumes/xdisc/_scratch/merged.xml
```

Saving your work in athenaCL is very important, and should be done often. The athenaCL system can not reconstruct an AthenaObject from an EventList or an audio file; an athenaCL session can only be reconstructed by loading an AthenaObject XML file.
      
