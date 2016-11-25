import random
from datetime import timedelta
import datetime
from CronJob import CCronJob
from CronLogger import CCronLogger
from deap import creator, base, tools
from collections import OrderedDict
import intervaltree
import math
import statistics
import os
from scoop import futures


class CCronOptimalizer:
    def __init__(self,cronList,options):
        self.cronList=cronList
        
        
        self.cnt=0
        
        self._maxShifts=[]
        self._minShifts=[]
        
        self.setOptions(options)
        
        self.totalIntervals = self._intervals * self._duration
        
        self.sumWeight=0
        self._origWeights=[]
        self._endPoints=set()
        
        
        self._prepareWeightList()
        self.testIntervals=self.createTestIntervals(self.firstTime - datetime.timedelta(minutes=self.smallestShift), self.lastTime+datetime.timedelta(minutes=self.largestShift))
        self.tree=self.createIntervalTree(self.testIntervals)
        
        
        
        self.currentIndex=0

    
    def setOptions(self,options):
        try:
            self._intervals=int(options["intervalsperday"])
            CCronLogger.debug("Intervals per day: "+str(self._intervals))
        except ValueError:
            CCronLogger.error("Invalid intervals per day. Setting to default: 10.")
            self._intervals=10
        except KeyError:
            CCronLogger.info("Intervals per day directive not found. Setting to default: 10.")
            self._intervals=10
            
        try:
            self._duration=int(options["predictionduration"])
            CCronLogger.debug("Duration of prediction: "+str(self._duration)+" days.")
        except ValueError:
            CCronLogger.error("Invalid duration of prediction. Setting to default: 30.")
            self._duration=30
        except KeyError:
            CCronLogger.info("Duration of prediction directive not found. Setting to default: 30.")
            self._duration=30
            
        try:
            self._numberOfGenerations=int(options["numberofgenerations"])
            CCronLogger.debug("Number of generations: "+str(self._numberOfGenerations)+" generations.")
        except ValueError:
            CCronLogger.error("Invalid number of generations. Setting to default: 100.")
            self._numberOfGenerations=100
        except KeyError:
            CCronLogger.info("Number of generations directive not found. Setting to default: 100.")
            self._numberOfGenerations=100
            
        try:
            self._sizeOfPopulation=int(options["sizeofpopulation"])
            CCronLogger.debug("Size of population: "+str(self._sizeOfPopulation)+".")
        except ValueError:
            CCronLogger.error("Invalid size of populaton. Setting to default: 75.")
            self._sizeOfPopulation=75
        except KeyError:
            CCronLogger.info("Size of population directive not found. Setting to default: 75.")
            self._sizeOfPopulation=75
            
        try:
            self._crossoverProb=float(options["crossoverprobability"])
            CCronLogger.debug("Crossover probability: "+str(self._crossoverProb * 100)+" %.")
        except ValueError:
            CCronLogger.error("Invalid crossover probability. Setting to default: 0.75.")
            self._crossoverProb=0.75
        except KeyError:
            CCronLogger.info("Invalid probability directive not found. Setting to default: 0.75.")
            self._crossoverProb=0.75
            
            
        try:
            self._mutationProb=float(options["mutationprobability"])
            CCronLogger.debug("Mutation probability: "+str(self._mutationProb * 100)+" %.")
        except ValueError:
            CCronLogger.error("Invalid mutation probability. Setting to default: 0.05.")
            self._mutationProb=0.05
        except KeyError:
            CCronLogger.info("Mutation probability directive not found. Setting to default: 0.05.")
            self._mutationProb=0.05
    
    def _prepareWeightList(self):
        cronID=0
        self.firstTime=datetime.datetime.now().replace(year=9999)
        self.lastTime=datetime.datetime.now().replace(year=1)
        
        self.smallestShift=None
        self.largestShift=None
        
        for cron in self.cronList:
            
            if len(cron.cronJobList) == 0:
                continue

            if cron.startTime < self.firstTime:
                self.firstTime=cron.startTime
                
            if cron.startTime is not None and cron.endTime > self.lastTime:
                self.lastTime=cron.endTime
                
            if (self.smallestShift == None) or (cron.leftShift < self.smallestShift):
                self.smallestShift = cron.leftShift
                
            if (self.largestShift == None) or (cron.leftShift > self.largestShift):
                self.largestShift = cron.leftShift
                
            if (self.smallestShift == None) or (cron.rightShift < self.smallestShift):
                self.smallestShift = cron.rightShift
                
            if (self.largestShift == None) or (cron.rightShift > self.largestShift):
                self.largestShift = cron.rightShift
                
            self._maxShifts.append(cron.rightShift)
            self._minShifts.append(cron.leftShift)
            for cronJob in cron.cronJobList:
                self._origWeights.append([cronJob.startTime,cronJob.endTime,cron.weight,cronID])
            cronID+=1
        
        self.cronNr=cronID-1
        self._origWeights=sorted(self._origWeights,key=lambda t: t[0])
        self.avgLoadAmount,_ = self.avgLoad(self._origWeights)
        print(self.avgLoadAmount)
    
    def genRandomShift(self,index):
        return random.randint(self._minShifts[index],self._maxShifts[index])
    
    def customInitRepeat(self,container,func,n):
        shifts=[]
        for i in range(n):
            shifts.append(func(i))
        return container(shifts)    
    
    def optimize(self):
        
        creator.create("FitnessMinLoad", base.Fitness, weights=(-1,))
        creator.create("Individual", list, fitness=creator.FitnessMinLoad)
        toolbox = base.Toolbox()
        # Attribute generator
        toolbox.register("map", futures.map)
        toolbox.register("attr_bool", self.genRandomShift)
        # Structure initializers
        toolbox.register("individual", self.customInitRepeat, creator.Individual, 
            toolbox.attr_bool, len(self.cronList))
        
        
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        
        # Operator registering
        toolbox.register("evaluate", self.evalOneMinLoad)
        toolbox.register("mate", tools.cxUniform, indpb=0.1)
        
        toolbox.register("mutate", tools.mutUniformInt, low=self._minShifts, up=self._maxShifts, indpb=0.01)
        toolbox.register("select", tools.selTournament, tournsize=3)
        
        
        random.seed(64)
        #random.seed(os.urandom(100))
        
        pop = toolbox.population(n=self._sizeOfPopulation)
        CXPB, MUTPB, NGEN = self._crossoverProb, self._mutationProb, self._numberOfGenerations
        
        print("Start of evolution")
        
        # Evaluate the entire population
        fitnesses = list(toolbox.map(toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
        
        print("  Evaluated %i individuals" % len(pop))
        
        # Begin the evolution
        for g in range(NGEN):
            print("-- Generation %i --" % g)
            
            # Select the next generation individuals
            offspring = toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(toolbox.map(toolbox.clone, offspring))
        
            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values
    
            for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
            self.cnt+=1
        
            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            print("  Evaluated %i individuals" % len(invalid_ind))
            
            # The population is entirely replaced by the offspring
            pop[:] = offspring
            
            # Gather all the fitnesses in one list and print the stats
            fits = [ind.fitness.values[0] for ind in pop]
            
            length = len(pop)
            mean = sum(fits) / length
            sum2 = sum(x*x for x in fits)
            std = abs(sum2 / length - mean**2)**0.5
            
            print("  Min %s" % min(fits))
            print("  Max %s" % max(fits))
            print("  Avg %s" % mean)
            print("  Std %s" % std)
            
            myMax=-1
            if max(fits) > myMax:
                myMax=max(fits)
        
        print("-- End of (successful) evolution --")
        
        best_ind = tools.selBest(pop, 1)[0]
        print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))
        self.applyBestShift(best_ind)
        return best_ind, self.cronList
        
    def applyBestShift(self,shift):
        cronID=0
        for cron in self.cronList:
            shiftAmount=shift[cronID]
            for i in range(0,len(cron.cronJobList)):
                start=cron.cronJobList[i].startTime
                end=cron.cronJobList[i].endTime
                
                diff=timedelta(minutes=shiftAmount)
                start+=diff
                end+=diff
                
                cron.cronJobList[i]=CCronJob(start,end)
                
            cron.printCron()
            cronID+=1
                
    
    def applyShift(self,shift):
        firstTime = datetime.datetime.now().replace(year=9999)
        lastTime = datetime.datetime.now().replace(year=1)
        self.endPoints=set()
        for i in range(0,len(self._weights)):
            start, end, w, idCron = self._weights[i]
            shiftAmount=shift[idCron]
            
            diff=timedelta(minutes=shiftAmount)
            start+=diff
            end+=diff
            
            if start < firstTime:
                firstTime=start
                
            if end > lastTime:
                lastTime=end
            
            self._weights[i] = start, end, w, idCron
            
            self.endPoints.add(start)
            self.endPoints.add(end)
            
        return firstTime, lastTime
    
    def addWeight(self,w,amount):
        return w+amount
    
    def makeWeightList(self):
        intervalsFinal=[]
        summedWeights=OrderedDict()
        
        timeFormat="%Y-%m-%d %H:%M:%S"
        self.endPoints=sorted(self.endPoints)
        prevEndPoint=None
        
        
        for endPoint in self.endPoints:
            if prevEndPoint is not None:
                intervalsFinal.append([prevEndPoint,endPoint])
            prevEndPoint=endPoint
            
        for startX,endX in intervalsFinal:
            for startY,endY,weight,cronID in self._weights:
                if self.IsOverlap(startX,endX,startY,endY):
                    start=startX.strftime(timeFormat)
                    stop=endX.strftime(timeFormat)
                    try:
                        w=summedWeights[start+"$"+stop]
                        w+=weight
                        summedWeights[start+"$"+stop]=w
                    except KeyError:
                        summedWeights[start+"$"+stop]=weight
        
        print(summedWeights)
        return summedWeights
        
    
    def IsOverlap(self,startX,endX,startY,endY):
        if (startX < endY) and (startY < endX):
            return True
        else:
            return False     
        
    def toList(self,summedWeight):
        weights=[]
        timeFormat="%Y-%m-%d %H:%M:%S"
        for key,weight in self.summedWeights.items():
            start,stop = key.split("$")
            startTime=datetime.datetime.strptime(start,timeFormat)
            stopTime=datetime.datetime.strptime(stop,timeFormat)
            weights.append([startTime,stopTime,weight])
        return weights
    
    def avgLoad(self,weights):
        totalLoad=0
        totalDuration=0
        for start,end,weight,_ in weights:
            start=start.timestamp()
            end=end.timestamp()
            duration = end - start
            totalLoad+=duration * weight
            totalDuration+=duration
        
        return totalLoad / totalDuration, totalDuration
    
    def createIntervalTree(self,testIntervals):
        tree = intervaltree.IntervalTree()
        
        for start,end,weight in testIntervals:
            tree.addi(start, end, weight)
            
        return tree
    
    def createTestIntervals(self,firstTime, lastTime):
        duration = lastTime - firstTime
        part = duration / self.totalIntervals
        testIntervals = []
        
        tmpStart=firstTime
        #print("Testing intervals: ")
        for _ in range(0,self.totalIntervals):
            #print(tmpStart," ---> ",(tmpStart+part))
            testIntervals.append([tmpStart.timestamp(),(tmpStart+part).timestamp(),0])
            tmpStart+=part
            
        return testIntervals
        
    def sumWeightsInTestIntervals(self,tree,testIntervals):
        for start, end, w, _ in self._weights:
            results = tree.search(start.timestamp(),end.timestamp())
            for res in results:
                s,e,data = res
                data+=w
                tree.discard(res)
                tree.addi(s,e,data)
        return tree.items()
    
    def calculateStandardDeviation(self,testIntervals,avgLoad):
        diffs = []
        for _,_, w in testIntervals:
            diff = (w - avgLoad) ** 2
            diffs.append(diff)
        sumDiffs = sum(diffs)
        stdDev = math.sqrt(sumDiffs / self.totalIntervals)
        return stdDev
    
    def avgLoad2(self,testIntervals):
        totalLoad = 0 
        totalDuration = 0
        for start, end, weight in testIntervals:
            duration = end - start
            totalLoad += duration * weight
            totalDuration += duration
            
        return totalLoad / totalDuration
        
        
    def modifyCronList(self,individual):
        
        firstTime, lastTime = self.applyShift(individual)
        
        w2 = self.sumWeightsInTestIntervals(self.tree, self.testIntervals)
        
                
        #stdDev = self.calculateStandardDeviation(testIntervals, avgLoad)
        
        stdDev = statistics.stdev([row[2] for row in w2])
        
        #self.summedWeights=self.makeWeightList()
            
        #weightFin=self.toList(self.summedWeights)
        
        
        length = lastTime.timestamp() - firstTime.timestamp()
        diff = sum(individual)
        
        return stdDev, length, diff
    
    
        
    def evalOneMinLoad(self,individual):
        #print(individual)
        self._weights=self._origWeights[:]
        self.sumWeight=0
        avgLoad, length, diff=self.modifyCronList(individual)
        return avgLoad,length,diff,
        
        