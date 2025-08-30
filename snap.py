import os
import logging
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# إعدادات اللوق
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل التوكنات من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

if not TOKEN or not RAPIDAPI_KEY:
    raise ValueError("❌ Missing environment variables: TOKEN or RAPIDAPI_KEY")

# إعداد البوت
bot = Bot(token=TOKEN)

# Flask app
app = Flask(__name__)

# Dispatcher
dispatcher = Dispatcher(bot, None, workers=0)

# أمر /start
def start(update: Update, context):
    update.message.reply_text("👋 مرحباً! أرسل رابط سناب شات وسأقوم بتحميل الفيديو لك.")

# معالجة الروابط
def handle_url(update: Update, context):
    url = update.message.text.strip()
    if "snapchat.com" not in url:
        update.message.reply_text("❌ أرسل رابط سناب شات صحيح.")
        return

    api_url = f"https://{RAPIDAPI_HOST}/download"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    params = {"url": url}

    try:
        res = requests.get(api_url, headers=headers, params=params, timeout=15)
        data = res.json()

        if "media" in data and len(data["media"]) > 0:
            video_url = data["media"][0]["url"]
            update.message.reply_video(video_url)
        else:
            update.message.reply_text("⚠️ لم أتمكن من جلب الفيديو. جرب رابط آخر.")
    except Exception as e:
        logger.error(f"خطأ: {e}")
        update.message.reply_text("❌ حدث خطأ أثناء جلب الفيديو.")

# ربط الأوامر بالبوت
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_url))

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/")
def home():
    return "✅ Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
