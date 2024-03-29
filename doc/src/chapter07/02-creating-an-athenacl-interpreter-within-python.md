## Creating an athenaCL Interpreter within Python

Within a Python interpreter or a Python script on any platform, one or more instances of the athenaCL Interpreter can be created and programmatically controlled. Programming a sequence of athenaCL commands via a Python script provides maximal control and flexibility in using athenaCL. Loops, external procedures, and a variety of programming designs can be combined with the high-level syntax of the athenaCL command line. Furthermore, command sequences can be stored, edited, and developed. 
      
The cmd() method of the athenaCL Interpreter can be used to be pass  strings or Python data structures. The cmd() method will raise an exception on error. The following example creates an athenaCL Interpter instance named ath and sends it a number of commands to generate a drum beat. 
      

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

For advanced and/or extended work with athenaCL, automating command string execution is highly recommended. Included with the athenaCL distribution is over 30 Python files demonstrating fundamental concepts of working with the system. These files can be found in the demo directory and also in .
      
