#-----------------------------------------------------------------||||||||||||--
# Name:          dialog.py
# Purpose:       cross platform dialogs
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import sys, os, time, random
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import typeset
from athenaCL.libATH import language
lang = language.LangObj()

# this module is higher than drawer and typeset

_MOD = 'dialog.py'

#-----------------------------------------------------------------||||||||||||--
# gui, graphics quaries

def autoDlgMethod():
    """auto-detects which guis are available and selects one
    used when a dialog method is called without specifying
    which gui to use. acts as default selector (does _not_ use preference)
    """
    if os.name == 'mac':
        carbon = drawer.isCarbon()
        if carbon: # macfs or carbon is available
            dlgVisualMethod = 'mac'
        else: #-1 , use text
            dlgVisualMethod = 'text'
    elif os.name == 'posix':
        visMethods = drawer.imageFormats()
        if 'tk' in visMethods:
            dlgVisualMethod = 'tk'
        else:
            dlgVisualMethod = 'text'
    else:    # all windows flavors
        visMethods = drawer.imageFormats()
        if 'tk' in visMethods:
            dlgVisualMethod = 'tk'
        else:
            dlgVisualMethod = 'text'
    return dlgVisualMethod


def _fixQuery(query):
    """query strings need to end with a space; this makes sure they do
    choice can be none, or a list of options to be appended after query
    in paranthessis"""
    if query != '':
        if query[-1] != ' ': # add space if missing
            query = query + ' '
    return query
    
#-----------------------------------------------------------------||||||||||||--
# general dialogs

def msgOut(msg, termObj=None):
    """almost all text outputted to user goes through this fuction
    general filter for all text display
    athenaCmd.Interpreter.out uses this f to output main text
    other command in Interpreter use sys.stdout
    """
    if termObj != None: # all athenacl sessions have a termObj
        h, w = termObj.size()# fit to terminal
        msg = typeset.wrapText(msg, w, 0, 'line')
    if termObj != None:
        if termObj.sessionType == 'cgi': # dont want any output
            return # do nothing, nothing to stdout, str taken elsewhere
    sys.stdout.write(msg)

def msgError(msg, termObj=None):
    """almost all text outputted to user goes through this fuction
    general filter for all text display
    athenaCmd.Interpreter.out uses this f to output main text
    other command in Interpreter use sys.stdout
    """
    if termObj != None: # all athenacl sessions have a termObj
        h, w = termObj.size()# fit to terminal
        msg = typeset.wrapText(msg, w, 0, 'line')
    if termObj != None:
        if termObj.sessionType == 'cgi': # dont want any output
            return # do nothing, nothing to stderr, str taken elsewhere
    sys.stderr.write(msg)
    
def rawInput(prompt, termObj=None):
    """use this to replace built-in raw-input, as this provides
    line wrapping on the query message if possible"""
    if termObj != None: # all athenacl sessions have a termObj
        h, w = termObj.size()# fit to terminal
        prompt = typeset.wrapText(prompt, w, 0, 'line')
    # line wraping may remove the last space after prompt; make sure it is 
    # still there
    return raw_input(_fixQuery(prompt))

#-----------------------------------------------------------------||||||||||||--

def askStr(query, termObj=None, strip=1):
    """function for requesting a string from user
    strip turns off character stripping
    returns None on error given and strip is true (does not return '')
    """
    if termObj != None:
        sessionType = termObj.sessionType
    else:
        sessionType = 'terminal'
    # TypeError raised when object.readline() returned non-string
    try:
        answer = rawInput(query, termObj)
    except (KeyboardInterrupt, EOFError, TypeError):
        return None # cancel
    if strip:
        answer = answer.strip()
    if answer == '' or answer == None:
        return None
    else:
        return answer

def askYesNoCancel(query, defaultSel=1, termObj=None):
    """function for querying user yes, no, or cancel
    returns 1 for yes, 0 for no, -1 for cancel
    """
    if termObj != None:
        sessionType = termObj.sessionType
    else:
        sessionType = 'terminal'
    # need to fix query before appending
    query = _fixQuery(query)
    qString = query + '(y, n, or cancel): '
    if sessionType in ['terminal', 'idle', 'gui-tk']:
        status = -2 # place holder
        while 1:
            try:
                aString = rawInput(qString, termObj)
            except (KeyboardInterrupt, EOFError, TypeError):
                status = -1 # cancel
                break
            status = typeset.convertBoolCancel(aString)
            if status != None:
                break # status set to 0, 1, -1
            else:
                msgOut(lang.msgConfusedInput)
                continue
    return status

def askYesNo(query, defaultSel=1, termObj=None):
    """function for querying user yes, no
    returns 1 for yes, 0 for no
    """
    if termObj != None:
        sessionType = termObj.sessionType
    else:
        sessionType = 'terminal'
    query = _fixQuery(query)
    qString = query + '(y or n): '
    if sessionType in ['terminal', 'idle', 'gui-tk']:
        status = None # place holder
        while 1: # 1 for yes, 0 for no
            try:
                aString = rawInput(qString, termObj)
            except (KeyboardInterrupt, EOFError, TypeError):
                status = 0 # cancel
                break
            status = typeset.convertBool(aString)
            if status != None: # an error:
                break # status set to 0, 1
            else:
                msgOut(lang.msgConfusedInput)
                continue
    return status



#-----------------------------------------------------------------||||||||||||--
# mac gui file dialogs

def _macGetDirectory(prompt='select a directory'):
    carbon = drawer.isCarbon()
    if carbon:
        import EasyDialogs
        path = EasyDialogs.AskFolder(message=prompt)
        if path == None: return '', 0
        else: return path, 1
    else:
        import macfs
        fsspec, ok = macfs.GetDirectory(prompt)
        if ok != 1:
            return '', 0 # failure
        path = fsspec.as_pathname()
        drawer.pathScrub(path)
        return path, 1

def _macPutFile(prompt='save a file', defaultName='test.txt', defaultDir=None):
    carbon = drawer.isCarbon()
    if carbon:
        import EasyDialogs
        path = EasyDialogs.AskFileForSave(message=prompt, 
                                        savedFileName=defaultName)
        if path == None: return '', 0
        else: return path, 1
    else:
        import macfs
        fsspec, ok = macfs.PromptPutFile(prompt, defaultName)
        if ok != 1:
            return '', 0
        path = fsspec.as_pathname()
        ## check extension, add if missing
        path = drawer.pathScrub(path)
        return path, 1

def _macGetFile(prompt='pick a file', defaultDir=None):
    carbon = drawer.isCarbon()
    if carbon:
        import EasyDialogs
        path = EasyDialogs.AskFileForOpen(message=prompt)
        if path == None: return '', 0
        else: return path, 1
    else:
        import macfs
        fsspec, ok = macfs.PromptGetFile(prompt)
        if ok != 1: return '', 0 # failure
        path = fsspec.as_pathname()
        path = drawer.pathScrub(path)
        return path, 1

#-----------------------------------------------------------------||||||||||||--
# general files service functions

def _textGetDirectory(prompt='select a directory: ', sampleDir='',
                             termObj=None):
    """this method allows the user to select a directory using a text
    based interface.
    """
    if sampleDir != '':
        currentDir = sampleDir
    elif drawer.getcwd() != None:
        currentDir = drawer.getcwd()
    elif drawer.getud() != None:
        currentDir = drawer.getud()
    else: currentDir = ''       
    currentDir = drawer.pathScrub(currentDir)

    while 1:
        cwdContents = os.listdir(currentDir)
        maxLength = 0
        for fName in cwdContents:
            if len(fName) >= maxLength:
                maxLength = len(fName)
        maxLength = maxLength + 2 # add two spaces of buffer
        header = '%s' % currentDir #delete extra space here

        if termObj == None: # update termwidth
            termWidth = 80 # default
        else:
            h, termWidth = termObj.size()

        msg = typeset.formatEqCol(header, cwdContents, maxLength, 
                                        termWidth, 'off')
        msgOut((msg + prompt), termObj) # dont want extra return
        usrStr = askStr(lang.msgMenuChangeDir, termObj)
        finalPath = '' # keep empty until cmds parsed
        # scan for each of the options
        if usrStr == None: continue # bad input
        if usrStr.lower() == 's': # if entry is s, return cwd
            finalPath = currentDir # selected, asuign to final
        if usrStr == '..': # up one dir, display
            pathValid = os.path.exists(currentDir)
            currentDir = os.path.dirname(currentDir)
            continue
        if finalPath == '': # still not asigned, check if its a path
            downDir = os.path.join(currentDir, usrStr)
            downDir = drawer.pathScrub(downDir) # assume this is a dir
            cwdContents = os.listdir(currentDir)
            if usrStr in cwdContents:
                if os.path.isdir(downDir) != 1: # if not a dir
                    continue
                else: # is a dir
                    currentDir = downDir # make downDir current, back to top
                    continue
        if finalPath == '': #user has entered a abs path
            absPath = drawer.pathScrub(usrStr)
            ### resolve aliases here!
            if os.path.exists(absPath) and os.path.isdir(absPath): 
                currentDir = absPath # this is a dir, same as selecting a dir
                continue
        if finalPath == '': # not assigned yet
            if usrStr.lower() == 'c':
                return '', 0 # canceled
            else: # bad input, continue
                msgOut((lang.msgDlgBadInput % usrStr), termObj)
                continue
        if not os.path.exists(finalPath): # if doesnt exist
            status = askYesNo(lang.msgDlgBadPath, 1, termObj)
            if status != 1:
                return '', 0 # cancle msg
            else: continue
        else: # its good
            finalPath = drawer.pathScrub(finalPath)
            return finalPath, 1


def promptGetDir(prompt='select a directory:', sampleDir='', 
                                 dlgVisualMethod=None, termObj=None):
    """multi platform/gui methods for optaining a directory
    text based version displays dir listings
    """
    if dlgVisualMethod == None: # test for vis method if not provided
        dlgVisualMethod = autoDlgMethod()
    # check for bad directories
    if sampleDir != '': pass # used as default dir selection
    elif drawer.getcwd() != None:
        sampleDir = drawer.getcwd()
    elif drawer.getud() != None:
        sampleDir = drawer.getud()
    else: sampleDir = ''
    sampleDir = drawer.pathScrub(sampleDir)
    
    pathToFile = None # empty until defined
    # platform specific file dialogs.
    if dlgVisualMethod == 'mac':
        try:
            path, stat = _macGetDirectory(prompt)
            return path, stat
        except:
            print lang.msgDlgMacError

    # platform specific file dialogs.
    if dlgVisualMethod[:2] == 'tk':
        try:
            import Tkinter
            import tkFileDialog
            TK = 1
        except ImportError:
            TK = 0
            print lang.msgDlgTkError

    if dlgVisualMethod[:2] == 'tk' and TK == 1:
        tkTemp = Tkinter.Tk()
        tkTemp.withdraw()
        ## "dir" only shows directories, but are unable to select 
        options = {'filetypes':[("directory", "*")], 
                        'title'   : prompt,      
                        'parent'      : tkTemp}
        # need to check if defaultDir still exists
        if os.path.isdir(sampleDir):
            options['initialdir'] = sampleDir
            
        guiTemp = tkFileDialog.Open()
        guiTemp.options = options
        # filename = apply(tkFileDialog.Open, (), options).show(
        try:
            pathToFile = guiTemp.show() 
            del guiTemp # clean up gui mess
            tkTemp.destroy()
        except: # tk broke somehow
            pass
        # return path
        if pathToFile not in ['', None] and drawer.isStr(pathToFile):
            pathToFile = os.path.dirname(pathToFile)    # remove file name
            pathToFile = drawer.pathScrub(pathToFile)
            return pathToFile, 1
        elif pathToFile == None: # if not set yet, something went wrong
            pass                 # fall below to text based
        else:
            return '', 0
    # for all other platforms, dlgVisualMethod == text
    try:
        msg, ok = _textGetDirectory(prompt, sampleDir, termObj)
    except (OSError, IOError): # catch file errors, or dirs called tt dont exist
        msg = '' # this is usually the path itself
        ok = 0
    return msg, ok

#-----------------------------------------------------------------||||||||||||--
def _textPutFile(prompt='name this file:', defaultName='name', defaultDir='',
                      extension='*', dlgVisualMethod='text', termObj=None):
    """text based ui for getting a file to save"""
    finalPath = ''
    status = -2 # init value
    # check if dir has been cleared, recheck
    if defaultDir != '': # used as default dir selection
        directory = defaultDir
    elif drawer.getcwd() != None:
        directory = drawer.getcwd()
    elif drawer.getud() != None:
        directory = drawer.getud()
    else: directory = ''
    
    directory = drawer.pathScrub(directory)
    while 1:
        usrStr = askStr(prompt, termObj) # get file name
        if usrStr == None:
            return None, -1 # error
        # check for bad chars in fileName
        if usrStr[0] not in lang.IDENTCHARS:
            msgOut(lang.msgDlgBadFileNameStart % usrStr[0], termObj)
            return None, -1 # error
        for char in usrStr:
            if char not in lang.FILECHARS:
                msgOut(lang.msgDlgBadFileNameChar % char, termObj)
                return None, -1

        # get directory
        status = askYesNoCancel((lang.msgDlgSaveInThisDir % directory), termObj)
        if status == -1:    #cancel
            break
        if status == 0: #no, get new directory
            path, ok = promptGetDir('', directory, dlgVisualMethod, termObj)
            if ok != 1:
                status = -1
                break
            else:
                directory = path
                status = 1
        if status == 1: # test for existing file 
            dirContent = os.listdir(directory)
            if usrStr in dirContent:
                ok = askYesNoCancel(lang.msgDlgFileExists, termObj)
                if ok != 1: continue
        finalPath = os.path.join(directory, usrStr)
        finalPath = drawer.pathScrub(finalPath)
        ok = askYesNoCancel((lang.msgDlgSaveThisFile % finalPath), termObj)
        if ok == -1:
            status = -1
            break
        elif ok == 0:
            continue
        elif ok == 1:
            status = 1
            break
    return finalPath, status


def promptPutFile(prompt='name this file:', defaultName='name', 
                defaultDir='', extension='*', dlgVisualMethod=None, termObj=None):
    """multi platform/gui methods for selecting a file to write to
    text version allows user to browse file system
    """
    if dlgVisualMethod == None: # test for vis method if not provided
        dlgVisualMethod = autoDlgMethod()
    path = None # empty until defined

    # platform specific file dialogs.
    if dlgVisualMethod == 'mac':
        stat = 0
        try:
            path, stat = _macPutFile(prompt, defaultName, defaultDir)
            return path, stat
        except: # will be MacOS.Error but must import MacOS to select?
            print lang.msgDlgMacError

    # platform specific file dialogs.
    if dlgVisualMethod[:2] == 'tk':
        try:
            import Tkinter
            import tkFileDialog
            TK = 1
        except ImportError:
            TK = 0
            print lang.msgDlgTkError

    if dlgVisualMethod[:2] == 'tk' and TK == 1:
        tkTemp = Tkinter.Tk()
        tkTemp.withdraw()
        # put extension here, but dont know if i need period or not
        options = {'filetypes':[("all files", "*")],    
                        'title'   : prompt,      
                        'parent'      : tkTemp}
        # need to check if directory still exists
        if os.path.isdir(defaultDir):
            options['initialdir'] = defaultDir
                        
        guiTemp = tkFileDialog.SaveAs()
        guiTemp.options = options
        # filename = apply(tkFileDialog.Open, (), options).show(
        try:
            path = guiTemp.show()
            del guiTemp # clean up gui mess
            tkTemp.destroy()    # return path
        except: pass # tk broke somehow
        if path not in ['', None] and drawer.isStr(path):
            path = drawer.pathScrub(path)
            return path, 1
        # may be problem here with a keyboard interupt exception
        #elif path == None: # if not set yet, something went wrong
        #    pass                 # fall below to text based
        else:
            return '', 0

    # for all other platforms
    try:
        msg, ok = _textPutFile(prompt, defaultName, defaultDir, extension, 
                                  dlgVisualMethod, termObj)
    except (OSError, IOError): # catch file errors, or dirs called tt dont exist
        msg = '' # this is usually the path itself
        ok = 0
    return msg, ok

#-----------------------------------------------------------------||||||||||||--
def _textGetFile(prompt='select a file', defaultDir='', mode='file',
                      dlgVisualMethod='text', termObj=None):
    """text based ui for user selection of files; can optionally be used
    to get applications; this is tricky as sometimes apps are folders, not files
    mode can either be file or app
    """
    finalPath = ''
    if defaultDir != '': # used as default dir selection
        directory = defaultDir
    elif drawer.getcwd() != None:
        directory = drawer.getcwd()
    elif drawer.getud() != None:
        directory = drawer.getud()
    else: directory = ''
    directory = drawer.pathScrub(directory)

    while 1:
        header = '\n%s' % directory
        msgOut('%s\n' % prompt, termObj)
        usrStr = askStr(lang.msgMenuFile, termObj)
        if usrStr == None: return None, -1 # cancel
        # check first for a complete path
        elif os.path.isfile(drawer.pathScrub(usrStr)):
            status = 1
            finalPath = drawer.pathScrub(usrStr)
        elif usrStr.lower() == 'cd': # change directory
            path, ok = promptGetDir('', directory, dlgVisualMethod, termObj)
            if not ok: # error
                status = -1
                break # cancel entire session
            else:
                directory = path
                continue
        elif usrStr.lower() == 'c': # cancel selected
            return None, -1 # cancel
        else:
            if usrStr.lower() != 'f':
                msgOut(lang.msgConfusedInput, termObj)
                continue
            status = 0 # reinit status flag
            while 1: # file selection loop
                name = askStr(lang.msgDlgNameFile, termObj)
                if name == None: return None, -1 # will cancel
                # if an application, filter path before testing
                if mode == 'app':
                    name = drawer.appPathFilter(name)
                # check first if this is an absolute file path, accept if so
                if ((os.path.isabs(name) and mode == 'file' and 
                    not os.path.isdir(name) and os.path.exists(name)) or 
                    (os.path.isabs(name) and mode == 'app' and 
                    drawer.isApp(name) and os.path.exists(name))):
                    finalPath = name
                    break
                # else see if name is in dir; cant adjust name for apps here
                # must assume that they are displayed to e user in w/ extension
                elif name in os.listdir(directory):
                    fp = os.path.join(directory, name)
                    # check: if a dir or not app, fail
                    if ((mode == 'file' and os.path.isdir(fp)) or
                        (mode == 'app' and not drawer.isApp(fp))): 
                        if mode == 'file':  
                            errorMsg = lang.msgDlgDirNotFile
                        elif mode == 'app':
                            errorMsg = lang.msgDlgNotApp
                        ok = askYesNo(errorMsg, 1, termObj)
                        if ok: continue
                        elif not ok:
                            status = -2
                            break
                    finalPath = fp
                    break
                else: # not in this directory
                    ok = askYesNoCancel(lang.msgDlgBadFileName, termObj)
                    if ok: continue
                    elif not ok:
                        status = -2 # wil continue
                        break
                    else: break
        if status == -2: continue
        # final check
        if finalPath == '':
            status = -1
            break
        else: # final check
            query = lang.msgDlgSelectThisFile % finalPath
            ok = askYesNoCancel(query, termObj)
            if ok == -1: # cancel selection
                status = -1
                break
            elif ok == 0: continue # no, retry
            elif ok:
                status = 1
                break
    finalPath = drawer.pathScrub(finalPath)
    return finalPath, status            


def promptGetFile(prompt='select a file', defaultDir='', mode='file',
                                 dlgVisualMethod=None, termObj=None):
    """multi platform/gui methods for selecting file to open
    text version allowes user to browse file system
    mode can be either filr or app, to allow application selection
        this is only explicitly necessary in text-based file selection
    """

    if dlgVisualMethod == None: # test for vis method if not provided
        dlgVisualMethod = autoDlgMethod()

    if defaultDir != '': pass # used as default dir selection
    elif drawer.getcwd() != None:
        defaultDir = drawer.getcwd()
    elif drawer.getud() != None:
        defaultDir = drawer.getud()
    else: defaultDir = ''
    defaultDir = drawer.pathScrub(defaultDir)
            
    path = None # empty until defined
    # platform specific file dialogs.
    if dlgVisualMethod == 'mac':
        try:
            path, stat = _macGetFile(prompt, defaultDir)
            return path, stat
        except:
            print lang.msgDlgMacError

    # platform specific file dialogs.
    if dlgVisualMethod[:2] == 'tk':
        try:
            import Tkinter
            import tkFileDialog
            TK = 1
        except ImportError:
            TK = 0
            print lang.msgDlgTkError

    if dlgVisualMethod[:2] == 'tk' and TK:
        tkTemp = Tkinter.Tk()
        tkTemp.withdraw()
        options = {'filetypes':[("all files", "*")], 
                        'title'   : prompt,      
                        'parent'      : tkTemp}
        # need to check if defaultDir still exists
        if os.path.isdir(defaultDir):
            options['initialdir'] = defaultDir
        
        guiTemp = tkFileDialog.Open()
        guiTemp.options = options
        # filename = apply(tkFileDialog.Open, (), options).show(
        try:
            path = guiTemp.show()
            # clean up gui mess
            del guiTemp
            tkTemp.destroy()
        except: pass # tk broke somehow
        if path not in ['', None] and drawer.isStr(path):
            path = drawer.pathScrub(path)
            return path, 1
        # may be problem here with a keyboard interupt exception
        #elif path == None: # if not set yet, something went wrong
        #    pass                 # fall below to text based
        else:
            return '', 0 # failure 

    # for all other platforms, dlgVisualMethod == text
    try:
        msg, ok = _textGetFile(prompt, defaultDir, mode, dlgVisualMethod, termObj)
    except (OSError, IOError): # catch file errors, or dirs called tt dont exist
        msg = '' # this is usually the path itself
        ok = 0
    return msg, ok           


#-----------------------------------------------------------------||||||||||||--
# def getSalutation(cursorToolConvert):
#     """selects a welcom message based on time of day
#     cursor tool convert is a dictionary of strings used to make cursor
#     can customized by the user
#     if no cursor is displayed, no prompts are displayed
#     """
#     timeTuple = time.localtime()
#     localYear = timeTuple[0]
#     localMonth = timeTuple[1]
#     localDay     = timeTuple[2]
#     localHour = timeTuple[3]
#     localMin     = timeTuple[4]
#     localSec     = timeTuple[5]
# 
#     if localHour >= 3 and localHour < 5:
#         salutation = lang.salutationAm1
#     elif localHour >= 5 and localHour < 12:
#         salutation = lang.salutationAm2
#     elif localHour >= 12 and localHour < 17:
#         salutation = lang.salutationPm1
#     elif localHour >= 17 and localHour < 22:
#         salutation = lang.salutationPm2
#     elif localHour >= 22 and localHour < 24:
#         salutation = lang.salutationPm3
#     elif localHour >= 0 and localHour < 3:
#         salutation = lang.salutationAm0
#     
#     # provide exceptions for special times
#     if localMonth == lang.BIRTH[1] and localDay == lang.BIRTH[2]:
#         age = abs(localYear - lang.BIRTH[0])
#         salutation = lang.salutationBirth % age
# 
#     if localSec % 13 == 0: # 13, 26, 39, 52, use salutation
#         cursTool = cursorToolConvert['['] + salutation + cursorToolConvert[']']
#     else: # provide a blank cursor (cursor tool may not be displayed)
#         cursTool = cursorToolConvert['empty'] % ('','') # must fill with empty str
#     return cursTool

def getEncouragement():
    options = [lang.provoke1, lang.provoke2, lang.provoke3, 
                  lang.provoke4, lang.provoke5, lang.provoke6, ]
    str = '%s enter "help"\n' % random.choice(options)
    return str

def getAdmonishment(line):
    options = [lang.admonish1, lang.admonish2, lang.admonish3, 
                  lang.admonish4, lang.admonish5, lang.admonish6, ]
    str = random.choice(options) % line # line is usr str
    str = '%s\n' % str 
    return str



#-----------------------------------------------------------------||||||||||||--
# this needs to be moved
# and needs to be adapted to use rhythm.Timer()
# might be best placed in command.py

def getTempo():
    """simple method for getting tempos from the user.
    based in part on code by Paul Winkler
    note: this uses raw_input; should use standard dialogs"""
    
    exit = 0
    while exit == 0:
        sys.stdout.write('tap a beat with the return key. enter "q" followed by a return key to end.')
        times = [] # save the time when keys are pressed.
        diffs = []
        i = 0
        while 1:
            c = raw_input('')
            when = time.time()
            if c.find("q") >= 0:
                break
            else:
                times.append(when)
                if i >= 1:
                    diffs.append(times[i] - times[i-1])
                    estimate = 60.0 / diffs[i-1] 
                    sys.stdout.write("  (%.2f s/beat)    " % (when-times[i-1]))
                else:
                    sys.stdout.write("  (%.2f s/beat)    " % 0)
                i = i + 1

        # watch for division by zero errors
        if len(diffs) == 0:
            return None, None
        sum = 0
        for d in diffs:
             sum = sum + d
        avgBeatT = sum / len(diffs)
        avgTempo = 60.0 / avgBeatT
        print "average tempo %.2f BPM (%.2f s/beat)" % (avgTempo, avgBeatT)
        q_string = "    keep, repeat, or cancel? (k, r, or c): "
        usrStr = raw_input(q_string)
        usrStr = usrStr.lower()
        if usrStr == '' or usrStr == None:
            exit = 1 #keep, dont cancel
        if usrStr.find('k') >= 0:
            exit = 1 #xits loop
        elif usrStr.find('r') >= 0:
            exit = 0 # repeats loop
        elif usrStr.find('c') >= 0:
            return None, None
    
    return avgTempo, avgBeatT


#-----------------------------------------------------------------||||||||||||--
# class Animate:
#     """string animation
#     this points out that print displays immediatly only if 
#     when carriage return is encountered
#     print ignores \b, must use stdout
#     stdout.write display no result until after process
#     note: this does not work in IDLE
#     this is never called from within a cgi sessions, as cgi sessions
#     are always single threaded
#     """
#     def __init__(self, termObj=None, mode='normal'):
#         """setup frame rate"""
#         self.chars = ('  ', 
#                           ': ', 
#                           '::', 
#                           ' :',
#                           '  ',) 
#         # idle does not execute /b
#         # w/o erase, give warning message if process > tToWarn
#         self.mode = mode # normal or minimal
#         self.warnGiven   = 0 # boolean for if init warning has been given
#         self.tToWarn     = 4 # seconds before givimg message to usr
#         self.tMsgPeriod = 8 # seconds before givimg message after first
#         # keep time, need to be cleard after use
#         self.index = 0   # counts frames
#         self.tStart = 0.0 # holds start time 
#         self.tLastPeriod = 0.0# used to count chunks
#         self.strLast = '' # string printed in last frame
#         self.pollCount = 0 # number of times draw has been called, one per poll
#         self.pollModulo = 10 # number of polls per display
#             # higher numbers reduce quality of animation, but on terms that
#             # \b fakes, reduces amount of garbage on screen
#         # width is platform dependent
#         if termObj == None: # update termwidth
#             w = 80 # default
#         else:
#             h, w = termObj.size()
#             if termObj.sessionType in ['idle', 'cgi']: 
#                 # idle and cgi never use threading, so minimal mode is not called
#                 self.mode = 'minimal' # cant back space
#         self.w = w # may be overridden
# 
#     def reset(self):
#         self.index = 0   
#         self.tStart = 0.0
#         self.tElap = 0.0
#         self.strLast = ''
#         self.warnGiven = 0 
# 
#     def setStart(self):
#         "stores a time in seconds"
#         self.tStart = time.time()
#             
#     def clearFrame(self):
#         """attempt to erase the last line printed, including the return carriage
#         """
#         if self.tElap > self.tToWarn: # after 10 sec, give a warning
#             if os.name == 'mac':
#                 # mac (os9 classic) does not measure whole line, but last str
#                 w = len(self.strLast) + 1 # add return carriage
#             elif os.name == 'posix':
#                 w = self.w
#             else:    # all windows flavors
#                 w = self.w
#     
#             if self.mode == 'minimal':
#                 pass # erase fails, skip
#             else:
#                 if self.pollCount % self.pollModulo == 0:
#                     sys.stdout.write('\b' * w)
#                     sys.stdout.write(' '     * w)
#                     sys.stdout.write('\b' * w)
# 
#     def printFrame(self):
#         """writes frame, advances counters"""
#         # dont do anything unitl after timeTowWarn
#         self.tElap = int(round((time.time() - self.tStart)))
# 
#         if self.tElap > self.tToWarn: # after warning, give a warning
#             if self.mode == 'minimal':
#                 if self.tElap > self.tToWarn and self.warnGiven == 0:
#                      # after 10 sec, give a warning
#                     print lang.msgPleaseWait
#                     self.warnGiven = 1 # only do once
#                     self.tLastPeriod = self.tElap # set as new period
#                 elif self.warnGiven == 1: # second phase, give periodic
#                     if (self.tElap - self.tLastPeriod) >= self.tMsgPeriod:
#                         print lang.msgPleaseWait
#                         self.tLastPeriod = self.tElap # set as new period
#             else:
#                 if self.pollCount % self.pollModulo == 0:
#                     char = self.chars[self.index % len(self.chars)] # mod gets char
#                     self.index = self.index + 1
#                     char = char + ' processing (%ss)' % self.tElap
#                     self.strLast = char # store for erasing on some plats
#                     print char # show whole screen
# 
#     def advanceFrame(self):
#         "call after each poll to add to poll count"
#         self.pollCount = self.pollCount + 1
# 
#     def play(self, totDur=5, frameRate=6):
#         """used to play a sequence of frames, rather than manually
#             calling
#         """
#         frameDur = 1.0 / frameRate # in seconds
#         self.setStart() # set start time
#         while 1:
#             self.printFrame()
#             time.sleep(frameDur)
#             self.clearFrame()
#             self.advanceFrame()
#             if self.tElap >= totDur:
#                 break
#         self.reset() # clear counters

#-----------------------------------------------------------------||||||||||||--

def testStr(n=100, newLines=0):
    """used for testing wrapping text"""
    import random, string
    msg = []
    i = 1
    for x in range(0, n):
        if newLines == 1 and x % 10 == 1: # once in a while
            msg.append('\n%sNewLine' % i) # show a new line
        else:
            max = random.choice(range(1,10))# len of word
            msg.append(str(i))
            for x in range(0, max):
                msg.append(random.choice(string.lowercase))
        msg.append(' ')
        i += 1
    return ''.join(msg)


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




