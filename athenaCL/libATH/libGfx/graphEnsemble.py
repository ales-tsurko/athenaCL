#-----------------------------------------------------------------||||||||||||--
# Name:          graphEnsemble.py
# Purpose:       draw window of textres and clones.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

from athenaCL.libATH import imageTools

_MOD = 'graphEnsemble.py'
# COLORfgMain #grey: group (meta-row) label
# COLORbgMargin #almost-black: general-bkg
# COLORbgGrid #grey: single-line, brightest color
# COLORfgAlt #grey: row-level label 
# COLORbgGrid # darker than bg2
# COLORtxTitle #grey: group (meta-row) text
# COLORtxLabel #grey: row-level text
# COLORtxUnit #dark-rose: button-label text

# this is the data structure read by TEmap to produce image.
tiMapDemo = {
'textureA' : {'tRange':(0,8), 'muteStatus': 0, 
                 'cloneDict':{'clone1': {'tRange': (3, 4), 'muteStatus': 0},
                                  'clone2': {'tRange': (3, 8), 'muteStatus': 0},
                                  'clone3': {'tRange': (3, 4), 'muteStatus': 0},
                                  },
                },
'textureB' : {'tRange':(1,6), 'muteStatus':1, 'cloneDict':{}},
'textureC' : {'tRange':(.5,20),'muteStatus':0,'cloneDict':{}},
'textureD' : {'tRange':(12,15),'muteStatus':1, 
                 'cloneDict':{'clone1': {'tRange': (3, 4), 'muteStatus': 0},
                                  'clone2': {'tRange': (2, 10), 'muteStatus': 1},
                                  'clone3': {'tRange': (2, 8), 'muteStatus': 0},
                                  },
                 }
}


class TEmapCanvas:
    def __init__(self, ao=None, tiMapDict=None, barHEIGHT=8, 
                     winWIDTH=700, fmt='tk', master=None):
        # bar height is the height of texture in pixels. the total height of a
        # of a window is determined by the number of textures         
        if ao == None:
            from athenaCL import athenaObj # update needed for color prefs
            update = athenaObj.External()
            update.updateAll('noMessages')
            self.tiMapDict = tiMapDemo
        else:
            update = ao.external # rename update from AO
            textureLib = ao.textureLib
            self.tiMapDict = tiMapDict

        fontTitle = 'micro'
        fontText = 'micro' 
        COLORfgMain = update.getPref('gui', 'COLORfgMain')
        COLORfgMainFrame = update.getPref('gui', 'COLORfgMainFrame')  
        COLORfgAlt = update.getPref('gui', 'COLORfgAlt') 
        COLORfgAltFrame = update.getPref('gui', 'COLORfgAltFrame') 
        COLORbgMargin = update.getPref('gui', 'COLORbgMargin') 
        COLORbgGrid = update.getPref('gui', 'COLORbgGrid') 
        COLORbgAbs = update.getPref('gui', 'COLORbgAbs') 
        COLORtxTitle = update.getPref('gui', 'COLORtxTitle') 
        COLORtxLabel = update.getPref('gui', 'COLORtxLabel') 
        COLORtxUnit = update.getPref('gui', 'COLORtxUnit') 

        self.maxTime = self._findMaxTime(self.tiMapDict)

        self.noEntries = len(self.tiMapDict.keys())
        for textName in self.tiMapDict.keys(): #count clones
            self.noEntries = self.noEntries + len(self.tiMapDict[       
                                    textName]['cloneDict'].keys())
        self.noGutters = self.noEntries + 1
        self.mapGUTTER = 3 # in pixels
        self.headHeight = 2 # band at top of entry blocks
        
        self.rMarginSize = 4
        self.tMarginSize = 12
        self.lMarginSize = 96
        self.bMarginSize = 4
        
        # this calculate the height of the entire window
        self.winHEIGHT = ((self.noEntries * barHEIGHT) + 
                              (self.noGutters * self.mapGUTTER) + self.tMarginSize
                              + self.bMarginSize)
                              
        if winWIDTH < 200: self.winWIDTH = 200
        elif winWIDTH > 3000: self.winWIDTH = 3000
        else: self.winWIDTH = winWIDTH  #600 #
        
        # map is region where digram exists; does not include key
        self.mapHEIGHT = self.winHEIGHT - (self.tMarginSize + self.bMarginSize)
        self.mapWIDTH   = self.winWIDTH - (self.lMarginSize + self.rMarginSize)
        
        self.widthAllGutters = self.mapGUTTER * self.noGutters
        self.widthAllEntries = self.mapHEIGHT - self.widthAllGutters
        #round to nearest pix
        if self.noEntries > 0:
            self.widthEntry = round(self.widthAllEntries / (self.noEntries+0.0))
        else:
            self.widthEntry = 0

        # create canvas
        self.c = imageTools.Canvas(fmt, self.winWIDTH, self.winHEIGHT, 
                                            COLORbgAbs, 'TEmap', master)
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
                
        # key is one gutter from the window height
        # this is total time
        self.c.gridText(self.mapGUTTER, self.mapGUTTER, 'nw',
                             '%.2f'% (self.maxTime), fontTitle, COLORtxUnit)
        # key for time
        noPartitions = 16 # needs to be int
        keyWidth = float(self.mapWIDTH) / noPartitions
        xCurrentPos = self.lMarginSize
        # draw grid
        for keyPartition in range(0, noPartitions):          
            xStart = xCurrentPos 
            xEnd = xCurrentPos + keyWidth
            # y must start at 1, not zero, otherwise grids gets shited up 1
            yStart = 1 # will shift b/n lines and key labels
            yEnd = self.winHEIGHT - self.bMarginSize # set at bottom
            # post vector: skip as causes error in vector version
            # redundant in most cases anyways
            if keyPartition == 0: # first needs to be bkg color
                pass
                #self.c.line(xStart, yStart, xStart, yEnd, COLORbgAbs, 1)
            elif (keyPartition % 2) == 0:
                self.c.line(xStart, yStart+self.tMarginSize, 
                                xStart, yEnd, COLORbgMargin, .5)
                timeStr =  '%.1f' % ((self.maxTime / noPartitions) * keyPartition)
                # this adds numbers to key; buffer by a gutter from edge of window
                self.c.gridText(xCurrentPos, self.mapGUTTER,
                                     'nc', timeStr, fontTitle, COLORtxUnit)
            else: # use sub pixel line size for vector version
                self.c.line(xStart, yStart+self.tMarginSize, 
                                xStart, yEnd, COLORbgGrid, .5)
            xCurrentPos = xCurrentPos + keyWidth

        # draw textures
        yPosition = self.tMarginSize + self.mapGUTTER # initial space
        tNameList = self.tiMapDict.keys()
        tNameList.sort()
        for tName in tNameList:
            yEndPos = yPosition + self.widthEntry
            # this is actually the absolute time range
            tStart, tEnd = self.tiMapDict[tName]['tRange']

            barOffsetStart = int(round(self.mapWIDTH * 
                                  (float(tStart) / self.maxTime)))
            # must add 1 here to get off margin, and into map
            xStart = self.lMarginSize + barOffsetStart + 1
            
            barOffsetEnd = int(round(self.mapWIDTH * 
                                  (float(tEnd) / self.maxTime)))
            # must subtract 1 here to get into map 
            xEnd = self.lMarginSize + barOffsetEnd - 1

            yHeadStart = yPosition
            yHeadEnd = yPosition + self.headHeight
            yBodyStart = yPosition + self.headHeight
            yBodyEnd = yEndPos

            # create head box
            self.c.rectangle(xStart, yHeadStart, xEnd, yHeadEnd, 
                                  COLORfgMainFrame, None, 0)
            if self.tiMapDict[tName]['muteStatus'] == 0: # normal
                self.c.rectangle(xStart, yBodyStart, xEnd, yBodyEnd, 
                                      COLORfgMain, None, 0) 
            else: # silenced
                self.c.rectangle(xStart, yBodyStart, xEnd, yBodyEnd, 
                                 None,  COLORfgMain, 1)             
            # create texture label
            self.c.gridText(self.mapGUTTER, yBodyStart, 'nw', tName, fontTitle, 
                                 COLORtxTitle)
            # shift down
            yPosition = yEndPos + self.mapGUTTER
            # clones
            cNameList = self.tiMapDict[tName]['cloneDict'].keys()
            cNameList.sort()
            for cName in cNameList:
                yEndPos = yPosition + self.widthEntry
                cStart, cEnd = self.tiMapDict[tName]['cloneDict'][cName]['tRange']
                barOffsetStart =    int(round(self.mapWIDTH * 
                                            (float(cStart) / self.maxTime)))
                # must add one to get onto map
                xStart = self.lMarginSize + barOffsetStart + 1
                
                barOffsetEnd = int(round(self.mapWIDTH *
                                        (float(cEnd) / self.maxTime)))
                # must remove one to get onto map
                xEnd = self.lMarginSize + barOffsetEnd - 1
                
                yHeadStart = yPosition
                yHeadEnd      = yPosition + self.headHeight
                yBodyStart = yPosition + self.headHeight
                yBodyEnd      = yEndPos
                # create head box
                self.c.rectangle(xStart, yHeadStart, xEnd, yHeadEnd, 
                                      COLORfgAltFrame, None, 0)

                if self.tiMapDict[tName]['cloneDict'][cName]['muteStatus'] == 0:
                    self.c.rectangle(xStart, yBodyStart, xEnd, yBodyEnd, 
                                          COLORfgAlt, None, 0)
                else: # silenced
                    self.c.rectangle(xStart,yBodyStart, xEnd, yBodyEnd, 
                                          None, COLORfgAlt, 1)                   
                # clone labels are shifted right a bit
                self.c.gridText((self.mapGUTTER*4), yBodyStart, 'nw',
                                          cName, fontTitle, COLORtxLabel)
                # shift down
                yPosition = yEndPos + self.mapGUTTER

    def show(self, dir=None, prefDict=None):
        self.c.show(dir, prefDict)

    def write(self, fp, openMedia):
        self.c.write(fp, openMedia)

    # utility to get max time; may be replaced
    # w/ data stored in data struct passed to this command
    # not that these time ranges are based on user-supplied time ranges
    # not on actual duration...
    def _findMaxTime(self, tiMapDict):
        maxTime = 0.0
        for tiName in tiMapDict.keys():
            s, e = tiMapDict[tiName]['tRange']
            if maxTime <= e:
                maxTime = e
            for cloneName in tiMapDict[tiName]['cloneDict'].keys():
                s, e = tiMapDict[tiName]['cloneDict'][cloneName]['tRange']
                if maxTime <= e:
                    maxTime = e
        return float(maxTime) # must be a float for division errors




#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    TEmap = TEmapCanvas(None, tiMapDemo, 10, 700, 'pil')
    TEmap.show()
    #TEmap = TEmapCanvas(None, tiMapDemo, 10, 700, 'tk')
    #TEmap.show()


