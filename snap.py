import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# قراءة التوكنات من Environment Variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# التأكد من وجود المتغيرات
if not TOKEN:
    raise ValueError("Environment variable TELEGRAM_TOKEN is not set.")
if not RAPIDAPI_KEY:
    raise ValueError("Environment variable RAPIDAPI_KEY is not set.")

# رابط RapidAPI (تأكد تستبدله بالـ Endpoint الصحيح من الـ API اللي اخترته في RapidAPI)
RAPIDAPI_URL = "https://snapchat-downloader.p.rapidapi.com/story"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً! أرسل رابط Story سناب شات وسأقوم بتحميله لك 📥")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    payload = {"url": url}
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "snapchat-downloader.p.rapidapi.com"
    }

    try:
        resp = requests.post(RAPIDAPI_URL, headers=headers, json=payload, timeout=60).json()
    except Exception as e:
        await update.message.reply_text(f"🚫 خطأ في الاتصال بـ RapidAPI: {e}")
        return

    # حسب الاستجابة من RapidAPI API (عدل المفتاح لو API مختلف)
    video_url = resp.get("video") or resp.get("download_url")
    if not video_url:
        await update.message.reply_text("🚫 لم أجد أي فيديو في الرابط، تأكد أنه صحيح.")
        return

    await update.message.reply_video(video_url)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()

if __name__ == "__main__":
    main()
