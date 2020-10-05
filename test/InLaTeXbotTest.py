import unittest
from unittest.mock import Mock, MagicMock, call
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
        self.sut._usersManager = Mock()
        
    def testOnStart(self):
        self.sut._usersManager.getKnownUsers = Mock(return_value = {273230920})
    
        update = MagicMock()
        update.message.from_user.id = 273230920
        self.sut.onStart(self.bot, update)
        update.message.from_user.id = "lol"
        self.sut.onStart(self.bot, update)
        
    def testIncorrectPreambleRegistration(self):
    
        update = MagicMock()
        update.message.from_user.id = 115
        self.sut.onSetCustomPreamble(self.bot, update)

        update = MagicMock()
        update.message.text.__len__ = Mock(return_value = self.sut._resourceManager.getNumber("max_preamble_length")+1)
        update.message.from_user.id = 115
        
        self.sut.onPreambleArrived(self.bot, update)
        update.message.reply_text.assert_called_with(self.sut._resourceManager.getString("preamble_too_long")%self.sut._resourceManager.getNumber("max_preamble_length"))
        
        self.assertTrue(115 in self.sut._usersRequestedCustomPreambleRegistration)
        self.sut.onAbort(self.bot, update)
        self.assertFalse(115 in self.sut._usersRequestedCustomPreambleRegistration)
        
    def testCorrectPreambleRegistration(self):
    
        update = MagicMock()
        update.message.from_user.id = 115
        self.sut.onSetCustomPreamble(self.bot, update)
        
        self.sut.onSetCustomPreamble(self.bot, update)
    
        update = MagicMock()
        update.message.text = "\documentclass{article}"
        update.message.from_user.id = 115

        self.sut.onPreambleArrived(self.bot, update)
    
    def testDoublePreambleSetup(self):
        update = MagicMock()
        update.message.from_user.id = 115
        self.sut.onSetCustomPreamble(self.bot, update)
        self.sut.onSetCustomPreamble(self.bot, update)
        
        self.assertTrue(115 in self.sut._usersRequestedCustomPreambleRegistration)
        self.sut.onAbort(self.bot, update)
        self.assertFalse(115 in self.sut._usersRequestedCustomPreambleRegistration)
        
    def testPreambleSetupAndEventConsumed(self):
        self.sut.onPreambleArrived = Mock()
        self.sut.onExpressionArrived = Mock()
        update = MagicMock()
        update.message.from_user.id = 115
        self.sut.onSetCustomPreamble(self.bot, update)

        preamble = "TEST"
        update = Mock()
        message = Mock()
        message.text = preamble
        message.from_user.id = 115
        update.message = message
        
        self.sut.dispatchTextMessage(self.bot, update)
        self.assertTrue(self.sut.onPreambleArrived.called)
        self.assertFalse(self.sut.onExpressionArrived.called)

    def testOnInlineQuery(self):
        self.sut._inlineQueryResponseDispatcher = Mock()
        self.sut._inlineQueryResponseDispatcher.dispatchInlineQueryResponse = Mock()
        update = MagicMock()
        update.inline_query.query = "$x^2$"
        update.inline_query.from_user.id = 1151
        update.inline_query.id = "id"
        self.sut.onInlineQuery(self.bot, update)
        self.sut._inlineQueryResponseDispatcher.dispatchInlineQueryResponse.assert_called_with(update.inline_query)
        
    def testDispatchExpressionMessage(self):
        self.sut._messageQueryResponseDispatcher = Mock()

        expression = "TEST"
        update = Mock()
        message = Mock()
        message.text = expression
        update.message = message 
        
        self.sut.dispatchTextMessage(self.bot, update)
        
        self.sut._messageQueryResponseDispatcher.dispatchMessageQueryResponse.assert_called_with(message)


    def testBroadcasting(self):

        def wait(*args, **kwargs):
            sleep(1)

        self.sut._updater = MagicMock()
        self.sut._updater.bot = MagicMock()
        self.sut._updater.bot.sendMessage = MagicMock(side_effect = wait)

        m = "Test message: hello! Sorry, you were not supposed to recieve this..." \
            " I'm just trying something with broadcasting =)"

        self.sut.broadcastHTMLMessage(m, range(20), parse_mode="test", force=True)

        calls = [call(id, m, parse_mode = "test") for id in range(20)]

        self.sut._updater.bot.sendMessage.assert_has_calls(calls)
        
if __name__ == '__main__':
    unittest.main()
     
