import unittest
from unittest.mock import Mock, MagicMock, ANY

from time import sleep

from src.MessageQueryResponseDispatcher import MessageQueryResponseDispatcher
from src.ResourceManager import ResourceManager
from src.UserOptionsManager import UserOptionsManager

class MessageQueryResponseDispatcherTest(unittest.TestCase):

    def setUp(self):
        self.latexConverter = Mock()
        self.bot = Mock()
        self.sut = MessageQueryResponseDispatcher(self.bot, self.latexConverter, ResourceManager())
    
    def testRespondToMessageQuery(self):
        
        message = Mock()
        message.id=111
        message.from_user.id = 115
        message.chat.id = 115
        message.text="$x^2$"
        
        bot = Mock()
        bot.sendPhoto = Mock()
        self.latexConverter.convertExpression = Mock(return_value=(Mock(), Mock()))
        
        self.sut.respondToMessageQuery(message)
        
        self.bot.sendPhoto.assert_called_with(message.from_user.id, ANY)
                
if __name__ == '__main__':
    unittest.main()
     
