#-----------------------------------------------------------------||||||||||||--
# Name:          feedback.py
# Purpose:       models of biological feedback systems
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2007-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import random, copy
import unittest, doctest

from athenaCL.libATH import error
from athenaCL.libATH import drawer
from athenaCL.libATH import unit

_MOD = 'feedback.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)




# bipolar feedback: increases and decreases output
# hunting is a term used to describe oscillation around boundary
# Hunting is a self-exciting oscillation of a system, and is common in systems which incorporate feedback. It is an important phenomenon in many fields, including engineering, economics and biology.


# hunting as parametric variance; an object model of bipolar variance for algorithmic parameter generation

# In biological systems such as organisms, ecosystems, or the biosphere, most parameters must stay under control within a narrow range around a certain optimal level under certain environmental conditions.

# Any self-regulating natural process involves feedback and is prone to hunting. A well known example in ecology is the oscillation of the population of snowshoe hares due to predation from lynxes.

# Positive feedback is a feedback loop system in which the system responds to the perturbation in the same direction as the perturbation (It is sometimes referred to as cumulative causation). In contrast, a system that responds to the perturbation in the opposite direction is called a negative feedback system. 

# In the real world, positive feedback loops are always controlled eventually by negative feedback of some sort

# One example of a biological positive feedback loop is the onset of contractions in childbirth. When a contraction occurs, the hormone oxytocin is released into the body, which stimulates further contractions. This results in contractions increasing in amplitude and frequency.

#-----------------------------------------------------------------||||||||||||--

# as each sensor will produce a particle based on a common threshold 
# measure, the more sensorProducers, the larger the swings above and below the 
# threshold; a ratio of 1/10 sensor/threshold seems to be useful.

# if the threshold is very high, and particle life is too short, sensorProducers
# are not able to produce enough partilces to get to threshold
# solve by permitting sensorProducers to produce more than 1 particle?


class FeedbackError(Exception):
    pass


#-----------------------------------------------------------------||||||||||||--

class ParticleCore(object):
    def __init__(self, lifeCycle):
        """A model of a multi-state particle that is defined by an ordered series of states, and a number of frames at that state. 

        `lifeCycle` is a list of pairs; each pair gives a state (as a string letter) followed by a number of frames at which that state exists
        after all states have passed, the particle is dead.

        >>> pairs = [('a', 30), ('b',30)]
        >>> a = Particle(pairs)
        >>> a.lifeSpan
        60
        >>> a.lifeBounds
        {'a': (1, 30), 'b': (31, 60)}


        >>> pairs = [('a', 10)]
        >>> a = Particle(pairs)
        >>> a.lifeSpan
        10
        >>> a.lifeBounds
        {'a': (1, 10)}
        """
        if not drawer.isList(lifeCycle):
            raise error.ParticleSyntaxError('life cycle must be a list')
        self.lifeCycle = lifeCycle
        self.lifeBounds = {}
        self.lifeSpan = 0 # number of frames in life
        self._updateLifeSpan() # update lifeSpan and lifeBounds
        self.age = 0 # number of cycles passed
        self.state = self.lifeCycle[0][0] # get first state

    def _updateLifeSpan(self):
        """
        >>> pairs = [('a', 10)]
        >>> a = Particle(pairs)
        >>> a.lifeSpan = 0
        >>> a._updateLifeSpan()
        >>> a.lifeSpan
        10
        """
        self.lifeSpan = 0
        pos = 1 # age zero is not counted
        for key, num in self.lifeCycle:
            if num <= 0:
                raise error.ParticleSyntaxError('number of frames defined for state (%s) is less than or equal to zero' % num)

            self.lifeSpan = self.lifeSpan + num
            next = pos + num
            self.lifeBounds[key] = (pos, next-1) # one less
            pos = next

    def advance(self, ageStep=1):
        """Advance the particle one frame.

        The `ageStep` argumetn can be a function that returns a number or a number (value around 1).
        This value is rounded to the nearest integer; floating point values outside of .5 and 1.5 cause shifts.

        >>> pairs = [('a', 2)]
        >>> a = Particle(pairs)
        >>> a.advance()
        True
        >>> a.advance()
        True
        >>> a.advance()
        False

        >>> pairs = [('a', 2)]
        >>> a = Particle(pairs)
        >>> a.advance(2)
        True
        >>> a.advance(2)
        False

        >>> pairs = [('a', 1), ('b', 1), ('c', 1)]
        >>> a = Particle(pairs)
        >>> a.advance()
        True
        >>> a.state
        'a'
        >>> a.advance()
        True
        >>> a.state
        'b'
        >>> a.advance()
        True
        >>> a.state
        'c'
        >>> a.advance()
        False
        >>> a.state == None
        True
        """
        if drawer.isNum(ageStep):
            ageUnit = ageStep
        else:
            ageUnit = ageStep() # assume it is a function

        # Probabilistic rounding of floating point values
        ageUnitInt = drawer.floatToInt(ageUnit, 'weight')
        self.age += ageUnitInt

        if self.age > self.lifeSpan: # must be greater, not >=
            self.state = None
            return False # cant advance, as is dead
        # check each state in the life bounds, see if this age
        # is within the range of any of those bounds
        for key in self.lifeBounds:
            if (self.age >= self.lifeBounds[key][0] and self.age <= 
                self.lifeBounds[key][1]):
                self.state = key # assign new state
                break
        return True # still alive

    def isDead(self):
        """return boolean if particle is dead

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = Particle(pairs)
        >>> a.advance(3)
        True
        >>> a.isDead()
        False
        >>> a.state
        'b'
        >>> a.advance() # kills the particle
        False
        >>> a.isDead()
        True

        """
        if self.age > self.lifeSpan: return True # greater, not gt equal
        else: return False

    def getState(self):
        """return current state

        >>> lc = [('a', 1), ('b', 2)]
        >>> a = Particle(lc)
        >>> a.advance(3)
        True
        >>> a.getState()
        'b'
        """
        return self.state

    def reset(self):
        '''
        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = Particle(pairs)
        >>> a.advance(4)
        False
        >>> a.getState() == None
        True
        >>> a.isDead()
        True
        >>> a.reset()
        >>> a.isDead()
        False
        >>> a.state == None # no state until we advance
        True
        >>> a.advance()
        True
        >>> a.getState()
        'a'
        '''
        self.age = 0
        self.state = None
        self._updateLifeSpan()



#-----------------------------------------------------------------||||||||||||--
class Particle(ParticleCore):
    def __init__(self, lifeCycle):
        """A standard Particle
        """
        ParticleCore.__init__(self, lifeCycle)


    def __call__(self, ageStep=1):
        """advance the particle

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = Particle(pairs)
        >>> a(2)
        True
        >>> a.getState()
        'b'
        """
        return self.advance(ageStep)
        # will return 0 when dead

        # alternate approach that would permit multi-frame advance
        #for i in range(frame):
        #    ok = self._advance()
        #    if not ok: break # dead
        

    def __repr__(self):
        '''
        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = Particle(pairs)
        >>> a.advance(2)
        True
        >>> repr(a)
        '<Particle: state b; age 2; dead False>'
        >>> a.advance(1)
        True
        >>> repr(a)
        '<Particle: state b; age 3; dead False>'
        >>> a.advance(1)
        False
        >>> repr(a)
        '<Particle: state None; age 4; dead True>'
        >>> a.advance(1) # can age beyond death, but has no state
        False
        >>> repr(a)
        '<Particle: state None; age 5; dead True>'

        '''
        
        return '<Particle: state %s; age %s; dead %s>' % (self.state, self.age, self.isDead())




#-----------------------------------------------------------------||||||||||||--
class ParticleTransformer(ParticleCore):
    """Object for transforming and/or destroying Particles

    All particles share the same life span and state structure (lifeCycle).

    Particle's state is what is sensed at a given time

    particleTransformMap determines what is done each time the ParticleTransformer processes a Particle

    A ParticleTransformer does one processing routine per cycle; ParticleTransformer dies after processing is com,plete

    >>> lc = [('a', 1), ('b', 2)]
    >>> a = ParticleTransformer(lc)
    """

    def __init__(self, lifeCycle):
        ParticleCore.__init__(self, lifeCycle)

        # >>> pairs = [('a', 2)]


        # life span, however, is the focus of the particle at a given time
        # dynamic attention is then permitted
        # life span represented as other particles: [('a', 1), ('b', 2)]
        
        # provide a target and weighting for the most likely outcome
        # a weighting of None cause immediate distruction
        # can map to other particles; mapping to same is no change
        # essential a first order weighting of sorts
        self.transformMap = {'a':[(None, 3), ('a', 1)]}


    def setTransformMap(self, transformMap):
        """set particle transformMap
        this likely will only be set once per 

        >>> lc = [('a', 1), ('b', 2)]
        >>> tm = {'a':[(None, 3), ('a', 1)]}
        >>> a = ParticleTransformer(lc)
        >>> a.setTransformMap(tm)
        """
        self.transformMap = transformMap


    def transform(self, particleArray):
        '''Given an array of Particles, select one and process
        '''
        if len(particleArray) == 0: # empty
            return None

        pIndex = random.choice(list(range(len(particleArray))))
        p = particleArray[pIndex]
        # only process if state matches current state of this particle
        if p.getState() != self.getState():
            return particleArray # return unaltered reference
        # find transform        
        if self.getState() not in list(self.transformMap.keys()):
            return None

        weights = []
        options = []
        for o, w in self.transformMap[self.getState()]:
            weights.append(w)
            options.append(o)
        boundary = unit.unitBoundaryProportion(weights)
        i = unit.unitBoundaryPos(random.random(), boundary)
        result = options[i] # index is in position

        if result == None: # remove
            #environment.printDebug(['transform(); removing particle:', p])
            particleArray.pop(pIndex)
        # if a string value the same as the current state of the particle
        elif result == p.getState():
            pass # do nothing
        else: # not yet implemented: need to convert do a different state
            # for this wee need a life cycle argument 
            pass
    
    def __call__(self, particleArray, ageStep=1):
        """Transform any particles in the array; advance this particles state

        >>> lc = [('a', 1), ('b', 2)]
        >>> tm = {'a':[(None, 1)]} # destroy 1
        >>> pa = [Particle(lc), Particle(lc), Particle(lc)]
        >>> a = ParticleTransformer(lc)
        >>> a.setTransformMap(tm)
        >>> a(pa, 2)
        True
        >>> a.getState()
        'b'
        >>> pa # only have two particles now
        [<Particle: state a; age 0; dead False>, <Particle: state a; age 0; dead     False>]

        """
        self.transform(particleArray)
        return self.advance(ageStep)


    def __repr__(self):
        '''
        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = ParticleTransformer(pairs)
        >>> a.advance(2)
        True
        >>> repr(a)
        '<ParticleTransformer: state b; age 2; dead False>'
        >>> a.advance(1)
        True
        >>> repr(a)
        '<ParticleTransformer: state b; age 3; dead False>'
        >>> a.advance(1)
        False
        >>> repr(a)
        '<ParticleTransformer: state None; age 4; dead True>'
        >>> a.advance(1) # can age beyond death, but has no state
        False
        >>> repr(a)
        '<ParticleTransformer: state None; age 5; dead True>'

        '''
        
        return '<ParticleTransformer: state %s; age %s; dead %s>' % (self.state, self.age, self.isDead())




#-----------------------------------------------------------------||||||||||||--
class SensorProducer(object):
    """Object for detecting number of particles and producing new particles; could be thought of as a gland, exreter, or something else

    All particles share the same life span and state structure (lifeCycle).

    Procduces only 1 type of Particle, and 1 type of ParticleTransformer

    >>> a = SensorProducer()
    """

    def __init__(self):
        self.particleLifeCycle = None # life cycle of particles produced
        self.particleTransformerLifeCycle = None # life cycle
        self.particleTransformMap = None

        # this is a string matching the type of particle this sense matches
        self.particleSenseType = None 

        # an integer represnting the count of particles that this SensorProducer
        # targets to create
        self.threshold = None # desired value
        
        # given a distance form the threshold, determine 
        # how many particles to create; for each max span, define a range 
        # difference from threshold that maps to a range form min to max values
        # produced
        # default here always produces 1 value
        self.productionCountRange = {None: 1}

        # shift are calculated in relation to threshold
        self.boundaryShiftUpper = None # count above threshold that is permitted
        self.boundaryShiftLower = None # count below threshold that is permitted
        
    def setThreshold(self, threshold, lower=2, upper=2):
        """Set threshold as well as upper and lower boundaries. 

        sets abs count range around threshold
        upper and lower are fixed here; might be useful to add noise to boundary
        this may need to be called for each state

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(pairs, 'b')

        >>> a.setThreshold(30)
        >>> a._getBoundary()
        (28, 32)

        >>> a.setThreshold(30, 5, 2)
        >>> a._getBoundary()
        (25, 32)
        """
        self.threshold = threshold
        self.boundaryShiftUpper = upper
        self.boundaryShiftLower = lower
        
    def setParticle(self, particleLifeCycle, particleSenseType):
        """set particle life cycle and particle sense type
        this likely will only be set once per 

        >>> lc = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(lc, 'b')
        """
        self.particleLifeCycle = particleLifeCycle
        self.particleSenseType = particleSenseType

    def setParticleTransformer(self, particleLifeCycle, transformMap):
        """set particle life cycle and particle sense type
        this likely will only be set once per 

        >>> lc = [('a', 1), ('b', 2)]
        >>> tm = {'a':[(None, 3), ('a', 1)]}
        >>> a = SensorProducer()
        >>> a.setParticle(lc, 'b')
        >>> a.setParticleTransformer(lc, tm)
        """
        self.particleTransformerLifeCycle = particleLifeCycle
        self.particleTransformMap = transformMap

    def setProductionCountRange(self, productionCountRange):
        '''
        >>> pcr = {(0,10):1, (10, 20):2, None: [3, 5]}
        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(pairs, 'b')
        >>> a.setProductionCountRange(pcr)
        '''
        self.productionCountRange = productionCountRange


    #-------------------------------------------------------------||||||||||||--
    def produceParticle(self):
        """return a particle object. Can be used to force the production of a new particle, as used in initializing Environments. 

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(pairs, 'b')
        >>> a.produceParticle()
        <Particle: state a; age 0; dead False>

        """
        part = Particle(self.particleLifeCycle)
        return part

    def produceParticleTransformer(self):
        """return a particle object. Can be used to force the production of a new particle, as used in initializing Environments. 

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(pairs, 'b')
        >>> a.produceParticle()
        <Particle: state a; age 0; dead False>

        """
        part = ParticleTransformer(self.particleTransformerLifeCycle)
        part.setTransformMap(self.particleTransformMap)
        return part

    def sense(self, composition):
        """This returns the number of particles sensed that are found in the composition dictionary.

        Provide a dictionary of an envrionment's composition
        look for particleSenseType
        if above or below boundary, determine action

        >>> pairs = [('a', 1), ('b', 2)]
        >>> composition = {'a': 10, 'b': 20}
        >>> a = SensorProducer()
        >>> a.setThreshold(30)
        >>> a.setParticle(pairs, 'b')
        >>> a.produceParticle()
        <Particle: state a; age 0; dead False>
        >>> a.sense(composition) # count of snesed particles found in the comp
        20 
        """
        senseLevel = 0
        for partType in list(composition.keys()): # keys in a dictionary
            if self.particleSenseType == partType:
                senseLevel = composition[self.particleSenseType]
                break
        return senseLevel

    def _getBoundary(self):
        '''
        >>> a = SensorProducer()
        >>> a.setThreshold(30, 10, 10)
        >>> a._getBoundary()
        (20, 40)
        '''
        max = self.threshold + self.boundaryShiftUpper
        if max < self.threshold: max = self.threshold
        min = self.threshold - abs(self.boundaryShiftLower)
        if min > self.threshold: 
            min = self.threshold
        if min < 0: 
            min = 0
        return min, max


    def _getProductionCount(self, span):
        '''Given a number representing range to threshold, provide the number of particles produced.

        >>> pcr = {(-10,-1):8, (0,10):1, (11, 20):2, None: [3, 5]}
        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setThreshold(30)
        >>> a.setParticle(pairs, 'b')
        >>> a.setProductionCountRange(pcr)
        >>> a._getProductionCount(3)
        1
        >>> a._getProductionCount(12)
        2
        >>> a._getProductionCount(34) in [3,4,5]
        True
        >>> a._getProductionCount(-4)
        8
        '''
        countRaw = None
        for key in list(self.productionCountRange.keys()):
            # a None key provides a default value range
            if key == None: 
                continue
            # key is inclusive min max:
            if span >= key[0] and span <= key[1]:
                countRaw = self.productionCountRange[key]
        # if no match, get None, for all spans out of defined ranges
        if countRaw == None:
            countRaw = self.productionCountRange[None]

        if not drawer.isList(countRaw): # create an inclusive range
            countRaw = [countRaw, countRaw]
        count = random.choice(list(range(countRaw[0], countRaw[1]+1)))
        return count


    def getComposition(self, particleArray):
        """Return numbers of each particle in a dictionary
        pass this dictionary to sensorProducers

        """
        post = {}
        for part in particleArray: # part is a particle object
            state = part.getState()
            if state not in post:
                post[state] = 0
            post[state] = post[state] + 1        
        return post


    def process(self, particleArray, particleTransformerArray,
             composition=None):
        """Sense the level of the target particle based on the system composition provided as an argument. 

        If composition is provided, this composition value is used, rather than a dynamically allocated value. 

        If the number of sensed particles is less than the lower boundary, create one particle. 

        get senseLevel, and min and max boundaries;
        determine how many particles to produce
        return a list of particles

        its possible that the number of particles produced should be controlled
        with a probabilistic function

        >>> lc = [('a', 1), ('b', 2)]
        >>> composition = {'a': 10, 'b': 20}
        >>> pa = [Particle(lc), Particle(lc)]
        >>> a = SensorProducer()
        >>> a.setThreshold(30)
        >>> a.setParticle(lc, 'b')
        >>> a.process(pa, [])
        >>> pa
        [<Particle: state a; age 0; dead False>, <Particle: state a; age 0; dead False>, <Particle: state a; age 0; dead False>]

        >>> # if we are over the threshold, no particles are produced
        >>> composition = {'a': 10, 'b': 35}
        >>> a.process(pa, [])
        >>> pa
        [<Particle: state a; age 0; dead False>, <Particle: state a; age 0; dead False>, <Particle: state a; age 0; dead False>, <Particle: state a; age 0; dead False>]

        """
        if composition == None:
            composition = self.getComposition(particleArray)
        else:
            composition = composition

        senseLevel = self.sense(composition)
        min, max = self._getBoundary()
        span = self.threshold - senseLevel # may be positive or negative

        # presently this is only looking at threshold; min/max range
        # is not being examined
        # if out of span, the same production count will be shown
        if senseLevel < self.threshold: # return particles
            for x in range(self._getProductionCount(span)):
                particleArray.append(self.produceParticle())
        elif senseLevel > self.threshold:
            # only create transformers if defined
            if self.particleTransformerLifeCycle != None:
                for x in range(self._getProductionCount(span)):
                #for x in range(2):
                    particleTransformerArray.append(
                        self.produceParticleTransformer())
                #environment.printDebug(['here', particleTransformerArray])
    def __repr__(self):
        '''
        >>> pairs = [('a', 1), ('b', 2)]
        >>> composition = {'a': 10, 'b': 20}
        >>> a = SensorProducer()
        >>> a.setThreshold(30)
        >>> a.setParticle(pairs, 'b')
        >>> repr(a)
        "<SensorProducer: particleLifeCycle [('a', 1), ('b', 2)]>"
        '''
        return '<SensorProducer: particleLifeCycle %s>' % (self.particleLifeCycle)


#-----------------------------------------------------------------||||||||||||--
class _Environment:
    '''
    A base class for modeling various envrionments. 


    >>> a = EnvironmentThermostat()
    >>> a.fillSensorProducer()
    '''
    def __init__(self):

        self._sensorProducerArray = [] # a list of gland objects
        self._particleArray = [] # a list of particle objects
        self._particleTransformerArray = [] # a list of transformer objects

        # sample values, all provided to one type of Sensor
        self.sensorProducerCount = 10
        self.range = [30, 140]

        # store one object and make copies
        self.spArchetype = None
        
    def clear(self):
        '''Remove all particles and sensors.
        '''
        self._particleArray = [] # a list of particle objects
        self._sensorProducerArray = [] # a list of gland objects
        # will call method of subclass

    def fillSensorProducer(self):
        '''Depending on self.sensorProducerCount, create as many SensorProducer objects as specified. All have th8e same lifeCycle and threshold.
        '''
        if self.spArchetype == None: # get default
            spSrc = SensorProducer()
            spSrc.setParticle([('a',4)], 'a') 
            spSrc.setThreshold(100, 4, 4)
        else:
            environment.printDebug(['using self.spArchetype', self.spArchetype])
            spSrc = self.spArchetype

        for x in range(self.sensorProducerCount): 
            sp = copy.deepcopy(spSrc)
            # set life cycle and sense
            self._sensorProducerArray.append(sp)

    def fillParticle(self, count=1):
        """Fill the envrionment with existing particles
        can be used for creating initial conditions
        will use existing sensorProducers to fill
        count is     number of times through all sensor producers
        """
        for i in range(count):
            for sp in self._sensorProducerArray:
                self._particleArray.append(sp.produceParticle()) 

    def getComposition(self, normalize=False, boundaryMethod=None):
        """Return numbers of each particle in a dictionary
        pass this dictionary to sensorProducers

        >>> a = _Environment()
        >>> a.fillSensorProducer()
        >>> a.getComposition()
        {}
        >>> a.advance() 
        >>> a.getComposition()
        {'a': 10}
        >>> a.advance() 
        >>> a.getComposition()
        {'a': 20}

        """
        post = {}
        for part in self._particleArray: # part is a particle object
            state = part.getState()
            if state not in post:
                post[state] = 0
            post[state] = post[state] + 1        
        if boundaryMethod != None:
            for key in list(post.keys()):
                pre = post[key]
                post[key] = unit.boundaryFit(self.range[0], 
                    self.range[1], pre, boundaryMethod)
        if normalize:
            for key in list(post.keys()):
                pre = post[key]
                post[key] = unit.unitNorm(pre, self.range)
        return post

    def getSensorThresholdAverage(self):
        """Examine all sensors; for each particle type, get threshold, 
        determine average

        >>> a = _Environment()
        >>> a.fillSensorProducer()
        >>> a.getComposition()
        {}
        >>> a.advance() 
        >>> a.getComposition()
        {'a': 10}
        >>> a.getSensorThresholdAverage()
        {'a': 100.0}
    
        """
        post = {}
        for sp in self._sensorProducerArray:
            if sp.particleSenseType not in list(post.keys()):
                post[sp.particleSenseType] = [0, 0] # count, threshold sum
            # increment count
            post[sp.particleSenseType][0] += 1
            post[sp.particleSenseType][1] += sp.threshold
        # get all averages
        avg = {}
        for senseType in post: # get keys
            # divide threshold sum by number of sensors for average
            avg[senseType] = post[senseType][1] / float(post[senseType][0])
        return avg


    def _applyParticleTransformer(self):

        #environment.printDebug(['current particle transformer array', self._particleTransformerArray])
        for partIndex in range(len(self._particleTransformerArray)):        
            pt = self._particleTransformerArray[partIndex]
            pt.transform(self._particleArray)


    def _advanceParticle(self, ageStep):
        """Advance each particle by the number of frames given in the ageStep.
        ageStep is rounded to the nearest integer
        providing a value between 0 and 1 will give 50% chance of advancing
        providing a value between 0 and 2 will give 50% chance of advancing
            25% of not, 25% of advancing 2
        can provide an integer, number, or function
        """
        # advance particles; if dead, store index, delete after
        deadIndex = []
        for partIndex in range(len(self._particleArray)):        
            live = self._particleArray[partIndex].advance(ageStep) 
            if not live:
                deadIndex.append(partIndex)
        # remove dead particles, should already be low to high      
        deadIndex.reverse() 
        for partIndex in deadIndex: # delete indices in reverse
            del self._particleArray[partIndex]


    def _advanceParticleTransformer(self, ageStep):
        """Advance each particle by the number of frames given in the ageStep.
        """
        # advance particles; if dead, store index, delete after
        deadIndex = []
        for partIndex in range(len(self._particleTransformerArray)):        
            live = self._particleTransformerArray[partIndex].advance(ageStep) 
            if not live:
                deadIndex.append(partIndex)
        # remove dead particles, should already be low to high      
        deadIndex.reverse() 
        for partIndex in deadIndex: # delete indices in reverse
            del self._particleTransformerArray[partIndex]

    def _advanceSensor(self):
        """Process all sensors
        """
        composition = self.getComposition()
        for sp in self._sensorProducerArray:
            # this changes the particle array in place
            sp.process(self._particleArray, self._particleTransformerArray,
                     composition=composition)


    def advance(self, ageStep=1):
        """Advance all particles the specified number of steps. 

        Providing fractional age steps creates probabilities in aging. 
        """
        # first, apply any existing transformers
        #environment.printDebug(['pre apply transformer', self.getComposition()])
        self._applyParticleTransformer()
        #environment.printDebug(['post apply transformer', self.getComposition()])

        # age any transformers
        self._advanceParticleTransformer(ageStep)

        # advance all existing particles; remove any dead particles
        self._advanceParticle(ageStep)
        # an ageStpe greawter than one only advnaces the particles ages
        # sps are only advanced one step
        self._advanceSensor() 


    def reprPartcle(self):
        post = self.getComposition()
        post = list(post.items())
        post.sort()
        return post
        
    def __repr__(self):
        return '<Environment particle: %s; sensorProducer: %s>' % (self.reprPartcle(), len(self._sensorProducerArray))



#-----------------------------------------------------------------||||||||||||--
class EnvironmentThermostat(_Environment):

    def __init__(self):
        """this model uses one type of particle
        each particle has the same threshold; 
            not all threholds have to be the same

        >>> a = EnvironmentThermostat()
        >>> 
        """
        # call base class init
        _Environment.__init__(self)

        # must define some attributes before calling base class
        # more sensorProducers cause more value stability
        self.sensorProducerCount = 6

        self.range = [50, 120]


        # define SensorProducer object; copied for producton
        self.spArchetype = SensorProducer()
        self.spArchetype.setThreshold(100)
        self.spArchetype.setParticle([('a', 10)], 'a')

        pcr = {(-30,-10): [1,2], (1,10): [1, 2], (11, 20): [1, 4], None: [1, 8]}
        self.spArchetype.setProductionCountRange(pcr)


    def getValue(self):
        dict = self.getComposition(normalize=True, boundaryMethod='limit')
        return dict['a']






class EnvironmentClimateControl(_Environment):

    def __init__(self):
        """
        >>> a = EnvironmentClimateControl()
        >>> 
        """
        # call base class init
        _Environment.__init__(self)

        # must define some attributes before calling base class
        # more sensorProducers cause more value stability
        self.sensorProducerCount = 10

        self.range = [30, 140]


        # define SensorProducer object; copied for producton
        self.spArchetype = SensorProducer()
        self.spArchetype.setThreshold(100)
        self.spArchetype.setParticle([('a', 5)], 'a')
        # always delete 1
        self.spArchetype.setParticleTransformer([('a', 2)], 
            {'a':[(None, 1)]})


        pcr = {(-30,-10): [6,8], (1,10): [1, 2], (11, 20): [1, 4], None: [1, 8]}
        self.spArchetype.setProductionCountRange(pcr)


    def getValue(self):
        dict = self.getComposition(normalize=True, boundaryMethod='limit')
        return dict['a']


#-----------------------------------------------------------------||||||||||||--
def libraryParser(usrStr):
    """decode feedback models

    >>> libraryParser('t')
    'thermostat'
    >>> libraryParser('cc')
    'climateControl'
    """
    ref = {
        'climateControl' : ['cc', 'climage'],
        'thermostat' : ['t', 'temp'],
            }
    usrStr = drawer.selectionParse(usrStr, ref)
    if usrStr == None:
        selStr = drawer.selectionParseKeyLabel(ref)
        raise FeedbackError('bad user string name: %s.' % selStr)
    return usrStr


def factory(usrStr):
    '''given a model name as a string, return the object

    >>> factory('cc')
    <Environment particle: []; sensorProducer: 0>

    '''
    model = libraryParser(usrStr)
    if model == 'climateControl':
        return EnvironmentClimateControl()
    elif model == 'thermostat':
        return EnvironmentThermostat()
    else:
        raise FeedbackError('bad feedback name: %s.' % usrStr)

#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)

    def testParticle(self):
        a = Particle([('a',3), ('b',4), ('c',8)])
        while 1:
            post = a(random.random()+.125)
            if post == 0: break


    def testSensorProducer(self):
        threshold = 10
        boundaryShift = 4 # use for up and down
        particleLifeCycle = [('a', 10)]
        particleSenseType = 'a'

        sp = SensorProducer() 
        sp.setThreshold(threshold, boundaryShift, boundaryShift)
        sp.setParticle(particleLifeCycle, particleSenseType) 
        a = sp.produceParticle()

    def testEnvironmentThermostat(self):
        environment.printDebug(['testing EnvironmentThermostat'])
        a = EnvironmentThermostat()
        a.fillSensorProducer()
        self.assertEqual(a.getComposition(), {})

        for i in range(100):
            ageStep = random.choice([1, 1.5, 2, 2.5])
            a.advance(ageStep)
            environment.printDebug([a.getComposition(normalize=False, boundaryMethod='limit'), a.getValue()])   

 

    def testEnvironmentClimateControl(self):
        environment.printDebug(['testing EnvironmentClimateControl'])
        a = EnvironmentClimateControl()
        a.fillSensorProducer()
        self.assertEqual(a.getComposition(), {})

        for i in range(100):
            ageStep = random.choice([1, 1.5, 2, 2.5])
            a.advance(ageStep)
            environment.printDebug([a.getComposition(normalize=False, boundaryMethod='limit'), a.getValue()])   




#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)







        