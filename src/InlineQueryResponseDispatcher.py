import logging
from logging import Formatter
from logging.handlers import TimedRotatingFileHandler

from multiprocessing import Process, Lock, Event
from threading import Thread

from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, \
    MessageHandler, Filters



class InlineQueryResponseDispatcher():

    loggingHandler = TimedRotatingFileHandler(
        'log/inlatexbot.log', when="midnight", backupCount=1)
    loggingFormat = '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s'
    loggingFormatter = Formatter(fmt=loggingFormat, datefmt='%I:%M:%S')
    loggingHandler.setFormatter(loggingFormatter)
    logger = logging.getLogger('inlinequeryresponsedispatcher')
    logger.setLevel("DEBUG")
    logger.addHandler(loggingHandler)
    
    def __init__(self, bot, latexConverter, resourceManager, devnullChatId):
        self._bot = bot
        self._latexConverter = latexConverter
        self._resourceManager = resourceManager
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
        
        result = None
        try:
            expressionPngFileStream = self._latexConverter.convertExpressionToPng(expression, senderId, str(queryId)+str(senderId))
            if not nextQueryArrivedEvent.is_set():
                result = self.uploadImage(expressionPngFileStream, expression)
        except ValueError:
            result = self.getWrongSyntaxResult(expression)
        except TelegramError as err:
            errorMessage = self._resourceManager.getString("telegram_error")+str(err)
            logger.warn(errorMessage)
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
    
    def getWrongSyntaxResult(self, query):
        self.logger.debug("Wrong syntax in the query")
        errorMessage= self._resourceManager.getString("latex_syntax_error")
        return InlineQueryResultArticle(0, errorMessage, InputTextMessageContent(query))
            
    def uploadImage(self, image, expression):
        attempts = 0
        errorMessage = None
        
        while attempts < 3:
            try:
                latex_picture_id = self._bot.sendPhoto(self._devnullChatId, image).photo[0].file_id
                self.logger.debug("Image successfully uploaded for %s", expression)
                return InlineQueryResultCachedPhoto(0, photo_file_id=latex_picture_id)
            except TelegramError as err:
                errorMessage = self._resourceManager.getString("telegram_error")+str(err)
                logger.warn(errorMessage)

        return InlineQueryResultArticle(0, errorMessage, InputTextMessageContent(expression))
        
        
