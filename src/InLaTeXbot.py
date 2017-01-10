from telegram.ext import Updater, CommandHandler, InlineQueryHandler, MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from src.LatexConverter import LatexConverter
from src.PreambleManager import PreambleManager


class InLaTeXbot():
    
    expressionPngFile = "expression.png"
    
    def __init__(self, token="", devnullChatId=-1):
        self._token = token
        self._updater = Updater(token)
        self._latexConverter = LatexConverter()
        self._preambleManager = PreambleManager()
        self._devnullChatId = devnullChatId

        self._updater.dispatcher.add_handler(CommandHandler('start', self.onStart))
        self._updater.dispatcher.add_handler(CommandHandler('abort', self.onAbort))
        self._updater.dispatcher.add_handler(CommandHandler("help", self.onHelp))
        self._updater.dispatcher.add_handler(CommandHandler('registerCustomPreamble', self.onRegisterCustomPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getMyPreamble', self.onGetMyPreamble))
        self._updater.dispatcher.add_handler(CommandHandler('getDefaultPreamble', self.onGetDefaultPreamble))
        

        inline_caps_handler = InlineQueryHandler(self.onInlineQuery)
        self._updater.dispatcher.add_handler(inline_caps_handler)
        
        self._messageHandler = None
    
    def launch(self):
        self._updater.start_polling()
        
    def stop(self):
        self._updater.stop()
         
    def onStart(self, bot, update):
        update.message.reply_text("Hi there! I'm an inline LaTeX bot, and I can help you to send cool pictures with LaTeX to any chat. Just call me from there and give me the code, like this:")
        with open("resources/demo.png", "rb") as f: 
            self._updater.bot.sendPhoto(update.message.from_user.id, f)
        update.message.reply_text("You can also type /help here to see list of available customization commands.")

    def onAbort(self, bot, update):
        if self._messageHandler is None:
            update.message.reply_text("Nothing to abort!")
        else:
            self._updater.dispatcher.remove_handler(self._messageHandler, 1)
            self._messageHandler = None
            update.message.reply_text("Operation aborted!")
    
    def onHelp(self, bot, update):
        with open("resources/available_commands.html", "r") as f:
            update.message.reply_text(f.read(), parse_mode="HTML")
    
    def onGetMyPreamble(self, bot, update):
        try:
            preamble = self._preambleManager.getPreambleFromDatabase(update.message.from_user.id)
            update.message.reply_text("Here is your custom preamble:\n"+preamble)
        except KeyError:
            preamble = self._preambleManager.getPreambleFromDatabase("default")
            update.message.reply_text("Your have the default preamble:\n"+preamble)
            
    def onGetDefaultPreamble(self, bot, update):
        preamble = self._preambleManager.getPreambleFromDatabase("default")
        update.message.reply_text("Here is the default preamble:\n"+preamble)
    
    def onRegisterCustomPreamble(self, bot, update):
        self._messageHandler = MessageHandler(Filters.text, self.onPreambleArrived)
        self._updater.dispatcher.add_handler(self._messageHandler, 1)
        update.message.reply_text("Great, then let's register a custom preamble for you. Just message me the code, and I'll deal with everything else.")
    
    def onPreambleArrived(self, bot, update):
        preamble = update.message.text
        update.message.reply_text("Cool. Let me check it...")
        if self._preambleManager.validatePreamble(preamble):
            self._preambleManager.putPreambleToDatabase(update.message.from_user.id, preamble)
            update.message.reply_text("Congratulations, your preamble is valid and now will be used for your queries.")
            self._updater.dispatcher.remove_handler(self._messageHandler, 1)
            self._messageHandler = None
        else:
            update.message.reply_text("Tough luck, it doesn't compile! Check your code!")
        
    def onInlineQuery(self, bot, update):
        query = update.inline_query.query
        senderId = update.inline_query.from_user.id
        if not query:
            return
        print("\rReceived query: "+query, end="")
        
        results = []
        
        try:
            self._latexConverter.setPreambleId(senderId)
            self._latexConverter.convertExpressionToPng(query)
            with open(self.expressionPngFile, "rb") as f:
                latex_picture_id = self._updater.bot.sendPhoto(self._devnullChatId, f).photo[0].file_id
            print("... image successfully uploaded, id: "+latex_picture_id, end="")
            
            results.append(InlineQueryResultCachedPhoto(id=0, photo_file_id=latex_picture_id))
            bot.answerInlineQuery(update.inline_query.id, results, cache_time=1)

        except ValueError:
            print("... wrong syntax in the query!", end="")
            results.append(InlineQueryResultArticle(id=0, title='Syntax error!', input_message_content=InputTextMessageContent(query)))
            bot.answerInlineQuery(update.inline_query.id, results)
            
        except TelegramError as err:
            print(err)
            results.append(InlineQueryResultArticle(id=0, title='Telegram error: '+str(err), input_message_content=InputTextMessageContent(query)))
            bot.answerInlineQuery(update.inline_query.id, results)
            
if __name__ == '__main__':
    bot = InLaTeXbot()
    bot.launch()

