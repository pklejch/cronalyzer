import datetime
import os

class CCronLogger:
    @classmethod
    def initLog(cls):   
        if os.path.exists(cls.logFile) and cls.removeLog:
            try:
                os.remove(cls.logFile)    
            except OSError:
                cls.errorToConsole("Removing log file failed.")   
        if cls.logLevel >= 0:
            with open(cls.logFile, "a") as file:
                now=datetime.datetime.now()
                nowDate=now.strftime("%d.%m.%Y %H:%M:%S")
                file.write("*** Logging started @ "+nowDate+" ***\n")
            
    @classmethod
    def finishLog(cls,statsBefore,statsAfter):
        if cls.logLevel >= 0:
            cls.createSumary(statsBefore, statsAfter)
            with open(cls.logFile, "a") as file:
                now=datetime.datetime.now()
                nowDate=now.strftime("%d.%m.%Y %H:%M:%S")
                file.write("*** Logging finished @ "+nowDate+" ***\n")
                
    @classmethod
    def createSumary(cls,before,after):
        cls.info("====================== SUMARY ======================")
        cls.info("BEFORE:")
        cls.info("\t Standard deviation in test intervals: "+str(before[0]))
        cls.info("\t Max weight in test intervals: "+str(before[1]))
        cls.info("\t Min weight in test intervals: "+str(before[2]))
        cls.info("AFTER:")
        cls.info("\t Standard deviation in test intervals: "+str(after[0]))
        cls.info("\t Max weight in test intervals: "+str(after[1]))
        cls.info("\t Min weight in test intervals: "+str(after[2]))
        cls.info("====================================================")
    
    @classmethod
    def setLogLevel(cls,logLevel):
        if logLevel.lower() == "debug":
            return 0
        elif logLevel.lower() == "info":
            return 1
        else:
            print("[info]: Unknown debug level, setting to info level.")
            return 1
        
    @classmethod
    def debug(cls,msg):
        msg=msg.replace("\n","\n\t")
        if cls.logLevel == 0:
            with open(cls.logFile, "a") as file:
                file.write("[debug]: "+msg+"\n")
    
    @classmethod
    def info(cls,msg):
        msg=msg.replace("\n","\n\t")
        if cls.logLevel == 1 or cls.logLevel == 0:
            with open(cls.logFile, "a") as file:
                file.write("[info]: "+msg+"\n")
    
    @classmethod
    def error(cls,msg):
        msg=msg.replace("\n","\n\t")
        with open(cls.logFile, "a") as file:
            file.write("[error]: "+msg+"\n")
                
    @classmethod
    def debugToConsole(cls,msg):
        if cls.logLevel==0:
            print("[debug]: "+msg)
    
    @classmethod    
    def debugToConsoleWithLineFeed(cls,msg):
        if cls.logLevel==0:
            print("[debug]: "+msg,end="\r")
            
    @classmethod
    def infoToConsole(cls,msg):
        if cls.logLevel==0 or cls.logLevel==1:
            print("[info]: "+msg)
            
    @classmethod
    def errorToConsole(cls,msg):
        print("[error]: "+msg)