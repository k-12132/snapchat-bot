import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# توكن بوت تيليجرام
TOKEN = os.getenv("8063208023:AAEtS9ufEf452dsxxen0pfvLypG0k5miXJU")

# توكن RapidAPI
RAPIDAPI_KEY = os.getenv("e063166858msh759b8dd68f14471p1c86c8jsnc333e7700feb")

# معرف الـ Actor الخاص بتنزيل ستوري سناب
ACTOR_ID = "scrapearchitect/snapchat-spotlight-story-video-downloader-metadata-extractor"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً! أرسل رابط Story سناب شات وسأقوم بتحميله لك 📥")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    payload = {
        "video_urls": [url],
        "useKeyValueStore": False
    }
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY
    }

    resp = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?waitForFinish=true",
        headers=headers,
        json=payload
    ).json()

    items = resp.get("output", {}).get("items", [])
    if not items:
        await update.message.reply_text("🚫 لم أجد أي محتوى قابل للتحميل، تأكد من الرابط.")
        return

    item = items[0]
    videos = item.get("videos") or item.get("metadata", {}).get("medias", [])
    if not videos:
        await update.message.reply_text("🚫 لا يوجد فيديو في هذا الرابط.")
        return

    for media in videos:
        link = media if isinstance(media, str) else media.get("url")
        await update.message.reply_video(link)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()

if __name__ == "__main__":
    main()
