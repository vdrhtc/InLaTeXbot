import pickle
from multiprocessing import Lock

class UserOptionsManager():
    
    def __init__(self, optionsFile = "./resources/options.pkl"):
        self._optionsFile = optionsFile
        self._lock = Lock()
        
        
    def getCodeInCaptionOption(self, userId):
        try:
            userOptions = self.getUserOptions(userId)
        except KeyError:
            userOptions = self.getDefaultUserOptions()
        return userOptions['show_code_in_caption']
        
    def setCodeInCaptionOption(self, userId, value):
        try:
            userOptions = self.getUserOptions(userId)
        except KeyError:
            userOptions = self.getDefaultUserOptions()
        userOptions['show_code_in_caption'] = value
        self.setUserOptions(userId, userOptions)
        
    def getUserOptions(self, userId):
        with self._lock:
            with open(self._optionsFile, "rb") as f:
                userOptions = pickle.load(f)[userId]
            return userOptions
    
    def setUserOptions(self, userId, userOptions):
        with self._lock:
            with open(self._optionsFile, "rb") as f:
                options = pickle.load(f)
            options[userId] = userOptions
            with open(self._optionsFile, "wb") as f:
                pickle.dump(options, f)
        
    def getDefaultUserOptions(self):
        return {'show_code_in_caption': False}
