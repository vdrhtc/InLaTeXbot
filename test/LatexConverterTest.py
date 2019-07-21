import unittest
from unittest.mock import Mock

import os
from datetime import datetime as dt
from subprocess import check_output, CalledProcessError, STDOUT

from src.LatexConverter import LatexConverter
from src.PreambleManager import PreambleManager
from src.ResourceManager import ResourceManager
from src.UserOptionsManager import UserOptionsManager

class LatexConverterTest(unittest.TestCase):

    def setUp(self):
        userOptionsManager = Mock()
        userOptionsManager.getDpiOption = Mock(return_value = 720)
        self.sut = LatexConverter(PreambleManager(ResourceManager()), userOptionsManager)

    def testExtractBoundingBox(self):
        self.sut.logger.debug("Extracting bbox")
        self.sut.extractBoundingBox(720, "resources/test/bbox.pdf")
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

    def testPdflatexHangupHandling(self):
        try:
            self.sut.pdflatex("resources/test/pdflatex_hanging_file.tex")
        except ValueError as err:
            self.assertEqual(err.args[0], "Pdflatex has likely hung up and had to be killed. Congratulations!")

    def testConvertExpressionToPng(self):
        binaryData = self.sut.convertExpressionToPng("$x^2$", 115, "id").read()
        with open('resources/test/xsquared.png', "rb") as f:
            correctBinaryData = f.read()
        self.assertAlmostEqual(len(binaryData), len(correctBinaryData), delta=50)
        
        binaryData = self.sut.convertExpressionToPng("$x^2$"*10, 115, "id").read()
        with open('resources/test/xsquared10times.png', "rb") as f:
            correctBinaryData = f.read()
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
            
    def testReturnPdf(self):
        pdfBinaryData = self.sut.convertExpressionToPng("lol", 115, "id", True)[1].read()
        with open('resources/test/cropped.pdf', "rb") as f:
            correctBinaryData = f.read()
        self.assertAlmostEqual(len(pdfBinaryData), len(correctBinaryData), delta=50)
       
    #def testPrivacySettings(self):
    #    self.sut.logger.debug("Started pdflatex")
    #    self.sut.pdflatex("resources/test/privacy.tex")
    #    self.sut.logger.debug("Pdflatex finished")
    
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
    
