import logging
import sys
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
sh.setFormatter(formatter)
logger.addHandler(sh)

KEYBOARD = [
    [
        InlineKeyboardButton("0.25", callback_data="0.25"),
        InlineKeyboardButton("0.5", callback_data="0.50"),
        InlineKeyboardButton("0.75", callback_data="0.75"),
        InlineKeyboardButton("1", callback_data="1.00")
    ],
]
REPLY_MARKUP = InlineKeyboardMarkup(KEYBOARD)


def parse_initial(text):
    users = []
    stats = {
        "mean": "-",
        "min": "-",
        "max": "-",
    }
    for user in text.split(" "):
        if user.startswith("@"):
            users.append({"name": user[1:], "vote": "-"})
    return users, stats


def parse_message(text, current_username, button_value, force=False):
    text = text.split("\n")[1]
    users = []
    stats = {
        "mean": "-",
        "min": "-",
        "max": "-",
    }
    for user in text.split(";"):
        user = user.strip()

        if "@" not in user:
            continue

        username = user.split(" ")[0].replace("@", "").replace(":", "")
        if username == current_username:
            users.append({"name": username, "vote": float(button_value)})
        else:
            users.append({"name": username, "vote": float(user.split(" ")[-1])})

    if all(user["vote"] != "-" for user in users) or force:
        stats = {
            "mean": 0,
            "min": 100,
            "max": 0,
        }
        total = sum(user["vote"] for user in users if user["vote"] != "-")
        for user in users:
            if user["vote"] > stats["max"]:
                stats["max"] = user["vote"]

            if user["vote"] < stats["min"]:
                stats["min"] = user["vote"]

            stats["mean"] = round(total / len(users), 2)

    return users, stats


def generate_message(users, stats):
    users_text = "".join(f"@{user['name']}: {user['vote']}; " for user in users)
    if all(user["vote"] != "-" for user in users):
        final_text = (
            f"The votes are in.\n"
            f"{users_text}\n\n"
            f"Stats: mean: {stats['mean']}, min: {stats['min']}, max: {stats['max']}"
        )
    else:
        final_text = (
            f"Waiting for votes.\n"
            f"{users_text}\n\n"
            f"Stats: mean: {stats['mean']}, min: {stats['min']}, max: {stats['max']}"
        )
    return final_text


async def helpme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Type /poker title @user1 @user2")


async def poker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users, stats = parse_initial(update.message.text)
    text = generate_message(users, stats)
    reply_markup = InlineKeyboardMarkup(KEYBOARD)
    await update.message.reply_text(text, reply_markup=REPLY_MARKUP)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    await query.answer()

    users, stats = parse_message(query.message.text, query.from_user.username, query.data)
    text = generate_message(users, stats)

    await query.edit_message_text(text=text, reply_markup=REPLY_MARKUP)


if __name__ == "__main__":
    logger.info("Starting poker planning bot...")
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("help", helpme))
    app.add_handler(CommandHandler("poker", poker))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
