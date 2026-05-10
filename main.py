import os
import time
import logging
import sqlite3

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
# 🔧 إعدادات البوت
# =========================
logging.basicConfig(level=logging.INFO)

# توكن البوت
BOT_TOKEN = "ضع_توكن_البوت_هنا"

# مفتاح Groq
GROQ_API_KEY = "ضع_مفتاح_GROQ_هنا"

# ايدي الأدمن
ADMIN_ID = "8629019996"

# تشغيل عميل Groq
client = Groq(api_key=GROQ_API_KEY)

FREE_LIMIT = 20
MAX_HISTORY = 8

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
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users VALUES (?, 0, 0, ?)",
            (user_id, int(time.time()))
        )
        conn.commit()


def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
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
SYSTEM_PROMPT = """
أنت مساعد ذكي اسمه أبو جميل من مركز بن علي التكنولوجي.
خبير في صيانة الهواتف والبطاريات والذكاء الصناعي.
ترد بالعربية بشكل احترافي ومختصر.
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

    # التحقق من الحد المجاني
    if user[1] == 0 and user[2] >= FREE_LIMIT:
        await update.message.reply_text(
            "🚫 انتهى الحد المجاني اليوم.\n"
            "💎 اشترك VIP للاستمرار بدون حدود."
        )
        return

    try:
        # حالة الكتابة
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # سجل المحادثة
        history = get_history(user_id)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + history + [
            {"role": "user", "content": text}
        ]

        # طلب الذكاء
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
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
        await update.message.reply_text(f"🤖 {reply}")

    except Exception as e:
        logging.error(e)

        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء الاتصال."
        )

# =========================
# ▶️ /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 مرحباً بك في بوت أبو جميل بمركز بن علي التكنولوجي!"
    )

# =========================
# 🚀 تشغيل البوت
# =========================
def main():

    print("🚀 BOT IS STARTING...")

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
# 🏁 البداية
# =========================
if __name__ == "__main__":
    main()
