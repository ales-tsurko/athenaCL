#-----------------------------------------------------------------||||||||||||--
# Name:          dist.py
# Purpose:       Distribution and uploading script
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import os, sys


import googlecode_upload # placed in site-packages

from athenaCL.libATH import athenaObj
from athenaCL.libATH import info

_MOD = 'dist.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)


class Distributor(object):
    def __init__(self):
        self.fpEgg = None
        self.fpWin = None
        self.fpTar = None

        self.fpDistDir = os.path.join(athenaObj.fpPackageDir, 'dist')
        self.fpBuildDir = os.path.join(athenaObj.fpPackageDir, 'build')
        self.fpEggInfo = os.path.join(athenaObj.fpPackageDir,
                        'athenaCL.egg-info')

        self._updatePaths()

    def _updateDocs(self):
        foObj = info.InfoManager()
        
        # update man page, readme
        infoObj.historyScrub()
        infoObj.writeMan()
        infoObj.writeReadme()

    def _updatePaths(self):
        # get most recent files
        contents = os.listdir(self.fpDistDir)
        for fn in contents:
            fp = os.path.join(self.fpDistDir, fn)
            if athenaObj.athVersion in fn and fn.endswith('.egg'):
                self.fpEgg = fp
            elif athenaObj.athVersion in fn and fn.endswith('.exe'):
                fpNew = fp.replace('.macosx-10.3-fat.exe', '.exe')
                os.rename(fp, fpNew)
                self.fpWin = fpNew
            elif athenaObj.athVersion in fn and fn.endswith('.tar.gz'):
                self.fpTar = fp

        for fn in [self.fpEgg, self.fpWin, self.fpTar]:
            if fn == None:
                environment.printWarn('missing fn path')
            environment.printWarn(fn)


    def build(self):
        infoObj = info.InfoManager()
        infoObj.main()

        os.system('cd %s; python setup.py bdist_egg' % athenaObj.fpPackageDir)
        os.system('cd %s; python setup.py bdist_wininst' % 
                    athenaObj.fpPackageDir)
        os.system('cd %s; python setup.py sdist' % 
                    athenaObj.fpPackageDir)
        self._updatePaths()

        # remove build dir, egg-info dir
        environment.printWarn('removing %s' % self.fpEggInfo)
        os.system('rm -r %s' % self.fpEggInfo)
        environment.printWarn('removing %s' % self.fpBuildDir)
        os.system('rm -r %s' % self.fpBuildDir)


    def _uploadPyPi(self):
        os.system('cd %s; python setup.py bdist_egg upload' % 
                athenaObj.fpPackageDir)
        os.system('cd %s; python setup.py register' % athenaObj.fpPackageDir)

    def _uploadGoogleCode(self, fp):
        summary = athenaObj.athVersion
        project = 'athenacl'
        user = 'christopher.ariza'

        if fp.endswith('.tar.gz'):
            labels = ['OpSys-All', 'Featured', 'Type-Archive']
        elif fp.endswith('.exe'):
            labels = ['OpSys-Windows', 'Featured', 'Type-Installer']
        elif fp.endswith('.egg'):
            labels = ['OpSys-All', 'Featured', 'Type-Archive']
    
        environment.printWarn(['starting GoogleCode upload of:', fp])
        status, reason, url = googlecode_upload.upload_find_auth(fp, 
                        project, summary, labels, user)
        environment.printWarn([status, reason])

    def upload(self):    
        self._uploadPyPi()
        for fp in [self.fpTar, self.fpEgg, self.fpWin]:
            self._uploadGoogleCode(fp)

        # uplaod to flexatone.net



if __name__ == '__main__':
    a = Distributor()
    a.build()
    a.upload()