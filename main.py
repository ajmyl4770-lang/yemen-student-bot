from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")

# 📚 تحميل الكتب من ملف
def load_books():
    try:
        with open("books.txt", "r", encoding="utf-8") as f:
            return f.read().lower()
    except:
        return ""

BOOKS_DATA = load_books()

# 🤖 البحث داخل الكتب
def search_answer(question):
    question = question.lower()

    # تقسيم بسيط حسب الجمل
    sentences = BOOKS_DATA.split("\n")

    results = []
    for s in sentences:
        if any(word in s for word in question.split()):
            results.append(s)

    if results:
        return "📚 من الكتب:\n\n" + "\n".join(results[:5])

    return "❌ ما لقيت شرح واضح في الكتب، حاول تسأل بطريقة أبسط."

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 أهلاً بك في بوت المدرّس\n"
        "اكتب سؤالك وأنا أشرح لك من الكتب"
    )

# 💬 الردود
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    answer = search_answer(user_text)
    await update.message.reply_text(answer)

def main():
    if not TOKEN:
        print("❌ TELEGRAM_TOKEN غير موجود في Render")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
