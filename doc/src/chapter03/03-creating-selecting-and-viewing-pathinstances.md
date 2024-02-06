## Creating, Selecting, and Viewing PathInstances

To create a PathInstance, enter PIn (for PathInstance new) at the athenaCL prompt. You must name the new Path, and then supply a pitch group, Forte-number, Xenakis sieve, or alternative pitch representation (enter "help pitch" for more information on pitch representations).
      

**Creating a new PathInstance with PIn**

```
pi{}ti{} :: pin
name this PathInstance: pathA
enter a pitch set, sieve, spectrum, or set-class: e$, e, c#
      SC 3-2B as (D#4,E4,C#4)? (y, n, or cancel): y
      add another set? (y, n, or cancel): y
enter a pitch set, sieve, spectrum, or set-class: 0,1,6,7
      SC 4-9 as (C4,C#4,F#4,G4)? (y, n, or cancel): y
      add another set? (y, n, or cancel): y
enter a pitch set, sieve, spectrum, or set-class: 3-11
      SC 3-11A as (C4,D#4,G4)? (y, n, or cancel): y
      add another set? (y, n, or cancel): y
enter a pitch set, sieve, spectrum, or set-class: 7@3|6@4, g2, c4
      SC 4-6 as (A#2,B2,F3,B3,C4)? (y, n, or cancel): y
      add another set? (y, n, or cancel): n
PI pathA added to PathInstances.

pi{pathA}ti{} :: 
```

Note that after successfully creating a Path, the athenaCL cursor tool changes to reflect the active Path: the name in parenthesis following "pi" designates the active Path ("pathA"). The same information is provided for a TextureInstance following the "ti" prefix. To view the active PI, enter PIv at the athenaCL prompt:
      

**Viewing a Path with PIv**

```
pi{pathA}ti{} :: piv
PI: pathA
psPath              3,4,1       0,1,6,7        0,3,7      -14,-13,-7,-1,0  
                    D#4,E4,C#4  C4,C#4,F#4,G4  C4,D#4,G4  A#2,B2,F3,B3,C4  
pcsPath             3,4,1       0,1,6,7        0,3,7      10,11,5,11,0     
scPath              3-2B        4-9            3-11A      4-6              
durFraction         1(25%)      1(25%)         1(25%)     1(25%)           
TI References: none.
```

This display provides all essential information about a Path. The header contains the name of the Path ("pathA"). The parallel presentation of psPath, pcsPath, and scPath illustrates the simultaneous availability of pitch space, pitch class space, and set class representations. The label "TI references", when needed, provides information on which TextureInstances link to this PathInstance.
      
In order to hear a possible interpretation of this Path, the command PIh generates a MIDI file based on a simple interpretation of the Path with the active TextureModule. The resulting musical structure is only provided to audition the Path, and uses default values for all musical parameters. The MIDI file is written in the user-specified scratch directory (see ) and is opened via the operating system.
      

**Creating a MIDI file with PIh**

```
pi{pathA}ti{} :: pih
PI pathA hear with TM LineGroove complete.
(/Volumes/xdisc/_scratch/ath2010.07.02.16.29.39.mid)
```

A second Path can be created exclusively with Forte set class numbers. In this example, all arguments are provided via the command line:

**Creating a Path with Forte numbers**

```
pi{pathA}ti{} :: pin pathB 5-3 6-4 7-34 4-14
PI pathB added to PathInstances.
```

A newly-created Path always becomes the active Path. Entering PIv will display the details of the newly created Path:
      

**Displaying a Path**

```
pi{pathB}ti{} :: piv
PI: pathB
psPath              0,1,2,4,5        0,1,2,4,5,6          0,1,3,4,6,8,10        
                    C4,C#4,D4,E4,F4  C4,C#4,D4,E4,F4,F#4  C4,C#4,D#4,E4,F#4,G#4,
pcsPath             0,1,2,4,5        0,1,2,4,5,6          0,1,3,4,6,8,10        
scPath              5-3A             6-4                  7-34                  
durFraction         1(25%)           1(25%)               1(25%)                
                    ............................................................
                         0,2,3,7       
                    A#4  C4,D4,D#4,G4  
                         0,2,3,7       
                         4-14A         
                         1(25%)        
TI References: none.
```

As is clear from the PIv display above, when a Multiset in a Path is entered as a Set class, a pitch space and a pitch class space representation (psPath, pcsPath) are created from the normal-form of the desired SetClass.
      
In order to display the complete collection of Paths available in the AthenaObject, the user enters PIls, for PathInstance list:
      

**Listing Paths**

```
pi{pathB}ti{} :: pils
PathInstances available:
{name,TIrefs,scPath}
   pathA            0  3-2B,4-9,3-11A,4-6  
 + pathB            0  5-3A,6-4,7-34,4-14A 
```

Many displays provided by athenaCL are given in columns of data. After whatever header information is give, a key, in braces ("{}"), is provided to define the data provided in each column. In the example above, the key shows that each row contains the name of the PI, the number of TI references, the number of PathVoices, and an scPath representation of the Path. The "+" next to "pathB" illustrates that this PI is currently active. All "ls" commands use a similar designation.
      
Many commands in athenaCL function by using an "active" object. The active PI defines which Path is used in many different commands. For example, the PIv command, when used without an argument for which Path to display, displays the active Path.
      
To select a different PI as the active PI, simply enter PIo. The user is prompted to either enter the name of the Path to select, or its order number from the "ls" view (where 1 is pathA, 2 is pathB). Displaying the list of all PathInstances will confirm that pathA is now the selected PI.
      

**Selecting Paths**

```
pi{pathB}ti{} :: pio
select a path to activate: (name or number 1-2): pathA
PI pathA now active.

pi{pathA}ti{} :: pils
PathInstances available:
{name,TIrefs,scPath}
 + pathA            0  3-2B,4-9,3-11A,4-6  
   pathB            0  5-3A,6-4,7-34,4-14A 
```

Alternatively the user can enter the name of the Path to be selected as a command-line argument with the PIo command. After making pathA active, the user can make pathB active again by entering the following:
      

**Selecting a Path with an argument**

```
pi{pathA}ti{} :: pio pathB
PI pathB now active.
```

