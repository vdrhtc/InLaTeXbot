from subprocess import check_output, CalledProcessError, STDOUT, TimeoutExpired

from src.PreambleManager import PreambleManager
from src.LoggingServer import LoggingServer
import io

class LatexConverter():

    logger = LoggingServer.getInstance()
    
    def __init__(self, preambleManager, userOptionsManager):
         self._preambleManager = preambleManager
         self._userOptionsManager = userOptionsManager

    def extractBoundingBox(self, dpi, pathToPdf):
        bbox = check_output("gs -q -dBATCH -dNOPAUSE -sDEVICE=bbox "+pathToPdf, 
                            stderr=STDOUT, shell=True).decode("ascii")
        bounds = [int(_) for _ in bbox[bbox.index(":")+2:bbox.index("\n")].split(" ")]
        llc = bounds[:2]
        ruc = bounds[2:]
        size_factor = dpi/72
        width = (ruc[0]-llc[0])*size_factor
        height = (ruc[1]-llc[1])*size_factor
        translation_x = llc[0]
        translation_y = llc[1]
        if width == 0 or height == 0:
            self.logger.warn("Expression had zero width/height bbox!")
            raise ValueError("Empty expression!")
        return width, height, -translation_x, -translation_y
    
    def correctBoundingBoxAspectRaito(self, dpi, boundingBox, maxWidthToHeight=3, maxHeightToWidth=1):
        width, height, translation_x, translation_y = boundingBox
        size_factor = dpi/72
        if width>maxWidthToHeight*height:
            translation_y += (width/maxWidthToHeight-height)/2/size_factor
            height = width/maxWidthToHeight
        elif height>maxHeightToWidth*width:
            translation_x += (height/maxHeightToWidth-width)/2/size_factor
            width = height/maxHeightToWidth
        return width, height, translation_x, translation_y
        
    def getError(self, log):
        for idx, line in enumerate(log):
            if line[:2]=="! ":
                return "".join(log[idx:idx+2])
        
    def pdflatex(self, fileName):
        try:
            check_output(['pdflatex', "-interaction=nonstopmode", "-output-directory", 
                    "build", fileName], stderr=STDOUT, timeout=5).decode("ascii")
        except CalledProcessError as inst:
            with open(fileName[:-3]+"log", "r") as f:
                msg = self.getError(f.readlines())
                self.logger.debug(msg)
                raise ValueError(msg)
        except TimeoutExpired:
                msg = "Pdflatex has likely hung up and had to be killed. Congratulations!"
                raise ValueError(msg)
    
    def cropPdf(self, sessionId):
        bbox = check_output("gs -q -dBATCH -dNOPAUSE -sDEVICE=bbox build/expression_file_%s.pdf"%sessionId, 
                            stderr=STDOUT, shell=True).decode("ascii")
        bounds = tuple([int(_) for _ in bbox[bbox.index(":")+2:bbox.index("\n")].split(" ")])

        command_crop = 'gs -o build/expression_file_cropped_%s.pdf -sDEVICE=pdfwrite\
                         -c "[/CropBox [%d %d %d %d]"   -c " /PAGES pdfmark" -f build/expression_file_%s.pdf'\
                         %((sessionId,)+bounds+(sessionId,))
        check_output(command_crop, stderr=STDOUT, shell=True)
            
    def convertPdfToPng(self, dpi, sessionId, bbox):
        command = 'gs  -o build/expression_%s.png -r%d -sDEVICE=pngalpha  -g%dx%d  -dLastPage=1 \
                    -c "<</Install {%d %d translate}>> setpagedevice" -f build/expression_file_%s.pdf'\
                    %((sessionId, dpi)+bbox+(sessionId,))
        check_output(command, stderr=STDOUT, shell=True)

    def convertExpressionToPng(self, expression, userId, sessionId, returnPdf = False):
        
        preamble=""
        try:
            preamble=self._preambleManager.getPreambleFromDatabase(userId)
            self.logger.debug("Preamble for userId %d found", userId)
        except KeyError:
            self.logger.debug("Preamble for userId %d not found, using default preamble", userId)
            preamble=self._preambleManager.getDefaultPreamble()
            
        fileString = preamble+"\n\\begin{document}\n"+expression+"\n\\end{document}"
            
        with open("build/expression_file_%s.tex"%sessionId, "w+") as f:
            f.write(fileString)
        
        dpi = self._userOptionsManager.getDpiOption(userId)
        
        try:
            self.pdflatex("build/expression_file_%s.tex"%sessionId)
                
            bbox = self.extractBoundingBox(dpi, "build/expression_file_%s.pdf"%sessionId)
            bbox = self.correctBoundingBoxAspectRaito(dpi, bbox)
            self.convertPdfToPng(dpi, sessionId, bbox)
            
            self.logger.debug("Generated image for %s", expression)
            
            with open("build/expression_%s.png"%sessionId, "rb") as f:
                imageBinaryStream = io.BytesIO(f.read())

            if returnPdf:
                self.cropPdf(sessionId)
                with open("build/expression_file_cropped_%s.pdf"%sessionId, "rb") as f:
                    pdfBinaryStream = io.BytesIO(f.read())
                return imageBinaryStream, pdfBinaryStream
            else:
                return imageBinaryStream
                
        finally:
            check_output(["rm build/*_%s.*"%sessionId], stderr=STDOUT, shell=True)
        
