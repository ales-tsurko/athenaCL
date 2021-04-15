athenaCL Copyright (c) 2000-2010 Christopher Ariza and others.
athenaCL is free software, distributed under the GNU General Public License.

www.athenacl.org

====================================================================
athenaCL 2.0.0a16
April 2021
This document contains the following information:

I. Platform Dependencies
II. Software Dependencies
IIIa. Quick Start Distributions
IIIb. Quick Start Installers
IVa. Installation
IVb. athenaCL via Command Line Interface
IVc. athenaCL via IDLE
IVd. athenaCL via Python Prompt
V. Documentation
VI. Contact Information
VII. Credits and Acknowledgments

====================================================================
I. PLATFORM DEPENDENCIES:

athenaCL is distributed as executable cross-platform source-code. Platform-specific distributions and installers are provided for convenience. Make sure you have downloaded the correct archive for your platform:

    Distributions:

Python EGG
http://www.flexatone.net/athenaCL/athenaCL.egg

unix (GNU/Linux, BSD), Macintosh MacOS X
http://www.flexatone.net/athenaCL/athenaCL.tar.gz

Windows (any)
http://www.flexatone.net/athenaCL/athenaCL.exe


====================================================================
II. SOFTWARE DEPENDENCIES:

athenaCL requires Python 3.0 and better. There is no athenaCL binary: athenaCL interactive sessions run inside a Python interpreter. Python is free and runs on every platform. No additional software is required for basic athenaCL operation. Download Python here:
http://www.python.org/download

athenaCL produces both Csound and MIDI scores. Csound 6 is recommended; Csound 4.16 or better is required to render Csound scores. Csound is free and runs on every platform. Download Csound here:
https://csound.com/

athenaCL produces images with various Python-based graphic output systems. These output systems include the Python TkInter GUI library and the Python Image Library (PIL), and may require additional Python software. Most Python distributions include TkInter (MacOS systems may require additional configuration); PIL is easily added to Python. Download PIL here:
http://www.pythonware.com/products/pil/

====================================================================
IIIa. QUICK-START DISTRIBUTIONS:

All Platforms
    1. install Python 3
    2. decompress athenaCL distribution and place wherever desired

UNIX, Command Line Environments, Macintosh MacOS X:
    3. % python setup.py
    4. % python athenacl.py

For more information and additional installation options, see below.

====================================================================
IIIb. QUICK-START INSTALLERS:

Python Prompt
    1. double click the installer and follow the instructions
    2. start Python
    3. >>> import athenaCL.athenacl
    
Windows Installer (exe)
    1. double click the .exe file and follow the instructions
    2. start python.exe
    3. >>> import athenaCL.athenacl

For more information and additional installation options, see below.

====================================================================
IVa. INSTALLATION:

Two installation methods are available: (1) placing the athenaCL directory wherever desired, or (2) installing the athenaCL source into the Python library with the Python Distribution Utilities (distutils). Both permit using athenaCL as an interactive application and as a library imported in Python.

Installing athenaCL consist of running the file "setup.py", a script that performs installation procedures.

The setup.py script can take arguments to perform optional installation procedures. (1) the "tool" argument, on UNIX and MacOS X systems, will install a command-line utility launcher, "athenacl," as well as a corresponding man page. (2) the "install" argument, on all platforms, will perform a Python distutils installation into the Python site-packages directory. (3) the "uninstall" option will remove all athenaCL installation files and directories.

====================================================================
IVb. athenaCL VIA COMMAND LINE INTERFACE (CLI):

installing:
    1. decompress athenaCL
    2. place athenaCL directory wherever you like
    3. enter the athenaCL directory
    4. % python setup.py

or, to install the "athenacl" launcher and the athenaCL man page:
    4. % python setup.py tool

or, to perform a distutils installation
    4. % python setup.py install

launching from the command line interface:
    5. % python athenacl.py

launching with the athenaCL tool:
    5. % /usr/local/bin/athenacl

launching with the athenaCL tool and /usr/local/bin in PATH:
    5. % athenacl

====================================================================
IVd. athenaCL VIA IDLE:

installing:
    1. decompress athenaCL
    2. place athenaCL directory wherever you like
    3. enter the athenaCL directory
    4. double-click "setup.py"

launching on Windows:
    5. double-click "athenacl.py"
    6. enter "y" when asked to start athenaCL in IDLE

launching from the command line interface:
    5. % python athenacl.py -s idle

====================================================================
IVd. athenaCL VIA PYTHON PROMPT

If the athenaCL setup.py script has been successfully completed, Python should already by aware of the location of the current athenaCL installation. If the athenaCL setup.py script has not been properly run, the directory containing athenaCL must be manually added to the Python sys.path:
(if the athenaCL directory is located in the directory "/src")
    1. >>> import sys
    2. >>> sys.path.append('/src')

launching:
    3. >>> import athenaCL.athenacl

====================================================================
V. DOCUMENTATION:

For complete documentation, tutorials, and reference, see the athenaCL Tutorial Manual:
www.flexatone.net/athenaDocs/

====================================================================
VI. CONTACT INFORMATION:

Send questions, comments, and bug reports to:
athenacl@googlegroups.com
athenaCL development is hosted at GoogleCode:
http://code.google.com/p/athenacl/

====================================================================
VII. CREDITS and ACKNOWLEDGMENTS:

athenaCL was created by Christopher Ariza. Updated to run under Python 3 by Ales Tsurko in 2020. Version 2.0.0a16 was updated by Michael Gogins: the implementation of seeds for the random generators. Numerous generator ParameterObjects based in part on the Object-oriented Music Definition Environment (OMDE/pmask), Copyright 2000-2001 Maurizio Umberto Puxemdu; Cmask was created by Andre Bartetzki. The Command Line Interpreter is based in part on cmd.py; the module textwrap.py is by Greg Ward; both are distributed with Python, Copyright 2001-2003 Python Software Foundation. The fractional noise implementation in dice.py, Audacity spectrum importing, and dynamic ParameterObject boundaries are based in part on implementations by Paul Berg. The module genetic.py is based in part on code by Robert Rowe. The module midiTools.py is based in part on code by Bob van der Poel. The module chaos.py is based in part on code by Hans Mikelson. The module permutate.py is based in part on code by Ulrich Hoffman. Pitch class set names provided in part by Larry Solomon. The Rabin-Miller Primality Test is based in part on an implementation by Stephen Krenzel. The mpkg installer is generated with py2app (bdist_mpkg) by Bob Ippolito. Python language testing done with PyChecker (by Neal Norwitz Copyright 2000-2001 MetaSlash Inc.) and pyflakes (by Phil Frost Copyright 2005 Divmod Inc.). Thanks to the following people for suggestions and feedback: Paul Berg, Per Bergqvist, Marc Demers, Ryan Dorin, Elizabeth Hoffman, Anthony Kozar, Paula Matthusen, Robert Rowe, Jonathan Saggau, Jesse Sklar and Menno Knevel. Thanks also to the many users who have submitted anonymous bug-reports.

Apple, Macintosh, Mac OS, and QuickTime are trademarks or registered trademarks of Apple Computer, Inc. Finale is a trademark of MakeMusic! Inc. Java is a trademark of Sun Microsystems. Linux is a trademark of Linus Torvalds. Max/MSP is a trademark of Cycling '74. Microsoft Windows and Visual Basic are trademarks or registered trademarks of Microsoft, Inc. PDF and PostScript are trademarks of Adobe, Inc. Sibelius is a trademark of Sibelius Software Ltd. SourceForge.net is a trademark of VA Software Corporation. UNIX is a trademark of The Open Group.

