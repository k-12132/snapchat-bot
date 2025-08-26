import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# قراءة التوكنات من Environment Variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not TOKEN:
    raise ValueError("Environment variable TELEGRAM_TOKEN is not set.")
if not RAPIDAPI_KEY:
    raise ValueError("Environment variable RAPIDAPI_KEY is not set.")

RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أرسل رابط سناب شات وسأحمله لك 📥")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # التحقق من وجود رابط للفيديو
    video_url = data.get("video") or data.get("media") or None
    if not video_url:
        await update.message.reply_text("🚫 لم أجد فيديو في الرابط، جرب رابط آخر.")
        return

    await update.message.reply_video(video_url)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()

if __name__ == "__main__":
    main()
