from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from PyPDF2 import PdfReader

TOKEN = os.environ.get("TELEGRAM_TOKEN")

# 📚 جميع ملفات PDF في المشروع
PDF_FILES = [
    "book.pdf",
    "كتاب_الرياضيات_الجزء_الأول_الطبعة_2017_الصف_التاسع_اليمن.pdf",
    "كتاب_الرياضيات_الجزء_الثاني_الطبعة_2017_الصف_التاسع_اليمن.pdf",
    "كتاب_لغتي_العربية_الجزء_الأول_الطبعة_2026_الصف_التاسع_صنعاء_اليمن.pdf",
    "كتاب_لغتي_العربية_الجزء_الثاني_الطبعة_2023_للصف_التاسع_اليمن.pdf",
    "ملخص النحو اهداء صفحة المدرس بوك.pdf",
    "ملخص عربي صف تاسع( المعمري) (1).pdf"
]

# 📚 قراءة كل الكتب
def load_all_books():
    text = ""
    for file in PDF_FILES:
        try:
            reader = PdfReader(file)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return text.lower()

BOOK_TEXT = load_all_books()

# 🔍 بحث ذكي
def search(question):
    question = question.lower()
    lines = BOOK_TEXT.split("\n")

    results = []
    for line in lines:
        score = sum(1 for w in question.split() if w in line)
        if score > 0:
            results.append((score, line))

    results.sort(reverse=True, key=lambda x: x[0])

    if results:
        return "📚 من الكتب:\n\n" + "\n".join([r[1] for r in results[:7]])

    return "❌ لم أجد شرح واضح في الكتب، جرّب صياغة السؤال."

# 🚀 start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 أنا مدرسك من كل كتب التاسع اليمني\nاكتب سؤالك")

# 💬 رسائل
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(search(update.message.text))

def main():
    if not TOKEN:
        print("❌ TELEGRAM_TOKEN غير موجود")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("✅ BOT RUNNING (MULTI PDF)")
    app.run_polling()

if __name__ == "__main__":
    main()
