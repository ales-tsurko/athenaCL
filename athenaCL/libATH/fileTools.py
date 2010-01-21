#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          fileTools.py
# Purpose:       file and operating system wrappers.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2003-2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import sys, os, re, random, time, sndhdr

from athenaCL.libATH import dialog
from athenaCL.libATH import drawer
from athenaCL.libATH import error
from athenaCL.libATH import htmlTools #htmlTools does not import fileTools
from athenaCL.libATH import osTools
# imageTools is imported below

_MOD = 'fileTools.py'


#-----------------------------------------------------------------||||||||||||--
# extensions are expected to be stored with a leading .
# all general purpose extension groups
imageEXT = osTools.imageEXT
audioEXT = osTools.audioEXT
videoEXT = osTools.videoEXT
dataEXT = osTools.dataEXT
codeEXT = osTools.codeEXT
textEXT = osTools.textEXT
# bundle extensions
mediaEXT = osTools.mediaEXT
knownEXT = osTools.knownEXT

# extension groups used for special fileTools applications
webEXT    = ('.htm', '.css', '.gif', '.html') # ext used for web
distroEXT  = ('.py',     '.xml', '.txt', '.htm', '.pdf', '.aif') 
athDataEXT = ('.bat', '.sco', '.orc', '.xml', '.csd', '.mid', '.txt')
# distro compressions; always place longest first
athCompEXT = ('.mpkg.zip', '.tar.gz', '.sit.hqx', '.zip', '.dmg', '.exe', 
                  '.deb', '.rpc') 

#-----------------------------------------------------------------||||||||||||--

class FileInfo:
    """create an object with file info"""
    def __init__(self, absPath, parentDir=None):

        self.absPath = absPath
        self.relPath = osTools.pathTrimStub(absPath, parentDir)
        self.parentDir = parentDir

        self.relDir, self.name = os.path.split(self.relPath)
        if self.relDir == '': # no parent dir
            self.relDir = None

        nameStub, self.ext = osTools.extSplit(self.name)

        self.statInfo = os.stat(absPath)
        self.size = self.statInfo[6]
        self.sizeKb, self.sizeMb = self._sizeConvert(self.size)

        self.aTime = self.statInfo[7] # last acess: includes simply opening a file
                                                # not a good measure of newness
        # this is actually creation time:
        self.mTime = self.statInfo[8] # last modification: this is most important
        self.cTime = self.statInfo[9] # last status change

        self.mTimeStr = time.ctime(self.mTime)

        # check for rsrc
        emptyRsrc = '\x00\x00\x00\x00'
        if drawer.isDarwin():
            self.creator, self.type = osTools.rsrcGetCreator(self.absPath)
            if self.creator == emptyRsrc: # result with no rsrc
                self.creator = None
            if self.type == emptyRsrc: # result with no rsrc
                self.type = None
        else:
            self.creator = None
            self.type = None

        # check if it is an audio file
        # note that this does not work for some raw audio files 
        try:
            audioData = sndhdr.what(self.absPath)
        except RuntimeError, e:
            print _MOD, 'bad audio file: %s' % absPath
            audioData = None

        if audioData == None:
            self.audioSr = None
            self.audioCh = None
            self.audioType = None
            self.audioBits = None
            self.audioDur = None
        else:
            type, sr, ch, frame, bits = audioData
            self.audioSr = sr
            self.audioCh = ch
            self.audioType = type
            self.audioBits = bits
            self.audioDur = frame / float(sr)

    def _sizeConvert(self, bytes):
        sizeKb = round(bytes / 1024.0, 1)
        sizeMb = round(sizeKb / 1024.0, 1)
        return sizeKb, sizeMb


#-----------------------------------------------------------------||||||||||||--
class DirWalk:
    def __init__(self, searchDir=None, excludeEndswith=None):
        self.searchDir = searchDir
        self.excludeEndswith = excludeEndswith
        self.fileList = [] # list of complete path of desired files
        self.dirList = [] # all dirs searched
        self.curFiles = 0
        self.maxFiles = 10000000 # raises error if exceeded

    def constrainNames(self, fileName):
        """constrains files to a particular set"""
        if self.excludeEndswith != None:
            for exclude in self.excludeEndswith:
                if fileName.endswith(exclude):
                    return None # exclude, return None
        return fileName # okay, return whole name

    def constrainDirs(self, dirname):
        """constrains dirs to a particular set"""
        # modify in subclass, return name or non
        return dirname

    def fileFilter(self):
        newList = []
        for entry in self.fileList:
            if os.path.isdir(entry):
                continue # skip things that are dirs
            x = self.constrainNames(entry)
            if x == None: pass
            else: newList.append(x)
        del self.fileList
        self.fileList = newList

    def dirFilter(self):
        newList = []
        for entry in self.dirList:
            if not os.path.isdir(entry):
                continue # skip things that are not dirs
            x = self.constrainDirs(entry)
            if x == None: pass
            else: newList.append(x)
        del self.dirList
        self.dirList = newList

    def visitFunc(self, args, dirname, names):
        for file in names:
            self.fileList.append(os.path.join(dirname, file))
            self.curFiles = self.curFiles + 1  
        self.dirList.append(dirname)
        if self.curFiles >= self.maxFiles: # break
            raise('ExceededMaxFiles')

    def walk(self):
        # the results of this are stored in self.curFiles, self.dirList
        os.path.walk(self.searchDir, self.visitFunc, '')
        self.fileFilter()
        self.dirFilter()

    def getDirList(self):
        "just get directories"
        self.walk()
        return self.dirList

    def report(self):
        "return complete information"
        self.walk()
        return self.dirList, self.fileList

#-----------------------------------------------------------------||||||||||||--
class GatherSrc(DirWalk):
    def __init__(self, searchDir=None):
        searchDir = drawer.pathScrub(searchDir)
        if not os.path.isdir(searchDir):
            raise error.ArgumentError
        DirWalk.__init__(self, searchDir) # call base init

    def constrainNames(self, fileName):
        """constrains files to a particular set"""
        if (fileName[-3:] == '.py' or fileName[-4:] == '.xml' or 
             fileName[-4:] == '.cgi'):
            return fileName
        else:
            return None

    def constrainDirs(self, dirname):
        """constrains files to a particular set"""
        dir, name = os.path.split(dirname)
        if name == 'CVS':
            return None
        elif name[0] == '.':
            return None
        else:
            return dirname


#-----------------------------------------------------------------||||||||||||--
class FileStats(DirWalk):
    def __init__(self, searchDir=None):
        searchDir = drawer.pathScrub(searchDir)
        if not os.path.isdir(searchDir):
            raise error.ArgumentError
        DirWalk.__init__(self, searchDir) # call base init

    def constrainNames(self, fileName):
        """constrains files to a particular set"""
        if fileName[-3:] == '.py':
            return fileName
        else:
            return None

    def constrainDirs(self, dirname):
        """constrains files to a particular set"""
        dir, name = os.path.split(dirname)
        if name == 'CVS':
            return None
        elif name[0] == '.':
            return None
        else:
            return dirname

    def constrainLines(self, line):
        """examines a line of text
            excludes white space and comments"""
        line = line.strip()
        if line == '': # a blank line
            return 'white', None
        elif line[0] == '#': # a comment
            return 'comment', None
        else: # it is a line of code
            if line[:3] == 'def':
                return 'line', 'def'
            elif line[:5] == 'class':
                return 'line', 'class'
            else: # regular line of code
                return 'line', None

    def countLines(self):
        self.walk()
        sum = 0
        comments = 0
        white = 0
        defs = 0
        classes = 0
        for entry in self.fileList:
            f = open(entry, 'r')
            fileLines = f.readlines()
            f.close()
            for line in fileLines:
                x, y = self.constrainLines(line)
                if x == 'white':
                    white = white + 1
                elif x == 'comment':
                    comments = comments + 1
                elif x == 'line':
                    sum = sum + 1
                    if y == 'def':
                        defs = defs + 1
                    elif y == 'class':
                        classes = classes + 1
        return sum, white, comments, defs, classes
    
    def reportCount(self):
        sum, white, comments, defs, classes = self.countLines()
        for entry in self.dirList:
            print entry
        print '\n%s lines of code found for %s .py files' % (sum,
                                                      len(self.fileList))
        print '(%s white, %s comments)' % (white, comments) 
        print '%s class, %s def statements\n' % (classes, defs)

#-----------------------------------------------------------------||||||||||||--
class GatherCvs(DirWalk):
    "gathers all cvs files that shold be removed from a dir tree"
    def __init__(self, searchDir=None):
        DirWalk.__init__(self, searchDir) # call base init

    def constrainDirs(self, dirname):
        """constrains files to a particular set"""
        dir, name = os.path.split(dirname)
        if name == 'CVS':
            return dirname
        else:
            return None

    def constrainNames(self, fileName):
        """constrains files to a particular set"""
        if fileName.endswith('.cvsignore'):
            return fileName
        else:
            return None

    def report(self):
        self.walk()
        return self.dirList + self.fileList

#-----------------------------------------------------------------||||||||||||--
class GatherImage(DirWalk):
    "gathers all image files"
    def __init__(self, searchDir=None):
        DirWalk.__init__(self, searchDir) # call base init

    def constrainDirs(self, dirname):
        """constrains files to a particular set"""
        return dirname

    def constrainNames(self, fileName):
        """constrains files to a particular set"""
        for ext in imageEXT:
            if fileName.endswith(ext) or fileName.endswith(ext.upper()):
                return fileName
        return None

    def report(self):
        self.walk()
        return self.fileList

#-----------------------------------------------------------------||||||||||||--
class GatherAudio(DirWalk):
    "gathers all audio files"
    def __init__(self, searchDir=None):
        DirWalk.__init__(self, searchDir) # call base init

    def constrainDirs(self, dirname):
        """constrains files to a particular set"""
        return dirname

    def constrainNames(self, fileName):
        """constrains files to a particular set"""
        for ext in audioEXT:
            if fileName.endswith(ext) or fileName.endswith(ext.upper()):
                return fileName
        if drawer.isDarwin(): # check resources
            creator, type = osTools.rsrcGetCreator(fileName)
            if type in ['AIFF', 'WAVE', 'Sd2f', 'MPG3', 'M4A ',]:
                return fileName
        return None

    def report(self):
        self.walk()
        return self.fileList
        
#-----------------------------------------------------------------||||||||||||--
class AllFiles(DirWalk):
    """returns all files within nested dirs, except those named _exclude
    can optionally provide a file extension, or list of file extensions, 
    to match; does not matter if ext starts w/ period or not.
    """
    def __init__(self, searchDir=None, fileExt=None):
        DirWalk.__init__(self, searchDir) # call base init
        self.fileExt = fileExt # may be a list of 

        if self.fileExt != None:
            if drawer.isStr(self.fileExt): # add to list
                self.fileExtList = [self.fileExt]
            else: # its a list of strings:
                self.fileExtList = self.fileExt

    def constrainDirs(self, dirname):
        """constrains files to a particular set"""
        dir, name = os.path.split(dirname)
        if name == '_exclude':
            return None
        else:
            return dirname

    def constrainNames(self, fileName):
        """constrains files to a particular set"""
        if fileName.find('_exclude') >= 0: # get everything
            return None
        else:
            if self.fileExt != None: # some extensions are defined
                for ext in self.fileExtList:
                    if (fileName[-(len(ext)):].lower() == ext.lower()):
                        return fileName # return if found
            else:
                return fileName
        return None # if gets this far

    def report(self):
        self.walk()
        return self.fileList


#-----------------------------------------------------------------||||||||||||--
class ConvertBreaks:
    "converts line breaks, format as mac or win"
    def __init__(self, args):
        if len(args) != 2:
            raise error.ArgumentError
        searchDir = args[0]
        searchDir = drawer.pathScrub(searchDir)
        if not os.path.isdir(searchDir):
            raise error.ArgumentError
        dstFormat = args[1].lower()
        if dstFormat not in ['mac', 'win']:
            raise error.ArgumentError
        self.searchDir = searchDir
        self.dstFormat = dstFormat.lower()

    def convert(self, pathList, convertTo='mac'):
        """accepts a list of complete paths, performs conversion"""
        if convertTo.lower() == 'mac':
            newLF = "\r"
        elif convertTo.lower() == 'win':
            newLF = "\r\n"
        else:
            return 'bad args, canceled'
    
        for path in pathList:
            if os.path.isdir(path):
                print "not a file (dir): %s" % path
                continue
            data = open(path, "rb").read()
            if '\0' in data:
                print "not a file (binary): %s" % path
                continue

            newdata = re.sub("\r?\n", newLF, data)
            if newdata != data:
                # print file
                f = open(path, "wb")
                f.write(newdata)
                f.close()
    
    def batchConvert(self):  
        selNames, selPaths = osTools.dirGather(self.searchDir,
                                         ['txt', 'py', 'xml'])
        filteredFileList = selPaths
        if len(filteredFileList) == 0:
            print 'empty directory: %s' % self.searchDir
        else:
            fileNumber = '%i' % len(filteredFileList)
            msg = ('convert to %s: %s files in %s' % 
                                      (self.dstFormat.upper(), 
                                      fileNumber.rjust(4), 
                                      self.searchDir))
            print msg
            self.convert(filteredFileList, self.dstFormat)



#-----------------------------------------------------------------||||||||||||--
class RenameQuad:
    def __init__(self, searchDir=None):
        searchDir = drawer.pathScrub(searchDir)
        if not os.path.isdir(searchDir):
            raise error.ArgumentError
        self.searchDir = searchDir
        self.conversion = {'CH1': 'L',
                                 'CH2': 'R',
                                 'CH4': 'Ls',
                                 'CH3': 'Rs', }

    def collGroups(self):
        self.group = {}
        fileList = os.listdir(self.searchDir)
        for file in fileList:
            if (file[-3:] == 'CH1' or file[-3:] == 'CH2' 
                or file[-3:] == 'CH3' or file[-3:] == 'CH4'):
                newKey = file[:-3] # name, with out period ?
                newRef = file[-3:] # ext
                if self.group.has_key(newKey):
                    self.group[newKey].append(newRef)
                else:
                    self.group[newKey] = []
                    self.group[newKey].append(newRef)

    def rename(self):
        for fileGroup in self.group.keys():
            print 'renaming %s' % fileGroup
            for ext in self.group[fileGroup]:
                oldName = fileGroup + ext
                newName = fileGroup + '.' + self.conversion[ext] # . needed
                oldPath = os.path.join(self.searchDir, oldName)
                newPath = os.path.join(self.searchDir, newName)
                cmdStr = 'mv %s %s' % (oldPath, newPath)
                print cmdStr
                os.system(cmdStr)
        print ''        

class RenameStereo:
    """strip L,R extensions from files"""
    def __init__(self, searchDir=None):
        searchDir = drawer.pathScrub(searchDir)
        if not os.path.isdir(searchDir):
            raise error.ArgumentError
        self.searchDir = searchDir
        self.conversion = {'.L': '.a',
                                 '.R': '.b',}
        # run script
        self.collGroups()
        self.rename()

    def collGroups(self):
        self.group = {}
        fileList = os.listdir(self.searchDir)
        for file in fileList:
            if file[-2:] == '.L' or file[-2:] == '.R':
                newKey = file[:-2] # name, with out period
                newRef = file[-2:] # extension
                if self.group.has_key(newKey):
                    self.group[newKey].append(newRef)
                else:
                    self.group[newKey] = []
                    self.group[newKey].append(newRef)

    def rename(self):
        for fileGroup in self.group.keys():
            print 'renaming %s' % fileGroup
            for ext in self.group[fileGroup]:
                oldName = fileGroup + ext
                if len(self.group[fileGroup]) == 1: # if only one file here
                    newName = fileGroup # use just the name, no extension
                else:
                    newName = fileGroup + self.conversion[ext] # . included
                oldPath = os.path.join(self.searchDir, oldName)
                newPath = os.path.join(self.searchDir, newName)
                cmdStr = 'mv %s %s' % (oldPath, newPath)
                #print cmdStr
                os.system(cmdStr)
        print ''        

#-----------------------------------------------------------------||||||||||||--

class BundleFiles:
    """gathers all extra athenacl files, except the audio file,
        and places them in a dir with the same name as the files"""
    def __init__(self, searchDir=None):
        searchDir = drawer.pathScrub(searchDir)
        if not os.path.isdir(searchDir):
            raise error.ArgumentError

        self.searchDir = searchDir
        self.audioEXT = audioEXT
        self.athDataEXT = athDataEXT

        selNames, selPaths = osTools.dirGather(self.searchDir,
                                    self.athDataEXT) # gather .xml, .sco, .orc
        selPaths.sort()
        bundleDict = {}
        for path in selPaths:
            dir, name = os.path.split(path)
            for ext in self.athDataEXT:
                if name[-len(ext):] == ext: # if has this ext
                    nameStub = name[:-len(ext)]
                    break
            if nameStub not in bundleDict.keys():
                bundleDict[nameStub] = []
            bundleDict[nameStub].append(path)

        for groupName in bundleDict.keys():
            if len(bundleDict[groupName]) > 1: # dont bundle single items
                groupDir = os.path.join(self.searchDir, groupName)
                if os.path.isdir(groupDir) != 1: # if doesnt exists
                    print groupDir # if doesnt exist
                    os.mkdir(groupDir)
                else:
                    print "dir in the way: %s" % groupDir 

                for path in bundleDict[groupName]:
                    dir, name = os.path.split(path)
                    newDst = os.path.join(groupDir, name)
                    cmdStr = 'mv %s %s' % (path, newDst)
                    if os.path.exists(newDst) != 1: # if doesnt exist
                        #print cmdStr
                        os.system(cmdStr)
                    else:
                        print "file in the way: %s" % newDst 


class BundleAudio:
    """gathers audio files and places in _audio directory"""
    def __init__(self, searchDir):
        searchDir = drawer.pathScrub(searchDir)
        if not os.path.isdir(searchDir):
            raise error.ArgumentError

        self.searchDir = searchDir
        self.audioEXT = audioEXT
        self.audioDirPath = os.path.join(self.searchDir, '_audio')
        # create dir
        if os.path.isdir(self.audioDirPath) != 1: # if doesnt exit
            os.mkdir(self.audioDirPath)
        selNames, selPaths = osTools.dirGather(self.searchDir,
                                    self.audioEXT) # gather .aif, .wav
        for path in selPaths:
            dir, name = os.path.split(path)
            newDst = os.path.join(self.audioDirPath, name)
            if os.path.exists(newDst) != 1: # if dst doesnt exist
                cmdStr = 'mv %s %s' % (path, newDst)
                os.system(cmdStr)
            else:
                print "file in the way: %s" % newDst 








#-----------------------------------------------------------------||||||||||||--


class ProofSheet:
    "parent class for proof sheets"
    def __init__(self, dirPath):
        if not os.path.isdir(dirPath):
            print 'got bad dir path', dirPath
            raise error.ArgumentError, 'bad file path supplied'
        dirPath = drawer.pathScrub(dirPath)

        self.dirPath = dirPath
        junk, self.dirName = os.path.split(dirPath)

        self.proofDirName = '_proof'
        # create proof dir
        self.proofDirPath = os.path.join(self.dirPath, self.proofDirName)
        if os.path.exists(self.proofDirPath) != 1:
            os.mkdir(self.proofDirPath)
            print 'writing: %s' % self.proofDirPath
        else: pass
        # create index path
        self.indexPath = os.path.join(self.proofDirPath, 'index.html')

    def htmlPrep(self):
        # html options
        self.colorDict = {}
        self.colorDict['bg']        = '#000000'
        self.colorDict['p']     = '#666666'
        self.colorDict['h1']        = '#cccccc'
        self.colorDict['h2']        = '#cccccc'
        self.colorDict['h3']        = '#cccccc'
        self.colorDict['link']  = '#999999'
        self.colorDict['hover'] = '#666633'
        self.colorDict['post']  = '#666666'
        self.colorDict['hr']        = '#808080'# grey used in divider

        self.fontDict = {}
        self.fontDict['p']  = 8
        self.fontDict['h1'] = 8
        self.fontDict['h2'] = 8
        self.fontDict['h3'] = 6

        # html prep
        popObj = htmlTools.PopUp()
        headScript = popObj.script()

        # sizing issues
        self.leftColWIDTH = 120   
        self.gutterWIDTH = 6     
        self.dataWIDTH = 220 
        self.nameWIDTH = 180 # only used in audio sheet 

        self.totalWIDTH = 640 # guess, should be set elsewhere

        # set master width at 640
        self.wpObj = htmlTools.WebPage(self.totalWIDTH, self.title, 
                                          self.colorDict, self.fontDict) 
        self.wpObj.titleRoot = self.title
        self.wpObj.headInit('%s' % (self.dirPath),'',headScript)

        # create a top-level loader
        self.proofLoaderPath = os.path.join(self.dirPath, '_proof.html')
        dst = '%s/index.html' % self.proofDirName
        self.wpObj.writeRefreshPage(self.proofLoaderPath, dst)


    def openPage(self):
        import webbrowser
        webbrowser.open('file://' + self.proofLoaderPath)

    def run(self):
        self.process()
        self.htmlPrep()
        self.writePage()
        self.openPage()
      
    def runNoView(self):
        self.process()
        self.htmlPrep()
        self.writePage()
        #self.openPage()

class ImageSheet(ProofSheet):
    def __init__(self, args):
        size = 256
        dirPath = None

        for entry in args:
            if entry[0] == '-': # find switches
                sizeStr = entry[1:]
                if    sizeStr == 'xs': size = 32
                elif sizeStr == 's': size = 64
                elif sizeStr == 'm': size = 128
                elif sizeStr == 'l': size = 256
                elif sizeStr == 'xl': size = 512
                elif sizeStr == 'xl': size = 768
                else: size = 128
            else:
                dirPath = entry

        ProofSheet.__init__(self, dirPath)
        self.title = 'ImageSheet'
        self.size = size

    def process(self):
        # import here, not at top level
        #htmlTools does not import fileTools
        from athenaCL.libATH import imageTools 
        # create images dir, remove old
        self.proofThumbDirPath = os.path.join(self.proofDirPath, 'images')
        if os.path.exists(self.proofThumbDirPath):
            osTools.rm(self.proofThumbDirPath) # erase old, recursive
        os.mkdir(self.proofThumbDirPath)

        # get all file paths (after removing old images dir!)
        obj = GatherImage(self.dirPath)
        self.allPaths = obj.report()
        thumbObj = imageTools.Thumb(self.allPaths, self.size)
        procFiles = thumbObj.reduce()

        # move files to proper location
        adjProcFiles = []
        for src, dst in procFiles:
            dir, name = os.path.split(dst)
            adjDst = os.path.join(self.proofThumbDirPath, name)
            osTools.mv(dst, adjDst)
            adjProcFiles.append([src, adjDst])

        del procFiles
        self.procFiles = adjProcFiles


    def _exifProcess(self, filePath):
        viewKeys = {'MakerNote Saturation':'sat', 
                        'MakerNote Whitebalance':'whitebal', 
                      # 'MakerNote ImageAdjustment':'adj', 
                        'EXIF MeteringMode':'metering',
                     #   'EXIF ExifImageWidth':'w', 
                     #   'EXIF ExifImageLength':'l', 
                        'MakerNote Quality':'quality', 
                        'EXIF Flash':'flash', 
                        'EXIF FNumber':'f',
                     #   'MakerNote FocusMode':'focus', 
                        'EXIF FocalLength':'flen', 
                        'EXIF ExposureTime':'exp', 
                        'EXIF ISOSpeedRatings':'iso', 
                      # 'MakerNote ISOSelection':'isomode'
                      }
        try:
            import EXIF
            exifReport = 1
            f = open(filePath)
            exifData = EXIF.process_file(f)
        except ImportError:
            return None
        except:
            return None
        msg = []
        sortKeys = exifData.keys()
        sortKeys.sort()
        for key in sortKeys:
            #if not drawer.isStr(exifData[key]):
            #    print '%s: %s' % (key, exifData[key].printable)
            if key in viewKeys.keys():
                msg.append('%s-%s' % (viewKeys[key], exifData[key]))
        f.close()
        if msg == []:
            return None
        return ' | '.join(msg)



    def writePage(self):
        body = []
        lastDirStr = ''

        for target, dst in self.procFiles:
            # try to get EXIF info
            exifMsg = self._exifProcess(target) # returns None if fails

            dir, thumb = os.path.split(dst) # remove path, will append images

            junk, name = os.path.split(target)

            fileObj = FileInfo(target, self.dirPath)
            relPath = fileObj.relPath

            dir, name = os.path.split(target) # remove path, will append images
            if fileObj.relDir != lastDirStr: # same as last  
                body.append(self.wpObj.BR)   
            lastDirStr = fileObj.relDir

            if fileObj.relDir == None: relDirStr = '/'
            else: relDirStr = fileObj.relDir

            dirStr = self.wpObj.pText('%s' % (relDirStr))
            # link string is included with data string
            linkStr = self.wpObj.linkStringWindow(target, name, 1)

            if exifMsg != None:
                dataStr = self.wpObj.pText('%s%s%s MB | %s%s%s' % (linkStr, 
                          self.wpObj.BR, fileObj.sizeMb, fileObj.mTimeStr,
                          self.wpObj.BR, exifMsg), 'p')
            else:
                dataStr = self.wpObj.pText('%s%s%s MB | %s' % (linkStr, 
                          self.wpObj.BR, fileObj.sizeMb, fileObj.mTimeStr,
                          ), 'p')

            imageStr = self.wpObj.linkImageWindow(target, thumb, thumb, 0)

            colList = []
            colList.append({'width':self.leftColWIDTH, 'align':'left', 
                                 'color':None, 
                                 'content':dirStr })
            colList.append({'width':self.gutterWIDTH, 'align':'left', 
                                 'color':None,
                                 'content':''})
            colList.append({'width':self.dataWIDTH, 'align':'left', 'color':None, 
                                 'content':dataStr })
            colList.append({'width':self.gutterWIDTH, 'align':'left', 
                                 'color':None,
                                 'content':''})
            colList.append({'width':self.size, 'align':'left', 'color':None,
                                 'content':imageStr})
            body.append(self.wpObj.nTable(colList))
            body.append(self.wpObj.BR)   

        self.wpObj.basicPage(self.indexPath, ''.join(body), self.dirName)



class GraphicSheet(ProofSheet):
    """like an imagesheet, but with more extra information and text info"""
    def __init__(self, args):
        size = 256
        dirPath = None

        for entry in args:
            if entry[0] == '-': # find switches
                sizeStr = entry[1:]
                if    sizeStr == 'xs': size = 32
                elif sizeStr == 's': size = 64
                elif sizeStr == 'm': size = 128
                elif sizeStr == 'l': size = 256
                elif sizeStr == 'xl': size = 512
                elif sizeStr == 'xl': size = 768
                else: size = 128
            else:
                dirPath = entry

        ProofSheet.__init__(self, dirPath)
        self.title = 'GraphicSheet'
        self.size = size

    def process(self):
        # import here, not at top level
        #htmlTools does not import fileTools
        from athenaCL.libATH import imageTools 
        # create images dir, remove old
        self.proofThumbDirPath = os.path.join(self.proofDirPath, 'images')
        if os.path.exists(self.proofThumbDirPath):
            osTools.rm(self.proofThumbDirPath) # erase old, recursive
        os.mkdir(self.proofThumbDirPath)

        # get all file paths (after removing old images dir!)
        obj = GatherImage(self.dirPath)
        self.allPaths = obj.report()
        thumbObj = imageTools.Thumb(self.allPaths, self.size)
        procFiles = thumbObj.reduce()

        # move files to proper location
        adjProcFiles = []
        for src, dst in procFiles:
            dir, name = os.path.split(dst)
            adjDst = os.path.join(self.proofThumbDirPath, name)
            osTools.mv(dst, adjDst)
            adjProcFiles.append([src, adjDst])

        del procFiles
        self.procFiles = adjProcFiles


    def _textProcess(self, filePath):
        """look for a text file with the same path (.txt) and then add as 
        comments"""
        pathStub, ext = osTools.extSplit(filePath)
        txtPath = '%s.txt' % pathStub 
        if os.path.exists(txtPath):
            f = open(txtPath)
            strMsg = f.read()
            f.close()
            return strMsg
        else:
            return None

    def writePage(self):
        body = []
        lastDirStr = ''

        for target, dst in self.procFiles:
            # try to get text info
            strMsg = self._textProcess(target) # returns None if fails
            if strMsg == None:
                strMsg = '...'

            dir, thumb = os.path.split(dst) # remove path, will append images
            junk, name = os.path.split(target)

            dataStr = self.wpObj.pText('%s' % (strMsg))
            # link string is included with data string
            linkStr = self.wpObj.linkStringWindow(target, name, 1)

            imageStr = self.wpObj.linkImageWindow(target, thumb, thumb, 0)

            colList = []
            colList.append({'width':self.leftColWIDTH, 'align':'left', 
                                 'color':None, 
                                 'content':dataStr })

            colList.append({'width':self.gutterWIDTH, 'align':'left', 
                                 'color':None,
                                 'content':''})
            colList.append({'width':self.size, 'align':'left', 'color':None,
                                 'content':imageStr})
            body.append(self.wpObj.nTable(colList))
            body.append(self.wpObj.BR)   

        self.wpObj.basicPage(self.indexPath, ''.join(body), self.dirName)




#-----------------------------------------------------------------||||||||||||--

class AudioSheet(ProofSheet):
    def __init__(self, dirPath):
        ProofSheet.__init__(self, dirPath)
        self.title = 'AudioSheet'

    def process(self):
        # get all file paths (after removing old images dir!)
        obj = GatherAudio(self.dirPath)
        self.allPaths = obj.report()


    def writeMediaPage(self, count, label, mediaSrc, width):
        fileName =  'media-%s.html' % count
        filePath = os.path.join(self.proofDirPath, fileName)
        dir, mediaName = os.path.split(mediaSrc)

        self.mpObj = htmlTools.WebPage(width, label, 
                        self.colorDict, self.fontDict) 
        self.mpObj.titleRoot = ''
        self.mpObj.headInit(mediaName, '')
        body = [] #[self.mpObj.BR]

        width = width - 16 # adjust a bit here, dont know why
        colList = []
        colList.append({'width':width, 'align':'center', 'color':None, 
                             'content':self.mpObj.embed(mediaSrc) })
        body.append(self.mpObj.nTable(colList))

        caption = self.mpObj.BR + self.mpObj.pText('%s' % mediaName)
        colList = []
        colList.append({'width':width, 'align':'center', 'color':None, 
                             'content':caption })
        body.append(self.mpObj.nTable(colList))

        self.mpObj.basicPage(filePath, ''.join(body), mediaName)
        return fileName

    def writePage(self):
        body = []
        lastDirStr = ''
        count = 0

        for target in self.allPaths:
            fileObj = FileInfo(target, self.dirPath)
            relPath = fileObj.relPath

            dir, name = os.path.split(target) # remove path, will append images
            if fileObj.relDir != lastDirStr: # same as last  
                body.append(self.wpObj.BR)   
            lastDirStr = fileObj.relDir

            if fileObj.relDir == None: relDirStr = '/'
            else: relDirStr = fileObj.relDir

            mediaWidth = 220
            mediaHeight = 40
            fileName = self.writeMediaPage(count, name, target, mediaWidth)
            popObj = htmlTools.PopUp()

            linkStrAlt = self.wpObj.linkStringWindow(target, ' +', 0)
            linkStr = self.wpObj.pText(popObj.linkToPop(fileName, name, 
                        mediaWidth, mediaHeight, 0) + linkStrAlt)
            dirStr = self.wpObj.pText('%s' % (relDirStr))
            if fileObj.audioType == None:
                dataStr = self.wpObj.pText('%s MB | %s' % (fileObj.sizeMb,
                                                                         fileObj.mTimeStr))
            else:
                dataStr = self.wpObj.pText('%s MB | %s | %s | %s' % (fileObj.sizeMb,
                             fileObj.audioType, fileObj.audioBits, fileObj.mTimeStr))

            colList = []
            colList.append({'width':self.leftColWIDTH, 'align':'left',
                                 'color':None, 
                                 'content':dirStr })
            colList.append({'width':self.gutterWIDTH,    'align':'left', 
                                 'color':None,
                                 'content':''})
            colList.append({'width':self.nameWIDTH, 'align':'left', 
                                 'color':None, 
                                 'content':linkStr})
            colList.append({'width':self.gutterWIDTH,    'align':'left', 
                                 'color':None,
                                 'content':''})
            colList.append({'width':self.dataWIDTH,  'align':'left', 
                                 'color':None,
                                 'content':dataStr})
            body.append(self.wpObj.nTable(colList))
            count = count + 1
            #body.append(popObj.linkToPop())
        self.wpObj.basicPage(self.indexPath, ''.join(body), self.dirName)



class LinkSheet(ProofSheet):
    def __init__(self, args):
        writeDir = osTools.tempDir()
        ProofSheet.__init__(self, writeDir)
        self.title = 'LinkSheet'
        self.url = drawer.urlPrep(args[0], 'http')
        self.keyWords = args[1:]

    def process(self):
        # get all file paths (after removing old images dir!)
        from urllib import urlopen

        doc = urlopen(self.url).read()

        self.filteredLinks = []

        links = htmlTools.getLinks(self.url)
        if links == None:
            return None
                
        for descr, url in links: # automatically an and search
            descr = descr.lower()
            matches = 0
            for word in self.keyWords:
                word = word.lower()
                if descr.find(word) >= 0:
                    matches = matches + 1
            if matches == len(self.keyWords): # all have to match
                self.filteredLinks.append((descr, url))
        #for entry in filteredLinks:
        #    print entry

    def writePage(self):
        body = []
        lastDirStr = ''
        count = 0

        if self.filteredLinks == []:
            print 'no matches'
            return None
            
        for descr, url in self.filteredLinks:
            dataStr = self.wpObj.linkString(url, descr, 0)

            colList = []
            colList.append({'width':self.totalWIDTH, 'align':'left',
                                 'color':None, 
                                 'content':dataStr })

            body.append(self.wpObj.nTable(colList))
            count = count + 1
            #body.append(popObj.linkToPop())
        self.wpObj.basicPage(self.indexPath, ''.join(body), self.dirName)




#-----------------------------------------------------------------||||||||||||--



class CompareDir:
    """compares two directories recursively and returns a report"""
    def __init__(self, args):
        self.args = args
        if len(self.args) <= 1:
            raise error.ArgumentError
        else: # 2 or  more args
            if self.args[0] == self.args[1]:
                raise error.ArgumentError # cant do on same dir

            self.srcA = self.args[0]
            if not os.path.isdir(self.srcA):
                raise error.ArgumentError
            self.srcB = self.args[1]
            if not os.path.isdir(self.srcB):
                # create a dir if argB does not exist
                if not os.path.exists(self.srcB):
                    osTools.mkdir(self.srcB)
                else: # exists but is not a dir
                    raise error.ArgumentError

        # a list of '.endswith' strings to ignore as files
        self.excludeEndswith = ['.DS_Store', '.pyc']

        objA = DirWalk(self.srcA, self.excludeEndswith)
        objB = DirWalk(self.srcB, self.excludeEndswith)

        absDirListA, self.filesA = objA.report() # raw path to all files
        absDirListB, self.filesB = objB.report()

        self.fileDictA = None # stores file objects
        self.fileDictB = None
        self.mergedFileDict = {} # store infor about diffs and outdatedness
        self.mergedDirDict = {}
    
        self.dirListA = []
        self.dirListB = []
        self.fileMissListA = []
        self.fileMissListB = []
        self.dirMissListA = []
        self.dirMissListB = []

        self.fileOutdateListA = [] # files outdated on a
        self.fileOutdateListB = [] # files outdated on b

        self.fileDictA = self._prepFiles(self.filesA, self.srcA)      
        self.fileDictB = self._prepFiles(self.filesB, self.srcB)

    def _prepFiles(self, allFiles, parentDir):
        # can use filecmp.cmp(f1, f2)
        # but this compares more features then needed, including last access
        # owner/group info
        fileDict = {}
        for absPath in allFiles:
            fileObj = FileInfo(absPath, parentDir)
            fileDict[fileObj.relPath] = fileObj
        return fileDict


    def _findDirs(self):
        """count relative subdirs, excluding parent dir
        first method called to gather all file data"""
        self.dirListA = []
        for file in self.fileDictA.keys():
            relDir = self.fileDictA[file].relDir
            if relDir != None:
                if relDir not in self.dirListA:
                    self.dirListA.append(relDir)
        self.dirListB = []
        for file in self.fileDictB.keys():
            relDir = self.fileDictB[file].relDir
            if relDir != None:
                if relDir not in self.dirListB:
                    self.dirListB.append(relDir)
                

    def _mergeFiles(self):
        "combine files from a, b into a composite"
        for file in self.fileDictA.keys():
            if file not in self.mergedFileDict.keys():
                self.mergedFileDict[file] = {} #each entry a dictionary
            if not self.mergedFileDict[file].has_key('found'):
                self.mergedFileDict[file]['found'] = []
            self.mergedFileDict[file]['found'].append('a')
        for file in self.fileDictB.keys():
            if file not in self.mergedFileDict.keys():
                self.mergedFileDict[file] = {} #each entry a dictionary
            if not self.mergedFileDict[file].has_key('found'):
                self.mergedFileDict[file]['found'] = []
            self.mergedFileDict[file]['found'].append('b')
        #print self.mergedFileDict

    def _mergeDirs(self):
        "combine dirs from a, b into a composite"
        for file in self.fileDictA.keys():
            relDir = self.fileDictA[file].relDir
            if relDir != None: # not toplevel dir
                if relDir not in self.mergedDirDict.keys():
                    self.mergedDirDict[relDir] = {}
                if not self.mergedDirDict[relDir].has_key('found'):
                    self.mergedDirDict[relDir]['found'] = []
                # only need one mark for many files in this dir
                if 'a' not in self.mergedDirDict[relDir]['found']:
                    self.mergedDirDict[relDir]['found'].append('a')
        for file in self.fileDictB.keys():
            relDir = self.fileDictB[file].relDir
            if relDir != None: # not toplevel dir
                if relDir not in self.mergedDirDict.keys():
                    self.mergedDirDict[relDir] = {}
                if not self.mergedDirDict[relDir].has_key('found'):
                    self.mergedDirDict[relDir]['found'] = []
                # only need one mark for many files in this dir
                if 'b' not in self.mergedDirDict[relDir]['found']:
                    self.mergedDirDict[relDir]['found'].append('b')

    def _findFileMiss(self):
        "find each file in merged that does not have a copy in a, then b"
        self.fileMissListA = []
        self.fileMissListB = []
        for file in self.mergedFileDict.keys():
            if len(self.mergedFileDict[file]['found']) == 2:
                pass # has both
            else:
                if self.mergedFileDict[file]['found'][0] == 'a':
                    self.fileMissListB.append(file)# missing in b, only found in a
                if self.mergedFileDict[file]['found'][0] == 'b':
                    self.fileMissListA.append(file)# missing in a, only found in b

    def _findDirMiss(self):
        "find each dir in merged that does not have a copy in a, then b"
        self.dirMissListA = []
        self.dirMissListB = []
        for dir in self.mergedDirDict.keys():
            if len(self.mergedDirDict[dir]['found']) == 2:
                pass # has both
            else:
                if self.mergedDirDict[dir]['found'][0] == 'a':
                    self.dirMissListB.append(dir)
                if self.mergedDirDict[dir]['found'][0] == 'b':
                    self.dirMissListA.append(dir)
        self.dirMissListA.sort()
        self.dirMissListB.sort()

    def _compFileObj(self, fileObjA, fileObjB):
        """finds difference based on mTime, cTime, size, creator, and type
        ranks most recent file first by mTime; if mTime cannot give a
        most recent, then cTime is used
        """
        reasonList = []
        reasonInt = 0
        mostrecent = None

        if fileObjA.mTime != fileObjB.mTime:
            reasonInt = reasonInt + 1
            reasonList.append('mTime')
            if fileObjA.mTime > fileObjB.mTime:
                mostrecent = 'a'
            if fileObjB.mTime > fileObjA.mTime:
                mostrecent = 'b'

        # cTime identifies as different anything that
        # has different write times, not just modification times
        # if used, cTime causes many false changes
#         if fileObjA.cTime != fileObjB.cTime:
#             reasonInt = reasonInt + 1
#             reasonList.append('cTime')
#             if mostrecent == None: # only use if value not set w/ mTime
#                 if fileObjA.cTime > fileObjB.cTime:
#                     mostrecent = 'a'
#                 if fileObjB.cTime > fileObjA.cTime:
#                     mostrecent = 'b'

        if fileObjA.size != fileObjB.size:
            reasonInt = reasonInt + 1
            reasonList.append('size')
        # only darwin/macos x
        if fileObjA.creator != fileObjB.creator:
            reasonInt = reasonInt + 1
            reasonList.append('creator')
        if fileObjA.type != fileObjB.type:
            reasonInt = reasonInt + 1
            reasonList.append('type')

        # if the files are different and there is not a mostrecent
        # there is a special problem (data corruption?)
        # must be handled carefully
        if reasonInt > 0 and mostrecent == None:
            mostrecent = 'ERROR'
            print 'ambiguity with %s' % fileObjA.relPath
            print 'mTimeA %s mTimeB %s' % (fileObjA.mTime, fileObjB.mTime)
            print 'cTimeA %s cTimeB %s' % (fileObjA.cTime, fileObjB.cTime)

        return reasonInt, reasonList, mostrecent

    def _findFileDiff(self):
        "find all files that are in a, b and are different"
        self.fileOutdateListA = [] # files outdated on a
        self.fileOutdateListB = [] # files outdated on b

        for file in self.mergedFileDict.keys():
            if len(self.mergedFileDict[file]['found']) == 2: # has both
                fileObjA = self.fileDictA[file]
                fileObjB = self.fileDictB[file]
                data = self._compFileObj(fileObjA, fileObjB)
                reasonInt, reasonList, mostrecent = data
                self.mergedFileDict[file]['diff'] = reasonInt, reasonList
                self.mergedFileDict[file]['mostrecent'] = mostrecent
                if mostrecent == 'a': # most recent a, update b
                    self.fileOutdateListB.append(file)
                elif mostrecent == 'b': # most recent b, outdated on a
                    self.fileOutdateListA.append(file)
                elif mostrecent == 'ERROR':
                    pass # cant tell which is mostrecent
                elif mostrecent == None:
                    pass # the same, no difference
            else: # not in both a, b
                self.mergedFileDict[file]['diff'] = 0, None
                self.mergedFileDict[file]['mostrecent'] = None
                
    def _displayFileDiff(self):
        fileDiffList = [] # temporary
        for file in self.mergedFileDict.keys():
            if self.mergedFileDict[file]['diff'][0] > 0: # a 
                relPathA = self.fileDictA[file].relPath
                relPathB = self.fileDictB[file].relPath
                assert relPathA == relPathB

                str1 = '%s, (%s) %s' % (relPathA, 
                                         self.mergedFileDict[file]['diff'][0],
                             ','.join(self.mergedFileDict[file]['diff'][1]))
                str2 = 'most recent: %s' % self.mergedFileDict[file]['mostrecent']

                fileDiffList.append(str1 + ': ' + str2)
        return fileDiffList


    def _findCopyAB(self):
        "list of paths to copy from a to b"
        cpAB = [] # a tp b
        mkdirB = []
        for file in self.fileOutdateListB: # outdated on b, copy from a
            A = self.fileDictA[file]
            B = self.fileDictB[file]
            src = A.absPath # source
            dst = B.absPath 
            cpAB.append((file, src, dst))
        for file in self.fileMissListB: # missing in b, copy from a
            A = self.fileDictA[file]
            #B = self.fileDictB[file] # doesnt exist in B
            src = A.absPath  
            dst = os.path.join(self.srcB, A.relPath)    
            cpAB.append((file, src, dst))
        for dir in self.dirMissListB: # missing in b, make new
            dst = os.path.join(self.srcB, dir)
            mkdirB.append(dst)
        self.cpAB = cpAB
        self.mkdirB = mkdirB

    def _findCopyBA(self):
        "list of paths to copy from b to a"
        cpBA = [] # b tp a
        mkdirA = []
        for file in self.fileOutdateListA: # outdated on a, copy from b
            A = self.fileDictA[file]
            B = self.fileDictB[file]
            src = B.absPath # source
            dst = A.absPath 
            cpBA.append((file, src, dst))
        for file in self.fileMissListA: # missing in a, copy from b
            #A = self.fileDictA[file] # doesnt exist in A
            B = self.fileDictB[file]
            src = B.absPath  
            dst = os.path.join(self.srcA, B.relPath)    
            cpBA.append((file, src, dst))
        for dir in self.dirMissListA: # missing in a, make new
            dst = os.path.join(self.srcA, dir)
            mkdirA.append(dst)
        self.cpBA = cpBA
        self.mkdirA = mkdirA

    def _processDir(self):
        for dir in (self.mkdirA + self.mkdirB):
            osTools.mkdir(dir)

    def _processFile(self):
        darwin = drawer.isDarwin()
        for file, src, dst in (self.cpBA + self.cpAB):
            if darwin:
                # ditto copies resources, as well as last-updated date
                osTools.dittoSudo(src, dst)
            else:
                osTools.cp(src, dst)

    def analyze(self):
        "do all processing necessary"
        self._findDirs()
        self._mergeDirs()
        self._mergeFiles()
        self._findDirMiss()
        self._findFileMiss()
        self._findFileDiff()
        self._findCopyAB()
        self._findCopyBA()

        #for key in fileDictA.keys():
        #    print key, fileDictA[key].size, fileDictA[key].mTime 

    def _printList(self, list):
        if len(list) == 0: pass
        for entry in list:
            if drawer.isStr(entry):
                print '\t%s' % entry
            else:
                print '\t%s\n\t%s --> \n\t%s' % (entry[0], entry[1], entry[2])

    def report(self):
        self.analyze()

        # display all files that must be movied
        print 'A: %s' % self.srcA
        print 'B: %s' % self.srcB

        print 'AB: (diff)'
        self._printList(self._displayFileDiff())

        print 'A: (mkdir)'
        self._printList(self.mkdirA)
        print 'B to A: (cp)'
        self._printList(self.cpBA)

        print 'B: (mkdir)'
        self._printList(self.mkdirB)
        print 'A to B: (cp)'
        self._printList(self.cpAB)

        # display statistics of numbers
        print 'A: %s' % self.srcA
        print 'B: %s' % self.srcB
        print '\t\t\tA\tB\tAB'
        print 'total dirs\t\t%s\t%s\t%s' % (len(self.dirListA), 
                                                  len(self.dirListB),
                                                  len(self.mergedDirDict.keys()))
        print 'total files\t\t%s\t%s\t%s' % (len(self.fileDictA.keys()), 
                                                    len(self.fileDictB.keys()),
                                                    len(self.mergedFileDict.keys()))
        print 'missing dirs\t\t%s\t%s'  % (len(self.dirMissListA), 
                                                      len(self.dirMissListB))
        print 'missing files\t\t%s\t%s' % (len(self.fileMissListA), 
                                                      len(self.fileMissListB))
        print 'outdated files\t\t%s\t%s' % (len(self.fileOutdateListA), 
                                                            len(self.fileOutdateListB))

    def update(self):
        # self.report() # call separately
        if len(self.cpBA) > 0 or len(self.cpAB) > 0:
            ok = dialog.askYesNo('\nare you sure you want to update these files?')
            if ok != 1:
                print 'no changes made'
            else:
                self._processDir() # create dirs first
                self._processFile()
        else:
            print 'files and directories are up to date!'





#-----------------------------------------------------------------||||||||||||--

def profileStr(methodStr):
    import pstats
    import profile
    statFile = osTools.tempFile('.stat.txt')         
    profile.bias = 2.02479752025e-05
    profile.run(methodStr, statFile)
    proStats = pstats.Stats(statFile)
    proStats.print_stats()
        

class Profiler:
    """wrapper for python profiler
    methodStr should be a file path to a file"""
    def __init__(self, methodStr=None, statFile=None, recalibrate=1,
                     givenCalibrationNum = 2.02479752025e-05):
        modName, ext = osTools.extSplit(methodStr, ['.py'])
        if ext != None: # its a python file
            fullPath = drawer.pathScrub(methodStr)
            dir, name = os.path.split(fullPath) # complete path
            # add to sys.path, then, couple w/ execfile command
            sys.path.insert(0, dir)
            methodStr = 'execfile(%r)' % fullPath
        else: #assume it is a method string in a name space
            pass
        if statFile != None:
            statFile = drawer.pathScrub(statFile)
        self.runProfile(methodStr, statFile, recalibrate, givenCalibrationNum)

    def test(self):
        x = []
        for each in range(3000):
            x = x + [1]
    
    def calibrator(self, numberOfTimes = 5):
        import profile
        p = profile.Profile()
        calibrator = 0
        for counter in range(numberOfTimes):
            calibrator += p.calibrate(10000)
        calibrator /= numberOfTimes
        print calibrator
        return calibrator
    
    def runProfile(self, methodStr=None, statFile=None, recalibrate=1,\
                        givenCalibrationNum = None):
        """method is already a string"""
        import pstats
        import profile

        if methodStr == None:
            methodStr = 'self.test()'
        if statFile == None:
            statFile = osTools.tempFile('.stat')
        
        if recalibrate == True:
            calibrationNum = self.calibrator()
        else:
            calibrationNum = givenCalibrationNum
            
        if givenCalibrationNum == None:
            givenCalibrationNum = 2.02479752025e-05
            
        profile.bias = calibrationNum
        profile.run(methodStr, statFile)
        proStats = pstats.Stats(statFile)
        proStats.print_stats()
        















#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--

# run tests
class test:
    def __init__(self):
        # create scratch dirs and populate with files
        self._dcPopulateDir()
        args = (self.dirA, self.dirB)
        obj = CompareDir(args) 
        obj.report()
        obj.update()
        obj = CompareDir(args) 
        obj.report()
        obj.update()

    #-----------------------------------------------------------------------||--
    def _randStr(self):
        txt = '' # to add to files
        for char in range(0, random.choice(range(10, 500))):
            txt = txt + random.choice(['a', 'b', 'c', 'd', 'e', 'f'])
        return txt

    def _randMutate(self, path):
        if random.choice(range(0,99)) % 2 == 0: # if even
            if drawer.isDarwin():
                if random.choice([0,1]) == 1:
                    osTools.rsrcSetCreator(path, 'R*ch')
                else:
                    osTools.rsrcSetCreator(path, 'TVOD', 'AIFF')


    def _randFilePopulate(self, dirA, dirB):
        """takes two dirs, random choices two file either or both, creates random
        file to and populates it with some text"""
        if dirB == None:
            options = [0]
        if dirA == None:
            options = [1]
        if dirA != None and dirB != None:
            options = [0,1,2]
        if dirA == None and dirB == None:
            return None
        for x in range(0, 5):
            r = random.choice(options)
            if r == 0:
                fPath = os.path.join(dirA, '%s.txt' % x)
                osTools.touch(fPath, self._randStr())
            if r == 1:
                fPath = os.path.join(dirB, '%s.txt' % x)
                osTools.touch(fPath, self._randStr())
            if r == 2:
                fPath = os.path.join(dirA, '%s.txt' % x)
                osTools.touch(fPath, self._randStr())
                self._randMutate(fPath)
                time.sleep(1) # delay creation times
                fPath = os.path.join(dirB, '%s.txt' % x)
                osTools.touch(fPath, self._randStr())
                self._randMutate(fPath)
        return 1

    def _randDirGen(self, dirA, dirB):
        """to be used to recursively generate directors in two branches
        if one branch is chosen to end, it maintains as and 
        """
        # random close one dir off:
        r = random.choice([0,1,2,3])
        if r == 0: dirA = None
        if r == 1: dirB = None

        # create dir if needed
        subDirList = ['__c', '__d', '__e', '__f', '__g', '__h']
        newDir = random.choice(subDirList)
        if dirA == None and dirB != None:
            osTools.mkdir(os.path.join(dirB, newDir))
            return None, os.path.join(dirB, newDir)
        if dirA != None and dirB == None:
            osTools.mkdir(os.path.join(dirA, newDir))
            return os.path.join(dirA, newDir), None
        if dirA != None and dirB != None:
            osTools.mkdir(os.path.join(dirA, newDir))
            osTools.mkdir(os.path.join(dirB, newDir))
            return os.path.join(dirA, newDir), os.path.join(dirB, newDir)
        if dirA == None and dirB == None:
            return None, None

    def _dcPopulateDir(self):
        self.dirA = os.path.join(osTools.tempDir(), '__A')
        self.dirB = os.path.join(osTools.tempDir(), '__B')
        if os.path.exists(self.dirA):
            osTools.rm(self.dirA)
        if os.path.exists(self.dirB):
            osTools.rm(self.dirB)

        osTools.mkdir(self.dirA)
        osTools.mkdir(self.dirB)
        result = self._randFilePopulate(self.dirA, self.dirB)

        a = self.dirA
        b = self.dirB
        for x in range(0,3):
            a, b = self._randDirGen(a, b)
            result = self._randFilePopulate(a, b)
            if result == None:
                break # no more paths left
