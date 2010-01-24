athenaCL Copyright (c) 2000-2009 Christopher Ariza and others.
athenaCL is free software, distributed under the GNU General Public License.

www.athenacl.org

_______________________._________________________________.__________
athenaCL 1.4.9
15 August 2009
This document contains the following information:

I.    Platform Dependencies
II.   Software Dependencies
IIIa. Quick Start Distributions
IIIb. Quick Start Installers
IVa.  Application Environments
IVb.  Installation
IVc.  athenaCL via Command Line Interface
IVd.  athenaCL via Python Interpreter Application
IVe.  athenaCL via IDLE
IVf.  athenaCL via Python Prompt
V.    Documentation
VI.   Contact Information
VII.  Credits and Acknowledgments

_____.______________________________________________________________
I.    PLATFORM DEPENDENCIES:

athenaCL is distributed as executable cross-platform source-code. Platform-specific distributions and installers are provided for convenience. Make sure you have downloaded the correct archive for your platform:

   Distributions:

unix (GNU/Linux, BSD)
http://www.flexatone.net/athenaCL/athenaCL.tar.gz

Macintosh MacOS X
http://www.flexatone.net/athenaCL/athenaCL.dmg

Windows (any)
http://www.flexatone.net/athenaCL/athenaCL.zip

   Installers:

Windows Installer (exe)
http://www.flexatone.net/athenaCL/athenaCL.exe

__________._______.______.__________________________________________
II.   SOFTWARE DEPENDENCIES:

athenaCL requires Python 2.3 to 2.6. Python 3.0 and better is not yet supported. There is no athenaCL binary: athenaCL interactive sessions run inside a Python interpreter. Python is free and runs on every platform. No additional software is required for basic athenaCL operation. Download Python here:
http://www.python.org/download

athenaCL produces both Csound and MIDI scores. Csound 5 is recommended; Csound 4.16 or better is required to render Csound scores. Csound is free and runs on every platform. Download Csound here:
http://www.csounds.com

athenaCL produces images with various Python-based graphic output systems. These output systems include the Python TkInter GUI library and the Python Image Library (PIL), and may require additional Python software. Most Python distributions include TkInter (MacOS systems may require additional configuration); PIL is easily added to Python. Download PIL here:
http://www.pythonware.com/products/pil/

_________________________.________________________________.___.__.__
IIIa.  QUICK START DISTRIBUTIONS:

All Platforms
   1. install Python 2.3 to 2.6
   2. decompress athenaCL distribution and place wherever desired

UNIX, Command Line Environments, Macintosh MacOS X:
   3. % pythonw setup.py
   4. % pythonw athenacl.py

Macintosh MacOS X:
   3. double-click "setup.command"
   4. double-click "athenacl.command"

For more information and additional installation options, see below.

______________._________________________.___________________________
IIIb.  QUICK START INSTALLERS:

Python Prompt
   1. double click the installer and follow the instructions
   2. start Python
   3. >>> import athenaCL.athenacl
   
Windows Installer (exe)
   1. double click the .exe file and follow the instructions
   2. start python.exe
   3. >>> import athenaCL.athenacl

For more information and additional installation options, see below.

_________.________._________________________________________________
IVa.   APPLICATION ENVIRONMENTS

athenaCL can be run in four different Python environments, depending on your platform and Python installation. These four environments are explained below.

CLI: Command line interface. This is Python run from a system's native command line environment. Running athenaCL within the CLI is recommended whenever possible, and provides the greatest application functionality (including proper line-wrapping and readline on unix environments).

IDLE: IDLE is the tk gui-based Integrated Development Environment distributed with every Python installation. IDLE provides configurable syntax coloring as well as a complete text editor.

PP: Python Prompt. If already in a Python interpreter, athenaCL can be imported directly from the Python prompt.

The following list recommends an environment for each platform. Individual instructions for each environment are provided below.

UNIX (any): CLI
Mac OSX (10.3, 10.4, 10.5 System Python or MacPython): CLI
Windows (95/98/ME/XP/Vista): IDLE
Windows (NT/2000/XP/Vista): CLI

Notes for Mac OSX Users: MacOS X 10.3 (Panther), 10.4 (Tiger), and 10.5 (Leopard) include a complete Python installation (available via Terminal.app) that will run athenaCL without additional configuration (found at /usr/bin/python or /usr/bin/pythonw). The athenaCL.app application, included with the .dmg distribution, assists the user in installing and running athenaCL. MacOS X users may install the official Macintosh Python distribution instead (installed at /usr/local/bin/python).

Notes for Windows Users: When launching a Python interpreter on some versions of Windows, the resulting console does not have text scrolling and text selection features. For this reason, Windows users will be asked when launching athenaCL if they want to load athenaCL in IDLE. Loading athenaCL in IDLE may provide a better command-line interface.

__________________________._________.____._____________________.____
IVb.  INSTALLATION:

When not using a platform-specific installer, the user can configure the method of distribution installation. Two methods are available: (1) placing the athenaCL directory wherever desired, or (2) installing the athenaCL source into the Python library with the Python Distribution Utilities (distutils). Both permit using athenaCL as an interactive application and as a library imported in Python.

Installing athenaCL consist of running the file "setup.py", a script that performs installation procedures. Note: "setup.py" compiles large files to byte-code and, depending on hardware, my take some time to complete. 

The setup.py script can take arguments to perform optional installation procedures. (1) the "tool" argument, on UNIX and MacOS X systems, will install a command-line utility launcher, "athenacl," as well as a corresponding man page. (2) the "install" argument, on all platforms, will perform a Python distutils installation into the Python site-packages directory. (3) the "report" argument provides information on all possible installation features. (4) the "uninstall" option will remove all athenaCL installation files and directories.

________________________.______.________________________.___________
IVc.  athenaCL VIA COMMAND LINE INTERFACE (CLI):

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

____________________________________________________________________
IVd.  athenaCL VIA PYTHON INTERPRETER APPLICATION (PIA):

installing:
	1. decompress athenaCL
	2. place athenaCL directory wherever you like
	3. enter the athenaCL directory
	4. double-click "setup.py"

launching:
	5. double-click "athenacl.py"

_____.___________________________.___.____________._________________
IVe.  athenaCL VIA IDLE:

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

____________________________________________________________________
IVf.  athenaCL VIA PYTHON PROMPT (PP)

if the athenaCL setup.py script has been successfully completed, Python should already by aware of the location of the current athenaCL installation (either via a .pth file installed in site-packages, or a complete installation in site-packages). If the athenaCL setup.py script has not been run, the directory containing athenaCL must be manually added to the Python sys.path:
(if the athenaCL directory is located in the directory "/src")
	1. >>> import sys
	2. >>> sys.path.append('/src')

launching:
	3. >>> import athenaCL.athenacl

__________________._.__________________________________.____________
V.    DOCUMENTATION:

For complete documentation, tutorials, and reference, see the athenaCL Tutorial Manual:
www.flexatone.net/athenaDocs/

____._______________________________________________________________
VI.   CONTACT INFORMATION:

Send questions, comments, and bug reports to:
athenacl-development@lists.sourceforge.net
athenaCL development is hosted at SourceForge:
www.sourceforge.net/projects/athenacl

_______________________________________________._______________.____
VII.  CREDITS and ACKNOWLEDGMENTS:

athenaCL was created and is maintained by Christopher Ariza. Numerous generator ParameterObjects based in part on the Object-oriented Music Definition Environment (OMDE/pmask), Copyright 2000-2001 Maurizio Umberto Puxemdu; Cmask was created by Andre Bartetzki. The Command Line Interpreter is based in part on cmd.py; the module textwrap.py is by Greg Ward; both are distributed with Python, Copyright 2001-2003 Python Software Foundation. The fractional noise implementation in dice.py, Audacity spectrum importing, and dynamic ParameterObject boundaries are based in part on implementations by Paul Berg. The module genetic.py is based in part on code by Robert Rowe. The module midiTools.py is based in part on code by Bob van der Poel. The module chaos.py is based in part on code by Hans Mikelson. The module permutate.py is based in part on code by Ulrich Hoffman. Pitch class set names provided in part by Larry Solomon. Voice leading tools based on a model by Joseph N. Straus. The module OSC.py is Copyright 2002 Daniel Holth and Clinton McChesney. Additional OSC programming and Python interface by Jonathan Saggau. The Notification Framework is Copyright 2001, 2002, 2003 Sebastien Bigaret. The Singleton Pattern is by Jurgen Hermann. The Future thread model is by David Perry. The Rabin-Miller Primality Test is based in part on an implementation by Stephen Krenzel. The mpkg installer is generated with py2app (bdist_mpkg) by Bob Ippolito. Python language testing done with PyChecker (by Neal Norwitz Copyright 2000-2001 MetaSlash Inc.) and pyflakes (by Phil Frost Copyright 2005 Divmod Inc.). Thanks to the following people for suggestions and feedback: Paul Berg, Per Bergqvist, Marc Demers, Ryan Dorin, Elizabeth Hoffman, Anthony Kozar, Paula Matthusen, Robert Rowe, Jonathan Saggau, and Jesse Sklar. Thanks also to the many users who have submitted anonymous bug-reports.

Apple, Macintosh, Mac OS, and QuickTime are trademarks or registered trademarks of Apple Computer, Inc. Finale is a trademark of MakeMusic! Inc. Java is a trademark of Sun Microsystems. Linux is a trademark of Linus Torvalds. Max/MSP is a trademark of Cycling '74. Microsoft Windows and Visual Basic are trademarks or registered trademarks of Microsoft, Inc. PDF and PostScript are trademarks of Adobe, Inc. Sibelius is a trademark of Sibelius Software Ltd. SourceForge.net is a trademark of VA Software Corporation. UNIX is a trademark of The Open Group.

