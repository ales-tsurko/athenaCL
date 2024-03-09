# -----------------------------------------------------------------||||||||||||--
# Name:          graphCellular.py
# Purpose:       draw a PIL/tk window of CA.
#
# Authors:       Jonathan Saggau and Christopher Ariza
#
# Copyright:     (c) 2001-2006 Jonathan Saggau and Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

from athenaCL.libATH import imageTools

_MOD = "graphCellular.py"


class CAmapCanvas:
    def __init__(
        self,
        ao=None,
        caData=[],
        caDataDstValues=None,
        cellWIDTH=4,
        cellHEIGHT=4,
        fmt="png",
        master=None,
        title=None,
    ):

        if ao == None:
            from athenaCL.libATH import athenaObj  # update need for color prefs

            update = athenaObj.External()
            update.updateAll("noMessages")
        else:
            update = ao.external  # rename update from AO

        fontTitle = "micro"
        fontText = "micro"
        COLORfgMain = update.getPref("gui", "COLORfgMain")
        COLORbgMargin = update.getPref("gui", "COLORbgMargin")
        COLORbgGrid = update.getPref("gui", "COLORbgGrid")
        COLORbgAbs = update.getPref("gui", "COLORbgAbs")
        COLORfgAlt = update.getPref("gui", "COLORfgAlt")
        COLORtxTitle = update.getPref("gui", "COLORtxTitle")
        COLORtxLabel = update.getPref("gui", "COLORtxLabel")
        COLORtxUnit = update.getPref("gui", "COLORtxUnit")

        self.caData = caData
        self.caDataDstValues = caDataDstValues  # None if continuous
        # scale bit data

        self.gutterWid = 0  # 1 # pix between cells
        self.gutterColor = COLORbgMargin
        self.cellHEIGHT = cellHEIGHT
        self.cellWIDTH = cellWIDTH

        self.tMargin = 4  # same as value from imagePath.py
        self.lMargin = 96  # same as imagePath.py
        self.bMargin = 4  # same as value from imagePath.py
        self.rMargin = 4  # same as value from imagePath.py

        self.marginColor = self.gutterColor  # make the same

        self.noCols = len(self.caData[0])
        self.noRows = len(self.caData)

        self.winHEIGHT = (
            (self.cellHEIGHT * self.noRows)
            + self.bMargin
            + ((self.noRows - 1) * self.gutterWid)
            + self.tMargin
        )
        self.winWIDTH = (
            (self.cellWIDTH * self.noCols)
            + self.rMargin
            + ((self.noCols - 1) * self.gutterWid)
            + self.lMargin
        )

        self._makeBitMap()  # processes self.caData
        # create canvas
        self.c = imageTools.Canvas(
            fmt, self.winWIDTH, self.winHEIGHT, COLORbgAbs, "AUca", master
        )
        # self.graph = imageTools.BitGraph(self.caData, fg, bg, self.c, iconSize)
        self.c.bitmap(self.lMargin, self.tMargin, self.scaleData, None)
        labelStr = ""

        # draw margins
        self.c.rectangle(
            0, 0, self.winWIDTH, self.tMargin - 1, self.marginColor, None, 0
        )
        self.c.rectangle(
            0, 0, self.lMargin - 1, self.winHEIGHT, self.marginColor, None, 0
        )
        # bottom
        self.c.rectangle(
            0,
            self.winHEIGHT - self.bMargin,
            self.winWIDTH,
            self.winHEIGHT,
            self.marginColor,
            None,
            0,
        )
        # right
        self.c.rectangle(
            self.winWIDTH - self.rMargin,
            0,
            self.winWIDTH,
            self.winHEIGHT,
            self.marginColor,
            None,
            0,
        )

        if title != None:
            # could be COLORtxUnit
            # cant use lMargin here, b/c it is very large!
            y = self.tMargin
            for chunk in title.split("\n"):
                self.c.gridText(
                    self.tMargin, y, "nw", chunk, "micro", COLORtxTitle, 1, None, 1, 1
                )
                y = y + 10

    def _makeBitMap(self):
        self.scaleData = []
        y = 0
        for row in self.caData:
            newRow = []
            x = 0
            for col in row:
                # last value in dst values is largest
                if self.caDataDstValues != None:  # discrete
                    colFloat = float(col) / self.caDataDstValues[-1]
                else:  # continuus
                    colFloat = col
                # get color as gray mapping between unit interval
                color = imageTools.RGBToHTMLColor(imageTools.FloatToRGB(colFloat))
                for i in range(0, self.cellWIDTH):
                    newRow.append(color)
                if x != len(row):  # if not last
                    for i in range(0, self.gutterWid):
                        newRow.append(self.gutterColor)
                x = x + 1
            for i in range(0, self.cellHEIGHT):
                self.scaleData.append(newRow)
            if y != len(self.caData):  # not last
                for i in range(0, self.gutterWid):
                    newRow = [self.gutterColor] * self.winWIDTH
                    self.scaleData.append(newRow)
            y = y + 1

    def show(self, dir=None, prefDict=None):
        "Opens default image viewer and shows picture"
        self.c.show(dir, prefDict)

    def write(self, fp, openMedia):
        self.c.write(fp, openMedia)


# -----------------------------------------------------------------||||||||||||--
def display(usrStr, rule=0, mutation=0):
    from athenaCL.libATH import automata

    ca = automata.factory(usrStr, rule, mutation)
    if ca == None:
        return _MOD, "error, no such ca available"

    ca.gen(ca.spec.get("y"))
    print(_MOD, "values generated, drawing...\n%s" % ca.repr("full"))

    # more pixels causes more time
    obj = CAmapCanvas(
        None,
        ca.getCells(
            "table",
            0,
            ca.spec.get("s"),
            None,
            ca.spec.get("c"),
            ca.spec.get("w"),
        ),
        ca.dstValues,
        2,
        2,
        "png",
        None,
        ca.repr("brief"),
    )
    obj.show()


# >>> graphCellular.displayGradient(400, 50, 't', 3, 1, 130, 132, 'center', .01)
# graphCellular.py values generated, drawing...
# totalistic CA: k=3 r=1 rule=132 mutation=0.01 init=center

# >>> graphCellular.displayGradient(400, 50, 't', 5, 1, 1000, 1001, 'center', .01)

# >>> graphCellular.displayGradient(400, 50, 't', 5, 1, 20000, 20001, 'center', .01)

# graphCellular.displayGradient(400, 50, 't', 5, 1, 500003, 500006, 'center',
# .01)

# >>> graphCellular.displayGradient(400, 50, 'c', 2, 1, .01, .20, 'center', .01)


# -----------------------------------------------------------------||||||||||||--


if __name__ == "__main__":
    pass
