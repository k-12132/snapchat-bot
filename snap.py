import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# قراءة المتغيرات من Environment Variables في Render
TOKEN = os.getenv("TOKEN")
APP_URL = os.getenv("APP_URL")  # لازم تضيفه في Render Dashboard → Environment
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

if not TOKEN or not APP_URL or not RAPIDAPI_KEY:
    raise ValueError("⚠️ Missing environment variables: TOKEN / APP_URL / RAPIDAPI_KEY")

# إنشاء تطبيق Flask
app = Flask(__name__)

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً! أرسل لي رابط ستوري سناب شات وسأحمّله لك 🎥")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "snapchat.com" not in url:
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح من سناب شات.")
        return

    api_url = f"https://{RAPIDAPI_HOST}/download"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    query = {"url": url}

    try:
        r = requests.get(api_url, headers=headers, params=query, timeout=15)
        r.raise_for_status()
        data = r.json()

        if "media" in data and data["media"]:
            video_url = data["media"][0]["url"]
            await update.message.reply_video(video_url)
        else:
            await update.message.reply_text("⚠️ لم أستطع العثور على الفيديو. جرب رابط آخر.")
    except Exception as e:
        await update.message.reply_text(f"🚨 حدث خطأ: {e}")

# بناء البوت
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

# ربط Flask مع Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok", 200

# تشغيل Webhook
@app.route("/setwebhook")
async def set_webhook():
    webhook_url = f"{APP_URL}/{TOKEN}"
    success = application.bot.set_webhook(webhook_url)
    return f"Webhook setup: {success}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
