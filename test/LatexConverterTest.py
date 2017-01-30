import unittest
import os

from src.LatexConverter import LatexConverter
from src.PreambleManager import PreambleManager
from src.ResourceManager import ResourceManager

class LatexConverterTest(unittest.TestCase):

    def setUp(self):
        self.sut = LatexConverter(PreambleManager(ResourceManager()), pngResolution=720)

    def testExtractBoundingBox(self):
        pass
    
    def testCorrectBoundingBoxAspectRaito(self):
        pass

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
            self.sut.convertExpressionToPng("$$$$", 115, "id").read()
        except ValueError:
            self.assertEqual(len(os.listdir("build/")), 0)
        
        try:
            self.sut.convertExpressionToPng("$^$ <> lo_\asdasd", 115, "id").read()
        except ValueError:
            self.assertEqual(len(os.listdir("build/")), 0)
    
    def testEmptyQuery(self):
        with self.assertRaises(ValueError):
            self.sut.convertExpressionToPng("$$$$", 115, "id").read()
        
if __name__ == '__main__':
    unittest.main()
    
