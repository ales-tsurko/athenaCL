#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          genetic.py
# Purpose:       genetic algorithms for creating groups of rhythms.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# Note:          this software is based in part on c++ code with the following 
#                copyright: (c) 2000 by Robert Rowe
#-----------------------------------------------------------------||||||||||||--



import unittest, doctest
import random, copy


_MOD = 'genetic.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)


#-----------------------------------------------------------------||||||||||||--
# TODO:
# objects need string representations, and some str rep code needs to be removed
# needs to handle pulse objects, instead of raw list implementation


def getTwoLoci(bitLength):
    """return two index values for a list of pulses
    special case for but lenghts of 1 and 2: will raise error elsewhere
    returns only possible indexes in these cases

    >>> len(getTwoLoci(10))
    2
    >>> len(getTwoLoci(20))
    2

    """
    if bitLength == 1: # rhythms of one or two pulses
        return 0, 0
    elif bitLength == 2: # rhythms of one or two pulses
        return 0, 1
    else:
        locusP = random.randint(0,bitLength-1)
        w = 0
        while 1:
            locusQ = random.randint(0,bitLength-1)
            if locusQ == locusP:
                continue
            else:
                break
        if locusP > locusQ: # return smallest, largest
            return locusQ, locusP     
        else:
            return locusP, locusQ


#-----------------------------------------------------------------||||||||||||--
class Chromosome:
    def __init__(self, fitVector, mutationRate=0.10, beatTime=120.0, 
                    initCheck=False, initMutate=True, firstVector=None):
        """
        If useFit is True, this substitutes use the fitVector as the vectro of this Chromosome. Otherwise, the a new, random vector is generated from the components of the source vector.

        >>> a = Chromosome([(4,3,0), (2,1,1)])
        """
    
        self.beatTime = beatTime     # this needs to be changed?
        self.fitVector = fitVector

        self.fitValues = []   # list of possibilities to fill the list with
        # store one of each of the fit values in a list
        for entry in self.fitVector:
            if entry not in self.fitValues:
                self.fitValues.append(entry)

        self.fitDuration = self._pulseVectorToSeconds(self.beatTime, 
                           self.fitVector) 
        self.fitNoteRestDuration = self._pulseVectorToNoteRestDur(self.beatTime,
                                                      self.fitVector)                 
        self.duration = 0.0
        self.noteRestDuration = (0.0, 0.0)
                         
        self.bitLength = len(fitVector)      
        self.mutationRate = mutationRate # percentage of mutation                  
        self.fitness = 0 # int fitness rating

        #self.limit = int(pow(2.0, bitLength)) # dont need?

        # this creates a random bit array from the fitValues (the source) 
        # make bit vector to a list with registers 0 to bitLength - 1
        self.bitVector = []
        if firstVector != None:  
            self.bitVector = copy.deepcopy(firstVector)
        else:
            for i in range(self.bitLength):
                # choose a random init value for each bit on vector
                p = random.choice(self.fitValues)
                self.bitVector.append(copy.deepcopy(p))

        self.calcFitness() # updates duration as well

        if initCheck: # not needed during mating! (value are replace)
            if self.fitness <= 0.1: 
            # if fitVector has been constructed, mutate
                if initMutate:
                    self.mutate('force')
                self.calcFitness()
        
    def _pulseToSeconds(self, beatTime, rhythmicTuple):
        """Calculate the duration of a single note/gene

        TODO: this will not be necessary with Pulse objects

        >>> a = Chromosome([(4,3,0), (2,1,1)])
        >>> a._pulseToSeconds(120, (4,3,0))
        90.0
        >>> a._pulseToSeconds(120, (4,2,0))
        60.0
        """        
        ogDiv, ogMult, ogStat = rhythmicTuple 
        #environment.printDebug([rhythmicTuple])
        dur = ((beatTime / float(ogDiv)) * ogMult)
        return dur
        
    def _pulseVectorToSeconds(self, beatTime, bitVector):
        """calcs whole duration of a vector

        >>> a = Chromosome([(4,3,0), (2,1,1)])
        >>> v = [(4,3,0), (2,1,1), (4,2,1)]
        >>> a._pulseVectorToSeconds(120, v)
        210.0
        """
        durSum = 0
        for entry in bitVector:
            durSum = durSum + self._pulseToSeconds(beatTime, entry)
        return durSum
        
    def _pulseVectorToNoteRestDur(self, beatTime, bitVector):
        """calcs whole duration of a vector

        >>> a = Chromosome([(4,3,0), (2,1,1)])
        >>> v = [(4,3,0), (2,1,1), (4,2,1)]
        >>> a._pulseVectorToNoteRestDur(120, v)
        (120.0, 90.0)
        """      
        noteSum = 0.0
        restSum = 0.0
        for entry in bitVector:
            ogDiv,ogMult,ogStat = entry
            if ogStat == 1: # this is a note
                noteSum = noteSum + self._pulseToSeconds(beatTime, entry)
            else: # a rest
                restSum = restSum + self._pulseToSeconds(beatTime, entry)
        return noteSum, restSum

    def _updateDur(self):
        """Updates duration representations from the self.bitVector
        Called with each calcFitness call

        >>> a = Chromosome([(4,3,0), (2,1,1)])
        >>> a._updateDur()
        >>> a.duration > 50 # randomly determined
        True
        >>> len(a.noteRestDuration)
        2

        """
        self.duration = self._pulseVectorToSeconds(self.beatTime, 
                        self.bitVector)
        self.noteRestDuration = self._pulseVectorToNoteRestDur(self.beatTime, 
                                        self.bitVector)
        

    #-----------------------------------------------------------------------||--

    def calcFitness(self):
        '''Calculate fitness

        >>> v1 = [(4,3,0), (2,1,1), (4,2,1)]
        >>> v2 = [(4,3,0), (2,1,1), (4,2,0)]
        >>> v3 = [(4,2,0), (4,1,1), (2,1,1), (4,2,0)]
        >>> v4 = [(3,1,1), (3,1,1), (3,5,1), (3,9,0)]
        >>> v5 = [(4,3,0), (2,1,1), (4,1,1)]
        >>> v6 = [(4,3,0), (2,1,1), (4,3,1)]

        >>> a = Chromosome(v1, initMutate=False, firstVector=v1)
        >>> a.calcFitness()
        >>> a.fitness # the fitness is zero b/c a perfect fit match
        0.0 

        >>> a = Chromosome(v1, initMutate=False, firstVector=v2)
        >>> a.calcFitness()
        >>> a.fitness # the fitness is zero b/c a perfect fit match
        250.0

        >>> a = Chromosome(v1, initMutate=False, firstVector=v3)
        >>> a.calcFitness()
        >>> a.fitness # the fitness is zero b/c a perfect fit match
        323.2400...

        >>> a = Chromosome(v1, initMutate=False, firstVector=v4)
        >>> a.calcFitness()
        >>> a.fitness # the fitness is zero b/c a perfect fit match
        2713.1400...

        >>> a = Chromosome(v1, initMutate=False, firstVector=v5)
        >>> a.calcFitness()
        >>> a.fitness # the fitness is zero b/c a perfect fit match
        214.8600...

        >>> a = Chromosome(v1, initMutate=False, firstVector=v6)
        >>> a.calcFitness()
        >>> a.fitness # the fitness is zero b/c a perfect fit match
        248.1800...

        '''
        self._updateDur()    # update durations
        self.fitness = 0    # reset to zero

        noteDur, restDur = self.noteRestDuration
        fitNoteDur, fitRestDur = self.fitNoteRestDuration
        
        restDurDif = abs(restDur - fitRestDur)
        if restDurDif < .00001:
            restValue = 0    # best match
        else:
            restValue = restDurDif    
                    
        noteDurDif = abs(noteDur - fitNoteDur)
        if noteDurDif < .00001:
            noteValue = 0
        else:
            noteValue = noteDurDif       
        
        durationDif = abs(self.duration - self.fitDuration)
        if durationDif < .00001:
            durValue = 0
        else:
            durValue = durationDif

        matchGene  = 0            
        matchValue = 0
        for i in range(self.bitLength):
            ogDiv, ogMult, ogStat = self.bitVector[i]
            ftDiv, ftMult, ftStat = self.fitVector[i]
            # find abs of difference between bit and fit vector
            durDif = abs(
                self._pulseToSeconds(self.beatTime, self.bitVector[i]) - 
                self._pulseToSeconds(self.beatTime, self.fitVector[i]))
            # if nearly now difference and both rest/active status
            if durDif < .00001 and ftStat == ogStat:
                matchGene += 1 # exact match of gene (dur and rhythm)
            if durDif < .00001:           # match of dur, rest/note may be offs
                matchValue += 1 
                
        # for each gene out of place, add gene-duration                              
        matchGeneScore = (self.bitLength - matchGene) * (self.duration / 
                             float(self.bitLength))
        # for each values out of place, add gene-duration
        matchValueScore = (self.bitLength - matchValue) * (self.duration / 
                             float(self.bitLength))

        # make fitness up based on these weightings
        self.fitness = ((durValue*2.33) + (restValue *1.5)+ (noteValue*1.5) + 
                       (matchGeneScore*1.0) + (matchValueScore*.666))

        # weightings are very important
        # dV=3  rV=1.5 nv=1.5 mGS=1 mVS=3  # too fast on small, to slow on big  
        # dV=3      rV=1.5  nv=1.5   mGS=1  mVS=1.5      # pretty good
        # dV=2.33   rV=1.5  nv=1.5   mGS=1  mVS=.666         
        # more divesity with small population, 
        # a large chromo needs a large population
            

    def mutate(self, forceMutate=False):
        """ five ways of mutation of rhythm vectors:
        0: replace an entry wiht any rhythm from self.fitValues
        the weight of th rhthm in the chromo is proportional to how iften it will get chosen
        0: inversion of inner segment
        1: divides or mutilplies a rhythm, equivalent
        2: add or subtracts a value from multiplier
        3: add or subtracts a value from divisor 
        4: flip note/rest


        >>> v = [(4,3,0), (2,1,1), (4,2,1)]
        >>> a = Chromosome(v)
        >>> a.mutate()
        >>> a.mutate()
        """
    
        if forceMutate:
            cutoffDecimal = 1.00
        else:
            cutoffDecimal = self.mutationRate
        # randomly determine if mutation happens
        if random.random() > cutoffDecimal: 
            #environment.printDebug(['not mutating'])
            return None
        #environment.printDebug(['mutating'])

        mutationTypes = ['ratioEq','divisorMutate','multiplierMutate', 
                         'flipNoteRest', 'inversion']#,'inversion']
        selectType = random.choice(mutationTypes)
                
        # inversion: select two segments and reverse          
        if selectType == 'inversion':
            locusP, locusQ = getTwoLoci(self.bitLength)
            segment = copy.deepcopy(self.bitVector[locusP:(locusQ+1)])
            segment.reverse()
            locus = locusP # start at L endpoint
            for entry in segment:
                self.bitVector[locus] = entry
                locus += 1
            
        # this divides or multiplies a rhythm: (4,1) == (8,2) == (12,3),
        # this low ratio alteration
        elif selectType == 'ratioEq':
            locus = random.randint(0, self.bitLength-1) 
            ogDiv, ogMult, ogStat = copy.deepcopy(self.bitVector[locus])
            if ogDiv % 2 == 0 and ogMult % 2 == 0: ## if both are even
                if random.randint(0,1) == 1: # half
                    ogDiv = ogDiv / 2
                    ogMult = ogMult / 2
                else: # double
                    ogDiv = ogDiv * 2
                    ogMult = ogMult * 2
            elif ogDiv % 3 == 0 and ogMult % 3 == 0: ## if both are div by 3
                if random.randint(0,1) == 1: # half
                    ogDiv = ogDiv / 3
                    ogMult = ogMult / 3
                else: # double
                    ogDiv = ogDiv * 3
                    ogMult = ogMult * 3                      
            else: # multiply by 2 or 3
                if random.randint(0,1) == 1:
                    ogDiv = ogDiv * 2
                    ogMult = ogMult * 2
                else:
                    ogDiv = ogDiv * 3
                    ogMult = ogMult * 3                      
            self.bitVector[locus] = (ogDiv, ogMult, ogStat)               
            
        # this adds/subtracts from mutltiplier unit
        elif selectType == 'multiplierMutate':
            locus = random.randint(0, self.bitLength-1) 
            ogDiv, ogMult, ogStat = copy.deepcopy(self.bitVector[locus])
            if ogMult == 1: # if multiplier is one, must add
                # add any value betwen 1 and divisor 
                if ogDiv == 1:
                    value = 1
                else: # previously, add just one here
                    value = random.choice(range(1,ogDiv))
                ogMult = ogMult + value  
            # current value greater than one, choose add or subrtact
            else:   
                if random.randint(0,1):
                    if ogDiv == 1: # error with random if this value is one
                        value = 1
                    else:# previously, to add just one here
                        value = random.choice(range(1,ogDiv))   
                    ogMult = ogMult + value
                else: # cannot subtract more than the mutliplier
                    if ogMult == 1:
                        value = 1
                    else: # previously, to add just one here
                        value = random.choice(range(1,ogMult))   
                    ogMult = ogMult - value  # max value is ogMult-1
            self.bitVector[locus] = (ogDiv, ogMult, ogStat) 
            
        # this adds/subtracts a divisor unit
        elif selectType == 'divisorMutate':
            locus = random.randint(0, self.bitLength-1) 
            ogDiv, ogMult, ogStat = copy.deepcopy(self.bitVector[locus])
            if ogDiv == 1:
                ogDiv += 1
            else:
                if random.randint(0,1):
                    ogDiv += 1
                else:
                    ogDiv = ogDiv - 1
            self.bitVector[locus] = (ogDiv, ogMult, ogStat) 
                            
        # flip status from rest to note
        elif selectType == 'flipNoteRest':
            locus = random.randint(0, self.bitLength-1) 
            ogDiv, ogMult, ogStat = copy.deepcopy(self.bitVector[locus])
            if ogStat == 1:
                ogStat = 0
            else:
                ogStat = 1
            self.bitVector[locus] = (ogDiv, ogMult, ogStat) 
            
                                
    def randomize(self):
        '''Randomize the bitVector order 
        '''
        self.bitVector = []       
        for i in range(0,self.bitLength):
            # choose a random init value for each bit on vector
            initValue = random.choice(self.fitValues)    
            self.bitVector.append(initValue) 
            




#-----------------------------------------------------------------||||||||||||--
class SortRecord:
    def __init__(self): # provide init values
        self.fitness = 0
        self.id = 0



#-----------------------------------------------------------------||||||||||||--
class GeneticAlgorithm:
    def __init__(self, popSize=8, fitVector=None, beatTime=120, 
                 crossoverRate=.40, mutationRate=.011,
                initMutate=True, firstVector=None):
        '''
        >>> v = [(4,3,0), (2,1,1), (4,2,1)]
        >>> a = GeneticAlgorithm(20, v)
        >>> len(a.population)
        20
        >>> len(a.newPopulation)
        20


        '''
        if fitVector == None: # get default
            fitVector = [(8,3,1),(8,3,1),(8,1,0),(4,1,1)]

        self.fitVector = fitVector
        self.bitLength = len(self.fitVector)
        self.beatTime = beatTime
        self.crossoverRate = crossoverRate
        self.mutationRate = mutationRate
        self.populationSize = popSize
        # poulation is a numbered dictionary of chromosomes
        self.population = {}
        self.newPopulation = {}
        
        # initialize populations with a chromosome object
        for i in range(self.populationSize):
            self.population[i] = Chromosome(self.fitVector, self.mutationRate,
                                self.beatTime, initCheck=True, 
                                initMutate=initMutate, firstVector=firstVector) # assign instance
            #self.population[i].calcFitness()     # calc fitness       
            self.newPopulation[i] = Chromosome(self.fitVector, 
                              self.mutationRate, self.beatTime, initCheck=True,
                                initMutate=initMutate, firstVector=firstVector)
            #self.newPopulation[i].calcFitness()

        # sort is a dictionary of sort records
        self.sortDict = {} 
        for i in range(self.populationSize):
            self.sortDict[i] = SortRecord()   # dict of sort record
            
        self._sortPopulation()
        # gets the ID (key) number of best chromo
        self.bestC = self.sortDict[0].id      


    def _totalFitness(self):
        """calculate total fitness

        >>> v1 = [(4,3,0), (2,1,1), (4,2,1)]
        >>> v2 = [(4,3,0), (2,3,1), (4,2,1)]
        >>> a = GeneticAlgorithm(20, v1, initMutate=False, firstVector=v1)
        >>> a._totalFitness() # perfect match
        (0.0, 0.0)

        >>> a = GeneticAlgorithm(20, v1, initMutate=False, firstVector=v2)
        >>> a._totalFitness() # perfect match
        (12857.200000000003, 642.86000000000001)

        """
        maxFitness = 0 # this is the worst value
        fitnessSum = 0
        for key in self.population.keys():
            fitnessSum = fitnessSum + self.population[key].fitness
            if self.population[key].fitness >= maxFitness:
                maxFitness = self.population[key].fitness
        return fitnessSum, maxFitness

    def getAvgFitness(self):
        """average fitness
        >>> v1 = [(4,3,0), (2,1,1), (4,2,1)]
        >>> v2 = [(4,3,0), (2,3,1), (4,2,1)]
        >>> a = GeneticAlgorithm(20, v1, initMutate=False, firstVector=v1)
        >>> a.getAvgFitness() # perfect match
        0.0

        >>> a = GeneticAlgorithm(20, v1, initMutate=False, firstVector=v2)
        >>> a.getAvgFitness() # perfect match
        642.860...

        """
        fitnessSum, maxFitness = self._totalFitness()
        avgFitness = fitnessSum / float(self.populationSize)
        return avgFitness

    
    def _selectParent(self): # rulette wheel selection
        # this deals with decimals by multiplying all fitness numbers
        fitScaler = 10  
        fitnessSum, maxFitness = self._totalFitness()

        # proportional slices from adjusted fitness
        # min adjusted fitness == (maxFit * 1.5) - 0         
        # max adjusted fitness == (maxFit * 1.5) - maxFit    (best chromo)

        # this adjust means that not all areas will be available for selection?
        maxFitness = maxFitness * 1.5 
        
        adjustedSum = 0
        for key in self.population.keys():
            adjustedSum = adjustedSum + int(round((maxFitness - 
                             self.population[key].fitness) * fitScaler))      

        #TODO: rewrite with unit.py tools        
        stopPoint = random.randint(0,adjustedSum)
        currentPoint = 0
        chromoKeys = self.population.keys()
        for dummykey in self.population.keys(): # keys are randomized
            key = random.choice(chromoKeys)
            keyPosition = chromoKeys.index(key)
            del chromoKeys[keyPosition]
            
            localStart = currentPoint
            # subtract fitness from max to increase percentage of lowest valued
            localStop = currentPoint + int(round((maxFitness - 
                            self.population[key].fitness) * fitScaler))
            currentPoint = currentPoint + int(round((maxFitness - 
                                self.population[key].fitness) * fitScaler))
            # stopPoint is the value we are looking for
            if stopPoint >= localStart and stopPoint <= localStop:
                return self.population[key]

        return self.population[key]  # gets last one in case of breakage

    def _getParents(self):
        '''
        >>> v1 = [(4,3,0), (2,1,1), (4,2,1)]
        >>> v2 = [(4,3,0), (2,3,1), (4,2,1)]
        >>> a = GeneticAlgorithm(20, v1, initMutate=False, firstVector=v1)
        >>> b, c = a._getParents()
        >>> b.bitVector
        [(4, 3, 0), (2, 1, 1), (4, 2, 1)]
        >>> c.bitVector
        [(4, 3, 0), (2, 1, 1), (4, 2, 1)]

        '''

        mom = self._selectParent()
        dad = self._selectParent()
        if mom.bitVector == dad.bitVector: # try to get a different pair
            counter = 0
            while 1:
                dad = self._selectParent()
                # see if these are the same instance
                if mom.bitVector != dad.bitVector: 
                    break
                counter += 1
                if counter > 20:
                    environment.printDebug(['cannot find different parents; getting random parent'])
                    dad = self.population[random.randint(
                          0, self.populationSize-1)]    
                    break
        return dad, mom
    

    def _sortPopulation(self):      
        sortList = []
        for key in self.population.keys():
            sortList.append((self.population[key].fitness, key))
        sortList.sort()
        #sortList.reverse()
        i = 0
        for entry in sortList:
            fitness, key = entry
            self.sortDict[i].fitness = fitness
            self.sortDict[i].id = key
            i = i + 1
        self.bestC = self.sortDict[0].id
            

    def _mate(self, chromoDad, chromoMom, offspringList):
        """
        >>> a = Chromosome([(4,1,1), (2,1,1), (4,3,1)])
        >>> b = Chromosome([(2,3,0), (4,1,1), (4,1,1)])

        >>> v1 = [(4,3,0), (2,1,1), (4,2,1)]
        >>> ga = GeneticAlgorithm(20, v1, initMutate=False, firstVector=v1)
        """
        # list of chromo object references
        offspringDict = {}
        i = 0
        for entry in offspringList:
            offspringDict[i] = entry
            i += 1
        maxIndex = i

        j = 0
        while j < maxIndex:
            # there is another offspring avaiable
            if (j+1) in offspringDict.keys(): 
                chromoA = offspringDict[j]
                chromoB = offspringDict[j+1]
                locus = 0
                # percantage that are crossed over
                if (random.randint(0,9999) / 10000.0) < self.crossoverRate:  
                    locusP, locusQ = getTwoLoci(self.bitLength)
                
                    Da = copy.deepcopy(chromoDad.bitVector[0:locusP])   # i 
                    Db = copy.deepcopy(chromoDad.bitVector[locusP:locusQ])
                    Dc = copy.deepcopy(
                        chromoDad.bitVector[locusQ:self.bitLength])
                    Ma = copy.deepcopy(chromoMom.bitVector[0:locusP])   # i 
                    Mb = copy.deepcopy(chromoMom.bitVector[locusP:locusQ])
                    Mc = copy.deepcopy(
                        chromoMom.bitVector[locusQ:self.bitLength])
        
                    chromoA.bitVector = Da + Mb + Dc
                    chromoB.bitVector = Ma + Db + Mc
                else: # create a clone,  # copies entire vector
                    chromoA.bitVector = copy.deepcopy(chromoDad.bitVector)
                    chromoB.bitVector = copy.deepcopy(chromoMom.bitVector)  
                j += 2

            else: # one off spring left
                chromo = offspringDict[j]
                locus = 0
                if (random.randint(0,9999) / 10000.0) < self.crossoverRate:
                    locusP, locusQ = getTwoLoci(self.bitLength)
                
                    Da = copy.deepcopy(chromoDad.bitVector[0:locusP])   # i 
                    Db = copy.deepcopy(chromoDad.bitVector[locusP:locusQ])
                    Dc = copy.deepcopy(
                        chromoDad.bitVector[locusQ:self.bitLength])
                    Ma = copy.deepcopy(chromoMom.bitVector[0:locusP])   # i 
                    Mb = copy.deepcopy(chromoMom.bitVector[locusP:locusQ])
                    Mc = copy.deepcopy(
                        chromoMom.bitVector[locusQ:self.bitLength])
    
                    if random.randint(0,1) == 1:    # pick random arrangment
                        bitV = Da + Mb + Dc
                    else:
                        bitV = Ma + Db + Mc
                    chromo.bitVector = bitV
                else: # create a clone, # copies entire vector
                    chromo.bitVector = copy.deepcopy(chromoDad.bitVector) 
                j += 1

    # list of chromo object reference
    def _mateOnePoint(self, chromoDad, chromoMom, offspringList): 
        offspringDict = {}
        i = 0
        for entry in offspringList:
            offspringDict[i] = entry
            i = i + 1
        for key in offspringDict.keys():
            chromo = offspringDict[key]
            locus = 0
            if (random.randint(0,9999) / 10000.0) < self.crossoverRate:
                locus = random.randint(0,self.bitLength-1)
                if random.randint(0,1): # flip which parent is first randomly
                    a = copy.deepcopy(chromoDad.bitVector[0:locus])  # i 
                    b = copy.deepcopy(chromoMom.bitVector[locus:self.bitLength]) 
                else:
                    b = copy.deepcopy(chromoDad.bitVector[0:locus])  # i 
                    a = copy.deepcopy(chromoMom.bitVector[locus:self.bitLength]) 
                chromo.bitVector = a + b
            else: # create a clone, # copies entire vector
                chromo.bitVector = copy.deepcopy(chromoDad.bitVector) 

    #-----------------------------------------------------------------------||--             
    def generationStep(self, percentElite=.00):
        """process one generation 

        >>> v1 = [(4,3,0), (2,1,1), (4,2,1)]
        >>> v2 = [(4,3,0), (2,3,1), (4,2,1)]
        >>> a = GeneticAlgorithm(20, v1, initMutate=False, firstVector=v2)
        >>> a.generationStep()

        >>> a = GeneticAlgorithm(20, v1)
        >>> a.generationStep()
        >>> a.generationStep()

        """
        i = 0
        cutoffIndex = int(round(percentElite * self.populationSize))
        eliteCount  = 0
        while i < self.populationSize:
            # take a percentage of elite and pass to next gen
            if i < cutoffIndex: 
                self.newPopulation[i] = copy.deepcopy(
                     self.population[self.sortDict[eliteCount].id])
                eliteCount = eliteCount + 1
                i = i + 1
                continue
                
            chromoDad, chromoMom = self._getParents()
            if (i < self.populationSize-1):
                son = Chromosome(self.fitVector, self.mutationRate, self.beatTime)
                daughter = Chromosome(
                    self.fitVector, self.mutationRate, self.beatTime)
                # third arg is ref to offspring obj
                self._mate(chromoDad, chromoMom, [son, daughter]) 

                self.newPopulation[i] = son
                self.newPopulation[i].mutate()
                self.newPopulation[i].calcFitness()
                self.newPopulation[i+1] = daughter
                self.newPopulation[i+1].mutate()
                self.newPopulation[i+1].calcFitness()
                i = i + 2
            else: # case of an odd sized population, last chromo
                son = Chromosome(self.fitVector, self.mutationRate, self.beatTime)
                # third arg is ref to offspring obj
                self._mate(chromoDad, chromoMom,[son,])  
                self.newPopulation[i] = son
                self.newPopulation[i].mutate()  #prop here
                self.newPopulation[i].calcFitness()
                i = i + 1
                    
        for i in range(0, self.populationSize):
            self.population[i] = copy.deepcopy(self.newPopulation[i])
            del self.newPopulation[i]
        self._sortPopulation()
        # returns key of best vector in population 
        self.bestC = self.sortDict[0].id 




#-----------------------------------------------------------------||||||||||||--
class Genome:
    def __init__(self, popSize=20, fitVector=None, beatTime=120.0, 
                    crossoverRate=.70, mutationRate=.025, percentElite=.00):
        """
        >>> v1 = [(4,3,0), (2,1,1), (4,2,1)]
        >>> v2 = [(4,3,0), (2,3,1), (4,2,1)]
        >>> a = Genome(20, v1)
        >>> a.gen(30)
        """
        if fitVector == None:
            fitVector = [(8,3,1),(8,3,1),(8,1,0),(4,1,1)]
        self.popSize = popSize
        self.fitVector = fitVector
        self.beatTime = beatTime

        self.ga = GeneticAlgorithm(popSize, self.fitVector, self.beatTime, 
                  crossoverRate, mutationRate)

        self.genCounter = 0
        self.lastBestBitVector = []
        self.uniqueBestList   = []
        self.trueUniqueBestList= []
        self.trueUniqueSecondBestList = []

        self.bitLength = len(self.fitVector)
        self.percentElite = percentElite

    def _testMatch(self, chromoA, chromoB):
        matchValue = 0
        for i in range(0,len(chromoA)):
            aDiv,aMult,aStat = chromoA[i]    
            bDiv,bMult,bStat = chromoB[i]    
            
            durDif = abs((aMult / (aDiv + 0.0)) - (bMult / (bDiv+0.0)))
            if durDif < .00001 and aStat == bStat:
                matchValue = matchValue + 1
        if matchValue == len(chromoA): # each position matches
            return 1 # they are the same
        else:
            return 0 # not the same
        
    def gen(self, numGenerations=50, silentDisplay=False):
        # silentDisplay = 0 shows all, =1 supress geninfo, =2 supress all info
        maxVectorSize = 40
        for i in range(0, numGenerations):
            # do 10 cycles for each generation
            for i in range(0,1): 
                self.ga.generationStep(self.percentElite)
                self.genCounter = self.genCounter + 1
                
                tempVectorListA = []
                for entry in self.uniqueBestList:
                    fitness, chromo = entry
                    tempVectorListA.append(chromo)
                if (self.ga.population[self.ga.bestC].bitVector not in 
                    tempVectorListA):
                    self.uniqueBestList.append( 
                        (self.ga.population[self.ga.bestC].fitness, 
                        self.ga.population[self.ga.bestC].bitVector) )   
                        
            self.lastBestBitVector = copy.deepcopy( 
                           self.ga.population[self.ga.bestC].bitVector)

            if not silentDisplay: # if 0
                sampleChromo = str(
                    self.ga.population[self.ga.bestC].bitVector).replace(" ", "")

                avgFit = "%.2f" % self.ga.getAvgFitness()              
                bstFit = "%.2f" % self.ga.population[self.ga.bestC].fitness
                bstLine = 'bstFit:%s' % bstFit

                bstDur = "%.2f" % self.ga.population[self.ga.bestC].duration
                durLine = 'bstDur:%s' % bstDur

                fitChromo = str(self.fitVector).replace(" ","")
                fitDur = "%.2f" % self.ga.population[self.ga.bestC].fitDuration

                genPrintLine = "bst%s i:%5i avgFit:%s" % ( 
                               sampleChromo, self.genCounter, avgFit)
                genPrintLine = genPrintLine + ' ' + bstLine + ' ' + durLine
                environment.printDebug([genPrintLine])
            
                if self.genCounter % 20 == 0: # print every 20 counts
                    msg = "fit chromosome: %s" % fitChromo
                    environment.printDebug([msg])
                    
                    msg = ("Pn:%s  Pc:%.3f  Pm:%.3f fitDur:%s" %     
                        (self.ga.populationSize, self.ga.crossoverRate,  
                         self.ga.mutationRate, fitDur))
                    environment.printDebug([msg])

        self.uniqueBestList.sort()
        if not silentDisplay:
            environment.printDebug(['unique BestFit BitVectors'])
            for entry in self.uniqueBestList:
                fitness, chromo = entry
                sampleChromo = str(chromo).replace(" ","")
                msg = "%s fitness = %.4f" % (sampleChromo, fitness)
                environment.printDebug([msg])
            
        for entry in self.uniqueBestList:
            fitnessA, chromoA = entry   # this is the chromo to test
            if len(self.trueUniqueBestList) == 0:
                self.trueUniqueBestList.append((fitnessA, chromoA )) 
                continue
            uniqueScore = 0  
            # must test agains all already found items
            for uniqueEntry in self.trueUniqueBestList: 
                fitnessB, chromoB = uniqueEntry
                # compare each found to best of this pop
                matchCheck = self._testMatch(chromoA, chromoB) 
                if matchCheck == 1: # a chromo like this already exists
                    continue
                else:    # these chromos are not the same
                    uniqueScore = uniqueScore + 1
            # chromoA is unique to each one
            if uniqueScore == len(self.trueUniqueBestList): 
                self.trueUniqueBestList.append((fitnessA, chromoA))  
 
        self.trueUniqueBestList.sort()            
        if not silentDisplay:
            environment.printDebug(['true unique BestFit BitVectors'])
            for entry in self.trueUniqueBestList:
                fitness, chromo = entry
                sampleChromo = str(chromo).replace(" ","")
                msg = "%s fitness = %.4f" % (sampleChromo, fitness)
                environment.printDebug([msg])
        else:
            tubList = []
            for entry in self.trueUniqueBestList:
                fitness, chromo = entry       
                tubList.append(chromo)   
            return tubList
            
    #-----------------------------------------------------------------------||--             
    def edit(self, crossoverRate=.40, mutationRate=.025):
        self.ga.mutationRate = mutationRate
        self.ga.crossoverRate = crossoverRate
        
    def clear(self):
        for key in self.ga.population.keys():
            self.ga.population[key].randomize()
        self.genCounter = 0
        self.lastBestBitVector = []
        self.uniqueBestList   = []
        self.trueUniqueBestList= []
        






#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testRandom(self):

        pulsePool = [(4,1,0), (4,1,1), (4,2,1), (4,3,1), (4,4,1), (4,5,1), (4,6,1), (4,7,1)]

        for x in [4, 6, 8, 12, 16]:
            v = []
            for i in range(x): # size
                v.append(random.choice(pulsePool))
            environment.printDebug(['start', v])
            a = Genome(50, v, crossoverRate=.90, 
                       mutationRate=.15, percentElite=.01)            
            a.gen(50)
            environment.printDebug(['best last', a.lastBestBitVector])


#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)





#-----------------------------------------------------------------||||||||||||--
# if __name__ == '__main__':
# 
#     ga = Genome()
#     ga.gen()

# test rhythms:
# c = [(4,1,0),(3,1,1),(3,1,1),(3,1,0),(2,1,0),(8,1,1)]
# d = [(5,1,1),(5,1,1),(5,1,1),(5,1,0),(5,1,1),(4,1,0)]
# c
# f = [(8,1,0),(8,3,1),(4,1,0),(4,1,1)]

# end
