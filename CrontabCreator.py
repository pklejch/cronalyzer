from CronLogger import CCronLogger

class CCrontabCreator:
    def __init__(self,shiftVector,cronList,emptyCronList,crontabs):
        self.shiftVector=shiftVector
        self.cronList=cronList
        self.emptyCronList=emptyCronList
        self.crontabs=crontabs
        
        self.newCrontab=""
        
    def createLists(self,cron):
        cron.fillSets()
        
        
    def shiftCron(self,cron,shiftAmount):
                
        shiftAmountAbs=abs(shiftAmount)
        
        if shiftAmountAbs < 60 and shiftAmountAbs >=0:
            if shiftAmount < 0:
                minutes = -1*(shiftAmountAbs % 60)
            else:
                minutes = shiftAmount % 60
            #posouvam o 0 - 59 minut, hodina se muze posunout, taky den a mesic o 1
            shiftHour,direction = self.shiftMinute(cron,minutes)
            if shiftHour:
                if direction=="F":
                    shiftDay,direction=self.shiftHours(cron,1)
                elif direction=="B":
                    shiftDay,direction=self.shiftHours(cron,-1)
                if shiftDay:
                    if direction=="F":
                        shiftMonth,direction = self.shiftDays(cron,1)
                    elif direction=="B":
                        shiftMonth,direction = self.shiftDays(cron,-1)
                    if shiftMonth:
                        if direction == "F":
                            self.shiftMonths(cron,1)
                        elif direction == "B":
                            self.shiftMonths(cron,-1)
                            
        elif shiftAmountAbs >= 60 and shiftAmountAbs < 1440:
            #posouva se o 1 - 24(bez) hodin; den,mesic se muze posunout o 1
            if shiftAmount < 0:
                minutes = -1*(shiftAmountAbs % 60)
                hours = -1*(shiftAmountAbs // 60)
            else:
                minutes = shiftAmount % 60
                hours = shiftAmount // 60
                
            shiftHour,direction = self.shiftMinute(cron,minutes)
            if shiftHour:
                if direction == "F":
                    shiftDay,direction=self.shiftHours(cron, hours + 1)
                elif direction == "B":
                    shiftDay,direction=self.shiftHours(cron, hours - 1)
            else:
                shiftDay,direction=self.shiftHours(cron, hours)
                
                
            if shiftDay:
                if direction == "F":
                    shiftMonth,direction = self.shiftDays(cron,1)
                elif direction == "B":
                    shiftMonth,direction = self.shiftDays(cron,-1)
                if shiftMonth:
                    if direction == "F":
                        self.shiftMonths(cron,1)
                    elif direction == "B":
                        self.shiftMonths(cron,-1)
                        
        elif shiftAmountAbs >= 1440 and shiftAmountAbs < 44640:
            #posouva se o 1 - 31(bez) dni; mesic se muze posunout o 1
            if shiftAmount < 0:
                minutes = -1*(shiftAmountAbs % 60)
                hours = -1*((shiftAmountAbs // 60) % 24)
                days = -1*(shiftAmountAbs // 1440)
            else:
                minutes = shiftAmount % 60
                hours = (shiftAmount // 60) % 24
                days = shiftAmount // 1440

            shiftHour,direction = self.shiftMinute(cron,minutes)
            if shiftHour:
                if direction == "F":
                    shiftDay, direction=self.shiftHours(cron, hours + 1)
                elif direction == "B":
                    shiftDay, direction=self.shiftHours(cron, hours - 1)
            else:
                shiftDay,direction = self.shiftHours(cron, hours)

            if shiftDay:
                if direction == "F":
                    shiftMonth,direction = self.shiftDays(cron, days + 1)
                elif direction == "B":
                    shiftMonth,direction = self.shiftDays(cron, days - 1)
            else:
                shiftMonth,direction = self.shiftDays(cron, days)

            if shiftMonth:
                if direction == "F":
                    self.shiftMonths(cron,1)
                elif direction == "B":
                    self.shiftMonths(cron,-1)
        elif shiftAmountAbs >= 44640:
            #posouva se o 1 az 12 mesicu
            if shiftAmount < 0:
                minutes = -1*(shiftAmountAbs % 60)
                hours = -1*((shiftAmountAbs // 60) % 24)
                days = -1*((shiftAmountAbs // 1440) % 31)
                months = -1*(shiftAmountAbs // 44640)
            else:
                minutes = shiftAmount % 60
                hours = (shiftAmount // 60) % 24
                days = (shiftAmount // 1440) % 31
                months = shiftAmount // 44640
            shiftHour,direction = self.shiftMinute(cron,minutes)
            if shiftHour:
                if direction == "F":
                    shiftDay,direction=self.shiftHours(cron, hours + 1)
                elif direction == "B":
                    shiftDay,direction=self.shiftHours(cron, hours - 1)
            else:
                shiftDay,direction = self.shiftHours(cron, hours)

            if shiftDay:
                if direction == "F":
                    shiftMonth,direction = self.shiftDays(cron, days + 1)
                elif direction == "B":
                    shiftMonth,direction = self.shiftDays(cron, days - 1)
            else:
                shiftMonth,direction = self.shiftDays(cron, days)

            if shiftMonth:
                if direction == "F":
                    self.shiftMonths(cron,months + 1)
                elif direction == "B":
                    self.shiftMonths(cron,months - 1)
            else:
                self.shiftMonths(cron, months)
            
    def shiftMinute(self,cron,shiftAmount):
        shiftHour=False
        direction=""
        newMinuteSet=[]
        for minute in cron.minuteSet:
            newMinute = minute + shiftAmount
            if newMinute > 59:
                shiftHour=True
                direction="F"
            if newMinute < 0:
                shiftHour=True
                direction="B"
            newMinuteSet.append(newMinute%60)
        cron.minuteSet = sorted(newMinuteSet)
        return shiftHour,direction
            
    def shiftHours(self,cron,shiftAmount):
        shiftDay=False
        direction=""
        newHourSet=[]
        for hour in cron.hourSet:
            newHour = hour + shiftAmount
            if newHour > 23:
                shiftDay=True
                direction="F"
            if newHour < 0:
                shiftDay=True
                direction="B"
            newHourSet.append(newHour%24)
        cron.hourSet=sorted(newHourSet)
        return shiftDay,direction
        
    def shiftDays(self,cron,shiftAmount):
        newDaySet=[]
        newDayOfWeekSet=[]
        direction=""
        shiftMonth=False
        #na miste dnu v tydnu je "*" => nekoukam na ne
        if (cron.allDays and cron.allDaysOfWeek) or (not cron.allDays and cron.allDaysOfWeek): 
            for day in cron.daySet:
                newDay = day + shiftAmount
                if newDay > 31:
                    shiftMonth = True
                    direction="F"
                if newDay < 1:
                    shiftMonth = True
                    direction="B"
                newDay = self.checkDayRange(newDay)
                newDaySet.append(newDay)
            #ulozim nove dny
            cron.daySet=sorted(newDaySet)
                
        #na miste dny v tydnu je neco konkretniho a dny jsou vsechny "*", posunu dny v tydnu
        elif cron.allDays and not cron.allDaysOfWeek:
            for dayOfWeek in cron.dayOfWeekSet:
                newDayOfWeek = dayOfWeek + shiftAmount
                newDayOfWeek = self.checkDayOfWeekRange(newDayOfWeek)
                newDayOfWeekSet.append(newDayOfWeek)
            #ulozim nove dny v tydnu
            cron.dayOfWeekSet=sorted(newDayOfWeekSet)
        
        #dny i dny v tydnu jsou konkretni, posunu oba
        elif not cron.allDays and not cron.allDaysOfWeek:
            
            #posunu dny v tydnu
            for dayOfWeek in cron.dayOfWeekSet:
                newDayOfWeek = dayOfWeek + shiftAmount
                newDayOfWeek = self.checkDayOfWeekRange(newDayOfWeek)
                newDayOfWeekSet.append(newDayOfWeek)
            #ulozim nove dny v tydnu
            cron.dayOfWeekSet=sorted(newDayOfWeekSet)
            
            #posunu dny
            for day in cron.daySet:
                newDay = day + shiftAmount
                if newDay > 31:
                    shiftMonth = True
                    direction="F"
                if newDay < 1:
                    shiftMonth = True
                    direction="B"
                newDay = self.checkDayRange(newDay)
                newDaySet.append(newDay)
            #ulozim nove dny
            cron.daySet=sorted(newDaySet)
        
        return shiftMonth,direction
        
    def shiftMonths(self,cron,shiftAmount):
        newMonthSet=[]
        for month in cron.monthSet:
            newMonth = month + shiftAmount
            newMonth = self.checkMonthRange(newMonth)
            newMonthSet.append(newMonth)
        cron.monthSet=sorted(newMonthSet)
        
    def checkDayOfWeekRange(self,dayOfWeek):
        if dayOfWeek < 0:
            while dayOfWeek < 0:
                dayOfWeek+=7
            return dayOfWeek
        elif dayOfWeek > 6:
            return dayOfWeek%7
        else:
            return dayOfWeek
        
    def checkDayRange(self,day):
        if day > 31:
            return (day%32)+1
        elif day < 1:
            while day < 1:
                day+=31
            return day
        else:
            return day
        
    def checkMonthRange(self,month):
        if month > 12:
            return (month%13)+1
        elif month < 1:
            while month < 1:
                month+=12
            return month
        else:
            return month
    

    def createCrontab(self):
        cronID=0
        for i in range(0,len(self.cronList)):
            cron = self.cronList[i]
            #vyplni seznamy s minutami, hodinami, ...
            self.createLists(cron)
            
            shiftAmount=self.shiftVector[cronID]
            
            #posune
            self.shiftCron(cron, shiftAmount)
            cronID+=1
            
            #opravi mnozin (stahne napr. 1,2,3,4,5 do intervalu 1-5, atd)
            cron.repairNewSets()
            
            #vytvori nove crontab polozky pro minutu, hodiny, ...
            cron.createNewSets()
            #cron.printNewSets()
            cron.createInfo()
            #cron.printInfo()
        for crontab,_ in self.crontabs:
            first=True
            self.newCrontab=self.newCrontab+"#NEW CRONTAB: "+crontab+"\n"
            for cron in self.cronList:
                if crontab == cron.fromCrontab:
                    self.newCrontab=self.newCrontab+(cron.newSets+cron.info+"\n")
                    
            if len(self.emptyCronList) > 0:
                for cron in self.emptyCronList:
                    if crontab == cron.fromCrontab:
                        if first:
                            self.newCrontab = self.newCrontab+"#Following cron jobs wasn't optimized \n"
                            first=False
                        self.newCrontab=self.newCrontab+cron.cronToStr()+"\n"
            self.newCrontab=self.newCrontab+"\n"
        return self.newCrontab
    
    def printCrontab(self):
        print("*** OUTPUT CRONTAB ***")
        print(self.newCrontab)