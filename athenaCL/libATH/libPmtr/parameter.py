#-----------------------------------------------------------------||||||||||||--
# Name:          parameter.py
# Purpose:       public interface to all parameter objects.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2007 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import os, copy, random
from athenaCL.libATH import drawer
from athenaCL.libATH import error
from athenaCL.libATH.libPmtr import basePmtr
from athenaCL.libATH.libPmtr import valueSingle
from athenaCL.libATH.libPmtr import valueSingleOmde
from athenaCL.libATH.libPmtr import valueFile
from athenaCL.libATH.libPmtr import rhythmSingle
from athenaCL.libATH.libPmtr import textureStatic
from athenaCL.libATH.libPmtr import cloneStatic
from athenaCL.libATH.libPmtr import cloneFilter

# modules where parameters can be found
pmtrModules = (valueSingle, valueSingleOmde, valueFile, 
                    rhythmSingle, textureStatic, cloneStatic, cloneFilter)

_MOD = 'parameter.py'

#-----------------------------------------------------------------||||||||||||--
# full pmtr names are the name of the object in the module file
# though first character is caped
genPmtrNames = {
    # original (pre 1.1) parameter objects
    'bg' :'basketGen',
    'c'  :'constant',
    'cg' :'cyclicGen',
    'ss' :'sampleSelect',
    'as' :'analysisSelect',
    # general pmtr objects
    'bs' :'basketSelect', # given a fixed list, use unit interval vals to select
    'ds' :'directorySelect',
    'cf' :'constantFile', # provide a file path as a constant
    # output conversion to a different type format or display
    'tf' :'typeFormat',
    'oo' :'oneOver', # any value over one
    #'cp' :'convertPulse' # convert a pulse to seconds, or convert rhythm po to g
    # data access
    'pr' :'pathRead',
    # numerical
    'fs' :'fibonacciSeries',
    'vs' :'valueSieve',
    'sf' :'sieveFunnel',
    'sl' :'sieveList',
    'lp' :'listPrime', 
    'vp' :'valuePrime',
    # chaotic
    'lm' :'logisticMap',
    'hb' :'henonBasket', # collect henon values, normalize
    'lb' :'lorenzBasket', # collect lorenze values, normalize
    # tools
    'n'  :'noise',
    'm'  :'mask',
    'ms' :'maskScale', # takes values, normalize, and then map to pmtr objs
    'mr' :'maskReject', # reject values w/n mask region

    #'mc' : 'maskCompressor' # model dyamic processors
    #'me' : 'maskExpander' # model dyamic processors, based on rejection?

    'fb': 'funnelBinary', # dynamic rounding
    'a'  :'accumulator',
    'q'  :'quantize',
    # markov generators
    'mv' :'markovValue',        # provide string specification
    'mga':'markovGeneratorAnalysis', # provide a PO, a number of gens, analyze
    #'ma':'markovAnalysis' # provide a list/file to analyze
    # automata generators
    'cv' : 'caValue',
    'cl' : 'caList', # non unit-interval version
    # meta-generators
    'ig' :'iterateGroup', # pos/neg for skip, repeat
    'iw' :'iterateWindow', # select from a list of pmtrObjs
    'ih' :'iterateHold', # fill list from pmtrObj and select
    'ic' :'iterateCross', # cross b/n two pmtr objs w/ unit control
    'is' :'iterateSelect', # fill a list, select w/ unit control
    'sah' :'sampleAndHold', # only call generator when trigger is met

    # python raw code tools
    #'lc': 'listComprehension',  provide a list comprehension expression?

    # 8 wave types
    'ws' :'waveSine',
    'wc' :'waveCosine',
    'wpd':'wavePowerDown',
    'wpu':'wavePowerUp',
    'wp' :'wavePulse',
    'wsd':'waveSawDown',
    'wsu':'waveSawUp',
    'wt' :'waveTriangle',
    # 12 random types
    'ru' :'randomUniform',
    'rl' :'randomLinear',
    'ril':'randomInverseLinear',
    'rt' :'randomTriangular',
    'rit':'randomInverseTriangular',
    're' :'randomExponential',
    'rie':'randomInverseExponential',
    'rbe':'randomBilateralExponential',
    'rg' :'randomGauss',
    'rc' :'randomCauchy',
    'rb' :'randomBeta',
    'rw' :'randomWeibull',

    # envelope generators (rhythm pmtr objs using break point)
    # all support relative (proportion to duration) and absolute (seconds)
    # 'ert' : 'envelopeRhythmTrapezoid', # convert rhtyhm gen to variable pulse
    # 'eru' : 'envelopeRhythmUnit', # convert rhtyhm gen to unit envelope
    # 'era' : 'envelopeRhythmAdsr', # convert rhtyhm gen to adsr

    'egt' : 'envelopeGeneratorTrapezoid', # convert gen to variable pulse seq
    'egu' : 'envelopeGeneratorUnit', # convert gen to unit envelope
    'ega' : 'envelopeGeneratorAdsr', # convert gen to adsr


    # break point functions
    'bpl':'breakPointLinear',
    'bpp':'breakPointPower',
    'bphc':'breakPointHalfCosine', # half cosine interpolation
    'bpf':'breakPointFlat',

# use embedded parameter obj to create values (x) and time or event segments
# could be breakPointConstructor, dynamicPoint, breakGraph
    'bgl':'breakGraphLinear', 
    'bgp':'breakGraphPower', 
    'bghc':'breakGraphHalfCosine', 
    'bgf':'breakGraphFlat', 

    # operators
    'oa' :'operatorAdd',
    'os' :'operatorSubtract',
    'om' :'operatorMultiply',
    'od' :'operatorDivide',
    'op' :'operatorPower',
    'oc' :'operatorCongruence', # moduls
    # formerly hidden
    'sr' :'staticRange',
    'si' :'staticInst',
    }

rthmPmtrNames = {
    # rhythm objects
    # for len(k), define unique pulses for values, use ca grid to gen
    # exclude continuous; have accent value produced by a generator po
    #'cr' : 'caRhythm', # binary interpretation?
    'cs'    :'convertSecond',
    'cst' :'convertSecondTriple',
    'pt'    :'pulseTriple',
    'ba'    :'binaryAccent',
    'gr'    :'gaRhythm', 
    'l' :'loop',
    'ps'    :'pulseSieve',
    'rs'    :'rhythmSieve',
    'irg' :'iterateRhythmGroup',
    'irw' :'iterateRhythmWindow',
    'irh' :'iterateRhythmHold',
    'mp'    :'markovPulse', # directly specify markov string
    'mra' :'markovRhythmAnalysis', 
    }
    
textPmtrNames = {
    'pml' :'parallelMotionList',
    #'nrs' :'nonRedundantSwitch', # removed 1.4.4
    'mto' :'maxTimeOffset',
    'lws' :'loopWithinSet',  # here multisets are refered to as sets
    'ols' :'ornamentLibrarySelect', # was ornamentLibrary
    'omd' :'ornamentMaxDensity', # was ornamentDensity
    'lfm' :'levelFieldMonophonic',
    'lom' :'levelOctaveMonophonic',
    'lfp' :'levelFieldPolyphonic',
    'lop' :'levelOctavePolyphonic',
    'lep' :'levelEventPartition',

    'imc' :'interpolationMethodControl',
    'lfd' :'levelFrameDuration',
    'pic' :'parameterInterpolationControl',
    'sst' :'snapSustainTime',
    'set' :'snapEventTime',

    'tec' :'totalEventCount',
    'tsc' :'totalSegmentCount', 
    'edp' :'eventDensityPartition',
    'lec' :'levelEventCount', 
    'psc' :'pitchSelectorControl', 
    'msc' :'multisetSelectorControl', 
    'pdf' :'pathDurationFraction', # on or off; default is on
    }

clonePmtrNames = {
    'trs' :'timeReferenceSource', # was timeReference
    'rmt' :'retrogradeMethodToggle', # was retrogradeMethod
    }

filterPmtrNames = {
    'b'  :'bypass',
    'r'  :'replace',
    'ob' :'orderBackward',
    'or' :'orderRotate',
    'pl' :'pipeLine',
    'fa' :'filterAdd', # cannot use 'fs': already takne by fibonaccit
    'fm' :'filterMultiply',
    'fd' :'filterDivide', # not sure this is necessary
    'fma':'filterMultiplyAnchor',
    'fda':'filterDivideAnchor',
    'fp' :'filterPower',

    'fq' :'filterQuantize', # quantize as a filter; better than a funnel
    'ffb':'filterFunnelBinary', # convert to binary based on boundary
    'mf': 'maskFilter',
    'msf': 'maskScaleFilter',
    #'mcf': 'maskCompressorFilter',
    }


#-----------------------------------------------------------------||||||||||||--

# cannot store all parameters, as key classes may happen between libraries
genPmtrObjs = genPmtrNames.values() # values are class names
rthmPmtrObjs = rthmPmtrNames.values()
textPmtrObjs = textPmtrNames.values()
clonePmtrObjs = clonePmtrNames.values()
filterPmtrObjs = filterPmtrNames.values()

# all parameter objects; juts the full names, as a list (no clashes)
allPmtrObjs = (rthmPmtrObjs + genPmtrObjs + 
                    textPmtrObjs + clonePmtrObjs + filterPmtrObjs)

pmtrLibNames = {
    'g' : 'genPmtrObjs',
    'r' : 'rthmPmtrObjs',
    't' : 'textPmtrObjs',
    'c' : 'clonePmtrObjs',
    'f' : 'filterPmtrObjs',
    }
    
    
    
#-----------------------------------------------------------------||||||||||||--
# parameter objects to add:

# eventRead: read values from the current event
# including amp, pan, oct, field, bpm, 
# embed a filter parameter object to allow processing this value?
# can be used, as a filter processes all values at once...
# what if read from the parameter this this is in ?
# this a paradox...

# interpolate, fade, or morph?
# need a way to move b/n two things
# provide a 0 to 1 attractor to determine movement

# chaos: multiple output parameter objects
# select which parameer you want: x or y, standard map, henon, lorenze

# binary realizations: take numbers and convert to binary
# read 1/0 from this realization as a list, seletor to read from position



#-----------------------------------------------------------------||||||||||||--

def pmtrLibParser(usrStr):
    """convert lib names into user strings"""
    parsed = drawer.acronymExpand(usrStr, pmtrLibNames)
    if parsed == None:
        raise ValueError, 'bad parameter library provided: %s' % usrStr
    return parsed
    
def pmtrLibTitle(libName):
    """convert lib names into user strings"""
    if libName == 'genPmtrObjs':
        name = 'Generator'
    elif libName == 'rthmPmtrObjs':
        name = 'Rhythm Generator'
    elif libName == 'textPmtrObjs':
        name = 'Texture Static'
    elif libName == 'clonePmtrObjs':
        name = 'Clone Static'
    elif libName == 'filterPmtrObjs':
        name = 'Filter'
    else:
        raise ValueError, 'bad parameter library provided: %s' % libName
    return '%s %s' % (name, 'ParameterObject')

def pmtrLibList(libName):
    """get a sorted list of names from a lib name"""
    if libName == 'genPmtrObjs':
        data = genPmtrObjs
    elif libName == 'rthmPmtrObjs':
        data = rthmPmtrObjs
    elif libName == 'textPmtrObjs':
        data = textPmtrObjs
    elif libName == 'clonePmtrObjs':
        data = clonePmtrObjs
    elif libName == 'filterPmtrObjs':
        data = filterPmtrObjs
    else:
        raise ValueError, 'bad parameter library provided: %s' % libName
    data = list(data)
    data.sort()
    return data


#-----------------------------------------------------------------||||||||||||--
def pmtrTypeParser(typeName, libName='genPmtrObjs'):
    """utility functions for parsing user paramter strings into proper
    parameter names. accepts short names and long names, regardless of case
    does not raise an error if no match: returns string unmodified
    parameters can have the same abbreviation if they are in different libraries
    """
    assert typeName != None 
    #print _MOD, 'pmtrTypeParser', typeName, libName

    usrStr = copy.deepcopy(typeName)
    usrStr = drawer.strScrub(usrStr, 'lower')
    # get all parameter names in a dictionary
    if libName == 'genPmtrObjs':
        pmtrNames = genPmtrNames
    elif libName == 'rthmPmtrObjs':
        pmtrNames = rthmPmtrNames
    elif libName == 'textPmtrObjs':
        pmtrNames = textPmtrNames
    elif libName == 'clonePmtrObjs':
        pmtrNames = clonePmtrNames
    elif libName == 'filterPmtrObjs':
        pmtrNames = filterPmtrNames
    else:
        raise error.ParameterObjectSyntaxError, 'no parameter library named: %r' % usrStr
    for key in pmtrNames.keys():
        className = pmtrNames[key]
        if usrStr == key:
            return className
        elif usrStr == className.lower():
            return className
    # if not mattched, raise an error
    raise error.ParameterObjectSyntaxError, 'no parameter named %r in %s' % (usrStr, pmtrLibTitle(libName)) 

#-----------------------------------------------------------------||||||||||||--
# arguments for parameter objects are assigned at creation of object
# they are not tested, however, until when check args is called
# string parsers, then, do not raise an error, but keep user input


def locator(usrStr, libName='genPmtrObjs'):
    # convert acronum or other into fully named parameter string
    assert usrStr != None
    #print _MOD, 'locator', usrStr, libName
    objType = pmtrTypeParser(usrStr, libName) #check type string
    # fix case, capitalize lead character:
    if objType == None: 
        raise error.ParameterObjectSyntaxError, 'name error: no parameter named %r' % usrStr 
    objType = objType[0].upper() + objType[1:]
    modFound = None
    # this actually looks through external module files
    for mod in pmtrModules: # look through all mods for
        reload(mod)
        classList = dir(mod)
        if objType in classList:
            modFound = mod
            break
    if modFound == None:# failure
        raise error.ParameterObjectSyntaxError, 'name error: no parameter named %r' % usrStr
    # return reference to object, and string name of object
    # may want to retrun objType first char to lower case?
    return modFound, objType

def factory(rawArgs, libName='genPmtrObjs', refDict=None):
    """this is used only for loading and returning an object
    can return obj or parsed args
    first thing in list must be a string, type def

    libName can be a list or a string
    rawArgs is a list of python data types, starting with the po name
    exceptions that may be raised: error.ParameterObjectSyntaxError
    """
    reload(basePmtr) # reload base class
    if not drawer.isList(rawArgs):
        # NOTE: this is experimental: seeing if this causes 
        # problmes. if so revert to method below
        rawArgs = eval(drawer.restringulator(rawArgs))

        # old method simply put rawArgs, if a string, as a first argument
        # rawArgs = [rawArgs,] # add to a list, could be a single str

    # first arg is always a string, naming the parameter type
    # obj args could be empty if requires no arguments
    objType, objArgs = rawArgs[0], list(rawArgs[1:])

    libOpt = [] # option libs
    if not drawer.isList(libName):
        libOpt.append(libName)
    else: 
        libOpt = libName
    for i in range(0, len(libOpt)):
        name = pmtrLibParser(libOpt[i]) # name of possible library
        #print _MOD, 'testing', libOpt, name, i, rawArgs
        try: # will raise exception on error
            mod, modStr = locator(objType, name) #check type string
        except error.ParameterObjectSyntaxError, e: modStr = None
        if modStr == None:
            if i != len(libOpt) - 1:
                continue # if not the last one to try
            else:
                raise error.ParameterObjectSyntaxError, 'parameter lib error (%s:%s)' % (
                                                                          name, objType) 
        else: # got a good object
            break
            # failure
    pmtrObjAttr = getattr(mod, modStr)
    #print _MOD, 'factory loading object', mod, objType
    pmtrObj = pmtrObjAttr(objArgs, refDict)
    return pmtrObj


# this may be no longer necessary
def doc(rawName, libName='genPmtrObjs', fmt='full'):
    """just get the doc string of a parameter object"""
    mod, objType = locator(rawName, libName) #check type string
    objRef = getattr(mod, objType) # gets ref, not obh
    obj = objRef([], {})
    return obj.reprDoc(fmt)
    
#     if fmt == 'full':
#         return docStr
#     elif fmt == 'paragraph': # exclude first line
#         msg = docStr.split('\n')[1:]
#         return ' '.join(msg)
#     elif fmt == 'args':
#         return docStr.split('\n')[0]


#-----------------------------------------------------------------||||||||||||--
#-----------------------------------------------------------------||||||||||||--

# run tests
class TestOld:
    def __init__(self):
        # call test methods
        #self.testBpf()
        #self.testFile()
        self.testParameter()
        #self.testRhythm()
        #self.testSelect()
        self.testSieve()

    def testParameter(self):
        self.wrap(self.testStaticInst, 1)
        self.wrap(self.testStaticRange, 1)
        self.wrap(self.testCyclicGen, 1)
        self.wrap(self.testConstant, 1)
        self.wrap(self.testBasketGen, 1)

        self.wrap(self.testWaveSine, 1)
        self.wrap(self.testWaveCosine, 1)
        self.wrap(self.testWaveSawUp, 1)
        self.wrap(self.testWaveSawDown, 1)
        self.wrap(self.testWavePulse, 1)
        self.wrap(self.testWaveTriangle, 1)

        self.wrap(self.testWavePowerUp, 1)
        self.wrap(self.testWavePowerDown, 1)

        self.wrap(self.testRandomUniform, 2)
        self.wrap(self.testRandomLinear, 2)
        self.wrap(self.testRandomInverseLinear, 2)
        self.wrap(self.testRandomTriangular, 2)
        self.wrap(self.testRandomInverseTriangular, 2)

        self.wrap(self.testRandomExponential, 2)
        self.wrap(self.testRandomInverseExponential, 2)
        self.wrap(self.testRandomBilateralExponential, 2)

        self.wrap(self.testRandomGauss, 2)
        self.wrap(self.testRandomCauchy, 2)
        self.wrap(self.testRandomBeta, 2)
        self.wrap(self.testRandomWeibull, 2)

        self.wrap(self.testFibonacciSeries, 2)
        
        
    def testSieve(self):
        self.wrap(self.testIterateWindow, 1)
        self.wrap(self.testIterateGroup, 1)
        self.wrap(self.testValueSieve, 2)

    def testFile(self):
        self.wrap(self.testDirectorySelect, 1)
        self.wrap(self.testSampleSelect, 2)

    def testBpf(self):
        self.wrap(self.testAccumulator, 2)
        self.wrap(self.testBreakPointLinear, 1)
        self.wrap(self.testBreakPointPower, 1)

    def testRhythm(self):
        self.wrap(self.testBinaryAccent, 1)
        self.wrap(self.testGaRhythm, 1)
        self.wrap(self.testLoop, 1)
        self.wrap(self.testSievePulse, 1)
        self.wrap(self.testConvertSecond, 1)

    def testSelect(self):
        self.wrap(self.testGaRhythm, 1)

    def wrap(self, method, iterations=1):
        from athenaCL.libATH import dialog
        for i in range(0, iterations):
            os.system('clear')
            method()
            print '=' * 80
            dialog.askStr('for NEXT press return')
            #time.sleep(2)

    def _testBasic(self, obj, count=10, refDict=None):
        """basic procedures for testing"""
        if refDict == None:
            refDict = {}
            refDict['bpm'] = 120
            refDict['stateCurrentChord'] = (0,1)
            refDict['stateCurrentPitchRaw'] = 0
            refDict['ssdr'] = ['/src/athenaCL/libATH/ssdir']
        print obj.reprDoc()
        print obj.checkArgs()
        print obj.repr()
        out = []
        for x in range(count):
            refDict['stateCurrentPitchRaw'] = (random.choice([0,1]))
            out.append(obj(x, refDict))
        print out
        print # need a space
            
    #-----------------------------------------------------------------------||--

    def testBinaryAccent(self):
        obj = factory(('binaryAccent', ((2,1),(4,1))), 'rthmPmtrObjs')
        self._testBasic(obj, 10)

    def testGaRhythm(self):
        obj = factory(('gaRhythm', ((3,1),(4,1),(5,1,0),(6,1,1))),
                            'rthmPmtrObjs')
        self._testBasic(obj, 20)

        obj = factory( ('gaRhythm', ((3,1),(4,1),(5,1,0),(6,1,1)), 
                                             .70, .025, .01, 'rw'), 'rthmPmtrObjs')
        self._testBasic(obj, 20)

    def testLoop(self):
        obj = factory(('loop', ((3,1),(4,1),(5,1,0),(6,1,1)), 'oc'), 
                            'rthmPmtrObjs')
        self._testBasic(obj, 10)

        obj = factory(('loop', ((3,1),(4,1),(5,1,0),(6,1,1)), 'rp'),
                            'rthmPmtrObjs')
        self._testBasic(obj, 10)

        obj = factory(('loop', ((3,1),(4,1),(5,1,0),(6,1,1)), 'oo'),
                            'rthmPmtrObjs')
        self._testBasic(obj, 10)


    def testSievePulse(self):
        obj = factory(('pulseSieve', '2|3', 9, (3,1,1), 'oo' ), 'rthmPmtrObjs')
        self._testBasic(obj, 20)

        obj = factory(('pulseSieve', '2|3', 9, (3,1,1), 'rw' ), 'rthmPmtrObjs')
        self._testBasic(obj, 20)

    def testConvertSecond(self):
        obj = factory(('convertSecond', ('waveSine', 30, 0, 1, 0)), 
                            'rthmPmtrObjs')
        self._testBasic(obj, 20)

    #-----------------------------------------------------------------------||--
    def testStaticInst(self):
        args = ('staticInst', 3,)
        self._testBasic(factory(args), 5)

    def testStaticRange(self):
        args = ('staticRange', (0, 50),)
        self._testBasic(factory(args), 5)


    #-----------------------------------------------------------------------||--
    def testCyclicGen(self):
        args = ('cyclicGen', 'ldu', 40, 70, 2.5)
        self._testBasic(factory(args), 20)

        args = ('cyclicGen', 'ld', 50, 60, 1)
        self._testBasic(factory(args), 20)

    def testConstant(self):
        args = ('constant', 'this is a constant',)
        self._testBasic(factory(args), 5)

    def testBasketGen(self):
        args = ('basketGen', 'rw', (230, 12, 'green'))
        self._testBasic(factory(args), 10)

        args = ('basketGen', 'oo', (230, 12, 'green'))
        self._testBasic(factory(args), 10)

        args = ('basketGen', 'rp', (230, 12, 'green'))
        self._testBasic(factory(args), 10)


    def testIterateGroup(self):
        args = ['iterateGroup', ('bg', 'oc', [3,8,1,7]), 
                                  ('bg', 'rc', [3,1,-2,-4]),]
        self._testBasic(factory(args), 20)

        args = ['iterateGroup', ('bg', 'oc', [3,8,1,7]), 
                 ('iw', (('bg', 'oc', [1,3,5]), ('bg', 'rc', [-1,-2])), 
                                                          ('c', 1), 'rw'),]
        self._testBasic(factory(args), 20)



    def testIterateWindow(self):
    
        # a double selection example
        args = 'iw', (('bg','rc',[0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5])),('bg', 'oc', [3,-2,3,-1]), 'oc'
        self._testBasic(factory(args), 40)

        # this extreme example is a test of the lte principle; not sure
        # if it makes a difference
        args = ['iterateWindow', (
        ('iw', (('bg','rc',[0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5])),('bg', 'oc', [3,-2,3,-1]), 'oc'), 
        ('iw', (('bg','rc',[0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5])),('bg', 'oc', [3,-2,3,-1]), 'oc'), 
        ('iw', (('bg','rc',[0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5]),('bg', 'rc', [0,1,2,3,4,5])),('bg', 'oc', [3,-2,3,-1]), 'oc')), 
              ('bg', 'oc', [3,-2,3,-1]), 'oc']
        self._testBasic(factory(args), 40)


        args = ['iterateWindow', (('ru',0,1), ('ru', 5,10), ('bg','rc',[4,4.5,5])), ('bg', 'rc', [3,8,7]), 'rc']
        self._testBasic(factory(args), 20)


    def testQuantize(self):
        args = ['quantize',('a',0,('c',0)),
                                 ('a',.5,('c',.0125)),1,('c',1),('ru',0,5)]


    #-----------------------------------------------------------------------||--
    def testDirectorySelect(self):  
        args = ('directorySelect', 
                  '/src/athenaCL/libATH/ssdir', 'aif', 'rw')
        obj = factory(args)
        self._testBasic(obj, 20)

        args = ('directorySelect', 
                  '/src/athenaCL/libATH/ssdir', 'aif', 'oo')
        obj = factory(args)
        self._testBasic(obj, 20)


    def testSampleSelect(self):
        args = ('sampleSelect', ('metal03.aif','cloth02.aif','latch01.aif'), 'rw')
        obj = factory(args)
        self._testBasic(obj, 20)

        args = ('sampleSelect', ('metal03.aif','cloth02.aif','latch01.aif'), 'rp')
        obj = factory(args)
        self._testBasic(obj, 20)

        args = ('sampleSelect', ('metal03.aif','cloth02.aif','latch01.aif'), 'oo')
        obj = factory(args)
        self._testBasic(obj, 20)


    #-----------------------------------------------------------------------||--
    def testWaveSine(self):
        args = ('waveSine', 't', 30, 0, 0, 10)
        self._testBasic(factory(args), 30)

    def testWaveCosine(self):
        args = ('waveCosine', 't', 30, 0, 0, 10)
        self._testBasic(factory(args), 30)

    def testWaveSawUp(self):
        args = ('waveSawUp', 't', 30, 0, 0, 10)
        self._testBasic(factory(args), 30)

    def testWaveSawDown(self):
        args = ('waveSawDown', 't', 30, 0, 0, 10)
        self._testBasic(factory(args), 30)

    def testWavePulse(self):
        args = ('wavePulse', 't', 30, 0, 0, 10)
        self._testBasic(factory(args), 30)

    def testWaveTriangle(self):
        args = ('waveTriangle', 't', 30, 0, 0, 10)
        self._testBasic(factory(args), 30)

    def testWavePowerUp(self):
        args = ('wavePowerUp', 't', 30, 0, 2.5, 0, 10)
        self._testBasic(factory(args), 30)

    def testWavePowerDown(self):
        args = ('wavePowerDown', 't', 30, 0, 2.5, 0, 10)
        self._testBasic(factory(args), 30)

    #-----------------------------------------------------------------------||--
    def testRandomUniform(self):
        args = ('randomUniform', 0, 10)
        self._testBasic(factory(args), 30)

    def testRandomLinear(self):
        args = ('randomLinear', 20, 50)
        self._testBasic(factory(args), 30)

    def testRandomInverseLinear(self):
        args = ('randomInverseLinear', 20, 50)
        self._testBasic(factory(args), 30)

    def testRandomTriangular(self):
        args = ('randomTriangular', 20, 50)
        self._testBasic(factory(args), 30)

    def testRandomInverseTriangular(self):
        args = ('randomInverseTriangular', 20, 50)
        self._testBasic(factory(args), 30)

    #-----------------------------------------------------------------------||--
    def testRandomExponential(self):
        args = ('randomExponential', .5, 20, 2000)
        self._testBasic(factory(args), 30)

    def testRandomInverseExponential(self):
        args = ('randomInverseExponential', .5, 20, 2000)
        self._testBasic(factory(args), 30)

    def testRandomBilateralExponential(self):
        args = ('randomBilateralExponential', .5, 20, 2000)
        self._testBasic(factory(args), 30)

    #-----------------------------------------------------------------------||--
    def testRandomGauss(self):
        args = ('randomGauss', .5, 1, 1, 9)
        self._testBasic(factory(args), 30)

    def testRandomCauchy(self):
        args = ('randomCauchy', .1, .5, 1, 9)
        self._testBasic(factory(args), 30)

    def testRandomBeta(self):
        args = ('randomBeta', .1, .1, 1, 9)
        self._testBasic(factory(args), 30)

    def testRandomWeibull(self):
        args = ('randomWeibull', .5, 2.0, 1, 9)
        self._testBasic(factory(args), 30)

    #-----------------------------------------------------------------------||--
    def testFibonacciSeries(self):  
        args = ('fibonacciSeries', 1, 5, 1, 0, 'rw')
        self._testBasic(factory(args), 10)
    
        args = ('fibonacciSeries', 400, -8, 50, 20, 'rp')
        self._testBasic(factory(args), 10)
    
        args = ('fibonacciSeries', 2, -20, 1, 0, 'oo')
        self._testBasic(factory(args), 10)

    #-----------------------------------------------------------------------||--
    def testValueSieve(self):    
        args = ('valueSieve', '3|4|13', 26, 1, 0, 'rw')
        self._testBasic(factory(args), 20)

        args = ('valueSieve', '3|4|13', 19, 1, 0, 'rp')
        self._testBasic(factory(args), 20)

        args = ('sieveList', '3|4|13', -12, 12, 'b', 'oc')
        self._testBasic(factory(args), 20)

        args = ('sieveList', '3|4|13', -12, 12, 'WIDTH', 'rp')
        self._testBasic(factory(args), 20)

    def testLogisticMap(self):
        pass

    def testPathRead(self):
        pass




    #-----------------------------------------------------------------------||--
    def testBreakPointLinear(self):
        args = ('breakPointLinear', 'e', 'l', ((0,0), (5,1), (10,.5)))
        self._testBasic(factory(args), 20)

    def testBreakPointPower(self):
        args = ('breakPointPower', 'e', 'l', ((0,0), (5,1), (10,.5)), 2)
        self._testBasic(factory(args), 20)

    def testAccumulator(self):
        args = ('accumulator', 20, ('waveSine', 30, 0, 10, 0),)
        self._testBasic(factory(args), 20)

        args = ('accumulator', 20, ('bg', 'rc', (100, 10, 1)))
        self._testBasic(factory(args), 20)


if __name__ == '__main__':
    TestOld()





# command line tests
