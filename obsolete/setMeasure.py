#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          setMeasure.py
# Purpose:       provides class and subclass for SetMeasur .
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2006 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--


from athenaCL.libATH import SC

_MOD = 'setMeasure.py'

#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--


class SetMeasure:
    """general class for all SetMeasures"""
    
    def __init__(self, tonic=None, dominant=None, scObj=None): 
        """convert any foreign data inot proper Multiset objects"""
        if scObj == None:
            scObj = SC.SetClass()
        self.scObj = scObj
        #opt tonic/dom args when inherited
        if tonic == None or dominant == None:
            self.tonic = None
            self.dominant = None
        # if given scTriples, load set objects
        else:
            self.tonic = self._objectifySet(tonic)
            self.dominant = self._objectifySet(dominant)

    def _objectifySet(self, usrData):
        """check an scTruiple to see if it is an object; if not objectify"""
        if hasattr(usrData, 'get'): # its a Multiset object
            return usrData
        else:
            return SC.Multiset(None, usrData, self.scObj)


    def _fillMinMax(self):
        """gets actual range for setMeasure similarity values"""
        rl = self.scObj.analysisRange(self.srcKey)
        self.min = rl['min']
        self.max = rl['max']
            
    def compareSet(self, SCx, SCy, tni=1):
        "provide analysis of two arbitrary sets"
        SCx = self._objectifySet(SCx)
        SCy = self._objectifySet(SCy)
        #print _MOD, SCx, SCy
        try:
            value = self.scObj.analysis(self.srcKey, SCx, SCy, tni)
        except ZeroDivisionError:
            value = None # if no comparison possible
        #print _MOD, 'compareSet', SCx, SCy, value
        return value

    def compareSelf(self, tni=1):
        """provide analysis of two internal set objects"""
        return self.compareSet(self.tonic, self.dominant, tni)
            
    def searchSim(self, SCx=None, pcentSimRange=(.5, 1), tolarance=0, 
                             tniTog=1, cardRange=(1,12)):
        """input source key with type of analyss, sc-x is initial chord
        min/max are the range of similarity values accepted; 
        search all chords, return 0 on failure to find match
        returns a list of scTriple, value pairs
    
        # search all chords first and store results
        # might need to test card of sc_x
        # list of chords to compare, after taking into account tn/tni
        """
        if SCx == None: # use tonic if no scTriple is provided
            SCx = self.tonic.get('sc')

        scToCompare = self.scObj.getAllScTriples(cardRange, tniTog)
        if len(scToCompare) == 0:   # in_case something goes wrong
            print(_MOD, 'bad cardRange', cardRange, end=' ')
            return None

        analysisValues = []     # enter as pairs: (chord, value)          
        for scTriple in scToCompare:
            # egines that have tn/tni distinction
            if self.srcKey in ['ATMEMB','REL','TpRel']: 
                value = self.compareSet(SCx, scTriple, tniTog)
            else:
                value = self.compareSet(SCx, scTriple)
            if value == None:
                print(_MOD, 'failed set comparison:', SCx, scTriple)
                continue

            analysisValues.append((scTriple, value))
            
        # get ranges from_usr percentage for_particular path_engine
        if self.min > self.max:       # 1.0 > 0.0 max similarity          
            high = self.min
            low  = self.max
        else:
            high = self.max           # 0.0 < 1.0 max similarity     
            low  = self.min
        usrMin = pcentSimRange[0] 
        usrMax = pcentSimRange[1]
        if usrMin < 0.00: usrMin = 0.00  # 0%
        if usrMax > 1.00: usrMax = 1.00  # 100%
            
        totRange = abs(high - low)       # in_scale of analysis algorithm
        initMin = totRange * usrMin # multiply by percentage to find actual val
        initMax = totRange * usrMax
        
        incrMult = 0 # multiple tolarance to increase selection range
        lastTry = 0
        matchingScTriples = []
        
        numFirstR = 0   # track number of matches within initial range
        while 1:
            curMin = initMin - ((tolarance * incrMult) * totRange)
            if curMin < low:
                curMin = low
            curMax = initMax + ((tolarance * incrMult) * totRange)
            if curMax > high:
                curMax = high
            if curMin <= low and curMax >= high:
                lastTry = 1 # range already expanded, must end

            for scTriple, analValue in analysisValues: 
                if analValue >= curMin and analValue <= curMax:
                    matchingScTriples.append((scTriple, analValue)) 

            if incrMult == 0:
                numFirstR = len(matchingScTriples)
                if tolarance == 0:
                    break
            if len(matchingScTriples) > 0: lastTry = 1          
            if lastTry: break
            incrMult = incrMult + 1 # increase to increase range

        return matchingScTriples, numFirstR, len(matchingScTriples)




#-----------------------------------------------------------------||||||||||||--


# these classes inherit frm M_path: do not need to 
# call M_path instance.
# each class has a multipath atribute where the multi is stored, 
# and passed to the interface

# percent sim range gives range of 'correct' similarities that pass_test. 
# always between 0 and 1, w/ 1==max sim: so a range of (.65, .85) 
# would try_to only 
# find matching sc's in that range
# if fail, then the range is expanded by the tolarance percent
# if tolarance is .05 (5%) than the above range would be atmotaically re-serched 
# at (.60, .80), until maximum range is reached

# table used to convert from old names
# also used to check available methods
engines = {
        'K'   : 'morris_K',      
     # 'pRel'  : 'castren_TpREL', # requres a 'n' argument 
     # 'R1'  : 'self.forte_R1',           
        'R2'      : 'Forte_r2',         
     # 'R0'  : 'self.forte_R0',           
     # 'SI'   : 'teitelbaum_SI',     #only pairs of same card   
        'SIM'     : 'morris_SIM',             
        'ASIM'  : 'morris_ASIM',          
     # 'sf'   : 'lord_sf',        # only pairs same cardinality
        'IcVSIM': 'isaacson_IcVSIM',     
        'IcVD1' : 'rogers_IcVD1',       
        'IcVD2' : 'rogers_IcVD2',        
        'COST'  : 'Rogers_COST',         
        'Ak'      : 'Rahn_Ak',               
     # 'MEMBn' : 'rahn_MEMBn',       # requires a 'n' argument
        'TMEMB' : 'rahn_TMEMB',      
        'ATMEMB': 'Rahn_Ak',             
        'REL'     : 'lewin_REL',              
        'TpRel' : 'castren_TpREL',        
        }

class R2(SetMeasure): 
    """Forte (1973a:46-60). No Tn/TnI distinction"""
        #This engine matches common 
        # vector elements, three or more, to find adjacent set classes
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Forte r2'
        self.srcKey = 'R2'
        self.tnStat = 0 # 0 == no tn/tni diff
        self.cite = 'Forte' # (1973a:46-60)'
        self._fillMinMax()

class K(SetMeasure): 
    """Morris (1979-80). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Morris K'
        self.srcKey = 'K'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Morris' # (1979-80)'
        self._fillMinMax()

class SIM(SetMeasure): 
    """Morris (1979-80). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Morris SIM'
        self.srcKey = 'SIM'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Morris' # (1979-80)'
        self._fillMinMax()

class ASIM(SetMeasure): 
    """Morris (1979-80). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Morris ASIM'
        self.srcKey = 'ASIM'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Morris' # (1979-80)'
        self._fillMinMax()

class IcVSIM(SetMeasure):
    """Isaacson (1990). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Isaacson IcVSIM'
        self.srcKey = 'IcVSIM'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Isaacson' # (1990)'
        self._fillMinMax()


class IcVD1(SetMeasure):
    """Rogers (1992). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Rogers IcVD1'
        self.srcKey = 'IcVD1'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Rogers' # (1992)'
        self._fillMinMax()

class IcVD2(SetMeasure):
    """Rogers (1992). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Rogers IcVD2'
        self.srcKey = 'IcVD2'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Rogers' # (1992)'
        self._fillMinMax()

class COST(SetMeasure):
    """Rogers (1992). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Rogers COST'
        self.srcKey = 'COST'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Rogers' # (1992)'
        self._fillMinMax()

class Ak(SetMeasure):  
    """Rahn (1979-80). No Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Rahn Ak'
        self.srcKey = 'Ak'
        self.tnStat  = 0 # 0 == no tn/tni diff
        self.cite = 'Rahn' # (1979-80)'
        self._fillMinMax()

class TMEMB(SetMeasure): 
    """Rahn (1979-80). Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Rahn TMEMB'
        self.srcKey = 'TMEMB'
        self.tnStat  = 1 # 0 == no tn/tni diff
        self.cite = 'Rahn' # (1979-80)'
        self._fillMinMax()

class ATMEMB(SetMeasure): 
    """Rahn (1979-80). Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Rahn ATMEMB'
        self.srcKey = 'ATMEMB'
        self.tnStat  = 1 # 0 == no tn/tni diff
        self.cite = 'Rahn' # (1979-80)'
        self._fillMinMax()

class REL(SetMeasure):  
    """Lewin 1979-80b. Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Lewin REL'
        self.srcKey = 'REL'
        self.tnStat  = 1 # 0 == no tn/tni diff
        self.cite = 'Lewin' # 1979-80b'
        self._fillMinMax()

class TpRel(SetMeasure): 
    """Castren. Tn/TnI distinction"""
    def __init__(self, tonic=None, dominant=None, scObj=None):
        SetMeasure.__init__(self, tonic, dominant, scObj)
        self.name = 'Castren T%REL'
        self.srcKey = 'TpRel'
        self.tnStat  = 1 # 0 == no tn/tni diff
        self.cite = 'Castren' # 1994'
        self._fillMinMax()









#-----------------------------------------------------------------||||||||||||--



class TestOld:
    def __init__(self):
        self.testPathMulti()


    def testPathMulti(self):
        a = ATMEMB((3,1,0),(3,1,0), None)


if __name__ == '__main__':
    a = TestOld()

