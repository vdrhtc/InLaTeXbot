from multiprocessing import Process, Lock, Event
from threading import Thread

from telegram import TelegramError
from telegram.error import NetworkError

from src.LoggingServer import LoggingServer

class MessageQueryResponseDispatcher():

    logger = LoggingServer.getInstance()
        
    def __init__(self, bot, latexConverter, resourceManager):
        self._bot = bot
        self._latexConverter = latexConverter
        self._resourceManager = resourceManager
            
    def dispatchMessageQueryResponse(self, message):
        
        self.logger.debug("Received message: "+message.text+\
                   ", id: "+str(message.message_id)+", from: "+str(message.chat.id))
                                
        responder = Process(target = self.respondToMessageQuery, args=[message])
        responder.start()
        Thread(target=self.joinProcess, args=[responder]).start()
            
    def joinProcess(self, process):
        process.join()

    def respondToMessageQuery(self, message):
        senderId = message.from_user.id
        chatId = message.chat.id
        messageId = message.message_id
        expression = message.text
        
        errorMessage = None
        try:
            imageStream, pdfStream = self._latexConverter.convertExpression(expression, senderId, str(messageId) + str(senderId), returnPdf=True)
            self._bot.sendDocument(chatId, pdfStream, filename="expression.pdf")
            self._bot.sendPhoto(chatId, imageStream)
        except ValueError as err:
            errorMessage = self.getWrongSyntaxResult(expression, err.args[0])
        except TelegramError as err:
            errorMessage = self._resourceManager.getString("telegram_error")+str(err)
            self.logger.warn(errorMessage)
        except Exception as err:
            self.logger.warn("Uncaught exception: " + str(err))
        finally:
            if not errorMessage is None:
                self._bot.sendMessage(chatId, errorMessage)
            self.logger.debug("Answered to message from %d, chatId %d, expression: %s", 
                                                        senderId, chatId, expression)
    
    def getWrongSyntaxResult(self, message, latexError):
        self.logger.debug("Wrong syntax in the message")
        errorMessage= self._resourceManager.getString("latex_syntax_error")
        return errorMessage+"\n"+latexError
        
