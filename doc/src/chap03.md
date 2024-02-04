# Tutorial 3: Creating and Editing Paths

This tutorial demonstrates the basic features of the Path, including creating,
storing, examining, and editing Paths.
      



## Introduction to Paths

A PathInstance (or a Path or PI) is an ordered collection of pitch groups. A
pitch group, or a Multiset, is the simultaneous representation of pitch-space,
pitch-class space, and set-class information for a collection of
microtonally-specified pitches. This collection can be treated as an ordered or
unordered collection, can be edited by transposition, replacement, or serial
re-ordering, and can be used by one or more Textures to provide pitch materials
that are then independently transposed and interpreted by the Texture and its
ParameterObjects.
      
A PathInstance allows the representation of ordered content groups, and presents
this representation as a multifaceted object. Paths can be of any length, from
one to many Multisets long. A Multiset can be specified in terms of pitch class
(excluding octave information with integers from 0 to 11), or in terms of
pitch-space (including octave information with integers below 0 or above 11, or
with register-specific note names such as C3 and G#12). A Multiset can also be
specified as a group, set, or scale sequence such as a Forte set-class (Forte
1973 [AN#161]) or a Xenakis sieve (Ariza 2005 [AN#613]). Finally, Multisets can
be derived from spectrums and frequency analysis information provided from the
cross-platform audio editor Audacity (enter "help audacity" for more
information).
      
A Path can be developed as a network of intervallic and motivic
associations. The interpretation of a Path by a Texture provides access to
diverse pitch representations for a variety of musical contexts, and permits
numerous Textures to share identical or related pitch information. The use of a
Path in a Texture, however, is optional: a Path can function, at a minimum,
simply as a referential point in Pitch space from which subsequent Texture
transpositions are referenced.
      



## Creating, Selecting, and Viewing PathInstances

To create a PathInstance, enter PIn (for PathInstance new) at the athenaCL
prompt. You must name the new Path, and then supply a pitch group, Forte-number,
Xenakis sieve, or alternative pitch representation (enter "help pitch" for more
information on pitch representations).
      

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

Note that after successfully creating a Path, the athenaCL cursor tool changes
to reflect the active Path: the name in parenthesis following "pi" designates
the active Path ("pathA"). The same information is provided for a
TextureInstance following the "ti" prefix. To view the active PI, enter PIv at
the athenaCL prompt:
      

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

This display provides all essential information about a Path. The header
contains the name of the Path ("pathA"). The parallel presentation of psPath,
pcsPath, and scPath illustrates the simultaneous availability of pitch space,
pitch class space, and set class representations. The label "TI references",
when needed, provides information on which TextureInstances link to this
PathInstance.
      
In order to hear a possible interpretation of this Path, the command PIh
generates a MIDI file based on a simple interpretation of the Path with the
active TextureModule. The resulting musical structure is only provided to
audition the Path, and uses default values for all musical parameters. The MIDI
file is written in the user-specified scratch directory (see ) and is opened via
the operating system.
      

**Creating a MIDI file with PIh**

```
pi{pathA}ti{} :: pih
PI pathA hear with TM LineGroove complete.
(/Volumes/xdisc/_scratch/ath2010.07.02.16.29.39.mid)
```

A second Path can be created exclusively with Forte set class numbers. In this
example, all arguments are provided via the command line:

**Creating a Path with Forte numbers**

```
pi{pathA}ti{} :: pin pathB 5-3 6-4 7-34 4-14
PI pathB added to PathInstances.
```

A newly-created Path always becomes the active Path. Entering PIv will display
the details of the newly created Path:
      

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

As is clear from the PIv display above, when a Multiset in a Path is entered as
a Set class, a pitch space and a pitch class space representation (psPath,
pcsPath) are created from the normal-form of the desired SetClass.
      
In order to display the complete collection of Paths available in the
AthenaObject, the user enters PIls, for PathInstance list:
      

**Listing Paths**

```
pi{pathB}ti{} :: pils
PathInstances available:
{name,TIrefs,scPath}
   pathA            0  3-2B,4-9,3-11A,4-6  
 + pathB            0  5-3A,6-4,7-34,4-14A 
```

Many displays provided by athenaCL are given in columns of data. After whatever
header information is give, a key, in braces ("{}"), is provided to define the
data provided in each column. In the example above, the key shows that each row
contains the name of the PI, the number of TI references, the number of
PathVoices, and an scPath representation of the Path. The "+" next to "pathB"
illustrates that this PI is currently active. All "ls" commands use a similar
designation.
      
Many commands in athenaCL function by using an "active" object. The active PI
defines which Path is used in many different commands. For example, the PIv
command, when used without an argument for which Path to display, displays the
active Path.
      
To select a different PI as the active PI, simply enter PIo. The user is
prompted to either enter the name of the Path to select, or its order number
from the "ls" view (where 1 is pathA, 2 is pathB). Displaying the list of all
PathInstances will confirm that pathA is now the selected PI.
      

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

Alternatively the user can enter the name of the Path to be selected as a
command-line argument with the PIo command. After making pathA active, the user
can make pathB active again by entering the following:
      

**Selecting a Path with an argument**

```
pi{pathA}ti{} :: pio pathB
PI pathB now active.
```




## Copying and Removing PathInstances

In order to manage the collection of Paths in the AthenaObject, the user can
copy and remove Paths. In all cases of copying and removing user-defined objects
in athenaCL, the active object is never assumed to be the object that the
command should be performed upon. Said another way, the user must always specify
which object(s) to copy or remove.
      
To copy a Path instance, enter PIcp and select a Path to copy:
      

**Copying a Path with PIcp**

```
pi{pathB}ti{} :: picp
select a path to copy: (name or number 1-2): pathB
name the copy of path pathB: pathC
PI pathC added to PathInstances.

pi{pathC}ti{} :: pils
PathInstances available:
{name,TIrefs,scPath}
   pathA            0  3-2B,4-9,3-11A,4-6  
   pathB            0  5-3A,6-4,7-34,4-14A 
 + pathC            0  5-3A,6-4,7-34,4-14A 
```

To delete a Path, enter PIrm and select a Path to delete as above. In the
example below, the Path to delete is given with a command line argument:
      

**Removing a Path with PIrm**

```
pi{pathC}ti{} :: pirm pathB
PI pathB destroyed.
```




## Editing PathInstances

A Path can be edited as a serial succession of Multisets with the standard
assortment of serial operations: retrograde, rotation, and slice. Additionally,
each Multiset in a Path can be changed, either by transposition or replacement.
      
Whenever a serial edit is performed on a Path, the edited Path becomes a new,
distinct Path and the original Path is left unchanged. For example, to create
the retrograde of the active Path, enter PIret. The user must provide the name
of the new Path:
      

**Creating a retrograde of a Path with PIret**

```
pi{pathC}ti{} :: piret
name this PathInstance: pathCret
retrograde PI pathCret added to PathInstances.

pi{pathCret}ti{} :: pils
PathInstances available:
{name,TIrefs,scPath}
   pathA            0  3-2B,4-9,3-11A,4-6  
   pathC            0  5-3A,6-4,7-34,4-14A 
 + pathCret         0  4-14A,7-34,6-4,5-3A 
```

To create a rotation, the user, after entering PIrot, must enter the number of
the Multiset to occupy the new first position. If the new first position is to
be the second Multiset, the user would enter 2:
      

**Creating a rotation of a Path with PIrot**

```
pi{pathCret}ti{} :: pirot
name this PathInstance: pathCretRot
which chord should start the rotation? (positions 2-4): 2
rotation PI pathCretRot added to PathInstances.

pi{pathCretRot}ti{} :: pils
PathInstances available:
{name,TIrefs,scPath}
   pathA            0  3-2B,4-9,3-11A,4-6  
   pathC            0  5-3A,6-4,7-34,4-14A 
   pathCret         0  4-14A,7-34,6-4,5-3A 
 + pathCretRot      0  7-34,6-4,5-3A,4-14A 
```

A slice will extract a segment from a Path. To create a slice, enter PIslc. The
user is prompted for the name of the new Path, and the start and end Multiset
positions. If the slice is to only contain the last two chords of a four chord
Path, for example, the start and end positions would be 3,4:

**Creating a slice of a Path with PIslc**

```
pi{pathCretRot}ti{} :: pislc
name this slice of path pathCretRot: pathD
which chords should bound the slice? (positions 1 - 4): 3,4
slice PI pathD added to PathInstances.

pi{pathD}ti{} :: pils
PathInstances available:
{name,TIrefs,scPath}
   pathA            0  3-2B,4-9,3-11A,4-6  
   pathC            0  5-3A,6-4,7-34,4-14A 
   pathCret         0  4-14A,7-34,6-4,5-3A 
   pathCretRot      0  7-34,6-4,5-3A,4-14A 
 + pathD            0  5-3A,4-14A      
```

There are three ways to edit a single Multiset within a Path using the PIe
command: by replacement, by transposition, or by inversion. In all cases, the
number of elements in the Multiset must be maintained.
      
To edit a single Multiset in a Path enter PIe:
      

**Transposing a set within a Path**

```
pi{pathD}ti{} :: pie
edit PI pathD
enter position to edit (positions 1-2): 2
replace, transpose, or invert set (0,2,3,7): (r, t, or i): t
enter a transposition method: literal or modulus? (l or m): l
enter a positive or negative transposition: 8
PI pathD edited.

pi{pathD}ti{} :: piv
PI: pathD
psPath              0,1,2,4,5        8,10,11,15      
                    C4,C#4,D4,E4,F4  G#4,A#4,B4,D#5  
pcsPath             0,1,2,4,5        8,10,11,3       
scPath              5-3A             4-14A           
durFraction         1(50%)           1(50%)          
TI References: none.
```

Here the user has selected the Multiset in position "2" of PI "pathD" to
edit. The user next selects to edit the set by transposition, entering
"t". There are two methods of transposition available: a "literal" transposition
is done in pitch space, creating a new set in the range of all positive and
negative integers; a "modulus" transposition is done in pitch-class space,
creating a new set in the range of pitch-classes 0 through 11. In the example
above the user has selected a literal ("l") transposition and enters "8" as the
transposition value.  This shifts each pitch in the Multiset up 8
half-steps. Since this is a literal and not a modulus transposition, pitch 5
becomes pitch 15, or D#5.
      
Any Multiset in a Path can be replaced with a Multiset of equal size. For
example, the same Multiset edited above can be replaced with any four-element
Multiset:

**Replacing a Multiset with a new Multiset**

```
pi{pathD}ti{} :: pie
edit PI pathD
enter position to edit (positions 1-2): 2
replace, transpose, or invert set (8,10,11,15): (r, t, or i): r
enter a pitch set, sieve, spectrum, or set-class: 2,2,4,4
      SC 2-2 as (D4,D4,E4,E4)? (y, n, or cancel): y
PI pathD edited.

pi{pathD}ti{} :: piv
PI: pathD
psPath              0,1,2,4,5        2,2,4,4      
                    C4,C#4,D4,E4,F4  D4,D4,E4,E4  
pcsPath             0,1,2,4,5        2,2,4,4      
scPath              5-3A             2-2          
durFraction         1(50%)           1(50%)       
TI References: none.
```

