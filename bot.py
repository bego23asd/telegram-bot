import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

# ─── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ─── Constants ──────────────────────────────────────────────────────────
receipt_map = {}
OWNER_GROUP_ID = -4676264326  # Replace with your actual owner group ID

AUTO_REPLY_TEXT = """💳 𝗖𝗔𝗦𝗜𝗡𝗢 𝗦𝗖𝗥𝗜𝗣𝗧 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦  

📤 𝗦𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗿𝗲𝗰𝗲𝗶𝗽𝘁 𝘁𝗼 𝗽𝗿𝗼𝗰𝗲𝘀𝘀 𝘆𝗼𝘂𝗿 𝗹𝗶𝗰𝗲𝗻𝘀𝗲 𝗸𝗲𝘆.  

━━━━━━━━━━━━━━━━━━━  
💰 𝗣𝗥𝗜𝗖𝗜𝗡𝗚  
✅ ₱150 – 1 𝗗𝗮𝘆 𝗔𝗰𝗰𝗲𝘀𝘀  

📌 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗢𝗣𝗧𝗜𝗢𝗡𝗦  
🔵 𝗚𝗖𝗮𝘀𝗵: `0994 585 0063`  
🟢 𝗠𝗮𝘆𝗮: `0991 390 7143`  

⚠️ 𝐓𝐫𝐚𝐧𝐬𝐚𝐜𝐭𝐢𝐨𝐧 𝐢𝐬𝐬𝐮𝐞𝐬? 𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐬𝐮𝐩𝐩𝐨𝐫𝐭: @lyco0202 | @Belonm0299   
━━━━━━━━━━━━━━━━━━━  
"""

# ─── Telegram Handlers ──────────────────────────────────────────────────

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == OWNER_GROUP_ID:
        return
    await update.message.reply_text(AUTO_REPLY_TEXT)

async def forward_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    client_chat_id = update.message.chat_id

    forwarded_msg = await context.bot.forward_message(
        chat_id=OWNER_GROUP_ID,
        from_chat_id=client_chat_id,
        message_id=update.message.message_id
    )

    receipt_map[forwarded_msg.message_id] = client_chat_id

    await context.bot.send_message(
        chat_id=OWNER_GROUP_ID,
        text=f"📩 Receipt received from @{user.username or user.first_name} (ID: {client_chat_id})\n"
             f"Reply to this message to send a message back to the client."
    )

    await update.message.reply_text("⏳ Processing... Please wait for your license key.")

async def owner_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != OWNER_GROUP_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to a forwarded receipt message.")
        return

    replied_msg = update.message.reply_to_message
    forwarded_msg_id = replied_msg.message_id

    if forwarded_msg_id not in receipt_map:
        await update.message.reply_text("⚠️ Cannot find client chat ID. Reply to a forwarded receipt message.")
        return

    client_chat_id = receipt_map[forwarded_msg_id]

    await context.bot.send_message(
        chat_id=client_chat_id,
        text=f"{update.message.text}"
    )

    await update.message.reply_text("✅ Message sent to the client!")

# ─── Flask Server (for Render) ──────────────────────────────────────────

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return '🤖 Telegram bot is running!', 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# ─── Main Entrypoint ────────────────────────────────────────────────────

def main():
    # Start Flask server in a background thread
    threading.Thread(target=run_flask).start()

    # Start Telegram bot
    app = ApplicationBuilder().token("7900770091:AAG6ysqNb3nDofaHZPQQuGsbwMCZcsVNKrM").build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Chat(OWNER_GROUP_ID), auto_reply))
    app.add_handler(MessageHandler(filters.PHOTO, forward_receipt))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT & filters.Chat(OWNER_GROUP_ID), owner_reply_handler))

    print("🤖 Bot is running with Flask keep-alive...")
    app.run_polling()

if __name__ == "__main__":
    main()
