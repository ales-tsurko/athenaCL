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
reporter = prefTools.Reporter(_MOD)
reporter.status = 1 # force printing on regardless of debug pref


class Distributor(object):
    def __init__(self):
        self.fpEgg = None
        self.fpWin = None
        self.fpTar = None

        self.fpDistDir = os.path.join(athenaObj.fpPackageDir, 'dist')
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
                raise Exception('missing fn path')
            reporter.printDebug(fn)


    def build(self):
        infoObj = info.InfoManager()
        infoObj.main()

        os.system('cd %s; python setup.py bdist_egg' % athenaObj.fpPackageDir)
        os.system('cd %s; python setup.py bdist_wininst' % 
                    athenaObj.fpPackageDir)
        os.system('cd %s; python setup.py sdist' % 
                    athenaObj.fpPackageDir)
        self._updatePaths()


    def _uploadPyPi(self):
        os.system('cd %s; python setup.py bdist_egg upload' % 
                athenaObj.fpPackageDir)


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
    
        reporter.printDebug(['starting GoogleCode upload of:', fp])
        status, reason, url = googlecode_upload.upload_find_auth(fp, 
                        project, summary, labels, user)
        reporter.printDebug([status, reason])

    def upload(self):    
        self._uploadPyPi()
        for fp in [self.fpTar, self.fpEgg, self.fpWin]:
            self._uploadGoogleCode(fp)

        # uplaod to flexatone.net



if __name__ == '__main__':
    a = Distributor()
    a.build()
    a.upload()