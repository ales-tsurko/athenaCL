#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          setup.py
# Purpose:       provides setup features for athenaCL install.
#                    loads large modules
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2009 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import sys, os

#-----------------------------------------------------------------||||||||||||--
try: import libATH #assume we are in package dir
except ImportError:
    try: from athenaCL import libATH
    except ImportError: print 'athenaCL package cannot be found'; sys.exit()
libPath = libATH.__path__[0] # list, get first item
if not os.path.isabs(libPath): #relative path, add cwd
    libPath = os.path.abspath(libPath)
_PKGDIR = os.path.dirname(libPath) # athenaCL dir
_OUTDIR = os.path.dirname(_PKGDIR) # outer dir tt contains athenaCL dir
if _OUTDIR not in sys.path: sys.path.append(_OUTDIR)
#-----------------------------------------------------------------||||||||||||--
_MOD = 'setup.py ::'

from athenaCL.libATH import dialog
from athenaCL import athenaObj
from athenaCL.libATH import drawer
from athenaCL.libATH import argTools
from athenaCL.libATH import language
lang = language.LangObj()
from athenaCL.libATH import osTools
from athenaCL.libATH import info


#-----------------------------------------------------------------||||||||||||--
# optional imports supports creation of meta-packages
try: import bdist_mpkg
except ImportError: pass


# used to show that things have started on slow machines
# dialog.msgOut('%s initiated\n' % _MOD)


#-----------------------------------------------------------------||||||||||||--
def importRawModules():
    """ this currently only imports select large modules
    this was designed to avoid memory problems on ancient macos9"""
    print _MOD, 'compiling modules into Python bytecode'                    
    # get all py modules from libATH dir
    libDirList = os.listdir(os.path.join(_PKGDIR, 'libATH'))
    modList = []
    for name in libDirList:
        if name.endswith('.py'):
            modList.append(name[:-3])
    for mod in modList:
        while 1:
            try:
                exec('from athenaCL.libATH import %s' % mod)
                exec('del %s' % mod) # free from memory
            except MemoryError:
                msg = lang.msgMemoryError % mod
                ok = dialog.askYesNo(msg)
                if not ok: sys.exit()
                else: continue
            break

#-----------------------------------------------------------------||||||||||||--
# assume right permission for writing in the pth destination

def writePthLoader(athenaDir):
    """a pth file named athenaCL.pth can be placed in site-packages
    to give the path to the outer dir (not athenaCL dir), 
    allowing easy imports w/o having to move files..."""
    print _MOD, 'writing pth file'
    # get dir outside of athenaCL dir
    # allows from athenaCL.libATH import ...
    msg = '%s\n' % os.path.dirname(athenaDir)
    dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
    try:
        f = open(dst, 'w')      
        f.write(msg)
        f.close()
    except IOError: 
        print lang.msgFileIoError % dst

def removePthLoader(sudoFound=None):
    """remove old pth loader"""
    print _MOD, 'removing outdated pth file'
    dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        print _MOD, 'no pth file exists'
        
def reportPthLoader(sudoFound=None):
    """remove old pth loader"""
    dst = os.path.join(osTools.findSitePackages(), 'athenaCL.pth')
    if os.path.exists(dst):
        print _MOD, 'pth file exists: %s' % dst
        f = open(dst)
        msg = f.read()
        f.close()
        print _MOD, 'pth contents:', msg.strip()
    else:
        print _MOD, 'no pth file exists'
        
        
#-----------------------------------------------------------------||||||||||||--          
def writeUnixLauncher(pathLaunchScript, pathShellScript, optInstallTool=0,
                             sudoFound=None, optFink=0):
    """used to create shell scripts that act as application launcher
    creates file in local directory first, using paths in args
    will optional move to /usr/local/bin if optInstallTool is 1
    pathLaunchScript is the path to the python file
    pathShellScript is the path to the shell script to be written\
    if optInstallTool == 2; case were to assume already root
    """
    print _MOD, 'writing launcher script:\n%s' % pathLaunchScript
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
        print lang.msgFileIoError % pathShellScript
    # optionally move this script to /usr/local/bin
    # this would be different if a fink installation: /usr/bin
    if optInstallTool >= 1: # install tool into /usr/local/bin
        binPath = osTools.findBinPath(optFink)
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

def removeUnixLauncher(sudoFound=None, optFink=0):
    """only remove if it is found within /usr/local/bin"""
    print _MOD, 'removing athenacl unix launcher'
    
    dst = osTools.findAthBinPath(optFink)
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        print _MOD, 'no athenacl unix launcher exists (%s)' % dst
            
def reportUnixLauncher(optFink=0):
    """only remove if it is found within /usr/local/bin"""  
    dst = osTools.findAthBinPath(optFink)
    if os.path.exists(dst):
        print _MOD, 'athenacl unix launcher exists:', dst
        f = open(dst)
        msg = f.read()
        f.close()
        print _MOD, 'launcher contents:', msg.strip()
    else:
        print _MOD, 'no athenacl unix launcher exists (%s)' % dst
        
        
#-----------------------------------------------------------------||||||||||||--
def copyMan(athenaDir, sudoFound=None, optFink=0):
    """if install tool == 1, use sudo
    if install tool == 2, assume already root"""
    print _MOD, 'copying manual-page file'
    if not optFink:
        manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    else: # a fink install
        manDir = osTools.findManPath(info.MANGROUP, 'fink') 
    if manDir == None: return None
    src = os.path.join(athenaDir, 'docs', info.MANFILE)
    dst = os.path.join(manDir, info.MANFILE)
    osTools.cpSudo(src, dst, sudoFound)

def removeMan(sudoFound=None, optFink=0):
    """removing man file"""
    print _MOD, 'removing manual-page file'
    if not optFink:
        manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    else: # a fink install
        manDir = osTools.findManPath(info.MANGROUP, 'fink') 
    if manDir == None: return None
    dst = os.path.join(manDir, info.MANFILE)
    if os.path.exists(dst):
        osTools.rmSudo(dst, sudoFound)
    else:
        print _MOD, 'no athenacl manual-page exists (%s)' % dst

def reportMan(optFink=0):
    if not optFink:
        manDir = osTools.findManPath(info.MANGROUP) # assumes group 1 of man pages
    else: # a fink install
        manDir = osTools.findManPath(info.MANGROUP, 'fink') 
    if manDir == None:
        print _MOD, 'no manual directory found'
        return None
    dst = os.path.join(manDir, info.MANFILE)
    if os.path.exists(dst):
        print _MOD, 'man path exists:', dst
    else:
        print _MOD, 'no athenacl manual-page exists (%s)' % dst




#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
# either do a distutils or build compile modules manually
# alternative:
# dont install into site-packages
# instead, simply create a athenaCL.pth file in site-packages, 
# given the path to the location of the athenaCL folder...

# building distribution commands w/ dist utils
# find formats here: python setup.py bdist --help-formats

# this is a pure module distribution
# distribution root: the top-level directory of your source tree (or source distribution); the directory where setup.py exists. Generally setup.py will be run from this directory.   

# can change the build directory with this option:
# --dist-dir 

# python setup.py bdist_mpkg --zipdist
# python setup.py bdist_wininst
# bdist_rpm
# bdist_deb

#-----------------------------------------------------------------||||||||||||--
# Each file name in files is interpreted relative to the setup.py script at the top of the package source distribution. No directory information from files is used to determine the final location of the installed file; only the name of the file is used.

def _getAudioPaths():
    """get list of file names found in the ssdir"""
    fileList = os.listdir(os.path.join(_PKGDIR, 'audio'))
    filterList = []
    for name in fileList:
        if name.endswith('.aif'):
            filterList.append(os.path.join(_PKGDIR, 'audio', name))
    return filterList

def _getDemoPaths():
    """get list of file names found in the demo dir"""
    fileList = os.listdir(os.path.join(_PKGDIR, 'demo'))
    filterList = []
    for name in fileList:
        if name.endswith('.xml') or name.endswith('.txt'):
            filterList.append(os.path.join('demo', name))
    return filterList

def _getDocsPaths():
    """get list of file names found in the doc dir"""
    fileList = os.listdir(os.path.join(_PKGDIR, 'docs'))
    filterList = []
    for name in fileList:
        if name in ['athenacl.1', ]:
            filterList.append(os.path.join('docs', name))
    return filterList

def _getPackagesList():
    """list of all packages, delimited by period"""
    pkg = ('athenaCL', 
             'athenaCL.demo', 
             'athenaCL.docs', 
             'athenaCL.libATH', 
             'athenaCL.libATH.libAS', 
             'athenaCL.libATH.libCompat', 
             'athenaCL.libATH.libGfx', 
             'athenaCL.libATH.libOrc', 
             'athenaCL.libATH.libPmtr', 
             'athenaCL.libATH.libTM', 
             'athenaCL.libATH.libUtil', 
             'athenaCL.libATH.omde', 
             'athenaCL.libATH.osc', 
             'athenaCL.libATH.patterns', 
             'athenaCL.libATH.patterns.notification', 
             'athenaCL.audio',#creates dir, not files
             'athenaCL.libATH.sadir',#creates dir, not files
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
     
def _pkgDataManager(argField):
    """there are 2 methods to install data files; package_data is best, 
    but is only defined for python 2.4 and later; this will check
    and provide the necessary arguments to distutils depending on python        
    version"""
    # use data files for all python versions before 2.4
    if drawer.isPy24Better(): 
        methodForce = 'package_data'
    else:
        methodForce = 'data_files'

    print _MOD, 'package data manager forced method:', methodForce
    
    # create empty arg data depending on requested field
    if argField == 'data_files': argNot = []
    elif argField == 'package_data': argNot = {}
        
    # pass will return proper arg data; otherwise return argNot
    if argField == 'data_files' and methodForce == 'data_files': 
        pass # return data
    elif argField == 'data_files' and methodForce == 'package_data': 
        return argNot
    elif argField == 'package_data' and methodForce == 'data_files': 
        return argNot
    elif argField == 'package_data' and methodForce == 'package_data': 
        pass # return data
        
    # old method of install package data
    # install files into site-packages dir, path directories are absolute
    if methodForce == 'data_files':
        # get site-packages dirs absolute file path
        # relative paths for data files do not work, do not drop dirs in site pkg
        sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')          
        sitePkgDemo = os.path.join(sitePkgAthena, 'demo')
        sitePkgDocs = os.path.join(sitePkgAthena, 'docs')
        sitePkgSsdir = os.path.join(sitePkgAthena, 'audio')
        argData = [(sitePkgSsdir, _getAudioPaths()),
                      (sitePkgDemo, _getDemoPaths()),
                      (sitePkgDocs, _getDocsPaths())
                     ]
    # package data says only works w/ python 2.4.
    # avoids problem with windows intaller getting wrong path
    elif methodForce == 'package_data':
        argData = {'athenaCL': 
                      _getAudioPaths() + _getDemoPaths() + _getDocsPaths()
                     }
    return argData

    
def removeDisutils(sudoFound=None):
    # get site-packages dirs absolute file path
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')      
    if os.path.exists(sitePkgAthena):
        osTools.rmSudo(sitePkgAthena, sudoFound)
    else:
        print _MOD, 'no distutuls install'

def reportDisutils(sudoFound=None):
    # get site-packages dirs absolute file path
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')      
    if os.path.exists(sitePkgAthena):
        print _MOD, 'distutuls install:', sitePkgAthena
    else:
        print _MOD, 'no distutuls install'

def runDisutils():
    import distutils.core   
    # store object for later examination
    distutils.core.setup(name = 'athenaCL', 
        version = athVersion,
        description = lang.msgAthDescShort, 
        long_description = lang.msgAthDescLong,
        author = lang.msgAuthor,
        author_email = lang.msgAuthorEmail,
        license = lang.msgLicenseName, 
        url = drawer.urlPrep(lang.msgAthURL),
        classifiers = _getClassifiers(),
        download_url = lang.msgAthDownloadTar,
        
        # empty package ('') stands for root dir
        # tell that packages are above this dir
        # this does not work; cannot find athenaCL dir
        # package_dir = {'':'athenaCL'}, 
        # get directory outside of athenaCL src dir (not site dir copy) 
        # this works, but may not function on windows
        # not sure '..' will work on every platform
        #package_dir = {'': '..',}, 
        package_dir = {'': os.path.dirname(_ATHENADIR)}, 
        
        packages = _getPackagesList(),        
        package_data = _pkgDataManager('package_data'),                  
        data_files = _pkgDataManager('data_files'),

    ) # close setup args
    
    # return absolute file path to athenaCL dir in site-packages
    sitePkgAthena = os.path.join(osTools.findSitePackages(), 'athenaCL')          
    return sitePkgAthena
        

def writeManifest(athenaDir):
    """write the manifst file for preparing a source distribution
    this file needs to be in the same directory as setup.py
    name a relative path, form the athenaCL dir, for each file"""
    print _MOD, 'writing manifest file'
    msg = [] # join with returns
    outDir = os.path.dirname(athenaDir)
    # enter as complete plats first
    for stub in _getPackagesList():
        path = os.path.join(outDir, stub.replace('.', os.sep))
        for name in os.listdir(path):
            if name.endswith('.py'): # only get py files
                msg.append(os.path.join(path, name))
    # remove lead to athenacl dir to make relative from setup.py level
    msgFilter = []
    for path in msg:
        alt = path.replace(athenaDir, '')
        alt = '%s\n' % alt[1:]
        msgFilter.append(alt)       
    # non code files: these ar relative to athenaCL dir
    for stub in _getAudioPaths() + _getDemoPaths() + _getDocsPaths():
        msgFilter.append('%s\n' % stub)
    # write file
    dst = os.path.join(athenaDir, 'MANIFEST')
    if os.path.exists(dst):
        print _MOD, 'manifest file cannot be written (file in the way)'
    else:
        f = open(dst, 'w')
        f.writelines(msgFilter)
        f.close()









#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
# module level operations, for when called without args
# defaults

athVersion = athenaObj.__version__

# _ATHENADIR should be path to athenaCL directory
_ATHENADIR = os.getcwd() # this is a default, must be in the athenaCL dir when called
if _ATHENADIR != _PKGDIR:
    print _MOD, 'cwd is not the athenaCL package directory in sys.path'
    CWDISAODIR = 0
else: CWDISAODIR = 1

# most options here are only for unix plats
optImportRawModules = 1
optWriteManifest = 0
optRemoveDist = 0 
optInstallDist = 0 
optRemovePthLoader = 1 # always remove, may have changed locations
optWritePthLoader = 1
optRemoveLauncher = 0 
optWriteLauncher = 0 
optInstallTool = 0
optRemoveMan = 0 
optInstallMan = 0 
optReport = 0
optFink = 0 # fink installation

flags = ['-o','build', 'tool', 'install', 'bdist', 'uninstall', 
            'report', 'man', 'launcher', 'sdist', 'register', 
            'bdist_mpkg', 'bdist_rpm', 'bdist_deb', 'bdist_wininst', '--fink']
parsedArgs = argTools.parseFlags(sys.argv, flags)

# loop through each arg pair
for argPair in parsedArgs:
    # some options will configure settings
    if argPair[0] == '-o': # changes assumed athDir
        if argPair[1] != None:
            tempPath = drawer.pathScrub(argPair[1])
            if os.path.isdir(tempPath):
                _ATHENADIR = tempPath
    elif argPair[0] == '--fink': # changes assumed athDir
        optFink = 1
        if '--fink' in sys.argv: # remove --fink from sys.args to avoid conflict
            sys.argv.pop(sys.argv.index('--fink'))
    # options that set function operations
    elif argPair[0] == 'tool': # installs a loader script
        optInstallDist = 0 # do a distutils install
        optImportRawModules = 1
        optWritePthLoader = 1
        optWriteLauncher = 1 # write launchers to athenaCL src dir
        optInstallTool = 1 # adds athenacl to /usr/local/bin
        optInstallMan = 1 # installls man page in bin
    elif argPair[0] == 'build': # do nothing, turn off defaults
        optImportRawModules = 0
        optWritePthLoader = 0
        optRemovePthLoader = 0 
    elif argPair[0] == 'report': # do nothing, turn off defaults
        optImportRawModules = 0
        optWritePthLoader = 0
        optRemovePthLoader = 0 
        optReport = 1
    elif argPair[0] == 'man': # do nothing but install man
        optImportRawModules = 0
        optWritePthLoader = 0
        optRemovePthLoader = 0 
        optInstallMan = 1
    elif argPair[0] == 'launcher': # do nothing but install launcher
        optImportRawModules = 0
        optWritePthLoader = 0
        optRemovePthLoader = 0 
        optWriteLauncher = 1 # in local dir
        optInstallTool = 1
    elif argPair[0] == 'install': # site packages install
        optInstallDist = 1 # do a distutils install
        optImportRawModules = 0 # done by distutils
        optWritePthLoader = 0 # never write pth if doing a distutils install
        optWriteLauncher = 1 # write launchers to athenaCL src dir after distutil
        optInstallTool = 1 # 2 if this is done in root
        optInstallMan = 1 # installls man page in bin
    elif argPair[0] in ['bdist', 'sdist', 'register', 
                              'bdist_mpkg', 'bdist_rpm', 'bdist_deb', 'bdist_wininst']:
        optWriteManifest = 1
        optInstallDist = 1 # not a distutils install, call setup method
        optImportRawModules = 0
        optWritePthLoader = 0
        optRemovePthLoader = 0 # dont remove, not an install
    elif argPair[0] == 'uninstall':
        optInstallDist = 0 
        optRemoveDist = 1
        optImportRawModules = 0
        optRemovePthLoader = 1 # always remove, may have changed locations
        optWritePthLoader = 0
        optWriteLauncher = 0 
        optRemoveLauncher = 1 
        optInstallTool = 0
        optRemoveMan = 1
        optInstallMan = 0 
        
#-----------------------------------------------------------------||||||||||||--
# main platform specific branck

print _MOD, 'active athenaCL directory: %s' % _ATHENADIR

if os.name == 'mac': # os9 and classic mac
    if optImportRawModules: importRawModules() 
    if optRemoveDist: removeDisutils()
    if optInstallDist:
        _ATHENADIR = runDisutils() # update athena directory to site-packages
        print _MOD, 'active athenaCL directory: %s' % _ATHENADIR
    if optRemovePthLoader: removePthLoader()
    if optWritePthLoader: writePthLoader(_ATHENADIR)

elif os.name == 'posix': # create launch script
    if optImportRawModules: importRawModules() 
    if (optWriteLauncher or optInstallMan or optRemoveLauncher 
        or optRemovePthLoader or optRemoveDist or optRemoveMan):
        sudoFound = drawer.isSudo() # always detect once, pass to other methods
    if optWriteManifest: writeManifest(_ATHENADIR)
    if optRemoveDist: removeDisutils(sudoFound)
    if optInstallDist:
        _ATHENADIR = runDisutils() # update athena directory to site-packages
        print _MOD, 'active athenaCL directory: %s' % _ATHENADIR
    if optRemoveLauncher: removeUnixLauncher(sudoFound, optFink)
    if optWriteLauncher: # will determine optInstallTool 
        # move to /usr/local/bin depending on install too option
        # create launcher script
        if optFink:
            pathLaunchScript = os.path.join(osTools.findSitePackages(), 
                                                     'athenaCL', 'athenacl.py')
        else:
            pathLaunchScript = os.path.join(_ATHENADIR, 'athenacl.py')
        pathShellScript = os.path.join(_ATHENADIR, 'athenacl') 
        writeUnixLauncher(pathLaunchScript, pathShellScript, 
                                optInstallTool, sudoFound, optFink)
    if optRemoveMan: removeMan(sudoFound, optFink)
    if optInstallMan: copyMan(_ATHENADIR, sudoFound, optFink)
    if optRemovePthLoader: removePthLoader(sudoFound)
    if optWritePthLoader: writePthLoader(_ATHENADIR)

else: # all windows flavors
    if optImportRawModules: importRawModules() 
    if optRemoveDist: removeDisutils(sudoFound)
    if optInstallDist:
        _ATHENADIR = runDisutils() # update athena directory to site-packages
        print _MOD, 'active athenaCL directory: %s' % _ATHENADIR
    if optRemovePthLoader: removePthLoader()
    if optWritePthLoader: writePthLoader(_ATHENADIR)

if optReport:
    print '::', 'athenaCL setup.py report'
    reportDisutils()
    reportUnixLauncher(optFink)
    reportMan(optFink)
    reportPthLoader()
    
# final confirmation
dialog.msgOut('%s complete\n' % _MOD)


