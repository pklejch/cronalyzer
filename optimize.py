#!/usr/bin/python3

import random
from datetime import timedelta
import datetime
from CronJob import CCronJob
from CronLogger import CCronLogger
import statistics
import multiprocessing
import os

try:
    from deap import creator, base, tools
    import intervaltree
except ImportError:
    CCronLogger.errorToConsole("You don't have required Python module.")
    CCronLogger.debugToConsole("Required modules are: deap, intervaltree")

def init(cronList,options): 
    
    global cnt
    cnt=0

    global intervalLen
    intervalLen,duration,numberOfGenerations,sizeOfPopulation,crossoverProb,mutationProb,parallel,mateOp, uniformProb, tournamentSize=setOptions(options)
    
    
    
    origWeights2,minShifts2,maxShifts2=prepareWeightList(cronList)
    
    global origWeights
    origWeights=origWeights2
    global maxShifts
    global minShifts
    maxShifts=maxShifts2
    minShifts=minShifts2
    

    shiftVector, newCronList = optimize(cronList, minShifts, maxShifts, sizeOfPopulation, numberOfGenerations, crossoverProb, mutationProb,parallel,mateOp, uniformProb, tournamentSize)
    
    return shiftVector, newCronList

def setOptions(options):
        try:
            intervalLen=int(options["testintervallength"])
            if intervalLen < 1:
                CCronLogger.error("Invalid interval length. Setting to default: 1.")
                intervalLen=1
            CCronLogger.debug("Interval length: "+str(intervalLen))
        except ValueError:
            CCronLogger.error("Invalid interval length. Setting to default: 1.")
            intervalLen=1
        except KeyError:
            CCronLogger.info("Interval length directive not found. Setting to default: 1.")
            intervalLen=1
            
            
        try:
            mateOp=options["mateoperator"]
            mateOp=mateOp.lower()
            if mateOp == "onepoint" or mateOp == "twopoint" or mateOp == "uniform":
                CCronLogger.debug("Mate operator: "+str(mateOp))
            else:
                CCronLogger.error("Unknown value for mate operator. Setting to default: OnePoint.")
                mateOp="onepoint"
        except KeyError:
            CCronLogger.info("Mate operator directive not found. Setting to default: OnePoint.")
            mateOp="onepoint"
            
        try:
            parallel=options["parallelcomputation"]
            CCronLogger.debug("Parallel computation: "+str(parallel))
        except KeyError:
            CCronLogger.info("Parallel computation directive not found. Setting to default: false.")
            parallel=False
            
        try:
            duration=int(options["predictionduration"])
            if duration < 1:
                CCronLogger.error("Invalid duration of prediction. Setting to default: 30.")
                duration=30
            CCronLogger.debug("Duration of prediction: "+str(duration)+" days.")
        except ValueError:
            CCronLogger.error("Invalid duration of prediction. Setting to default: 30.")
            duration=30
        except KeyError:
            CCronLogger.info("Duration of prediction directive not found. Setting to default: 30.")
            duration=30
            
        try:
            numberOfGenerations=int(options["numberofgenerations"])
            if numberOfGenerations < 1:
                CCronLogger.error("Invalid number of generations. Setting to default: 100.")
                numberOfGenerations=100
            CCronLogger.debug("Number of generations: "+str(numberOfGenerations)+" generations.")
        except ValueError:
            CCronLogger.error("Invalid number of generations. Setting to default: 100.")
            numberOfGenerations=100
        except KeyError:
            CCronLogger.info("Number of generations directive not found. Setting to default: 100.")
            numberOfGenerations=100
            
        try:
            sizeOfPopulation=int(options["sizeofpopulation"])
            if sizeOfPopulation < 1:
                CCronLogger.error("Invalid size of populaton. Setting to default: 75.")
                sizeOfPopulation=75
            CCronLogger.debug("Size of population: "+str(sizeOfPopulation)+".")
        except ValueError:
            CCronLogger.error("Invalid size of populaton. Setting to default: 75.")
            sizeOfPopulation=75
        except KeyError:
            CCronLogger.info("Size of population directive not found. Setting to default: 75.")
            sizeOfPopulation=75
            
        try:
            crossoverProb=float(options["crossoverprobability"])
            if crossoverProb < 0:
                CCronLogger.error("Invalid crossover probability. Setting to default: 0.75.")
                crossoverProb=0.75
            CCronLogger.debug("Crossover probability: "+str(crossoverProb * 100)+" %.")
        except ValueError:
            CCronLogger.error("Invalid crossover probability. Setting to default: 0.75.")
            crossoverProb=0.75
        except KeyError:
            CCronLogger.info("Invalid probability directive not found. Setting to default: 0.75.")
            crossoverProb=0.75
            
            
        try:
            mutationProb=float(options["mutationprobability"])
            if mutationProb < 0:
                CCronLogger.error("Invalid mutation probability. Setting to default: 0.05.")
                mutationProb=0.05
            CCronLogger.debug("Mutation probability: "+str(mutationProb * 100)+" %.")
        except ValueError:
            CCronLogger.error("Invalid mutation probability. Setting to default: 0.05.")
            mutationProb=0.05
        except KeyError:
            CCronLogger.info("Mutation probability directive not found. Setting to default: 0.05.")
            mutationProb=0.05
            
        try:
            uniformProb=float(options["uniformoperatorprobability"])
            if uniformProb < 0:
                CCronLogger.error("Invalid Uniform crossover probability. Setting to default: 0.75.")
                uniformProb=0.75
            CCronLogger.debug("Uniform crossover probability: "+str(uniformProb * 100)+" %.")
        except ValueError:
            CCronLogger.error("Invalid Uniform crossover probability. Setting to default: 0.75.")
            uniformProb=0.75
        except KeyError:
            CCronLogger.info("Uniform crossover probability directive not found. Setting to default: 0.75.")
            uniformProb=0.75
            
        try:
            tournamentSize=int(options["tournamentsize"])
            if tournamentSize < 2:
                CCronLogger.error("Invalid tournament size. Setting to default: 3.")
                tournamentSize=3
            CCronLogger.debug("Tournament size: "+str(tournamentSize)+".")
        except ValueError:
            CCronLogger.error("Invalid tournament size. Setting to default: 3.")
            tournamentSize=3
        except KeyError:
            CCronLogger.info("Tournament size directive not found. Setting to default: 3.")
            tournamentSize=3
            
        return intervalLen, duration, numberOfGenerations,sizeOfPopulation,crossoverProb,mutationProb,parallel, mateOp, uniformProb, tournamentSize
    

def prepareWeightList(cronList):
    cronID=0
    
    origWeights=[]
    maxShifts=[]
    minShifts=[]
    
    for cron in cronList:
        leftShift=cron.leftShift
        rightShift=cron.rightShift
        cronJobList=cron.cronJobList
        weight=cron.weight
        
        if len(cronJobList) == 0:
            continue
            
        maxShifts.append(rightShift)
        minShifts.append(leftShift)
        
        
        for cronJob in cronJobList:
            start=cronJob.startTime
            end=cronJob.endTime
            origWeights.append([start,end,weight,cronID])
        cronID+=1
        
    
    CCronLogger.debugToConsole("Total number of cron jobs: "+str(len(origWeights)))
    
    origWeights=sorted(origWeights,key=getKey)
    return [origWeights,minShifts,maxShifts]

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
    for i in range(0,len(cronList)):
        cronJobList=cronList[i].cronJobList
        shiftAmount=shift[cronID]
        newCronJobList=[]
        
        newStart=None
        newEnd=None
        cronJobCnt=0
        for cronJob in cronJobList:
            start=cronJob.startTime
            end=cronJob.endTime

            
            diff=timedelta(minutes=shiftAmount)
            start+=diff
            end+=diff
            
            if cronJobCnt==0:
                newStart=start
            
            if cronJobCnt==len(cronJobList)-1:
                newEnd=end
            
            newCronJobList.append(CCronJob(start,end))
            cronJobCnt+=1
        
        #ulozeni upraveneho cronu
        cronList[i].startTime = newStart
        cronList[i].endTime = newEnd
        cronList[i].cronJobList = newCronJobList
        #printCron()
        cronID+=1
    return cronList
            

def applyShift(shift,weights):
    firstTime = datetime.datetime.now().replace(year=9999)
    lastTime = datetime.datetime.now().replace(year=1)
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
        
    return firstTime, lastTime, weights

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

def createTestIntervals(firstTime, lastTime, intervalLen):
    part = timedelta(minutes=intervalLen)
    testIntervals = []
    tmpStart=firstTime
    while tmpStart<lastTime:
        testIntervals.append([tmpStart.timestamp(),(tmpStart+part).timestamp(),0])
        #print(str(tmpStart)+" --- "+str(tmpStart+part))
        tmpStart+=part
    return testIntervals
    
def sumWeightsInTestIntervals(tree, weights, shifts):    
    #dotazovani
    for start, end, w, _ in weights:
        results = tree.search(start.timestamp(),end.timestamp())
        for res in results:
            s,e,data = res
            data+=w
            tree.discard(res)
            tree.addi(s,e,data)
    return tree.items()

    
    
def modifyCronList(individual,weights):
    firstTime,lastTime,weights=applyShift(individual, weights)
    testIntervals=createTestIntervals(firstTime,lastTime,intervalLen)
    tree=createIntervalTree(testIntervals)
    
    w2 = sumWeightsInTestIntervals(tree, weights, individual)
    w2 = sorted(w2,key=lambda time: time[0])
    
    stdDev = statistics.pstdev([row[2] for row in w2])
    
    length = lastTime - firstTime
    diff = sum(map(abs,individual))
    
    return stdDev, length, diff


    
def evalOneMinLoad(individual):
    weights=origWeights[:]
    avgLoad, length, diff=modifyCronList(individual,weights)
    return avgLoad,length,diff,

def optimize(cronList,minShifts,maxShifts,sizeOfPopulation,numberOfGenerations,crossoverProb, mutationProb, parallel, mateOp, uniformProb, tournamentSize):
    #zaregistrovani fitness
    creator.create("FitnessMinLoad", base.Fitness, weights=(-1,))
    
    #vytvoreni jedince
    creator.create("Individual", list, fitness=creator.FitnessMinLoad)
    toolbox = base.Toolbox()

    
    toolbox.register("gene", genRandomShift)
    
    
    # vytvoreni listu jedincu
    toolbox.register("individual", customInitRepeat, creator.Individual, toolbox.gene, len(cronList))
    

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # nastaveni fitness fce
    toolbox.register("evaluate", evalOneMinLoad)
    
    
    #nastaveni mate operatoru
    if mateOp == "uniform":
        toolbox.register("mate", tools.cxUniform, indpb=uniformProb)
    elif mateOp == "onepoint":
        toolbox.register("mate", tools.cxOnePoint)
    elif mateOp == "twopoint":
        toolbox.register("mate", tools.cxTwoPoint)
        
    
    #nastaveni operatoru mutace
    toolbox.register("mutate", tools.mutUniformInt, low=minShifts, up=maxShifts, indpb=1/len(cronList))
    toolbox.register("select", tools.selTournament, tournsize=tournamentSize)
    
    pool = multiprocessing.Pool()
    
    #vymena map za paralelni map
    if parallel:
        toolbox.register("map", pool.map)
    else:
        toolbox.register("map", map)
        
        
    #random.seed(64)
    random.seed(os.urandom(100))
    
    pop = toolbox.population(n=sizeOfPopulation)
    CXPB, MUTPB, NGEN = crossoverProb, mutationProb, numberOfGenerations
    
    CCronLogger.infoToConsole("Start of evolution")
    CCronLogger.info("Start of evolution")
    
    # ohodnoceni cele populace
    fitnesses = list(toolbox.map(evalOneMinLoad, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    CCronLogger.infoToConsole("  Evaluated %i individuals" % len(pop))
    CCronLogger.info("  Evaluated %i individuals" % len(pop))
    
    # zacatek evoluce
    for g in range(NGEN):
        CCronLogger.infoToConsole("-- Generation %i --" % g)
        CCronLogger.info("-- Generation %i --" % g)
        
        # vyber jedincu do dalsi populace
        offspring = toolbox.select(pop, len(pop))
        # klonovani vybranych jedincu
        offspring = list(toolbox.map(toolbox.clone, offspring))
    
        # aplikovani operatoru mutace a krizeni
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values
    
        # ohodnoceni jedincu
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(evalOneMinLoad, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        CCronLogger.infoToConsole("  Evaluated %i individuals" % len(invalid_ind))
        CCronLogger.info("  Evaluated %i individuals" % len(invalid_ind))
        
        pop[:] = offspring
        
        fits = [ind.fitness.values[0] for ind in pop]
        
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5
        
        CCronLogger.infoToConsole("  Min %s" % min(fits))
        CCronLogger.info("  Min %s" % min(fits))
        
        CCronLogger.infoToConsole("  Max %s" % max(fits))
        CCronLogger.info("  Max %s" % max(fits))
        
        CCronLogger.infoToConsole("  Avg %s" % mean)
        CCronLogger.info("  Avg %s" % mean)
        
        CCronLogger.infoToConsole("  Std %s" % std)
        CCronLogger.info("  Std %s" % std)
        
        myMax=-1
        if max(fits) > myMax:
            myMax=max(fits)
    
    CCronLogger.infoToConsole("-- End of (successful) evolution --")
    CCronLogger.info("-- End of (successful) evolution --")
    
    best_ind = tools.selBest(pop, 1)[0]
    CCronLogger.infoToConsole("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))
    CCronLogger.info("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))
    cronList=applyBestShift(best_ind,cronList)
    return best_ind, cronList

def main(cronList,options):
    
    shiftVector, newCronList = init(cronList,options)
    
    return shiftVector, newCronList

if __name__ == '__main__':
    main()
    exit(0)