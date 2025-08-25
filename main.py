import os, re, json
import requests
from urllib.parse import quote
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========[ الإعدادات عبر متغيرات بيئة ]=========
# ضع توكن بوتك في المتغير TG_TOKEN (لا تكتبه صريحاً داخل الكود)
TG_TOKEN          = os.getenv("TG_TOKEN")              # مثال: 8063...:AAE...
RAPIDAPI_KEY      = os.getenv("RAPIDAPI_KEY")          # من RapidAPI
RAPIDAPI_HOST     = os.getenv("RAPIDAPI_HOST")         # مثل: download-snapchat-video-spotlight-online.p.rapidapi.com
# قالب الرابط الكامل من تبويب Code Snippets في RapidAPI:
# مثال شائع: https://download-snapchat-video-spotlight-online.p.rapidapi.com/?url={}
FULL_URL_TEMPLATE = os.getenv("FULL_URL_TEMPLATE")     # يجب أن يحتوي {} مكان عنوان السناب

assert TG_TOKEN and RAPIDAPI_KEY and RAPIDAPI_HOST and FULL_URL_TEMPLATE, "رجاءً اضبط متغيرات البيئة: TG_TOKEN, RAPIDAPI_KEY, RAPIDAPI_HOST, FULL_URL_TEMPLATE"

# =========[ أدوات مساعدة ]=========
URL_RE = re.compile(r'https?://\S+', re.IGNORECASE)

def find_media_urls(obj):
    """يستخرج أي روابط فيديو/صورة محتملة من JSON غير معروف الهيكل."""
    found = set()
    def walk(x):
        if isinstance(x, dict):
            for k,v in x.items():
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, str):
            s = x.strip()
            if s.startswith("http"):
                if any(ext in s.lower() for ext in [".mp4", ".mov", ".m4v", ".jpg", ".jpeg", ".png", ".gif"]):
                    found.add(s)
    walk(obj)
    return list(found)

def is_snap_url(text: str) -> bool:
    return "snapchat.com" in text.lower() or "story.snapchat.com" in text.lower()

# =========[ Handlers ]=========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "أهلًا 👋\n"
        "أرسل رابط ستوري أو Spotlight من سناب شات (من داخل سناب اضغط: Share Story → Copy Link) وسأحمله لك.\n\n"
        "مثال: https://story.snapchat.com/..."
    )
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط ستوري/Spotlight من سناب، وسأعيد لك الفيديو/الصور. إذا واجهت خطأ، جرّب رابطًا آخر.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # التحقق من وجود رابط
    m = URL_RE.search(text)
    if not m or not is_snap_url(m.group(0)):
        await update.message.reply_text("رجاءً أرسل **رابط ستوري/Spotlight من سناب** بعد نسخه من زر *Share Story* داخل التطبيق.")
        return

    snap_url = m.group(0)
    await update.message.chat.send_action("upload_video")

    # استدعاء RapidAPI
    try:
        full_url = FULL_URL_TEMPLATE.format(quote(snap_url, safe=":/?&=%"))
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
        }
        r = requests.get(full_url, headers=headers, timeout=40)

        # بعض واجهات RapidAPI قد ترجع مباشرة JSON برابط الفيديو، وأخرى قد تعيد الرابط مباشرة.
        media_urls = []
        ctype = r.headers.get("content-type", "").lower()
        if "application/json" in ctype:
            data = r.json()
            media_urls = find_media_urls(data)
        else:
            # لو أرجعت نص فيه رابط، حاول التقاط mp4 منه
            txt = r.text if hasattr(r, "text") else ""
            for u in re.findall(r'https?://\S+', txt):
                if any(u.lower().endswith(ext) for ext in [".mp4",".mov",".m4v",".jpg",".jpeg",".png",".gif"]):
                    media_urls.append(u)

        if not media_urls:
            await update.message.reply_text("لم أجد ملفًا مباشرًا للتحميل. جرّب رابطًا آخر أو أرسل ستوري مختلفة.")
            return

        # أرسل أول 3 ملفات فقط لتقليل الضغط
        sent = 0
        for url in media_urls:
            if url.lower().endswith((".jpg",".jpeg",".png",".gif")):
                await update.message.reply_photo(url)
            else:
                await update.message.reply_video(url)
            sent += 1
            if sent >= 3:
                break

        if len(media_urls) > sent:
            await update.message.reply_text(f"تم إرسال {sent} عنصر. يوجد عناصر إضافية ({len(media_urls)-sent})، أعطني أمرًا لو احتجتها كلها.")

    except requests.HTTPError as e:
        await update.message.reply_text(f"HTTP Error: {e}")
    except requests.RequestException:
        await update.message.reply_text("تعذّر الاتصال بخدمة التحميل. حاول لاحقًا.")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ غير متوقع: {e}")

def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
