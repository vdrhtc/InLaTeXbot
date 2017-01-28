import unittest
import pickle

from src.UsersManager import UsersManager

class UserOptionsManagerTest(unittest.TestCase):
    
    def setUp(self):
        testFile = "/tmp/testUsers.pkl"
        with open(testFile, "w+b") as f:
            pickle.dump({"":None}, f)
            
        self.sut = UsersManager(testFile)
        
    def test(self):
        self.sut.setUser("115", {})
        self.assertEqual(self.sut.getUser("115"), {})
    
    def testGetKnownUsers(self):
        self.sut.setUser("115", {})
        self.assertTrue("115" in self.sut.getKnownUsers())
        
    
