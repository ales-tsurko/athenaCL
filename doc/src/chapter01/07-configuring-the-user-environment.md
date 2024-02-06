## Configuring the User Environment

athenaCL has many configurable settings that are saved in a preference file and loaded for each athenaCL session. Some of these settings have default values; others will need to be configured the first time a command is used.
      
For example, following the athenaCL prompt ("::") is the the athenaCL "cursor tool." This tool, providing information on the active Texture and Path, can be turned on or off with the command APcurs, for AthenaPreferences cursor:
      

**Toggling the athenaCL cursor tool with APcurs**

```
pi{b}ti{} :: apcurs
cursor tool set to off.

:: apcurs
cursor tool set to on.

pi{b}ti{} :: 
```

athenaCL writes files. Some of these files are audio file formats, some are event list formats (scores, MIDI files), and some are image files. In most cases, athenaCL will write a file in a user specified "scratch" directory with an automatically-generated file name. This is convenient and fast. To set the scratch directory, enter the APdir command, for AthenaPreferences directory. (Replace "/Volumes/xdisc/_scratch" with a complete file path to a suitable directory.)
      

**Setting the scratch directory with APdir**

```
pi{b}ti{} :: apdir
select directory to set: scratch or audio. (x or a): x
/Users/ariza/_x/src/athenaCL
................................................................................
.cvsignore      .DS_Store       __init__.py     __init__.pyc    __init__.pyo    
athenacl.py     athenacl.pyc    athenaObj.py    athenaObj.pyc   athenaObj.pyo   
CVS             demo            docs            libATH          setup.py        
tools     
select a scratch directory:
to change directory enter name, path, or ".."
cancel or select? (c or s): /Volumes/xdisc/_scratch
/Volumes/xdisc/_scratch
................................................................................
.DS_Store       a.mid           
select a scratch directory:
to change directory enter name, path, or ".."
cancel or select? (c or s): s
user scratch directory set to /Volumes/xdisc/_scratch.
```

The command PIh, for PathInstance hear, allows the creation of a MIDI file from a single Path specification. In this case, athenaCL writes the MIDI file in the user-specified scratch directory. After the file is written, athenaCL opens the file with the operating system. Depending on how the operating system is configured, the MIDI file should open in an appropriate player. The athenaCL system frequently works in this manner with the operating system and external programs and resources.
      

**Creating a MIDI file with PIh**

```
pi{b}ti{} :: pih
command.py: temporary file: /Volumes/xdisc/_scratch/ath2010.07.01.16.12.52.xml 
PI b hear with TM LineGroove complete.
(/Volumes/xdisc/_scratch/ath2010.07.01.16.12.52.mid)
```

Numerous types of graphical aids are provided by athenaCL to assist in the representation of musical materials. Depending on the user's Python installation, numerous formats of graphic files are available. Formats include text (within the Interpreter display), Encapsulated PostScript (convertible to PDF), Tk GUI Windows, JPEG, and PNG. Tk requires the Python TkInter GUI installation; JPEG and PNG require the Python Imaging Library (PIL) installation.
      
The user can set an active graphic format with the APgfx command. For example:
      

**Setting the active graphics format with APgfx**

```
pi{b}ti{} :: apgfx
active graphics format: png.
select text, eps, tk, jpg, png. (t, e, k, j, or p): p
graphics format changed to png.
```

To test the production of graphic output, the TPmap command, for TextureParameter map, can be used:
      

**Producing a graphical diagram with TPmap**

```
pi{b}ti{} :: tpmap 100 ru
randomUniform, (constant, 0), (constant, 1)
TPmap display complete.
```

