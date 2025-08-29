import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# -------------------------
# قراءة التوكنات من البيئة
# -------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")       # توكن البوت من BotFather
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") # مفتاح RapidAPI

if not TOKEN or not RAPIDAPI_KEY:
    raise ValueError("Missing TELEGRAM_TOKEN or RAPIDAPI_KEY")

RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

# -------------------------
# دوال البوت
# -------------------------
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

# -------------------------
# إعداد البوت
# -------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()  # يستخدم Polling بدل Webhook لتشغيل مباشر

if __name__ == "__main__":
    main()
