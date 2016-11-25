#!/usr/bin/python3
from Cron import CCron
import urllib
from urllib import parse
from urllib import request

def test(testFile,n=100):
    #otevru soubor s testovacimi daty pro cteni
    file=open(testFile,"r")
    #aktualni cislo radky
    lineNr=0
    #nacti kazdy radek
    for line in file.readlines():
        #smaz bile znaky
        line=line.rstrip()
        #rozsekej radek podle mezer
        splitLine=line.split(" ")
        #vyvor cron a podle testovacich dat a udelej n iteraci a zapis je do souboru 
        CCron(splitLine[0],splitLine[1],splitLine[2],splitLine[3],splitLine[4]).test(lineNr,n)
        #porovnej vystup programu s vystupem z weboveho nastroje
        compare(line,lineNr,n)
        lineNr+=1
    file.close()
        
def compare(line,lineNr,n):
    #preved do URL formatu
    query=urllib.parse.quote(line,"")
    #sestav URL
    url="http://cron.schlitt.info/index.php?cron="+query+"&iterations="+str(n)+"&test=Test"
    #ziskej data z webu
    response=urllib.request.urlopen(url)
    data=response.read()
    text=data.decode('utf-8')
    
    #ziskej relevantni data
    output=text[(text.index('<ol class=\'cron\'>')+len('<ol class=\'cron\'>')):text.index("<li>…</li>")]
    output=output.strip()
    output=output.replace("<li>","")
    output=output.replace("</li>","")
    
    splittedOuput=output.split("\n")
    firstLineFromWeb=splittedOuput[0]
    lastLineFromWeb=splittedOuput[-1]
    
    
    #nacti vystup programu
    file=open("./test/output"+str(lineNr),"r")
    fileContent=file.read().strip()
    splittedFileContent=fileContent.split("\n")
    firstLineFromFile=splittedFileContent[0]
    lastLineFromFile=splittedFileContent[-1]
    
    file.close()
    
    #porovnej vystup programu a vystup weboveho nastroje
    if fileContent == output:
        print("Test #"+str(lineNr)+" OK")
    else:
        print("Test #"+str(lineNr)+" FAILED")
        print("********************************")
        print("FIRST LINE OF OUTPUT, WEB FIRST:")
        print(firstLineFromWeb)
        print(firstLineFromFile)
        print("LAST LINE OF OUTPUT, WEB FIRST:")
        print(lastLineFromWeb)
        print(lastLineFromFile)
        print("********************************")
        file=open("./test/output"+str(lineNr)+"_web","w+")
        file.write(output+"\n")
        file.close()
        
def main():
    test("data/crons1")
    
if __name__ == '__main__':
    main()
    
        