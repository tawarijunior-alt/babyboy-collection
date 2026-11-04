import os
import logging
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from groq import Groq
from fastapi import FastAPI
import uvicorn

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👑 *Welcome to BABY BOY, {user.first_name}*.\n\n"
        "_A Royal Essence for the Discerning._\n\n"
        "Discover our signature collections, explore personalized fragrances, "
        "or create a scent that is uniquely yours.\n\n"
        "Your scent. Your story. Your signature."
    )
    
    keyboard = [
        [InlineKeyboardButton("👑 Shop Collections", callback_data="shop_collections")],
        [InlineKeyboardButton("🧪 Create Your Own Scent (AI)", callback_data="create_scent")],
        [InlineKeyboardButton("🛍️ My Orders", callback_data="my_orders"), InlineKeyboardButton("🔐 My Fragrances", callback_data="my_fragrances")],
        [InlineKeyboardButton("📞 Contact Support", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "shop_collections":
        keyboard = [
            [InlineKeyboardButton("✨ Baby Boy Collection (6 Signatures)", callback_data="col_babyboy")],
            [InlineKeyboardButton("⚡ Switch Collection (5 Fragrances)", callback_data="col_switch")],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Select a collection to explore:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "create_scent":
        await query.edit_message_text(
            "🧪 *BABY BOY AI Fragrance Studio*\n\n"
            "Describe the exact scent you want in your own words:\n\n"
            "*(Type your description in the chat below!)*",
            parse_mode="Markdown"
        )
        
    elif query.data == "main_menu":
        await start(update, context)

# --- FASTAPI WEB SERVER (Runs in background thread to satisfy Render) ---
app = FastAPI()

@app.api_route("/", methods=["GET", "HEAD", "POST"])
def health_check():
    return {"status": "BABY BOY Bot is online"}

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

if __name__ == "__main__":
    # Start FastAPI web server in a background thread so Render's health checks pass
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logger.info("FastAPI Web Server started in background thread.")

    # Run Telegram Bot on the main thread (satisfies Python signal handlers)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No Telegram Bot Token found!")
    else:
        application = Application.builder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("Telegram Bot is polling on main thread...")
        application.run_polling(drop_pending_updates=True)
