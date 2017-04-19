from multiprocessing import Process, Lock, Event
from threading import Thread

from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, \
    MessageHandler, Filters

from src.LoggingServer import LoggingServer

class InlineQueryResponseDispatcher():

    logger = LoggingServer.getInstance()
    
    def __init__(self, bot, latexConverter, resourceManager, userOptionsManager, devnullChatId):
        self._bot = bot
        self._latexConverter = latexConverter
        self._resourceManager = resourceManager
        self._userOptionsManager = userOptionsManager
        self._devnullChatId = devnullChatId
        self._nextQueryArrivedEvents = {}
            
    def dispatchInlineQueryResponse(self, inline_query):
        
        self.logger.debug("Received inline query: "+inline_query.query+\
                                ", id: "+str(inline_query.id)+", from user: "+str(inline_query.from_user.id))
                                
        try:
            self._nextQueryArrivedEvents[inline_query.from_user.id].set()
            self._nextQueryArrivedEvents[inline_query.from_user.id] = Event()
        except KeyError:
            self._nextQueryArrivedEvents[inline_query.from_user.id] = Event()
            
        responder = Process(target = self.respondToInlineQuery, args=[inline_query, 
            self._nextQueryArrivedEvents[inline_query.from_user.id]])
        responder.start()
        Thread(target=self.joinProcess, args=[responder]).start()
            
    def joinProcess(self, process):
        process.join()

    def respondToInlineQuery(self, inline_query, nextQueryArrivedEvent):
        senderId = inline_query.from_user.id
        queryId = inline_query.id
        expression = inline_query.query
        
        caption = self.generateCaption(senderId, expression)
        
        result = None
        try:
            expressionPngFileStream = self._latexConverter.convertExpressionToPng(expression, senderId, str(queryId)+str(senderId))
            if not nextQueryArrivedEvent.is_set():
                result = self.uploadImage(expressionPngFileStream, expression, caption)
        except ValueError as err:
            result = self.getWrongSyntaxResult(expression, err.args[0])
        except TelegramError as err:
            errorMessage = self._resourceManager.getString("telegram_error")+str(err)
            self.logger.warn(errorMessage)
            result = InlineQueryResultArticle(0, errorMessage, InputTextMessageContent(expression))
        finally:
            if not self.skipForNewerQuery(nextQueryArrivedEvent, senderId, expression):
                self._bot.answerInlineQuery(queryId, [result], cache_time=0)
                self.logger.debug("Answered to inline query from %d, expression: %s", senderId, expression)
    
    def skipForNewerQuery(self, nextQueryArrivedEvent, senderId, expression):
        if nextQueryArrivedEvent.is_set():
            self.logger.debug("Skipped answering query from %d, expression: %s; newer query arrived", senderId, expression)
            return True
        return False
    
    def getWrongSyntaxResult(self, query, latexError):
        if len(query)>=250:
            self.logger.debug("Query may be too long")
            errorMessage= self._resourceManager.getString("inline_query_too_long")
        else:
            self.logger.debug("Wrong syntax in the query")
            errorMessage= self._resourceManager.getString("latex_syntax_error")
        return InlineQueryResultArticle(0, errorMessage, InputTextMessageContent(query), description = latexError)
            
    def uploadImage(self, image, expression, caption):
        attempts = 0
        errorMessage = None
        
        while attempts < 3:
            try:
                latex_picture_id = self._bot.sendPhoto(self._devnullChatId, image).photo[0].file_id
                self.logger.debug("Image successfully uploaded for %s", expression)
                return InlineQueryResultCachedPhoto(0, photo_file_id=latex_picture_id, caption = caption)
            except TelegramError as err:
                errorMessage = self._resourceManager.getString("telegram_error")+str(err)
                self.logger.warn(errorMessage)
                attempts += 1

        return InlineQueryResultArticle(0, errorMessage, InputTextMessageContent(expression))
    
    def generateCaption(self, senderId, expression):
        if self._userOptionsManager.getCodeInCaptionOption(senderId) is True:
            return expression[:200]
        else:
            return ""
    
        
