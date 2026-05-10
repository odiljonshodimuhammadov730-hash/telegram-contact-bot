#!/usr/bin/env python3
import json
import os
import re
from difflib import SequenceMatcher
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8727718384:AAGatf93CQ359-2v_22NP3DCC1vHqfqul0o")
ADMIN_IDS = [455785118]
CONTACTS_FILE = "contacts.json"
SIMILARITY_THRESHOLD = 0.45

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return {}
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_contacts(contacts):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)

def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return text

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def fuzzy_search(query, contacts):
    query_norm = normalize(query)
    results = []
    for name, info in contacts.items():
        name_norm = normalize(name)
        full_sim = similarity(query_norm, name_norm)
        parts = name_norm.split()
        part_sim = max((similarity(query_norm, p) for p in parts), default=0)
        contains = query_norm in name_norm
        best_sim = max(full_sim, part_sim)
        if contains or best_sim >= SIMILARITY_THRESHOLD:
            results.append({"name": name, "phone": info.get("phone", ""), "note": info.get("note", ""), "score": 1.0 if contains else best_sim})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update, context):
    text = "👋 *Teshiktosh Mahalla Kontaktlar Boti*\n\n📞 Raqam topish:\n  `/nomer Akmal`\n\n🔍 Guruhda:\n  _«Akmalning nomeri bormi?»_\n\n📋 *Admin buyruqlari:*\n  `/qosh Ism | +998901234567 | izoh`\n  `/ochir Ism`\n  `/royxat`"
    await update.message.reply_text(text, parse_mode="Markdown")

async def nomer(update, context):
    if not context.args:
        await update.message.reply_text("❓ Misol: `/nomer Akmal`", parse_mode="Markdown")
        return
    query = " ".join(context.args)
    contacts = load_contacts()
    if not contacts:
        await update.message.reply_text("📭 Bazada kontakt yo'q.")
        return
    results = fuzzy_search(query, contacts)
    if not results:
        await update.message.reply_text(f"🔍 *«{query}»* topilmadi.", parse_mode="Markdown")
        return
    lines = [f"📞 *«{query}»* bo'yicha:\n"]
    for r in results:
        line = f"👤 *{r['name']}* — `{r['phone']}`"
        if r["note"]:
            line += f"\n   _{r['note']}_"
        lines.append(line)
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def qosh(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return
    if not context.args:
        await update.message.reply_text("📝 Format: `/qosh Ism | +998901234567 | izoh`", parse_mode="Markdown")
        return
    raw = " ".join(context.args)
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2:
        await update.message.reply_text("❌ Misol: `/qosh Akmal | +998901234567`", parse_mode="Markdown")
        return
    name, phone = parts[0], parts[1]
    note = parts[2] if len(parts) > 2 else ""
    phone_clean = re.sub(r"[\s\-()]", "", phone)
    if not re.match(r"^\+?[\d]{9,13}$", phone_clean):
        await update.message.reply_text("❌ Telefon raqam noto'g'ri!")
        return
    contacts = load_contacts()
    contacts[name] = {"phone": phone_clean, "note": note}
    save_contacts(contacts)
    await update.message.reply_text(f"✅ *{name}* qo'shildi!\n📞 {phone_clean}", parse_mode="Markdown")

async def ochir(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return
    if not context.args:
        await update.message.reply_text("📝 Format: `/ochir Ism`", parse_mode="Markdown")
        return
    name = " ".join(context.args)
    contacts = load_contacts()
    if name in contacts:
        del contacts[name]
        save_contacts(contacts)
        await update.message.reply_text(f"🗑 *{name}* o'chirildi.", parse_mode="Markdown")
    else:
        results = fuzzy_search(name, contacts)
        if results:
            found_name = results[0]["name"]
            del contacts[found_name]
            save_contacts(contacts)
            await update.message.reply_text(f"🗑 *{found_name}* o'chirildi.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ *{name}* topilmadi.", parse_mode="Markdown")

async def royxat(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return
    contacts = load_contacts()
    if not contacts:
        await update.message.reply_text("📭 Baza bo'sh.")
        return
    lines = [f"📋 *Barcha kontaktlar ({len(contacts)} ta):*\n"]
    for name, info in sorted(contacts.items()):
        line = f"• *{name}* — `{info['phone']}`"
        if info.get("note"):
            line += f" _{info['note']}_"
        lines.append(line)
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > 3800:
            await update.message.reply_text(chunk, parse_mode="Markdown")
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await update.message.reply_text(chunk, parse_mode="Markdown")

async def handle_message(update, context):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    trigger_words = ["nomeri", "raqami", "telefoni", "kontakti", "nomer", "raqam"]
    if not any(word in text for word in trigger_words):
        return
    query = text
    for word in trigger_words + ["bormi", "bor", "kim", "bilasizmi", "?"]:
        query = query.replace(word, " ")
    query = " ".join(query.split()).strip()
    if len(query) < 2:
        return
    contacts = load_contacts()
    if not contacts:
        return
    results = fuzzy_search(query, contacts)
    if not results:
        return
    lines = [f"📞 *{results[0]['name']}*\n`{results[0]['phone']}`"]
    if results[0]["note"]:
        lines.append(f"_{results[0]['note']}_")
    if len(results) > 1:
        lines.append("\n🔍 Boshqa natijalar:")
        for r in results[1:3]:
            lines.append(f"• *{r['name']}* — `{r['phone']}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nomer", nomer))
    app.add_handler(CommandHandler("qosh", qosh))
    app.add_handler(CommandHandler("ochir", ochir))
    app.add_handler(CommandHandler("royxat", royxat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
