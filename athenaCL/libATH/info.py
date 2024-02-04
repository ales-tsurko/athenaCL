# -----------------------------------------------------------------||||||||||||--
# Name:          info.py
# Purpose:       tools for creating documentation, help, faq, and build config
#                    files from athenaCL.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2002-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import os, sys
import unittest, doctest


from athenaCL.libATH import athenaObj
from athenaCL.libATH import typeset
from athenaCL.libATH import language

lang = language.LangObj()
from athenaCL.libATH import osTools

_MOD = "info.py"

from athenaCL.libATH import prefTools

environment = prefTools.Environment(_MOD)

# bbedit man page in man1, assume this is good.
MANGROUP = 1  # man1 (general) or man7 (miscellaneous) seem best
MANFILE = "athenacl.%s" % MANGROUP


# -----------------------------------------------------------------||||||||||||--


class InfoManager:
    """utility methods to generate information files for athenaCL and related
    projects: readme, man page, .info files, sgml and html documentation
    pages"""

    def __init__(self, fpDocDir=None):
        """
        >>> a = InfoManager()
        """

        self.ao = athenaObj.AthenaObject()

        if fpDocDir == None:
            fpDocDir = self.ao.external.fpDocDir

        if os.path.exists(fpDocDir) == 1 and os.path.isdir(fpDocDir) == 1:
            pass
        else:  # this will fail, but usefull for getting info
            raise ValueError("bad path")

        environment.printWarn(fpDocDir)
        self.fpDocDir = fpDocDir

        self.athVersion = athenaObj.__version__
        # self.athRevision = athenaObj.athRevision

        # info file for fink packages
        # self.fnInfo = 'athenacl-%s-%s.info' % (self.athVersion,
        #                                             self.athRevision)
        # self.fpInfo = os.path.join(self.fpDocDir, self.fnInfo)

        # bbedit man page in man1, assume this is good.
        self.manGroup = MANGROUP
        self.fnMan = MANFILE
        self.fpMan = os.path.join(self.fpDocDir, self.fnMan)

        self.fnReadme = "README.txt"
        self.fpReadme = os.path.join(self.fpDocDir, self.fnReadme)

        # for decorative elements
        self._divChar = ["="] * 24
        self._divWidth = 68

    # -----------------------------------------------------------------------||--
    def historyScrub(self):

        path = os.path.join(self.fpDocDir, "HISTORY.txt")
        environment.printWarn(["history updated", path])
        f = open(path)
        msg = f.readlines()
        f.close()

        newMsg = []
        for line in msg:
            if line.count("_") >= 10:
                line = "%s\n" % lang.msgDividerAlgo(self._divWidth, self._divChar)
            newMsg.append(line)

        if len(msg) != len(newMsg):
            environment.printWarn("old, new", len(msg), len(newMsg))
            raise ValueError

        f = open(path, "w")
        f.writelines(newMsg)
        f.close()

    # -----------------------------------------------------------------------||--
    def writeReadme(self):
        """write a the readme file"""

        msgContents = """\
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
"""

        msgPlatDepend = """\
I. PLATFORM DEPENDENCIES:

athenaCL is distributed as executable cross-platform source-code. Platform-specific distributions and installers are provided for convenience. Make sure you have downloaded the correct archive for your platform:

    Distributions:

Python EGG
http://www.flexatone.net/athenaCL/athenaCL.egg

unix (GNU/Linux, BSD), Macintosh MacOS X
http://www.flexatone.net/athenaCL/athenaCL.tar.gz

Windows (any)
http://www.flexatone.net/athenaCL/athenaCL.exe

"""

        msgSoftDepend = """\
II. SOFTWARE DEPENDENCIES:

There is no athenaCL binary: athenaCL interactive sessions run inside a Python interpreter. No additional software is required for basic athenaCL operation.

athenaCL produces both Csound and MIDI scores.

athenaCL produces images with various Python-based graphic output systems. These output systems include the Python TkInter GUI library and the Python Image Library (PIL), and may require additional Python software. Most Python distributions include TkInter (MacOS systems may require additional configuration); PIL is easily added to Python. Download PIL here:
http://www.pythonware.com/products/pil/
"""

        msgQuickStartA = """\
IIIa. QUICK-START DISTRIBUTIONS:

All Platforms
    1. install Python
    2. decompress athenaCL distribution and place wherever desired

UNIX, Command Line Environments, Macintosh MacOS X:
    3. % python setup.py
    4. % python athenacl.py

For more information and additional installation options, see below.
"""

        msgQuickStartB = """\
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
"""

        # Macintosh MacOS X Package Installer (mpkg)
        #     1. double click the .mpkg file and follow the instructions
        #     2. start Python
        #     3. >>> import athenaCL.athenacl

        # Macintosh MacOS X via fink
        #     1. % fink install athenacl
        #     2. % athenacl
        # unix (GNU/Linux):
        #     1. install rpc however desired
        #     2. % athenacl
        #
        # or, alternatively:
        #     2. % python -c'import athenaCL.athenacl'
        #

        msgInstall = """\
IVa. INSTALLATION:

Two installation methods are available: (1) placing the athenaCL directory wherever desired, or (2) installing the athenaCL source into the Python library with the Python Distribution Utilities (distutils). Both permit using athenaCL as an interactive application and as a library imported in Python.

Installing athenaCL consist of running the file "setup.py", a script that performs installation procedures.

The setup.py script can take arguments to perform optional installation procedures. (1) the "tool" argument, on UNIX and MacOS X systems, will install a command-line utility launcher, "athenacl," as well as a corresponding man page. (2) the "install" argument, on all platforms, will perform a Python distutils installation into the Python site-packages directory. (3) the "uninstall" option will remove all athenaCL installation files and directories.
"""

        msgCLI = """\
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
"""

        msgIDLE = """\
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
"""

        msgPP = """\
IVd. athenaCL VIA PYTHON PROMPT

If the athenaCL setup.py script has been successfully completed, Python should already by aware of the location of the current athenaCL installation. If the athenaCL setup.py script has not been properly run, the directory containing athenaCL must be manually added to the Python sys.path:
(if the athenaCL directory is located in the directory "/src")
    1. >>> import sys
    2. >>> sys.path.append('/src')

launching:
    3. >>> import athenaCL.athenacl
"""

        msgDoc = (
            """\
V. DOCUMENTATION:

For complete documentation, tutorials, and reference, see the athenaCL Tutorial Manual:
%s
"""
            % lang.msgAthDocURL
        )

        msgContact = """\
VI. CONTACT INFORMATION:

Send questions, comments, and bug reports to:
%s
athenaCL development is hosted at GoogleCode:
%s
""" % (
            lang.msgBugReport,
            lang.msgAthDeveloperURL,
        )

        msgCredits = """\
VII. CREDITS and ACKNOWLEDGMENTS:

%s

%s
""" % (
            lang.msgCredits,
            lang.msgTrademarks,
        )

        _divChar = self._divChar
        _divWidth = self._divWidth

        msg = []
        msg.append("%s %s\n" % (lang.msgAth, lang.msgAthCopyright))
        msg.append("%s\n" % (lang.msgLicenseShort))
        msg.append("%s\n\n" % lang.msgAthURL)

        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s %s\n" % (lang.msgAth, athenaObj.athVersion))
        msg.append("%s\n" % athenaObj.athDate)
        msg.append("%s\n" % msgContents)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgPlatDepend)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgSoftDepend)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgQuickStartA)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgQuickStartB)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        #         msg.append('%s\n' % msgAppEnviron)
        #         msg.append('%s\n' % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgInstall)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgCLI)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgIDLE)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgPP)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgDoc)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgContact)
        msg.append("%s\n" % lang.msgDividerAlgo(_divWidth, _divChar))
        msg.append("%s\n" % msgCredits)

        f = open(self.fpReadme, "w")
        f.write("".join(msg))
        f.close()
        print("info.py: writing %s" % self.fpReadme)

    # -----------------------------------------------------------------------||--
    # athenaCL should be installed in python's site-packages;

    # section was 'audio'; changed to 'sound'

    #     def writeDeb(self):
    #         pkgName = "%s_%s_%s.deb" % (lang.msgAth.lower(), self.athVersion, arch)
    #         ctrlFile = """Package: %s
    # Version: %s
    # Section: sound
    # Priority: optional
    # Architecture: all
    # Essential: no
    # Depends: python (>= 2.3)
    # Pre-Depends: python (>= 2.3)
    # Recommends: csound
    # Installed-Size: 1024
    # Maintainer: %s [%s]
    # Provides: %s
    # Description: %s
    # """ % (lang.msgAth.lower(), self.athVersion, lang.msgAuthor,
    #         lang.msgAuthorEmail, lang.msgAth.lower(), lang.msgAthDescShort)

    # -----------------------------------------------------------------------||--
    # fink configuration issues
    # version identified should have revision: athenacl-1.4.2-1

    #     def writeInfo(self, strMd5):
    #         """create a fink installer
    #         strMd5 myst be provided for file pointed to here"""
    #         # %n the name of the current package
    #         # %v the package version
    #         # %p, %P     the prefix where Fink is installed, e.g. /sw
    #         #%i  the full install-phase prefix, equivalent to %d%p
    #         # this is the destination where built, with the
    #         msg = []
    #         msg.append("""Package: %s
    # Version: %s
    # Revision: %s
    # """ % (lang.msgAth.lower(), self.athVersion, self.athRevision))
    #         msg.append("""Maintainer: %s <%s>
    # Homepage: %s
    # """ % (lang.msgAuthor, lang.msgAuthorEmail, lang.msgAthURL))
    #         msg.append("""Depends: python | python-nox
    # """)
    #
    # # Source2: http://easynews.dl.sourceforge.net/sourceforge/athenacl/athenaCL-%s.tar.gz
    # # Source3: http://surfnet.dl.sourceforge.net/sourceforge/athenacl/athenaCL-%s.tar.gz
    #
    #         # modify source string for fink expansions
    #         # downloadTar = lang.msgAthDownloadTar.replace('%s', '%v')
    #         # note that fink flag here will be ignored if not existant on dst system
    #         msg.append("""Source: %s
    # Source-MD5: %s
    # """ % (lang.msgAthDownloadTar, strMd5))
    #
    #         msg.append("""CompileScript: <<
    # %p/bin/python setup.py build
    # <<
    # InstallScript: <<
    # %p/bin/python setup.py install --fink --prefix=%i
    # <<
    # """)
    #
    #         # paths based on local system; update with %p expansion
    #         # build is the last phase, done after compile and install
    #         # prerm is before package is removed or upgraded
    #         postManPath = os.path.join(osTools.findManPath(MANGROUP, 'fink'), MANFILE)
    #         postManPath = postManPath.replace('/sw', '%p')
    #         postBinPath = osTools.findAthBinPath(1)
    #         postBinPath = postBinPath.replace('/sw', '%p')
    #         msg.append("""PreRmScript: <<
    # rm -f %s
    # rm -f %s
    # <<
    # """ % (postBinPath, postManPath))
    #
    #
    #         # defining doc files is required
    #         msg.append("""License: %s
    # DocFiles: README.txt LICENSE.txt
    # """ % lang.msgLicenseName)
    #
    #         # adjust leading capital in description
    #         descShort = (lang.msgAthDescMicroMini[0].upper() +
    #                          lang.msgAthDescMicroMini[1:])
    #         descLong = typeset.wrapText(lang.msgAthDescLong.strip(), 60)
    #         msg.append("""Description: %s
    # DescDetail: <<
    # %s
    # <<
    # """ % (descShort, descLong))
    #
    #         # copy .info file to fink local
    #         dstFink = os.path.join('/sw/fink/dists/local/main/finkinfo',
    #                                       self.fnInfo)
    #         if os.path.exists(dstFink):
    #             osTools.rm(dstFink)
    #         for dst in [self.fpInfo, dstFink]:
    #             print _MOD, 'writing', dst
    #             f = open(dst, 'w')
    #             f.write(''.join(msg))
    #             f.close()
    #
    #         # validate
    #         cmd = 'fink validate %s' % dstFink
    #         os.system(cmd)
    #
    #         # build fink distro
    #         cmd = 'fink build athenacl'
    #         os.system(cmd)
    #
    #         # move to dist folder
    #         src = '/sw/fink/10.4-transitional/local/main/binary-darwin-powerpc/athenacl_%s-1_darwin-powerpc.deb' % self.athVersion
    #         junk, name = os.path.split(src)
    #         fpDocDir = os.path.join(osTools.findAthenaPath(), 'dist')
    #         if not os.path.exists(fpDocDir):
    #             osTools.mkdir(fpDocDir)
    #         dst = os.path.join(fpDocDir, name)
    #         if not os.path.exists(src):
    #             print _MOD, 'ERROR: no .deb file exists'
    #         else:
    #             osTools.mv(src, dst)
    #

    # -----------------------------------------------------------------------||--
    def writeMan(self):
        "writes a man file"

        # need to get flags from athenacl.py w/o falling into
        # interactive session; do this by adding to sys.argv
        environment.printWarn("updating man page")

        # this will start an interepreter instance when run
        sys.argv.append("-e quit confirm")
        from athenaCL.athenacl import flagsRef  # get from w/n module

        # clean garbage from sys.argv
        sys.argv.pop(sys.argv.index("-e quit confirm"))

        # format is 10 june 2004
        timeList = athenaObj.athDate.split(" ")
        timeStr = "%s %s, %s" % (timeList[1], timeList[0], timeList[2])
        # should be June 6, 2000
        msg = []
        msg.append(
            """.\" -*- nroff -*-
.Dd %s
.Dt %s %s URM
.Sh NAME
.Nm %s
.Nd %s"""
            % (
                timeStr,
                lang.msgAth.upper(),
                self.manGroup,
                lang.msgAth.lower(),
                lang.msgAthDescShort,
            )
        )

        msg.append(
            """
.Sh SYNOPSIS
.Nm
.Op Ar options
.Op Ar commands
.Sh DESCRIPTION
%s"""
            % (lang.msgAthDescLong)
        )

        msg.append(
            """
.Sh OPTIONS
.Bl -tag -width flag"""
        )

        for key in list(flagsRef.keys()):
            flagStr = ", ".join(key)  # key is a list
            msg.append("\n.It Cm %s\n" % flagStr)
            msg.append("%s" % flagsRef[key])
        msg.append("\n.El")  # dont end w/ return carriage
        # add homage page tag
        msg.append(
            """
.Sh HOMEPAGE
%s"""
            % (lang.msgAthURL)
        )

        msg.append(
            """
.Sh BUGS
To report bugs, email %s.
.Sh AUTHOR
The original author and current maintainer of 
.Nm
is %s <%s>."""
            % (lang.msgBugReport, lang.msgAuthor, lang.msgAuthorEmail)
        )

        print("info.py: writing %s" % self.fpMan)

        f = open(self.fpMan, "w")
        f.writelines(msg)
        f.close()

    # -----------------------------------------------------------------------||--
    def main(self):
        "writes standard files"
        self.historyScrub()
        self.writeMan()
        self.writeReadme()


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":

    from athenaCL.test import baseTest

    baseTest.main(Test)

    a = InfoManager()
    a.main()
