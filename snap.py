import os
import requests
from flask import Flask, request, Response
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# -------------------------
# قراءة المتغيرات من البيئة
# -------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
APP_URL = os.getenv("APP_URL")  # الرابط العام للخدمة على Render

if not TOKEN or not RAPIDAPI_KEY or not APP_URL:
    raise ValueError("Environment variables TELEGRAM_TOKEN, RAPIDAPI_KEY, APP_URL must be set")

RAPIDAPI_HOST = "download-snapchat-video-spotlight-online.p.rapidapi.com"

# -------------------------
# إنشاء Flask App و Bot
# -------------------------
app = Flask(__name__)
bot = Bot(TOKEN)

# -------------------------
# دوال البوت
# -------------------------
async def start(update: Update, context):
    """الرد على /start"""
    await update.message.reply_text("👋 أرسل رابط سناب شات وسأحمله لك 📥")

async def handle_url(update: Update, context):
    """معالجة روابط سناب شات"""
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
# إنشاء التطبيق
# -------------------------
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

# -------------------------
# Webhook route
# -------------------------
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    """
    هذا المسار يستقبل تحديثات Telegram عبر POST.
    لا تفتحه في المتصفح لأنه GET → Not Found طبيعي.
    """
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return Response("ok", status=200)

# -------------------------
# ضبط Webhook في Telegram
# -------------------------
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """
    افتح هذا الرابط في المتصفح مرة واحدة بعد النشر:
    https://YOUR_APP_URL/set_webhook
    ليتم تعيين Webhook في Telegram
    """
    url = f"{APP_URL}/webhook/{TOKEN}"
    success = bot.set_webhook(url)
    return f"Webhook set: {success}"

# -------------------------
# تشغيل Flask
# -------------------------
if __name__ == "__main__":
    # Render يعطي PORT تلقائيًا، لذلك نستخدمه
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
