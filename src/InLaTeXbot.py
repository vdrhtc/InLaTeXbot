from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, \
    MessageHandler, Filters

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
        self._usersRequestedCustomPreambleRegistration.add(update.message.from_user.id)
        update.message.reply_text(self._resourceManager.getString("register_preamble"))
    
    def dispatchTextMessage(self, bot, messageUpdate):
        for messageFilter in self._messageFilters:
            messageUpdate = messageFilter(bot, messageUpdate)
            if messageUpdate is None:
                # Update consumed
                return
                
    def filterPreamble(self, bot, update):
        senderId = update.message.from_user.id
        if senderId in self._usersRequestedCustomPreambleRegistration:
            self.logger.debug("Filtered preamble text message")
            self.onPreambleArrived(bot, update)
        else:
            return update
    
    def onPreambleArrived(self, bot, update):
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
            
    def filterExpression(self, bot, update):
        # Always consumes, last filter
        self.logger.debug("Filtered expression text message")
        self.onExpressionArrived(bot, update)
    
    def onExpressionArrived(self, bot, update):
        self._messageQueryResponseDispatcher.dispatchMessageQueryResponse(update.message)
        
    def onSetCodeInCaptionOn(self, bot, update):
        userId  = update.message.from_user.id
        self._userOptionsManager.setCodeInCaptionOption(userId, True)
    
    def onSetCodeInCaptionOff(self, bot, update):
        userId = update.message.from_user.id
        self._userOptionsManager.setCodeInCaptionOption(userId, False)
    
    def onSetDpi(self, bot, update):
        userId = update.message.from_user.id
        try:
            dpi = int(update.message.text[8:])
            if not 100<=dpi<=1000:
                raise ValueError("Incorrect dpi value")
            self._userOptionsManager.setDpiOption(userId, dpi)
            update.message.reply_text(self._resourceManager.getString("dpi_set")%dpi)
        except ValueError:
            update.message.reply_text(self._resourceManager.getString("dpi_value_error"))
        
    def onInlineQuery(self, bot, update):
        if not update.inline_query.query:
            return
        self._inlineQueryResponseDispatcher.dispatchInlineQueryResponse(update.inline_query)
        
    def broadcastHTMLMessage(self, message):
        var = input("Are you sure? yes/[no]: ")
        if var != "yes":
            print("Aborting!")
            return
            
        for userId in self._usersManager.getKnownUsers():
            try:
                self._updater.bot.sendMessage(userId, message, parse_mode="HTML")
            except TelegramError as err:
                self.logger.warn("Could not broadcast message for %d, error: %s", userId, str(err))
            
if __name__ == '__main__':
    bot = InLaTeXbot()
    bot.launch()

