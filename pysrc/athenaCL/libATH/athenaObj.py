# -----------------------------------------------------------------||||||||||||--
# Name:          athenaObj.py
# Purpose:       defines the following objects:
#                    External: find all necessary files, prefs, xml data
#                    AthenaObject: data container for athena object
#                    Terminal: object interface for terminal display
#                    Interpreter: object for parsing commands, logging, help
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import sys, os, time, random, traceback, http.client, urllib.request, urllib.parse, urllib.error
import unittest

athVersion = "2.0.0"
athBuild = "2024.04.10"
athDate = "4 October 2024"  # human readable version
__version__ = athVersion
__license__ = "GPL"


# athenaObj.py needs correct dir information for writing
# a file (prefs) and loading demos, and opening .xml and other resources
# External is sometimes called by itself, needs to find correct paths
# this checks for correct path access, attempts to mangle sys.path to fix
# imports if necssary
# -----------------------------------------------------------------||||||||||||--
try:
    from . import libTM  # assume we are in libATH
except ImportError:
    try:
        from athenaCL.libATH import libTM
    except ImportError:
        sys.stdout.write("athenaCL package cannot be found.\n")
        sys.exit()

from athenaCL.libATH import argTools
from athenaCL.libATH import command
from athenaCL.libATH import dialog
from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import help
from athenaCL.libATH import ioTools  # needed for bkwdCompat object
from athenaCL.libATH import rhythm  # needed for timing
from athenaCL.libATH import language

lang = language.LangObj()
# from athenaCL.libATH import SC
from athenaCL.libATH.libOrc import orc
from athenaCL.libATH.libTM import texture  # needed for test script
from athenaCL.libATH import clone  # needed for proc_AUtest

# objects not stored in ao, but nameing data needed
from athenaCL.libATH import eventList

_MOD = "athenaObj.py"
from athenaCL.libATH import prefTools

environment = prefTools.Environment(_MOD)


# -----------------------------------------------------------------||||||||||||--
class External(object):
    """used to remaintain remote files used by the AthenaObject
    handles preferences (stored in xml) and error log files
    also reloads textures, gets path preferences, orchestra files
    """

    def __init__(self, termObj=None):
        """termObj used to provide session type information

        >>> a = External()
        """
        if termObj != None:
            self.termObj = termObj
            self.sessionType = termObj.sessionType
        else:
            self.termObj = None
            self.sessionType = "terminal"  # standard default


    def updateAll(self, verbose=0):
        """does all init updates, called whenever an ao is created"""
        self._updateLogs()
        self.updatePrefs()


    def _updateLogs(self):
        """update path for error log files"""
        if os.name == "mac":
            logFileName = "athenacl-log.txt"
        elif os.name == "posix":
            logFileName = ".athenacl-log"  # make hidden file
        else:  # win or other
            logFileName = ".athenacl-log.txt"
        self.logPath = os.path.join(drawer.getPrefsDir(), logFileName)


    def logWrite(self, dataLines):
        """for adding an error to= the error lig"""
        if os.path.exists(self.logPath):  # append lines
            f = open(self.logPath, "r")
            logLines = f.readlines()
            f.close()
        else:
            logLines = []
        for line in dataLines:
            logLines.append(line)
        # add a separator b/n log entries
        logLines.append("\n")
        f = open(self.logPath, "w")
        f.writelines(logLines)
        f.close()

    def _logParse(self):
        """open the log file and parse it into useful data"""
        charSep = "-"

        f = open(self.logPath, "r")
        logLines = f.readlines()
        f.close()
        bundle = {}
        i = -1  # first will be zero
        for line in logLines:  # in order, ERROR always comes first
            if line.strip() == "":
                continue
            if line.startswith("ERROR"):
                i = i + 1  # increment
                bundle[i] = []  # create new list
            bundle[i].append(line)
        # convert to value pairs
        param = {}
        for group in list(bundle.keys()):  # order here does not matter
            i = 0  # first will be zero
            for field in bundle[group]:  # order here matters
                key = "%s%s%s" % (group, charSep, i)
                param[key] = field
                i = i + 1
        return param

    def logCheck(self):
        """test to see if a log exists; called when quitting to see
        if a log send should be done"""
        if os.path.exists(self.logPath):
            return 1  # no log, do nothing
        else:
            return 0

    def _logDelete(self):
        """delete the error log, assuming that it is empty"""
        os.remove(self.logPath)

    def logSend(self):
        """attempt to submit a log file"""
        paramRaw = self._logParse()
        paramRaw["stateNext"] = "8"  # state 8 is bug processing
        params = urllib.parse.urlencode(paramRaw)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
        }
        try:
            conn = http.client.HTTPConnection(lang.msgCgiDomain)
            conn.request("POST", lang.msgCgiURL, params, headers)
            connect = 1
        except:  # no connection active
            connect = 0
        if connect:
            try:
                response = conn.getresponse()
            except:  # some other failure is possible here
                print("unknown connection error.")
                return None
            if response.status == 200:  # good
                data = response.read()
                dataLines = data.split("\n")
                print(dataLines[0])
                self._logDelete()  # delete old log
            else:
                environment.printWarn(["http error:", response.status])

            conn.close()
            return 1
        else:
            return None  # nothing happened

    def onlineVersionFetch(self):
        """if online, check current version
        returns None if not available"""
        try:  # read number of chars lines 1.1.1.1000.10.10
            webpage = urllib.request.urlopen(drawer.urlPrep(lang.msgVersionURL)).read(
                24
            )
        except IOError as e:  # cant get online
            webpage = None
        except:  # all others
            webpage = None
        if webpage != None:
            versionStr = webpage.strip()
            return argTools.Version(versionStr)  # return object
        else:
            return None

    # -----------------------------------------------------------------------||--
    def updatePrefs(self, forcePath=None):
        """check for prefs, update and add if missing"""
        prefsFileName = drawer.getPrefsName()

        if forcePath != None:
            self.prefDict = prefTools.getXmlPrefDict(forcePath)
            self.prefDict = prefTools.updatePrefDict(self.prefDict, os.name)
            prefTools.writePrefDict(drawer.getPrefsPath(), self.prefDict)

        elif self.sessionType != "cgi":  # cgi cant use any prefs
            prefDirContent = os.listdir(drawer.getPrefsDir())
            createNewPrefs = 0
            if prefsFileName in prefDirContent:
                self.prefDict = prefTools.getXmlPrefDict(drawer.getPrefsPath())
                self.prefDict = prefTools.updatePrefDict(self.prefDict, os.name)
                prefTools.writePrefDict(drawer.getPrefsPath(), self.prefDict)
            else:  # new prefs on first start, or after deleting
                createNewPrefs = 1
            if createNewPrefs:
                self.prefDict = prefTools.getDefaultPrefDict(os.name)
                prefTools.writePrefDict(drawer.getPrefsPath(), self.prefDict)

        elif self.sessionType == "cgi":  # if cgi session, only use pref dict
            self.prefDict = prefTools.getDefaultPrefDict(os.name)

    def writePref(self, category, key, value):
        """writes new value or pref file"""
        from athenaCL.libATH import prefTools

        self.prefDict[category][key] = value
        if self.sessionType != "cgi":  # dont write if cgi
            prefTools.writePrefDict(drawer.getPrefsPath(), self.prefDict)

    def getPref(self, category, key, evaluate=0):
        """returns value of a pref
        some prefs are lists or numbers and need to be evaluated"""
        strPref = self.prefDict[category][key]
        if not evaluate:
            return strPref
        else:  # this may raise an exception
            evalPref = eval(self.prefDict[category][key])
            if drawer.isList(evalPref):  # make sure it is a list, not tuple
                evalPref = list(evalPref)
            return evalPref

    def getPrefGroup(self, category):
        """get an entire pref group, and load into a dictionary
        useful passing app preferences from external to osTools"""
        d = {}
        for key in self.prefDict[category]:
            d[key] = self.prefDict[category][key]
        return d


    def getFilePathAudio(self):
        """returns a list of file paths for samples"""
        userAudioPath = self.getPref("athena", "fpAudioDir")
        return [userAudioPath]


    def getVisualMethod(self, status="normal"):
        """checks to see if vis methods have been updated
        if not avail, updates
        this is a bit of a time suck and should be done once
        per session
        status == 'init' allows the attibute self.visualMethod
        to be initialized to None, updates on next call
        visual methodis a list containing all avalable methods
        """
        if status == "init":
            self.visualMethod = None  # set to none, but dont update until called
        else:  # checks guis: a speed clog on startup
            # done only if set to none, once per sess
            if self.visualMethod == None:
                self.visualMethod = drawer.imageFormats()
            return self.visualMethod


class AthenaObject(object):
    """methods for internal processsing of done with command objecst from
    command.py
    includes internal functions for processing objects
    athenaCmd.py wraps and exposes methods of this class
    """

    def __init__(self, termObj=None):
        """creates all attributes of the athenaObject
        update object handles finding all modules and creating util objects
        command.py operates upon these attributes and sub-objects
        also handles reference of commands, getting help from commands, display

        information/objects that need to be accessed both in Interpreter (holds
        one permanent ao) and many command objects (one ao passed to them)

        >>> a = AthenaObject()
        """
        self.athVersion = athVersion
        self.athBuild = athBuild
        self.versionObj = argTools.Version("%s.%s" % (self.athVersion, self.athBuild))
        self.athDate = athDate

        # defaut terminal handler, from Interpreter
        self.termObj = self._configTerminal(termObj)

        # possible session types are 'terminal', 'idle', 'cgi';
        # these methods initializes external modules and resources
        self.external = External(self.termObj)
        self.external.updateAll("on")  # msgs on
        # self.external.reloadTextures()
        self.external.getVisualMethod("init")  # prep, dont resolve

        # utility objects
        self.help = help.HelpDoc(self.termObj)  # pass ref termObj
        self.backward = ioTools.BackwardsCompat()

        # data and objects saved with AO
        # ATHENA DATA
        self.author = ""  # stored for a loaded athenaObj
        self.tniMode = 0  # true == TnI, false == Tn
        # PATH DATA
        # self.activeSetMeasure = 'ASIM' # default
        self.pathLib = {}
        self.activePath = ""
        # TEXTURE DATA
        self.activeTextureModule = "LineGroove"  # name of class
        self.textureLib = {}
        self.activeTexture = ""  # name of
        # CLONE DATA
        self.cloneLib = clone.CloneManager()  # added post 1.3
        self.midiTempo = 120  # default value, changed with TEmidi, added 1.1

        # these are stored here, with with project;
        # audioFormat is stored in user prefs
        self.audioChannels = 2  # default, saved w/ ao
        self.audioRate = 44100  # default, saved w/ ao

        # this may be init from a pref; but loaded and stored in ao
        self.orcObj = None  # initialized from setEventMode
        self.activeEventMode = None
        # cannot store an em object, contains ao, but must instant orc
        # sets self.activeEventMode and self.orcObj
        self.setEventMode(self.external.getPref("athena", "eventMode"), "csoundNative")
        # local information either (1) not saved in AO (2) temporary data or
        # (3) derived from file based preferences

        # temporary session data, scoFP and others
        # stores outputs completed after ELn; can be used to determine what
        # files were actually made
        self.aoInfo = {}

        # list of paths: built in audio dir, and user-defined dir
        self.aoInfo["fpAudioDirs"] = self.external.getFilePathAudio()
        # self.fpAudioDirs = self.external.getFilePathAudio()
        self.aoInfo["fpLastDir"] = self.external.getPref("athena", "fpLastDir")
        # self.fpLastDir = self.external.getPref('athena', 'fpLastDir')
        self.aoInfo["fpLastDirEventList"] = self.external.getPref(
            "athena", "fpLastDirEventList"
        )
        # self.fpLastDirEventList = self.external.getPref('athena', 'fpLastDirEventList')

        self.aoInfo["refreshMode"] = self.external.getPref("athena", "refreshMode", 1)
        self.aoInfo["cursorToolOption"] = self.external.getPref(
            "athena", "cursorToolOption"
        )
        self.aoInfo["version"] = self.athVersion
        self.aoInfo["outComplete"] = []  # will be filled after creating files
        self.aoInfo["history"] = {}  # store command history # mod in Interpreter

        # static data and strings shared by Interpreter and Command objects
        self.promptSym = "::"  # symbol used for prompt
        # this is directory of main commands presented to user
        # any other commands are considered hidden
        self.cmdDict = {
            "piCmd": (
                "PathInstance",
                "PIn(new)",
                "PIcp(copy)",
                "PIrm(remove)",
                "PIo(select)",
                "PIv(view)",
                "PIe(edit)",
                "PIdf(duration)",
                "PIls(list)",
                "PIh(hear)",
                "PIret(retro)",
                "PIrot(rot)",
                "PIslc(slice)",
            ),
            "tmCmd": (
                "TextureModule",
                "TMo(select)",
                "TMv(view)",
                "TMls(list)",
                "TMsd(seed)",
            ),
            "tpCmd": (
                "TextureParameter",
                "TPls(list)",
                "TPv(select)",
                "TPmap(map)",
                "TPsd(seed)",
                "TPe(export)",
            ),
            "tiCmd": (
                "TextureInstance",
                "TIn(new)",
                "TIcp(copy)",
                "TIrm(remove)",
                "TIo(select)",
                "TIv(view)",
                "TIe(edit)",
                "TIls(list)",
                "TImode(mode)",
                "TImute(mute)",
                "TIdoc(doc)",
                "TImap(map)",
                "TImidi(midi)",
            ),
            "tcCmd": (
                "TextureClone",
                "TCn(new)",
                "TCcp(copy)",
                "TCrm(remove)",
                "TCo(select)",
                "TCv(view)",
                "TCe(edit)",
                "TCls(list)",
                "TCmute(mute)",
                "TCmap(map)",
            ),
            "ttCmd": ("TextureTemperament", "TTls(list)", "TTo(select)"),
            "teCmd": (
                "TextureEnsemble",
                "TEv(view)",
                "TEe(edit)",
                "TEmap(map)",
                "TEmidi(midi)",
            ),
            "eoCmd": (
                "EventOutput",
                "EOls(list)",
                "EOo(select)",
                "EOrm(remove)",
            ),
            "emCmd": (
                "EventMode",
                "EMls(list)",
                "EMo(select)",
                "EMv(view)",
                "EMi(inst)",
            ),
            "elCmd": (
                "EventList",
                "ELn(new)",
                "ELw(save)",
                "ELv(view)",
                "ELh(hear)",
                "ELr(render)",
                "ELauto(auto)",
            ),
            #       'cpCmd':('CsoundPreferences',
            #                   'CPff(format)', 'CPch(channel)'),
            "aoCmd": (
                "AthenaObject",
                "AOw(save)",
                "AOl(load)",
                "AOmg(merge)",
                "AOrm(remove)",
            ),
            "ahCmd": ("AthenaHistory", "AHls(list)", "AHexe(execute)"),
            "auCmd": (
                "AthenaUtility",
                "AUsys(system)",
                "AUdoc(docs)",
                "AUup(update)",
                "AUbeat(beat)",
                "AUpc(pitch)",
                "AUmg(markov)",
                "AUma(markov)",
                "AUca(automata)",
            ),
            "apCmd": (
                "AthenaPreferences",
                "APdir(directory)",
                "APea(external)",
                "APa(audio)",
                "APgfx(graphics)",
                "APcurs(cursor)",
                "APr(refresh)",
                "APwid(width)",
            ),
        }

        self.cmdOrder = [
            None,
            "piCmd",  #'psCmd', 'pvCmd',
            None,
            "tmCmd",
            "tpCmd",
            "tiCmd",
            "tcCmd",
            "ttCmd",
            "teCmd",
            None,
            "eoCmd",
            "emCmd",
            "elCmd",
            None,
            "apCmd",
            "ahCmd",
            "auCmd",
            "aoCmd",
        ]
        # two-letter prefix for all athenaCL commands
        self.cmdPrefixes = []  # store w/ caps
        for key in self.cmdDict:
            self.cmdPrefixes.append(key[:2].upper())  # first two chars
        # this is only used in the cmdManifest method below
        self._cmdSpecial = [
            "w",
            "c",
            "r",
            "cmd",
            "py",
            "quit",
            "q",
            "help",
            "shell",
        ]
        # store a list of all commands
        self.cmdRef = self.cmdManifest()
        self.cmdRef.sort()

    def prefixCmdGroup(self, prefix):
        """for a given prefix will return a list of
        cmds and a list of their names
        only returns heirarchical commands, never special commands

        >>> a = AthenaObject()
        >>> a.prefixCmdGroup('tmCmd')
        (['TMo', 'TMv', 'TMls'], ['select', 'view', 'list'])
        >>> a.prefixCmdGroup('teCmd')
        (['TEv', 'TEe', 'TEmap', 'TEmidi'], ['view', 'edit', 'map', 'midi'])
        """
        if prefix not in list(self.cmdDict.keys()):
            prefix = prefix.lower() + "Cmd"
        if prefix in list(self.cmdDict.keys()):
            cmdNameList = self.cmdDict[prefix]
            cmdList = []
            nameList = []
            for name in cmdNameList:
                ## this ignores things that are not cmds, like heading names
                if name.find("(") < 0:
                    continue
                name = name.replace("(", " ")
                name = name.replace(")", " ")
                cmdStr, nameStr = name.split()  # always into two things
                cmdList.append(cmdStr)
                nameList.append(nameStr)
            return cmdList, nameList
        else:
            return None

    def prefixName(self, prefix):
        """
        >>> a = AthenaObject()
        >>> a.prefixName('tm')
        'TextureModule'
        """
        return self.cmdDict[prefix.lower() + "Cmd"][0]  # 0 gets title

    def _configTerminal(self, termObj):
        """Provide a default Terminal if not provided"""
        if termObj == None:
            return Terminal("terminal")
        else:
            return termObj

    # -----------------------------------------------------------------------||--
    # managing and displaying command names

    def cmdDisplay(self):
        """get heirarchical display, scaled to screen widthw
        used for cmd display

        >>> a = AthenaObject()
        >>> post = a.cmdDisplay()
        """
        w = self.termObj.w
        msg = []
        msg.append("athenaCL Commands:\n")
        for cmdName in self.cmdOrder:
            if cmdName == None:  # none is a divider
                msg.append(lang.DIVIDER * w)
            else:
                msg.append(
                    typeset.formatEqCol("", self.cmdDict[cmdName], 20, w, outLine=True)
                )
        return "".join(msg)

    def cmdCorrect(self, line):
        """Acts as an athenaCL cmd parser: Capitalizes and corrects first part of user cmd strings called within cmdExecute. Does not deal with special commands like q, quit, cmd, and others.

        If `checkFirstArg` is True, the first arg in the string is assumed to be a command.

        >>> a = AthenaObject()
        >>> a.cmdCorrect('tils')
        'TIls'
        >>> a.cmdCorrect('TILS')
        'TIls'
        >>> a.cmdCorrect('TILS extra Command MAY be 3 4 5 345,1.234,345')
        'TIls extra Command MAY be 3 4 5 345,1.234,345'
        >>> a.cmdCorrect('aol A file With caps')
        'AOl A file With caps'
        >>> a.cmdCorrect('tin BLOB 234')
        'TIn BLOB 234'
        >>> a.cmdCorrect('apEA mp /Applications/QuickTime Player.app')
        'APea mp /Applications/QuickTime Player.app'
        >>> a.cmdCorrect('apea mp /Applications/QuickTime Player.app')
        'APea mp /Applications/QuickTime Player.app'
        >>> a.cmdCorrect('tin     BLOB      234   23.235')
        'TIn     BLOB      234   23.235'
        """
        if line == None:
            return None

        line = line.strip()
        if len(line) <= 1:  # short command get no change?
            return line

        # if first two letters lower case, make upper
        if " " not in line:  # no spaces or extra args
            prefix = line[:2].upper()
            postfix = line[2:].lower()
            postarg = ""
        else:
            lineSplit = line.split(" ")
            cmdStr = lineSplit[0]  # must be first
            prefix = cmdStr[:2].upper()
            postfix = cmdStr[2:].lower()
            # need leading space, need to return to a singel string
            postarg = " " + " ".join(lineSplit[1:])  # all the rest

        if prefix in self.cmdPrefixes:  # check for lower case
            newPrefix = prefix
            line = newPrefix + postfix + postarg
        # otherwise line stays the same
        return line

    def cmdManifest(self):
        """get all commands from command.py;

        >>> a = AthenaObject()
        >>> post = a.cmdManifest()
        """
        cmdList = dir(command)  # get listing from module
        cmdFilter = []
        for entry in cmdList:
            if (
                entry[0:2] in self.cmdPrefixes
                and entry[0].isupper()
                and entry[1].isupper()
                and len(entry) > 2
                and entry.find("funct") < 0
                and entry.find("class") < 0
            ):  # remove modules imported
                if entry[-1] == "_":  # some commands have tag at end
                    cmdFilter.append(entry[:-1])
                else:
                    cmdFilter.append(entry)
            elif entry in self._cmdSpecial:  # non-standard command names
                cmdFilter.append(entry)
        cmdFilter.sort()
        return cmdFilter

    def cmdDocManifest(self):
        """gets all commands by looking in class attributes
        this listing includes hidden commands and commands not
        getAllCmds, formerly

        >>> a = AthenaObject()
        >>> post = a.cmdDocManifest()
        """
        cmdsDoc = []
        cmdsUndoc = []
        allHelpTopics = self.help.listCmdDoc()
        for cmd in self.cmdRef:  # check against all commands in command.py
            if cmd in allHelpTopics:  # command has documentation
                cmdsDoc.append(cmd)
                allHelpTopics.remove(cmd)  # remove from all help topics
            else:  # command without any help
                cmdsUndoc.append(cmd)
        # after checking all, remaining topics are general help topics
        # these are not really used here
        helpTopics = allHelpTopics  # all that remain
        return cmdsDoc, cmdsUndoc, helpTopics

    def prefixMatch(self, prefix, usrStr):
        """will attempt to match a user string to a command, knowing the prefix
        that command will be found in. if an PI command, user can enter both v or
        PIv. returns the complete command string, or unmodified if no match

        >>> a = AthenaObject()
        >>> a.prefixMatch('pi', 'v')
        'PIv'
        >>> a.prefixMatch('pi', 'view')
        'PIv'
        >>> a.prefixMatch('pi', 'piv')
        'PIv'
        """
        if usrStr == None:
            return None
        prefix = prefix.upper()
        usrStr = self.cmdCorrect(usrStr)
        result = self.prefixCmdGroup(prefix.lower() + "Cmd")
        if result == None:  # bad prefix
            return usrStr
        else:
            cmds, nameList = result

        if usrStr in cmds:  # complete match
            pass  # its good
        elif prefix + usrStr.lower() in cmds:
            usrStr = prefix + usrStr.lower()
        elif len(usrStr) >= 2:
            i = 0
            for cmdShortName in nameList:
                if usrStr.lower() == cmdShortName.lower():
                    usrStr = cmds[i]
                i = i + 1
        return usrStr

    # -----------------------------------------------------------------------||--
    # tools for version checking

    def compareVersion(self, versionOther=None):
        """compare version to current version
        version is a string

        >>> a = AthenaObject()
        >>> a.compareVersion(argTools.Version('99.0.0'))
        ('major', '99.0.0')
        """
        if versionOther == None:  # assume we want to compare to online
            versionOther = self.external.onlineVersionFetch()
            if versionOther == None:
                return None, None  # if not online

        if self.versionObj == versionOther:  # the same version
            status = "current"
        elif versionOther > self.versionObj:  # other is more recent
            if versionOther.point > self.versionObj.point:
                status = "major"  # major update is point
            else:  # just the dates are different
                status = "minor"
        else:  # this version is more up to date than other
            status = "current"

        if status == "minor":
            versionStr = versionOther.repr("dot", 1)
        elif status == "major":
            versionStr = versionOther.repr("dot", 0)  # leave out date info
        elif status == "current":
            versionStr = self.versionObj.repr("dot", 0)
        return status, versionStr

    def timeSinceLastVersionCheck(self):
        """return seconds since last started"""
        tLast = self.external.getPref("athena", "tLastVersionCheck")
        try:
            tLast = float(tLast)
        except (ValueError, TypeError, SyntaxError):
            tLast = 0  # set at zero
        tNow = time.time()
        dif = round(abs(tNow - tLast), 1)
        # print 'time since last version check %s\n' % dif
        return dif

    # -----------------------------------------------------------------------||--
    # these are used in error messages, AUsys

    def osStr(self):
        return "%s.%s" % (os.name, sys.platform)

    def pyStr(self):
        major, minor, micro, level, serial = sys.version_info
        return "%i.%i.%i.%s" % (major, minor, micro, level)

    def aoStr(self, fmt="dot", date=1):
        # formats can be dot or human
        return self.versionObj.repr(fmt, 1)

    def infoStr(self):
        """used in sending error message w/ data stored in aoInfo"""
        headStr = "%s-%s-%s" % (
            self.osStr(),
            self.pyStr(),
            self.aoStr(),
        )
        return headStr

    # -----------------------------------------------------------------------||--
    # methods to maintain internal utility objects

    def setEventMode(self, usrStr, default=None):
        """
        >>> a = AthenaObject()
        >>> a.setEventMode('m')
        """
        # print _MOD, usrStr
        usrStr = eventList.eventModeParser(usrStr)
        # in the case that a bad eventMode was stored
        if usrStr == None and default != None:
            usrStr = default
        assert usrStr != None
        self.activeEventMode = usrStr
        self.orcObj = orc.factory(eventList.selectEventModeOrc(self.activeEventMode))

    def setPreference(self, filePath):
        """set the preference file to an arbitraray path
        this is used for automated image generation in documentation"""
        self.external.updatePrefs(filePath)  # msgs on


# -----------------------------------------------------------------||||||||||||--
# this term handling thanks in part to avkutil.py
class Terminal(object):
    """terminal management.
    represents basic screen presentation issues, even w/o a tty
    size - return height, width of the terminal
    self.termLive determines if the term is in a unix that can get size
    if not, returs default width
    """

    def __init__(self, sessionType="terminal"):
        """possible session types are 'terminal', 'idle', 'cgi'

        >>> a = Terminal()
        """
        self.sessionType = sessionType
        # try to import readline
        try:
            import readline
        except ImportError:
            pass  # not available on every platform
        # determine if interface is interactive or nots
        if sessionType in ["terminal", "idle"]:
            self.interact = 1
        else:  # 'cgi' is not interactive
            self.interact = 0
        # determine if term is live or dead
        if sessionType == "terminal":
            try:
                global termios
                import termios

                self.termLive = 1
            except ImportError:
                self.termLive = 0
        elif sessionType in ["cgi", "idle"]:
            self.termLive = 0
        # defaults spacings
        self.defaultW = 72  # for plats that dont have termio
        self.defaultH = 24
        self.cursesTest = 0  # bool if curses test has been completed
        # do session type adjustments on default sizes
        if sessionType == "cgi":
            self.defaultW = 58

    def clear(self):
        """Clear screen."""
        if self.termLive:
            # replace this with backspace in dialog.py
            os.system("clear")

    def _sizeCurses(self):
        """get size from curses: note, using this tweaks the terminal environment
        and reduces the performance of /b animations. only use when abs necessary
        """
        self.cursesTest = 1  # only run this method once
        if self.termLive:
            try:  # as list ditch test, load curses to get size
                import curses

                curses.initscr()
                self.cursesH, self.cursesW = curses.LINES, curses.COLS
                curses.endwin()
                del curses
            except ImportError:
                self.cursesW = None  # try to get size at init
                self.cursesH = None  # from curses if around

    def size(self):
        """Return terminal size as tuple (height, width).
        this is called once with each command, updated size

        >>> a = Terminal()
        >>> post = a.size()
        """
        if self.termLive:
            h, w = self.defaultH, self.defaultW
            try:
                import struct, fcntl

                h, w = struct.unpack(
                    "hhhh", fcntl.ioctl(0, termios.TIOCGWINSZ, "\000" * 8)
                )[0:2]
            except:  # get size from curses if available; last ditch
                if not self.cursesTest:
                    self._sizeCurses()  # run curses method only if not yet run once
                if self.cursesW != None and self.cursesH != None:
                    h, w = self.cursesH, self.cursesW
        else:  # if no term active, get default
            h, w = self.defaultH, self.defaultW
        return h, w

    def __getattr__(self, name):
        """provode interface as attributes"""
        h, w = self.size()
        if name == "h":
            return h
        elif name == "w":
            return w
        else:
            raise AttributeError

    def setWidth(self, width):
        self.defaultW = width
        self.termLive = 0  # disables using termios

    def setHight(self, height):
        self.defaultH = height


# -----------------------------------------------------------------||||||||||||--
# this Interpreter is based on Python cmd.py


class Interpreter(object):
    """command line envonment to interact with athenaObj.py
    useful for developing parameter objects and textures

    verbose: determine amount of messages given back and forth
        0: quite output: nothign returned
        1: return msg, no warning
        2: return msg, give warnings, errors,

    >>> a = Interpreter()
    """

    def __init__(self, sessionType="terminal", verbose=0):

        # instance of athenaObj class, where all athena processing takes place
        self.sessionType = sessionType  # can be: terminal, idle, Tkinter, cgi
        self.verbose = verbose  # determine output level
        # sets echoing of command lines; prints commands
        # this is used when scripting and you want to see what commands are fired
        self.echo = 0
        # create objects
        self.termObj = Terminal(self.sessionType)
        self.ao = AthenaObject(self.termObj)
        self.athVersion = self.ao.athVersion
        self.athBuild = self.ao.athBuild
        # special handling for threads
        # self.threadAble, threadStr = self._testThreads(threadAble)
        # self.pollDur = .25 # time between polls in seconds

        self.versionCheckWait = rhythm.TimeValue.sPerDay * 28  # every 28 days
        # self.cmdqueue    = [] # not used

        # these are just used for fun
        self._emptyCount = 0  # count empty lines returned
        self._blankCount = 0  # count blank lines returned

        self.cursorToolConvert = self._getCursorToolConvert()
        self._updatePrompt()  # creates self.prompt
        athTitle = "\n" + "athenaCL %s (on %s via %s)\n" % (
            self.athVersion,
            sys.platform,
            self.sessionType,
        )
        # two returns required after changes to line wrapping function
        self.intro = athTitle + lang.msgAthIntro + "\n\n"

    # -----------------------------------------------------------------------||--
    def out(self, msg):
        """main output filter for all text displays
        all text output, when using the intereter, passes through here
        if verbosity set to 0, not output is given at all
        """
        if self.verbose >= 1:
            dialog.msgOut(msg, self.termObj)

    # -----------------------------------------------------------------------||--
    def _getCmdClass(self, cmd):
        """gets a reference to command object; this may get modules that
        are imported into the command module; this is a problem"""
        # some cmds strings cannot be properly filtered unles directly avoided
        # lang pbject will print an error if an attr is not found
        if cmd in ["lang"]:
            return None
        try:
            func = getattr(command, cmd)  # from command module, get class
        except AttributeError:
            func = None
        if drawer.isMod(func):  # if a module, not a command object, do not run
            func = None
        # all cmd sub-class must have these methods
        elif not hasattr(func, "do") and not hasattr(func, "undo"):
            func = None
        return func

    def _proc(self, cmdObj, data):
        """gets a processor, only used for sub commands

        >>> a = Interpreter()
        >>> from athenaCL.libATH import command
        >>> ao = AthenaObject()
        >>> b = command.q(ao)
        >>> a._proc(b, 'confirm')
        -1
        """
        func = getattr(self, "proc_" + cmdObj.cmdStr)
        return func(data)

    def _lineCmdArgSplit(self, line):
        """take a user input line and parse into cmd and arg
        does special character translations
        handles specian commands like SC by adding underscore

        >>> a = Interpreter()
        >>> a._lineCmdArgSplit('? test')
        ('help', 'test')
        >>> a._lineCmdArgSplit('pin a 2,3,4')
        ('pin', 'a 2,3,4')

        >>> a._lineCmdArgSplit('pin TEST CAPS')
        ('pin', 'TEST CAPS')

        >>> a._lineCmdArgSplit('tie x6 cf,"a quoted string"')
        ('tie', 'x6 cf,"a quoted string"')
        """
        if drawer.isList(line):  # accept lists of strings
            lineNew = [str(part) for part in line]
            line = " ".join(lineNew)

        line = line.strip()
        if not line:
            return None
        elif line[0] == "?":
            line = "help " + line[1:]
        elif line[0] == "!":
            line = "shell " + line[1:]
        i = 0

        # extract command from args, assuming that all cmds use identchars
        while i < len(line) and line[i] in lang.IDENTCHARS:
            i += 1
        cmd, arg = line[:i], line[i:].strip()
        if cmd in self.ao.cmdPrefixes:
            cmd = cmd + "_"  # special menu command need an added character

        return cmd, arg

    # -----------------------------------------------------------------------||--
    def _cmd(self, line):
        """Internal command loop command execution for interactive usage within thd Interpreter. See cmd(), below, for public interface.

        does actual processing of each command, adding do prefix
        separates args from command
        all commands pass through this method, inner most try/except loop
        sub commands provide data dictionaries that are then processed in
        the interepreter (not in the command object itself)

        >>> a = Interpreter()
        >>> a._cmd('pin a 3')
        >>> a._cmd('tin a 0')
        >>> a._cmd('q confirm')
        -1
        """
        splitLine = self._lineCmdArgSplit(line)
        if splitLine == None:
            self._emptyline()
            return None
        cmd, arg = splitLine
        cmdClassName = self._getCmdClass(cmd)
        if cmdClassName == None:
            return self._default(line)
        self._clearCount()  # clears cmd blank/bad counting
        try:  # execute cmdClassNametion, manage threads
            cmdObj = cmdClassName(self.ao, arg, verbose=self.verbose)
            ok, result = cmdObj.do()  # returns a dict if a subCmd, otherwise str
            if result == None:  # no msg returned; nothing to report
                stop = None
            elif not drawer.isDict(result):  # if not a dictionary
                self.out(result)  # disply str output
                stop = None  # only needed
            else:  # it is a subCmd, must be a dictionary result
                stop = self._proc(cmdObj, result)  # do processing on result
            if cmdObj.cmdStr != "quit":  # no history for quit
                self._historyAdd(cmdObj.log())  # log may return none
        except:  # print error message for all exceptions
            # TODO: could restore previous AthenaObject here to
            # remove the chance of damagin error
            tbObj = sys.exc_info()  # get traceback object
            stop = None  # must be assigned on error
            self._errorReport(cmd, arg, tbObj)  # writes log file
            self.out(lang.msgAthObjError)
        return stop

    def _prepareCommandArguments(self, line, arguments=[], errorMode="exception"):
        """Prepare a list, or a string, or a bunch of extrac args, for processing.

        >>> i = Interpreter()
        >>> i._prepareCommandArguments('tin a 3')
        ('tin', 'a 3')
        >>> i._prepareCommandArguments('tin', 'a 3')
        ('tin', ['a', '3'])
        """
        # environment.printDebug(['arguments initial', arguments])

        # at this level, commands should already be parsed by
        # line. thus, we can permit line breaks and replace with spaces
        if drawer.isStr(line):
            line = line.replace("\n", "")
            line = line.replace("\t", " ")

        # if line is a lost and arguments are empty, assume that first
        # element is command and remaining are args
        if drawer.isList(line) and arguments == []:
            arguments = line[1:]  # must assign this first
            line = line[0]

        if len(arguments) == 0:  # no args, assume cmd needs to be split
            splitLine = self._lineCmdArgSplit(line)
            if splitLine == None:
                if errorMode == "exception":
                    raise Exception("no command given")
                elif errorMode == "return":
                    return 0, "no command given"
            # here, args are still space-separated strings
            # cannut divide by spaces, as we me have a file path
            cmd, arg = splitLine
        else:  # args are given, so line is command name
            cmd = line  # add any additional arguments added individually
            argsExtra = []
            if not drawer.isList(arguments):
                arguments = arguments.split(" ")
            for part in arguments:
                # note: here we are converting to a string
                # part = str(part)
                if drawer.isStr(part):
                    part = part.strip()
                    part = part.replace("\n", "")
                    part = part.replace("\t", " ")
                if part != "":
                    argsExtra.append(part)

            # add to whatever was passed as arg
            arg = argsExtra  # keep as a list
            # arg = ' '.join(argsExtra)

        # environment.printDebug(['_prepareCommandArguments()', 'cmd:', cmd, 'arg:', arg])
        return cmd, arg

    def cmd(self, line, *arguments, **keywords):
        """Public interface for executing a single command line. This duplicates the functionality of _cmd(), above, yet provides features for a public interface.

        The `errorMode` is a keyword argument; can be 'exception' or 'return.'

        Given cmdline, or cmd arguments; cmdline will be split if arg == None
        good for calling a single command from cgi, or external interpreter
        return output as string, not printed. Does not log errors, does not keep a history.

        >>> a = Interpreter()
        >>> post = a.cmd('pin a 3')
        >>> post.startswith('PI a added to PathInstances')
        True
        >>> a = Interpreter()
        >>> post = a.cmd('pin', 'a', '3')
        >>> post.startswith('PI a added to PathInstances')
        True
        >>> a = Interpreter()
        >>> post = a.cmd('''pin   a     3''')
        >>> post.startswith('PI a added to PathInstances')
        True
        """

        # note: this form  does not work any more
        # this may not be a problem

        #         >>> a = Interpreter()
        #         >>> a.cmd('pin', 'a 3', errorMode='return')[0]
        #         1

        errorMode = "exception"  # default
        if "errorMode" in list(keywords.keys()):
            errorMode = keywords["errorMode"]
        # separate the command string from the args, which may be a list
        # or a string
        cmd, arg = self._prepareCommandArguments(line, arguments, errorMode=errorMode)
        # temporarily coerce into string
        #         if drawer.isList(arg):
        #             arg = [str(x) for x in arg]
        #             arg = ' '.join(arg)

        # cmdCorrect called here; this is done in cmdExecute and not in _cmd
        # as this is a public method
        # this treates the first arg as a string and provides necssary
        # corrections for creating a command class
        cmdClassName = self._getCmdClass(self.ao.cmdCorrect(cmd))

        if errorMode == "exception":
            if cmdClassName == None:
                raise Exception("no command given")
            result = "no additional cmd message"
            try:  # execute cmdClassNametion, manage threads
                cmdObj = cmdClassName(self.ao, arg, verbose=self.verbose)
                ok, result = cmdObj.do()  # no out on resutl here
                if not ok or lang.ERROR in result:
                    raise Exception("command level error: %s" % result.strip())
            except Exception:
                raise  # raise the same Exception
            return ok, result

        # this error mode is for backwards compatibility
        elif errorMode == "return":
            if cmdClassName == None:
                return 0, "no command given"
            try:  # execute cmdClassNametion, manage threads
                cmdObj = cmdClassName(self.ao, arg, verbose=self.verbose)
                ok, result = cmdObj.do()  # no out on resutl here
                if lang.ERROR in result:
                    ok = 0  # make not ok
            except:  # print error message
                # stop = None # must be assigned on error; no longer in use
                # self.out(self._errorReport(cmd))
                traceback.print_exc()  # print teaceback, dont log error
                result = "error occured"
                ok = 0
            return ok, result.strip()

        else:  # catch bad parameter setting
            raise Exception("bad error mode")

    # -----------------------------------------------------------------------||--
    def _precmd(self, line):
        return line

    def _postcmd(self, stop, line):
        """done after a command is executed; has nothing to do w/ a sub command
        called w/n cmdExecute"""
        if stop == -1:  # case of quit
            return stop
        self._updatePrompt()
        return stop

    # -----------------------------------------------------------------------||--
    def cmdExecute(self, cmdList):
        """Proess a list of commands.

        Used for processing multiple comamnds when separated by semicolon.

        A list of commands is executed one at a time
        called from self.cmdLoop

        >>> a = Interpreter()
        >>> a.cmdExecute(['pin a 3-4', 'tin b 0'])
        """
        for cmdLine in cmdList:
            if cmdLine == None:
                continue
            cmdLine = self.ao.cmdCorrect(cmdLine)
            if self.echo:  # no echo if set to quiet
                self.out(("%s %s\n" % (self.ao.promptSym, cmdLine)))
            # exceptions are handled in side this method
            stop = self._cmd(cmdLine)
            stop = self._postcmd(stop, cmdLine)
            self.out("\n")  # prints a space after each command
        return stop

    def cmdLoop(self, cmdList=None):
        """main command loop of athenaCL
        gets input from user in a loop; adds the cmd to cmdList
        calls self.cmdExecute to do work, not self.cmd
        """
        self.out(self.intro)
        stop = None
        while not stop:
            if cmdList == None:
                try:  # get raw data form user
                    line = dialog.rawInput(self.prompt, self.termObj)
                except (KeyboardInterrupt, EOFError):
                    line = "quit confirm"  # quit immediatly
                cmdList = line.split(";")  # split into mult cdms by ;
            else:  # use the command list
                self.echo = 1
            stop = self.cmdExecute(cmdList)
            if cmdList != None:
                cmdList = None  # clear command list
                self.echo = 0

    # -----------------------------------------------------------------------||--
    def _clearCount(self):
        """clear cmd counts"""
        self._emptyCount = 0  # clear
        self._blankCount = 0  # clear

    def _emptyline(self):
        """print result if an empty command has been found"""
        if self._emptyCount >= random.choice(list(range(7, 20))):
            self._emptyCount = 0
            self.out(dialog.getEncouragement())
        self._emptyCount = self._emptyCount + 1
        # return nothing

    def _default(self, line):
        """if no command is parsed out of line"""
        if self._blankCount >= random.choice(list(range(3, 10))):
            self._blankCount = 0
            self.out(dialog.getAdmonishment(line))
        else:
            self.out(lang.msgUnknownCmd)  # standard result
        self._blankCount = self._blankCount + 1
        # return nothing

    # -----------------------------------------------------------------------||--

    def _getCursorToolConvert(self):
        """read prefs and return a conversion dictionary
        called on init of Interpreter"""
        # get a blank command object; myst be a AthenaPreferences
        convert = {}
        convert["["] = self.ao.external.getPref("athena", "cursorToolLb")
        convert["]"] = self.ao.external.getPref("athena", "cursorToolRb")
        convert["("] = self.ao.external.getPref("athena", "cursorToolLp")
        convert[")"] = self.ao.external.getPref("athena", "cursorToolRp")
        convert["PI"] = self.ao.external.getPref("athena", "cursorToolP")
        convert["TI"] = self.ao.external.getPref("athena", "cursorToolT")

        convert["empty"] = self._cursorTool(convert)  # adds fake
        return convert

    def _cursorTool(self, convert=None):
        "need optional arg to build a default curos in _getCursor"
        if convert == None:
            convert = self.cursorToolConvert
        post = []
        post.append("%s%s%s" % (convert["["], convert["PI"], convert["("]))
        post.append("%s")
        post.append("%s%s%s" % (convert[")"], convert["TI"], convert["("]))
        post.append("%s")
        post.append("%s%s" % (convert[")"], convert["]"]))
        return "".join(post)

    def _updatePrompt(self):
        """update prompt graphics; done each time command is called"""
        promptRoot = self.ao.promptSym
        # this used to get pref from file; get now from aoInfo
        cursTemplate = self._cursorTool()
        #         if msg: # intial startup msg
        #             cursTool = dialog.getSalutation(self.cursorToolConvert)
        #         else: # update appearance
        cursTool = cursTemplate % (self.ao.activePath, self.ao.activeTexture)
        if self.ao.aoInfo["cursorToolOption"] != "cursorToolOff":
            self.prompt = "%s %s " % (cursTool, promptRoot)
        else:
            self.prompt = "%s " % (promptRoot)

    def toggleEcho(self):
        """flips echo status on and off"""
        if self.echo == 1:
            self.echo = 0
        else:
            self.echo = 1

    # -----------------------------------------------------------------------||--
    # error handling and logging
    def _errorReport(self, cmd, arg, tbObj):
        """fmtTbList is a list of formatted tb data
        writes to error log file"""
        timeTag = time.asctime(time.localtime())
        msg = []
        msg.append("ERROR, %s, %s\n" % (self.ao.infoStr(), timeTag))
        msg.append("%s %s\n" % (cmd, arg))

        tbList = traceback.extract_tb(tbObj[2])  # get tracebackobject
        for fileName, lineNo, funcName, text in tbList:
            msg.append("%s, %s, %s\n%s\n" % (fileName, lineNo, funcName, text))
        msg.append(str(tbObj[0]) + "\n")  # class, name of exception
        msg.append(str(tbObj[1]) + "\n")  # object, string about exception
        # adds an error report to a log file using external manager
        self.ao.external.logWrite(msg)  # give formatted data
        # report public info, dont show traceback

    def _historyAdd(self, log):
        """add a log to to dictionary
        if none, dont add or treat special"""
        timeTag = time.time()  # use raw seconds
        if log != None:  # only deal w/ successful logs
            self.ao.aoInfo["history"][timeTag] = log
        # dont do

    # -----------------------------------------------------------------------||--
    # proc_ commands need acces to interpreter to function
    # have initila shell in command.py

    def proc_menu(self, data):
        # used for menu commands?
        cmdStr = data["command"]
        if cmdStr == None:
            dialog.msgOut(lang.msgReturnCancel, self.termObj)
        else:
            self.cmdExecute(
                [
                    cmdStr,
                ]
            )

    def proc_quit(self, data):
        del self.ao
        return -1

    def proc_shell(self, data):
        """provides an interactive python session"""
        if os.name == "mac":
            dialog.msgOut(lang.msgPlatformError % os.name, self.termObj)
        elif os.name == "posix":
            os.system(data["shellCmd"])
        else:  # all windows flavors
            dialog.msgOut(lang.msgPlatformError % os.name, self.termObj)

    def proc_py(self, data):
        """provides an interactive python session"""
        import code

        if os.name == "mac":
            exitStr = "Control-D"
        elif os.name == "posix":
            exitStr = "Control-D"
        else:  # all windows flavors
            exitStr = "Control-Z"
        msg = "Python Interactive. enter %s to exit:" % exitStr
        code.interact(msg)

    def proc_AOrm(self, data):
        dialog.msgOut("reinitializing AthenaObject.\n", self.termObj)
        del self.ao
        self.ao = AthenaObject(self.termObj)

    def proc_AHexe(self, data):
        self.echo = 1
        self.cmdExecute(data["cmdList"])
        self.echo = 0
        dialog.msgOut("AthenaHistory Execute complete.\n", self.termObj)


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)

    def testInterpreterPaths(self):

        cmdListB = [
            "PIn test1  5-4  3-4     2-5",
            "PIn test2  (3,4,4,4,4) (3,3,3) (1,1,2,3)",
            "PIn test3  8-3  (3,4,3)  7-5",
            "PIv",
            "PIcp test1  test4",
            "PIrm test4",
            "PIls",
            "PIo test1",
        ]

        cmdListD = [
            "PIret test1retro",
            "PIrot test1retroRot     2",
            "PIslc test1retroRotSlc  2,3",
            "PIo test2",
            # pvn
        ]

        athInt = Interpreter("terminal")
        for cmd in cmdListB + cmdListD:
            ok, result = athInt.cmd(cmd, errorMode="return")
            if not ok:
                raise Exception("failed cmd (%s): %s" % (cmd, result))

    def testInterpreterTextures(self):
        from athenaCL.libATH.libTM import texture

        cmdListE = []
        for i in range(len(list(texture.tmNames.values()))):
            tmName = list(texture.tmNames.values())[i]

            name = "t%s" % i
            cmdListE.append("EMo cn")
            cmdListE.append("TMo %s" % tmName)
            cmdListE.append("tin %s 3" % name)
            cmdListE.append("TIcp %s test2" % name)
            cmdListE.append("TIls ")
            cmdListE.append("TIo test2")
            cmdListE.append("TIv test2")
            cmdListE.append("TImute test2")
            cmdListE.append("TImode p   pcs")
            cmdListE.append("TIrm test2")
            cmdListE.append("TIo %s" % name)
            cmdListE.append("TIe t  1.5, 3")
            cmdListE.append("TIe r  l, ((4,1,1),(8,1,1),(8,3,1))")

        cmdListF = [
            "TMv",
            "TMls",
            "EMo cn",
            "tin test1 3",
            "TIn test2 80",
            'TEe b  "c", 120',
            'TEe a  "cg", "lu", .6, .7, .01',
            "TEv beat",
            "TEv a",
            "TIdoc test1",
            "TIdoc test2",
            "TTls ",
            "TTo NoiseLight",
            "TCn echoA",
            "TCcp echoA echoB",
            "TCls ",
            "TCrm echoB",
            "TCe t fa,(c,10)",
            "TEmap ",
            "EMi ",
            "TPls ",
            "TPv sieve ",
            #  'CPch 2',
            # 'CPff a',
        ]

        athInt = Interpreter("terminal")
        for cmd in cmdListE + cmdListF:
            ok, result = athInt.cmd(cmd, errorMode="return")
            if not ok:
                raise Exception("failed cmd (%s): %s" % (cmd, result))

    def testInterpreterLoad(self):

        cmdList = [
            # do all test load files
            "AOl tests/xml/test01.xml",
            #'AOl demo03.xml',
            #'AOl demo05.xml',
            "AOmg pysrc/athenaCL/demo/legacy/demo01.xml",
            # AOdlg
            "APwid 80",
            "APcurs",
            "APcurs",  # twice to toggle back
            "cmd",
            "help",
            "AUsys",
        ]

        athInt = Interpreter("cgi")
        for cmd in cmdList:
            ok, result = athInt.cmd(cmd, errorMode="return")
            if not ok:
                raise Exception("failed cmd (%s): %s" % (cmd, result))

    def testInterpreterAthenaUtility(self):
        cmdList = [
            "AUca f{f}x{101}y{100} .89124 .01",
            "AUca x{20} ru,0,20 ru,0,0.04",
            "AUma 4 9 2 9 3 9 3 8 3 9 3 8 4 8 3 9 3 8 3 4 9 2 3 8 4 9",
            "AUmg 120 0 a{0}b{1}:{a=3|b=8}",
        ]

        athInt = Interpreter("terminal")
        for cmd in cmdList:
            ok, result = athInt.cmd(cmd, errorMode="return")
            if not ok:
                raise Exception("failed cmd (%s): %s" % (cmd, result))

    def testInterpreterClone(self):
        cmdList = [
            "pin a 5|7|11,c1,c8",
            "emo m",
            "tmo lh",
            "tin a 1",
            "tie t 0,5",
            "tie r loop,((8,1,+),(9,2,+)),rc",
            "tcn a",
            # do a scaling, and a shift, to a part
            "tce t pl,((fa,(c,5)),(fma,l,(c,.5)))",
            "tce s1 ei",
            "tcn b",
            "tce t pl,((fa,(c,10)),(fma,l,(c,1.25)))",
            "tce s1 ti",
        ]

        athInt = Interpreter("terminal")
        for cmd in cmdList:
            ok, result = athInt.cmd(cmd, errorMode="return")
            if not ok:
                raise Exception("failed cmd (%s): %s" % (cmd, result))

    def testInterpreterEmbeddedParameterObject(self):

        ai = Interpreter("terminal")

        # test results of preparing command arguments
        for preLine, preArgs, post in [
            ("tin a 3", [], ("tin", "a 3")),
            ("tin", ["a", "3"], ("tin", ["a", "3"])),
            # the number is retained
            ("tin", ["a", 3], ("tin", ["a", 3])),
            ("tin", ["a", 3, None], ("tin", ["a", 3, None])),
            ("tin a b 200 1234", [], ("tin", ("a b 200 1234"))),
            (["tin", "a", "b", 200, 1234], [], ("tin", ["a", "b", 200, 1234])),
        ]:
            self.assertEqual(ai._prepareCommandArguments(preLine, preArgs), post)

        ai.cmd("pin a 3", errorMode="exception")

        ai.cmd("emo m", errorMode="exception")
        ai.cmd("tin a 1", errorMode="exception")
        # ai.cmd('tin', 'b', 2, errorMode='exception')
        # ai.cmd(['tin', 'c', 65], errorMode='exception')

        ai.cmd("tie", "a", ("bg", "rc", (0.2, 0.8)), errorMode="exception")

        from athenaCL.libATH.libPmtr import parameter, basePmtr

        po1 = parameter.factory("bg, rc, (.1, 1)")
        ai.cmd("tie", "a", po1, errorMode="exception")

        po2 = parameter.factory("bg, rc, (-1, -2, -3)")
        self.assertEqual(True, isinstance(po2, basePmtr.Parameter))
        ai.cmd("tie", "o", po2, errorMode="exception")

        # TODO: this works, but actually creates a new instance
        # need to modify Texture to get isntance sharing

        # ai.cmd('eln')
        # ai.cmd('elh')


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":

    if len(sys.argv) == 1:  # normal conditions

        from athenaCL.test import baseTest

        baseTest.main(Test)

    elif len(sys.argv) > 1:
        a = Test()
        a.testInterpreterEmbeddedParameterObject()
