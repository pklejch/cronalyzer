import datetime
from datetime import timedelta
from collections import OrderedDict
from CronLogger import CCronLogger
import random
import statistics

try:
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter
    from matplotlib.pyplot import savefig
    import intervaltree
    from numpy import  asarray
except ImportError:
    CCronLogger.errorToConsole("You don't have required Python module.")
    CCronLogger.debugToConsole("Required modules are: matplotlib, intervaltree, numpy")

class CCronPlotter:
    def __init__(self,cronList,options,plotBetter=False):
    
        self.plotBetter=plotBetter
        self.setOptions(options)
        
        self._endPoints=dict()
        self._weights=[]
        self._cronList=cronList
        self.oneMinute=timedelta(minutes=1)
        self.oneHour=timedelta(hours=1)
        self.oneDay=timedelta(days=1)
        self.oneWeek=timedelta(weeks=1)
        self.oneMonth=timedelta(weeks=4)
        self._ticks=[]
        
        self.cronJobsSum()
        self.findStartEndTime()
        self.testIntervals=self.createTestIntervals(self.startTime,self.endTime)
        self.tree=self.createIntervalTree(self.testIntervals)
        
    def cronJobsSum(self):
        self.cronJobsTotal=0
        newCronList=[]
        for cron in self._cronList:
            if len(cron.cronJobList) > 0:
                self.cronJobsTotal+=cron.cronJobCount
                newCronList.append(cron)
        self._cronList=newCronList
    
    def findStartEndTime(self):
        startTime=datetime.datetime.now().replace(year=9999)
        endTime=datetime.datetime.now().replace(year=1)
        for cron in self._cronList:
            if cron.startTime<startTime:
                startTime=cron.startTime
                
            if cron.endTime>endTime:
                endTime=cron.endTime
            
        self.startTime=startTime
        self.endTime=endTime
        self.totalDuration=endTime-startTime
        CCronLogger.debugToConsole("Start time of first job: "+str(startTime))
        CCronLogger.debugToConsole("End time of last job: "+str(endTime))
        CCronLogger.debugToConsole("Total duration: "+str(self.totalDuration))
        
    def createIntervalTree(self,testIntervals):
        tree = intervaltree.IntervalTree()
        
        for start,end,weight in testIntervals:
            tree.addi(start, end, weight)
            
        return tree

    def createTestIntervals(self,firstTime, lastTime):
        part = timedelta(minutes=self._intervalLen)
        testIntervals = []
        tmpStart=firstTime
        while tmpStart < lastTime:
            testIntervals.append([tmpStart.timestamp(),(tmpStart+part).timestamp(),0])
            #print(str(tmpStart)+" --- "+str(tmpStart+part))
            tmpStart+=part 
        return testIntervals
    
    def sumWeightsInTestIntervals(self,tree,testIntervals):
        for start, end, w in self._weights:
            results = tree.search(start.timestamp(),end.timestamp())
            for res in results:
                s,e,data = res
                data+=w
                tree.discard(res)
                tree.addi(s,e,data)
        return tree.items()    
    

    def setOptions(self,options):
        try:
            self._threshold=int(options["threshold"])
            if self._threshold < 0:
                CCronLogger.error("Invalid threshold. Setting to default: 30.")
                self._threshold=30
            CCronLogger.debug("Threshold: "+str(self._threshold))
        except ValueError:
            CCronLogger.error("Invalid threshold. Setting to default: 30.")
            self._threshold=30
        except KeyError:
            CCronLogger.info("Threshold directive not found. Setting to default: 30.")
            self._threshold=30
            
        try:
            self._duration=int(options["predictionduration"])
            if self._duration < 1:
                CCronLogger.error("Invalid duration of prediction. Setting to default: 30.")
                self._duration=30
            CCronLogger.debug("Duration of prediction: "+str(self._duration)+" days.")
        except ValueError:
            CCronLogger.error("Invalid duration of prediction. Setting to default: 30.")
            self._duration=30
        except KeyError:
            CCronLogger.info("Duration of prediction directive not found. Setting to default: 30.")
            self._duration=30
            
        try:
            self._intervalLen=int(options["testintervallength"])
            if self._intervalLen < 1:
                CCronLogger.error("Invalid interval length. Setting to default: 1.")
                self._intervalLen=1
            CCronLogger.debug("Interval length: "+str(self._intervalLen))
        except ValueError:
            CCronLogger.error("Invalid interval length. Setting to default: 1.")
            self._intervalLen=1
        except KeyError:
            CCronLogger.info("Interval length directive not found. Setting to default: 1.")
            self._intervalLen=1
            
        try:
            self._samplesize=int(options["loadgraphsamplesize"])
            if self._samplesize < 1:
                CCronLogger.error("Invalid sample size. Setting to default: 200.")
                self._samplesize=200
            CCronLogger.debug("Sample size: "+str(self._samplesize))
        except ValueError:
            CCronLogger.error("Invalid sample size. Setting to default: 200.")
            self._samplesize=200
        except KeyError:
            CCronLogger.info("Sample size directive not found. Setting to default: 200.")
            self._samplesize=200
            
        try:
            self._cronLenLimit=int(options["ignoreshortcronjobslimit"])
            if self._cronLenLimit < 1:
                CCronLogger.error("Invalid short cron job limit. Setting to default: 30s.")
                self._cronLenLimit=30
            CCronLogger.debug("Short cron job limit: "+str(self._cronLenLimit)+" seconds.")
        except ValueError:
            CCronLogger.error("Invalid short cron job limit. Setting to default: 30s.")
            self._cronLenLimit=30
        except KeyError:
            CCronLogger.info("Short cron job limit directive not found. Setting to default: 30s.")
            self._cronLenLimit=30
            
        try:
            self._showImages=options["showinteractiveimages"]
            CCronLogger.debug("Show interactive image: "+str(self._showImages))
        except KeyError:
            CCronLogger.info("Show interactive images directive not found. Setting to default: True.")
            self._showImages=True
            
        try: 
            self._ignoreShort=options["ignoreshortcronjobs"]
            CCronLogger.debug("Ignore short cron jobs: "+str(self._ignoreShort))
        except KeyError:
            CCronLogger.info("Ignore short cron jobs directive not found. Setting to default: False.")
            self._ignoreShort=False
            
        try:
            self._outputDir=options["outputdir"]
            CCronLogger.debug("Output directory: "+self._outputDir)
        except KeyError:
            CCronLogger.info("Output directory directive not found. Setting to default: working directory.")
            self._outputDir="./"
            
            
        try:
            self._timeFormat=options["timeformatonxaxis"]
            try:
                _=datetime.datetime.now().strftime(self._timeFormat)
            except ValueError:
                CCronLogger.error("Invalid time format. Setting to default: %d.%m.%Y %H:%M:%S")
                self._timeFormat="%d.%m.%Y %H:%M:%S"
            CCronLogger.debug("Time format on X axis: "+self._timeFormat)
        except KeyError:
            CCronLogger.info("Time format on X axis directive not found. Setting to default: %d.%m.%Y %H:%M:%S")
            self._timeFormat="%d.%m.%Y %H:%M:%S"
            
            
        try: 
            self.weightGraphLineWidth=float(options["weightgraphlinewidth"])
            if self.weightGraphLineWidth < 0.5:
                CCronLogger.error("Invalid weight graph line width. Setting to default: 0.75.")
                self.weightGraphLineWidth=0.75
            CCronLogger.debug("Weight graph line width: "+str(self.weightGraphLineWidth))
        except ValueError:
            CCronLogger.error("Invalid weight graph line width. Setting to default: 0.75.")
            self.weightGraphLineWidth=0.75
        except KeyError:
            CCronLogger.info("Weight graph line width directive not found. Setting to default: 0.75.")
            self.weightGraphLineWidth=0.75
            
        try: 
            self._graphName=options["graphname"]
            CCronLogger.debug("Graph name: "+self._graphName)
        except KeyError:
            CCronLogger.info("Graph name directive not found. Setting to default: graph.pdf.")
            self._graphName="graph.pdf"
            
        try: 
            self._weightGraphName=options["weightgraphname"]
            CCronLogger.debug("Weight graph name: "+self._weightGraphName)
        except KeyError:
            CCronLogger.info("Weight graph name directive not found. Setting to default: weightGraph.pdf.")
            self._weightGraphName="weightGraph.pdf"
            
        try: 
            self._approximation=options["loadgraphapproximation"]
            CCronLogger.debug("Weight graph approximaton: "+str(self._approximation))
        except KeyError:
            CCronLogger.info("Weight graph directive not found. Setting to default: True.")
            self._approximation=True
            
            
        
    def IsOverlap(self,startX,endX,startY,endY):
        if (startX < endY) and (startY < endX):
            return True
        else:
            return False                
    
    
    def makeWeightIntervals(self):
        summedWeights=OrderedDict()
        w2 = self.sumWeightsInTestIntervals(self.tree, self.testIntervals)
        w2 = sorted(w2,key=lambda time: time[0])
        centers=[]
        weights=[]
        maxW=0
        minW=None
        for start,end,w in w2:
            start=datetime.datetime.fromtimestamp(start)
            end=datetime.datetime.fromtimestamp(end)
            centers.append(start)
            centers.append(end)
            weights.append(w)
            weights.append(w)
            if w > maxW:
                maxW = w
            if minW is None or  w < minW:
                minW = w
            summedWeights[start.strftime("%Y-%m-%d %H:%M:%S")+"$"+end.strftime("%Y-%m-%d %H:%M:%S")]=w
        
        weightsForStatistics=[row[2] for row in w2]
        #print(weightsForStatistics)
        centers, weights = self.chooseRandomSample(centers,weights)
        
        return centers,weights,maxW,minW,summedWeights,weightsForStatistics
    
    
    def chooseRandomSample(self,centers,weights):
        centersAndWeights=[]
        #spojim do jednoho pole
        for i in range(0,len(centers)):
            centersAndWeights.append([centers[i],weights[i]])
        
        #vyberu vzorek
        if self._approximation:
            try:
                sample=random.sample(centersAndWeights,self._samplesize)
            except ValueError:
                CCronLogger.info("Sample larger than population. Using all data.")
                CCronLogger.infoToConsole("Sample larger than population. Using all data.")
                sample=centersAndWeights
            sample=sorted(sample,key=getKey)
        else:
            sample=centersAndWeights
        
        #roztrhnu do dvou poli
        centers=[]
        weights=[]
        
        for center, weight in sample:
            centers.append(center)
            weights.append(weight)
            
        return centers, weights
    
    def findLoadPeaks(self, summedWeights):
        loadPeaks=[]
        timeFormat="%Y-%m-%d %H:%M:%S"
        for interval,weight in summedWeights.items():
            if weight>self._threshold:
                start,stop = interval.split("$")
                startTime=datetime.datetime.strptime(start,timeFormat)
                stopTime=datetime.datetime.strptime(stop,timeFormat)
                loadPeaks.append([startTime,stopTime,weight])
        return loadPeaks
                
        
    def plotWeightGraph(self, length,centers, weights, maxWeight):
        #inicializace
        width = int(self._duration*10)
        if width > 25:
            width=25    
        fig = plt.figure(figsize=(width ,6))
        ax = fig.add_subplot(111)
        
        thresholds=asarray([self._threshold]*len(weights))
        
        plt.plot(centers,weights,color="k",lw=self.weightGraphLineWidth)
        
        plt.fill_between(centers,weights,thresholds,where=weights>thresholds,interpolate=True,color="r")

            
        ax.xaxis_date()
        
        
        dateFormat = DateFormatter(self._timeFormat)
            
        #nastaveni osyX format casu
        ax.xaxis.set_major_formatter(dateFormat)
             
        
        #rezerva na oseX
        
        #rozsah osyX (zacatecni,konecny cas) + nejaka rezerva
        #popis osyX
        plt.xlabel('Time')
        
        plt.ylabel("Load")
        fig.autofmt_xdate()
        
        padd=maxWeight/10
        plt.ylim(0,maxWeight+padd)
        
        #autoupraveni odsazeni kolem grafu, aby se tam veslo vsechno
        plt.tight_layout()
        
        #export do pdf
        if self.plotBetter:
            CCronLogger.info("Saving plot with weights to: "+self._outputDir+"improved_"+self._weightGraphName)
            CCronLogger.infoToConsole("Saving plot with weights to: "+self._outputDir+"improved_"+self._weightGraphName)
            try:
                savefig(self._outputDir+"improved_"+self._weightGraphName)
            except:
                CCronLogger.errorToConsole("Error while saving image.")
                CCronLogger.error("Error while saving image.")
        else:
            CCronLogger.info("Saving plot with weights to: "+self._outputDir+self._weightGraphName)
            CCronLogger.infoToConsole("Saving plot with weights to: "+self._outputDir+self._weightGraphName)
            try:
                savefig(self._outputDir+self._weightGraphName)
            except:
                CCronLogger.errorToConsole("Error while saving image.")
                CCronLogger.error("Error while saving image.")
        
        
        #ukazani grafu v Tk
        if self._showImages:
            plt.show()
        
    
    def _drawLine(self, y, start, stop, color='b'):
        
        #vykresli vodorovnou caru - y souradnice a dve x souradnice (zacatek, konec) 
        plt.hlines(y, start, stop, color, lw=self.lineWidth)
        
    
    def _countTotalOverlaps(self):
        totalOverlaps=0
        for cron in self._cronList:
            totalOverlaps+=(cron.overlaps + 1) 
            
        self.totalOverlaps=totalOverlaps
        
    def createStatistics(self,maxWeight,weights):
        std=round(statistics.pstdev(weights),1)
        
        msg="Standard deviation of weights in test intervals: "+str(std)
        CCronLogger.infoToConsole(msg)
        CCronLogger.info(msg)
        
        msg="Max weight in test interval: "+str(maxWeight)
        CCronLogger.infoToConsole(msg)
        CCronLogger.info(msg)
        
        return std
        
    def _setLineWidth(self):

        
        if self.totalOverlaps < 20:
            self.lineWidth = 15
        else:
            self.lineWidth=25
    
    def plotCronJobs(self):
        
        if len(self._cronList) == 0:
            CCronLogger.errorToConsole("No viable cron jobs to plot and analyze.")
            return False,None,None,None
        
        height_graph=2+ (len(self._cronList) / 2)             

        #inicializace
        fig = plt.figure(figsize=(8,height_graph))
        ax = fig.add_subplot(111)
        
        
        self._countTotalOverlaps()
        self._setLineWidth()
        
        firstTime=datetime.datetime.now().replace(year=9999)
        lastTime=datetime.datetime.now().replace(year=1)
        cronNameList=[]
        yLabels=[]
        
        cronCounter=0
        cronID=1
        counter=0
        
        shown=False
        print("Plotting cron jobs.")
        for cron in self._cronList:
            
            if self._ignoreShort and cron.duration < timedelta(seconds=self._cronLenLimit):
                CCronLogger.debug("Cron job "+str(cron)+" is too short, it will be skipped.")
                continue
            
            #pokud je prikaz moc dlouhy, orizni ho
            if len(cron.command) > 30:
                cronNameList.append(cron.command[0:27]+" ...")
            else:
                cronNameList.append(cron.command)
                
            if cron.overlaps > 0:
                CCronLogger.info("Cron job "+str(cron)+" starts before previous run isn't finished. It should be manually optimized.")
                CCronLogger.infoToConsole("Cron job "+str(cron)+" starts before previous run isn't finished. It should be manually optimized.")

                
            yLabels.append(cronID + (cron.overlaps / 2) )
            jobID=0
            for job in cron.cronJobList:
                                
                self._weights.append([job.startTime,job.endTime,cron.weight])
                
                self._endPoints[job.startTime]=None
                self._endPoints[job.endTime]=None
                
                if job.startTime<firstTime:
                    firstTime=job.startTime
                    
                if job.endTime>lastTime:
                    lastTime=job.endTime
                    
                #cron joby se prekryvaji
                if cron.overlaps>0:
                    #vykresli je nad sebe, cervene
                    self._drawLine(cronID + (jobID % (cron.overlaps + 1) ),job.startTime,job.endTime,"r")
                #crony se neprekryvaji
                else:
                    self._drawLine(cronID,job.startTime,job.endTime,"k")
                
                #prubeh
                progress=int(counter*100/self.cronJobsTotal)
                if not progress%5:
                    if not shown:
                        CCronLogger.debugToConsoleWithLineFeed("Progress: "+str(progress)+"%")
                        shown=True
                else:
                    shown=False


                counter+=1
                jobID+=1
            cronID+=(cron.overlaps+1)
            cronCounter+=1
            
            #pokud to neni posledni vykreslovany cron, udelej vodorovnou caru
            if cronCounter!=len(self._cronList):
                plt.axhline(cronID - 0.5,color="black")
        
        CCronLogger.debugToConsole("Progress: 100%")
        
        if counter == 0:
            CCronLogger.error("No crons to plot.")
            CCronLogger.errorToConsole("No crons to plot.")
            return False,None,None,None
            
        #osaX = cas
        ax.xaxis_date()
        #format casu na ose
        length=lastTime-firstTime
        
        self.startTime=firstTime
        self.endTime=lastTime
        self.duration=length
        
        dateFormat = DateFormatter(self._timeFormat)

            
        #nastaveni osyX format casu
        ax.xaxis.set_major_formatter(dateFormat)
             
        
        #rezerva na oseX
        delta=(lastTime-firstTime)/100
        
        
        #rozsah osy y
        plt.ylim(-0.5,cronID)
        
        #rozsah osyX (zacatecni,konecny cas) + nejaka rezerva
        plt.xlim(firstTime-delta, lastTime+delta)
        #popis osyX
        plt.xlabel('Time')
        
        
        #plt.ylabel("Cron jobs")
        
        fig.autofmt_xdate()
        

        
        
        centers, weights, maxWeight, minWeight, summedWeights,weightsForStatistics = self.makeWeightIntervals()
        
        std=self.createStatistics(maxWeight, weightsForStatistics)
        
        
        loadPeaks = self.findLoadPeaks(summedWeights)
        
        if len(loadPeaks) > 0:
            yLabels.insert(0, 0)
            cronNameList.insert(0, "Bottlenecks")
            plt.axhline(0.5,color="black",lw=2.5)
        
        loadPeaksLen=timedelta(seconds=0)
        totalWeight=0
        for peak in loadPeaks:
            plt.hlines(0, peak[0], peak[1], "r", lw=self.lineWidth)
            startTime=peak[0].strftime("%d.%m.%Y %H:%M:%S")
            endTime=peak[1].strftime("%d.%m.%Y %H:%M:%S")
            totalWeight+= peak[2]
            loadPeaksLen+=(peak[1]-peak[0])
            CCronLogger.info("Found bottleneck: "+startTime+" <---> "+endTime)
            
        CCronLogger.info("Total length of load peaks: "+str(loadPeaksLen)+" of total weight: "+str(totalWeight))
        CCronLogger.infoToConsole("Total length of load peaks: "+str(loadPeaksLen)+" of total weight: "+str(totalWeight))
        
        #popisky osyY: 1.arg list ID (unikatni cronjoby), 2.arg = list popisku (nazvy cronjobu)
        plt.yticks(yLabels, cronNameList)
        
        #autoupraveni odsazeni kolem grafu, aby se tam veslo vsechno
        plt.tight_layout()
        
        #export do pdf
        if self.plotBetter:
            CCronLogger.info("Saving plot with cron jobs to: "+self._outputDir+"improved_"+self._graphName)
            CCronLogger.infoToConsole("Saving plot with cron jobs to: "+self._outputDir+"improved_"+self._graphName)
            try:
                savefig(self._outputDir+"improved_"+self._graphName)
            except:
                CCronLogger.errorToConsole("Error while saving image.")
                CCronLogger.error("Error while saving image.")
        else:
            CCronLogger.info("Saving plot with cron jobs to: "+self._outputDir+self._graphName)
            CCronLogger.infoToConsole("Saving plot with cron jobs to: "+self._outputDir+self._graphName)
            try:
                savefig(self._outputDir+self._graphName)
            except:
                CCronLogger.errorToConsole("Error while saving image.")
                CCronLogger.error("Error while saving image.")
        
        #ukazani grafu v Tk
        if self._showImages:
            plt.show()
        
        self.plotWeightGraph(length, centers, weights, maxWeight)
        
        return True,std,maxWeight,minWeight

def getKey(item):
    return item[0]   
def getKey2(item):
    start,_=item[0].split("$")
    return start   
def getKey3(item):
    return item[1] 