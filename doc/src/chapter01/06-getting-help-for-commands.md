## Getting Help for Commands

athenaCL provides two ways of helping the user access and learn commands. If the user only remembers the prefix of a command, this prefix can be entered at the prompt to produce a list of all commands associated with that prefix:
      

**Displaying a command listing**

```
pi{b}ti{} :: pi
PI (PathInstance) commands:
   PIn              new      
   PIcp             copy     
   PIrm             remove   
   PIo              select   
   PIv              view     
   PIe              edit     
   PIdf             duration 
   PIls             list     
   PIh              hear     
   PIret            retro    
   PIrot            rot      
   PIslc            slice 
```

Help information is available for each command and can be accessed from the athenaCL prompt by typing either "?" or "help" followed by the name of the command. The following example provides the documentation for the PIn command. Notice that the main documentation is followed by "usage" documentation, or the format required for providing command-line arguments:
      

**Using the help command**

```
pi{b}ti{} :: help pin
{topic,documentation}
PIn                 PIn: PathInstance: New: Create a new Path from user-
                    specified pitch groups. Users may specify pitch groups in a
                    variety of formats. A Forte set class number (6-23A), a
                    pitch-class set (4,3,9), a pitch-space set (-3, 23.2, 14),
                    standard pitch letter names (A, C##, E~, G#), MIDI note
                    numbers (58m, 62m), frequency values (222hz, 1403hz), a
                    Xenakis sieve (5&3|11), or an Audacity frequency-analysis
                    file (import) all may be provided. Pitches may be specified
                    by letter name (psName), pitch space (psReal), pitch class,
                    MIDI note number, or frequency. Pitch letter names may be
                    specified as follows: a sharp is represented as "#"; a flat
                    is represented as "$"; a quarter sharp is represented as
                    "~"; multiple sharps, quarter sharps, and flats are valid.
                    Octave numbers (where middle-C is C4) can be used with pitch
                    letter names to provide register. Pitch space values (as
                    well as pitch class) place C4 at 0.0. MIDI note numbers
                    place C4 at 60. Numerical representations may encode
                    microtones with additional decimal places. MIDI note-numbers
                    and frequency values must contain the appropriate unit as a
                    string ("m" or "hz"). Xenakis sieves are entered using logic
                    constructions of residual classes. Residual classes are
                    specified by a modulus and shift, where modulus 3 at shift 1
                    is notated 3@1. Logical operations are notated with "&"
                    (and), "|" (or), "^" (symmetric difference), and "-"
                    (complementation). Residual classes and logical operators
                    may be nested and grouped by use of braces ({}).
                    Complementation can be applied to a single residual class or
                    a group of residual classes. For example:
                    -{7@0|{-5@2&-4@3}}. When entering a sieve as a pitch set,
                    the logic string may be followed by two comma-separated
                    pitch notations for register bounds. For example "3@2|4, c1,
                    c4" will take the sieve between c1 and c4. Audacity
                    frequency-analysis files can be produced with the cross-
                    platform open-source audio editor Audacity. In Audacity,
                    under menu View, select Plot Spectrum, configure, and
                    export. The file must have a .txt extension. To use the
                    file-browser, enter "import"; to select the file from the
                    prompt, enter the complete file path, optionally followed by
                    a comma and the number of ranked pitches to read.
usage:              pin name set1 ... setN
```

The same help command can be used to access information concerning additional topics, notations, and representations used within athenaCL. For example, information about Markov transition strings can be accessed with the same help command:
      

**Accessing additional help topics**

```
pi{b}ti{} :: ? markov
{topic,documentation}
Markov Notation     Markov transition strings are entered using symbolic
                    definitions and incomplete n-order weight specifications.
                    The complete transition string consists of two parts: symbol
                    definition and weights. Symbols are defined with alphabetic
                    variable names, such as "a" or "b"; symbols may be numbers,
                    strings, or other objects. Key and value pairs are notated
                    as such: name{symbol}. Weights may be give in integers or
                    floating point values. All transitions not specified are
                    assumed to have equal weights. Weights are specified with
                    key and value pairs notated as such: transition{name=weight
                    | name=weight}. The ":" character is used as the zero-order
                    weight key. Higher order weight keys are specified using the
                    defined variable names separated by ":" characters. Weight
                    values are given with the variable name followed by an "="
                    and the desired weight. Multiple weights are separated by
                    the "|" character. All weights not specified, within a
                    defined transition, are assumed to be zero. For example, the
                    following string defines three variable names for the values
                    .2, 5, and 8 and provides a zero order weight for b at 50%,
                    a at 25%, and c at 25%: a{.2}b{5}c{8} :{a=1|b=2|c=1}.
                    N-order weights can be included in a transition string.
                    Thus, the following string adds first and second order
                    weights to the same symbol definitions: a{.2}b{5}c{8}
                    :{a=1|b=2|c=1} a:{c=2|a=1} c:{b=1} a:a:{a=3|b=9}
                    c:b:{a=2|b=7|c=4}. For greater generality, weight keys may
                    employ limited single-operator regular expressions within
                    transitions. Operators permitted are "*" (to match all
                    names), "-" (to not match a single name), and "|" (to match
                    any number of names). For example, a:*:{a=3|b=9} will match
                    "a" followed by any name; a:-b:{a=3|b=9} will match "a"
                    followed by any name that is not "b"; a:b|c:{a=3|b=9} will
                    match "a" followed by either "b" or "c".
```

Throughout this document additional information for the reader may be recommended by suggesting the use of the help command. For example: (enter "help markov" for more information).
      
