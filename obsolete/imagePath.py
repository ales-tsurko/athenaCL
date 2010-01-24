#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          imagePath.py
# Purpose:       provides display of paths and path voices.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

# from athenaCL.libATH import SC
# from athenaCL.libATH import MC
from athenaCL.libATH import multiset
from athenaCL.libATH import drawer
from athenaCL.libATH import imageTools

# scObj = SC.SetClass()
# mcObj = MC.MapClass() 

class PVviewCanvas:
    #_w = '.' # this makes stdOUT disabled

    def __init__(self, ao=None, barHEIGHT=10, winWIDTH=None, fmt='pil', 
                     master=None):
        # bar height is the height of texture in pixels. the total height of a
        # of a window is determined by the number of textures         
        if ao == None:
            from athenaCL.libATH import athenaObj # update need for color prefs
            update = athenaObj.External()
            update.updateAll('noMessages')
            pcsPath = [(4,3,10),(1,5,4,3),(2,11,4),(7,5,3)]
            scPath  = [(3,2,1),(4,14,0),(3,2,-1),(3,5,1)]
            mapDict = None
            activePath = 'testPath'
        else:
            update = ao.external # rename update from AO
            pathLib = ao.pathLib
            activePath = ao.activePath
            pcsPath = pathLib[activePath].get('pcsPath')
            scPath  = pathLib[activePath].get('scPath')
            # gets a dict of (sourcePosition, destinationPosition) : map entries
            if pathLib[activePath].voiceType == 'none':
                mapDict = None
            else:
                mapDict = pathLib[activePath].voiceLib[
                                pathLib[activePath].activeVoice]['maps']

        fontTitle = 'micro' 
        fontText = 'micro' 
        COLORfgMain = update.getPref('gui', 'COLORfgMain') 
        COLORbgMargin = update.getPref('gui', 'COLORbgMargin') 
        COLORbgGrid = update.getPref('gui', 'COLORbgGrid') 
        COLORbgAbs = update.getPref('gui', 'COLORbgAbs') 
        COLORfgAlt = update.getPref('gui', 'COLORfgAlt') 
        COLORtxTitle = update.getPref('gui', 'COLORtxTitle') 
        COLORtxLabel = update.getPref('gui', 'COLORtxLabel') 
        COLORtxUnit = update.getPref('gui', 'COLORtxUnit') 

        self.totalSets = len(pcsPath)

        self.vertEntries = 0 # max number of vertical cells
        for set in pcsPath:
            if len(set) >= self.vertEntries:
                self.vertEntries = len(set)
        # add ont vertical entry for the set-class key accross the top
        self.vertEntries = self.vertEntries + 1
        self.noGutters = self.vertEntries + 1
        self.mapGUTTER = 3 # in pixels, space between cells
        
        self.rMarginSize = 4
        self.tMarginSize = 4
        self.lMarginSize = 96 # same as imagePmtr; was 100
        self.bMarginSize = 4 # half of imagePmtr
        
        # this calculate the height of the entire window
        self.winHEIGHT   = (self.vertEntries * barHEIGHT) + (self.noGutters * 
                          self.mapGUTTER) + self.tMarginSize + self.bMarginSize
                          
        if winWIDTH == None:
            self.winWIDTH = (self.lMarginSize + self.rMarginSize) + (66 * 
                                  self.totalSets)
        elif winWIDTH < 200:
            self.winWIDTH = 200
        elif winWIDTH > 3000:
            self.winWIDTH = 3000
        else:
            self.winWIDTH   = winWIDTH  #600 #
        # get size of just the data region
        self.mapHEIGHT = self.winHEIGHT - (self.tMarginSize + self.bMarginSize)
        self.mapWIDTH   = self.winWIDTH  - (self.lMarginSize + self.rMarginSize)
        
        # map height includes all gutters; dont need to add belwo5
        self.heightAllGutters = self.mapGUTTER * self.noGutters
        self.heightAllEntries = self.mapHEIGHT - self.heightAllGutters
        
        if self.vertEntries > 0: #round to nearest pix
            self.cellHeight = round(self.heightAllEntries/(self.vertEntries+0.0))
        else: self.cellHeight = 0

        self.cellWidth = round(self.mapWIDTH / (self.totalSets + 0.0))
        self.cellEntryWidth = 18 # pixels for each pc entry
        # offset of lines above cell bottom
        self.vertCellOffset = round(self.cellHeight * .5) 

        # create canvas
        self.c = imageTools.Canvas(fmt, self.winWIDTH, self.winHEIGHT, 
                                 COLORbgAbs, 'PVview: %s' % activePath, master)

        # draw margin rectangles
        self.c.rectangle(0, 0, self.winWIDTH, self.tMarginSize, 
            COLORbgMargin, None, 0)
        self.c.rectangle(0, 0, self.lMarginSize, self.winHEIGHT, 
            COLORbgMargin, None, 0)
        self.c.rectangle(0, self.tMarginSize + self.mapHEIGHT, 
                              self.winWIDTH, self.winHEIGHT, 
                              COLORbgMargin, None, 0)
        self.c.rectangle(self.mapWIDTH + self.lMarginSize, 0, 
                              self.winWIDTH, self.winHEIGHT, 
                              COLORbgMargin, None, 0)

        # set name in upper left
        self.c.gridText(self.mapGUTTER, self.mapGUTTER + self.tMarginSize, 'nw', 
                             activePath, fontTitle, COLORtxUnit)

        # draw key for sets
        xCurrentPos = self.lMarginSize
        for keyPartition in range(self.totalSets):          
            xStart  = xCurrentPos
            xEnd      = xCurrentPos + self.cellWidth
            yStart  = self.tMarginSize
            yEnd      = self.winHEIGHT

            # commented out portions create filled rectangles
            if keyPartition == 0: # first needs to be bkg color
                # removing first grid to remove ob1 error w/ vector graphics
                #self.c.line(xStart,yStart,xStart,yEnd, COLORbgAbs, width=1)
                scName = multiset.scToStr(scPath[keyPartition])
                # this adds numbers to key
                self.c.gridText((xCurrentPos+self.mapGUTTER), 
                    self.mapGUTTER + self.tMarginSize, 'nw',
                    scName, fontTitle, COLORtxUnit)
                    
            elif (keyPartition % 1) == 0:
                self.c.line(xStart,yStart,xStart,yEnd, COLORbgMargin, .5)
                scName = multiset.scToStr(scPath[keyPartition])
                # this adds numbers to key
                self.c.gridText((xCurrentPos+self.mapGUTTER), 
                    self.mapGUTTER + self.tMarginSize, 'nw',
                    scName, fontTitle, COLORtxUnit)

            else: # this are the lines that divide verticalities
                self.c.line(xStart,yStart,xStart,yEnd, COLORbgGrid, .5)

            xCurrentPos = xCurrentPos + self.cellWidth

        # sets
        xPosition = self.lMarginSize
        axisDict = {}
        columnCount  = 0
        for chord in pcsPath:
            xPosition = xPosition + self.mapGUTTER
            yPosition = self.tMarginSize + (self.mapGUTTER*2) + self.cellHeight
            rowCount = 0
            for note in chord:
                #yPosition = yPosition #+ self.mapGUTTER #+ self.cellHeight
                yLineStart = yPosition + 8 # needs to be shifted down
                xLineStart = xPosition - self.mapGUTTER - 1 # shift left 1
                # axis dict used for drawing lines
                axisDict[(columnCount, rowCount)] = (xLineStart, yLineStart)

                pcString = '%i' % note
                self.c.gridText(xPosition, yPosition, 'nw',
                                     pcString, fontText, COLORtxTitle)
                rowCount = rowCount + 1
                yPosition = yPosition + self.cellHeight + self.mapGUTTER

            xPosition = xPosition + (self.cellWidth - self.mapGUTTER)
            columnCount = columnCount + 1
            
        # draw even if voices are not possible
        if mapDict != None:
            for i in range(self.totalSets-1):
                thisSetIndex = i
                nextSetIndex = i + 1
                # this has been a source of error, but not clear why
                # some keys have produced a key error
                mapDictkey = (thisSetIndex, nextSetIndex)
                map = mcObj.fetchMap(mapDict[mapDictkey])
                for j in range(len(map)): # go down vertically
                    startCord = axisDict[(i,j)]
                    nextRowPosition = map[j]
                    if drawer.isList(nextRowPosition):
                        for subRowPosition in nextRowPosition:
                            # get next position
                            endCord = axisDict[((i+1),subRowPosition)]
                            self.c.line((startCord[0]+self.cellEntryWidth), 
                                (startCord[1]-self.vertCellOffset), 
                                (endCord[0]), 
                            (endCord[1]-self.vertCellOffset), COLORfgMain, 1)
                    else:
                        # get next position
                        endCord = axisDict[((i+1),nextRowPosition)] 
                        self.c.line((startCord[0]+self.cellEntryWidth), 
                            (startCord[1]-self.vertCellOffset), 
                            (endCord[0]), 
                            (endCord[1]-self.vertCellOffset), COLORfgMain, 1)



    def show(self, dir=None, prefDict=None):
        self.c.show(dir, prefDict)

    def write(self, fp, openMedia):
        self.c.write(fp, openMedia)


if __name__ == '__main__':
    #import Tkinter
    #root = Tkinter.Tk()
    PVview = PVviewCanvas(None)
    PVview.show()
