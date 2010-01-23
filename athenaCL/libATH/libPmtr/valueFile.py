#-----------------------------------------------------------------||||||||||||--
# Name:          valueFile.py
# Purpose:       parameter objects for dealing with files.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import os
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import rhythm
from athenaCL.libATH import language
from athenaCL.libATH import error
lang = language.LangObj()

from athenaCL.libATH.libPmtr import basePmtr

# this import is in /tools dir, used to find samples
from athenaCL.libATH import fileTools

#-----------------------------------------------------------------||||||||||||--

# a general purpose file grabber
# subclasses need only change self.type
# a list of directories is given each time the command is called
# allowing the user to specify only file names
# List of dirs given in TMclass.TextureOps.getAux, each time command is called

class _FileChooser(basePmtr.Parameter):
    def __init__(self, args, refDict):
        """searches a list of directories recursively and finds all files
            files named in args are found within these directories
            dirs are onlys serached if list of dirs has changed"""
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = None # in subclass
        self.outputFmt = 'str' # declare outputFmt as string
        self.argTypes = [['list', 'str'], 'str']
        self.argNames = ['fileNameList', 'selectionString']
        self.argDefaults = [[], 'rc']
        
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError, msg # report error

        self.dirList = [] # used to look for changes
        self.filePathList = [] # updated on __call__
        self.timer = rhythm.Timer() # sets start time
        self.updatePathList = 1 # forces update of paths
        # not sure this is functioning
        #self.tLastUpdate = 0.0 # time of last file dir update

        if drawer.isList(self.args[0]):
            self.nameList = self.args[0]
        elif drawer.isStr(self.args[0]):
            tempList = []
            tempList.append(self.args[0])
            self.nameList = tuple(tempList)

        self.control = self._selectorParser(self.args[1]) # raises exception
        # choose names from name list
        self.selector = basePmtr.Selector(self.nameList, self.control)

    def checkArgs(self):
        if len(self.nameList) == 0:
            return 0, 'provide a list of files to select from.'
        return 1, '' # no problems

    def repr(self, format=''):
        nameListStr = self._scrubList(self.nameList)
        return '%s, %s, %s' % (self.type, nameListStr, self.control)

    def _findFile(self, allFilePaths, target):
        """takes a list of possible paths and returns that path of target
        not implemented: will try to match partial file paths 
        if they contain os.sep
        paths with more os.seps will be checked first"""
        for path in allFilePaths:
            dir, name = os.path.split(path)
            if name == target:
                return path
        return None # not found

    def _updateFileList(self, dirList):
        """generates a big list of all possible audio files
        only run when list of paths differs form already
        updates list of potential complete file paths; searches, from 
        self.nameList, for a match with _findFile, then provides
        the cimplete file path"""
        self.dirList = dirList # update
        self.filePathList = [] # clear
        for path in self.dirList: # dirs provided in ref dict
            if path == '': pass # empty pref
            else:
                obj = fileTools.AllFiles(path)
                fileList = obj.report()
                self.filePathList = self.filePathList + fileList

    def reset(self):
        self.updatePathList = 1 # forces update of paths
        self.selector.reset()

    def __call__(self, t, refDict):
        """dirs are passed with call, so we cant know if files are found
        until call is called"""
        if self.type == 'sampleSelect':
            dirList = refDict['fpAudioDirs']
#         elif self.type == 'analysisSelect':
#             dirList = refDict['sadr']

        # if more than 60s have passed, update dirs
        # always update on start (self.updatePathList == 1)
        if self.updatePathList == 1 or self.timer() > 60: # update after 60s
            self._updateFileList(dirList)
            self.updatePathList = 0 # only do first time
            self.timer.start() # restart timer, reset time

        path = None
        count = 0
        missingReport = []
        while 1:
            fileName = self.selector() # gets from self.nameList 
            # check for a complete file path outside of dir
            if os.path.isfile(fileName):
                path = fileName # assume its a complete path
                break
            path = self._findFile(self.filePathList, fileName)
            if path == None:
                if fileName not in missingReport:
                    print lang.WARN, 'missing file %s' % fileName
                missingReport.append(fileName)
                #path = os.path.join(self.dirList[0], 'error') # defualt error!
                count = count + 1 
                if count > self.FAILLIMIT:
                    path = 'error.aif'
                    print lang.WARN, 'supplying default: %s' % path
                    break
                else:
                    continue
            else: break # found a path
        self.currentValue = '"%s"' % path
        return self.currentValue

# subclass of sampleSelect: just change name
class SampleSelect(_FileChooser):
    def __init__(self, args, refDict):
        """searches a list of directories recursively and finds all files
            files named in args are found within these directories
            dirs are onlys serached if list of dirs has changed"""
        _FileChooser.__init__(self, args, refDict) # call base init
        self.type = 'sampleSelect'
        self.doc = lang.docPoSs

# analysis will need to copy and rename
# all found files in a dir... scratch?
# rename pvoc.1, .2, etcetera
# cd to this dir in batch file

class AnalysisSelect(_FileChooser):
    def __init__(self, args, refDict):
        """searches a list of directories recursively and finds all files
            files named in args are found within these directories
            dirs are onlys serached if list of dirs has changed"""
        _FileChooser.__init__(self, args, refDict) # call base init
        self.type = 'analysisSelect'
        self.doc = lang.docPoAs


#-----------------------------------------------------------------||||||||||||--
class DirectorySelect(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = 'directorySelect'     
        self.doc = lang.docPoDs
        self.outputFmt = 'str' # declare outputFmt as string
        self.argTypes = ['str', 'str', 'str']
        self.argNames = ['directoryFilePath', 'fileExtension', 'selectionString']
        self.argDefaults = ['.', 'aif', 'rw']
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError, msg # report error

        self.dirPath = ''
        self.fileExt = '' # can start w/ period or not
        self.filePathList = [] # updated on __call__
        self.timer = rhythm.Timer() # sets start time

        self.dirPath = self.args[0]
        self.fileExt = self.args[1]
        self.control = self._selectorParser(self.args[2]) # raises exception
        # will update in self._updateFileList
        # can initialize selector empty, but cannot call empty
        self.selector = basePmtr.Selector([], self.control)
        self.updatePathList = 1 # force update of path list on init

    def checkArgs(self):
        self._updateFileList()
        if not os.path.isdir(self.dirPath):
            return 0, 'directory file path error: not a directory.'
        # this should catch errors when no files match
        if len(self.filePathList) == 0:
            return 0, 'directory file path error: no matching files.'
        return 1, '' # no problems

    def repr(self, format=''):
        self._updateFileList()
        msg = []
        msg.append('%s, %s, %s, %s' % (self.type, self.dirPath, 
                                            self.fileExt, self.control))
        if format == 'argsOnly': 
            return ''.join(msg)
        # show extra data
        msg.append('\n')
        msg.append(self.LMARGIN + '%s files found' % len(self.filePathList))
        return ''.join(msg)

    def _updateFileList(self):
        "updates periodically"
        obj = fileTools.AllFiles(self.dirPath, self.fileExt)
        self.filePathList = obj.report()
        self.filePathList.sort()
        self.selector.update(self.filePathList)

    def reset(self):
        self.selector.reset()

    def __call__(self, t=None, refDict=None):
        """dirs are passed with call, so we cant know if files are found
        until call is called"""
        # if more than 60s have passed, update dirs
        # always update on start (self.updatePathList == 1)
        # update after 60s
        if (self.timer() > 60 or self.updatePathList 
            or not self.selector.getStatus()): 
            self._updateFileList()
            self.timer.start() # restart timer, reset time
            self.updatePathList = 0 # only do first time
        try:
            filePath = self.selector()
        except IndexError: # if no values are availabl (directory gone or other)
            filePath = ''
        self.currentValue = '"%s"' % filePath
        return self.currentValue


#-----------------------------------------------------------------||||||||||||--
# a special constant file PO is needed b/c quotes must be forced
# around string output; this does not happen w/ constant parameter obj
# which insterprets a strings as is
# can now use typeFormat po to force strings on other output methods

class ConstantFile(basePmtr.Parameter):
    def __init__(self, args, refDict):
        basePmtr.Parameter.__init__(self, args, refDict) # call base init
        self.type = 'constantFile'    
        self.doc = lang.docPoCf
        self.outputFmt = 'str' # declare outputFmt as string
        self.argTypes = ['str']
        self.argNames = ['absoluteFilePath']
        self.argDefaults = [''] # no default possible
        # check raw arguments for number, type
        ok, msg = self._checkRawArgs()
        if ok == 0: raise error.ParameterObjectSyntaxError, msg # report error
        self.filePath = drawer.pathScrub(self.args[0])

    def checkArgs(self):
        if not os.path.exists(self.filePath):
            return 0, 'file path error: file does not exist.'
        # this should catch errors when no files match
        return 1, '' # no problems

    def repr(self, format=''):
        msg = []
        msg.append('%s, %s' % (self.type, self.filePath))
        return ''.join(msg)

    def reset(self):
        pass

    def __call__(self, t=None, refDict=None):
        """must wrap in quotes"""
        self.currentValue = '"%s"' % self.filePath
        return self.currentValue


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
