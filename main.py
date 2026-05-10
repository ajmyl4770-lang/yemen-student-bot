from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from PyPDF2 import PdfReader

TOKEN = os.environ.get("TELEGRAM_TOKEN")

PDF_FILE = "book.pdf"  # ضع ملفك هنا

# 📚 قراءة PDF
def read_pdf():
    text = ""
    try:
        reader = PdfReader(PDF_FILE)
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
    except Exception as e:
        return ""
    return text.lower()

BOOK_TEXT = read_pdf()

# 🔍 بحث داخل الكتاب
def search(question):
    question = question.lower()
    sentences = BOOK_TEXT.split("\n")

    results = []
    for s in sentences:
        score = sum(1 for w in question.split() if w in s)
        if score > 0:
            results.append((score, s))

    results.sort(reverse=True, key=lambda x: x[0])

    if results:
        return "📚 من الكتاب:\n\n" + "\n".join([r[1] for r in results[:5]])

    return "❌ ما لقيت شرح داخل الكتاب، جرّب تسأل بطريقة أوضح."

# 🚀 start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 أهلاً بك، اكتب سؤالك من الكتاب")

# 💬 رسائل
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = search(update.message.text)
    await update.message.reply_text(answer)

def main():
    if not TOKEN:
        print("❌ TELEGRAM_TOKEN غير موجود")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("✅ BOT RUNNING WITH PDF")
    app.run_polling()

if __name__ == "__main__":
    main()
