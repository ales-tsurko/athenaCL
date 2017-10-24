#-----------------------------------------------------------------||||||||||||--
# Name:          typeset.py
# Purpose:       cross platform text display tools.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import textwrap
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import language
lang = language.LangObj()

# this module is higher than drawer, lower than dialog
# like drawer, but imports langauge

_MOD = 'typeset.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)




#-----------------------------------------------------------------||||||||||||--
# common user interface string conversions, both for cli and ui args
# uses language.py, and this cannot be in drawer
def convertBoolCancel(usrData):
    """converts arg strings: on, off, or cancel
    or numbers 0, 1
    get strings from language; check english for preferences

    >>> convertBoolCancel('y')
    1
    >>> convertBoolCancel('no')
    0
    >>> convertBoolCancel(-1)
    -1
    """
    if drawer.isNum(usrData):
        usrStr = str(int(round(usrData)))
    else:
        usrStr = drawer.strScrub(usrData, 'L')
    if usrStr == '':
        return None

    # off
    if (usrStr in ['0', lang.OFF.lower(), lang.NO.lower(), lang.FALSE.lower()] or
            usrStr[0] == lang.NO[0].lower()):
        return 0
    if len(usrStr) >= len(lang.OFF): 
        if usrStr[-len(lang.OFF):] == lang.OFF.lower():
            return 0
    if len(usrStr) >= 3: # check literal english
        if usrStr[-3:] == 'off':
            return 0

    # on
    if (usrStr in ['1', lang.ON.lower(), lang.YES.lower(), lang.TRUE.lower()] or 
            usrStr[0] == lang.YES[0].lower()):
        return 1
    if len(usrStr) >= len(lang.ON):
        if usrStr[-len(lang.ON):] == lang.ON.lower():
            return 1
    if len(usrStr) >= 2: # check literal english
        if usrStr[-2:] == 'on':
            return 1

    # cancel
    if (usrStr in ['-1', lang.CANCEL.lower(), lang.BREAK.lower()] or 
            usrStr[0] == lang.CANCEL[0].lower()):
        return -1

    # if no match return None
    return None

def convertBool(usrData):
    """converts arg strings: on, off
    cancel is not accepted

    >>> convertBool('y')
    1
    """
    val = convertBoolCancel(usrData)
    if val == -1: # if cancel is determined
        return None # report as nothing
    else:
        return val

def boolAsStr(controlData, style=None):
    """return control data int as a ui string
    
    >>> boolAsStr(1)
    'on'
    >>> boolAsStr(0)
    'off'
    """
    controlData = convertBoolCancel(controlData)
    if style == None:
        if controlData == 0:
            return lang.OFF
        elif controlData == 1:
            return lang.ON
        elif controlData == -1:
            return lang.CANCEL


#-----------------------------------------------------------------||||||||||||--
# any data to str: here b/c it refs bool functions

def sigDigMeasure(num):
    """for a number, suggest a quantity of significant digits

    >>> sigDigMeasure(3.2345)
    2
    """
    if drawer.isInt(num): return 0
    num = float(num)
    junk, floatPart = divmod((num), 1) # float will split into int, dec
    if floatPart == 0:
        sigDig = 0
    elif floatPart < .0000001: 
        sigDig = 8
    elif floatPart < .000001: 
        sigDig = 7
    elif floatPart < .00001: 
        sigDig = 6
    elif floatPart < .0001: 
        sigDig = 5
    elif floatPart < .001: 
        sigDig = 4
    elif floatPart < .01: 
        sigDig = 3
    else: # this sets a minimum value for all floats
        sigDig = 2
    return sigDig

# utilty functions used below
def _maxSigDig(numA, numB):
    """compare two numbers; find one with most sig dig"""
    a = sigDigMeasure(numA)
    b = sigDigMeasure(numB)
    if a >= b: return a
    else: return b

def _maxStrLen(strA, strB):
    a = len(strA)
    b = len(strB)
    if a >= b: return a
    else: return b

def anyDataToStr(usrData, sigDig=None, seqBrace='tuple'):
    """convert any data to a proper string, taking type into account
    lists are recursive examined with the same function
    note: this will convert a list [] into a tuple representation
    depending on optional arg
    will automatically remove space between comma-separated lists

    >>> anyDataToStr('test')
    'test'
    >>> anyDataToStr([3, 'mixed', [3,4,5]])
    '(3,mixed,(3,4,5))'
    >>> anyDataToStr([2.35, ('a', (234, 34))])
    '(2.35,(a,(234,34)))'

    """
    if drawer.isStr(usrData):
        return usrData
    elif drawer.isInt(usrData):
        return '%i' % usrData
    elif drawer.isFloat(usrData):
        if sigDig != None: # force a certain length
            return '%s' % str(round(usrData, sigDig))
        else: # adaptive by size:
            sigDig = sigDigMeasure(usrData)
            return '%s' % str(round(usrData, sigDig))
    elif drawer.isBool(usrData): # does not work, evaluates as string?
        return boolAsStr(usrData)        
    elif usrData == None:   
        return 'none'
    elif drawer.isList(usrData):
        newData = []
        for q in usrData: # recursively apply to each element in list
            newData.append(anyDataToStr(q, sigDig, seqBrace))
        if seqBrace == 'tuple':
            return '(%s)' % ','.join(newData)
        elif seqBrace == 'list':
            return '[%s]' % ','.join(newData)
    else:
        return repr(usrData)

def timeRangeAsStr(tRange, format=''):
    """provide the display of a time range;

    >>> timeRangeAsStr([3,2])
    '3.0--2.0'
    >>> timeRangeAsStr([8, 2])
    '8.0--2.0'
    """
    # allow none as tRange
    if tRange == None: # not known
        return '?--?'
    tStart, tEnd = tRange
    # always make time values into floats
    sigDig = _maxSigDig(tStart, tEnd)
    startStr = '%s' % anyDataToStr(float(tStart), sigDig)
    endStr = '%s' % anyDataToStr(float(tEnd), sigDig)
    if format == 'argsOnly': # used ot 'data' but no longer used
        return '%s, %s' % (startStr, endStr)
    strLen = _maxStrLen(startStr, endStr)
    startStr = startStr.rjust(strLen)
    endStr = endStr.rjust(strLen)
    startStr = startStr.replace(' ','0')
    endStr = endStr.replace(' ','0')
    return '%s--%s' % (startStr, endStr)


#-----------------------------------------------------------------||||||||||||--
# used by both basePmtr and baseTexture

def descriptionAsStr(docStr, delimit='\n', argStr=None, demoStr=None):
    """format a descriptions string; add args if available

    >>> descriptionAsStr('this is a test')
    'Description: This is a test...'
    """
    msg = []
    msg.append('Description: ')
    msg.append('%s%s' % (docStr[0].upper(), docStr[1:]))
    msg.append(delimit)
    if argStr != None:
        msg.append('Arguments: ')
        msg.append(argStr)
        msg.append(delimit)
    if demoStr != None:
        msg.append('Sample Arguments: ')
        msg.append(demoStr)
    return ''.join(msg)

#-----------------------------------------------------------------||||||||||||--

def _lastReturnCheck(srcStr, dstStr):
    """check srcStr, dstStr and make sure same number of return 
    carriages at the end
    """
    # special cases
    if srcStr == '' and dstStr == '':
        return dstStr # dont do anything
    elif srcStr == '' and dstStr == '\n':
        return '\n' # keep if dst string is only a return
    elif srcStr == '\n' and dstStr == '':
        return '\n'
        
    # common operations
    if srcStr[-1] == '\n' and dstStr[-1] != '\n':
        dstStr = dstStr + '\n'
    elif srcStr[-1] != '\n' and dstStr[-1] == '\n':
        dstStr = dstStr[:-1]
    else: pass # no change
    return dstStr

def _softWrap(msg, charW, indentW):
    """slick word based line wrapping, leveraging textwrap module"""
    if indentW > 0:
        kwargs = {'replace_whitespace': 0,
                     'break_long_words' : 1,
                     'subsequent_indent' : (' ' * abs(indentW)),}
    elif indentW < 0: # neg does first line
        kwargs = {'replace_whitespace': 0,
                     'break_long_words' : 1,
                     'initial_indent': (' ' * abs(indentW)),}
    else: # 0
        kwargs = {'replace_whitespace': 0,
                     'break_long_words' : 1}
    lines = textwrap.wrap(msg, charW, **kwargs)
    return lines

def _hardWrap(line, charW, indentW):
    """primitive line wrapping with forced breaks"""
    wrapLines = []
    lineCount = 0
    exit = 0
    while exit != 1:
        if line.strip() == '': break # all space left, exit
        elif len(line) <= (charW - indentW):
            thisPortion = line
            exit = 1
        else:
            if lineCount == 0 or indentW == 0: # first line normal
                cutPos = charW
            else: # indenting line other than the first
                cutPos = charW - indentW
            thisPortion = line[:cutPos]
            line = line[cutPos:]
        if lineCount != 0 and indentW > 0:  # indent if W given
            thisPortion = (indentW * ' ') + thisPortion
        # append to stored list
        wrapLines.append(thisPortion)
        lineCount = lineCount + 1
    return wrapLines

def _singleLineWrap(line, charW, indentW=0, wrapType='line'):
    """wrap a line of text and return a list of lines; add white space indent
    wrap type can be line or bundle
    """
    if len(line) > charW:
        if indentW > 0: # subsequent lines are indented
            if charW <= indentW:
                indentW = 0 # force remove indent if too small
        if wrapType == 'line': 
            wrapLines = _softWrap(line, charW, indentW)
        elif wrapType == 'bundle':
            wrapLines = _hardWrap(line, charW, indentW)
    else: # no wrap necessary
        wrapLines = []
        wrapLines.append(line)
    return wrapLines


def _bundleLines(charW, indentW, bundledLines):
    """takes a list of lists, and bundles them
    expects lines to be hard warped
    this allowes columns to be mainted after wrapping
    """
    newBundles = []
    bundleNo = len(bundledLines)
    lineNo = 0
    for bundle in bundledLines: # each bundle is a list of lines
        if len(bundle) >= lineNo:
            lineNo = len(bundle) # get max lines

    for lineCount in range(0, lineNo):
        emptyLines = []
        for bundleCount in range(0, bundleNo):
            emptyLines.append(0) # palce holder
        # add extra space for divider, except when last line
        if bundleNo > 1 and lineCount != (lineNo-1): 
            emptyLines.append(0)
        newBundles.append(emptyLines)

    for lineCount in range(0, lineNo):
        for bundleCount in range(0, bundleNo):
            try:
                data = bundledLines[bundleCount][lineCount]
            except IndexError:
                data = ''
            newBundles[lineCount][bundleCount] = data
            # if last, addd divider, except very last group
            # used to be > 1 here, buts caused error on two line bundles
            if (bundleCount >= 1 and bundleCount == (bundleNo-1) and
                lineCount != (lineNo-1) ):
                if indentW == 0:
                    data = charW * lang.DIVIDER
                else:
                    data = (indentW * ' ') + ((charW-indentW) * lang.DIVIDER)
                newBundles[lineCount][bundleCount+1] = data
    return newBundles


def wrapText(msg, charW=40, indentW=0, wrapType='line'):
    """convert line breaks into a list
    indent: if pos, applied to all lines except the first
            if neg, applied only to first line
    wrap type 'line' wraps each line
    wrapType 'bundle' wraps all lines as a single unit
        reads actual line breaks and groups all lines as whole
        not repeating next line until all lines have been shown
        usefill when presenting a long line of data that is broken
        into columns
    returns a string, not a list of strings

    """
    strIndex = 0
    startPosition = 0
    if msg == None: return None
    # find natural line breaks and separate into lines
    # do not remove any white space or any adjustments
    entryLines = msg.split('\n')
    if entryLines[-1] == '':
        entryLines = entryLines[:-1]

    # bundle lines into a list
    bundledLines = []
    bundledMaps  = []
    for line in entryLines:
        wrapLines = _singleLineWrap(line, charW, indentW, wrapType)
        bundledLines.append(wrapLines)
        #bundledMaps.append(lineMap)

    # add list lines to string
    if wrapType == 'line':
        pass
    elif wrapType == 'bundle': #print parallel info
        bundledLines = _bundleLines(charW, indentW, bundledLines)

    # make the new string
    newMsg = []
    for bundle in bundledLines:
        for line in bundle:
            if not drawer.isStr(line):
                pass # case where it is a 0, as appended    in bundleLines
            else:
                newMsg.append(line)
    # compare source to new string for last return
    newMsg = _lastReturnCheck(msg, '\n'.join(newMsg)) # check last \n
    return newMsg




#-----------------------------------------------------------------||||||||||||--
# general dispaly functions for athenaCL

def _scrubEntryLines(entryLines):
    """run over entry lines and make sure each sub list is a list and
    not a tuple; return None if empty"""
    entryLines = list(entryLines) # make sure its alist
    i = 0
    empty = 0
    for line in entryLines:
        if drawer.isList(line):
            entryLines[i] = list(line)
            if len(entryLines[i]) == 0:
                empty = empty + 1
        # maybe do other conversions here too
        i = i + 1
    if empty == i: # if all lines are empty
        return None
    return entryLines

def formatVariCol(headerKey, entryLines, minWidthList, bufList=[],
                            justList=[], termObj=None, wrapMode='none', 
                            wrapType='line', minBufferW=1, ):
    """takes a list of entries and creates parallel widths for each line
    takes a list of listed entries, a list of minWidths, a list of 
    justifications.
    if, after analysis, a col width needs to be expanded, it is
    headerKey is a list of keys as a header
    entryLines is a list of a list of things to be printed
    minWidhtList is a list of minimum widths, without buffering
    justList is justifications, l, r, c
    bufList is boolean for wether a the buffer should be added or not
    """
    # check for lists
    entryLines = _scrubEntryLines(entryLines)
    if entryLines == None:
        return "no data to format (dialog.py)."
    minWidthList = list(minWidthList)
    bufList = list(bufList)
    justList = list(justList)

    # get width
    if termObj == None:
        charWidth = 72
    else:
        h, charWidth = termObj.size()
    # convert all entries to strings
    noColumns = 0

    lineCount = 0
    for line in entryLines:
        colCount = 0
        for entry in line:
            if not drawer.isStr(entry): # not a string
                entry = str(entry)
                entry = entry.strip() # removie outer white space
                entry = entry.replace(' ','') # remove spaces
            entryLines[lineCount][colCount] = entry
            colCount = colCount + 1
        if colCount >= noColumns:
            noColumns = colCount 
        lineCount = lineCount + 1
    #find min width for each column based on entry size
    fitColWidths = []
    for col in range(0,noColumns):
        fitColWidths.append(0)
        try:
            a = minWidthList[col]
        except IndexError:
            minWidthList.append(0)
        try:
            a = justList[col]
        except IndexError:
            justList.append('l') # default
        try:
            a = bufList[col]
        except IndexError:
            bufList.append(1) # use default

    for line in entryLines:
        colCount = 0
        for entry in line:
            if len(entry) >= fitColWidths[colCount]:
                fitColWidths[colCount] = len(entry)
            colCount = colCount + 1
    # create lines
    finalColWidths = []
    msgBody = []
    lineCount = 0
    for line in entryLines:
        colCount = 0
        lineStr = []
        for entry in line:
            if fitColWidths[colCount] > minWidthList[colCount]:
                finalW = fitColWidths[colCount]
            else:
                finalW = minWidthList[colCount]
            if (bufList[colCount] != 0 and 
                    fitColWidths[colCount] >= minWidthList[colCount]): 
                    # add a bufer if found width is greater or equal to fit
                finalW = minBufferW + finalW
            finalColWidths.append(finalW)

            if justList[colCount].lower() == 'l':
                lineStr.append(entry.ljust(finalColWidths[colCount]))
            elif justList[colCount].lower() == 'r':
                lineStr.append(entry.rjust(finalColWidths[colCount]))
            elif justList[colCount].lower() == 'c':
                lineStr.append(entry.center(finalColWidths[colCount]))       
            colCount = colCount + 1
        if ''.join(lineStr).strip() == '': # draw a line        
            lineStr.append(charWidth * lang.DIVIDER)
        if lineCount < (len(entryLines) - 1): # addreturn
            lineStr.append('\n')
        else: # last one, no \n
            pass
        msgBody = msgBody + lineStr # add lists
        lineCount = lineCount + 1

    msgBody = ''.join(msgBody) # convert to string
    if wrapMode == 'none':
        pass
    elif wrapMode == 'normal':
        msgBody = wrapText(msgBody, charWidth, 0, wrapType)
    elif wrapMode == 'tab':
        msgBody = wrapText(msgBody, charWidth, lang.TABW, wrapType)
    elif wrapMode == 'lmargin':
        msgBody = wrapText(msgBody, charWidth, lang.LMARGINW, wrapType)
    elif wrapMode == 'oneColumn':
        indentWidth = finalColWidths[0]
        msgBody = wrapText(msgBody, charWidth, indentWidth, wrapType)
    elif wrapMode == 'twoColumn':
        indentWidth = finalColWidths[0]+finalColWidths[1]
        msgBody = wrapText(msgBody, charWidth, indentWidth, wrapType)
    elif wrapMode == 'threeColumn':
        indentWidth = finalColWidths[0]+finalColWidths[1]+finalColWidths[2]
        msgBody = wrapText(msgBody, charWidth, indentWidth, wrapType)
    elif wrapMode == 'fourColumn':
        indentWidth = (finalColWidths[0]+finalColWidths[1]+
                            finalColWidths[2]+finalColWidths[3])
        msgBody = wrapText(msgBody, charWidth, indentWidth, wrapType)
    # create header keys
    colCount = 0
    totW = 0
    headStr = []
    headStr.append('{')
    for head in headerKey:
        if colCount < (len(headerKey) - 1):
            if head != '':
                headStr.append(head + ',') # key divider
        else:
            headStr.append(head)
        colCount = colCount + 1
    headStr.append('}')
    headStr.append('\n') # + (lang.DIVIDER * totW) + '\n'
    if len(headerKey) != 0: # skip header if empty list
        headStr.append(msgBody)
        msgFinal = ''.join(headStr)
    else:
        msgFinal = msgBody
    return msgFinal


def formatEqCol(header, entries, minColWidth, charWidth=70, outLine=False):
    """takes a list and prints colums based on a minimum width
    two modes:
    outLine: prints each new line of a group indented
    off: prints normal columns

    >>> formatEqCol('test', ['a', 'b'], 10, charWidth=10)
    'test\\n..........\\na         \\nb         \\n'
    >>> formatEqCol('test', ['a', 'b'], 10, charWidth=10, outLine=True)
    'test\\n..........\\na         \\n          b         \\n'
    >>> formatEqCol('test', ['a'], 10, charWidth=10)
    'test\\n..........\\na         \\n'
    >>> formatEqCol('test', 'a', 10, charWidth=10)
    'test\\n..........\\na         \\n'
    >>> formatEqCol('test', '', 10, charWidth=10)
    'test\\n..........\\n\\n'
    >>> formatEqCol('', '', 10, charWidth=10)
    '\\n'
    """
    if header == '':
        ruler = ''
    else:
        ruler = lang.DIVIDER
    msg = []
    if header != '':
        msg.append(header + '\n')
    if ruler != '':
        msg.append((ruler * charWidth) + '\n')

    if minColWidth <= 0: # will cause div by zero error
        environment.printDebug('minColWidth set to zero; auto correcting') 
        minColWidth = 10 # a common default

    entryPerLine, junk = divmod(charWidth, minColWidth)
    if (entryPerLine * minColWidth) > charWidth:
        entryPerLine = entryPerLine - 1
    if entryPerLine <= 0:
        entryPerLine = 1 # has to be greater than 0
    # if not a pefect match, columns need extra padding
    if (entryPerLine * minColWidth) != charWidth:
        surplus = charWidth - (entryPerLine * minColWidth)
        distDiff = surplus / entryPerLine # want downward round
        minColWidth = minColWidth + distDiff
    col = entryPerLine
    for cmd in entries:
        cmd = cmd.strip()
        if col == 0:
            msg.append('\n')
            # outline mode indents all entry after first entry of each group
            if outLine: # only if special mode is desired
                if cmd != entries[0]: # if not the first
                    whiteSpace = ' ' * minColWidth
                    msg.append(whiteSpace)
                    col = (col+1) % entryPerLine # shift col but dont skip cmd
        addedSpace = int(minColWidth - len(cmd))
        whiteSpace = ' ' * addedSpace
        msg.append(cmd + whiteSpace)
        col = (col+1) % entryPerLine
    msg.append('\n')
    return ''.join(msg)


#-----------------------------------------------------------------||||||||||||--

def graphDuration(totalDur, start, end, charWidth=50, fullChar='_'):
    """produces a graph of an object in a field
    values are assumed to be seconds
    """
    pcentStart = float(start) / totalDur
    pcentEnd      = float(end) / totalDur
    emptyChar  = ' '
    str = []
    for counter in range(0, charWidth):
        pcentCurent = float(counter) / (charWidth-1)
        if pcentCurent >= pcentStart and pcentCurent <= pcentEnd:
            str.append(fullChar)
        else:
            str.append(emptyChar)
    return ''.join(str)


def graphNumber(min, max, value, charWidth=50, emptyChar='.', fullChar='+'):
    """produces a graph of an object in a field
    values can be ints or floats
    """
    if min > max:
        high = min
        low  = max
        rev  = 1 # reverse string at end
    else:
        high = max
        low  = min
        rev  = 0
    if value == None or drawer.isStr(value):
        value = low - 1 # off range

    distance      = high - low
    pcentValue = float((value-low)) / distance
    pcentInc      = 1.0 / charWidth
    litInc    = float(distance) / charWidth

    str = []
    pcentPosition    = 0.0
    literalPosition = low

    for counter in range(0, charWidth):
        if (pcentValue >= pcentPosition and 
            pcentValue < (pcentPosition + pcentInc)):
            str.append(fullChar)
        elif counter == (charWidth-1): # last register
            if pcentValue >= (1.0 - pcentInc) and pcentValue <= 1.0:
                #print pcentValue, pcentPosition
                str.append(fullChar)
            else:
                str.append(emptyChar)
        else:
            str.append(emptyChar)
        pcentPosition = pcentPosition + pcentInc
    if rev == 1:
        l = list(str)
        l.reverse()
        str = []
        for letter in l:
            str.append(letter)
    return ''.join(str)


def graphRuler(charWidth=50, divisions=9, emptyChar='.', fullChar='+'):
    """produces horizontal ruler as a string with spaced characters"""
    rulerStr = ' ' * charWidth
    pointList = []
    for i in range(0, divisions):
        str = graphNumber(0, (divisions-1), i, charWidth, emptyChar, fullChar)
        counter = 0
        for char in str:
            if str[counter] == fullChar:
                rulerStr = '%s%s%s' % (rulerStr[:counter], str[counter], 
                                              rulerStr[(counter+1):])
            counter = counter + 1
    counter = 0
    marks = 0
    for char in rulerStr:
        if char == fullChar:
            if (marks % 2) == 0:
                rulerStr = '%s|%s' % (rulerStr[:counter], rulerStr[(counter+1):])
            elif (marks % 2) == 1:
                rulerStr = '%s.%s' % (rulerStr[:counter], rulerStr[(counter+1):])
            marks = marks + 1
        counter = counter + 1
    return rulerStr


def graphLabeledRuler(llabel, rlabel, charWidth=50, divisions=5, 
                             emptyChar='.', fullChar='+'):
    """produces horizontal ruler with labeled endopints"""
    rulerStr = graphRuler(charWidth, divisions, emptyChar, fullChar)
    startLeftReplace = 0
    endLeftReplace = len(llabel) + 0
    endRightReplace = len(rulerStr) - 0 # gets second to last
    startRightReplace = endRightReplace - len(rlabel)

    rulerStr = '%s%s%s' % (rulerStr[:startLeftReplace], llabel,
                          rulerStr[endLeftReplace:])
    rulerStr = '%s%s%s' % (rulerStr[:startRightReplace], rlabel, 
                                  rulerStr[endRightReplace:])
    return rulerStr



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testFormatEqCol(self):
        material = [['test'], ['a', 'b']]
        minColWidth = list(range(0, 20, 5))
        charWidth = list(range(0, 20, 5))

        for m in material:
            for mcw in minColWidth:
                for cw in charWidth:
                    post = formatEqCol('', m, mcw, cw) # could return zero div

#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)


