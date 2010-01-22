#-----------------------------------------------------------------||||||||||||--
# Name:          drawer.py
# Purpose:       provides simple functions shared in multiple places
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


import sys, os, string, types, random
import unittest, doctest

# primitive module: do not import any larger mods.

_MOD = 'drawer.py'
#-----------------------------------------------------------------||||||||||||--

def isList(usrData):
    """check if usr data is a list or tuple, return boolean
        
    >>> isList([])
    True
    >>> isList('')
    False
    """
    if (isinstance(usrData, types.ListType) or 
         isinstance(usrData, types.TupleType)):
        return True
    else:
        return False

def isNum(usrData):
    """check if usr data is a number (float or int), return boolean
    
    >>> isNum([])
    False
    >>> isNum(3.2)
    True
    >>> isNum(3)
    True
    """
    if (isinstance(usrData, types.FloatType) or 
         isinstance(usrData, types.IntType) or 
         isinstance(usrData, types.LongType)):
        return True
    else:
        return False

def isBool(usrData):
    """check if usr data is boolean, return boolean

    >>> isBool(True)
    True
    >>> isBool(0)
    False
    """
    if isinstance(usrData, types.BooleanType):
        return True
    else:
        return False

def isFloat(usrData):
    """check if usr data is a float, return boolean
    
    >>> isFloat(3.2)
    True
    >>> isFloat(3)
    False
    """
    if isinstance(usrData, types.FloatType):
        return True
    else:
        return False

def isInt(usrData):
    """check if usr data is an integer, return boolean
    will fail if integer is a long: types.LongType

    >>> isInt(3)
    True
    >>> isInt('3')
    False
    """
    if isinstance(usrData, types.IntType):
        return True
    else:
        return False

def isStr(usrData):
    """check if usr data is a string, return boolean

    >>> isStr('test')
    True
    >>> isStr(3.2)
    False
    """
    if isinstance(usrData, types.StringType):
        return True
    else:
        return False

def isDict(usrData):
    """check if usr data is a ldictionary, return boolean
    
    >>> isDict({})
    True
    >>> isDict('false')
    False
    """
    if isinstance(usrData, types.DictType):
        return True
    else:
        return False


#-----------------------------------------------------------------||||||||||||--
# higher level types

def isMod(usrData):
    """check if usr data is a module, return boolean

    >>> from athenaCL.libATH import markov
    >>> isMod(markov)
    True
    >>> isMod(True)
    False
    """
    if isinstance(usrData, types.ModuleType):
        return True
    else:
        return False

def isFunc(usrData):
    """check if usr data is a function, return boolean

    >>> def mock(): pass
    >>> isFunc(mock)
    True
    >>> isFunc(False)
    False
    """
    if isinstance(usrData, types.FunctionType):
        return True
    else:
        return False

def isCharNum(usrData):
    """determine if a character array does contains a number as a string
    if not should be interpreted as a string, otherwise, it is a float or other
    string symbol arrangement; will not remove list delimiters

    >>> isCharNum('adsf')
    False
    >>> isCharNum('34')
    True
    >>> isCharNum('34.234')
    True
    """
    match = len(usrData)
    count = 0
    for char in usrData: # cannot have a comma here
        if char.isdigit() or char in ['.', '-', ' ', '+']:
            count = count + 1
    if count == match:
        return True
    else: 
        return False
    
#-----------------------------------------------------------------||||||||||||--
def typeAsStr(typeStr):
    """convert types strings to user friendly type names

    >>> typeAsStr('float')
    'floating point number'
    """
    if typeStr == 'list':
        return 'list'
    elif typeStr == 'num':
        return 'number'
    elif typeStr == 'bool':
        return 'yes or no'
    elif typeStr == 'float':
        return 'floating point number'
    elif typeStr == 'int':
        return 'integer number'
    elif typeStr == 'str':
        return 'string'
    elif typeStr == 'dict':
        return 'dictionary'
    else:
        return 'unknown (%s)' % typeStr
    
# may want to use this in argTools.strongType ?

def isType(usrData, type):
    """
    >>> isType(True, 'bool')
    True
    """
    if type == 'list':
        return isList(usrData)
    elif type == 'num':
        return isNum(usrData)
    elif type == 'bool':
        return isBool(usrData)
    elif type == 'float':
        return isFloat(usrData)
    elif type == 'int':
        return isInt(usrData)
    elif type == 'str':
        return isStr(usrData)
    elif type == 'dict':
        return isDict(usrData)
    else:
        raise ValueError, 'bad data type given'

#-----------------------------------------------------------------||||||||||||--
# list searching and confirmation

def inList(value, valueList, caseSens='case'):
    """checks to see if value (string or number) in list
    if not, return None
    caseSense optional

    >>> inList(3, [3,4,5])
    3
    >>> inList('f', [3,'F',4,5]) == None
    True
    >>> inList('f', [3,'F',4,5], 'noCase')
    'F'
    """
    if value == None:
        return None
    if caseSens == 'case':
        if value in valueList:
            return value
        for choice in valueList: # try partial matches
            if isStr(choice) and isStr(value):
                if choice.startswith(value):
                    return choice
    elif caseSens == 'noCase':
        for choice in valueList:
            if isStr(choice) and isStr(value):
                if value.lower() == choice.lower():
                    return choice
        # try to match partial selections
        for choice in valueList:
            if isStr(choice) and isStr(value):
                if choice.lower().startswith(value):
                    return choice
    else:
        return None

def inListSearch(usrStr, choiceList):
    """given a list of things, search with usrString and produce
    a list of possible matches. if no match, return None

    >>> inListSearch('pi', ['piv', 'pils'])
    ['piv', 'pils']

    """
    usrStr = usrStr.strip()
    usrStr = usrStr.lower()
    if usrStr == '': return None # return None if no match
    filterList = []
    exactList = []
    for topic in choiceList:
        topicLower = topic.lower()
        if topicLower == usrStr:
            exactList.append(topic)
        if topicLower.find(usrStr) >= 0:
            filterList.append(topic)
    if filterList == []: return None
    elif exactList != []: return exactList # prioritize exact matches
    else: return filterList

    
#-----------------------------------------------------------------||||||||||||--
# quaries of system status, utilities

def isCarbon():
    "determins which mac tools to use; carbon only avail post 2.3"
    try:
        import Carbon.File
        carbon = 1
    except ImportError:
        try:
            import macfs
            carbon = 0 # macfs
        except ImportError:
            carbon = -1 # no macfs
    return carbon

def isDarwin():
    "test to see if this unix is darwin not"
    uname = os.uname()[0].lower()
    if uname.startswith('darwin'): return 1
    else: return 0 

def isIdle():
    """discover if idle is active 
    normal: '<type 'file'>'
    idle: 'idlelib.rpc.rpcproxy'
    """
    stdinClass = str(sys.stdin.__class__).lower()
    if stdinClass.find('idle') >= 0: return 1
    else: return 0

def isPy24Better():
    """is python version 2.4 or better"""
    if sys.version[:3] in ['1.5', '1.6', '2.0', '2.1', '2.2', '2.3']: return 0
    else: return 1
        
def isSudo():
    """test to see if sudo availabe on unix platforms
    this should be altered to use the command module"""
    if os.name != 'posix': return 0 # no sudo
    import commands
    stat, str = commands.getstatusoutput('sudo -V')
    if stat == 0: # success if it returns zero
        return 1
    else: return 0
        
def imageFormats():
    """finds available guis and produces a list of options
    used by imageTools as well as dialog.py
    same conditional import done w/n imageTools.py
    this function takes time, as tk window creation may take some time 
    """
    available = ['text', 'eps'] # always available
    try:
        import Image, ImageDraw, ImageFont #ImageFilter, ImageTk
        PIL = 1
    except ImportError:
        PIL = 0
    try:
        import Tkinter
        TK = 1
    except ImportError:
        TK = 0  
    if TK:
        try: # tkinter already imported; check creation, as may still fail
            tkTemp = Tkinter.Tk()
            tkTemp.withdraw()
            tkTemp.destroy()
            del tkTemp
            available.append('tk')
        except: pass
    if PIL:
        available.append('png')
        available.append('jpg') # uses pil to write the file
    return available


#-----------------------------------------------------------------||||||||||||--
# evaluating and filtering paths to applications    
    
def isApp(fp):
    """determine, in a platform specific manner, if a file or directory
    is an application or not; must provide absolute path"""
    if fp == None: return 0
    if not os.path.exists(fp): return 0

#     if os.name == 'mac': # cant be a directory
#         if os.path.isdir(fp): return 0
#         else: return 1
    if os.name == 'posix':
        if isDarwin():
            if fp.endswith('.app'): return 1
        # otherwise, see if it is an executable: how?
        if os.path.isdir(fp): return 0
        else: return 1
    else: # all win apps must end in exe
        if fp.endswith('.exe'): return 1 # win or other
        else: return 0

def appPathFilter(fp):
    """determine, in a platform specific manner, if a path to an application
    has been given, but the path is not complete: it may be missing a .app or
    .exe extension"""
    if fp == None or fp == '': return fp
#     if os.name == 'mac': 
#         pass # nothing to do
    if os.name == 'posix':
        if isDarwin():
            fpMod = fp + '.app'
            if not os.path.exists(fp) and os.path.exists(fpMod):
                return fpMod
    else: # all win apps must end in exe
        fpMod = fp + '.exe'
        if not os.path.exists(fp) and os.path.exists(fpMod):
            return fpMod
    # return unchanged
    return fp
    
  

#-----------------------------------------------------------------||||||||||||--
# functions for dealing w/ pesky strings
# cleaning and converting

def strToNum(usrStr, numType='num', min=None, max=None, force=0):
    """convert a raw user string to number; return None on error
    min and max are inclusive; returns None if exceeds bounds
    if force, resolve values tt exceed min/max to min/max

    >>> strToNum('345')
    345
    >>> strToNum('345.234')
    345.23...
    """
    if usrStr == None: return None
    try:
        if numType == 'float':
            numEval = float(usrStr)
        elif numType == 'int':
            numEval = int(usrStr)
        elif numType == 'num': # evaluate, could be either float or int
            numEval = eval(usrStr)
            # note that reserved strings will be evaluated:
            # 'open' evaluates to a file object
            if not isNum(numEval):
                raise ValueError, 'bad number format: %s' % numType     
        else: # should not happen
            raise ValueError, 'bad number format: %s' % numType
    except (SyntaxError, NameError, ValueError, TypeError, ZeroDivisionError):
        return None
    if min != None:  # check for min and max
        if numEval < min:
            if force: return min
            else: return None
    if max != None:
        if numEval > max:
            if force: return max
            else: return None
    return numEval


def intToStr(num, zeroBuff=None):
    """for typesetting a number w/ zero spacing
    
    >>> intToStr(3)
    '3'
    >>> intToStr(3, 3)
    '003'
    """
    if zeroBuff == None:
        return str(num)
    else:
        msg = str(num)
        if zeroBuff > len(msg):
            for x in range(zeroBuff-len(msg)):
                msg = '0' + msg
        return msg
        

def intHalf(num):
    """take a number, split into two parts; if number is odd
    provide proper sizes, with right having more

    >>> intHalf(3)
    (1, 2)
    >>> intHalf(4)
    (2, 2)
    """
    if num % 2 == 0: # if event
        return num/2, num/2
    else: # odd 
        return num/2, (num/2)+1

def strScrub(usrStr, case=None, rm=[]):
    """common string cleaning necessities
    rm is a list of characters to remove

    >>> strScrub('    sdfwer       \t\t')
    'sdfwer'
    """
    if not isStr(usrStr): # convert to string if not already
        usrStr = str(usrStr)
    if case != None:
        case = case.lower()
        if case.find('u') >= 0: # upper case
            usrStr = usrStr.upper()
        elif case.find('l') >= 0: # lower case
            usrStr = usrStr.lower()
        else:
            raise ValueError, 'bad case type given'
    usrStr = usrStr.strip()
    if rm != []:
        for char in rm:
            usrStr = usrStr.replace(char, '')
    return usrStr

def strStripAlpha(usrStr):            
    """use to remove alphas from a string

    note: this leaves whitespace

    >>> strStripAlpha('sdf234isdf345sg   234sdf4')
    '234345   2344'

    """
    if usrStr == '': return ''
    newStr = []
    for char in usrStr:
        if not char.isalpha():
            newStr.append(char)
    return ''.join(newStr)

def strExtractAlpha(usrStr, opt=[]):            
    """use to gather non-numbers from a string
    will return all alphas, alone, from a string
    opt: a list of additional chars that are accepted as alpha-like

    >>> strExtractAlpha('sfd234dfg09')
    'sfddfg'

    """
    if usrStr == '': return ''
    newStr = []
    for char in usrStr:
        if char.isalpha() or char in opt:
            newStr.append(char)
    return ''.join(newStr)

def strExtractNum(usrStr, optAccept=''):
    """extract numbers from a string in order
    optAccept is string of oher characters accepted

    >>> strExtractNum('sdf2349dfg3234')
    ('23493234', 'sdfdfg')
    """
    numbers = list(string.digits) + list(optAccept)
    usrStr = strScrub(usrStr)
    foundStr = []
    remainStr = []
    for char in usrStr:
        if char in numbers:
            foundStr.append(char)
        else:
            remainStr.append(char)
    # returns numbers, and then characeters
    return ''.join(foundStr), ''.join(remainStr)

def strCompactSpace(usrStr):
    """take a string of space-separated arguments
    remove all white space, tab, and returns, and replace any 
    span of white space with exactly one space, good for splitting

    >>> strCompactSpace('adsf     234 sdf 493  345   asdf')
    'adsf 234 sdf 493 345 asdf'
    """
    newStr = []
    count = 0
    usrStr = usrStr.strip() # remove lead and trail space
    for char in usrStr:
        if not char.isspace(): # if not white space
            if count != 0: # if some white space has been found, add one space
                newStr.append(' ')
            newStr.append(char)
            count = 0
        else: # white space
            count = count + 1
    return ''.join(newStr)

def strToPercent(usrStr, fmt=None):
    """convert a usrStr into a percentage
    auto determine if its a unit interval percent, or a 100 percent
    accepts strings like '.5, .9' or '40, 60'
    fromats can be 'unit' or 'macro'
    
    originally part of sc commands
    always return as unit-interval percent
    returns None on error
    if fmt== None, tries to auto determine if unit or macro percent
    if a percentage sign is given, it is always interpreted as macro

    >>> strToPercent(.5)
    0.5
    >>> strToPercent(40)
    0.40...
    >>> strToPercent('6.18%')
    0.061...
    """
    usrStr = strScrub(usrStr)
    if usrStr == None: return None
    if usrStr.find('%') >= 0:
        usrStr = usrStr.replace('%', '')
        fmt = 'macro'
    num = strToNum(usrStr, 'float', 0, 100)
    if num == None: return None
    # auto determin format if format is not given, or not already determined
    # one is assumed to be a unit value, not macro
    if fmt == None and num > 1:
        fmt = 'macro'
    if fmt == 'macro':
        num = num / 100.0
    return num

def strToList(usrStr, delimit=','):
    """force a string into a list of strings
    if commas are present, use to demarcate
    if not, add string as single element in a list
    can use variable delimiters: default is ,

    >>> strToList('this, is, a, test')
    ['this', ' is', ' a', ' test']
    """
    # replace delimit w/ commas (if not commas)
    usrStr = usrStr.replace(delimit, ',')
    # scrub only after replacing delimit
    usrStr = strScrub(usrStr)
    # split will add to a list, even if no commas present
    q = usrStr.split(',')
    # there may be empty strings in the list; not sure if they
    # should be removed
    return q

def strToListFlat(usrStr, case=None, delimit=','):
    """force a string into a list
    assume this is a flat level, and do not need inner () or []
    if commas are present, use to demarcate
    if not, add string as single element in a list
    can use variable delimiters: default is ,

    >>> strToListFlat('this, (is, a), test')
    ['this', ' is', ' a', ' test']

    """
    # replace delimit w/ commas (if not commas)
    usrStr = usrStr.replace(delimit, ',')
    # check for redundant delimitters, and nesting
    if usrStr.find(',,') >= 0:    # this will correct stupid mistakes
        usrStr = usrStr.replace(',,', ',')
    usrStr = usrStr.replace(')','')
    usrStr = usrStr.replace('(','')
    usrStr = usrStr.replace(']','')
    usrStr = usrStr.replace('[','')
    # scrub only after replacing delimit
    usrStr = strScrub(usrStr, case)
    # split will add to a list, even if no commas present
    q = usrStr.split(',')
    # there may be empty strings in the list; not sure if they
    # should be removed
    return q

def strToSequence(usrStr, dataLen=None, dataTypeList=None, delimit=','):
    """convert a comma-delimited string entry to a list of
    data; list shuold not contain embedded lists (for now)
    dataLen, if not None, ensures that data is of a specific length
    dataTypeList, if not None, ensures that data is of type in order
    returns None on error
    a single item will be returned in a list

    >>> strToSequence('3, 6, 3')
    [3, 6, 3]

    """
    # produce a list of string values
    usrList = strToList(usrStr, delimit)
    if usrList == []: # nothing here
        return None
    newList = []
    if dataLen != None:
        if len(usrList) != dataLen: return None
    for i in range(len(usrList)):
        try:
            data = eval(usrList[i])
        except (SyntaxError, NameError, ValueError, TypeError, ZeroDivisionError):
            return None
        if dataTypeList != None:
            # get type string modulo, so that they wrap if necessary
            typeStr = dataTypeList[i%len(dataTypeList)]
            if not isType(data, typeStr):
                return None
        newList.append(data)
    return newList

def pathScrub(usrStr):
    """standard utilities to clean file paths of debris
    will raise exception on error
    note: may want to use os.abspath to find abs paths"""
    if not isStr(usrStr):
        raise ValueError, 'non-string submitted as a path string: %r' % usrStr

    if os.name == 'posix':
        # expand user must be done before realpath on posix
        # causes a strange arrnagment otherwise
        usrStr = os.path.expanduser(usrStr)
        # NOTE: if given just a file name, this will assume append cwd
        # to a name; this can be very confusing
        # real path will raise error if getcwd fails
        if usrStr.find(os.sep) >= 0: # not the same as os.path.isabs
            try: usrStr = os.path.realpath(usrStr)
            except OSError: pass # make no changes
    else: # win or other
        pass
    # check for double terminating os.sep; was problem in macos 9
    doubleSep = os.sep + os.sep
    if usrStr[-len(doubleSep):] == doubleSep:
        usrStr = usrStr[:-len(doubleSep)]
        
    #normcase does not seem necessary, and my cause problems on windows
    #usrStr = os.path.normcase(usrStr)
    usrStr = os.path.normpath(usrStr)
    usrStr = os.path.expandvars(usrStr)
    return usrStr

def pathExists(usrData):
    """check if a path exists as a list or single entity
    if any one exists, return false"""
    if not isList(usrData):
        pathList = [usrData]
    else:
        pathList = usrData
    for path in pathList:
        if os.path.exists(path):
            return 1
    return 0
    
def getcwd():
    """get cwd, returning None on exceptions
    exceptions happen if the dir no longer exists"""
    try:
        path = os.getcwd()
    except OSError:
        path = None
    return path
    
def getud():
    """get a users directory; if cannot be found get cwd
    will be None if error cannot be avoided"""
    if os.name == 'mac': # macos 9
        return None
    elif os.name == 'posix':
        return os.path.expanduser('~') # get active users dir
    else: # win or other
        dir = None
        if 'USERPROFILE' in os.environ.keys(): # windows xp and others
            dir = os.environ['USERPROFILE'] #windows NT,2k,XP,etc
            if not os.path.isdir(dir):
                dir = None
        if dir == None: # expand user works on win xp
            dir = os.path.expanduser("~") 
            if not os.path.isdir(dir):
                dir = None
        return dir

def listToStr(set, space='rmSpace'):
    """converts a list/tuple to a string, removes space

    >>> listToStr([3,4,2.3])
    '(3,4,2.3)'
    """
    if isNum(set): # if a single number
        set = [set] # place in a list
#     try:
#         set = tuple(set) # gets paren, not bracket
#     except TypeError, e: # if an error, get more information 
#         raise TypeError, '%s: %s' % (e, repr(set))
    setRepr = []
    for part in set:
        setRepr.append(str(part))

    setRepr = '(%s)' % ','.join(setRepr)
    if space == 'rmSpace':
        setRepr = setRepr.replace(' ', '')
    return setRepr

def listToStrGrammar(items, finalSeparator=None): 
    """convert a list into a grammatical sentence, with a final 'and' or
    'or' at the end, add space, commas in between

    >>> listToStrGrammar(['red', 'green', 'blue'], 'and')
    'red, green, and blue'

    """
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        if finalSeparator != None:
            return '%s %s %s' % (items[0], finalSeparator, items[1])
        else:
            return ', '.join(items)
    else:
        msg = []
        for i in range(len(items)):
            length = len(items)
            if i < length - 2: # not second to last
                msg.append(items[i])
                msg.append(', ')
            elif i == length - 2: # second to last in list
                msg.append(items[i])
                if finalSeparator != None:
                    msg.append(', %s ' % finalSeparator)
                else:
                    msg.append(', ')
            elif i == length - 1: # last in list
                msg.append(items[i])
        return ''.join(msg)
                
def typeListAsStr(typeList, finalSeparator=None):
    """convert a list to string list, separated by commas
    optional finalSeparator adds a 'and' or 'or' before last element

    >>> typeListAsStr(['float', 'bool', 'int'], 'or')
    'floating point number, yes or no, or integer number'
    """
    items = []
    for typeStr in typeList:
        items.append('%s' % (typeAsStr(typeStr)))
    return listToStrGrammar(items, finalSeparator)
                

def listScrub(set, space='rmSpace', quote=None):
    """converts a list/tuple to string, removes space
    outer braces, and trailing commas, 
    can remove space: either rmSpace or None
    can remove quotes: either rmQuote or None

    >>> listScrub([3,4,5])
    '3,4,5'

    """
    if isNum(set): # if a single number
        set = [set] # place in a list
    if len(set) == 0: # if empty
        return 'none'
    setRepr = listToStr(set, space)
    if setRepr[0] == '(' and setRepr[-1] == ')':
        setRepr = setRepr[1:-1] # removes outer braces
    if setRepr[0] == '[' and setRepr[-1] == ']':
        setRepr = setRepr[1:-1] # removes outer braces
    if setRepr[-1] == ',':
        setRepr = setRepr[:-1]
    if quote != None:
        setRepr = setRepr.replace('"','')
        setRepr = setRepr.replace("'",'')
    return setRepr

def listInterleave(a, b, offset=0):
    """interleave two lists, optionally remove redundances

    >>> listInterleave([1,2,3], ['a', 'b', 'c'])
    [1, 'a', 2, 'b', 3, 'c']
    """
    post = []
    lastA = None
    lastB = None
    # offset takes a bit from first list
    for x in range(0, offset):
        post.append(a[x])         
    for x in range(0, len(b)):
        if not (offset + x) >= len(a): # index may exceed a b/c of offset
            post.append(a[offset+x])
        post.append(b[x])
    return post
    
def listSliceWrap(src, a, b, fmt='value'):
    """take a list and return a slice; if a and b exceed the range
    wrap from the each other side
    format is value, active, index, or pair
    active skips pairs with values > zero; may not return whole size
    this may be implemented elsewhere


    >>> listSliceWrap(['a','b'], 0, 6)
    ['a', 'b', 'a', 'b', 'a', 'b']
    >>> listSliceWrap(['a','b'], -1, 2)
    ['b', 'a', 'b']
    >>> listSliceWrap(['a','b','c'], -1, 2)
    ['c', 'a', 'b']
    >>> listSliceWrap(['a','b','c'], -3, 3)
    ['a', 'b', 'c', 'a', 'b', 'c']
    >>> listSliceWrap(['a','b'], 0, 2, 'index')
    [0, 1]
    >>> listSliceWrap(['a','b'], -3, 3, 'index')
    [1, 0, 1, 0, 1, 0]
    """
    fmt = fmt.lower()
    if a == b: return [] # equal value returns empty list
    elif a < b:
        min = a
        max = b
    else: # a > b
        min = b
        max = a
    post = []
    for i in range(min, max):
        q = i % len(src)
        if fmt == 'value': # this is default behavior
            post.append(src[q])
        elif fmt == 'index':
            post.append(q)
        elif fmt == 'valueactive': 
            if src[q] > 0: post.append(src[q])
        elif fmt == 'valuepassive': 
            if src[q] == 0: post.append(src[q])
        elif fmt == 'indexactive': 
            if src[q] > 0: post.append(q)
        elif fmt == 'indexpassive': 
            if src[q] == 0: post.append(q)
        elif fmt == 'pair':
            post.append((q, src[q]))
        else: raise ValueError
    return post
    
    
def urlStrBreak(url):
    """takes a url and adds spaces, allowing for proper typesetting"""
    if url[:7] == 'http://':
        head = url[:7]
        tail = url[7:]
    else: # no leading http
        head = ''
        tail = url
    tail = tail.replace('/', '/ ') # add spaces
    # in case of long cgi quaries
    tail = tail.replace(';', '; ') # add spaces
    tail = tail.replace('=', '= ') # add spaces
    url = head + tail
    return url

def urlPrep(url, fmt=None):
    """prep a url: add http:// if needed

    >>> urlPrep('athenacl.org')
    'http://athenacl.org'
    >>> urlPrep('http://athenacl.org')
    'http://athenacl.org'
    """
    httpStub = 'http://'
    fileStub = 'file://' # may be different for dif browsers/plats
    if fmt == None:
        fmt = httpStub # assume http
    elif fmt == 'http':
        fmt = httpStub
    elif fmt == 'file':
        fmt = fileStub
    if url[:len(fmt)] != fmt: # assume 
        return '%s%s' % (fmt, url)
    else:
        return url # dont change

def pathStrBreak(path):
    """takes a path and adds spaces, allowing for proper typesetting
    used for urls more than real file paths"""
    path = path.replace('/', '/ ') # add spaces
    return path

#-----------------------------------------------------------------||||||||||||--                  
# numerical conversions and utilities

def floatToInt(x, method='round'):
    """convert a float to an int with various methods
    methods: round, floor, weight
    weight performa a probabilistic rounding to the nearest integer
        this means that at .5, there is an equal chance

    >>> floatToInt(3.5)
    4
    >>> floatToInt(3.5, 'floor')
    3
    >>> floatToInt(3.5, 'ceiling')
    4
    >>> post = [floatToInt(3.5, 'weight') for x in range(100)]
    >>> post.count(3) > 35
    True
    >>> post.count(4) > 35
    True
    """
    if isInt(x): return x # dont change if already an int
    if method == 'round':
        return int(round(x))
    elif method == 'floor':
        x, y = divmod(x, 1)
        return int(x)
    elif method == 'ceiling':
        x, y = divmod(x, 1)
        shift = 0
        if y > 0: shift = 1
        return int(x) + shift
    elif method == 'weight':
        q = random.random() # random val b/n 0 and 1
        # if .5, an even prob of going each way
        a, b = divmod(x, 1)
        if b == .5: # if at half, equal chance for either direction
            if q >= .5: weight = 1
            else: weight = 0
        elif b > .5: # b is large, favor going up
            if q <= b: weight = 1
            else: weight = 0
        elif b < .5: # b is small, favor going down
            if q >= b: weight = 0
            else: weight = 1
        return int(a+weight)
        

#-----------------------------------------------------------------||||||||||||--                  
def _labelOrdered(msg, n, symbols):
    """recursive function to create symbol labels
    """
    x, y = divmod(n, len(symbols))
    # y can always be used to access a character
    # x is one more than the necessary value
    xPost = x - 1 
    # xPost should be used to access symbols if necessary
    msg = []
    if x != 0 and xPost < len(symbols): # greater tn 26
        msg.append(symbols[xPost])
        msg.append(symbols[y])
    elif x != 0 and xPost >= len(symbols): # x is greater than number of symbols
        msg = _labelOrdered(msg, xPost, symbols)
        msg.append(symbols[y])
    elif x == 0:
        msg.append(symbols[y])   
    return msg

def genAlphaLabel(number):
    """generate alphabetic symbol labels, in the form: 
    a-z, aa, ab, ..., ba, bb, ...
    
    >>> genAlphaLabel(12)
    ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']
    """          
    label = []
    for n in range(number):
        msg = []
        msg = _labelOrdered(msg, n, string.ascii_lowercase)
        label.append(''.join(msg))
    return label
        

#-----------------------------------------------------------------||||||||||||--
# acronym tools

def acronymLibToStr(refDict):
    """convert a refDict of acronyms and names into
    two stings presentable to the user, showing the expanded string
    and the acronym

    >>> refDict = {'o': 'open', 'ls':'list'}
    >>> acronymLibToStr(refDict)
    ('list, open', 'ls, o')
    """
    short = []
    long = []
    keys = refDict.keys()
    keys.sort()
    for key in keys:
        value = refDict[key]
        short.append(key)
        long.append(value)
    return ', '.join(long), ', '.join(short)
        
        
def acronymExtract(usrStr):
    """take a usrStr and compact into an accronym if capitals are used
    if not capitals, just get first letter
    always returned in lower case

    >>> acronymExtract('thisIsATest')
    'tiat'
    >>> acronymExtract('thisIsAnotherTest')
    'tiat'
    """
    # serach usrStr before reducing case
    autoStr = []
    for i in range(0, len(usrStr)):
        if i == 0: # always get first character
            autoStr.append(usrStr[i])
        elif usrStr[i] in string.ascii_uppercase:
            autoStr.append(usrStr[i])
    autoStr = strScrub(''.join(autoStr), 'lower')
    return autoStr
        
def optionUniqueKeyLeadChar(refDict):
    """determine if a dictionary of options has unique first
    characters, such that auto acronym expansion can happen

    >>> refDict = {'oc':'orderedCyclic', 'rw':'randomWalk'}
    >>> optionUniqueKeyLeadChar(refDict)
    True
    """
    firstChar = []
    for label in refDict.keys(): # keys are acronymes
        label = label.lower()
        char = label[0] # get firs character
        if char in firstChar:
            # cant auto search, as more than one key have same first letter
            return False
        firstChar.append(char)
    return True # all keys have unique first characters
        
def acronymExpand(usrStr, refDict, autoSearch=None):
    """provide a standard name reference dictionary in the format:
    accronym: expansion (w/Case)
    usrStr is scrubed, and then is searched for matches as either an
    acronym, or as a complete string; 
    
    if autoSearch is on, will attempt to extact an acronyme from capitals or
    first letter; only good if no like matches possible just by first char
    if None: will automatically determin if the refDict is good for this
    
    in this refDict, the desired string is the value, not the key:
        a = {'oc':'orderedCyclic', }

    >>> refDict = {'oc':'orderedCyclic', 'rw':'randomWalk'}
    >>> acronymExpand('oc', refDict)
    'orderedCyclic'
    >>> acronymExpand('OC', refDict)
    'orderedCyclic'
    """
    if usrStr == None: return None
    assert isStr(usrStr) and isDict(refDict)
    if usrStr == '': return None
    if autoSearch == None: # compare first chars of refDict keys
        autoSearch = optionUniqueKeyLeadChar(refDict)   
    # do before changing case
    autoStr = acronymExtract(usrStr)
    usrStr = strScrub(usrStr, 'lower')
    for key in refDict.keys():
        # check if key mathces first
        if usrStr == key.lower():
            return refDict[key] # return value, not key
        # check if line matches
        elif usrStr == refDict[key].lower():
            return refDict[key]
    # if not match, and auto on, search auto extraction
    if autoSearch:
        for key in refDict.keys():
            # check if key mathces first; dont check whole string
            if autoStr == key.lower():
                return refDict[key]
    return None # no match found


def selectionParse(usrStr, refDict, autoSearch=None):
    """prvide a ref dict of possible values and the necessary key
    in the form key: ['oc', 'ordered', 'orderedCyclic']
    will search all options and try to find a match; 
    if auto Search is on, will try to match first chars or do auto
    acronyme expansion
    if no match is found, None is returned
    
    in this refDict, the desired string is the key, not the values:
        a = {'orderedCyclic': ['oc', 3, 'order'], }

    >>> refDict = {'orderedCyclic': ['oc', 3, 'order'], }
    >>> selectionParse('oc', refDict)
    'orderedCyclic'
    >>> selectionParse('order', refDict)
    'orderedCyclic'
    """
    if usrStr == None: return None
    assert isDict(refDict) and (isStr(usrStr) or isNum(usrStr))
    # convert usrStr to a string (it may be a a number)
    if isNum(usrStr):
        usrStr = str(usrStr)
    
    if usrStr == '': return None
    if autoSearch == None: # compare first chars of refDict keys
        # this will reassign a value to autoSearch if not explicitly
        # declared on or off
        autoSearch = optionUniqueKeyLeadChar(refDict)  
    # do before changing case
    autoStr = acronymExtract(usrStr)          
    # serach values in dict
    usrStr = strScrub(usrStr, 'lower')
    for key in refDict.keys():
        if isStr(key):
            if key.lower() == usrStr:
                return key
        else:
            if str(key) == usrStr:
                return key
        for val in refDict[key]:
            if not isStr(val):
                val = str(val) # get as a string
            if val.lower() == usrStr:
                return key
    if autoSearch:
        for key in refDict.keys():
            # may just get first letter
            autoKey = acronymExtract(key)
            if autoStr == autoKey:
                return key
    return None # no match found
    
def selectionParseKeyLabel(ref, finalStr='or'):
    """utility to convert a selection parse dictionary to a text label
    that can be presented to users as a help string"""
    names = ref.keys()
    if len(names) == 1:
        return names[0] # value alone
    names.sort()
    names[-1] = '%s %s' % (finalStr, names[-1])
    if len(names) <= 2:
        return ' '.join(names)
    else:
        return ', '.join(names)
    
    
#-----------------------------------------------------------------||||||||||||--

def _restringComma(direction, usrStr):
    """replace or restore commas for a huge string
    look for commas w/n parallel quotes, or commas w/n braces
    direction == in, out
    will not work with an expression like this:
        cant evalueat from outside in...
        "(123, 123, "2,3")"
    will work with this:
        "a{3,1,1}b",30,{2,1,1},(123, 123, "2,3")
    """
    sym = '???????'
    COMMA = ','
    if direction == 'out': # restore comma
        return usrStr.replace(sym, COMMA)

    pairs = (("'", "'"), ('"', '"'), ('{', '}'))
    curStr = usrStr[:]
    newStr = []
    # do each pair at a time
    for open, close in pairs:
        status = 0
        for char in curStr:
            if char == open:
                status = 1
            if char == close:
                status = 0
            # examine and append
            if char != COMMA:
                newStr.append(char)
            else: # found a comma, see if we are w/n a boundary
                if status:
                    newStr.append(sym)
                else: # keep comma otherwise
                    newStr.append(COMMA)
        # clear for next pass
        curStr = ''.join(newStr)
        #print _MOD, curStr
        newStr = []
    return curStr
    

def restringulator(usrStr):
    """check if a string list has strings that are unquoted; 
    if so, quote, otherwise check if there is an even number of strings
    used in all TIe commands to process lists that may contain strings
    allows string to evaluated into a list of string, ints, or lists
    will handle any level of embedded lists, like (((a),(b)),(c))
    will assume any comma-separated chunk w/ any alpha char is a string
    note: will specificall look for logical strings that have | or & and
        stringulate
    note: will choke if a comma is found inside of string arg!
        will also choke if a comma is fonud w/n a brace
        for these reasons a special check is done

    >>> restringulator('this, is, a , test')
    "'this','is','a','test'"
    >>> restringulator('this, 3, 12.5, (test, (a, 3, 4)), test')
    "'this',3,12.5,['test',['a',3,4]],'test'"

    """
    if usrStr == '': return usrStr
    newStr = []
    # primary division is between commas; for this reason 
    # commas myst be encoded before division
    usrStr = _restringComma('in', usrStr)
    # divide by quotes
    for part in usrStr.split(','): # split at commas
        part = part.strip()
        part = part.replace('[', '(') # change everything to a paren char
        part = part.replace(']', ')') # will re-convert to list at end
        # create a version of the part w/ paren stripped
        partClean = part[:] # no brackets, just paren
        partClean = partClean.replace('(', '') 
        partClean = partClean.replace(')', '') 

        if part.find('"') >= 0 or part.find("'") >= 0:
            if part.count('"') % 2 == 0 and part.count("'") == 0:
                # even number of ", no incidence of '
                newStr.append(part)
                continue # assume it has quotes already
            elif part.count("'") % 2 == 0 and part.count('"') == 0:
                # even number of ', no incidence of "
                newStr.append(part)
                continue # assume it has already
            else: # badly matched quotes, need to be fixed: remove all
                part = part.replace('"','')
                part = part.replace("'",'')
        alpha = 0 # assume not
        # different ways of determining of this part is a string char seq
        for char in part: # scroll through chars, accept only ( or alpha
            if char == '(' or char == ' ': # allow leading spaces
                continue
            elif char.isalpha() or char in ['/', '+', '_']: 
                # special chars, as in file paths, rhythm notations
                alpha = 1 # look for first one
                break
            else: # any char that is not a ( or an alpha; may be a number, or sieve
                alpha = 0
                break
        # a global check of the part ot see if does not have number chars
        # is this all that is necessary: ex '+3.' should be string, for rhythm
        # '-3.' is a not stringulated
        if not isCharNum(partClean): # only use cleaned part, w/o paren
                alpha = 1
        # special selection of logical, sieve, and markov strings
        # if contain alpha, will already be interpreted as string
        # sieves will not contain alphas, only numbers and symbols
        for sym in ['|', '&', '@', '{', '}', '=']:
            if sym in part:
                alpha = 1
                break
        # if a string collection then process
        if alpha:
            # must watch for partial lists that have been broken
            parenO = [] #open
            parenC = [] # close
            partStr = []
            for char in part:
                if char == '(':
                    parenO.append(char)
                elif char == ')':
                    parenC.append(char)
                else:
                    partStr.append(char)
            partStr = ''.join(partStr)
            partStr = partStr.strip() # remove white space
            newStr.append('%s%r%s' % (''.join(parenO), partStr,
                                             ''.join(parenC)))
        else:
            newStr.append(part)
    # convert everything to a list w/ brackets
    # this solves many problems of single elemetns in parenthesis
    finalStr = ','.join(newStr)
    finalStr = finalStr.replace('(', '[')
    finalStr = finalStr.replace(')', ']')
    # decode enbedded commas
    finalStr = _restringComma('out', finalStr)
    
    #print _MOD, finalStr
    return finalStr


#-----------------------------------------------------------------||||||||||||--


class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testSelection(self):

        # sometimes we need robust collections of synonymes
        choiceA = {'limit': ['l', 'limit', 3], 
                      'wrap': ['wsdf', 'wrap'], 
                      'reflect' :['r', 'reflect']
                     }
                     
        for usrStr in ['l', 'LIMIT', 3]:
            self.assertEqual(selectionParse(usrStr, choiceA), 'limit')

        for usrStr in ['w']:
            self.assertEqual(selectionParse(usrStr, choiceA), 'wrap')

        # sometiems we just want to acronymes
        choiceB = {
            'co'      :'csoundOrchestra',
            'cs'      :'csoundScore',
            'cd'      :'csoundData', 
            'cb'      :'csoundBatch',
            'mf'      :'midiFile',
            'ts'      :'textSpace',
            'tt'      :'textTab',
            'mc'      :'maxColl',
            'xao'     :'xmlAthenaObject',
            }

        for usrStr in ['co']:
            self.assertEqual(acronymExpand(usrStr, choiceB), 'csoundOrchestra')
        for usrStr in ['ts', 'textspace']:
            self.assertEqual(acronymExpand(usrStr, choiceB), 'textSpace')


    def testFloatToInt(self):
        '''add examination here'''
        for x in range(0,50):
            [floatToInt(x, 'weight') for x in [
                    .05,.2,.3,.4,7,.5,.5,.5,.5,7,.6,.7,.8,.95]]


#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)
















