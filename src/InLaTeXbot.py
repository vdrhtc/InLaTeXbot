from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, \
    MessageHandler, Filters

from src.LatexConverter import LatexConverter
from src.PreambleManager import PreambleManager
from src.ResourceManager import ResourceManager
from src.InlineQueryResponseDispatcher import InlineQueryResponseDispatcher
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
        self._latexConverter = LatexConverter(self._preambleManager)
        self._inlineQueryResponseDispatcher = InlineQueryResponseDispatcher(updater.bot, self._latexConverter, self._resourceManager, self._userOptionsManager, devnullChatId)
        self._devnullChatId = devnullChatId

        self._updater.dispatcher.add_handler(CommandHandler('start', self.onStart))
        self._updater.dispatcher.add_handler(CommandHandler('abort', self.onAbort))
        self._updater.dispatcher.add_handler(CommandHandler("help", self.onHelp))
        self._updater.dispatcher.add_handler(CommandHandler('setcustompreamble', self.onSetCustomPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getmypreamble', self.onGetMyPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getdefaultpreamble', self.onGetDefaultPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('setcodeincaptionon', self.onSetCodeInCaptionOn))
        self._updater.dispatcher.add_handler(CommandHandler('setcodeincaptionoff', self.onSetCodeInCaptionOff))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.text, self.onPreambleArrived), 1)

        inline_handler = InlineQueryHandler(self.onInlineQuery)
        self._updater.dispatcher.add_handler(inline_handler)
        
        self._usersRequestedCustomPreambleRegistration = []
        
    def launch(self):
        self._updater.start_polling()
        
    def stop(self):
        self._updater.stop()
    
    def onStart(self, bot, update):
        senderId = update.message.from_user.id 
        if not senderId in self._usersManager.getKnownUsers():
            self._usersManager.setUser(senderId, {})
            self.logger.debug("Added a new user to database")
            
        update.message.reply_text(self._resourceManager.getString("greeting_line_one"))
        with open("resources/demo.png", "rb") as f:
            self._updater.bot.sendPhoto(update.message.from_user.id, f)
        update.message.reply_text(self._resourceManager.getString("greeting_line_two"))

    def onAbort(self, bot, update):
        senderId = update.message.from_user.id
        try:
            self._usersRequestedCustomPreambleRegistration.remove(senderId)
            update.message.reply_text(self._resourceManager.getString("preamble_registration_aborted"))            
        except ValueError:
            update.message.reply_text(self._resourceManager.getString("nothing_to_abort"))            
            
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
        self._usersRequestedCustomPreambleRegistration.append(update.message.from_user.id)
        update.message.reply_text(self._resourceManager.getString("register_preamble"))
    
    def onPreambleArrived(self, bot, update):
        senderId = update.message.from_user.id
        if senderId in self._usersRequestedCustomPreambleRegistration:
            preamble = update.message.text
            update.message.reply_text(self._resourceManager.getString("checking_preamble"))
            valid, preamble_error_message = self._preambleManager.validatePreamble(preamble)
            if valid:
                self.logger.debug("Registering preamble for user %d", senderId)
                self._preambleManager.putPreambleToDatabase(senderId, preamble)
                update.message.reply_text(self._resourceManager.getString("preamble_registered"))
                self._usersRequestedCustomPreambleRegistration.remove(senderId)
            else:
                update.message.reply_text(preamble_error_message)
        
    def onSetCodeInCaptionOn(self, bot, update):
        userId  = update.message.from_user.id
        self._userOptionsManager.setCodeInCaptionOption(userId, True)
    
    def onSetCodeInCaptionOff(self, bot, update):
        userId = update.message.from_user.id
        self._userOptionsManager.setCodeInCaptionOption(userId, False)
    
    def onInlineQuery(self, bot, update):
        if not update.inline_query.query:
            return
        self._inlineQueryResponseDispatcher.dispatchInlineQueryResponse(update.inline_query)
        
    def broadcastHTMLMessage(self, message):
        for userId in self._usersManager.getKnownUsers():
            try:
                self._updater.bot.sendMessage(userId, message, parse_mode="HTML")
            except TelegramError as err:
                self.logger.warn("Could not broadcast message for %d, error: %s", userId, str(err))
            
if __name__ == '__main__':
    bot = InLaTeXbot()
    bot.launch()

