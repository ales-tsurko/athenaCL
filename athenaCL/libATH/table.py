#-----------------------------------------------------------------||||||||||||--
# Name:          unit.py
# Purpose:       basic table object, with outputs for unit interval normalization
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2006-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import copy
import unittest, doctest

from athenaCL.libATH import drawer
from athenaCL.libATH import unit
_MOD = 'table.py'


#-----------------------------------------------------------------||||||||||||--







#-----------------------------------------------------------------||||||||||||--


tableMonoFormatRef = {
        'flatRow'         : ['fr', 'f', 'flat'], # read row first
        'flatRowActive'  : ['fra'], 
        'flatRowPassive' : ['frp'], 
        'flatRowIndex'           : ['fri'], 
        'flatRowIndexActive'     : ['fria'], 
        'flatRowIndexPassive' : ['frip'], 

        'flatColumn'          : ['fc'],
        'flatColumnActive'  : ['fca'],
        'flatColumnPassive' : ['fcp'],
        'flatColumnIndex'            : ['fci'],
        'flatColumnIndexActive'  : ['fcia'],
        'flatColumnIndexPassive' : ['fcip'],
         
        'flatRowReflect'            : ['frr'], 
        'flatRowReflectActive'  : ['frra'], 
        'flatRowReflectPassive' : ['frrp'], 
        'flatRowReflectIndex'         : ['frri'], 
        'flatRowReflectIndexActive'  : ['frria'],
        'flatRowReflectIndexPassive' : ['frrip'],

        'flatColumnReflect'         : ['fcr'],
        'flatColumnReflectActive'   : ['fcra'],
        'flatColumnReflectPassive' : ['fcrp'],
        'flatColumnReflectIndex'          : ['fcri'],
        'flatColumnReflectIndexActive'  : ['fcria'],
        'flatColumnReflectIndexPassive' : ['fcrip'],
        
        'sumRow'             : ['sr', 'sum', 's'],
        'sumRowActive'   : ['sra'],
        'sumRowPassive' : ['srp'],
        'sumRowIndex'           : ['sri'],
        'sumRowIndexActive' : ['sria'],
        'sumRowIndexPassive' : ['srip'],

        'sumColumn'          : ['sc'],
        'sumColumnActive'    : ['sca'],
        'sumColumnPassive' : ['scp'],
        'sumColumnIndex'            : ['sci'],
        'sumColumnIndexActive'  : ['scia'],
        'sumColumnIndexPassive' : ['scip'],

        'averageRow'          : ['ar', 'average', 'a', 'ar'],
        'averageRowActive'  : ['ara'],
        'averageRowPassive' : ['ari'],
        'averageRowIndex'            : ['ari'],
        'averageRowIndexActive'  : ['aria'],
        'averageRowIndexPassive' : ['arip'],
        
        'averageColumn'       : ['ac'],
        'averageColumnActive'  : ['aca'],
        'averageColumnPassive' : ['acp'],
        'averageColumnIndex'             : ['aci'],
        'averageColumnIndexActive'   : ['acia'],
        'averageColumnIndexPassive' : ['acip'],

        'productRow'          : ['pr', 'product', 'p',],
        'productRowActive'  : ['pra'],
        'productRowPassive' : ['prp'],
        'productRowIndex'            : ['pri'],
        'productRowIndexActive'  : ['pria'],
        'productRowIndexPassive' : ['prip'],
                
        'productColumn'       : ['pc'],
        'productColumnActive'  : ['pca'],
        'productColumnPassive' : ['pcp'],
        'productColumnIndex'             : ['pci'],
        'productColumnIndexActive'   : ['pcia'],
        'productColumnIndexPassive' : ['pcip'],
        
            }

def monoFormatParser(usrStr):
    """
    >>> monoFormatParser('pcia')
    'productColumnIndexActive'
    """
    # only allow one-dimensional outputs
    ref = tableMonoFormatRef
    usrStr = drawer.selectionParse(usrStr, ref)
    return usrStr # may be None


class Table:
    """a class for handling mostly discrete data in a table, like a ca
    may be useful for other things
    requires unit.py conversions above; could be autonomous module"""
    def __init__(self, data, cellMin=None, cellMax=None):
        """
        >>> a = Table([[1,2,3], [4,5,6]])
        >>> a.colCount
        3
        >>> a.rowCount
        2
        >>> len(a.outFmt)
        65
        """
        # store data table
        self.data = data
        self.colCount = len(data[0]) # all rows must be same size, colCoutn
        self.rowCount = len(data) 
        # store possible cell min/max, can be none
        if cellMin != None and cellMax != None:
            self.cellMinMax = [cellMin, cellMax] # must be a list
        else: self.cellMinMax = None
        self.cellMin = cellMin
        self.cellMax = cellMax
        
        # format strings are analyzed, so not all combinations named
        # default method is to get value; indexes and pairs can be gotten
        # active cells are those that are > zero
        self.outFmt = ['table', 
            'flatRowPair','flatColumnPair',
            'flatRowReflectPair', 'flatColumnReflectPair', 
                            ] + tableMonoFormatRef.keys()

    def _rotate(self, data):
        """given data in a table, need to get
        if rows are not all the same length, slide values
        when table is not square, this may not be undoable, rotation can be
        such that you cannot get to the value"""
        # need to find longest row
        spread = 0
        for row in data:
            if len(row) > spread:
                spread = len(row)
        newData = []
        for i in range(spread): # for data in columns
            newRow = []
            for row in data:
                if i < len(row): # make sure i is in range of row
                    newRow.append(row[i])
            newData.append(newRow)
        return newData
        
    def rotate(self):
        """rotate and replace internal data"""
        self.data = self._rotate(self.data)
        
    def __repr__(self): 
        msg = []
        for row in self.data:
            msg.append(str(row))
        return '\n'.join(msg)
        
    def _getCenter(self):
        """get center"""
        # index values are one less, so no need to add extra 1 for center
        return self.colCount/2 # let floor
        
    def _getMinMax(self, refSeries=None):
        """get a min Max if possible, combining supplied min, max if available
        if a refSeries is available, use to find min and max


        """      
        if refSeries == []: refSeries = None        
        if self.cellMinMax != None: # if defined, always use
            minMax = self.cellMinMax
        # if a refSeries and one of min/max defined, combine
        elif refSeries != None:
            if self.cellMin != None and self.cellMax == None:
                # supply min if defined separately; useful for forcing zero
                # when zero may not be in table
                minMax = [self.cellMin, unit.seriesMinMax(refSeries)[1]]
            elif self.cellMin == None and self.cellMax != None:
                minMax = [unit.seriesMinMax(refSeries)[0], self.cellMax]
            else: minMax = None
        else: # no ref series, no minMax, cannot do anything
            minMax = None
        return minMax
        
    def extract(self, fmt='table', norm=1, rowStart=None, rowEnd=None, 
                      centerOffset=0, width=None):
        """ tage a segmetn from the 2d table datas
        width should not be negative
        norm: turn normalizing on or off; will change into list, even if an array

        >>> a = Table([[1,2,3], [4,5,6]])
        >>> a.extract('table', 1, 0, 1, 2)
        [[1.0, 0.0, 0.5]]
        """
        fmt = fmt.lower() # lower for reading values
        if rowStart == None: rowStart = 0
        if rowEnd == None: rowEnd = len(self.data)
        if centerOffset == None: centerOffset = 0
        if width == None: width = self.colCount
        elif width <= 0: width = 1 # never less than == 0
            
        # provide modulus of start
        rowStart = rowStart % self.rowCount
        rowEnd = rowEnd % (self.rowCount+1)

        data = self.data[rowStart:rowEnd]
        
        c = self._getCenter() + centerOffset # shift index value
        lOffset, rOffset = drawer.intHalf(width)

        # note: these values may exceed index values:
        # will be wraped with the drawer util
        lSlice = (c - lOffset)
        rSlice = (c + rOffset)

        # this will force that a copy is made and og data is not altered
        dataFilter = []

        if 'pair' in fmt: fmtCellExtract = 'pair'
        elif 'indexactive' in fmt: fmtCellExtract = 'indexactive'
        elif 'indexpassive' in fmt: fmtCellExtract = 'indexpassive'
        # these must follow searches above
        elif 'index' in fmt: fmtCellExtract = 'index'
        elif 'active' in fmt: fmtCellExtract = 'valueactive'
        elif 'passive' in fmt: fmtCellExtract = 'valuepassive'          
        else: fmtCellExtract = 'value' # default
        
        for step in data:
            dataFilter.append(drawer.listSliceWrap(step, lSlice, 
                                                    rSlice, fmtCellExtract))

        # tabular output
        if fmt == 'table': # should these range be provided?
            # cannot provide values to getMinMax; will return None if both
            # min and max not set, and unit proc will find automatically
            if norm: return unit.unitNormRangeTable(dataFilter, self._getMinMax())
            else: return dataFilter
            
        # read tabel and concat into one list
        elif 'flat' in fmt: # 
            if 'column' in fmt: # must rotate to read columns
                dataFilter = self._rotate(dataFilter)
            # 'row' or default
            dataFlat = []
            for row in dataFilter: 
                if 'reflect' in fmt or 'flip' in fmt: row.reverse()
                for val in row:
                    dataFlat.append(val)
            if norm: # minMax may be None
                dataFlat = unit.unitNormRange(dataFlat, self._getMinMax(dataFlat))
            return dataFlat
        # lists of data based on row/col operations; 
        # one value per row/col; min is always 0, max may be much greater
        else:             
            if 'column' in fmt: # must rotate to read columns
                dataFilter = self._rotate(dataFilter)
            # 'row' or default
            dataFlat = []            
            if 'sum' in fmt:
                for row in dataFilter:
                    x = 0
                    for val in row: 
                        x = x + val
                    dataFlat.append(x)  
            elif 'average' in fmt: 
                rowWidth = len(dataFilter[0]) # all rows must be the same
                for row in dataFilter:
                    x = 0
                    for val in row: x = x + val
                    # only change integers, as other number types may be here, 
                    # such as floats and decimals
                    if drawer.isInt(x): x = float(x)
                    dataFlat.append(x/rowWidth)
            elif 'product' in fmt: # multiply each value
                for row in dataFilter:
                    x = 1 # init value here is 1
                    for val in row: x = x * val
                    dataFlat.append(x)
            # noramlization for all but binary
            if norm:
                dataFlat = unit.unitNormRange(dataFlat, self._getMinMax(dataFlat))
            return dataFlat






#-----------------------------------------------------------------||||||||||||--

class TestOld:

    def __init__(self):
        self.testTable()
        



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testTable(self):
        for test in [[[0,1,0,2],[1,1,2,1],[0,1,1,0],[1,0,2,0]],
                         [[0,1],[2,3],[4,5]], 
                         [[0,1,2,3,4], [5,6,7,8,9]]
                        ]:
            a = Table(test)
            for fmtStr in a.outFmt:
                post = a.extract(fmtStr, 0)

#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)