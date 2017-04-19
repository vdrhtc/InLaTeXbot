import unittest
from unittest.mock import Mock, MagicMock, ANY

from time import sleep

from src.InlineQueryResponseDispatcher import InlineQueryResponseDispatcher
from src.ResourceManager import ResourceManager
from src.UserOptionsManager import UserOptionsManager

class InlineQueryResponseDispatcherTest(unittest.TestCase):

    def setUp(self):
        self.latexConverter = Mock()
        self.bot = Mock()
        self.sut = InlineQueryResponseDispatcher(self.bot, self.latexConverter, ResourceManager(), UserOptionsManager(), -1)
    
    def testRespondToInlineQuery(self):
        bot = Mock()
        returnVal = Mock()
        photoVal = MagicMock()
        photoVal.file_id = "photo_id"
        returnVal.photo = [photoVal]
        bot.sendPhoto = Mock(return_value=returnVal)
        self.sut._bot = bot
        
        inline_query= Mock()
        inline_query.query = "$x^2$"
        inline_query.from_user.id = 1153
        inline_query.id = "id"
        
        nextQueryArrivedEvent = Mock()
        nextQueryArrivedEvent.is_set = Mock(return_value=False)
        
        self.sut.respondToInlineQuery(inline_query, nextQueryArrivedEvent)
        
        bot.sendPhoto.assert_called_with(ANY, ANY)
        
    def testRespondToTwoConsequentInlineQueries(self):
        bot = Mock()
        returnVal = Mock()
        photo = MagicMock()
        photo.file_id = "photo_id"
        returnVal.photo = [photo]
        bot.sendPhoto = Mock(return_value=returnVal)
        bot.answerInlineQuery = Mock()
        self.sut._bot = bot
        
        inline_query= Mock()
        inline_query.query = "$x^2$"
        inline_query.from_user.id = 1153
        inline_query.id = "id"
        
        nextQueryArrivedEvent = Mock()
        nextQueryArrivedEvent.is_set = Mock(return_value=False)
        self.sut.respondToInlineQuery(inline_query, nextQueryArrivedEvent)
        
        nextQueryArrivedEvent = Mock()
        nextQueryArrivedEvent.is_set = Mock(return_value=True)
        self.sut.respondToInlineQuery(inline_query, nextQueryArrivedEvent)
        self.assertEqual(self.sut._bot.answerInlineQuery.call_count, 1)
                
if __name__ == '__main__':
    unittest.main()
     
