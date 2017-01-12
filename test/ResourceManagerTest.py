import unittest
from src.ResourceManager import ResourceManager

class ResourceManagerTest(unittest.TestCase):
    
    def setUp(self):
        self.sut = ResourceManager()
        
    def testGetString(self):
        self.assertEqual(self.sut.getString("telegram_error"), "Telegram error: ")
        
    def testGetString(self):
        self.assertEqual(self.sut.getNumber("max_preamble_length"), 4000)
