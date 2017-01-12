from subprocess import check_output, CalledProcessError, STDOUT
from src.PreambleManager import PreambleManager
import io

class LatexConverter():

    def __init__(self, preambleManager, preambleId = "default", pngResolution=720):
         self._preambleId = preambleId
         self._pngResolution = pngResolution
         self._preambleManager = preambleManager
         
    def setPreambleId(self, preambleId):
        self._preambleId = preambleId

    def extractBoundingBox(self, pathToPdf):
        bbox = check_output("gs -q -dBATCH -dNOPAUSE -sDEVICE=bbox "+pathToPdf, 
                            stderr=STDOUT, shell=True).decode("ascii")
        bounds = [int(_) for _ in bbox[bbox.index(":")+2:bbox.index("\n")].split(" ")]
        llc = bounds[:2]
        ruc = bounds[2:]
        size_factor = self._pngResolution/72
        width = (ruc[0]-llc[0])*size_factor
        height = (ruc[1]-llc[1])*size_factor
        translation_x = llc[0]
        translation_y = llc[1]
        return width, height, -translation_x, -translation_y
    
    def correctBoundingBoxAspectRaito(self, boundingBox, maxWidthToHeight=3, maxHeightToWidth=1):
        width, height, translation_x, translation_y = boundingBox
        size_factor = self._pngResolution/72
        if width>maxWidthToHeight*height:
            translation_y += (width/maxWidthToHeight-height)/2/size_factor
            height = width/maxWidthToHeight
        elif height>maxHeightToWidth*width:
            translation_x += (height/maxHeightToWidth-width)/2/size_factor
            width = height/maxHeightToWidth
        return width, height, translation_x, translation_y

    def  convertExpressionToPng(self, expression, userId):
        
        preamble=""
        try:
            preamble=self._preambleManager.getPreambleFromDatabase(userId)
        except KeyError:
            preamble=self._preambleManager.getPreambleFromDatabase("default")
            
        templateString = preamble+"\n\\begin{document}%s\\end{document}"
            
        with open("build/expression_file_%d.tex"%userId, "w+") as f:
            f.write(templateString%expression)
            
        try:
            check_output(['pdflatex', "-interaction=nonstopmode", "-output-directory", "build", "build/expression_file_%d.tex"%userId], stderr=STDOUT).decode("ascii")
        except CalledProcessError as inst:
            raise ValueError("Wrong LaTeX syntax in the query")
            
        bbox = self.extractBoundingBox("build/expression_file_%d.pdf"%userId)
        bbox = self.correctBoundingBoxAspectRaito(bbox)
        
        command = 'gs  -o resources/expression_%d.png -r%d -sDEVICE=pngalpha  -g%dx%d  -dLastPage=1 \
                -c "<</Install {%d %d translate}>> setpagedevice" -f build/expression_file_%d.pdf'\
                %((userId, self._pngResolution)+bbox+(userId,))
            
        check_output(command, stderr=STDOUT, shell=True)
        with open("resources/expression_%d.png"%userId, "rb") as f:
            binaryDataStream = io.BytesIO(f.read())
            
        check_output(["rm build/*_%d.*"%userId], stderr=STDOUT, shell=True)
        check_output(["rm resources/*_%d.png"%userId], stderr=STDOUT, shell=True)
        
        return binaryDataStream
        
