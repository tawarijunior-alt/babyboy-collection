import os
import logging
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from fastapi import FastAPI
import uvicorn

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Preferred Telegram DM Chat ID for Admin Notifications
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "6375911140")

# --- PRODUCT CATALOG (Naira ₦) ---
CATALOG = {
    "col_babyboy": {
        "title": "✨ Baby Boy Collection (Signature Oils)",
        "items": [
            {"id": "bb_1", "name": "Oud Royal", "desc": "Deep, woody, rich royal Arabic oud.", "price": 5500},
            {"id": "bb_2", "name": "Bleu de Boss", "desc": "Crisp citrus with an amber-woody dry down.", "price": 5000},
            {"id": "bb_3", "name": "Vanilla Velvet", "desc": "Smooth warm vanilla layered with soft musk.", "price": 4500},
            {"id": "bb_4", "name": "Savage Elixir", "desc": "Spicy, raw, magnetic, and masculine.", "price": 5500},
            {"id": "bb_5", "name": "Milionaire", "desc": "Opulent blend of blood mandarin, leather, and cinnamon.", "price": 5000},
            {"id": "bb_6", "name": "Black Smoke", "desc": "Smoky leather, tobacco leaf, and cognac.", "price": 6000}
        ]
    },
    "col_switch": {
        "title": "⚡ Switch Collection (Versatile & Fresh)",
        "items": [
            {"id": "sw_1", "name": "Aqua Rush", "desc": "Refreshing marine notes with sea salt and mint.", "price": 4500},
            {"id": "sw_2", "name": "Velvet Musk", "desc": "Clean, intimate, skin-like musky luxury.", "price": 4000},
            {"id": "sw_3", "name": "Golden Tobacco", "desc": "Warm honeyed tobacco with sweet spices.", "price": 5000},
            {"id": "sw_4", "name": "Emerald Wood", "desc": "Pine forest freshness balanced with earthy vetiver.", "price": 4500},
            {"id": "sw_5", "name": "Midnight Noir", "desc": "Dark lavender, iris, and rich woody notes.", "price": 5000}
        ]
    }
}

USER_SESSIONS = {}

# --- TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👑 *Welcome to BABY BOY, {user.first_name}*.\n\n"
        "_A Royal Essence for Selection & Status._\n\n"
        "Explore our signature oil collections, request a custom scent blended directly with our admin, "
        "or manage your orders seamlessly.\n\n"
        "Your scent. Your story. Your signature."
    )
    
    keyboard = [
        [InlineKeyboardButton("👑 Shop Collections", callback_data="shop_collections")],
        [InlineKeyboardButton("🧪 Create Custom Scent (Admin)", callback_data="create_custom_scent")],
        [InlineKeyboardButton("🛒 View Cart / Checkout", callback_data="view_cart")],
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
    user_id = query.from_user.id
    data = query.data
    
    if data == "shop_collections":
        keyboard = [
            [InlineKeyboardButton("✨ Baby Boy Collection (6 Signatures)", callback_data="col_babyboy")],
            [InlineKeyboardButton("⚡ Switch Collection (5 Fragrances)", callback_data="col_switch")],
            [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Select a collection to explore:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data in CATALOG:
        col = CATALOG[data]
        text = f"*{col['title']}*\n\n"
        keyboard = []
        for item in col["items"]:
            text += f"▪️ *{item['name']}* - ₦{item['price']:,}\n_{item['desc']}_\n\n"
            keyboard.append([InlineKeyboardButton(f"➕ Add {item['name']} (₦{item['price']:,})", callback_data=f"add_{item['id']}")])
        keyboard.append([InlineKeyboardButton("🛒 View Cart", callback_data="view_cart"), InlineKeyboardButton("⬅️ Collections", callback_data="shop_collections")])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data.startswith("add_"):
        item_id = data.replace("add_", "")
        found_item = None
        for c in CATALOG.values():
            for i in c["items"]:
                if i["id"] == item_id:
                    found_item = i
                    break
        
        if found_item:
            if user_id not in USER_SESSIONS:
                USER_SESSIONS[user_id] = {"cart": [], "custom_mode": False, "checkout_mode": False}
            USER_SESSIONS[user_id]["cart"].append(found_item)
            
            keyboard = [
                [InlineKeyboardButton("🛒 View Cart & Checkout", callback_data="view_cart")],
                [InlineKeyboardButton("🛍️ Continue Shopping", callback_data="shop_collections")]
            ]
            await query.edit_message_text(f"✅ *{found_item['name']}* has been added to your cart!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            
    elif data == "view_cart":
        if user_id not in USER_SESSIONS or not USER_SESSIONS[user_id]["cart"]:
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]]
            await query.edit_message_text("🛒 Your shopping cart is currently empty.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        cart = USER_SESSIONS[user_id]["cart"]
        total = sum(item["price"] for item in cart)
        text = "🛒 *Your BABY BOY Shopping Cart:*\n\n"
        for idx, item in enumerate(cart, 1):
            text += f"{idx}. *{item['name']}* — ₦{item['price']:,}\n"
        text += f"\n*Total: ₦{total:,}*\n\nReady to place your order?"
        
        keyboard = [
            [InlineKeyboardButton("💳 Proceed to Payment & Receipt Upload", callback_data="checkout_order")],
            [InlineKeyboardButton("🗑️ Clear Cart", callback_data="clear_cart")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "clear_cart":
        if user_id in USER_SESSIONS:
            USER_SESSIONS[user_id]["cart"] = []
        await query.edit_message_text("🛒 Your cart has been cleared.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]))
        
    elif data == "checkout_order":
        if user_id not in USER_SESSIONS:
            USER_SESSIONS[user_id] = {}
        USER_SESSIONS[user_id]["checkout_mode"] = True
        
        cart = USER_SESSIONS[user_id].get("cart", [])
        total = sum(item["price"] for item in cart)
        
        checkout_text = (
            f"💳 *Order Checkout & Payment Verification*\n\n"
            f"Total Amount Due: *₦{total:,}*\n\n"
            f"Please transfer to our official account:\n"
            f"🏦 *Bank:* Opay\n"
            f"📌 *Account Number:* `9099959259`\n"
            f"👤 *Account Name:* Clinton Ojeaga\n\n"
            f"📸 **Mandatory Step:** Please **upload your payment receipt screenshot here in the chat**, along with your delivery address and phone number to complete your order!"
        )
        await query.edit_message_text(checkout_text, parse_mode="Markdown")
        
    elif data == "create_custom_scent":
        if user_id not in USER_SESSIONS:
            USER_SESSIONS[user_id] = {"cart": [], "custom_mode": False, "checkout_mode": False}
        USER_SESSIONS[user_id]["custom_mode"] = True
        
        await query.edit_message_text(
            "🧪 *BABY BOY Custom Fragrance Request*\n\n"
            "Please describe the exact scent you want in detail (e.g., _'Rich woody scent with sweet vanilla and smoky leather'_).\n\n"
            "⚠️ **Important:** Kindly include your **Telegram Username** and **Phone Number** in your message so our master curator can contact you directly!\n\n"
            "✍️ *Type your description & contact info right here in the chat:*",
            parse_mode="Markdown"
        )
        
    elif data == "support":
        support_text = (
            "📞 *BABY BOY Concierge Support*\n\n"
            "Need assistance with custom blending, wholesale orders, or tracking? Reach out directly to our lead curator:\n\n"
            "📱 *Phone / WhatsApp:* `+2349099959259`\n"
            "💬 *Telegram:* @ambIntegrity"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(support_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "main_menu":
        if user_id in USER_SESSIONS:
            USER_SESSIONS[user_id]["custom_mode"] = False
            USER_SESSIONS[user_id]["checkout_mode"] = False
        await start(update, context)

# --- MESSAGE ROUTER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sender = update.effective_user
    session = USER_SESSIONS.get(user_id, {})
    
    # 1. Custom Scent Request Handler
    if session.get("custom_mode"):
        session["custom_mode"] = False
        user_text = update.message.text or "Media provided"
        
        if ADMIN_CHAT_ID:
            try:
                admin_msg = (
                    f"🧪 *NEW CUSTOM SCENT REQUEST!*\n\n"
                    f"👤 *From:* {sender.first_name} (@{sender.username or 'No Username'})\n"
                    f"🆔 *User ID:* `{user_id}`\n\n"
                    f"📝 *Details:*\n{user_text}"
                )
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Admin custom scent forward error: {e}")
        
        keyboard = [[InlineKeyboardButton("👑 Return to Main Menu", callback_data="main_menu")]]
        await update.message.reply_text(
            "✅ *Custom Scent Request Submitted!*\n\nSent directly to our admin team. We will review and contact you shortly!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # 2. Checkout Receipt Upload Handler
    if session.get("checkout_mode"):
        session["checkout_mode"] = False
        cart = session.get("cart", [])
        total = sum(item["price"] for item in cart)
        
        items_summary = "\n".join([f"• {item['name']} - ₦{item['price']:,}" for item in cart]) if cart else "Cart Items"
        
        if ADMIN_CHAT_ID:
            try:
                order_summary = (
                    f"🚨 *NEW ORDER & PAYMENT SUBMISSION!*\n\n"
                    f"👤 *Customer:* {sender.first_name} (@{sender.username or 'No Username'})\n"
                    f"🆔 *User ID:* `{user_id}`\n\n"
                    f"🛒 *Items Ordered:*\n{items_summary}\n\n"
                    f"💰 *Total Amount:* ₦{total:,}\n\n"
                    f"👇 *Attached Payment Receipt / Details Below:*"
                )
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_summary, parse_mode="Markdown")
                await context.bot.forward_message(
                    chat_id=ADMIN_CHAT_ID,
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                logger.error(f"Admin order forward error: {e}")
        
        session["cart"] = []
        
        keyboard = [[InlineKeyboardButton("👑 Return to Main Menu", callback_data="main_menu")]]
        await update.message.reply_text(
            "✅ *Order & Receipt Submitted Successfully!*\n\n"
            "Your payment receipt and order details have been forwarded to our admin for bank verification. "
            "We will reach out to you once confirmed!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # Default fallback forwarding
    if ADMIN_CHAT_ID:
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            await update.message.reply_text("📥 *Message received!* Our admin team will review it shortly.", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Forward error: {e}")
    else:
        await update.message.reply_text("Tap /start to open the BABY BOY main menu.")

# --- FASTAPI SERVER ---
app = FastAPI()

@app.api_route("/", methods=["GET", "HEAD", "POST"])
def health_check():
    return {"status": "BABY BOY Bot is online 24/7"}

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logger.info("FastAPI Web Server started in background.")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No Telegram Bot Token found!")
    else:
        application = Application.builder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
        
        logger.info("Telegram Bot is polling on main thread...")
        application.run_polling(drop_pending_updates=True)
