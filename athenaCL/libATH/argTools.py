# -----------------------------------------------------------------||||||||||||--
# Name:          argTools.py
# Purpose:       arg tools, flags and command line args
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import types
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import typeset

_MOD = "argTools.py"
from athenaCL.libATH import prefTools

environment = prefTools.Environment(_MOD)


# -----------------------------------------------------------------||||||||||||--
def parseFlags(argv, flags, posStart=1, spaceLimit=0):
    """Parse flags as given form the command line.

    read args flags into a list of flags. Flags may all be 2 char '-f' like flags. Longer flags are accepted, but second priority in searching more than one of the same flag can be used values con be attached to flag, or be the next arg. posStart is the index in the arg list to start (usually not 0)

    spaceLimit: if args are spce delimited or flag delimited
        if true, only one space will be allowed after a flag; and this
        will end the accumlation of arg data; extra args
        will be stored under None keys; if false, all data after the flag
        until the next flag, will be accumlated under that flag
        initial data (w/o flag) is stored uner None: difference is that w/
        spaceLimt==1, there can be multipe None entries
    flags that dont have values get a None
    values that dont have flags:
        after first flag, all values are gathered together until end
        or next flag
    return a list of flag, value pairs.

    >>> parseFlags(['-f', 'test', '-ogreen'], ['-f', '-o'], 0)
    [('-f', 'test'), ('-o', 'green')]
    >>> parseFlags(['-t', 'test', '-tgreen'], ['-t', '-g'], 0)
    [('-t', 'test'), ('-t', 'green')]

    """
    # flags me be ref dict with doc vaules; check type
    if isinstance(flags, dict):
        flagTemp = []
        for entry in list(flags.keys()):
            flagTemp = flagTemp + list(entry)  # str, tuple convert to list
        flags = flagTemp
    # for flag in flags:
    # assert len(flag) == 2 # all falgs must be 2 chars
    parsedArgs = []
    unflaged = []  # list of strings not flaged
    if len(argv) > posStart:  # the first is the name of module
        i = posStart
        while 1:
            flagSymbol = None
            flagValue = None
            argRemainder = ""
            extraData = []

            arg = argv[i]  # get text chunk from list of strings
            # will check for 2 character flags first
            if arg[:2] in flags:  # session type
                flagSymbol = arg[:2]
                if arg[2:] != "":
                    extraData.append(arg[2:])
            elif arg in flags:  # full word arg
                flagSymbol = arg
            else:  # not a flag; store under None
                extraData.append(arg)

            # accumate all data, if no spaceLimit, or if no flag found
            if not spaceLimit or flagSymbol == None:
                while 1:  # check what follows, increment i
                    # if its not a flag, or doesnt start w/ a flag, append it
                    if (
                        i + 1 < len(argv)
                        and argv[i + 1] != ""
                        and argv[i + 1][:2] not in flags
                        and argv[i + 1] not in flags
                    ):
                        # next arg not a flag
                        extraData.append(argv[i + 1])
                        i = i + 1  # move forward one b/c it was  value
                    else:
                        break
            else:  # space limit, only check one in advance
                if extraData == []:  # have not found any data attached to flag
                    if (
                        i + 1 < len(argv)
                        and argv[i + 1] != ""
                        and argv[i + 1][:2] not in flags
                        and argv[i + 1] not in flags
                    ):
                        extraData.append(argv[i + 1])
                        i = i + 1
                else:  # already have some data w/ this flag, assume that is all
                    print("spaceLimit, no data to add", flagSymbol)
                    pass

            flagValue = " ".join(extraData)  # put space between args
            flagValue = flagValue.strip()  # remove outer space
            # remove trailing space
            if flagValue == "":
                flagValue = None
            parsedArgs.append((flagSymbol, flagValue))
            i = i + 1
            if i >= len(argv):
                break

    return parsedArgs


# -----------------------------------------------------------------||||||||||||--
def strongType(usrArgs, argTypes, defaultArgs=[], argCountOffset=0):
    """Argument checking tool.

    checks raw arg type and number, one level deep
        (does not recurse into list)
    will supply defaults if missing args after last given and
        self.defaultArgs defined
    two arguments required, both lists:
        args = a list of arguments, of proper python data types
        argTypes = list of one-level deap types, specified w/ strings
            'list', 'num', 'float', 'int', 'str'; see drawer.py
    one optional args
        defaultArgs = list of default args to substitute
    returns: newArgs, ok, msg

    >>> strongType([[1,2,3]], ['list'])
    ([[1, 2, 3]], 1, '')
    >>> strongType([.5, 3, 'three'], ['float', 'int', 'str'])
    ([0.5, 3, 'three'], 1, '')
    >>> strongType([3.2], ['num', 'num'])
    ([3.2000...], 0, 'incorrect number of arguments; enter 2 arguments.')
    >>> strongType([3.2, 5, 6], ['num', 'num'])
    ([3.2000..., 5, 6], 0, 'too many arguments; enter 2 arguments.')
    """
    argCount = len(argTypes)
    if len(usrArgs) < argCount:
        # try to get from defaults
        if len(defaultArgs) == argCount:  # defaults exits (default is 0)
            for retrieve in defaultArgs[len(usrArgs) :]:
                usrArgs.append(retrieve)  # add missing to end
                # print 'argTools.py: adding default', retrieve, defaultArgs
        else:  # nothing we can do: failure
            msg = "incorrect number of arguments; enter %i arguments." % (
                argCount + argCountOffset
            )  # add incase if name offset
            return usrArgs, 0, msg
    elif len(usrArgs) > argCount:
        # print _MOD, len(usrArgs), argCount
        msg = "too many arguments; enter %i arguments." % (argCount + argCountOffset)
        return usrArgs, 0, msg

    for pos in range(0, argCount):
        argTest = usrArgs[pos]
        # can be [list, num, float, int, str]
        typeCandidates = argTypes[pos]
        if not drawer.isList(typeCandidates):
            typeCandidates = [
                typeCandidates,
            ]  # add to list
        for type in typeCandidates:
            if type == "list" and drawer.isList(argTest):
                match = 1
                break
            elif type == "num" and drawer.isNum(argTest):
                match = 1
                break
            elif type == "float" and drawer.isFloat(argTest):
                match = 1
                break
            elif type == "int" and drawer.isInt(argTest):
                match = 1
                break
            elif type == "str" and drawer.isStr(argTest):
                match = 1
                break
            else:  # dont break; need to through other possbilities
                match = 0
        # should covnert types to better strings
        if match == 0:
            msg = (
                "wrong type of data used as an argument. replace %s with a %s argument type."
                % (
                    repr(typeset.anyDataToStr(argTest)),
                    # provide 'or' to show that any type in candidate is good
                    drawer.typeListAsStr(typeCandidates, "or"),
                )
            )
            return usrArgs, 0, msg
    # all good
    return usrArgs, 1, ""


# -----------------------------------------------------------------||||||||||||--
class ArgOps:
    """Object to handle parsing of commandline arguments, provided either as a space-delimited string or as a list of arguments.

    Args are given w/o commas, space delimited, as used in Interpreter
    this arg lists only use positional values; not flags are permitted
    optional argument may follow required ones"""

    def __init__(self, argStr, stripComma=False):
        """Note: `argStr` can be either a string or a list of pre-partitioned objects.

        >>> a = ArgOps('test 1 2 3')
        >>> a.get(2)
        '2'
        >>> a.get(2, evaluate=True)
        2
        >>> b = ArgOps(['test', 1, 2, 3])
        >>> b.get(2)
        2
        >>> b.get(2, evaluate=True)
        2
        >>> b.get(1, sumRange=True) # will realize values as strings
        '123'

        >>> b = ArgOps('test, stip, comma', stripComma=True)
        >>> b.get(0)
        'test'
        >>> b = ArgOps('test, stip, comma', stripComma=False)
        >>> b.get(0)
        'test,'

        """
        if drawer.isList(argStr):  # accept already partitioned lists
            self.argList = argStr
        else:
            argStr = argStr.strip()  # clear trailing white space
            self.argList = argStr.split()  # will split b/n or more spaces

        # strip trailing comma
        # if stripComma != 'noStrip':
        if stripComma:
            counter = 0
            for entry in self.argList:
                # only remove comma of last line
                if len(entry) > 1 and entry[-1] == ",":
                    self.argList[counter] = entry[:-1]
                counter += 1

    def get(self, index, sumRange=False, evaluate=False, keepSpace=False):
        """returns args as strings
        sum range allowes gather all space-delimited arg positions into one arg
        keepSpace can be used to remove spaces (default) or keep
            this is necessary when taking all values
        if no arg exists for a given index, returns None on error or no arg

        >>> a = ArgOps('tin a 3')
        >>> a.get(1)
        'a'
        >>> a.get(2)
        '3'
        >>> a.get(2, evaluate='on')
        3
        >>> a.get(1, sumRange='end')
        'a3'
        >>> a.get(1, sumRange='end', keepSpace='space')
        'a 3'

        >>> b = ArgOps('apea mp /Applications/QuickTime Player.app')
        >>> b.get(0)
        'apea'
        >>> b.get(1)
        'mp'
        >>> b.get(2, sumRange=False)
        '/Applications/QuickTime'
        >>> b.get(2, sumRange=True, keepSpace=False)
        '/Applications/QuickTimePlayer.app'
        >>> b.get(2, sumRange=True, keepSpace=True)
        '/Applications/QuickTime Player.app'
        """
        if len(self.argList) == 0 or index >= len(self.argList):
            return None

        if sumRange in ["single", False]:
            output = self.argList[index]
        elif sumRange in ["end", True]:
            output = []
            for i in range(index, len(self.argList)):
                if not drawer.isStr(self.argList[i]):  # coerce into str for now
                    output.append(str(self.argList[i]))
                else:
                    output.append(self.argList[i])
            # environment.printDebug([output])
            if keepSpace not in [False, "noSpace"]:  # add space
                output = " ".join(output)
            else:  # if false
                output = "".join(output)
        else:
            raise Exception("bad sum range argument: %s" % sumRange)

        if evaluate in ["off", False]:
            return output
        else:
            if drawer.isStr(output):
                try:
                    return eval(output)
                except:  # should report this error in a better fashion
                    return None
            else:  # already evalauted
                return output

    def list(self, index, sumRange=False, evaluate=False):
        """returns args as a list of strings
        index: arg number to start with
        sumRange: either False (only the index given)
            or True (from index to end of args)
        evaluate: when on, evaluates each member of resultant list

        >>> a = ArgOps('tin a 3')
        >>> a.list(1)
        ['a']
        >>> a.list(0, sumRange=True)
        ['tin', 'a', '3']
        >>> a.list(0, sumRange=False)
        ['tin']
        """
        if len(self.argList) == 0:
            return None
        if index >= len(self.argList):
            return None

        if sumRange in ["single", False]:
            output = [
                self.argList[index],
            ]
        elif sumRange in ["end", True]:
            output = []
            for i in range(index, len(self.argList)):
                output.append(self.argList[i])
        else:
            raise Exception("bad sum range argument: %s" % sumRange)

        # final changes and returns
        if evaluate in ["off", False]:
            return output
        else:  # evaluate each member of the list, not entire    list
            for i in range(0, len(output)):
                try:
                    output[i] = eval(output[i])
                except:
                    return None
            return output


# -----------------------------------------------------------------||||||||||||--
# version object for checking


class VersionException(Exception):
    pass


class Version:
    """simple object to handle checking and evaluating versions"""

    def __init__(self, vStr):
        """split string, remove beta or other tags, place into local dict
        a beta tag is not enough to distinguish versions; a beta should
        evaluate the same as the normal version
        date distinctions only evaluated if present in both objects

        >>> a = Version('3.25.3')
        >>> a = Version('3.25')
        Traceback (most recent call last):
        VersionException: cannot process version number 3.25
        >>> a = Version('3.25.3a5')
        >>> a.betaTag
        'a5'
        """
        vList = vStr.split(".")
        if len(vList) >= 3:
            a, b, c = vList[0], vList[1], vList[2]

            # c may have a -beta tag on it, or aX: must remove
            if "-" in c:
                cRemain = c.split("-")[0]
                self.betaTag = c.split("-")[1]
            elif "a" in c:
                cRemain = c.split("a")[0]
                self.betaTag = "a" + c.split("a")[1]  # get second item
            elif "b" in c:
                cRemain = c.split("b")[0]
                self.betaTag = "b" + c.split("b")[1]  # get second item
            else:
                cRemain = c
                self.betaTag = None
            self.point = int(a), int(b), int(cRemain)  # assign all to point
        else:
            raise VersionException("cannot process version number %s" % vStr)

        # get date info
        if len(vList) >= 6:
            self.date = int(vList[3]), int(vList[4]), int(vList[5])
        else:
            self.date = None

    def repr(self, format="dot", date=1):
        """
        >>> a = Version('3.25.5')
        >>> a.repr()
        '3.25.5'
        """
        if self.date != None:
            vDate = "%s.%.2i.%.2i" % self.date
        else:
            vDate = None

        if self.betaTag == None:
            vPoint = "%s.%s.%s" % self.point
        else:  # add beta tage
            vPoint = "%s.%s.%s-%s" % (
                self.point[0],
                self.point[1],
                self.point[2],
                self.betaTag,
            )
        # check to see if date should be provided
        if vDate != None and date == 1:
            if format == "dot":
                return "%s.%s" % (vPoint, vDate)
            elif format == "human":
                return "%s (%s)" % (vPoint, vDate)
        else:
            return vPoint

    def __str__(self):
        return self.repr()  # get default

    def __eq__(self, other):
        """only compare date if both have set date

        >>> a = Version('3.25.5')
        >>> b = Version('3.6.0')
        >>> a == b
        False

        >>> a = Version('2.0.0')
        >>> b = Version('2.0.0a3')
        >>> a == b
        False
        """
        if other == None:
            return False
        if self.date == None or other.date == None:
            if self.point == other.point:
                if self.betaTag == other.betaTag:
                    return True
                else:
                    return False
            else:
                return False
        else:  # both have date
            if self.point == other.point:
                if self.date == other.date:
                    if self.betaTag == other.betaTag:
                        return True
            return False

    #     def __ne__(self, other):
    #         """only compare date if both have set date
    #
    #         >>> a = Version('3.25.5')
    #         >>> b = Version('3.6.0')
    #         >>> a != b
    #         True
    #         """
    #         if other == None: return 1
    #         if self.date == None or other.date == None:
    #             if self.point != other.point: return True
    #             else: return False
    #         else: # both have date
    #             if self.point != other.point:
    #                 if self.date != other.date:
    #                     return True
    #             return False

    def __lt__(self, other):
        """only compare date if both have set date

        >>> a = Version('3.25.5')
        >>> b = Version('4.6.0')
        >>> a < b
        True
        """

        # TODO: comparisons here do not look at betaTag
        # this needs to be fixed

        if self.date == None or other.date == None:
            if self.point < other.point:
                return True
            else:
                return False
        else:
            if self.point <= other.point:  # lt or equal
                if self.date < other.date:
                    return True
            return False


#     def __le__(self, other):
#         """only compare date if both have set date
#
#         >>> a = Version('3.25.5')
#         >>> b = Version('4.6.0')
#         >>> a <= b
#         True
#         """
#         if self.date == None or other.date == None:
#             if self.point <= other.point: return True
#             else: return False
#         else:
#             if self.point <= other.point:
#                 if self.date <= other.date:
#                     return True
#             return False
#
#     def __gt__(self, other):
#         """only compare date if both have set date
#
#         >>> a = Version('3.25.5')
#         >>> b = Version('4.6.0')
#         >>> b > a
#         True
#         """
#         if self.date == None or other.date == None:
#             if self.point > other.point: return True
#             else: return False
#         else:
#             if self.point >= other.point: # gt or equal
#                 if self.date > other.date:
#                     return True
#             return False
#
#     def __ge__(self, other):
#         """only compare date if both have set date
#
#         >>> a = Version('3.25.5')
#         >>> b = Version('4.6.0')
#         >>> b >= a
#         True
#         """
#         if self.date == None or other.date == None:
#             if self.point >= other.point: return True
#             else: return False
#         else:
#             if self.point >= other.point:
#                 if self.date >= other.date:
#                     return True
#             return False
#


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
