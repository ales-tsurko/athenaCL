## Creating a Path with a Duration Fraction

First, the user creates a path consisting of three Multisets. As demonstrated in , there are many ways to create and edit a Path. In the following example, the user creates a new path named q1 by simply providing pitch space values using conventional note names. The path is the then viewed with the PIv command, and auditioned with the PIh command.
      

**Creating a Path with PIn**

```
pi{}ti{} :: pin
name this PathInstance: q1
enter a pitch set, sieve, spectrum, or set-class: D2,G#3,A3,D3,E2,B2,A2
      SC 5-29A as (D2,G#3,A3,D3,E2,B2,A2)? (y, n, or cancel): y
      add another set? (y, n, or cancel): y
enter a pitch set, sieve, spectrum, or set-class: C4,C#4,F#3,G4,A3
      SC 5-19A as (C4,C#4,F#3,G4,A3)? (y, n, or cancel): y
      add another set? (y, n, or cancel): y
enter a pitch set, sieve, spectrum, or set-class: G#5,A4,D#4,E5
      SC 4-8 as (G#5,A4,D#4,E5)? (y, n, or cancel): y
      add another set? (y, n, or cancel): n
PI q1 added to PathInstances.

pi{q1}ti{} :: piv
PI: q1
psPath              -22,-4,-3,-10,-20,-13,-15  0,1,-6,7,-3       20,9,3,16      
                    D2,G#3,A3,D3,E2,B2,A2      C4,C#4,F#3,G4,A3  G#5,A4,D#4,E5  
pcsPath             2,8,9,2,4,11,9             0,1,6,7,9         8,9,3,4        
scPath              5-29A                      5-19A             4-8            
durFraction         1(33%)                     1(33%)            1(33%)         
TI References: none.

pi{q1}ti{} :: pih
PI q1 hear with TM LineGroove complete.
(/Volumes/xdisc/_scratch/ath2010.07.03.19.05.21.mid)
```

As should be clear from the psPath display or the auditioned MIDI file, Path q1 covers a wide pitch range, from E2 to G#5. Notice also that the "durFraction" specifies that each Multiset in the Path has an equal duration weighting (1, or 33%). The durFraction of a Path is a means of providing a proportional temporal weighting to each Multiset in the Path. When a Texture interprets a Path, it partitions its duration into as many segments as there are Path Multisets, and each segment is given a duration proportional to the Path durFraction. The command PIdf can be used to alter a Path's duration weighting. The user must supply a list of values, either as percentages (floating point or integer) or simply as numeric weightings. In the following example, after calling PIdf, the command PIh is used to audition the results of an altered durFraction:
      

**Altering a Path's durFraction with PIdf**

```
pi{q1}ti{} :: pidf
edit PI q1
enter a list of duration fractions: 8,5,3
PI q1 edited.

pi{q1}ti{} :: piv
PI: q1
psPath              -22,-4,-3,-10,-20,-13,-15  0,1,-6,7,-3       20,9,3,16      
                    D2,G#3,A3,D3,E2,B2,A2      C4,C#4,F#3,G4,A3  G#5,A4,D#4,E5  
pcsPath             2,8,9,2,4,11,9             0,1,6,7,9         8,9,3,4        
scPath              5-29A                      5-19A             4-8            
durFraction         8(50%)                     5(31%)            3(19%)         
TI References: none.

pi{q1}ti{} :: pih
PI q1 hear with TM LineGroove complete.
(/Volumes/xdisc/_scratch/ath2010.07.03.19.08.09.mid)
```

The PIv display shows that the Multisets are weighted such that the first is given 50%, the second 31%, and the last 19%. The MIDI file created with PIh should confirm this distribution.
      
