import unittest

from src.UserOptionsManager import UserOptionsManager

class UserOptionsManagerTest(unittest.TestCase):
    
    def setUp(self):
        self.sut = UserOptionsManager()
        
    def test(self):
        self.sut.setUserOptions("115", self.sut.getDefaultUserOptions())
        self.assertEqual(self.sut.getUserOptions("115"), self.sut.getDefaultUserOptions())
        
    def testSetCodeInCaption(self):
        self.sut.setCodeInCaptionOption("115", True)
        self.assertEqual(self.sut.getUserOptions("115")["show_code_in_caption"], True)
