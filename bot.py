#!/usr/bin/env python3
import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
ADMIN_NAME = os.environ.get("ADMIN_NAME")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "tests_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tests": {}}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Obuna xato: {e}")
        return False

async def send_subscription_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
    ]
    text = (
        "⚠️ <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
        f"📢 Kanal: {CHANNEL_USERNAME}\n\n"
        "Obuna bo'lgandan so'ng «✅ Obunani tekshirish» tugmasini bosing."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_subscription(update, context):
        await send_subscription_message(update, context)
        return
    admin_text = ""
    if user.id == ADMIN_ID:
        admin_text = (
            "\n\n👑 <b>Admin buyruqlari:</b>\n"
            "📌 <code>/test KOD*JAVOBLAR</code> — Test yaratish\n"
            "   Misol: <code>/test 134*abababcdcd</code>\n\n"
            "📋 <code>/testlar</code> — Barcha testlar\n"
            "🗑 <code>/ochir KOD</code> — Testni o'chirish"
        )
    await update.message.reply_text(
        f"👋 Salom, <b>{user.full_name}</b>!\n\n"
        "🎓 <b>Matematika Test Botiga xush kelibsiz!</b>\n\n"
        "📝 Javob yuborish:\n"
        "<code>TESTKODI*JAVOBLARINGIZ</code>\n\n"
        "Misol: <code>135*abcdabcdab</code>"
        f"{admin_text}",
        parse_mode="HTML"
    )

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_subscription(update, context):
        await query.message.edit_text(
            f"✅ <b>Kanalga obuna bo'lgansiz!</b>\n\n"
            f"👋 Xush kelibsiz, <b>{query.from_user.full_name}</b>!\n\n"
            "📝 Test javobini yuboring:\n"
            "<code>TESTKODI*JAVOBLARINGIZ</code>",
            parse_mode="HTML"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await query.message.edit_text(
            "❌ Hali obuna bo'lmagansiz!\nIltimos kanalga obuna bo'ling.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def create_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return
    args = context.args
    if not args or "*" not in " ".join(args):
        await update.message.reply_text(
            "❌ Format xato!\n\n✅ To'g'ri: <code>/test KOD*JAVOBLAR</code>\nMisol: <code>/test 134*abababcdcd</code>",
            parse_mode="HTML"
        )
        return
    full_text = " ".join(args)
    parts = full_text.split("*", 1)
    test_code = parts[0].strip()
    answers_raw = parts[1].strip().lower()
    if not test_code.isdigit():
        await update.message.reply_text("❌ Test kodi faqat raqamlardan iborat bo'lishi kerak!")
        return
    db = load_db()
    if test_code in db["tests"]:
        await update.message.reply_text(
            f"⚠️ <b>{test_code}</b> kodli test allaqachon mavjud!\nO'chirish: <code>/ochir {test_code}</code>",
            parse_mode="HTML"
        )
        return
    answers_list = list(answers_raw)
    db["tests"][test_code] = {"answers": answers_raw, "creator": ADMIN_NAME, "count": len(answers_list)}
    save_db(db)
    preview = "".join(f"{i}. {a.upper()}\n" for i, a in enumerate(answers_list, 1))
    await update.message.reply_text(
        f"✅ <b>Test yaratildi!</b>\n\n"
        f"📌 Test kodi: <b>{test_code}</b>\n"
        f"📋 Savollar: <b>{len(answers_list)} ta</b>\n"
        f"👤 Yaratuvchi: <b>{ADMIN_NAME}</b>\n\n"
        f"<b>Javoblar:</b>\n{preview}",
        parse_mode="HTML"
    )

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

def check_answers(correct_str, user_str):
    correct = list(correct_str.lower())
    user = list(user_str.lower())
    results = []
    total_correct = 0
    for i, (c, u) in enumerate(zip(correct, user), 1):
        ok = c == u
        if ok:
            total_correct += 1
        results.append((i, u.upper(), ok, 1 if ok else 0))
    if len(user) > len(correct):
        for i in range(len(correct) + 1, len(user) + 1):
            results.append((i, user[i-1].upper(), False, 0))
    return results, total_correct, len(correct)

def format_results(test_code, test_info, results, total_correct, total_q):
    pct = (total_correct / total_q * 100) if total_q > 0 else 0
    text = (
        f"📌<b>Test kodi: {test_code}</b>\n"
        f"📋<b>Savollar soni: {total_q} ta</b>\n"
        f"👤<b>Test yaratuvchisi: {test_info['creator']}</b>\n"
        f"📝<b>Natijalar:</b>\n"
    )
    for q_num, ans, ok, ball in results:
        text += f"{q_num}. {ans} {'✅' if ok else '❌'}  {ball} ball\n"
    text += f"\n📊<b>Jami: {total_correct} ta ({pct:.1f}%)</b>"
    return text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip() if update.message.text else ""
    if not await check_subscription(update, context):
        await send_subscription_message(update, context)
        return
    if "*" not in text:
        await update.message.reply_text(
            "❓ Javob yuborish uchun:\n\n<code>TESTKODI*JAVOBLARINGIZ</code>\n\nMisol: <code>135*abcdabcdab</code>",
            parse_mode="HTML"
        )
        return
    parts = text.split("*", 1)
    test_code = parts[0].strip()
    user_answers = parts[1].strip().lower()
    db = load_db()
    if test_code not in db["tests"]:
        await update.message.reply_text("❌<b>Test kodi mavjud emas</b>", parse_mode="HTML")
        return
    test_info = db["tests"][test_code]
    results, total_correct, total_q = check_answers(test_info["answers"], user_answers)
    await update.message.reply_text(format_results(test_code, test_info, results, total_correct, total_q), parse_mode="HTML")
    # Natijani saqlash (reyting uchun)
db2 = load_db()
if "results" not in db2:
    db2["results"] = {}
if test_code not in db2["results"]:
    db2["results"][test_code] = []
db2["results"][test_code].append({
    "name": user.full_name,
    "correct": total_correct,
    "total": total_q
})
save_db(db2)
    if total_q > 0:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🧾 <b>Yangi javob:</b>\n👤 {user.full_name}\n📝 {text}\n📊 Natija: {total_correct}/{total_q} ({total_correct/total_q*100:.1f}%)",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Admin xabar xato: {e}")

async def reyting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Format: <code>/reyting KOD</code>", parse_mode="HTML")
        return
    test_code = args[0].strip()
    db = load_db()
    results = db.get("results", {}).get(test_code, [])
    if not results:
        await update.message.reply_text("📭 Bu test uchun hali natija yo'q.")
        return
    sorted_results = sorted(results, key=lambda x: x["correct"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    text = f"🏆 <b>{test_code}-test reytingi:</b>\n\n"
    for i, r in enumerate(sorted_results, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        pct = r["correct"] / r["total"] * 100
        text += f"{medal} {r['name']} — {r['correct']}/{r['total']} ({pct:.0f}%)\n"
    await update.message.reply_text(text, parse_mode="HTML")
def main():
    print("🤖 Matematika boti ishga tushmoqda...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", create_test))
    app.add_handler(CommandHandler("testlar", list_tests))
    app.add_handler(CommandHandler("ochir", delete_test))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    app.add_handler(CommandHandler("reyting", reyting))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
        
