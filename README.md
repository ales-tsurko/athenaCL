# athenaCL

athenaCL is an algorithmic composition tool created by Christopher Ariza.

Or, as described by the author more specifically, it is a tool for:
> modular poly-paradigm algorithmic music composition in a cross-platform
> interactive command-line environment.




## About This Fork

The last commit in the original repo pushed in 2011. It was written in Python 2,
this repo updates the code to Python 3.

So far all tests of the main module (`libATH`) passed and it seems like it works
in the terminal.  But test coverage is far from 100% and many bugs introduced by
the conversion may still exist.

For now, I don't have any plans to introduce new features, but if you'll find
any bugs, I'm ready to try to fix them when I have time. So fill free to open
issues. Also, feel free to open PR's.

When I finish with the manual and fixing bugs I'll find in the examples of
tutorials, I'm going to keep it on "life support" - just fixing bugs, when I
find some while using the application as a normal user (i.e. not a tester).

I'd also like to add a front end to this application, but that would be a
separate project.




---

athenaCL Copyright (c) 2000-2024 Christopher Ariza and others.
athenaCL is free software, distributed under the GNU General Public License.

athenaCL 2.0.0a15




## Contents

1. [I. Software Dependencies](#i-software-dependencies)
2. [II. Quick Start](#ii-quick-start)
3. [IIIa. Installation](#iiia-installation)
4. [IIIb. athenaCL via Command Line Interface](#iiib-athenacl-via-command-line-interface)
5. [IIIc. athenaCL via IDLE](#iiic-athenacl-via-idle)
6. [IIId. athenaCL via Python Prompt](#iiid-athenacl-via-python-prompt)
7. [IV. Documentation](#iv-documentation)
8. [V. Credits and Acknowledgments](#v-creadits-and-acknowledgments)




## I. SOFTWARE DEPENDENCIES

athenaCL produces both Csound and MIDI scores. Csound is free and runs on 
every platform. Download Csound here:
https://csound.com/.

athenaCL produces images with various Python-based graphic output systems.
These output systems include the Python TkInter GUI library and the fork of
Python Image Library (Pillow), and may require additional Python software. Most
Python distributions include TkInter (MacOS systems may require additional
configuration); Pillow is easily added to Python.  https://python-pillow.org/




## II. QUICK-START

1. `$ python setup.py`
2. `$ python athenaCL/athenacl.py`

Or via python prompt:

1. `>>> import athenaCL.athenacl`




## IIIa. INSTALLATION

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




## IIIb. athenaCL VIA COMMAND LINE INTERFACE

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




## IIIc. athenaCL VIA IDLE

installing:

1. place athenaCL directory wherever you like
2. enter the athenaCL directory
3. double-click "setup.py"

launching on Windows:

4. double-click "athenacl.py"
5. enter "y" when asked to start athenaCL in IDLE

launching from the command line interface:

4. `$ python athenacl.py -s idle`




## IIId. athenaCL VIA PYTHON PROMPT

If the athenaCL setup.py script has been successfully completed, Python should
already be aware of the location of the current athenaCL installation. If the
athenaCL setup.py script has not been properly run, the directory containing
athenaCL must be manually added to the Python sys.path:

(if the athenaCL directory is located in the directory "/src")

1. `>>> import sys`
2. `>>> sys.path.append('/src')`

launching:

3. `>>> import athenaCL.athenacl`




## IV. DOCUMENTATION

For complete documentation, tutorials, and reference, see the athenaCL Tutorial
Manual: www.flexatone.net/athenaDocs/




## V. CREDITS and ACKNOWLEDGMENTS

athenaCL was created by Christopher Ariza. Numerous generator ParameterObjects
based in part on the Object-oriented Music Definition Environment (OMDE/pmask),
Copyright 2000-2001 Maurizio Umberto Puxemdu; Cmask was created by Andre
Bartetzki. The Command Line Interpreter is based in part on cmd.py; the module
textwrap.py is by Greg Ward; both are distributed with Python, Copyright
2001-2003 Python Software Foundation. The fractional noise implementation in
dice.py, Audacity spectrum importing, and dynamic ParameterObject boundaries are
based in part on implementations by Paul Berg.  The module genetic.py is based
in part on code by Robert Rowe. The module midiTools.py is based in part on code
by Bob van der Poel. The module chaos.py is based in part on code by Hans
Mikelson. The module permutate.py is based in part on code by Ulrich
Hoffman. Pitch class set names provided in part by Larry Solomon. The
Rabin-Miller Primality Test is based in part on an implementation by Stephen
Krenzel. The mpkg installer is generated with py2app (bdist_mpkg) by Bob
Ippolito. Python language testing done with PyChecker (by Neal Norwitz Copyright
2000-2001 MetaSlash Inc.) and pyflakes (by Phil Frost Copyright 2005 Divmod
Inc.). Thanks to the following people for suggestions and feedback: Paul Berg,
Per Bergqvist, Marc Demers, Ryan Dorin, Elizabeth Hoffman, Anthony Kozar, Paula
Matthusen, Robert Rowe, Jonathan Saggau, Jesse Sklar and Menno Knevel. Thanks
also to the many users who have submitted anonymous bug-reports.

Apple, Macintosh, Mac OS, and QuickTime are trademarks or registered trademarks
of Apple Computer, Inc. Finale is a trademark of MakeMusic! Inc.  Java is a
trademark of Sun Microsystems. Linux is a trademark of Linus Torvalds. Max/MSP
is a trademark of Cycling '74. Microsoft Windows and Visual Basic are trademarks
or registered trademarks of Microsoft, Inc. PDF and PostScript are trademarks of
Adobe, Inc. Sibelius is a trademark of Sibelius Software Ltd. SourceForge.net is
a trademark of VA Software Corporation. UNIX is a trademark of The Open Group.
