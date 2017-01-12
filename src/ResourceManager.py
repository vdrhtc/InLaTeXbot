import json

class ResourceManager():
    
    def __init__(self, stringsFile = "resources/strings.json", numbersFile = "resources/numbers.json"):
        self._stringsFile = stringsFile
        self._numbersFile = numbersFile
        
    def getString(self, stringId):
        with open(self._stringsFile, "r") as f:
            return json.load(f)[stringId]
    
    def getNumber(self, numberId):
        with open(self._numbersFile, "r") as f:
            return json.load(f)[numberId]
