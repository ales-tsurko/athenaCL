# -----------------------------------------------------------------||||||||||||--
# Name:          command.py
# Purpose:       define classes for all commands
#                    provide a sub-class for each command, taking an ao as an arg.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2003-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import sys, os, time, random, copy
import unittest
import xml.etree.ElementTree as ET

from athenaCL.libATH import argTools
from athenaCL.libATH import audioTools
from athenaCL.libATH import automata
from athenaCL.libATH import clone
from athenaCL.libATH import dialog
from athenaCL.libATH import drawer
from athenaCL.libATH import eventList
from athenaCL.libATH import imageTools
from athenaCL.libATH import ioTools
from athenaCL.libATH import language
from athenaCL.libATH import markov
from athenaCL.libATH import error

lang = language.LangObj()
from athenaCL.libATH import osTools
from athenaCL.libATH import outFormat
from athenaCL.libATH import pitchPath
from athenaCL.libATH import pitchTools
from athenaCL.libATH import rhythm
from athenaCL.libATH import temperament
from athenaCL.libATH import typeset
from athenaCL.libATH import multiset
from athenaCL.libATH.libPmtr import parameter
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.libTM import texture
from athenaCL.libATH.libOrc import generalMidi
from athenaCL.libATH.omde import rand
import dialogExt

# conditional imports that may fail but are not necessary
try:
    from athenaCL.libATH.libGfx import graphPmtr
    from athenaCL.libATH.libGfx import graphEnsemble
    from athenaCL.libATH.libGfx import graphCellular
except ImportError:  # pil or tk may not be installed
    pass

_MOD = "command.py"
from athenaCL.libATH import prefTools

from xmlToolsExt import checkFileFormat

environment = prefTools.Environment(_MOD)


# -----------------------------------------------------------------||||||||||||--
class Command(object):
    """parent class for all athenacl commands
    commands can be two types: a normal command, and a subCmd
    a normal command does process and returns a display; display methods exist
    a subCmd does processing, but returns data to Interpreter; this data
        must be processed further by a CMD_proc method in the interpreter
        if a subCmd returns a string (anything other than dict) the interpreter
        will not run the _proc method
    errors and warnings;
        if gather or process return anything other None, an error or cancel is
        is understood
        do method:
        what needs to happen: each step can return None, or a triple
            triple contains msg, warn, error ?

    command objects _do_ have access to terminal object
    """

    def __init__(self, ao, args="", **keywords):
        """
        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> a = Command(ao)
        >>> post = a.do()
        """
        self.ao = ao
        self.termObj = self.ao.termObj
        # self.scObj = self.ao.external.scObj
        # self.mcObj = self.ao.external.mcObj
        self.setFactory = multiset.MultisetFactory()  # for building set objs

        self.args = args
        if "verbose" in keywords:
            self.verbose = keywords["verbose"]

        self.cmdStr = None  # command name, give in subclass
        self.processSwitch = 1  # if methods should be called
        self.gatherSwitch = 1

        # necessary to avoid testing gfx arrangment and printing warnings
        self.gfxSwitch = 0  # default is tt comands dont graphics: must open
        self.processStatus = 0  # complete or not
        self.gatherStatus = 0  # complete or not

        self.subCmd = 0  # subcommands are executed from method in interpreter

    def gather(self):
        """get args from user. should return None, unless error cancel
        return a string to display or cancel"""
        pass

    def process(self):
        """should return None, unless error cancelc
        return a string to display or cancel"""
        pass

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def unprocess(self):
        pass

    def result(self):
        """only used for subCmds, to get data back after process is run"""
        pass

    def display(self):
        """return a string w/ the result ofthe command"""
        pass

    def displayGfx(self, dir=None):
        """if a gui window is made
        only drawn if self.gfxSwitch is set"""
        pass

    def do(self):
        """threading only sometimes works
        gather and process optional;
        when a method returns None, there are no errors
            if not None, do not continue and return result
        need to set an ok: error/warning flag and return a triple
        ok 1 is good, 0 is error
        """
        # init whenever do is called (may happen more than once
        self.processStatus = 0  # complete or not
        self.gatherStatus = 0  # complete or not

        # (1) get args
        if self.gatherSwitch:
            post = self.gather()
            if post != None:  # an error occured in the gather stage
                ok = 0
                return ok, post
        self.gatherStatus = 1  # gather complete complete
        # (2) process
        if self.processSwitch:
            # optional execution in separate thread
            post = self.process()
            if post != None:
                ok = 0
                return ok, post  # an error or cancel str
        self.processStatus = 1  # process complete complete
        # after gather and process, assume that no processing errors will happen
        ok = 1
        if not self.subCmd:  # not a sub command, return displays
            if self.gfxSwitch:  # command obj defines gfx method
                okGfx, fmt, dir = self._validGfxSetup()
                if okGfx:
                    self.displayGfx(fmt, dir)  # may be an empty method
            # return text display always
            return ok, self.display()
        else:  # its is a sub command, call result instead of display
            return ok, self.result()  # returns a dictionary of data

    def undo(self):
        pass

    # -----------------------------------------------------------------------||--
    # utility display functions
    def _nameTest(self, name, charInclude=""):
        """makes sure a name has valid characters"""
        if len(name) > 40:
            return lang.msgBadNameLength
        for char in name:
            if char not in (lang.NAMECHARS + charInclude):
                return lang.msgBadNameChars
        return None  # a good name

    def _nameReplace(self, name):
        """replace spaces with underscores
        called whenever a user gives a pi, ti, tc, or pv name
        replaces spaces before checking for conflicts"""
        return name.replace(" ", "_")

    def _fileNameTest(self, name):
        """test for a rational file name, presumably always with an extension
        b/c there is a .xml extension, length has to be greater than 4 chars
        returs ok, msg
        """
        # possible problem with ancient platforms that do not support long filenames
        if len(name) > 64 or len(name) <= 4:
            return 0, lang.msgBadNameLength
        for char in name:
            if char not in (lang.FILECHARS):
                return 0, lang.msgBadNameChars
        return 1, ""  # a good name

    def _getNoTI(self):
        """returns number of textures"""
        return len(list(self.ao.textureLib.keys()))

    def _getNoPI(self):
        """returns number of paths"""
        return len(self.ao.pathLib)

    def _getUsage(self, optStr=None):
        """this is used by all commands to return usage documentation
        upond command line error"""
        return self.ao.help.reprUsage(self.cmdStr, optStr)

    def _getNumber(self, query, numType, min=None, max=None):
        """gets number from user using query
        converts to float or int depending on numType
        returns None on error
        """
        while 1:
            numStr = dialog.askStr(query, self.termObj)
            if numStr == None:
                return None
            numEval = drawer.strToNum(numStr, numType, min, max)
            if numEval == None:
                dialog.msgOut(lang.msgIncorrectEntry, self.termObj)
                continue
            else:
                return numEval

    def _strRawToData(self, usrStr, errorPreface=lang.ERROR):
        """Method for evaluating user strings provided for Texture editing.
        prohibits doing wack things, provides error messages
        calls restringulator to quote all char/sym sequences

        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> a = Command(ao)
        >>> a._strRawToData('ru, 0, 1')
        (('ru', 0, 1), '')
        >>> a._strRawToData('cf, "a quoted string"')
        (('cf', 'a quoted string'), '')
        """
        if usrStr == None:
            return None, "no user data provided"
        msg = ""  # no error
        # if user str is already an evaluated number, return it w/o error
        if drawer.isNum(usrStr):
            return usrStr, msg  # already evaluated
        if usrStr.find("__") == 0:
            msg = "%s: %s" % (errorPreface, "Internal Access Attempt")
            usrDataEval = None
        else:
            # environment.printDebug(['pre restringulator:', usrStr])
            usrStr = drawer.restringulator(usrStr)  # add quotes if necessary
            try:
                usrDataEval = eval(usrStr)
            except TypeError as e:
                msg = "%s %s" % (errorPreface, e)  #'type-error')
                usrDataEval = None
            except SyntaxError as e:
                msg = "%s %s" % (errorPreface, e)  #'syntax-error')
                usrDataEval = None
            except NameError as e:  # if strings given without a quote not converted
                msg = "%s %s" % (errorPreface, "name-error (quote all strings)")
                usrDataEval = None

        # environment.printDebug(['results of _strRawToData():', usrDataEval, msg])
        return usrDataEval, msg

    def _strListToArgList(self, usrStr):
        """convert a list of strings to a string separated by spaces
        used in logging command line args"""
        setStr = drawer.listScrub(usrStr, "rmSpace", "rmQuote")
        setStr = setStr.replace(",", " ")  # replace quotes with spacess
        return setStr

    def _setReturnError(self, rawSet):
        """adds one to each value of list/tuple
        returns a list
        this is useful for reconverting ranges back to usr strings
        used in log methods
        """
        rawSet = list(copy.deepcopy(rawSet))
        for i in range(len(rawSet)):
            rawSet[i] = rawSet[i] + 1
        return rawSet

    def _chooseFromList(self, prompt, choiceList, caseSens="case", parseMethod=None):
        """form a list of elements, allows user to select by name or number
        caseSense can be 'case' or 'noCase'
        tries 3 ways: parseMethod, choiceList, and by integer
        parseMethod can be a standard method that converts valid strings
            and returns None on error"""
        if choiceList == None:
            return None
        choiceList = list(choiceList)  # make sure its a list
        choiceList.sort()
        prompt = prompt + " (name or number 1-%s):" % len(choiceList)
        name = dialog.askStr(prompt, self.termObj)
        if name == None:
            return None
        # if parseMethod exists, try first
        if parseMethod != None:
            found = parseMethod(name)
            if found != None:
                return found
        # otherwise, check if in list
        found = drawer.inList(name, choiceList, caseSens)
        if found != None:
            return found
        # last, look for an index number
        try:  # check for integer number
            listNumber = int(name)
        except (SyntaxError, NameError, TypeError, ValueError):
            return None
        if listNumber <= len(choiceList) and listNumber >= 1:
            name = choiceList[listNumber - 1]  # adjust index
            return name
        else:
            return None  # error message

    def _checkInRange(self, value, min, max):
        """checks to see if value >= min
        <= max. performs no corrections
        returns None on failure
        input value as int or float, not string
        """
        if value == None:
            return None
        if value >= min and value <= max:
            return value
        else:
            return None

    def _convertListRange(self, rangeStr, start, end, ADJ=1):
        """gets a tuple of two numbers separated by a comma
        start and end are given un-corrected
        1 is subtracted from user values after being obtained
        input as a string in the form (a,b)
        provide all option to automaticlal get all elements in a range
        correction value can be turned off by canging ADJ value
        """
        if rangeStr == None or rangeStr == "":
            return None
        elif rangeStr.lower() == lang.ALL:
            return [start - ADJ, end - ADJ]
        try:
            rangeStr = eval(rangeStr)
        except (SyntaxError, NameError):
            return None
        if drawer.isList(rangeStr):
            rangeList = list(rangeStr)
        if drawer.isNum(rangeStr):  # if one given, assume this and next
            rangeList = list((rangeStr, rangeStr))

        # human correction to count from 1
        rangeList[0] = int(rangeList[0] - ADJ)
        rangeList[1] = int(rangeList[1] - ADJ)
        if (
            rangeList[0] < (start - ADJ)
            or rangeList[0] > (end - ADJ)
            or rangeList[1] < (start - ADJ)
            or rangeList[1] > (end - ADJ)
        ):
            return None
        else:
            return rangeList

    # -----------------------------------------------------------------------||--
    # file path utilities
    def _findFilePath(self, usrStr):
        """if a complete path, checks existence and returns
        if a file name, searches directories for file and
        returns complete file path
        """
        if usrStr == None:
            return None
        if usrStr.find(os.sep) >= 0:  # a complete path
            filePath = drawer.pathScrub(usrStr)
            if (
                os.path.exists(filePath) == 1 and os.path.isdir(filePath) != 1
            ):  # not a directory
                return filePath
        else:
            possibleDirs = []  # all demo dirs
            possibleDirs.append(self.ao.aoInfo["fpLastDir"])
            possibleDirs.append(self.ao.aoInfo["fpLastDirEventList"])
            dir = drawer.getcwd()
            if dir != None:
                possibleDirs.append(dir)
            for directory in possibleDirs:
                try:
                    dirContents = os.listdir(directory)
                except OSError:
                    continue
                if usrStr in dirContents:
                    filePath = os.path.join(directory, usrStr)
                    filePath = drawer.pathScrub(filePath)
                    if (
                        os.path.exists(filePath) == 1 and os.path.isdir(filePath) != 1
                    ):  # not a directory
                        return filePath
            return None  # failed to find anything

    # -----------------------------------------------------------------------||--
    # high level string parsing or interactive path assignment

    def _selectAppPath(self, usrStr, appType, appName, appPathPref):
        """get a path for an application type; either parse
        a string and test, or get interactively; will chnage path if different
        appPathPref     = ('external', 'csoundPath')
        """
        # environment.printDebug(['_selectAppPath:', usrStr])
        path = None
        changeAppPath = None
        if usrStr != None:  # raw command arg string
            usrStr = drawer.pathScrub(usrStr)  # scrub, expand, links
            # even if appStrKey == '', will return 0
            if os.path.exists(usrStr) and drawer.isApp(usrStr):
                path = usrStr  # good path
                changeAppPath = 1
            else:
                changeAppPath = 0
        else:  # interactive
            if appName != None:
                appDialogQuery = "select a %s application (%s):" % (appType, appName)
            else:
                appDialogQuery = "select a %s application:" % (appType)
            while 1:
                path, ok = dialogExt.promptChooseFile(
                    appDialogQuery,
                    self.ao.aoInfo["fpLastDir"]
                )
                if not ok or path == None or not os.path.exists(path):
                    changeAppPath = 0  # dont change
                    break
                else:
                    changeAppPath = 1  # path found
                    break  # path ok

        if changeAppPath and path != None:
            self.ao.external.writePref(
                appPathPref[0], appPathPref[1], drawer.pathScrub(path)
            )
        # return path after change
        ok = 1
        if changeAppPath:
            return path, ok
        else:
            return None, 0  # return None on failure

    # -----------------------------------------------------------------------||--
    # valid path and preference utilities
    def _validWritePath(self, usrStr, forceExtension=None, forceDir=None):
        """for use when a user supplies a command line arugment for writing
        a file; need to find complete path, check for invalid characters
        makes sure has extensions

        if forceDir is not error, and the user provides only name, and the
        the combined forceDir and name do not exists, tn a path is
        auto constrcuted. this behaviour may be misleading...

        do not accept a path unless it resolves to a complete path
        return None on error

        note: this has a sideffect, as when eln happens the only file path that
        is provide is the .xml; wheres the event mode may create many other files
        the potential conflict will not be noticed.
        """
        if usrStr == None or not drawer.isStr(usrStr):
            return None
        if forceExtension != None:
            if usrStr[-len(forceExtension) :] != forceExtension:
                return None  # if no extensions, return none
        # determine if an absolute or relative path was given _initially_
        if usrStr.find(os.sep) >= 0:
            abs = 1
        else:
            abs = 0
        # try to get a complete path; will not append cwd if just a name
        filePath = drawer.pathScrub(usrStr)
        # never try to replace a directory
        if os.path.exists(filePath) and os.path.isdir(filePath):
            return None

        dir, fileName = os.path.split(filePath)
        # test for valid characters in file name
        ok, msg = self._fileNameTest(fileName)
        if not ok:
            return None
        # provide a dir if non given
        if dir == "" and forceDir != None:  # if not
            # used to use getcwd here, but not sure this is a good idea?
            if forceDir == "fpLastDir" and self.ao.aoInfo["fpLastDir"] != "":
                dir = self.ao.aoInfo["fpLastDir"]
            elif (
                forceDir == "fpLastDirEventList"
                and self.ao.aoInfo["fpLastDirEventList"] != ""
            ):
                dir = self.ao.aoInfo["fpLastDirEventList"]
            # may want to get cwd here, as this is standard behaviour
            elif drawer.getcwd() != None:
                dir = drawer.getcwd()
            else:  # no dir can be found
                return None
            # should already be set, user did not _initially_ provide abs path
            abs = 0  # will not over-write existing file
            filePath = os.path.join(dir, fileName)

        # check that there is a dir here
        # a dir of '' will return false for os.path.exists()
        if not os.path.isdir(dir):  # a directory
            return None
        # overwrite existing file if abs path given
        # create a temporary eventList
        emObj = eventList.factory(self.ao.activeEventMode, self.ao)
        pathList = emObj.getWritePaths(filePath)
        if drawer.pathExists(pathList):
            if abs:  # overwrite only if initially given as abs path
                return filePath
            else:
                return None
        else:  # doesnt exist
            return filePath

    def _validGfxPreference(self):
        """check if the user preference vis method is a available
        this is a time-suck only the first time it is called
        valid gfx methods are tk, pil, file, text"""
        fmt = self.ao.external.getPref("athena", "gfxVisualMethod")
        if fmt in self.ao.external.getVisualMethod():
            if fmt == "text":  # not active in gfx presentations
                return None
            return fmt
        else:  # set as pref but not available
            return None

    #     def _validScratchDir(self):
    #         """use to set valid scratch dir; get from user if necessary
    #
    #         note that if this is called and the scratch directory
    #         is not set, an interactive prompt will begin
    #
    #         TODO: use of this method should be phased out; instead
    #         temp files should be created if the scratch dir is not set
    #         """
    #         path = self.ao.external.getPref('athena', 'fpScratchDir')
    #         if not os.path.isdir(path):
    #             cmdObj = APdir(self.ao, '', argForce={'name':'fpScratchDir'})
    #             ok, msg = cmdObj.do() # will call gather, process, etcetera
    #         else: ok = 1
    #         if ok:
    #             path = self.ao.external.getPref('athena','fpScratchDir')
    #             return path
    #         else: return None

    #     def _validScratchFp(self, ext='.xml'):
    #         """provide a valid xml file name
    #         return None on error"""
    #         path = self._validScratchDir()
    #         if path == None: return None
    #         else: return os.path.join(path, drawer.tempFileName(ext))

    def _validGfxSetup(self):
        """check if the user preference scratch is a good dir
        get dir if not set
        check format compatabilities
        returns ok, and dir path

        """
        fmt = self._validGfxPreference()  # checks is pref fmt is available
        if fmt == None:
            return 0, fmt, None  # error
        # check scratch dir for methods that write files
        if fmt in ["jpg", "png", "eps"]:
            # scratch dir can be None if not yet set;
            # temp file will be created in image tools methods
            fpScratchDir = environment.getScratchDirPath()
            ok = 1  # fpScratchDir is good
        else:  # formats taht dont write files
            ok = 1  # okay for graphics, scratch dir not needed
            fpScratchDir = None  # not needed for tk
        # check format and resources available
        if fmt == "tk" and not imageTools.TK:
            environment.printWarn([lang.WARN, lang.msgGfxTkError])
            ok = 0
        # check if we are in idle and gfx is tk: this will not work
        if fmt == "tk" and drawer.isIdle():
            environment.printWarn([lang.WARN, lang.msgGfxIdleError])
            ok = 0
        # see if pil module is available
        if fmt in ["jpg", "png"] and not imageTools.PIL:
            environment.printWarn([lang.WARN, lang.msgGfxPilError])
            ok = 0

        if ok:  # get to get fpScratchDir again as set w/ APdir command
            return ok, fmt, fpScratchDir  # fpScratchDir is a directory
        else:  # not okay
            return ok, fmt, None

    # -----------------------------------------------------------------------||--
    def _numPmtrDetermineFormat(self, usrStr, srcFmt=None):
        """strip leading characters from aux, text, and dyn notations"""
        allFormats = [basePmtr.AUXQ, basePmtr.TEXTQ, basePmtr.DYNQ, basePmtr.CLONEQ]
        fmt = None
        noStr = ""
        for stub in allFormats:
            if usrStr[: len(stub)] == stub.lower():
                fmt = stub
                noStr = usrStr[len(stub) :]
        if fmt == None:  # check single character synonymes
            if usrStr[:1] == "p":
                noStr = usrStr[1:]
                fmt = basePmtr.AUXQ
            elif usrStr[:1] == "x":
                noStr = usrStr[1:]
                fmt = basePmtr.AUXQ
            elif usrStr[:1] in ["e", "s"]:
                noStr = usrStr[1:]
                fmt = basePmtr.TEXTQ
            elif usrStr[:1] in ["y", "d"]:
                noStr = usrStr[1:]  # remvoe dynQ
                fmt = basePmtr.DYNQ
            elif usrStr[:1] == "c":
                noStr = usrStr[1:]  # remvoe auxQ
                fmt = basePmtr.CLONEQ
            else:  # failure: cannot find a match, may not be right label
                # assume that usrStr is just a number, add srcFmt
                fmt = srcFmt
                noStr = usrStr
        return fmt, noStr

    def _numPmtrConvertLabel(self, usrStr, tName, srcFmt=None, force=0):
        """check for a number after aux, text, or clone pmtr
        seperates number from strings, and returns coorect label
        force, if true, will return None if usrStr is not a numeric label
        can use this w/ clones, as have same aux as t, and cloneQ is fixed
        """
        srcStr = copy.deepcopy(usrStr)
        usrStr = drawer.strScrub(usrStr, "l")
        if usrStr == None:
            return None

        fmt, noStr = self._numPmtrDetermineFormat(usrStr, srcFmt)
        if fmt == None or fmt != srcFmt:  # not a numeric label, not srcFmt
            if force:
                return None  # mark this as an error
            else:
                return srcStr  # return value unchanged

        if noStr == "":
            return None
        try:
            no = int(noStr)
        except (NameError, ValueError, SyntaxError, ZeroDivisionError):
            return None
        # check that number is in proper range
        if fmt == basePmtr.AUXQ:
            if no not in list(range(0, self.ao.textureLib[tName].auxNo)):
                return None
        elif fmt == basePmtr.TEXTQ:
            if no not in list(range(0, self.ao.textureLib[tName].textPmtrNo)):
                return None
        elif fmt == basePmtr.DYNQ:
            if no not in list(range(0, self.ao.textureLib[tName].dynPmtrNo)):
                return None
        elif fmt == basePmtr.CLONEQ:
            if no not in list(range(0, self.ao.cloneLib.clonePmtrNo())):
                return None
        label = "%s%s" % (fmt, no)
        return label

    # -----------------------------------------------------------------------||--
    def _getNumPmtr(self, pmtrType, tName, usrStr=None):
        """have user select a numeric parameter
        owrks w/ all types
        note: event w/ clones, clone name need not be provided"""
        if pmtrType[:3] == "aux":
            valMax = self.ao.textureLib[tName].auxNo - 1
            stub = basePmtr.AUXQ
            title = "an auxiliary"
            char = "x"
        elif pmtrType[:4] == "text":
            valMax = self.ao.textureLib[tName].textPmtrNo - 1
            stub = basePmtr.TEXTQ
            title = "a texture static"
            char = "s"
        elif pmtrType[:5] == "clone":
            valMax = self.ao.cloneLib.clonePmtrNo() - 1
            stub = basePmtr.CLONEQ
            title = "a clone static"
            char = "s"
        elif pmtrType[:3] == "dyn":
            valMax = 0
            stub = basePmtr.DYNQ
            title = "a texture dynamic"
            char = "d"
        # usr may have already provide nevessary numerica label
        if usrStr != None:
            label = self._numPmtrConvertLabel(usrStr, tName, stub, 1)
            if label != None:
                return label  # skip interface
        while 1:
            usrStr = dialog.askStr(
                (
                    "select %s parameter to edit, from %s0 to %s%s:"
                    % (title, char, char, valMax)
                ),
                self.termObj,
            )
            if usrStr == None:
                return None
            label = self._numPmtrConvertLabel(usrStr, tName, stub, 1)
            if label == None:
                dialog.msgOut(lang.msgDlgEnterIntRange % valMax, self.termObj)
                continue
            else:
                return label

    # -----------------------------------------------------------------------||--
    # sc display utilities

    def _scGetTnStr(self):
        if self.ao.tniMode == 1:
            classStr = lang.msgSCtni
        else:
            classStr = lang.msgSCtn
        return classStr

    # -----------------------------------------------------------------------||--
    # these function are used to test the current state of all path instances
    def _piTestExistance(self):
        """checks if a path exists"""
        if len(self.ao.pathLib) == 0:
            return lang.msgPIcreateFirst
        else:
            return None

    def _piTestNameExists(self, name=None):
        """checks if a path name exists"""
        if name == None:
            name = self.ao.activePath
        if (name in self.ao.pathLib) != 1:
            return lang.msgPImissingName
        else:
            return None

    def _piTestNoVL(self):
        """checks if a path voices are allowed"""
        try:
            if self.ao.pathLib[self.ao.activePath].voiceType == "none":
                return lang.msgPVnotAvailable
            else:
                return None
        except:
            return lang.msgPVnotAvailable

    #     def _piTestCurrentPVgroupNameExists(self):
    #         """checks if a path voice name exists"""
    #         try:
    #             if (self.ao.pathLib[self.ao.activePath].activeVoice in
    #                  self.ao.pathLib[self.ao.activePath].voiceNames()):
    #                 return None
    #             else:
    #                 return lang.msgPVgroupMissingName
    #         except:
    #             return lang.msgPVgroupMissingName

    def _piAutoCreate(self, name="auto", psList=[0]):
        """creates and loads a path,
        used for default, when a texture has lost its path
        for eventModes that requre a path
        will not overwrite existing paths with the same name"""
        if name not in list(self.ao.pathLib.keys()):
            self.ao.pathLib[name] = pitchPath.PolyPath(name)
            self.ao.pathLib[name].autoFill(psList)
        self.ao.activePath = name
        # all updates now done w/ load opperations

    def _piAutoCreateMidiPercussion(self, inst):
        """utiliy method for event mode midi percussion instrument editing"""
        pName = "auto-%s" % generalMidi.getPercNameFromNoteName(inst)
        # inst number is midi pitch; convert to psReal, put in list
        self._piAutoCreate(pName, [pitchTools.midiToPs(inst)])
        # return a reference
        return self.ao.pathLib[pName]

    def _piGetNewName(self, query):
        """asks user for a path name, checking against existing paths"""
        while 1:
            name = dialog.askStr(query, self.termObj)
            if name == None:
                return None
            name = self._nameReplace(name)
            if self._nameTest(name) != None:
                dialog.msgOut(self._nameTest(name), self.termObj)
            elif name in self.ao.pathLib:
                dialog.msgOut(lang.msgPInameTaken, self.termObj)
            else:
                return name

    def _piGetPathPosition(self, query, start, end):
        """start and end are the limits of integers offered
        does not performa list correct (suctracting one)"""
        query = query + " (positions %i-%i):" % (start, end)
        while 1:
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            rotZero = drawer.strToNum(usrStr, "int", start, end)
            if rotZero != None:
                return rotZero
            else:
                dialog.msgOut(
                    ("%sincorrect path position. try again.\n" % lang.TAB), self.termObj
                )

    def _piGetIntegerRange(self, query, start, end):
        """gets a tuple of two numbers separated by a comma
        start and end are given un-corrected
        1 is subtracted from user values after being optained"""
        while 1:
            outputRangeStr = dialog.askStr(query, self.termObj)
            if outputRangeStr == None:
                return None
            outputRangeTuple = self._convertListRange(outputRangeStr, start, end)
            if outputRangeTuple == None:
                dialog.msgOut(lang.msgPIbadSliceRange, self.termObj)
                continue
            else:
                return outputRangeTuple

    # -----------------------------------------------------------------------||--
    def _tiTestExistance(self):
        if len(self.ao.textureLib) == 0:
            return lang.msgTIcreateFirst
        else:
            return None

    def _tiTestMuteStatus(self):
        """check if textures and associated clones are muted
        used to determine if there is any material to generate
        this is an improved version used for ELn; this allowes for muted
        textures to exist with active clones"""
        activeCount = 0
        for tName in list(self.ao.textureLib.keys()):
            t = self.ao.textureLib[tName]
            # if active and no clonse
            if not t.mute and tName not in self.ao.cloneLib.tNames():
                activeCount = activeCount + 1
                continue
            # if muted and no clonse
            elif t.mute and tName not in self.ao.cloneLib.tNames():
                continue
            # there are clonse
            elif tName in self.ao.cloneLib.tNames():
                if not t.mute:  # active texture; always add, no matter clone
                    activeCount = activeCount + 1
                # check for clone activity
                for cName in self.ao.cloneLib.cNames(tName):
                    c = self.ao.cloneLib.get(tName, cName)
                    if not c.mute:  # if not muted, give active value
                        activeCount = activeCount + 1
        # print _MOD, '_tiTestMustStatus', activeCount
        if activeCount > 0:
            return 0  # textures or clonse are active
        else:
            return 1  # all sources are muted

    def _tiTestNameExists(self, name=None):
        if name == None:
            name = self.ao.activeTexture
        if (name in self.ao.textureLib) != 1:
            return lang.msgTImissingName
        else:
            return None

    def _tiConvertPrePost(self, usrStr):
        ref = {
            "pre": ["pre", "r"],
            "post": ["post", "s"],
        }
        return drawer.selectionParse(usrStr, ref)  # may be None

    def _tiConvertEventTime(self, usrStr):
        ref = {
            "event": ["event", "e"],
            "time": ["time", "t"],
        }
        return drawer.selectionParse(usrStr, ref)  # may be None

    def _tiGetDemo(self, tName, p, label, type="edit"):
        """p is the parameter key
        used edit commands to provide an exmaple to user of entry format
        label is string used to describe p
        """
        if type == "edit":
            prefaceStr = "current"
            forbidden = ["inst"]
        elif type == "listedit":
            prefaceStr = "sample"
            forbidden = ["auxQ", "textQ", "dynQ"]
        if p[:4] in forbidden or p[:5] in forbidden:
            if p[:4] == "auxQ":
                return None, (lang.TAB + lang.msgTEnoAuxEdit)
            if p[:5] == "textQ":
                return None, (lang.TAB + lang.msgTEnoTextEdit)
            if p[:4] == "dynQ":
                return None, (lang.TAB + lang.msgTEnoDynEdit)

        t = self.ao.textureLib[tName]
        if p == "path":
            attribute_to_edit = t.path
            for pair in list(self.ao.pathLib.items()):
                if pair[1] == attribute_to_edit:
                    old_name = pair[0]
            path_string = t.path.repr("scPath")
            demo = "%s %s: %s: %s" % (prefaceStr, label, old_name, path_string)
        elif p in (
            "inst",
            "rhythmQ",
            "tRange",
            "beatT",
            "fieldQ",
            "octQ",
            "ampQ",
            "panQ",
        ):
            dataStr = t.pmtrObjDict[p].repr("argsOnly")
            demo = "%s %s: %s" % (prefaceStr, label, dataStr)
        elif p[:4] == "auxQ":
            demo = {}  # here demo is a dictionary!!!
            if t.auxNo < 1:
                return None, (lang.TAB + lang.msgTInoAuxEdit)
            for i, p in basePmtr.auxLabel(t.auxNo, 1):
                dataStr = t.pmtrObjDict[p].repr("argsOnly")
                demo[p] = "%s value for x%i: %s" % (prefaceStr, i, dataStr)
        elif p[:5] == "textQ":
            demo = {}  # here demo is a dictionary
            if t.textPmtrNo < 1:
                return None, (lang.TAB + lang.msgTInoTextEdit)
            for i, p in basePmtr.textLabel(t.textPmtrNo, 1):
                dataStr = t.pmtrObjDict[p].repr("noType")
                demo[p] = "%s value for s%i: %s" % (prefaceStr, i, dataStr)
        elif p[:4] == "dynQ":
            demo = {}  # here demo is a dictionary
            if t.dynPmtrNo < 1:
                return None, (lang.TAB + lang.msgTInoDynEdit)
            for i, p in basePmtr.dynLabel(t.dynPmtrNo, 1):
                dataStr = t.pmtrObjDict[p].repr("argsOnly")
                demo[p] = "%s value for d%i: %s" % (prefaceStr, i, dataStr)
        else:
            return None, lang.msgTIbadPmtrName
        if drawer.isStr(demo):  # adjust prompt
            demo = demo + "\nnew value:"
            demoAdjust = ""
        else:  # only for aux demo, as it is a list
            demoAdjust = "\nnew value:"
        return demo, demoAdjust

    def _tiEvalUsrStr(self, usrStr, p=None, tName=None):
        """Filter and evaluate user-entered string data. Used for all TIe commands, whenever user is giving complex arguments for ParameterObjects. Also used for command line TIe argument passing

        optionally check if p is supported in this tName
            this optional b/c w/ TIe, know which texture
            w/ TEe, data is evaluated before a texture is selected
        note: this calls re-stringulation with _strRawToData method

        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> a = Command(ao)
        >>> a._tiEvalUsrStr('ru,0,1')
        (('ru', 0, 1), '')
        >>> a._tiEvalUsrStr('ru, 0, 1')
        (('ru', 0, 1), '')
        >>> a._tiEvalUsrStr('cf, "a quoted string"')
        (('cf', 'a quoted string'), '')
        """
        if tName != None:
            if (
                p in self.ao.textureLib[tName].pmtrCommon
                and p not in self.ao.textureLib[tName].pmtrActive
            ):
                return None, "no %s parameter in TI %s\n" % (p, tName)
        usrDataEval, msg = self._strRawToData(usrStr, lang.msgTIeditArgError)
        # do parameter specific adjustments
        if p == "path":  # given  a string arg, retrurn the reference to e path
            if usrDataEval not in list(self.ao.pathLib.keys()):
                return None, "no path named %s.\n" % str(usrDataEval)
            usrDataEval = self.ao.pathLib[usrDataEval]  # get reference of path
        elif p == "tRange":  # must be a number
            if not drawer.isList(usrDataEval):
                return None, "enter two time values seperated by a comma.\n"
        elif p == "inst":  # must be a number
            if not drawer.isInt(usrDataEval):
                return None, "instrument number must be an integer.\n"
        elif p == None:  # case of evaluating user parameter obs w/o a texture
            pass  #  may returns a string as usrDataEval; cannot check for errors
        return usrDataEval, msg

    def _tiCompleteEditData(self, p, usrDataEval, textureName):
        """autocompletes special parameter argument lists
        if an error is found, returns None and a msg

        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> a = Command(ao)
        >>> a._tiCompleteEditData('a', ('ru', 0, 1), None)
        (('ru', 0, 1), None)

        """
        msg = None  # if an error is found, store string
        if p == "tRange":
            evalData = ("staticRange", usrDataEval)
        elif p == "inst":
            evalData = ("staticInst", usrDataEval, "%s" % (self.ao.orcObj.name))
        elif p[:5] == "textQ":  # add option name
            # single arguments will not be evaluated as a list
            if not drawer.isList(usrDataEval):
                usrDataEval = [
                    usrDataEval,
                ]
            try:  # this may raise a ValueError
                pmtrName = self.ao.textureLib[textureName].getTextStaticName(p)
                evalData = tuple(
                    [
                        pmtrName,
                    ]
                    + list(usrDataEval)
                )
            except ValueError as e:
                evalData = None
                msg = e  # store error message
        else:  # all other parameters return unmodified
            evalData = usrDataEval
        return evalData, msg

    def _tiEdit(self, tName, p, usrDataEval, refresh=1):
        """edits a parameter using a texture's built in method
        if p == None (no parameter given) will refresh all data
        by creating new scores; this is useful for mode changes and the like.
        will update all clones if edit is succesful and refresh is true
        refresh: can turn off generating a new score"""
        # if this texture has any clones, those will need to be updated
        t = self.ao.textureLib[tName]
        ok, msg = t.editPmtrObj(p, usrDataEval, refresh)
        # do post edit updates external to the texture object
        if ok:
            if p == "inst":  # if parameter is an instrument, update clone
                for cName in self.ao.cloneLib.cNames(tName):
                    c = self.ao.cloneLib.get(tName, cName)
                    c.updatePmtrObj("inst", t.getRefClone())
                # if 'midiPercussion' event mode, must also create a path
                if self.ao.activeEventMode == "midiPercussion":
                    if t.getInstOrcName() == "generalMidiPercussion":
                        environment.printWarn("creating and updating path")
                        pRef = self._piAutoCreateMidiPercussion(t.getInst())
                        # must update path as well
                        ok, msg = t.editPmtrObj("path", pRef, refresh)

            # rescoring all clones will update tRefAbs values
            if refresh:
                for cName in self.ao.cloneLib.cNames(tName):
                    c = self.ao.cloneLib.get(tName, cName)
                    c.score(t.getScore(), t.getRefClone())
        return ok, msg

    def _tiRefresh(self, tName):
        """refrsh textures and clones alone: not associated with editing a
        parameter; will create new esObj in textures, and pas these to clones
        note: there is a different way to refresh inside the Performer and
        EventSequenceSplit objects; these are done all all textures
        when event lists are created
        """
        t = self.ao.textureLib[tName]
        ok = t.score()
        if not ok:
            return ok, "Texture %s contains incompatible ParameterObjects"
        for cName in self.ao.cloneLib.cNames(tName):
            c = self.ao.cloneLib.get(tName, cName)
            c.score(t.getScore(), t.getRefClone())
        return ok, ""  # good

    def _tcEdit(self, tName, cName, p, usrDataEval, refresh=1):
        """edits clone parameter objects
        will provide clone with most recent texture esObj
        """
        t = self.ao.textureLib[tName]
        c = self.ao.cloneLib.get(tName, cName)
        ok, msg = c.editPmtrObj(p, usrDataEval, t.getRefClone(), t.getScore(), refresh)
        return ok, msg

    def _tiGetNewName(self, query):
        """asks user for a texture name, checking against existing paths"""
        while 1:
            name = dialog.askStr(query, self.termObj)
            if name == None or name == "":
                return None
            name = self._nameReplace(name)
            if self._nameTest(name) != None:
                dialog.msgOut(self._nameTest(name), self.termObj)
            elif name in self.ao.textureLib:
                dialog.msgOut(lang.msgTInameTaken, self.termObj)
            else:
                return name

    def _tiRemove(self, name):  # args is name of texture
        if name in list(self.ao.textureLib.keys()):
            self.ao.textureLib[name].path.refDecr()
            del self.ao.textureLib[name]  # del object
            if name in self.ao.cloneLib.tNames():  # del clone dict,if exists
                self.ao.cloneLib.delete(name)  # deletes all clones w/ this text
            if name == self.ao.activeTexture:
                if len(list(self.ao.textureLib.keys())) == 0:
                    self.ao.activeTexture = ""
                else:  # gets a random texture to replace
                    self.ao.activeTexture = random.choice(
                        list(self.ao.textureLib.keys())
                    )
            return "TI %s destroyed.\n" % name
        else:
            return None  # error

    def _tpConvertPmtrObj(self, usrStr):
        """convert pmtr string to pmtr obj"""
        # allow th use of direct integer number specifications
        if usrStr == None:  # if a bad string is given, for example
            return 0, "missing arguments"
        usrNum, junk = drawer.strExtractNum(usrStr, ".")  # accept period
        if len(usrNum) == len(usrStr):  # all numbers, no floats
            usrStr = "c,%s" % usrNum
        # perform nomal procedures
        usrDataEval, msg = self._tiEvalUsrStr(usrStr, None)
        if usrDataEval == None:
            return 0, msg
        try:
            obj = parameter.factory(usrDataEval, "g")
        except error.ParameterObjectSyntaxError as e:
            return 0, e
        return 1, obj

    def _tpGetPmtrObj(self, query):
        """returns None or a instantiated object"""
        while 1:
            poStr = dialog.askStr(query, self.termObj)
            if poStr == None:
                return None
            # msg may be object
            ok, msg = self._tpConvertPmtrObj(poStr)
            if not ok:
                # note: this does not format correctly, may double tab
                # may also preface as a TIe ERROR, though this is wrong
                dialog.msgOut("%s%s\n" % (lang.TAB, msg), self.termObj)
                continue
            return msg  # msg is object

    def _teGetTimeMapDict(self):
        tiMapDict = {}  # clear
        # muteList = self._tiMuteList()
        for tName in list(self.ao.textureLib.keys()):
            t = self.ao.textureLib[tName]
            tiMapDict[tName] = {}  # add a dictionary w/ name for key
            tiMapDict[tName]["tRange"] = t.timeRangeAbs  # this is abs time
            tiMapDict[tName]["muteStatus"] = t.mute
            tiMapDict[tName]["cloneDict"] = {}
            if tName in self.ao.cloneLib.tNames():
                # need to get and esObj to get time range
                for cName in self.ao.cloneLib.cNames(tName):
                    c = self.ao.cloneLib.get(tName, cName)
                    # need to suply ref dict to clone from parent texture
                    tiMapDict[tName]["cloneDict"][cName] = {}
                    tiMapDict[tName]["cloneDict"][cName]["tRange"] = c.timeRangeAbs
                    tiMapDict[tName]["cloneDict"][cName]["muteStatus"] = c.mute
        return tiMapDict

    def _teGetTotalTimeRange(self, tiMapDict=None):
        """look at all textures and clones, find amximal range"""
        if tiMapDict == None:
            tiMapDict = self._teGetTimeMapDict()
        startTime = 0
        endTime = 0
        for tName in list(tiMapDict.keys()):
            s, e = tiMapDict[tName]["tRange"]
            if s <= startTime:
                startTime = s
            if e >= endTime:
                endTime = e
            for cName in list(tiMapDict[tName]["cloneDict"].keys()):
                s, e = tiMapDict[tName]["cloneDict"][cName]["tRange"]
                # check for a clone that is longer
                if s <= startTime:
                    startTime = s
                if e >= endTime:
                    endTime = e
        totalDur = endTime - startTime
        return startTime, endTime, totalDur  # all in seconds

    # -----------------------------------------------------------------------||--
    def _tcTestExistance(self, tName):
        """test if this texxture has any clones"""
        if self.ao.cloneLib.number(tName) == 0:
            return lang.msgTCcreateFirst
        else:
            return None

    def _tcGetNewName(self, query, textureName):
        """asks user for a texture clone name, checking against existing paths"""
        while 1:
            name = dialog.askStr(query, self.termObj)
            if name == None:
                return None
            name = self._nameReplace(name)
            if self._nameTest(name) != None:
                dialog.msgOut(self._nameTest(name), self.termObj)
            elif self.ao.cloneLib.cExists(textureName, name):
                dialog.msgOut(lang.msgTCnameTaken, self.termObj)
            else:
                return name

    def _tcGetDemo(self, tName, cName, p, label, type="edit"):
        """p is the parameter key
        used edit commands to provide an exmaple to user of entry format
        label is string used to describe p
        """
        if type == "edit":
            prefaceStr = "current"
            forbidden = []  # not used in clone
        elif type == "listedit":
            prefaceStr = "sample"
            forbidden = []

        t = self.ao.textureLib[tName]
        c = self.ao.cloneLib.get(tName, cName)
        if p in ("time", "sus", "acc", "fieldQ", "octQ", "ampQ", "panQ"):
            dataStr = c.pmtrObjDict[p].repr("argsOnly")
            demo = "%s %s: %s" % (prefaceStr, label, dataStr)
        elif p[:4] == "auxQ":
            demo = {}  # here demo is a dictionary!!!
            if t.auxNo < 1:
                return None, (lang.TAB + lang.msgTCnoAuxEdit)
            for i, p in basePmtr.auxLabel(c.auxNo, 1):
                dataStr = c.pmtrObjDict[p].repr("argsOnly")
                demo[p] = "%s value for x%i: %s" % (prefaceStr, i, dataStr)
        elif p[:6] == "cloneQ":
            demo = {}  # here demo is a dictionary
            if t.textPmtrNo < 1:
                return None, (lang.TAB + lang.msgTInoTextEdit)
            for i, p in basePmtr.cloneLabel(c.clonePmtrNo, 1):
                dataStr = c.pmtrObjDict[p].repr("noType")
                demo[p] = "%s value for c%i: %s" % (prefaceStr, i, dataStr)
        else:
            return None, lang.msgTCbadPmtrName

        if drawer.isStr(demo):  # adjust prompt
            demo = demo + "\nnew value:"
            demoAdjust = ""
        else:  # only for aux demo, as it is a list
            demoAdjust = "\nnew value:"
        return demo, demoAdjust

    def _tcEvalUsrStr(self, usrStr, p):
        """filter and evaluate user entered data"""
        usrDataEval, msg = self._strRawToData(usrStr, lang.msgTCeditArgError)
        return usrDataEval, msg

    def _tcCompleteEditData(self, p, usrDataEval, tName, cName):
        """autocompletes special parameter argument lists"""
        if p[:6] == "cloneQ":  # add option name
            # single arguments will not be evaluated as a list
            if not drawer.isList(usrDataEval):
                usrDataEval = [
                    usrDataEval,
                ]
            clone = self.ao.cloneLib.get(tName, cName)
            pmtrName = clone.getCloneStaticName(p)
            evalData = tuple(
                [
                    pmtrName,
                ]
                + list(usrDataEval)
            )
        else:  # all other parameters return unmodified
            evalData = usrDataEval
        return evalData

    # -----------------------------------------------------------------------||--
    def _elCheckInstrumentNo(self, instNo):
        """checks if instrument exists. if true, returns number
        if no inst, return None
        """
        if not drawer.isInt(instNo):
            try:
                instNo = int(instNo)  # covnert to int
            except (ValueError, SyntaxError, NameError, TypeError):
                return None
        # test if number is valid
        if self.ao.orcObj.instNoValid(instNo):
            return instNo
        else:
            return None

    def _elGetInstrumentNo(self):
        """asks user for instrument number, displays list if asked"""
        # instInfo, instNoList = self.ao.orcObj.getInstInfo()
        # get a user string for representing the list of instruments
        instNoStr = self.ao.orcObj.instNoList("user")
        while 1:
            if instNoStr == None:
                usrStr = dialog.askStr("enter any instrument number:", self.termObj)
            else:
                usrStr = dialog.askStr(
                    'enter instrument number:\n%s\nor "?" for instrument help:'
                    % instNoStr,
                    self.termObj,
                )
            if usrStr == None:
                return None
            testCmdStr = usrStr.lower()
            if testCmdStr == "":
                return None
            elif testCmdStr in ["?", "eli", "i"]:
                cmdObj = EMi(self.ao)
                ok, instrumentInfo = cmdObj.do()
                dialog.msgOut(instrumentInfo, self.termObj)
                continue
            inst = self._elCheckInstrumentNo(testCmdStr)
            if inst == None:
                dialog.msgOut(lang.msgEMnoInstrument, self.termObj)
            else:
                return inst


# -----------------------------------------------------------------||||||||||||--
# non standard commands


# display cmds
class w(Command):
    """w display

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = w(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "w"

    def display(self):
        return "%s\n" % self.ao.help.w


class c(Command):
    """w display
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = c(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "c"

    def display(self):
        return "%s\n" % self.ao.help.c


class r(Command):
    """r display

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = c(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "r"

    def display(self):
        return "%s\n" % lang.msgCredits


class cmd(Command):
    """cmd display

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = cmd(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "cmd"

    def display(self):
        return self.ao.cmdDisplay()


class bug(Command):
    """bug test command

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = bug(ao)
    >>> post = a.do()
    Traceback (most recent call last):
    TestError
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1
        self.gatherSwitch = 0
        self.cmdStr = "bug"

    def process(self):
        raise error.TestError


class clear(Command):
    """clear the screen

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = clear(ao)
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0
        self.gatherSwitch = 0
        self.cmdStr = "clear"

    def display(self):
        self.termObj.clear()


class py(Command):
    """start a python interactive

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = py(ao)
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0
        self.gatherSwitch = 0
        self.subCmd = 1  # if 1, executed within method of interptreter
        self.cmdStr = "py"

    def result(self):
        return {}  # dict required return


class shell(Command):
    """fire a shell command

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = shell(ao)
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0
        self.gatherSwitch = 1
        self.subCmd = 1  # if 1, executed within method of interptreter
        self.cmdStr = "shell"

    def gather(self):
        """optional argument for command of help desired"""
        self.usrStr = None
        if self.args != "":
            self.args = argTools.ArgOps(self.args)  # no strip
            self.usrStr = self.args.get(0, "end", "off", "space")
        else:
            return lang.msgReturnCancel

    def result(self):
        return {"shellCmd": self.usrStr}  # dict required return


class help(Command):
    """translates ? to help in   Interpreter._lineCmdArgSplit

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = help(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "help"

    def gather(self):
        """optional argument for command of help desired"""
        self.usrStr = None
        if self.args != "":
            self.args = argTools.ArgOps(self.args)  # no strip
            self.usrStr = self.args.get(0, "end", "off", "space")

    def display(self):
        """of arg given, does help command. if no hard, help menu printed
        needs to be interpreter; in order to have access to Interpreter"""
        if self.usrStr:  # get help file
            return self.ao.help.reprCmd(self.usrStr)
        else:  # print listing of all commands
            # sorted commands by theose that exists, and those that have docs
            cmdsDoc, cmdsUndoc, helpTopics = self.ao.cmdDocManifest()
            h, w = self.termObj.size()
            msg = []
            msg.append(lang.DIVIDER * w)
            msg.append(lang.msgDocAdditionalHelp)
            msg.append(lang.msgDocCmd)
            # msg.append(lang.msgDocPrefix)
            msg.append(lang.msgDocBrowser)
            msg.append(lang.msgDocHead)
            msg.append(lang.DIVIDER * w)
            msg.append(typeset.formatEqCol("", cmdsDoc, 10, w))
            if len(helpTopics) > 0:
                msg.append(lang.DIVIDER * w)
                msg.append(typeset.formatEqCol("", helpTopics, 10, w))
            if len(cmdsUndoc) > 0:
                msg.append(lang.DIVIDER * w)
                msg.append(typeset.formatEqCol("", cmdsUndoc, 10, w))
            return "".join(msg)


class man(help):
    """alias to help command
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = man(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        help.__init__(self, ao, args, **keywords)


class quit(Command):
    "SUBCMD"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "quit"
        self.subCmd = 1  # if 1, executed within method of interptreter

    def gather(self):
        args = self.args
        self.confirm = ""
        if args != "":
            args = argTools.ArgOps(args)
            self.confirm = args.get(0, "end")
        if self.confirm != "confirm":
            askUsr = dialog.askYesNo("exit athenaCL? ", 0, self.termObj)
            if askUsr != 1:
                return lang.msgReturnCancel
            self.confirm = "confirm"

            # only do this if user has interactively confirmed quit
            if self.ao.external.logCheck() == 1:  # log exists, submit
                ckUser = dialog.askYesNo(lang.msgSubmitLog, 0, self.termObj)
                if ckUser == 1:
                    result = self.ao.external.logSend()
                    if result == None:  # nothing happend
                        dialog.msgOut(lang.msgSubmitLogFail, self.termObj)
                    else:
                        dialog.msgOut(lang.msgSubmitLogSuccess, self.termObj)

    def result(self):
        return {"confirm": 1}


class q(quit):
    """alias to quit command"""

    def __init__(self, ao, args="", **keywords):
        quit.__init__(self, ao, args, **keywords)


# -----------------------------------------------------------------||||||||||||--


class PIals(Command):
    """list all attributes of a path,  a hidden function

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIals(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "PIals"

    def gather(self):
        pass

    def process(self):
        pass

    def display(self):
        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists() != None:  # check name
            return self._piTestNameExists()
        directoryOfattributes = dir(self.ao.pathLib[self.ao.activePath])
        msg = []
        msg.append("attributes of PI %s:\n" % self.ao.activePath)
        entryLines = []
        for entry in directoryOfattributes:
            value = getattr(self.ao.pathLib[self.ao.activePath], entry)
            value = str(value).replace(" ", "")
            entryLines.append([entry, value])
        headerKey = ["name", "value"]
        minWidthList = [lang.LMARGINW, 0]
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class PIn(Command):
    """creates a path instance
    args are given as:
    args: pin  name  eval(pathString)

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIn(ao, args='b 8,12,21,34')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIn"

    def _piGetMultisetList(self):
        """gets a list pitch space sets good for making a path"""
        objList = []
        currentPosition = 0
        while 1:
            data = self.setFactory(self.ao, None)
            if data == None:
                return None  # lang.msgMCerrorCreatingChord
            objList.append(data)
            query = lang.TAB + "add another set?"
            askUsr = dialog.askYesNoCancel(query, 1, self.termObj)
            if askUsr == 1:
                currentPosition = currentPosition + 1
                continue  # return to top of loop if yes
            elif askUsr == -1:
                return None
            elif askUsr == 0:
                return objList

    def _piMultisetListToStr(self, objList):
        "used to convert object data into strings for log"
        msg = []
        for obj in objList:
            msg.append(obj.repr("psReal"))
        return " ".join(msg)  # separate with spaces

    def gather(self):
        args = self.args
        self.name = None
        self.dataList = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            self.name = args.get(0)
            if self.name == None:
                return self._getUsage()
            if self._nameTest(self.name) != None:
                return self._getUsage(self._nameTest(self.name))
            pssList = args.list(1, "end")  #
            if pssList == None:
                return self._getUsage()
            self.dataList = []
            for setStr in pssList:  # converts to string
                a = self.setFactory(self.ao, setStr)
                if a == None:
                    break
                self.dataList.append(a)
            if len(self.dataList) < 1:
                self.dataList = None
        if self.name == None or self.dataList == None:  # get frm user
            self.name = self._piGetNewName(lang.msgPInameGet)
            if self.name == None:
                return lang.msgReturnCancel
            self.dataList = self._piGetMultisetList()
            if self.dataList == None:
                return lang.msgPIcancel

    def process(self):
        self.ao.pathLib[self.name] = pitchPath.PolyPath(self.name)
        self.ao.pathLib[self.name].loadMultisetList(self.dataList)  # does updates
        self.ao.activePath = self.name

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s %s" % (
                self.cmdStr,
                self.name,
                self._piMultisetListToStr(self.dataList),
            )

    def display(self):
        return "PI %s added to PathInstances.\n" % self.name


class PIv(Command):
    """displays a path

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()

    >>> a = PIn(ao, args='a 3-2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIv(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIv"

    def gather(self):
        args = self.args
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.nameToView = args.get(0)
        else:
            self.nameToView = self.ao.activePath
        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists(self.nameToView) != None:  # check name
            return self._piTestNameExists(self.nameToView)

    def process(self):
        pass

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.nameToView)

    def display(self):
        nameToView = self.nameToView

        msg = []
        msg.append("PI: %s\n" % (nameToView))
        entryLines = []
        dataList = [
            "psPath",
        ]
        dataList = dataList + self.ao.pathLib[nameToView].reprList("psPath")
        entryLines.append(dataList)

        # show ps note names
        dataList = [
            "",
        ] + self.ao.pathLib[
            nameToView
        ].reprList("psName")
        entryLines.append(dataList)

        dataList = [
            "pcsPath",
        ]
        dataList = dataList + self.ao.pathLib[nameToView].reprList("pcsPath")
        entryLines.append(dataList)

        dataList = [
            "scPath",
        ]
        dataList = dataList + self.ao.pathLib[nameToView].reprList("scPath")
        entryLines.append(dataList)

        dataList = [
            "durFraction",
        ]
        dataList = dataList + self.ao.pathLib[nameToView].reprList("dur")
        entryLines.append(dataList)

        headerKey = []
        minWidthList = (lang.LMARGINW,)
        bufList = []  # use default
        justList = []  # useDefault
        tableA = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
            "bundle",
            2,
        )
        msg.append("%s\n" % tableA)
        if self.ao.pathLib[nameToView].refCount == 0:
            msg.append("TI References: none.\n")
        else:
            entryLines = []
            label = "TI References (%s): " % self.ao.pathLib[nameToView].refCount
            listOfTInames = []
            for tName in list(self.ao.textureLib.keys()):
                if (
                    self.ao.textureLib[tName].path.name
                    == self.ao.pathLib[nameToView].name
                ):
                    listOfTInames.append(tName)
            nameStr = []
            for entry in listOfTInames:
                nameStr.append("%s" % entry)
                if entry != listOfTInames[-1]:  # not last
                    nameStr.append(", ")
            entryLines.append([label, "".join(nameStr)])
            headerKey = []
            minWidthList = (lang.LMARGINW, 0)
            bufList = [0, 1]
            justList = ["c", "l"]
            tableB = typeset.formatVariCol(
                headerKey,
                entryLines,
                minWidthList,
                bufList,
                justList,
                self.termObj,
                "oneColumn",
            )
            msg.append("%s\n" % tableB)

        #         if self.ao.pathLib[nameToView].voiceType == 'none':
        #             msg.append('PathVoices: none.\n')
        #         else:    ## this is the vl list command
        #             entryLines = []
        #             msg.append('PathVoices:\n')
        #             groupNames = self.ao.pathLib[nameToView].voiceNames()
        #             groupNames.sort()
        #             for name in groupNames:
        #                 if name == self.ao.pathLib[nameToView].activeVoice:
        #                     status = lang.ACTIVE
        #                 else: status = lang.INACTIVE
        #                 mapStringList = self.ao.pathLib[nameToView].voiceRepr(name)
        #                 entryLines.append([status, name, mapStringList])
        #             headerKey    = []
        #             minWidthList = (lang.TABW, lang.NAMEW, 0)
        #             bufList      = [0, 1, 0]
        #             justList         = ['c','l','l']
        #             tableC = typeset.formatVariCol(headerKey, entryLines, minWidthList,
        #                                         bufList, justList, self.termObj,
        #                                         'twoColumn')
        #             msg.append('%s\n' % tableC)

        return "".join(msg)


class PIe(Command):
    """edits a single set of a path

    TODO: does not yet accept command args, and thus cannot be remotely tested
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIe"

    def _piConvertEditType(self, usrStr):
        ref = {
            "t": ["t", "transpose"],
            "r": ["r", "replace"],
            "i": ["i", "invert"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr  # may be None

    def _piGetEditType(self, oldSet):
        query = "replace, transpose, or invert set %s: (r, t, or i):"
        while 1:
            usrStr = dialog.askStr(query % drawer.listToStr(oldSet), self.termObj)
            if usrStr == None:
                return None
            transType = self._piConvertEditType(usrStr)
            if transType == None:
                continue
            else:
                return transType  # either l or m

    def _piConvertTransType(self, usrStr):
        ref = {
            "l": ["l", "literal"],
            "m": ["m", "modulus"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr  # may be None

    def _piGetTransType(self):
        query = "enter a transposition method: literal or modulus? (l or m):"
        while 1:
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            transType = self._piConvertTransType(usrStr)
            if transType == None:
                continue
            else:
                return transType  # either l or m

    def _piConvertTransposition(self, usrStr, transType):
        if usrStr == None:
            return None
        transInt = drawer.strToNum(usrStr, "int")
        if transInt == None:
            return None
        if transType == "m":  # modulous
            return transInt % 12
        elif transType == "l":  # literal
            return transInt

    def _piGetMatchingSet(self, sizeToMatch):
        """used pie to get a set of the smae size as a sorouce"""
        while 1:
            setObj = self.setFactory(self.ao, None)
            if setObj == None:
                return None
            if len(setObj) == sizeToMatch:
                return setObj
            else:
                query = "%sincorrect set size: enter a set of %s elements.\n" % (
                    lang.TAB,
                    sizeToMatch,
                )
                dialog.msgOut(query, self.termObj)
                continue

    def _piGetTransposition(self, transType):
        """gets transposition form user
        modules does mod 12 to value entered
        """
        if transType == "m":
            query = "enter a positive or negative transposition between 1 and 11:"
        elif transType == "l":
            query = "enter a positive or negative transposition:"
        while 1:
            trans = dialog.askStr(query, self.termObj)
            if trans == None:
                return None
            trans = self._piConvertTransposition(trans, transType)
            if trans == None:  # error encountered
                continue
            else:
                return trans

    def gather(self):
        """does not yet accept command line args"""
        args = self.args

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists() != None:  # check name
            return self._piTestNameExists()

        name = self.ao.activePath
        oldUsrPath = self.ao.pathLib[name].get("psPath")
        noSets = len(oldUsrPath)
        length = len(self.ao.pathLib[name])

        query = "edit PI %s\nenter position to edit" % name
        # start at 2, second position
        locInt = self._piGetPathPosition(query, 1, noSets)
        if locInt == None:
            return lang.msgReturnCancel
        locInt = locInt - 1  # correct to list spacing

        self.oldPos = locInt
        oldSet = self.ao.pathLib[self.ao.activePath].copyMultiset(self.oldPos)
        oldSetPsReal = oldSet.get("psReal")
        oldSize = len(oldSet)

        self.editType = self._piGetEditType(oldSetPsReal)
        if self.editType == None:
            return lang.msgReturnCancel

        if self.editType == "t":  ## transpose
            transType = self._piGetTransType()
            if transType == None:
                return lang.msgReturnCancel
            self.transInt = self._piGetTransposition(transType)
            if self.transInt == None:
                return lang.msgReturnCancel
        elif self.editType == "r":  # replace
            self.setObj = self._piGetMatchingSet(oldSize)
            if self.setObj == None:
                return lang.msgReturnCancel
        elif self.editType == "i":  # invert
            pass  # no args needed

    def process(self):
        path = self.ao.pathLib[self.ao.activePath]
        if self.editType == "t":
            path.t(self.transInt, self.oldPos)  # call invert method
        elif self.editType == "r":  # replace
            path.insert(self.setObj, self.oldPos)  # call insert method
        elif self.editType == "i":  # invert
            path.i(self.oldPos)  # call invert method

    def display(self):
        return "PI %s edited.\n" % self.ao.activePath


class PIdf(Command):
    """duration fraction settings
        uses currently selected path
        user can enter a list as an arg

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIdf(ao, args='3,2')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIdf"

    def _piConvertDurFraction(self, length, usrStr):
        """checks a list for matching length and all values greater than 0"""
        # this will accept a singel argumetn, lije a string or number
        # without a comma or other, and turn into a list
        durList = drawer.strToSequence(usrStr, length, ["num"])
        if durList == None:  # bad data given
            return None
        for value in durList:
            if value <= 0:  # check for values less than 0
                return None
        return durList

    def _piGetDurFraction(self, length, name):
        """prompts user for a list of values, or values separated by a list"""
        query = "edit PI %s\nenter a list of duration fractions:" % name
        while 1:
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            newDurFraction = self._piConvertDurFraction(length, usrStr)
            if newDurFraction == None:
                dialog.msgOut((lang.msgPIbadDuration % length), self.termObj)
                continue
            else:
                return newDurFraction  # list of values greater than 1

    def gather(self):
        args = self.args

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists() != None:  # check name
            return self._piTestNameExists()
        self.name = self.ao.activePath
        oldDurFraction = self.ao.pathLib[self.name].get("durFraction")
        length = len(self.ao.pathLib[self.name])
        self.newDurFraction = None

        if args != "":
            args = argTools.ArgOps(args)
            self.newDurFraction = self._piConvertDurFraction(length, args.get(0, "end"))
            if self.newDurFraction == None:
                return self._getUsage()

        if self.newDurFraction == None:  # get frm user
            self.newDurFraction = self._piGetDurFraction(length, self.name)
            if self.newDurFraction == None:
                return lang.msgReturnCancel

    def process(self):
        self.ao.pathLib[self.name].loadDur(self.newDurFraction)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, drawer.listScrub(self.newDurFraction))

    def display(self):
        return "PI %s edited.\n" % self.name


class PIls(Command):
    """list all paths

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIls(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIls"

    def gather(self):
        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()

    def process(self):
        pass

    def display(self):
        msg = []
        msg.append("PathInstances available:\n")
        entryLines = []
        pathNames = list(self.ao.pathLib.keys())
        pathNames.sort()
        for name in pathNames:
            pathStr = self.ao.pathLib[name].repr("scPath")
            if name == self.ao.activePath:
                status = lang.ACTIVE
            else:
                status = lang.INACTIVE
            refNo = self.ao.pathLib[name].refCount
            # noGroup  = len(self.ao.pathLib[name].voiceNames())
            entryLines.append([status, name, refNo, pathStr])
        headerKey = ["", "name", "TIrefs", "scPath"]
        minWidthList = (lang.TABW, lang.NAMEW, 3, 3, 0)
        bufList = [0, 1, 1, 1, 0]
        justList = ["c", "l", "l", "l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "fourColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class PIcp(Command):
    """copies a path

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIcp(ao, args = 'a b')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIcp"

    def _piCopy(self, srcName, dstName):
        """copies one path to new path"""
        if (
            srcName != dstName
            and srcName in self.ao.pathLib
            and dstName not in list(self.ao.pathLib.keys())
        ) == 1:
            # sets name attribute
            self.ao.pathLib[dstName] = self.ao.pathLib[srcName].copy(dstName)
            self.ao.activePath = dstName
            return "PI %s added to PathInstances.\n" % dstName
        else:
            return None

    def gather(self):
        args = self.args
        self.cpList = []
        self.oldName = None

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            msg = []
            self.oldName = drawer.inList(args.get(0), list(self.ao.pathLib.keys()))
            if self.oldName == None:
                return self._getUsage()
            if args.list(1, "end") != None:
                for newName in args.list(1, "end"):
                    self.cpList.append(newName)
            else:
                return self._getUsage()

        if self.cpList == []:
            self.oldName = self._chooseFromList(
                "select a path to copy:", list(self.ao.pathLib.keys()), "case"
            )
            if self.oldName == None:
                return lang.msgPIbadName
            query = "name the copy of path %s:" % self.oldName
            name = self._piGetNewName(query)
            if name == None:
                return lang.msgReturnCancel
            self.cpList.append(name)

    def process(self):
        self.report = []
        for name in self.cpList:
            msg = self._piCopy(self.oldName, name)
            if msg != None:  # fall through if fails
                self.report.append(msg)
            else:
                self.report.append(lang.msgBadArgFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s %s" % (
                self.cmdStr,
                self.oldName,
                self._strListToArgList(self.cpList),
            )

    def display(self):
        return "".join(self.report)


class PIrm(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIrm(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIrm"

    def _piRemove(self, name):  # args is name of path
        if name in list(self.ao.pathLib.keys()):
            # this is 0 when there are no longer any TIs that link to this path
            if self.ao.pathLib[name].refCount != 0:
                return (
                    'PI %s is being used by %i Textures. either delete Textures ("TIrm") or change their Path ("TIe").\n'
                    % (name, self.ao.pathLib[name].refCount)
                )
            if name == self.ao.activePath:
                self.ao.activePath = ""
            del self.ao.pathLib[name]
            if name == self.ao.activePath:
                if len(list(self.ao.pathLib.keys())) == 0:
                    self.ao.activePath = ""
                else:
                    self.ao.activePath = random.choice(list(self.ao.pathLib.keys()))
            return "PI %s destroyed.\n" % name
        else:
            return None  # error

    def gather(self):
        args = self.args
        self.rmList = []

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            msg = []
            if args.list(0, "end") != None:
                for name in args.list(0, "end"):
                    name = drawer.inList(name, list(self.ao.pathLib.keys()))
                    if name == None:
                        return self._getUsage()
                    self.rmList.append(name)
            else:
                return self._getUsage()
        if self.rmList == []:
            name = self._chooseFromList(
                "select a path to delete:", list(self.ao.pathLib.keys()), "case"
            )
            if name == None:
                return lang.msgPIbadName
            query = "are you sure you want to delete path %s?"
            askUsr = dialog.askYesNoCancel((query % name), 1, self.termObj)
            if askUsr == 1:
                self.rmList.append(name)
            else:
                return lang.msgReturnCancel

    def process(self):
        self.report = []
        for name in self.rmList:
            str = self._piRemove(name)
            if str != None:
                self.report.append(str)
            else:
                self.report.append(lang.msgBadArgFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self._strListToArgList(self.rmList))

    def display(self):
        return "".join(self.report)


class PIo(Command):
    """sets self.ao.activePath
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIn(ao, args='b 2@3')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIo(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIo"

    def gather(self):
        args = self.args
        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        self.name = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = drawer.inList(args.get(0), list(self.ao.pathLib.keys()))
            if self.name == None:
                return self._getUsage()
        if self.name == None:
            self.name = self._chooseFromList(
                "select a path to activate:", list(self.ao.pathLib.keys()), "case"
            )
            if self.name == None:
                return lang.msgPIbadName

    def process(self):
        self.ao.activePath = self.name

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.name)

    def display(self):
        return "PI %s now active.\n" % self.ao.activePath


class PImv(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PImv(ao, args='a b')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PImv"

    def _piMove(self, oldPathName, newPathName):
        """renames a path, appending underscore if duplicate
        updates dependencies in self.ao.textureLib
        """
        if newPathName == oldPathName:
            while newPathName == oldPathName:
                newPathName = newPathName + "_"
        else:
            pass  # use args
        textureBinRef = self.ao.textureLib
        pathBinRef = self.ao.pathLib

        # this copies reference numbers (to TIs) (number, not name)
        pathBinRef[newPathName] = pathBinRef[oldPathName]
        # set at init, must change after copy
        pathBinRef[newPathName].name = newPathName
        for key in list(textureBinRef.keys()):
            ### change
            if textureBinRef[key].path.name == oldPathName:  # had old name
                # sets attribute obj, name, value
                setattr(textureBinRef[key], "path", pathBinRef[newPathName])
        del pathBinRef[oldPathName]
        return newPathName

    def gather(self):
        args = self.args

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists() != None:  # check name
            return self._piTestNameExists()

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            oldPathName = drawer.inList(args.get(0), list(self.ao.pathLib.keys()))
            if oldPathName == None:
                return self._getUsage()
            newPathName = args.get(1)
            if newPathName == None:
                return self._getUsage()
        else:  # only works with args
            return lang.msgReturnCancel
        self.newPathName = newPathName
        self.oldPathName = oldPathName

    def process(self):
        # may change name here
        self.newPathName = self._piMove(self.oldPathName, self.newPathName)
        self.ao.activePath = self.newPathName

    def display(self):
        return "PI %s moved to PI %s.\n" % (self.oldPathName, self.ao.activePath)


class PIret(Command):
    """create new path as a retrograde of current path

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIret(ao, args='e')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIret"

    def gather(self):
        args = self.args

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists() != None:  # check name
            return self._piTestNameExists()
        newName = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            newName = args.get(0)
        if newName == None:
            query = "name this retrograde of path %s:" % self.ao.activePath
            newName = self._piGetNewName(lang.msgPInameGet)
            if newName == None:
                return lang.msgReturnCancel
        self.newName = newName
        self.oldName = self.ao.activePath

    def process(self):
        self.ao.pathLib[self.newName] = self.ao.pathLib[self.oldName].copy(self.newName)
        self.ao.pathLib[self.newName].retro()
        self.ao.activePath = self.newName

    def display(self):
        return "retrograde PI %s added to PathInstances.\n" % self.ao.activePath


class PIrot(Command):
    """create new path as a rotation of current path
    since this is a rotation, cannot copy old maps over to new PI
    args: pirot  name    startPosition

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23, 2-3')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIrot(ao, args='b 2')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIrot"

    def gather(self):
        args = self.args

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists() != None:  # check name
            return self._piTestNameExists()
        self.newName = None
        self.rotZero = None
        self.oldName = self.ao.activePath
        self.length = len(self.ao.pathLib[self.oldName])

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            self.newName = args.get(0)
            if self.newName == None:
                return self._getUsage()
            self.rotZero = args.get(1, "single", "eval")
            self.rotZero = self._checkInRange(self.rotZero, 2, self.length)
            if self.rotZero == None:
                return self._getUsage()
        if self.newName == None or self.rotZero == None:
            query = "name this rotation of path %s:" % self.ao.activePath
            self.newName = self._piGetNewName(lang.msgPInameGet)
            if self.newName == None:
                return lang.msgReturnCancel
            query = "which chord should start the rotation?"
            # start at 2, second position
            self.rotZero = self._piGetPathPosition(query, 2, self.length)
            if self.rotZero == None:
                return lang.msgReturnCancel

    def process(self):
        cut = self.rotZero - 1  # needs to be corrected
        self.ao.pathLib[self.newName] = self.ao.pathLib[self.oldName].copy(self.newName)
        self.ao.pathLib[self.newName].rotate(cut)
        self.ao.activePath = self.newName

    def display(self):
        return "rotation PI %s added to PathInstances.\n" % self.newName


class PIslc(Command):
    """create a new path as a slice of current path
        args: pislc  name    startPos,endPos

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23, 2-3')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIslc(ao, args='b 1')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIslc"

    def gather(self):
        args = self.args

        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        if self._piTestNameExists() != None:  # check name
            return self._piTestNameExists()
        self.oldName = self.ao.activePath
        length = len(self.ao.pathLib[self.oldName])
        self.newName = None
        self.sl = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            self.newName = args.get(0)
            if self.newName == None or self.newName == self.oldName:
                return self._getUsage()
            self.sl = self._convertListRange(args.get(1), 1, length)
            if self.sl == None:
                return self._getUsage()
        if self.newName == None or self.sl == None:
            query = "name this slice of path %s:" % self.oldName
            self.newName = self._piGetNewName(query)
            if self.newName == None:
                return lang.msgReturnCancel
            query = "which chords should bound the slice? (positions 1 - %i):"
            self.sl = self._piGetIntegerRange(query % length, 1, length)
            if self.sl == None:
                return lang.msgReturnCancel

        self.sl[1] = self.sl[1] + 1  # add one for proper last position

    def process(self):
        self.ao.pathLib[self.newName] = self.ao.pathLib[self.oldName].copy(self.newName)
        self.ao.pathLib[self.newName].slice(self.sl)
        self.ao.activePath = self.newName

    def display(self):
        return "slice PI %s added to PathInstances.\n" % self.ao.activePath


class PIh(Command):
    """create an event list of just the current path

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = PIn(ao, args='a 3-2 6,7,23, 2-3')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = PIh(ao) # running will open a player
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "PIh"

    def gather(self):
        if self._piTestExistance() != None:  # check existance
            return self._piTestExistance()
        self.pName = self.ao.activePath
        self.filePath = environment.getTempFile(".xml")
        # self.filePath = self._validScratchFp() # return None on error
        if self.filePath == None:
            return lang.msgReturnCancel

    def process(self):
        p = self.ao.pathLib[self.pName]
        # create a temporary texture w/ this path
        lclTimes = {}
        lclTimes["tRange"] = ("staticRange", (0, 10))
        lclTimes["beatT"] = ("c", 90)
        # use current texture module, ignore refresh status
        t = texture.factory(self.ao.activeTextureModule, "temp")
        t.loadDefault(0, p, self.ao.aoInfo["fpAudioDirs"], lclTimes, "generalMidi")
        self.emObj = eventList.factory("midi", self.ao)
        self.emObj.setRootPath(self.filePath)
        # provide a list of textures to process
        # turn off refreshing for faster processing`
        ok, msg, outComplete = self.emObj.process([t], [], 0)
        self.pathMidi = self.emObj.outFormatToFilePath("midiFile")

    def display(self):
        msg = []
        prefDict = self.ao.external.getPrefGroup("external")
        failFlag = osTools.openMedia(self.pathMidi, prefDict)
        if failFlag == "failed":
            msg.append(lang.msgELhearError % self.pathMidi)
        else:
            # msg.append(lang.msgELhearInit % hPath)
            msg.append(
                "PI %s hear with TM %s complete.\n(%s)\n"
                % (self.pName, self.ao.activeTextureModule, self.pathMidi)
            )
        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--


class TMo(Command):
    """selects currtne texture module

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = TMo(ao, args='da')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TMo"

    def gather(self):
        args = self.args
        choiceList = texture.tmObjs
        self.name = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = texture.tmTypeParser(args.get(0))
            # self.name = drawer.inList(args.get(0), choiceList, 'noCase')
            if self.name == None:
                return self._getUsage()
        if self.name == None:
            self.name = self._chooseFromList(
                "which TextureModule to activate?",
                choiceList,
                "noCase",
                texture.tmTypeParser,
            )
            if self.name == None:
                return lang.msgTMbadName

    def process(self):
        self.ao.activeTextureModule = self.name

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.name)

    def display(self):
        return "TextureModule %s now active.\n" % self.ao.activeTextureModule


class TMv(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = TMv(ao, args='da')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 0  # display only

    def process(self):
        self.mod = texture.factory(self.ao.activeTextureModule)

    def display(self):
        headList, entryLines = self.mod.reprDoc("entryLines")
        headerKey = []
        minWidthList = [lang.LMARGINW, 0]
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        headList.append("%s\n" % table)
        return "".join(headList)


class TMls(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = TMls(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "TMls"

    def gather(self):
        pass

    def process(self):
        pass
        # self.ao.external.reloadTextures()

    def display(self):
        msg = []
        msg.append("TextureModules available:\n")
        entryLines = []
        texture.tmObjs.sort()
        for name in texture.tmObjs:
            if name == self.ao.activeTextureModule:
                activity = lang.ACTIVE
            else:
                activity = lang.INACTIVE
            refCount = 0
            for textName in list(self.ao.textureLib.keys()):
                # see if TIs are using this TM
                if self.ao.textureLib[textName].tmName == name:
                    refCount = refCount + 1
            entryLines.append([activity, name, refCount])

        headerKey = ["", "name", "TIreferences"]
        minWidthList = (lang.TABW, lang.NAMEW, 0)
        bufList = [0, 1, 0]
        justList = ["c", "l", "l"]
        table = typeset.formatVariCol(
            headerKey, entryLines, minWidthList, bufList, justList, self.termObj
        )
        msg.append("%s\n" % table)
        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--
# texture paramter command get help for parameter objects and test parameter obj

# parameter libraries

# parameter.genPmtrObjs
# parameter.rthmPmtrObjs
# parameter.textPmtrObjs

# parameter.filterPmtrObjs
# parameter.clonePmtrObjs


class _CommandTP(Command):

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)

    def _tpGetLib(self, mode):
        """get a listing of texture parameters based on texture, clone mode"""
        if mode == "texture":
            return ("genPmtrObjs", "rthmPmtrObjs", "textPmtrObjs")
        elif mode == "clone":
            return ("filterPmtrObjs", "clonePmtrObjs")
        elif mode == "all":  # all general
            return (
                "genPmtrObjs",
                "rthmPmtrObjs",  #'textPmtrObjs',
                "filterPmtrObjs",
            )  #'clonePmtrObjs')

    def _tpConvertLibType(self, usrStr):
        """Only provide access to three main types

        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> a = _CommandTP(ao)
        >>> a._tpConvertLibType('genPmtrObjs')
        'genPmtrObjs'
        >>> a._tpConvertLibType('filterPmtrObjs')
        'filterPmtrObjs'
        """
        try:
            usrStr = parameter.pmtrLibParser(usrStr)
        except ValueError:  # no such parameter
            return None
        if usrStr not in ["genPmtrObjs", "rthmPmtrObjs", "filterPmtrObjs"]:
            return None
        return usrStr

    def _tpGetLibType(self):
        """Needed for interactive form of TPmap command"""
        libNames = "Generator, Rhythm, or Filter. (g, r, f)"
        query = "select a library: %s:" % libNames
        while 1:
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            lib = self._tpConvertLibType(usrStr)
            if lib == None:
                continue
            else:
                return lib  # either l or m

    def _tpGetBundleFmt(self, lib):
        """For a given library, determine the number and types of POs that
        are necessary to create an image
        """
        if lib == "filterPmtrObjs":
            bundle = ("filterPmtrObjs", "genPmtrObjs")
            eventListSplitFmt = "pf"
            noPmtrObjs = 2
        elif lib == "rthmPmtrObjs":
            bundle = ("rthmPmtrObjs",)
            eventListSplitFmt = "pr"
            noPmtrObjs = 1
        elif lib == "genPmtrObjs":
            bundle = ("genPmtrObjs",)
            eventListSplitFmt = "pg"
            noPmtrObjs = 1
        else:  # an error
            raise Exception("cannot accept library of type: %s" % lib)
        return bundle, eventListSplitFmt, noPmtrObjs

    def _tpGetExportFormat(self):
        msgPre = ""  # this format improves wrapping
        while 1:
            query = "enter an export format:"
            if msgPre != "":
                query = "%s %s" % (msgPre, query)
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            usrStr = outFormat.outputExportFormatParser(usrStr)
            if usrStr == None:
                msgPre = "format error: select %s:" % drawer.listToStrGrammar(
                    list(outFormat.outputExportFormatNames.values()), "or"
                )
                # dialog.msgOut(msg, self.termObj)
            else:
                return usrStr


class TPls(_CommandTP):
    """displays texture parameter object information

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = TPls(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        _CommandTP.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TPls"

    def gather(self):
        self.libList = self._tpGetLib("all")  # clone or texture
        self.pmtrTitles = []
        self.pmtrObjList = []
        for name in self.libList:
            self.pmtrTitles.append(parameter.pmtrLibTitle(name))
            self.pmtrObjList.append(parameter.pmtrLibList(name))

    def process(self):
        pass

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s" % (self.cmdStr,)

    def display(self):
        msg = []
        for i in range(0, len(self.pmtrTitles)):
            lib = self.libList[i]
            msg.append(self.pmtrTitles[i])
            entryLines = []
            # entryLines.append(('%s' % self.pmtrTitles[i], ''))
            for name in self.pmtrObjList[i]:
                # doc = parameter.doc(name, lib, 'args')
                entryLines.append(("", name))
            headerKey = [
                "",
                "name",
            ]
            minWidthList = (
                lang.TABW,
                lang.LMARGINW,
            )
            bufList = [0, 1]
            justList = ["l", "l"]
            table = typeset.formatVariCol(
                headerKey,
                entryLines,
                minWidthList,
                bufList,
                justList,
                self.termObj,
                "oneColumn",
            )
            msg.append("%s\n" % table)

        return "\n".join(msg)


class TPv(_CommandTP):
    """displays texture rhythm object information

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = TPv(ao, args='ru')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        _CommandTP.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TPv"

    def _tpGetFindString(self, argString=""):
        """gets find string from user"""
        if argString == "":
            query = "enter a search string:"
            while 1:
                data = dialog.askStr(query, self.termObj)
                if data == None:
                    return None
                else:
                    return data
        else:
            return argString

    def gather(self):
        args = self.args
        # not the same as all, has static values as well
        self.libList = self._tpGetLib("texture") + self._tpGetLib("clone")
        self.pmtrTitles = []
        self.pmtrObjList = []
        for name in self.libList:
            self.pmtrTitles.append(parameter.pmtrLibTitle(name))
            self.pmtrObjList.append(parameter.pmtrLibList(name))

        if args != "":
            args = argTools.ArgOps(args)
            self.usrStr = args.get(0)
        else:  # get from user
            self.usrStr = self._tpGetFindString()
            if self.usrStr == None:
                return lang.msgReturnCancel

        self.filterList = []
        for i in range(0, len(self.libList)):
            lib = self.libList[i]
            try:
                obj, parsedUsrStr = parameter.locator(self.usrStr, lib)
            except error.ParameterObjectSyntaxError:  # failed
                parsedUsrStr = None
            if parsedUsrStr != None:
                self.filterList.append([parsedUsrStr])
                continue
            result = drawer.inListSearch(self.usrStr, self.pmtrObjList[i])
            if result != None:
                self.filterList.append(result)
                continue
            self.filterList.append([])

    def process(self):
        pass

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.usrStr)

    def display(self):
        msg = []
        foundCount = 0
        for i in range(0, len(self.pmtrTitles)):
            if len(self.filterList[i]) == 0:
                continue  # skip empty lists
            lib = self.libList[i]
            msg.append(self.pmtrTitles[i])
            entryLines = []
            # entryLines.append(('%s' % self.pmtrTitles[i], ''))
            for name in self.filterList[i]:
                foundCount = foundCount + 1
                # creates an object and calls its 'reprDoc' method
                doc = parameter.doc(name, lib, "paragraph")
                args = parameter.doc(name, lib, "args")
                entryLines.append((name, args))
                entryLines.append(("", doc))

            headerKey = ["name", "documentation"]
            minWidthList = (lang.LMARGINW, 0)
            bufList = [1, 1]
            justList = ["l", "l"]
            table = typeset.formatVariCol(
                headerKey,
                entryLines,
                minWidthList,
                bufList,
                justList,
                self.termObj,
                "oneColumn",
            )
            msg.append("%s\n" % table)
        if foundCount != 0:
            return "\n".join(msg)
        else:
            return "no mathes found.\n"


class TPmap(_CommandTP):
    """
    TODO: update method of getting temporary files
    TODO: interactive version has different command sequence than cl

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = TPmap(ao, args='120 ru,0,1')
    """

    def __init__(self, ao, args="", **keywords):
        _CommandTP.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.gfxSwitch = 1  # display
        self.cmdStr = "TPmap"

    def gather(self):
        """
        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> a = TPmap(ao, args='120 ru,0,1')
        >>> a.gather()
        """
        args = self.args
        lib = None
        self.events = None
        self.argBundle = []
        self.fp = None

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            # lib = self._tpConvertLibType(args.get(0))
            # if lib == None: return self._getUsage()

            self.events = drawer.strToNum(args.get(0), "int")
            if self.events == None:
                return self._getUsage("number of events cannot be determined")

            # get lib by looking at the first parameter object given
            lib = parameter.pmtrNameToPmtrLib(args.get(1))
            # environment.printDebug(['got first arg lib', lib])

            lib = self._tpConvertLibType(lib)  # only certain libs are spported
            if lib == None:
                return self._getUsage(
                    "cannot access parameter object from %s" % args.get(1)
                )

            bundle, self.eventListSplitFmt, noPmtrObjs = self._tpGetBundleFmt(lib)
            if bundle == None:
                return self._getUsage("cannot determine library")

            pos = 1
            for subLib in bundle:
                # environment.printDebug(['subLib', subLib])
                usrDataEval, msg = self._tiEvalUsrStr(args.get(pos), None)
                if usrDataEval == None:
                    return self._getUsage(msg)
                self.argBundle.append((subLib, usrDataEval))
                pos += 1

            # allow an optional final argument for abs file path
            self.fp = args.get(pos)  # may return None
            if self.fp != None and not os.path.isabs(self.fp):
                self.fp = None

        if self.argBundle == []:
            lib = self._tpGetLibType()
            if lib == None:
                return lang.msgReturnCancel
            self.events = self._getNumber("number of events:", "int")
            if self.events == None:
                return lang.msgReturnCancel
            bundle, self.eventListSplitFmt, noPmtrObjs = self._tpGetBundleFmt(lib)
            for subLib in bundle:
                titleStr = parameter.pmtrLibTitle(subLib)
                usrStr = dialog.askStr("enter a %s argument:" % titleStr, self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
                usrDataEval, errorMsg = self._tiEvalUsrStr(usrStr, None)
                if usrDataEval == None:
                    return errorMsg
                self.argBundle.append((subLib, usrDataEval))
            # a file path is no requested

        self.noPmtrObjs = noPmtrObjs  # only process necessary bundles

    def process(self):
        self.objBundle = []
        self.msg = []  # store string representations
        pmtrCount = 0
        self._textDisplay = 0

        # environment.printDebug(['argBundle', self.argBundle])
        # in the case of filter pos, need to have generator first
        if len(self.argBundle) > 1 and self.argBundle[0][0] == "filterPmtrObjs":
            self.argBundle.reverse()
        # environment.printDebug(['argBundlePost', self.argBundle])

        for subLib, usrDataEval in self.argBundle:
            # print _MOD, 'subLib, usrdataEval', subLib, usrDataEval
            if pmtrCount >= self.noPmtrObjs:
                environment.printDebug([lang.WARN, "too many parameter objects given"])
                break
            try:
                obj = parameter.factory(usrDataEval, subLib)
            except error.ParameterObjectSyntaxError as msg:
                return "%s\n" % msg
            ok, msg = obj.checkArgs()
            if not ok:
                return "%s\n" % msg
            # make sure this is not a string outputting parameter object
            dlgVisMet = self.ao.external.getPref("athena", "gfxVisualMethod")
            if obj.outputFmt == "str" or dlgVisMet == "text":
                self._textDisplay = 1  # this will stop gfx processing

            self.msg.append(obj.repr("argsOnly"))
            titleStr = parameter.pmtrLibTitle(subLib)
            self.objBundle.append((titleStr, subLib, obj))
            pmtrCount += 1

        # environment.printDebug(['objBundle', self.objBundle])

    def display(self):
        # note: this is an unconventional use of aoInfo
        # in the future, ssdr and sadr should be moved into aoInfo anyways
        aoInfo = self.ao.aoInfo
        if self._textDisplay:  # this may override user preference
            splitSco = eventList.EventSequenceSplit(
                self.objBundle, self.eventListSplitFmt, self.events, 0, aoInfo
            )
            splitSco.load("pre", 0)  # 0 turns off string bypass
            for pmtr in splitSco.getKeys():
                # xRelation will always be 'event' for parameter displays
                self.msg.append(splitSco.getTitle(pmtr))
                dataList = splitSco.getCoord(pmtr, "event")
                dataStr = "".join(["%s%s\n" % (lang.TAB, y) for x, y in dataList])
                self.msg.append(str(dataStr))

        self.msg.append("TPmap display complete.\n")
        return "\n".join(self.msg)

    def displayGfx(self, fmt, dir=None):
        if self._textDisplay:
            return None
        if self.events == None:
            return None
        # print _MOD, 'self.objBundle', self.objBundle
        obj = graphPmtr.TPmapCanvas(
            self.ao, self.objBundle, self.eventListSplitFmt, self.events, fmt
        )
        prefDict = self.ao.external.getPrefGroup("external")
        obj.show(dir, prefDict)  # if writing a file, creates temporary path

    def displayGfxUtil(self, fmt, fp):
        if self._textDisplay:
            return None
        if self.events == None:
            return None

        # this method is for use in auto-documentation generation
        # can supply complete path rather than just a directory
        obj = graphPmtr.TPmapCanvas(
            self.ao, self.objBundle, self.eventListSplitFmt, self.events, fmt
        )
        # second arg sets openMedia to false
        obj.write(fp, 0)


class TPe(_CommandTP):
    """sub class TPmap for exporting generator values

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> a = TPe(ao, args='pda 120 ru,0,1')
    >>> a.gather()
    """

    def __init__(self, ao, args="", **keywords):
        _CommandTP.__init__(self, ao, args, **keywords)
        self.processSwitch = 1
        self.gatherSwitch = 1
        self.gfxSwitch = 0  # display
        self.cmdStr = "TPe"
        self.lib = "genPmtrObjs"  # fixed

    def gather(self):
        args = self.args
        self.fmt = None
        self.events = None
        self.argBundle = []
        self.fp = None  # optional file path arg

        if args != "":
            args = argTools.ArgOps(args)
            self.fmt = outFormat.outputExportFormatParser(args.get(0))
            if self.fmt == None:
                opts = drawer.listToStrGrammar(
                    list(outFormat.outputExportFormatNames.values())
                )
                return self._getUsage("no format %s; select %s" % (args.get(0), opts))

            self.events = drawer.strToNum(args.get(1), "int")
            if self.events == None:
                return self._getUsage()

            bundle, self.eventListSplitFmt, noPmtrObjs = self._tpGetBundleFmt(self.lib)
            pos = 2  # 2 args already given
            for subLib in bundle:
                usrDataEval, msg = self._tiEvalUsrStr(args.get(pos), None)
                if usrDataEval == None:
                    return self._getUsage(msg)
                self.argBundle.append((subLib, usrDataEval))
                pos += 1
            # allow an optional final argument for abs file path
            self.fp = args.get(pos)  # may return None
            if self.fp != None and not os.path.isabs(self.fp):
                self.fp = None

        if self.argBundle == []:
            self.fmt = self._tpGetExportFormat()
            if self.fmt == None:
                return lang.msgReturnCancel

            self.events = self._getNumber("number of events:", "int")
            if self.events == None:
                return lang.msgReturnCancel

            bundle, self.eventListSplitFmt, noPmtrObjs = self._tpGetBundleFmt(self.lib)
            for subLib in bundle:
                titleStr = parameter.pmtrLibTitle(subLib)
                usrStr = dialog.askStr("enter a %s argument:" % titleStr, self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
                usrDataEval, errorMsg = self._tiEvalUsrStr(usrStr, None)
                # this may not catch all bad arguments; only evaluates
                if usrDataEval == None:
                    return errorMsg
                self.argBundle.append((subLib, usrDataEval))
            # a file path is not requested

        self.noPmtrObjs = noPmtrObjs  # only process necessary bundles

    def process(self):
        # adding an extra argument here to get control over file-path
        # settings; this is a temporary solution to a larger problem
        self.objBundle = []
        for subLib, usrDataEval in self.argBundle:
            try:
                obj = parameter.factory(usrDataEval, subLib)
            except error.ParameterObjectSyntaxError as msg:
                return "%s\n" % msg
            ok, msg = obj.checkArgs()
            if not ok:
                return "%s\n" % msg
            titleStr = parameter.pmtrLibTitle(subLib)
            self.objBundle.append((titleStr, subLib, obj))

        self.splitSco = eventList.EventSequenceSplit(
            self.objBundle, self.eventListSplitFmt, self.events
        )
        self.splitSco.load()
        self.pathList = []
        # get out object
        self.outObj = outFormat.factory(self.fmt)
        if self.fp == None:
            self.fp = environment.getTempFile(self.outObj.ext)

        if self.outObj.name in ["textSpace", "textTab"]:  # textSpace, textTab
            if self.outObj.name == "textSpace":
                self.splitSco.writeTable(self.fp, " ")
            elif self.outObj.name == "textTab":
                self.splitSco.writeTable(self.fp, "\t")
        elif self.outObj.name in ["pureDataArray"]:
            self.splitSco.writeOutputEngine(self.outObj.name, self.fp)
        elif self.outObj.name in ["audioFile"]:  # use .aif, but use pref later
            self.splitSco.writeBuffer(self.fp)

        self.pathList.append(self.fp)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            pmtrStr = drawer.strScrub(self.objBundle[0][2].repr(), None, " ")
            return "%s %s %s %s" % (self.cmdStr, self.fmt, self.events, pmtrStr)

    def display(self):
        msg = []
        prefDict = self.ao.external.getPrefGroup("external")
        for self.fp in self.pathList:
            failFlag = osTools.openMedia(self.fp, prefDict)
            if failFlag == "failed":
                msg.append("cannot open: %s\n" % self.fp)
            else:
                msg.append("complete: (%s)\n" % self.fp)
        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--


class TIn(Command):
    """create a new texture instance
    of a texture created, uses last duration and tempo

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIn"

    def _tiGetCurrentTextTime(self):
        """get data for loading pmtr obj"""
        lclTimes = None
        if self.ao.activeTexture != "":
            lclTimes = {}
            t = self.ao.textureLib[self.ao.activeTexture]
            lclTimes["tRange"] = t.pmtrQDict["tRange"]
            lclTimes["beatT"] = t.pmtrQDict["beatT"]  # get data
        return lclTimes

    def gather(self):
        args = self.args
        self.name = None
        self.inst = None
        self.auxNo = None  # optional argument, used depending on eventMode
        if args != "":
            args = argTools.ArgOps(args)
            self.name = args.get(0)
            if self.name == None:
                return self._getUsage()
            if self.name in list(self.ao.textureLib.keys()):
                return self._getUsage()
            if self._nameTest(self.name) != None:
                return self._getUsage(self._nameTest(self.name))
            self.inst = self._elCheckInstrumentNo(args.get(1))
            if self.inst == None:
                return self._getUsage()
            if self.ao.activeEventMode in ["csoundExternal"]:
                self.auxNo = drawer.strToNum(args.get(2), "int", 0)
                if self.auxNo == None:
                    return self._getUsage()
            # if midiController, must get info for each controller number

        if self.name == None or self.inst == None:
            self.name = self._tiGetNewName(lang.msgTIname)
            if self.name == None:
                return lang.msgReturnCancel
            self.inst = self._elGetInstrumentNo()
            if self.inst == None:
                return lang.msgReturnCancel
            if self.ao.activeEventMode in ["csoundExternal"]:
                query = "provide number of auxiliary parameters:"
                self.auxNo = self._getNumber(query, "int", 0)
                if self.auxNo == None:
                    return lang.msgReturnCancel
            # if midiController, must get info for each controller number

    def process(self):
        mod = self.ao.activeTextureModule  # same as self.tmName
        self.ao.textureLib[self.name] = texture.factory(mod, self.name)
        # if refresh mode is active, will auto-score to test
        refresh = self.ao.aoInfo["refreshMode"]
        # get current texture values
        lclTimes = self._tiGetCurrentTextTime()
        # in some cases, supply (and create) a different path
        if self.ao.activeEventMode == "midiPercussion":
            # after, activePath as pName, returns a unused piRef not necessary
            piRef = self._piAutoCreateMidiPercussion(self.inst)
        else:  # check that current path exists
            if (
                self._piTestExistance() != None or self._piTestNameExists() != None
            ):  # check existance
                # if not path exists, create
                self._piAutoCreate()  # will be named autp

        pathObj = self.ao.pathLib[self.ao.activePath]  # this is a reference
        self.ao.pathLib[self.ao.activePath].refIncr()  # add ref
        # auxNo will be provided; if None, aux is taken from instrument
        # if given, will override aux provided from orchestra
        self.ao.textureLib[self.name].loadDefault(
            self.inst,
            pathObj,
            self.ao.aoInfo["fpAudioDirs"],
            lclTimes,
            self.ao.orcObj.name,
            self.auxNo,
            refresh,
        )
        self.ao.activeTexture = self.name

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s %s" % (self.cmdStr, self.name, self.inst)

    def display(self):
        return lang.msgTIcreated % self.ao.activeTexture


class TIo(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIn(ao, args='b 32')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIo(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIo"

    def gather(self):
        args = self.args

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        self.name = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = drawer.inList(args.get(0), list(self.ao.textureLib.keys()))
            if self.name == None:
                return self._getUsage()
        if self.name == None:
            self.name = self._chooseFromList(
                "which TextureInstnace to make active?",
                list(self.ao.textureLib.keys()),
                "case",
            )
            if self.name == None:
                return lang.msgTIbadName

    def process(self):
        self.ao.activeTexture = self.name

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.name)

    def display(self):
        return "TI %s now active.\n" % self.ao.activeTexture


class TImute(Command):
    """mutes the current texture

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TImute(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TImute"

    def _tiMute(self, nameToMute):
        if nameToMute in list(self.ao.textureLib.keys()):
            if self.ao.textureLib[nameToMute].mute:
                self.ao.textureLib[nameToMute].mute = 0
                return "TI %s is no longer muted.\n" % nameToMute
            else:
                self.ao.textureLib[nameToMute].mute = 1
                return "TI %s is now muted.\n" % nameToMute
        return None

    def gather(self):
        args = self.args
        self.mList = []
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists(self.ao.activeTexture) != None:  # check name
            return self._tiTestNameExists(self.ao.activeTexture)
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            if args.list(0, "end") != None:  # if supplied
                for name in args.list(0, "end"):
                    self.mList.append(name)
            else:
                return self._getUsage()
        else:
            self.mList.append(self.ao.activeTexture)

    def process(self):
        self.report = []
        for name in self.mList:
            msg = self._tiMute(name)
            if msg != None:
                self.report.append(msg)
            else:
                self.report.append(lang.msgBadArgFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self._strListToArgList(self.mList))

    def display(self):
        return "".join(self.report)


class TImode(Command):
    """sets pitch, poly, silence, and postMap mode of current texture
    args: timode  modeChoice  modeValue

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TImode(ao, args='pitch ps')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TImode"

    def _tiConvertMode(self, usrStr):
        """converts strings to pitch or poly mode"""
        ref = {
            "p": ["pitch", "p"],
            "s": ["silence", "s"],
            "m": ["map", "m", "postmap", "pm"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr  # may be None

    #     def _tiConvertPolyMode(self, usrStr):
    #         """converts user entry to poly mode strings"""
    #         ref = {
    #             'set' : ['set', 's'],
    #             'part' : ['part', 'p'],
    #                 }
    #         usrStr = drawer.selectionParse(usrStr, ref)
    #         return usrStr # may be None

    def _tiConvertPitchMode(self, usrStr):
        """converts user entry to pitch mode strings"""
        ref = {
            "sc": ["sc", "setclass"],
            "pcs": ["pcs", "pc", "pitchclass"],
            "ps": ["ps", "pss", "pitchspace"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr  # may be None

    def gather(self):
        args = self.args

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        t = self.ao.textureLib[self.ao.activeTexture]
        currentPitchMode = t.getPitchMode()  # this does a string conversion
        # currentPolyMode = t.polyphonyMode
        currentSilenceMode = t.silenceMode
        currentOrcMapMode = t.orcMapMode

        modeChoice = None
        modeValue = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            modeChoice = self._tiConvertMode(args.get(0))
            if modeChoice == None:
                return self._getUsage()
            if modeChoice == "p":
                modeValue = self._tiConvertPitchMode(args.get(1))
                if modeValue == None:
                    return self._getUsage()
            #             elif modeChoice == 'y':
            #                 modeValue = self._tiConvertPolyMode(args.get(1))
            #                 if modeValue == None: return self._getUsage()
            elif modeChoice == "s":
                modeValue = typeset.convertBool(args.get(1))
                if modeValue == None:
                    return self._getUsage()
            elif modeChoice == "m":
                modeValue = typeset.convertBool(args.get(1))
                if modeValue == None:
                    return self._getUsage()

        if modeChoice == None or modeValue == None:
            modeChoice = dialog.askStr(
                lang.msgTImodeChoose % self.ao.activeTexture, self.termObj
            )
            if modeChoice == None:
                return lang.msgReturnCancel
            modeChoice = self._tiConvertMode(modeChoice)
            if modeChoice == "p":
                while modeValue == None:
                    query = lang.msgTImodePitchChoose % currentPitchMode
                    modeValue = dialog.askStr(query, self.termObj)
                    if modeValue == None:
                        return lang.msgReturnCancel
                    modeValue = self._tiConvertPitchMode(modeValue)
                    if modeValue == None:
                        dialog.msgOut(lang.msgTInoSuchPitchMode, self.termObj)
                        continue
            #             elif modeChoice == 'y':
            #                 while modeValue == None:
            #                     query = lang.msgTImodePolyChoose % currentPolyMode
            #                     modeValue = dialog.askStr(query, self.termObj)
            #                     if modeValue == None: return lang.msgReturnCancel
            #                     modeValue = self._tiConvertPolyMode(modeValue)
            #                     if modeValue == None:
            #                         dialog.msgOut(lang.msgTInoSuchPolyMode, self.termObj)
            #                         continue
            elif modeChoice == "s":
                while modeValue == None:
                    query = lang.msgTImodeSilenceChoose % typeset.boolAsStr(
                        currentSilenceMode
                    )
                    modeValue = dialog.askStr(query, self.termObj)
                    if modeValue == None:
                        return lang.msgReturnCancel
                    modeValue = typeset.convertBool(modeValue)
                    if modeValue == None:
                        dialog.msgOut(lang.msgTInoSuchSilenceMode, self.termObj)
                        continue
            elif modeChoice == "m":
                while modeValue == None:
                    query = lang.msgTImodeMixChoose % typeset.boolAsStr(
                        currentOrcMapMode
                    )
                    modeValue = dialog.askStr(query, self.termObj)
                    if modeValue == None:
                        return lang.msgReturnCancel
                    modeValue = typeset.convertBool(modeValue)
                    if modeValue == None:
                        dialog.msgOut(lang.msgTInoSuchMapMode, self.termObj)
                        continue

            else:
                return lang.msgTInoSuchMode

        self.modeChoice = modeChoice
        self.modeValue = modeValue

    def process(self):
        """note: changing modes requires updating the internal esObj
        representation; as such, _tiEdit must be called w/ a parameter
        to update all esObjs in textures and clones"""
        name = self.ao.activeTexture

        if self.modeChoice == "p":
            self.ao.textureLib[name].pitchMode = self.modeValue
        #         elif self.modeChoice == 'y':
        #             if self.modeValue == 'part':
        #                 p = self.ao.textureLib[name].path
        #                 pSizeType = p.voiceType
        #                 if pSizeType != 'part':
        #                     return lang.msgTInoPolyModePath % p.name
        #             self.ao.textureLib[name].polyphonyMode = self.modeValue
        elif self.modeChoice == "s":
            self.ao.textureLib[name].silenceMode = self.modeValue
        elif self.modeChoice == "m":
            self.ao.textureLib[name].orcMapMode = self.modeValue
        # update will be executed if refresh mode is on
        if self.ao.aoInfo["refreshMode"]:
            ok, msg = self._tiRefresh(name)  # force new esObj creation
            if not ok:
                return msg

    def display(self):
        t = self.ao.textureLib[self.ao.activeTexture]
        if self.modeChoice == "p":
            modeStr = t.getPitchMode()
            return "Pitch Mode changed to %s\n" % modeStr
        #         elif self.modeChoice == 'y':
        #             modeStr = t.polyphonyMode
        #             return 'Polyphony Mode changed to %s\n' % self.modeValue
        elif self.modeChoice == "s":
            modeStr = t.silenceMode
            return "Silence Mode changed to %s\n" % typeset.boolAsStr(self.modeValue)
        elif self.modeChoice == "m":
            modeStr = t.orcMapMode
            return "PostMap Mode changed to %s\n" % typeset.boolAsStr(self.modeValue)


class TImidi(Command):
    """sets midi settings for the current texture
        work done mostly from within midiTools.py

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TImidi(ao, args='pgm 3')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TImidi(ao, args='ch 2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TImidi"

    def _tiConvertMidiPmtr(self, usrStr):
        """converts strings to pgm or channel mode"""
        ref = {
            "p": ["p", "pgm", "program"],
            "c": ["c", "ch", "channel"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr  # may be None

    def _tiGetMidiProgram(self):
        while 1:
            pmtrValue = dialog.askStr(lang.msgTImidiPgmSel, self.termObj)
            if pmtrValue == None:
                return None
            pmtrValue = generalMidi.getPgmNumber(pmtrValue)
            if pmtrValue == None:
                dialog.msgOut(lang.msgTImidiPgmError, self.termObj)
                continue
            else:
                return pmtrValue

    def _tiConvertMidiCh(self, usrStr):
        "convert usr usrStr to channel int, first ch as 1"
        chInt = drawer.strToNum(usrStr, "int", 1, 16)
        return chInt  # may be None

    def _tiGetMidiCh(self):
        query = "enter a midi channel between 1 and 16:"
        while 1:
            pmtrValue = dialog.askStr(query, self.termObj)
            if pmtrValue == None:
                return None
            pmtrValue = self._tiConvertMidiCh(pmtrValue)
            if pmtrValue == None:
                continue
            else:
                return pmtrValue

    def gather(self):
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        args = self.args
        pmtrChoice = None
        pmtrValue = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            pmtrChoice = self._tiConvertMidiPmtr(args.get(0))
            if pmtrChoice == None:
                return self._getUsage()
            if pmtrChoice == "p":
                pmtrValue = generalMidi.getPgmNumber(args.get(1))
                if pmtrValue == None:
                    return self._getUsage()
            elif pmtrChoice == "c":
                pmtrValue = self._tiConvertMidiCh(args.get(1))
                if pmtrValue == None:
                    return self._getUsage()

        if pmtrChoice == None or pmtrValue == None:
            pmtrChoice = dialog.askStr(
                lang.msgTImidiPmtrSel % self.ao.activeTexture, self.termObj
            )
            if pmtrChoice == None:
                return lang.msgReturnCancel
            pmtrChoice = self._tiConvertMidiPmtr(pmtrChoice)
            if pmtrChoice == "p":
                pmtrValue = self._tiGetMidiProgram()
                if pmtrValue == None:
                    return lang.msgReturnCancel
            # channel not implemented yet
            elif pmtrChoice == "c":
                pmtrValue = self._tiGetMidiCh()
                if pmtrValue == None:
                    return lang.msgReturnCancel
            else:
                return lang.msgTImidiPmtrError

        self.pmtrChoice = pmtrChoice
        self.pmtrValue = pmtrValue

    def process(self):
        if self.pmtrChoice == "p":  # set num
            self.ao.textureLib[self.ao.activeTexture].midiPgm = self.pmtrValue[1]
        elif self.pmtrChoice == "c":
            self.ao.textureLib[self.ao.activeTexture].midiCh = self.pmtrValue

    def display(self):
        if self.pmtrChoice == "p":  # set name
            return "midi program changed to %s\n" % self.pmtrValue[0]
        elif self.pmtrChoice == "c":
            return "midi channel changed to %s\n" % self.pmtrValue


class TIv(Command):
    """views the current texture, or name if provided with args

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIv(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIv"

    def gather(self):
        args = self.args
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = args.get(0)
        else:
            self.name = self.ao.activeTexture
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists(self.name) != None:  # check name
            return self._tiTestNameExists(self.name)

    def process(self):
        pass

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.name)

    def display(self):
        nameToView = self.name
        extData = {}
        extData["cloneNo"] = self.ao.cloneLib.number(nameToView)
        headList, entryLines = self.ao.textureLib[nameToView].repr("full", extData)
        headerKey = []  # removes header
        minWidthList = [lang.LMARGINW, 0]
        bufList = [0, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        headList.append("%s\n" % table)
        return "".join(headList)


class TIe(Command):
    """eidits attributes of a texture

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIv(ao, args='a ru,0,1')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIe"

    def gather(self):
        """
        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> ao.setEventMode('m')

        >>> a = TIn(ao, args='a 0')
        >>> ok, result = a.do()

        >>> a = TIe(ao, args='a ru,0,1')
        >>> a.gather()
        >>> a.usrDataEval
        ('ru', 0, 1)

        >>> a = TIe(ao, args='a ru, 0, 1')
        >>> a.gather()
        >>> a.usrDataEval
        ('ru', 0, 1)

        >>> a = TIe(ao, args='x4 cf,"path to file"')
        >>> a.gather()
        >>> a.usrDataEval
        ('cf', 'path to file')
        """

        args = self.args
        # environment.printDebug(['raw args', args])

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        # get ref to method
        decodePmtrName = self.ao.textureLib[self.ao.activeTexture].decodePmtrName
        p = None
        usrDataEval = None
        tName = self.ao.activeTexture

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            p, label = decodePmtrName(args.get(0), "str")
            p = self._numPmtrConvertLabel(p, tName)
            if p == None:
                return self._getUsage()

            if isinstance(args.get(1), basePmtr.Parameter):
                usrDataEval = args.get(1)
                msg = ""
                environment.printDebug(["TIe", "found Parameter subclass", usrDataEval])
            else:
                # note: here we are keeping spaces with args.get().
                # this is important in the case of passing a file path s
                # this may have potential side effects
                usrDataEval, msg = self._tiEvalUsrStr(
                    args.get(1, "end", keepSpace=True), p, tName
                )
                usrDataEval, msg = self._tiCompleteEditData(p, usrDataEval, tName)
            if usrDataEval == None:
                return self._getUsage(msg)

        if p == None or usrDataEval == None:
            p = dialog.askStr(lang.msgTIePmtrSel % tName, self.termObj)
            p, label = decodePmtrName(p, "str")
            if p == None:
                return lang.msgTIbadPmtrName
            demo, demoAdjust = self._tiGetDemo(tName, p, label, "edit")
            if demo == None:
                return demoAdjust  # this is the error message
            if p == "path":
                usrStr = self._chooseFromList(
                    demo, list(self.ao.pathLib.keys()), "case"
                )
                if usrStr == None:
                    return lang.msgPIbadName
                usrDataEval, errorMsg = self._tiEvalUsrStr(usrStr, p, tName)
                if usrDataEval == None:
                    return errorMsg
            elif p in (
                "ampQ",
                "panQ",
                "fieldQ",
                "octQ",
                "beatT",
                "tRange",
                "inst",
                "rhythmQ",
            ):
                if p == "inst":
                    usrStr = self._elGetInstrumentNo()
                else:
                    usrStr = dialog.askStr(demo, self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            elif p[:4] == "auxQ":
                p = self._getNumPmtr("aux", tName, p)  # get properlabel
                if p == None:
                    return lang.msgReturnCancel
                usrStr = dialog.askStr((demo[p] + demoAdjust), self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            elif p[:5] == "textQ":
                p = self._getNumPmtr("text", tName, p)  # get proper label
                if p == None:
                    return lang.msgReturnCancel
                usrStr = dialog.askStr((demo[p] + demoAdjust), self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            elif p[:4] == "dynQ":
                p = self._getNumPmtr("dyn", tName, p)  # get proper label
                if p == None:
                    return lang.msgReturnCancel
                usrStr = dialog.askStr((demo[p] + demoAdjust), self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            # eval data, evaluate and complete complete
            usrDataEval, errorMsg = self._tiEvalUsrStr(usrStr, p, tName)
            if usrDataEval == None:
                return errorMsg
            usrDataEval, errorMsg = self._tiCompleteEditData(p, usrDataEval, tName)
            if usrDataEval == None:
                return errorMsg
        self.p = p
        self.usrDataEval = usrDataEval
        self.label = label

    def process(self):
        tName = self.ao.activeTexture
        refresh = self.ao.aoInfo["refreshMode"]
        self.ok, self.msg = self._tiEdit(tName, self.p, self.usrDataEval, refresh)

    def log(self):
        if self.gatherStatus and self.ok != None:  # if complete
            return "%s %s %s" % (
                self.cmdStr,
                self.p,
                drawer.listToStr(self.usrDataEval),
            )

    def display(self):
        if not self.ok:  # error encountered
            return lang.TAB + "TIe %s %s\n" % (lang.ERROR, self.msg)
        else:
            return "TI %s: parameter %s updated.\n" % (
                self.ao.activeTexture,
                self.label,
            )


class TIls(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIls(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIls"

    def gather(self):
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()

    def _tiGetActiveStr(self, name):
        if name == self.ao.activeTexture:
            return lang.ACTIVE
        else:
            return lang.INACTIVE

    def process(self):
        pass

    def display(self):
        msg = []
        msg.append("TextureInstances available:\n")
        tNames = list(self.ao.textureLib.keys())
        tNames.sort()
        entryLines = []
        for name in tNames:
            muteOnOff = self.ao.textureLib[name].repr("mute")
            activity = self._tiGetActiveStr(name)
            inst = self.ao.textureLib[name].pmtrObjDict["inst"].repr("argsOnly")
            text = self.ao.textureLib[name].tmName
            pathName = self.ao.textureLib[name].path.name
            timeStr = self.ao.textureLib[name].pmtrObjDict["tRange"].repr()
            noClones = self.ao.cloneLib.number(name)
            entryLines.append(
                [activity, name, muteOnOff, text, pathName, inst, timeStr, noClones]
            )
        headerKey = ["", "name", lang.MUTELABEL, "TM", "PI", "instrument", "time", "TC"]
        minWidthList = (lang.TABW, lang.NAMEW, 2, 12, 12, 4, 0, 3)
        bufList = [0, 1, 0, 1, 1, 0, 1, 0]
        justList = ["c", "l", "l", "l", "l", "l", "l", "r"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "twoColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class TIrm(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIrm(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIrm"

    def gather(self):
        args = self.args
        self.rmList = []

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            if args.list(0, "end") != None:  # if supplied
                for name in args.list(0, "end"):
                    name = drawer.inList(name, list(self.ao.textureLib.keys()))
                    if name == None:
                        return self._getUsage()
                    self.rmList.append(name)
            else:
                return self._getUsage()

        if self.rmList == []:
            name = self._chooseFromList(
                "which TextureInstnace to delete?",
                list(self.ao.textureLib.keys()),
                "case",
            )
            if name == None:
                return lang.msgTIbadName
            query = "are you sure you want to delete texture %s?" % name
            askUsr = dialog.askYesNoCancel(query, 1, self.termObj)
            if askUsr == 1:  # /* return to top of loop if yes */
                self.rmList.append(name)
            else:
                return lang.msgReturnCancel

    def process(self):
        self.report = []
        for name in self.rmList:
            msg = self._tiRemove(name)
            if msg != None:
                self.report.append(msg)
            else:
                self.report.append(lang.msgBadArgFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self._strListToArgList(self.rmList))

    def display(self):
        return "".join(self.report)


class TIcp(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIcp(ao, args='a b')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIcp"

    def _tiCopy(self, srcName, copyName):
        """copies a texture"""
        if srcName != copyName and (srcName in self.ao.textureLib) == 1:
            self.ao.textureLib[copyName] = self.ao.textureLib[srcName].copy(copyName)
            # increment references for this path
            self.ao.textureLib[copyName].path.refIncr()
            self.ao.activeTexture = copyName
            # copy clones
            if srcName in self.ao.cloneLib.tNames():
                self.ao.cloneLib.tCopy(srcName, copyName)
            return "TextureInstance %s created.\n" % copyName
        else:
            return None

    def gather(self):
        args = self.args
        self.cpList = []
        self.oldName = None

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            self.oldName = drawer.inList(args.get(0), list(self.ao.textureLib.keys()))
            if self.oldName == None:
                return self._getUsage()
            if args.list(1, "end") != None:  # if supplied
                for newName in args.list(1, "end"):
                    self.cpList.append(newName)
            else:
                return self._getUsage()

        if self.cpList == []:
            self.oldName = self._chooseFromList(
                "which TextureInstnace to copy?",
                list(self.ao.textureLib.keys()),
                "case",
            )
            if self.oldName == None:
                return lang.msgTIbadName
            query = "name this copy of TI %s:" % (repr(self.oldName))
            name = self._tiGetNewName(query)
            if name == None:
                return lang.msgReturnCancel
            self.cpList.append(name)

    def process(self):
        self.report = []
        for newName in self.cpList:
            msg = self._tiCopy(self.oldName, newName)
            if msg != None:  # fall through if fails
                self.report.append(msg)
            else:
                self.report.append(lang.msgBadArgFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s %s" % (
                self.cmdStr,
                self.oldName,
                self._strListToArgList(self.cpList),
            )

    def display(self):
        return "".join(self.report)


class TImv(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TImv(ao, args='a b')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TImv"

    def _tiMove(self, oldTextName, newTextName):
        """renames a textire, appending underscore if duplicate
        update dependences in self.textureCloneObj
        """
        if newTextName == oldTextName:
            while newTextName == oldTextName:
                newTextName = newTextName + "_"
        self.ao.textureLib[newTextName] = self.ao.textureLib[oldTextName]
        if oldTextName in self.ao.cloneLib.tNames():
            self.ao.cloneLib.tMove(oldTextName, newTextName)
        del self.ao.textureLib[oldTextName]
        # must change the internal name attrubt of the Texture:
        self.ao.textureLib[newTextName].editName(newTextName)
        return newTextName

    def gather(self):
        args = self.args

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            self.oldTextName = drawer.inList(
                args.get(0), list(self.ao.textureLib.keys())
            )
            if self.oldTextName == None:
                return self._getUsage()
            self.newTextName = args.get(1)
            if self.newTextName == None:
                return self._getUsage()
        else:  # only works with args
            return lang.msgReturnCancel

    def process(self):
        self.newTextName = self._tiMove(self.oldTextName, self.newTextName)
        self.ao.activeTexture = self.newTextName

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s %s" % (self.cmdStr, self.oldTextName, self.newTextName)

    def display(self):
        return "TI %s moved to TI %s.\n" % (self.oldTextName, self.ao.activeTexture)


class TIdoc(Command):
    """displays all essential information about parameters
    of this texture, as well as in
    args can be the name of a different texture

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIdoc(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIdoc"

    def gather(self):
        args = self.args
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            tName = args.get(0)
        else:
            tName = self.ao.activeTexture

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists(tName) != None:  # check name
            return self._tiTestNameExists(tName)
        self.tName = tName

    def display(self):
        """this should be moved inside of texture"""
        tName = self.tName
        t = self.ao.textureLib[tName]
        headList, entryLines = t.repr("doc")

        headerKey = []  # removes header
        minWidthList = [lang.LMARGINW, 0]
        bufList = [0, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        headList.append("%s\n" % table)
        return "".join(headList)


class TIals(Command):
    """list all attributes of a texture, a hidden command

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> ao.setEventMode('m')
    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIals(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TIals"

    def gather(self):
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

    def process(self):
        pass

    def display(self):
        directoryOfattributes = dir(self.ao.textureLib[self.ao.activeTexture])
        msg = []
        msg.append("attributes of TI %s:\n" % self.ao.activeTexture)
        entryLines = []
        for entry in directoryOfattributes:
            value = getattr(self.ao.textureLib[self.ao.activeTexture], entry)
            value = str(value).replace(" ", "")
            entryLines.append([entry, value])
        headerKey = ["name", "value"]
        minWidthList = [lang.LMARGINW, 0]
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class TImap(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')
    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TImap(ao) # cannot test interactively

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.gfxSwitch = 1  # display
        self.cmdStr = "TImap"

    def gather(self):
        args = self.args
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        self.tmRelation = "pre"  # default
        self.xRelation = "event"  # 'event'/'time'default
        self.tName = self.ao.activeTexture

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.xRelation = self._tiConvertEventTime(args.get(0))
            if self.xRelation == None:
                return self._getUsage()
            self.tmRelation = self._tiConvertPrePost(args.get(1))
            if self.tmRelation == None:
                return self._getUsage()
        else:  # use default
            pass  # get from user eventually

    def process(self):
        # if refresh mode set to off
        if not self.ao.aoInfo["refreshMode"]:
            ok, msg = self._tiRefresh(self.tName)  # update esObj if refreshmode off

    def display(self):
        return "TImap (%s-base, %s-TM) display complete.\n" % (
            self.xRelation,
            self.tmRelation,
        )

    def displayGfx(self, fmt, dir=None):
        prefDict = self.ao.external.getPrefGroup("external")
        obj = graphPmtr.TImapCanvas(
            self.ao, self.tName, None, self.tmRelation, self.xRelation, fmt
        )
        obj.show(dir, prefDict)

    def displayGfxUtil(self, fmt, fp):
        obj = graphPmtr.TImapCanvas(
            self.ao, self.tName, None, self.tmRelation, self.xRelation, fmt
        )
        # second arg sets openMedia to false
        obj.write(fp, 0)


# -----------------------------------------------------------------||||||||||||--
class TEe(Command):
    """edits all textures

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIn(ao, args='b 2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TEe(ao, args='a ru,.3,1')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TEe"

    def gather(self):
        """
        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> ao.setEventMode('m')
        >>> a = TIn(ao, args='a 0')
        >>> ok, result = a.do()

        >>> a = TEe(ao, args='a 0')
        >>> ok, result = a.do()

        >>> a = TEe(ao, args='a ru,0,1')
        >>> a.gather()
        >>> a.usrDataEval
        ('ru', 0, 1)

        >>> a = TEe(ao, args='a ru, 0, 1')
        >>> a.gather()
        >>> a.usrDataEval
        ('ru', 0, 1)

        >>> a = TEe(ao, args='x4 cf,"path to file"')
        >>> a.gather()
        >>> a.usrDataEval
        ('cf', 'path to file')
        """

        args = self.args
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        decodePmtrName = self.ao.textureLib[self.ao.activeTexture].decodePmtrName

        p = None
        usrDataEval = None
        tName = self.ao.activeTexture

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            p, label = decodePmtrName(args.get(0), "str")
            p = self._numPmtrConvertLabel(p, tName)
            if p == None:
                return self._getUsage()
            else:
                usrDataEval, msg = self._tiEvalUsrStr(
                    args.get(1, "end", keepSpace=True), p, tName
                )
                usrDataEval, msg = self._tiCompleteEditData(p, usrDataEval, tName)
            if usrDataEval == None:
                return self._getUsage(msg)

        # same as tie save query string
        if p == None or usrDataEval == None:
            p = dialog.askStr(lang.msgTEePmtrSel, self.termObj)
            p, label = decodePmtrName(p, "str")
            if p == None:
                return lang.msgTIbadPmtrName
            demo, demoAdjust = self._tiGetDemo(tName, p, label, "listedit")
            if demo == None:
                return demoAdjust  # this is the error message

            if p == "path":
                usrStr = self._chooseFromList(
                    demo, list(self.ao.pathLib.keys()), "case"
                )
                if usrStr == None:
                    return lang.msgPIbadName
            elif p in (
                "ampQ",
                "panQ",
                "fieldQ",
                "octQ",
                "beatT",
                "tRange",
                "inst",
                "rhythmQ",
            ):
                if p == "inst":
                    usrStr = self._elGetInstrumentNo()
                else:
                    usrStr = dialog.askStr(demo, self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            elif p[:4] == "auxQ":  # p7 already included
                p = self._getNumPmtr("aux", tName, p)
                if p == None:
                    return lang.msgReturnCancel
                usrStr = dialog.askStr((demo[p] + demoAdjust), self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel

            # eval data, evaluate and complete complete
            usrDataEval, errorMsg = self._tiEvalUsrStr(usrStr, p)
            if usrDataEval == None:
                return errorMsg
            usrDataEval, errorMsg = self._tiCompleteEditData(p, usrDataEval, tName)
            if usrDataEval == None:
                return errorMsg

        self.p = p
        self.usrDataEval = usrDataEval
        self.label = label

    def process(self):
        self.report = []
        refresh = self.ao.aoInfo["refreshMode"]
        # no errors: do final changes on ALL TEXTURES
        for tName in list(self.ao.textureLib.keys()):
            # if self.p is not part of this texture (w/ an aux, or text)
            # an errormsg will be returned
            self.ok, msgEdit = self._tiEdit(tName, self.p, self.usrDataEval, refresh)
            if not self.ok:  # error encountered
                self.report.append("%sTIe %s %s\n" % (lang.TAB, lang.ERROR, msgEdit))
            else:
                self.report.append(
                    "TI %s: parameter %s updated.\n" % (tName, self.label)
                )

    def log(self):
        if self.gatherStatus and self.ok != None:  # if complete
            return "%s %s %r" % (self.cmdStr, self.p, self.usrDataEval)

    def display(self):
        return "".join(self.report)


class TEv(Command):
    """ensemble view, displays parallel attributes for all textures

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIn(ao, args='b 2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TEv(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TEv"

    def gather(self):
        args = self.args
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        decodePmtrName = self.ao.textureLib[self.ao.activeTexture].decodePmtrName

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            p, label = decodePmtrName(args.get(0), "str")
            if p == None:
                return self._getUsage()
        else:
            p = dialog.askStr(lang.msgTIcompareParam, self.termObj)
            p, label = decodePmtrName(p, "str")
            if p == None:
                return lang.msgTIbadPmtrName
        self.p = p
        self.label = label

    def process(self):
        pass

    def display(self):
        p = self.p  # this is the name of the texture 'self' variable
        label = self.label

        text_keys = list(self.ao.textureLib.keys())
        text_keys.sort()
        msg = []
        msg.append("compare parameters: ")
        entryLines = []

        if p == "inst":
            msg.append("%s\n" % label)
            for key in text_keys:
                dataStr = self.ao.textureLib[key].pmtrObjDict["inst"].repr()
                entryLines.append([key, dataStr, ""])
        elif p == "path":
            msg.append("path\n")
            for key in text_keys:
                name = "unknown"
                for pair in list(self.ao.pathLib.items()):
                    if pair[1] == self.ao.textureLib[key].path:
                        name = pair[0]
                pathStr = self.ao.textureLib[key]._getPathList("string")
                entryLines.append([key, name, pathStr])
        elif p in ("tRange", "rhythmQ", "beatT", "fieldQ", "octQ", "ampQ", "panQ"):
            msg.append("%s\n" % label)
            for key in text_keys:
                dataStr = self.ao.textureLib[key].pmtrObjDict[p].repr()
                entryLines.append([key, dataStr, ""])
        elif p in ["auxQ", "textQ", "dynQ"]:
            msg.append("no %s ensemble view available.\n" % label)

        if entryLines == []:  # nothing found
            return "".join(msg)
        headerKey = ["name", "value", ""]
        minWidthList = [lang.LMARGINW, lang.NAMEW, 0]
        bufList = [1, 1, 1]
        justList = ["l", "l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class TEmap(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIn(ao, args='b 2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TEmap(ao, args='a')

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.gfxSwitch = 1  # display
        self.cmdStr = "TEmap"

    def gather(self):
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()

    def process(self):
        if not self.ao.aoInfo["refreshMode"]:  # if refresh mode is off
            for tName in list(self.ao.textureLib.keys()):
                ok, msg = self._tiRefresh(tName)  # update esObj if refreshmode off
        self.tiMapDict = self._teGetTimeMapDict()

    def display(self):
        tiMapDict = self.tiMapDict
        termWidth = self.termObj.w
        graphWidth = termWidth - lang.LMARGINW
        startTime, endTime, totalDur = self._teGetTotalTimeRange(tiMapDict)

        durString = "%.2fs" % totalDur
        ruler = "%s%s\n" % (
            durString.ljust(lang.LMARGINW),
            typeset.graphRuler(graphWidth),
        )
        msg = []
        msg.append("TextureEnsemble Map:\n")
        msg.append(ruler)
        tiNameList = list(tiMapDict.keys())
        tiNameList.sort()
        for tiName in tiNameList:
            s, e = tiMapDict[tiName]["tRange"]
            graph = typeset.graphDuration(totalDur, s, e, graphWidth, "_")
            msg.append("%s%s\n" % (tiName.ljust(lang.LMARGINW), graph))
            for tcName in list(tiMapDict[tiName]["cloneDict"].keys()):
                cloneS, cloneE = tiMapDict[tiName]["cloneDict"][tcName]["tRange"]
                graph = typeset.graphDuration(totalDur, cloneS, cloneE, graphWidth, ".")
                nameLabel = lang.TAB + tcName.ljust((lang.LMARGINW - lang.TABW))
                msg.append("%s%s\n" % (nameLabel, graph))
        return "".join(msg)

    def displayGfx(self, fmt, dir=None):
        prefDict = self.ao.external.getPrefGroup("external")
        barHEIGHT = 8  # height of each texture-bar
        winWIDTH = 700  # should be able to be set w/ cmd-line arg
        obj = graphEnsemble.TEmapCanvas(
            self.ao, self.tiMapDict, barHEIGHT, winWIDTH, fmt
        )
        obj.show(dir, prefDict)

    def displayGfxUtil(self, fmt, fp):
        barHEIGHT = 8  # height of each texture-bar
        winWIDTH = 540  # should be able to be set w/ cmd-line arg
        obj = graphEnsemble.TEmapCanvas(
            self.ao, self.tiMapDict, barHEIGHT, winWIDTH, fmt
        )
        # second arg sets openMedia to false
        obj.write(fp, 0)


class TEmidi(Command):
    """sets midi tempo for the complete midi score
    work done mostly from within midiTools.py

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TIn(ao, args='b 2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TEmidi(ao, args='230')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TEmidi"

    def _teCheckTempo(self, usrStr):
        """util to check tempo values for midi master tempo
        must be an integer"""
        usrVal = drawer.strToNum(usrStr, "float", 0, 9999)
        if usrVal == None:
            return None
        else:
            usrVal = int(round(usrVal))  # round to an integer
            return usrVal

    def gather(self):
        args = self.args

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        pmtrValue = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            pmtrValue = self._teCheckTempo(args.get(0))  # get number
            if pmtrValue == None:
                return self._getUsage()
        if pmtrValue == None:
            while 1:
                query = lang.msgTEgetTempo % self.ao.midiTempo
                pmtrValue = dialog.askStr(query, self.termObj)
                if pmtrValue == None:
                    return lang.msgReturnCancel
                pmtrValue = self._teCheckTempo(pmtrValue)
                if pmtrValue == None:
                    dialog.msgOut(lang.msgTEtempoError, self.termObj)
                    continue
                break
        self.pmtrValue = pmtrValue

    def process(self):
        self.ao.midiTempo = self.pmtrValue  # num

    def display(self):
        return "midi tempo changed to %s.\n" % self.pmtrValue  # name


# -----------------------------------------------------------------||||||||||||--


class TCn(Command):
    """creates exact duplicate of texture instance at shifted time
    check for negative start times
    args: tcn  name  timeShift

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCn"

    def gather(self):
        args = self.args

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        # make copy to work on and replace: cretes new dict if necessary
        # cloneDict = self.ao.cloneLib.getCloneDict(self.ao.activeTexture)
        self.name = None
        # self.timeShift = None # time shift value
        self.tName = self.ao.activeTexture

        if args != "":
            args = argTools.ArgOps(args)
            self.name = args.get(0)
            if self.name == None:
                return self._getUsage()
            if self._nameTest(self.name) != None:
                return self._getUsage(self._nameTest(self.name))
            if self.ao.cloneLib.cExists(self.tName, self.name):
                return self._getUsage()  # 1 means that self.name exists
        if self.name == None:  # get frm user
            query = "name this TextureClone:"
            self.name = self._tcGetNewName(query, self.tName)
            if self.name == None:
                return lang.msgReturnCancel

    def process(self):
        t = self.ao.textureLib[self.tName]
        auxNo = t.auxNo
        auxFmt = t.getAuxOutputFmt()
        self.ao.cloneLib.loadDefault(self.tName, self.name, auxNo, auxFmt)
        # need to score clone to update absTime if refresh mode is on
        if self.ao.aoInfo["refreshMode"]:
            c = self.ao.cloneLib.get(self.tName, self.name)
            c.score(t.getScore(), t.getRefClone())

    def display(self):
        msg = "TC %s created.\n" % self.name
        return msg


class TCv(Command):
    """views the current clone, or name if provided with args

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCv(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCv"

    def gather(self):
        args = self.args
        self.tName = self.ao.activeTexture

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        if self._tcTestExistance(self.tName) != None:  # check if clones exist
            return self._tcTestExistance(self.tName)

        self.name = None

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = args.get(0)
            if not self.ao.cloneLib.cExists(self.tName, self.name):
                return self._getUsage()
        else:
            self.name = self.ao.cloneLib.current(self.tName)

    def process(self):
        pass

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.name)

    def display(self):
        extData = {}
        clone = self.ao.cloneLib.get(self.tName, self.name)
        headList, entryLines = clone.repr("full", extData)
        headerKey = []  # removes header
        minWidthList = [lang.LMARGINW, 0]
        bufList = [0, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        headList.append("%s\n" % table)
        return "".join(headList)


class TCo(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='b')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCo(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCo"

    def gather(self):
        args = self.args

        self.tName = self.ao.activeTexture
        if self._tcTestExistance(self.tName) != None:  # check existance
            return self._tcTestExistance(self.tName)
        self.name = None
        cloneNames = self.ao.cloneLib.cNames(self.tName)
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = drawer.inList(args.get(0), cloneNames)
            if self.name == None:
                return self._getUsage()
        if self.name == None:
            self.name = self._chooseFromList(
                "which TextureClone to make active?", cloneNames, "case"
            )
            if self.name == None:
                return lang.msgTIbadName

    def process(self):
        self.ao.cloneLib.select(self.tName, self.name)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.name)

    def display(self):
        return "TC %s of TI %s now active.\n" % (self.name, self.tName)


class TCmute(Command):
    """mutes the current clone

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCmute(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCmute"

    def _tcMute(self, tName, cName):
        # will toggle
        self.ao.cloneLib.mute(tName, cName)
        if not self.ao.cloneLib.muteStatus(tName, cName):
            return "TC %s of TI %s is no longer muted.\n" % (cName, tName)
        else:
            return "TC %s of TI %s is now muted.\n" % (cName, tName)
        return None

    def gather(self):
        args = self.args
        self.mList = []
        self.tName = self.ao.activeTexture

        if self._tcTestExistance(self.tName) != None:  # check existance
            return self._tcTestExistance(self.tName)

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            if args.list(0, "end") != None:  # if supplied
                for name in args.list(0, "end"):
                    self.mList.append(name)
            else:
                return self._getUsage()
        else:
            self.mList.append(self.ao.cloneLib.current(self.tName))

    def process(self):
        self.report = []
        for name in self.mList:
            msg = self._tcMute(self.tName, name)
            if msg != None:
                self.report.append(msg)
            else:
                self.report.append(lang.msgBadArgFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self._strListToArgList(self.mList))

    def display(self):
        return "".join(self.report)


class TCls(Command):
    """shows all clones for current texture, with adjust start and end
    times (ls for current textre)
    check for negative start times

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCls(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCls"

    def gather(self):
        self.tName = self.ao.activeTexture
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        if self._tcTestExistance(self.tName) != None:  # check if clones exist
            return self._tcTestExistance(self.tName)

    def _tcGetActiveStr(self, cName):
        if cName == self.ao.cloneLib.current(self.tName):
            return lang.ACTIVE
        else:
            return lang.INACTIVE

    def process(self):
        pass

    def display(self):
        tName = self.ao.activeTexture
        msg = []
        msg.append("TextureClones of TI %s\n" % tName)
        # need time range from texture
        refDict = self.ao.textureLib[tName].getRefClone()
        entryLines = []
        for cName in self.ao.cloneLib.cNames(tName):
            # add status to refDict
            refDict["activeStr"] = self._tcGetActiveStr(cName)
            clone = self.ao.cloneLib.get(tName, cName)
            entryLines.append(clone.repr("list", refDict))

        headerKey = [
            "",
            "name",
            lang.MUTELABEL,
            "duration",
        ]
        minWidthList = [
            lang.TABW,
            lang.NAMEW,
            2,
            16,
        ]
        bufList = [0, 1, 0, 1]
        justList = [
            "c",
            "l",
            "l",
            "l",
        ]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class TCe(Command):
    """eidits attributes of a clone

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCe(ao, args='a fa,(ru,0,1)')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCe"

    def gather(self):
        args = self.args
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        tName = self.ao.activeTexture
        if self._tcTestExistance(tName) != None:  # check if clones exist
            return self._tcTestExistance(tName)
        # get ref to method
        decodePmtrName = self.ao.cloneLib.decodePmtrName
        p = None
        usrDataEval = None
        cName = self.ao.cloneLib.current(tName)

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            p, label = decodePmtrName(args.get(0), "str")  # aprop to clone
            p = self._numPmtrConvertLabel(p, tName)
            if p == None:
                return self._getUsage()
            else:  # do for path too
                usrDataEval, msg = self._tcEvalUsrStr(
                    args.get(1, "end", keepSpace=True), p
                )
                usrDataEval = self._tcCompleteEditData(p, usrDataEval, tName, cName)
            if usrDataEval == None:
                return self._getUsage()

        if p == None or usrDataEval == None:
            p = dialog.askStr(lang.msgTCePmtrSel % tName, self.termObj)
            p, label = decodePmtrName(p, "str")
            if p == None:
                return lang.msgTCbadPmtrName
            demo, demoAdjust = self._tcGetDemo(tName, cName, p, label, "edit")
            if demo == None:
                return demoAdjust  # this is the error message
            if p in ("time", "sus", "acc", "fieldQ", "octQ", "ampQ", "panQ"):
                usrStr = dialog.askStr(demo, self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            elif p[:4] == "auxQ":
                p = self._getNumPmtr("aux", tName, p)
                if p == None:
                    return lang.msgReturnCancel
                usrStr = dialog.askStr((demo[p] + demoAdjust), self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            elif p[:6] == "cloneQ":
                p = self._getNumPmtr("clone", tName, p)
                if p == None:
                    return lang.msgReturnCancel
                usrStr = dialog.askStr((demo[p] + demoAdjust), self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
            # eval data, evaluate and complete complete
            usrDataEval, errorMsg = self._tcEvalUsrStr(usrStr, p)
            if usrDataEval == None:
                return errorMsg
            usrDataEval = self._tcCompleteEditData(p, usrDataEval, tName, cName)
        self.p = p
        self.usrDataEval = usrDataEval
        self.label = label
        self.tName = tName
        self.cName = cName

    def process(self):
        refresh = self.ao.aoInfo["refreshMode"]
        self.ok, self.msg = self._tcEdit(
            self.tName, self.cName, self.p, self.usrDataEval, refresh
        )

    def log(self):
        if self.gatherStatus and self.ok != None:  # if complete
            return "%s %s %s" % (
                self.cmdStr,
                self.p,
                drawer.listToStr(self.usrDataEval),
            )

    def display(self):
        if not self.ok:  # error encountered
            return lang.TAB + "TCe %s %s\n" % (lang.ERROR, self.msg)
        else:
            return "TC %s: parameter %s updated.\n" % (self.cName, self.label)


class TCcp(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCcp(ao, args='a b')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCcp"

    def _tcCopy(self, srcName, copyName):
        """copies a texture"""
        # self.ao.cloneLib
        if (
            srcName != copyName
            and self.ao.cloneLib.cExists(self.tName, srcName)
            and copyName not in self.ao.cloneLib.cNames(self.tName)
        ):
            self.ao.cloneLib.cCopy(self.tName, srcName, copyName)
            return "TC %s created.\n" % copyName
        else:
            return None

    def gather(self):
        args = self.args
        self.cpList = []
        self.oldName = None

        self.tName = self.ao.activeTexture
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        if self._tcTestExistance(self.tName) != None:  # check if clones exist
            return self._tcTestExistance(self.tName)

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            self.oldName = drawer.inList(
                args.get(0), self.ao.cloneLib.cNames(self.tName)
            )
            if self.oldName == None:
                return self._getUsage()
            if args.list(1, "end") != None:  # if supplied
                for newName in args.list(1, "end"):
                    self.cpList.append(newName)
            else:
                return self._getUsage()

        if self.cpList == []:
            self.oldName = self._chooseFromList(
                "which Clone to copy?", self.ao.cloneLib.cNames(self.tName), "case"
            )
            if self.oldName == None:
                return lang.msgTCbadName
            query = "name this copy of TC %s:" % (repr(self.oldName))
            name = self._tcGetNewName(query, self.tName)
            if name == None:
                return lang.msgReturnCancel
            self.cpList.append(name)

    def process(self):
        self.report = []
        for newName in self.cpList:
            msg = self._tcCopy(self.oldName, newName)
            if msg != None:  # fall through if fails
                self.report.append(msg)
            else:
                self.report.append(lang.msgBadArgFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s %s" % (
                self.cmdStr,
                self.oldName,
                self._strListToArgList(self.cpList),
            )

    def display(self):
        return "".join(self.report)


class TCmap(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCmap(ao) # cannot test interactively

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.gfxSwitch = 1  # display
        self.cmdStr = "TCmap"

    def gather(self):
        args = self.args
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        self.tName = self.ao.activeTexture
        if self._tcTestExistance(self.tName) != None:  # check if clones exist
            return self._tcTestExistance(self.tName)

        self.cName = self.ao.cloneLib.current(self.tName)
        self.tmRelation = "post"  # cant change, always post for clone
        self.xRelation = "event"  # can change to time

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.xRelation = self._tiConvertEventTime(args.get(0))
            if self.xRelation == None:
                return self._getUsage()
        else:  # use default
            pass  # get from user eventually

    def process(self):
        if not self.ao.aoInfo["refreshMode"]:  # if refeshmode off
            ok, msg = self._tiRefresh(self.tName)  # update esObj if refreshmode off

    def display(self):
        return "TCmap (%s-base, %s-TM) display complete.\n" % (
            self.xRelation,
            self.tmRelation,
        )

    def displayGfx(self, fmt, dir=None):
        prefDict = self.ao.external.getPrefGroup("external")
        obj = graphPmtr.TImapCanvas(
            self.ao, self.tName, self.cName, self.tmRelation, self.xRelation, fmt
        )
        obj.show(dir, prefDict)


class TCdoc(Command):
    """displays all essential information about parameters
    of this texture, as well as in
    args can be the name of a different texture

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCdoc(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCdoc"

    def gather(self):
        args = self.args
        self.tName = self.ao.activeTexture

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        if self._tcTestExistance(self.tName) != None:  # check if clones exist
            return self._tcTestExistance(self.tName)

        self.name = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = args.get(0)
        else:
            self.name = self.ao.cloneLib.current(self.tName)

    def process(self):
        pass

    def display(self):
        """this should be moved inside of texture"""
        tName = self.tName
        t = self.ao.textureLib[tName]
        orcObj = t.getOrc()
        c = self.ao.cloneLib.get(tName, self.name)

        # part of clone doc comes from texture; clone has no instrument rep
        # get clone static data, head
        headList, entryLines = c.repr("docStandard")
        # get inst, aux information from texture

        # can interleave aux info here
        auxInterleave = drawer.listInterleave(
            t.repr("docAuxNames"), c.repr("docAuxArgs"), 1
        )
        # inst not needed, not in tcv: t.repr('docInst')
        entryLines = entryLines + auxInterleave + c.repr("docStatic")

        headerKey = []  # removes header
        minWidthList = [lang.LMARGINW, 0]
        bufList = [0, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        headList.append("%s\n" % table)
        return "".join(headList)


class TCrm(Command):
    """remove a clone from this textures clone dict
        check for negative start times

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCrm(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCrm"

    def _tcRemove(self, tiName, cloneName):
        if tiName in self.ao.cloneLib.tNames():
            if self.ao.cloneLib.cExists(tiName, cloneName) == 1:  # exists
                self.ao.cloneLib.delete(tiName, cloneName)
                return "TC %s destroyed.\n" % cloneName
        else:
            return None

    def gather(self):
        args = self.args
        self.rmList = []

        tiName = self.ao.activeTexture

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        if self._tcTestExistance(tiName) != None:  # check if clones exist
            return self._tcTestExistance(tiName)

        if args != "":  # removes all in list
            args = argTools.ArgOps(args, stripComma=True)
            if args.list(0, "end") != None:  # if supplied
                for name in args.list(0, "end"):
                    name = drawer.inList(name, self.ao.cloneLib.cNames(tiName))
                    if name == None:
                        return self._getUsage()
                    self.rmList.append(name)
            else:
                return self._getUsage()

        if self.rmList == []:
            choiceList = self.ao.cloneLib.cNames(tiName)
            name = self._chooseFromList(
                "select a TextureClone to delete:", choiceList, "case"
            )
            if name == None:
                return lang.msgTCbadName
            query = "are you sure you want to delete TextureClone %s? " % name
            askUsr = dialog.askYesNoCancel(query, 1, self.termObj)
            if askUsr == 1:
                self.rmList.append(name)
            else:
                return lang.msgReturnCancel
        self.tiName = tiName

    def process(self):
        self.report = []
        for name in self.rmList:
            msg = self._tcRemove(self.tiName, name)
            if msg != None:
                self.report.append(msg)
            else:
                self.report.append(lang.msgBadArgFormat)

    def display(self):
        return "".join(self.report)


class TCals(Command):
    """list all attributes of a texture, a hidden command

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCn(ao, args='a')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TCals(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TCals"

    def gather(self):
        self.tName = self.ao.activeTexture

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()
        if self._tcTestExistance(self.tName) != None:  # check if clones exist
            return self._tcTestExistance(self.tName)
        self.name = self.ao.cloneLib.current(self.tName)

    def process(self):
        pass

    def display(self):
        clone = self.ao.cloneLib.get(self.tName, self.name)
        directoryOfattributes = dir(clone)
        msg = []
        msg.append("attributes of TC %s:\n" % self.name)
        entryLines = []
        for entry in directoryOfattributes:
            value = getattr(clone, entry)
            value = str(value).replace(" ", "")
            entryLines.append([entry, value])
        headerKey = ["name", "value"]
        minWidthList = [lang.LMARGINW, 0]
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--


class TTls(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TTls(ao)
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TTls"

    def gather(self):
        # may need to limit this to textures of the same module
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

    def process(self):
        pass

    def display(self):
        keyList = temperament.temperamentNames
        msg = []
        msg.append("TextureTemperaments available for TI %s:\n" % self.ao.activeTexture)
        entryLines = []
        for entry in keyList:
            if entry == self.ao.textureLib[self.ao.activeTexture].temperamentName:
                status = lang.ACTIVE
            else:
                status = lang.INACTIVE
            # tuning string takes too much space
            entryLines.append([status, entry, ""])
        headerKey = ["", "name", "tunning"]
        minWidthList = (lang.TABW, lang.NAMEW, 1)
        bufList = [0, 2, 1]
        justList = ["c", "l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "twoColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class TTo(Command):
    """
    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = TIn(ao, args='a 0')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = TTo(ao, args='nl')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TTo"

    def gather(self):
        args = self.args

        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()
        if self._tiTestNameExists() != None:  # check name
            return self._tiTestNameExists()

        # temperamentObj = temperament.Temperament() # generic
        # keyList = temperament.temperamentNames

        self.name = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = temperament.temperamentNameParser(args.get(0))
            if self.name == None:
                return self._getUsage()
        if self.name == None:  # self.names are not translated
            query = lang.msgTTselectName % self.ao.activeTexture
            self.name = self._chooseFromList(
                query,
                temperament.temperamentNames,
                "noCase",
                temperament.temperamentNameParser,
            )
            if self.name == None:
                return lang.msgTTbadName

    def process(self):
        self.ao.textureLib[self.ao.activeTexture].updateTemperament(self.name)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.name)

    def display(self):
        return "TT %s now active for TI %s.\n" % (self.name, self.ao.activeTexture)


# -----------------------------------------------------------------||||||||||||--


class _CommandEO(Command):
    """parent of all eventMode commands"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)

    def _emSelectOutputFormat(self):
        """have user select format"""
        longName, shortName = drawer.acronymLibToStr(outFormat.outputFormatNames)
        query = lang.msgEMgetOutput % (longName, shortName)
        while 1:
            reply = dialog.askStr(query, self.termObj)
            if reply == None:
                return None
            reply = outFormat.outputFormatParser(reply)
            if reply == None:
                dialog.msgOut(lang.msgEMnoOutput, self.termObj)
                continue
            else:
                return reply

    def _emGetOutputFormats(self, format="data"):
        prefList = self.ao.external.getPref("athena", "eventOutput")
        prefData = list(eval(prefList))
        if format == "data":
            return prefData  # return as list of strings
        elif format == "str":
            # using grammar version here without connector
            return drawer.listToStrGrammar(prefData, None)

    def _emSetOuptutFormats(self, fmtList):
        prefList = []
        for usrStr in fmtList:
            valStr = outFormat.outputFormatParser(usrStr)
            if valStr == None:  # error
                environment.printWarn(
                    [lang.WARN, "bad output format given: %s" % usrStr]
                )
                continue
            if valStr not in prefList:  # filter to remove redundancies
                prefList.append(valStr)
        prefStr = repr(tuple(prefList))
        self.ao.external.writePref("athena", "eventOutput", prefStr)


class EOo(_CommandEO):
    """add an output format"""

    def __init__(self, ao, args="", **keywords):
        _CommandEO.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "EOo"

    def gather(self):
        args = self.args
        self.currentFormat = self._emGetOutputFormats()
        self.fmt = []
        self.update = 0

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            argList = args.list(0, "end")  # args.list will get a list
            if argList == None:
                return self._getUsage()
            for fmt in argList:
                fmt = outFormat.outputFormatParser(fmt)
                if fmt == None:
                    return self._getUsage()
                else:
                    self.fmt.append(fmt)

        if self.fmt == []:  # get from user
            self.fmt = self._emSelectOutputFormat()
            if self.fmt == None:
                return lang.msgReturnCancel
            self.fmt = [self.fmt]  # make into a list

        for fmt in self.fmt:
            if fmt not in self.currentFormat:
                self.currentFormat.append(fmt)
                self.update = 1

    def process(self):
        if self.update:
            self._emSetOuptutFormats(self.currentFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            fmtStr = drawer.listScrub(self.fmt, None, "rmQuote")
            return "%s %s" % (self.cmdStr, fmtStr)

    def display(self):
        prefList = self._emGetOutputFormats("str")
        if len(prefList) > 0:
            return "EventOutput formats: %s.\n" % prefList
        else:
            return "EventOutput formats active: none.\n"


class EOrm(_CommandEO):
    """remove an output format"""

    def __init__(self, ao, args="", **keywords):
        _CommandEO.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "EOrm"

    def gather(self):
        args = self.args
        self.currentFormat = self._emGetOutputFormats()
        self.fmt = []
        self.update = 0

        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            argList = args.list(0, "end")  # args.list will get a list
            if argList == None:
                return self._getUsage()
            for fmt in argList:
                fmt = outFormat.outputFormatParser(fmt)
                if fmt == None:
                    return self._getUsage()
                else:
                    self.fmt.append(fmt)

        if self.fmt == []:  # get from user
            self.fmt = self._emSelectOutputFormat()
            if self.fmt == None:
                return lang.msgReturnCancel
            self.fmt = [self.fmt]  # make into a list

        for fmt in self.fmt:
            if fmt in self.currentFormat:
                self.currentFormat.remove(fmt)
                self.update = 1

    def process(self):
        if self.update:
            self._emSetOuptutFormats(self.currentFormat)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            fmtStr = drawer.listScrub(self.fmt, None, "rmQuote")
            return "%s %s" % (self.cmdStr, fmtStr)

    def display(self):
        prefList = self._emGetOutputFormats("str")
        if len(prefList) > 0:
            return "EventOutput formats: %s.\n" % prefList
        else:
            return "EventOutput formats active: none.\n"


class EOls(_CommandEO):
    def __init__(self, ao, args="", **keywords):
        _CommandEO.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "EOls"

    def gather(self):
        pass

    def process(self):
        pass

    def display(self):
        msg = []
        msg.append("EventOutput active:\n")
        entryLines = []
        prefList = self._emGetOutputFormats()
        allEvents = list(outFormat.outputFormatNames.values())
        allEvents.sort()
        for entry in allEvents:
            if entry in prefList:
                status = lang.ACTIVE
            else:
                status = lang.INACTIVE
            # tuning string takes too much space
            entryLines.append([status, entry])
        headerKey = ["", "name"]
        minWidthList = (lang.TABW, lang.NAMEW)
        bufList = [0, 2]
        justList = [
            "c",
            "l",
        ]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "twoColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--
class EMo(Command):
    """switches value of self.ao.activeEventMode"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "EMo"

    def _elConvertMode(self, usrStr):
        return eventList.eventModeParser(usrStr)

    def gather(self):
        args = self.args
        self.modeVal = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            modeStr = args.get(0, "end")
            if modeStr == None:
                return self._getUsage()
            self.modeVal = self._elConvertMode(modeStr)
            if self.modeVal == None:
                return self._getUsage()
        if self.modeVal == None:
            while self.modeVal == None:
                query = lang.msgEMselect
                self.modeVal = dialog.askStr(query, self.termObj)
                if self.modeVal == None:
                    return lang.msgReturnCancel
                self.modeVal = self._elConvertMode(self.modeVal)
                if self.modeVal == None:
                    dialog.msgOut(lang.msgEMbadMode, self.termObj)
                    continue

    def process(self):
        # does necessary updating of self.ao.orcObj
        self.ao.setEventMode(self.modeVal)
        self.ao.external.writePref("athena", "eventMode", self.modeVal)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.modeVal)

    def display(self):
        return lang.msgEMmodeSet % self.modeVal


class EMls(Command):
    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "EMls"

    def gather(self):
        pass

    def process(self):
        pass

    def display(self):
        msg = []
        msg.append("EventMode modes available:\n")
        entryLines = []
        names = list(eventList.eventModeNames.values())
        names.sort()
        for entry in names:
            if entry == self.ao.activeEventMode:
                status = lang.ACTIVE
            else:
                status = lang.INACTIVE
            # tuning string takes too much space
            entryLines.append([status, entry])
        headerKey = ["", "name"]
        minWidthList = (lang.TABW, lang.NAMEW)
        bufList = [0, 2]
        justList = [
            "c",
            "l",
        ]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "twoColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class EMv(Command):
    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "EMv"

    def gather(self):
        pass

    def process(self):
        pass

    def display(self):
        emObj = eventList.factory(self.ao.activeEventMode, self.ao)
        outRequest = self.ao.external.getPref("athena", "eventOutput", 1)

        headList, entryLines = emObj.reprDoc(outRequest)
        headerKey = []
        minWidthList = [lang.LMARGINW, 0]
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        headList.append("%s\n" % table)
        return "".join(headList)


class EMi(Command):
    """prints a list of all instruments"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0
        self.gatherSwitch = 1
        self.cmdStr = "EMi"

    def gather(self):
        args = self.args
        self.instNoRange = None

        self.instInfo, self.instNoList = self.ao.orcObj.getInstInfo()
        self.instNoList = list(self.instNoList)
        self.instNoList.sort()
        minInstNo = self.instNoList[0]
        maxInstNo = self.instNoList[-1]  # last should be max
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.instNoRange = [
                drawer.strToNum(args.get(0), "int", minInstNo, maxInstNo)
            ]
            if args.get(1) != None:
                self.instNoRange.append(
                    drawer.strToNum(args.get(1), "int", minInstNo, maxInstNo)
                )
            self.instNoRange.sort()
        else:  # use default
            pass  # get from user eventually

    def display(self):
        msg = []
        msg.append(lang.msgEMinstAvail % self.ao.orcObj.name)
        entryLines = []
        for key in self.instNoList:
            if self.instNoRange != None:
                if key < self.instNoRange[0]:
                    continue
                if len(self.instNoRange) > 1:
                    if key > self.instNoRange[1]:
                        continue
            insts = str(self.instInfo[key][0])
            entryLines.append(["", key, insts])

        headerKey = ["", "number", "name"]
        minWidthList = [lang.TABW, lang.SHIFTW, 0]
        bufList = [0, 1, 1]
        justList = ["l", "l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--


class ELn(Command):
    """creates a score and all related files as needed"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "ELn"
        # only difference w/ elw
        self.refresh = 1

    def gather(self):
        if self._tiTestExistance() != None:  # check existance
            return self._tiTestExistance()

        # if len(self.ao.textureLib) == len(self._tiMuteList()):
        #  return lang.msgTIunmuteFirst

        if self._tiTestMuteStatus():  # if all textures and clonse are muted
            return lang.msgTIunmuteFirst

        self.scoPath = None
        if self.args != "":
            self.args = argTools.ArgOps(self.args)  # no strip
            self.scoPath = self._validWritePath(
                self.args.get(0, "end"), ".xml", "fpLastDirEventList"
            )
            if self.scoPath == None:
                return self._getUsage()
            scoDir, scoName = os.path.split(self.scoPath)

        if self.scoPath == None:
            self.scoPath = environment.getTempFile(".xml")
            if self.scoPath == None:
                return lang.msgReturnCancel
            scoDir, scoName = os.path.split(self.scoPath)

        # this is a dir, not a path
        self.ao.aoInfo["fpLastDirEventList"] = scoDir

        # if csound native, check the csound path with APea
        # this most be done w/ eln, as batch files are written their
        if self.ao.activeEventMode == "csoundNative":
            path = self.ao.external.getPref("external", "csoundPath")
            if path == "":
                # call command with first arg for csoundCommand
                cmdObj = APea(self.ao, "cc")
                ok, msg = cmdObj.do()
                if not ok:
                    return lang.msgReturnCancel

    def process(self):
        self.report = []
        # update last paths
        self.ao.external.writePref(
            "athena", "fpLastDirEventList", self.ao.aoInfo["fpLastDirEventList"]
        )
        # create a score object, do score conversions
        # an orc object is created from activeEventMode inside emObj
        # do not store emObj
        emObj = eventList.factory(self.ao.activeEventMode, self.ao)
        emObj.setRootPath(self.scoPath)
        # None processes all objects in the init ao
        # 1 gets evaluated preference string
        outRequest = self.ao.external.getPref("athena", "eventOutput", 1)
        ok, msg, outComplete = emObj.process(None, outRequest, self.refresh)
        if ok:  # scores exist
            self.report.append(msg)
        else:  # no scores were created
            return "%s %s" % (lang.msgELnoScores, msg)
        # writing an athenaobj happens outside of the eventmode
        if "xmlAthenaObject" in outRequest:
            # getting pathe here from EventMode object
            pathXml = emObj.outFormatToFilePath("xmlAthenaObject")
            cmdObj = AOw(self.ao, pathXml, "quite")
            ok, result = cmdObj.do()
            outComplete.append("xmlAthenaObject")
            self.report.append("%s\n" % pathXml)
        # print _MOD, 'output complete', outComplete
        self.ao.aoInfo["outComplete"] = outComplete

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.scoPath)

    def display(self):
        # only do auto render if in csound Native
        if self.ao.activeEventMode not in ["csoundNative"]:
            return "".join(self.report)
        # check if auto on is happening
        if self.ao.external.getPref("external", "autoRenderOption") == "autoOn":
            cmdObj = ELr(self.ao)
            ok, msg = cmdObj.do()
            self.report.append(msg)
            cmdObj = ELh(self.ao)
            ok, msg = cmdObj.do()
            self.report.append(msg)
        return "".join(self.report)


class ELw(ELn):
    """writes a score and all related files as needed
    does not refresh event lists, unless refresh mode is set
    """

    def __init__(self, ao, args="", **keywords):
        ELn.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "ELw"
        # only difference w/ eln
        if not self.ao.aoInfo["refreshMode"]:
            # update esObj if refreshmode off; this is necessary as user may
            # have edited textures; if this procedes w/o refreshing, edits
            # will not have been made, and el will reflect its initial form
            self.refresh = 1
        else:
            self.refresh = 0


class ELr(Command):
    """renders the most recent score in csound"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "ELr"

    def gather(self):
        # even though we just need the bat path, check to make sure
        # tt csd and sco/orc files are around
        # check last created files

        if self.ao.activeEventMode not in ["csoundNative"]:
            return lang.msgELrNotAvailable % self.ao.activeEventMode
        outComplete = self.ao.aoInfo["outComplete"]
        if "csoundData" in outComplete:
            csd = 1
        elif "csoundScore" in outComplete and "csoundOrchestra" in outComplete:
            csd = 0
        else:
            return lang.msgELcreateFirst

        # these paths have nothing to do with what files are actually created
        # these paths are always created, regardless of success
        if csd:
            csdPath = self.ao.aoInfo["fpCsd"]
            if not os.path.isfile(csdPath):
                return lang.msgELfileMoved % csdPath
        else:
            scoPath = self.ao.aoInfo["fpSco"]
            orcPath = self.ao.aoInfo["fpOrc"]
            if not os.path.isfile(scoPath):
                return lang.msgELfileMoved % scoPath
            if not os.path.isfile(orcPath):
                return lang.msgELfileMoved % orcPath
        # if csound event type was created, then all paths created will be filled
        self.batPath = self.ao.aoInfo["fpBat"]
        if not os.path.isfile(self.batPath):
            return lang.msgELfileMoved % self.batPath

    def process(self):
        pass

    def display(self):
        # include this is a display so as not to use separat thread?
        self.failFlag = osTools.launch(self.batPath)
        if self.failFlag == "failed":
            msg = lang.msgELrenderError % self.batPath
        else:
            msg = lang.msgELrenderInit % self.batPath
        return msg


class ELh(Command):
    """opens the audio file most recently created
    uses platform specific apps
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "ELh"

    def gather(self):
        outComplete = self.ao.aoInfo["outComplete"]
        if outComplete == []:
            return lang.msgELcreateFirst

        self.fmtFound = []
        msg = []

        # all outputs that produce an audio file
        self.audioPath = self.ao.aoInfo["fpAudio"]
        if "csoundData" in outComplete or "csoundScore" in outComplete:
            if os.path.isfile(self.audioPath):  # if file found
                self.fmtFound.append(self.audioPath)
            else:  # files was created but does not exists
                msg.append(lang.msgELaudioMoved % self.audioPath)

        # only midi file prodiuces an output
        self.midPath = self.ao.aoInfo["fpMidi"]
        if "midiFile" in outComplete:
            if os.path.isfile(self.midPath):  # if file found
                self.fmtFound.append(self.midPath)
            else:
                msg.append(lang.msgELaudioMoved % self.midPath)
        if self.fmtFound == []:
            return "".join(msg)

    def process(self):
        # this file render prep should be done after EMr
        #         if os.name == 'mac': # must check that fp is in found
        #             if self.audioPath in self.fmtFound:
        #                 prefDict = self.ao.external.getPrefGroup('external')
        #                 audioTools.setMacAudioRsrc(prefDict['audioFormat'],
        #                                                     self.audioPath, prefDict)
        if os.name == "posix":
            pass
        else:  # win or other
            pass

    def display(self):
        msg = []
        prefDict = self.ao.external.getPrefGroup("external")
        for hPath in self.fmtFound:  # audio path
            failFlag = osTools.openMedia(hPath, prefDict)
            if failFlag == "failed":
                msg.append(lang.msgELhearError % hPath)
            else:
                msg.append(lang.msgELhearInit % hPath)
        return "".join(msg)


class ELv(Command):
    """displays the csound score file most recently created
    uses platform specific apps
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "ELv"

    def gather(self):
        outComplete = self.ao.aoInfo["outComplete"]
        if outComplete == []:
            return lang.msgELcreateFirst
        self.viewPath = self.ao.aoInfo["fpView"]
        if not os.path.isfile(self.viewPath):  # if not a rela file
            return lang.msgELfileMoved % self.viewPath

    def process(self):
        pass

    def display(self):
        prefDict = self.ao.external.getPrefGroup("external")
        failFlag = osTools.openMedia(self.viewPath, prefDict)
        if failFlag == "failed":
            msg = lang.msgEMviewError % self.viewPath
        else:
            msg = lang.msgELviewInit % self.viewPath
        return msg


class ELauto(Command):
    """causes eln to auto render and hear a newly created score"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1
        self.gatherSwitch = 1
        self.cmdStr = "ELauto"

    def gather(self):
        args = self.args
        self.value = None
        # store current value
        self.curValue = self.ao.external.getPref("external", "autoRenderOption")
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            msg = args.get(0, "end")
            if msg == None:
                return self._getUsage()
            self.value = typeset.convertBool(msg)  # will handly off/on
            if self.value == None:
                return self._getUsage()
            if self.value:
                self.value = "autoOn"  # if true
            else:
                self.value = "autoOff"
        if self.value == None:  # w/ no args it toggles
            if self.curValue in ["", "autoOff"]:
                self.value = "autoOn"
            else:
                self.value = "autoOff"

    def process(self):
        if self.value != self.curValue:  # only chang if changed
            self.ao.external.writePref("external", "autoRenderOption", self.value)
        if self.value == "autoOn":  # get a string version
            self.valueStr = lang.ON
        else:
            self.valueStr = lang.OFF

    def display(self):
        return lang.msgELauto % self.valueStr


# -----------------------------------------------------------------||||||||||||--
class _CommandAO(Command):
    """parent class of all AO commands"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)

    # -----------------------------------------------------------------------||--
    # methods for loading and files

    def _tiLoad(
        self,
        textureName,
        textureModName,
        pathName,
        temperamentName,
        pitchMode,
        auxNo,
        pmtrQDict,
        midiPgm,
        midiCh,
        mute,
        silenceMode,
        orcMapMode,
    ):
        """this method is needs to load a texture from dry parameter list
        it will call a .create() method from a TI
        called from AOload when load xml files
        """
        self.ao.textureLib[textureName] = texture.factory(textureModName, textureName)
        # test to see if pathname exists
        pathObj = self.ao.pathLib[pathName]  ## this is a reference, not a copy
        self.ao.textureLib[textureName].load(
            pmtrQDict,
            pathObj,
            temperamentName,
            pitchMode,
            auxNo,
            self.ao.aoInfo["fpAudioDirs"],
            midiPgm,
            midiCh,
            mute,
            silenceMode,
            orcMapMode,
        )

    def _piUpdateAllReferences(self):
        """clears all ref counts on paths and recounts all uses of a path"""
        # clear all current values
        extantPaths = []
        for pathName in list(self.ao.pathLib.keys()):
            self.ao.pathLib[pathName].refCount = 0
            extantPaths.append(pathName)
        for textureName in list(self.ao.textureLib.keys()):
            pathName = self.ao.textureLib[textureName].path.name
            if pathName in extantPaths:
                self.ao.pathLib[pathName].refIncr()
            else:  # missing path check for auto, assign. no auto, create
                if "auto" not in extantPaths:
                    self._piAutoCreate("auto")
                self.ao.textureLib[textureName].path = self.ao.pathLib["auto"]
                self.ao.pathLib["auto"].refIncr()

    def _aoLoadAthenaData(self, athenaData):
        """load an athena dictionary into current athenaObject"""
        # version only written on output, not on load
        # set at startup
        self.ao.audioChannels = copy.deepcopy(athenaData["audioChannels"])
        self.ao.audioRate = copy.deepcopy(athenaData["audioRate"])

        if athenaData["author"] != "":
            # set at startup
            self.ao.author = copy.deepcopy(athenaData["author"])
        self.ao.tniMode = copy.deepcopy(athenaData["tniMode"])
        self.ao.setEventMode(athenaData["activeEventMode"])
        # will set local orchestra as well

    def _aoSaveAthenaData(self):
        """save all athena data in a dictionary"""
        athenaData = {}
        athenaData["audioChannels"] = self.ao.audioChannels
        athenaData["audioRate"] = self.ao.audioRate

        if self.ao.author == "":  # only change if it has not been set
            try:
                self.ao.author = os.environ["USER"]
            except:
                self.ao.author = ""  # default value on startup
        athenaData["author"] = self.ao.author
        athenaData["tniMode"] = self.ao.tniMode
        # remove date info from version representation
        athenaData["version"] = self.ao.versionObj.repr("dot", 0)
        athenaData["date"] = time.asctime(time.localtime())
        athenaData["activeEventMode"] = self.ao.activeEventMode
        return athenaData

    def _aoLoadPathData(self, pathData, replace="replace"):
        """load a path dictionary into current athenaObject"""
        self.ao.activePath = copy.deepcopy(pathData["activePath"])
        # self.ao.activeSetMeasure = copy.deepcopy(pathData['activeSetMeasure'])
        if replace == "replace":
            self.ao.pathLib = {}  # reinit path bin
        else:  # a name check must make sure that no paths with same name exist
            pass  # do nothing, and add paths
        if len(list(pathData["pathLib"].keys())) > 0:  # paths exist
            for pathName in list(pathData["pathLib"].keys()):
                self.ao.pathLib[pathName] = pitchPath.PolyPath(pathName)
                self.ao.pathLib[pathName].loadDataModel(pathData["pathLib"][pathName])
        else:  # no paths exist, create dummy plug
            self._piAutoCreate("auto")  # creates a path named 'auto'

    def _aoSavePathData(self):
        """save all path data in a dictionary"""
        pathData = {}
        pathData["activePath"] = self.ao.activePath
        pathData["pathLib"] = {}
        if len(list(self.ao.pathLib.keys())) > 0:  # paths exist
            for pathName in list(self.ao.pathLib.keys()):
                p = self.ao.pathLib[pathName].writeDataModel()
                pathData["pathLib"][pathName] = p
        else:  # no paths exist, create dummy plug
            pass
        return pathData

    def _aoLoadTextureData(self, textureData, replace="replace"):
        """load a texture dictionary into current athenaObject
        supply a None for parameters that have are new and have not been
        defined
        let updating go on in TMclass and below
        """
        self.ao.midiTempo = copy.deepcopy(textureData["midiTempo"])
        self.ao.activeTextureModule = copy.deepcopy(textureData["activeTextureModule"])
        if replace == "replace":
            self.ao.activeTexture = copy.deepcopy(textureData["activeTexture"])
            self.ao.textureLib = {}  # reinit path bin
        if len(list(textureData["textureLib"].keys())) > 0:  # textures exist
            for textureName in list(textureData["textureLib"].keys()):
                t = textureData["textureLib"][textureName]
                pathName = copy.deepcopy(t["pathName"])
                tmName = copy.deepcopy(t["tmName"])
                # polyphonyMode = copy.deepcopy(t['polyphonyMode'])
                temperamentName = copy.deepcopy(t["temperamentName"])
                pitchMode = copy.deepcopy(t["pitchMode"])
                silenceMode = copy.deepcopy(t["silenceMode"])
                orcMapMode = copy.deepcopy(t["orcMapMode"])
                auxNo = copy.deepcopy(t["auxNo"])
                pmtrQDict = copy.deepcopy(t["pmtrQDict"])
                midiPgm = copy.deepcopy(t["midiPgm"])
                midiCh = copy.deepcopy(t["midiCh"])
                mute = copy.deepcopy(t["mute"])
                self._tiLoad(
                    textureName,
                    tmName,
                    pathName,
                    temperamentName,
                    pitchMode,
                    auxNo,
                    pmtrQDict,
                    midiPgm,
                    midiCh,
                    mute,
                    silenceMode,
                    orcMapMode,
                )
        if replace == "replace":
            self.ao.cloneLib = clone.CloneManager()
        for tag in list(textureData["cloneLib"].keys()):
            post = tag.split(",")  # comma separated
            tName, cName = post[0], post[1]
            c = textureData["cloneLib"][tag]
            mute = copy.deepcopy(c["mute"])
            auxNo = copy.deepcopy(c["auxNo"])
            # always update from texture
            auxFmt = self.ao.textureLib[tName].getAuxOutputFmt()
            # now in pmtrQDicts
            # timeRef = copy.deepcopy(c['timeRef'])
            pmtrQDict = copy.deepcopy(c["pmtrQDict"])
            # load data into clone bin
            self.ao.cloneLib.load(tName, cName, pmtrQDict, auxNo, auxFmt, mute)
            # manually score each texture to refresh values
            t = self.ao.textureLib[tName]
            c = self.ao.cloneLib.get(tName, cName)
            c.score(t.getScore(), t.getRefDict())

    def _aoSaveTextureData(self):
        """save all texture data in a dictionary"""
        textureData = {}
        textureData["activeTexture"] = self.ao.activeTexture
        textureData["activeTextureModule"] = self.ao.activeTextureModule
        textureData["midiTempo"] = self.ao.midiTempo  # added 1.1
        textureData["textureLib"] = {}
        if len(list(self.ao.textureLib.keys())) > 0:  # textures exist
            for tName in list(self.ao.textureLib.keys()):
                textureData["textureLib"][tName] = {}
                t = textureData["textureLib"][tName]
                t["pathName"] = self.ao.textureLib[tName].path.name
                t["tmName"] = self.ao.textureLib[tName].tmName
                # t['polyphonyMode'] = self.ao.textureLib[tName].polyphonyMode
                t["temperamentName"] = self.ao.textureLib[tName].temperamentName
                t["midiPgm"] = self.ao.textureLib[tName].midiPgm
                t["midiCh"] = self.ao.textureLib[tName].midiCh
                t["mute"] = self.ao.textureLib[tName].mute
                t["pitchMode"] = self.ao.textureLib[tName].pitchMode
                t["silenceMode"] = self.ao.textureLib[tName].silenceMode
                t["orcMapMode"] = self.ao.textureLib[tName].orcMapMode
                t["auxNo"] = self.ao.textureLib[tName].auxNo
                t["pmtrQDict"] = self.ao.textureLib[tName].pmtrQDict
        textureData["cloneLib"] = {}
        for tName in self.ao.cloneLib.tNames():
            for cName in self.ao.cloneLib.cNames(tName):
                tag = "%s,%s" % (tName, cName)
                textureData["cloneLib"][tag] = {}
                c = textureData["cloneLib"][tag]
                clone = self.ao.cloneLib.get(tName, cName)
                c["mute"] = clone.mute
                c["auxNo"] = clone.auxNo
                # do not store auxFmt; always update from load
                # c['timeRef'] = clone.timeRef
                c["pmtrQDict"] = clone.pmtrQDict
        return textureData

    def _aoDetermineFileFormat(self, path):
        "check xml type of a file, or determine if it is an old pickled file"
        with open(path, "r") as f:
            content = f.read()

        return checkFileFormat(content)

    # -----------------------------------------------------------------------||--
    # tools for updating data imported from xml and evaluated, but not loaded

    def _aoRenameConflicts(self, pData, tData):
        """takes path and texture dictionaries and compares to local
        self.ao.pathLib and self.ao.textureLib
        corrects for name conflicts by appending underscore
        """
        for mgTextureName in list(tData["textureLib"].keys()):
            if mgTextureName in list(self.ao.textureLib.keys()):
                oldMgTextureName = copy.deepcopy(mgTextureName)
                while 1:
                    mgTextureName = mgTextureName + "_"
                    if mgTextureName not in list(self.ao.textureLib.keys()):
                        break
                newData = copy.deepcopy(tData["textureLib"][oldMgTextureName])
                tData["textureLib"][mgTextureName] = newData
                if oldMgTextureName in list(tData["cloneLib"].keys()):
                    data = copy.deepcopy(tData["cloneLib"][oldMgTextureName])
                    tData["cloneLib"][mgTextureName] = data
                    del tData["cloneLib"][oldMgTextureName]
                del tData["textureLib"][oldMgTextureName]
        for mgPathName in list(pData["pathLib"].keys()):
            if mgPathName in list(self.ao.pathLib.keys()):
                oldMgPathName = copy.deepcopy(mgPathName)
                while 1:
                    mgPathName = mgPathName + "_"
                    if mgPathName not in list(self.ao.pathLib.keys()):
                        break
                newData = copy.deepcopy(pData["pathLib"][oldMgPathName])
                pData["pathLib"][mgPathName] = newData
                for textureName in list(tData["textureLib"].keys()):
                    thisPathName = tData["textureLib"][textureName]["pathName"]
                    if thisPathName == oldMgPathName:
                        tData["textureLib"][textureName]["pathName"] = mgPathName
                del pData["pathLib"][oldMgPathName]
        return pData, tData


class AOl(_CommandAO):
    """load an AthenaObject, replacing the current one

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = AOl(ao, args='empty01.xml')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = AOl(ao, args='empty02.xml')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        _CommandAO.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "AOl"

    def gather(self):
        args = self.args

        self.path = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.path = self._findFilePath(args.get(0))
            if self.path == None:
                return self._getUsage()
        if self.path == None:
            self.path, ok = dialogExt.promptChooseFile(
                lang.msgAOselectFile,
                self.ao.aoInfo["fpLastDir"],
            )
            if ok != 1:
                return lang.msgReturnCancel
        # problem if path is still == None

    def process(self):
        self.timer = rhythm.Timer()  # start
        fileFormat, msg = self._aoDetermineFileFormat(self.path)
        if fileFormat == "unknown":
            return msg
        elif fileFormat == "xml":  # open xml
            aData, pData, tData = ioTools.extractXML(self.path)
            aData, pData, tData = ioTools.evalObjectDictionary(aData, pData, tData)
            self.formatString = "%s xml" % aData["version"]
        # check backwards compat issues
        aData, pData, tData = self.ao.backward.process(aData, pData, tData)
        # load data
        self._aoLoadAthenaData(aData)
        self._aoLoadPathData(pData, "replace")
        self._aoLoadTextureData(tData, "replace")
        self._piUpdateAllReferences()
        # only after self.path + texture data are loaded
        self.timer.stop()
        # update last paths
        self.ao.aoInfo["fpLastDir"] = os.path.dirname(self.path)
        self.ao.external.writePref("athena", "fpLastDir", self.ao.aoInfo["fpLastDir"])

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.path)

    def display(self):
        return "%s%s AthenaObject loaded (%s):\n%s\n" % (
            lang.TAB,
            self.formatString,
            self.timer,
            self.path,
        )


class AOw(_CommandAO):
    """creates an XML AthenaObject file
    uses _aoSave methods to create dictionaries w/ an xml shape
    these dictionaries are then passed to ioTools
    """

    def __init__(self, ao, args="", verbose="normal", **keywords):
        _CommandAO.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.verbose = verbose
        self.cmdStr = "AOw"

    def gather(self):
        args = self.args

        if len(self.ao.pathLib) == 0:
            return lang.msgAOcreateFirst
        self.path = None

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.path = self._validWritePath(args.get(0, "end"), ".xml", "fpLastDir")
            if self.path == None:
                return self._getUsage()
        if self.path == None:
            dlgVisMet = self.ao.external.getPref("athena", "dlgVisualMethod")
            prompt = lang.msgAOnameFile
            while 1:  ## to make sure you a get a .xml ending
                self.path, ok = dialogExt.promptSaveFile(
                    prompt,
                    "ao.xml",
                )
                if ok != 1:
                    return lang.msgReturnCancel
                if self.path[-4:] == ".xml":
                    break
                else:
                    dialog.msgOut(lang.msgAObadName, self.termObj)
                    continue

    def process(self):
        athenaData = self._aoSaveAthenaData()
        pathData = self._aoSavePathData()
        textureData = self._aoSaveTextureData()
        try:
            ioTools.writeXML(self.path, athenaData, pathData, textureData)
        except (IOError, OSError):  # a bad path may be given
            return lang.msgFileError

        # sytem dependent adjustments to AO file
        if os.name == "mac":
            bbeditCreator = "R*ch"
            osTools.rsrcSetCreator(self.path, bbeditCreator, "TEXT")
            # used to be 'fLEx'
        elif os.name == "posix":
            pass
        else:  # win or other
            pass
        # update last paths
        self.ao.aoInfo["fpLastDir"] = os.path.dirname(self.path)
        self.ao.external.writePref("athena", "fpLastDir", self.ao.aoInfo["fpLastDir"])

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.path)

    def display(self):
        if self.verbose == "quite":  # not return string
            return
        else:
            return lang.TAB + "AthenaObject saved:\n%s\n" % self.path


class AOmg(_CommandAO):
    """load path and texture data into the local athenaObject
    must check for name conflicts

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = AOl(ao, args='empty01.xml')
    >>> ok, result = a.do()
    >>> ok == True
    True

    >>> a = AOmg(ao, args='empty01.xml')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        _CommandAO.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "AOmg"

    def gather(self):
        args = self.args
        self.path = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.path = self._findFilePath(args.get(0, "end"))
            if self.path == None:
                return self._getUsage()
        if self.path == None:
            self.path, ok = dialogExt.promptChooseFile(
                lang.msgAOselectFile,
                self.ao.aoInfo["fpLastDir"],
            )
            if ok != 1:
                return lang.msgReturnCancel

    def process(self):
        self.timer = rhythm.Timer()  # starts
        fileFormat, msg = self._aoDetermineFileFormat(self.path)
        if fileFormat == "unknown":
            return msg
        elif fileFormat == "xml":  # open xml
            aData, pData, tData = ioTools.extractXML(self.path)
            aData, pData, tData = ioTools.evalObjectDictionary(aData, pData, tData)
            self.formatString = "%s xml" % aData["version"]
        # check backwards compat issues
        aData, pData, tData = self.ao.backward.process(aData, pData, tData)
        pData, tData = self._aoRenameConflicts(pData, tData)
        self._aoLoadPathData(pData, "noReplace")
        self._aoLoadTextureData(tData, "noReplace")
        self._piUpdateAllReferences()  # only after path + ti data are loaded

        self.timer.stop()
        # update last paths
        self.ao.aoInfo["fpLastDir"] = os.path.dirname(self.path)
        self.ao.external.writePref("athena", "fpLastDir", self.ao.aoInfo["fpLastDir"])

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.path)

    def display(self):
        return "%s%s AthenaObject merged (%s):\n%s\n" % (
            lang.TAB,
            self.formatString,
            self.timer,
            self.path,
        )


class AOals(_CommandAO):
    """view internal attributes of athean object. hidden command

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = AOals(ao, args='empty01.xml')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        _CommandAO.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "AOals"

    def gather(self):
        pass

    def process(self):
        pass

    def display(self):
        directoryOfattributes = dir(self.ao)
        msg = []
        msg.append("attributes of AthenaObject:\n")
        entryLines = []
        for entry in directoryOfattributes:
            value = getattr(self.ao, entry)
            entryLines.append([entry, value])
        headerKey = ["name", "value"]  # table settings
        minWidthList = [lang.LMARGINW, 0]
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class AOrm(_CommandAO):
    "SUBCMD"

    def __init__(self, ao, args="", **keywords):
        _CommandAO.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "AOrm"
        self.subCmd = 1  # if 1, executed within method of interptreter

    def gather(self):
        args = self.args
        self.confirm = ""
        if args != "":
            args = argTools.ArgOps(args)
            self.confirm = args.get(0, "end")
        if self.confirm != "confirm":
            askUsr = dialog.askYesNo(
                "destroy the current AthenaObject? ", 0, self.termObj
            )
            if askUsr != 1:
                return lang.msgReturnCancel
            self.confirm = "confirm"

    def process(self):
        pass

    def log(self):  # no history stored, as ao is removed
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.cmdStr, self.confirm)

    def result(self):
        return {}


class APgfx(Command):
    """toggles between graphics modes
    note: this currently allows the selction of a visual mode that is not
    available: for instance, tk can be selected on a plat that does not have tk
    all command objs that call graphics check the pref fmt against available fmts
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "APgfx"

    def _apGetGfxFmt(self):
        while 1:
            dlgVisMet = self.ao.external.getPref("athena", "gfxVisualMethod")
            usrStr = dialog.askStr(lang.msgAPgfxSelect % dlgVisMet, self.termObj)
            if usrStr == None:
                return None
            usrStr = drawer.imageFormatParser(usrStr)
            if usrStr == None:
                continue
            else:
                return usrStr

    def gather(self):
        args = self.args
        self.formatStr = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.formatStr = drawer.imageFormatParser(args.get(0, "end"))
            if self.formatStr == None:
                return self._getUsage()
        if self.formatStr == None:
            self.formatStr = self._apGetGfxFmt()
            if self.formatStr == None:
                return lang.msgReturnCancel

    def process(self):
        self.ao.external.writePref("athena", "gfxVisualMethod", self.formatStr)

    def display(self):
        msg = lang.msgAPgfxConfirm % self.ao.external.getPref(
            "athena", "gfxVisualMethod"
        )
        return msg


class APcurs(Command):
    """toggles between cursor modes"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "APcurs"

    def process(self):
        curVal = self.ao.external.getPref("athena", "cursorToolOption")
        if curVal in ["", "cursorToolOn"]:
            self.ao.external.writePref("athena", "cursorToolOption", "cursorToolOff")
            self.ao.aoInfo["cursorToolOption"] = "cursorToolOff"
            self.value = lang.OFF
        else:
            self.ao.external.writePref("athena", "cursorToolOption", "cursorToolOn")
            self.ao.aoInfo["cursorToolOption"] = "cursorToolOn"
            self.value = lang.ON

    def display(self):
        return lang.msgAPcursorTool % self.value


class APr(Command):
    """toggles refresh modes"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "APr"

    def gather(self):
        args = self.args
        self.modeVal = None
        if args != "":
            args = argTools.ArgOps(args, stripComma=True)
            modeStr = args.get(0, "end")
            if modeStr == None:
                return self._getUsage()
            self.modeVal = typeset.convertBool(modeStr)
            if self.modeVal == None:
                return self._getUsage()
        # w/ no args it toggles
        if self.modeVal == None:
            if self.ao.aoInfo["refreshMode"]:
                self.modeVal = 0
            else:
                self.modeVal = 1

    def process(self):
        curVal = self.ao.external.getPref("athena", "refreshMode", 1)
        if self.modeVal != curVal:  # change
            self.ao.external.writePref("athena", "refreshMode", str(self.modeVal))
            self.ao.aoInfo["refreshMode"] = self.modeVal

    def display(self):
        curVal = typeset.convertBool(self.ao.aoInfo["refreshMode"])
        return lang.msgAPrefreshMode % typeset.boolAsStr(curVal)


class APwid(Command):
    """manually sets screen width"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "APwid"

    def _apConvertWidth(self, usrStr):
        """range checks width value"""
        usrStr = drawer.strToNum(usrStr, "int", 30, 300)
        return usrStr  # may be None

    def _apGetWidth(self):
        """quaries user for a screen width, returns None on error"""
        while 1:
            usrString = dialog.askStr("enter a screen width:", self.termObj)
            if usrString == None:
                return None
            number = self._apConvertWidth(usrString)
            if number == None:
                dialog.msgOut(lang.msgAObadWidth, self.termObj)
                continue
            else:
                return number

    def gather(self):
        args = self.args

        width = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            width = self._apConvertWidth(args.get(0, "end"))
            if width == None:
                return self._getUsage()
        if width == None:
            width = self._apGetWidth()
            if width == None:
                return lang.msgReturnCancel
        self.width = width

    def process(self):
        self.termObj.setWidth(self.width)

    def display(self):
        return "screen width set to %s.\n" % self.width


class APdir(Command):

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "APdir"
        # argForce is used here to reduce arg usage when called
        # by other commands, here, the do() method of Command
        # argForce gives a quasi interactive nature
        if "argForce" in list(keywords.keys()):
            self.argForce = keywords["argForce"]
        else:
            self.argForce = None

    def _updateTextureFilePaths(self):
        for name in list(self.ao.textureLib.keys()):
            self.ao.textureLib[name].updateFilePaths(self.ao.aoInfo["fpAudioDirs"])

    def _apConvertDirName(self, usrStr):
        """
        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> ao.setEventMode('m')

        >>> a = APdir(ao, args='')
        >>> a._apConvertDirName('ss')
        'fpAudioDir'
        """
        ref = {
            "fpAudioDir": ["a", "ss", "ssdir", "audio"],
            "fpScratchDir": ["c", "x", "scratch"],  # must be preference key
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr  # may be None

    def _apGetName(self):
        """quaries user name"""
        while 1:
            usrStr = dialog.askStr(lang.msgAOselAdirOrSdir, self.termObj)
            if usrStr == None:
                return None
            formatStr = self._apConvertDirName(usrStr)
            if usrStr == None:
                continue
            else:
                return formatStr

    def _apGetDir(self, name):
        # TODO: convert the name to a proper string to present to the user
        # need a module-level way to convert preference values to
        # user strings
        while 1:
            path, ok = dialogExt.promptChooseDir(
                ("select a %s directory:\n" % name),
                self.ao.aoInfo["fpLastDir"],
            )
            if ok != 1:  # path canceled
                return None
            elif os.path.isdir(path) != 1:  ## true if file is missing
                dialog.msgOut("this is not a directory", self.termObj)
                continue
            else:
                return path

    def gather(self):
        args = self.args
        self.name = None
        self.dir = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.name = self._apConvertDirName(args.get(0))
            if self.name == None:
                return self._getUsage()
            self.dir = args.get(1, "end")
            if self.dir == None:
                return self._getUsage()
            self.dir = drawer.pathScrub(self.dir)  # scrub, expand, links
            if not os.path.isdir(self.dir):
                return self._getUsage()
        if self.name == None:
            if self.argForce == None:
                self.name = self._apGetName()
                if self.name == None:
                    return lang.msgReturnCancel
            else:  # use arg from argForce dict, called form another command
                self.name = self.argForce["name"]
            self.dir = self._apGetDir(self.name)
            if self.dir == None:
                return lang.msgReturnCancel

    def process(self):
        self.ao.external.writePref("athena", "%s" % self.name, self.dir)
        # must update local variable in athenaObject
        self.ao.aoInfo["fpAudioDirs"] = self.ao.external.getFilePathAudio()
        # self.ao.fpAudioAnalysisDirs = self.ao.external.getFilePathAnalysis()
        self._updateTextureFilePaths()  # update ti objects

    def display(self):
        return "user %s directory set to %s.\n" % (self.name, self.dir)


class APea(Command):
    """select the path to various executable and other helper applications
    for backwards compat
    the csound executable on mac, sets the creator type of the csound app
    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "APea"

    def _apConvertAppType(self, usrStr):
        ref = {
            "csoundCommand": ["c", "cc"],
            #             'superColliderSynth' : ['scs', 's'],
            #             'chucK'                 : ['ck']
            "midiPlayer": ["m", "mp"],
            "audioPlayer": ["a", "ap"],
            "textReader": ["t", "tr"],
            "imageViewer": ["i", "iv"],
            "psViewer": ["p", "pv", "post"],
        }
        return drawer.selectionParse(usrStr, ref)  # may be None

    def _apGetAppType(self):
        query = "enter a file path to set: csoundCommand, midiPlayer, audioPlayer, textReader, imageViewer, or psViewer? (cc, mp, ap, tr, iv, or pv):"
        while 1:
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            appType = self._apConvertAppType(usrStr)
            if appType == None:
                continue
            else:
                return appType

    def gather(self):
        # environment.printDebug(['raw args', self.args])
        args = self.args
        args = argTools.ArgOps(args)  # no strip

        # this method using a slight different order, as it is necessary to
        # to issues this command w/ the first arg given programmatically
        # and the second arg given interactively; for this reason args are
        # accessed one at a time

        appType = None
        path = None

        if args.get(0) != None:
            appType = self._apConvertAppType(args.get(0))
            if appType == None:
                return self._getUsage()
        else:
            appType = self._apGetAppType()  # interactive command
            if appType == None:
                return lang.msgReturnCancel

        # not used for all cases, this is default
        appName = None  # not necessary in all cases
        # cases for each app class
        if appType == "csoundCommand":  # will be presented to the user
            appPathPref = ("external", "csoundPath")
            if os.name == "posix":
                appName = "csound"
            else:  # win or other
                appName = "winsound.exe"
        elif appType == "midiPlayer":  # will be presented to the user
            appPathPref = ("external", "midiPlayerPath")
        elif appType == "audioPlayer":  # will be presented to the user
            appPathPref = ("external", "audioPlayerPath")
        elif appType == "textReader":  # will be presented to the user
            appPathPref = ("external", "textReaderPath")
        elif appType == "imageViewer":  # will be presented to the user
            appPathPref = ("external", "imageViewerPath")
        elif appType == "psViewer":  # will be presented to the user
            appPathPref = ("external", "psViewerPath")
        else:
            raise Exception("unknown appType requested: %s" % appType)

        # get old path to present to user in interactive mode
        # args have already been converted above
        if args.get(1, sumRange=True) != None:
            path = args.get(1, sumRange=True, keepSpace=True)
            # environment.printDebug(['arg path received', path])
            if os.path.exists(path):
                path, ok = self._selectAppPath(path, appType, appName, appPathPref)
            else:
                return self._getUsage()
            if path == None:
                return self._getUsage()  # also failure

        else:  # get from user
            oldPath = self.ao.external.getPref(appPathPref[0], appPathPref[1])
            if oldPath == "":
                oldPath = "none"  # give string to show user
            dialog.msgOut(lang.msgAPcurentAppPath % oldPath, self.termObj)
            path, ok = self._selectAppPath(None, appType, appName, appPathPref)
            if path == None:
                return lang.msgReturnCancel

        self.path = path
        self.changed = ok

    def display(self):
        if self.changed:
            msg = "application file path changed:\n%s\n" % (self.path)
        else:
            msg = "no changes made to application file path.\n"
        return msg


class APa(Command):
    """set the value of the number of channels

    channels and sampling rate are stored in atheanobj
    file type is stored in preference file

    >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
    >>> ao.setEventMode('m')

    >>> a = APa(ao, args='f aif')
    >>> ok, result = a.do()
    >>> ok == True
    True
    >>> post = a.log()

    >>> a = APa(ao, args='ch 2')
    >>> ok, result = a.do()
    >>> ok == True
    True

    """

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "APa"

    def _apConvertAudioPrefName(self, usrStr):
        """
        >>> from athenaCL.libATH import athenaObj; ao = athenaObj.AthenaObject()
        >>> ao.setEventMode('m')

        >>> a = APa(ao, args='')
        >>> a._apConvertAudioPrefName('format')
        'audioFormat'
        """
        ref = {
            "audioFormat": ["f", "format", "ff", "type"],
            "audioChannels": ["c", "ch", "channel", "channels"],
            "audioRate": ["r", "rate", "sr"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        return usrStr  # may be None

    def _apGetAudioPref(self):
        query = "select format, channels, or rate. (f,c,r):"
        while 1:
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            post = self._apConvertAudioPrefName(usrStr)
            if post == None:
                continue
            else:
                return post

    def _apConvertChannels(self, usrStr):
        """return an integer value"""
        ref = {
            "1": ["1", "m", "mono"],
            "2": ["2", "s", "stereo"],
            "4": ["4", "q", "quad"],
        }
        usrStr = drawer.selectionParse(usrStr, ref)
        if usrStr != None:
            usrStr = int(usrStr)  # convert to int
        return usrStr  # may be None

    def _apGetChannels(self):
        query = (
            "current number of channels: %s.\nselect mono, stereo, or quad. (1,2,4):"
            % self.ao.audioChannels
        )
        while 1:
            usrStr = dialog.askStr(query, self.termObj)
            if usrStr == None:
                return None
            channels = self._apConvertChannels(usrStr)
            if channels == None:
                continue
            else:
                return channels

    def _apGetFileFormat(self):
        while 1:
            audioFormat = self.ao.external.getPref("external", "audioFormat")
            usrStr = dialog.askStr(
                "current audio file format: %s.\nselect aif, wav, or sd2. (a, w, or s):"
                % audioFormat,
                self.termObj,
            )
            if usrStr == None:
                return None
            formatStr = audioTools.audioFormatParser(usrStr)
            if usrStr == None:
                continue
            else:
                return formatStr

    def gather(self):
        args = self.args

        self.pref = None
        self.prefValue = None

        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.pref = self._apConvertAudioPrefName(args.get(0))

            if self.pref == None:
                return self._getUsage()

            if self.pref == "audioChannels":
                self.prefValue = self._apConvertChannels(args.get(1, "end"))
                if self.prefValue == None:
                    return self._getUsage()
            elif self.pref == "audioRate":
                self.prefValue = 44100
            elif self.pref == "audioFormat":
                self.prefValue = audioTools.audioFormatParser(args.get(1, "end"))
                if self.prefValue == None:
                    return self._getUsage()

        if self.pref == None:
            self.pref = self._apGetAudioPref()
            if self.pref == None:
                return lang.msgReturnCancel

            if self.pref == "audioChannels":
                self.prefValue = self._apGetChannels()
                if self.prefValue == None:
                    return self._getUsage()
            elif self.pref == "audioRate":
                self.prefValue = 44100
            elif self.pref == "audioFormat":
                self.prefValue = self._apGetFileFormat()
                if self.prefValue == None:
                    return lang.msgReturnCancel

    def process(self):
        if self.pref == "audioChannels":
            self.ao.audioChannels = self.prefValue
        elif self.pref == "audioRate":
            pass
            # self.prefValue = 44100
        elif self.pref == "audioFormat":
            self.ao.external.writePref("external", "audioFormat", self.prefValue)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (self.pref, self.prefValue)

    def display(self):
        label = self.pref.replace("audio", "").lower()
        msg = "audio %s set to %r.\n" % (label, self.prefValue)
        return msg


# class CPff(Command):
#     """set the values of the audio foile format
#     """
#
#     def __init__(self, ao, args='', **keywords):
#         Command.__init__(self, ao, args, **keywords)
#         self.processSwitch = 1 # display only
#         self.gatherSwitch = 1 # display only
#         self.cmdStr = 'CPff'
#
#
#     def gather(self):
#         args = self.args
#         self.formatStr = None
#         if args != '':
#             args = argTools.ArgOps(args) # no strip
#             self.formatStr = audioTools.audioFormatParser(args.get(0,'end'))
#             if self.formatStr == None: return self._getUsage()
#         if self.formatStr == None:
#
#     def process(self):
#         self.ao.external.writePref('external', 'audioFormat', self.formatStr)
#
#     def log(self):
#         if self.gatherStatus and self.processStatus: # if complete
#             return '%s %s' % (self.cmdStr, self.formatStr)
#
#     def display(self):
#         msg = 'audio file format changed to %s.\n' % (
#                       self.ao.external.getPref('external', 'audioFormat'))
#         return msg
#
#


# -----------------------------------------------------------------||||||||||||--
# athena history commands
class AHls(Command):
    "list history"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "AHls"

    def gather(self):
        pass

    def process(self):
        pass

    def display(self):
        keys = list(self.ao.aoInfo["history"].keys())
        keys.sort()
        if len(keys) == 0:
            return "no history.\n"

        msg = []
        msg.append("history:\n")
        entryLines = []
        i = 1
        for key in keys:
            timeStr = time.asctime(time.localtime(key))  # not displayed
            iStr = str(i)
            cmdStr = "%s" % (self.ao.aoInfo["history"][key])
            entryLines.append([iStr, cmdStr])
            i = i + 1

        headerKey = ["index", "cmd"]  # table settings
        minWidthList = [lang.LMARGINW, 0]
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class AHrm(Command):
    "list history"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "AHrm"

    def gather(self):
        pass

    def process(self):
        self.ao.aoInfo["history"] = {}  # clear

    def display(self):
        msg = []
        msg.append("history destroyed.\n")
        return "".join(msg)


# athena history commands
class AHexe(Command):
    "SUBCMD: execute history"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "AHexe"
        self.subCmd = 1  # if 1, executed within method of interptreter

    def gather(self):
        self.keys = list(self.ao.aoInfo["history"].keys())
        self.keys.sort()
        if len(self.keys) == 0:
            return "no history.\n"

        args = self.args
        self.cmdRange = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.cmdRange = self._convertListRange(
                args.get(0, "end"), 1, len(self.keys)
            )
            if self.cmdRange == None:
                return self._getUsage()

        if self.cmdRange == None:
            query = "enter a command range, between %s and %s:" % (1, len(self.keys))
            while 1:
                usrStr = dialog.askStr(query, self.termObj)
                if usrStr == None:
                    return lang.msgReturnCancel
                self.cmdRange = self._convertListRange(usrStr, 1, len(self.keys))
                if self.cmdRange == None:
                    dialog.msgOut("bad command range.", self.termObj)
                    continue
                else:
                    break

    def process(self):
        self.cmdList = []
        i = 0
        for key in self.keys:
            if i in range(self.cmdRange[0], self.cmdRange[1] + 1):
                self.cmdList.append(self.ao.aoInfo["history"][key])
            i = i + 1

    def log(self):  # may cause an infinite loop
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s %s" % (
                self.cmdStr,
                drawer.listScrub(self._setReturnError(self.cmdRange)),
            )

    def result(self):
        return {"cmdList": self.cmdList}


# -----------------------------------------------------------------||||||||||||--
# athena utility commands
class AUdoc(Command):
    "open html documentation"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "AUdoc"

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def display(self):
        import webbrowser

        url = drawer.urlPrep(lang.msgAthDocURL, "http")
        msg = "on-line documentation opened.\n"
        try:
            webbrowser.open(url)
        # this exception was found from a bug report on linux
        except KeyboardInterrupt:
            msg = "unable to open documentation: visit https://github.com/ales-tsurko/athenaCL\n"

        return msg


class AUup(Command):
    "check for athenacl updates"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "AUup"

    def gather(self):
        # update last version check even if connection not made
        self.ao.external.writePref("athena", "tLastVersionCheck", time.time())

        ok = dialog.askYesNo(lang.msgVersionCheck, self.termObj)
        if ok != 1:
            return lang.msgReturnCancel

        status, versionStr = self.ao.compareVersion()
        if status == None:  # problem, not online, not new
            return lang.msgSubmitLogFail  # not online
        elif status == "current":  # up to date
            return lang.msgUpTodate % self.ao.aoStr("human")
        ok = dialog.askYesNo(lang.msgVersionUpdate % (status, versionStr), self.termObj)
        if ok != 1:
            return lang.msgReturnCancel

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def display(self):
        import webbrowser

        webbrowser.open(drawer.urlPrep(lang.msgAthDownloadURL))
        return "%s.\n" % lang.COMPLETE


class AUlog(Command):
    "open the athenacl log file"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "AUlog"

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def display(self):
        if self.ao.external.logCheck():  # if a log exists
            prefDict = self.ao.external.getPrefGroup("external")
            osTools.openMedia(self.ao.external.logPath, prefDict)
        return "%s.\n" % lang.COMPLETE


class AUsys(Command):
    """provide a display about the system"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "AUsys"

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def display(self):
        w = self.termObj.w
        tniStat = self._scGetTnStr()
        startTime, endTime, totalDur = self._teGetTotalTimeRange()
        msg = []
        msg.append("athenaCL system:\n")
        msg.append(lang.DIVIDER * w)
        msg.append("\n")
        entryLines = []
        entryLines.append(["athenaCL version:", self.ao.aoStr()])
        entryLines.append(["python version:", self.ao.pyStr()])
        entryLines.append(["os name, sys platform:", self.ao.osStr()])
        entryLines.append(["", ""])  # draw line
        entryLines.append(["SC dictionary mode:", tniStat])
        # entryLines.append(['current SetMeasure:', self.ao.activeSetMeasure])
        entryLines.append(["current PathInstance:", self.ao.activePath])
        entryLines.append(["total PI:", self._getNoPI()])
        entryLines.append(["current TextureModule:", self.ao.activeTextureModule])
        entryLines.append(["current TextureInstance:", self.ao.activeTexture])
        entryLines.append(["total TI:", self._getNoTI()])
        entryLines.append(["total duration:", ("%.1f" % totalDur)])

        entryLines.append(["", ""])  # draw line
        entryLines.append(["current EventMode:", self.ao.activeEventMode])

        value = self.ao.external.getPref("athena", "eventOutput")
        valStr = drawer.listScrub(eval(value), None, "noQuote")
        entryLines.append(["current EventOutput formats:", valStr])

        value = self.ao.external.getPref("external", "autoRenderOption")
        entryLines.append(["EventMode auto render:", typeset.boolAsStr(value)])

        entryLines.append(["audio channels:", self.ao.audioChannels])

        value = self.ao.external.getPref("external", "audioFormat")
        entryLines.append(["audio file format:", value])
        entryLines.append(["midi tempo:", self.ao.midiTempo])

        entryLines.append(["", ""])  # draw line
        value = self.ao.external.getPref("athena", "dlgVisualMethod")
        entryLines.append(["dialog method:", value])
        value = self.ao.external.getPref("athena", "gfxVisualMethod")
        entryLines.append(["graphics format:", value])
        value = self.ao.external.getPref("athena", "refreshMode", 1)
        entryLines.append(["refresh mode:", typeset.boolAsStr(value)])

        entryLines.append(["", ""])  # draw line
        entryLines.append(["preferences:", drawer.getPrefsPath()])
        if self.ao.external.logCheck():
            entryLines.append(["log:", self.ao.external.logPath])
        value = self.ao.external.getPref("athena", "fpScratchDir")
        entryLines.append(["user scratch:", value])
        value = self.ao.external.getPref("athena", "fpAudioDir")
        entryLines.append(["user audio:", value])

        value = drawer.getcwd()
        if value == None:
            value = "none"
        entryLines.append(["working directory:", value])
        entryLines.append(["python executable:", sys.executable])

        for key, title in [
            ("midiPlayerPath", "midi player"),
            ("audioPlayerPath", "audio player"),
            ("textReaderPath", "text reader"),
            ("imageViewerPath", "image viewer"),
            ("psViewerPath", "postscript viewer"),
            ("csoundPath", "csound path"),
        ]:
            value = self.ao.external.getPref("external", key)
            entryLines.append(["%s:" % title, value])

        headerKey = []  # removes header
        minWidthList = [lang.MMARGINW, 0]
        bufList = [0, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class AUbeat(Command):
    "utility to get a beat with tapping; not currently in use"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "AUbeat"

    def gather(self):
        self.avgTempo, avgBeatT = dialog.getTempo()

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def display(self):
        if self.avgTempo == None:  # error or cancel
            return lang.msgReturnCancel
        else:
            return "average tempo found: %f\n" % self.avgTempo  # return as string


class AUpc(Command):
    "utility for pitch conversion"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "AUpc"

    def gather(self):
        args = self.args
        self.pObj = None
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.pObj = multiset.getPitch(self.termObj, args.get(0, "end"))
            if self.pObj == None:
                return self._getUsage()
        if self.pObj == None:
            self.pObj = multiset.getPitch(self.termObj)
            if self.pObj == None:
                return lang.msgReturnCancel

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            # get raw pitch srcData
            return "%s %s" % (self.cmdStr, str(self.pObj.srcData))

    def display(self):
        msg = ["AthenaUtility Pitch Converter\n"]

        entryLines = self.pObj.report()
        headerKey = []  # removes header
        minWidthList = [lang.LMARGINW, 0]
        bufList = [0, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)
        return "".join(msg)


class AUmg(Command):
    "utility for markov generation"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1
        self.gatherSwitch = 1
        self.cmdStr = "AUmg"

    def _auGetMarkovTransition(self, mObj, query):
        while 1:
            tStr = dialog.askStr(query, self.termObj)
            if tStr == None:
                return None
            try:
                self.mObj.loadTransition(tStr)
            except error.TransitionSyntaxError as e:
                dialog.msgOut("%s%s\n" % (lang.TAB, e), self.termObj)
                continue
            return tStr

    def gather(self):
        args = self.args
        # create empty markov object
        self.count = None
        self.order = None
        self.mObj = markov.Transition()
        self.post = None  # store results
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.count = args.get(0, "single", "eval")
            self.count = self._checkInRange(self.count, 1, 999)
            if self.count == None:
                return self._getUsage()
            self.order = args.get(1, "single", "eval")
            self.order = self._checkInRange(self.order, 0, 10)
            if self.order == None:
                return self._getUsage()
            try:
                self.mObj.loadTransition(args.get(2, "end", "off", "space"))
            except error.TransitionSyntaxError as e:
                return self._getUsage(e)
        if self.count == None:  # get args from user
            self.count = self._getNumber("number of generations:", "int", 1, 999)
            if self.count == None:
                return lang.msgReturnCancel
            self.order = self._getNumber("desired order:", "int", 0, 10)
            if self.order == None:
                return lang.msgReturnCancel
            msg = "enter Markov transition string:"
            post = self._auGetMarkovTransition(self.mObj, msg)  # will load in
            if post == None:
                return lang.msgReturnCancel

    def process(self):
        self.post = []
        for x in range(self.count):
            self.post.append(self.mObj.next(random.random(), self.post, self.order))

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s %s %s %s" % (self.cmdStr, self.count, self.order, str(self.mObj))

    def display(self):
        msg = ["AthenaUtility Markov Generator\n"]
        msg.append(typeset.anyDataToStr(self.post)[1:-1])
        msg.append("\n")
        return "".join(msg)


class AUma(Command):
    "utility for markov analysis"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1
        self.gatherSwitch = 1
        self.cmdStr = "AUma"

    def _auGetMarkovSequence(self, query):
        while 1:
            tStr = dialog.askStr(query, self.termObj)
            if tStr == None:
                return None
            return tStr

    def gather(self):
        args = self.args
        # create empty markov object
        self.orderMax = None
        self.sequence = None
        self.post = None  # store string
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.orderMax = args.get(0, "single", "eval")
            if self.orderMax == None:
                return self._getUsage()
            self.sequence = args.get(1, "end", "off", "space")
        if self.orderMax == None:  # get args from user
            self.orderMax = self._getNumber("maximum analysis order:", "int", 0, 10)
            if self.orderMax == None:
                return lang.msgReturnCancel
            msg = "enter space-separated string:"
            self.sequence = self._auGetMarkovSequence(msg)
            if self.sequence == None:
                return lang.msgReturnCancel

    def process(self):
        mObj = markov.Transition()
        mObj.loadString(self.sequence, self.orderMax)
        self.post = mObj.repr()  # get repr of trans string

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s %s %s" % (self.cmdStr, self.orderMax, self.sequence)

    def display(self):
        msg = ["AthenaUtility Markov Analysis\n"]
        msg.append(self.post)
        msg.append("\n")
        return "".join(msg)


class AUca(Command):

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.gfxSwitch = 1  # display
        self.cmdStr = "AUca"

    def _auGetCaSpec(self, query):
        while 1:
            spec = dialog.askStr(query, self.termObj)
            if spec == None:
                return None
            try:
                specObj = automata.AutomataSpecification(spec)
            except error.AutomataSpecificationError as e:
                dialog.msgOut("%s%s\n" % (lang.TAB, e), self.termObj)
                continue
            return spec  # return spec, not object

    def gather(self):
        self.specStr = None
        self.rule = None
        self.mutation = None

        if self.args != "":
            args = argTools.ArgOps(self.args)
            self.specStr = args.get(0, "single")
            ok, msg = self._tpConvertPmtrObj(args.get(1))
            if not ok:
                return self._getUsage("rule error: %s" % msg)
            else:
                self.rule = msg  # msg is object
            if args.get(2) == None:  # permit defualt of zero
                ok, self.mutation = self._tpConvertPmtrObj("c,0")
            else:
                ok, msg = self._tpConvertPmtrObj(args.get(2))
                if not ok:
                    return self._getUsage("mutation error: %s" % msg)
                else:
                    self.mutation = msg  # msg is object

        if self.specStr == None:
            msg = "enter a CA specification:"
            self.specStr = self._auGetCaSpec(msg)  # will load in
            if self.specStr == None:
                return lang.msgReturnCancel
            msg = "enter a Generator ParameterObject for rule:"
            self.rule = self._tpGetPmtrObj(msg)
            if self.rule == None:
                return lang.msgReturnCancel
            msg = "enter a Generator ParameterObject for mutation:"
            self.mutation = self._tpGetPmtrObj(msg)
            if self.mutation == None:
                return lang.msgReturnCancel

    def process(self):
        refDict = basePmtr.REFDICT_SIM
        ruleStart = self.rule(0, refDict)
        mutationStart = self.mutation(0, refDict)
        try:
            self.ca = automata.factory(self.specStr, ruleStart, mutationStart)
        except error.AutomataSpecificationError as e:
            return "error in CA specification: %s\n" % e
        for i in range(1, self.ca.spec.get("yTotal")):  # already got zero
            self.ca.gen(1, self.rule(i, refDict), self.mutation(i, refDict))

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            caStr = self.specStr  # has been checked
            mStr = self.mutation.repr("argsOnly").replace(" ", "")
            rStr = self.rule.repr("argsOnly").replace(" ", "")
            return "%s %s %s %s" % (self.cmdStr, caStr, rStr, mStr)

    def display(self):
        return "%s\ncomplete.\n" % self.ca

    def displayGfx(self, fmt, dir=None):
        # supply self as first arg to get instance of command
        prefDict = self.ao.external.getPrefGroup("external")
        obj = graphCellular.CAmapCanvas(
            self.ao,
            self.ca.getCells(
                "table",
                0,
                self.ca.spec.get("s"),
                None,
                self.ca.spec.get("c"),
                self.ca.spec.get("w"),
            ),
            self.ca.dstValues,
            2,
            2,
            fmt,
            None,
            self.ca.repr("line"),
        )
        obj.show(dir, prefDict)

    def displayGfxUtil(self, fmt, fp):
        # this method is for use in auto-documentation generation
        # can supply complete path rather than just a directory
        obj = graphCellular.CAmapCanvas(
            self.ao,
            self.ca.getCells(
                "table",
                0,
                self.ca.spec.get("s"),
                None,
                self.ca.spec.get("c"),
                self.ca.spec.get("w"),
            ),
            self.ca.dstValues,
            2,
            2,
            fmt,
            None,
            self.ca.repr("line"),
        )
        # second arg sets openMedia to false
        obj.write(fp, 0)


class AUbug(Command):
    "utility testing"

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0  # display only
        self.gatherSwitch = 0  # display only
        self.cmdStr = "AUpc"
        a = 4 / 0  # raise an error


class TMsd(Command):
    "Sets the random seed for Texture Modules (only)."

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TMsd"
        self.seed = None
        self.rng = None

    def gather(self):
        args = argTools.ArgOps(self.args)  # no strip
        self.seed = args.get(0, evaluate=True)

    def process(self):
        self.rng = rand.UniformRNG()
        self.rng.seed(self.seed)
        self.log()
        self.display()

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def display(self):
        if self.seed == None:  # error or cancel
            return lang.msgReturnCancel
        else:
            return "TextureModule seed: %s\n" % (self.seed)


class TPsd(Command):
    "Sets the random seed for Parameter Objects and all other RNGs (except Texture Modules)."

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 1  # display only
        self.gatherSwitch = 1  # display only
        self.cmdStr = "TPsd"
        self.new_seed = None
        self.rng = None

    def gather(self):
        args = argTools.ArgOps(self.args)  # no strip
        self.seed = args.get(0, evaluate=True)

    def process(self):
        self.rng = random
        self.rng.seed(self.seed)

    def log(self):  # return an executable command str, subclass
        if self.gatherStatus and self.processStatus:
            return "%s" % (self.cmdStr)

    def display(self):
        if self.seed == None:  # error or cancel
            return lang.msgReturnCancel
        else:
            return "TextureParameterObjects seed: %s\n" % (self.seed)


# -----------------------------------------------------------------||||||||||||--
# command directory commands


class _Menu(Command):
    """base class for menu commands
    note: child classes have underscore appended to name
    this underscore is removed in ao.cmdManifest, and
    re-added in Interpreter._lineCmdArgSplit"""

    def __init__(self, ao, args="", **keywords):
        Command.__init__(self, ao, args, **keywords)
        self.processSwitch = 0
        self.gatherSwitch = 1
        self.subCmd = 1  # if 1, executed within method of interptreter
        self.cmdStr = "menu"
        # modify in subclasses
        self.prefix = None

    def gather(self):
        """optional argument for command of help desired"""
        args = self.args
        self.usrStr = None
        self.name = self.ao.prefixName(self.prefix)

        args = self.args
        if args != "":
            args = argTools.ArgOps(args)  # no strip
            self.prefix = args.get(0)  # can overide prefix w/ command line arg
            self.usrStr = args.get(1)
        elif self.usrStr == None or self.prefix == None:  # no command line args
            dialog.msgOut(
                ("%s (%s) commands:\n" % (self.prefix, self.name)), self.termObj
            )
            lowerPrefix = "%sCmd" % self.prefix.lower()
            cmds, cmdNames = self.ao.prefixCmdGroup(lowerPrefix)
            entryLines = []
            for i in range(0, len(cmdNames)):
                entryLines.append(["", cmds[i], cmdNames[i]])
            headerKey = []  # table setup
            minWidthList = [lang.TABW, lang.NAMEW, 0]
            bufList = [0, 1, 1]
            justList = ["c", "l", "l"]
            table = typeset.formatVariCol(
                headerKey, entryLines, minWidthList, bufList, justList, self.termObj
            )
            dialog.msgOut((table + "\n"), self.termObj)
            self.usrStr = dialog.askStr("command?", self.termObj)

        self.usrCmd = self.ao.prefixMatch(self.prefix, self.usrStr)

    def log(self):
        if self.gatherStatus and self.processStatus:  # if complete
            return "%s" % (self.usrCmd)

    def result(self):
        return {"command": self.usrCmd}  # dict required return


class PI_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "PI"


class TM_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "TM"


class TP_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "TP"


class TI_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "TI"


class TC_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "TC"


class TT_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "TT"


class TE_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "TE"


class EO_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "EO"


class EM_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "EM"


class EL_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "EL"


class AO_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "AO"


class AP_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "AP"


class AH_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "AH"


class AU_(_Menu):
    """menu command"""

    def __init__(self, ao, args="", **keywords):
        _Menu.__init__(self, ao, args, **keywords)
        self.prefix = "AU"


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)

    def testTPv(self):
        from athenaCL.libATH import athenaObj

        ao = athenaObj.AthenaObject()
        from athenaCL.libATH.libPmtr import parameter

        # TODO: this takes a long time to do all;
        # thus, only doing the first 10
        # ultimate: do all
        for tp in parameter.allPmtrObjs[:10]:
            a = TPv(ao, args=tp)
            ok, result = a.do()
            self.assertEqual(ok, True)

    def testTMsd(self):
        from athenaCL.libATH import athenaObj

        interpreter = athenaObj.Interpreter("terminal")
        interpreter.cmd("TMsd 200")
        first = rand.UniformRNG().random()
        interpreter.cmd("TMsd 200")
        second = rand.UniformRNG().random()
        self.assertEqual(first, second)

    def testTPsd(self):
        from athenaCL.libATH import athenaObj

        interpreter = athenaObj.Interpreter("terminal")
        interpreter.cmd("TPsd 300")
        first = random.random()
        interpreter.cmd("TPsd 300")
        second = random.random()
        self.assertEqual(first, second)


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    from athenaCL.test import baseTest

    baseTest.main(Test)
