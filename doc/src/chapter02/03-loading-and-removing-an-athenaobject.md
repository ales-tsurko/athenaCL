## Loading and Removing an AthenaObject

The command AOl, for AthenaObject load, permits the user to load an AthenaObject XML file. Numerous small demonstration files are included within athenaCL. In the following example, the user loads the file "demo01.xml".
      
The following display demonstrates use of the text-based file-dialogs. When using the text-based interface, the user must select a directory before selecting a file. In the example below, the user enters "demo" to enter the "demo" directory in the athenaCL directory. The user then enter "s" to select this directory. Next, the user has the option the select a file from this directory, change the directory, or cancel. The user chooses to select a file with "f". After entering the name of the file ("demo01.xml") and confirming, the AthenaObject is loaded:
      

**Loading an AthenaObject with text-based file selection**

```
pi{}ti{} :: aol
select an AthenaObject file:
name file, change directory, or cancel? (f, cd, c): cd
/Volumes/xdisc/_sync/_x/src/athenacl/athenaCL/demo/legacy
................................................................................
.svn            __init__.py     demo01.xml      demo03.xml      demo05.xml      
spectrum01.txt  tutorial02.xml  tutorial03.xml  tutorial04.xml  tutorial05.xml  
tutorial06.xml  tutorial07.xml  tutorial09.xml  
to change directory enter name, path, or ".."
cancel or select? (c or s): s
select an AthenaObject file:
name file, change directory, or cancel? (f, cd, c): f
name file? demo01.xml
      1.3.1 xml AthenaObject loaded (00:01):
/Volumes/xdisc/_sync/_x/src/athenacl/athenaCL/demo/legacy/demo01.xml
```

To confirm that the AthenaObject has been loaded, the user may enter TIls to display a list of all TextureInstances. (For more information concerning Textures, see ).
      

**Listing TextureInstances with Tils**

```
pi{y0}ti{a2} :: tils
TextureInstances available:
{name,status,TM,PI,instrument,time,TC}
   _space           + MonophonicOrnament x0          62  39.0--40.0   0
   a0               + MonophonicOrnament y0          50  01.0--41.0   0
   a1               + MonophonicOrnament y0          50  01.0--41.0   0
 + a2               + MonophonicOrnament y0          50  01.0--41.0   0
```

The entire AthenaObject can be erased and set to its initial state without restarting the athenaCL program. The following example uses AOrm, for AthenaObject remove, to re-initialize the AthenaObject. Note: the AOrm will permanently remove all objects within athenaCL and cannot be un-done.
      

**Reinitializing the AthenaObject with AOrm**

```
pi{y0}ti{a2} :: aorm
destroy the current AthenaObject? (y or n): y
reinitializing AthenaObject.

pi{}ti{} :: 
```

If the AthenaObject file is located in the athenaCL "demo" directory, or a directory from which a file was opened or saved-to by the user within the current session, athenaCL can find the file by giving the AOl command with the file's name as a command-line argument. To reload "demo01.xml", the user may enter the following arguments:
      

**Loading an AthenaObject from the command-line**

```
pi{}ti{} :: aol demo01.xml
      1.3.1 xml AthenaObject loaded (00:01):
/Volumes/xdisc/_sync/_x/src/athenacl/athenaCL/demo/legacy/demo01.xml
```

