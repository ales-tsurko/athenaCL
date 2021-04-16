#-----------------------------------------------------------------||||||||||||--
# Name:          imageTools.py
# Purpose:       General image processing and drawing tools using PIL, Tk, and 
#                    vector graphics
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import os, random, string, copy, time, array
import unittest, doctest


from athenaCL.libATH import drawer
from athenaCL.libATH import interpolate
from athenaCL.libATH import fontLibrary
# dialog import imageTools.py for finding dlg visual formats
from athenaCL.libATH import osTools

_MOD = 'imageTools.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)


#-----------------------------------------------------------------||||||||||||--
# note: this imports must match those tested in drawer.imageFormats
try:
    from PIL import Image, ImageDraw, ImageFont #, ImageFilter ImageTk
    PIL = 1
except ImportError:
    PIL = 0
try:
    import tkinter
    TK = 1
except ImportError:
    TK = 0


#-----------------------------------------------------------------||||||||||||--
FONTPATH = os.path.join(os.path.expanduser('~'), 'Library', 'FontsPIL')
if not os.path.exists(FONTPATH):
    FONTPATH = None
    # load the better than nothing default
    # print _MOD, 'no PIL fonts available'

    
#-----------------------------------------------------------------||||||||||||--
# these methods borrowed from:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/266466/index_txt

def RGBToHTMLColor(rgb_tuple):
    """ convert an (R, G, B) tuple to #RRGGBB 

    >>> RGBToHTMLColor((3,4,5))
    '#030405'
    """
    if drawer.isStr(rgb_tuple):
        if rgb_tuple[0] == '#': # already a string
            return rgb_tuple
    for x in rgb_tuple:
        assert x < 256 and x >= 0
    hexcolor = '#%02x%02x%02x' % rgb_tuple
    # that's it! '%02x' means zero-padded, 2-digit hex values
    hexcolor = hexcolor.upper()
    return hexcolor

def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple 

    >>> HTMLColorToRGB(('#ffffff'))
    (255, 255, 255)
    """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError("input #%s is not in #RRGGBB format" % colorstring)
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)
    
def HTMLColorToUnitRGB(colorstring):
    """ converts #RRGGBB to postScript style float values
    assume that there are 256 values

    >>> HTMLColorToUnitRGB('#ffffff')
    (1.0, 1.0, 1.0)
    """
    max = 255.0
    r, g, b = HTMLColorToRGB(colorstring)
    r = r / max
    g = g / max
    b = b / max
    return r, g, b

def HTMLColorToPILColor(colorstring):
    """ converts #RRGGBB to PIL-compatible integers"""
    colorstring = colorstring.strip()
    while colorstring[0] == '#': colorstring = colorstring[1:]
    # get bytes in reverse order to deal with PIL quirk
    colorstring = colorstring[-2:] + colorstring[2:4] + colorstring[:2]
    # finally, make it numeric
    color = int(colorstring, 16)
    return color

def PILColorToRGB(pil_color):
    """ convert a PIL-compatible integer into an (r, g, b) tuple """
    hexstr = '%06x' % pil_color
    # reverse byte order
    r, g, b = hexstr[4:], hexstr[2:4], hexstr[:2]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)

def PILColorToHTMLColor(pil_integer):
    return RGBToHTMLColor(PILColorToRGB(pil_integer))

def RGBToPILColor(rgb_tuple):
    return HTMLColorToPILColor(RGBToHTMLColor(rgb_tuple))

# added for easy processing
def FloatToRGB(cellValue):
    """translate a cell value to a color or gray shade
    positive shift will make that much brighter
    negative shift will make darker"""
    # must invert cell value, so 1 is black, or 0
    cellValue = 1-cellValue
    # if not float return after reversing, could be a decimal
    return (float(str(cellValue)) * 255, float(str(cellValue)) * 255,
             float(str(cellValue)) * 255)

#     if not drawer.isInt(cellValue):
#         print _MOD, 'converting non int'
# 
#     cellMax = 255 * max
#     if cellMax >= 255: cellMax = 255
#     cellMin = 255 * min
#     if cellMin <= 0: cellMin = 0
#     cellRange = cellMax - cellMin
#     shade = int(round(cellMin + (cellRange * cellValue))) 
#     tk_rgb = (shade,shade,shade) # (shade, shade, shade) 
#     return tk_rgb


#-----------------------------------------------------------------||||||||||||--
# tools for determining image format types
# vetor here referes to a trademarked name
# dynamic testing of available formats in drawer.imageFormats



        
    
#-----------------------------------------------------------------||||||||||||--
# designed for use with PIL fonts found here
# http://effbot.org/downloads/
fontLibPil = {
    'char' : ('charI', 'charR', ),
    'courier' : ('courB', 'courO', 'courR'),
    'helvetica' : ('helvR', 'helvO', 'helvB'),
    'lub' : ('lubB', 'luBIS', 'lubI', 'luBS', 'lubR', 
                'luIS', 'luRS', 'lutBS', 'lutRS'),
    'ncen' : ('ncenB', 'ncenBI', 'ncenI', 'ncenR'),
    'symbol' : ('symb', ),
    'tech' : ('tech', 'techB',),
    'term' : ('termB', 'term',),
    'times' : ('timB', 'timBI', 'timI', 'timR'),
    }

def getFontPath(xxx_todo_changeme): # dont check for errrs
    (face, style, size) = xxx_todo_changeme
    for n in fontLibPil[face]:
        if style in n or style == n:
            group = n
            break
    if size <= 9:
        sizeStr = '0%s' % size
    else:
        sizeStr = str(size)
    name = '%s%s.pil' % (group, sizeStr)
    return os.path.join(FONTPATH, name)
    
    
    
#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
# note: these objects require PIL
class Thumb:
    def __init__(self, fileList, size=256, fmt='.jpg'):
        "create a thumbnail; if size is none, dont resize"
        self.sizeW = size
        self.sizeH = size
        self.fmt = fmt
        # check if file list is a dir, if so, get a listing of image files
        if drawer.isList(fileList):
            self.fileList = fileList
        else:
            self.fileList = [fileList, ] # its a single file

    def reduce(self):
        from PIL import Image
        procFiles = [] # stores tuples of src, dst file
        nameOutFiles = []
        for infile in self.fileList:
            if self.sizeW == None:
                outfile = os.path.splitext(infile)[0] + self.fmt
            else:
                outfile = os.path.splitext(infile)[0] + ".th%s%s" % (
                                                              self.sizeW, self.fmt)
            if infile.endswith('.gif'):
                print(_MOD, 'cannot process gif files: %s' % infile)
            elif outfile in nameOutFiles:
                print(_MOD, 'file already generated: %s' % outfile)
            elif infile != outfile:
                try:
                    im = Image.open(infile)
                    if self.sizeW != None: # only resize if size is not None
                        print(_MOD, 'reducing size to %s' % self.sizeW)
                        im.thumbnail((self.sizeW, self.sizeH), Image.ANTIALIAS)
                    #im.save(outfile, "JPEG")
                    im.save(outfile)
                    procFiles.append([infile, outfile])
                    nameOutFiles.append(outfile)
                except IOError as msg:
                    print(_MOD, "cannot create thumbnail: %s" % infile, msg) 
            else:
                print(_MOD, 'name conflict: %s' % infile)
        return procFiles




#-----------------------------------------------------------------||||||||||||--
class GridGraphic:
    """uess a list of lists as matrix for generating images"""

    def __init__(self, gridData=None, dataType='float', transp=None):
        """if dataType == float values are interpreted as gray scale
        if dataType == hex, html hex a decimal strings expected
        if dataType == rgb, assume rgb triples
        rot is rotatioin in degrees
        transparency: None is off, value is color that is transparent?

        """
        self.dataType = dataType
        self.transp = transp
        if gridData == None: # use demo
            self.gridData = [] # a list of lists
            for x in range(20):
                self.gridData.append([1,1,1,1,.5,.5,.5,.5,1,1,1,1,
                                             0,0,0,1,1,1,1,0,0,0,0])
        else:
            self.gridData = gridData
        self.noCols = len(self.gridData[0])
        self.noRows = len(self.gridData)
          
        self.RGBData = self._convertToRGB() 

        self.imageObj = Image.new("RGB", (self.noCols, self.noRows))
        self.imageObj.putdata(self.RGBData)

        # not needed for transparency create mask
        #self.imageObj = self.imageObj.convert("RGBA") 
        #mask = Image.new("1", (self.noCols, self.noRows))
        #self.imageObj.putalpha(mask)

        # putalpha(band)
        # To add an alpha (transparency) band to an "RGBA"-mode image, 
        # call this method and pass it an
        # image of the same size having mode "L" or "1". The pixels of the band
        # image replace the alpha
        # band of the original image in place

    def _convertToRGB(self):
        "translate a list of cells to RGB"
        inputList = [] # self.gridData
        outputList = []
        # flatten grid into one long list
        for row in self.gridData:
            for col in row:
                inputList.append(col)
                
        for cell in inputList:
            if self.dataType == 'float':
                outputList.append(FloatToRGB(cell))
            elif self.dataType == 'hex':
                outputList.append(HTMLColorToRGB(cell))
            elif self.dataType == 'rgb':
                outputList.append(cell)
        #for each in self.gridData._flatten(self.gridData):
        return outputList

    def scale(self, xMult, yMult):
        self.imageObj = self.imageObj.resize((self.noCols*xMult, 
                                 self.noRows*yMult))

    def rotate(self, angle):
        if angle != 0:
            self.imageObj = self.imageObj.rotate(angle)

    def write(self, filePath, openMedia=1):
        "Saves the Image; .png and .jpg both work; format based on extensions"
        self.filePath = filePath
        if self.transp != None:
            self.imageObj.save(self.filePath, transparency=self.transp)
        else: #determine format from name
            self.imageObj.save(self.filePath)

    def show(self, dir=None, prefDict=None):
        "Opens default image viewer and shows picture"
        self.imageObj.show(dir, prefDict)

    def getData(self):
        bundle = []
        seq = list(self.imageObj.getdata())
        row = []
        for pix in seq:
            if len(row) == self.noCols:
                bundle.append(row)
                row = []
            row.append(pix)
        return bundle




class BarCode(GridGraphic):
    def __init__(self, src=None, width=120, foreColor='#000000', 
                          backColor='#aaaaaa', xMult=1, yMult=1, horizontal=1):
        if width == None and src == None:
            raise ValueError('not enough arguments')
        #foreColor can be a list of colors that are chosen from at random
        if not drawer.isList(foreColor):
            foreColor = [foreColor,]
        if not drawer.isList(backColor):
            backColor = [backColor,]
        if backColor[0] == None: # if none, back it transparent   
            self.transp = 0 # black
            backColor[0] = '#000000' # make it black
        else:
            self.transp = None # none is no transp

        if width == None:
            width = len(src)

        # do not apply xmult yet, but account for it in the lineGraph
        lineGraph = []
        if src == None: # creates a random distribution
            for i in range(0,width):
                pixel = random.choice((0,1)) # choose on or off
                lineGraph.append(pixel)
        else: # wrap src to fill width
            for i in range(0,width):
                pixel = src[i % len(src)] # wrap
                lineGraph.append(pixel)

        gridRow = []
        for pixel in lineGraph:
            #choose random color
            if pixel: # if 1
                color = random.choice(foreColor)
            else:
                color = random.choice(backColor)
            for x in range(0, xMult):
                gridRow.append(color)
        gridData = [gridRow]

        GridGraphic.__init__(self, gridData, 'hex', self.transp)
        self.scale(xMult, yMult)
        if not horizontal: # rotate 90 degrees      
            self.rotate(90)
        

class GridText(GridGraphic):
    def __init__(self, msg='test', foreColor='#000000', 
                     backColor='#aaaaaa', font='micro', kernBit=1, 
                     vertBit=None, xMult=1, yMult=1, horizontal=1, 
                     charWrapWidth=None):

        #foreColor can be a list of colors that are chosen from at random
        if not drawer.isList(foreColor):
            foreColor = [foreColor,]
        if not drawer.isList(backColor):
            backColor = [backColor,]
        if backColor[0] == None: # if none, back it transparent   
            self.transp = 0 # black
            backColor[0] = '#000000' # make it black
        else:
            self.transp = None # none is no transp

        kernEqual = 0 # treat as equla spaced?
        vertBit = None # use default
        obj = fontLibrary.FontBitMap(msg, font, kernEqual, kernBit, vertBit, 
                charWrapWidth)
        gridData = obj.encode()
        for row in range(0, len(gridData)):
            rowData = gridData[row]
            for col in range(0, len(rowData)):
                if gridData[row][col] == 1:
                    gridData[row][col] = random.choice(foreColor)
                else: # its 0
                    gridData[row][col] = random.choice(backColor)

        GridGraphic.__init__(self, gridData, 'hex', self.transp)
        self.scale(xMult, yMult)
        if not horizontal: # rotate 90 degrees      
            self.rotate(90)



class GridBlend(GridGraphic):
    def __init__(self, colorStart='#000000', colorEnd='#333333', length=20, 
                     direction='x', width=40):
        if direction == 'y':
            horizontal = 0
        else:
            horizontal = 1

        colorListStart = HTMLColorToRGB(colorStart)
        colorListEnd = HTMLColorToRGB(colorEnd)


        colorArray = [[], [], []]

        for i in range(3): # for r g b
            s = colorListStart[i]
            e = colorListEnd[i]
            interpObj = interpolate.OneDimensionalLinear(s, e)
            for val in interpObj.discrete(length, 0):
                colorArray[i].append(int(val))

        gridData = []
        for row in range(length):
            rowData = []
            code = RGBToHTMLColor((colorArray[0][row], 
                                          colorArray[1][row], colorArray[2][row]))
            for col in range(width):
                rowData.append(code)
            gridData.append(rowData)

        GridGraphic.__init__(self, gridData, 'hex', None)
        if not horizontal: # rotate 90 degrees      
            self.rotate(90)


#-----------------------------------------------------------------||||||||||||--
class FontText:
    """used for creating text chunk images for web pages"""
    def __init__(self, text=None, fontInfo=None, size=None, 
                     bg="#000000", fg="#ffffff", xMult=1, yMult=1, 
                     anti=0):
        if text == None:
            text = string.ascii_letters
        if fontInfo == None: # default font
            fontInfo = ('helvetica', 'R', 12)
        if FONTPATH == None:
            font = ImageFont.load_default() # get basic
        else:
            font = ImageFont.load(getFontPath(fontInfo))

        # should be based on size of text
        if size == None: # area of background
            width = len(text) * fontInfo[2]
            height= fontInfo[2] * 2
        else:
            width, height = size

        if bg == None: # assume transparent
            bg = '#000000'
            self.transp = 0 # trans color is black?
        else:
            self.transp = None # no transparency

        bg = HTMLColorToRGB(bg)
        fg = HTMLColorToRGB(fg)

        self.im = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(self.im)
        draw.text((0, 0), text, font=font, fill=fg)

        #im = im.resize((width, height), Image.ANTIALIAS)
        if anti:
            self.im = self.im.resize((width*xMult, height*yMult), Image.ANTIALIAS)
        else:
            self.im = self.im.resize((width*xMult, height*yMult))

        #self.im.show()

    def write(self, filePath, openMedia=1):
        "Saves the Image; .png and .jpg both work; format based on extensions"
        self.filePath = filePath
        if self.transp != None:
            self.im.save(self.filePath, transparency=self.transp)
        else: #determine format from name
            self.im.save(self.filePath)


#-----------------------------------------------------------------||||||||||||--
class WebText:
    """writes a text image with special styles and mods on a transparent bkg"""
    def __init__(self, text, fg, style):
        if style in ['miniLargeA', 'macro']:
            self.image = GridText(text, fg, None, 'macro', 4, None, 1, 1)

            #text = text.upper() # make all caps
            #newText = []
            #for char in text:
            #    newText.append('%s ' % char)
            #fontInfo = ('helvetica', 'R', 8)
            #Text.__init__(self, ''.join(newText), fontInfo, None, None, fg, 2, 1)

        elif style in ['miniSmallA', 'micro']:
            wrapW = 60 # chars
            self.image = GridText(text, fg, None, 'micro', 2, None, 1, 1, 1, wrapW)

            #fontInfo = ('helvetica', 'R', 8)
            #Text.__init__(self, text, fontInfo, None, None, fg, 1, 1)

        elif style in ['poster']:
            wrapW = 60 # chars
            self.image = GridText(text, fg, None, 'poster', 2, None, 
                                         1, 1, 1, wrapW)
        elif style in ['strong']:
            wrapW = 60 # chars
            self.image = GridText(text, fg, None, 'strong', 2, None, 
                                         1, 1, 1, wrapW)
        elif style in ['strongDouble']:
            wrapW = 60 # chars
            self.image = GridText(text, fg, None, 'strong', 2, None, 
                                         2, 2, 1, wrapW)
        elif style in ['capitalSingle', 'capital']:
            wrapW = 60 # chars
            self.image = GridText(text, fg, None, 'capital', 2, None, 
                                         1, 1, 1, wrapW)
        elif style in ['capitalDouble']:
            wrapW = 60 # chars
            self.image = GridText(text, fg, None, 'capital', 2, None, 
                                         2, 2, 1, wrapW)
        elif style in ['capitalQuad']:
            wrapW = 60 # chars
            self.image = GridText(text, fg, None, 'capital', 2, None, 
                                         4, 4, 1, wrapW)

        else:
            raise KeyError('no such style name %r' % style)

    def write(self, filePath):
        self.image.write(filePath)





#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--
# note: these objects use PIL and TK, and only use pil

class _CanvasBase:
    """abstract convas object to allow for drawing in both PIL and tk
    all colors are in html style hex"""

    def __init__(self, w, h, bg, fmt='png', name='image', transp=None):
        self.w = w
        self.h = h
        self.bg = bg
        self.fmt = fmt
        self.name = name
        self.transp = transp # transparancy only works w/ pil

    def _gridCenter(self, point):
        """to find the center of a bitMap dimensions an off by 1 error
        occurs in the standard case. a 1 shift must be applied"""
        return int(round((point * .5))) - 1 

    def _widthRound(self, width):
        """vector can hadle floating point widths
        here, round; if 0 or None, keep"""
        if width == 0 or width == None:
            return width
        width = int(round(width)) # vector may have fractional widths
        if width == 0: # .2, rounded down, for example
            width = 1
        return width 

    def gridText(self, x, y, anchor, msg, font='micro', fill='#ffffff', 
             kernBit=1, vertBit=None, xMult=1, yMult=1, 
             horizontal=1, charWrapWidth=None):
        """create bit map font; same method for Tk and PIL, as these use
        the bitmap method
        a postscript version of this actually uses fonts
        anchor can be: nw, ne, nc; sw, se, sc
        """
        kernEqual = 0 # treat as equal spaced?
        vertBit = None # use default
        obj = fontLibrary.FontBitMap(msg, font, kernEqual, kernBit, vertBit, 
                charWrapWidth)
        gridData = obj.encode()
        xLen = len(gridData[0]) # get first row
        yLen = len(gridData)
        if anchor == 'nw': # default for most applications: uppr left
            xShift = 0
            yShift = 0
        elif anchor == 'ne': #
            xShift = -xLen
            yShift = 0
        elif anchor == 'nc': #
            xShift = -self._gridCenter(xLen)
            yShift = 0
            
        # vertical centering
        elif anchor == 'cw': #
            xShift = 0
            yShift = -self._gridCenter(yLen)
        elif anchor == 'ce': #
            xShift = -xLen
            yShift = -self._gridCenter(yLen)
        elif anchor == 'cc': #
            xShift = -self._gridCenter(xLen)
            yShift = -self._gridCenter(yLen)

        elif anchor == 'sw':
            xShift = 0
            yShift = -yLen + 1 # neg shift (reduce nw anchor by vert length)
        elif anchor == 'se':
            xShift = -xLen
            yShift = -yLen + 1
        elif anchor == 'sc':
            xShift = -self._gridCenter(xLen)
            yShift = -yLen + 1
        # move bitmap points (they assume a 'nw' origin'
        # with shift values calculated based on anchor points
        self.bitmap(x+xShift, y+yShift, gridData, fill) # bitmap method in child

    def rotate(self, degrees=90):
        pass # only PIL
    
    def write(self, filePath=None, openMedia=1):
        pass # PIL, PostScript

    def destroy(self):
        pass # only TK


#-----------------------------------------------------------------||||||||||||--
class TkCanvas(_CanvasBase):

    def __init__(self, w, h, bg, name, master):
        if not TK:
            raise ImportError('Tkinter not loaded')
        _CanvasBase.__init__(self, w, h, bg, 'tk', name)
        if master == None:
            self.master = tkinter.Tk()
        else:
            self.master = master
        # not sure this is needed
        #self.top = Tkinter.Toplevel() # create a top level?
        self.frame = tkinter.Frame(self.master, width=self.w, height=self.h, bd=0,
                                     bg=self.bg, relief='flat')
        self.frame.pack(fill='both', pady=0, padx=0)
        # create base canvas
        self.c = tkinter.Canvas(self.frame, bg=self.bg, bd=0, width=self.w, 
                    height=self.h, highlightthickness=0, 
                    closeenough=1, confine=1)
        self.c.pack(fill='both', pady=0, padx=0) 

    def rectangle(self, x1, y1, x2, y2, fill, outline, width=1):
        width = self._widthRound(width) # vector may have fractional widths
        # attempt to fix off by one error
        # this creates rectangles that better match PIL model
        self.c.create_rectangle(x1,y1,x2+1,y2+1, fill=fill, outline=outline, 
                                        width=width)

    def line(self, x1, y1, x2, y2, fill, width=1):
        width = self._widthRound(width) # vector may have fractional widths
        self.c.create_line(x1, y1, x2, y2, fill=fill, width=width)

    def fontText(self, x, y, anchor, text, font, fill):
        """anchors supirted: 'nw', 'sw', 'ne', 'se'
        default is nw (upper left corner)
        """
        self.c.create_text(x, y, text, font=font, fill=fill, anchor=anchor)

    def oval(self, x1, y1, x2, y2, fill, outline, width=1):
        width = self._widthRound(width) # vector may have fractional widths
        self.c.create_oval(x1, y1, x2, y2, fill=fill, outline=outline, 
                                 width=width)

    def bitmap(self, xShift, yShift, gridData, color=None):
        """if color==None, use data value in grid data as color value
        note: drawing a pixel image is not uniform b/n tk implementations
        on win nothing resuls from equal points: must add a single point"""

        # get constant shift values
        if os.name == 'mac': xBuf = 0
        elif os.name == 'posix': xBuf = 0
        else: xBuf = 1 # win tk requires extra pixel 

        x = 0
        y = 0
        for row in gridData:
            for col in row:
                if color != None:
                    if col == 0: # nothing here, and not a color value
                        colorUse = None # do not draw
                    else: # if 1, binary but mapp
                        colorUse = color
                elif color == None: # color not given, use values
                    colorUse = col
                if colorUse != None:
                    self.c.create_line((xShift+x, yShift+y, xShift+x+xBuf, yShift+y),
                                          fill=colorUse, width=1, capstyle="round")
                    # capstyle may not be the same on differnt tks, must specify
                x = x + 1
            x = 0
            y = y + 1

    def show(self, dir=None, prefDict=None):
        """dir and prefDict do nothing here"""
        # may need to pack again?
        #frame.pack(expand=1, fill='both', pady=0, padx=0)
        self.master.title(self.name)
        self.master.iconname(self.name)
        geometryStr = "%dx%d%+d%+d" % (self.w, self.h, 100, 100) # upLeft offset
        self.master.geometry(geometryStr)
        self.master.maxsize(width=self.w, height=self.h)
        self.master.minsize(width=self.w, height=self.h)
        self.master.resizable(width=0, height=0) # prohibit resizing
        # not calling these allows the window to be detached 
        #self.master.mainloop()
        # this should freeze the window
        #self.master.wait_window(self.c)

    def destroy(self):
        # might want to use self.frame instead?
        self.master.withdraw()
        self.master.destroy()
        del self.master


#-----------------------------------------------------------------||||||||||||--
class PilCanvas(_CanvasBase):
    def __init__(self, w, h, bg, name, transp, subFmt):
        _CanvasBase.__init__(self, w, h, bg, 'png', name, transp)
        self.subFmt = subFmt # may be 'jpg' or 'png'
        self.imageObj = Image.new("RGB", (self.w, self.h))
        self.c = ImageDraw.Draw(self.imageObj)
        # add background color if not None
        if self.bg == None or transp != None: pass
        else:
            self.c.rectangle((0,0,self.w, self.h), self.bg, outline=None)

    def rectangle(self, x1, y1, x2, y2, fill, outline, width=1):
        width = self._widthRound(width) # vector may have fractional widths
        self.c.rectangle((x1, y1, x2, y2), fill=fill, outline=outline)
        if outline == None:
            width = 0
        if width > 1: # draw rectangles inside to create width on outline
            for i in range(1, width): # one pixel is laready drawin
                self.c.rectangle((x1+i, y1+i, x2-i, y2-i), 
                                     fill=None, outline=outline)

    def line(self, x1, y1, x2, y2, fill, width=1):
        """lines in pil do not have a widht attribute, which forces
        drawing multiple lines to simulate width"""
        width = self._widthRound(width) # vector may have fractional widths
        if width == 1:
            self.c.line((x1, y1, x2, y2), fill=fill)
        elif width > 1: # even is drawn + 1 (down)
            #for i in range(1, width):
            for i in range(1, width):
                if x1 == x2: # its a vertical line
                    self.c.line((x1+i, y1, x2+i, y2), fill=fill)
                elif y1 == y2: # its a vertical line
                    self.c.line((x1, y1+i, x2, y2+i), fill=fill)
                else: # diagonal: draw a rectangle? this doesnt work well
                    if i % 2 == 0: # of even
                        self.c.line((x1+i, y1, x2+i, y2), fill=fill)
                    else: # odd
                        self.c.line((x1, y1+i, x2, y2+i), fill=fill)

    def fontText(self, x, y, anchor, text, font, fill):
        # default anchord position is 'ne' # position is upper right
        fontObj = ImageFont.load_default() # gets default font
        self.c.text((x, y), text, fill=fill, font=fontObj)

    def oval(self, x1, y1, x2, y2, fill, outline, width=1):
        width = self._widthRound(width) # vector may have fractional widths
        self.c.ellipse((x1, y1, x2, y2), fill=fill, outline=outline)
        if outline == None:
            width = 0
        if width > 1:
            for i in range(1, width):
                self.c.ellipse((x1+i, y1+i, x2-i, y2-i), 
                                     fill=None, outline=outline)

    def bitmap(self, xShift, yShift, gridData, color=None):
        """if color==None, use data value in grid data as color value"""
        x = 0
        y = 0
        for row in gridData:
            for col in row:
                if color != None:
                    if col == 0: # nothing here, and not a color value
                        colorUse = None # do not draw
                    else: # if 1, binary but mapp
                        colorUse = color
                elif color == None: # color not given, use values
                    colorUse = col
                if colorUse != None:
                    self.c.point((xShift+x, yShift+y), fill=colorUse)
                x = x + 1
            x = 0
            y = y + 1

    def rotate(self, angle=90):
        self.imageObj = self.imageObj.rotate(angle)
    
    def write(self, filePath=None, openMedia=1, prefDict=None):
        """transparency is stored at init"""
        #del self.c # not sure if this is necessary
        if filePath == None:
            ext = '.%s' % self.subFmt
            filePath = environment.getTempFile(ext)
            #filePath = drawer.tempFile(ext) # jpg/png       

        if self.transp != None: # transparency not working
            self.imageObj.save(filePath, transparency=self.transp)
        else: #determine format from name
            self.imageObj.save(filePath)
        if openMedia:
            osTools.openMedia(filePath, prefDict) #open for user
        self.filePath = filePath

    def show(self, dir=None, prefDict=None):
        """dir provides a directory to write a file w/ auto-gen name"""
        if dir != None: # get path
            ext = '.%s' % self.subFmt
            filePath = os.path.join(dir, drawer.tempFileName(ext))
        else:
            ext = '.%s' % self.subFmt
            filePath = environment.getTempFile(ext)
            #filePath = drawer.tempFile(ext) # jpg/png       
        self.write(filePath, 1, prefDict)
        #if self.subFmt == 'jpg': # gets defaul pil format, which is jpeg
        #    self.imageObj.show() # used to use show, but sometimes fails
        #elif self.subFmt == 'png': # write a file
        #    self.write()


#-----------------------------------------------------------------||||||||||||--
class EpsCanvas(_CanvasBase):
    """write a postscript vector graphics file"""
    def __init__(self, w, h, bg=None, name='untitled'):
        # increase size of w/h by to handle ob1 error
        _CanvasBase.__init__(self, w, h, bg, 'eps', name)
        self.title = name
        self.creator = 'athenaCL'
        self.forStr = 'athenaCL'
        self.date = time.asctime(time.localtime())
        self.defIndex = 0
        # canvas as a list of strings; append 
        self.c = []
        self.c.append(self._headStr())
        # add background color if not None
        if self.bg == None: pass
        else: # will append to c
            self.rectangle(0,0,self.w, self.h, self.bg, None, 0)
            
    def _headStr(self):
        """the head string for an eps/ps file is very sensitive
        changing this can result in cropping or other strangness
        do not define page size or anything else"""
        msg = []
        #msg.append('%!PS-Adobe-2.0\n')
        msg.append('%!PS-Adobe-3.1 EPSF-3.0\n') # for eps
        # % image or page area: lower left x y: upper right x y % 
        msg.append('%%BoundingBox: ')
        # as LLx, LLy, URx, URy
        msg.append(" %s %s %s %s " % (0, 0, self.w, self.h))
        msg.append("""
%%Title: %s 
%%Creator: %s   
%%For: %s
%%CreationDate: %s 
%%EndComments
/defaults save def
""" % (self.title, self.creator, self.forStr, self.date))
        return ''.join(msg)
  
    def _tailStr(self):
        """showpage actual prints ont pages
        returns a string: does not append to c"""
        msg = []
        msg.append("""
%%EndPage 
%%Trailer
grestore showpage defaults restore
%%EOF""")
        return ''.join(msg)
  
    #-----------------------------------------------------------------------||--
    # conversion utilities
    def _convertCoordSquare(self, x1, y1, x2, y2):
        """convert xy pairs to four points necessary for drawing
        assume xy pars are upper left, lower right
        but all measurements from ll, ur
        
        NOTE: there is an error in coordinates from lower left to upper right
        the sometimes are reversed (rotated 180 degrees)
        """     
        #assert y1 <= self.h
        #assert y2 <= self.h
        if y1 >= y2:
            yMin = y2
            yMax = y1
        else:
            yMin = y1
            yMax = y2
        # this was recently added; may cause errors...           
        if x1 >= x2:
            xMin = x2
            xMax = x1
        else:
            xMin = x1
            xMax = x2
            
        ll = (xMin, self.h - yMax) # lower left
        ul = (xMin, self.h - yMin) # upper left
        lr = (xMax, self.h - yMax) # lower right
        ur = (xMax, self.h - yMin) # upper right
        # return points measured from bottom
        return ll, ul, ur, lr

    def _convertCoordLine(self, x1, y1, x2, y2):
        # using square conversion causes errors when points are specified
        # from lower left to upper right; need to just return the appropriate
        # sides
        ll, ul, ur, lr = self._convertCoordSquare(x1, y1, x2, y2)
        if y1 > y2 and x1 < x2: # lower left to upper right
            return ll, ur
        elif y1 > y2 and x1 > x2: # lower right to upper left
            return lr, ul
        elif y1 <= y2 and x1 >= x2: # upper right to lower left
            return ur, ll 
        else: # standard case: upper left to lower right
            return ul, lr

    def _convertCoordArc(self, x1, y1, x2, y2):
        # find center point: add smaller size, plus half point
        x = x1 + ((x2 - x1) * .5)
        y = y1 + ((y2 - y1) * .5)
        # readius is simply mid-point: assume this is a circle
        radius = (x2 - x1) * .5 # assume its a circle
        # all points are the same
        ll, ul, ur, lr = self._convertCoordSquare(x, y, x, y)
        return ll[0], ll[1], radius
        
    def _getDefName(self):
        # get object def name
        strDef = 'obj%s' % self.defIndex         
        self.defIndex = self.defIndex + 1 # increment def index
        return strDef
            
    #-----------------------------------------------------------------------||-- 
    
    def rectangle(self, x1, y1, x2, y2, fill=None, 
                      outline=None, width=1):
        """closepath: enclose shape, which can be filled
        grey's vary from 0 to 1 
        set color w/ "setrgbcolor
        gsave and grestone necessary to wrap all definitions from 
            global namespace
            
        rectangles, to correspond to bit-map coordds, will add 1 to x and y 
        coords...
        """
        # if x or y are equal, draw a line instead of a rectangle
        # give the line a 1 point width
#         if x1 == x2 and y1 == y2:
#             self.line(x1, y1, x2, y2, fill, 1)
#             return None
#         elif x1 == x2 or y1 == y2:
#             self.line(x1, y1, x2, y2, fill, 1)        
#             return None
            
        ll, ul, ur, lr = self._convertCoordSquare(x1, y1, x2+1, y2+1) 
        # convert coords                                 
        if fill == None: strFill = ''
        else:
            r, g, b = HTMLColorToUnitRGB(fill)
            strFill = '%s %s %s setrgbcolor fill' % (r, g, b) 
        if outline == None: strOutline = ''
        else:
            r, g, b = HTMLColorToUnitRGB(outline)
            strOutline = '%s setlinewidth %s %s %s setrgbcolor stroke' % (width,
                                r, g, b)
        strDefName = self._getDefName() # get a unique def identifier        
        msg = []
        msg.append("""
/%s { newpath %s %s moveto %s %s lineto %s %s lineto %s %s lineto closepath gsave %s grestore gsave %s grestore} def """ % (strDefName, 
        ll[0], ll[1], ul[0], ul[1], ur[0], ur[1], lr[0], lr[1], 
        strFill, strOutline))
        msg.append("""
gsave %s 1 1 scale grestore
""" % strDefName)
        self.c.append(''.join(msg))

    def line(self, x1, y1, x2, y2, fill, width=.5):
        # there may be an ob1 error as in rectangle here; but cant fix
        # as would make straight lines crooked...
        pairL, pairR = self._convertCoordLine(x1, y1, x2, y2) # convert coords                               
        if fill == None: fill = ''
        else:
            r, g, b = HTMLColorToUnitRGB(fill)
            # linecap 2 sets projecting caps, extending to width
            # this does not yet seem to work
            strFill = '%s setlinewidth 2 setlinecap %s %s %s setrgbcolor stroke'%( 
                width, r, g, b)
        strDefName = self._getDefName() # get a unique def identifier        
        msg = []
        msg.append("""
/%s { newpath %s %s moveto %s %s lineto closepath gsave %s grestore} def 
""" % (strDefName, 
        pairL[0], pairL[1], pairR[0], pairR[1], 
        strFill))
        msg.append("""
gsave %s 1 1 scale grestore
""" % strDefName)
        self.c.append(''.join(msg))


    def _charFilter(self, usrStr):
        """replace characters in a usrStr w/ necssary escape chars"""
        msg = []
        for char in usrStr:
            if char in ['(', ')',]: # not sure if back-slash should be here
                msg.append('\%s' % char) # escape
            else:
                msg.append(char)
        return ''.join(msg) 

    def fontText(self, x, y, anchor='nw', text='test', font=None,
                     fill="#342396"):
        """vector font text defines 6 acnhors:
        nw, ne, nc; sw, se, sc"""
        # fontInfo = ('helvetica', 'R', 12)
        # for postscript, default anchor is 'sw'; need to translate

        # thought these were standard ps fonts: these do not seem to work for all
        # times-(roman/bold/italic/bolditalic)
        # helvetica-(bold/oblique/boldoblique)
        # courier-(bold/oblique/boldoblique)
        # symbol
        text = self._charFilter(text) # escape necessary characters       
        ll, ul, ur, lr = self._convertCoordSquare(x, y, x, y) # convert coords                               

        if font == None:
            fontFace = 'Times-Roman' 
            fontSize = '12' 
        else:
            # note: hyphenated font names do not work w/ eps
            # it may be that the style was not in the right case
            #if font[1] != None:
            #    fontFace = '%s-%s' % (font[0], font[1])
            #else:
            fontFace = '%s' % font[0]
            fontSize = str(font[2])
            
        # find the fontHeight, not the same as fontSize
        # this is found experimentally w/ courier
        # want upper left corner of font
        fontHeight = round((int(fontSize) * .55), 1)
        # this adjustment should be added to vertical positon 
        # (shifted upward) to account for strange spacing, on
        x = ll[0]   
        y = ll[1]
        
        if fill == None:
            strFill = ''
        else:
            r, g, b = HTMLColorToUnitRGB(fill)
            strFill = '%s %s %s setrgbcolor' % (r, g, b)
        if anchor == 'sw': # default is lower left
            strMove = '%s %s moveto' % (x, y)
        elif anchor == 'se': # pop removes y coord
            strMove = '%s (%s) stringwidth pop sub %s moveto' % (
                                        x, text, y)
        elif anchor == 'sc': # pop removes y coord
            strMove = '%s (%s) stringwidth pop 2 div sub %s moveto' % (
                                        x, text, y)
        elif anchor == 'cw': 
            strMove = '%s %s %s 2 div sub moveto' % (
                                        x, y, fontHeight)    
        elif anchor == 'ce': # pop removes y coord
            strMove = '%s (%s) stringwidth pop sub %s %s 2 div sub moveto' % (
                                        x, text, y, fontHeight)
        elif anchor == 'cc': # pop removes y coord
            strMove = '%s (%s) stringwidth pop 2 div sub %s 2 div moveto' % (
                                        x, text, fontHeight)                                          
        elif anchor == 'nw': 
            strMove = '%s %s %s sub moveto' % (x, y, fontHeight)
        # first put x coord on stack, then measure, remove y, then subtract
        elif anchor == 'ne': # pop removes y coord
            strMove = '%s (%s) stringwidth pop sub %s %s sub moveto' % (
                                        x, text, y, fontHeight)
        elif anchor == 'nc': 
            strMove = '%s (%s) stringwidth pop 2 div sub %s %s sub moveto' % (
                                        x, text, y, fontHeight)                                      
        msg = []
        msg.append("""
/%s findfont 
%s scalefont setfont 
newpath 
%s
%s 
(%s) show
""" % (fontFace, fontSize, strMove, strFill, text))
        self.c.append(''.join(msg))
        
    def oval(self, x1, y1, x2, y2, fill, outline, width=1):
        xCenter, yCenter, radius = self._convertCoordArc(x1, y1, x2, y2)
        if fill == None: strFill = ''
        else:
            r, g, b = HTMLColorToUnitRGB(fill)
            strFill = '%s %s %s setrgbcolor fill' % (r, g, b) 
        if outline == None: strOutline = ''
        else:
            r, g, b = HTMLColorToUnitRGB(outline)
            strOutline = '%s setlinewidth %s %s %s setrgbcolor stroke' % (width,
                                r, g, b)
        strDefName = self._getDefName() # get a unique def identifier        
        msg = []
        msg.append("""
/%s { newpath %s %s %s %s %s arc closepath gsave %s grestore gsave %s grestore} def """ % (
        strDefName, 
        xCenter, yCenter, radius, 0, 360,
        strFill, strOutline))
        msg.append("""
gsave %s 1 1 scale grestore
""" % strDefName)
        self.c.append(''.join(msg))

    #-----------------------------------------------------------------------||--     
    def gridText(self, x, y, anchor='nw', msg='test', font='micro', 
                fill='#ffffff', kernBit=1,
                vertBit=None, xMult=1, yMult=1, horizontal=1, charWrapWidth=None):
        """over-ride this method to provide font support wihtout using 
        bitmap; get anchor from normal gridText calls"""        
        # there will be a size that fits similar to a real gridText
        if font == 'micro':
            # keep case
            fontSize = 7 * yMult
            fontInfo = ('Courier', 'bold', fontSize)
        elif font == 'macro': # make caps
            msg = msg.upper()
            fontSize = 14 * yMult
            fontInfo = ('Courier', 'bold', fontSize)
        # will append to self.c
        self.fontText(x, y, anchor, msg, fontInfo, fill)


#     alternative method; but does not work properly 
#     def bitmap(self, xShift, yShift, gridData, color=None):
#         """if color==None, use data value in grid data as color value
#         """
#         pairL, pairR = self._convertCoordLine(xShift, yShift, xShift, yShift) 
#         pixSize = 1
#         strDefName = self._getDefName() # get a unique def identifier     
#         msg = []
#         msg.append("""
# /%s %s %s translate %s %s scale { 1 1 1 [1 0 0 1 0 0] {<c936>} image } def 
# """ % (strDefName, pairL[0], pairL[1], pixSize, pixSize)
#         )
#         msg.append("""
# gsave %s 1 1 scale grestore
# """ % strDefName)
#         self.c.append(''.join(msg))

    def bitmap(self, xShift, yShift, gridData, color=None):
        """this method draws rectangle for every bit; this works but is
        very slow"""
        x = 0
        y = 0
        for row in gridData:
            for col in row:
                if color != None:
                    if col == 0: # nothing here, and not a color value
                        colorUse = None # do not draw
                    else: # if 1, binary but mapp
                        colorUse = color
                elif color == None: # color not given, use values
                    colorUse = col
                if colorUse != None:
                    self.rectangle(xShift+x, yShift+y, xShift+x, yShift+y,
                                         colorUse, None, 0)
                    # capstyle may not be the same on differnt tks, must specify
                x = x + 1
            x = 0
            y = y + 1
        
    #-----------------------------------------------------------------------||--     
    
    def write(self, filePath=None, openMedia=1, prefDict=None):
        if filePath == None:
            #filePath = drawer.tempFile('.eps')    
            filePath = environment.getTempFile('.eps')           
        f = open(filePath, 'w')
        f.writelines(''.join(self.c) + self._tailStr())
        f.close
        if openMedia:
            osTools.openMedia(filePath, prefDict)            
        self.filePath = filePath

    def show(self, dir=None, prefDict=None):
        """show action is to write file"""
        if dir != None: # get path
            ext = '.eps'
            filePath = os.path.join(dir, drawer.tempFileName(ext))
        else:
            #filePath = drawer.tempFile('.eps') # jpg/png    
            filePath = environment.getTempFile('.eps')
        self.write(filePath, 1, prefDict)


#-----------------------------------------------------------------||||||||||||--
# factory returns an object
def Canvas(fmt, w, h, bg='#000000', name='image', master=None, transp=None):
    # this needs to be changed: jpg, png 
    if fmt in ['jpg','png']:
        obj = PilCanvas(w, h, bg, name, transp, fmt)
    elif fmt == 'tk':
        obj = TkCanvas(w, h, bg, name, master)
    elif fmt == 'eps':
        obj = EpsCanvas(w, h, bg, name)
    else:
        raise ValueError('bad canvas format type: %s' % fmt)
    return obj









#-----------------------------------------------------------------||||||||||||--
class ProcessGraphCoordData:
    """process data into a bit map data format
    assumes that data is set of numerical coordinants
    designed to process multiple streams of data, w/ same rez
    finds all real-world values w/n an integer space"""

    def __init__(self, dataLib=None, xRez=100, yRez=100, 
                             dataSigDig=(2,2), axisSigDig=(0,0),):
        """dataLib is a dictionary of (x,y) coordinants
        key is symbol to be used, value is a list of coords
        max and min are calculated based on data
        dataLib may contain four coords: (x,y,x,y) for rectangular segments
        """
        self.xRez = xRez
        self.yRez = yRez
        self.dataSigDig = dataSigDig
        self.axisSigDig = axisSigDig
        if dataLib != None:
            self.dataLib = dataLib
        else: # generate a random dataLib
            self.dataLib = {}
            self.dataLib[1] = []
            for x in range(1, 101): # fill w/ random values
                #self.dataLib[1].append((x, random.random()))
                self.dataLib[1].append((x, x, x+3, x))
        # check if these are 4-point coords
        if len(self.dataLib[1][0]) == 4:
            self.dataMode = 'line' # two coords
        else:
            self.dataMode = 'point' # one coord

    def _findRange(self):
        """find min, max x values
        check the data for anything that we cannot process
        like strings...
        """
        self.xRangeLib = {}
        self.yRangeLib = {}
        for key in list(self.dataLib.keys()):
            xMax = self.dataLib[key][0][0] # seed w/ values from data
            xMin = self.dataLib[key][0][0]
            yMax = self.dataLib[key][0][1]
            yMin = self.dataLib[key][0][1]          
            if self.dataMode == 'point':
                allPointList = self.dataLib[key]
            elif self.dataMode == 'line':
                allPointList = []
                for x, y, p, q in self.dataLib[key]:
                    allPointList.append((x,y)) # stack all pairs of coords
                    allPointList.append((p,q))
            else:
                raise ValueError
            for x, y in allPointList:
                if x >= xMax: xMax = x
                if x <= xMin: xMin = x
                if y >= yMax: yMax = y
                if y <= yMin: yMin = y
            # special case for constant values
            if xMax == xMin: # if the same
                xMax = xMax + 1
                xMin = xMin - 1
            if yMax == yMin: # if the same
                yMax = yMax + 1
                yMin = yMin - 1
            self.xRangeLib[key] = (xMin, xMax)
            self.yRangeLib[key] = (yMin, yMax)                  

    def _genAxis(self, min, max, steps, side):
        """reverses y axis, so returns from largest to smallest
        seems to be bug here, as max has to be manually added; is not
        reached through increment addition
        float axis values must have higher specificity than sigDig"""
        axis = []
        if side == 'x':
            sigDig = self.axisSigDig[0]
        elif side == 'y':
            sigDig = self.axisSigDig[1]
        
        if sigDig != 0:
            if drawer.isInt(min): rMin = min
            else: rMin = round(min, sigDig)
            if drawer.isInt(max): rMax = max              
            else: rMax = round(max, sigDig)
        else: # make into an int
            if not drawer.isInt(min):
                rMin = int(round(min, sigDig))
            else: rMin = min
            if not drawer.isInt(max):
                rMax = int(round(max, sigDig))
            else: rMax = max

        incRaw = float(abs(rMax - rMin)) / (steps)
        if sigDig != 0:
            inc = round(incRaw, sigDig+4) # add extra resolution
        else:
            inc = int(round(incRaw, sigDig))

        axis.append(rMin) # add first
        i = copy.copy(rMin)
        for x in range(1, steps-1): # first already added, last to be added
            i = i + inc
            axis.append(i)
        axis.append(rMax) # add first

        if side == 'y': # y should go from higher to lower
            axis.reverse()
        #print _MOD, min, max, rMin, rMax, axis, len(axis)
        return axis

    def _findAxis(self):
        self.xAxisLib = {}
        self.yAxisLib = {}
        for key in list(self.dataLib.keys()):
            self.xAxisLib[key] = self._genAxis(self.xRangeLib[key][0], 
                                        self.xRangeLib[key][1], self.xRez, 'x')
            self.yAxisLib[key] = self._genAxis(self.yRangeLib[key][0], 
                                        self.yRangeLib[key][1], self.yRez, 'y')

    def _findIndexInAxis(self, axis, value, side):
        """given an axis, value, and side, determine which point
        on the axis the value should be assigned to
        axis are already rounded"""
        # round value w/ data from sigDig local attribute
        # for sig dig, x is 0, y is 1
        if side == 'x':
            value = round(value, self.dataSigDig[0])
        elif side == 'y':
            value = round(value, self.dataSigDig[1])
        else:
            raise ValueError

        for i in range(0, len(axis)):
            if side == 'x':
                if value == axis[i]:
                    return i
                elif i >= len(axis) - 1: # the last point of axis
                    return i
                elif value > axis[i] and value < axis[i+1]:
                    lower = abs(value - axis[i])
                    upper = abs(value - axis[i+1])
                    if lower < upper: # closer to lower:
                        return i
                    elif upper < lower: # closer to upper
                        return i + 1
                    elif upper == lower: # equal?
                        return i # round to lower?
                    else: print(_MOD, 'x error')
            elif side == 'y': # greater to lesser values
                if value == axis[i]:
                    return i
                elif i >= len(axis) - 1: # the last point of axis
                    return i
                elif value < axis[i] and value > axis[i+1]:
                    lower = abs(value - axis[i])
                    upper = abs(value - axis[i+1])
                    if lower < upper: # closer to lower:
                        return i
                    elif upper < lower: # closer to upper
                        return i + 1
                    elif upper == lower: # equal?
                        return i # round to lower?
                    else: print(_MOD, 'y error')

    def _findPlot(self):
        """create a bit map based on resolution
        this used to store a double array of e entire but map
        now this converts the floating point values into integer values
        within the defined resultion
        these values are stored in self.plotLib; provide additional
        method to get values out in old format"""
        self.plotLib = [] # used to be a dictionary
        # each key represents a color/symbol/fill-pattern group
        for key in list(self.dataLib.keys()):
            for data in self.dataLib[key]:
                if self.dataMode == 'point':
                    x, y = data
                    # determine which axis position this point is closer to?
                    xPos = self._findIndexInAxis(self.xAxisLib[key], x, 'x')
                    yPos = self._findIndexInAxis(self.yAxisLib[key], y, 'y')
                    #self.plotLib[key][yPos][xPos] = key # key is symbol in this pos
                    self.plotLib.append((key, xPos, yPos))
                    #print _MOD, x, y, xSig, ySig, xPos, yPos
                elif self.dataMode == 'line':
                    x1, y1, x2, y2 = data
                    x1Pos = self._findIndexInAxis(self.xAxisLib[key], x1, 'x')
                    y1Pos = self._findIndexInAxis(self.yAxisLib[key], y1, 'y')
                    x2Pos = self._findIndexInAxis(self.xAxisLib[key], x2, 'x')
                    y2Pos = self._findIndexInAxis(self.yAxisLib[key], y2, 'y')
                    #self.plotLib[key][yPos][xPos] = key # key is symbol in this pos
                    self.plotLib.append((key, x1Pos, y1Pos, x2Pos, y2Pos))
                else:
                    raise ValueError
                    
    def getBitLib(self):
        """after calling _findPlt aboive, this method will convert self.plotLib
        into an old format bit-map, a list of nested lists, w/ each value in 
        the list being the integer value of the necessary key/fromat/colo 
        indicator
        this may be very inefficient; only use if abs necessary
        """
        self.bitLib = {} # this is like the old plotLib format
        # build empty double array
        for key in list(self.dataLib.keys()):
            self.bitLib[key] = []
            for y in range(self.yRez): # replace w/ array?
                row = array.array('i')
                for x in range(self.xRez):
                    row.append(0) # fill with zeros
                self.bitLib[key].append(row)
        # fill w/ key, non-zero values
        for data in self.plotLib: # plotLib is a list now
            if self.dataMode == 'point':
                key, x, y = data
                # y comes before x because of nested lists
                self.bitLib[key][y][x] = key
            elif self.dataMode == 'line': # this is likely not used for line graphs
                # connect points b/n lines
                key, x1, y1, x2, y2 = data
                # just store first point
                self.bitLib[key][y1][x1] = key
            else:
                raise ValueError
        #print self.bitLib
        return self.bitLib
                
    def getPlotLib(self):
        """plotlib is a raw data point value list
        leading values are id symbols (ints0
        than any number of xy pairs"""
        return self.plotLib
    
    def keys(self):
        return list(self.dataLib.keys())
    
    def gridKey(self, key, side='x', lines=3):
        """returns a grid key for this axis
        lines are number of lines, not number of spaces
        NOT reversed for y axis"""
        if side == 'y':
            axis = self.yAxisLib[key]
        else:
            axis = self.xAxisLib[key]
        gridKey = [0] * len(axis)
        partitions = lines + 1
        step = int(round((len(axis) / float(partitions)), 0))
        pos = 0
        for i in range(0, lines): # always one less
            pos = pos + step
            #print _MOD, pos, i, lines, len(gridKey)
            if pos < len(gridKey):
                gridKey[pos] = 1 # indicate grid line w/ 1
            else:
                pass 
                #print _MOD, 'grid (%s:%s) line out of range' % (side, lines)
        if side == 'y':
            gridKey.reverse() # must reverse y axis
        return gridKey

    def unitKey(self, key, side, gridKey, forceExtreme='min'):
        """uses grid key to get a unit key (label each grid)
        fore range adds first and last values
        axis values are not rounded; need to be for units"""
        if side == 'x':
            sigDig = self.axisSigDig[0]
        elif side == 'y':
            sigDig = self.axisSigDig[1]

        if side == 'y':
            axis = self.yAxisLib[key] # alrady reversed
        else:
            axis = self.xAxisLib[key]
        unitKey = [None] * len(axis)
        for i in range(0, len(axis)):
            if gridKey[i] > 0: # if grid active
                if sigDig != 0:
                    unitKey[i] = round(axis[i], sigDig)
                else:
                    unitKey[i] = int(round(axis[i], sigDig))
        if side == 'x':
            if forceExtreme in ['min', 'range']:
                if sigDig != 0:
                    unitKey[0] = round(axis[0], sigDig)
                else:
                    unitKey[0] = int(round(axis[0], sigDig))
            if forceExtreme in ['max','range']:
                j = len(axis) - 1 # last value
                if sigDig != 0:
                    unitKey[j] = round(axis[j], sigDig)
                else:
                    unitKey[j] = int(round(axis[j], sigDig))
        if side == 'y':
            if forceExtreme in ['min', 'range']:
                j = len(axis) - 1 # last value
                if sigDig != 0:
                    unitKey[j] = round(axis[j], sigDig)
                else:
                    unitKey[j] = int(round(axis[j], sigDig))
            if forceExtreme in ['max','range']:
                if sigDig != 0:
                    unitKey[0] = round(axis[0], sigDig)
                else:
                    unitKey[0] = int(round(axis[0], sigDig))
        return unitKey

    def __call__(self):
        self._findRange()
        self._findAxis()
        self._findPlot()
        #self.display()






#-----------------------------------------------------------------||||||||||||--
class _GraphBase:
    def __init__(self, xRez, yRez, plotLib, origin=(0,0)):
        """canvas is only provided through update method
        only call update once after setting parameters
        xRez and yRez are integer resolution sizes (w/h of a bit map)
        plotLib is a list of points, each a list: key, x, y, x, y
        """
        # self.bitData
        self.plotLib = plotLib
        self.xRez = xRez
        self.yRez = yRez
        
        self.xOrigin, self.yOrigin = origin
        self.master = None
        # cells must be an odd number (so that there is a center
        self.wIcon = 9
        self.hIcon = 9
        # widht of horizontal and vertical margins
        # applied to one side
        self.wIconGutter = 18
        self.hIconGutter = 18

        self.lMargin = 40 # left
        self.rMargin = 2     # right
        self.tMargin = 2     # top  
        self.bMargin = 40    # bottom

        #grid binary key for each angle: determines if grid line is drawn
        # may want to add other symbols for variation
        self.rowGridKey = [0,1,1]
        self.colGridKey = [0,1,0,1]

        #ticks extend into margin, separate color
        # value determines length
        # NB: problem w/ 1 pixel horizontal ticks
        self.lTickKey = [1,5,2]   # left
        self.rTickKey = [2,1] # right
        self.tTickKey = [2,1,2,0] # top 
        self.bTickKey = [3,1,1,4] # bottom

        # give string for each necessary unit marker
        # None translated to no unit
        self.colUnitKey = ['a', 'b', 'c', None, 3, 4, 5]
        self.rowUnitKey = ['a', 'b', 'c', None, 3, 4, 5]
        self.unitGutter = 2 # pixel spacing from tick mark, or edge if none

        # labels for x y axis
        self.xLabel = 'events'
        self.yLabel = 'db'
        self.labelGutter = 6 # pixels spaciing from unit gutter +tick

        # colors
        self.colorBkg     = '#000000'
        self.colorGrid    = '#000033'
        self.colorTick    = '#CC6600'
        self.colorMargin = '#333333'
        self.colorUnits  = '#333399'
        self.colorLabel  = '#000000'
        self.colorTitle  = '#333333'

        self.bitColorDict = {1 : '#336633',
                                    2 : '#003366',
                                    3 : '#003366', }
        self.transp = None # transparancy default off, passed to canvas
        # stores methods for drawing icons
        self.bitDict = {}

        self.font = 'micro'
        self.kernEqual = 0
        self.kernBit = 1
        self.title = ''
        self.titlePos = 'bl' # pick a corner, bottom left here
        self.titleGutterVert = 2 # pix from vertical edges
        self.titleGutterHorz = 2 # pix from horiz edges
        # update values
        # self.update(canvas)

    def update(self, canvas='png'):
        """ canvas can be an object or format string
        update all calculated size values
        regenerates Canvas, and this bkg color and self.tranp make a dif
        must be done manually from out side object after loading all necessary
        data formats
        if canvas is == None, does not create a canvas, just calc values"""
        # size of data
        self.graphCol = self.xRez
        self.graphRow = self.yRez
        # width of graph = icon width, and margins plus 1
        self.wGraph = ((self.wIcon * self.graphCol) + 
                            (self.wIconGutter * (self.graphCol + 1)))
        self.hGraph = ((self.hIcon * self.graphRow) + 
                            (self.hIconGutter * (self.graphRow + 1)))
        #print _MOD, self.wGraph, self.hGraph, self.graphCol, self.graphRow
        self.wTotal = self.wGraph + (self.lMargin + self.rMargin)
        self.hTotal = self.hGraph + (self.tMargin + self.bMargin)
        # create canvas if given a string, othewise use existing canvas
        if drawer.isStr(canvas): # its a format string
            self.fmt = canvas
            self.canvas = Canvas(self.fmt, self.wTotal, self.hTotal, 
                              self.colorBkg, 'graph', self.master, self.transp)
        elif canvas != None: # its canvas already
            self.fmt = canvas.fmt
            self.canvas = canvas
        else: # used only to calculate size
            self.canvas = None
        # upper left corner of where graph starts
        self.graphOrigin = (self.xOrigin+self.lMargin, self.yOrigin+self.tMargin)

        if self.canvas != None:
            self.canvas.rectangle(self.xOrigin, self.yOrigin, 
                          self.xOrigin+self.wTotal-1, self.yOrigin+self.hTotal-1,
                          self.colorBkg, None)
        # create dumy char to measure size
        obj = fontLibrary.FontBitMap('a', self.font)
        self.wFont = obj.wFont
        self.hFont = obj.hFont

    def destroy(self):
        """useful for tk windows only"""
        self.canvas.destroy()
        del self.canvas

    #-----------------------------------------------------------------------||--
    def setIconSize(self, wIcon, hIcon, wIconGutter, hIconGutter):
        # reinit w/ the format string, not w/ the canvas
        self.wIcon = wIcon
        self.hIcon = hIcon
        self.wIconGutter = wIconGutter
        self.hIconGutter = hIconGutter

    def setMargin(self, lMargin, rMargin, tMargin, bMargin):
        self.lMargin = lMargin
        self.rMargin = rMargin
        self.tMargin = tMargin
        self.bMargin = bMargin

    def setLabel(self, xLabel, yLabel, labelGutter):
        self.xLabel = xLabel
        self.yLabel = yLabel
        self.labelGutter = labelGutter # must include any unit size

    def setGrid(self, rowGridKey, colGridKey, rowUnitKey, colUnitKey):
        self.rowGridKey = rowGridKey
        self.colGridKey = colGridKey
        self.rowUnitKey = rowUnitKey
        self.colUnitKey = colUnitKey

    def setTitle(self, title, titlePos='br', 
                     titleGutterVert=2, titleGutterHorz=None):
        self.title = title
        self.titlePos = titlePos
        self.titleGutterVert = titleGutterVert
        if titleGutterHorz != None:
            self.titleGutterHorz = titleGutterHorz
        else: # make same as vert
            self.titleGutterHorz = titleGutterVert
        # no update necessary

    def setColors(self, bkg, grid, tick, margin, units, label, title,
                      bitColorDict):
        self.colorBkg = bkg
        self.colorGrid = grid
        self.colorTick = tick
        self.colorMargin = margin
        self.colorUnits = units
        self.colorLabel = label
        self.colorTitle = title
        self.bitColorDict = bitColorDict
        # no update necessary

    #-----------------------------------------------------------------------||--
    def _iconA(self, args):
        # x and y do not include margin; are icon's upper left and right corner
        # if x1 == x2, this is a width of 1 (in a bit map relm)
        x, y = args
        if self.hIcon == 1: # draw a line
            self.canvas.rectangle(x, y, x+self.wIcon-1, y,
                                     self.bitColorDict[1], None, 0)
            #self.canvas.line(x, y, x+self.wIcon, y, color, None, 1)
        else:
            self.canvas.rectangle(x, y, x+self.wIcon-1, y+self.hIcon-1,
                                     self.bitColorDict[1], None, 0)
    def _iconB(self, args):
        x, y = args
        self.canvas.rectangle(x, y, x+self.wIcon-1, y+self.hIcon-1,
                                     self.bitColorDict[2], None, 1)
    def _iconC(self, args):
        x, y = args
        self.canvas.rectangle(x, y, x+self.wIcon-1, y+self.hIcon-1,
                                     self.bitColorDict[3], None, 0)
                                     
    def _updateBitDict(self):
        self.bitDict = {1 : '_iconA',
                             2 : '_iconB',
                             3 : '_iconC',
                            } # map integers to icon methods


    #-----------------------------------------------------------------------||--
    def _drawMargin(self):
        # draw top
        if self.tMargin != 0:
            self.canvas.rectangle(self.xOrigin, self.yOrigin, 
                         self.wTotal+self.xOrigin-1, self.yOrigin+self.tMargin-1, 
                         self.colorMargin, None, 0)
        # draw left
        if self.lMargin != 0:
            self.canvas.rectangle(self.xOrigin, self.yOrigin,
                          self.xOrigin+self.lMargin-1, self.yOrigin+self.hTotal-1, 
                          self.colorMargin, None, 0)
        # draw right
        if self.rMargin != 0:
            self.canvas.rectangle((self.xOrigin+self.lMargin+self.wGraph),
                                         self.yOrigin, 
                            self.wTotal+self.xOrigin-1, self.yOrigin+self.hTotal-1, 
                            self.colorMargin, None, 0)
        # draw bottom
        if self.bMargin != 0:
            self.canvas.rectangle(self.xOrigin, 
                                        (self.yOrigin+self.tMargin+self.hGraph), 
                         self.wTotal+self.xOrigin-1, self.hTotal+self.yOrigin-1, 
                         self.colorMargin, None, 0)


    #-----------------------------------------------------------------------||--
    def _yGraphPosList(self):
        """gets a list of all necessary graph positions
        these are absoult points based on origin values
        gets real x/y points as integers?"""
        points = []
        x = copy.copy(self.graphOrigin[0])
        y = copy.copy(self.graphOrigin[1])
        i = 0
        for row in range(self.yRez):
            y = y + self.hIconGutter # upper left of icon
            yPos = y + (self.hIcon/2) # center of icon
            points.append((x, y, yPos, i)) # add data
            # incr data
            y = y + self.hIcon
            i = i + 1
        return points

    def _xGraphPosList(self):
        """gets a list of all necessary graph positions
        values are in pixels"""
        points = []
        x = copy.copy(self.graphOrigin[0])
        y = copy.copy(self.graphOrigin[1])
        j = 0
        for col in range(self.xRez): # read col events from first row of data
            x = x + self.wIconGutter
            xPos = x + (self.wIcon/2)
            points.append((x, y, xPos, j)) # add data
            # incr data
            x = x + self.wIcon
            j = j + 1 # j is an index of values
        #print _MOD, 'xGraphPosList', points
        return points

    #-----------------------------------------------------------------------||--
    def _drawGrid(self):
        """to deal with error, add to length of horizontal grid"""
        if self.rowGridKey != []:
            for x, y, yPos, i in self._yGraphPosList():
                if self.rowGridKey[i % len(self.rowGridKey)] != 0:
                    # x was reduced by one to account for some error
                    # this introduced another off by one error in the vector version
                    # not backgrounded to try to remove problems
                    self.canvas.line(x, yPos, x+self.wGraph, yPos, self.colorGrid)
                    #self.canvas.line(x-1, yPos, x+self.wGraph, 
                    #                     yPos, self.colorGrid)
        if self.colGridKey != []:
            for x, y, xPos, j in self._xGraphPosList():
                if self.colGridKey[j % len(self.colGridKey)] != 0: 
                    # pre vector version
                    self.canvas.line(xPos, y, xPos, y+self.hGraph, self.colorGrid)
                    #self.canvas.line(xPos, y-1, xPos, y+self.hGraph, self.colorGrid)

    def _drawTick(self):
        for x, y, yPos, i in self._yGraphPosList():
            # do left
            if self.lTickKey != []: # not empty
                pix = self.lTickKey[i % len(self.lTickKey)]
                if pix != 0:
                    self.canvas.line(x-pix, yPos, 
                                          x-1, yPos, self.colorTick)
            # do right
            if self.rTickKey != []: # not empty
                pix = self.rTickKey[i % len(self.rTickKey)]
                if pix != 0:
                    self.canvas.line(x+self.wGraph, yPos, 
                                  x+self.wGraph+pix-1, yPos, self.colorTick)

        for x, y, xPos, j in self._xGraphPosList():
            # do bottom
            if self.bTickKey != []: # not empty
                pix =    self.bTickKey[j % len(self.bTickKey)]
                if pix != 0:    
                    self.canvas.line(xPos, y + self.hGraph, 
                                          xPos, y + self.hGraph + pix, self.colorTick)
            # do top
            if self.tTickKey != []: # not empty
                pix = self.tTickKey[j % len(self.tTickKey)]
                if pix != 0:    
                    self.canvas.line(xPos, y-pix, 
                                          xPos, y, self.colorTick)

    def _getUnitGutter(self, side):
        if side in ['col', 'b', 'x']:
            tick = self.bTickKey
        elif side in ['row', 'l', 'y']:
            tick = self.lTickKey
        max = 0
        for pix in tick:
            if pix >= max:
                max = pix
        return max + self.unitGutter

    def _drawUnits(self):
        """draw units on grid line spacings
        """
        rowGutter = self._getUnitGutter('row')
        colGutter = self._getUnitGutter('col')
        #self.yUnitMaxShift = 0
        self.yUnitOuterIndex = self.yRez #len(self.bitData)
        if self.rowUnitKey != []:
            for x, y, yPos, i in self._yGraphPosList():
                char = self.rowUnitKey[i % len(self.rowUnitKey)]
                if char != None: # should be 'ce'
                    self.canvas.gridText(x-rowGutter, yPos, 'ce', str(char), 
                        self.font, self.colorUnits, self.kernBit)
                    if i <= self.yUnitOuterIndex:
                        self.yUnitOuterIndex = i
        #self.xUnitMaxShift = 0
        self.xUnitOuterIndex = 0
        if self.colUnitKey != []:
            for x, y, xPos, j in self._xGraphPosList():
                char = self.colUnitKey[j % len(self.colUnitKey)]
                if char != None:    
                    self.canvas.gridText(xPos, y+self.hGraph+colGutter, 'nc', 
                        str(char), self.font, self.colorUnits, self.kernBit)
                    if j >= self.xUnitOuterIndex:
                        self.xUnitOuterIndex = j

    def _getLabelGutter(self, side):
        if side == 'col' or side == 'b' or side == 'x':
            tick = self.bTickKey
            #fontShift = self.hFont # need only char height here
        elif side == 'row' or side == 'l' or side == 'y':
            tick = self.lTickKey
            #fontShift = self.yUnitMaxShift # need max word length, not char
        max = 0 # get tick size
        for pix in tick:
            if pix >= max:
                max = pix
        return max + self.unitGutter + self.labelGutter #+ fontShift

    def _drawLabels(self):
        # these values may no be incorrect; double check
        rowGutter = self._getLabelGutter('row')
        colGutter = self._getLabelGutter('col')     
        if self.yLabel != '':
            for x, y, yPos, i in self._yGraphPosList():
                if i == self.yUnitOuterIndex: # 0 gets first first
                    # used to be center of y; now use north anchor
                    self.canvas.gridText(x-rowGutter, yPos, 'ce', self.yLabel, 
                        self.font, self.colorLabel, self.kernBit)
                    break                     
        if self.xLabel != '':
            for x, y, xPos, j in self._xGraphPosList():
                if j == self.xUnitOuterIndex: #len(self.bitData[0]) - 1: # 
                    self.canvas.gridText(xPos, y+self.hGraph+colGutter,
                        'ne', self.xLabel, self.font, self.colorLabel, self.kernBit)
                    break

    def _drawTitle(self):
        if self.title == '': return None # bail 
        x = copy.copy(self.xOrigin)
        y = copy.copy(self.yOrigin)
        xPos = x
        yPos = y
        # can be 'bl' or 'rt' or the like
        if 'b' in self.titlePos:
            #yPos = y + self.hTotal - hText - self.titleGutterVert
            yPos = (y + self.hTotal) - self.titleGutterVert
            anchorVertical = 's'
        if 'l' in self.titlePos:
            xPos = x + self.titleGutterHorz
            anchorHorizontal = 'w'
        if 'r' in self.titlePos:
            #xPos = x + self.wTotal - (wText + self.titleGutterHorz)
            xPos = x + self.wTotal - self.titleGutterHorz
            anchorHorizontal = 'e'
        if 't' in self.titlePos:
            #yPos = y + hText + self.titleGutterVert
            yPos = y + self.titleGutterVert
            anchorVertical = 'n'
        anchor = anchorVertical + anchorHorizontal # combine anchor notation
        self.canvas.gridText(xPos, yPos, anchor, self.title, 
            self.font, self.colorTitle, self.kernBit)
        #self.canvas.bitmap(xPos, yPos, gridData, self.colorTitle)

    #-----------------------------------------------------------------------||--
    def _xGridToPixel(self, xRaw):
        """returns upper left corner for an integer grid bit map
        translated into pixel positions"""
        # always a margin (at 0) so add 1
        # no width at zero, so leave as is
        x = (self.graphOrigin[0] + ((xRaw + 1) * self.wIconGutter) +
              (xRaw * self.wIcon))
        return x

    def _yGridToPixel(self, yRaw):
        """returns upper left corner for an integer grid bit map
        translated into pixel positions"""
        # always a margin (at 0) so add 1
        # no width at zero, so leave as is
        y = (self.graphOrigin[1] + ((yRaw + 1) * self.hIconGutter) +
              (yRaw * self.hIcon))
        return y

# old version did things in order
#     def _drawIcon(self):
#         """draw each icon
#         point based to icon method is the upper left point"""
#         x = copy.copy(self.graphOrigin[0])
#         y = copy.copy(self.graphOrigin[1])
#         for row in self.bitData:
#             y = y + self.hIconGutter
#             for col in row:
#                 x = x + self.wIconGutter
#                 if col != 0:
#                     meth = getattr(self, self.bitDict[col])
#                     meth((x, y))
#                 x = x + self.wIcon
#             # reset x
#             x = copy.copy(self.graphOrigin[0])
#             # add horizontal 
#             y = y + self.hIcon

    def _drawIcon(self):
        """alternative method: just look at data points, calc shift and pos"""
        for data in self.plotLib:
            if len(data) == 3:
                # three element data points are used for point graphs
                key, xRaw, yRaw = data # these are raw data points, starting from 0
                x = self._xGridToPixel(xRaw)
                y = self._yGridToPixel(yRaw)
                args = (x,y)
            elif len(data) == 5: 
                # 5 element args used for bar graphs
                key, x1Raw, y1Raw, x2Raw, y2Raw = data 
                x1 = self._xGridToPixel(x1Raw)
                y1 = self._yGridToPixel(y1Raw)
                x2 = self._xGridToPixel(x2Raw)
                y2 = self._yGridToPixel(y2Raw)

                # use raw integer x values to get widht, tn convert to pixel
                widthStep = x2Raw-x1Raw # number of 'cells' to span 
                width = ((widthStep * self.wIcon) + 
                          ((widthStep+1) * self.wIconGutter)) # one more gutter 
                args = (x1, y1, x1+width, y1)
            
            meth = getattr(self, self.bitDict[key])
            meth(args)


    #-----------------------------------------------------------------------||--
    def draw(self):
        self._updateBitDict()
        self._drawGrid() # covers horizontal error introduced for vector version
        self._drawMargin()
        self._drawTick()
        self._drawUnits()
        self._drawIcon()
        self._drawLabels()
        self._drawTitle()

    def show(self, dir=None, prefDict=None):
        """some canvases use show to write files; a dir can be provided
        to use w/ automatically generated files names"""
        self.canvas.show(dir, prefDict)

    def write(self, filePath=None):
        """Saves the Image; .png and .jpg both work; format based on extensions
        None automatically gets a temp file name"""
        self.canvas.write(filePath)
        self.filePath = self.canvas.filePath # get from lower canvas


#-----------------------------------------------------------------||||||||||||--
class NumericalPointGraph(_GraphBase):
    """this graph is designed for points on a lone
    it assumes a fixed icon size
    this graph is used for TImap and TPmap displays"""
    def __init__(self, dataObj=None, origin=(0,0)):
    
        groupKey = list(dataObj.keys())[0] # take first key, will be 1
        # graph base wants a bit-map of enter data to be written
        _GraphBase.__init__(self, dataObj.xRez, dataObj.yRez, 
                                  dataObj.getPlotLib(), origin)
        # set preferences

        # cells must be an odd number (so that there is a center
        self.wIcon = 3
        self.hIcon = 3
        # widht of horizontal and vertical margins
        # applied to one sides
        self.wIconGutter = 0
        self.hIconGutter = 0

        self.lMargin = 60 # left
        self.rMargin = 1     # right
        self.tMargin = 1     # top  
        self.bMargin = 60    # bottom

        #grid binary key for each angle: determines if grid line is drawn
        # may want to add other symbols for variation
        self.rowGridKey = dataObj.gridKey(groupKey, 'y', 8)
        self.colGridKey = dataObj.gridKey(groupKey, 'x', 8)

        #ticks extend into margin, separate color
        # value determines length
        # NB: problem w/ 1 pixel horizontal ticks
        self.lTickKey = []  # left
        self.rTickKey = [] # right
        self.tTickKey = [] # top 
        self.bTickKey = [] # bottom

        # give string for each necessary unit marker
        # None translated to no unit
        self.rowUnitKey = dataObj.unitKey(groupKey, 'y', self.rowGridKey)
        self.colUnitKey = dataObj.unitKey(groupKey, 'x', self.colGridKey)
        self.unitGutter = 2 # pixel spacing from tick mark, or edge if none

        # labels for x y axis
        self.xLabel = 'x'
        self.yLabel = 'y'
        self.labelGutter = 4 # pixels spaciing from unit+tick

        # colors
        self.colorBkg   = '#000000'
        self.colorGrid = '#333333'
        self.colorTick = "#CC6600"
        self.colorMargin = '#333333'
        self.colorUnits  = '#333399'
        self.colorLabel  = '#000000'
        self.bitColorDict = {1 : '#aaaaaa',}

        # update calculated values

    def _iconA(self, args):
        x, y = args
        # x and y do not include margin; are icon's upper left and right corner
        self.canvas.rectangle(x, y, x+self.wIcon-1, y+self.hIcon-1,
                                     self.bitColorDict[1], None, 0)

    def _iconB(self, args):
        x, y = args
        # x and y do not include margin; are icon's upper left and right corner
        self.canvas.rectangle(x, y, x+self.wIcon-1, y+self.hIcon-1,
                                     self.bitColorDict[2], None, 0)

    def _updateBitDict(self):
        self.bitDict = {1 : '_iconA',
                             2 : '_iconB',
                            } # map integers to icon methods

#-----------------------------------------------------------------||||||||||||--
class NumericalBarGraph(_GraphBase):
    """this graph is designed for points on a lone
    it assumes a fixed icon size
    this graph is used for TImap and TPmap displays
    dataObj is a raw dictionary of values organized by symbol (all are 1 for 
    now; may be real-value x,y pairs or x,y,x,y quads"""
    def __init__(self, dataObj=None, origin=(0,0)):
    
        groupKey = list(dataObj.keys())[0] # take first key, will be 1
        # will assign self.plotLib
        _GraphBase.__init__(self, dataObj.xRez, dataObj.yRez, 
                                  dataObj.getPlotLib(), origin)
        # set preferences

        # cells must be an odd number (so that there is a center
        self.wIcon = 3 # used for relative grid size
        self.hIcon = 3
        # widht of horizontal and vertical margins
        # applied to one sides
        self.wIconGutter = 0
        self.hIconGutter = 0

        self.lMargin = 60 # left
        self.rMargin = 1     # right
        self.tMargin = 1     # top  
        self.bMargin = 60    # bottom

        #grid binary key for each angle: determines if grid line is drawn
        # may want to add other symbols for variation
        self.rowGridKey = dataObj.gridKey(groupKey, 'y', 8)
        self.colGridKey = dataObj.gridKey(groupKey, 'x', 8)

        #ticks extend into margin, separate color
        # value determines length
        # NB: problem w/ 1 pixel horizontal ticks
        self.lTickKey = []  # left
        self.rTickKey = [] # right
        self.tTickKey = [] # top 
        self.bTickKey = [] # bottom

        # give string for each necessary unit marker
        # None translated to no unit
        self.rowUnitKey = dataObj.unitKey(groupKey, 'y', self.rowGridKey)
        self.colUnitKey = dataObj.unitKey(groupKey, 'x', self.colGridKey)
        self.unitGutter = 2 # pixel spacing from tick mark, or edge if none

        # labels for x y axis
        self.xLabel = 'x'
        self.yLabel = 'y'
        self.labelGutter = 4 # pixels spaciing from unit+tick

        # colors
        self.colorBkg   = '#000000'
        self.colorGrid = '#333333'
        self.colorTick = "#CC6600"
        self.colorMargin = '#333333'
        self.colorUnits  = '#333399'
        self.colorLabel  = '#000000'

        self.bitColorDict = {1 : '#aaaaaa',
                                    }
        # update calculated values

    def _iconA(self, args):
        x1, y1, x2, y2 = args
        # x and y do not include margin; are icon's upper left and right
        # corner
        # x2+self.wIcon-1
        self.canvas.rectangle(x1, y1, x2-1, y2+self.hIcon-1,
                                     self.bitColorDict[1], None, 0)

    def _iconB(self, args):
        x1, y1, x2, y2 = args
        self.canvas.rectangle(x1, y1, x2-1, y2+self.hIcon-1,
                                     self.bitColorDict[2], None, 0)


    def _updateBitDict(self):
        self.bitDict = {1 : '_iconA',
                             2 : '_iconB',
                            } # map integers to icon methods




#-----------------------------------------------------------------||||||||||||--
class TextGraph(_GraphBase):
    """create text in a graph 
    same interface as GridText object"""
    def __init__(self, msg=None, fg='#666633', style='dotMediumA',   
                     backColor=None,
                     font='micro', kernBit=1, vertBit=None, charWrapWidth=None):
        if msg == None:
            msg = 'algorithmic.net'
        # process data
        obj = fontLibrary.FontBitMap(msg, font, 0, kernBit, 
                vertBit, charWrapWidth)
        gridData = obj.encode()
        gridData = self._addNoise(gridData)
        xRez, yRez, plotLib = self._gridToPlotLib(gridData)
        # call base class
        canvas ='png'
        _GraphBase.__init__(self, xRez, yRez, plotLib)
        # set preferences

        # cells must be an odd number (so that there is a center
        self.wIcon = 2
        self.hIcon = 1
        # widht of horizontal and vertical margins
        # applied to one sides
        self.wIconGutter = 1
        self.hIconGutter = 1
        #grid binary key for each angle: determines if grid line is drawn
        # may want to add other symbols for variation
        self.rowGridKey = []
        self.colGridKey = []
        # colors
        self.colorBkg   = '#000000'
        self.colorGrid = '#333333'
        self.colorTick = "#CC6600"
        self.colorMargin = '#333333'
        self.colorUnits  = '#333399'
        self.colorLabel  = '#000000'

        self.bitColorDict = {1 : fg,
                                    2 : fg,
                                    }
        # other image settings
        self.transp = 1

        # not used so much in font
        self.lTickKey = []  # left
        self.rTickKey = [] # right
        self.tTickKey = [] # top 
        self.bTickKey = [] # bottom
        self.lMargin = 0 # left
        self.rMargin = 0     # right
        self.tMargin = 0     # top  
        self.bMargin = 0    # bottom
        # give string for each necessary unit marker
        # None translated to no unit
        self.rowUnitKey = []
        self.colUnitKey = []
        self.unitGutter = 2 # pixel spacing from tick mark, or edge if none
        # labels for x y axis
        self.xLabel = ''
        self.yLabel = ''
        self.labelGutter = 4 # pixels spaciing from unit+tick
        # update calculated values
        self.update(canvas)

    def _gridToPlotLib(self, gridData):
        """translate a full bit-map grid into a plotLib"""
        plotLib = []
        for row in range(len(gridData)):
            for col in range(len(gridData[0])):
                key = gridData[row][col]
                if key == 0: pass
                plotLib.append((key, col, row))
        yRez = len(gridData)
        xRez = len(gridData[0])
        return xRez, yRez, plotLib

    def _addNoise(self, gridData, distribution=[1,1,1,1,1,2]):
        for row in range(len(gridData)):
            for col in range(len(gridData[0])):
                if gridData[row][col] == 0:
                    pass
                else:
                    gridData[row][col] = random.choice(distribution)
        return gridData

    def _iconA(self, args):
        x, y = args   
        # x and y do not include margin; are icon's upper left and right
        # corner
        self.canvas.rectangle(x, y, x+self.wIcon-1, y+self.hIcon-1,
                                     self.bitColorDict[1], None, 1)

    def _iconB(self, args):
        x, y = args
        self.canvas.rectangle(x, y, x+self.wIcon-1, y+self.hIcon-1,
                                     self.bitColorDict[2], None, 1)









#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--

class TestOld:
    def __init__(self):
        self.testGraph()
        self.testGraphText()
        self.testCanvas()
        self.testProcGraphCoord()
        
    def testBarCode(self):
        bg = '#000000'
        fg = ['#666633','#333366', '#336633']
        a = BarCode(None, 50, fg, bg, 1, 50, 1)
        a.show()

    def testText(self):
        bg = '#000000'
        fg = ['#666633','#333366', '#336633']
        #a = TextWebTitle('testingTESTNGIN', '#333366', 'algoNetLarge')
        #a = TextWebTitle('testingTESTNGIN', '#333366', 'algoNetSmall')
        a = GridText('testing a long sample of text!', fg, bg, 'micro', 6, None,
                         2, 2, 1, 10)
        a.show()

    def testCanvas(self):
        fmtList = ['tk', 'png', 'eps']
        import time
        for fmt in fmtList:
            print(_MOD, 'testing format', fmt)
            a = Canvas(fmt, 200, 200)
            a.rectangle(10, 10, 120, 120, '#333333', '#ffffff', 5)
            a.rectangle(150, 150, 180, 180, None, '#ffffff', 2)
            a.line(10, 130, 200, 130, '#663399', 3)
            a.line(10, 180, 10, 200, '#663399', 1)            
            a.oval(50, 50, 150, 150, '#999933', '#cccccc', 3)
            a.oval(75, 75, 125, 125, '#99ff33', None, 0)
            a.oval(90, 90, 110, 110, None, '#ff3333', 1)
            
            a.line(0, 100, 200, 100, '#999999', .25)
            a.line(100, 0, 100, 200, '#999999', .25)
            # problem case
            a.line(0, 200, 200, 0, '#999999', .25)

            a.gridText(0, 0, 'nw', 'testing some large text', 'micro', 
                '#33ff99', 2)
            a.gridText(20, 180, 'nw', 'a big title', 'macro', '#cccc33',  2)

            a.gridText(100, 100, 'ne', 'northEast', 'micro', '#000000')
            a.gridText(100, 100, 'nw', 'northWest', 'micro', '#333333')
            a.gridText(100, 25, 'nc', 'northCenter', 'micro', '#cccccc')
            a.gridText(25, 100,  'ce', 'centerEast', 'micro', '#cccccc')

            a.gridText(100, 100, 'se', 'southEast', 'micro', '#666666')
            a.gridText(100, 100, 'sw', 'southWest', 'micro', '#999999')
            a.gridText(100, 175, 'sc', 'southCenter', 'micro', '#aaaaaa')
            a.gridText(175, 100, 'cw', 'centerWest', 'micro', '#aaaaaa')
            a.show()
            del a
            time.sleep(1) # wait a second
            
            
# out of date
#     def testGraph(self):
#         fmtList = ['tk', 'png', 'eps']
#         import time
#         for fmt in fmtList:
#             print _MOD, 'testing format', fmt
#             canvas = Canvas(fmt, 400, 600, '#666666')
#             a = _GraphBase(None, (30,30))
#             a.update(canvas)
#             a.draw()
#     
#             b = _GraphBase(None, (30,30+a.hTotal+2))
#             b.setTitle('testTitle')
#             b.update(canvas)
#             b.draw()   
#             b.show()


    def testGraphText(self):
        #d = TextGraph()
        #d.draw()
        #d.show()

        obj = TextGraph('test', '#333366', 'dotMediumA')
        obj.draw()
        path = '/Volumes/xdisc/_scratch/a.gif'
        obj.write(path)
        os.system('open %s' % path)





#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testProcGraphCoord(self):
        a = ProcessGraphCoordData()
        a()



#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)
