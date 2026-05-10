import os
import time
import logging
import sqlite3
import threading

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from groq import Groq

# =========================
# 🔧 الإعدادات
# =========================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is missing")

if not GROQ_API_KEY:
    raise Exception("GROQ_API_KEY is missing")

client = Groq(api_key=GROQ_API_KEY)

FREE_LIMIT = 20
MAX_HISTORY = 8

# =========================
# 📚 قراءة الكتب
# =========================
BOOK_CONTENT = ""

try:
    with open("books.txt", "r", encoding="utf-8") as f:
        BOOK_CONTENT = f.read()

except:
    BOOK_CONTENT = "لا يوجد كتاب مرفوع حالياً"

# =========================
# 🗄 قاعدة البيانات
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    vip INTEGER DEFAULT 0,
    daily_count INTEGER DEFAULT 0,
    last_reset INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    role TEXT,
    content TEXT
)
""")

conn.commit()

# =========================
# 👤 وظائف المستخدم
# =========================
def create_user(user_id):

    cur.execute(
        "SELECT id FROM users WHERE id=?",
        (user_id,)
    )

    if not cur.fetchone():

        cur.execute(
            "INSERT INTO users VALUES (?, 0, 0, ?)",
            (user_id, int(time.time()))
        )

        conn.commit()

def get_user(user_id):

    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    return cur.fetchone()

def reset_if_needed(user_id):

    user = get_user(user_id)

    if user:

        last_reset = user[3]

        if time.time() - last_reset > 86400:

            cur.execute(
                "UPDATE users SET daily_count=0, last_reset=? WHERE id=?",
                (int(time.time()), user_id)
            )

            conn.commit()

# =========================
# 💬 الذاكرة
# =========================
def get_history(user_id):

    cur.execute(
        """
        SELECT role, content
        FROM messages
        WHERE user_id=?
        ORDER BY rowid DESC
        LIMIT ?
        """,
        (user_id, MAX_HISTORY)
    )

    rows = cur.fetchall()

    history = [
        {"role": row[0], "content": row[1]}
        for row in reversed(rows)
    ]

    return history

# =========================
# 🤖 رسالة النظام
# =========================
SYSTEM_PROMPT = f"""
أنت مساعد ذكي اسمه أبو جميل من مركز بن علي التكنولوجي.

مهمتك:
- الإجابة اعتماداً على الكتب المرفوعة.
- إذا وجدت الإجابة داخل الكتاب فأجب منها مباشرة.
- إذا لم تجد الإجابة قل:
لم أجد الإجابة داخل الكتب.

- أجب بالعربية بشكل مرتب وواضح.

محتوى الكتب:

{BOOK_CONTENT}
"""

# =========================
# 🤖 معالجة الرسائل
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    text = update.message.text

    create_user(user_id)
    reset_if_needed(user_id)

    user = get_user(user_id)

    # الحد المجاني
    if user[1] == 0 and user[2] >= FREE_LIMIT:

        await update.message.reply_text(
            "🚫 انتهى الحد المجاني اليوم.\n"
            "💎 اشترك VIP للاستمرار بدون حدود."
        )

        return

    try:

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        history = get_history(user_id)

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + history + [
            {
                "role": "user",
                "content": text
            }
        ]

        # طلب الذكاء
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
        )

        reply = response.choices[0].message.content.strip()

        # حفظ الرسائل
        cur.execute(
            "INSERT INTO messages VALUES (?, ?, ?)",
            (user_id, "user", text)
        )

        cur.execute(
            "INSERT INTO messages VALUES (?, ?, ?)",
            (user_id, "assistant", reply)
        )

        # زيادة العداد
        cur.execute(
            "UPDATE users SET daily_count = daily_count + 1 WHERE id=?",
            (user_id,)
        )

        conn.commit()

        # الرد
        await update.message.reply_text(
            f"📚 {reply}"
        )

    except Exception as e:

        logging.error(e)

        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء الاتصال."
        )

# =========================
# ▶️ start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 مرحباً بك في بوت أبو جميل\n\n📚 أرسل أي سؤال وسأجيبك من الكتب المرفوعة."
    )

# =========================
# 🌐 Flask
# =========================
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

def run_web():

    port = int(os.environ.get("PORT", 10000))

    web_app.run(
        host="0.0.0.0",
        port=port
    )

# =========================
# 🚀 تشغيل البوت
# =========================
def main():

    print("🚀 BOT STARTED")

    # تشغيل Flask
    threading.Thread(target=run_web).start()

    # تشغيل البوت
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )
    )

    app.run_polling()

# =========================
# ▶️ البداية
# =========================
if __name__ == "__main__":
    main()
