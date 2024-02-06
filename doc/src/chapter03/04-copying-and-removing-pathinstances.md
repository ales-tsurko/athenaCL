## Copying and Removing PathInstances

In order to manage the collection of Paths in the AthenaObject, the user can copy and remove Paths. In all cases of copying and removing user-defined objects in athenaCL, the active object is never assumed to be the object that the command should be performed upon. Said another way, the user must always specify which object(s) to copy or remove.
      
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

To delete a Path, enter PIrm and select a Path to delete as above. In the example below, the Path to delete is given with a command line argument:
      

**Removing a Path with PIrm**

```
pi{pathC}ti{} :: pirm pathB
PI pathB destroyed.
```

