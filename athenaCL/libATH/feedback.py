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

_MOD = 'feedback.py'

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
class Particle:
    def __init__(self, lifeCycle):
        """life cycle is a dictionary of pairs
        each pair gives a state (as a string letter) followed by
        a number of frames at which that state exists
        after all states have passed, the particle is dead 
        """
        self.lifeCycle = lifeCycle
        self.lifeBounds = {}
        self.lifeSpan = 0 # number of frames in life
        self._updateLifeSpan() # update lifeSpan and lifeBounds
        self.age = 0 # number of cycles passed
        self.state = self.lifeCycle[0][0] # get first state

    def _updateLifeSpan(self):
        self.lifeSpan = 0
        pos = 1 # age zero is not counted
        for key, num in self.lifeCycle:
            if num <= 0:
                raise error.ParticleSyntaxError

            self.lifeSpan = self.lifeSpan + num
            next = pos + num
            self.lifeBounds[key] = (pos, next-1) # one less
            pos = next
                            
    def advance(self, ageStep=1):
        """advance one frame
        ageStep can be a function or a number (value around 1)
        ageStep is rounded to the nearest integer
        thus floating point values outside of .5 and 1.5 cause shifts
        """
        if drawer.isNum(ageStep):
            ageUnit = ageStep
        else:
            ageUnit = ageStep() # assume it is a function

        self.age = self.age + int(round(ageUnit))
        if self.age > self.lifeSpan: # must be greater, not >=
            self.state = None
            return 0 # cant advance, as is dead
        for key in self.lifeBounds:
            if (self.age >= self.lifeBounds[key][0] and self.age <= 
                self.lifeBounds[key][1]):
                self.state = key
                break
        return 1

    def isDead(self):
        """return boolean if particle is dead"""
        if self.age > self.lifeSpan: return 1 # greater, not gt equal
        else: return 0

    def getState(self):
        """return current state"""
        return self.state

    def reset(self):
        self.age = 0
        self.state = None
        self._updateLifeSpan()

    def __repr__(self):
        return '<Particle: state %s; age %s; dead %s>' % (self.state, self.age, self.isDead())

    def __call__(self, ageStep=1):
        """advance the particle"""
        return self.advance(ageStep)
        # will return 0 when dead

        # alternate approach that would permit multi-frame advance
        #for i in range(frame):
        #    ok = self._advance()
        #    if not ok: break # dead
        


#-----------------------------------------------------------------||||||||||||--
class SensorProducer:
    """object for detecting number of particles
    and producing new particles
    could be thought of as a gland, exreter, or something else

    may sense only 1 particles
    may produce 1 or more particles
    """

    def __init__(self):
        self.particleLifeCycle = None # life cycle of particles produced b
        self.particleSenseType = None # particle type this sensor senses
        self.threshold = None # desired value
        
        # shift are calculated in relation to threshold
        self.boundaryShiftUpper = None # count above threshold that is permitted
        self.boundaryShiftLower = None # count below threshold that is permitted
        
    def setThreshold(self, threshold, lower=2, upper=2):
        """sets abs count range around threshold
        upper and lower are fixed here; might be useful to add noise to boundary
        this may need to be called for each state"""
        self.threshold = threshold
        self.boundaryShiftUpper = upper
        self.boundaryShiftLower = lower
        
    def setParticle(self, particleLifeCycle, particleSenseType):
        """set particle life cycle and particle sense type
        this likely will only be set once per """
        self.particleLifeCycle = particleLifeCycle
        self.particleSenseType = particleSenseType

    def produce(self):
        """return a particle object based """
        part = Particle(self.particleLifeCycle)
        return part

    def sense(self, composition):
        """provide a dictionary of an envrionment's compositioin
        look for particleSenseType
        if above or below boundary, determine action"""
        senseLevel = 0
        for partType in composition: # keys in a dictionary
            if self.particleSenseType == partType:
                senseLevel = composition[self.particleSenseType]
                break
        return senseLevel

    def _getBoundary(self):
        max = self.threshold + self.boundaryShiftUpper
        if max < self.threshold: max = self.threshold
        min = self.threshold - abs(self.boundaryShiftLower)
        if min > self.threshold: min = self.threshold
        if min < 0: min = 0
        return min, max

    def process(self, composition):
        """get senseLevel, and min and max boundaries;
        determine how many particles to produce
        return a list of particles

        its possible that the number of particles produced shuold be controlled
        with a probabilistic function
        """
        senseLevel = self.sense(composition)
        min, max = self._getBoundary()
         
        if senseLevel < min: # return particles
            partCount = 1
        elif senseLevel >= min and senseLevel < self.threshold: # return particles
            partCount = 1
        elif senseLevel == self.threshold: # return particles
            partCount = 0
        elif senseLevel > self.threshold and senseLevel <= max: # return particles
            partCount = 0
        elif senseLevel > max: # produce nothing
            partCount = 0

        #print _MOD, 'senseLevel, partCount', senseLevel, partCount
        post = []
        for x in range(partCount):
            post.append(self.produce())
        return post


    def __repr__(self):
        return '<SensorProducer: particleLifeCycle %s>' % (self.particleLifeCycle)


#-----------------------------------------------------------------||||||||||||--
class _Environment:
    def __init__(self):
        self._particleArray = [] # a list of particle objects
        self._sensorProducerArray = [] # a list of gland objects
        # will call method of subclass
        self.fillSensorProducer()


    def fillSensorProducer(self):
        """define in subclass; fill array with congigured sensorProducers"""
        pass 

    def fillParticle(self, count=1):
        """fille the envrionment with existing particles
        can be used for creating initial conditions
        will use existing sensorProducers to fill
        count is     number of times through all sensor producers
        """
        for i in range(count):
            for sp in self._sensorProducerArray:
                self._particleArray.append(sp.produce()) 

    def getComposition(self):
        """return numbers of each particle in a dictionary
        pass this dictionary to sensorProducers"""
        post = {}
        for part in self._particleArray: # part is a particle object
            state = part.getState()
            if state not in post:
                post[state] = 0
            post[state] = post[state] + 1
        return post


    def getSensorThresholdAverage(self):
        """examine all sensors; for each particle type, get threshold, 
        determine average"""
        post = {}
        for sp in self._sensorProducerArray:
            if sp.particleSenseType not in post:
                post[sp.particleSenseType] = (0, 0) # count, threshold sum
            # increment count
            post[sp.particleSenseType][0] = post[sp.particleSenseType][0] + 1
            t = sp.threshold
            post[sp.particleSenseType][1] = post[sp.particleSenseType][1] + t
        # get all averages
        avg = {}
        for senseType in post: # get keys
            # divide threshold sum by number of sensors
            avg[senseType] = post[1] / float(post[0]) # average
        return avg


    def fillEquilibrium(self):
        """challange to figure out what kind of particles to create
        each sensorProducer may have a uniqe type of particle definition
        """
        pass


    def _advanceParticle(self, ageStep):
        """advnace each particle by one frame
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
        for partIndex in deadIndex: # delet indices in reverse
            del self._particleArray[partIndex]


    def _advanceSensor(self, composition):
        """get particles from all sensors"""
        for sp in self._sensorProducerArray:
            # output a list of zero or more particles
            self._particleArray = self._particleArray + sp.process(composition)


    def advance(self, ageStep=1):
        """general method to advance the environemtn by one states"""
        # advance all existing particles; remove any dead particles
        self._advanceParticle(ageStep)
        self._advanceSensor(self.getComposition())


    def reprPartcle(self):
        post = self.getComposition()
        post = post.items()
        post.sort()
        return post
        
    def __repr__(self):
        return '<Environment particle: %s; sensorProducer: %s>' % (self.reprPartcle(), 
                                                    len(self._sensorProducerArray))



#-----------------------------------------------------------------||||||||||||--

class EnvironmentThermostat(_Environment):

    def __init__(self):

        """this model uses one type of particle
        each particle has the same threshold; 
            not all threholds have to be the same
        """

        # must define some attributes before calling base class
        self.sensorCount = 10
        self.threshold = 100
        self.boundaryShift = 4 # use for up and down
        self.particleLifeCycle = [('a', 4)]
        self.particleSenseType = 'a'

        # call base class init, will call fillSensorProducer
        _Environment.__init__(self)


    def fillSensorProducer(self):

        for x in range(self.sensorCount): 
            sp = SensorProducer()
            # set life cycle and sense
            sp.setParticle(self.particleLifeCycle, self.particleSenseType) 
            sp.setThreshold(self.threshold, self.boundaryShift, self.boundaryShift)
            self._sensorProducerArray.append(sp)




#-----------------------------------------------------------------||||||||||||--
# class TestOld:
#     def __init__(self):
#         pass
#     
#     def testParticle(self):
#         a = Particle([('a',3), ('b',4), ('c',8)])
#         print a.lifeCycle
#         print a.lifeBounds
#         while 1:
#             post = a(random.random()+.125)
#             print a
#             if post == 0: break
# 
# 
#     def testSensorProducer(self):
#         threshold = 10
#         boundaryShift = 4 # use for up and down
#         particleLifeCycle = [('a', 10)]
#         particleSenseType = 'a'
# 
#         sp = feedback.SensorProducer() 
#         sp.setThreshold(threshold, boundaryShift, boundaryShift)
#         sp.setParticle(particleLifeCycle, particleSenseType) 
#         print sp._getBoundary()
#         a = sp._produce()
#         print a
#         print sp._sense({'d':80,'a':10,'b':20})
# 
# 
#     def testEnvironment(self):
#         pass



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

#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)







        