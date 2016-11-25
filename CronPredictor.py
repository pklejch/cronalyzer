import datetime
import re
import calendar
from itertools import tee
from CronJob import CCronJob
from datetime import timedelta

class CCronPredictor:
    """ predicts runs of cron"""
    def __init__(self,minute,hour,day,month,dayOfWeek,length,command, includeRareJobs=False):     
        self.minute=minute
        self.hour=hour
        self.day=day
        self.month=month
        self.dayOfWeek=dayOfWeek
        self.length=length
        self.command=command
        
        self.constantSpaces=True
        self.spaceBetweenRuns=None
        
        self.rareJob=False
        
        #jsou v polozce dnu vsechny dny (*) ?
        if(self.day=="*"):
            self._allDays=True
        else:
            self._allDays=False
            
        #jsou v polozce dnu v tydnu vsechny dny v tydnu (*) ?    
        if(self.dayOfWeek=="*"):
            self._allDaysOfWeek=True
        else:
            self._allDaysOfWeek=False
            
            
        #jsou v polozce dny nasobky ? (*/2)
        if re.match('\*/[0-9]+', self.day):
            self._multipleDays=True
        else:
            self._multipleDays=False
        
        #vytvori aktualni cas
        self.nextTime=datetime.datetime.now()

        #nastavi sekundy a microsekundy na 0
        self.nextTime=self.nextTime.replace(second=0,microsecond=0)
        
        #vytvorim si startovni cas, pro vypocet prvni iterace
        self.startTime=self.nextTime
        
        #vyresetuju pristi cas na minimum (1. ledna 00:00)
        self.nextTime=self.nextTime.replace(minute=0,hour=0,day=1,month=1)
        
        #inicializace
        self._makeSets(self.minute, self.hour, self.day, self.month, self.dayOfWeek)
        self._isRare(includeRareJobs)
        self._makeGens()    
        self._setFirstTime()
        
        
    def _isRare(self, includeRareJobs):
        if len(self.monthSet) < 6 and includeRareJobs:
            self.monthSet=list(range(1,13))

    def _makeMinuteSet(self,minute):
        """ creates iterable sets filled with minutes """
        #v mnozine budou vsechny minuty [0,1,2,...,59]
        if minute=="*":
            minuteSet=list(range(0,60))
        #v mnozine bude jedno konkretni cislo [5]
        elif re.match('^[0-9]+$', minute):
            minuteSet=[int(minute)]
        #v mnozine bude seznam cisel [0,1,15,25]
        elif re.match('^([0-9]+,)+[0-9]+$', minute):
            minuteSet=sorted(list(set(map(int,minute.split(',')))))
        #v mnozine bude rozsah cisel [10,11,12,13,14,15]
        elif re.match('^[0-9]+-[0-9]+$', minute):
            fromTo=list(map(int,minute.split('-')))
            minuteSet=list(range(fromTo[0],fromTo[1]+1))
        #v mnozine budou cisla odpovidajici napr. "kazdych 5" = [0,5,10,...,55]
        elif re.match('\*/[0-9]+', minute):
            #inicializuju prazdny list
            minuteSet=[]
            #rozsekam zapis */5 na casti
            line=minute.split('/')
            #vyberu jen cast s cislem (jak casto, se to bude dit) 
            howOften=int(line[1])
            #vytvorim si list s minutami od 0 do 59
            allMinutes=list(range(0,60))
            #projedu vsechny minuty a minuty, ktere splnuji kriteria pridam do vysledne mnoziny minut 
            for i in allMinutes:
                if i%howOften == 0:
                    minuteSet.append(i)
        #rozsah a modulo, napr: 0-20/5
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', minute):
            minuteSet=[]
            line=minute.split("/")
            howOften=int(line[1])
            fromTo=list(map(int,line[0].split('-')))
            allMinutes=list(range(fromTo[0],fromTo[1]+1))
            for i in allMinutes:
                if i%howOften == 0:
                    minuteSet.append(i)
                    
        #kombinace rozsahu: 10-15,20-15 nebo kombinace rozsahu a vyctu: 1,10-15,17,19
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',minute):
            minuteSet=set()
            line=minute.split(",")
            for part in line:
                if re.match('^[0-9]+-[0-9]+$', part):
                    fromTo=list(map(int,part.split('-')))
                    subRange=list(range(fromTo[0],fromTo[1]+1))
                    for i in subRange:
                        minuteSet.add(i)
                else:
                    minuteSet.add(int(part))
            minuteSet=sorted(list(minuteSet))
            
        return minuteSet      
    
    def _makeDayOfWeekSet(self,dayOfWeek):
        #v mnozine budou vsechny dny v tydnu [0,...,6]
        if dayOfWeek=="*":
            dayOfWeekSet=list(range(0,7))
        #v mnozine bude jedno konkretni cislo [5]
        elif re.match('^[0-7]$', dayOfWeek):
            dayOfWeekSet=[int(dayOfWeek)]
        #v mnozine bude seznam cisel [0,1,4,6]
        elif re.match('^([0-7],)+[0-7]$', dayOfWeek):
            dayOfWeekSet=sorted(list(set(map(int,dayOfWeek.split(',')))))
        #v mnozine bude rozsah dnu v tydnu [0,1,2]
        elif re.match('^[0-7]-[0-7]$', dayOfWeek):
            fromTo=list(map(int,dayOfWeek.split('-')))
            dayOfWeekSet=list(range(fromTo[0],fromTo[1]+1))
        #v mnozine budou cisla odpovidajici napr. "kazdych 5" = [0,5,10,...,55]
        elif re.match('\*/[0-9]+', dayOfWeek):
            #inicializuju prazdny list
            dayOfWeekSet=[]
            #rozsekam zapis */5 na casti
            line=dayOfWeek.split('/')
            #vyberu jen cast s cislem (jak casto, se to bude dit) 
            howOften=int(line[1])
            #vytvorim si list s dny v tydnu od 0 do 6
            allDaysOfWeek=list(range(0,7))
            #projedu vsechny dny v tydnu a dny v tydnu, ktere splnuji kriteria pridam do vysledne mnoziny dnu v tydnu 
            for i in allDaysOfWeek:
                if i%howOften == 0:
                    dayOfWeekSet.append(i)
        #rozsah a modulo, napr: 0-6/2
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', dayOfWeek):
            dayOfWeekSet=[]
            line=dayOfWeek.split("/")
            howOften=int(line[1])
            fromTo=list(map(int,line[0].split('-')))
            allMinutes=list(range(fromTo[0],fromTo[1]+1))
            for i in allMinutes:
                if i%howOften == 0:
                    dayOfWeekSet.append(i)
                    
        #kombinace rozsahu: 10-15,20-15 nebo kombinace rozsahu a vyctu: 1,10-15,17,19
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',dayOfWeek):
            dayOfWeekSet=set()
            line=dayOfWeek.split(",")
            for part in line:
                if re.match('^[0-9]+-[0-9]+$', part):
                    fromTo=list(map(int,part.split('-')))
                    subRange=list(range(fromTo[0],fromTo[1]+1))
                    for i in subRange:
                        dayOfWeekSet.add(i)
                else:
                    dayOfWeekSet.add(int(part))
            dayOfWeekSet=sorted(list(dayOfWeekSet))
                    
        return dayOfWeekSet  

    def _makeHourSet(self,hour):
        #v mnozine budou vsechny hodiny [0,1,2,...,23]
        if hour=="*":
            hourSet=list(range(0,24))
        #v mnozine bude jedno konkretni cislo [5]
        elif re.match('^[0-9]+$', hour):
            hourSet=[int(hour)]
        #v mnozine bude seznam cisel [0,1,15,22]
        elif re.match('^([0-9]+,)+[0-9]+$', hour):
            hourSet=sorted(list(set(map(int,hour.split(',')))))
        #v mnozine bude rozsah cisel [10,11,12,13,14,15]
        elif re.match('^[0-9]+-[0-9]+$', hour):
            fromTo=list(map(int,hour.split('-')))
            hourSet=list(range(fromTo[0],fromTo[1]+1))
        #v mnozine budou cisla odpovidajici napr. "kazdych 5" = [0,5,10,...,55]
        elif re.match('\*/[0-9]+', hour):
            #inicializuju prazdny list
            hourSet=[]
            #rozsekam zapis */5 na casti
            line=hour.split('/')
            #vyberu jen cast s cislem (jak casto, se to bude dit) 
            howOften=int(line[1])
            #vytvorim si list s hodinami od 0 do 23
            allHours=list(range(0,24))
            #projedu vsechny hodiny a hodiny, ktere splnuji kriteria pridam do vysledne mnoziny hodin 
            for i in allHours:
                if i%howOften == 0:
                    hourSet.append(i)
        #rozsah a modulo, napr: 0-20/5
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', hour):
            hourSet=[]
            line=hour.split("/")
            howOften=int(line[1])
            fromTo=list(map(int,line[0].split('-')))
            allMinutes=list(range(fromTo[0],fromTo[1]+1))
            for i in allMinutes:
                if i%howOften == 0:
                    hourSet.append(i)
                    
        #kombinace rozsahu: 10-15,20-15 nebo kombinace rozsahu a vyctu: 1,10-15,17,19
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',hour):
            hourSet=set()
            line=hour.split(",")
            for part in line:
                if re.match('^[0-9]+-[0-9]+$', part):
                    fromTo=list(map(int,part.split('-')))
                    subRange=list(range(fromTo[0],fromTo[1]+1))
                    for i in subRange:
                        hourSet.add(i)
                else:
                    hourSet.add(int(part))
            hourSet=sorted(list(hourSet))
                    
        return hourSet

    def _makeDaySet(self,day):        
        #v mnozine budou vsechny dny [1,2,...,31] nebo [1,...,28], atd...
        if day=="*":
            daySet=[]
        #v mnozine bude jedno konkretni cislo [5]
        elif re.match('^[0-9]+$', day):
            daySet=[int(day)]
        #v mnozine bude seznam cisel [0,1,15,25]
        elif re.match('^([0-9]+,)+[0-9]+$', day):
            daySet=sorted(list(set(map(int,day.split(',')))))
        #v mnozine bude rozsah cisel [10,11,12,13,14,15]
        elif re.match('^[0-9]+-[0-9]+$', day):
            fromTo=list(map(int,day.split('-')))
            daySet=list(range(fromTo[0],fromTo[1]+1))
        #v mnozine budou cisla odpovidajici napr. "kazdych 5" = [0,5,10,...,55]
        #dodela se pozdeji v zavislosti na danem mesici
        elif re.match('\*/[0-9]+', day):
            daySet=[]
        #rozsah a modulo, napr: 0-20/5
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', day):
            daySet=[]
            line=day.split("/")
            howOften=int(line[1])
            fromTo=list(map(int,line[0].split('-')))
            allMinutes=list(range(fromTo[0],fromTo[1]+1))
            for i in allMinutes:
                if i%howOften == 1:
                    daySet.append(i)
                    
        #kombinace rozsahu: 10-15,20-15 nebo kombinace rozsahu a vyctu: 1,10-15,17,19
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',day):
            daySet=set()
            line=day.split(",")
            for part in line:
                if re.match('^[0-9]+-[0-9]+$', part):
                    fromTo=list(map(int,part.split('-')))
                    subRange=list(range(fromTo[0],fromTo[1]+1))
                    for i in subRange:
                        daySet.add(i)
                else:
                    daySet.add(int(part))
            daySet=sorted(list(daySet))
                    
        return daySet

    def _makeDaySetAfter(self,day):
        #inicializuju prazdny list
        daySet=[]
        #rozsekam zapis */5 na casti
        line=day.split('/')
        #vyberu jen cast s cislem (jak casto, se to bude dit) 
        howOften=int(line[1])
        #vytvorim si list s dny, podle aktualniho mesice a roku
        self._adjustDaySetByMonth()
        allDays=self.daySet
        #projedu vsechny dny a dny, ktere splnuji kriteria pridam do vysledne mnoziny dnu 
        for i in allDays:
            if i%howOften == 1:
                daySet.append(i)
        return daySet

    def _makeMonthSet(self,month):
        #v mnozine budou vsechny mesice [1,2,...,12]
        if month=="*":
            monthSet=list(range(1,13))
        #v mnozine bude jedno konkretni cislo [5]
        elif re.match('^[0-9]+$', month):
            monthSet=[int(month)]
        #v mnozine bude seznam cisel [0,1,15,25]
        elif re.match('^([0-9]+,)+[0-9]+$', month):
            monthSet=sorted(list(set(map(int,month.split(',')))))
        #v mnozine bude rozsah cisel [10,11,12,13,14,15]
        elif re.match('^[0-9]+-[0-9]+$', month):
            fromTo=list(map(int,month.split('-')))
            monthSet=list(range(fromTo[0],fromTo[1]+1))
        #v mnozine budou cisla odpovidajici napr. "kazdych 5" = [0,5,10,...,55]
        elif re.match('\*/[0-9]+', month):
            #inicializuju prazdny list
            monthSet=[]
            #rozsekam zapis */5 na casti
            line=month.split('/')
            #vyberu jen cast s cislem (jak casto, se to bude dit) 
            howOften=int(line[1])
            #vytvorim si list s mesici od 1 do 12
            allMonths=list(range(1,13))
            #projedu vsechny mesice a mesice, ktere splnuji kriteria pridam do vysledne mnoziny mesicu 
            for i in allMonths:
                if i%howOften == 1:
                    monthSet.append(i)
        #rozsah a modulo, napr: 0-20/5
        elif re.match('^[0-9]+-[0-9]+/[0-9]+$', month):
            monthSet=[]
            line=month.split("/")
            howOften=int(line[1])
            fromTo=list(map(int,line[0].split('-')))
            allMinutes=list(range(fromTo[0],fromTo[1]+1))
            for i in allMinutes:
                if i%howOften == 1:
                    monthSet.append(i)
                    
        #kombinace rozsahu: 10-15,20-15 nebo kombinace rozsahu a vyctu: 1,10-15,17,19
        elif re.match('^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$',month):
            monthSet=set()
            line=month.split(",")
            for part in line:
                if re.match('^[0-9]+-[0-9]+$', part):
                    fromTo=list(map(int,part.split('-')))
                    subRange=list(range(fromTo[0],fromTo[1]+1))
                    for i in subRange:
                        monthSet.add(i)
                else:
                    monthSet.add(int(part))
            monthSet=sorted(list(monthSet))
        return monthSet
    
    def _adjustDaySet(self,month,year):
        if(month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12):
            #mesic ma 31 dni
            daySet=list(range(1,32))
        elif (month == 4 or month == 6 or month == 9 or month == 11):
            #mesic ma 30 dni
            daySet=list(range(1,31))
        else:
            #je to unor a prestupny rok = 29 dni
            if (calendar.isleap(year)):
                daySet=list(range(1,30))
            #je to unor a neprestupny rok = 28 dni            
            else:
                daySet=list(range(1,29))
        return daySet
    
    def _generateMinutes(self,minuteSet):
        for i in minuteSet:
            yield i
            
    def _generateDayOfWeek(self,dayOfWeekSet):
        for i in dayOfWeekSet:
            yield i
            
    def _generateHours(self,hourSet):
        for i in hourSet:
            yield i
    
    def _generateDays(self,daySet):
        for i in daySet:
            yield i
            
    def _generateMonths(self, monthSet):
        for i in monthSet:
            yield i
    
    def _nextMinute(self):
        self.nextTime=self.nextTime.replace(minute=next(self.minutes))
        
    def _nextHour(self):
        self.nextTime=self.nextTime.replace(hour=next(self.hours))
        
    def _adjustDaySetByMonth(self, save=True):
        #zkopiruju si generator mesicu
        self.months, prevMonths = tee(self.months)
        #zkusim se podivat na dalsi mesic v mnozine
        try:
            nextYear=self.nextTime.year
            nextMonth=next(self.months)
        #mnozina dosla
        except StopIteration:
            #vyresetuju generator
            self.months=self._generateMonths(self.monthSet)
            #nactu dalsi mesic
            nextMonth=next(self.months)
            #zvysim rok
            nextYear=nextYear+1
        #vratim generator do stavu pred posunutim
        self.months=prevMonths
        #upravim mnozinu dni pro nasledujici mesic
        #bud ji ulozim do objektu nebo ji jen vratim
        if save:
            self.daySet=self._adjustDaySet(nextMonth, nextYear)
        else:
            return self._adjustDaySet(nextMonth, nextYear)
        
    def _nextDay(self):
        #den i den v tydnu jsou vsechny (*)
        if self._allDays and self._allDaysOfWeek:
            #posunu den podle vytvorene mnoziny dni
            self.nextTime=self.nextTime.replace(day=next(self.days))
        #dny jsou vsechny (*), dny v tydnu nejsou vsechny (konkretni den, vycet, rozsah)
        elif self._allDays and not self._allDaysOfWeek:
            #posunu den v tydnu podle vytvorene mnoziny dnu v tydnu
            # => posun datum o +1 den dokud nebude splnovat aktualni den v tydnu z mnoziny                
            found=False
            while True:
                if found:
                    break
                try:
                    self.nextTime=self.nextTime.replace(day=next(self.days))
                    self.daysOfWeek=self._generateDayOfWeek(self.dayOfWeekSet)
                    for dayOfWeek in self.daysOfWeek:
                        dayOfWeek=self._cron2python(dayOfWeek)
                        if self.nextTime.weekday() == dayOfWeek:
                            found=True
                            break
                except StopIteration:
                    #uprav daySet pro nasledujici mesic, pokud je zadan kazdy den
                    if self._allDays:
                        self._adjustDaySetByMonth()
                    #nebo pokud byly zadany nasobky dnu
                    elif self._multipleDays:
                        self.daySet=self._makeDaySetAfter(self.day)
                    #vyresetuj mnozinu dni                     
                    self.days=self._generateDays(self.daySet)
                    #posun o den
                    self.nextTime=self.nextTime.replace(day=next(self.days))
                    #zkus posunout mesic
                    try:
                        self._nextMonth()
                    #jsme na konci mnoziny mesicu, bude se posouvat i rok
                    except StopIteration:
                        #vyresetuj mnozinu mesicu
                        self.months=self._generateMonths(self.monthSet)
                        #posun mesic
                        self._nextMonth()
                        #posun rok (mnozina roku neni, nemusi se nic hlidat)
                        self._nextYear()
                    self.daysOfWeek=self._generateDayOfWeek(self.dayOfWeekSet)                      
                    for dayOfWeek in self.daysOfWeek:
                        dayOfWeek=self._cron2python(dayOfWeek)
                        if self.nextTime.weekday() == dayOfWeek:
                            found=True
                            break
                self._dateUsed=True
        #dny nejsou vsechny (konkretni den, vycet, rozsah), dny v tydnu jsou vsechny (*)
        elif not self._allDays and self._allDaysOfWeek:
            #posunu den podle vytvorene mnoziny dni
            self.nextTime=self.nextTime.replace(day=next(self.days))
        #dny nejsou vsechny (konkretni den, vycet, rozsah) ani dny v tydnu nejsou vsechny (konkretni den, vycet, rozsah)
        else:
            #posunu oboje dokud nebude splnena aspon jedna podminka
            #napr: 10.den v mesici a utery => pristi iterace bude v 10.den v mesici NEBO v utery (utery nemusi byt 10. den v mesici)
            #raise NotImplementedError
        
            found=False
            while True:
                if found:
                    break
                try:
                    self.nextTime=self.nextTime.replace(day=next(self._allDaysGen))
                    #vyresetuj generator dnu v tydnu
                    self.daysOfWeek=self._generateDayOfWeek(self.dayOfWeekSet)
                    #projdi dny v tydnu a hledej shodu
                    for dayOfWeek in self.daysOfWeek:
                        dayOfWeek=self._cron2python(dayOfWeek)
                        if self.nextTime.weekday() == dayOfWeek:
                            found=True
                            break
                    
                    #vyresetuj generator dnu v mesici
                    self.days=self._generateDays(self.daySet)
                    
                    #projdi dny v mesici a hledej shodu
                    for day in self.days:
                        if self.nextTime.day == day:
                            found=True
                            break

                except StopIteration:
                    #vytvor pomocnou mnozinu vsech dni pro pristi mesic
                    self._allDaySet=self._adjustDaySetByMonth(False)
                    
                    #vyresetuj pomocnou mnozinu vsech dni                     
                    self._allDaysGen=self._generateDays(self._allDaySet)
                    
                    #posun o den
                    self.nextTime=self.nextTime.replace(day=next(self._allDaysGen))
                    #zkus posunout mesic
                    try:
                        self._nextMonth()
                    #jsme na konci mnoziny mesicu, bude se posouvat i rok
                    except StopIteration:
                        #vyresetuj mnozinu mesicu
                        self.months=self._generateMonths(self.monthSet)
                        #posun mesic
                        self._nextMonth()
                        #posun rok (mnozina roku neni, nemusi se nic hlidat)
                        self._nextYear()

                    #vyresetuj generator dnu v tydnu
                    self.daysOfWeek=self._generateDayOfWeek(self.dayOfWeekSet)
                    #projdi dny v tydnu a hledej shodu
                    for dayOfWeek in self.daysOfWeek:
                        dayOfWeek=self._cron2python(dayOfWeek)
                        if self.nextTime.weekday() == dayOfWeek:
                            found=True
                            break
                    
                    #vyresetuj generator dnu v mesici
                    self.days=self._generateDays(self.daySet)
                    
                    #projdi dny v mesici a hledej shodu
                    for day in self.days:
                        if self.nextTime.day == day:
                            found=True
                            break
                self._dateUsed=True     
 
    def _nextMonth(self):
        try:
            self.nextTime=self.nextTime.replace(month=next(self.months))
            return True
        except ValueError:
            return False
            
        
    def _nextYear(self):
        currYear=self.nextTime.year
        self.nextTime=self.nextTime.replace(year=currYear+1)
        
    def _cron2python(self, dayOfWeek):
        return (dayOfWeek+6)%7
    
    def _makeSets(self, minute, hour, day, month, dayOfWeek):
        #vytvori mnoziny
        self.minuteSet=self._makeMinuteSet(minute)
        self.hourSet=self._makeHourSet(hour)
        self.monthSet=self._makeMonthSet(month)
        self.daySet=self._makeDaySet(day)
        self.dayOfWeekSet=self._makeDayOfWeekSet(dayOfWeek)
        
    
    def _makeGens(self):      
        #vytvori generatory z mnozin
        self.minutes=self._generateMinutes(self.minuteSet)
        self.hours=self._generateHours(self.hourSet)
        self.days=self._generateDays(self.daySet)
        self.months=self._generateMonths(self.monthSet)
        self.daysOfWeek=self._generateDayOfWeek(self.dayOfWeekSet)
        
        #vytvoreni pomocne mnoziny vsech dni
        if not self._allDays and not self._allDaysOfWeek:
            self._allDaySet=self._adjustDaySetByMonth(False)
            self._allDaysGen=self._generateDays(self._allDaySet)
        
        #doupraveni mnoziny dni pro zapisy "*/5" atd. a vytvoreni prislusneho generatoru
        if self._multipleDays:
            self.daySet=self._makeDaySetAfter(self.day)
            self.days=self._generateDays(self.daySet)
        
        #douprave mnoziny dni pro zapisy "*" a vytvoreni prislusneho generatoru
        if self._allDays:
            #vytvor mnozinu dni podle nasledujiciho mesice a roku
            self._adjustDaySetByMonth()
            #vytvor generator
            self.days=self._generateDays(self.daySet)
    
    def _setFirstTime(self):       
        self._dateUsed=False   
        
        
        #inicializace generatoru
        self._nextMinute()
        self._nextHour()
        self._nextMonth()
        self._nextDay()

        while ((self.nextTime<=self.startTime)):
            self._dateUsed=False
            #posun cas
            self._predictNext()
        self._dateUsed=False
        
    def _predictNext(self):        
        try:
            #zkus posunout minutu dal
            self._nextMinute()
        except StopIteration:
            #dorazilo se na konec mnoziny, bude se posouvit i hodina
            #vyresetuj generator minut
            self.minutes=self._generateMinutes(self.minuteSet)
            #posun opet minutu
            self._nextMinute()
            #zkus posunout i hodinu
            try:
                self._nextHour()
            #jsme na konci mnoziny hodin, bude se posouvat i den
            except StopIteration:
                #vyresetuj mnozinu hodin
                self.hours=self._generateHours(self.hourSet)
                #posun hodinu
                self._nextHour()
                #zkus posunout den
                try:
                    self._nextDay()
                #jsme na konci mnoziny dni, bude se posouvat i mesic
                except StopIteration:
                    #uprav daySet pro nasledujici mesic, pokud je zadan kazdy den
                    if self._allDays:
                        self._adjustDaySetByMonth()
                    #nebo pokud byly zadany nasobky dnu
                    elif self._multipleDays:
                        self.daySet=self._makeDaySetAfter(self.day)
                    #vyresetuj mnozinu dni                     
                    self.days=self._generateDays(self.daySet)
                    #posun den
                    self._nextDay()
                    #zkus posunout mesic
                    #pokud je den fixni, napr. 30 a mesic nema tolik dni (napr. unor), preskoc ho a zkus dalsi
                    try:
                        while not self._nextMonth():
                            pass
                    #jsme na konci mnoziny mesicu, bude se posouvat i rok
                    except StopIteration:
                        #vyresetuj mnozinu mesicu
                        self.months=self._generateMonths(self.monthSet)
                        #posun mesic
                        self._nextMonth()
                        #posun rok (mnozina roku neni, nemusi se nic hlidat)
                        self._nextYear()
        
    def _printTime(self):
        print(self.nextTime.strftime("%H:%M:%S %d.%m.%Y"))
        
    def _printInterval(self,timeFrom,timeTo):
        print(timeFrom.strftime("%H:%M:%S %d.%m.%Y")+" ---> "+timeTo.strftime("%H:%M:%S %d.%m.%Y"))
        
    def _addTime(self,startTime,length):
        lengthTimedelta=timedelta(seconds=length)
        endTime=startTime+lengthTimedelta
        return endTime
        
    def iterate(self,n,cronJobList):
        for _ in range(n):
            endTime=self._addTime(self.nextTime, self.length)
            cronJobList.append(CCronJob(self.nextTime,endTime))
            #self._printInterval(self.nextTime, endTime)
            self._predictNext()
            self._dateUsed=False
        return cronJobList
            
    def iterateUntil(self,toDate,cronJobList):
        prevDuration=None
        while self.nextTime<=toDate:
            prevTime=self.nextTime
            endTime=self._addTime(self.nextTime, self.length)
            cronJobList.append(CCronJob(self.nextTime,endTime))
            #self._printInterval(self.nextTime, endTime)
            self._predictNext()
            duration = self.nextTime - prevTime
            self.spaceBetweenRuns=duration
            if prevDuration is not None and prevDuration != duration:
                self.constantSpaces=False
                self.spaceBetweenRuns=None
            prevDuration = duration
            self._dateUsed=False
        return cronJobList
              
    
    def test(self,name, n=100):
        #otevri soubor pro zapis vystupu predikce cronu
        file=open("/home/petr/git/Cron Analyzer/test/"+"output"+str(name),"w+")   
        for _ in range(n):
            file.write(self.nextTime.strftime("%Y-%m-%d %H:%M:%S")+"\n")
            self._predictNext()
            self._dateUsed=False  
        file.close()
        
    def getAllDays(self):
        return self._allDays
    
    def getAllDaysOfWeek(self):
        return self._allDaysOfWeek
            





