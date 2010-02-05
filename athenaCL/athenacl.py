#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          athenacl.py
# Purpose:       command line launcher for all athenaCL session types.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--
import sys, os

#-----------------------------------------------------------------||||||||||||--
try: 
    import libATH #assume we are in package dir
except ImportError:
    try: from athenaCL import libATH # if sys.path setup right
    except ImportError: 
        sys.stdout.write('athenaCL package cannot be found.\n')
        sys.exit()
fpLibATH = libATH.__path__[0] # list, get first item
if not os.path.isabs(fpLibATH): #relative path, add cwd
    fpLibATH = os.path.abspath(fpLibATH)
fpSrcDir = os.path.dirname(fpLibATH)
fpPackageDir = os.path.dirname(fpSrcDir)
if fpPackageDir not in sys.path: sys.path.append(fpPackageDir)

#-----------------------------------------------------------------||||||||||||--
from athenaCL.libATH import dialog
from athenaCL.libATH import argTools
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import drawer
from athenaCL.libATH import osTools
from athenaCL.libATH import athenaObj

_MOD = 'athenacl.py'
# check if in idle; this file may call this file again (under idle) and thus
IDLE_ACTIVE = drawer.isIdle()

#-----------------------------------------------------------------||||||||||||--
# reference for all flags and doc strings for each
flagsRef = {('-s',) : 'Takes an argument to determine athenaCL session type: options include "terminal", "idle", "cgi". Default is "terminal".',
                ('-e',) : 'Any single athenaCL command line string can be provided following this flag, to be executed at startup. Any number of these flags can be used to execute multiple commands.',
                ('-q',) : 'Causes athenaCL to provide no text output.',
 ('-v','--version') : 'Display athenaCL version information.',
    ('-h', '--help') : 'Display help text.',}


def helpMsg(athVersionStr, flagsRef):
    """print a help file"""
    msg = []
    msg.append('%s, %s\n' % (athVersionStr, lang.msgAthCopyright))
    msg.append('%s\n' % lang.msgLicenseShort)
    msg.append('%s\n\n%s\n\n' % (lang.msgAthDescLong, lang.msgAthUsage))
    msg.append('Options:\n')
    for key in flagsRef.keys():
        flagStr = ''
        for entry in key:
            flagStr = flagStr + '%s, ' % entry
        if flagStr[-2:] == ', ':
            flagStr = flagStr[:-2]
        msg.append('%s%s: %s\n' % (lang.TAB, flagStr, flagsRef[key]))
    msg.append('\nVisit %s for more information.\n' % 
                             drawer.urlPrep(lang.msgAthURL))
    return ''.join(msg)      
        
#-----------------------------------------------------------------||||||||||||--
sessionType = None # set to none on default
exit = 0 # used to get infor and exit immediatly
verbose = 1 # standard is 1 (0 through 3)
cmdList = None

parsedArgs = argTools.parseFlags(sys.argv, flagsRef)
athVersionStr = 'athenaCL %s' % athenaObj.athVersion
# parse args
for argPair in parsedArgs:
    # only terminal and idle can be launched interactively
    if argPair[0] == '-s':
        if argPair[1] != None:
            option = argPair[1]
            if option in ['terminal', 'idle', 'cgi']: # cgi just for test
                sessionType = option
            else: sessionType = None # get default
    elif argPair[0] == '-e': 
        if cmdList == None: cmdList = []
        cmdList.append(argPair[1])
    elif argPair[0]  in ['-q', '--quiet']: 
        verbose = 0 # 2 is no output
    elif argPair[0] in ['-v', '--version']:
        dialog.msgOut(('%s\n' % athVersionStr))
        exit = 1 # exit after getting info
    elif argPair[0] in ['-h', '--help']:
        dialog.msgOut(helpMsg(athVersionStr, flagsRef))
        exit = 1 # exit after print help
        
if exit: 
    sys.exit() # help, version, exit after command function

# command flag over-rides
if IDLE_ACTIVE: # regardless of platform, always force these options
    sessionType = 'terminal' # session shold look like a terminal
else: # idle not active, get default session if not set
    if os.name == 'posix':
        if sessionType == None: sessionType = 'terminal'
    else: # all win plats
        if sessionType == None: # not already selected
            if dialog.askYesNo('start athenacl in IDLE?'):
                sessionType = 'idle'
            else: sessionType = 'terminal'

#-----------------------------------------------------------------||||||||||||--
def launchIdle():
    # flag for athenacl to now its an idle session
    # passing -s, 'terminal' here does not work...
    # this will cal this same module again, but under idle, w/ terminal session
    sys.argv = ['python', '-t', 'athenacl via IDLE', 
                    '-c', 'import athenaCL.athenacl',] # force threads off
    # attribute error is rause when idle quits by closing window mid proc
    # cant avoid by catching error; traceback start in the framework
    try:
        import idle
    except ImportError:
        idlePath = osTools.findIdle()
        if idlePath == None:
            dialog.msgOut('idle cannot be found\n')
            return None
        sys.path.append(idlePath)
        dialog.msgOut('launching idle from:\n%s\n' % idlePath)
        try:
            import idle
        except (ImportError, AttributeError):
            return None
    except AttributeError: # happens on session interrupt
        return None
    #temp = dialog.askStr(lang.msgReturnToExit)

def launch(sessionType, verbose, cmdList):
    # general launch procedure
    interp = athenaObj.Interpreter(sessionType, verbose)
    interp.cmdLoop(cmdList)
        
#-----------------------------------------------------------------||||||||||||--
# start sessions
if sessionType == 'terminal':
    launch(sessionType, verbose, cmdList)      
elif sessionType == 'idle': # only for loading from cmd line
    launchIdle() # will start session as 'terminal force'



