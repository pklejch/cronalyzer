#!/usr/bin/python3
from subprocess import call
import sys
import time
import math

OUTPUT="./data/lengths.txt"

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
        with open(fileName,"a+") as file:
            file.write(str(self._length)+" "+command+"\n")
        
if __name__ == "__main__":
    arguments=sys.argv
    command=arguments[1:]
    if len(command) == 0:
        exit(1)
    wrapper=CCronWrapper(command)
    wrapper.measureTime()
    wrapper.writeLengthToFile(OUTPUT)