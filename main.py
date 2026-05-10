import os
import time
import logging
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

# =========================
# 🔧 إعدادات مركز بن علي
# =========================
logging.basicConfig(level=logging.INFO)

# التوكنات مباشرة لضمان عدم حدوث خطأ "مفقود"
BOT_TOKEN ="ادخل توكمن "
ادخل مفتاح هناGROQ_API_KEY =""
ADMIN_ID ="8629019996"

client = Groq(api_key=GROQ_API_KEY)

FREE_LIMIT = 20
MAX_HISTORY = 8

# =========================
# 🗄 قاعدة البيانات
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, vip INTEGER DEFAULT 0, daily_count INTEGER DEFAULT 0, last_reset INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (user_id TEXT, role TEXT, content TEXT)")
conn.commit()

# =========================
# 👤 وظائف المستخدم
# =========================
def create_user(user_id):
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES (?, 0, 0, ?)", (user_id, int(time.time())))
        conn.commit()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    return cur.fetchone()

def reset_if_needed(user_id):
    user = get_user(user_id)
    if user and time.time() - user[3] > 86400:
        cur.execute("UPDATE users SET daily_count=0, last_reset=? WHERE id=?", (int(time.time()), user_id))
        conn.commit()

# =========================
# 💬 الذاكرة والذكاء
# =========================
def get_history(user_id):
    cur.execute("SELECT role, content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?", (user_id, MAX_HISTORY))
    return list(reversed([{"role": r[0], "content": r[1]} for r in cur.fetchall()]))

SYSTEM_PROMPT = "أنت مساعد ذكي اسمه أبوجميل من مركز بن علي التكنولوجي. خبير في صيانة الهواتف والبطاريات."

# =========================
# 🤖 المعالجة
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    create_user(user_id)
    reset_if_needed(user_id)

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        history = get_history(user_id)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": text}]

        # استخدام الموديل الجديد والشغال
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
        cur.execute("INSERT INTO messages VALUES (?, 'user', ?), (?, 'assistant', ?)", (user_id, text, user_id, reply))
        cur.execute("UPDATE users SET daily_count = daily_count + 1 WHERE id=?", (user_id,))
        conn.commit()

        await update.message.reply_text(f"🤖 {reply}")
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("⚠️ خطأ في الاتصال، حاول مجدداً.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 مرحباً بك في بوت أبو جميل بمركز بن علي التكنولوجي!")

# =========================
# 🏁 التشغيل
# =========================
def main():
    print("🚀 BOT IS STARTING...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__":
    main()
