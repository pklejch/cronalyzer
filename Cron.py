from CronPredictor import CCronPredictor
from itertools import count, groupby

class CCron:
    def __init__(self,minute,hour,day,month,dayOfWeek,user="",command="",length=0,weight=0,leftShift=0,rightShift=0,fromCrontab="",includeRareJobs=False):
        self.minute=minute
        self.hour=hour
        self.day=day
        self.month=month
        self.dayOfWeek=dayOfWeek
        self.user=user
        self.fromCrontab=fromCrontab
        self.predictor=CCronPredictor(self.minute, self.hour, self.day, self.month,
                                       self.dayOfWeek, length, command, includeRareJobs)
        
        #nactu informace jestli cron ma * v polozce dnu a dnu v tydnu
        self.allDays=self.predictor.getAllDays()
        self.allDaysOfWeek=self.predictor.getAllDaysOfWeek()
        
        #vyplneni metadat
        self.command=command
        self.length=length
        self.weight=weight
        self.leftShift=leftShift
        self.rightShift=rightShift
        self.cronJobList=[]
        self.cronJobCount=0
        self.overlaps=0
        self.spaceBetweenRuns=None
        
    def IsOverlap(self,startX,endX,startY,endY):
        if (startX < endY) and (startY < endX):
            return True
        else:
            return False         
        
    def countOverlaps(self):
        overlaps=0
        firstJob=None
        for job in self.cronJobList:
            if firstJob is not None:
                if self.IsOverlap(firstJob.startTime, firstJob.endTime, job.startTime, job.endTime):
                    overlaps+=1
                else:
                    break
            else:
                firstJob=job
        self.overlaps=overlaps
        
    def findStartEndTime(self):
        if len(self.cronJobList) > 0: 
            self.startTime=self.cronJobList[0].startTime
            self.endTime=self.cronJobList[-1].endTime
            self.duration=self.cronJobList[0].endTime-self.cronJobList[0].startTime

    def printCron(self):
        print(self.minute+" "+self.hour+" "+self.day+" "+self.month+" "+self.dayOfWeek+
              " "+self.user+" "+self.command+" # duration="+str(self.length)+", weight="+str(self.weight)+", shift="+str(self.leftShift)+":"+str(self.rightShift))
        
        for cronJob in self.cronJobList:
            print(str(cronJob.startTime)+" ---> "+str(cronJob.endTime))
            
            
    def createInfo(self):
        self.info=""
        if self.user!="":
            self.info=" "+self.user
        self.info=self.info+" "+self.command+" # duration="+str(self.length)+", weight="+str(self.weight)+", shift="+str(self.leftShift)+":"+str(self.rightShift)     
    
    def printInfo(self):
        print(self.info)
        
    def __str__(self):
        cron = self.minute+" "+self.hour+" "+self.day+" "+self.month+" "+self.dayOfWeek
        if self.user!="":
            cron=cron+" "+self.user
        cron=cron+" "+self.command+" # duration="+str(self.length)+", weight="+str(self.weight)+", shift="+str(self.leftShift)+":"+str(self.rightShift)
        return cron
    
    def cronToStr(self):
        cron=self.__str__()
        return cron
        
    def predict(self,n=10):
        self.cronJobList=self.predictor.iterate(n,self.cronJobList)
        self.findStartEndTime()
        self.cronJobCount=len(self.cronJobList)
        self.countOverlaps()
        
    def predictUntil(self,toDate):
        self.cronJobList=self.predictor.iterateUntil(toDate,self.cronJobList)
        self.findStartEndTime()
        self.cronJobCount=len(self.cronJobList)
        self.countOverlaps()
    
    def fillSets(self):
        self.minuteSet = self.predictor.minuteSet
        self.hourSet = self.predictor.hourSet
        self.daySet = self.predictor.daySet
        self.monthSet = self.predictor.monthSet
        self.dayOfWeekSet = self.predictor.dayOfWeekSet

    def createNewSets(self):
        self.newSets=str(self.minuteSet)+" "+ str(self.hourSet)+" "+str(self.daySet)+" "+str(self.monthSet)+" "+str(self.dayOfWeekSet)
        
    def printNewSets(self):
        print(self.newSets, end="")
        
    def repairNewSets(self):
        self.repairHourSet()
        self.repairMinuteSet()
        self.repairDaySet()
        self.repairMonthSet()
        self.repairDayOfWeekSet()
        
    def repairHourSet(self):
        if self.hourSet == list(range(0,24)):
            self.hourSet="*"
        else:
            self.hourSet = self.repairRanges(self.hourSet)
    
    def repairMinuteSet(self):
        if self.minuteSet == list(range(0,60)):
            self.minuteSet="*"
        else:
            self.minuteSet = self.repairRanges(self.minuteSet)
        
    def repairDaySet(self):
        if self.daySet == list(range(1,32)):
            self.daySet="*"
        else:
            self.daySet = self.repairRanges(self.daySet)
    
    def repairMonthSet(self):
        if self.monthSet == list(range(1,13)):
            self.monthSet = "*"
        else:
            self.monthSet = self.repairRanges(self.monthSet)
        
    
    def repairDayOfWeekSet(self):
        if self.dayOfWeekSet == list(range(0,7)):
            self.dayOfWeekSet = "*"
        else:
            self.dayOfWeekSet = self.repairRanges(self.dayOfWeekSet)
            
    def repairRanges(self,mySet):
        ranges=(list(x) for _,x in groupby(mySet, lambda x,c=count(): next(c)-x))
        return ",".join("-".join(map(str,(g[0],g[-1])[:len(g)])) for g in ranges)
        
    def test(self,name,n=100):
        self.predictor.test(name,n)
        