## Executing Commands

To use a command, simply enter its name. The user will be prompted for all additional information. For example, type "PIn" (or "pin") at the athenaCL prompt:
      

**Entering a command**

```
pi{}ti{} :: pin
name this PathInstance: a
enter a pitch set, sieve, spectrum, or set-class: b,c#,g
      SC 3-8B as (B4,C#4,G4)? (y, n, or cancel): y
      add another set? (y, n, or cancel): n
PI a added to PathInstances.
```

This command prompts the user for a "pitch set, sieve, spectrum, or set-class" and then creates a multiset component of a Path. A Xenakis sieve (Xenakis 1990 [AN#327], 1992 [AN#60]; Ariza 2004 [AN#443], 2005 [AN#613], 2009 [AN#1990]) can be entered using a logical string and a pitch range. Set class labels are given using Forte names. The user may enter the chord itself as pitch-names (with sharps as "#" and flats as "$") or pitch-classes (integers that represent the notes of the chromatic scale) (Straus 1990 [AN#34]). For instance, the chord D-major can be represented with the following pitch-name string: (D, F#, A). Or, the same chord can be represented as a pitch class set: (2,6,9), where 0 is always C, 1=C#, 2=D, …, 10=A#, and 11=B. Calling the PIn command to create a new path named "b" with this pitch class set gives us the following results:
      

**Entering a command with arguments**

```
pi{a}ti{} :: pin b d,f#,a
PI b added to PathInstances.
```

Notice that in the above example the Path name and pitch collection arguments are entered at the same time as the command: "pin b d,f#,a". As an interactive command-line program, athenaCL can obtain arguments from the user, and can, alternatively, accept space-separated arguments following a command. Command-line arguments allow advanced users ease and speed and, when called from an external environment (such as a UNIX shell or Python script), permit advanced scripting automation. All athenaCL commands can function both with arguments and with interactive prompts. Command-line arguments, however, are never required: if arguments are absent, the user is prompted for the necessary details.
      
