import logging
import os
import json
import asyncio

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# .env dan tokenni yuklaymiz
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CONTACTS_FILE = "contacts.json"

# 🔐 Faqat shu ID’lar kontakt qo‘sha oladi
ADMINS = [
    455785118,   # ← Sizning ID'ingiz
]


def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return []
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(contacts):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=4)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def find_contact(text: str, contacts):
    norm = normalize(text)
    for c in contacts:
        for alias in c["names"]:
            if normalize(alias) in norm:
                return c
    return None


def should_trigger_lookup(text: str) -> bool:
    t = text.lower()
    keys = ["nomer", "raqam", "telefon", "номер", "телефон"]
    return any(k in t for k in keys)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}!\n"
        f"Sizning Telegram ID'ingiz: {user.id}\n\n"
        "Bu bot guruhda kontaktlarni topib beradi.\n"
        "Kontakt qo‘shish faqat adminlarga ruxsat etilgan."
    )


# 🔐 /addcontact — faqat adminlar uchun
async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # 🔒 ID tekshiramiz
    if user.id not in ADMINS:
        await update.message.reply_text("❌ Siz kontakt qo‘sha olmaysiz. Bu faqat bot adminlariga ruxsat.")
        return

    try:
        text = update.message.text.replace("/addcontact", "").strip()

        parts = [p.strip() for p in text.split("|")]
        if len(parts) != 3:
            await update.message.reply_text(
                "❌ Format noto‘g‘ri!\n"
                "To‘g‘ri format:\n"
                "/addcontact Ism | izoh | +99890xxxxxxx"
            )
            return

        name, label, phone = parts

        contacts = load_contacts()

        new_contact = {
            "names": [name.lower()],
            "label": label,
            "phone": phone
        }

        contacts.append(new_contact)
        save_contacts(contacts)

        await update.message.reply_text(f"✅ {name} kontakt bazaga qo‘shildi.")

    except Exception as e:
        await update.message.reply_text("Xatolik yuz berdi.")
        print(e)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return
    
    text = msg.text
    contacts = load_contacts()

    if should_trigger_lookup(text):
        match = find_contact(text, contacts)
        if match:
            await msg.reply_text(
                f"📲 Topildi:\n"
                f"👤 {match['label']}\n"
                f"📞 {match['phone']}"
            )
        else:
            await msg.reply_text("❌ Kontakt topilmadi.")


def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except:
        pass

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcontact", add_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
