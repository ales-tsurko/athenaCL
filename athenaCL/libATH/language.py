#-----------------------------------------------------------------||||||||||||--
# Name:          language.py
# Purpose:       handles strings for various langauges.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

# encoding will be
# -*- coding: UTF-8 -*-


import string, random
import unittest, doctest
# language must be set by this class reading a preference file
# otherwise, works only as a global class


class LangObj:
# interface constants

    def __init__(self, language='en'):
        """
        >>> a = LangObj()
        """
        self.language = language
        self.langDict = {}
        # always need en, can optional load other language
        self.langDict['en'] = LangEn() # english 

        self.errorStr = 'missing string (%s)'

        if self.language not in self.langDict.keys():
            raise ValueError, 'no such language'

    def __getattr__(self, name):
        # language can be dynamically changed.
        if self.language not in self.langDict.keys():
            raise ValueError, 'no such language'

        if self.language == 'en': # en should have all strings
            try:
                return getattr(self.langDict['en'], name)
            except AttributeError:
                #print self.errorStr % name
                return self.errorStr % name
        else:
            try:
                return getattr(self.langDict[self.language], name)
            except AttributeError: # if missing in a language get english version
                return getattr(self.langDict['en'], name)

    def listAttr(self):
        'give a list of all attribute names that are strings'
        attributes = dir(self.langDict['en']) # use eng, as most complete
        strAttr = []
        for name in attributes:
            if name[0] != '_': # if leads with underscore, dont add
                strAttr.append(name)
        return strAttr

    def msgDividerAlgo(self, width=60, chars=['_','_','_']):
        msg = []
        for x in range(0, width):
            msg.append(random.choice(chars))
        return ''.join(msg)


class LangEn:
    """all english strings
    used to genearate attributes list: thus only strings can have
    full attribute names
    if other methods are needed, use _name for private
    """
    
    #-----------------------------------------------------------------------||--
    # sizes and symbols
    TAB  = '      '
    TABW = 3 # width of tab, cannot be greater than 9
    LMARGINW = 20 # size of all display margins. includes a tab if used
    MMARGINW = 30 # size of all mid margins 
    NAMEW    = LMARGINW - TABW # size of all display names, 17
    SHIFTW = (LMARGINW / 2) - TABW # half of lmargin - tab, or 7
    
    # name chars used for path/texture/clone names, as well as custom cursors
    # leave out # and %: python usesm leave out < > &, xml needs escaped
    # removed post 1.3.1: ^`~
    NAMECHARS  = string.letters + string.digits + '_@$|*-=+(){}[].?!'
    # chars allowed in a file name, no spaces allowed
    FILECHARS  = string.letters + string.digits + '_-[].?!'
    # all commands can only use these chars
    IDENTCHARS = string.letters + string.digits + '_'
    # define symbols and common words used
    DIVIDER = '.'
    ACTIVE  = '+'
    INACTIVE = ''
    MUTEON  = 'o'
    MUTEOFF = '+'
    MUTELABEL = 'status'
    ON   = 'on'
    OFF = 'off'
    ALL = 'all' # string to be used to select all members of a collection
    COMPLETE = 'complete'
    YES = 'yes'
    NO = 'no'
    TRUE = 'true'
    FALSE = 'false'
    CANCEL = 'cancel'
    BREAK = 'break'
    WARN = 'WARNING:'
    ERROR = 'ERROR:'
    
    # other data
    BIRTH = (2000, 6, 30) # first release date

    #-----------------------------------------------------------------------||--
    #strings
    msgCommentBreak = ('-'*65) + ('|'*12) + ('-'*2)
    msgAth = 'athenaCL'
    msgAthURL = 'www.athenacl.org'
    msgAthDocURL = 'www.flexatone.net/athenaDocs/'
    msgAthDeveloperURL = 'http://code.google.com/p/athenacl/'
    msgAuthor = 'Christopher Ariza'
    msgAuthorEmail = 'ariza@flexatone.net'
    msgBugReport = 'athenacl-development@lists.sourceforge.net'

    msgCgiDomain = 'www.flexatone.net:80'
    msgCgiURL = '/cgi-bin/py/flexNet/software/q.cgi' #?stateNext=8'
    msgVersionURL = 'www.flexatone.net/athenaCL/version.txt'
    msgAthDownloadURL = 'www.flexatone.net/athena.html#athenaDownload'
    # common file path to a tar file; insert version number
    msgAthDownloadTar = 'http://athenacl.googlecode.com/files/athenaCL-%s.tar.gz'

    msgAthIntro = 'Enter "cmd" to see all commands. For help enter "?".\nEnter "c" for copyright, "w" for warranty, "r" for credits.\n'
    
    #-----------------------------------------------------------------------||--
    # key description paragrahs
    
    # very short
    msgAthDescMicroMini = "poly-paradigm algorithmic music composition"

    msgAthDescMini = "poly-paradigm algorithmic music composition in an interactive command-line environment"
    
    # normal subtitle
    msgAthDescShort = """\
modular poly-paradigm algorithmic music composition in a cross-platform interactive command-line environment."""

    msgAthDescLong = """\
The athenaCL system is an open-source, object-oriented composition tool written in Python. The system can be scripted and embedded, and includes integrated instrument libraries, post-tonal and microtonal pitch modeling tools, multiple-format graphical outputs, and musical output in Csound, SuperCollider, Pure Data, MIDI, audio file, XML, and text formats."""

    
    # sf net limits to only 254 characters, also for fink desc detail
    msgAthDescSf ="""
Modular poly-paradigm algorithmic music composition in a cross-platform interactive command-line environment written in Python and providing musical output in Csound, SuperCollider, Pure Data, MIDI, audio file, XML, and text formats.     
    """

    # not worth saying: extensible (its open and in Python)
    # sieves/specturm pitch tools: not clear

    _pmtrObjSummary = "Over eighty specialized Generator, Rhythm, and Filter ParameterObjects provide tools for stochastic, chaotic, cellular automata based, Markov based, generative grammar and Lindenmayer system (L-system), wave-form, fractional noise (1/f), genetic, Xenakis sieve, linear and exponential break-point segments, masks, and various other algorithmic models. ParameterObjects can be embedded in other ParameterObjects to provide powerful dynamic and masked value generation."
    
    # use this in addition to msgAthDescLong for complete listing
    msgAthDescFull = """\
Musical parts are deployed as Textures, layered surface-defining objects containing numerous independent ParameterObjects to control pitch, tempo, rhythm, amplitude, panning, and instrument (Csound) parameters. The system includes an integrated library of Csound and SuperCollider instruments, and supports output for external Csound instruments, MIDI, and a variety of alternative formats. %s Textures can be combined and edited, and tuned with algorithmic Temperament objects. Texture Clones allow the filtering and processing of Texture events, performing transformations not possible with parameter generation alone.

The algorithmic system uses Path objects to organize and share pitch groups. Paths provide simultaneous representations of ordered content groups in set-class, pitch-class space, and pitch space.""" % (_pmtrObjSummary)

    msgAthFeatInterface =  """\
Advanced, easy to use, interactive command line: enter commands with arguments, or just enter the command and athenaCL will prompt the user for all necessary data.

Command history logging, and executable command history.

Graphical displays in EPS (convertible to PDF), Tk GUI, PNG, and JPEG formats, providing Texture arrangement views, Path voice leadings, and Texture parameter event graphs. 

Interactive help for every command. Complete HTML / PDF tutorials and reference documentation.
"""

    msgAthFeatAlgo = """\
Rapid creation of polyphonic event list structures. Theses event lists can be composed for GeneralMidi or as Csound scores using a built in library of internal instruments. Output formats include scores for internal or external Csound instruments, MIDI files, text-based output formats, and support for alternative algorithmic composition systems including Paul Berg's AC Toolbox and Michael Goggins' Silence.

Over sixty integrated Csound instruments, all with default values and documentation.

Combine any number of musical parts or Textures, controlling tempo, pitch, rhythm, amplitude, panning, and instrument-dependent parameters with modular customizable ParameterObjects. %s

Control panning as a standard parameter in mono, stereo, or (with Csound) quadraphonic space.

Control pitch data with Paths: reusable, partitioned pitch collections. Paths    can be specified as Xenakis sieves, set classes, microtonally specified pitch collections, or through spectral analysis files from the audio editor Audacity. Further shape pitches within Textures with algorithmic Temperament objects.  
""" % (_pmtrObjSummary)

    msgAthFeatAnalytic = """\
Pitch set class dictionary containing all 351 sets (all Tn types from the singleton to the dodecachord) and capable of quickly converting any pitch set, Forte number, or Xenakis sieve to normal-form.
"""



    #-----------------------------------------------------------------------||--
    msgAthCopyright = 'Copyright (c) 2000-2010 Christopher Ariza and others.'
    msgLicenseShort = 'athenaCL is free software, distributed under the GNU General Public License.\n'
    msgLicenseName = 'GPL' # this is the necessary package code 
    msgAthUsage = 'Usage: athenacl [options]'

    msgCredits = """\
athenaCL was created and is maintained by Christopher Ariza. Numerous generator ParameterObjects based in part on the Object-oriented Music Definition Environment (OMDE/pmask), Copyright 2000-2001 Maurizio Umberto Puxemdu; Cmask was created by Andre Bartetzki. The Command Line Interpreter is based in part on cmd.py; the module textwrap.py is by Greg Ward; both are distributed with Python, Copyright 2001-2003 Python Software Foundation. The fractional noise implementation in dice.py, Audacity spectrum importing, and dynamic ParameterObject boundaries are based in part on implementations by Paul Berg. The module genetic.py is based in part on code by Robert Rowe. The module midiTools.py is based in part on code by Bob van der Poel. The module chaos.py is based in part on code by Hans Mikelson. The module permutate.py is based in part on code by Ulrich Hoffman. Pitch class set names provided in part by Larry Solomon. The Rabin-Miller Primality Test is based in part on an implementation by Stephen Krenzel. The mpkg installer is generated with py2app (bdist_mpkg) by Bob Ippolito. Python language testing done with PyChecker (by Neal Norwitz Copyright 2000-2001 MetaSlash Inc.) and pyflakes (by Phil Frost Copyright 2005 Divmod Inc.). Thanks to the following people for suggestions and feedback: Paul Berg, Per Bergqvist, Marc Demers, Ryan Dorin, Elizabeth Hoffman, Anthony Kozar, Paula Matthusen, Robert Rowe, Jonathan Saggau, and Jesse Sklar. Thanks also to the many users who have submitted anonymous bug-reports."""
    
    # these are only used for athenacl now
    msgTrademarks             = """\
Apple, Macintosh, Mac OS, and QuickTime are trademarks or registered trademarks of Apple Computer, Inc. Finale is a trademark of MakeMusic! Inc. Java is a trademark of Sun Microsystems. Linux is a trademark of Linus Torvalds. Max/MSP is a trademark of Cycling '74. Microsoft Windows and Visual Basic are trademarks or registered trademarks of Microsoft, Inc. PDF and PostScript are trademarks of Adobe, Inc. Sibelius is a trademark of Sibelius Software Ltd. SourceForge.net is a trademark of VA Software Corporation. UNIX is a trademark of The Open Group."""

# IBM PC is trademark of IBM. 
    
    #-----------------------------------------------------------------------||--
    msgAthObjError = 'apologies: the previous command could not be completed as expected.\nplease report this bug when quitting, or examine the log (AUlog).\n'
    msgSubmitLog = 'anonymously submit bug report?'
    msgSubmitLogFail = 'no connection possible; try again when on-line.\n'
    msgSubmitLogSuccess = 'thank you! submitting bugs is very important, please continue to do so in the future.\n'
    msgVersionCheck = 'check online for updates to athenaCL?'
    msgVersionUpdate = 'a %s update to athenaCL (%s) is now available.\nopen download page in a browser?'
    msgUpTodate = 'athenaCL %s is up to date.\n'

    msgBadPmtrFormat = 'incorrect parameter format.\n'
    msgBadArgFormat = 'incorrect argument format.\n'
    msgConfusedInput = TAB + 'incomprehensible input, try again.\n'
    msgIncorrectEntry = TAB + 'incorrect entry. try again.\n'
    # this was just empty, but was not giving a proper new line in some cases
    msgReturnCancel  = '' #'   .' 
    msgMenuChangeDir = 'to change directory enter name, path, or ".."\ncancel or select? (c or s):'
    msgMenuFile = 'name file, change directory, or cancel? (f, cd, c):'
    msgBadAthObj = TAB + 'there is a problem with this AthenaObject file. make sure an AthenaObject has been selected, then try (1) opening the file in a text editor and re-saving the file with the appropriate line endings or (2) restart athenaCL and try again.\n'
    msgBadInput = TAB + 'unidentified input. try again:\n'
    msgBadNameChars = TAB + 'this name consists of invalid characters. try again:\n'
    msgBadNameLength = TAB + 'this name is too long. try again:\n'
    msgUnknownCmd = 'unknown command. enter "cmd" to see all commands.\n'   
    msgFileError = 'a bad file path has been selected; try to write files in a better location.\n'
    msgFileIoError = 'error occurred while trying to write %s.'
    msgPlatformError = 'this command is not available on %s platforms.\n'

    msgGfxTkError = 'install Tk in Python for tk graphic output.'
    msgGfxIdleError = 'tk graphics are not available during an IDLE session.'
    msgGfxPilError = 'install PIL in Python for jpg or png graphic output.'
    
    msgReturnToExit = 'press return to exit:'
    msgPleaseWait = 'processing.'
    
    msgMissingLibATH = '\nlibATH cannot be found. reinstall athenaCL\n'
    msgMissingLibTM = '\nlibTM cannot be found. reinstall athenaCL\n'
    msgMissingLibAS = '\nlibAS cannot be found. reinstall athenaCL\n'
    msgMissingXML = '\nno XML parsers found: athenaCL requires Python xml.dom.minidom.\nupgrade or replace this version of Python.\n'
    msgMissingDemo = '\ndemo cannot be found. reinstall athenaCL\n'
    msgMemoryError = '\nnot enough memory to load %s.py: try again?'
    
    msgDlgBadPath = TAB + 'this is not a valid path. try again?'
    msgDlgBadInput = TAB + ERROR + ' %s not understood. try again.\n'
    msgDlgSaveInThisDir = '%s\n' + TAB + 'save in this directory?'
    msgDlgFileExists = 'this file already exists. replace?'
    msgDlgSaveThisFile = '%s\n' + TAB + 'save this file?'
    msgDlgBadFileNameStart = TAB + ERROR + ' a file name cannot start with "%s". try again.\n'
    msgDlgBadFileNameChar = TAB + ERROR + ' a file name cannot contain "%s". try again.\n'
    msgDlgEnterIntRange = TAB + 'enter an integer between 0 and %s.\n'

    msgDlgNoSuchDir = 'no such directory\n'
    msgDlgDirNotFile = 'this is a directory, not a file. try again?'
    msgDlgNotApp = 'this is neither an application nor an executable. try again?'
    msgDlgNameFile = 'name file?'
    msgDlgBadFileName = 'no such file exists. try again?'
    msgDlgSelectThisFile = '%s\n' + TAB + 'select this file?'
    msgDlgMacError = 'Mac dialogs not currently available.'
    msgDlgTkError = 'Tk dialogs not currently available.'

    msgDocAdditionalHelp = 'for help with a command, enter "?" followed by the command.\n'
    msgDocCmd = 'to see a hierarchical listing of commands, enter "cmd".\n'
    msgDocPrefix = 'to see all commands associated with a prefix, enter that prefix.\n'
    msgDocBrowser = 'to open documentation in a browser, enter "AUdoc".\n'
    msgDocHead = 'athenaCL commands:\n'

    #-----------------------------------------------------------------------||--
    # strings for particular commands
    msgSCselectX              = 'select SC X:\n'
    msgSCselectY              = 'select SC Y:\n'
    msgSCenterSimCentRange = 'enter a similarity percentage range:'
    msgSCcentRangeError   = TAB + 'a percentage range must be entered as two values separated by a comma. try again.\n'
    msgSCcentValueError   = TAB + 'percentage values can be either decimals (0 to 1) or percentages (0 to 100).\n'
    msgSCtni                      = 'TnI'
    msgSCtn                   = 'Tn'
    msgSCtniMode              = TAB + msgSCtni + ' classification\n'
    msgSCtnMode               = TAB + msgSCtn + ' classification\n'
    msgSCsetTni               = 'SC classification set to %s.\n' % msgSCtni
    msgSCsetTn                = 'SC classification set to %s.\n' % msgSCtn
    msgSCsimRange             = 'similarity range:'
    msgSCnoSuchSet            = TAB + 'no such set exists, try again.\n'
    msgSCgetSet               = 'enter a pitch set, sieve, spectrum, or set-class:'
    msgSCgetAudacity          = 'select an Audacity spectrum file (.txt):'
    msgSCenterFindMethod      = 'select a find method: name, z-relation, or super-sets? (n, z, s):'
    msgSCenterFindString      = 'enter a search string:'
    
    msgMCgetBadSize       = TAB + 'no maps are available between %r and %r voices.'
    msgMCgetRefOrder          = 'enter a referential ordering for %s:'
    msgMCgetRefOrderBad   = TAB + 'the referential ordering must contain all elements.'
    msgMCgetBadVlPairs    = TAB + 'cannot yet handle vl pairs between boundaries of different sizes.'
    msgMCgetBadVlParse    = TAB + 'unable to parse vl pairs.\n'
    msgMCgetBadVlLimit    = TAB + 'vl pairs can describe at most 6 voices.'

    msgMCbadMapRange          = TAB + 'incorrect map range. enter a start map, a comma, and an end map.\n'
    msgMCbadPosition          = TAB + 'incorrect position entry. try again.\n'
    msgMCbadRankRange         = TAB + 'incorrect rank range. enter a start rank, a comma, and an end rank.\n'
    msgMCbadVoiceRange    = TAB + 'incorrect entry. enter (sourceNumber, destinationNumber).\n'
    msgMCbadVoiceValue    = TAB + 'the number of voices in a source or destination must be between 1 and 6.\n'
    msgMCbadRawMapFormat      = TAB + 'incorrect raw map format.\n'
    msgMCbadVoiceFormat   = TAB + 'incorrect voice-leading format.\n'
    msgMCbadMapChoice         = TAB + 'between %r and %r voices you must choose a MC between 1 and %r.\n'
    msgMCerrorCreatingChord= TAB + 'set cancelled.\n'
    msgMCnoSuchMap            = TAB + 'no such map exists, try again.\n'
    msgMCnoSuchRank       = TAB + 'no such map rank exists, try again.\n'
    msgMCenterRankMethod      = 'enter ranking method: Smoothness, Uniformity or Balance? (s, u, or b):'
    msgMCenterVoiceRange      = 'enter the number of voices in source, destination:'
    msgMCenterTwoSetSizes  = 'enter two set-sizes to compare:'
    msgMCenterMapRange    = 'there are %i maps in this ranking. enter a range: (beginRank,endRank):'
    msgMCenterMapSizeRange = 'there are %i maps in this size group. enter a range: (beginMap,endMap):'
    msgMCgetMapMenu       = 'enter a map, map class, or vl pairs:'
    msgMCminDisplVal          = 'minimum displacement values for all sets between cardinality %i and %i\n'
    msgMCchooseRank       = 'choose a rank of %s between 1 and %s:'
    msgMCthisAsthat       = TAB + 'MC %s as %s?'
    
#     msgPEnoNamedPE            = 'no such SetMeasure exists. enter "SMls" to see all names.\n'    
#     msgPEblankNowActive   = 'SetMeasure %s now active.\n'
    
    msgPInameGet              = 'name this PathInstance:'
    msgPIcreateFirst          = 'create a PathInstance first: enter "PIn".\n'
    msgPImissingName          = 'that PathInstance no longer exists: enter "PIo".\n'
    msgPIbadName              = 'no such PathInstance exists. enter "PIls" to see all names.\n'
    msgPInameTaken            = 'that PI name already exists, choose another.\n'
    msgPIcancel               = 'path cancelled.\n'
    msgPIoptOrAntiopt         = 'optimize or anti-optimize? (o or a):'
    msgPIbadSliceRange    = TAB + 'incorrect slice format. enter (start, end).\n'
    msgPIbadDuration          = TAB + 'enter a list of %s values greater than zero, separated by commas.\n'  

#     msgPVnotAvailable         = 'no PV operations are available.\n'
#     msgPVgroupMissingName  = 'that PathVoice no longer exists: enter "PVo".\n'
#     msgPVbadName              = 'no such PathVoice exists. enter "PVls" to see all names.\n'
#     msgPVnameTaken            = TAB + 'that PathVoice name already exists, choose another.\n'
#     msgPVmapOrRankError   = TAB + 'select rank or map by entering r or m.\n'
#     msgPVselectFirstLast      = 'select first or last map from each ranking? (f or l):'
#     msgPVfirstOrLastError  = TAB + 'select first or last by entering f or l.\n'
    
    msgTMbadName              = 'no such TextureModule exists. enter "TMls" to see all names.\n' 
    
    msgTIcreateFirst          = 'create a TextureInstance first: enter "TIn".\n'
    msgTIselectFirst          = 'select a TextureInstance first: enter "TIo".\n' 
    msgTIunmuteFirst          = 'unmute a texture or a clone first: enter "TImute" or "TCmute".\n'
    msgTIbadName              = 'no such TextureInstance exists. enter "TIls" to see all names\n'
    msgTImissingName          = 'that TextureInstance no longer exists: enter "TIo".\n'
    msgTIname                 = 'name this texture:'
    msgTIcreated              = 'TI %s created.\n'
    msgTInameTaken            = 'that TI name already exists, choose another.\n'
    msgTIbadPmtrName          = 'no such parameter exists: enter "TIv" to display parameters.\n'
    msgTIcompareParam         = 'compare texture parameters: which parameter?'
    msgTInoPolyModePath   = 'the path referenced to this texture (%s) does not support part Polyphony Mode\n'
    msgTIeditTempoMenu    = TAB + 'beat edit: enter value or tap new tempo? (v, t):'
    msgTIeditArgError         = TAB + 'TIe %s ' % ERROR + 'unable to convert argument to data:'
    msgTIePmtrSel             = 'edit TI %s\nwhich parameter? (i,t,b,r,p,f,o,a,n,x,s,d):'
    msgTInoAuxEdit            = 'TIe %s' % ERROR + ' this instrument has no auxiliary parameter fields\n'
    msgTInoTextEdit       = 'TIe %s' % ERROR + ' this texture has no static texture parameters\n'
    msgTInoDynEdit            = 'TIe %s' % ERROR + ' this texture has no dynamic texture parameters\n'

    msgTImodeChoose   = 'edit TI %s: Pitch, Polyphony, Silence, or PostMap Mode? (p, y, s, m):'
    msgTImodePitchChoose = TAB + 'current Pitch Mode: %s. enter new mode (sc, pcs, ps):'
    msgTImodePolyChoose   = TAB + 'current Polyphony Mode: %s. enter new mode (set, part):'
    msgTImodeSilenceChoose = TAB + 'current Silence Mode: %s. enter new mode (on, off):'
    msgTImodeMixChoose    = TAB + 'current PostMap Mode: %s. enter new mode (on, off):'
    msgTInoSuchMode       = 'no such mode exists: enter "TIv" to display parameters.\n'
    msgTInoSuchPitchMode      = 'no such pitch mode exists: enter sc, pcs, or ps.\n'
    msgTInoSuchPolyMode   = 'no such polyphony mode exists: enter set or part.\n'
    msgTInoSuchSilenceMode = 'no such silence mode exists: enter on or off.\n'
    msgTInoSuchMapMode    = 'no such postMap mode exists: enter on or off.\n'

    
    msgTImidiPmtrSel          = 'edit midi settings for TI %s: program or channel? (p or c):'
    msgTImidiPmtrError    = 'no such midi setting available.\n'
    msgTImidiPgmSel       = 'enter a program number or general midi program name:'
    msgTImidiPgmError         = TAB + 'no such program exists: enter a name or number.\n'

    msgTCnameTaken            = 'that TextureClone name already exists, choose another.\n'
    msgTCcreateFirst          = 'create a TextureClone first: enter "TCn".\n' 
    msgTCbadName              = 'no such TextureClone exists. enter "TCls" to see all names.\n'
    msgTCbadTimeEntry         = TAB + 'a TextureClone cannot start before time 0. enter a more positive timeShift.\n'
    msgTCbadPmtrName          = 'no such parameter exists: enter "TCls" to display all parameters.\n'
    msgTCbadEdit              = 'bad TC edit data. no changes have been made.\n'
    msgTCnoAuxEdit            = 'TCe %s' % ERROR + ' this instrument has no auxiliary parameter fields\n'     
    msgTCnoTextEdit       = 'TCe %s' % ERROR + ' this clone has no static clone parameters\n'
    msgTCeditArgError         = TAB + 'TCe %s ' % ERROR + 'unable to convert argument to data:'


    msgTCePmtrSel             = 'edit TC %s\nwhich parameter? (t,u,c,f,o,a,n,x,s):'
    msgTCbadPmtrName          = 'no such parameter exists: enter "TCv" to display parameters.\n'

    msgTTbadName              = 'no such TextureTemperament exists. enter "TTls" to see all names.\n'
    msgTTselectName       = 'select a TextureTemperament for TI %s:'
    
    msgTEePmtrSel             = 'edit all TextureInstances\nwhich parameter? (i,t,b,r,p,f,o,a,n,x):'
    msgTEgetTempo             = 'current midi tempo %s: enter a new tempo:'
    msgTEtempoError       = TAB + 'midi tempo values must be a number between 0 and 9999.\n'
    msgTEnoAuxEdit            = 'TEe %s' % ERROR + ' no auxiliary list-edit available\n'
    msgTEnoTextEdit       = 'TEe %s' % ERROR + ' no texture static list-edit available\n'
    msgTEnoDynEdit            = 'TEe %s' % ERROR + ' no texture dynamic list-edit available\n'

    msgEMviewError            = 'EventMode view failed (%s).\n'
    msgEMinstAvail            = '%s instruments:\n' # used to say Orchestra here
    msgEMmodeSet              = 'EventMode mode set to: %s.\n'
    msgEMselect               = 'select an EventMode mode:'
    msgEMbadMode = TAB + 'no such EventMode mode exists. try again.\n'
    msgEMnoInstrument  = TAB + 'no such instrument available, enter "?" to view all instruments.\n'
    msgEMgetOutput  = 'select output format: %s? (%s):'
    msgEMnoOutput = TAB + 'no such format exists.\n'


    msgELcreateFirst = 'create an event list first. enter "ELn".\n'
    msgELfileMoved = 'the file (%s) cannot be found. enter "ELn" to create new EventList files.\n'
    msgELnoScores   = 'too many rests: no events were created.\n'
    msgELviewInit = 'EventList view initiated: %s\n'
    msgELnameScore            = 'name an EventList. use a ".xml" extension:'
    msgELbadScoreName         = 'EventList files must end with a ".xml" extension.\n'
    msgELrenderError          = 'audio rendering failed (%s). check audio and csound preferences.\n'
    msgELrenderInit       = 'audio rendering initiated: %s\n'
    msgELrNotAvailable    = 'EventList rendering not available under EventMode: %s\n'
    msgELaudioMoved       = 'audio file (%s) cannot be found. enter "ELr" to render an audio file.\n'
    msgELhearError            = 'EventList hear failed (%s).\n'
    msgELhearInit             = 'EventList hear initiated: %s\n'


    msgAPcurentAppPath    = 'current application path:\n%s\n'
    
    msgELauto                 = 'csound auto score render control set to %s.\n'

    msgAObadWidth             = 'the character width should be between 30 and 300. try again.\n'
    msgAObadName              = 'AthenaObject files must end with a ".xml" extension. try again.\n'
    msgAOnameFile             = 'name this AthenaObject. use a ".xml" extension:'
    msgAOselectFile       = 'select an AthenaObject file:'
    msgAOcreateFirst          = 'create a path or a texture first: enter "PIn" to begin.\n'
    msgAOnotXML               = TAB + 'this is not an AthenaObject xml document.\n'
    msgAOerrorXML             = TAB + 'unable to parse xml document.\n'
    msgAOnotAOdoc             = TAB + 'this is not an AthenaObject document.\n'
    msgAOselAdirOrSdir = 'select directory to set: scratch or audio. (x or a):'

    msgAPdlgSelect            = 'active dialog visual method: %s.\nselect text, tk, or mac. (t, k, or m):'
    msgAPdlgConfirm       = 'dialog visual method changed to %s.\n'
    msgAPgfxSelect            = 'active graphics format: %s.\nselect text, eps, tk, jpg, png. (t, e, k, j, or p):' 
    msgAPgfxConfirm       = 'graphics format changed to %s.\n'
    msgAPcursorTool       = 'cursor tool set to %s.\n'
    msgAPrefreshMode          = 'refresh mode set to %s.\n'

    #-----------------------------------------------------------------------||--
    salutationAm0 = 'welcome'
    salutationAm1 = 'good day.'
    salutationAm2 = 'good morning.'
    salutationPm1 = 'good afternoon.'
    salutationPm2 = 'good evening.'
    salutationPm3 = 'evening.'
    salutationBirth  = 'athenaCL was first released on this day %s years ago.'
    provoke1 = 'nothing.'
    provoke2 = 'anything?'
    provoke3 = 'attempt a command?'
    provoke4 = 'try something.'
    provoke5 = 'empty?'
    provoke6 = 'still nothing.'
    admonish1                 = '%s does not make any sense.'
    admonish2                 = 'what is a %s?'
    admonish3                 = '%s is irrational.'
    admonish4                 = '%s?'
    admonish5                 = 'never implemented a %s.'
    admonish6                 = '%s is a curious thing to consider.'
    
    #-----------------------------------------------------------------------||--
    # documentation stringsL output engines
    
    docOeAudioFile = 'Translates events to audio samples, and writes an audio file. Each event\'s amplitude is scaled between -1 and 1. Event timing and other event parameter data are stripped. Compatible with all Orchestras.'
    
    docOeCsoundNative = 'Translates events to a Csound score for use with the native Csound orchestra. All event parameters are retained. Compatible only with the CsoundNative Orchestra.'

    docOeSuperColliderTask = 'Translates events to a SuperCollider task process file for use with the native SuperCollider orchestra. All event parameters are retained. Compatible only with the SuperColliderNative Orchestra.'

    
    docOeCsoundExternal = 'Translates events to a Csound score for use with an external orchestra. Event parameters instrument number, start time, and duration are always the first three parameters. Additional event parameters taken from auxiliary parameters. Compatible with all Orchestras.'
    
    docOeCsoundSilence = 'Translates Texture and Clone events to a Csound score for use with the Csound Silence system by Michael Goggins. Event parameters follow a standard number and order. Standard panning control applied to x pan event parameter. Compatible only with the CsoundSilence Orchestra.' 
    
#     docOeMaxColl = 'Translates events to a Max coll object data format for use inside Max/MSP. All values are converted to MIDI integer values. Events, for each Texture or Clone, are stored as triples of MIDI pitch, MIDI velocity, and event time span. All events for Textures or Clones are labeled with numbered keys, starting from 1. Compatible with all Orchestras; GeneralMidi Orchestra will be used for event postMap conversions.'

    docOePDArray = 'Translates all event parameter streams to individual Pure Data (PD) arrays. Such arrays can be read from at the control or audio rate from within PD using tabread and related objects. Compatible with all Orchestras.'
    
    # note: find out what type of midi file
    docOeMidiFile = 'Translates events to a standard (type 1) MIDI file. Compatible with all Orchestras; in all cases events are translated with the GeneralMidi Orchestra.'
    
    docOeAcToolbox = 'Translates each Texture and each Clone into a Section and writes an Environment file for loading within Paul Berg\'s AC Toolbox. A Parallel Section, containing references to each of these Sections, is also provided. Compatible with all Orchestras; GeneralMidi Orchestra will be used for event postMap conversions.'
    
    docOeText = 'Translate events to a plain text file. All event parameter values are separated by a delimiter (tab or space) and ended with a return carriage. Compatible with all Orchestras; EventMode Orchestra will be used for event postMap conversions.'
    
    #-----------------------------------------------------------------------||--
    # documentation strings: tm
    docTmMonophonicOrnament = "This TextureModule performs each set of a Path as a literal line; pitches are chosen from sets in order, and are optionally repeated within a single set's duration. Algorithmic ornamentation is added to a line based on two factors: the selection of an ornament repertory, and the specification of ornament density."
    
    docTmIntervalExpansion =  "This TextureModule performs each set of a Path as a literal line; pitches are chosen from sets in order, and are optionally repeated within a single set's duration. Algorithmic ornamentation is added to a line based on two factors: the selection of an ornament repertory, and the specification of ornament density. Ornament pitch values, where integers are half steps, are additionally shifted by a value produced by a generator ParameterObject."
    
    docTmDroneArticulate = "This non-linear TextureModule treats each pitch in each set of a Path as an independent voice; each voice is written one at time over the complete time range of each set in the Texture."
    
    docTmDroneSustain = "This TextureModule performs a simple vertical presentation of the Path, each set sustained over the complete duration proportion of the set within the Texture. Note: rhythm and bpm values have no effect on event durations."
    
    docTmLineCluster = "This TextureModule performs each set of a Path as a chord cluster, randomly choosing different voicings."
    
    docTmLineGroove = "This TextureModule performs each set of a Path as a simple monophonic line; pitches are chosen from sets in the Path based on the pitch selector control."
    
    docTmLiteralHorizontal = "This TextureModule performs each set of a Path as a literal horizontal line; pitches are chosen from sets in fixed order, and are optionally repeated within a single set's proportional duration."
    
    docTmLiteralVertical = "This TextureModule performs each set of a Path as a literal verticality; pitches are chosen from sets in fixed order, and are optionally repeated within a single set's proportional duration."

    docTmTimeFill = "This non-linear TextureModule fills a Texture time range with events; event start times are determined by mapping values produced by a generator ParameterObject (set to output values between 0 and 1) to the Texture time range. Remaining event parameters are determined by their respective ParameterObjects."

    docTmTimeSegment = "This non-linear TextureModule fills a Texture time range with events; event start times are determined by mapping values produced by a generator ParameterObject (set to output values between 0 and 1) to segments of the Texture time range, where each segment width is determined by both a generator ParameterObject for segment weight and a the total segment count. Segment weights are treated as proportional weightings of the Texture's duration. Remaining event parameters are determined by their respective ParameterObjects."
    
    docTmHarmonicShuffle = "This TextureModule provides limited access to Path pitch collections in an order, rate, simultaneity size, and simultaneity composition determined by generator ParameterObjects. Path Multisets and pitches within Multisets are chosen by selectors. The number of simultaneities that are created from a Multiset, and the number of pitches in each simultaneity, are controlled by generator ParameterObjects; all values are probabilistically rounded to the nearest integer. When extracting pitches, a size of zero takes all pitches from the selected Multiset; sizes greater than the number of available pitches are resolved to the maximum number of pitches. Remaining event parameters are determined by their respective ParameterObjects."

    docTmHarmonicAssembly = "This TextureModule provides free access to Path pitch collections in an order, rate, simultaneity size, and simultaneity composition determined by generator ParameterObjects. Path Multisets are directly selected by index values generated by a ParameterObject; all values are probabilistically rounded to the nearest integer and are resolved by the modulus of the Path length. The number of simultaneities created from a selected Multiset is controlled by a generator ParameterObject; all values are probabilistically rounded to the nearest integer. Pitches within Multisets are directly chosen by index values generated by a ParameterObject; all values are probabilistically rounded to the nearest integer and are resolved by the modulus of the Multiset size. The number of pitches extracted from a Multiset is controlled by a generator ParameterObject; a size of zero takes all pitches from the selected Multiset; sizes greater than the number of pitches are resolved to the maximum number of pitches. Remaining event parameters are determined by their respective ParameterObjects."

    _interpolation = "All standard and auxiliary parameters, or just time parameters, can be interpolated. Interpolation method may be linear, power, or half-cosine. Frames are generated between each event at a rate controlled by a ParameterObject. Frame rates can be updated once per event or once per frame, as set by the level frame duration texture parameter. Power segment interpolation may use dynamic exponent values from a ParameterObject; exponent values are updated once per event. Note: independent of silenceMode, silent events are always created."

    docTmInterpolateLine = "This TextureModule interpolates parameters between events generated under a linear monophonic context. %s" % (_interpolation)

    docTmInterpolateFill = "This TextureModule interpolates parameters between events generated under a non-linear monophonic context. %s" % (_interpolation)

    #-----------------------------------------------------------------------||--
    # documentation strings: po
    # generators
    
    _dynamicMarkovOrder = 'Markov transition order is specified by a ParameterObject that produces values between 0 and the maximum order available in the Markov transition string. If generated-orders are greater than those available, the largest available transition order will be used. Floating-point order values are treated as probabilistic weightings: for example, a transition of 1.5 offers equal probability of first or second order selection.'
    
    _dyanmicalSystem = 'For some parameter settings the system exhibits chaotic behavior, for others, periodic behavior; small changes in initial parameters may demonstrate the butterfly effect.'

    # selection  
    _selectionStr = 'Values are chosen from this list using the selector specified by the selectionString argument.'

    # unit scaling
    _normalizedList = 'The resulting list of values is normalized within the unit interval.'

    # min max tags        
    _scaleCommon = 'This value is scaled within the range designated by min and max; min and max may be specified with ParameterObjects.'

    # min max evelopes
    _scaleEnvelope = 'The minimum and maximum envelope value is scaled within the range designated by min and max; min and max are selected once per envelope; min and max may be specified with ParameterObjects.'

    _envelopeCommon = 'Envelope duration is specified by the duration ParameterObject; all values are interpreted in seconds. The scaleString parameter determines if shape values are interpreted as proportional values or absolute values in seconds. The number of envelopes generated is controlled by the eventCount parameter; envelopes are looped when necessary'

    _scaleCommonPlural = 'These values are scaled within the range designated by min and max; min and max may be specified with ParameterObjects.'

    _scaleAfter = 'After selection, this value is scaled within the range designated by min and max; min and max may be specified with ParameterObjects.'

    _controlFailure = 'if the control ParameterObject fails to produce positive values after many attempts, a value will be automatically generated from the selected ParameterObject'
    
    _symLinks = 'symbolic links (aliases or shortcuts) and home directory symbols (~) are expanded into complete paths'
    
    _waveValuePeriod = 'between 0 and 1 at a rate given in either time or events per period.'
    
    _waveSecondsPerCycle = 'Depending on the stepString argument, the period rate (frequency) may be specified in spc (seconds per cycle) or eps (events per cycle).'

    _waveCommon = '%s %s The phase argument is specified as a value between 0 and 1. Note: conventional cycles per second (cps or Hz) are not used for frequency.' % (_waveSecondsPerCycle, _scaleCommon)

    _waveSecondsPerCycleHalfPeriod = 'Depending on the stepString argument, the half-period rate (frequency) may be specified in spc (seconds per cycle) or eps (events per cycle).'

    _waveHalfPeriodCommon = '%s %s The phase argument is specified as a value between 0 and 1. Half-period oscillators update seconds/event per cycle only once per half-period, permitting smooth transitons between diverse half-period segments. Note: conventional cycles per second (cps or Hz) are not used for frequency.' % (_waveSecondsPerCycleHalfPeriod, _scaleCommon)


    _bpmIndependent = 'when using this Rhythm Generator, tempo information (bpm) has no effect on event timing'
    
    _sieveHeader = 'Using the user-supplied logical string, this Generator produces a Xenakis sieve segment within the z range of zero to one less than the supplied length.'

    _caHeader = 'One dimensional cellular automata may be standard, totalistic, continuous, or float formats, and are defined with a caSpec string. The caSpec string may contain one or more CA parameters defined in key{value} pairs. All parameters not defined assume default values. Valid parameters include f (format), k, r, i (initialization), x (row width), y (number of steps), w (extracted width), c (extracted center), and s (initial step skip). Rule and mutation values may be provided by embedded Generator ParameterObjects.'

    _tableExtract = 'Values may be extracted into a list from the resulting table as defined by the tableFormatString.'

    _maskFit = 'The fit is determined by the boundaryString: limit will fix the value at the nearest boundary; wrap will wrap the value through the range defined by the boundaries; reflect will bounce values in the opposite direction through the range defined by the boundaries.'

    _divisionByZeroFilter = 'Division by zero, if encountered, returns the value of the input value unaltered.'

    _divisionByZeroGenerator = 'Division by zero, if encountered, returns the value of the first Generator.'


    # doc strings
    
    docPoSah = 'A sample and hold generator. Produces, and continues to produce, a value drawn from the source Generator until the trigger Generator produces a value equal to the threshold Generator. All values are converted to floating-point values.'

    docPoSi = 'Supplies instrument number and orchestra name.'
    
    docPoSr = 'Supplies start and end time values. Start and end values are specified as a list of two values.'
    
    docPoCg = 'Cycles between static minimum (min) and maximum (max) values with a static increment value. Cycling direction and type is controlled by the directionString argument.'

    docPoTf = 'Convert the output of any ParameterObject into a different type or display format.'

    docPoC = 'Return a constant string or numeric value.'
    
    docPoBg = 'Chooses values from a user-supplied list (valueList). Values can be strings or numbers. %s' % _selectionStr

    docPoBs = 'Chooses values from a user-supplied list (valueList). Values can be strings or numbers. Values are choosen from the list with values within the unit interval produced by an embedded ParameterObject. Values that exceed the unit interval are limited within the unit interval.'

    docPoBf = 'Chooses values from a ParameterObject generated list of values. The number of values generated is determined by the valueCount integer. Valuse are generated only at initialization. %s' % _selectionStr

    docPoBfs = 'Chooses values from a ParameterObject generated list of values. The number of values generated is determined by the valueCount integer. Valuse are generated only at initialization. Values are choosen from the list with values within the unit interval produced by an embedded ParameterObject. Values that exceed the unit interval are limited within the unit interval.'

    docPoSl = 'Produces a Xenakis sieve as a raw, variable format sieve segment list. A z is defined by the range of integers from zMin to zMax. Depending on format type, the resulting segment can be given as an integer, width, unit, or binary segment. %s' % _selectionStr
    
    docPoVs = '%s %s %s %s' % (_sieveHeader, _normalizedList, 
                                        _selectionStr, _scaleAfter)

    docPoSf = '%s Values produced with the fill value Generator ParameterObject are funneled through this sieve: given a fill value, the nearest sieve value is selected and returned. Note: the fill value ParameterObject min and max should be set to 0 and 1.' % (_sieveHeader)
    
    docPoLp = 'Produces a segment of prime (pseudoprime) integers defined by a positive or negative start value and a length. Depending on format type, the resulting segment can be given as an integer, width, unit, or binary segment. %s' % _selectionStr

    docPoVp = 'Produces a segment of prime (pseudoprime) integers defined by a positive or negative start value and a length. %s %s %s' % (_normalizedList, _selectionStr, _scaleAfter)

    docPoCl = 'Produces values from a one-dimensional cellular automata table. %s %s %s' % (_caHeader, _tableExtract, _selectionStr)

    docPoCv = 'Produces values from a one-dimensional cellular automata table scaled within dynamic min and max values. %s %s %s %s' % (_caHeader, _tableExtract, _selectionStr, _scaleAfter)

    docPoGt = 'Produces values from a one-dimensional string rewrite rule, or Lindenmayer-system generative grammar. The terminus, or final result of the number of generations of values specifed by the stepCount parameter, is used to produce a list of defined values. %s' % ( _selectionStr)

    docPoFml = 'A model of a feedback system made from discrete particles. %s' % ( _scaleCommon)


    docPoPr = "Extracts pitch information from the current Multiset within a Texture's Path. Data can be presented in a variety of formats including representations of the Multiset as 'forte', 'mason', or data on the current active pitch as 'fq' (frequency), 'ps' (psReal), 'midi' (midi pitch values), 'pch' (Csound pitch octave format), or 'name' (alphabetic note names)."


    docPoLm = "Performs the logistic map, or the Verhulst population growth equation. The logistic map is a non-linear one-dimensional discrete deterministic dynamical system. %s Variable x represents the population value; value p represents a combined rate for reproduction and starvation. The p argument allows the user to provide a static or dynamic value to the equation. Certain p-value presets can be provided with strings: 'bi', 'quad', or 'chaos'. If a number is provided for p, the value will be used to create a constant ParameterObject. The equation outputs values within the unit interval. %s" % (_dyanmicalSystem, _scaleCommonPlural)
    
    docPoHb =  "Performs the Henon map, a non-linear two-dimensional discrete deterministic dynamical system. %s Variables x and y describe coordinate positions; values a (alpha) and b (beta) configure the system. As the output range cannot be predicted, as many values as specified by the valueCount argument, as well as any combination of variables with the valueSelect argument, are generated and stored at initialization. These values are then scaled within the unit interval. %s %s Note: some values may cause unexpected results; alpha values should not exceed 2.0." % (_dyanmicalSystem, _selectionStr, _scaleAfter) 
    
    docPoLb = "Performs the Lorenz attractor, a non-linear three-dimensional discrete deterministic dynamical system. The equations are derived from a simplified model of atmospheric convection rolls. %s Variables x, y, and z are proportional to convective intensity, temperature difference between descending and ascending currents, and the difference in vertical temperature profile from linearity. Values s (sigma), r, and b are the Prandtl number, the quotient of the Rayleigh number and the critical Rayleigh number, and the geometric factor. As the output range cannot be predicted, as many values as specified by the valueCount argument, as well as any combination of variables with the valueSelect argument, are generated and stored at initialization. These values are then scaled within the unit interval. %s %s Note: some values may cause unexpected results; r should not exceed 90." % (_dyanmicalSystem, _selectionStr, _scaleAfter)   
    
    
    docPoN = "Fractional noise (1/fn) Generator, capable of producing states and transitions between 1/f white, pink, brown, and black noise. Resolution is an integer that describes how many generators are used. The gamma argument determines what type of noise is created. All gamma values are treated as negative. A gamma of 0 is white noise; a gamma of 1 is pink noise; a gamma of 2 is brown noise; and anything greater is black noise. Gamma can be controlled by a dynamic ParameterObject. The value produced by the noise generator is scaled within the unit interval. This normalized value is then scaled within the range designated by min and max; min and max may be specified by ParameterObjects."
    
    docPoA = 'For each evaluation, this Generator adds the result of the Generator ParameterObject to the stored cumulative numeric value; the initialization value argument initValue is the origin of the cumulative value, and is the first value returned.'
    

    docPoM = 'Given values produced by two boundary ParameterObjects in parallel, the Generator ParameterObject value is fit within these values. %s' % (_maskFit)

    docPoMr = 'Given values produced by two boundary ParameterObjects in parallel, the Generator ParameterObject value is fit outside of these values. %s' % (_maskFit)

    docPoMs = "Given values produced by two boundary ParameterObjects in parallel, the Generator ParameterObject value is scaled within these values. A collection of values created by the Generator ParameterObject are stored. %s %s %s" % (_normalizedList, _selectionStr, _scaleAfter)




    _binaryFunnel = 'Given values produced by two boundary parameterObjects and a threshold ParameterObject, the output of a Generator ParameterObject value is shifted to one of the boundaries (or the threshold) depending on the relationship of the generated value to the threshold. If the generated value is equal to the threshold, the value may be shifted to the upper or lower value, or retain the threshold value.'
    
    docPoFb = 'A dynamic, two-part variable funnel. %s' % _binaryFunnel

    _iterateWindow = 'A numeric value from a control ParameterObject is used to determine the selected ParameterObject behavior. A positive value (rounded to the nearest integer) will cause the selected ParameterObject to produce that many new values. After output of these values, a new ParameterObject is selected. A negative value (rounded to the nearest integer) will cause the selected ParameterObject to generate and discard that many values, and force the selection of a new ParameterObject. A value equal to 0 is treated as a bypass, and forces the selection of a new ParameterObject. ParameterObject selection is determined with a string argument for a selection method. Note: %s.' % (_controlFailure)
    
    docPoIw = 'Allows a ParameterObject, selected from a list of ParameterObjects, to generate values, to skip values (a number of values are generated and discarded), or to bypass value generation. %s' % (_iterateWindow)

    docPoIrw = 'Allows a Rhythm ParameterObject, selected from a list of Rhythm ParameterObjects, to generate values, to skip values (a number of values are generated and discarded), or to bypass value generation. %s' % (_iterateWindow)
    
    
    _iterateGroup = 'A numeric value from a control ParameterObject is used to determine the source ParameterObject behavior. A positive value (rounded to the nearest integer) will cause the value provided by the source ParameterObject to be repeated that many times. After output of these values, a new control value is generated. A negative value (rounded to the nearest integer) will cause that many number of values to be generated and discarded from the source ParameterObject, and force the selection of a new control value. A value of 0 is treated as a bypass, and forces the selection of a new control value. Note: %s.' % (_controlFailure)
    
    docPoIg = 'Allows the output of a source ParameterObject to be grouped (a value is held and repeated a certain number of times), to be skipped (a number of values are generated and discarded), or to be bypassed. %s' % _iterateGroup

    docPoIrg = 'Allows the output of a source Rhythm ParameterObject to be grouped (a value is held and repeated a certain number of times), to be skipped (a number of values are generated and discarded), or to be bypassed. %s' % _iterateGroup
    


    _iterateHold = '%s A numeric value from a size ParameterObject is used to determine how many values are drawn from the source ParameterObject. A numeric value from a refresh count ParameterObject is used to determine how many events must pass before a new size value is drawn and the source ParameterObject is used to refill the stored list. A refresh value of zero, once encountered, will prohibit any further changes to the stored list. Note: if the size ParameterObject fails to produce a non-zero value for the first event, an alternative count value will be assigned.' % (_selectionStr)

    
    docPoIh = 'Allows a variable number of outputs from a source ParameterObject, collected and stored in a list, to be held and selected. %s' % (_iterateHold)

    docPoIs = 'Allows a variable number of outputs from a source ParameterObject, collected and stored in a list, to be selected with values within the unit interval produced by an embedded ParameterObject. Values that exceed the unit interval are limited within the unit interval. %s' % (_iterateHold)

    docPoIrh = 'Allows a variable number of outputs from a source Rhythm ParameterObject, collected and stored in a list, to be held and selected. %s' % (_iterateHold)
    
    docPoIc = 'Produces a single value cross faded between two values created by two Generator ParameterObjects in parallel. The cross fade is expressed as a number within the unit interval, where a value of zero is the output of the first Generator, a value of one is the output of the second Generator, and all other values are proportionally and linearly cross faded.'

    _quantize = 'For each value provided by the source ParameterObject, a grid is created. This grid is made by taking the number of steps specified by the stepCount integer from the step width Generator ParameterObject. The absolute value of these widths are used to create a grid above and below the reference value, with grid steps taken in order. The value provided by the source ParameterObject is found within this grid, and pulled to the nearest grid line. The degree of pull can be a dynamically allocated with a unit-interval quantize pull ParameterObject. A value of 1 forces all values to snap to the grid; a value of .5 will cause a weighted attraction.'
    
    docPoQ = 'Dynamic grid size and grid position quantization. %s' % _quantize
    
    docPoMv = 'Produces values by means of a Markov transition string specification and a dynamic transition order generator. %s' % _dynamicMarkovOrder
        
    docPoMga = 'Produces values by means of a Markov analysis of values provided by a source Generator ParameterObject; the analysis of these values is used with a dynamic transition order Generator to produce new values. The number of values drawn from the source Generator is specified with the valueCount argument. The maximum order of analysis is specified with the maxAnalysisOrder argument. %s' % _dynamicMarkovOrder 
    
    docPoOa = 'Adds the value of the first ParameterObject to the second ParameterObject.'
        
    docPoOs = 'Subtracts the value of the second ParameterObject from the first ParameterObject.'
    
    docPoOd = 'Divides the value of the first ParameterObject object by the second ParameterObject. %s' % _divisionByZeroGenerator
    
    docPoOm = 'Multiplies the value of the first ParameterObject by the second.'
    
    docPoOp = 'Raises the value of the first ParameterObject to the power of the second ParameterObject.'
    
    docPoOc = 'Produces the congruent value of the first ParameterObject object as the modulus of the second ParameterObject. A modulus by zero, if encountered, returns the value of the first ParameterObject unaltered.'

    docPoOo = 'Produces the value of one over the value of a ParameterObject. Divisors of zero are resolved to 1.'

    #-----------------------------------------------------------------------||--
    # omde pmtrObjects
    
    docPoWs = 'Provides sinusoid oscillation %s %s' % (_waveValuePeriod,
                                                           _waveCommon)    
    docPoWc = 'Provides cosinusoid oscillation %s %s' % (_waveValuePeriod,
                                                             _waveCommon)
    docPoWsu = 'Provides a saw-up wave %s %s' % (_waveValuePeriod, _waveCommon)
    docPoWsd = 'Provides a saw-down wave %s %s' % (_waveValuePeriod, _waveCommon)
    docPoWp = 'Provides a pulse (square) wave %s %s' % (_waveValuePeriod,
                                                        _waveCommon)
    docPoWt = 'Provides a triangle wave %s %s' % (_waveValuePeriod, _waveCommon)
    docPoWpu = 'Provides a power up wave %s %s' % (_waveValuePeriod, _waveCommon)
    docPoWpd = 'Provides a power down wave %s %s' % (_waveValuePeriod,
                                                            _waveCommon)
    
    docPoWhps = 'Provides half-period sinusoid oscillation %s %s' % (_waveValuePeriod, _waveHalfPeriodCommon)    
    docPoWhpc = 'Provides half-period cosinusoid oscillation %s %s' % (_waveValuePeriod, _waveHalfPeriodCommon)    
    docPoWhpp = 'Provides half-period pulse (square) wave oscillation %s %s' % (_waveValuePeriod, _waveHalfPeriodCommon)    
    docPoWhpt = 'Provides half-period triangle wave oscillation %s %s' % (_waveValuePeriod, _waveHalfPeriodCommon)    


    docPoRu = 'Provides random numbers between 0 and 1 within an uniform distribution. %s Note: values are evenly distributed between min and max.' % _scaleCommon
    docPoRl = 'Provides random numbers between 0 and 1 within a linearly decreasing distribution. %s Note: values are distributed more strongly toward min.' % _scaleCommon
    docPoRil = 'Provides random numbers between 0 and 1 within a linearly increasing distribution. %s Note: values are distributed more strongly toward max.' % _scaleCommon
    docPoRt = 'Provides random numbers between 0 and 1 within a triangular distribution. %s Note: values are distributed more strongly toward the mean of min and max.' % _scaleCommon
    docPoRit = 'Provides random numbers between 0 and 1 within an inverse triangular distribution. %s Note: values are distributed more strongly away from the mean of min and max.' % _scaleCommon
    
    docPoRe = 'Provides random numbers between 0 and 1 within an exponential distribution. %s Lambda values should be greater than 0. Lambda values control the spread of values; larger values (such as 10) increase the probability of events near the minimum.' % _scaleCommon
    docPoRie = 'Provides random numbers between 0 and 1 within an inverse exponential distribution. Lambda values control the spread of values; larger values (such as 10) increase the probability of events near the maximum. %s' % _scaleCommon
    docPoRbe = 'Provides random numbers between 0 and 1 within a bilateral exponential distribution. %s' % _scaleCommon
    
    docPoRg = 'Provides random numbers between 0 and 1 within a Gaussian distribution. %s Note: suggested values: mu = 0.5, sigma = 0.1.' % _scaleCommon
    docPoRc = 'Provides random numbers between 0 and 1 within a Cauchy distribution. %s Note: suggested values: alpha = 0.1, mu = 0.5.' % _scaleCommon
    docPoRb = 'Provides random numbers between 0 and 1 within a Beta distribution. %s Alpha and beta values should be between 0 and 1; small alpha and beta values (such as 0.1) increase the probability of events at the boundaries.' % _scaleCommon
    docPoRw = 'Provides random numbers between 0 and 1 within a Weibull distribution. %s Note: suggested values: alpha = 0.5, beta = 2.0.' % _scaleCommon



    docPoEgt = 'Generates a sequence of dynamic envelopes with durations controlled by a Generator Parameter Object. %s. %s' % (_envelopeCommon, _scaleEnvelope)

    docPoEga = 'Generates a sequence of dynamic envelopes with durations controlled by a Generator Parameter Object. %s. %s' % (_envelopeCommon, _scaleEnvelope)

    docPoEgu = 'Generates a sequence of dynamic envelopes with durations controlled by a Generator Parameter Object. %s. %s' % (_envelopeCommon, _scaleEnvelope)

    

    docPoFs = "Provides values derived from a contigous section of the Fibonacci series. A section is built from an initial value (start) and as many additional values as specified by the length argument. Negative length values reverse the direction of the series. %s %s %s" % (_normalizedList, _selectionStr, _scaleAfter)
    
    #-----------------------------------------------------------------------||--
    _bpCommon = 'from a list of (x,y) coordinate pairs (pointList). A step type (stepString) determines if x values in the pointList refer to events or real-time values. Interpolated y values are the output of the Generator. The edgeString argument determines if the break-point function loops, or is executed once at the given coordinates.'
    
    docPoBpl = 'Provides a break-point function with linear interpolation %s' % _bpCommon
    
    docPoBpp = 'Provides a break-point function with exponential interpolation %s The exponent argument may be any positive or negative numeric value.' % _bpCommon

    docPoBphc = 'Provides a break-point function with half-cosine interpolation %s' % _bpCommon

    docPoBpf = 'Provides a break-point function without interpolation %s' % _bpCommon
    
    #-----------------------------------------------------------------------||--
    _bgCommon = 'A list of (x,y) coordinate pairs is generated from two embedded Generator ParameterObjects. The number of generated pairs is determined by the count argument. A step type (stepString) determines if x values in the pointList refer to events or real-time values. Interpolated y values are the output of the Generator. The edgeString argument determines if the break-point function loops, or is executed once at the given coordinates.'
    
    docPoBgl = 'Provides a dynamic break-point function with linear interpolation. %s' % _bgCommon
    
    docPoBgp = 'Provides a dynamic break-point function with exponential interpolation. %s The exponent argument may be any positive or negative numeric value.' % _bgCommon

    docPoBghc = 'Provides a dynamic break-point function with half-cosine interpolation. %s The exponent argument may be any positive or negative numeric value.' % _bgCommon

    docPoBgf = 'Provides a dynamic break-point function without interpolation. %s' % _bgCommon


    docPoLs = 'Provides a dynamic line segment created from three embedded Generator ParameterObjects. Start and end values, taken from min and max generators, are used to create a line segment spaning the time or event distance provided by the secPerCycle argument. %s' % (_waveSecondsPerCycle)
    
    #-----------------------------------------------------------------------||--
    # file pmtrObjects
    
    docPoSs = "Given a list of file names (fileNameList), this Generator provides a complete file path to the file found within either the athenaCL/audio or the user-selected audio directory. %s" % _selectionStr
    
    docPoAs = "Given a list of file names (fileNameList), this Generator provides a complete file path to the file found within either the libATH/sadir or the user-selected sadir. %s" % _selectionStr
    
    docPoDs = 'Within a user-provided directory (directoryFilePath) and all sub-directories, this Generator finds all files named with a file extension that matches the fileExtension argument, and collects these complete file paths into a list. %s Note: the fileExtension argument string may not include a leading period (for example, use "aif", not ".aif"); %s.' % (_selectionStr, _symLinks)

    docPoCf = 'Given an absolute file path, a constant file path is returned as a string. Note: %s.' % _symLinks
    
    #-----------------------------------------------------------------------||--
    # rhythm parameter objects
    
    docPoBa = 'Deploys two Pulses based on event pitch selection. Every instance of the first pitch in the current set of a Texture\'s Path is assigned the second Pulse; all other pitches are assigned the first Pulse. Amplitude values of events that have been assigned the second pulse are increased by a scaling function.'
    
    docPoGr = "Uses a genetic algorithm to create rhythmic variants of a source rhythm. Crossover rate is a percentage, expressed within the unit interval, of genetic crossings that undergo crossover. Mutation rate is a percentage, expressed within the unit interval, of genetic crossings that undergo mutation. Elitism rate is a percentage, expressed within the unit interval, of the entire population that passes into the next population unchanged. All rhythms in the final population are added to a list. Pulses are chosen from this list using the selector specified by the control argument."
    
    docPoL = 'Deploys a fixed list of rhythms. Pulses are chosen from this list using the selector specified by the selectionString argument.'
    
    docPoCs = "Allows the use of a Generator ParameterObject to create rhythm durations. Values from this ParameterObject are interpreted as equal Pulse duration and sustain values in seconds. Accent values are fixed at 1. Note: %s." % (_bpmIndependent)
    
    docPoCst = "Allows the use of three Generator ParameterObjects to directly specify duration, sustain, and accent values. Values for duration and sustain are interpreted as values in seconds. Accent values must be between 0 and 1, where 0 is a measured silence and 1 is a fully sounding event. Note: %s." % (_bpmIndependent)
    
    docPoPs = "%s This sieve, as a binary or width segment, is interpreted as a pulse list. The length of each pulse and the presence of rests are determined by the user-provided Pulse object and the articulationString argument. An articulationString of 'attack' creates durations equal to the provided Pulse for every non-zero binary sieve segment value; an articulationString of 'sustain' creates durations equal to the Pulse times the sieve segment width, or the duration of all following rests until the next Pulse. %s" % (_sieveHeader, _selectionStr)
    
    docPoRs = '%s The resulting binary sieve segment is used to filter any non-rest Pulse sequence generated by a Rhythm ParameterObject. The sieve is interpreted as a mask upon the ordered positions of the generated list of Pulses, where a sieve value retains the Pulse at the corresponding position, and all other Pulses are converted to rests. Note: any rests in the generated Pulse sequence will be converted to non-rests before sieve filtering.' % (_sieveHeader)
    
    docPoMp = 'Produces Pulse sequences by means of a Markov transition string specification and a dynamic transition order generator. The Markov transition string must define symbols that specify valid Pulses. %s' % _dynamicMarkovOrder
    
    docPoMra = 'Produces Pulse sequences by means of a Markov analysis of a rhythm provided by a source Rhythm Generator ParameterObject; the analysis of these values is used with a dynamic transition order Generator to produce new values. The number of values drawn from the source Rhythm Generator is specified with the pulseCount argument. The maximum order of analysis is specified with the maxAnalysisOrder argument. %s' % _dynamicMarkovOrder     

    docPoPt = 'Produces Pulse sequences with four Generator ParameterObjects that directly specify Pulse triple values and a sustain scalar. The Generators specify Pulse divisor, multiplier, accent, and sustain scalar. Floating-point divisor and multiplier values are treated as probabilistic weightings. Note: divisor and multiplier values of 0 are not permitted and are replaced by 1; the absolute value is taken of all values.'

    #-----------------------------------------------------------------------||--
    # filter parameter objects    
    
    docPoB = 'Each input value is returned unaltered.'
    
    docPoOb = 'All values input are returned in reversed order.'
    
    docPoOr = 'Rotates all input values as many steps as specified; if the number of steps is greater than the number of input values, the modulus of the input length is used.'
    
    docPoPl = 'Provide a list of Filter ParameterObjects; input values are passed through each filter in the user-supplied order from left to right.'
    
    docPoR = 'Replace input values with values produced by a Generator ParameterObject.'
    
    docPoFa = 'Each input value is added to a value produced by a user-supplied ParameterObject.'

    docPoFm = 'Each input value is multiplied by a value produced by a user-supplied ParameterObject.'

    docPoFd = 'Each input value is divided by a value produced by a user-supplied ParameterObject. %s' % _divisionByZeroFilter

    docPoFp = 'Each input value is taken to the power of the value produced by a user-supplied ParameterObject.'
    
    _anchorTemplate = 'All input values are first shifted so that the position specified by anchor is zero; then each value is %s by the value produced by the parameterObject. All values are then re-shifted so that zero returns to its former position.'

    docPoFma = _anchorTemplate % 'multiplied'

    docPoFda = _anchorTemplate % 'divided' + ' %s' % _divisionByZeroFilter
    
    docPoFfb = 'A dynamic, two-part variable funnel filter. %s' % _binaryFunnel
    
    docPoFq = 'Dynamic grid size and grid position quantization filter. %s' % _quantize
    
    docPoMf = 'Each input value is fit between values provided by two boundary Generator ParameterObjects. %s' % (_maskFit)

    docPoMsf = 'Each input value is collected into a list. %s %s %s' % (_normalizedList, _selectionStr, _scaleAfter)

    #-----------------------------------------------------------------------||--
    # static parameter objects
    docPoPml = 'List is a collection of transpositions created above every Texture-generated base note. The timeDelay value determines the amount of time in seconds between each successive transposition in the transpositionList.'
     
    docPoOls = 'Selects a library of ornaments to use with a Texture.'
    
    docPoOmd = 'Controls maximum percent of events that are ornamented. Density value should be specified within the unit interval.'
     
    docPoMto = 'Used to select an offset time in seconds. Offset is applied with the absolute value of a gaussian distribution after the Texture-generated event start time.'
     
    docPoNrs = 'Toggle selection of pitches between either random selection or random permutation.'
     
    docPoLws = 'Controls if pitches in a set are repeated by a Texture within the set\'s duration fraction.'
     
    docPoPdf = 'Toggle Path duration fraction; if off, Path duration fractions are not used to partition Path deployment over the duration of the Texture. Instead, each Path set is used to create a single event.'

    docPoSst = 'Controls if all event sustain values are scaled to the frame width.'

    docPoSet = 'Controls if all event start times are shifted to align with frame divisions.'

    docPoLfm = "Toggle between selection of local field (transposition) values per set of the Texture Path, or per event."
     
    docPoLom = "Toggle between selection of local octave (transposition) values per set of the Texture Path, or per event."
     
    docPoLfp = "Toggle between selection of local field (transposition) values per set of the Texture Path, per event, or per polyphonic voice event."
     
    docPoLop = "Toggle between selection of local octave (transposition) values per set of the Texture Path, per event, or per polyphonic voice event."
    
    docPoTrs = 'Selects time reference source used in calculating ParameterObjects.'
     
    docPoRmt = 'Selects type of retrograde transformation applied to Texture events.'

    docPoTec = 'Selects the total number of events generated within the Texture time range.'

    docPoLep = "Toggle between selection of event start time per set of the Texture Path, or per Path. This control will determine if the event generator is mapped within the Texture time range, or within the set time range. When set to path, this control will over-ride event density partitioning."
    # either divide e number of events by number of sets, or scale by dur
    # fractions

    docPoLfd = "Toggle between selection of frame duration values per frame or per event."

    docPoPic = "Controls if all non-duration parameter values are interpolated between events."


    docPoPsc = 'Define the selector method of Path pitch selection used by a Texture.'

    docPoMsc = 'Define the selector method of Multiset selection within a Path used by a Texture.'
     
    docPoEdp = 'Define how event count is distributed within a Texture, either proportional to path duration or equal proportion per path set.'

    docPoLec = 'Define at what level event count values are generated: once per Texture for the total event count (with a distribution per segment proportional to segment duration), or once per segment for each segment event count.'

    docPoTsc = "Set the number of segments with which to divide the Texture's duration."
     
    docPoImc = 'Selects the type of interpolation used for all parameters.'

    
    def __init__(self): 
        """
        >>> a = LangEn()
        """
        pass



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)




