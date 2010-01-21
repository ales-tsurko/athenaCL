#-----------------------------------------------------------------||||||||||||--
# Name:          athenaObj.py
# Purpose:       defines the following objects:
#                    External: find all necessary files, prefs, xml data
#                    AthenaObject: data container for athena object
#                    Terminal: object interface for terminal display
#                    Interpreter: object for parsing commands, logging, help
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import sys, os, time, random, traceback, httplib, urllib

athVersion  = '2.0.0-beta'
athBuild        = '2009.08.15'
athRevision = 1 # for debian based versioning
athDate     = '15 August 2009' # human readable version
__version__ = athVersion
__license__ = "GPL"

# athenaObj.py needs correct dir information for writing
# a file (prefs) and loading demos, and opening .xml and and other resources 
# External is sometimes called by itself, needs to find correct paths
# this checks for correct path access, attempts to mangle sys.path to fix
#-----------------------------------------------------------------||||||||||||--
try: import libATH #assume we are in package dir
except ImportError:
    try: from athenaCL import libATH
    except ImportError: print 'athenaCL package cannot be found.'; sys.exit()
libPath = libATH.__path__[0] # list, get first item
if os.path.isabs(libPath) != 1: #relative path, add cwd
    libPath = os.path.abspath(libPath)
_PKGDIR = os.path.dirname(libPath)
_OUTDIR = os.path.dirname(_PKGDIR)
if _OUTDIR not in sys.path: sys.path.append(_OUTDIR)




#-----------------------------------------------------------------||||||||||||--
from athenaCL.libATH import argTools
from athenaCL.libATH import command
from athenaCL.libATH import dialog
from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import help
from athenaCL.libATH import ioTools # needed for bkwdCompat object
from athenaCL.libATH import prefTools
from athenaCL.libATH import rhythm # needed for timing
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import SC
from athenaCL.libATH import setMeasure
from athenaCL.libATH import MC
from athenaCL.libATH.libOrc import orc
from athenaCL.libATH.libTM import texture # needed for test script
from athenaCL.libATH import clone # needed for proc_AUtest
# objects not stored in ao, but nameing data needed
from athenaCL.libATH import eventList

_MOD = 'athenaObj.py'




#-----------------------------------------------------------------||||||||||||--
class External:
    """used to remaintain remote files used by the AthenaObject
    handles preferences (stored in xml) and erro log files
    also reloads textures, gets path preferences, orchestra files
    """
    def __init__(self, termObj=None):
        """termObj used to provide session type information"""
        if termObj != None:
            self.termObj = termObj
            self.sessionType = termObj.sessionType
        else:
            self.termObj = None
            self.sessionType = 'terminal' # standard default

    def updateAll(self, verbose=0):
        """does all init updates, called whenever an ao is created
        """
        self._updateDirs(verbose)
        self._updateLogs()
        self.updatePrefs()

    #-----------------------------------------------------------------------||--
    def _updateDirs(self, verbose=0):
        """called to get athenaCL directories and load modules
        checks for libATH, libATH/libTM, libATH/libAS
        verbose does not currently do anything
        """
        self.topLevelDir = _PKGDIR # global from mod loading, athenaCL package dir
        topLevelContent = os.listdir(self.topLevelDir) # check 'libATH' directory   
        if 'libATH' in topLevelContent:
             self.libATHpath = os.path.join(self.topLevelDir,'libATH')
             self.libATHpath = drawer.pathScrub(self.libATHpath)
        else:
            dialog.msgOut(lang.msgMissingLibATH, self.termObj)
            temp = dialog.askStr(lang.msgReturnToExit, self.termObj)
            sys.exit()
        try: # check for XML abilities:
            import xml.dom.minidom
            doc = xml.dom.minidom.parseString("<doc>test.</doc>")        
        except: # xml.sax._exceptions.SAXReaderNotAvailable
            dialog.msgOut(lang.msgMissingXML, self.termObj)
            temp = dialog.askStr(lang.msgReturnToExit, self.termObj)
            sys.exit()
        # create util objects
        self.scObj = SC.SetClass() 
        self.mcObj = MC.MapClass()

        # check for texture module directory, demo dirs
        libATHcontents = os.listdir(self.libATHpath)
        if 'libTM' in libATHcontents:
            self.libTMpath = os.path.join(self.libATHpath, 'libTM')
            self.libTMpath = drawer.pathScrub(self.libTMpath)
        else:
            dialog.msgOut(lang.msgMissingLibTM, self.termObj)
            temp = dialog.askStr(lang.msgReturnToExit, self.termObj)
            sys.exit()
        # check for athena scripts folder
        if 'libAS' in libATHcontents:
            self.libASpath = os.path.join(self.libATHpath, 'libAS')
            self.libASpath = drawer.pathScrub(self.libASpath)
        else:
            dialog.msgOut(lang.msgMissingLibAS, self.termObj)
            temp = dialog.askStr(lang.msgReturnToExit, self.termObj)
            sys.exit()

        # check for demo files
        self.demoDirList = []
        if 'demo' in topLevelContent:
            demoPath = os.path.join(self.topLevelDir, 'demo')
            self.demoDirList.append(drawer.pathScrub(demoPath))
            # cvs versions will have a test dir in demo; check for this and add
            if 'test' in os.listdir(demoPath):
                demoTestPath = os.path.join(demoPath, 'test')
                self.demoDirList.append(drawer.pathScrub(demoTestPath))

        if 'CVS' in topLevelContent: # check if there is a cvs dir
            self.cvsDirPresent = 1
        else:
            self.cvsDirPresent = 0

        if 'docs' in topLevelContent: # get docs path
            self.docsPath = os.path.join(self.topLevelDir, 'docs')
            self.docsPath = drawer.pathScrub(self.docsPath)
        else:
            self.docsPath = None

        # assign a dir in which to write pref/log files
        if os.name == 'mac': # macos 9
            self.prefsDir = self.libATHpath
        elif os.name == 'posix':
            self.prefsDir = drawer.getud() # get active users dir
        else: # win or other
            self.prefsDir = drawer.getud()
            if self.prefsDir == None: # cant use getcwd
                self.prefsDir = self.libATHpath # used before and two versions 1.4.2
            
    #-----------------------------------------------------------------------||--
    def getCvsStat(self):
        """return string if this is likely a cvs co"""
        if self.cvsDirPresent: return 'cvs'
        else: return 'package'

    def _updateLogs(self):
        """update path for error log files"""
        if os.name == 'mac':     
            logFileName = 'athenacl-log.txt'
        elif os.name == 'posix':
            logFileName = '.athenacl-log' # make hidden file
        else: # win or other
            logFileName = '.athenacl-log.txt'
        self.logPath = os.path.join(self.prefsDir, logFileName)

    def logWrite(self, dataLines):
        """for adding an error to= the error lig"""
        if os.path.exists(self.logPath): # append lines
            f = open(self.logPath, 'r')
            logLines = f.readlines()
            f.close()
        else:
            logLines = []
        for line in dataLines:
            logLines.append(line)
        # add a separator b/n log entries
        logLines.append('\n')
        f = open(self.logPath, 'w')
        f.writelines(logLines)
        f.close()

    def _logParse(self):
        """open the log file and parse it into useful data"""
        charSep = '-'

        f = open(self.logPath, 'r')
        logLines = f.readlines()
        f.close()
        bundle = {}
        i = -1 # first will be zero
        for line in logLines: # in order, ERROR always comes first
            if line.strip() == '':
                continue
            if line.startswith('ERROR'):
                i = i + 1 # increment
                bundle[i] = [] # create new list
            bundle[i].append(line)
        # convert to value pairs
        param = {}
        for group in bundle.keys(): # order here does not matter
            i = 0 # first will be zero
            for field in bundle[group]: # order here matters
                key = '%s%s%s' % (group, charSep, i)
                param[key] = field
                i = i + 1
        return param

    def logCheck(self):
        """test to see if a log exists; called when quitting to see 
        if a log send should be done"""
        if os.path.exists(self.logPath): return 1 # no log, do nothing
        else: return 0

    def _logDelete(self):
        """delete the error log, assuming that it is empty"""
        os.remove(self.logPath)

    def logSend(self):
        """attempt to submit a log file"""
        paramRaw = self._logParse()
        paramRaw['stateNext'] = '8' # state 8 is bug processing
        params = urllib.urlencode(paramRaw)
        headers = {"Content-type": "application/x-www-form-urlencoded", 
                      "Accept": "text/plain"}
        try:
            conn = httplib.HTTPConnection(lang.msgCgiDomain)
            conn.request("POST", lang.msgCgiURL, params, headers)
            connect = 1
        except: # no connection active
            connect = 0
        if connect:
            try:
                response = conn.getresponse()
            except: # some other failure is possible here
                print 'unknown connection error.'
                return None
            if response.status == 200: # good
                data = response.read()
                dataLines = data.split('\n')
                print dataLines[0]
                self._logDelete() # delete old log
            else:
                print 'http error:', response.status

            conn.close() 
            return 1
        else:
            return None # nothing happened

    def onlineVersionFetch(self):
        """if online, check current version
        returns None if not available"""
        try: # read number of chars lines 1.1.1.1000.10.10
            webpage = urllib.urlopen(drawer.urlPrep(lang.msgVersionURL)).read(24)
        except IOError, e: # cant get online
            webpage = None
        except: # all others
            webpage = None        
        if webpage != None:
            versionStr = webpage.strip()
            return argTools.Version(versionStr) # return object
        else:
            return None

    #-----------------------------------------------------------------------||--
    def updatePrefs(self, forcePath=None):
        """check for prefs, update and add if missing
        """
        # watch for sesion type here; dont write files if cgi type
        if os.name == 'mac':     
            prefsFileName = 'athenaclrc.xml'
        elif os.name == 'posix':
            prefsFileName = '.athenaclrc' # make hidden file
        else: # win or other
            prefsFileName = '.athenaclrc.xml'

        if forcePath != None:
            self.prefsPath = forcePath # assign
            self.prefDict = prefTools.getXmlPrefDict(self.prefsPath)
            self.prefDict = prefTools.updatePrefDict(self.prefDict, os.name)
            prefTools.writePrefDict(self.prefsPath, self.prefDict)
        elif self.sessionType != 'cgi': # cgi cant use any prefs
            prefDirContent = os.listdir(self.prefsDir)
            self.prefsPath = os.path.join(self.prefsDir, prefsFileName)
            createNewPrefs = 0
            if prefsFileName in prefDirContent:
                self.prefDict = prefTools.getXmlPrefDict(self.prefsPath)
                self.prefDict = prefTools.updatePrefDict(self.prefDict, os.name)
                prefTools.writePrefDict(self.prefsPath, self.prefDict)
            else: # new prefs on first start, or after deleting
                createNewPrefs = 1
            if createNewPrefs:
                self.prefDict = prefTools.getDefaultDict(os.name)
                prefTools.writePrefDict(self.prefsPath, self.prefDict)

        elif self.sessionType == 'cgi': # if cgi session, only use pref dict
            self.prefDict = prefTools.getDefaultDict(os.name)

    def writePref(self, category, key, value):
        """writes new value or pref file"""
        from athenaCL.libATH import prefTools
        self.prefDict[category][key] = value
        if self.sessionType != 'cgi': # dont write if cgi
            prefTools.writePrefDict(self.prefsPath, self.prefDict)

    def getPref(self, category, key, evaluate=0):
        """returns value of a pref
        some prefs are lists or numbers and need to be evaluated"""
        strPref = self.prefDict[category][key]
        if not evaluate:
            return strPref
        else: # this may raise an exception
            evalPref = eval(self.prefDict[category][key])
            if drawer.isList(evalPref): # make sure it is a list, not tuple
                evalPref = list(evalPref)
            return evalPref
            
    def getPrefGroup(self, category):
        """get an entire pref group, and load into a dictionary
        useful passing app preferences from external to osTools"""
        d = {}
        for key in self.prefDict[category]:
            d[key] = self.prefDict[category][key]
        return d
        
    #-----------------------------------------------------------------------||--
    def getFilePathSample(self):
        """returns a list of file paths for samples"""
        ssdrPath = os.path.join(self.libATHpath, 'ssdir')
        ssdrPath = drawer.pathScrub(ssdrPath)
        ssdrPathUsr = self.getPref('athena', 'ssdir')
        pathList = [ssdrPath, ssdrPathUsr]
        return pathList

    def getFilePathAnalysis(self):
        """returns a list of file paths for analysis"""
        sadrPath = os.path.join(self.libATHpath, 'sadir')
        sadrPath = drawer.pathScrub(sadrPath)
        sadrPathUsr = self.getPref('athena', 'sadir')
        pathList = [sadrPath, sadrPathUsr]
        return pathList

    def getVisualMethod(self, status='normal'):
        """checks to see if vis methods have been updated
        if not avail, updates
        this is a bit of a time suck and should be done once
        per session
        status == 'init' allows the attibute self.visualMethod
        to be initialized to None, updates on next call
        visual methodis a list containing all avalable methods
        """
        if status == 'init':
            self.visualMethod = None # set to none, but dont update until called
        else: # checks guis: a speed clog on startup
            if self.visualMethod == None: # done only if set to none, once per sess
                self.visualMethod = drawer.imageFormats()
            return self.visualMethod




#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--

class AthenaObject:
    """methods for internal processsing of done with command objecst from 
    command.py
    includes internal functions for processing objects
    athenaCmd.py wraps and exposes methods of this class
    """

    def __init__(self, termObj=None, debug=0):
        """creates all attributes of the athenaObject
        update object handles finding all modules and creating util objects
        command.py operates upon these attributes and sub-objects
        also handles reference of commands, getting help from commands, display
        
        information/objects that need to be accessed both in Interpreter (holds 
        one permanent ao) and many command objects (one ao passed to them)
        """
        self.athVersion = athVersion
        self.athBuild = athBuild
        self.versionObj = argTools.Version('%s.%s' % (self.athVersion, 
                                                        self.athBuild))
        self.athDate = athDate

        # defaut terminal handler, from Interpreter
        self.termObj = self._configTerminal(termObj) 
        self.debug = debug # debug option

        # possible session types are 'terminal', 'idle', 'cgi';
        # these methods initializes external modules and resources
        self.external = External(self.termObj) 
        self.external.updateAll('on') # msgs on
        #self.external.reloadTextures()
        self.external.getVisualMethod('init') # prep, dont resolve
        # utility objects
        self.help = help.HelpDoc(self.termObj) # pass ref termObj
        self.backward = ioTools.BackwardsCompat(self.debug)

        # data and objects saved with AO
        # ATHENA DATA
        self.author = '' # stored for a loaded athenaObj
        self.tniMode = 0    #true == TnI, false == Tn
        # PATH DATA
        self.activeSetMeasure = 'ASIM' # default
        self.pathLib = {}
        self.activePath = ''
        # TEXTURE DATA
        self.activeTextureModule = 'LineGroove' # name of class
        self.textureLib = {}
        self.activeTexture = '' #name of
        # CLONE DATA
        self.cloneLib = clone.CloneManager() # added post 1.3
        self.midiTempo = 120 # default value, changed with TEmidi, added 1.1
        self.nchnls = 2  # default, saved w/ ao

        # this may be init from a pref; but loaded and stored in ao
        self.orcObj = None # initialized from setEventMode
        self.activeEventMode = None
        # cannot store an em object, contains ao, but must instant orc
        # sets self.activeEventMode and self.orcObj
        self.setEventMode(self.external.getPref('athena', 'eventMode'),
                                'csoundNative')
        # local information either (1) not saved in AO (2) temporary data or
        # (3) derived from file based preferences
        # these might be better put in teh aoInfo dictionary?
        self.fpSSDR = self.external.getFilePathSample()   # list of paths
        self.fpSADR = self.external.getFilePathAnalysis() # list of paths
        self.fpLastDir = self.external.getPref('athena', 'fpLastDir')
        self.fpLastDirSco = self.external.getPref('athena', 'fpLastDirSco')
        # determines how texture/clone editing happens

        # temporary session data, scoFP and others
        # stores outputs completed after ELn; can be used to determine what
        # files were actually made
        self.aoInfo = {} 
        self.aoInfo['refreshMode'] = self.external.getPref('athena',
                                                                  'refreshMode', 1)
        self.aoInfo['cursorToolOption'] = self.external.getPref('athena',
                                                     'cursorToolOption')
        self.aoInfo['version'] = self.athVersion
        self.aoInfo['outComplete'] = [] # will be filled after creating files
        self.aoInfo['history'] = {} # store command history # mod in Interpreter

        # static data and strings shared by Interpreter and Command objects
        self.promptSym   = '::' # symbol used for prompt
        # this is directory of main commands presented to user
        # any other commands are considered hidden
        self.cmdDict = {
#       'scCmd':('SetClass', 'SCv(view)', 'SCcm(comp)', 
#                   'SCf(find)', 'SCs(search)', 'SCmode(mode)', 'SCh(hear)',),
#       'smCmd':('SetMeasure',    
#                   'SMls(list)', 'SMo(select)',),
#       'mcCmd':('MapClass', 'MCv(view)', 'MCcm(comp)', 
#                   'MCopt(optimum)', 'MCgrid(grid)', 'MCnet(network)'),
      'piCmd':('PathInstance', 'PIn(new)',      'PIcp(copy)', 
                  'PIrm(remove)','PIo(select)', 'PIv(view)', 
                  'PIe(edit)', 'PIdf(duration)', 'PIls(list)', 'PIh(hear)', 
                  'PIret(retro)', 
                  'PIrot(rot)', 'PIslc(slice)'),
# 'PIopt(optimum)'
#       'psCmd':('PathSet','PScma(compA)','PScmb(compB)'),
#       'pvCmd':('PathVoice', 'PVn(new)', 'PVcp(copy)', 'PVrm(remove)',
#                   'PVo(select)', 'PVv(view)',    'PVe(edit)',     
#                   'PVls(list)', 
#                   'PVan(analysis)', 'PVcm(compare)', 'PVauto(auto)'),
      'tmCmd':('TextureModule', 'TMo(select)', 'TMv(view)',                                  
                  'TMls(list)'),
      'tpCmd':('TextureParameter', 'TPls(list)', 'TPv(select)', 'TPmap(map)', 
                  'TPeg(export)'),
      'tiCmd':('TextureInstance', 'TIn(new)', 'TIcp(copy)', 
                  'TIrm(remove)', 'TIo(select)', 'TIv(view)', 
                  'TIe(edit)', 'TIls(list)', 'TImode(mode)', 
                  'TImute(mute)', 'TIdoc(doc)', 'TImap(map)',
                  'TImidi(midi)'), 
      'tcCmd':('TextureClone', 'TCn(new)', 'TCcp(copy)', 'TCrm(remove)', 
                  'TCo(select)', 'TCv(view)','TCe(edit)',
                  'TCls(list)', 'TCmute(mute)', 'TCmap(map)'), 
      'ttCmd':('TextureTemperament', 'TTls(list)',  'TTo(select)'),
      'teCmd':('TextureEnsemble', 'TEv(view)',  'TEe(edit)', 
                  'TEmap(map)', 'TEmidi(midi)',),
      'eoCmd':('EventOutput', 'EOls(list)', 'EOo(select)','EOrm(remove)',),
      'emCmd':('EventMode', 'EMls(list)', 'EMo(select)', 'EMv(view)',
                  'EMi(inst)',),
      'elCmd':('EventList', 'ELn(new)', 'ELw(save)', 
                  'ELv(view)', 'ELh(hear)', 'ELr(render)',),
      'cpCmd':('CsoundPreferences', 
                  'CPff(format)', 'CPch(channel)', 'CPauto(auto)'),
      'aoCmd':('AthenaObject', 'AOw(save)', 'AOl(load)', 'AOmg(merge)',
                  'AOrm(remove)',),
      'asCmd':('AthenaScript', 'ASexe(execute)',), # hidden!
      'ahCmd':('AthenaHistory', 'AHls(list)', 'AHexe(execute)'),
      'auCmd':('AthenaUtility', 'AUsys(system)', 'AUdoc(docs)', 'AUup(update)',  
                  'AUbeat(beat)', 'AUpc(pitch)', 'AUmg(markov)', 'AUma(markov)', 
                  'AUca(automata)'),
      'apCmd':('AthenaPreferences', 'APcurs(cursor)', 'APdlg(dialogs)',
                  'APgfx(graphics)', 'APdir(directory)', 'APea(external)', 
                  'APr(refresh)', 'APwid(width)', 'APcc(custom)' ),
        }

        self.cmdOrder = [None, 'piCmd', #'psCmd', 'pvCmd', 
                      None, 'tmCmd', 'tpCmd', 'tiCmd', 'tcCmd', 
                              'ttCmd', 'teCmd', 
                      None, 'eoCmd', 'emCmd', 'elCmd', 'cpCmd', 
                      None, 'apCmd', 'ahCmd', 'auCmd', 'aoCmd']
        # two-letter prefix for all athenaCL commands
        self.cmdPrefixes = [] # store w/ caps
        for key in self.cmdDict: 
            self.cmdPrefixes.append(key[:2].upper()) # first two chars
        # this is only used in the cmdManifest method below
        self._cmdSpecial = ['w', 'c', 'r', 'cmd', 'pypath', 
                                 'py', 'quit', 'q', 'help', 'shell']
        # store a list of all commands
        self.cmdRef = self.cmdManifest()
        self.cmdRef.sort()

    def prefixCmdGroup(self, prefix):
        """for a given prefix will return a list of 
        cmds and a list of their names
        only returns heirarchical commands, never special commands
        """
        if prefix in self.cmdDict.keys():
            cmdNameList = self.cmdDict[prefix]
            cmdList = []
            nameList = []
            for name in cmdNameList:
                ## this ignores things that are not cmds, like heading names
                if name.find('(') < 0: continue
                name = name.replace('(', ' ')
                name = name.replace(')', ' ')
                cmdStr, nameStr = name.split() # always into two things
                cmdList.append(cmdStr)
                nameList.append(nameStr)
            return cmdList, nameList
        else: return None

    def prefixName(self, prefix):
        return self.cmdDict[prefix.lower()+'Cmd'][0] # 0 gets title


    def _configTerminal(self, termObj):
        """Provide a default Termainl if not provided
        """
        if termObj == None:
            return Terminal('terminal', None)
        else:
            return termObj


    #-----------------------------------------------------------------------||--
    # managing and displaying command names

    def cmdDisplay(self):
        """get heirarchical display, scaled to screen widthw
        used for cmd display"""
        w = self.termObj.w
        msg = []
        msg.append('athenaCL Commands:\n')
        for cmdName in self.cmdOrder:
            if cmdName == None: # none is a divider
                msg.append(lang.DIVIDER * w)
            else:
                msg.append(typeset.formatEqCol('', self.cmdDict[cmdName], 18, 
                                                        w, 'outLineMode'))
        return ''.join(msg)

    def cmdCorrect(self, line):
        """acts as an athenaCL cmd parser:
        capitalizes and corrects user cmd strings called w/n cmdExecute
        does not deal with special commands like q, quit, cmd, and others"""
        if line == None:
            return None
        line = line.strip()
        if len(line) <= 1: return line
        # if first two letters lower case, make upper
        prefix  = line[:2].upper()
        postfix = line[2:]
        if prefix in self.cmdPrefixes: #check for lower case
            newPrefix = prefix
            line = newPrefix + postfix
        else: # line stays the same
            newPrefix = prefix 
        return line

    def cmdManifest(self):
        "get all commands from command.py;"
        cmdList = dir(command) # get listing from module
        cmdFilter = []
        for entry in cmdList:
            if (entry[0:2] in self.cmdPrefixes and 
                entry[0].isupper() and 
                entry[1].isupper() and 
                len(entry) > 2 and 
                entry.find('funct') < 0 and
                entry.find('class') < 0): # remove modules imported 
                if entry[-1] == '_': # some commands have tag at end
                    cmdFilter.append(entry[:-1])
                else:
                    cmdFilter.append(entry)
            elif entry in self._cmdSpecial: # non-standard command names
                cmdFilter.append(entry)
        cmdFilter.sort()
        return cmdFilter

    def cmdDocManifest(self):
        """gets all commands by looking in class attributes
        this listing includes hidden commands and commands not
        getAllCmds, formerly 
        """
        cmdsDoc = []
        cmdsUndoc = []
        allHelpTopics = self.help.listCmdDoc()        
        for cmd in self.cmdRef: # check against all commands in command.py          
            if cmd in allHelpTopics: # command has documentation
                cmdsDoc.append(cmd)
                allHelpTopics.remove(cmd) # remove from all help topics
            else: # command without any help
                cmdsUndoc.append(cmd)
        # after checking all, remaining topics are general help topics 
        # these are not really used here
        helpTopics = allHelpTopics # all that remain
        return cmdsDoc, cmdsUndoc, helpTopics

    def prefixMatch(self, prefix, usrStr):
        """will attempt to match a user string to a command, knowing the prefix
        that command will be found in. if an SC command, user can enter both v or         
        SCv. returns the complete command string, or unmodified if no mathc"""
        if usrStr == None:
            return None
        prefix = prefix.upper()
        usrStr = self.cmdCorrect(usrStr)
        result = self.prefixCmdGroup(prefix.lower() + 'Cmd')
        if result == None: # bad prefix 
            return usrStr
        else:
            cmds, nameList = result
 
        if usrStr in cmds: # complete match
            pass # its good
        elif prefix + usrStr.lower() in cmds:
            usrStr = prefix + usrStr.lower()
        elif len(usrStr) >= 2:
            i = 0
            for cmdShortName in nameList:             
                if usrStr.lower() == cmdShortName.lower():
                    usrStr = cmds[i]
                i = i + 1
        return usrStr

    #-----------------------------------------------------------------------||--
    # tools for version checking

    def compareVersion(self, versionOther=None):
        """compare version to current version
        version is a string"""
        if versionOther == None:# assume we want to compare to online 
            versionOther = self.external.onlineVersionFetch()
            if versionOther == None: return None, None # if not online

        if self.versionObj == versionOther: # the same version
            status = 'current'
        elif versionOther > self.versionObj: # other is more recent
            if versionOther.point > self.versionObj.point:
                status = 'major' # major update is point
            else: # just the dates are different
                status = 'minor'
        else: # this version is more up to date than other
            status = 'current'

        if status == 'minor':
            versionStr = versionOther.repr('dot', 1)
        elif status == 'major':
            versionStr = versionOther.repr('dot', 0) # leave out date info
        elif status == 'current':
            versionStr = self.versionObj.repr('dot', 0)
        return status, versionStr

    def timeSinceLastVersionCheck(self):
        """return seconds since last started"""
        tLast = self.external.getPref('athena', 'tLastVersionCheck')
        try:
            tLast = float(tLast)
        except (ValueError, TypeError, SyntaxError):
            tLast = 0 # set at zero
        tNow = time.time()
        dif = round(abs(tNow - tLast), 1)
        #print 'time since last version check %s\n' % dif
        return dif

    #-----------------------------------------------------------------------||--
    # these are used in error messages, AUsys

    def osStr(self):
        return '%s.%s' % (os.name, sys.platform)

    def pyStr(self):
        major, minor, micro, level, serial = sys.version_info
        return '%i.%i.%i.%s' % (major, minor, micro, level)

    def aoStr(self, fmt='dot', date=1):
        # formats can be dot or human
        return self.versionObj.repr(fmt, 1)

    def infoStr(self):
        """used in sending error message w/ data stored in aoInfo"""
        headStr = '%s-%s-%s-%s' % (self.osStr(), self.pyStr(), 
                         self.aoStr(), self.external.getCvsStat())
        return headStr

    #-----------------------------------------------------------------------||--
    # methods to maintain internal utility objects

    def setEventMode(self, usrStr, default=None):
        #print _MOD, usrStr
        usrStr = eventList.eventModeParser(usrStr)
        # in the case that a bad eventMode was stored
        if usrStr == None and default != None:
            usrStr = default
        assert usrStr != None
        self.activeEventMode = usrStr
        self.orcObj = orc.factory(eventList.selectEventModeOrc(
                          self.activeEventMode))

    def setPreference(self, filePath):
        """set the preference file to an arbitraray path
        this is used for automated image generation in documentation"""
        self.external.updatePrefs(filePath) # msgs on





#-----------------------------------------------------------------||||||||||||--
# this term handling thanks in part to avkutil.py
class Terminal:
    """terminal management.
    represents basic screen presentation issues, even w/o a tty
    size - return height, width of the terminal
    self.termLive determines if the term is in a unix that can get size
    if not, returs default width
    """
    def __init__(self, sessionType='terminal', parentGUI=None):
        """possible session types are 'terminal', 'idle', 'cgi' """
        self.sessionType = sessionType
        self.parentGUI = parentGUI # keep for gui management
        # try to import readline
        try: import readline
        except ImportError: pass # not available on every platform       
        # determine if interface is interactive or nots
        if sessionType in ['terminal', 'idle']:
            self.interact = 1
        else: # 'cgi' is not interactive
            self.interact = 0
        # determine if term is live or dead       
        if sessionType == 'terminal':
            try:
                global termios
                import termios
                self.termLive = 1
            except ImportError:
                self.termLive = 0
        elif sessionType in ['cgi', 'idle']:
            self.termLive = 0
        # defaults spacings
        self.defaultW = 72 # for plats that dont have termio
        self.defaultH = 24
        self.cursesTest = 0 # bool if curses test has been completed
        # do session type adjustments on default sizes
        if sessionType == 'cgi':
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
        self.cursesTest = 1 # only run this method once
        if self.termLive:
            try: # as list ditch test, load curses to get size
                import curses
                curses.initscr()
                self.cursesH, self.cursesW = curses.LINES, curses.COLS
                curses.endwin()
                del curses
            except ImportError:
                self.cursesW = None # try to get size at init
                self.cursesH = None # from curses if around

    def size(self):
        """Return terminal size as tuple (height, width).
        this is called once with each command, updated size 
        """
        if self.termLive:
            h, w = self.defaultH, self.defaultW
            try:
                import struct, fcntl
                h, w = struct.unpack("hhhh", fcntl.ioctl(0, 
                         termios.TIOCGWINSZ, "\000"*8))[0:2]
            except: # get size from curses if available; last ditch
                if not self.cursesTest:
                    self._sizeCurses() # run curses method only if not yet run once
                if self.cursesW != None and self.cursesH != None:
                    h, w = self.cursesH, self.cursesW
        else: # if no term active, get default
            h, w = self.defaultH, self.defaultW
        return h, w

    def __getattr__(self, name):
        """provode interface as attributes"""
        h, w = self.size()
        if name == 'h':
            return h
        elif name == 'w':
            return w
        else:
            raise AttributeError

    def setWidth(self, width):
        self.defaultW = width
        self.termLive = 0 # disables using termios
        
    def setHight(self, height):
        self.defaultH = height


#-----------------------------------------------------------------||||||||||||--
# this Interpreter is based on Python cmd.py

class Interpreter:
    """command line envonment to interact with athenaObj.py
    useful for developing parameter objects and textures
    
    verbose: determine amount of messages given back and forth
        0: quite output: nothign returned
        1: return msg, no warning
        2: return msg, give warnings, errors, 
        3: debug mode: very verbose 

    debug option passed to all commands; used to remove error checking
        changes some processing in order to provide more accurate errors.
    """

    def __init__(self, sessionType='terminal', threadAble=1, 
        verbose=0, debug=0):

        # instance of athenaObj class, where all athena processing takes place
        self.sessionType = sessionType # can be: terminal, idle, Tkinter, cgi
        self.verbose = verbose # determine output level
        self.debug = debug # turn on debugging mode
        # sets echoing of command lines; prints commands
        # this is used when scripting and you want to see what commands are fired
        self.echo = 0 
        # create objects
        self.parentGUI = None # used to be used; no longer, but kept incase
        self.termObj = Terminal(self.sessionType, self.parentGUI)
        self.ao = AthenaObject(self.termObj, self.debug)
        self.athVersion = self.ao.athVersion
        self.athBuild = self.ao.athBuild
        # special handling for threads
        self.threadAble, threadStr = self._testThreads(threadAble)
        self.pollDur = .25 # time between polls in seconds
        self.versionCheckWait = rhythm.TimeValue.sPerDay * 28 # every 28 days
        #self.cmdqueue    = [] # not used

        # these are just used for fun
        self._emptyCount = 0 # count empty lines returned
        self._blankCount = 0 # count blank lines returned
        
        # update vars passed to command obj; sets command environ
        self._updateCmdEnviron()  # creates self.cmdEnviron
        self.cursorToolConvert = self._getCursorToolConvert() # done once at init
        self._updatePrompt('msg') # creates self.prompt
        athTitle = '\n' + 'athenaCL %s (on %s via %s %s)\n' % (
                          self.athVersion, sys.platform, 
                          self.sessionType, threadStr)
        # two returns required after changes to line wrapping function
        self.intro = athTitle + lang.msgAthIntro + '\n\n'


    #-----------------------------------------------------------------------||--
    def out(self, msg):
        """main output filter for all text displays
        all text output, when using the intereter, passes through here
        if verbosity set to 0, not output is given at all
        """
        if self.verbose >= 1:
            dialog.msgOut(msg, self.termObj)

    #-----------------------------------------------------------------------||--

    def _updateCmdEnviron(self):
        "passed to command objects for interperter prefs"
        self.cmdEnviron = {}
        self.cmdEnviron['threadAble'] = self.threadAble
        self.cmdEnviron['pollDur'] = self.pollDur
        self.cmdEnviron['verbose'] = self.verbose
        self.cmdEnviron['debug'] = self.debug

    def _getFunc(self, cmd):
        """gets a reference to command object; this may get modules that
        are imported into the command module; this is a problem"""
        # some cmds strings cannot be properly filtered unles directly avoided
        # lang pbject will print an error if an attr is not found
        if cmd in ['lang']:
            return None
        try:
            func = getattr(command, cmd) # from command module, get class
        except AttributeError:
            func = None
        if drawer.isMod(func): # if a module, not a command object, do not run
            func = None
        # all cmd sub-class must have these methods
        elif not hasattr(func, 'do') and not hasattr(func, 'undo'): 
            func = None
        return func

    def _proc(self, cmdObj, data):
        """gets a processor, only used for sub commands"""
        func = getattr(self, 'proc_' + cmdObj.cmdStr)   
        return func(data)         

    def _lineCmdArgSplit(self, line):
        """take a user input line and parse into cmd and arg
        does special character translations
        handles specian commands like SC by adding underscore"""
        line = line.strip()
        if not line: return None
        elif line[0] == '?':
            line = 'help ' + line[1:]
        elif line[0] == '!':
            line = 'shell ' + line[1:]
        i = 0
        # extract command from args, assuming that all cmds use identchars
        while i < len(line) and line[i] in lang.IDENTCHARS:
            i = i + 1
        cmd, arg = line[:i], line[i:].strip()
        if cmd in self.ao.cmdPrefixes: # special sc commands
            cmd = cmd + '_'
        return cmd, arg


    #-----------------------------------------------------------------------||--
    def _cmd(self, line):
        """does actual processing of each command, adding do prefix
        separates args from command
        all commands pass through this method, inner most try/except loop
        sub commands provide data dictionaries that are then processed in
        the interepreter (not in the command object itself)
        """
        self._updateCmdEnviron() # update vars passed to command obj
        splitLine = self._lineCmdArgSplit(line)
        if splitLine == None:
            self._emptyline()
            return None
        cmd, arg = splitLine
        func = self._getFunc(cmd)
        if func == None: return self._default(line)
        self._clearCount() # clears cmd blank/bad counting
        try: # execute function, manage threads
            cmdObj = func(self.ao, self.cmdEnviron, arg)
            ok, result = cmdObj.do() # returns a dict if a subCmd, otherwise str
            if result == None: # no msg returned; nothing to report
                stop = None
            elif not drawer.isDict(result): # if not a dictionary
                self.out(result) # disply str output
                stop = None # only needed
            else: # it is a subCmd, must be a dictionary result
                stop = self._proc(cmdObj, result) # do processing on result
            if cmdObj.cmdStr != 'quit': # no history for quit
                self._historyAdd(cmdObj.log()) #log may return none if incomplete
        except: # print error message for all exceptions
            tbObj = sys.exc_info() # get traceback object
            stop = None # must be assigned on error
            self._errorReport(cmd, arg, tbObj) # writes log file
            self.out(lang.msgAthObjError)
        return stop

    def cmd(self, line, arg=None):
        """give cmdline, or cmd + arg; cmdline will be split if arg == None
        good for calling a single command from cgi, or external interpreter
        return output as string, not printed
        does not log errors, does not keep a history
        _not_ used in normal interactive loop
        returns a status flag, and msg string
        """
        self._updateCmdEnviron() # update vars passed to command obj
        if arg == None: # no args, assume cmd needs to be split
            splitLine = self._lineCmdArgSplit(line)
            if splitLine == None: return 0, "no command given"
            cmd, arg = splitLine
        else: # args are given, so line is command name
            cmd = line
        # cmdCorrect called here; this is done in cmdExecute and not in _cmd
        # as this is a public method, however, this may be necessary here
        cmd = self.ao.cmdCorrect(cmd)
        func = self._getFunc(cmd)
        if func == None: return 0, "no command given"

        try: # execute function, manage threads
            cmdObj = func(self.ao, self.cmdEnviron, arg)
            ok, result = cmdObj.do() # no out on resutl here
        except: # print error message
            # stop = None # must be assigned on error; no longer in use
            #self.out(self._errorReport(cmd))
            traceback.print_exc() # print teaceback, dont log error
            result = 'error occured'
            ok = 0
        return ok, result



    #-----------------------------------------------------------------------||--
    def _precmd(self, line):
        return line

    def _postcmd(self, stop, line):
        """done after a command is executed; has nothing to do w/ a sub command
        called w/n cmdExecute"""
        if stop == -1:# case of quit
            return stop
        self._updatePrompt()
        return stop

    #-----------------------------------------------------------------------||--
    def cmdExecute(self, cmdList):
        """used for athenaScripts, does many commands in a list
        a simple list of commands is executed one at a time
        called from self.cmdLoop
        """
        for cmdLine in cmdList:
            if cmdLine == None: continue
            cmdLine = self.ao.cmdCorrect(cmdLine)
            if self.echo: # no echo if set to quite
                self.out(('%s %s\n' % (self.ao.promptSym, cmdLine)))
            # exceptions are handled in side this method
            stop = self._cmd(cmdLine)
            stop = self._postcmd(stop, cmdLine)
            self.out('\n')   # prints a space after each command
        return stop

    def cmdLoop(self, cmdList=None):
        """main command loop of athenaCL
        gets input from user in a loop; adds the cmd to cmdList
        calls self.cmdExecute to do work, not self.cmd
        """
        #self.preloop()
        self.out(self.intro)
         # do only of cmdList is empty, and session not cgi
        if cmdList == None and self.sessionType not in ['cgi']:
            if self.ao.timeSinceLastVersionCheck() >= self.versionCheckWait:
                cmdList = ['AUup'] # add version check command at startup
        stop = None
        while not stop:
            if cmdList == None:
                try: # get raw data form user
                    line = dialog.rawInput(self.prompt, self.termObj)
                except (KeyboardInterrupt, EOFError):
                    line = 'quit confirm'  # quit immediatly
                cmdList = line.split(';') # split into mult cdms by ;
            else: # use the command list
                self.echo = 1
            stop = self.cmdExecute(cmdList)
            if cmdList != None:
                cmdList = None # clear command list
                self.echo = 0
        #self.postloop()


    #-----------------------------------------------------------------------||--
    def runScript(self, name, scriptArgs=None):
        """will run a script in libAS folder, or a complete path
        if given (not implemented yet)"""
        # this is experimental: seems to work
        # see http://www.python.org/doc/current/lib/built-in-funcs.html
        modImportStr = 'athenaCL.libATH.libAS.%s' % name
        try:
            name = __import__(modImportStr, globals(), locals(), [name,])
        except ImportError:
            print lang.WARN, 'no such module to import %s' % name
            return None
        scriptObj = name.Script(scriptArgs) #" % name)# call one instance
        self.echo = 1
        # stop value is not used here...
        stop = self.cmdExecute(scriptObj.cmdList)
        self.echo = 0

    #-----------------------------------------------------------------------||--
    #def preloop(self): pass
    #def postloop(self): pass
    def _clearCount(self):
        """clear cmd counts"""
        self._emptyCount = 0 # clear
        self._blankCount = 0 # clear

    def _emptyline(self):
        """print result if an empty command has been found"""
        if self._emptyCount >= random.choice(range(7,20)):
            self._emptyCount = 0
            self.out(dialog.getEncouragement())
        self._emptyCount = self._emptyCount + 1 
        # return nothing

    def _default(self, line):
        """if no command is parsed out of line"""
        if self._blankCount >= random.choice(range(3,10)):
            self._blankCount = 0
            self.out(dialog.getAdmonishment(line))
        else:
            self.out(lang.msgUnknownCmd) # standard result
        self._blankCount = self._blankCount + 1 
        # return nothing


    #-----------------------------------------------------------------------||--
    def _getCursorToolConvert(self):
        """read prefs and return a conversion dictionary
        called on init of Interpreter"""
        # get a blank command object; myst be a AthenaPreferences
        cmdObj = command.APcc(self.ao, self.cmdEnviron)
        convert = cmdObj._apGetCursorToolConvert() # reads prefs
        convert['empty'] = self._cursorTool(convert) # adds fake
        return convert
 
    def _cursorTool(self, convert=None):
        "need optional arg to build a default curos in _getCursor"
        if convert == None:
            convert = self.cursorToolConvert
        left    = '%s%s%s' % (convert['['], convert['PI'], convert['('])
        mid = '%s%s%s' % (convert[')'], convert['TI'], convert['('])
        right = '%s%s' % (convert[')'], convert[']'])
        return left + '%s' + mid + '%s' + right

    def _updatePrompt(self, msg=None):
        """update prompt graphics; done each time command is called"""
        promptRoot = self.ao.promptSym
        # this used to get pref from file; get now from aoInfo
        cursTemplate = self._cursorTool()
        if msg: # intial startup msg
            cursTool = dialog.getSalutation(self.cursorToolConvert)
        else: # update appearance
            cursTool = cursTemplate % (self.ao.activePath, self.ao.activeTexture)       
        if self.ao.aoInfo['cursorToolOption'] != 'cursorToolOff':
            self.prompt = '%s %s ' % (cursTool, promptRoot)
        else:
            self.prompt = '%s ' % (promptRoot)

    #-----------------------------------------------------------------------||--
    def _testThreads(self, force=0):
        """testing if threading modules are available
        cgi threads are always single-threaded
        """
        if force == 0 or self.sessionType in ['cgi', 'idle']:
            status = 0 # turn off
        else:
            status = 1
            if os.name == 'mac':
                pass
            elif os.name == 'posix':
                try: import threading
                except ImportError: status = 0
            else: # all win flavors
                status = 1
                # threads work fine in win, but even when not in idle
                # the animation trick does not do /b correctly
        if status == 0: # no threading
            msg = 'threading off' # need leading space
        elif status == 1:
            msg ='threading active' # need leading space
        return status, msg

    def toggleEcho(self):
        """flips echo status on and off"""
        if self.echo == 1: self.echo = 0
        else: self.echo = 1


    #-----------------------------------------------------------------------||--
    # error handling and logging
    def _errorReport(self, cmd, arg, tbObj):
        """fmtTbList is a list of formatted tb data
        writes to error log file"""
        timeTag = time.asctime(time.localtime())
        msg = []
        msg.append('ERROR, %s, %s\n' % (self.ao.infoStr(), timeTag))
        msg.append('%s %s\n' % (cmd, arg))

        tbList = traceback.extract_tb(tbObj[2]) # get tracebackobject
        for fileName ,lineNo, funcName, text in tbList:
            msg.append("%s, %s, %s\n%s\n" % (fileName, lineNo, 
                                                        funcName, text))
        msg.append(str(tbObj[0]) + '\n') # class, name of exception
        msg.append(str(tbObj[1]) + '\n') # object, string about exception
        # adds an error report to a log file using external manager
        self.ao.external.logWrite(msg) # give formatted data
         # report public info, dont show traceback

    def _historyAdd(self, log):
        """add a log to to dictionary
        if none, dont add or treat special"""
        timeTag = time.time() # use raw seconds
        if log != None: # only deal w/ successful logs
            self.ao.aoInfo['history'][timeTag] = log
        # dont do 


    #-----------------------------------------------------------------------||--
    # proc_ commands need acces to interpreter to function
    # have initila shell in command.py

    def proc_menu(self, data):
        # used for menu commands?
        cmdStr = data['command']
        if cmdStr == None:
            dialog.msgOut(lang.msgReturnCancel, self.termObj)   
        else:
            self.cmdExecute([cmdStr,])

    def proc_quit(self, data):
        del self.ao
        return -1

    def proc_shell(self, data):
        """provides an interactive python session"""
        if os.name == 'mac':
            dialog.msgOut(lang.msgPlatformError % os.name, self.termObj)
        elif os.name == 'posix':
            os.system(data['shellCmd'])
        else:    # all windows flavors
            dialog.msgOut(lang.msgPlatformError % os.name, self.termObj)

    def proc_py(self, data):
        """provides an interactive python session"""
        import code
        if os.name == 'mac':
            exitStr = 'Control-D' 
        elif os.name == 'posix':
            exitStr = 'Control-D' 
        else:    # all windows flavors
            exitStr = 'Control-Z' 
        msg = 'Python Interactive. enter %s to exit:' % exitStr
        code.interact(msg)


    def proc_ASexe(self, data):
        """run a script and print results
        """
        scriptArgs = {} # gather data to generate commands
        scriptArgs['setMeasureNames'] = setMeasure.engines.keys()
        scriptArgs['allCmds'] = self.ao.cmdDocManifest()
        scriptArgs['textureNames'] = texture.tmObjs
        
        fileName = data['name']
        if fileName[-3:] == '.py':
            fileName = fileName[:-3]

        timer = rhythm.Timer() # start timer
        self.runScript(fileName, scriptArgs)
        timer.stop()
        dialog.msgOut('\nAthenaScript Execute %s complete (%s):\n' % (
                                            data['name'], timer), self.termObj)

    def proc_AOrm(self, data):
        dialog.msgOut('reinitializing AthenaObject.\n', self.termObj)        
        del self.ao
        self.ao = AthenaObject(self.termObj)

    def proc_AHexe(self, data):
        self.echo = 1
        self.cmdExecute(data['cmdList'])
        self.echo = 0
        dialog.msgOut('AthenaHistory Execute complete.\n', self.termObj)         


