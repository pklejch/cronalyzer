import os
import glob 
import re
from Cron import CCron
from CronLogger import CCronLogger

class CCronParser:
    def __init__(self,options):
        
        self.setOptions(options)
        
        self._crontabFolders=[]
        
        #pridat slozky s crontaby do seznamu
        
        #obecna slozka s crontaby
        if self.includeCrondFolder:
            self._crontabFolders.append(["/etc/cron.d/",False])
        
        
        #uzivatelske slozky s crontaby
        if os.geteuid() == 0:
            for usercrontabdir in self.userCrontabDirs.split(":"):
                self._crontabFolders.append([usercrontabdir,True])
        else:
            CCronLogger.info("You have to run this tool as root to access user crontabs.")
            CCronLogger.infoToConsole("You have to run this tool as root to access user crontabs.")
            
        
        #ostatni slozky s crontaby, ktere nejsou uzivatelske
        for othercrontabdir in self.otherCrontabDirs.split(":"):
            if othercrontabdir!="":
                self._crontabFolders.append([othercrontabdir,False])
            
        
        #muj testovaci crontab
        #self._crontabFolders.append(["/home/petr/git/cronalyzer/data/crontabs/",True])
        
        
        self._crontabs=[]
        for crontabFolder,isUser in self._crontabFolders:
            for crontab in glob.glob(os.path.join(crontabFolder,"*")):
                if not crontab.endswith("~") and os.path.isfile(crontab):
                    self._crontabs.append([crontab,isUser])
                    CCronLogger.info("Added crontab: "+crontab+" to analysis.")
                    CCronLogger.infoToConsole("Added crontab: "+crontab+" to analysis.")
                
        # + /etc/crontab
        if self.includeMainCrontab:
            self._crontabs.append(["/etc/crontab",False])
            CCronLogger.info("Added crontab: /etc/crontab to analysis.")
            CCronLogger.infoToConsole("Added crontab: /etc/crontab to analysis.")
        
        
        #list s rozparsovanymi crony
        self._crons=[]
        
    def setOptions(self,options):

        try:
            self.defaultLength=int(options["defaultduration"])
            if self.defaultLength < 1:
                CCronLogger.error("Invalid default duration. Setting to default: 1.")
                self.defaultLength=1
            CCronLogger.debug("Default weight: "+str(self.defaultLength)+".")
        except ValueError:
            CCronLogger.error("Invalid default duration. Setting to default: 1.")
            self.defaultLength=1
        except KeyError:
            CCronLogger.info("Default duration directive not found. Setting to default: 1.")
            self.defaultLength=1    
        
        try:
            self.defaultWeight=int(options["defaultweight"])
            if self.defaultWeight < 1:
                CCronLogger.error("Invalid default weight. Setting to default: 5.")
                self.defaultWeight=5
            CCronLogger.debug("Default weight: "+str(self.defaultWeight)+".")
        except ValueError:
            CCronLogger.error("Invalid default weight. Setting to default: 5.")
            self.defaultWeight=5
        except KeyError:
            CCronLogger.info("Default weight directive not found. Setting to default: 5.")
            self.defaultWeight=5
            
        try:
            self.defaultMaxShift=int(options["defaultmaxshift"])
            CCronLogger.debug("Default MinShift: "+str(self.defaultMaxShift)+".")
        except ValueError:
            CCronLogger.error("Invalid default MaxShift. Setting to default: 0.")
            self.defaultMaxShift=0
        except KeyError:
            CCronLogger.info("Default MaxShift directive not found. Setting to default: 0.")
            self.defaultMaxShift=0      
            
        try:
            self.defaultMinShift=int(options["defaultminshift"])
            CCronLogger.debug("Default MinShift: "+str(self.defaultMinShift)+".")
        except ValueError:
            CCronLogger.error("Invalid default MinShift. Setting to default: 0.")
            self.defaultMinShift=0
        except KeyError:
            CCronLogger.info("Default MinShift directive not found. Setting to default: 0.")
            self.defaultMinShift=0
        
        if self.defaultMinShift > self.defaultMaxShift:
            CCronLogger.error("Invalid default MinShift and MaxShift. Setting both 0.")
            self.defaultMaxShift=0
            self.defaultMinShift=0
        
        try: 
            self.userCrontabDirs=options["usercrontabdirs"]
            CCronLogger.debug("User crontab directories: "+str(self.userCrontabDirs))
        except KeyError:
            CCronLogger.info("User crontab directories directive not found.")
            self.userCrontabDirs=""
            
        try: 
            self.otherCrontabDirs=options["othercrontabdirs"]
            CCronLogger.debug("Other crontab directories: "+str(self.otherCrontabDirs))
        except KeyError:
            CCronLogger.info("Other crontab directories directive not found.")
            self.otherCrontabDirs=""
            
        try: 
            self.includeRareJobs=options["includerarecronjobs"]
            CCronLogger.debug("Include rare cron jobs: "+str(self.includeRareJobs))
        except KeyError:
            CCronLogger.info("Include rare cron jobs directive not found. Setting to default: True.")
            self.includeRareJobs=True
            
        try: 
            self.includeMainCrontab=options["includemaincrontab"]
            CCronLogger.debug("Include main crontab: "+str(self.includeMainCrontab))
        except KeyError:
            CCronLogger.info("Include main crontab directive not found. Setting to default: False.")
            self.includeMainCrontab=False
            
        try: 
            self.includeCrondFolder=options["includecrondfolder"]
            CCronLogger.debug("Include /etc/cron.d/ folder: "+str(self.includeCrondFolder))
        except KeyError:
            CCronLogger.info("Include /etc/cron.d/ folder directive not found. Setting to default: False.")
            self.includeCrondFolder=False
        
    def parseCrontabs(self):
        for crontab,isUser in self._crontabs:
            try:
                with open(crontab,"r") as file:
                    content=file.readlines()
                    self._parseCrontab(content,crontab,isUser)
            except:
                CCronLogger.errorToConsole("Following crontab file couldn't be loaded: "+crontab)
                CCronLogger.error("Following crontab file couldn't be loaded: "+crontab)
                
        return self._crons
    
    def _checkMinute(self,minute):
        #je to vse
        if minute == "*":
            return True
        #je to konkretni cislo
        elif re.match('^[0-9]+$', minute):
            minute=int(minute)
            if minute >= 0 and minute <= 59:
                return True
            else:
                return False
        #je to vycet cisel
        elif re.match('^([0-9]+,)+[0-9]+$', minute):
            minutes=minute.split(",")
            for testMinute in minutes:
                testMinute=int(testMinute)
                if testMinute < 0 or testMinute > 59:
                    return False
            return True
        #je to rozsah cisel
        elif re.match('^[0-9]+-[0-9]+$', minute):
            minutes=minute.split("-")
            for testMinute in minutes:
                testMinute=int(testMinute)
                if testMinute < 0 or testMinute > 59:
                    return False
            return True
        #je to vse a modulo
        elif re.match('\*/[0-9]+', minute):
            _,testMinute=minute.split("/")
            testMinute=int(testMinute)
            if testMinute <= 0 or testMinute > 59:
                return False
            return True
        #je to rozsah a modulo
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', minute):
            minutes,mod= minute.split("/")
            
            if int(mod) <= 0 or int(mod) > 59:
                return False
            
            minutes2 = minutes.split("-")
            for testMinute in minutes2:
                testMinute=int(testMinute)
                if testMinute < 0 or testMinute > 59:
                    return False
            return True
        #je to kombinace rozsahu a listu nebo dalsich rozsahu
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',minute):
            minute=minute.replace("-",",")
            minutes=minute.split(",")
            for testMinute in minutes:
                testMinute=int(testMinute)
                if testMinute < 0 or testMinute > 59:
                    return False
            return True
        else:
            return False
        
    
    def _checkHour(self,hour):
        #je to vse
        if hour == "*":
            return True
        #je to konkretni cislo
        elif re.match('^[0-9]+$', hour):
            hour=int(hour)
            if hour >= 0 and hour <= 23:
                return True
            else:
                return False
        #je to vycet cisel
        elif re.match('^([0-9]+,)+[0-9]+$', hour):
            hours=hour.split(",")
            for testHour in hours:
                testHour=int(testHour)
                if testHour < 0 or testHour > 23:
                    return False
            return True
        #je to rozsah cisel
        elif re.match('^[0-9]+-[0-9]+$', hour):
            hours=hour.split("-")
            for testHour in hours:
                testHour=int(testHour)
                if testHour < 0 or testHour > 23:
                    return False
            return True
        #je to vse a modulo
        elif re.match('\*/[0-9]+', hour):
            _,testHour=hour.split("/")
            testHour=int(testHour)
            if testHour <= 0 or testHour > 23:
                return False
            return True
        #je to rozsah a modulo
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', hour):
            hours,mod= hour.split("/")
            
            if int(mod) <= 0 or int(mod) > 23:
                return False
            
            hours2 = hours.split("-")
            for testHour in hours2:
                testHour=int(testHour)
                if testHour < 0 or testHour > 23:
                    return False
            return True
        #je to kombinace rozsahu a listu nebo dalsich rozsahu
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',hour):
            hour=hour.replace("-",",")
            hours=hour.split(",")
            for testHour in hours:
                testHour=int(testHour)
                if testHour < 0 or testHour > 23:
                    return False
            return True
        else:
            return False
    
    def _checkDay(self,day):
        #je to vse
        if day == "*":
            return True
        #je to konkretni cislo
        elif re.match('^[0-9]+$', day):
            day=int(day)
            if day >= 1 and day <= 31:
                return True
            else:
                return False
        #je to vycet cisel
        elif re.match('^([0-9]+,)+[0-9]+$', day):
            days=day.split(",")
            for testDay in days:
                testDay=int(testDay)
                if testDay < 1 or testDay > 31:
                    return False
            return True
        #je to rozsah cisel
        elif re.match('^[0-9]+-[0-9]+$', day):
            days=day.split("-")
            for testDay in days:
                testDay=int(testDay)
                if testDay < 1 or testDay > 31:
                    return False
            return True
        #je to vse a modulo
        elif re.match('\*/[0-9]+', day):
            _,testDay=day.split("/")
            testDay=int(testDay)
            if testDay <= 1 or testDay > 31:
                return False
            return True
        #je to rozsah a modulo
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', day):
            days,mod= day.split("/")
            
            if int(mod) <= 1 or int(mod) > 31:
                return False
            
            days2 = days.split("-")
            for testDay in days2:
                testDay=int(testDay)
                if testDay < 1 or testDay > 31:
                    return False
            return True
        #je to kombinace rozsahu a listu nebo dalsich rozsahu
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',day):
            day=day.replace("-",",")
            days=day.split(",")
            for testDay in days:
                testDay=int(testDay)
                if testDay < 1 or testDay > 31:
                    return False
            return True
        else:
            return False
    
    def _checkMonth(self,month):
        #je to vse
        if month == "*":
            return True
        #je to konkretni cislo
        elif re.match('^[0-9]+$', month):
            month=int(month)
            if month >= 1 and month <= 12:
                return True
            else:
                return False
        #je to vycet cisel
        elif re.match('^([0-9]+,)+[0-9]+$', month):
            months=month.split(",")
            for testMonth in months:
                testMonth=int(testMonth)
                if testMonth < 1 or testMonth > 12:
                    return False
            return True
        #je to rozsah cisel
        elif re.match('^[0-9]+-[0-9]+$', month):
            month=month.split("-")
            for testMonth in months:
                testMonth=int(testMonth)
                if testMonth < 1 or testMonth > 12:
                    return False
            return True
        #je to vse a modulo
        elif re.match('\*/[0-9]+', month):
            _,testMonth=month.split("/")
            testMonth=int(testMonth)
            if testMonth <= 1 or testMonth > 12:
                return False
            return True
        #je to rozsah a modulo
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', month):
            months,mod= month.split("/")
            
            if int(mod) <= 1 or int(mod) > 12:
                return False
            
            months2 = months.split("-")
            for testMonth in months2:
                testMonth=int(testMonth)
                if testMonth < 1 or testMonth > 12:
                    return False
            return True
        #je to kombinace rozsahu a listu nebo dalsich rozsahu
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',month):
            month=month.replace("-",",")
            months=month.split(",")
            for testMonth in months:
                testMonth=int(testMonth)
                if testMonth < 1 or testMonth > 12:
                    return False
            return True
        else:
            return False
    
    def _checkDayOfWeek(self,dayOfWeek):
        #je to vse
        if dayOfWeek == "*":
            return True
        #je to konkretni cislo
        elif re.match('^[0-9]+$', dayOfWeek):
            dayOfWeek=int(dayOfWeek)
            if dayOfWeek >= 0 and dayOfWeek <= 7:
                return True
            else:
                return False
        #je to vycet cisel
        elif re.match('^([0-9]+,)+[0-9]+$', dayOfWeek):
            dayOfWeeks=dayOfWeek.split(",")
            for testdayOfWeek in dayOfWeeks:
                testdayOfWeek=int(testdayOfWeek)
                if testdayOfWeek < 0 or testdayOfWeek > 7:
                    return False
            return True
        #je to rozsah cisel
        elif re.match('^[0-9]+-[0-9]+$', dayOfWeek):
            dayOfWeeks=dayOfWeek.split("-")
            for testdayOfWeek in dayOfWeeks:
                testdayOfWeek=int(testdayOfWeek)
                if testdayOfWeek < 0 or testdayOfWeek > 7:
                    return False
            return True
        #je to vse a modulo
        elif re.match('\*/[0-9]+', dayOfWeek):
            _,testdayOfWeek=dayOfWeek.split("/")
            testdayOfWeek=int(testdayOfWeek)
            if testdayOfWeek <= 0 or testdayOfWeek > 7:
                return False
            return True
        #je to rozsah a modulo
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', dayOfWeek):
            dayOfWeeks,mod= dayOfWeek.split("/")
            
            if int(mod) <= 0 or int(mod) > 7:
                return False
            
            dayOfWeeks2 = dayOfWeeks.split("-")
            for testdayOfWeek in dayOfWeeks2:
                testdayOfWeek=int(testdayOfWeek)
                if testdayOfWeek < 0 or testdayOfWeek > 7:
                    return False
            return True
        #je to kombinace rozsahu a listu nebo dalsich rozsahu
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',dayOfWeek):
            dayOfWeek=dayOfWeek.replace("-",",")
            dayOfWeeks=dayOfWeek.split(",")
            for testdayOfWeek in dayOfWeeks:
                testdayOfWeek=int(testdayOfWeek)
                if testdayOfWeek < 0 or testdayOfWeek > 7:
                    return False
            return True
        else:
            return False
    
    def getCrontabs(self):
        return self._crontabs
    
    def _getMetadata(self,comment,metadata,lineNr,sourceCrontab):
        data=None
        for i in range(0,len(comment)):
            meta=comment[i]
            if meta.startswith(metadata+"="):
                _,value=meta.split("=")
                if value!="":
                    return value
                    
        try:
            idx=comment.index(metadata)
            if comment[idx+1]!="=":
                data=comment[idx+1]
                data=data.replace("=","")
            else:
                data=comment[idx+2]
        except ValueError:
            try:
                idx=comment.index(metadata+"=")
                data=comment[idx+1]
            except ValueError:
                CCronLogger.info(metadata.title()+" metadata not found in line "+str(lineNr)+" in "+sourceCrontab+".")
                CCronLogger.info("It will be replaced by default value.")
        return data
    
    def checkShifts(self, leftShift, rightShift, line):
        try:
            dummy=int(leftShift)
            dummy2=int(rightShift)
            
            if dummy > dummy2:
                raise ValueError
        except ValueError:
            CCronLogger.error("Invalid shift values in "+line)
            CCronLogger.error("Setting to default: 0:0")
            leftShift="0"
            rightShift="0"
        return leftShift, rightShift

    def checkLength(self,length, line):
        try:
            dummy=int(length)
            if dummy < 1:
                raise ValueError
        except ValueError:
            CCronLogger.error("Invalid duration value in "+line)
            CCronLogger.error("Setting to default: 1")
            length="1"
        return length
    
    def checkWeight(self,weight, line):
        try:
            dummy=int(weight)
            if dummy < 1:
                raise ValueError
        except ValueError:
            CCronLogger.error("Invalid weight value in "+line)
            CCronLogger.error("Setting to default: 1")
            weight="1"
        return weight
                
    def _parseCrontab(self, content, sourceCrontab, isUser):
        CCronLogger.infoToConsole("Parsing crontabs...")
        CCronLogger.info("Parsing crontabs...")
        lineNr=0
        for line in content:
            
            #odstraneni bilych znaku z konce radky
            line=line.rstrip()
            
            #pokud je to radek zacinajici # = komentar nebo prazdna radka, tak ji preskoc
            if re.match("^[ \t]*#",line) or line=="":
                continue
            
            #REGEX na radku s cron ulohou
            #cronEntry=re.match("^[ \t]*([^\s]+)[ \t]*([^\s]+)[ \t]*([^\s]+)[ \t]*([^\s]+)[ \t]*([^\s]+)[ \t]*([^#\n]*)[ \t]*#?[ \t]*([^\n]*)$", line)
            cronEntry=line.split()
            
            #neni to crontab zaznam, pravdepodovne nastaveni promenne prostredi
            
            if (isUser and len(cronEntry) < 6) or (not isUser and len(cronEntry) < 7):
                continue
            
            #minute=cronEntry.group(1)
            #hour=cronEntry.group(2)
            #day=cronEntry.group(3)
            #month=cronEntry.group(4)
            #dayOfWeek=cronEntry.group(5)
            #command=cronEntry.group(6)
            #comment=cronEntry.group(7)
            
            minute=cronEntry[0]
            hour=cronEntry[1]
            day=cronEntry[2]
            month=cronEntry[3]
            dayOfWeek=cronEntry[4]
            
            if not self._checkMinute(minute) or not self._checkHour(hour) or not self._checkDay(day) or not self._checkMonth(month) or not self._checkDayOfWeek(dayOfWeek):
                msg="Error while parsing crontab entry in file: "+sourceCrontab
                CCronLogger.errorToConsole(msg)
                CCronLogger.error(msg)
                continue
            
            if isUser:
                commandAndComment=cronEntry[5:]
                user=""
            else:
                user=cronEntry[5]
                commandAndComment=cronEntry[6:]
            comment=[]
            command=[]
            
            commentStarted=False
            jednoducheUv=0
            dvojiteUv=0
            for word in commandAndComment:
                jednoducheUv+=word.count("'")
                dvojiteUv+=word.count('"')
                if re.search("#",word) and not dvojiteUv%2 and not jednoducheUv%2:
                    commentStarted=True
                if commentStarted:
                    word=word.replace("#","")
                    words=word.split(",")
                    for word in words:
                        if word != "":
                            comment.append(word)
                else:
                    command.append(word)
            
            #check na neukoncene uvozovky
            if jednoducheUv%2 or dvojiteUv%2:
                msg="Unfinished quotation marks, skipping cron entry"
                CCronLogger.errorToConsole(msg)
                CCronLogger.error(msg)
                continue
            
            
            command=" ".join(command)
            
            
            length=self._getMetadata(comment, "duration", lineNr, sourceCrontab)
            weight=self._getMetadata(comment, "weight", lineNr, sourceCrontab)
            shift=self._getMetadata(comment, "shift", lineNr, sourceCrontab)
            
            if length is None:
                length=self.defaultLength
            
            if weight is None:
                weight=self.defaultWeight
                
            if shift is None:
                shift=str(self.defaultMinShift)+":"+str(self.defaultMaxShift)
            

            
            if shift is not None:
                shifts=shift.split(":")
                if len(shifts)<2:
                    leftShift="-"+shift
                    rightShift=shift
                else:
                    leftShift=shifts[0]
                    rightShift=shifts[1]

                            
            leftShift, rightShift = self.checkShifts(leftShift,rightShift,line)
            weight = self.checkWeight(weight,line)
            length = self.checkLength(length, line)
                               
            try:
                cron=CCron(minute, hour, day, month, dayOfWeek, user, command, int(length), int(weight), int(leftShift), int(rightShift), sourceCrontab, self.includeRareJobs)
                self._crons.append(cron)
            except ValueError:
                errMsg="Error occured while predicting following cronjob: \n"
                errMsg=errMsg+minute+" "+hour+" "+day+" "+month+" "+dayOfWeek+" "+user+" "+command+"\n"
                errMsg=errMsg+"from crontab: "+sourceCrontab+"\n"
                errMsg=errMsg+"maybe job is badly configured or check \"include rare cron job\" directive"
                CCronLogger.errorToConsole(errMsg)
                CCronLogger.error(errMsg)
            lineNr+=1