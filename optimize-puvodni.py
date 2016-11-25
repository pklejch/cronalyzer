#!/usr/bin/python3

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
import multiprocessing
import pickle

def init(cronList,options): 
    

    
    intervals,duration,numberOfGenerations,sizeOfPopulation,crossoverProb,mutationProb=setOptions(options)
    
    totalIntervals = intervals * duration
    
    
    
    origWeights2,firstTime,lastTime,smallestShift,largestShift,minShifts2,maxShifts2=prepareWeightList(cronList)
    global origWeights
    global maxShifts
    global minShifts
    origWeights=origWeights2
    
        
    global tree
    global testIntervals
    maxShifts=maxShifts2
    minShifts=minShifts2
    testIntervals=createTestIntervals(firstTime - datetime.timedelta(minutes=smallestShift), lastTime+datetime.timedelta(minutes=largestShift),totalIntervals)
    tree=createIntervalTree(testIntervals)
    

    shiftVector, newCronList = optimize(cronList, minShifts, maxShifts, sizeOfPopulation, numberOfGenerations, crossoverProb, mutationProb)
    
    return shiftVector, newCronList

def setOptions(options):
    #intervalu na den, delka predikce, generace, populace, sance na krizeni, sance na mutaci        
    return 1440,1,10,10,0.75,0.05
    

def prepareWeightList(cronList):
    cronID=0
    firstTime=datetime.datetime.now().replace(year=9999)
    lastTime=datetime.datetime.now().replace(year=1)
    
    smallestShift=None
    largestShift=None
    
    origWeights=[]
    maxShifts=[]
    minShifts=[]
    
    for startTime,endTime,leftShift,rightShift,cronJobList,weight in cronList:
        
        if len(cronJobList) == 0:
            continue

        if startTime < firstTime:
            firstTime=startTime
            
        if startTime is not None and endTime > lastTime:
            lastTime=endTime
            
        if (smallestShift == None) or (leftShift < smallestShift):
            smallestShift = leftShift
            
        if (largestShift == None) or (leftShift > largestShift):
            largestShift = leftShift
            
        if (smallestShift == None) or (rightShift < smallestShift):
            smallestShift = rightShift
            
        if (largestShift == None) or (rightShift > largestShift):
            largestShift = rightShift
            
        maxShifts.append(rightShift)
        minShifts.append(leftShift)
        for start,end in cronJobList:
            origWeights.append([start,end,weight,cronID])
        cronID+=1
    
    cronNr=cronID-1
    origWeights=sorted(origWeights,key=getKey)
    return [origWeights,firstTime,lastTime,smallestShift,largestShift,minShifts,maxShifts]

def getKey(a):
    return a[0]
    

def genRandomShift(index):
    return random.randint(minShifts[index],maxShifts[index])

def customInitRepeat(container,func,n):
    shifts=[]
    for i in range(n):
        shifts.append(func(i))
    return container(shifts)    
    
def applyBestShift(shift,cronList):
    cronID=0
    for j in range(0,len(cronList)):
        startTime,endTime,leftShift,rightShift,cronJobList,weight = cronList[j]
        shiftAmount=shift[cronID]
        for i in range(0,len(cronJobList)):
            start,end=cronJobList[i]

            
            diff=timedelta(minutes=shiftAmount)
            start+=diff
            end+=diff
            
            if start < startTime:
                startTime=start
            
            if end > endTime:
                endTime=end
            
            cronJobList[i]=[start,end]
        
        #ulozeni upraveneho cronu
        cronList[j] = startTime,endTime,leftShift,rightShift,cronJobList,weight
        #printCron()
        cronID+=1
    return cronList
            

def applyShift(shift,weights):
    firstTime = datetime.datetime.now().replace(year=9999)
    lastTime = datetime.datetime.now().replace(year=1)
    endPoints=set()
    for i in range(0,len(weights)):
        start, end, w, idCron = weights[i]
        shiftAmount=shift[idCron]
        
        diff=timedelta(minutes=shiftAmount)
        start+=diff
        end+=diff
        
        if start < firstTime:
            firstTime=start
            
        if end > lastTime:
            lastTime=end
        
        weights[i] = start, end, w, idCron
        
        endPoints.add(start)
        endPoints.add(end)
        
    return firstTime, lastTime

def addWeight(w,amount):
    return w+amount
    

def IsOverlap(startX,endX,startY,endY):
    if (startX < endY) and (startY < endX):
        return True
    else:
        return False     

def avgLoad(weights):
    totalLoad=0
    totalDuration=0
    for start,end,weight,_ in weights:
        start=start.timestamp()
        end=end.timestamp()
        duration = end - start
        totalLoad+=duration * weight
        totalDuration+=duration
    
    return totalLoad / totalDuration, totalDuration

def createIntervalTree(testIntervals):
    tree = intervaltree.IntervalTree()
    
    for start,end,weight in testIntervals:
        tree.addi(start, end, weight)
        
    return tree

def createTestIntervals(firstTime, lastTime, totalIntervals):
    duration = lastTime - firstTime
    part = duration / totalIntervals
    testIntervals = []
    
    tmpStart=firstTime
    #print("Testing intervals: ")
    for _ in range(0,totalIntervals):
        #print(tmpStart," ---> ",(tmpStart+part))
        testIntervals.append([int(tmpStart.strftime("%s")),int((tmpStart+part).strftime("%s")),0])
        tmpStart+=part
        
    return testIntervals
    
def sumWeightsInTestIntervals(tree,testIntervals,weights):
    for start, end, w, _ in weights:
        results = tree.search(int(start.strftime("%s")),int(end.strftime("%s")))
        for res in results:
            s,e,data = res
            data+=w
            tree.discard(res)
            tree.addi(s,e,data)
    return tree.items()

    
    
def modifyCronList(individual,weights):
    
    firstTime, lastTime = applyShift(individual,weights)
    
    w2 = sumWeightsInTestIntervals(tree, testIntervals, weights)
    
            
    #stdDev = calculateStandardDeviation(testIntervals, avgLoad)
    
    stdDev = statistics.stdev([row[2] for row in w2])
    
    #summedWeights=makeWeightList()
        
    #weightFin=toList(summedWeights)
    
    
    length = 0
    diff = sum(individual)
    
    return stdDev, length, diff


    
def evalOneMinLoad(individual):
    #print(individual)
    weights=origWeights[:]
    sumWeight=0
    avgLoad, length, diff=modifyCronList(individual,weights)
    return avgLoad,length,diff,

def optimize(cronList,minShifts,maxShifts,sizeOfPopulation,numberOfGenerations,crossoverProb, mutationProb):
    creator.create("FitnessMinLoad", base.Fitness, weights=(-1,))
    creator.create("Individual", list, fitness=creator.FitnessMinLoad)
    toolbox = base.Toolbox()
    # Attribute generator
    
    toolbox.register("attr_bool", genRandomShift)
    # Structure initializers
    toolbox.register("individual", customInitRepeat, creator.Individual, 
        toolbox.attr_bool, len(cronList))
    

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Operator registering
    toolbox.register("evaluate", evalOneMinLoad)
    toolbox.register("mate", tools.cxUniform, indpb=0.1)
    
    toolbox.register("mutate", tools.mutUniformInt, low=minShifts, up=maxShifts, indpb=0.01)
    toolbox.register("select", tools.selTournament, tournsize=3)
    
    pool = multiprocessing.Pool()
    toolbox.register("map", pool.map)
    random.seed(64)
    #random.seed(os.urandom(100))
    
    pop = toolbox.population(n=sizeOfPopulation)
    CXPB, MUTPB, NGEN = crossoverProb, mutationProb, numberOfGenerations
    
    print("Start of evolution")
    
    # Evaluate the entire population
    fitnesses = list(toolbox.map(evalOneMinLoad, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    print("  Evaluated %i individuals" % len(pop))
    
    # Begin the evolution
    for g in range(NGEN):
        print("-- Generation %i --" % g)
        
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
    
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
    
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(evalOneMinLoad, invalid_ind)
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
    cronList=applyBestShift(best_ind,cronList)
    return best_ind, cronList

def main(cronList,options):
    
    shiftVector, newCronList = init(cronList,options)
    
    
    return shiftVector, newCronList
if __name__ == '__main__':
    main()
    exit(0)