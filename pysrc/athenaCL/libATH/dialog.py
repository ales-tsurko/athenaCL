# -----------------------------------------------------------------||||||||||||--
# Name:          dialog.py
# Purpose:       cross platform dialogs
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import sys, time, random
import unittest


from athenaCL.libATH import typeset
from athenaCL.libATH import language

lang = language.LangObj()

# this module is higher than drawer and typeset

_MOD = "dialog.py"

def _fixQuery(query):
    """query strings need to end with a space; this makes sure they do
    choice can be none, or a list of options to be appended after query
    in paranthessis"""
    if query != "":
        if query[-1] != " ":  # add space if missing
            query = query + " "
    return query


def msgOut(msg, termObj=None):
    """almost all text outputted to user goes through this fuction
    general filter for all text display
    athenaCmd.Interpreter.out uses this f to output main text
    other command in Interpreter use sys.stdout
    """
    if termObj != None:  # all athenacl sessions have a termObj
        h, w = termObj.size()  # fit to terminal
        msg = typeset.wrapText(msg, w, 0, "line")
    if termObj != None:
        if termObj.sessionType == "cgi":  # dont want any output
            return  # do nothing, nothing to stdout, str taken elsewhere
    sys.stdout.write(msg)


def msgError(msg, termObj=None):
    """almost all text outputted to user goes through this fuction
    general filter for all text display
    athenaCmd.Interpreter.out uses this f to output main text
    other command in Interpreter use sys.stdout
    """
    if termObj != None:  # all athenacl sessions have a termObj
        h, w = termObj.size()  # fit to terminal
        msg = typeset.wrapText(msg, w, 0, "line")
    if termObj != None:
        if termObj.sessionType == "cgi":  # dont want any output
            return  # do nothing, nothing to stderr, str taken elsewhere
    sys.stderr.write(msg)


def rawInput(prompt, termObj=None):
    """use this to replace built-in raw-input, as this provides
    line wrapping on the query message if possible"""
    if termObj != None:  # all athenacl sessions have a termObj
        h, w = termObj.size()  # fit to terminal
        prompt = typeset.wrapText(prompt, w, 0, "line")
    # line wraping may remove the last space after prompt; make sure it is
    # still there
    return input(_fixQuery(prompt))


def askStr(query, termObj=None, strip=1):
    """function for requesting a string from user
    strip turns off character stripping
    returns None on error given and strip is true (does not return '')
    """
    if termObj != None:
        sessionType = termObj.sessionType
    else:
        sessionType = "terminal"
    # TypeError raised when object.readline() returned non-string
    try:
        answer = rawInput(query, termObj)
    except (KeyboardInterrupt, EOFError, TypeError):
        return None  # cancel
    if strip:
        answer = answer.strip()
    if answer == "" or answer == None:
        return None
    else:
        return answer


def askYesNoCancel(query, defaultSel=1, termObj=None):
    """function for querying user yes, no, or cancel
    returns 1 for yes, 0 for no, -1 for cancel
    """
    if termObj != None:
        sessionType = termObj.sessionType
    else:
        sessionType = "terminal"
    # need to fix query before appending
    query = _fixQuery(query)
    qString = query + "(y, n, or cancel): "
    if sessionType in ["terminal", "idle", "gui-tk"]:
        status = -2  # place holder
        while 1:
            try:
                aString = rawInput(qString, termObj)
            except (KeyboardInterrupt, EOFError, TypeError):
                status = -1  # cancel
                break
            status = typeset.convertBoolCancel(aString)
            if status != None:
                break  # status set to 0, 1, -1
            else:
                msgOut(lang.msgConfusedInput)
                continue
    return status


def askYesNo(query, defaultSel=1, termObj=None):
    """function for querying user yes, no
    returns 1 for yes, 0 for no
    """
    if termObj != None:
        sessionType = termObj.sessionType
    else:
        sessionType = "terminal"
    query = _fixQuery(query)
    qString = query + "(y or n): "
    if sessionType in ["terminal", "idle", "gui-tk"]:
        status = None  # place holder
        while 1:  # 1 for yes, 0 for no
            try:
                aString = rawInput(qString, termObj)
            except (KeyboardInterrupt, EOFError, TypeError):
                status = 0  # cancel
                break
            status = typeset.convertBool(aString)
            if status != None:  # an error:
                break  # status set to 0, 1
            else:
                msgOut(lang.msgConfusedInput)
                continue
    return status


def getEncouragement():
    options = [
        lang.provoke1,
        lang.provoke2,
        lang.provoke3,
        lang.provoke4,
        lang.provoke5,
        lang.provoke6,
    ]
    str = '%s enter "help"\n' % random.choice(options)
    return str


def getAdmonishment(line):
    options = [
        lang.admonish1,
        lang.admonish2,
        lang.admonish3,
        lang.admonish4,
        lang.admonish5,
        lang.admonish6,
    ]
    str = random.choice(options) % line  # line is usr str
    str = "%s\n" % str
    return str


# -----------------------------------------------------------------||||||||||||--
# this needs to be moved
# and needs to be adapted to use rhythm.Timer()
# might be best placed in command.py


def getTempo():
    """simple method for getting tempos from the user.
    based in part on code by Paul Winkler
    note: this uses raw_input; should use standard dialogs"""

    exit = 0
    while exit == 0:
        sys.stdout.write(
            'tap a beat with the return key. enter "q" followed by a return key to end.'
        )
        times = []  # save the time when keys are pressed.
        diffs = []
        i = 0
        while 1:
            c = input("")
            when = time.time()
            if c.find("q") >= 0:
                break
            else:
                times.append(when)
                if i >= 1:
                    diffs.append(times[i] - times[i - 1])
                    estimate = 60.0 / diffs[i - 1]
                    sys.stdout.write("  (%.2f s/beat)    " % (when - times[i - 1]))
                else:
                    sys.stdout.write("  (%.2f s/beat)    " % 0)
                i = i + 1

        # watch for division by zero errors
        if len(diffs) == 0:
            return None, None
        sum = 0
        for d in diffs:
            sum = sum + d
        avgBeatT = sum / len(diffs)
        avgTempo = 60.0 / avgBeatT
        print("average tempo %.2f BPM (%.2f s/beat)" % (avgTempo, avgBeatT))
        q_string = "    keep, repeat, or cancel? (k, r, or c): "
        usrStr = input(q_string)
        usrStr = usrStr.lower()
        if usrStr == "" or usrStr == None:
            exit = 1  # keep, dont cancel
        if usrStr.find("k") >= 0:
            exit = 1  # xits loop
        elif usrStr.find("r") >= 0:
            exit = 0  # repeats loop
        elif usrStr.find("c") >= 0:
            return None, None

    return avgTempo, avgBeatT


def testStr(n=100, newLines=0):
    """used for testing wrapping text"""
    import random, string

    msg = []
    i = 1
    for x in range(0, n):
        if newLines == 1 and x % 10 == 1:  # once in a while
            msg.append("\n%sNewLine" % i)  # show a new line
        else:
            max = random.choice(list(range(1, 10)))  # len of word
            msg.append(str(i))
            for x in range(0, max):
                msg.append(random.choice(string.lowercase))
        msg.append(" ")
        i += 1
    return "".join(msg)


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)
