import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CONTACTS_FILE = "contacts.json"
ADMIN_ID = 455785118


def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return {}
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(data):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "", "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
    "ғ": "g'", "қ": "q", "ў": "o'", "ҳ": "h"
}


def cyr_to_lat(text: str) -> str:
    text = text.lower()
    return "".join(CYR_TO_LAT.get(ch, ch) for ch in text)


def normalize(text: str) -> str:
    t = text.lower()
    t = cyr_to_lat(t)
    for ch in [",", ".", "!", "?", ":", ";", "(", ")", "\"", "'"]:
        t = t.replace(ch, " ")
    return " ".join(t.split())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 3:
        return 10

    dp = [[i + j for j in range(len(b) + 1)]]
    for i in range(1, len(a) + 1):
        row = [i]
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            row.append(min(
                dp[i - 1][j] + 1,
                row[j - 1] + 1,
                dp[i - 1][j - 1] + cost
            ))
        dp.append(row)
    return dp[-1][-1]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! Ism kiriting.")


async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Sizda ruxsat yo‘q!")

    if len(context.args) < 2:
        return await update.message.reply_text("Format: /add Ism Raqam")

    name = context.args[0]
    number = " ".join(context.args[1:])

    contacts = load_contacts()
    contacts[name] = number
    save_contacts(contacts)

    await update.message.reply_text(f"✔ Qo‘shildi:\n{name} → {number}")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = normalize(update.message.text)
    contacts = load_contacts()

    best = None
    best_score = 10

    for name, number in contacts.items():
        n = normalize(name)

        # To'g'ridan-to'g'ri ichida bo'lsa
        if query in n:
            return await update.message.reply_text(f"{name}: {number}")

        # Levenshtein bo'yicha tekshiramiz
        dist = levenshtein(query, n)
        if dist < best_score:
            best_score = dist
            best = (name, number)

    if best and best_score <= 2:
        name, number = best
        return await update.message.reply_text(f"{name}: {number}")

    await update.message.reply_text("❌ Topilmadi.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.run_polling()


if __name__ == "__main__":
    main()
