from concurrent.futures import ThreadPoolExecutor
from functools import partial
from time import sleep

from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, \
    MessageHandler, Filters, DispatcherHandlerStop
import html

from tqdm.notebook import tqdm

from src.LatexConverter import LatexConverter
from src.PreambleManager import PreambleManager
from src.ResourceManager import ResourceManager
from src.InlineQueryResponseDispatcher import InlineQueryResponseDispatcher
from src.MessageQueryResponseDispatcher import MessageQueryResponseDispatcher
from src.LoggingServer import LoggingServer
from src.UserOptionsManager import UserOptionsManager
from src.UsersManager import UsersManager

class InLaTeXbot():

    logger = LoggingServer.getInstance()

    def __init__(self, updater, devnullChatId=-1):

        self._updater = updater
        self._resourceManager = ResourceManager()
        self._userOptionsManager = UserOptionsManager()
        self._usersManager = UsersManager()
        self._preambleManager = PreambleManager(self._resourceManager)
        self._latexConverter = LatexConverter(self._preambleManager, self._userOptionsManager)
        self._inlineQueryResponseDispatcher = InlineQueryResponseDispatcher(updater.bot, self._latexConverter, self._resourceManager, self._userOptionsManager, devnullChatId)
        self._messageQueryResponseDispatcher = MessageQueryResponseDispatcher(updater.bot, self._latexConverter, self._resourceManager)
        self._devnullChatId = devnullChatId
        self._messageFilters = []

        self._updater.dispatcher.add_handler(CommandHandler('start', self.onStart))
        self._updater.dispatcher.add_handler(CommandHandler('abort', self.onAbort))
        self._updater.dispatcher.add_handler(CommandHandler("help", self.onHelp))
        self._updater.dispatcher.add_handler(CommandHandler('setcustompreamble', self.onSetCustomPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getmypreamble', self.onGetMyPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getdefaultpreamble', self.onGetDefaultPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('setcodeincaptionon', self.onSetCodeInCaptionOn))
        self._updater.dispatcher.add_handler(CommandHandler('setcodeincaptionoff', self.onSetCodeInCaptionOff))
        self._updater.dispatcher.add_handler(CommandHandler("setdpi", self.onSetDpi))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.text, self.dispatchTextMessage), 1)
        
        self._messageFilters.append(self.filterPreamble)
        self._messageFilters.append(self.filterExpression)
        
        inline_handler = InlineQueryHandler(self.onInlineQuery)
        self._updater.dispatcher.add_handler(inline_handler)
        
        self._usersRequestedCustomPreambleRegistration = set()

        self._executor = ThreadPoolExecutor(max_workers=32)

        
    def launch(self):
        self._updater.start_polling()
        
    def stop(self):
        self._updater.stop()
    
    def onStart(self, update, context):
        senderId = update.message.from_user.id 
        if not senderId in self._usersManager.getKnownUsers():
            self._usersManager.setUser(senderId, {})
            self.logger.debug("Added a new user to database")
            
        update.message.reply_text(self._resourceManager.getString("greeting_line_one"))
        with open("resources/demo.png", "rb") as f:
            self._updater.bot.sendPhoto(update.message.from_user.id, f)
        update.message.reply_text(self._resourceManager.getString("greeting_line_two"))

        raise DispatcherHandlerStop

    def onAbort(self, update, context):
        senderId = update.message.from_user.id
        try:
            self._usersRequestedCustomPreambleRegistration.remove(senderId)
            update.message.reply_text(self._resourceManager.getString("preamble_registration_aborted"))            
        except KeyError:
            update.message.reply_text(self._resourceManager.getString("nothing_to_abort"))

        raise DispatcherHandlerStop
            
    def onHelp(self, update, context):
        with open("resources/available_commands.html", "r") as f:
            update.message.reply_text(f.read(), parse_mode="HTML")

        raise DispatcherHandlerStop
        
    def onGetMyPreamble(self, update, context):
        try:
            preamble = self._preambleManager.getPreambleFromDatabase(update.message.from_user.id)
            update.message.reply_text(self._resourceManager.getString("your_preamble_custom")+preamble)
        except KeyError:
            preamble = self._preambleManager.getDefaultPreamble()
            update.message.reply_text(self._resourceManager.getString("your_preamble_default")+preamble)

        raise DispatcherHandlerStop
            
    def onGetDefaultPreamble(self, update, context):
        preamble = self._preambleManager.getDefaultPreamble()
        update.message.reply_text(self._resourceManager.getString("default_preamble")+preamble)

        raise DispatcherHandlerStop
    
    def onSetCustomPreamble(self, update, context):
        self._usersRequestedCustomPreambleRegistration.add(update.message.from_user.id)
        update.message.reply_text(self._resourceManager.getString("register_preamble"))

        raise DispatcherHandlerStop
    
    def dispatchTextMessage(self, messageUpdate, context):
        for messageFilter in self._messageFilters:
            messageUpdate = messageFilter(messageUpdate, context)
            if messageUpdate is None:
                # Update consumed
                raise DispatcherHandlerStop
                
    def filterPreamble(self, update, context):
        senderId = update.message.from_user.id
        if senderId in self._usersRequestedCustomPreambleRegistration:
            self.logger.debug("Filtered preamble text message")
            self.onPreambleArrived(update, context)
        else:
            return update
    
    def onPreambleArrived(self, update, context):
        preamble = update.message.text
        senderId = update.message.from_user.id
        update.message.reply_text(self._resourceManager.getString("checking_preamble"))
        valid, preamble_error_message = self._preambleManager.validatePreamble(preamble)
        if valid:
            self.logger.debug("Registering preamble for user %d", senderId)
            self._preambleManager.putPreambleToDatabase(senderId, preamble)
            update.message.reply_text(self._resourceManager.getString("preamble_registered"))
            self._usersRequestedCustomPreambleRegistration.remove(senderId)
        else:
            update.message.reply_text(preamble_error_message)
            
    def filterExpression(self, update, context):
        # Always consumes, last filter
        self.logger.debug("Filtered expression text message")
        self.onExpressionArrived(update, context)
    
    def onExpressionArrived(self, update, context):
        self._messageQueryResponseDispatcher.dispatchMessageQueryResponse(update.message)
        
    def onSetCodeInCaptionOn(self, update, context):
        userId  = update.message.from_user.id
        self._userOptionsManager.setCodeInCaptionOption(userId, True)

        raise DispatcherHandlerStop
    
    def onSetCodeInCaptionOff(self, update, context):
        userId = update.message.from_user.id
        self._userOptionsManager.setCodeInCaptionOption(userId, False)

        raise DispatcherHandlerStop

    def onSetDpi(self, update, context):
        userId = update.message.from_user.id
        try:
            dpi = int(update.message.text[8:])
            if not 100<=dpi<=1000:
                raise ValueError("Incorrect dpi value")
            self._userOptionsManager.setDpiOption(userId, dpi)
            update.message.reply_text(self._resourceManager.getString("dpi_set")%dpi)
        except ValueError:
            update.message.reply_text(self._resourceManager.getString("dpi_value_error"))

        raise DispatcherHandlerStop
        
    def onInlineQuery(self, update, context):
        if not update.inline_query.query:
            return
        update.inline_query.query = html.unescape(update.inline_query.query)
        update.inline_query.query = update.inline_query.query.replace("<br/>", "\n")
        self._inlineQueryResponseDispatcher.dispatchInlineQueryResponse(update.inline_query)

        raise DispatcherHandlerStop
        
    def broadcastHTMLMessage(self, message, userIds, parse_mode="HTML", force = False):
        if not force:
            print(message)
            var = input("Are you sure? yes/[no]: ")
            if var != "yes":
                print("Aborting!")
                return

        send_task = partial(self._sendMessageToUser, message = message, parse_mode=parse_mode)
        for userId in tqdm(self._executor.map(send_task, userIds), total=len(userIds), smoothing=0):
            if userId > 0:
                self.logger.debug("Broadcast message successfully for user %d"%userId)
            else:
                self.logger.debug("Failed to broadcast message for user %d"%-userId)


    def _sendMessageToUser(self, userId, message, parse_mode = "HTML"):
        attempt = 0
        while attempt < 10:
            try:
                self._updater.bot.sendMessage(userId, message, parse_mode=parse_mode)
                return userId
            except TelegramError as err:
                attempt += 1
                self.logger.warn("Could not broadcast message for %d, error: %s", userId, str(err))
                sleep(15)
        return -userId


if __name__ == '__main__':
    bot = InLaTeXbot()
    bot.launch()

