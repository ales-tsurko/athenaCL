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
try: 
    from athenaCL import libATH
except ImportError: 
    print('athenaCL package cannot be found')
    sys.exit()
fpLibATH = libATH.__path__[0] # list, get first item
if not os.path.isabs(fpLibATH): #relative path, add cwd
    fpLibATH = os.path.abspath(fpLibATH)
fpSrcDir = os.path.dirname(fpLibATH) # athenaCL dir
fpPackageDir = os.path.dirname(fpSrcDir) # outer dir tt contains athenaCL dir
if fpPackageDir not in sys.path: sys.path.append(fpPackageDir)
#-----------------------------------------------------------------||||||||||||--

from athenaCL.libATH import dialog
from athenaCL.libATH import athenaObj
from athenaCL.libATH import drawer
from athenaCL.libATH import argTools
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import osTools
from athenaCL.libATH import info

_MOD = 'setup.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)


#-----------------------------------------------------------------||||||||||||--
# optional imports supports creation of meta-packages
try: import bdist_mpkg
except ImportError: pass


#-----------------------------------------------------------------||||||||||||--
# assume right permission for writing in the pth destination

# note that .pth file writing does not seem necessary, as using the 
# atheancl.py launcher adds paths to sys.path, for non site packages install
# and, most will install in site-packages, so .pth is not necessary


def writePthLoader(fpPackageDir):
    """a pth file named athenaCL.pth can be placed in site-packages
    to give the path to the outer dir (not athenaCL dir), 
    allowing easy imports w/o having to move files..."""
    environment.printWarn('writing pth file')
    # get dir outside of athenaCL dir
    msg = '%s\n' % fpPackageDir
    dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
    try:
        f = open(dst, 'w')      
        f.write(msg)
        f.close()
    except IOError: 
        environment.printWarn(lang.msgFileIoError % dst)

def removePthLoader(sudoFound=None):
    """remove old pth loader"""
    environment.printWarn('removing outdated pth file')
    dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        environment.printWarn('no pth file exists')
        
def reportPthLoader(sudoFound=None):
    """remove old pth loader"""
    dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
    if os.path.exists(dst):
        environment.printWarn('pth file exists: %s' % dst)
        f = open(dst)
        msg = f.read()
        f.close()
        environment.printWarn(['pth contents:', msg.strip()])
    else:
        environment.printWarn('no pth file exists')
        
        
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
    environment.printWarn('writing launcher script:\n%s' % pathLaunchScript)
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
        environment.printWarn(lang.msgFileIoError % pathShellScript)

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
    environment.printWarn('removing athenacl unix launcher')
    
    dst = osTools.findAthBinPath()
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        environment.printWarn('no athenacl unix launcher exists (%s)' % dst)
            
def reportUnixLauncher():
    """only remove if it is found within /usr/local/bin"""  
    dst = osTools.findAthBinPath()
    if os.path.exists(dst):
        environment.printWarn(['athenacl unix launcher exists:', dst])
        f = open(dst)
        msg = f.read()
        f.close()
        environment.printWarn(['launcher contents:', msg.strip()])
    else:
        environment.printWarn('no athenacl unix launcher exists (%s)' % dst)
        
        
#-----------------------------------------------------------------||||||||||||--
def copyMan(athenaDir, sudoFound=None):
    """if install tool == 1, use sudo
    if install tool == 2, assume already root"""
    environment.printWarn('copying manual-page file')
    manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    if manDir == None: return None
    src = os.path.join(athenaDir, 'doc', info.MANFILE)
    dst = os.path.join(manDir, info.MANFILE)
    osTools.cpSudo(src, dst, sudoFound)

def removeMan(sudoFound=None):
    """removing man file"""
    environment.printWarn('removing manual-page file')
    manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    if manDir == None: return None

    dst = os.path.join(manDir, info.MANFILE)
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        environment.printWarn('no athenacl manual-page exists (%s)' % dst)

def reportMan():
    manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    if manDir == None:
        environment.printWarn('no manual directory found')
        return None
    dst = os.path.join(manDir, info.MANFILE)
    if os.path.exists(dst):
        environment.printWarn(['man path exists:', dst])
    else:
        environment.printWarn('no athenacl manual-page exists (%s)' % dst)


#-----------------------------------------------------------------||||||||||||--
def _getPackagesList():
    """list of all packages, delimited by period"""
    pkg = (  'athenaCL', 
             'athenaCL.demo', 
             'athenaCL.test', 
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
     
    
def removeDisutils(sudoFound=None):
    # get site-packages dirs absolute file path
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')      
    if os.path.exists(sitePkgAthena):
        osTools.rmSudo(sitePkgAthena, sudoFound)
    else:
        environment.printWarn('no distutuls install')

def reportDisutils(sudoFound=None):
    # get site-packages dirs absolute file path
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')      
    if os.path.exists(sitePkgAthena):
        environment.printWarn(['distutuls install:', sitePkgAthena])
    else:
        environment.printWarn('no distutuls install')


def runDisutils(bdistType):
    if bdistType == 'bdist_egg':
        print('using setuptools')
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
        download_url = lang.msgAthDownloadTar % athVersion,
        packages = _getPackagesList(), # first is 'athenaCL'   
        package_data = {'athenaCL' : ['audio/*.aif',

                                      'demo/csound/*.xml',
                                      'demo/csound/*.txt',
                                      'demo/csound/*.py',
                                      'demo/csound/*.mp3',

                                      'demo/legacy/*.xml',
                                      'demo/legacy/*.txt',
                                      'demo/legacy/*.py',

                                      'demo/manual/*.xml',
                                      'demo/manual/*.txt',
                                      'demo/manual/*.py',

                                      'demo/midi/*.xml',
                                      'demo/midi/*.txt',
                                      'demo/midi/*.py',
                                      'demo/midi/*.mid',

                                      'demo/supercollider/*.xml',
                                      'demo/supercollider/*.txt',
                                      'demo/supercollider/*.py',

                                      'doc/*.htm',
                                      'doc/*.txt',
                                      'doc/html/*.htm',
                                      'doc/html/*.css',
                                      'doc/html/images/*.png',

                                      'test/xml/*.xml',

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
    msg.append('global-include *.txt *.aif *.htm *.mid *.png *.xml *.css *.py *.mp3\n')
    msg.append('prune buildDoc\n')
    msg.append('prune dist\n')
    msg.append('prune tools\n')

    f = open(dst, 'w')
    f.writelines(msg)
    f.close()




#-----------------------------------------------------------------||||||||||||--
# module level operations, for when called without args
athVersion = athenaObj.__version__

# _fpPackageDir should be path to athenaCL directory
# must be in the athenaCL dir when called
_fpPackageDir = os.getcwd() 
if _fpPackageDir != fpPackageDir:
    environment.printWarn('cwd (%s) is not the athenaCL src directory (%s)' % (_fpPackageDir, fpSrcDir))

# most options here are only for unix plats
optWriteManifestTemplate = 0
optRemoveDist = 0 
optInstallDist = 0 
optRemovePthLoader = 0 # always remove, may have changed locations
optWritePthLoader = 0
optRemoveLauncher = 0 
optWriteLauncher = 0 
optInstallTool = 0
optRemoveMan = 0 
optInstallMan = 0 
optReport = 0
optBdistType = None # default needed when calling runDisutils()

flags = ['-o','build', 'tool', 'install', 'bdist', 'uninstall', 
            'report', 'man', 'pth', 'sdist', 'register', 'bdist_mpkg',
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
        optWriteLauncher = 1 # write launchers to athenaCL src dir
        optInstallTool = 1 # adds athenacl to /usr/local/bin
        optInstallMan = 1 # installls man page in bin

    elif argPair[0] == 'report': # do nothing, turn off defaults
        optReport = 1

    elif argPair[0] == 'pth': # do nothing but install man
        optRemovePthLoader = 1 # always remove, may have changed locations
        optWritePthLoader = 1

    elif argPair[0] == 'man': # do nothing but install man
        optInstallMan = 1

    elif argPair[0] == 'install': # site packages install
        optInstallDist = 1 # do a distutils install

    # for building distributions on the way out
    elif argPair[0] in ['bdist', 'sdist', 'register', 'bdist_mpkg',
                        'bdist_rpm', 'bdist_deb', 'bdist_wininst',
                        'bdist_egg']:
        optBdistType = argPair[0]
        optWriteManifestTemplate = 1
        optInstallDist = 1 # not a distutils install, call setup method

    elif argPair[0] == 'uninstall':
        optRemoveDist = 1
        optRemovePthLoader = 1 # always remove, may have changed locations
        optRemoveLauncher = 1 
        optRemoveMan = 1
        
#-----------------------------------------------------------------||||||||||||--
# main platform specific branch
environment.printWarn('active athenaCL package directory: %s' % _fpPackageDir)

if optWriteManifestTemplate: 
    writeManifestTemplate(_fpPackageDir)

if os.name == 'posix': # create launch script
    if (optWriteLauncher or optInstallMan or optRemoveLauncher 
        or optRemoveDist or optRemoveMan):
        sudoFound = drawer.isSudo() # always detect once, pass to other methods

    if optRemoveDist: 
        removeDisutils(sudoFound)
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
    if optRemoveMan: 
        removeMan(sudoFound)
    if optInstallMan: 
        copyMan(_fpPackageDir, sudoFound)

else: # all windows flavors
    if optRemoveDist:
        removeDisutils(sudoFound)
    if optInstallDist:
        # update athena directory to site-packages
        _fpSrcDir = runDisutils(optBdistType) 

if optRemovePthLoader: 
    removePthLoader()
if optWritePthLoader: 
    writePthLoader(_fpPackageDir)

if optReport:
    environment.printWarn('athenaCL setup.py report')
    reportDisutils()
    reportUnixLauncher()
    reportMan()
    reportPthLoader()


environment.printWarn('complete\n')
