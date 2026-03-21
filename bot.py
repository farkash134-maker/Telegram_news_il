import logging
import feedparser
from bs4 import BeautifulSoup
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרת לוגים לבדיקת תקלות ב-Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- שנה כאן את הפרטים שלך ---
TOKEN = "כאן_הטוקן_שלך_מבאטפאדר"
WEB_APP_URL = "https://your-username.github.io/your-repo/" 

# מקורות RSS (מעריב)
RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

def clean_html(html_text):
    if not html_text: return ""
    return BeautifulSoup(html_text, "html.parser").get_text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # יצירת כפתור מקלדת - חובה באייפון כדי ש-sendData יעבוד
    web_app = WebAppInfo(url=WEB_APP_URL)
    kb = [[KeyboardButton("📰 בחר קטגוריית חדשות", web_app=web_app)]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    
    await update.message.reply_text(
        "ברוך הבא! לחץ על הכפתור למטה כדי לפתוח את תפריט החדשות:",
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.effective_message.web_app_data.data
    feed_url = RSS_FEEDS.get(category)
    
    if not feed_url:
        await update.message.reply_text("קטגוריה לא נמצאה.")
        return

    status_msg = await update.message.reply_text(f"מושך חדשות בנושא {category}... ⏳")

    try:
        feed = feedparser.parse(feed_url)
        response = f"🗞️ **תקציר חדשות: {category}**\n\n"

        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            desc = clean_html(entry.get('description', ''))
            short_desc = (desc[:100] + '...') if len(desc) > 100 else desc
            response += f"📌 **{title}**\n{short_desc}\n[לכתבה המלאה]({link})\n\n"

        await status_msg.delete()
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=False)
    except Exception as e:
        await status_msg.edit_text("חלה שגיאה במשיכת הנתונים.")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.run_polling()
