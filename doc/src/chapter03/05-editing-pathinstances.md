## Editing PathInstances

A Path can be edited as a serial succession of Multisets with the standard assortment of serial operations: retrograde, rotation, and slice. Additionally, each Multiset in a Path can be changed, either by transposition or replacement.
      
Whenever a serial edit is performed on a Path, the edited Path becomes a new, distinct Path and the original Path is left unchanged. For example, to create the retrograde of the active Path, enter PIret. The user must provide the name of the new Path:
      

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

To create a rotation, the user, after entering PIrot, must enter the number of the Multiset to occupy the new first position. If the new first position is to be the second Multiset, the user would enter 2:
      

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

A slice will extract a segment from a Path. To create a slice, enter PIslc. The user is prompted for the name of the new Path, and the start and end Multiset positions. If the slice is to only contain the last two chords of a four chord Path, for example, the start and end positions would be 3,4:

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

There are three ways to edit a single Multiset within a Path using the PIe command: by replacement, by transposition, or by inversion. In all cases, the number of elements in the Multiset must be maintained.
      
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

Here the user has selected the Multiset in position "2" of PI "pathD" to edit. The user next selects to edit the set by transposition, entering "t". There are two methods of transposition available: a "literal" transposition is done in pitch space, creating a new set in the range of all positive and negative integers; a "modulus" transposition is done in pitch-class space, creating a new set in the range of pitch-classes 0 through 11. In the example above the user has selected a literal ("l") transposition and enters "8" as the transposition value.  This shifts each pitch in the Multiset up 8 half-steps. Since this is a literal and not a modulus transposition, pitch 5 becomes pitch 15, or D#5.
      
Any Multiset in a Path can be replaced with a Multiset of equal size. For example, the same Multiset edited above can be replaced with any four-element Multiset:

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

