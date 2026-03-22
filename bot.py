import logging
import feedparser
import threading
import http.server
import socketserver
from bs4 import BeautifulSoup
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרת לוגים - כדי שתוכל לראות ב-Render שהכל תקין
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- הגדרות סופיות ומעודכנות ---
TOKEN = "8708873598:AAH7CVVQdn65q4Iae0YeyYAssyFKw2A7154"
WEB_APP_URL = "https://farkash134-maker.github.io/Telegram_news_il/"

# מקורות RSS (נבדקו ותקינים)
RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

# שרת Health Check ל-Render (מונע שגיאת Port וקריסות)
def run_health_server():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            logging.info(f"Health check server active on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logging.error(f"Server error: {e}")

def clean_html(html_text):
    if not html_text: return ""
    return BeautifulSoup(html_text, "html.parser").get_text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת ה-start שיוצרת את כפתור המקלדת למעבר ל-Mini App"""
    web_app = WebAppInfo(url=WEB_APP_URL)
    kb = [[KeyboardButton("📰 בחר קטגוריית חדשות", web_app=web_app)]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    
    await update.message.reply_text(
        "שלום גלעד! ברוך הבא לבוט תקציר החדשות.\nלחץ על הכפתור למטה כדי לבחור נושא:",
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בנתונים שמגיעים מה-HTML לאחר לחיצה על כפתור"""
    category = update.effective_message.web_app_data.data
    logging.info(f"--- בקשה התקבלה לקטגוריה: {category} ---")
    
    url = RSS_FEEDS.get(category)
    if not url:
        await update.message.reply_text("מצטער, הקטגוריה לא נמצאה.")
        return

    status_msg = await update.message.reply_text(f"מושך עבורך עדכוני {category}... ⏳")

    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            await status_msg.edit_text("לא נמצאו כותרות חדשות כרגע.")
            return

        response = f"🗞️ **תקציר חדשות: {category}**\n\n"
        
        # הצגת 5 הידיעות האחרונות
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            desc = clean_html(entry.get('description', ''))
            short_desc = (desc[:110] + '...') if len(desc) > 110 else desc
            response += f"📌 **{title}**\n{short_desc}\n[לכתבה המלאה]({link})\n\n"

        await status_msg.delete()
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=False)
        
    except Exception as e:
        logging.error(f"Error fetching RSS: {e}")
        await status_msg.edit_text("חלה שגיאה במשיכת הנתונים. נסה שוב בעוד דקה.")

if __name__ == '__main__':
    # הרצת שרת הבריאות בשרשור נפרד
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # הקמת הבוט
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    logging.info("הבוט עולה ומנקה חיבורים קודמים...")
    
    # drop_pending_updates=True מבטיח שהבוט יתעלם מהודעות ישנות וישתלט על הקו
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
