import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from groq import Groq

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

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

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No Telegram Bot Token found!")
        return
        
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
