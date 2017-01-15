import unittest
from unittest.mock import Mock, MagicMock
from src.InLaTeXbot import InLaTeXbot
from time import sleep

class InLaTeXbotTest(unittest.TestCase):

    def setUp(self):
    
        self.bot = Mock()
        returnVal = Mock()
        photoVal = MagicMock()
        photoVal.file_id = "photo_file_id"
        returnVal.photo = [photoVal]
        self.bot.sendPhoto = Mock(return_value=returnVal)
        updater = Mock()
        updater.bot = self.bot
        
        self.sut = InLaTeXbot(updater)
        self.sut._preambleManager.putPreambleToDatabase = Mock()
        
    def testOnPreambleArrived(self):

        update = MagicMock()
        update.message.reply = Mock()
        update.message.text = Mock()
        update.message.text.__len__ = Mock(return_value = self.sut._resourceManager.getNumber("max_preamble_length")+1)
        self.sut.onPreambleArrived(self.bot, update)
        update.message.reply_text.assert_called_with(self.sut._resourceManager.getString("preamble_too_long")%self.sut._resourceManager.getNumber("max_preamble_length"))

    def testOnInlineQuery(self):
        self.sut._inlineQueryResponseDispatcher = Mock()
        self.sut._inlineQueryResponseDispatcher.dispatchInlineQueryResponse = Mock()
        update = MagicMock()
        update.inline_query.query = "$x^2$"
        update.inline_query.from_user.id = 1151
        update.inline_query.id = "id"
        self.sut.onInlineQuery(self.bot, update)
        self.sut._inlineQueryResponseDispatcher.dispatchInlineQueryResponse.assert_called_with(update.inline_query)
        
        
if __name__ == '__main__':
    unittest.main()
     
