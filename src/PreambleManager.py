from subprocess import check_output, CalledProcessError, STDOUT
from multiprocessing import Lock
import pickle as pkl
from src.ResourceManager import ResourceManager
from src.LoggingServer import LoggingServer

class PreambleManager():
    
    logger = LoggingServer.getInstance()

    def __init__(self, resourceManager, preamblesFile = "./resources/preambles.pkl"):
        self._resourceManager = resourceManager
        self._preamblesFile = preamblesFile
#        self._defaultPreamble = self.readDefaultPreamble()
        self._lock = Lock()
        
#    def getDefaultPreamble(self):
#        return self._defaultPreamble
        
    def getDefaultPreamble(self):
        with open("./resources/default_preamble.txt", "r") as f:
            return f.read()
    
    def getPreambleFromDatabase(self, preambleId):
        with self._lock:
            with open(self._preamblesFile, "rb") as f:
                preambles = pkl.load(f)
            return preambles[preambleId]
    
    def putPreambleToDatabase(self, preambleId, preamble):
        with self._lock:
            with open(self._preamblesFile, "rb") as f:
                preambles = pkl.load(f)
            preambles[preambleId] = preamble
            with open(self._preamblesFile, "wb") as f:
                pkl.dump(preambles, f)

    def getError(self, log):
        for idx, line in enumerate(log):
            if line[:2]=="! ":
                return "".join(log[idx:idx+2])
    
    def validatePreamble(self, preamble):
        if len(preamble) > self._resourceManager.getNumber("max_preamble_length"):
            return False, self._resourceManager.getString("preamble_too_long")%self._resourceManager.getNumber("max_preamble_length")
            
        document = preamble+"\n\\begin{document}TEST PREAMBLE\\end{document}"
        with open("./build/validate_preamble.tex", "w+") as f:
            f.write(document)
        try:
            check_output(['pdflatex', "-interaction=nonstopmode","-draftmode", "-output-directory", "./build", "./build/validate_preamble.tex"], stderr=STDOUT)
            return True, ""
        except CalledProcessError as inst:
            with open("./build/validate_preamble.log", "r") as f:
                msg = self.getError(f.readlines())[:-1]
                self.logger.debug(msg)
            return False, self._resourceManager.getString("preamble_invalid")+"\n"+msg
        finally:
            check_output(["rm ./build/validate_preamble.*"], stderr=STDOUT, shell=True)
    
