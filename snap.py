import os
import requests
from flask import Flask, request, Response
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters

# قراءة التوكنات من Environment Variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
APP_URL = os.getenv("APP_URL")  # رابط الخدمة على Render، مثل https://your-app.onrender.com

if not TOKEN:
    raise ValueError("Environment variable TELEGRAM_TOKEN is not set.")
if not RAPIDAPI_KEY:
    raise ValueError("Environment variable RAPIDAPI_KEY is not set.")
if not APP_URL:
    raise ValueError("Environment variable APP_URL is not set.")

RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

bot = Bot(TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
app = Flask(__name__)

# /start command
async def start(update: Update, context):
    await update.message.reply_text("👋 أرسل رابط سناب شات وسأحمله لك 📥")

# التعامل مع الروابط
async def handle_url(update: Update, context):
    url = update.message.text.strip()

    endpoint = f"https://{RAPIDAPI_HOST}/download"
    querystring = {"url": url}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    try:
        response = requests.get(endpoint, headers=headers, params=querystring, timeout=30)
        data = response.json()
    except Exception as e:
        await update.message.reply_text(f"🚫 خطأ أثناء الاتصال بـ RapidAPI: {e}")
        return

    video_url = data.get("video") or data.get("media") or None
    if not video_url:
        await update.message.reply_text("🚫 لم أجد فيديو في الرابط، جرب رابط آخر.")
        return

    await update.message.reply_video(video_url)

# إضافة الHandlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

# Webhook route
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return Response("ok", status=200)

# ضبط الـ webhook عند التشغيل
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    url = f"{APP_URL}/webhook/{TOKEN}"
    success = bot.set_webhook(url)
    return f"Webhook set: {success}"

# Main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
