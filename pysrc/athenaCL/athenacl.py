#!/usr/local/bin/python
# -----------------------------------------------------------------||||||||||||--
# Name:          athenacl.py
# Purpose:       command line launcher for all athenaCL session types.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--
import sys

from athenaCL.libATH import dialog
from athenaCL.libATH import argTools
from athenaCL.libATH import language

lang = language.LangObj()
from athenaCL.libATH import drawer
from athenaCL.libATH import athenaObj


# reference for all flags and doc strings for each
flagsRef = {
    (
        "-s",
    ): 'Takes an argument to determine athenaCL session type: options include "terminal", "idle", "cgi". Default is "terminal".',
    (
        "-e",
    ): "Any single athenaCL command line string can be provided following this flag, to be executed at startup. Any number of these flags can be used to execute multiple commands.",
    ("-q",): "Causes athenaCL to provide no text output.",
    ("-v", "--version"): "Display athenaCL version information.",
    ("-h", "--help"): "Display help text.",
}


def main():
    sessionType = "terminal"  # set to none on default
    exit = 0  # used to get infor and exit immediatly
    verbose = 1  # standard is 1 (0 through 3)
    cmdList = None

    parsedArgs = argTools.parseFlags(sys.argv, flagsRef)
    athVersionStr = "athenaCL %s" % athenaObj.athVersion

    # parse args
    for argPair in parsedArgs:
        # only terminal and idle can be launched interactively
        if argPair[0] == "-s":
            if argPair[1] != None:
                option = argPair[1]
                if option in ["terminal", "cgi"]:  # cgi just for test
                    sessionType = option
                else:
                    sessionType = None  # get default
        elif argPair[0] == "-e":
            if cmdList == None:
                cmdList = []
            cmdList.append(argPair[1])
        elif argPair[0] in ["-q", "--quiet"]:
            verbose = 0  # 2 is no output
        elif argPair[0] in ["-v", "--version"]:
            dialog.msgOut(("%s\n" % athVersionStr))
            exit = 1  # exit after getting info
        elif argPair[0] in ["-h", "--help"]:
            dialog.msgOut(helpMsg(athVersionStr, flagsRef))
            exit = 1  # exit after print help

    if exit:
        sys.exit()  # help, version, exit after command function

    launch(sessionType, verbose, cmdList)


def helpMsg(athVersionStr, flagsRef):
    """print a help file"""
    msg = []
    msg.append("%s, %s\n" % (athVersionStr, lang.msgAthCopyright))
    msg.append("%s\n" % lang.msgLicenseShort)
    msg.append("%s\n\n%s\n\n" % (lang.msgAthDescLong, lang.msgAthUsage))
    msg.append("Options:\n")
    for key in list(flagsRef.keys()):
        flagStr = ""
        for entry in key:
            flagStr = flagStr + "%s, " % entry
        if flagStr[-2:] == ", ":
            flagStr = flagStr[:-2]
        msg.append("%s%s: %s\n" % (lang.TAB, flagStr, flagsRef[key]))
    msg.append("\nVisit %s for more information.\n" % drawer.urlPrep(lang.msgAthURL))
    return "".join(msg)


def launch(sessionType, verbose, cmdList):
    # general launch procedure
    interp = athenaObj.Interpreter(sessionType, verbose)
    interp.cmdLoop(cmdList)


main()
