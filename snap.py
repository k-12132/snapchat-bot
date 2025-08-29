import os
import requests
from flask import Flask, request, Response
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# قراءة التوكنات من Environment Variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
APP_URL = os.getenv("APP_URL")  # رابط الخدمة على Render

if not TOKEN or not RAPIDAPI_KEY or not APP_URL:
    raise ValueError("Environment variables TELEGRAM_TOKEN, RAPIDAPI_KEY, APP_URL must be set")

RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

app = Flask(__name__)
bot = Bot(TOKEN)

# Handlers
async def start(update: Update, context):
    await update.message.reply_text("👋 أرسل رابط سناب شات وسأحمله لك 📥")

async def handle_url(update: Update, context):
    url = update.message.text.strip()
    endpoint = f"https://{RAPIDAPI_HOST}/download"
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}
    params = {"url": url}

    try:
        res = requests.get(endpoint, headers=headers, params=params, timeout=30)
        data = res.json()
    except Exception as e:
        await update.message.reply_text(f"🚫 خطأ أثناء الاتصال بـ RapidAPI: {e}")
        return

    video_url = data.get("video") or data.get("media")
    if not video_url:
        await update.message.reply_text("🚫 لم أجد فيديو في الرابط، جرب رابط آخر.")
        return

    await update.message.reply_video(video_url)

# إنشاء التطبيق
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

# Webhook route
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return Response("ok", status=200)

# ضبط Webhook
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    url = f"{APP_URL}/webhook/{TOKEN}"
    success = bot.set_webhook(url)
    return f"Webhook set: {success}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
