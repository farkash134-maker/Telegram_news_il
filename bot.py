import logging
import feedparser
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרות לוגים כדי שנראה אם יש שגיאות
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- הגדרות ---
TOKEN = "כאן_שמים_את_הטוקן_מבאטפאדר"
# הלינק של ה-GitHub Pages שלך
WEB_APP_URL = "https://your-username.github.io/your-repo-name/" 

# מפות של לינקים ל-RSS (דוגמאות)
RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

# פונקציית התחלה
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("פתח אפליקציית חדשות", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("ברוכים הבאים לבוט החדשות! לחץ על הכפתור למטה כדי לבחור קטגוריה:", reply_markup=reply_markup)

# פונקציה שמקבלת את הבחירה מהאפליקציה (ה-index.html)
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # הנתון שנשלח מה-HTML (למשל "ספורט")
    category = update.effective_message.web_app_data.data
    feed_url = RSS_FEEDS.get(category)
    
    if feed_url:
        await update.message.reply_text(f"מושך עבורך את עדכוני {category} האחרונים...")
        feed = feedparser.parse(feed_url)
        
        # בניית הודעת התקציר (5 ידיעות אחרונות)
        summary = f"📢 **עדכוני {category} מהשעה האחרונה:**\n\n"
        for entry in feed.entries[:5]:
            summary += f"🔹 [{entry.title}]({entry.link})\n\n"
        
        await update.message.reply_text(summary, parse_mode='Markdown', disable_web_page_preview=False)
    else:
        await update.message.reply_text(f"קיבלתי את הבחירה '{category}', אך לא מצאתי מקור חדשות מתאים.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # מאזין לנתונים שמגיעים מה-Web App
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    print("הבוט רץ ומחכה לפקודות...")
    app.run_polling()

if __name__ == '__main__':
    main()
