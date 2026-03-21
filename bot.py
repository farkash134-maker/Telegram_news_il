import logging
import feedparser
import threading
import http.server
import socketserver
import time
from bs4 import BeautifulSoup
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרת לוגים - כדי שתוכל לראות ב-Render שהכל עובד
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- הגדרות סופיות ומעודכנות ---
TOKEN = "8708873598:AAFhsbaOaQ2AueSjxW0uBorO6ZiN-wOnedg"

# שים לב: כאן אתה חייב לשנות את your-username ו-your-repo ללינק האמיתי שלך מ-GitHub Pages
WEB_APP_URL = "https://your-username.github.io/your-repo/" 

# מקורות RSS של מעריב - נבדקו ותקינים לשימוש בישראל
RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

# --- שרת Health Check עבור Render (מונע קריסות של Port) ---
def run_health_check_server():
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            logging.info(f"Health check server running on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logging.error(f"Health server error: {e}")

def clean_html(html_text):
    if not html_text: return ""
    return BeautifulSoup(html_text, "html.parser").get_text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """יוצר את כפתור המקלדת הגדול שפותח את האפליקציה"""
    web_app = WebAppInfo(url=WEB_APP_URL)
    # יצירת כפתור מקלדת (חובה באייפון כדי ש-sendData יעבוד)
    kb = [[KeyboardButton("📰 בחר קטגוריית חדשות", web_app=web_app)]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "ברוך הבא לבוט תקציר חדשות ישראל! 🇮🇱\nלחץ על הכפתור למטה כדי לבחור נושא ולקבל את הכותרות האחרונות:",
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מטפל בנתונים שמגיעים מה-Mini App (למשל 'ספורט')"""
    category = update.effective_message.web_app_data.data
    logging.info(f"User requested category: {category}")
    
    feed_url = RSS_FEEDS.get(category)
    if not feed_url:
        await update.message.reply_text("מצטער, הקטגוריה לא נמצאה במערכת.")
        return

    # הודעת "טוען" ראשונית
    status_msg = await update.message.reply_text(f"מושך עבורך את עדכוני {category} האחרונים... ⏳")

    try:
        # קריאת ה-RSS
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            await status_msg.edit_text("לא נמצאו כותרות חדשות כרגע בפיד זה.")
            return

        response = f"🗞️ **תקציר חדשות: {category}**\n"
        response += "▬▬▬▬▬▬▬▬▬▬▬▬\n\n"

        # לוקח את 5 הידיעות האחרונות
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            desc = clean_html(entry.get('description', ''))
            # חיתוך התקציר לאורך אופטימלי לטלגרם
            short_desc = (desc[:130] + '...') if len(desc) > 130 else desc
            response += f"📌 **{title}**\n{short_desc}\n[לכתבה המלאה]({link})\n\n"

        # מחיקת הודעת הסטטוס ושליחת החדשות המעוצבות
        await status_msg.delete()
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=False)
    
    except Exception as e:
        logging.error(f"RSS processing error: {e}")
        await status_msg.edit_text("חלה שגיאה במשיכת הנתונים. נסה שוב בעוד כמה דקות.")

if __name__ == '__main__':
    # הפעלת שרת ה-Health Check בשרשור נפרד
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # אתחול האפליקציה של טלגרם
    app = Application.builder().token(TOKEN).build()
    
    # הוספת מטפלי פקודות והודעות
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    logging.info("הבוט רץ ומוכן לעבודה!")
    
    # הרצה - polling_timeout עוזר למנוע שגיאות Conflict ברשתות לא יציבות
    app.run_polling(poll_timeout=30)
