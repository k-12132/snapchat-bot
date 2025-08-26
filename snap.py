# snap.py
import os
import logging
import aiohttp
from aiohttp import ClientTimeout
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ---------- إعداد اللوق (اختياري لكن مفيد جداً) ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- قراءة المتغيرات البيئية ----------
TOKEN = os.getenv("TELEGRAM_TOKEN")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")  # نفضّل استخدام APIFY_TOKEN عند استدعاء actors على api.apify.com

# تحقق سريع (نمنع التشغيل إذا كانت المتغيرات مفقودة)
if not TOKEN:
    logger.error("TELEGRAM_TOKEN is not set.")
    raise RuntimeError("Environment variable TELEGRAM_TOKEN is not set.")
if not APIFY_TOKEN:
    logger.error("APIFY_TOKEN is not set.")
    raise RuntimeError("Environment variable APIFY_TOKEN is not set. (You must provide it to call Apify actor)")

# معرف الـ Actor على Apify
ACTOR_ID = "scrapearchitect/snapchat-spotlight-story-video-downloader-metadata-extractor"

# ---------- مساعد صغير لاستخراج رابط الفيديو من كائن media ----------
def extract_media_url(media):
    if isinstance(media, str):
        return media
    # بحث عن المفاتيح الشائعة التي قد تحمل رابط الفيديو
    for key in ("url", "downloadUrl", "directUrl", "src", "link"):
        v = media.get(key)
        if v:
            return v
    return None

# ---------- دالة تتصل بـ Apify (غير محجوزة - تعمل بشكل async) ----------
async def run_apify_actor(video_url: str, timeout_seconds: int = 60):
    endpoint = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
    params = {"waitForFinish": "true", "token": APIFY_TOKEN}

    payload = {"video_urls": [video_url], "useKeyValueStore": False}
    timeout = ClientTimeout(total=timeout_seconds)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(endpoint, params=params, json=payload) as resp:
            text = await resp.text()
            if resp.status >= 300:
                logger.error("Apify returned status %s: %s", resp.status, text)
                raise RuntimeError(f"Apify error: {resp.status} - {text[:200]}")
            try:
                data = await resp.json()
            except Exception as e:
                logger.exception("Failed to parse JSON from Apify response")
                raise RuntimeError(f"Invalid JSON from Apify: {e}; raw: {text[:200]}")
            return data

# ---------- أوامر البوت ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً! أرسل رابط Story سناب شات وسأقوم بتحميله لك 📥")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text.startswith("http"):
        await update.message.reply_text("❗ أرسل رابط صالح يبدأ بـ http أو https.")
        return

    msg = await update.message.reply_text("⏳ جاري معالجة الرابط — قد يستغرق هذا بعض الوقت...")
    try:
        data = await run_apify_actor(text, timeout_seconds=120)
    except Exception as e:
        logger.exception("Error calling Apify")
        await msg.edit_text(f"🚫 فشل الاتصال بخدمة التنزيل أو حدث خطأ: {e}")
        return

    # مسار الاشتقاق حسب شكل مخرجات Apify
    items = data.get("output", {}).get("items") if isinstance(data, dict) else None
    if not items:
        await msg.edit_text("🚫 لم أجد أي محتوى قابل للتحميل (Apify رجعت بلا نتائج).")
        return

    item = items[0] if len(items) else {}
    videos = item.get("videos") or item.get("metadata", {}).get("medias", [])
    if not videos:
        await msg.edit_text("🚫 لا يوجد فيديو في هذا الرابط وفق مخرجات Apify.")
        return

    sent_any = False
    for media in videos:
        link = extract_media_url(media)
        if not link:
            continue
        try:
            # جرب إرسال الفيديو كرابط (Telegram يدعم ذلك عادةً)
            await update.message.reply_video(link)
            sent_any = True
        except Exception as e:
            logger.exception("Failed to send video via URL, fallback to sending link")
            # لو فشل، أرسل الرابط كنص
            await update.message.reply_text(f"رابط الفيديو: {link}")

    if sent_any:
        await msg.edit_text("✅ تم إرسال الفيديو(هات) إن وُجِدَت.")
    else:
        await msg.edit_text("⚠️ لم أستطع إرسال أي فيديو، لكن ربما أرسلت الروابط كرسائل منفصلة.")

# ---------- نقطة الدخول ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()

if __name__ == "__main__":
    main()
