import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# BOT_TOKEN Render dagi Environment Variables ichida turadi
BOT_TOKEN = os.getenv("BOT_TOKEN")

CONTACTS_FILE = "contacts.json"
ADMIN_ID = 455785118  # Sizning Telegram ID'ingiz


# ---------- Kontakt fayli bilan ishlash ----------

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return {}
    with open(CONCATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(data):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------- Kirill -> Lotin va normalizatsiya ----------

CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "", "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
    "ғ": "g'", "қ": "q", "ў": "o'", "ҳ": "h",
}


def cyr_to_lat(text: str) -> str:
    text = text.lower()
    return "".join(CYR_TO_LAT.get(ch, ch) for ch in text)


def normalize(text: str) -> str:
    if not text:
        return ""
    t = text.lower()
    t = cyr_to_lat(t)
    for ch in [",", ".", "!", "?", ":", ";", "(", ")", "\"", "'"]:
        t = t.replace(ch, " ")
    return " ".join(t.split())


# ---------- Levenshtein (2–3 xatogacha bardosh) ----------

def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)
    if abs(len(a) - len(b)) > 3:
        return 10  # juda uzoq bo'lsa, darrov yomon baho

    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        dp[i][0] = i
    for j in range(len(b) + 1):
        dp[0][j] = j

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # o'chirish
                dp[i][j - 1] + 1,      # qo'shish
                dp[i - 1][j - 1] + cost,  # almashtirish
            )
    return dp[-1][-1]


# ---------- Bot komandalar ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}!\n"
        f"Sizning ID'ingiz: {user.id}\n\n"
        "Ism yozing, men kontaktni qidirib beraman.\n"
        "Yangi kontakt qo'shish faqat admin uchun: /add Ism Raqam"
    )


async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Sizda kontakt qo‘shishga ruxsat yo‘q.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Format: /add Ism Raqam\n"
            "Misol: /add Alisher +998901234567"
        )
        return

    name = context.args[0]
    number = " ".join(context.args[1:])

    contacts = load_contacts()
    contacts[name] = number
    save_contacts(contacts)

    await update.message.reply_text(f"✔ Kontakt qo‘shildi:\n{name} → {number}")


async def search_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_raw = update.message.text or ""
    contacts = load_contacts()

    norm = normalize(text_raw)
    words = norm.split()

    stop_words = {"nomer", "raqam", "telefon", "aka", "uka", "domla", "ustoz", "kerak", "bering", "ber", "nomeri"}
    candidate_words = [w for w in words if w not in stop_words and len(w) >= 3]
    if not candidate_words:
        candidate_words = words

    best_match = None
    best_score = 10

    for name, number in contacts.items():
        norm_name = normalize(name)

        for q in candidate_words:
            # to'g'ridan-to'g'ri ichida bo'lsa
            if q and q in norm_name:
                best_match = (name, number)
                best_score = 0
                break

            dist = levenshtein(q, norm_name)
            if dist < best_score:
                best_score = dist
                best_match = (name, number)

        if best_score == 0:
            break

    if best_match and best_score <= 2:
        name, number = best_match
        await update.message.reply_text(f"📲 Topildi:\n{name} → {number}")
    else:
        await update.message.reply_text("❌ Kontakt topilmadi.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_contact))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
