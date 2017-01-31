import unittest
import os
from datetime import datetime as dt
from subprocess import check_output, CalledProcessError, STDOUT

from src.LatexConverter import LatexConverter
from src.PreambleManager import PreambleManager
from src.ResourceManager import ResourceManager

class LatexConverterTest(unittest.TestCase):

    def setUp(self):
        self.sut = LatexConverter(PreambleManager(ResourceManager()), pngResolution=720)

    def testExtractBoundingBox(self):
        self.sut.logger.debug("Extracting bbox")
        self.sut.extractBoundingBox("resources/test/bbox.pdf")
        self.sut.logger.debug("Extracted bbox")
    
    def testCorrectBoundingBoxAspectRaito(self):
        pass
    
    def testPdflatex(self):
        self.sut.logger.debug("Started pdflatex")
        self.sut.pdflatex("resources/test/pdflatex.tex")
        self.sut.logger.debug("Pdflatex finished")

        try: 
            self.sut.pdflatex("resources/test/pdflatexwerror.tex")
        except ValueError as err:
            self.assertEqual(err.args[0], "! Missing lol inserted\nasldkasdaskd;laskd;a\n")
            
        check_output(["rm build/pdflatex*"], stderr=STDOUT, shell=True)

    def testConvertExpressionToPng(self):
        binaryData = self.sut.convertExpressionToPng("$x^2$", 115, "id").read()
        with open('resources/test/xsquared.png', "rb") as f:
            correctBinaryData = f.read()
        self.assertAlmostEqual(len(binaryData), len(correctBinaryData), delta=50)
        
        binaryData = self.sut.convertExpressionToPng("$x^2$"*10, 115, "id").read()
        with open('resources/test/xsquared10times.png', "rb") as f:
            correctBinaryData = f.read()
        self.assertAlmostEqual(len(binaryData), len(correctBinaryData), delta=50)
        
        self.sut.setPreambleId("11")
        binaryData = self.sut.convertExpressionToPng("$x^2$"*10, 115, "id").read()
        self.assertAlmostEqual(len(binaryData), len(correctBinaryData), delta=50)
    
    def testDeleteFilesInAllCases(self):
        self.sut.convertExpressionToPng("$x^2$", 115, "id")
        self.assertEqual(len(os.listdir("build/")), 0)
        
        try:
            self.sut.convertExpressionToPng("$$$$", 115, "id1").read()
        except ValueError:
            self.assertEqual(len(os.listdir("build/")), 0)
        
        try:
            self.sut.convertExpressionToPng(r"lo \asdasd", 115, "id2").read()
        except ValueError:
            self.assertEqual(len(os.listdir("build/")), 0)
    
    def testEmptyQuery(self):
        with self.assertRaises(ValueError):
            self.sut.convertExpressionToPng("$$$$", 115, "id").read()
    
#    def testPerformance(self):
#        self.sut.logger.debug("Started performance test")
#        start = dt.now()
#        for i in range(0, 10):
#            self.sut.convertExpressionToPng("$x^2$", 115, "id")
#        elapsedTime = (dt.now()-start).total_seconds()/10*1000
#        self.sut.logger.debug("Performance test ended, time: %f ms", elapsedTime)
        
if __name__ == '__main__':
    test = LatexConverterTest()
    test.setUp()
    test.testPerformance()
#    unittest.main()
    
