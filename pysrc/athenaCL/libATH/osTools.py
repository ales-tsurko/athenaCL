#!/usr/local/bin/python
# -----------------------------------------------------------------||||||||||||--
# Name:          osTools.py
# Purpose:       low level operating system wrappers.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2003-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import os, tempfile, time, shutil, time
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import language

lang = language.LangObj()
# do not import any higher level modules here

_MOD = "osTools.py"
from athenaCL.libATH import prefTools

environment = prefTools.Environment(_MOD)


# -----------------------------------------------------------------||||||||||||--
# extensions are expected to be stored with a leading .
# all general purpose extension groups
imageEXT = (".jpg", ".jpeg", ".tif", ".tiff", ".gif", ".png")
audioEXT = (
    ".aif",
    ".aiff",
    ".wav",
    ".wave",
    ".sd2",
    ".mp3",
    ".m4a",
    ".mp4",
    ".m4p",
    ".m4b",
    ".mka",
)
midiEXT = (".mid", ".midi", ".mp4")
videoEXT = (
    ".mov",
    ".mpg",
    ".mpeg",
    ".avi",
    ".asf",
    ".wmv",
    ".m4v",
    ".mp4",
    ".mp4v",
    ".mkv",
)
dataEXT = (".dmg", ".tar", ".zip", ".gz", ".sit", ".hqx")
codeEXT = (
    ".py",
    ".xml",
    ".c++",
    ".c",
    ".h",
    ".htm",
    ".html",
    ".mid",
    ".sco",
    ".csd",
    ".orc",
    ".bat",
    ".css",
)
textEXT = (".txt", ".doc", ".csd")
psEXT = (".ps", ".eps", ".pdf")
# bundle extensions
mediaEXT = imageEXT + videoEXT  # only common downloaded media
knownEXT = (
    imageEXT + audioEXT + videoEXT + dataEXT + codeEXT + textEXT + midiEXT + psEXT
)


# -----------------------------------------------------------------||||||||||||--
# utility functions for naming, getting files
# moved to drawer.py

# def gmtimeStr():
#     """get a gm time string in a nice format"""
#     raw = time.gmtime()
#     asc = time.asctime(raw)
#     asc = asc.replace(' ', ' ') # removie double spaces
#     asc = asc.split(' ')
#     msg = '%s, %s %s %s %s GMT' % (asc[0], raw[2], asc[1],
#                                              raw[0], asc[3])
#     return msg
#
#
# def localtimeStr():
#     """get a gm time string in a nice format"""
#     raw = time.localtime()
#     asc = time.asctime(raw)
#     asc = asc.replace(' ', ' ') # removie double spaces
#     asc = asc.split(' ')
#     msg = '%s, %s %s %s %s EST' % (asc[0], raw[2], asc[1],
#                                              raw[0], asc[3])
#     return msg
#
# def gmtimeStamp(sigDig=6, zone='gmt'):
#     "returns a string with spaced 0s, can varry signif digits"
#     if zone == 'gmt':
#         timeTuple = list(time.gmtime()) # get time tuple
#     else: # if local
#         timeTuple = list(time.localtime()) # get time tuple
#     if sigDig > 0:
#         timeTuple = timeTuple[0:sigDig] # just get first 6 elements
#     else: # remove from the front
#         timeTuple = timeTuple[abs(sigDig):6] # just get first 6 elements
#     strName = ''
#     for entry in timeTuple:
#         if entry <= 9: # small nums perceed with 0
#             strName = strName + '.0%s' % str(entry)
#         else:
#             strName = strName + '.%s' % str(entry)
#     strName = strName[1:] # remove leading .
#     return strName
#
#
# def localtimeStamp(sigDig=6):
#     "returns a string with spaced 0s, can varry signif digits"
#     return gmtimeStamp(sigDig, 'local')
#
# def tempDir(tempPath='/Volumes/xdisc/_scratch'):
#     "get a temp directory"
#     if not os.path.exists(tempPath): # use temp dir if doesnt exist
#         tempPath = tempfile.mkdtemp()
#         environment.printWarn([lang.WARN, 'using %s as scratch directory' % tempPath])
#     return tempPath
#
# def tempFileName(ext):
#     return gmtimeStamp() + ext
#
# def tempFile(ext='.txt', fpDir=''):
#     """make temp file in temp dir, otherwise get standard temp file
#     branch by platform and do different things here
#
#     note: compare with developing method in prefTools.py
#     """
#     fpDir = tempDir(fpDir)
#     if not os.path.exists(fpDir): # use temp file
#         tempPath = tempfile.mktemp(ext)
#     else:
#         tempName = gmtimeStamp() + ext
#         tempPath = os.path.join(fpDir, tempName)
#     return tempPath

# -----------------------------------------------------------------||||||||||||--
# messagge formatting for standard output


def alertMsg(str="", prepend=""):
    print("%s--||||||||||||-- %s" % (prepend, str))


def cmtAlert(str="", prepend="#"):
    return "%s--||||||||||||-- %s\n" % (prepend, str)


def cmtHalfStr():
    return "      #" + "-" * 70 + "--||--\n"


def cmtFullStr():
    return "#" + "-" * 63 + "--||||||||||||--\n"


# -----------------------------------------------------------------||||||||||||--
# posix commands

PROMPTdarwin = "%s %s: (user password required)."
PROMPTposix = "%s %s: (superuser password required)."


def less(path, line=1):
    if os.name == "posix":  # create launch script
        if line <= 0:
            line = 1
        # -M info line
        # -e quite after run
        # -w highlights last line
        # -z-2 scoress -2 height
        # + starts at this line
        # -~ turns off tildes for eof
        cmdStr = "less -M -e -w -~ -z-3 +%s %s" % (line, path)
        os.system(cmdStr)


def touch(path, str=None):
    if os.name == "posix":  # create launch script
        os.system("touch '%s'" % path)
        if str != None:  # append to newly created file
            os.system("echo '%s' > %s" % (str, path))


def tag(src, ext, tagString):
    """changes a file by inserting a tagString before extension
    expects src to have the extension on it already
    """
    dir, name = os.path.split(src)
    if ext[0] != ".":  # add period if missing
        ext = "." + ext
    lenStub = len(name) - len(ext)
    tagName = name[:lenStub] + "-" + tagString + name[lenStub:]
    tagPath = os.path.join(dir, tagName)
    return tagPath


# -----------------------------------------------------------------||||||||||||--


def rmdir(path):
    if os.name == "posix":
        os.system('rmdir "%s"' % path)
    else:  # mac, windows
        os.rmdir(path)


def rm(path):
    if path == os.sep:
        raise ValueError("macro remove canceled")  # safety
    if os.name == "posix":
        os.system('rm -f -r "%s"' % path)
    else:  # mac, windows
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)


def rmSudo(path, sudoFound=None):
    """sudo is not avail on all plats, so su root on other nixes"""
    if path == os.sep:
        raise ValueError("macro remove canceled")  # safety
    if os.name == "posix":
        if sudoFound == None:  # test
            sudoFound = drawer.isSudo()  # 1 if exists
        if drawer.isDarwin() or sudoFound:
            print(PROMPTdarwin % ("removing", path))
            os.system('sudo rm -f -r "%s"' % path)
        else:  # other *nixes
            print(PROMPTposix % ("removing", path))
            os.system('su root -c "rm -f -r %s"' % path)
    else:  # mac, windows
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)


def cp(src, dst):
    """alwaws does a recursive backup"""
    if os.name == "posix":
        os.system('cp -r "%s" "%s"' % (src, dst))
    else:  # mac, windows
        if os.path.isdir():
            shutil.copytree(src, dst)
        else:  # assume a file
            shutil.copyfile(src, dst)


def cpTag(src, ext, tagString):
    "copies a file by inserting a tagString before extension"
    tagPath = tag(src, ext, tagString)
    cp(src, tagPath)
    return tagPath


def cpSudo(src, dst, sudoFound=None):
    """sudo is not avail on all plats, so su root on other nixes"""
    if os.name == "posix":
        if sudoFound == None:  # test
            sudoFound = drawer.isSudo()  # 1 if exists
        if drawer.isDarwin() or sudoFound:
            print(PROMPTdarwin % ("writing", dst))
            os.system("sudo cp %s %s" % (src, dst))
        else:  # other *nixes
            print(PROMPTposix % ("writing", dst))
            os.system('su root -c "cp %s %s"' % (src, dst))
    else:  # mac, windows
        if os.path.isdir():
            shutil.copytree(src, dst)
        else:  # assume a file
            shutil.copyfile(src, dst)


def cpTagSudo(src, ext, tagString, sudoFound=None):
    "copies a file by inserting a tagString before extension"
    tagPath = tag(src, ext, tagString)
    cpSudo(src, tagPath, sudoFound)
    return tagPath


def mv(src, dst):
    if os.name == "posix":
        os.system('mv "%s" "%s"' % (src, dst))
    else:  # mac, windows
        shutil.move(src, dst)


def mvTag(src, ext, tagString):
    "moves a file by inserting a tagString before extension"
    tagPath = tag(src, ext, tagString)
    mv(src, tagPath)
    return tagPath


def mvSudo(src, dst, sudoFound=None):
    """sudo is not avail on all plats, so su root on other nixes"""
    if os.name == "posix":
        if sudoFound == None:  # test
            sudoFound = drawer.isSudo()  # 1 if exists
        if drawer.isDarwin() or sudoFound:
            print(PROMPTdarwin % ("moving", dst))
            os.system("sudo mv %s %s" % (src, dst))
        else:  # other *nixes
            print(PROMPTposix % ("moving", dst))
            os.system('su root -c "mv %s %s"' % (src, dst))
    else:  # mac, windows
        shutil.move(src, dst)


def mkdir(path, flagStr=""):
    if os.name == "posix":
        os.system("mkdir %s '%s'" % (flagStr, path))
    else:
        os.mkdir(path)  # not recusive


def mkdirSudo(path, sudoFound=None, flagStr=""):
    """sudo is not avail on all plats, so su root on other nixes"""
    if os.name == "posix":
        if sudoFound == None:  # test
            sudoFound = drawer.isSudo()  # 1 if exists
        if drawer.isDarwin() or sudoFound:
            print(PROMPTdarwin % ("writing directory", path))
            os.system("sudo mkdir %s %s" % (flagStr, path))
        else:  # other *nixes
            print(PROMPTposix % ("writing directory", path))
            os.system('su root -c "mkdir %s %s"' % (flagStr, path))
    else:
        os.mkdir(path)


def chmod(
    value,
    path,
):
    if os.name == "posix":
        if not drawer.isStr(value):
            value = str(value)
        os.system("chmod %s '%s'" % (value, path))


def chmodSudo(value, path, sudoFound=None):
    """sudo is not avail on all plats, so su root on other nixes"""
    if os.name == "posix":
        if not drawer.isStr(value):
            value = str(value)
        if sudoFound == None:  # test
            sudoFound = drawer.isSudo()  # 1 if exists
        if drawer.isDarwin() or sudoFound:
            print(PROMPTdarwin % ("changing permissions", path))
            os.system('sudo chmod %s "%s"' % (value, path))
        else:  # other *nixes
            print(PROMPTposix % ("changing permissions", path))
            os.system('su root -c "chmod %s %s"' % (value, path))


# -----------------------------------------------------------------||||||||||||--
def md5checksum(filePath):
    """return an md5 checksum for a file

    TODO: update with hashlib
    """
    import md5  # this is depcreated; use hashlib

    print(_MOD, "mpd5 obtained from:", filePath)
    f = open(filePath)
    msg = f.read()
    f.close()
    val = md5.new(msg).hexdigest()
    print(_MOD, "md5:", val)
    return val


def man(path):
    cmd = "nroff -man %s | less" % path
    os.system(cmd)


# -----------------------------------------------------------------||||||||||||--
# posix commands, relying on external command line utils


def curlFtpUplad(srcPath, dstPath, user, pswd):
    # need quotes around user and password incase of crazy chars
    # -m is max transfer time; not set here as does not seem to make a difference
    cmdStr = 'curl -# --max-time 2048 -T %s -u "%s":"%s" ftp://%s' % (
        srcPath,
        user,
        pswd,
        dstPath,
    )
    os.system(cmdStr)


def curlFtpDelete(path, user, pswd, dummy="__init__.py"):
    # curl must access a file before executing a -q command
    # w/o -O or -T, will print file to stdio
    # must have a dummy file in the ftp dir that a deletion is desired
    # must cd to temp dir to avoid downloading and overwriting

    # assume that dummy file is py __init__.py
    # could optionally upload this file if not provided
    stub, name = os.path.split(path)
    # create new dummy path
    dummyPath = os.path.join(stub, dummy)
    cmdStr = 'curl -# -u "%s":"%s" ftp://%s -Q "-DELE %s" ' % (
        user,
        pswd,
        dummyPath,
        name,
    )
    os.system(cmdStr)


def tarGzip(path):
    "tars and gzips a directory"
    dir, name = os.path.split(path)
    tarName = "%s.tar" % name
    tarPath = os.path.join(dir, tarName)

    # -C changes cd for tar session
    cmdStr = "tar -C %s -cf %s %s" % (dir, tarPath, name)
    os.system(cmdStr)

    cmdStr = "gzip %s" % tarPath
    os.system(cmdStr)
    gzipPath = "%s.gz" % tarPath
    return gzipPath


def zip(path):
    "creates a zip of a dir"
    dir, name = os.path.split(path)
    cmdStr = "cd %s; zip -r %s %s" % (dir, name, name)
    os.system(cmdStr)
    zipPath = "%s.zip" % path
    return zipPath


def cvsCheckout(dstDir, pserver, package):
    "uses cvs to get a package from pserver a drop it in dstDir"
    currentDir = os.getcwd()
    os.chdir(dstDir)  # need to be in dir
    cmds = (
        "cvs -d:pserver:%s login" % pserver,
        "cvs -z3 -d:pserver:%s co %s" % (pserver, package),
    )
    for cmd in cmds:
        os.system(cmd)
    os.chdir(currentDir)  # return to previous dir


# cvs -d:pserver:ariza@cvs.sourceforge.net:/cvsroot/athenacl login
# cvs -z3 -d:pserver:ariza@cvs.sourceforge.net:/cvsroot/athenacl co athenaCL


def cvsSshCheckout(dstDir, pserver, package):
    "uses cvs to get a package from pserver a drop it in dstDir"
    currentDir = os.getcwd()
    os.chdir(dstDir)  # need to be in dir
    cmds = ("cvs -z3 -d:ext:%s co %s" % (pserver, package),)
    for cmd in cmds:
        os.system(cmd)
    os.chdir(currentDir)  # return to previous dir


def pdfMerge(fileDst, fileList):
    """uses ghostscript to merge pdf files into a new file"""
    if drawer.isStr(fileList):
        fileList = [
            fileList,
        ]
    cmd = "gs -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=%s " % fileDst
    for file in fileList:
        cmd = cmd + "%s " % file
    os.system(cmd)


def epsToJpg(srcPath, dstPath, rez=300, q=100, size=100):
    """convert and eps to a jpg with imagemagick"""
    if size != 100:
        sizeStr = "-geometry %s" % size + "%"  # make into a percent
    else:
        sizeStr = ""

    cmd = "convert %s -density %sx%s -quality %s %s %s" % (
        sizeStr,
        rez,
        rez,
        q,
        srcPath,
        dstPath,
    )
    os.system(cmd)


def jpgToTxt(srcPath, dstPath=None):
    """character recognition w/ gocr
    http://jocr.sourceforge.net/links.html
    use djpeg to convert to bpm
    note: this works very poorly
    """
    if dstPath == None:
        dir, name = os.path.split(srcPath)
        name, ext = extSplit(name)
        dstPath = os.path.join(dir, "%s-ocr.txt" % name)

    # pnm is the default, can be bmp
    cmd = "djpeg -pnm -gray %s | /usr/local/bin/gocr -f ASCII -o %s" % (
        srcPath,
        dstPath,
    )
    os.system(cmd)


# -----------------------------------------------------------------||||||||||||--
# darwin commands (not cross platform)


def ditto(src, dst):
    "copies a file w/ resources, only on darwin/macos x"
    os.system("ditto -rsrcFork '%s' '%s'" % (src, dst))


def dittoSudo(src, dst):
    os.system("sudo ditto -rsrcFork '%s' '%s'" % (src, dst))


def rsync(src, dst):
    if not src.endswith(os.sep):
        srcLead = src + "/"  # provides symmetrical behaviour
    if not dst.endswith(os.sep):
        dstLead = dst + "/"  # provides symmetrical behaviour
    os.system("rsync -auvz '%s' '%s'" % (srcLead, dst))


def osascript(lineList):
    "call an applescript as a list of applescript code lines"
    msg = []
    for entry in lineList:
        # remove blank lines
        if entry == "":
            continue
        msg.append(" -e '%s'" % entry)
    cmdStr = "osascript -l AppleScript %s" % "".join(msg)
    os.system(cmdStr)


def rez(path, creatorCode, typeCode, rsrcFilePath):
    flags = " -c " + creatorCode + " -t " + typeCode + " -o " + path
    cmdStr = "Rez " + rsrcFilePath + flags
    os.system(cmdStr)


def mountAfp(user, pswd, ip, dirVol):
    """mounts a afp drive; checks to see if it exists"""
    if not os.path.exists(dirVol):
        mkdir(dirVol)
        dir, vol = os.path.split(dirVol)
        cmdStr = 'mount_afp "afp://%s:%s@%s/%s" %s' % (user, pswd, ip, vol, dirVol)
        os.system(cmdStr)
    else:
        print("%s already exists." % dirVol)


def unmount(dirVol):
    os.system("umount %s" % dirVol)


def rsrcSetCreator(path, creator, type=None):
    if drawer.isCarbon():
        import Carbon.File

        fss = Carbon.File.FSSpec(path)
        finfo = fss.FSpGetFInfo()
        finfo.Creator = creator
        if type != None:
            finfo.Type = type
        fss.FSpSetFInfo(finfo)
    else:
        import macfs

        f = macfs.FSSpec(path)
        f.SetCreatorType(creator, type)


def rsrcGetCreator(path):
    if drawer.isCarbon():
        import Carbon.File

        fss = Carbon.File.FSSpec(path)
        finfo = fss.FSpGetFInfo()
        creator = finfo.Creator
        type = finfo.Type
    else:
        import macfs

        f = macfs.FSSpec(path)
        creator, type = f.GetCreatorType()
    return creator, type


def hide(path):
    "darwin/macos only: hides a file using SetFile"
    cmdStr = "SetFile -a V %s" % path
    os.system(cmdStr)


def dmg(version, path, readmePath=None, dmgRsrc=None, vTag=1):
    """creates a .dmg of a dir;
    path is the path to the dir that needs to be archived
    name is taken from name at end of path
    vTag = 1 means a version tagged copy is made with normal name
    """
    currentDir = os.getcwd()  # used only to return to

    buildDir, name = os.path.split(path)
    os.chdir(buildDir)  # need to be in dir where depositing archive

    if name in os.listdir("/Volumes"):
        raise Exception("a volume is in the way! remove it!")

    # make a folder to wrap image contents
    tmpDir = os.path.join(tempDir(), "dmgBuild")
    tmpPath = os.path.join(tmpDir, "%s" % name)
    ditto(path, tmpPath)  # copy original to inner folder
    # create message
    if readmePath == None:
        pass
    elif readmePath == "install":
        msgPath = os.path.join(tmpDir, "install.txt")
        str = (
            "To install %s, drag the %s folder to your Applications folder. Double click %s.app to start the program."
            % (name, name, name)
        )
        touch(msgPath, str)  # creates file and writes string
    else:
        readmeDir, readmeName = os.path.split(readmePath)
        msgPath = os.path.join(tmpDir, readmeName)
        ditto(readmePath, msgPath)
    # copy rsrc to dmg (for background, icons, etc)
    if dmgRsrc != None:
        for rsrcPath in dmgRsrc:
            rsrcDir, rsrcName = os.path.split(rsrcPath)
            dstPath = os.path.join(tmpDir, rsrcName)
            ditto(rsrcPath, dstPath)  # copy to volume

    dmgName = "%s-%s.dmg" % (name, version)
    dmgPath = os.path.join(buildDir, dmgName)
    dmgNameShort = "%s.dmg" % name
    dmgPathShort = os.path.join(buildDir, dmgNameShort)

    # used to store device id
    tmpDeviceTxtPath = os.path.join(buildDir, "tmpDeviceID.txt")

    # this is alreayd done once but it essential
    os.chdir(buildDir)  # need to be in dir where depositing archive
    # execute command
    cmdList = (
        "hdiutil create -megabytes 40 %s -layout NONE" % dmgNameShort,
        "hdid -nomount %s > %s" % (dmgNameShort, tmpDeviceTxtPath),
    )
    for cmdStr in cmdList:
        os.system(cmdStr)

    # get device id from text string
    f = open(tmpDeviceTxtPath, "r")
    txtLines = f.readlines()
    f.close()
    deviceStr = txtLines[0].strip()

    # finish commands
    cmdList = (
        "newfs_hfs -v %s %s" % (name, deviceStr),  # new fs
        "hdiutil eject %s" % (deviceStr),  # eject
        "hdid %s" % (dmgNameShort),
    )  # remount to write to
    for cmdStr in cmdList:
        os.system(cmdStr)

    # copy dirs to volume
    ditto(tmpDir, "/Volumes/%s/" % (name))  # copy to volume

    if dmgRsrc != None:
        print("Customize dmg now, then press return")
        os.system("read ")  # wait for return form user
        ### break to make manual adjustments
    # hide resource files, if around
    if dmgRsrc != None:
        for rsrcPath in dmgRsrc:  # already moved, have to change path
            rsrcDir, rsrcName = os.path.split(rsrcPath)
            dstPath = os.path.join(("/Volumes/%s" % name), rsrcName)
            hide(dstPath)  # uses a sytem find, not . pre thing

    # final commands
    cmdList = (
        "hdiutil eject %s" % (deviceStr),  # eject
        "hdiutil convert -format UDZO %s -o %s" % (dmgNameShort, dmgName),
        "rm %s" % dmgNameShort,
    )  # remove short
    for cmdStr in cmdList:
        os.system(cmdStr)

    # remove temporary files
    rm(tmpDir)
    rm(tmpDeviceTxtPath)

    # make a copy of dmg w/o version number
    ditto(dmgPath, dmgPathShort)
    if vTag != 1:  # dont keep the version tagged copy
        rm(dmgPath)
    # return dir
    os.chdir(currentDir)
    return dmgPath


# -----------------------------------------------------------------||||||||||||--
# path utilities


def extSplit(name, extList=None):
    """split name, extension; if extList is given, find only w/n this list
    return wholeName (even if a path), None if ext not found
    all '.' are dropped from both name and ext

    >>> extSplit('testing/this.py', ['.py'])
    ('testing/this', '.py')
    """
    if extList == None:
        extList = knownEXT  # search all known extensions
    nameStub = name
    foundExt = ""
    for ext in extList:
        if name[-len(ext) :].lower() == ext:  # if has this ext
            nameStub = name[: -len(ext)]
            foundExt = ext
            break
    if nameStub == name:  # no extension foudn
        return nameStub, None
    else:  # check for periods, extension should have leading period
        if nameStub[-1] == ".":
            nameStub = nameStub[:-1]
        if foundExt[0] != ".":  # start with leading period
            foundExt = "." + foundExt
        return nameStub, foundExt


def dirGather(searchDir, extList):
    """searches a dir for files that match a given list of
    of file extensions. returns a list of the names of these files.
    not recursive
    """
    dirContent = os.listdir(searchDir)
    selNames = []
    selPaths = []
    for entry in dirContent:
        for ext in extList:
            if entry[-len(ext) :] == ext:
                selNames.append(entry)
                selPaths.append(os.path.join(searchDir, entry))
                break
    return selNames, selPaths


def pathTrimStub(path, stub=None):
    """takes a path and removes the parent stub component
        path should always be longer then stub

    >>> pathTrimStub('this/is/a/long/path', 'this/is/a')
    'long/path'

    """
    if stub == None:
        return path  # do nothing
    stubList = stub.split(os.sep)
    pathList = path.split(os.sep)
    relList = pathList[len(stubList) :]
    relPath = ""
    for dir in relList:
        relPath = os.path.join(relPath, dir)
    return relPath


# -----------------------------------------------------------------||||||||||||--
def launch(pathExe):
    """a mulitplatform solution to launching a file
    can be used to run an executable script or file
    media files should use open below
    used for launching .bat files in elr commands as well"""
    failFlag = None
    #     if os.name == 'mac': # FUTURE: elr should launch csd file?
    #         import findertools
    #         try: findertools.launch(pathExe)
    #         except: failFlag = 'failed'
    #         del findertools
    if os.name == "posix":
        try:
            exitStatus = os.system(pathExe)
            # if not equal to zero an exit error has occured
            if exitStatus != 0:
                failFlag = "failed"
        except:
            failFlag = "failed"
    else:  # win or other
        try:  # spawns a new, detached process
            # this seems to be the best solution
            # same as win32api.ShellExecute()
            os.startfile(pathExe)
            # this works on most plats, but opens a new console window
            # os.system('start %s' % (pathExe))
            # this never actually gave a detached process on nt
            # os.spawnv(os.P_NOWAIT, pathExe, ['',])    # used to be P_DETACH
        except:
            failFlag = "failed"
        if failFlag == "failed":
            failFlag = None  # reset
            try:  # try second method if above method doesnt work
                os.system(pathExe)
            except:
                failFlag = "failed"
    return failFlag


def openMedia(path, prefDict=None):
    """open a media or text file, file type is determined by extension
    will assume that path is to a media file, rather than an exe
    for executable scripts, use launch
    if prefDict is provided, will get app path from there
    keys in this disc must start w/ media type; image, audio, midi, text, ps


    TODO: this should be updated to use application preferences
    stored in prefTools.py, not here
    """
    path = drawer.pathScrub(path)
    dir, name = os.path.split(path)
    name, ext = extSplit(name)

    # this should be as method of a the pref tools
    # pref object/dict, or a function in this module or drawer
    if ext in imageEXT:
        fileType = "image"
    elif ext in audioEXT:
        fileType = "audio"
    elif ext in videoEXT:
        fileType = "video"
    elif ext in midiEXT:
        fileType = "midi"
    elif ext in textEXT or ext in codeEXT:
        fileType = "text"
    elif ext in psEXT:
        fileType = "ps"
    else:
        fileType = None

    app = None  # default nothing

    if prefDict == None and fileType != None:  # get default apps
        #         if os.name == 'mac': pass # rely on system
        if os.name == "posix":
            if drawer.isDarwin():  # assume sys default for most
                if fileType in ["audio", "midi", "video"]:
                    app = "/Applications/QuickTime Player.app"
            else:  # other unix
                if fileType == "text":
                    app = "more"
                elif fileType == "audio":
                    app = "xmms"  #'play' should work too
                elif fileType == "midi":
                    app = "playmidi"  #
                elif fileType == "image":
                    app = "imagemagick"
                elif fileType == "ps":
                    app = "gs"
        else:  # win or other
            pass  # rely on system
    elif fileType != None:  # get from prefDict
        for key in list(prefDict.keys()):
            # match by filetype string leading key and path string
            if key.startswith(fileType) and "path" in key.lower():
                app = prefDict[key]  # may be a complete file path, or a name

    if app == "":
        app = None  # if given as empty, convert to none
    elif not drawer.isApp(app):
        app = None  # if not an app any more, drop

    #     if os.name == 'mac':     # os9
    #         cmdExe = '%s' % path # on mac, just launch txt file, rely on pref
    if os.name == "posix":
        if drawer.isDarwin():
            if app == None:  # no app use system default
                cmdExe = 'open "%s"' % path
            elif app.lower().endswith(".app"):  # if a .app type app
                cmdExe = 'open -a "%s" "%s"' % (app, path)
            else:  # its a unix style command
                cmdExe = "%s %s" % (app, path)
        else:  # other unix
            if app == None:
                cmdExe = "%s" % (path)
            else:
                cmdExe = "%s %s" % (app, path)
    else:  # win or other, rely on system settings
        cmdExe = "%s" % path  # on win, just launch path
    return launch(cmdExe)  # returns None on success


# -----------------------------------------------------------------||||||||||||--
# python, ath utilies


def findSiteLib():
    """this replaces site.here, which is no longer around after python 2.3
    /System/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3
    sys.prefix: (note that exec_prefix is also possible)
    '/System/Library/Frameworks/Python.framework/Versions/2.3'
    the solution below seems to be the only good cross platform solution
    """
    return os.path.dirname(os.__file__)


def findSitePackages():
    """same as a above, but add site-packages"""
    return os.path.join(os.path.dirname(os.__file__), "site-packages")


def findFinkDir():
    """this command only works on unix systems
    finds base fink dir stub
    retuns None on error: means no fink installation
    """
    if os.name == "posix":  # create launch script
        import subprocess

        msg = subprocess.getoutput("fink dumpinfo -p %p fink")
        # last line is somethign like: %p: /sw
        msgStr = msg.split("\n")[-1]  # get last if more tn 1 line
        if msgStr.find("command not found") >= 0:  # cant find fink command
            if os.path.exists("/sw/bin/fink"):
                return "/sw"
            else:
                return None
        else:
            preface = "%p: "
            if msgStr.startswith(preface):
                msgStr = msgStr.replace(preface, "")
            return msgStr  # return just directory string
    else:
        return None


def findSubDir(goal="athenaCL"):
    """recurse up a path search for dir"""
    srcPath = os.getcwd()
    while 1:
        path, dir = os.path.split(srcPath)
        if dir == goal:
            return srcPath
        if path == "" or dir == "":
            return None  # nowhere else to go
        srcPath = path  # reassign


def findManPath(group=1, altSys=None):
    """on unix opperating systems find man path for given group
    returns None of no man path found
    altSys sets options for specific sytems: fink
    """
    if os.name != "posix":
        return None
    # common places for man directories to resside
    commonManDirs = ["/usr/share/man/", "/usr/local/man", "/usr/man"]
    # check system type
    if altSys == None:
        dirs = commonManDirs
    elif altSys == "fink":
        finkStub = findFinkDir()
        if not finkStub == None:  # fink exists
            dirs = [os.path.join(finkStub, "share", "man")]
        else:  # use common dirs
            dirs = commonManDirs
    else:
        raise ValueError("bad system alternate option given")
    found = []
    for path in dirs:
        if os.path.isdir(path):
            manDir = "man%s" % group
            manDirPath = os.path.join(path, manDir)
            if os.path.isdir(manDirPath):  # check this group exists
                found.append(manDirPath)
    if found == []:
        return None
    else:
        return found[0]


def _idlePathCandidate():
    idlePath = []
    idlePath.append(os.path.join(os.path.dirname(findSiteLib()), "Tools", "idle"))
    idlePath.append(os.path.join(findSiteLib(), "idlelib"))


def findIdle():
    "finds idle on various platforms; returns dir with idle.py"
    # all platforms use one of these forms
    idlePath = []
    idlePath.append(os.path.join(os.path.dirname(findSiteLib()), "Tools", "idle"))
    idlePath.append(os.path.join(findSiteLib(), "idlelib"))
    # python 2.3 has changed the location of idle on win
    # site.here is "lib" dir in Python dir; must go up to tools
    # dont need to move up from site.here; Tools below site.here
    # py2.3 in macos x as framework install

    for path in idlePath:  # search list of possible paths
        if os.path.isdir(path) == 1:  # if a directory
            dirOfIdlePath = os.listdir(path)
            if "idle.py" in dirOfIdlePath:
                return path
            else:
                pass
        else:
            pass
    return None  # if nothing found


# -----------------------------------------------------------------||||||||||||--
# utilities used during installatioin


def findBinPath(optFink=0):
    """get path to launcher dir file on posix systems"""
    if os.name != "posix":
        return None
    if optFink:  # fink on darwin
        finkStub = findFinkDir()
        if not finkStub == None:  # if fink installed, release, other default
            return os.path.join(finkStub, "bin")
    # default for all unix systesms
    return "/usr/local/bin"


def findAthBinPath(optFink=0):
    """get path to launcher dir file on posix systems"""
    if os.name != "posix":
        return None
    dir = None
    if optFink:  # fink on darwin
        finkStub = findFinkDir()
        if not finkStub == None:  # if fink installed, release, other default
            dir = os.path.join(finkStub, "bin")
    if dir == None:
        # default for all unix systesms
        dir = "/usr/local/bin"
    # launcher is one word lower case
    return os.path.join(dir, "athenacl")


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
