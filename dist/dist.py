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

from athenaCL.libATH import athenaObj


def build():
    dir = athenaObj.fpPackageDir
    os.system('cd %s; python setup.py bdist_egg' % dir)
    os.system('cd %s; python setup.py sdist' % dir)


def upload():
    dir = athenaObj.fpPackageDir
    os.system('cd %s; python setup.py bdist_egg upload' % dir)


if __name__ == '__main__':
    build()
    #upload()