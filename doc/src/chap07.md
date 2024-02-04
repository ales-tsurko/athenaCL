# Tutorial 7: Scripting athenaCL in Python

This tutorial demonstrates some of the ways the athenaCL system can be
automated, scripted, and used from within the Python programming language.



## Creating an athenaCL Interpreter within Python

Within a Python interpreter or a Python script on any platform, one or more
instances of the athenaCL Interpreter can be created and programmatically
controlled. Programming a sequence of athenaCL commands via a Python script
provides maximal control and flexibility in using athenaCL. Loops, external
procedures, and a variety of programming designs can be combined with the
high-level syntax of the athenaCL command line. Furthermore, command sequences
can be stored, edited, and developed.
      
The cmd() method of the athenaCL Interpreter can be used to be pass strings or
Python data structures. The cmd() method will raise an exception on error. The
following example creates an athenaCL Interpter instance named ath and sends it
a number of commands to generate a drum beat.
      

**An athenaCL Interpreter in Python**

```
from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()
ath.cmd('emo mp')
ath.cmd('tmo lg')

ath.cmd('tin a1 36')
ath.cmd('tie r l,((4,3,1),(4,3,0),(4,2,1)),rc')

ath.cmd('tin b1 37')
ath.cmd('tie r l,((4,6,1),(4,1,1),(4,3,1)),rc')

ath.cmd('tin c1 53')
ath.cmd('tie r l,((4,1,1),(4,1,1),(4,6,0)),rw')

ath.cmd('tee a bg,rc,(.5,.7,.75,.8,1)')
ath.cmd('tee b ws,t,4,0,122,118')

ath.cmd('eln; elh')
```

For advanced and/or extended work with athenaCL, automating command string
execution is highly recommended. Included with the athenaCL distribution is over
30 Python files demonstrating fundamental concepts of working with the
system. These files can be found in the demo directory and also in .
      



## Creating athenaCL Generator ParameterObjects within Python

Components of the athenaCL system can be used in isolation as resources within
Python. Generator ParameterObjects offer particularly useful resources for a
range of generative activities.
      
To create a Generator ParameterObject, a Python list of ParameterObject
arguments must be passed to the factory() function of the parameter module. This
list of arguments must provide proper data objects for each argument.
      
The returned ParameterObject instance has many useful attributes and
methods. The doc attribute provides the ParameterObject documentation
string. The `__str__` method, accessed with the built-in str() function, returns
the complete formatted argument string. The `__call__` method, accessed by
calling the instance name, takes a single argument and returns the next value,
or the value at the specified argument time value.
      

**Creating a Generator ParameterObject**

```>>> from athenaCL.libATH.libPmtr import parameter
>>>  po = parameter.factory(['ws','t',6,0,-1,1])
>>> str(po)
'waveSine, time, (constant, 6), 0, (constant, -1), (constant, 1)'
>>> po.doc
'Provides sinusoid oscillation between 0 and 1 at a rate given in either time or events per period. This value is scaled within the range designated by min and max; min and max may be specified with ParameterObjects. Depending on the stepString argument, the period rate (frequency) may be specified in spc (seconds per cycle) or eps (events per cycle). The phase argument is specified as a value between 0 and 1. Note: conventional cycles per second (cps or Hz) are not used for frequency.' 
>>> po(1)
0.8660254037844386
>>> po(5)
-0.86602540378443904
```




## Creating athenaCL Generator ParameterObjects within Csound

Within Csound 5.0 orchestras, Python scripts can be written and objects from
Python libraries can be instantiated and processed. Numerous Generator
ParameterObjects and other athenaCL objects can be created, modified, and called
from within Csound instruments. For complete examples, see the detailed articles
on the topic (Ariza [AN#1824], [AN#1990]).
      
