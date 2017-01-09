import unittest
from LatexConverter import LatexConverter

class LatexConverterTest(unittest.TestCase):

    def setUp(self):
        self.sut = LatexConverter()

    def testExtractBoundingBox(self):
        pass
    
    def testCorrectBoundingBoxAspectRaito(self):
        pass

    def testConvertExpressionToPng(self):
        pngFile = self.sut.convertExpressionToPng("$x^2$")
#        with open("expression.png", "rb") as f:
#            binaryData = f.read()
#        with open('resources/test/xsquared.png', "rb") as f:
#            correctBinaryData = f.read()
#        self.assertEquals(binaryData, correctBinaryData)
        
        pngFile = self.sut.convertExpressionToPng("$x^2$"*10)
#        with open("expression.png", "rb") as f:
#            binaryData = f.read()
#        with open('resources/test/xsquared10times.png', "rb") as f:
#            correctBinaryData = f.read()
#        self.assertEquals(binaryData, correctBinaryData)
        self.sut.setPreambleId("11")
        pngFile = self.sut.convertExpressionToPng("$x^2$"*10)
                
        
if __name__ == '__main__':
    unittest.main()
    
