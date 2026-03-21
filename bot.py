import logging
import feedparser
import threading
import http.server
import socketserver
from bs4 import BeautifulSoup
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרת לוגים למעקב ב-Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- הגדרות סופיות ומעודכנות ---
TOKEN = "8708873598:AAFhsbaOaQ2AueSjxW0uBorO6ZiN-wOnedg"

# הלינק המדויק לפי הרפוזיטורי שלך:
WEB_APP_URL = "https://farkash134-maker.github.io/Telegram_news_il/" 

RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

# שרת Health Check עבור Render (מונע Status 1)
def run_server():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            logging.info(f"Health server running on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logging.error(f"Server error: {e}")

def clean_html(html_text):
    if not html_text: return ""
    return BeautifulSoup(html_text, "html.parser").get_text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # יצירת כפתור מקלדת - חובה באייפון
    web_app = WebAppInfo(url=WEB_APP_URL)
    kb = [[KeyboardButton("📰 בחר קטגוריית חדשות", web_app=web_app)]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    
    await update.message.reply_text(
        "שלום! ברוך הבא לבוט תקציר החדשות.\nלחץ על הכפתור למטה כדי לפתוח את התפריט:",
        reply_markup=reply_markup
    )

async def handle_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.effective_message.web_app_data.data
    url = RSS_FEEDS.get(category)
    
    if url:
        msg = await update.message.reply_text(f"מושך חדשות בנושא {category}... ⏳")
        feed = feedparser.parse(url)
        
        res = f"🗞️ **תקציר חדשות: {category}**\n\n"
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            desc = clean_html(entry.get('description', ''))
            short_desc = (desc[:100] + '...') if len(desc) > 100 else desc
            res += f"📌 **{title}**\n{short_desc}\n[לכתבה המלאה]({link})\n\n"
            
        await msg.delete()
        await update.message.reply_text(res, parse_mode='Markdown', disable_web_page_preview=False)
    else:
        await update.message.reply_text("קטגוריה לא נמצאה.")

if __name__ == '__main__':
    # הפעלת שרת הבריאות בשרשור נפרד
    threading.Thread(target=run_server, daemon=True).start()
    
    # הפעלת הבוט
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_data))
    
    logging.info("הבוט רץ ומחכה לפקודות...")
    app.run_polling()
