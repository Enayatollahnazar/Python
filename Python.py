import os
import nest_asyncio
import requests
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# دریافت مقادیر از متغیرهای محیطی برای امنیت بیشتر
MISTRAL_API_KEY = os.getenv("4vr72zG1enG9N53cBsDaW9PMbBQ5HeIW")
TELEGRAM_BOT_TOKEN = os.getenv("7221996894:AAHPhpADZ4y2wVNPHcpWE1JgBYnD_ip5Kis")
CHANNEL_USERNAME = "Ravan_Shinasi"

# ذخیره تاریخچه چت و وضعیت کاربران
user_chat_history = {}
user_message_count = {}
unlimited_users = {}

# بررسی عضویت در کانال
async def is_user_subscribed(user_id, context):
    try:
        chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# منوی اصلی
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("💬 چت با هوش مصنوعی", callback_data="chat_with_ai")],
        [InlineKeyboardButton("🚀 ارتقای حساب", callback_data="upgrade_account")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔹 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)

# مدیریت دکمه‌های ربات
async def button(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "support":
        keyboard = [[InlineKeyboardButton("🔙 برگشت به منو اصلی", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("📞 برای پشتیبانی به آیدی زیر پیام دهید:\n@rahmatedit", reply_markup=reply_markup)

    elif query.data == "chat_with_ai":
        user_chat_history.setdefault(user_id, [])
        user_message_count.setdefault(user_id, 0)
        keyboard = [[InlineKeyboardButton("🔙 برگشت به منو اصلی", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("💬 حالا می‌توانید پیام خود را ارسال کنید.", reply_markup=reply_markup)

    elif query.data == "upgrade_account":
        keyboard = [
            [InlineKeyboardButton("📆 اشتراک ماهانه - ۳۰ هزار تومان", callback_data="subscribe_1")],
            [InlineKeyboardButton("📆 اشتراک سه‌ماهه - ۷۰ هزار تومان", callback_data="subscribe_3")],
            [InlineKeyboardButton("📆 اشتراک ۱۲ ماهه - ۲۰۰ هزار تومان", callback_data="subscribe_12")],
            [InlineKeyboardButton("🔙 برگشت به منو اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("💳 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)

    elif query.data.startswith("subscribe_"):
        sub_type = query.data.split("_")[1]
        amounts = {"1": "۳۰,۰۰۰", "3": "۷۰,۰۰۰", "12": "۲۰۰,۰۰۰"}
        days = {"1": 30, "3": 90, "12": 365}
        amount = amounts[sub_type]
        days_selected = days[sub_type]

        keyboard = [[InlineKeyboardButton("🔙 برگشت به ارتقای حساب", callback_data="upgrade_account")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        payment_message = f"""💳 شماره کارت: 5022291330411024
👤 نام صاحب کارت: [سیما درویش کهن]
💰 مبلغ: {amount} تومان

⏳ لطفاً پس از پرداخت، رسید خود را ارسال کنید.
✅ بعد از تأیید پرداخت، حساب شما به مدت {days_selected} روز نامحدود خواهد شد. برای ارسال رسید به آیدی زیر پیام دهید: @rahmatedit
"""
        await query.message.edit_text(payment_message, reply_markup=reply_markup)

    elif query.data == "back_to_main":
        await start(update, context)

# چت طبیعی با Mistral
async def chat_with_mistral(update: Update, context):
    user_id = update.message.from_user.id
    user_message = update.message.text

    if not await is_user_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🚨 برای استفاده از ربات، ابتدا در کانال عضو شوید:", reply_markup=reply_markup)
        return

    if user_id not in unlimited_users and user_message_count.get(user_id, 0) >= 10:
        await update.message.reply_text("🚫 شما به سقف ۱۰ پیام رایگان در روز رسیده‌اید. لطفاً حساب خود را ارتقا دهید.")
        return

    user_message_count[user_id] = user_message_count.get(user_id, 0) + 1
    user_chat_history.setdefault(user_id, []).append({"role": "user", "content": user_message})

    try:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"model": "mistral-7b", "messages": user_chat_history[user_id]}
        response = requests.post("https://api.mistral.ai/v1/chat/completions", json=data, headers=headers)
        response_json = response.json()

        bot_reply = response_json.get("choices", [{}])[0].get("message", {}).get("content", "❌ متوجه نشدم، لطفاً دوباره بگو.")
        user_chat_history[user_id].append({"role": "assistant", "content": bot_reply})

        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

# ریست کردن تاریخچه چت کاربر
async def reset_chat(update: Update, context):
    user_chat_history.pop(update.message.from_user.id, None)
    await update.message.reply_text("✅ مکالمه شما پاک شد، می‌توانی دوباره شروع کنی.")

# اضافه کردن کاربران نامحدود
async def add_unlimited_user(update: Update, context):
    if update.message.from_user.id != 7134799893:
        await update.message.reply_text("🚫 شما اجازه اجرای این دستور را ندارید.")
        return

    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        unlimited_users[user_id] = datetime.now() + timedelta(days=days)
        await update.message.reply_text(f"✅ کاربر {user_id} به مدت {days} روز نامحدود شد.")
    except:
        await update.message.reply_text("⚠ فرمت صحیح:\n`/add_unlimited <user_id> <days>`")

# راه‌اندازی ربات
async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset_chat))
    application.add_handler(CommandHandler("add_unlimited", add_unlimited_user))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_mistral))
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())