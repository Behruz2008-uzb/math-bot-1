#!/usr/bin/env python3
"""
Matematika Kanali Telegram Bot
================================
Versiya: 2.0 (Mini App siz)
"""

import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# =============================================
#   SOZLAMALAR - BU YERLARNI TO'LDIRING
# =============================================
BOT_TOKEN = "SIZNING_BOT_TOKENINGIZ"        # @BotFather dan olingan token
ADMIN_ID = 123456789                          # Sizning Telegram ID raqamingiz
CHANNEL_USERNAME = "@sizning_kanalingiz"      # Kanal username (@ bilan)
CHANNEL_ID = -1001234567890                   # Kanal ID (manfiy raqam)
ADMIN_NAME = "Behro'z Nurboboyev"            # Admin ismi (natijada ko'rinadi)
# =============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_FILE = "tests_db.json"


# =============================================
#   MA'LUMOTLAR BAZASI
# =============================================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tests": {}}


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =============================================
#   OBUNA TEKSHIRISH
# =============================================
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]
    except Exception as e:
        logger.error(f"Obuna tekshirishda xato: {e}")
        return False


async def send_subscription_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Kanalga obuna bo'lish",
                              url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
    ]
    text = (
        "⚠️ <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
        f"📢 Kanal: {CHANNEL_USERNAME}\n\n"
        "Obuna bo'lgandan so'ng <b>«✅ Obunani tekshirish»</b> tugmasini bosing."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="HTML",
                                                      reply_markup=InlineKeyboardMarkup(keyboard))


# =============================================
#   /start
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await check_subscription(update, context):
        await send_subscription_message(update, context)
        return

    if user.id == ADMIN_ID:
        admin_text = (
            "\n\n👑 <b>Admin buyruqlari:</b>\n"
            "📌 <code>/test KOD*JAVOBLAR</code> — Test yaratish\n"
            "   Misol: <code>/test 134*abababcdcd</code>\n\n"
            "📋 <code>/testlar</code> — Barcha testlar ro'yxati\n"
            "🗑 <code>/ochir KOD</code> — Testni o'chirish"
        )
    else:
        admin_text = ""

    text = (
        f"👋 Salom, <b>{user.full_name}</b>!\n\n"
        "🎓 <b>Matematika Test Botiga xush kelibsiz!</b>\n\n"
        "📝 <b>Javob yuborish:</b>\n"
        "<code>TESTKODI*JAVOBLARINGIZ</code>\n\n"
        "Misol: <code>135*abcdabcdab</code>"
        f"{admin_text}"
    )

    await update.message.reply_text(text, parse_mode="HTML")


# =============================================
#   OBUNA CALLBACK
# =============================================
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await check_subscription(update, context):
        user = query.from_user
        await query.message.edit_text(
            f"✅ <b>Kanalga obuna bo'lgansiz!</b>\n\n"
            f"👋 Xush kelibsiz, <b>{user.full_name}</b>!\n\n"
            "📝 Test javobini yuboring:\n"
            "<code>TESTKODI*JAVOBLARINGIZ</code>\n\n"
            "Misol: <code>135*abcdabcd</code>",
            parse_mode="HTML"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish",
                                  url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await query.message.edit_text(
            "❌ Siz hali kanalga obuna bo'lmagansiz!\n\n"
            "Iltimos, avval kanalga obuna bo'ling.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =============================================
#   /test (FAQAT ADMIN)
# =============================================
async def create_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Format xato!\n\n"
            "✅ To'g'ri: <code>/test KOD*JAVOBLAR</code>\n"
            "Misol: <code>/test 134*abababcdcd</code>",
            parse_mode="HTML"
        )
        return

    full_text = " ".join(args)

    if "*" not in full_text:
        await update.message.reply_text(
            "❌ <code>*</code> belgisi kerak!\n"
            "Misol: <code>/test 134*abcdabcd</code>",
            parse_mode="HTML"
        )
        return

    parts = full_text.split("*", 1)
    test_code = parts[0].strip()
    answers_raw = parts[1].strip().lower()

    if not test_code.isdigit():
        await update.message.reply_text("❌ Test kodi faqat raqamlardan iborat bo'lishi kerak!")
        return

    db = load_db()

    if test_code in db["tests"]:
        await update.message.reply_text(
            f"⚠️ <b>{test_code}</b> kodli test allaqachon mavjud!\n"
            f"O'chirish uchun: <code>/ochir {test_code}</code>",
            parse_mode="HTML"
        )
        return

    answers_list = list(answers_raw)
    db["tests"][test_code] = {
        "answers": answers_raw,
        "creator": ADMIN_NAME,
        "count": len(answers_list)
    }
    save_db(db)

    preview = ""
    for i, ans in enumerate(answers_list, 1):
        preview += f"{i}. {ans.upper()}\n"

    await update.message.reply_text(
        f"✅ <b>Test yaratildi!</b>\n\n"
        f"📌 Test kodi: <b>{test_code}</b>\n"
        f"📋 Savollar soni: <b>{len(answers_list)} ta</b>\n"
        f"👤 Yaratuvchi: <b>{ADMIN_NAME}</b>\n\n"
        f"<b>Javoblar:</b>\n{preview}",
        parse_mode="HTML"
    )


# =============================================
#   /testlar
# =============================================
async def list_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return

    db = load_db()
    tests = db.get("tests", {})

    if not tests:
        await update.message.reply_text("📭 Hozircha hech qanday test yo'q.")
        return

    text = "📋 <b>Barcha testlar:</b>\n\n"
    for code, info in tests.items():
        text += f"🔹 Kod: <b>{code}</b> | Savollar: {info['count']} ta\n"

    await update.message.reply_text(text, parse_mode="HTML")


# =============================================
#   /ochir
# =============================================
async def delete_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ Format: <code>/ochir KOD</code>", parse_mode="HTML")
        return

    test_code = args[0].strip()
    db = load_db()

    if test_code not in db["tests"]:
        await update.message.reply_text(f"❌ <b>{test_code}</b> kodli test topilmadi!", parse_mode="HTML")
        return

    del db["tests"][test_code]
    save_db(db)

    await update.message.reply_text(f"✅ <b>{test_code}</b> kodli test o'chirildi!", parse_mode="HTML")


# =============================================
#   JAVOB TEKSHIRISH
# =============================================
def check_answers(correct_str: str, user_str: str):
    correct = list(correct_str.lower())
    user = list(user_str.lower())

    results = []
    total_correct = 0
    total_q = len(correct)

    for i, (c, u) in enumerate(zip(correct, user), 1):
        is_correct = (c == u)
        if is_correct:
            total_correct += 1
        results.append((i, u.upper(), is_correct, 1 if is_correct else 0))

    # Foydalanuvchi ortiqcha javob berganda
    if len(user) > len(correct):
        for i in range(len(correct) + 1, len(user) + 1):
            results.append((i, user[i - 1].upper(), False, 0))

    return results, total_correct, total_q


def format_results(test_code, test_info, results, total_correct, total_q):
    pct = (total_correct / total_q * 100) if total_q > 0 else 0

    text = (
        f"📌<b>Test kodi: {test_code}</b>\n"
        f"📋<b>Savollar soni: {total_q} ta</b>\n"
        f"👤<b>Test yaratuvchisi: {test_info['creator']}</b>\n"
        f"📝<b>Natijalar:</b>\n"
    )

    for q_num, ans, is_correct, ball in results:
        emoji = "✅" if is_correct else "❌"
        text += f"{q_num}. {ans} {emoji}  {ball} ball\n"

    text += f"\n📊<b>Jami: {total_correct} ta ({pct:.1f}%)</b>"
    return text


# =============================================
#   XABARLARNI QAYTA ISHLASH
# =============================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    text = message.text.strip() if message.text else ""

    if not await check_subscription(update, context):
        await send_subscription_message(update, context)
        return

    if "*" not in text:
        await message.reply_text(
            "❓ Javob yuborish uchun:\n\n"
            "<code>TESTKODI*JAVOBLARINGIZ</code>\n\n"
            "Misol: <code>135*abcdabcdab</code>",
            parse_mode="HTML"
        )
        return

    parts = text.split("*", 1)
    test_code = parts[0].strip()
    user_answers = parts[1].strip().lower()

    db = load_db()
    tests = db.get("tests", {})

    if test_code not in tests:
        await message.reply_text("❌<b>Test kodi mavjud emas</b>", parse_mode="HTML")
        return

    test_info = tests[test_code]
    results, total_correct, total_q = check_answers(test_info["answers"], user_answers)

    result_text = format_results(test_code, test_info, results, total_correct, total_q)
    await message.reply_text(result_text, parse_mode="HTML")

    # Adminga xabarnoma
    if total_q > 0:
        admin_text = (
            f"🧾 <b>Yangi javob:</b>\n"
            f"👤 {user.full_name}\n"
            f"📝 {text}\n"
            f"📊 Natija: {total_correct}/{total_q} ({total_correct / total_q * 100:.1f}%)"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xato: {e}")


# =============================================
#   ASOSIY
# =============================================
def main():
    print("🤖 Matematika boti ishga tushmoqda...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", create_test))
    app.add_handler(CommandHandler("testlar", list_tests))
    app.add_handler(CommandHandler("ochir", delete_test))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
