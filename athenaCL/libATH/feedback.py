#-----------------------------------------------------------------||||||||||||--
# Name:          feedback.py
# Purpose:       models of biological feedback systems
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2007-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import random
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


#-----------------------------------------------------------------||||||||||||--
class Particle(object):
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

        self.age = self.age + int(round(ageUnit))
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

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = Particle(pairs)
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
        



#-----------------------------------------------------------------||||||||||||--
class SensorTransformer(object):
    """Object for transforming and/or destroying Particles

    All particles share the same life span and state structure (lifeCycle).

    May sense only 1 particles, may produce 1 or more particles.

    >>> a = SensorProducer()
    """

    def __init__(self):
        
        # provide a target and weighting for the most likely outcom
        # a weighting of None cause immediate distruction
        # can map to other particles
        # essential a first order weighting of sorts
        self.particleTransformMap = {'a':[(None, 3), ('a', 1)]}

        # need to determine how many transformations this senor
        # does
        self.transformationCountRange = {None: 1}


    def setParticleMap(self, particleTransformMap, particleSenseType):
        """set particle life cycle and particle sense type
        this likely will only be set once per 

        >>> tm = {'a':[(None, 3), ('a', 1)]}
        >>> a = SensorProducer()
        >>> a.setParticleMap(tm, 'b')
        """
        self.particleTransformMap = particleTransformMap


    def process(self, particleArray):
        '''Given a particle array, perform transformations.
        '''
        count = 1
        for i in count:
            # pick a random target
            j = random.choice(range(len(particleArray))
            particle = particleArray[j]

            for key in self.particleTransformMap.keys():
                if particle.state == key:
                    # perform weighted selection of action
                    pass


#-----------------------------------------------------------------||||||||||||--
class SensorProducer(object):
    """Object for detecting number of particles and producing new particles; could be thought of as a gland, exreter, or something else

    All particles share the same life span and state structure (lifeCycle).

    May sense only 1 particles, may produce 1 or more particles.

    >>> a = SensorProducer()
    """

    def __init__(self):
        self.particleLifeCycle = None # life cycle of particles produced b

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

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(pairs, 'b')
        """
        self.particleLifeCycle = particleLifeCycle
        self.particleSenseType = particleSenseType


    def setProductionCountRange(self, productionCountRange):
        '''
        >>> pcr = {(0,10):1, (10, 20):2, None: [3, 5]}
        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(pairs, 'b')
        >>> a.setProductionCountRange(pcr)
        '''
        self.productionCountRange = productionCountRange

    def produce(self):
        """return a particle object. Can be used to force the production of a new particle, as used in initializing Environments. 

        >>> pairs = [('a', 1), ('b', 2)]
        >>> a = SensorProducer()
        >>> a.setParticle(pairs, 'b')
        >>> a.produce()
        <Particle: state a; age 0; dead False>

        """
        part = Particle(self.particleLifeCycle)
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
        >>> a.produce()
        <Particle: state a; age 0; dead False>
        >>> a.sense(composition) # count of snesed particles found in the comp
        20 
        """
        senseLevel = 0
        for partType in composition.keys(): # keys in a dictionary
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

        >>> pcr = {(0,10):1, (11, 20):2, None: [3, 5]}
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
        '''
        countRaw = None
        for key in self.productionCountRange.keys():
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
        count = random.choice(range(countRaw[0], countRaw[1]+1))
        return count


    def process(self, composition):
        """Sense the level of the target particle based on the system composition provided as an argument. 

        If the number of sensed particles is less than the lower boundary, create one particle. 

        If the number of of sensed particles is greater than that number, presently do nothing. Options: prudce consumer particles?

        get senseLevel, and min and max boundaries;
        determine how many particles to produce
        return a list of particles

        its possible that the number of particles produced should be controlled
        with a probabilistic function

        >>> pairs = [('a', 1), ('b', 2)]
        >>> composition = {'a': 10, 'b': 20}
        >>> a = SensorProducer()
        >>> a.setThreshold(30)
        >>> a.setParticle(pairs, 'b')
        >>> a.process(composition)
        [<Particle: state a; age 0; dead False>]

        >>> # if we are over the threshold, no particles are produced
        >>> composition = {'a': 10, 'b': 35}
        >>> a.process(composition)
        []
        """
        senseLevel = self.sense(composition)
        min, max = self._getBoundary()
        span = self.threshold - senseLevel

        # presently this is only looking at threshold; min/max range
        # is not being examined
        if senseLevel < self.threshold: # return particles
            partCount = self._getProductionCount(span)
        elif senseLevel == self.threshold: 
            partCount = 0
        elif senseLevel > self.threshold:
            partCount = 0

        #print _MOD, 'senseLevel, partCount', senseLevel, partCount
        post = []
        for x in range(partCount):
            post.append(self.produce())
        return post


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
        # sample values, all provided to one type of Sensor
        self.sensorProducerCount = 10
        self.sensorProductionCountRange = {None: 1}
        self.threshold = 100
        self.range = [30, 140]
        self.ageStepList = [1] # range of ages values selected from
        self.boundaryShift = 4 # use for up and down
        self.particleLifeCycle = [('a', 4)]
        self.particleSenseType = 'a'

        self._particleArray = [] # a list of particle objects
        self._sensorProducerArray = [] # a list of gland objects

    def clear(self):
        '''Remove all particles and sensors.
        '''
        self._particleArray = [] # a list of particle objects
        self._sensorProducerArray = [] # a list of gland objects
        # will call method of subclass

    def fillSensorProducer(self):
        '''Depending on self.sensorProducerCount, create as many SensorProducer objects as specified. All have th8e same lifeCycle and threshold.
        '''
        for x in range(self.sensorProducerCount): 
            sp = SensorProducer()
            # set life cycle and sense
            sp.setParticle(self.particleLifeCycle, self.particleSenseType) 
            sp.setThreshold(self.threshold, self.boundaryShift, 
                self.boundaryShift)
            sp.setProductionCountRange(self.sensorProductionCountRange)
            self._sensorProducerArray.append(sp)

    def fillParticle(self, count=1):
        """Fill the envrionment with existing particles
        can be used for creating initial conditions
        will use existing sensorProducers to fill
        count is     number of times through all sensor producers
        """
        for i in range(count):
            for sp in self._sensorProducerArray:
                self._particleArray.append(sp.produce()) 

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
            for key in post.keys():
                pre = post[key]
                post[key] = unit.boundaryFit(self.range[0], 
                    self.range[1], pre, boundaryMethod)
        if normalize:
            for key in post.keys():
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
            if sp.particleSenseType not in post.keys():
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


    def _advanceSensor(self, composition):
        """Get particles from all sensors based on the current composition of this state. 
        """
        for sp in self._sensorProducerArray:
            # output a list of zero or more particles
            self._particleArray = self._particleArray + sp.process(composition)


    def advance(self, ageStep=None):
        """Advance all particles the specified number of steps. 

        Providing fractional age steps creates probabilities in aging. 
        """
        if ageStep == None:
            ageStep = random.choice(self.ageStepList)
        # advance all existing particles; remove any dead particles
        self._advanceParticle(ageStep)
        # an ageStpe greawter than one only advnaces the particles ages
        # sps are only advanced one step
        self._advanceSensor(self.getComposition())

    def reprPartcle(self):
        post = self.getComposition()
        post = post.items()
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
        self.sensorProductionCountRange = {(1,10): [1, 2], 
                                           (11, 20): [2, 4], 
                                           None: [3, 8]}

        self.threshold = 100
        self.range = [30, 140]
        self.ageStepList = [1, 1.5, 2, 2.5] # range of ages values selected from

        self.boundaryShift = 4 # use for up and down
        self.particleLifeCycle = [('a', 6)]
        self.particleSenseType = 'a'






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
        a = sp.produce()

    def testEnvironmentThermostat(self):
        environment.printDebug(['testing EnvironmentThermostat'])
        a = EnvironmentThermostat()
        a.fillSensorProducer()
        self.assertEqual(a.getComposition(), {})

        for i in range(100):
            a.advance()
            environment.printDebug([a.getComposition(normalize=False, boundaryMethod='limit')])   



#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)







        