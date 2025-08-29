import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not TOKEN or not RAPIDAPI_KEY:
    raise ValueError("Missing environment variables")

RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أرسل رابط سناب شات وسأحمله لك 📥")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()  # <-- يستخدم Polling فقط، لا حاجة لـ Updater أو Webhook

if __name__ == "__main__":
    main()
