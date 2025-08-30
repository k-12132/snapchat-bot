import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# إعداد اللوقز
logging.basicConfig(level=logging.INFO)

# تحميل التوكن من المتغيرات
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ BOT_TOKEN مفقود في Environment Variables")

bot = Bot(token=TOKEN)

# Flask App
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Snapchat Bot is running!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Telegram Dispatcher
from telegram.ext import Updater
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# أوامر البوت
def start(update, context):
    update.message.reply_text("👋 أهلاً بك! أرسل لي رابط ستوري سناب شات.")

def echo(update, context):
    update.message.reply_text("📥 جاري معالجة الرابط...")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
