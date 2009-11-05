#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          imageNetwork.py
# Purpose:       provides network displays.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2002 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

from athenaCL.libATH import imageTools
from athenaCL.libATH import SC
from athenaCL.libATH import MC


# COLORfgMain #grey: group (meta-row) label
# COLORbgMargin #almost-black: general-bkg
# COLORbgGrid #grey: single-line, brightest color
# COLORfgAlt #grey: row-level label 
# COLORbgGrid # darker than bg2
# COLORtxTitle #grey: group (meta-row) text
# COLORtxLabel #grey: row-level text
# COLORtxUnit #dark-rose: button-label text

class MCnetCanvas:
    # find number of area points and side size
    # spacing provided by j. straus
    fixedPosChart = {(2,2): {'side':3,
                                  'setLoc': {(2,1,0):(0,0),# as x,y
                                                 (2,2,0):(0,1),
                                                 (2,3,0):(1,0),
                                                 (2,4,0):(1,1),
                                                 (2,5,0):(2,0),
                                                 (2,6,0):(2,1),
                                                },
                                    },
                          (3,3): {'side':7,
                                  'setLoc': {(3,1,0):(0,0),# as x,y
                                                 (3,2,1):(0,1),
                                                 (3,3,1):(0,2),
                                                 (3,4,1):(0,3),
                                                 (3,5,1):(0,4),
                                                 (3,6,0):(1,2),
                                                 (3,7,1):(1,3),
                                                 (3,8,1):(1,4),
                                                 (3,9,0):(1,5),
                                                (3,10,0):(2,4),
                                                (3,11,1):(2,5),
                                                (3,12,0):(3,6),
                                                },
                                    },
                          (4,4): {'side':11,
                                  'setLoc': {(4,1,0):(0,0),# as x,y
                                                 (4,2,1):(0,1),
                                                 (4,3,0):(2,1),
                                                 (4,4,1):(0,3),
                                                 (4,5,1):(0,5),
                                                 (4,6,0):(0,7),
                                                 (4,7,0):(4,3),
                                                 (4,8,0):(6,5),
                                                 (4,9,0):(8,7),
                                                (4,10,0):(1,2),
                                                (4,11,1):(2,3),
                                                (4,12,1):(1,4),
                                                (4,13,1):(2,5),
                                                (4,14,1):(1,6),
                                                (4,15,1):(4,5),
                                                (4,16,1):(6,7),
                                                (4,17,0):(2,9), ###
                                                (4,18,1):(4,7),
                                                (4,19,1):(4,9),
                                                (4,20,0):(6,9),
                                                (4,21,0):(3,4),
                                                (4,22,1):(3,6),
                                                (4,23,0):(5,6),
                                                (4,24,0):(3,8),
                                                (4,25,0):(7,8),
                                                (4,26,0):(7,4),##
                                                (4,27,1):(5,8),
                                                (4,28,0):(5,10),
                                                (4,29,1):(2,7),
                                                },
                                    },
                          (5,5): {'side':17,
                                  'setLoc': {(5,1,0):(0,0),# as x,y
                                                 (5,2,1):(0,1),
                                                 (5,3,1):(2,1),
                                                 (5,4,1):(0,2),
                                                 (5,5,1):(0,5),
                                                 (5,6,1):(7,2),
                                                 (5,7,1):(12,5),
                                                 (5,8,0):(1,4),
                                                 (5,9,1):(2,2),
                                                (5,10,1):(4,3),
                                                (5,11,1):(1,8),
                                                (5,12,0):(8,3),
                                                (5,13,1):(2,9),
                                                (5,14,1):(7,5),
                                                (5,15,0):(12,9),
                                                (5,16,1):(4,7),
                                                (5,17,0):(4,12),
                                                (5,18,1):(9,6),
                                                (5,19,1):(13,7),
                                                (5,20,1):(16,10),
                                                (5,21,1):(9,11),
                                                (5,22,0):(16,11),
                                                (5,23,1):(5,8),
                                                (5,24,1):(8,7),
                                                (5,25,1):(5,13),
                                                (5,26,1):(6,10),
                                                (5,27,1):(8,12),
                                                (5,28,1):(10,13),
                                                (5,29,1):(13,12),
                                                (5,30,1):(15,11),
                                                (5,31,1):(13,16),
                                                (5,32,1):(15,15),
                                                (5,33,0):(11,10),
                                                (5,34,0):(11,14),
                                                (5,35,0):(14,14),
                                                (5,36,1):(2,5),
                                                (5,37,0):(3,10),
                                                (5,38,1):(7,9),
                                                },
                                    },
                         }


    def __init__(self, cmdObj=None, srcSize=2, dstSize=2, fmt='pil',
                     master=None):
        # bar height is the height of texture in pixels. the total height of a
        # of a window is determined by the number of textures         

        if cmdObj == None:
            from athenaCL import athenaObj # update need for color prefs
            update = athenaObj.External()
            update.updateAll('noMessages')
            ao = athenaObj.AthenaObject()
            self.scObj = SC.SetClass()
            mcObj = MC.MapClass()
        else:
            ao = cmdObj.ao
            self.scObj = cmdObj.scObj
            update = ao.external # rename update from AO
            # this is not necesssary, and thwarts manual-pref loading
            #update.updatePrefs() # get new settings
            mcObj = cmdObj.mcObj

        fontTitle = 'micro' #eval(update.getPref('gui', 'fontTitle'))
        fontText     = 'micro' #eval(update.getPref('gui', 'fontText'))
        COLORfgMain = update.getPref('gui', 'COLORfgMain') 
        COLORfgAlt = update.getPref('gui', 'COLORfgAlt') 
        COLORbgMargin = update.getPref('gui', 'COLORbgMargin') 
        COLORbgGrid = update.getPref('gui', 'COLORbgGrid')        
        COLORtxTitle = update.getPref('gui', 'COLORtxTitle') 
        COLORtxLabel = update.getPref('gui', 'COLORtxLabel') 
        COLORtxUnit = update.getPref('gui', 'COLORtxUnit') 
        COLORbgAbs = update.getPref('gui', 'COLORbgAbs') 


        rowAxisSets = self.scObj.getAllScTriples(srcSize, ao.tniMode)
        columnAxisSets = self.scObj.getAllScTriples(dstSize, ao.tniMode)

        if srcSize == dstSize:
            self.totalSets = len(rowAxisSets) # ignoring col for now
            self.masterSetList = rowAxisSets
        else:
            self.totalSets = len(rowAxisSets) + len(columnAxisSets)
            self.masterSetList = rowAxisSets + columnAxisSets

        if (srcSize, dstSize) in self.fixedPosChart.keys():
            self.mapPostitionType = 'fixed'
        else:
            self.mapPostitionType = 'perimeter'

        if self.mapPostitionType == 'fixed':
            sideUnits = self.fixedPosChart[(srcSize, dstSize)]['side']
            area = pow(sideUnits,2)
        elif self.mapPostitionType == 'perimeter':
            for side in range(1,100):
                area = pow(side,2)
                circumSquar = (side * 4) - 4 # units the fill outer perimeter
                if self.totalSets <= circumSquar:
                    sideUnits = side
                    break

        self.areaKeys = range(0,area) # list to get a point for all area
        self.noGutters        = sideUnits + 1
        self.mapGUTTER        = 3 # in pixels
        self.nodeWidth        = 46
        self.nodeRadius   = 16
        #self.yMarginShift  = 0 #entryHeadHeight
        #self.xMarginShift  = 23 #boundary on left

        self.rMarginSize = 4
        self.tMarginSize = 4
        self.lMarginSize = 24
        self.bMarginSize = 4


        self.cordDict = {} # used to hold info on each position
        xCord = 0
        yCord = 0
        for x in self.areaKeys: # initialize with empty dicts
            self.cordDict[(xCord, yCord)] = {}
            xCord = xCord + 1
            if xCord == sideUnits:
                xCord = 0
                yCord = yCord + 1
        cordKeys = self.cordDict.keys()
        cordKeys.sort()

        # this calculate the height of the entire window
        self.winHEIGHT = ((sideUnits * self.nodeWidth) + (self.noGutters * 
                          self.mapGUTTER) + self.tMarginSize + self.bMarginSize)
        self.winWIDTH = ((sideUnits * self.nodeWidth) + (self.noGutters * 
                          self.mapGUTTER) + self.lMarginSize + self.rMarginSize)
                          
        self.mapHEIGHT = self.winHEIGHT - (self.tMarginSize + self.bMarginSize)
        self.mapWIDTH   = self.winWIDTH  - (self.lMarginSize + self.rMarginSize)
        self.heightAllGutters = self.mapGUTTER * self.noGutters
        self.heightAllEntries = self.mapHEIGHT - self.heightAllGutters


        # create canvas
        self.c = imageTools.Canvas(fmt, self.winWIDTH, self.winHEIGHT, 
                                            COLORbgAbs, 'MCnet', master)

        # draw margin rectangles
        self.c.rectangle(0, 0, self.winWIDTH, self.tMarginSize, 
                              COLORbgMargin, None, 0)
        self.c.rectangle(0, 0, self.lMarginSize, self.winHEIGHT, 
                              COLORbgMargin, None, 0)
        self.c.rectangle(0, self.tMarginSize + self.mapHEIGHT, 
                              self.winWIDTH, self.winHEIGHT, 
                              COLORbgMargin, None, 0)
        self.c.rectangle(self.mapWIDTH + self.lMarginSize, 0, 
                              self.winWIDTH, self.winHEIGHT, COLORbgMargin, None, 0)
            
        # fill coord dict with coords for square, center
        xPos = self.lMarginSize + self.mapGUTTER
        yPos = self.tMarginSize + self.mapGUTTER
        xCord = 0
        yCord = 0
        for x in self.areaKeys:
            self.cordDict[(xCord, yCord)]['set'] = None # empty
            self.cordDict[(xCord, yCord)]['box'] = (xPos,yPos,
                (xPos +self.nodeWidth),(yPos+self.nodeWidth))
            centerX = (xPos + (.5 * self.nodeWidth))
            centerY = (yPos + (.5 * self.nodeWidth))
            self.cordDict[(xCord, yCord)]['center'] = (centerX,centerY)
            xPos = xPos + self.nodeWidth + self.mapGUTTER
            if xPos >= (self.winWIDTH - self.nodeWidth):
                yPos = yPos + self.nodeWidth + self.mapGUTTER
                # rest to first x position
                xPos = self.lMarginSize + self.mapGUTTER
            xCord = xCord + 1
            if xCord == sideUnits:
                xCord = 0
                yCord = yCord + 1

        # assign sets to area positions
        if self.mapPostitionType == 'fixed':
            setLoc = self.fixedPosChart[(srcSize, dstSize)]['setLoc']
            # assign sets to coords
            for node in setLoc.keys():
                position = setLoc[node]
                self.cordDict[position]['set'] = node
          #  counter = counter + 1

        elif self.mapPostitionType == 'perimeter': # use parimiter method
            # get perimeter points
            locations =  self.cordDict.keys()
            tempLocs = []
            for node in locations:
                if node[0] == 0 or node[1] == 0:
                    tempLocs.append(node)
                elif node[0] == sideUnits-1 or node[1] == sideUnits-1:
                    tempLocs.append(node)
            # sort perimter clockwise
            perimeterLocs = []
            usedList = []
    
            rowList = []
            for node in tempLocs: # do top
                if node[1] == 0 and node not in usedList:
                    rowList.append(node)
                    usedList.append(node)
            rowList.sort()
            perimeterLocs = perimeterLocs + rowList
    
            rowList = []
            for node in tempLocs: # down right side
                if node[0] == (sideUnits-1) and node not in usedList:
                    rowList.append(node)
                    usedList.append(node) 
            rowList.sort()
            perimeterLocs = perimeterLocs + rowList
    
            rowList = []
            for node in tempLocs: # across bottom
                if node[1] == (sideUnits-1) and node not in usedList:
                    rowList.append(node)
                    usedList.append(node) 
            rowList.sort()
            rowList.reverse()
            perimeterLocs = perimeterLocs + rowList
    
            rowList = []
            for node in tempLocs: # across bottom
                if node[0] == 0 and node not in usedList:
                    rowList.append(node)
                    usedList.append(node) 
            rowList.sort()
            rowList.reverse()
            perimeterLocs = perimeterLocs + rowList
    
            # assign sets to coords
            xCord = 0
            yCord = 0
            counter = 0
            for node in self.masterSetList:
                position = perimeterLocs[counter]
                self.cordDict[position]['set'] = node
                counter = counter + 1


        # read coords, create boxes only when there is a sset
        xCord = 0
        yCord = 0
        for x in self.areaKeys:
            if self.cordDict[(xCord, yCord)]['set'] != None:
                x1, y1, x2, y2 = self.cordDict[(xCord, yCord)]['box']
                self.c.rectangle(x1,y1,x2,y2, COLORbgAbs, COLORfgAlt, 1)
            xCord = xCord + 1
            if xCord == sideUnits:
                xCord = 0
                yCord = yCord + 1
        # create line nets
        #netList = [((0,2),(1,2)),((0,1),(2,0)),((0,0),(0,1))]
        netList = []
        for colEntry in columnAxisSets: # 10 for leftmost column
            for rowEntry in rowAxisSets:
                srcSet = self.scObj.pcs(colEntry)
                dstSet = self.scObj.pcs(rowEntry)

                a = mcObj.displacement(srcSet, dstSet, 1)
                minDispl, maxDispl, orderedResults, counter = a
                if minDispl == 1: # find sets in grid
                    lineCords = [] # clear before finding two points
                    for node in self.cordDict.keys():
                        if self.cordDict[node]['set'] == colEntry:
                            lineCords.append(node)
                        if self.cordDict[node]['set'] == rowEntry:
                            lineCords.append(node)
                    if lineCords == []:
                        pass
                    elif lineCords in netList:
                        pass
                    elif (lineCords[1],lineCords[0]) in netList:
                        pass
                    else:
                        netList.append(lineCords)
        # draw lines
        for net in netList:
            a, b = net
            x1, y1 = self.cordDict[a]['center']
            x2, y2 = self.cordDict[b]['center']
            self.c.line(x1,y1,x2,y2, COLORfgMain, 1)
        # read coords, create circles and labels
        xCord = 0
        yCord = 0
        for x in self.areaKeys:
            if self.cordDict[(xCord, yCord)]['set'] != None:
                setStr = self.scObj.scToStr(self.cordDict[(xCord, yCord)]['set'])
                centerX, centerY = self.cordDict[(xCord, yCord)]['center']
                self.c.oval(centerX-self.nodeRadius,
                             centerY-self.nodeRadius,
                             centerX+self.nodeRadius,
                             centerY+self.nodeRadius,
                             COLORbgAbs, COLORfgMain, width=2)
                if len(setStr) <= 3: # smallest
                    centerShift = 7
                elif len(setStr) <= 4:
                    centerShift = 10
                else: # 5 or greater
                    centerShift = 12

                xLabel = centerX - centerShift
                yLabel = centerY - 3
                self.c.gridText(xLabel, yLabel, 'nw', 
                        setStr, fontTitle, COLORtxTitle)
            xCord = xCord + 1
            if xCord == sideUnits:
                xCord = 0
                yCord = yCord + 1

    def show(self, dir=None, prefDict=None):
        self.c.show(dir, prefDict)

    def write(self, fp, openMedia):
        self.c.write(fp, openMedia)

if __name__ == '__main__':
    MCnet = MCnetCanvas(None, 2, 2, 'pil')
    MCnet.show()
    MCnet = MCnetCanvas(None,   2, 2, 'tk')
    MCnet.show()


