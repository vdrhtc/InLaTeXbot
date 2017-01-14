import logging
from logging import Formatter
from logging.handlers import TimedRotatingFileHandler

from multiprocessing import Process, Lock
from threading import Thread

from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, \
    MessageHandler, Filters

from src.LatexConverter import LatexConverter
from src.PreambleManager import PreambleManager
from src.ResourceManager import ResourceManager


class InLaTeXbot():

    loggingHandler = TimedRotatingFileHandler(
        'log/inlatexbot.log', when="midnight", backupCount=1)
    loggingFormat = '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s'
    loggingFormatter = Formatter(fmt=loggingFormat, datefmt='%I:%M:%S')
    loggingHandler.setFormatter(loggingFormatter)
    logger = logging.getLogger('inlatexbot')
    logger.setLevel("DEBUG")
    logger.addHandler(loggingHandler)

    def __init__(self, updater, devnullChatId=-1):

        self._updater = updater
        self._resourceManager = ResourceManager()
        self._preambleManager = PreambleManager(self._resourceManager)
        self._latexConverter = LatexConverter(self._preambleManager)
        self._devnullChatId = devnullChatId

        self._updater.dispatcher.add_handler(CommandHandler('start', self.onStart))
        self._updater.dispatcher.add_handler(CommandHandler('abort', self.onAbort))
        self._updater.dispatcher.add_handler(CommandHandler("help", self.onHelp))
        self._updater.dispatcher.add_handler(CommandHandler('setcustompreamble', self.onSetCustomPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getmypreamble', self.onGetMyPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getdefaultpreamble', self.onGetDefaultPreamble))

        inline_handler = InlineQueryHandler(self.onInlineQuery)
        self._updater.dispatcher.add_handler(inline_handler)
        
        self._userResponseHandler = None
        
    def launch(self):
        self._updater.start_polling()
        
    def stop(self):
        self._updater.stop()
    
    def onStart(self, bot, update):
        update.message.reply_text(self._resourceManager.getString("greeting_line_one"))
        with open("resources/demo.png", "rb") as f:
            self._updater.bot.sendPhoto(update.message.from_user.id, f)
        update.message.reply_text(self._resourceManager.getString("greeting_line_two"))

    def onAbort(self, bot, update):
        if self._userResponseHandler is None:
            update.message.reply_text(self._resourceManager.getString("nothing_to_abort"))
        else:
            self._updater.dispatcher.remove_handler(self._userResponseHandler, 1)
            self._userResponseHandler = None
            update.message.reply_text(self._resourceManager.getString("operation_aborted"))
    
    def onHelp(self, bot, update):
        with open("resources/available_commands.html", "r") as f:
            update.message.reply_text(f.read(), parse_mode="HTML")
        
    def onGetMyPreamble(self, bot, update):
        try:
            preamble = self._preambleManager.getPreambleFromDatabase(update.message.from_user.id)
            update.message.reply_text(self._resourceManager.getString("your_preamble_custom")+preamble)
        except KeyError:
            preamble = self._preambleManager.getDefaultPreamble()
            update.message.reply_text(self._resourceManager.getString("your_preamble_default")+preamble)
            
    def onGetDefaultPreamble(self, bot, update):
        preamble = self._preambleManager.getDefaultPreamble()
        update.message.reply_text(self._resourceManager.getString("default_preamble")+preamble)
    
    def onSetCustomPreamble(self, bot, update):
        self._userResponseHandler = MessageHandler(Filters.text, self.onPreambleArrived)
        self._updater.dispatcher.add_handler(self._userResponseHandler, 1)
        update.message.reply_text(self._resourceManager.getString("register_preamble"))
    
    def onPreambleArrived(self, bot, update):
        preamble = update.message.text
        update.message.reply_text(self._resourceManager.getString("checking_preamble"))
        valid, preamble_error_message = self._preambleManager.validatePreamble(preamble)
        if valid:
            self._preambleManager.putPreambleToDatabase(update.message.from_user.id, preamble)
            update.message.reply_text(self._resourceManager.getString("preamble_registered"))
            self._updater.dispatcher.remove_handler(self._userResponseHandler, 1)
            self._userResponseHandler = None
        else:
            update.message.reply_text(preamble_error_message)
        
    def onInlineQuery(self, bot, update):
        if not update.inline_query.query:
            return
        self.logger.debug("Received inline query: "+update.inline_query.query+\
                                ", id: "+str(update.inline_query.id)+", from user: "+str(update.inline_query.from_user.id))

        responder = Process(target = self.respondToInlineQuery, args=[update.inline_query])
        responder.start()
        Thread(target=self.joinProcess, args=[responder]).start()
        
    def respondToInlineQuery(self, inline_query):
        bot = self._updater.bot
        senderId = inline_query.from_user.id
        queryId = inline_query.id
        query = inline_query.query

        result = None
        try:
            expressionPngFileStream = self._latexConverter.convertExpressionToPng(query, senderId, str(queryId)+str(senderId))
            latex_picture_id = bot.sendPhoto(self._devnullChatId, expressionPngFileStream).photo[0].file_id
            self.logger.debug("Image successfully uploaded, id: "+latex_picture_id)
            result = InlineQueryResultCachedPhoto(0, photo_file_id=latex_picture_id)
        except ValueError:
            self.logger.debug("Wrong syntax in the query")
            errorMessage= self._resourceManager.getString("latex_syntax_error")
            result = InlineQueryResultArticle(0, errorMessage, InputTextMessageContent(query))
        except TelegramError as err:
            self.logger.error(err)
            errorMessage = self._resourceManager.getString("telegram_error")+str(err)
            result = InlineQueryResultArticle(0, errorMessage, InputTextMessageContent(query))
        finally:
            bot.answerInlineQuery(queryId, [result], cache_time=0)
            self.logger.debug("Answered to inline query %d, queryId: %s", senderId, queryId)
            
    def joinProcess(self, process):
        process.join()

            
if __name__ == '__main__':
    bot = InLaTeXbot()
    bot.launch()

