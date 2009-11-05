#-----------------------------------------------------------------||||||||||||--
# Name:          script.py
# Purpose:       parent class for all athenacl scripts
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


class AthenaScript:
    """parent class that all scripts must inherit"""

    def __init__(self, scriptArgs=None):
        """scriptArgs can be a dictionary of whatever arguments needed"""
        self.scriptArgs = scriptArgs
        self.cmdList = None

    def __call__(self):
        """mandatory method that returns a list of commands to execute
        can be over-ridden for extra functionality"""
        return self.cmdList


