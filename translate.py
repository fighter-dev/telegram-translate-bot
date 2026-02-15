import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from deep_translator import GoogleTranslator

USERS_FILE = "users.txt"

def save_user(user_id: int):
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(str(user_id) + "\n")

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1144924292

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

translator = GoogleTranslator(source="auto", target="en")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Contact Admin", callback_data="contact")]
    ])

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Send me text in *any language* 🌍\n"
        "I’ll translate it to *English* 🇬🇧.\n\n"
        "Need linked? Tap below 👇",
        reply_markup=keyboard,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "contact":
        context.user_data["contacting_admin"] = True
        await query.message.reply_text(
            "✍️ Type your issue now.\n"
            "I’ll forward it to the admin."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if context.user_data.get("contacting_admin"):
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📩 New Issue\n\n"
                f"👤 User: @{update.message.from_user.username}\n"
                f"🆔 ID: {update.message.from_user.id}\n\n"
                f"💬 Message:\n{text}"
            )
        )
        await update.message.reply_text("✅ Sent to admin.")
        context.user_data["contacting_admin"] = False
        return

    translated = translator.translate(text)
    await update.message.reply_text(
        f"🌍 Translated to English:\n\n{translated}"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return  # silently ignore others

    if not os.path.exists(USERS_FILE):
        count = 0
    else:
        with open(USERS_FILE) as f:
            count = len(f.read().splitlines())

    await update.message.reply_text(f"👥 Total users: {count}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()

