import logging
import datetime
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from flask import Flask
from threading import Thread

# --- إعداد خادم بسيط لضمان بقاء الخدمة نشطة على Render ---
app = Flask('')
@app.route('/')
def home(): return "Makki Digital Clinic is Running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- إعدادات العيادة (د. محمد زاهر مكي) ---
TELEGRAM_TOKEN = '8333255779:AAF7Tszm4J-nNvQGPDqhTbm8tt8m6q9_sWA'
GEMINI_API_KEY = 'AIzaSyDLvwUXICkrVvNIf7p_VBpbLva1PzVLZSg'
ADMIN_ID = 8572108383 
ADMIN_USERNAME = "Zahermakki"
SHAM_CASH_ADDRESS = "992ca452c8cf0b99665c1f348de827d7"
SHAM_CASH_NUMBER = "0996481561"
DB_FILE = 'user_subscriptions.txt'

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
logging.basicConfig(level=logging.INFO)

def load_users():
    users = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            for line in f:
                try:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        users[int(parts[0])] = datetime.datetime.fromisoformat(parts[1])
                except: continue
    return users

def save_user(uid, expiry):
    users = load_users()
    users[uid] = expiry
    with open(DB_FILE, 'w') as f:
        for u_id, exp_date in users.items():
            f.write(f"{u_id},{exp_date.isoformat()},False\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_users()
    if user_id not in users:
        expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
        save_user(user_id, expiry)
        await update.message.reply_text("أهلاً بك في **عيادة مكي الرقمية** 🩺\nبإشراف الاستشاري **د. محمد زاهر مكي**\n\nتم تفعيل فترة تجريبية مجانية لمدة 24 ساعة لك.")
    else:
        await update.message.reply_text("أهلاً بك مجدداً في عيادتك الرقمية.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_users()
    now = datetime.datetime.now()
    is_active = (user_id == ADMIN_ID) or (user_id in users and now < users[user_id])

    if not is_active:
        keyboard = [[InlineKeyboardButton("إرسال إثبات التحويل", url=f"https://t.me/{ADMIN_USERNAME}")]]
        msg = f"💳 **تفاصيل الاشتراك:**\n\nقيمة الاشتراك: 50,000 ل.س شهرياً.\nالعنوان الرقمي: `{SHAM_CASH_ADDRESS}`"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        prompt = f"أنت مساعد طبي خبير في عيادة الدكتور محمد زاهر مكي. أجب بدقة طبية وباللغة العربية على: {update.message.text}"
        response = await asyncio.to_thread(model.generate_content, prompt)
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except:
        await update.message.reply_text("عذراً، يرجى المحاولة لاحقاً.")

async def activate_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        save_user(target_id, datetime.datetime.now() + datetime.timedelta(days=31))
        await update.message.reply_text(f"✅ تم تفعيل المستخدم {target_id}")
    except:
        await update.message.reply_text("الأمر: /activate [ID]")

if __name__ == '__main__':
    # تشغيل الخادم الوهمي لإبقاء Render مستيقظاً
    Thread(target=run_flask).start()
    
    # تشغيل البوت
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('activate', activate_user))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    
    print("🚀 العيادة الرقمية بدأت العمل على الخادم...")
    application.run_polling()
