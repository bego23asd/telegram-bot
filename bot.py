import logging
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

# -------------------------------
# 🔹 Securely Fetch Telegram Bot Token
# -------------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Store in environment variable!

if not TOKEN:
    raise ValueError("⚠️ ERROR: TELEGRAM_BOT_TOKEN not set!")

# -------------------------------
# 🔹 Enable Logging
# -------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# -------------------------------
# 🔹 Constants
# -------------------------------
OWNER_GROUP_ID = -4676264326  # Replace with actual owner group ID
receipt_map = {}  # Store mapping of forwarded messages to client chat IDs

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

# -------------------------------
# 🔹 Define Telegram Bot Handlers
# -------------------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-reply to client messages with payment instructions."""
    if update.message.chat_id == OWNER_GROUP_ID:
        return  # Ignore messages from the owner group
    await update.message.reply_text(AUTO_REPLY_TEXT)

async def forward_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward receipts to the admin group and store client chat IDs."""
    user = update.message.from_user
    client_chat_id = update.message.chat_id

    # Forward the receipt to the owner group
    forwarded_msg = await context.bot.forward_message(
        chat_id=OWNER_GROUP_ID,
        from_chat_id=client_chat_id,
        message_id=update.message.message_id
    )

    # Store mapping of forwarded message ID to client chat ID
    receipt_map[forwarded_msg.message_id] = client_chat_id

    # Notify the admin group
    await context.bot.send_message(
        chat_id=OWNER_GROUP_ID,
        text=f"📩 Receipt received from @{user.username or user.first_name} (ID: {client_chat_id})\n"
             f"Reply to this message to send a message back to the client."
    )

    # Notify the client
    await update.message.reply_text("⏳ Processing... Please wait for your license key.")

async def owner_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle owner's reply to a forwarded receipt and send it back to the client."""
    if update.message.chat_id != OWNER_GROUP_ID:
        return  # Ignore messages outside the admin group

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to a forwarded receipt message.")
        return

    # Get forwarded message ID
    forwarded_msg_id = update.message.reply_to_message.message_id

    if forwarded_msg_id not in receipt_map:
        await update.message.reply_text("⚠️ Cannot find client chat ID. Reply to a forwarded receipt message.")
        return

    client_chat_id = receipt_map[forwarded_msg_id]

    # Send the owner's reply to the client
    await context.bot.send_message(chat_id=client_chat_id, text=update.message.text)

    # Confirm message was sent
    await update.message.reply_text("✅ Message sent to the client!")

# -------------------------------
# 🔹 Initialize Telegram Bot
# -------------------------------
telegram_app = ApplicationBuilder().token(TOKEN).build()

# Register the handlers
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Chat(OWNER_GROUP_ID), auto_reply))
telegram_app.add_handler(MessageHandler(filters.PHOTO, forward_receipt))
telegram_app.add_handler(MessageHandler(filters.REPLY & filters.TEXT & filters.Chat(OWNER_GROUP_ID), owner_reply_handler))

# -------------------------------
# 🔹 Create Flask Web App
# -------------------------------
flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Receive updates from Telegram via webhook."""
    update_json = request.get_json(force=True)
    update = Update.de_json(update_json, telegram_app.bot)
    telegram_app.process_update(update)
    return 'OK', 200

@flask_app.route('/')
def index():
    return "Telegram Bot Webhook Server Running"

# -------------------------------
# 🔹 Run Flask App (For Local Testing Only)
# -------------------------------
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=5000)
