import logging
import feedparser
import threading
import http.server
import socketserver
from bs4 import BeautifulSoup
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8708873598:AAFhsbaOaQ2AueSjxW0uBorO6ZiN-wOnedg"
WEB_APP_URL = "https://farkash134-maker.github.io/Telegram_news_il/"

RSS_FEEDS = {
    "חדשות": "https://www.maariv.co.il/rss/rsschadashot",
    "כלכלה": "https://www.maariv.co.il/rss/rssfeedsasakim",
    "ספורט": "https://www.maariv.co.il/rss/rssfeedssport",
    "תרבות": "https://www.maariv.co.il/rss/rssfeedstarbot"
}

def run_health_server():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

def clean_html(html_text):
    if not html_text: return ""
    return BeautifulSoup(html_text, "html.parser").get_text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    web_app = WebAppInfo(url=WEB_APP_URL)
    kb = [[KeyboardButton("📰 פתח תפריט חדשות", web_app=web_app)]]
    await update.message.reply_text("ברוך הבא! בחר קטגוריה:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # קבלת הנתון
    category = update.effective_message.web_app_data.data
    logging.info(f"--- קיבלתי בקשה לקטגוריה: {category} ---")
    
    status_msg = await update.message.reply_text(f"מעבד את עדכוני {category}... ⏳")
    
    url = RSS_FEEDS.get(category)
    if not url:
        await status_msg.edit_text("קטגוריה לא נמצאה.")
        return

    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            await status_msg.edit_text("לא נמצאו חדשות כרגע בפיד.")
            return

        response = f"🗞️ **תקציר חדשות: {category}**\n\n"
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            desc = clean_html(entry.get('description', ''))
            short_desc = (desc[:100] + '...') if len(desc) > 100 else desc
            response += f"📌 **{title}**\n{short_desc}\n[לכתבה המלאה]({link})\n\n"
        
        # ניסיון שליחה
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=False)
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Error detail: {e}")
        await status_msg.edit_text(f"חלה שגיאה: {str(e)[:50]}")

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    logging.info("הבוט רץ...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
