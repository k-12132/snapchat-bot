import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask, request

# قراءة التوكن من متغير البيئة
TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

app = Flask(__name__)

# مثال أمر /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("أهلا! البوت يعمل الآن 🎉")

start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)

# لتشغيل البوت
if __name__ == "__main__":
    updater.start_polling()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
