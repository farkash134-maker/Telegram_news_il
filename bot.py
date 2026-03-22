import logging
import feedparser
import threading
import http.server
import socketserver
from bs4 import BeautifulSoup
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# לוגים ל-Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- הגדרות סופיות ---
TOKEN = "8708873598:AAFhsbaOaQ2AueSjxW0uBorO6ZiN-wOnedg"
WEB_APP_URL = "https://farkash134-maker.github.io/Telegram_news_il/"

RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

# שרת בריאות ל-Render (מונע Status 1)
def run_health_server():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

def clean_html(html):
    if not html: return ""
    return BeautifulSoup(html, "html.parser").get_text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # יצירת כפתור המקלדת - זהו הלב של המערכת!
    web_app = WebAppInfo(url=WEB_APP_URL)
    kb = [[KeyboardButton("📰 פתח תפריט חדשות", web_app=web_app)]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    
    await update.message.reply_text(
        "שלום! לחץ על הכפתור למטה (במקום המקלדת) כדי לבחור קטגוריה:",
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # כאן הבוט מקבל את המילה מה-HTML (למשל 'ספורט')
    category = update.effective_message.web_app_data.data
    logging.info(f"Received: {category}")
    
    url = RSS_FEEDS.get(category)
    if not url:
        await update.message.reply_text("קטגוריה לא נמצאה.")
        return

    msg = await update.message.reply_text(f"טוען עדכוני {category}... ⏳")
    
    try:
        feed = feedparser.parse(url)
        response = f"🗞️ **תקציר חדשות: {category}**\n\n"
        
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            desc = clean_html(entry.get('description', ''))
            short_desc = (desc[:100] + '...') if len(desc) > 100 else desc
            response += f"📌 **{title}**\n{short_desc}\n[לכתבה המלאה]({link})\n\n"
        
        await msg.delete()
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=False)
    except Exception as e:
        await msg.edit_text("שגיאה במשיכת הנתונים.")

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    # המאזין הקריטי ללחיצות בתוך האפליקציה
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    logging.info("Bot is running...")
    app.run_polling()
