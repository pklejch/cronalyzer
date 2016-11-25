#!/usr/bin/python3
from subprocess import call
import sys
import time
import math

OUTPUT="./durations.txt"

import configparser
class CConfigParser:
    def __init__(self, configName):
        self._configName=configName
        self._parser=configparser.RawConfigParser()
    def readOutFile(self):
        try:
            return self._parser.get("General", "FileWithDurations")
        except:
            return None
        
    def parseConfig(self):
        self._parser.read(self._configName, "utf-8")
        return self.readOutFile()
        

class CCronWrapper:
    def __init__(self, command):
        self._command=command
        
    def measureTime(self):
        startTime=time.time()
        call(self._command)
        endTime=time.time()
        self._length=math.ceil(endTime-startTime)
        
    def printLength(self):
        print(self._length)
        
    def writeLengthToFile(self,fileName):
        command=" ".join(self._command)
        try:
            with open(fileName,"a+") as file:
                file.write(str(self._length)+" "+command+"\n")
        except:
            pass
        
if __name__ == "__main__":

    arguments=sys.argv
    command=arguments[1:]
    if len(command) == 0:
        exit(1)
        
    parser=CConfigParser("/etc/cronalyzer/cronwrapper.conf")
    outFile=parser.parseConfig()
    if outFile is None:
        outFile=OUTPUT

    wrapper=CCronWrapper(command)
    try:
        wrapper.measureTime()
    except:
        pass
    wrapper.writeLengthToFile(outFile)