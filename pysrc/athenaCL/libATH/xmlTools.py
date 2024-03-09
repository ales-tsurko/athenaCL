# -----------------------------------------------------------------||||||||||||--
# Name:          xmlTools.py
# Purpose:       general tools for dealing w/ xml xsl.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


from athenaCL.libATH import drawer
import unittest, doctest

_MOD = "xmlTools.py"

# -----------------------------------------------------------------||||||||||||--

XMLHEAD = '<?xml version="1.0"?>'


# to go from normal strings to xml
def xmlScrub(usrStr):
    """only use for symbols that are common and always need to be changed"""
    # there may be abetter way to do this with
    # from xml.sax.saxutils import escape
    usrStr = usrStr.replace("&", "&amp;")
    usrStr = usrStr.replace(">", "&gt;")
    usrStr = usrStr.replace("<", "&lt;")
    return usrStr


def xmlScrubCopyright(usrStr):
    """replace (c) with the copyright symbol"""
    usrStr = usrStr.replace("(c)", "&copy;")
    return usrStr


# to go from xml to normal strings
def xmlUnScrub(usrStr):
    """this is usally not necessary, as xml parset seem to fix
    automatically"""
    if usrStr.find("&amp;") >= 0:
        usrStr = usrStr.replace("&amp;", "&")
        # print 'xmlTools.py: decoding &amp;'
    return usrStr


# -----------------------------------------------------------------||||||||||||--


def uniToXml(usrStr, encoding="ascii"):
    """
    Encode unicode_data for use as XML or HTML, with characters outside
    of the encoding converted to XML numeric character references.
    note: this is ascii compatble sgml/xml, not utf-8 xml
    """
    # assumes that unicode strings have not yet been decoded
    try:
        unicodeData = usrStr.decode("utf-8")
        msg = unicodeData.encode(encoding, "xmlcharrefreplace")
    except UnicodeDecodeError as e:
        print(_MOD, "utf problem", usrStr)
        # raise ValueError, '%s: %s' % (e, usrStr)
        msg = usrStr
    # for some reason, some characters return strange results:
    # this may be a problem with docbook, and not the xml; solutions
    # here should be compatible with both
    # for umlats (character not needed)
    msg = msg.replace("&#65533;", "")
    # for emdashes...
    msg = msg.replace("&#8211;", "&ndash;")
    msg = msg.replace("&#8212;", "&mdash;")
    # for r single quotes
    msg = msg.replace("&#8217;", "&rsquo;")
    return msg


# -----------------------------------------------------------------||||||||||||--


def paraToSgml(str):
    "convert text with \n marks into separate paragraphs"
    if str == None:
        print(_MOD, "got None for a sgml para conversion")
        str = "none: missing data."
    lines = str.split("\n")
    newStr = ""
    for row in lines:
        newStr = newStr + "<para>%s</para>" % row
    return newStr


# -----------------------------------------------------------------||||||||||||--
# functions for easily going back and forth b/n xml and python


def _dictionaryStrKey(data):
    """check to see this is a dictionary, and all keys are strings"""
    if drawer.isDict(data):  # recurse into dictionary, use key as name
        for key in list(data.keys()):
            if not drawer.isStr(key):
                return 0  # dictionary, but a key is not a string
        return 1  # all keys are strings, a dictionary
    return 0  # not a dictionary


def _resolveOuterName(orient, tab, levelMatch, parentName, name):
    matchKeys = list(levelMatch.keys())
    if "all" in matchKeys or parentName in matchKeys:
        if parentName in matchKeys:
            levelName = levelMatch[parentName]
        elif "all" in matchKeys:
            levelName = levelMatch["all"]
        if orient == "open":
            return '\n%s<%s name="%s">' % (tab, levelName, name)
        else:  # close
            return "\n%s</%s>" % (tab, levelName)

    else:  # dont change naming
        if orient == "open":
            return "\n%s<%s>" % (tab, name)
        else:
            return "\n%s</%s>" % (tab, name)


def pyToXml(parentName, name, dict, indent=1, levelManifest=[]):
    """convert nested python dictionary into an xml data structure
    indent is current indent level
    dictionaries found at node, that consist of all str keys, will be recursed
    levelManifest is a list of labels for each dictionary level
        None will use the dictionary name as is
        pairs match TagName, DisplayName"""

    if levelManifest == [] or levelManifest[0] == None:
        levelMatch = {}
    else:
        if not drawer.isList(levelManifest[0]):  # match all
            levelMatch = {"all": levelManifest[0]}  # match all parents
            # levelName = levelManifest[0]
        else:
            levelMatch = {}  # embeded pairs of possible matches
            for i in range(0, len(levelManifest[0]) - 1):
                # stores pairs in dictionary
                levelMatch[levelManifest[0][i]] = levelManifest[0][i + 1]

    # print _MOD, parentName, name, levelMatch
    # if a level match is given, only name for that object
    msg = []
    tab = "\t" * indent
    msg.append(_resolveOuterName("open", tab, levelMatch, parentName, name))

    keyList = list(dict.keys())
    keyList.sort()
    for key in keyList:
        tab = "\t" * (indent + 1)
        val = dict[key]
        # only recurse into dictionary if dict keys are strings
        if _dictionaryStrKey(val):
            # remove this levelName form the list
            # enter name as parent name
            msg = msg + pyToXml(name, key, val, indent + 1, levelManifest[1:])
        else:
            valStr = xmlScrub(str(val))
            msg.append('\n%s<attr key="%s" value="%s"/>' % (tab, key, valStr))

    tab = "\t" * indent
    msg.append(_resolveOuterName("close", tab, levelMatch, parentName, name))
    return msg  # do not join


def xmlToPy(parentNode):
    """recurse through an already parsed XML dom object"""
    data = {}
    for child in parentNode.childNodes:
        if child.nodeType == child.ELEMENT_NODE:  # primary entries

            # special clase of non-standrad design: need to get attributes
            # from things not nammed 'attr'
            # found in pre 1.3 clone representation
            keyTest = str(child.getAttribute("key"))
            valTest = str(child.getAttribute("value"))
            if keyTest != "" and valTest != "":
                force = 1
            else:
                force = 0

            # q used in pre 1.3 texture parameters
            # item used in preference files
            # these dont have 'name' attributes either
            if force or child.tagName in ["attr", "q", "item"]:  # do not recurse
                key = str(child.getAttribute("key"))
                value = str(child.getAttribute("value"))
                data[key] = value
            else:  # recurse
                subData = xmlToPy(child)
                nameOpt = []
                nameOpt.append(str(child.getAttribute("name")))
                # used in pre 1.3 pref files
                nameOpt.append(str(child.getAttribute("category")))
                name = ""  # default value
                for opt in nameOpt:  # find the opt that is not a ''
                    if opt != "":
                        name = opt
                if name != "":
                    data[str(name)] = subData
                else:
                    data[str(child.tagName)] = subData
    return data


# -----------------------------------------------------------------||||||||||||--
# -----------------------------------------------------------------||||||||||||--
# for generating style sheets


class Dsl:
    """basic class to write dsl files"""

    def __init__(self, docType=None):
        self.msg = []
        self.entityList = []
        self.parameterList = []
        if docType == None:
            docType = (
                "style-sheet",
                "PUBLIC",
                "-//James Clark//DTD DSSSL Style Sheet//EN",
            )
        self.docType = docType

    def addEntity(self, fmt, group, url):
        if (fmt, group, url) not in self.entityList:
            self.entityList.append((fmt, group, url))

    def addParameter(self, key, value, fmt=None):
        """variable are checked for redundancy
        fmt can be quote, noquote, or chunk, paren"""
        temp = {}
        for xKey, (xValue, xFmt) in self.parameterList:
            temp[xKey] = xValue, xFmt
        if key in list(temp.keys()):
            del temp[key]
        temp[key] = (value, fmt)
        self.parameterList = list(temp.items())  # restore as list
        # print self.variableList

    def _getEntity(self):
        """called from write outer"""
        dataStr = []
        for fmt, group, url in self.entityList:
            dataStr.append('<!ENTITY %s %s "%s" CDATA DSSSL>\n' % (fmt, group, url))
            print("xmlTools.py: dsl importing", url)
        return dataStr

    def _writeParameter(self):
        self.parameterList.sort()
        for key, (value, fmt) in self.parameterList:
            # cannot use normal expansion b/c of % needed
            if fmt == None or fmt == "quote":
                valStr = '"%s"' % value
                key = "%" + key + "% "
            elif fmt == "noquote":
                valStr = str(value)
                key = "%" + key + "% "
            elif fmt == "chunk":
                valStr = str(value)
                key = "%" + key + "% "
            elif fmt == "paren":
                valStr = str(value)
                key = "(%s) " % key

            dataStr = "\t(define " + key + valStr + ")\n"
            self.msg.append(dataStr)

    def _writeOuter(self):
        headStr = []
        headStr.append(
            """\
<!DOCTYPE %s %s "%s" 
[\n"""
            % self.docType
        )
        for dataStr in self._getEntity():
            headStr.append(dataStr)
        headStr.append(
            """\
]>
<style-sheet>
<style-specification use="l10n docbook">
<style-specification-body>\n"""
        )

        self.msg.insert(0, "".join(headStr))
        self.msg.append(
            """\
</style-specification-body>
</style-specification>
<external-specification id="docbook" document="dbstyle">
<external-specification id="l10n" document="l10n">
</style-sheet>\n"""
        )

    def update(self):
        self.msg = []
        self._writeParameter()
        self._writeOuter()

    def str(self):
        return "".join(self.msg)

    def write(self, path):
        f = open(path, "w")
        f.writelines(self.msg)
        f.close()


# -----------------------------------------------------------------||||||||||||--
class Xsl:
    def __init__(self):
        """inline determines if css will be inline of text or"""
        self.msg = []
        self.importList = []
        self.variableList = []
        self.parameterList = []

    def addImport(self, url):
        if url not in self.importList:
            self.importList.append(url)

    def addVariable(self, key, value):
        """variable are checked for redundancy"""
        self.variableList.sort()
        temp = {}
        for xKey, xValue in self.variableList:
            temp[xKey] = xValue
        if key in list(temp.keys()):
            del temp[key]
        temp[key] = value
        self.variableList = list(temp.items())  # restore as list
        # print self.variableList

    def addParameter(self, key, value):
        """variable are checked for redundancy"""
        self.parameterList.sort()
        temp = {}
        for xKey, xValue in self.parameterList:
            temp[xKey] = xValue
        if key in list(temp.keys()):
            del temp[key]
        temp[key] = value
        self.parameterList = list(temp.items())  # restore as list
        # print self.variableList

    def _writeImport(self):
        for url in self.importList:
            print("xmlTools.py: xsl importing", url)
            self.msg.append(
                """\
    <xsl:import href="%s"/>\n"""
                % url
            )  # import base

    def _writeVariable(self):
        for key, value in self.variableList:
            self.msg.append(
                """\
    <xsl:variable name="%s">%s</xsl:variable>\n"""
                % (key, value)
            )

    def _writeParameter(self):
        for key, value in self.parameterList:
            self.msg.append(
                """\
    <xsl:param name="%s">%s</xsl:param>\n"""
                % (key, value)
            )

    def _writeOuter(self):
        self.msg.insert(
            0,
            """\
<?xml version='1.0'?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    version="1.0"
    xmlns="http://www.w3.org/TR/xhtml1/transitional"
    exclude-result-prefixes="#default">\n""",
        )

        self.msg.append(
            """\
</xsl:stylesheet>\n"""
        )

    def update(self):
        self.msg = []
        self._writeImport()
        self._writeParameter()
        self._writeVariable()
        self._writeOuter()

    def str(self):
        return "".join(self.msg)

    def write(self, path):
        f = open(path, "w")
        f.writelines(self.msg)
        f.close()


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        a = {
            "a": 1,
            "b": 2,
            "d": {
                "3": "recursion",
                "five": {
                    "sdf": 2345,
                    "wer": [3, 4, 5],
                },
                "8": "rocks",
            },
            "f": {
                "3": "recursion",
                "5": {
                    "sdf": 2345,
                    "wer": [3, 4, 5],
                },
            },
            "c": 3,
        }

        g = pyToXml("", "test", a, 1, ["thingA", None, ("five", "thingB")])


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    from athenaCL.test import baseTest

    baseTest.main(Test)
