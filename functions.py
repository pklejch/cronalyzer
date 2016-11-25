from CronLogger import CCronLogger
import os
import sys
from argparse import ArgumentParser

def readArguments(args):
    parser=ArgumentParser()
    parser.add_argument("--version",action="version",version="1.0")
    parser.add_argument("config",help="Config file for cron analysis tool. Check man cronalyzer for more help.")
    arguments=parser.parse_args(args)
    return arguments.config

#chybovy vypis, ktery ukonci skript
def error(msg):
    print("[ERROR]: "+msg+"\n")
    exit(2)
    
def checkImportModule(module):
    try:
        __import__(module)
    except ImportError:
        return False
    else:
        return True

def testConfigFile(file):
    #existuje ?
    if not os.access(file,os.F_OK):
            error("Configuration file "+file+" doesn't exist.")
    
    #je to normalni soubor ?
    if not os.path.isfile(file):
            error("Configuration file "+file+" isn't regular file.")
            
    # je citelny ?
    if not os.access(file,os.R_OK):
            error("Configuration file "+file+" isn't readable.")
                
    #je prazdny ?
    if os.stat(file).st_size == 0:
            error("Configuration file "+file+" is empty.")

def checkEmptyCronJobs(cronList):
    newCronList=[]
    badCronList=[]
    for cron in cronList:
        if len(cron.cronJobList) > 0:
            newCronList.append(cron)
        else:
            CCronLogger.info("Following cron entry:"+str(cron)+" wont be analyzed or optimized, because it wont run in specified time window.")
            badCronList.append(cron)
    return newCronList,badCronList

def createOutputDir(outputDir):
    if os.path.exists(outputDir) and not os.path.isdir(outputDir):
        errorToConsole("Already exists file with same name as directory output.")
        exit(1)
    elif os.path.isdir(outputDir):
        infoToConsole("Output directory already exists.")
    elif not os.path.exists(outputDir):
        infoToConsole("Creating output directory: "+outputDir)
        os.makedirs(outputDir)
        
def getLogFile(options):
    try:
        logFile=options["outputdir"]+"logfile.log"
        debugToConsole("Log file: "+str(logFile)+".")
    except KeyError:
        infoToConsole("Output directory directive not found. Setting to default: working directory.")    
        logFile="./logfile.log"
    return logFile

def checkLogFile(file):
    if os.access(file,os.F_OK) and not os.path.isfile(file):
            error("Log file "+file+" isn't regular file.")

    if os.access(file,os.F_OK) and not os.access(file,os.W_OK):
            error("Log file "+file+" isn't writable.")
            
        
def checkPredictionDuration(options):
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
        
    return duration

def repairOutputDir(outputDir):
    #doplneni lomitka za konec slozky
    if not outputDir.endswith("/"):
        outputDir=outputDir+"/"
    return outputDir

def handler(signum, frame):
    CCronLogger.infoToConsole("Closing program.")
    exit(0)

def debugToConsole(msg):
    print("[debug]: "+msg)
    
def infoToConsole(msg):
    print("[info]: "+msg)
        
def errorToConsole(msg):
    print("[error]: "+msg)