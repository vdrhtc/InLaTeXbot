import unittest
import pickle

from src.UserOptionsManager import UserOptionsManager

class UserOptionsManagerTest(unittest.TestCase):
    
    def setUp(self):
        testFile = "/tmp/testUsers.pkl"
        with open(testFile, "w+b") as f:
            pickle.dump({"115":{'show_code_in_caption': False}}, f)
        self.sut = UserOptionsManager(testFile)
        
    def test(self):
        self.sut.setUserOptions("115", self.sut.getDefaultUserOptions())
        self.assertEqual(self.sut.getUserOptions("115"), self.sut.getDefaultUserOptions())
        
    def testSetCodeInCaption(self):
        self.sut.setCodeInCaptionOption("116", True)
        self.assertEqual(self.sut.getUserOptions("116")["show_code_in_caption"], True)
    
    def testGetDpiOption(self):
        dpi = self.sut.getDpiOption("115")
        self.assertEqual(dpi, 300)
