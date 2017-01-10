import unittest
from src.PreambleManager import PreambleManager

class PreambleManagerTest(unittest.TestCase):

    def setUp(self):
        self.sut = PreambleManager()

    def testValidatePreamble(self):
        correct_preamble="\documentclass[12pt]{article}"
        self.assertEqual(self.sut.validatePreamble(correct_preamble), True)

        incorrect_preamble="\documentclass[12pt]{arti}"
        self.assertEqual(self.sut.validatePreamble(incorrect_preamble), False)
        
if __name__ == '__main__':
    unittest.main()
    
