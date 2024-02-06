## Creating athenaCL Generator ParameterObjects within Python

Components of the athenaCL system can be used in isolation as resources within Python. Generator ParameterObjects offer particularly useful resources for a range of generative activities.
      
To create a Generator ParameterObject, a Python list of ParameterObject arguments must be passed to the factory() function of the parameter module. This list of arguments must provide proper data objects for each argument.
      
The returned ParameterObject instance has many useful attributes and methods. The doc attribute provides the ParameterObject documentation string. The __str__ method, accessed with the built-in str() function, returns the complete formatted argument string. The __call__ method, accessed by calling the instance name, takes a single argument and returns the next value, or the value at the specified argument time value.
      

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

