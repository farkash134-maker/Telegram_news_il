import logging
import feedparser
import threading
import http.server
import socketserver
from bs4 import BeautifulSoup
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרת לוגים - חשוב כדי לראות ב-Render אם הנתונים מגיעים
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- הגדרות סופיות ---
TOKEN = "8708873598:AAFfTSBxGT0eZStlV_Kbf9wGT8O1MRE71Mo"

# שים לב: כאן אתה צריך לוודא שהלינק הוא הלינק שלך מ-GitHub Pages (איפה שנמצא ה-index.html)
# אם הלינק שלך שונה, פשוט תשנה את השורה הזו באייפון:
WEB_APP_URL = "https://your-username.github.io/your-repo/" 

# מקורות RSS של מעריב (נבדקו ותקינים)
RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

# --- שרת קטן כדי ש-Render לא יכבה את הבוט (חובה למסלול החינמי) ---
def run_health_check_server():
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    # מונע שגיאות אם הפורט תפוס לרגע
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        logging.info(f"Health check server running on port {PORT}")
        httpd.serve_forever()

def clean_html(html_text):
    if not html_text: return ""
    return BeautifulSoup(html_text, "html.parser").get_text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת ה-start שיוצרת את כפתור המקלדת"""
    web_app = WebAppInfo(url=WEB_APP_URL)
    # יצירת כפתור מקלדת (זהו הכפתור היחיד שמאפשר שליחת נתונים באייפון)
    kb = [[KeyboardButton("📰 בחר קטגוריית חדשות", web_app=web_app)]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    
    await update.message.reply_text(
        "ברוך הבא! לחץ על הכפתור למטה כדי לפתוח את תפריט החדשות ולבחור נושא:",
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פונקציה שרצה כשהמשתמש בוחר קטגוריה ב-HTML"""
    category = update.effective_message.web_app_data.data
    logging.info(f"משתמש בחר קטגוריה: {category}")
    
    feed_url = RSS_FEEDS.get(category)
    if not feed_url:
        await update.message.reply_text("מצטער, לא מצאתי את הקטגוריה הזו.")
        return

    # הודעת "טוען..."
    status_msg = await update.message.reply_text(f"מושך עבורך את עדכוני {category} האחרונים... ⏳")

    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            await status_msg.edit_text("לא נמצאו כותרות חדשות כרגע.")
            return

        response = f"🗞️ **תקציר חדשות: {category}**\n"
        response += "------------------------------\n\n"

        # לוקח את 5 הידיעות האחרונות מהפיד
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            desc = clean_html(entry.get('description', ''))
            # חיתוך התקציר לאורך נוח לקריאה בטלגרם
            short_desc = (desc[:120] + '...') if len(desc) > 120 else desc
            response += f"📌 **{title}**\n{short_desc}\n[לכתבה המלאה]({link})\n\n"

        # מחיקת הודעת הסטטוס ושליחת החדשות
        await status_msg.delete()
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=False)
    
    except Exception as e:
        logging.error(f"שגיאה במשיכת ה-RSS: {e}")
        await status_msg.edit_text("חלה שגיאה במשיכת הנתונים. נסה שוב מאוחר יותר.")

if __name__ == '__main__':
    # הפעלת שרת ה-Health Check בשרשור נפרד כדי ש-Render לא יכשיל את ה-Deploy
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # הפעלת הבוט בשיטה המודרנית
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # המאזין הקריטי לנתונים שמגיעים מה-Web App
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    logging.info("הבוט רץ ומחכה לפקודות...")
    app.run_polling()
