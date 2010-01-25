#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          setup.py
# Purpose:       provides setup features for athenaCL install.
#                    loads large modules
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import sys, os

#-----------------------------------------------------------------||||||||||||--
try: import libATH #assume we are in package dir
except ImportError:
    try: from athenaCL import libATH
    except ImportError: print 'athenaCL package cannot be found'; sys.exit()
fpLibATH = libATH.__path__[0] # list, get first item
if not os.path.isabs(fpLibATH): #relative path, add cwd
    fpLibATH = os.path.abspath(fpLibATH)
fpSrcDir = os.path.dirname(fpLibATH) # athenaCL dir
fpPackageDir = os.path.dirname(fpSrcDir) # outer dir tt contains athenaCL dir
if fpPackageDir not in sys.path: sys.path.append(fpPackageDir)
#-----------------------------------------------------------------||||||||||||--
_MOD = 'setup.py'

from athenaCL.libATH import dialog
from athenaCL.libATH import athenaObj
from athenaCL.libATH import drawer
from athenaCL.libATH import argTools
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import osTools
from athenaCL.libATH import info

from athenaCL.libATH import prefTools
reporter = prefTools.Reporter(_MOD)
reporter.status = 1 # force printing on regardless of debug pref


#-----------------------------------------------------------------||||||||||||--
# optional imports supports creation of meta-packages
try: import bdist_mpkg
except ImportError: pass


# can use this to automatically upload to pypi
# setup.py bdist_egg upload



#-----------------------------------------------------------------||||||||||||--
# assume right permission for writing in the pth destination

# note that .pth file writing does not seem necessary, as using the 
# atheancl.py launcher adds paths to sys.path, for non site packages install
# and, most will install in site-packages, so .pth is not necessary


# def writePthLoader(athenaDir):
#     """a pth file named athenaCL.pth can be placed in site-packages
#     to give the path to the outer dir (not athenaCL dir), 
#     allowing easy imports w/o having to move files..."""
#     reporter.printDebug('writing pth file')
#     # get dir outside of athenaCL dir
#     # allows from athenaCL.libATH import ...
#     msg = '%s\n' % os.path.dirname(athenaDir)
#     dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
#     try:
#         f = open(dst, 'w')      
#         f.write(msg)
#         f.close()
#     except IOError: 
#         reporter.printDebug(lang.msgFileIoError % dst)
# 
# def removePthLoader(sudoFound=None):
#     """remove old pth loader"""
#     reporter.printDebug('removing outdated pth file')
#     dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
#     if os.path.exists(dst):
#         osTools.rmSudo(dst, sudoFound)
#     else:
#         reporter.printDebug('no pth file exists')
#         
# def reportPthLoader(sudoFound=None):
#     """remove old pth loader"""
#     dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
#     if os.path.exists(dst):
#         print _MOD, 'pth file exists: %s' % dst
#         f = open(dst)
#         msg = f.read()
#         f.close()
#         reporter.printDebug('pth contents:', msg.strip())
#     else:
#         reporter.printDebug('no pth file exists')
#         
        
#-----------------------------------------------------------------||||||||||||--          
def writeUnixLauncher(pathLaunchScript, pathShellScript, optInstallTool=0,
                             sudoFound=None):
    """used to create shell scripts that act as application launcher
    creates file in local directory first, using paths in args
    will optional move to /usr/local/bin if optInstallTool is 1
    pathLaunchScript is the path to the python file
    pathShellScript is the path to the shell script to be written\
    if optInstallTool == 2; case were to assume already root
    """
    reporter.printDebug('writing launcher script:\n%s' % pathLaunchScript)
    pythonExe = sys.executable
    # get name of shell script
    dir, name = os.path.split(pathShellScript)
    # sets command line options: -O for optimized 
    # sets -u for unbuffered standard out
    launchScript = '#!/bin/sh \n%s -O -u %s $*\n\n' % (pythonExe, 
                                                      pathLaunchScript)
    # erase if already exists
    if os.path.exists(pathShellScript):
        if optInstallTool <= 1:   # use sudo
            osTools.rmSudo(pathShellScript, sudoFound)
        elif optInstallTool == 2: # do not use sudo
            osTools.rm(pathShellScript)
    # touch a file first
    # always write a basic script in local dirs
    try:
        f = open(pathShellScript, 'w')  # test opening the file
        f.close()
        permissionError = 0
    except IOError:
        permissionError = 1
    if permissionError: # try to change mod of parent dir
        dir, name = os.path.split(pathShellScript)
        osTools.chmodSudo(775, dir, sudoFound)
    # try again w/ changed permissions
    try:
        f = open(pathShellScript, 'w')      
        f.write(launchScript)
        f.close()
        osTools.chmod(775, pathShellScript)
    except IOError:
        reporter.printDebug(lang.msgFileIoError % pathShellScript)

    # optionally move this script to /usr/local/bin
    if optInstallTool >= 1: # install tool into /usr/local/bin
        binPath = osTools.findBinPath()
        flagStr = '-p' # create intermediate dirs as required
        dstPath = os.path.join(binPath, name)
        print _MOD, 'installing launcher script:\n%s' % dstPath
        if not os.path.exists(binPath): # create directory
            if optInstallTool == 1: # use sudo
                osTools.mkdirSudo(binPath, sudoFound, flagStr)
            if optInstallTool == 2: # already root
                osTools.mkdir(binPath, flagStr)
        # mv launcher script to dir
        if optInstallTool == 1: # use sudo, get permissioin
            osTools.mvSudo(pathShellScript, dstPath, sudoFound)
        elif optInstallTool == 2: # already root
            osTools.mv(pathShellScript, dstPath)

def removeUnixLauncher(sudoFound=None):
    """only remove if it is found within /usr/local/bin"""
    reporter.printDebug('removing athenacl unix launcher')
    
    dst = osTools.findAthBinPath()
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        reporter.printDebug('no athenacl unix launcher exists (%s)' % dst)
            
def reportUnixLauncher():
    """only remove if it is found within /usr/local/bin"""  
    dst = osTools.findAthBinPath()
    if os.path.exists(dst):
        reporter.printDebug(['athenacl unix launcher exists:', dst])
        f = open(dst)
        msg = f.read()
        f.close()
        reporter.printDebug(['launcher contents:', msg.strip()])
    else:
        reporter.printDebug('no athenacl unix launcher exists (%s)' % dst)
        
        
#-----------------------------------------------------------------||||||||||||--
def copyMan(athenaDir, sudoFound=None):
    """if install tool == 1, use sudo
    if install tool == 2, assume already root"""
    reporter.printDebug('copying manual-page file')
    manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    if manDir == None: return None
    src = os.path.join(athenaDir, 'doc', info.MANFILE)
    dst = os.path.join(manDir, info.MANFILE)
    osTools.cpSudo(src, dst, sudoFound)

def removeMan(sudoFound=None):
    """removing man file"""
    reporter.printDebug('removing manual-page file')
    manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    if manDir == None: return None

    dst = os.path.join(manDir, info.MANFILE)
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        reporter.printDebug('no athenacl manual-page exists (%s)' % dst)

def reportMan():
    manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    if manDir == None:
        reporter.printDebug('no manual directory found')
        return None
    dst = os.path.join(manDir, info.MANFILE)
    if os.path.exists(dst):
        reporter.printDebug(['man path exists:', dst])
    else:
        reporter.printDebug('no athenacl manual-page exists (%s)' % dst)


#-----------------------------------------------------------------||||||||||||--
def _getPackagesList():
    """list of all packages, delimited by period"""
    pkg = (  'athenaCL', 
             'athenaCL.demo', 
             'athenaCL.libATH', 
             'athenaCL.libATH.libGfx', 
             'athenaCL.libATH.libOrc', 
             'athenaCL.libATH.libPmtr', 
             'athenaCL.libATH.libTM', 
             'athenaCL.libATH.omde', 
             )
    return pkg

def _getClassifiers():
    classifiers = [
             'Development Status :: 5 - Production/Stable',
             'Environment :: Console',
             'Intended Audience :: End Users/Desktop',
             'Intended Audience :: Developers',
             'License :: OSI Approved :: GNU General Public License (GPL)',
             'Natural Language :: English', 
             'Operating System :: MacOS',
             'Operating System :: Microsoft :: Windows',
             'Operating System :: POSIX',
             'Operating System :: OS Independent',
             'Programming Language :: Python',
             'Topic :: Multimedia :: Sound/Audio',
             'Topic :: Artistic Software',
             ]
    return classifiers
     
# def _pkgDataManager():
#     """there are 2 methods to install data files; package_data is best, 
#     but is only defined for python 2.4 and later; this will check
#     and provide the necessary arguments to distutils depending on python        
#     version"""
#     argData = {'athenaCL': 
#               _getAudioPaths() + _getDemoPaths() + _getDocsPaths()
#                      }
#     return argData

    
def removeDisutils(sudoFound=None):
    # get site-packages dirs absolute file path
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')      
    if os.path.exists(sitePkgAthena):
        osTools.rmSudo(sitePkgAthena, sudoFound)
    else:
        reporter.printDebug('no distutuls install')

def reportDisutils(sudoFound=None):
    # get site-packages dirs absolute file path
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')      
    if os.path.exists(sitePkgAthena):
        reporter.printDebug(['distutuls install:', sitePkgAthena])
    else:
        reporter.printDebug('no distutuls install')


def runDisutils(bdistType):
    print 'here'
    if bdistType == 'bdist_egg':
        print 'using setuptools'
        from setuptools import setup
    else:
        from distutils.core import setup
    # store object for later examination
    setup(name = 'athenaCL', 
        version = athVersion,
        description = lang.msgAthDescShort, 
        long_description = lang.msgAthDescLong,
        author = lang.msgAuthor,
        author_email = lang.msgAuthorEmail,
        license = lang.msgLicenseName, 
        url = drawer.urlPrep(lang.msgAthURL),
        classifiers = _getClassifiers(),
        download_url = lang.msgAthDownloadTar,
        packages = _getPackagesList(), # first is 'athenaCL'   
        package_data = {'athenaCL' : ['audio/*.aif',
                                      'demo/*.xml',
                                      'demo/*.txt',
                                      'doc/*.txt',
                                      'doc/*.pdf',
                                     ]}
    ) # close setup args
    
    # return absolute file path to athenaCL dir in site-packages
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')          
    return sitePkgAthena
        

def writeManifestTemplate(fpPackageDir):
    # remove old maniest
    osTools.rm(os.path.join(fpPackageDir, 'MANIFEST')) 
    dst = os.path.join(fpPackageDir, 'MANIFEST.in')
    msg = []
    msg.append('global-include *.txt *.aif *.pdf')
    msg.append('prune buildDoc dist')

    f = open(dst, 'w')
    f.writelines(msg)
    f.close()




#-----------------------------------------------------------------||||||||||||--
# module level operations, for when called without args
# defaults

athVersion = athenaObj.__version__

# _fpPackageDir should be path to athenaCL directory
_fpPackageDir = os.getcwd() # this is a default, must be in the athenaCL dir when called
if _fpPackageDir != fpSrcDir:
    reporter.printDebug('cwd (%s) is not the athenaCL src directory (%s)' % (_fpPackageDir, fpSrcDir))

# most options here are only for unix plats
optWriteManifestTemplate = 0
optRemoveDist = 0 
optInstallDist = 0 
#optRemovePthLoader = 1 # always remove, may have changed locations
#optWritePthLoader = 1
optRemoveLauncher = 0 
optWriteLauncher = 0 
optInstallTool = 0
optRemoveMan = 0 
optInstallMan = 0 
optReport = 0
optBdistType = None

flags = ['-o','build', 'tool', 'install', 'bdist', 'uninstall', 
            'report', 'man', 'sdist', 'register', 'bdist_mpkg',
            'bdist_rpm', 'bdist_deb', 'bdist_wininst', 'bdist_egg']
parsedArgs = argTools.parseFlags(sys.argv, flags)

# loop through each arg pair
for argPair in parsedArgs:
    # some options will configure settings
    if argPair[0] == '-o': # changes assumed athDir
        if argPair[1] != None:
            tempPath = drawer.pathScrub(argPair[1])
            if os.path.isdir(tempPath):
                _fpPackageDir = tempPath

    elif argPair[0] == 'tool': # installs a loader script
        optInstallDist = 0 # do a distutils install
        #optWritePthLoader = 1
        optWriteLauncher = 1 # write launchers to athenaCL src dir
        optInstallTool = 1 # adds athenacl to /usr/local/bin
        optInstallMan = 1 # installls man page in bin

    elif argPair[0] == 'build': # do nothing, turn off defaults
        pass
        #optWritePthLoader = 0
        #optRemovePthLoader = 0 

    elif argPair[0] == 'report': # do nothing, turn off defaults
        #optWritePthLoader = 0
        #optRemovePthLoader = 0 
        optReport = 1

    elif argPair[0] == 'man': # do nothing but install man
        #optWritePthLoader = 0
        #optRemovePthLoader = 0 
        optInstallMan = 1

    elif argPair[0] == 'install': # site packages install
        optInstallDist = 1 # do a distutils install
        #optWritePthLoader = 0 # never write pth if doing a distutils install
        # write launchers to athenaCL src dir after distutil
        optWriteLauncher = 1 
        optInstallTool = 1 # 2 if this is done in root
        optInstallMan = 1 # installls man page in bin

    elif argPair[0] in ['bdist', 'sdist', 'register', 'bdist_mpkg',
                        'bdist_rpm', 'bdist_deb', 'bdist_wininst',
                        'bdist_egg']:
        optBdistType = argPair[0]
        optWriteManifestTemplate = 1
        optInstallDist = 1 # not a distutils install, call setup method
        #optWritePthLoader = 0
        #optRemovePthLoader = 0 # dont remove, not an install

    elif argPair[0] == 'uninstall':
        optInstallDist = 0 
        optRemoveDist = 1
        #optRemovePthLoader = 1 # always remove, may have changed locations
        #optWritePthLoader = 0
        optWriteLauncher = 0 
        optRemoveLauncher = 1 
        optInstallTool = 0
        optRemoveMan = 1
        optInstallMan = 0 
        
#-----------------------------------------------------------------||||||||||||--
# main platform specific branck

reporter.printDebug('active athenaCL package directory: %s' % _fpPackageDir)

if os.name == 'posix': # create launch script
    if (optWriteLauncher or optInstallMan or optRemoveLauncher 
        or optRemoveDist or optRemoveMan):
        sudoFound = drawer.isSudo() # always detect once, pass to other methods
    if optWriteManifestTemplate: writeManifestTemplate(_fpPackageDir)
    if optRemoveDist: removeDisutils(sudoFound)

    if optInstallDist:
        # update athena directory to site-packages
        _fpSrcDir = runDisutils(optBdistType) 
    else: # use the src dir found based on imports, above
        _fpSrcDir = fpSrcDir

    if optRemoveLauncher:
        removeUnixLauncher(sudoFound)
    if optWriteLauncher: # will determine optInstallTool 
        # move to /usr/local/bin depending on install too option
        # create launcher script
        pathLaunchScript = os.path.join(_fpSrcDir, 'athenacl.py')
        pathShellScript = os.path.join(_fpSrcDir, 'athenacl') 
        writeUnixLauncher(pathLaunchScript, pathShellScript, 
                                optInstallTool, sudoFound)
    #if optRemoveMan: removeMan(sudoFound)
    #if optInstallMan: copyMan(_fpPackageDir, sudoFound)

else: # all windows flavors
    if optRemoveDist:
        removeDisutils(sudoFound)
    if optInstallDist:
        # update athena directory to site-packages
        _fpSrcDir = runDisutils(optBdistType) 

#if optRemovePthLoader: removePthLoader()
#if optWritePthLoader: writePthLoader(_fpPackageDir)

if optReport:
    reporter.printDebug('athenaCL setup.py report')
    reportDisutils()
    reportUnixLauncher()
    reportMan()
    #reportPthLoader()

