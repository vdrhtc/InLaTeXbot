from subprocess import check_output, CalledProcessError, STDOUT
import pickle as pkl
from src.ResourceManager import ResourceManager

class PreambleManager():
    
    def __init__(self, resourceManager):
        self._resourceManager = resourceManager
    
    def getPreambleFromDatabase(self, preambleId):
        with open("./resources/preambles.pkl", "rb") as f:
            preambles = pkl.load(f)
        return preambles[preambleId]
    
    def putPreambleToDatabase(self, preambleId, preamble):
        with open("./resources/preambles.pkl", "rb") as f:
            preambles = pkl.load(f)
        preambles[preambleId] = preamble
        with open("./resources/preambles.pkl", "wb") as f:
            pkl.dump(preambles, f)
    
    def validatePreamble(self, preamble):
        if len(preamble) > self._resourceManager.getNumber("max_preamble_length"):
            return False, self._resourceManager.getString("preamble_too_long")%self._resourceManager.getNumber("max_preamble_length")
            
        document = preamble+"\n\\begin{document}TEST PREAMBLE\\end{document}"
        with open("/tmp/validate_preamble.tex", "w+") as f:
            f.write(document)
        try:
            check_output(['pdflatex', "-interaction=nonstopmode","-output-directory", "/tmp", "/tmp/validate_preamble.tex"], stderr=STDOUT)
            return True, ""
        except CalledProcessError as inst:
            return False, self._resourceManager.getString("preamble_invalid")
    
