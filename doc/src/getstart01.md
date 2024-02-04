##  Software Dependencies

athenaCL produces both Csound and MIDI scores. Csound is free and runs on 
every platform. Download Csound here:
https://csound.com/.

athenaCL produces images with various Python-based graphic output systems.
These output systems include the Python TkInter GUI library and the fork of
Python Image Library (Pillow), and may require additional Python software. Most
Python distributions include TkInter (MacOS systems may require additional
configuration); Pillow is easily added to Python.  https://python-pillow.org/




## Quick-Start

1. `$ python setup.py`
2. `$ python athenaCL/athenacl.py`

Or via python prompt:

1. `>>> import athenaCL.athenacl`




## Installation

Two installation methods are available: (1) placing the athenaCL directory
wherever desired, or (2) installing the athenaCL source into the Python library
with the Python Distribution Utilities (distutils). Both permit using athenaCL
as an interactive application and as a library imported in Python.

Installing athenaCL consist of running the file "setup.py", a script that
performs installation procedures.

The setup.py script can take arguments to perform optional installation
procedures. (1) the "tool" argument, on UNIX and macOS systems, will install a
command-line utility launcher, "athenacl," as well as a corresponding man
page. (2) the "install" argument, on all platforms, will perform a Python
distutils installation into the Python site-packages directory. (3) the
"uninstall" option will remove all athenaCL installation files and directories.




## athenaCL Via Command Line Interface

installing:

1. place athenaCL directory wherever you like
2. enter the athenaCL directory
3. `python setup.py`

or, to install the "athenacl" launcher and the athenaCL man page:

3. `python setup.py tool`

or, to perform a distutils installation

3. `python setup.py install`

launching from the command line interface:

4. `python athenacl.py`

launching with the athenaCL tool:

4. `/usr/local/bin/athenacl`

launching with the athenaCL tool and `/usr/local/bin` in `PATH`:

4. `athenacl`




## athenaCL Via Idle

installing:

1. place athenaCL directory wherever you like
2. enter the athenaCL directory
3. double-click "setup.py"

launching on Windows:

4. double-click "athenacl.py"
5. enter "y" when asked to start athenaCL in IDLE

launching from the command line interface:

4. `$ python athenacl.py -s idle`




## athenaCL Via Python Prompt

If the athenaCL setup.py script has been successfully completed, Python should
already be aware of the location of the current athenaCL installation. If the
athenaCL setup.py script has not been properly run, the directory containing
athenaCL must be manually added to the Python sys.path:

(if the athenaCL directory is located in the directory "/src")

1. `>>> import sys`
2. `>>> sys.path.append('/src')`

launching:

3. `>>> import athenaCL.athenacl`
