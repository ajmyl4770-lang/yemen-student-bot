from flask import Flask, request
import os
import requests
from PyPDF2 import PdfReader
from openai import OpenAI

# 🔑 المفاتيح
TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# 📚 كتبك
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
        except:
            pass
    return text[:12000]

BOOK_TEXT = load_books()

# 🤖 ذكاء اصطناعي
def ask_ai(question):
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت مدرس ذكي لطلاب اليمن. استخدم الكتب إن أمكن."
                    + "\n\nالكتب:\n" + BOOK_TEXT
                },
                {"role": "user", "content": question}
            ]
        )
        return res.choices[0].message.content
    except:
        return "❌ خطأ في الذكاء الاصطناعي"

# 📤 إرسال رسالة
def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

# 🔥 Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        answer = ask_ai(text)
        send(chat_id, answer)

    except:
        pass

    return "ok"

# 🌐 اختبار السيرفر
@app.route("/")
def home():
    return "BOT IS RUNNING 🚀"

# 🚀 تشغيل السيرفر
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
