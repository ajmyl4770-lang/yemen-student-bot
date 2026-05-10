from flask import Flask
import os
import requests
import threading
from PyPDF2 import PdfReader
from openai import OpenAI

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# 🔑 المفاتيح
TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

# 🌐 Flask
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "BOT IS RUNNING 🚀"

# 📚 الكتب
PDF_FILES = [
    "كتاب_الرياضيات_الجزء_الأول_الطبعة_2017_الصف_التاسع_اليمن.pdf",
    "كتاب_الرياضيات_الجزء_الثاني_الطبعة_2017_الصف_التاسع_اليمن.pdf",
    "كتاب_لغتي_العربية_الجزء_الأول_الطبعة_2026_الصف_التاسع_صنعاء_اليمن.pdf",
    "كتاب_لغتي_العربية_الجزء_الثاني_الطبعة_2023_للصف_التاسع_اليمن.pdf",
    "ملخص النحو اهداء صفحة المدرس بوك.pdf",
    "ملخص عربي صف تاسع( المعمري) (1).pdf"
]

# 📖 تحميل الكتب
def load_books():
    text = ""

    for file in PDF_FILES:
        try:
            reader = PdfReader(file)

            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"

        except Exception as e:
            print(f"خطأ في الملف {file}: {e}")

    return text[:12000]

BOOK_TEXT = load_books()

# 🤖 الذكاء الاصطناعي
def ask_ai(question):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content":
                    "أنت مدرس ذكي لطلاب اليمن. استخدم الكتب إن أمكن.\n\n"
                    + BOOK_TEXT
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print(e)
        return "❌ حدث خطأ"

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 البوت شغال")

# 💬 استقبال الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    await update.message.reply_text("⏳ جاري التفكير...")

    answer = ask_ai(user_text)

    await update.message.reply_text(answer)

# 🤖 تشغيل البوت
def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("🚀 BOT STARTED")

    app.run_polling()

# ▶️ تشغيل البوت في Thread
threading.Thread(target=run_bot).start()

# 🌐 تشغيل Flask
PORT = int(os.environ.get("PORT", 10000))

app_flask.run(host="0.0.0.0", port=PORT)
