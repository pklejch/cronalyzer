from CronLogger import CCronLogger

try:
    import dominate
    from dominate.tags import *
except ImportError:
    CCronLogger.errorToConsole("You don't have required Python module.")
    CCronLogger.debugToConsole("Required modules are: dominate")

class CCronReport:
    def __init__(self,options, newCrontab, statsBefore, statsAfter, shiftVector, cronList):
        self.setOptions(options)
        self.newCrontab=newCrontab
        self.statsBefore=statsBefore
        self.statsAfter=statsAfter
        self.shiftVector=shiftVector
        self.cronList=cronList
        
    def setOptions(self,options):
        try:
            self._outputDir=options["outputdir"]
            CCronLogger.debug("Output directory: "+self._outputDir)
        except KeyError:
            CCronLogger.info("Output directory directive not found. Setting to default: working directory.")
            self._outputDir="./"       
        
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
            
    def createReport(self):
        document = dominate.document(title="Ouput report from Cronalyzer")
        document.head.add(meta(charset="utf-8"))
        
        document.body.add(h1("Output report from Cronalyzer"))
        document.body.add(h2("Plot with cronjobs before optimization:"))
        document.body.add(img(src=self._graphName, alt="Plot with cronjobs."))
        document.body.add(h2("Plot with weights of cronjobs before optimization:"))
        document.body.add(img(src=self._weightGraphName, alt="Plot with weights of cronjobs."))
        
        document.body.add(h2("Plot with cronjobs after optimization:"))
        document.body.add(img(src="improved_"+self._graphName, alt="Plot with cronjobs after optimization."))
        document.body.add(h2("Plot with weights of cronjobs after optimization:"))
        document.body.add(img(src="improved_"+self._weightGraphName, alt="Plot with weights of cronjobs after optimization."))
        
        document.body.add(h2("List of jobs and recommended shift in minutes"))
        vector=document.body.add(div())
        
        cronID=0
        for cron in self.cronList:
            shiftAmount=self.shiftVector[cronID]
            vector += str(cron)+" should be shift by: "+str(shiftAmount)+" minutes."
            vector += br()
            cronID+=1
        
        document.body.add(h2("Summary of optimization"))
        document.body.add(h3("Statistics before optimization"))
        before=document.body.add(div())
        
        before += "Standard deviation in test intervals: "+str(self.statsBefore[0])
        before += br()
        before += "Max weight in test intervals: "+str(self.statsBefore[1])
        before += br()
        before += "Min weight in test intervals: "+str(self.statsBefore[2])    
        before += br()
        
        
        
        document.body.add(h3("Statistics after optimization"))
        after=document.body.add(div())
        after+="Standard deviation in test intervals: "+str(self.statsAfter[0])
        after+=br()
        after+="Max weight in test intervals: "+str(self.statsAfter[1])
        after+=br()
        after+="Min weight in test intervals: "+str(self.statsAfter[2])
        after+=br()

        
        document.body.add(h2("Suggestion for better crontab."))
        document.body.add(pre(self.newCrontab))
        
        document.body.add(a("More information about analysis in logfile.",href="logfile.log"))
        
        try:
            with open(self._outputDir+"report.html","w") as f:
                f.write(document.render())
        except:
            CCronLogger.error("Error while saving report.")
            CCronLogger.errorToConsole("Error while saving report.")