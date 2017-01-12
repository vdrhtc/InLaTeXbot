import json

class ResourceManager():
    
    def __init__(self, stringsFile = "resources/strings.json"):
        self._stringsFile = stringsFile
        
    def getString(self, stringId):
        with open(self._stringsFile, "r") as f:
            return json.load(f)[stringId]
