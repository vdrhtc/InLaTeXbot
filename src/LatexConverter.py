from subprocess import check_output, CalledProcessError, STDOUT, TimeoutExpired

from src.PreambleManager import PreambleManager
from src.LoggingServer import LoggingServer
import io
import re


class LatexConverter():

    logger = LoggingServer.getInstance()
    
    def __init__(self, preambleManager, userOptionsManager):
         self._preambleManager = preambleManager
         self._userOptionsManager = userOptionsManager

    def extractBoundingBox(self, dpi, pathToPdf):
        try:
            bbox = check_output("gs -q -dBATCH -dNOPAUSE -sDEVICE=bbox " + pathToPdf,
                                stderr=STDOUT, shell=True).decode("ascii")
        except CalledProcessError:
            raise ValueError("Could not extract bounding box! Empty expression?")
        try:
            bounds = [int(_) for _ in bbox[bbox.index(":")+2:bbox.index("\n")].split(" ")]
        except ValueError:
            raise ValueError("Could not parse bounding box! Empty expression?")

        if bounds[0] == bounds[2] or bounds[1] == bounds[3]:
            self.logger.warn("Expression had zero width/height bbox!")
            raise ValueError("Empty expression!")

        hpad = 0.25 * 72  # 72 postscript points = 1 inch
        vpad = .1 * 72
        llc = bounds[:2]
        llc[0] -= hpad
        llc[1] -= vpad
        ruc = bounds[2:]
        ruc[0] += hpad
        ruc[1] += vpad
        size_factor = dpi/72
        width = (ruc[0]-llc[0])*size_factor
        height = (ruc[1]-llc[1])*size_factor
        translation_x = llc[0]
        translation_y = llc[1]
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
                    "build", fileName], stderr=STDOUT, timeout=5)
        except CalledProcessError as inst:
            with open(fileName[:-3]+"log", "r") as f:
                msg = self.getError(f.readlines())
                self.logger.debug(msg)
                raise ValueError(msg)
        except TimeoutExpired:
                msg = "Pdflatex has likely hung up and had to be killed. Congratulations!"
                raise ValueError(msg)
    
    def cropPdf(self, sessionId): # TODO: this is intersecting with the png part
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

    def convertExpression(self, expression, userId, sessionId, returnPdf = False):




        if r"\documentclass" in expression:
            fileString = expression
        else:
            try:
                preamble = self._preambleManager.getPreambleFromDatabase(userId)
                self.logger.debug("Preamble for userId %d found", userId)
            except KeyError:
                self.logger.debug("Preamble for userId %d not found, using default preamble", userId)
                preamble = self._preambleManager.getDefaultPreamble()
            finally:
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
        
