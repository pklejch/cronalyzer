import configparser
class CConfigParser:
    def __init__(self, configName):
        self._configName=configName
        self._parser=configparser.RawConfigParser()
        self.options=dict()
    def readToMap(self):
        for section in self._parser.sections():
            for option in self._parser.options(section):
                try:
                    self.options[option]=self._parser.getboolean(section, option)
                except ValueError:
                    self.options[option]=self._parser.get(section, option)
        
    def parseConfig(self):
        self._parser.read(self._configName, "utf-8")
        self.readToMap()
        return self.options
        