#!/usr/bin/python3
#hlavni skript nastroje

import datetime
from datetime import timedelta
from CronPlotter import CCronPlotter
from CronParser import CCronParser
from ConfigParser import CConfigParser
from CronLogger import CCronLogger
from functions import createOutputDir
from functions import checkPredictionDuration
from functions import readArguments
from functions import checkEmptyCronJobs
from functions import testConfigFile
from functions import getLogFile
from CrontabCreator import CCrontabCreator
from CronReport import CCronReport
from functions import repairOutputDir
from functions import handler
from functions import checkLogFile
import sys
import optimize

def main():    
    #pokud neni zadan skript, zkusi se doplnit z aktualniho adresare
    if len(sys.argv[1:]) == 0:
        configFile="config.conf"
    else:
        configFile=readArguments(sys.argv[1:])
    testConfigFile(configFile)
    
    configParser=CConfigParser(configFile)
    options=configParser.parseConfig()
    
    #nacteni a vytvoreni slozky
    try:
        outputDir=options["outputdir"]
    except KeyError:
        outputDir="."
    options["outputdir"]=repairOutputDir(outputDir)        
    createOutputDir(outputDir)
    
    
    logFile=getLogFile(options)
    
    checkLogFile(logFile)
    try:
        logLevel=options["loglevel"]
    except KeyError:
        logFile="info"
        
        
    try:
        removeLog=options["removelogonstart"]
    except KeyError:
        removeLog=False    
    
    try:
        onlyAnalysis=options["onlyanalysis"]
    except KeyError:
        onlyAnalysis=False
        
    CCronLogger.logFile=logFile
    CCronLogger.logLevel=CCronLogger.setLogLevel(logLevel)
    
    CCronLogger.removeLog=removeLog
    CCronLogger.initLog()

    
    #parsovani crontabu
    cronParser=CCronParser(options)
    cronList=cronParser.parseCrontabs()
    crontabs=cronParser.getCrontabs()
    
    
    predictionDuration=checkPredictionDuration(options)
    timeInterval=timedelta(days=predictionDuration)
    now=datetime.datetime.now()
    then=now+timeInterval
    
    #predikce uloh
    i=0
    for cron in cronList:
        try:
            cron.predictUntil(then)
        except ValueError:
            errMsg="Error occured while predicting following cronjob "+str(cron)+", maybe job is badly configured"
            CCronLogger.errorToConsole(errMsg)
            CCronLogger.error(errMsg)
        #cron.printCron()
        i+=1
    
    
    #zkontroluje prazdne cron joby
    cronList,emptyCronList=checkEmptyCronJobs(cronList)
        
        
    #vykreslovani uloh
    plotter=CCronPlotter(cronList,options)
    anyCrons,std,maxW,minW=plotter.plotCronJobs()
    
    if not anyCrons:
        exit(1)
    
    statsBefore=[std,maxW,minW]
    
    start=plotter.startTime
    end=plotter.endTime
    duration=plotter.duration
    
    if onlyAnalysis:
        exit(0)
    
    #zavolani optimalizatoru
    shiftVector, newCronList = optimize.main(cronList,options)
    
    
    CCronLogger.info("Starting to plot improved cron jobs.")
    CCronLogger.infoToConsole("Starting to plot improved cron jobs.")
    
    #vykresleni uloh po optimalizaci
    plotterAfter = CCronPlotter(newCronList,options,True)
    anyCrons,std,maxW,minW=plotterAfter.plotCronJobs()
    
    statsAfter=[std,maxW,minW]
    
    #vytvoreni noveho crontabu
    crontabCreator = CCrontabCreator(shiftVector,cronList,emptyCronList,crontabs)
    newCrontab=crontabCreator.createCrontab()
    
    reporter = CCronReport(options,newCrontab, statsBefore, statsAfter, shiftVector, cronList)
    reporter.createReport()
    
    CCronLogger.finishLog(statsBefore,statsAfter)
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
