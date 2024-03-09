# -----------------------------------------------------------------||||||||||||--
# Name:          htmlTools.py
# Purpose:       general tools for creating web pages.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2002-2008 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


import os, copy, time, random, datetime
from athenaCL.libATH import drawer

# imported by fileTools; do not import here

# optional modules
try:
    from html.parser import HTMLParser
except ImportError:
    pass

# -----------------------------------------------------------------||||||||||||--


class StyleSheet:
    """get style sheet as string for writting or embedding"""

    def __init__(self, inline=0):
        """inline determines if css will be inline of text or"""
        self.msg = []
        self.inline = inline
        # init w/ defaults
        self.setBkg()
        self.setFontFace()
        self.setColorDict()
        self.setFontDict()
        self.setTableDict()

    def setBkg(self, bkgImage=None, bkgAttach=None):
        if bkgImage == None:
            self.bkgImage = ""
        else:
            self.bkgImage = bkgImage
        if bkgAttach == None:
            self.bkgAttach = "fixed"  # can be something else
        else:
            self.bkgAttach = bkgAttach

    def setFontFace(self, fontBase=None, fontMono=None):
        if fontBase == None:
            self.fontBase = "Trebuchet MS, arial, sans-serif"
        else:
            self.fontBase = fontBase
        if fontMono == None:
            self.fontMono = "courier, typewriter, monospace"
        else:
            self.fontMono = fontMono

    def setTableDict(self, tableDict=None):
        # not yet implemented
        self.tableDict = {}
        self.tableDict["tableA-bgImage"] = ""
        self.tableDict["tableA-bgColor"] = ""

    # <STYLE TYPE="text/css">
    # <!--
    # .deepsea, .deepsea TD, .deepsea TH
    # {
    # background-image:url('deepsea.gif');
    # background-color:blue;
    # color:white;
    # font-family:sans-serif;
    # font-weight:600;
    # }
    # -->
    # </STYLE>

    def setColorDict(self, colorDict=None):
        # load defaults
        self.colorDict = {}
        self.colorDict["bg"] = "#000000"
        self.colorDict["p"] = "#cccccc"
        self.colorDict["h1"] = "#cccccc"
        self.colorDict["h2"] = "#cccccc"
        self.colorDict["h3"] = "#cccccc"
        self.colorDict["sm"] = "#cccccc"  # small
        self.colorDict["mon"] = "#cccccc"  # monospaced

        self.colorDict["link"] = "#CCCC99"
        self.colorDict["hover"] = "#666633"
        self.colorDict["post"] = "#999999"
        self.colorDict["hr"] = "#999999"

        if colorDict != None:  # assign
            for key in list(colorDict.keys()):
                self.colorDict[key] = colorDict[key]  # set new values

    def setFontDict(self, fontDict=None):
        self.fontDict = {}
        self.fontDict["p"] = 8
        self.fontDict["h1"] = 12
        self.fontDict["h2"] = 10
        self.fontDict["h3"] = 8
        self.fontDict["sm"] = 7
        self.fontDict["mon"] = 6

        if fontDict != None:
            for key in list(fontDict.keys()):
                self.fontDict[key] = fontDict[key]  # set new values

    def _writeBkg(self):
        self.msg.append(
            """
    body {background-color: %s;
            background-image: url(%s);
            background-attachment: %s
          }
    """
            % (self.colorDict["bg"], self.bkgImage, self.bkgAttach)
        )

    def _writeMain(self):
        self.msg.append(
            """
    pre {font-size: %spt;
        word-wrap: break-word;
        font-family: %s;
        color: %s;
        font-weight: plain;}
    kbd {font-size: %spt;
        word-wrap: break-word;
        font-family: %s;
        color: %s;
        font-weight: plain;}
    ol {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal}
    span {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal}
"""
            % (
                self.fontDict["mon"],
                self.fontMono,
                self.colorDict["mon"],
                self.fontDict["mon"],
                self.fontMono,
                self.colorDict["mon"],
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],  # p
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],
            )
        )

        self.msg.append(
            """
    p {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal;
        margin-bottom: 0em;}
    .plain {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal;}
    .bold {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: bold;}
    .boldgrey {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: bold;}

    .head {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: bold;
        margin-bottom: 0em;}
    .subhead {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: bold;
        margin-bottom: 0em;}
    .small {font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal;
        margin-bottom: 0em;}
    .userinput {font-size: %spt;
        word-wrap: break-word;
        font-family: %s;
        color: %s;
        font-weight: bold;}
        
"""
            % (
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],  # p
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["h2"],
                self.fontDict["h1"],
                self.fontBase,
                self.colorDict["h1"],
                self.fontDict["h2"],
                self.fontBase,
                self.colorDict["h2"],
                self.fontDict["sm"],
                self.fontBase,
                self.colorDict["sm"],
                self.fontDict["mon"],
                self.fontMono,
                self.colorDict["mon"],
            )
        )

        self.msg.append(
            """
    table{padding: 0px 0px 0px 0px;
        margin: 0px 0px 0px 0px;
        }
    tr{padding: 0px 0px 0px 0px;
        margin: 0px 0px 0px 0px;
        }
    th{font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal}
    td{font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal}
    dt{font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: normal}
"""
            % (
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],  # p
                self.fontDict["p"],
                self.fontBase,
                self.colorDict["p"],
            )
        )

        self.msg.append(
            """
    h1{font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: bold}
    h2{font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: bold}
    h3{font-size: %spt;
        font-family: %s;
        color: %s;
        font-weight: bold}
"""
            % (
                self.fontDict["h1"],
                self.fontBase,
                self.colorDict["h1"],
                self.fontDict["h2"],
                self.fontBase,
                self.colorDict["h2"],
                self.fontDict["h3"],
                self.fontBase,
                self.colorDict["h3"],
            )
        )

    def _writeHr(self):
        self.msg.append(
            """
    hr {size: 4;
         color: %s;
         noshade;}
"""
            % (self.colorDict["hr"])
        )

    def _writeLinks(self):
        self.msg.append(
            """
    a:link {
        text-decoration: none;
        color: %s}
    a:active     {
        text-decoration: none;
        color: %s}
    a:visited {
        text-decoration: none;
        color: %s}
    a:Hover {
        text-decoration : underline;
        color: %s;}
"""
            % (
                self.colorDict["link"],
                self.colorDict["link"],
                self.colorDict["post"],
                self.colorDict["hover"],
            )
        )

    def update(self):
        self.msg = []

        self._writeBkg()
        self._writeMain()
        self._writeHr()
        self._writeLinks()

        if self.inline:
            self.msg.insert(0, '<style type="text/css">\n')
            self.msg.append("</style>\n")

    def str(self):
        return "".join(self.msg)

    def write(self, path):
        f = open(path, "w")
        f.writelines(self.msg)
        f.close()


# -----------------------------------------------------------------||||||||||||--


class ImageNameBank:
    """used to store and generate file names for algo generated titles
    and other images
    localMode is for use as a cgi script: provides files names but does
    not try to render images
    """

    def __init__(self, localMode):
        self.localMode = localMode
        self.fileNames = {}  # dictionary of groups
        self.fileNames["_"] = []  # non-named
        # group max determines number of possible images
        # if max is reached, returns a random image from that group
        self.groupMax = {}
        self.groupMax["_"] = None

    def groupMax(self, group, max=10):
        self.groupMax[group] = max

    def _getName(self, group, ext):
        if self.localMode == "cgi":
            indexStr = "0"  # always get 0, and assume that its there
        else:
            indexStr = str(len(self.fileNames[group]))
        return "%s%s%s" % (group, indexStr, ext)

    def __call__(self, parentDir, ext=".gif", group=None, groupMax=None):
        if group == None:
            group = "_"
        if group not in list(self.fileNames.keys()):
            self.fileNames[group] = []
        # seems like this should only happen if groupMax is not
        # None, but not sure
        self.groupMax[group] = groupMax  # always allow resettting

        # if len more than max, and max is not None, then use an old image path
        if self.localMode == "cgi":
            name = self._getName(group, ext)
            path = os.path.join(parentDir, self._getName(group, ext))
            new = 0
        elif (
            len(self.fileNames[group]) >= self.groupMax[group]
            and self.groupMax[group] != None
        ):  # use old
            path = random.choice(self.fileNames[group])
            dir, name = os.path.split(path)
            new = 0  # suggests if a new file needs to be generated
        else:  # add to new
            name = self._getName(group, ext)
            path = os.path.join(parentDir, name)
            self.fileNames[group].append(path)
            new = 1
        return name, path, new

    def addLocal(self, parentDir, nameList):
        """set local files that are not dynamically generated, but
        paths need to be included for upload
        appends each time called"""
        group = "_local"
        groupMax = 999
        if group not in self.fileNames:
            self.fileNames[group] = []
            self.groupMax[group] = groupMax

        for name in nameList:
            path = os.path.join(parentDir, name)
            self.fileNames[group].append(path)

    def report(self):
        allPaths = []
        for group in list(self.fileNames.keys()):
            allPaths = allPaths + self.fileNames[group]
        return allPaths


# -----------------------------------------------------------------||||||||||||--


class RollOver:
    def __init__(self, imageDict, wpObj):
        self.imageDict = imageDict  # list of dictionaries of image data
        self.wpObj = wpObj

    def script(self):
        headScript = "<script>\n<!--\nif (document.images) {\n"

        sortedKeys = list(self.imageDict.keys())
        sortedKeys.sort()

        for key in sortedKeys:  # key is a number
            dict = self.imageDict[key]
            headScript = headScript + "\timage%son = new Image();\n" % key
            headScript = headScript + (
                '\timage%son.src = "%s";\n'
                % (key, self.wpObj.getImagePath(dict["onImage"]))
            )
        for key in sortedKeys:
            dict = self.imageDict[key]
            headScript = headScript + "\timage%soff = new Image();\n" % key
            headScript = headScript + (
                '\timage%soff.src = "%s";\n'
                % (key, self.wpObj.getImagePath(dict["offImage"]))
            )
        headScript = (
            headScript
            + """}
function turnOn(imageName) {
  if (document.images) {
     document[imageName].src = eval(imageName + "on.src");
  }
}
function turnOff(imageName) {
  if (document.images) {
     document[imageName].src = eval(imageName + "off.src");
  }
}
// -->
</script>
"""
        )
        return headScript

    def idList(self):  # id numbers, with 1 offset
        return list(self.imageDict.keys())

    def linkImage(self, id, postBreaks=0):
        imageName = "image%s" % id
        target = self.imageDict[id]["target"]  #
        label = self.imageDict[id]["label"]  #
        offSrc = self.imageDict[id]["offImage"]  #
        msg = []
        msg.append('<a href="%s" onMouseOver="turnOn' % target)
        msg.append("('%s')" % imageName)  # type of quotes matters
        msg.append('" onMouseOut="turnOff')
        msg.append("('%s')" % imageName)  # type of quotes matters
        msg.append(
            '"><img name="%s" src="%s" alt="%s" border=0></a>'
            % (imageName, self.wpObj.getImagePath(offSrc), label)
        )
        for i in range(0, postBreaks):
            msg.append("<br />\n")
        return "".join(msg)

    def linkImageTarget(self, id, target, label, postBreaks=0):
        imageName = "image%s" % id
        offSrc = self.imageDict[id]["offImage"]
        msg = []
        msg.append('<a href="%s" onMouseOver="turnOn' % target)
        msg.append("('%s')" % imageName)  # type of quotes matters
        msg.append('" onMouseOut="turnOff')
        msg.append("('%s')" % imageName)  # type of quotes matters
        msg.append(
            '"><img name="%s" src="%s" alt="%s" border=0></a>'
            % (imageName, self.wpObj.getImagePath(offSrc), label)
        )
        for i in range(0, postBreaks):
            msg.append("<br />\n")
        return "".join(msg)


class PopUp:
    def __init__(self):
        self.width = 80
        self.height = 60

    def script(self):
        codeC = """
<script language="JavaScript" type ="text/javascript">
function openDLWin(url, name, size) {
window.open(url, name, size + 'toolbar=no,location=no,directories=no,status=yes,menubar=no,scrollbars=no,resizable=no,copyhistory=yes');
      }
</script>
"""
        # can add   ,left=200,top=200
        # to set position on screen
        return codeC

    def linkToPop(self, html=None, label="open", width=200, height=80, postBreaks=1):
        codeC = """
<a href="" onclick="openDLWin('%s', '%s', 'width=%s, height=%s,');return false" onmouseover="window.status='';return true" onmouseout="window.status='';return true" title="%s" style="cursor:pointer;">%s</a>
""" % (
            html,
            label,
            width,
            height,
            label,
            label,
        )

        msg = [
            codeC,
        ]
        for i in range(0, postBreaks):
            msg.append("<br />\n")
        return "".join(msg)


# syntax: popup_window(URL, width, height)
# onclick="popup_window('javascript:document.write(&quot;<html><head><style>body{font: normal 100% verdana}</style><title>Dynamic Content</title></head><body> &quot; + opener.document.forms[0].sampletext.value + &quot;</body></html>&quot;);',500,400);return false;"> Display text in pop-up window </a>

# -----------------------------------------------------------------||||||||||||--


class WebPage:
    def __init__(
        self,
        tableW=640,
        description="",
        colorDict=None,
        fontDict=None,
        titleRoot="",
        keywords="",
        iconURL="",
    ):
        self.docType = ""  # can add in a subclass
        self.htmlOpen = """<html xmlns="http://www.w3.org/1999/xhtml">\n"""
        self.htmlClose = """</html>\n"""
        self.bodyOpen = "<body>\n"
        self.bodyClose = """</body>\n"""
        self.BR = "<br />"
        self.spanOpen = "<span>"
        self.spanClose = "</span>"
        self.divOpen = "<div id='%s'>"
        self.divClose = "</div>"

        self.pOpen = "<p>"
        self.pClose = "</p>"  # return probided by break
        self.h1Open = "<h1>"
        self.h1Close = "</h1>"
        self.h2Open = "<h2>"
        self.h2Close = "</h2>"
        self.h3Open = "<h3>"
        self.h3Close = "</h3>"

        self.preOpen = "<pre>"  # maintains formatted text
        self.preClose = "</pre>"

        if colorDict == None:
            self.colorDict = {}
            self.colorDict["bg"] = "#000000"
            self.colorDict["p"] = "#cccccc"
            self.colorDict["h1"] = "#cccccc"
            self.colorDict["h2"] = "#cccccc"
            self.colorDict["h3"] = "#cccccc"
            self.colorDict["link"] = "#CCCC99"
            self.colorDict["hover"] = "#666633"
            self.colorDict["post"] = "#999999"
            self.colorDict["hr"] = "#999999"
        else:
            self.colorDict = colorDict

        if fontDict == None:
            self.fontDict = {}
            self.fontDict["p"] = 12
            self.fontDict["h1"] = 14
            self.fontDict["h2"] = 14
            self.fontDict["h3"] = 12
        else:
            self.fontDict = fontDict

        self.tableW = tableW
        self.description = description.replace("\n", "")  # remove breaks
        self.titleRoot = titleRoot
        self.keywords = keywords
        self.iconURL = iconURL
        self.imageRoot = "images"  # use /images for absoulte links
        self.fileRoot = None
        self.headOpenClose = None  # header info; may be generated head of page

    # -----------------------------------------------------------------------||--
    def setImageRoot(self, path):
        self.imageRoot = path

    def getImagePath(self, name):
        if name[0:7] == "http://":  # its a complete path, cannot calter
            return name
        if self.imageRoot != "" and self.imageRoot != None:
            return os.path.join(self.imageRoot, name)
        else:  # no subdirectory
            return name

    def setFileRoot(self, path):
        """use for distingushing cgi/non cgi versions were abs paths are needed"""
        self.fileRoot = path

    def getFilePath(self, name):
        """ "assume given a name; determine if need to add path"""
        if name.startswith("http://") or name.startswith("javascript"):
            # its a complete path, cannot calter
            return name
        if self.fileRoot != "" and self.fileRoot != None:
            return os.path.join(self.fileRoot, name)
        else:  # no subdirectory
            return name

    def headInit(self, pageTitle, bkg="", script=None, css=None):
        """script can be any java script that needs to be included in the
        head tag; creates and adds css"""
        msg = []
        msg.append(
            """
<head>
<title>%s | %s</title>
<meta http-equiv="content-type" content="text/html;charset=ISO-8859-1">
<meta name="description" content=%r>
<meta name="keywords" content=%r>
<link rel="SHORTCUT ICON" href=%r>
"""
            % (self.titleRoot, pageTitle, self.description, self.keywords, self.iconURL)
        )

        if script != None:
            msg.append(script)

        if css == None:  # use basic style sheet
            inline = 1
            cssObj = StyleSheet(inline)
            cssObj.setFontFace(
                "Trebuchet MS, arial, sans-serif", "courier, typewriter, monospace"
            )
            cssObj.setColorDict(self.colorDict)
            cssObj.setFontDict(self.fontDict)
            cssObj.setBkg(self.getImagePath(bkg))
            cssObj.update()
            msg = msg + cssObj.msg  # add lines to list
        else:
            # if a file, use proper link
            if css.endswith(".css"):
                cssPath = self.getFilePath(css)
                msg.append(
                    """<link title="new" rel="stylesheet" href="%s" type="text/css"/>"""
                    % cssPath
                )
            # else, ssimply append css text, w/ start and end style tags
            else:
                msg.append(css)
        # contains both the head open and close, and all necessary stuff
        self.headOpenClose = "".join(msg)

    def tableInit(
        self, tableWidth, col, color=None, colHeight=1, colWidth=None, colAlign="left"
    ):
        """initializes table tags accoring to arguements"""
        if colWidth == None:
            if drawer.isStr(tableWidth):
                colWidth = tableWidth
            else:
                colWidth = tableWidth / col
        if tableWidth == None:
            tableWidth = col * colWidth

        self.tableOpen = """
<table cellspacing="0" cellpadding="0" width="%s">\n""" % (
            tableWidth
        )
        self.tableClose = """</table>\n"""
        self.trOpen = "\t<tr>\n"
        self.trClose = "\t</tr>\n"
        if color == None:
            self.tdOpen = """\t
<td width='%s' height='%s' align='%s' valign="top">\n""" % (
                colWidth,
                colHeight,
                colAlign,
            )
        else:
            self.tdOpen = """\t
<td width='%s' height='%s' align='%s' valign="top" bgcolor='%s'>\n
""" % (
                colWidth,
                colHeight,
                colAlign,
                color,
            )
        self.tdClose = """\t</td>\n"""

    def pText(self, textString, style="off", postBreaks=0):
        """wraps text in p/h tags as needed"""
        msg = []
        if style == "bold":
            msg.append("""<span class="bold">""")
        elif style == "boldgrey":
            msg.append("""<span class="boldgrey">""")
        elif style == "plain":
            msg.append("""<span class="plain">""")
        elif style == "mono":  # pre maintains fromatting
            msg.append(self.preOpen)
        elif style == "h3" or style == "small" or style == "sm":
            msg.append("""<span class="small">""")
        elif style == "h2" or style == "subhead":
            msg.append("""<span class="subhead">""")
        elif style == "h1" or style == "head":
            msg.append("""<span class="head">""")
        elif style == "p":
            msg.append(self.pOpen)
        else:
            msg.append(self.pOpen)
        # add text
        msg.append(textString)
        # close
        if style == "bold":
            msg.append(self.spanClose)
        elif style == "boldgrey":
            msg.append(self.spanClose)
        elif style == "plain":
            msg.append(self.spanClose)
        elif style == "mono":
            msg.append(self.preClose)
        elif style == "h3" or style == "small":
            msg.append(self.spanClose)
        elif style == "h2" or style == "subhead":
            msg.append(self.spanClose)
        elif style == "h1" or style == "head":
            msg.append(self.spanClose)
        elif style == "p":
            msg.append(self.pClose)
        else:
            msg.append(self.pClose)

        for i in range(0, postBreaks):
            msg.append(self.BR)
        return "".join(msg)

    def span(self, textString, classStr):
        return """<span class="%s">%s</span>""" % (classStr, textString)

    def hText(self, textStr, style="h1", postBreaks=0):
        """wrap text around a hedding tag"""
        msg = []
        if style == "h3":
            msg.append(self.h3Open)
        elif style == "h2":
            msg.append(self.h2Open)
        elif style == "h1":
            msg.append(self.h1Open)
        msg.append(textStr)
        if style == "h3":
            msg.append(self.h3Close)
        elif style == "h2":
            msg.append(self.h2Close)
        elif style == "h1":
            msg.append(self.h1Close)
        for i in range(0, postBreaks):
            msg.append(self.BR)
        return "".join(msg)

    def imageString(self, target, label="img", postBreaks=1):
        """creates a simple image entry with an alt lable
        assumes images/ dir
        """
        msg = []
        msg.append(
            "<img src='%s' alt='%s' border='0'>" % (self.getImagePath(target), label)
        )
        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def imageResize(self, target, label="img", w=None, h=None, postBreaks=1):
        """creates a simple image entry with an alt lable
        assumes images/ dir
        """
        msg = []
        if w == None and h == None:
            msg.append(
                "<img src='%s' alt='%s' border='0'>"
                % (self.getImagePath(target), label)
            )
        elif w == None and h != None:
            msg.append(
                "<img src='%s' alt='%s' border='0' height='%s'>"
                % (self.getImagePath(target), label, h)
            )
        elif w != None and h == None:
            msg.append(
                "<img src='%s' alt='%s' border='0' width='%s'>"
                % (self.getImagePath(target), label, w)
            )
        elif w != None and h != None:
            msg.append(
                "<img src='%s' alt='%s' border='0' width='%s' height='%s'>"
                % (self.getImagePath(target), label, w, h)
            )
        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def linkName(self, label):
        return "<a name='%s'></a>" % label

    def linkStringWindow(self, target, label, postBreaks=1, strBreak=1):
        """a link that opens a new window"""
        if strBreak > 0:  # used to be a max char length
            label = drawer.urlStrBreak(label)
        target = self.getFilePath(target)
        msg = []
        msg.append("<a href='%s' target='_blank'>%s</a>" % (target, label))
        for i in range(0, postBreaks):
            msg.append(self.BR)
        return "".join(msg)

    def linkString(self, target, label, postBreaks=1, strBreak=1):
        # if label is a url, modify with spaces so line's wrap netter
        if strBreak > 0:  # used to be a max char length
            label = drawer.urlStrBreak(label)
        target = self.getFilePath(target)
        msg = []
        msg.append('<a href="%s">%s</a>' % (target, label))
        for i in range(0, postBreaks):
            msg.append(self.BR)
        return "".join(msg)

    def linkImage(self, target, label, image, postBreaks=1):
        imagePath = self.getImagePath(image)
        target = self.getFilePath(target)
        msg = []
        msg.append(
            '<a href="%s"><img src="%s" alt="%s" border=0></a>'
            % (target, imagePath, label)
        )
        for i in range(0, postBreaks):
            msg.append(self.BR)
        # msg.append('\n')
        return "".join(msg)

    def linkImageWindow(self, target, label, image, postBreaks=1):
        target = self.getFilePath(target)
        imagePath = self.getImagePath(image)
        msg = []
        msg.append(
            "<a href='%s' target='_blank'><img src='%s' alt='%s' border=0></a>"
            % (target, imagePath, label)
        )
        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def linkAmazonId(self, isbn, label, id):
        "gen a item link; id can be isbn or asin"
        a = '<a href="http://www.amazon.com/exec/obidos/redirect?tag=%s' % id
        b = '&creative=9325&camp=1789&link_code=as2&path=ASIN/%s" ' % isbn
        c = 'target="_blank">%s' % label
        d = '</a><img src="http://www.assoc-amazon.com/e/ir?t=%s' % id
        e = (
            '&l=as2&o=1&a=%s" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px important!"/>'
            % isbn
        )
        return a + b + c + d + e

    def googleAnalytics(self, trackerId):
        a = """
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>"""
        b = """ 
<script type="text/javascript">
var pageTracker = _gat._getTracker("%s");
pageTracker._trackPageview();
</script>
""" % (
            trackerId
        )
        return a + b

    def embed(self, src):
        htmlStr = (
            """
<EMBED src="%s" autostart="false" 
         controls="console" width="160" height="16" autostart="true" loop="true" 
         volume="100" mastersound />"""
            % src
        )
        return htmlStr

    def refreshPage(self, dst):
        # NOTE : content and URL are in the same quote
        htmlStr = (
            """\
<html><head><meta http-equiv="REFRESH" content="0; URL=%s"></head></html>
"""
            % dst
        )
        return htmlStr

    def framePage(self, sizeList=None, pathList=None, nameList=None):
        # defaults are for docbook output
        if sizeList == None:
            sizeList = 30, 70
        if pathList == None:
            pathList = "www/indexFrame.htm", "www/index.htm"
        if nameList == None:
            nameList = "menu", "body"

        colStr = "%s@,%s@" % (sizeList[0], sizeList[1])
        colStr = colStr.replace("@", "%")  # insert precent
        # need a frame border on one side to resize horizontal width
        htmlStr = (
            """<html><frameset cols="%s"><frame src="%s" name="%s" frameborder="0" ><frame src="%s" name="%s" frameborder="1"></frameset></html>"""
            % (colStr, pathList[0], nameList[0], pathList[1], nameList[1])
        )
        return htmlStr

    ### specialized table utilities
    def dataTable(self, label, data, postBreaks=1):
        """creates simple table based on labels and data"""
        self.tableInit(self.tableW, 1)

        msg = []
        msg.append(self.tableOpen)
        msg.append(self.trOpen)

        msg.append(self.tdOpen)
        msg.append(self.pText(label, "bold"))
        msg.append(self.tdClose)
        msg.append(self.tdOpen)
        msg.append(self.pOpen)
        msg.append(data)
        msg.append(self.pClose)
        msg.append(self.tdClose)

        msg.append(self.trClose)
        msg.append(self.tableClose)

        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def equalTable(self, dataList, postBreaks=1):
        """divides text in a list into two tables"""
        halfIndex = len(dataList) / 2
        dataA = ""
        dataB = ""
        i = 0
        for entry in dataList:
            if i >= halfIndex:
                dataB = dataB + entry + self.BR
            else:
                dataA = dataA + entry + self.BR
            i = i + 1
        self.tableInit(self.tableW, 2)
        msg = []
        msg.append(self.tableOpen)
        msg.append(self.trOpen)
        msg.append(self.tdOpen)
        msg.append(self.pOpen)
        msg.append(dataA)
        msg.append(self.pClose)
        msg.append(self.tdClose)
        msg.append(self.tdOpen)
        msg.append(self.pOpen)
        msg.append(dataB)
        msg.append(self.pClose)
        msg.append(self.tdClose)
        msg.append(self.trClose)
        msg.append(self.tableClose)
        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def graphicTable(
        self,
        source=None,
        foreColor="#000000",
        backColor="#aaaaaa",
        xMult=1,
        yMult=1,
        rowHeight=1,
        postBreaks=0,
    ):
        """creates a graphic out of a table
        very inefficient, and should be replaced by PIL code"""
        # foreColor can be a list of colors that are chosen from at random
        if not drawer.isList(foreColor):
            foreColor = [
                foreColor,
            ]

        if source == None:  # creates a break with random distribution
            lineGraph = []
            widthSize = random.choice((1,))
            for i in range(0, (self.tableW / widthSize)):
                pixel = random.choice((0, 0, 0, 1, 1, 1, 1))
                lineGraph.append(pixel)
            source = (lineGraph,)

        newSource = []
        for row in source:
            newRow = []
            for col in row:
                for extraX in range(0, xMult):
                    newRow.append(col)
            for extraY in range(0, yMult):
                newSource.append(newRow)
        oldSource = copy.deepcopy(source)
        source = newSource

        sourceH = len(source)
        sourceW = len(source[0])
        self.tableInit(sourceW, sourceW)
        msg = []
        msg.append(self.tableOpen)
        for row in range(0, sourceH):
            msg.append(self.trOpen)
            for col in range(0, sourceW):
                if source[row][col] == 1:
                    if foreColor == None:  # last arg is row height
                        self.tableInit(sourceW, sourceW, None, rowHeight)
                    else:
                        color = random.choice(foreColor)
                        self.tableInit(sourceW, sourceW, color, rowHeight)
                else:
                    if backColor == None:
                        self.tableInit(sourceW, sourceW, None, rowHeight)
                    else:
                        self.tableInit(sourceW, sourceW, backColor, rowHeight)
                msg.append(self.tdOpen)
                msg.append(self.tdClose)
            msg.append(self.trClose)
        msg.append(self.tableClose)

        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def _updateColData(self, colData):
        """provides backward compat for col data"""
        # backward compat
        if "outline" not in colData:
            colData["outline"] = ""  # a string w / chars = 'lrtb'
        if "outlineWidth" not in colData:
            colData["outlineWidth"] = 1  # a string w / chars = 'lrtb'
        if "outlineColor" not in colData:
            colData["outlineColor"] = "#000000"  # a string w / chars = 'lrtb'
        if "pad" not in colData:
            colData["pad"] = 0  # can be vert, horiz, both
        if "color" not in colData:
            colData["color"] = None  # none
        return colData

    def nTable(self, colList=None, postBreaks=0):
        """creates any number of cols in a table based on sizes
            and info used in colList: a list of dictionaries defining each col
        padding must be thet same for all tables, if used
        """
        if colList == None:
            colList = []
            colList.append(
                {"width": 320, "align": "right", "color": None, "content": "colA"}
            )
            colList.append(
                {"width": 15, "align": "right", "color": None, "content": "colB"}
            )
            colList.append(
                {"width": 90, "align": "left", "color": None, "content": "colC"}
            )
        totWid = 0
        for entry in colList:
            totWid = totWid + entry["width"]

        msg = []
        self.tableInit("%s" % totWid, 1, None, 1, None, "left")  # for main
        msg.append(self.tableOpen)
        msg.append(self.trOpen)  # need one row

        for colData in colList:
            colData = self._updateColData(colData)

            if len(colData["outline"]) > 0:
                outlineOffset = len(colData["outline"]) * colData["outlineWidth"]
            else:
                outlineOffset = 0

            rawWidth = colData["width"]
            align = colData["align"]
            color = colData["color"]
            content = colData["content"]
            pad = colData["pad"]
            outline = colData["outline"]
            if outline == None:
                outline = ""  # replace w/ empty str
            outlineWidth = colData["outlineWidth"]
            outlineColor = colData["outlineColor"]

            if outline.find("l") >= 0:
                # create left line
                self.tableInit(None, 1, outlineColor, 1, outlineWidth, align)
                msg.append(self.tdOpen)
                msg.append(self.tdClose)

            if pad != 0:
                # create left pad
                self.tableInit(None, 1, color, 1, int(pad * 0.5), align)  # each column
                msg.append(self.tdOpen)
                msg.append(self.tdClose)

            # create content
            self.tableInit(None, 1, color, 1, (rawWidth - pad - outlineOffset), align)
            msg.append(self.tdOpen)
            msg.append(content)
            msg.append(self.tdClose)

            if pad != 0:
                # create left pad
                self.tableInit(None, 1, color, 1, int(pad * 0.5), align)  # each column
                msg.append(self.tdOpen)
                msg.append(self.tdClose)

            if outline.find("r") >= 0:
                # create left line
                self.tableInit(None, 1, outlineColor, 1, outlineWidth, align)
                msg.append(self.tdOpen)
                msg.append(self.tdClose)

        self.tableInit("%s" % totWid, 1, None, 1, None, "left")  # for
        msg.append(self.trClose)  # need one row
        msg.append(self.tableClose)

        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def dataTableAdj(self, label, data, lConfig=[100, "right"], rConfig=[100, "right"]):
        # like a data table, but with adjustable width
        colList = []
        colList.append(
            {"width": lConfig[0], "align": lConfig[1], "color": None, "content": label}
        )
        colList.append(
            {"width": rConfig[0], "align": rConfig[1], "color": None, "content": data}
        )
        return self.nTable(colList)

    ### general utilities
    def divider(self, type="image", imgFile=None, postBreaks=2):
        """creates a line break"""
        # none makes div, fg color, bg color, xscale, yscale, rowHeight, breaks
        if type == "table":
            return self.graphicTable(None, self.colorDict["hr"], None, 1, 1, 2, 1)
        elif type == "image":
            if imgFile == None:
                imgFile = "hr.gif"  # default name for hr
            return self.linkImage("#top", "----------", "%s" % imgFile, postBreaks)
        elif type == "hr":
            msg = ["<HR />"]
            for i in range(0, postBreaks):
                msg.append(self.BR)
            msg.append("\n")
            return "".join(msg)

    def fontSlice(
        self,
        sourceStr="this is a test",
        folder="charTitle",
        forceWidth=None,
        postBreaks=1,
    ):
        """this is designed to take an image for each character and string
        it into a tabel with all necessary values"""
        imageList = []
        sourceStr = sourceStr.lower()
        for char in sourceStr:
            if char == " ":
                target = "%s/%s.gif" % (folder, "_")
            elif char == "/":
                target = "%s/%s.gif" % (folder, "fSlash")
            else:
                target = "%s/%s.gif" % (folder, char)
            label = char
            imageList.append(self.imageString(target, label, 0))

        msg = []
        if forceWidth != None:  # pack text into table
            self.tableInit(None, len(imageList), None, 1, forceWidth, "center")
            msg.append(self.tableOpen)
            msg.append(self.trOpen)
            for entry in imageList:
                msg.append(self.tdOpen)
                msg.append(entry)
                msg.append(self.tdClose)
            msg.append(self.trClose)
            msg.append(self.tableClose)
        else:  # throw characters into one table
            self.tableInit(self.tableW, 1)
            msg.append(self.tableOpen)
            msg.append(self.trOpen)
            msg.append(self.tdOpen)
            msg.append("".join(imageList))
            msg.append(self.tdClose)
            msg.append(self.trClose)
            msg.append(self.tableClose)

        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def createParagraph(self, sourceStr, postBreaks=0):
        """replace \n into html <BR> commands"""
        lineList = []
        thisLine = []
        i = 0
        while sourceStr[0] == "\n":  # remove leading return carriage
            sourceStr = sourceStr[1:]
        msg = []
        if sourceStr.find(self.preOpen) >= 0:
            msg.append(sourceStr)  # dont mess with pre-formatted strings
        else:
            for char in sourceStr:
                thisLine.append(char)
                if char == "\n":
                    lineList.append("".join(thisLine))
                    thisLine = []
                elif i == len(sourceStr) - 1:  # if last, apend what is left
                    lineList.append("".join(thisLine))
                i = i + 1
            for i in range(0, len(lineList)):
                line = lineList[i]
                if i != len(lineList) - 1:  # if not last line
                    msg.append("%s%s\n" % (line, self.BR))
                else:
                    msg.append(line)
                i = i + 1
        # add post breaks
        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")  # for html formatting
        return "".join(msg)

    def dateStr(self, dateRepr):
        """convert a date format into one used for rss
        see http://www.daniweb.com/code/snippet346.html
        Sat, 07 Sep 2002 00:00:01 GMT
        """
        wkdLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        monthLabels = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        tStrDefault = "00:00:01 GMT"

        if drawer.isStr(dateRepr):
            # assume it is a string such as 2007.02.01
            dateList = dateRepr.split(".")
            year = int(dateList[0])
            month = int(dateList[1])
            day = int(dateList[2])
            obj = datetime.date(year, month, day)
            dayStr = wkdLabels[obj.weekday()]
            monthStr = monthLabels[obj.month - 1]
            return "%s, %s %s %s %s" % (
                dayStr,
                drawer.intToStr(day, 2),
                monthStr,
                year,
                tStrDefault,
            )

    def dateAbbreviate(self, dateStr):
        dayRef = {
            "Monday": "Mon",
            "Tuesday": "Tue",
            "Wednesday": "Wed",
            "Thursday": "Thu",
            "Friday": "Fri",
            "Saturday": "Sat",
            "Sunday": "Sun",
        }

        monthRef = {
            "January": "Jan",
            "February": "Feb",
            "March": "Mar",
            "April": "Apr",
            "May": "May",
            "June": "Jun",
            "July": "Jul",
            "August": "Aug",
            "September": "Sep",
            "October": "Oct",
            "November": "Nov",
            "December": "Dec",
        }

        for key, value in list(dayRef.items()):
            dateStr = dateStr.replace(key, value)
        for key, value in list(monthRef.items()):
            dateStr = dateStr.replace(key, value)

        # remove empty time designations
        dateStr = dateStr.replace(":00", "")

        return dateStr

    # -----------------------------------------------------------------------||--
    # common form templates

    def formSelect(self, optionPairs=None, postBreaks=0):
        if optionPairs == None:
            optionPairs = (("", "+"), ("http://www.algorithmic.net", "algorithmic.net"))
        name = "selector"
        msg = []

        msg.append(
            """<FORM NAME="menu">
 <SELECT NAME="%s" size="1" onChange="if (this.options[selectedIndex].value != '') location.href=this.options[selectedIndex].value" style="width: 110; font-size: 10px">
"""
            % ("links" + str(random.choice(list(range(0, 100)))))
        )
        for entry in optionPairs:
            url = entry[0]
            label = entry[1]
            if entry == optionPairs[0]:  # if first
                msg.append('<option value="%s" selected>%s</option>\n' % (url, label))
            else:
                msg.append('<option value="%s">%s</option>\n' % (url, label))
        msg.append(
            """
 </SELECT>
 </FORM>\n"""
        )

        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def formTextArea(self, rows=2, label="textMsg", width=160):
        msg = (
            '<textarea name="%s" rows="%s" wrap="physical" style="width: %s; font-size: 10px"></textarea>'
            % (label, rows, width)
        )  # attr: #cols=30
        return msg

    def formGraphicClearSubmit(self):
        return """
<input type="image" name="reset" value="reset" alt="reset" src="images/top3.gif"></input>
<input type="image" name="submit" value="submit" alt="submit" src="images/top3.gif"></input>
"""

    def formClearSubmit(self):
        return """<input value="clear" name="reset" type="reset" style="width: 60; font-size: 10px"> <input value="submit" name="submit" type="submit" style="width: 60; font-size: 10px">"""

    def formSubmit(self, label="Submit", name="submit"):
        return (
            """<input value="%s" name="%s" type="submit" style="width: 60; font-size: 10px">"""
            % (label, name)
        )

    def formRadioButton(self, group, value, label, style="plain"):
        label = self.pText(label, "plain", 0)
        msg = '<input TYPE="radio" NAME="%s" VALUE="%s">%s</input>' % (
            group,
            value,
            label,
        )
        return msg

    # -----------------------------------------------------------------------||--
    def getDateString(self, postBreaks=1, style=None):
        timeStr = time.asctime(time.localtime())
        msg = []
        if style == "formal":
            msg.append("Last updated %s." % timeStr)
        else:
            msg.append("last updated %s" % timeStr)
        for i in range(0, postBreaks):
            msg.append(self.BR)
        msg.append("\n")
        return "".join(msg)

    def imageTest(self, name):
        """tests a file name to see if it is an image"""
        if (
            name[-4:] == ".jpg"
            or name[-4:] == ".gif"
            or name[-4:] == ".png"
            or name[-5:] == ".jpeg"
        ):
            return 1
        else:
            return 0

    def calcDownloadTime(self, fileSize):
        "uses /n, not br's"
        unit = fileSize[-3:]
        unit = unit.lower()
        unit = unit.strip()  # remove white space

        size = fileSize[:-3]
        size = float(size)

        # convert mb to kb
        if unit == "mb":
            size = size * 1024.0
        size = size * 1000.0  # convert to bytes
        size = size * 8  # convert to bits, 1 byte = 8 bits
        # print 'size in bits %s' % size

        timeDict = {
            "56 kbs": [56000, 0, ""],
            # '128 kbs' : [128000, 0, ''],
            "512 kbs": [512000, 0, ""],
        }
        for key in list(timeDict.keys()):
            entry = timeDict[key]
            speed = entry[0]  # first is speed
            time = size / speed
            timeSec = int(round(time))  # round((time / 60.0), 1)
            timeDict[key][1] = timeSec  # second is time
            # make string
            if timeSec < 60:
                msg = "%s seconds" % timeSec
            elif timeSec < 3600:  # less than an hour in s
                msg = "%s minutes" % int(round((timeSec / 60.0), 0))
            else:
                msg = "%s hours" % round((timeSec / 3600.0), 1)
            timeDict[key][2] = "".join(msg)  # third is str

        headMsg = "estimated download time"
        msg = []
        msg.append(self.pText(headMsg, "plain", 0))
        msg.append("\n")
        ordKeys = ("56 kbs", "512 kbs")
        for key in ordKeys:
            msg.append("%s: %s\n" % (key, timeDict[key][2]))
        msg.append("\n")
        return "".join(msg)

    def pls(self, htmlPath, ipAddress, port, mountPoint, title):
        """generates a .pls file for streaming radio"""
        plsText = """[playlist]
numberofentries=1
File1=http://%s:%s/%s
Title1=%s
Length1=-1
Version=2

""" % (
            ipAddress,
            port,
            mountPoint,
            title,
        )

        f = open(htmlPath, "w")
        f.write(plsText)
        f.close()

    def formatFreeSoundCite(
        self, audioRef, strProject="This project", titleLinkSwitch="name", preBreaks=0
    ):
        """given a list of audio files, create a citation with links to the
        freesoudn project"""

        b = []
        for x in range(preBreaks):
            b.append(self.BR)
        b.append(
            """%s employs processed (creatively transformed) sounds drawn from %s. These sounds are used under the terms of the %s license, where the following links serve as attribution for the original source sounds."""
            % (
                strProject,
                self.linkString(
                    "http://freesound.iua.upf.edu", "The Freesound Project", 0
                ),
                self.linkString(
                    "http://creativecommons.org/licenses/sampling+/1.0",
                    "Creative Commons Sampling Plus 1.0",
                    0,
                ),
            )
        )

        b.append(self.BR * 2)
        for audioDict in audioRef:
            if titleLinkSwitch == "name":
                if "title" in list(audioDict.keys()):
                    titleLink = audioDict["title"]
                else:
                    titleLink = "Audio File Information"
            else:  # code
                titleLink = audioDict["url"].split("id=")[-1]  # code as string

            l = self.linkString(audioDict["url"], titleLink, 0)
            b.append(l)
            if audioDict != audioRef[-1]:  # if not last
                b.append(", ")

        return "".join(b)

    # -----------------------------------------------------------------------||--
    def htaccess(self, htmlPath, lines=None):
        """writes an htaaccess file, appends lines as needed
        lines is a list of strings to add to file
        note: must add mime types here"""
        msg = []
        msg.append(
            """
ErrorDocument 400 /400.html 
ErrorDocument 401 /401.html 
ErrorDocument 403 /403.html
ErrorDocument 404 /404.html 
ErrorDocument 500 /500.html 
AddType audio/x-m4a m4a
AddType video/x-m4v m4v
"""
        )
        if lines != None:
            for data in lines:
                msg.append("%s\n" % data)

        f = open(htmlPath, "w")
        f.writelines(msg)
        f.close()

    # this method will be overwrtten in subclass
    def basicPage(self, htmlPath, bodyText, pageTitle):
        "if no html path (None) prints page to stdout"

        if self.headOpenClose == None:  # need to gen header
            self.headInit(pageTitle)  # may have been generated separately
        msg = []
        msg.append(self.htmlOpen)
        msg.append(self.headOpenClose)
        msg.append(self.bodyOpen)
        msg.append(self.linkName("top"))

        self.tableInit("100%", 1, None, 1, None, "center")
        msg.append(self.tableOpen)
        msg.append(self.trOpen)
        msg.append(self.tdOpen)

        # main table
        self.tableInit(self.tableW, 1)
        msg.append(self.tableOpen)
        msg.append(self.trOpen)
        msg.append(self.tdOpen)

        msg.append(self.pOpen)
        msg.append(bodyText)
        msg.append(self.pClose)

        msg.append(self.tdClose)
        msg.append(self.trClose)
        msg.append(self.tableClose)
        # end main table

        msg.append(self.tdClose)
        msg.append(self.trClose)
        msg.append(self.tableClose)

        msg.append(self.bodyClose)
        msg.append(self.htmlClose)

        if htmlPath == None:  ## this should be printed
            print("".join(msg))
        else:
            f = open(htmlPath, "w")
            f.writelines(msg)
            f.close()

    # this method will be overwrtten
    def writeRefreshPage(self, htmlPath, dst):
        "if no html path (None) prints page to stdout"
        msg = self.refreshPage(dst)  # gets a tring
        if htmlPath == None:  ## this should be printed
            print("".join(msg))
        else:
            f = open(htmlPath, "w")
            f.write(msg)
            f.close()

    def writeFramePage(self, htmlPath, sizeList=None, pathList=None, nameList=None):
        "if no html path (None) prints page to stdout"
        msg = self.framePage(sizeList, pathList, nameList)  # use default
        if htmlPath == None:  ## this should be printed
            print("".join(msg))
        else:
            f = open(htmlPath, "w")
            f.write(msg)
            f.close()


# -----------------------------------------------------------------||||||||||||--
# various html/online client functions
def getWeather(displayFmt="print"):
    """display can be print or str"""
    import urllib.request, urllib.parse, urllib.error  # Library for retrieving files using a URL.
    import re  # Library for finding patterns in text.

    locDict = {
        "ams": "http://weather.noaa.gov/weather/current/EHAM.html",
        "nyc": "http://weather.noaa.gov/weather/current/KNYC.html",
    }

    # The NOAA web page, showing current conditions in New York.
    url = "http://weather.noaa.gov/weather/current/KNYC.html"
    # Open and read the web page.
    MAX_PAGE_LEN = 20000
    msg = []
    keys = list(locDict.keys())
    keys.sort()
    for locStr in keys:
        url = locDict[locStr]
        try:
            webpage = urllib.request.urlopen(url).read(MAX_PAGE_LEN)
        # An I/O error occurred; print the error message and exit.
        except IOError as e:
            msg.append("I/O error (%s): " % locStr, e.strerror)
            webpage = None
        # Pattern which matches text like '66.9 F'. The last
        # argument ('re.S') is a flag, which effectively causes
        # newlines to be treated as ordinary characters.

        if webpage != None:
            matchF = re.search(r"(-?\d+(?:\.\d+)?) F", webpage, re.S)
            matchC = re.search(r"(-?\d+(?:\.\d+)?) C", webpage, re.S)
            msg.append(
                "%s temperature: %s (f) %s (c)\n"
                % (locStr, matchF.group(1).ljust(4), matchC.group(1).ljust(4))
            )
    if displayFmt == "print":
        print("".join(msg))
    else:
        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--
# borrowed from
# http://c2.com/cgi/wiki?WebLinkListExampleInPython


class LinkParser(HTMLParser):

    def reset(self):
        HTMLParser.reset(self)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        href = [v for k, v in attrs if k.lower() == "href"]
        if href:
            self.hrefs.append(["", href[0]])
            self.hrefOpen = 1
        else:
            self.hrefOpen = 0

    def handle_data(self, data):
        if self.hrefOpen:
            self.hrefs[-1][0] = data  # add description infront
            self.hrefOpen = 0


def getLinks(url):
    import urllib.request, urllib.parse, urllib.error

    parser = LinkParser()
    try:
        parser.feed(urllib.request.urlopen(url).read())
    except Exception as e:
        print("%s: %s\n" % (e, url))
        return
    parser.close()
    if not parser.hrefs:
        return None
    return parser.hrefs
