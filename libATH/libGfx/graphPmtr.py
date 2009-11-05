#-----------------------------------------------------------------||||||||||||--
# Name:          TImap.py
# Purpose:       draw window of textres and clones.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2004-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import random
from athenaCL.libATH import imageTools
from athenaCL.libATH import eventList

_MOD = 'graphPmtr.py'

#-----------------------------------------------------------------||||||||||||--


class _MapCanvas: 
    """base class for map canvases"""
    def __init__(self):
        pass
    
    def _updateAoPrefs(self, ao):
        update = ao.external # rename update from AO
        # not sure this should be updated here...
        #update.updatePrefs() # get new settings

        self.fontTitle = 'micro' #eval(update.getPref('gui', 'fontTitle'))
        self.fontText = 'micro' #eval(update.getPref('gui', 'fontText'))
        self.COLORfgMain = update.getPref('gui', 'COLORfgMain') 
        self.COLORfgAlt = update.getPref('gui', 'COLORfgAlt') 
        self.COLORfgAbs = update.getPref('gui', 'COLORfgAbs') 

        self.COLORbgMargin = update.getPref('gui', 'COLORbgMargin') 
        self.COLORbgGrid = update.getPref('gui', 'COLORbgGrid') 
        self.COLORtxTitle = update.getPref('gui', 'COLORtxTitle') 
        self.COLORtxLabel = update.getPref('gui', 'COLORtxLabel') 
        self.COLORtxUnit = update.getPref('gui', 'COLORtxUnit') 
        self.COLORbgAbs = update.getPref('gui', 'COLORbgAbs') 

    def _updateSizePrefs(self):
        """this is used for multi-paramater displays"""
        if self.xRelation == 'event': # events determin resolution
            self.xRez = self.splitSco.nEvent # pixels
            self.dataSigDig = (0,2) # need ints for x values
            self.axisSigDig = (0,2)
        elif self.xRelation == 'time':
            # this value is the only determinate of window size
            self.xRez = 600 # manual resolution
            self.dataSigDig = (2,2) # need floats for x values
            self.axisSigDig = (2,2)
        else:
            raise ValueError
            
        self.yRez = 36   # min seems to be around 36

        self.lMarginSize = 40
        self.rMarginSize = 1     # small view uses small gutter
        self.tMarginSize = 1
        self.bMarginSize = 20

        self.titleGutterVert = 2 # pix from vertical edges
        self.titleGutterHorz = 2 # pix from horiz edges
        self.titleHide = 0 # hide title

        self.yGridLines = 3
        self.yIconSize = 1
        self.yIconMargin = 0

        if self.xRelation == 'event': # scale sizes
            if self.splitSco.nEvent <= 16:
                self.xGridLines = 3
                self.xIconSize = 9
                self.xIconMargin = 9
            elif self.splitSco.nEvent <= 32:
                self.xGridLines = 5
                self.xIconSize = 9
                self.xIconMargin = 3
            elif self.splitSco.nEvent <= 64:
                self.xGridLines = 5
                self.xIconSize = 3
                self.xIconMargin = 1
            elif self.splitSco.nEvent <= 256:
                self.xGridLines = 9
                self.xIconSize = 3
                self.xIconMargin = 1
            else:
                self.xGridLines = 9
                self.xIconSize = 1 
                self.xIconMargin = 1 # event should always have a margin
        elif self.xRelation == 'time': # dont scale
            self.xGridLines = 9
            self.xIconSize = 1 # minimum always
            self.xIconMargin = 0
        else:
            raise ValueError

    def _updateSizePrefsDetail(self):
        """this settings are primarily for creating images for presentations
        and print; used for single parameter dusplays
        TPmap uses this
        """
        # per graph settings

        self.xRez = self.splitSco.nEvent # pixels
        self.dataSigDig = (0,4)
        self.axisSigDig = (0,4)

        self.rMarginSize = 4
        self.tMarginSize = 4
        self.lMarginSize = 72
        self.bMarginSize = 24
        self.titleHide = 0 # hide title

        self.yRez = 72   # min seems to be around 36

        # detail display
        if self.splitSco.nEvent <= 24:
            self.yGridLines = 7
            self.yIconSize = 3 # should be odd
            self.yIconMargin = 0
            self.xGridLines = 3
            self.xIconSize = 11
            self.xIconMargin = 1
        else: # large display
            self.yGridLines = 5
            self.yIconSize = 1
            self.yIconMargin = 0
            self.xGridLines = 11
            self.xIconSize = 3
            self.xIconMargin = 1

        self.titleGutterVert = self.tMarginSize # pix from vertical edges
        self.titleGutterHorz = self.rMarginSize + 1 # pix from horiz edges

    def _updateSingleGraphSize(self):
        # initial canvas as a format to get test
        # test a graph to get size info
        pmtr = random.choice(self.splitSco.getKeys())
        dataList = self.splitSco.getCoord(pmtr, self.xRelation)
        gObj = self._genGraph(dataList)
        gObj.update(None) # create without a canvas
        self.hSingleGraph = gObj.hTotal # height of each graph
        self.wSingleGraph = gObj.wTotal
        #gObj.destroy()
        del gObj

    def _genGraph(self, dataList, x=0, y=0, title=''):
        """x y are orgins
        creates and returns gObj, does not draw"""
        dataLib = {} # ProcessGraphCoordData needs a dictionary
        groupKey = 1 # (self.nPointColor % 3) + 1 # cyclically vary 
        dataLib[groupKey] = dataList
        dataObj = imageTools.ProcessGraphCoordData(dataLib, self.xRez, self.yRez, 
                                 self.dataSigDig, self.axisSigDig)
        dataObj() # call to calculate values
        # last arg is origin of upper left start point
        
        # note: may need to use a different graph
        # to support alternate (time) xRelation
        if self.xRelation == 'event':
            gObj = imageTools.NumericalPointGraph(dataObj, (x,y))
        elif self.xRelation == 'time':
            gObj = imageTools.NumericalBarGraph(dataObj, (x,y))
        else: raise ValueError
            
        gObj.setMargin(self.lMarginSize, self.rMarginSize, 
                            self.tMarginSize, self.bMarginSize) #l, r, t, b
        gObj.setIconSize(self.xIconSize, self.yIconSize, 
                              self.xIconMargin, self.yIconMargin) 
                              #x, y, xMargin, yMargin
        gObj.setLabel('', '', 4) # remove labels
        rowGridKey = dataObj.gridKey(groupKey, 'y', self.yGridLines)
        colGridKey = dataObj.gridKey(groupKey, 'x', self.xGridLines)
        rowUnitKey = dataObj.unitKey(groupKey, 'y', rowGridKey)
        colUnitKey = dataObj.unitKey(groupKey, 'x', colGridKey)
        gObj.setGrid(rowGridKey, colGridKey, rowUnitKey, colUnitKey)
        if not self.titleHide:
            gObj.setTitle(title, 'br', self.titleGutterVert, self.titleGutterHorz)
        bitColorDict = {1 : self.COLORtxTitle,
                             2 : '#CCCCCC',
                             3 : '#AAAAAA',}

        bkg = self.COLORbgAbs #self.COLORbgGrid
        grid = self.COLORbgGrid #self.COLORbgGrid
        gObj.setColors(bkg, grid, None, self.COLORbgMargin, 
                      self.COLORtxUnit, self.COLORtxLabel, 
                      self.COLORtxTitle, bitColorDict)
        # bkg, grid, tick, margin, 
        #units, label, title, bigColorDict
        return gObj

    def show(self, dir=None, prefDict=None):
        self.c.show(dir, prefDict)

    def write(self, fp, openMedia):
        self.c.write(fp, openMedia)


#-----------------------------------------------------------------||||||||||||--
class TImapCanvas(_MapCanvas):
    """produces graphical display of a a texture or clone
    note: textures may be pre or post TM; clones can only be post TM
    """
    def __init__(self, ao, tName='', cName=None, tmRelation='pre', 
                    xRelation='event', fmt='tk', master=None):
        _MapCanvas.__init__(self)
        # bar height is the height of texture in pixels. the total height of a
        # of a window is determined by the number of textures         
        self.tName = tName
        self.cName = cName # if none, assumes it is a texture
        self.tmRelation = tmRelation
        self.xRelation = xRelation # event or time
        if cName != None: # its a clone, dont force post tmRelation
            self.tmRelation = 'post'
            srcObj = ao.cloneLib.get(tName, cName)
            srcFmt = 'c' # clone
        else:
            srcObj = ao.textureLib[tName]
            srcFmt = 't' # texture

        self.c = fmt
        self.splitSco = eventList.EventSequenceSplit(srcObj, srcFmt)
        self.splitSco.load(self.tmRelation)
        # call clean method to remove bad data (strings)
        self.splitSco.clean()
        
        # updates colors and sizeing issues, splitSco must be defined
        self._updateAoPrefs(ao)
        self._updateSizePrefs() # looks at self.xRelation
        self._updateSingleGraphSize()

        hGutter = 2 # space between graphs
        nGraphs = len(self.splitSco.getKeys())
        self.winWIDTH = self.wSingleGraph
        self.winHEIGHT = (self.hSingleGraph * nGraphs) + (hGutter * (nGraphs-1))
        # dynamic points
        xCurrent = 0
        yCurrent = 0
        # create canvas
        self.c = imageTools.Canvas(fmt, self.winWIDTH, self.winHEIGHT, 
                                  self.COLORbgAbs, 'TImap: %s' % tName, master)
        #draw all parameters
        for pmtr in self.splitSco.getKeys():
            dataList = self.splitSco.getCoord(pmtr, self.xRelation)
            # data list here is alist of x/y pairs, or possible xy/xy paurs
            # this will be process w/ process graph coord data
            title = self.splitSco.getTitle(pmtr)
            gObj = self._genGraph(dataList, xCurrent, yCurrent, title)
            gObj.update(self.c)
            gObj.draw()
            yCurrent = yCurrent + self.hSingleGraph + hGutter

            #gObj.write() # automatically opens


#-----------------------------------------------------------------||||||||||||--
class TPmapCanvas(_MapCanvas):
    """produces graphical display of a single parameter, or a clone src
    and filter value
    srcList is a list of label,pObj pairs
    """
    def __init__(self, ao, srcList, srcFmt='pg', events=240, 
                     fmt='tk', master=None):
        _MapCanvas.__init__(self)
        self.c = fmt
        self.events = events # number of events
        self.splitSco = eventList.EventSequenceSplit(srcList, srcFmt, self.events)
        self.splitSco.load()
        self.xRelation = 'event' # always event for tpmaps

        # updates colors and sizeing issues, splitSco must be defined
        self._updateAoPrefs(ao)
        self._updateSizePrefsDetail()
        self._updateSingleGraphSize()

        hGutter = 2 # space between graphs
        nGraphs = len(self.splitSco.getKeys())
        self.winWIDTH = self.wSingleGraph
        self.winHEIGHT = (self.hSingleGraph * nGraphs) + (hGutter * (nGraphs-1))
        # dynamic points
        xCurrent = 0
        yCurrent = 0
        # create canvas
        self.c = imageTools.Canvas(fmt, self.winWIDTH, self.winHEIGHT, 
                                            self.COLORbgAbs, 'TPmap', master)
        #draw all parameters
        for pmtr in self.splitSco.getKeys():
            # xRelation will always be 'event' for parameter displays
            dataList = self.splitSco.getCoord(pmtr, 'event')
            title = self.splitSco.getTitle(pmtr)
            gObj = self._genGraph(dataList, xCurrent, yCurrent, title)
            gObj.update(self.c)
            gObj.draw()
            yCurrent = yCurrent + self.hSingleGraph + hGutter



#-----------------------------------------------------------------||||||||||||--

if __name__ == '__main__':
    print 'test code must be re-done'
    #TImap = TImapCanvas(None, None, None, 'pil')
    #TImap.show()
    #TImap2 = TImapCanvas(None, None, 'tk')
    #TImap2.show()


