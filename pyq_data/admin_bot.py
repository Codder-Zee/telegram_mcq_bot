from telegram.ext import ApplicationBuilder, CommandHandler
import json, os

# ===== CONFIG =====
BOT_TOKEN = "PASTE_YOUR_ADMIN_BOT_TOKEN_HERE"
ADMIN_ID = 6572975961

FILE = "marathi.txt"
META = "meta.json"


# ===== HELPERS =====
def is_admin(update):
    return update.effective_user.id == ADMIN_ID


def load_meta():
    if not os.path.exists(META):
        return {"last_upload_count": 0, "last_poll": ""}
    with open(META, "r", encoding="utf-8") as f:
        return json.load(f)


def save_meta(meta):
    with open(META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# ===== COMMANDS =====

async def lastpoll(update, context):
    if not is_admin(update):
        return
    meta = load_meta()
    msg = meta.get("last_poll", "")
    if not msg:
        await update.message.reply_text("❌ No poll posted yet")
    else:
        await update.message.reply_text(f"🧠 Last Poll:\n\n{msg}")


async def new_upload(update, context):
    if not is_admin(update):
        return

    text = update.message.text.split("\n", 1)
    if len(text) < 2:
        await update.message.reply_text(
            "❌ /newUpload ke niche questions paste karo"
        )
        return

    data = text[1].strip()
    q_count = data.count("\nQ:")

    if q_count == 0:
        await update.message.reply_text("❌ Koi valid question nahi mila")
        return

    with open(FILE, "a", encoding="utf-8") as f:
        f.write("\n\n" + data)

    meta = load_meta()
    meta["last_upload_count"] = q_count
    save_meta(meta)

    await update.message.reply_text(f"✅ {q_count} questions successfully added")


async def delete_last_upload(update, context):
    if not is_admin(update):
        return

    meta = load_meta()
    count = meta.get("last_upload_count", 0)

    if count == 0:
        await update.message.reply_text("❌ Delete karne ke liye kuch nahi hai")
        return

    with open(FILE, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("\nQ:")
    keep = parts[:-count]

    new_content = "\nQ:".join(keep).rstrip()

    with open(FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    meta["last_upload_count"] = 0
    save_meta(meta)

    await update.message.reply_text(
        f"🗑️ Last upload deleted ({count} questions removed)"
    )


# ===== RUN =====
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("lastpoll", lastpoll))
app.add_handler(CommandHandler("newUpload", new_upload))
app.add_handler(CommandHandler("deleteFromLastUpload", delete_last_upload))

print("✅ Admin Bot is running...")
app.run_polling()
