import unittest
from src.InLaTeXbot import InLaTeXbot


class InLaTeXbotTest(unittest.TestCase):

    def setUp(self):
        self.sut = InLaTeXbot()
        
#    def testLaunch(self):
#        self.sut.launch()
#    
#    def testStop(self):
#        self.sut.stop()
        
if __name__ == '__main__':
    unittest.main()
     
