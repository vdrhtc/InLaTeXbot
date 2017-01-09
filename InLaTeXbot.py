from telegram.ext import Updater, CommandHandler, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultCachedPhoto, InlineQueryResult, TelegramError
from LatexConverter import LatexConverter


class InLaTeXbot():

    def __init__(self, token="", devnullChatId=-1):
        self._token = token
        self._updater = Updater(token)
        self._latexConverter = LatexConverter()
        self._devnullChatId = devnullChatId

        self._updater.dispatcher.add_handler(CommandHandler('start', self.onStart))

        inline_caps_handler = InlineQueryHandler(self.onInlineQuery)
        self._updater.dispatcher.add_handler(inline_caps_handler)
    
    def launch(self):
        self._updater.start_polling()
        
    def stop(self):
        self._updater.stop()
         
    def onStart(self, bot, update):
        update.message.reply_text("Hi there! I'm LaTeX bot, so I can create cool pictures with mathematical formulas from the latex expressions you give me. Make sure to try my inline mode by mentioning me in any other chat like this: @inlatexbot")
        update.message.reply

    def onInlineQuery(self, bot, update):
        query = update.inline_query.query    
        if not query:
            return
        print("\rReceived query: "+query, end="")
            
        results = []
        expressionPngFile = "expression.png"
        
        try:
            self._latexConverter.convertExpressionToPng(query)
            with open(expressionPngFile, "rb") as f:
                latex_picture_id = self._updater.bot.sendPhoto(self._devnullChatId, f).photo[0].file_id
            print("... image successfully uploaded, id: "+latex_picture_id, end="")
            
            results.append(InlineQueryResultCachedPhoto(id=0, title='Your expression', photo_file_id=latex_picture_id))
            bot.answerInlineQuery(update.inline_query.id, results, cache_time=1)

        except ValueError:
            print("... wrong syntax in the query!", end="")
            results.append(InlineQueryResultArticle(id=0, title='Syntax error!', input_message_content=InputTextMessageContent(query)))
            bot.answerInlineQuery(update.inline_query.id, results)
            
        except TelegramError as err:
            print(err)
            
if __name__ == '__main__':
    bot = InLaTeXbot()
    bot.launch()

