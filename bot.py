import logging
import json
import os
import aiohttp
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)
from web3 import Web3
from eth_account import Account
import secrets
from config import (
    TELEGRAM_BOT_TOKEN, 
    MONAD_RPC_URL, 
    EXPLORER_URL,
    CHAIN_ID,
    NATIVE_SYMBOL
)
import time

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL))

# User data storage
USERS_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()

def get_main_menu_keyboard():
    """Create the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🛒 Buy a Token", callback_data="buy_token"),
            InlineKeyboardButton("💰 Sell a Token", callback_data="sell_token")
        ],
        [
            InlineKeyboardButton("👛 Wallets", callback_data="wallets"),
            InlineKeyboardButton("📊 Portfolio", callback_data="portfolio")
        ],
        [
            InlineKeyboardButton("👥 Referral", callback_data="referral"),
            InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("📋 Manage Orders", callback_data="manage_orders"),
            InlineKeyboardButton("⚙️ Config", callback_data="config")
        ],
        [
            InlineKeyboardButton("📖 Trading Bot Guide", callback_data="guide")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wallet_menu_keyboard():
    """Create the wallet management inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("➕ New Wallet", callback_data="new_wallet"),
            InlineKeyboardButton("➕ New X Wallets", callback_data="new_x_wallets")
        ],
        [
            InlineKeyboardButton("🔑 Import Wallet", callback_data="import_wallet"),
            InlineKeyboardButton("🗑️ Delete Wallet", callback_data="delete_wallet")
        ],
        [
            InlineKeyboardButton("👁️ Show Private Key", callback_data="show_private_key")
        ],
        [
            InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_withdraw_menu_keyboard(selected_wallet=None):
    """Create the withdraw menu keyboard."""
    keyboard = []
    
    if selected_wallet:
        keyboard.append([
            InlineKeyboardButton("💰 Withdraw $MON", callback_data="withdraw_mon"),
            InlineKeyboardButton("🪙 Withdraw Tokens", callback_data="withdraw_tokens")
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_wallet_selection_keyboard(user_id: str, action: str):
    """Create keyboard for wallet selection."""
    keyboard = []
    if user_id in users and users[user_id]["wallets"]:
        for i, wallet in enumerate(users[user_id]["wallets"]):
            address = wallet["address"]
            short_address = f"{address[:6]}...{address[-4:]}"
            keyboard.append([
                InlineKeyboardButton(
                    f"💼 {short_address}",
                    callback_data=f"select_wallet_{action}_{i}"
                )
            ])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def generate_new_wallet():
    """Generate a new wallet with private key."""
    private_key = secrets.token_hex(32)
    account = Account.from_key(private_key)
    return {
        "address": account.address,
        "private_key": private_key,
        "encrypted_key": "encrypted_" + private_key  # Use proper encryption in production
    }

def start(update: Update, context: CallbackContext):
    """Send welcome message and main menu when the command /start is issued."""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Anonymous"
    
    is_new_user = user_id not in users
    
    if is_new_user:
        # Generate new wallet for new users
        new_wallet = generate_new_wallet()
        users[user_id] = {
            "username": username,
            "wallets": [new_wallet],
            "settings": {
                "slippage": 1.0,
                "auto_slippage": False,
                "gas_settings": "standard"
            }
        }
        save_users(users)
        
        # Send private key securely
        private_key_message = (
            "🔐 Your Wallet Has Been Generated!\n\n"
            "⚠️ IMPORTANT: Save this information securely!\n\n"
            f"Private Key: `{new_wallet['private_key']}`\n\n"
            "⚠️ WARNING:\n"
            "• Never share your private key\n"
            "• Store it safely\n"
            "• We will delete this message in 60 seconds"
        )
        key_msg = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=private_key_message,
            parse_mode='Markdown'
        )
        # Delete private key message after 60 seconds
        context.job_queue.run_once(
            lambda ctx: key_msg.delete(),
            60
        )
    
    # Get user's primary wallet address
    primary_wallet = users[user_id]["wallets"][0]["address"]
    
    welcome_text = (
        "Welcome to Monad Sniper Bot! 🚀\n\n"
        "Trade tokens effortlessly on the Monad Blockchain—fast, secure, and reliable.\n\n"
        f"🏦 Your Wallet:\n`{primary_wallet}`\n\n"
        "💰 Balance: 0 $MON\n\n"
        "More blockchain support coming soon...\n\n"
        "Bonus: Refer friends and earn UP TO 50% of Platform Revenue!"
    )
    
    if is_new_user:
        welcome_text += "\n\n⚠️ New wallet generated! Check above message for private key!"
    
    update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

def show_wallets(update: Update, context: CallbackContext):
    """Show wallet management interface."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    text = "👛 Wallets Management\n\n"
    if user_id in users and users[user_id]["wallets"]:
        text += "Connected Wallets:\n"
        for i, wallet in enumerate(users[user_id]["wallets"], 1):
            balance = "0.0"  # You can add balance fetching here
            text += f"{i}. `{wallet['address'][:6]}...{wallet['address'][-4:]}`\n"
            text += f"   Balance: {balance} {NATIVE_SYMBOL}\n\n"
    else:
        text += "No wallets connected. Create or import a wallet to start trading!\n\n"
    
    text += "Choose an option below:"
    
    query.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_wallet_menu_keyboard()
    )

def handle_new_wallet(update: Update, context: CallbackContext):
    """Handle new wallet creation."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    new_wallet = generate_new_wallet()
    
    if user_id not in users:
        users[user_id] = {
            "username": query.from_user.username or "Anonymous",
            "wallets": [],
            "settings": {
                "slippage": 1.0,
                "auto_slippage": False,
                "gas_settings": "standard"
            }
        }
    
    users[user_id]["wallets"].append(new_wallet)
    save_users(users)
    
    # Send private key securely
    private_key_message = (
        "🔐 Your New Wallet Has Been Generated!\n\n"
        "⚠️ IMPORTANT: Save this information securely!\n\n"
        f"Address: `{new_wallet['address']}`\n"
        f"Private Key: `{new_wallet['private_key']}`\n\n"
        "⚠️ WARNING:\n"
        "• Never share your private key\n"
        "• Store it safely\n"
        "• We will delete this message in 60 seconds"
    )
    
    key_msg = context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=private_key_message,
        parse_mode='Markdown'
    )
    
    # Delete private key message after 60 seconds
    context.job_queue.run_once(
        lambda ctx: key_msg.delete(),
        60
    )
    
    # Update the wallet list display
    show_wallets(update, context)

def handle_new_x_wallets(update: Update, context: CallbackContext):
    """Handle creation of multiple wallets."""
    query = update.callback_query
    
    # Ask for the number of wallets
    text = (
        "How many wallets would you like to create?\n\n"
        "Reply with a number between 1 and 10."
    )
    
    query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back", callback_data="wallets")
        ]])
    )
    
    # Set the next state to handle the number input
    context.user_data['waiting_for'] = 'num_wallets'

def handle_import_wallet(update: Update, context: CallbackContext):
    """Handle wallet import."""
    query = update.callback_query
    
    text = (
        "To import a wallet, please send your private key.\n\n"
        "⚠️ WARNING: Only send your private key in a private message, never in a group!\n\n"
        "Reply with your private key or click Back to cancel."
    )
    
    query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back", callback_data="wallets")
        ]])
    )
    
    # Set the next state to handle the private key input
    context.user_data['waiting_for'] = 'private_key'

def handle_delete_wallet(update: Update, context: CallbackContext):
    """Handle wallet deletion."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or not users[user_id]["wallets"]:
        query.message.edit_text(
            "You don't have any wallets to delete.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="wallets")
            ]])
        )
        return
    
    # Create keyboard with all user's wallets
    keyboard = []
    for i, wallet in enumerate(users[user_id]["wallets"]):
        address = wallet["address"]
        short_address = f"{address[:6]}...{address[-4:]}"
        keyboard.append([
            InlineKeyboardButton(
                f"💼 {short_address}",
                callback_data=f"confirm_delete_{i}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="wallets")])
    
    query.message.edit_text(
        "Select a wallet to delete:\n\n"
        "⚠️ Warning: This action cannot be undone!\n"
        "Make sure you have backed up any important wallets.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def confirm_delete_wallet(update: Update, context: CallbackContext, wallet_index: int):
    """Confirm and process wallet deletion."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
        query.message.edit_text(
            "Invalid wallet selection.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="wallets")
            ]])
        )
        return
    
    # Get wallet address for display
    wallet = users[user_id]["wallets"][wallet_index]
    address = wallet["address"]
    short_address = f"{address[:6]}...{address[-4:]}"
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"execute_delete_{wallet_index}"),
            InlineKeyboardButton("❌ No, Cancel", callback_data="delete_wallet")
        ]
    ]
    
    query.message.edit_text(
        f"Are you sure you want to delete wallet:\n\n"
        f"`{short_address}`?\n\n"
        "⚠️ This action cannot be undone!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def execute_delete_wallet(update: Update, context: CallbackContext, wallet_index: int):
    """Execute the wallet deletion."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
        query.message.edit_text(
            "Invalid wallet selection.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="wallets")
            ]])
        )
        return
    
    # Remove the wallet
    deleted_wallet = users[user_id]["wallets"].pop(wallet_index)
    save_users(users)
    
    # Show success message
    address = deleted_wallet["address"]
    short_address = f"{address[:6]}...{address[-4:]}"
    query.message.edit_text(
        f"✅ Successfully deleted wallet:\n`{short_address}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Wallets", callback_data="wallets")
        ]])
    )

def handle_show_private_key(update: Update, context: CallbackContext):
    """Handle showing private key."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or not users[user_id]["wallets"]:
        query.message.edit_text(
            "You don't have any wallets.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="wallets")
            ]])
        )
        return
    
    # Create keyboard with all user's wallets
    keyboard = []
    for i, wallet in enumerate(users[user_id]["wallets"]):
        address = wallet["address"]
        short_address = f"{address[:6]}...{address[-4:]}"
        keyboard.append([
            InlineKeyboardButton(
                f"🔑 {short_address}",
                callback_data=f"confirm_show_key_{i}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="wallets")])
    
    query.message.edit_text(
        "Select a wallet to view its private key:\n\n"
        "⚠️ Warning:\n"
        "• Never share your private key with anyone\n"
        "• The key will be shown for 60 seconds only\n"
        "• Make sure no one can see your screen",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def confirm_show_private_key(update: Update, context: CallbackContext, wallet_index: int):
    """Show confirmation before displaying private key."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
        query.message.edit_text(
            "Invalid wallet selection.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="wallets")
            ]])
        )
        return
    
    # Get wallet address for display
    wallet = users[user_id]["wallets"][wallet_index]
    address = wallet["address"]
    short_address = f"{address[:6]}...{address[-4:]}"
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Show Key", callback_data=f"execute_show_key_{wallet_index}"),
            InlineKeyboardButton("❌ No, Cancel", callback_data="show_private_key")
        ]
    ]
    
    query.message.edit_text(
        f"Are you sure you want to view the private key for:\n\n"
        f"`{short_address}`?\n\n"
        "⚠️ Warning:\n"
        "• Make sure you are in a private place\n"
        "• No one should be able to see your screen\n"
        "• Never share your private key with anyone",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def execute_show_private_key(update: Update, context: CallbackContext, wallet_index: int):
    """Show the private key with security measures."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
        query.message.edit_text(
            "Invalid wallet selection.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="wallets")
            ]])
        )
        return
    
    # Get wallet info
    wallet = users[user_id]["wallets"][wallet_index]
    address = wallet["address"]
    private_key = wallet["private_key"]
    
    # Create the private key message
    key_message = (
        "🔐 Wallet Private Key\n\n"
        f"Address: `{address}`\n"
        f"Private Key: `{private_key}`\n\n"
        "⚠️ IMPORTANT:\n"
        "• Never share this key with anyone\n"
        "• Store it securely\n"
        "• This message will be deleted in 60 seconds"
    )
    
    # Send private key message
    key_msg = context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=key_message,
        parse_mode='Markdown'
    )
    
    # Return to wallet menu
    query.message.edit_text(
        "✅ Private key has been sent in a separate message.\n"
        "It will be automatically deleted in 60 seconds.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Wallets", callback_data="wallets")
        ]])
    )
    
    # Delete private key message after 60 seconds
    context.job_queue.run_once(
        lambda ctx: key_msg.delete(),
        60
    )

def handle_withdraw(update: Update, context: CallbackContext):
    """Handle the withdraw command."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or not users[user_id]["wallets"]:
        query.message.edit_text(
            "You need to create or import a wallet first!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
            ]])
        )
        return
    
    text = (
        "🏧 Withdraw\n\n"
        "Choose a wallet to withdraw from:"
    )
    
    query.message.edit_text(
        text,
        reply_markup=get_wallet_selection_keyboard(user_id, "withdraw")
    )

def handle_wallet_selection_for_withdraw(update: Update, context: CallbackContext, wallet_index: int):
    """Handle wallet selection for withdrawal."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
        query.message.edit_text(
            "Invalid wallet selection.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
            ]])
        )
        return
    
    wallet = users[user_id]["wallets"][wallet_index]
    address = wallet["address"]
    short_address = f"{address[:6]}...{address[-4:]}"
    
    # Store selected wallet index in context
    context.user_data['selected_wallet_index'] = wallet_index
    
    text = (
        "🏧 Withdraw\n\n"
        f"Selected wallet: 💼 {short_address}\n\n"
        "Choose what to withdraw:"
    )
    
    query.message.edit_text(
        text,
        reply_markup=get_withdraw_menu_keyboard(selected_wallet=True)
    )

def handle_mon_withdrawal(update: Update, context: CallbackContext):
    """Handle $MON withdrawal."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    wallet_index = context.user_data.get('selected_wallet_index')
    
    if wallet_index is None or user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
        query.message.edit_text(
            "Please select a wallet first.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
            ]])
        )
        return
    
    # Store withdrawal type in context
    context.user_data['withdrawal_type'] = 'mon'
    
    text = (
        "💰 Withdraw $MON\n\n"
        "Please enter the amount of $MON to withdraw:\n\n"
        "Example: `1.5`"
    )
    
    # Add back button
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="withdraw")]]
    
    query.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Set state to wait for amount
    context.user_data['waiting_for'] = 'withdrawal_amount'

def handle_token_withdrawal(update: Update, context: CallbackContext):
    """Handle token withdrawal."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    wallet_index = context.user_data.get('selected_wallet_index')
    
    if wallet_index is None or user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
        query.message.edit_text(
            "Please select a wallet first.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
            ]])
        )
        return
    
    # Store withdrawal type in context
    context.user_data['withdrawal_type'] = 'token'
    
    text = (
        "🪙 Withdraw Tokens\n\n"
        "Please enter the token contract address:\n\n"
        "Example: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`"
    )
    
    # Add back button
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="withdraw")]]
    
    query.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Set state to wait for token address
    context.user_data['waiting_for'] = 'token_address'

def handle_text_input(update: Update, context: CallbackContext):
    """Handle text input for wallet operations and token contract addresses."""
    # Check if the text looks like a token contract address
    text = update.message.text.strip()
    if text.startswith("0x") and len(text) >= 40:  # Basic check for contract address format
        # Show loading message
        loading_msg = update.message.reply_text("⏳ Fetching token information...")
        
        # Create asyncio event loop and run token info fetch
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        token_data = loop.run_until_complete(fetch_token_info(text))
        loop.close()
        
        if not token_data:
            loading_msg.edit_text(
                "❌ Error fetching token information.\n\n"
                "This could be due to:\n"
                "• Invalid token contract\n"
                "• Contract not verified\n"
                "• Network issues\n"
                "• Token not listed on Kuru DEX"
            )
            return
        
        # Check if user has selected a wallet
        user_id = str(update.effective_user.id)
        has_selected_wallet = (
            user_id in users and 
            users[user_id]["wallets"] and 
            context.user_data.get('selected_trading_wallet') is not None
        )
        
        # Format and display token info
        text = format_token_info(token_data)
        loading_msg.edit_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_token_info_keyboard(has_selected_wallet)
        )
        return

    if 'waiting_for' not in context.user_data:
        return

    waiting_for = context.user_data['waiting_for']
    user_id = str(update.effective_user.id)
    
    if waiting_for == 'num_wallets':
        try:
            num_wallets = int(update.message.text)
            if 1 <= num_wallets <= 10:
                # Create the specified number of wallets
                for _ in range(num_wallets):
                    new_wallet = generate_new_wallet()
                    if user_id not in users:
                        users[user_id] = {
                            "username": update.effective_user.username or "Anonymous",
                            "wallets": [],
                            "settings": {
                                "slippage": 1.0,
                                "auto_slippage": False,
                                "gas_settings": "standard"
                            }
                        }
                    users[user_id]["wallets"].append(new_wallet)
                
                save_users(users)
                
                # Send wallet info
                wallet_info = "🔐 Your New Wallets:\n\n"
                for wallet in users[user_id]["wallets"][-num_wallets:]:
                    wallet_info += f"Address: `{wallet['address']}`\n"
                    wallet_info += f"Private Key: `{wallet['private_key']}`\n\n"
                
                wallet_info += "⚠️ WARNING: Save these keys securely! Message will be deleted in 60 seconds."
                
                key_msg = update.message.reply_text(
                    wallet_info,
                    parse_mode='Markdown'
                )
                
                # Delete private key message after 60 seconds
                context.job_queue.run_once(
                    lambda ctx: key_msg.delete(),
                    60
                )
                
                # Show updated wallet list
                update.message.reply_text(
                    "Select an option:",
                    reply_markup=get_wallet_menu_keyboard()
                )
            else:
                update.message.reply_text(
                    "Please enter a number between 1 and 10.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back", callback_data="wallets")
                    ]])
                )
                return
                
        except ValueError:
            update.message.reply_text(
                "Please enter a valid number between 1 and 10.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="wallets")
                ]])
            )
            return
            
    elif waiting_for == 'private_key':
        try:
            private_key = update.message.text
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            account = Account.from_key(private_key)
            new_wallet = {
                "address": account.address,
                "private_key": private_key,
                "encrypted_key": "encrypted_" + private_key  # Use proper encryption in production
            }
            
            if user_id not in users:
                users[user_id] = {
                    "username": update.effective_user.username or "Anonymous",
                    "wallets": [],
                    "settings": {
                        "slippage": 1.0,
                        "auto_slippage": False,
                        "gas_settings": "standard"
                    }
                }
            
            users[user_id]["wallets"].append(new_wallet)
            save_users(users)
            
            # Delete the message containing the private key
            update.message.delete()
            
            update.message.reply_text(
                "✅ Wallet imported successfully!",
                reply_markup=get_wallet_menu_keyboard()
            )
            
        except Exception as e:
            update.message.reply_text(
                "❌ Invalid private key. Please try again or go back.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="wallets")
                ]])
            )
            return
            
    elif waiting_for == 'withdrawal_amount':
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            # Store amount in context
            context.user_data['withdrawal_amount'] = amount
            
            # Ask for destination address
            text = (
                "Enter the destination address to receive the funds:\n\n"
                "Example: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`"
            )
            
            update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            
            # Update state to wait for address
            context.user_data['waiting_for'] = 'withdrawal_address'
            
        except ValueError:
            update.message.reply_text(
                "❌ Invalid amount. Please enter a valid positive number.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            return
            
    elif waiting_for == 'withdrawal_address':
        try:
            to_address = update.message.text
            if not w3.is_address(to_address):
                raise ValueError("Invalid address")
            
            amount = context.user_data.get('withdrawal_amount')
            if amount is None:
                raise ValueError("Amount not set")
            
            wallet_index = context.user_data.get('selected_wallet_index')
            if wallet_index is None or user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
                raise ValueError("Invalid wallet")
            
            # Here you would implement the actual withdrawal logic
            # For now, we'll just show a success message
            update.message.reply_text(
                f"✅ Withdrawal request submitted!\n\n"
                f"Amount: {amount} $MON\n"
                f"To: {to_address[:6]}...{to_address[-4:]}\n\n"
                "Transaction is being processed...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")
                ]])
            )
            
            # Clear stored data
            if 'withdrawal_amount' in context.user_data:
                del context.user_data['withdrawal_amount']
            
        except ValueError as e:
            update.message.reply_text(
                "❌ Invalid address. Please enter a valid Ethereum address.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            return
            
    elif waiting_for == 'token_address':
        try:
            token_address = update.message.text
            if not w3.is_address(token_address):
                raise ValueError("Invalid token address")
            
            # Store token address in context
            context.user_data['token_address'] = token_address
            
            # Ask for amount
            text = (
                "Enter the amount to withdraw:\n\n"
                "Example: `100`"
            )
            
            update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            
            # Update state to wait for token amount
            context.user_data['waiting_for'] = 'token_amount'
            
        except ValueError:
            update.message.reply_text(
                "❌ Invalid token address. Please enter a valid contract address.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            return
            
    elif waiting_for == 'token_amount':
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            # Store amount in context
            context.user_data['token_amount'] = amount
            
            # Ask for destination address
            text = (
                "Enter the destination address to receive the tokens:\n\n"
                "Example: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`"
            )
            
            update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            
            # Update state to wait for address
            context.user_data['waiting_for'] = 'token_destination_address'
            
        except ValueError:
            update.message.reply_text(
                "❌ Invalid amount. Please enter a valid positive number.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            return
            
    elif waiting_for == 'token_destination_address':
        try:
            to_address = update.message.text
            if not w3.is_address(to_address):
                raise ValueError("Invalid address")
            
            token_address = context.user_data.get('token_address')
            amount = context.user_data.get('token_amount')
            if token_address is None or amount is None:
                raise ValueError("Missing token information")
            
            wallet_index = context.user_data.get('selected_wallet_index')
            if wallet_index is None or user_id not in users or wallet_index >= len(users[user_id]["wallets"]):
                raise ValueError("Invalid wallet")
            
            # Here you would implement the actual token withdrawal logic
            # For now, we'll just show a success message
            update.message.reply_text(
                f"✅ Token withdrawal request submitted!\n\n"
                f"Token: {token_address[:6]}...{token_address[-4:]}\n"
                f"Amount: {amount}\n"
                f"To: {to_address[:6]}...{to_address[-4:]}\n\n"
                "Transaction is being processed...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")
                ]])
            )
            
            # Clear stored data
            for key in ['token_address', 'token_amount']:
                if key in context.user_data:
                    del context.user_data[key]
            
        except ValueError as e:
            update.message.reply_text(
                "❌ Invalid address. Please enter a valid Ethereum address.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="withdraw")
                ]])
            )
            return
    
    # Clear the waiting state
    del context.user_data['waiting_for']

def get_manage_orders_keyboard():
    """Create the manage orders menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📋 Active Orders", callback_data="active_orders"),
            InlineKeyboardButton("📜 Order History", callback_data="order_history")
        ],
        [
            InlineKeyboardButton("❌ Cancel Orders", callback_data="cancel_orders")
        ],
        [
            InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_order_list_keyboard(orders, action_prefix, page=0, items_per_page=5):
    """Create keyboard for list of orders with pagination."""
    keyboard = []
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    
    # Add order buttons
    for i, order in enumerate(orders[start_idx:end_idx], start=start_idx):
        order_type = "Buy" if order.get("type") == "buy" else "Sell"
        token_symbol = order.get("token_symbol", "Unknown")
        amount = order.get("amount", 0)
        short_id = order.get("id", "")[:8]
        
        button_text = f"{order_type} {amount} {token_symbol} (#{short_id})"
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"{action_prefix}_{i}"
            )
        ])
    
    # Add pagination buttons if needed
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"{action_prefix}_page_{page-1}")
        )
    if end_idx < len(orders):
        nav_buttons.append(
            InlineKeyboardButton("➡️ Next", callback_data=f"{action_prefix}_page_{page+1}")
        )
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="manage_orders")])
    
    return InlineKeyboardMarkup(keyboard)

def handle_manage_orders(update: Update, context: CallbackContext):
    """Handle the manage orders menu."""
    query = update.callback_query
    
    text = (
        "📊 Manage Orders\n\n"
        "• View your active orders\n"
        "• Check your order history\n"
        "• Cancel active orders\n\n"
        "Select an option:"
    )
    
    query.message.edit_text(
        text,
        reply_markup=get_manage_orders_keyboard()
    )

def handle_active_orders(update: Update, context: CallbackContext):
    """Show active orders."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    page = context.user_data.get('active_orders_page', 0)
    
    # Get active orders from user data
    # This would normally come from your order tracking system
    active_orders = context.user_data.get('active_orders', [])
    
    if not active_orders:
        query.message.edit_text(
            "You have no active orders.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="manage_orders")
            ]])
        )
        return
    
    text = (
        "📋 Active Orders\n\n"
        "Select an order to view details:"
    )
    
    query.message.edit_text(
        text,
        reply_markup=get_order_list_keyboard(active_orders, "view_active", page)
    )

def handle_order_history(update: Update, context: CallbackContext):
    """Show order history."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    page = context.user_data.get('history_page', 0)
    
    # Get order history from user data
    # This would normally come from your order tracking system
    order_history = context.user_data.get('order_history', [])
    
    if not order_history:
        query.message.edit_text(
            "You have no order history.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="manage_orders")
            ]])
        )
        return
    
    text = (
        "📜 Order History\n\n"
        "Select an order to view details:"
    )
    
    query.message.edit_text(
        text,
        reply_markup=get_order_list_keyboard(order_history, "view_history", page)
    )

def handle_cancel_orders(update: Update, context: CallbackContext):
    """Show orders that can be cancelled."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    page = context.user_data.get('cancel_page', 0)
    
    # Get active orders that can be cancelled
    # This would normally come from your order tracking system
    active_orders = context.user_data.get('active_orders', [])
    
    if not active_orders:
        query.message.edit_text(
            "You have no active orders to cancel.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="manage_orders")
            ]])
        )
        return
    
    text = (
        "❌ Cancel Orders\n\n"
        "Select an order to cancel:"
    )
    
    query.message.edit_text(
        text,
        reply_markup=get_order_list_keyboard(active_orders, "cancel", page)
    )

def show_order_details(update: Update, context: CallbackContext, order, is_active=True):
    """Show details of a specific order."""
    query = update.callback_query
    
    # Format order details
    order_type = "Buy" if order.get("type") == "buy" else "Sell"
    token_symbol = order.get("token_symbol", "Unknown")
    amount = order.get("amount", 0)
    price = order.get("price", 0)
    status = order.get("status", "Unknown")
    order_id = order.get("id", "Unknown")
    
    text = (
        f"Order #{order_id[:8]}\n\n"
        f"Type: {order_type}\n"
        f"Token: {token_symbol}\n"
        f"Amount: {amount}\n"
        f"Price: {price} $MON\n"
        f"Status: {status}\n"
    )
    
    # Add transaction hash if available
    tx_hash = order.get("tx_hash")
    if tx_hash:
        text += f"\nTx: `{tx_hash}`"
    
    # Create keyboard based on order type
    keyboard = []
    if is_active:
        keyboard.append([
            InlineKeyboardButton("❌ Cancel Order", callback_data=f"confirm_cancel_{order_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="active_orders" if is_active else "order_history")
    ])
    
    query.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_order_cancellation(update: Update, context: CallbackContext, order_id):
    """Handle the order cancellation process."""
    query = update.callback_query
    
    # Here you would implement the actual order cancellation logic
    # For now, we'll just show a success message
    
    text = (
        "✅ Order cancellation submitted!\n\n"
        f"Order #{order_id[:8]} is being cancelled.\n"
        "This may take a few moments to process."
    )
    
    query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Orders", callback_data="active_orders")
        ]])
    )

def get_token_info_keyboard(has_selected_wallet=False):
    """Create the token info and trading keyboard."""
    keyboard = []
    
    # Top row - Vision and Chart
    keyboard.append([
        InlineKeyboardButton("👁️ Sui Vision", callback_data="sui_vision"),
        InlineKeyboardButton("📊 Chart", callback_data="show_chart")
    ])
    
    # Trading options
    if has_selected_wallet:
        keyboard.append([
            InlineKeyboardButton("📈 Limit Order", callback_data="limit_order"),
            InlineKeyboardButton("📊 Portfolio", callback_data="portfolio")
        ])
        keyboard.append([
            InlineKeyboardButton("⚙️ Manage Order", callback_data="manage_orders")
        ])
        keyboard.append([
            InlineKeyboardButton("💼 Select wallets", callback_data="select_trading_wallet")
        ])
        keyboard.append([
            InlineKeyboardButton("⚡ Slippage: 1%", callback_data="set_slippage"),
            InlineKeyboardButton("⛽ Gas: 750 MIST", callback_data="set_gas")
        ])
        keyboard.append([
            InlineKeyboardButton("🛒 Buy", callback_data="buy_token"),
            InlineKeyboardButton("💰 Sell", callback_data="sell_token")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("💼 Select Wallet to Trade", callback_data="select_trading_wallet")
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def format_token_info(token_data):
    """Format token information for display."""
    return (
        f"🪙 {token_data.get('name', 'Unknown')} - ${token_data.get('symbol', 'Unknown')}\n\n"
        f"📍 Contract Address:\n`{token_data.get('address', 'Unknown')}`\n\n"
        f"⛓️ Chain: {token_data.get('chain', 'Unknown')} 💧\n"
        f"💱 Exchange: {token_data.get('exchange', 'Unknown')}\n\n"
        f"💵 Price: {token_data.get('price', '0')} {token_data.get('base_currency', 'SUI')}\n"
        f"💰 Market Cap: ${token_data.get('market_cap', '0')}\n"
        f"💧 Liquidity: ${token_data.get('liquidity', '0')} "
        f"({token_data.get('liquidity_tokens', '')})\n"
        f"🔥 LP Burned: {token_data.get('lp_burned', '0%')}\n"
        f"⏰ Pair Age: {token_data.get('pair_age', 'Unknown')}\n\n"
        f"🔒 Security Check:\n"
        f"• {token_data.get('security_mintable', '❌ Not Mintable')}\n"
        f"• {token_data.get('security_blacklist', '✅ Cannot be blacklisted')}\n"
        f"• {token_data.get('security_modifiable', '✅ Contract is not modifiable')}\n\n"
        f"🌐 Social Links:\n{token_data.get('socials', 'No social links available')}"
    )

async def fetch_token_info(token_address):
    """Fetch token information from Monad blockchain and Kuru DEX."""
    try:
        # Initialize Web3 connection to Monad
        w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL))
        
        # Load token contract ABI - standard ERC20 ABI
        token_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        # Create contract instance
        token_contract = w3.eth.contract(address=token_address, abi=token_abi)
        
        # Fetch basic token info from contract
        token_name = token_contract.functions.name().call()
        token_symbol = token_contract.functions.symbol().call()
        token_decimals = token_contract.functions.decimals().call()
        total_supply = token_contract.functions.totalSupply().call()
        
        # Fetch price and liquidity info from Kuru DEX API
        kuru_api_url = "https://api.kuru.io"  # Changed from testnet to mainnet
        
        async with aiohttp.ClientSession() as session:
            # Get token info
            token_info_url = f"{kuru_api_url}/v1/tokens/{token_address}"
            async with session.get(token_info_url) as response:
                if response.status == 200:
                    token_data = await response.json()
                    price = token_data.get('price', '0')
                    liquidity = token_data.get('liquidity', '0')
                    pair_created_at = token_data.get('pairCreatedAt')
                else:
                    price = "0"
                    liquidity = "0"
                    pair_created_at = None
            
            # Get pair info
            pair_info_url = f"{kuru_api_url}/v1/pairs/{token_address}"
            async with session.get(pair_info_url) as response:
                if response.status == 200:
                    pair_data = await response.json()
                    lp_info = pair_data.get('lpInfo', {})
                    total_lp = lp_info.get('totalSupply', '0')
                    burned_lp = lp_info.get('burnedAmount', '0')
                    token0_reserve = pair_data.get('reserve0', '0')
                    token1_reserve = pair_data.get('reserve1', '0')
                else:
                    total_lp = "0"
                    burned_lp = "0"
                    token0_reserve = "0"
                    token1_reserve = "0"
        
        # Calculate pair age if available
        if pair_created_at:
            current_time = int(time.time())
            pair_age = current_time - int(pair_created_at)
            days = pair_age // (24 * 3600)
            hours = (pair_age % (24 * 3600)) // 3600
            pair_age_str = f"{days} days, {hours} hours"
        else:
            pair_age_str = "Unknown"
        
        # Calculate LP burned percentage
        try:
            total_lp = float(total_lp)
            burned_lp = float(burned_lp)
            if total_lp > 0:
                burn_percentage = (burned_lp * 100) / total_lp
                lp_burned = f"{burn_percentage:.2f}%"
            else:
                lp_burned = "0%"
        except:
            lp_burned = "Unknown"
        
        # Format liquidity tokens
        try:
            token0_amount = w3.from_wei(int(token0_reserve), 'ether')
            token1_amount = w3.from_wei(int(token1_reserve), 'ether')
            liquidity_tokens = f"({token0_amount:.2f} MON + {token1_amount:.2f} {token_symbol})"
        except:
            liquidity_tokens = "Unknown"
        
        # Check security features
        is_mintable = False
        can_blacklist = False
        is_modifiable = False
        
        try:
            # Check if contract has mint function
            mint_function = token_contract.functions.mint
            is_mintable = True
        except:
            pass
            
        try:
            # Check if contract has blacklist function
            blacklist_function = token_contract.functions.blacklist
            can_blacklist = True
        except:
            pass
            
        try:
            # Check if contract has upgrade/modify function
            upgrade_function = token_contract.functions.upgrade
            is_modifiable = True
        except:
            pass
        
        # Format the token data
        token_data = {
            "name": token_name,
            "symbol": token_symbol,
            "address": token_address,
            "chain": "Monad",
            "exchange": "Kuru DEX",
            "price": f"{float(price):.8f}",
            "base_currency": "MON",
            "market_cap": f"{float(price) * float(total_supply) / (10 ** token_decimals):.2f}",
            "liquidity": liquidity,
            "liquidity_tokens": liquidity_tokens,
            "lp_burned": lp_burned,
            "pair_age": pair_age_str,
            "security_mintable": "⚠️ Token is mintable!" if is_mintable else "✅ Token is not mintable",
            "security_blacklist": "⚠️ Can be blacklisted!" if can_blacklist else "✅ Cannot be blacklisted",
            "security_modifiable": "⚠️ Contract is modifiable!" if is_modifiable else "✅ Contract is not modifiable",
            "socials": await fetch_token_socials(token_address, kuru_api_url)
        }
        
        return token_data
        
    except Exception as e:
        logger.error(f"Error fetching token info: {str(e)}")
        return None

async def fetch_token_socials(token_address, kuru_api_url):
    """Fetch token social links from Kuru DEX."""
    try:
        async with aiohttp.ClientSession() as session:
            # Get token social info from Kuru API
            social_url = f"{kuru_api_url}/v1/tokens/{token_address}/social"
            async with session.get(social_url) as response:
                if response.status == 200:
                    social_data = await response.json()
                    socials = []
                    
                    if social_data.get('website'):
                        socials.append(f"🌐 Website: {social_data['website']}")
                    if social_data.get('telegram'):
                        socials.append(f"📱 Telegram: {social_data['telegram']}")
                    if social_data.get('twitter'):
                        socials.append(f"🐦 Twitter: {social_data['twitter']}")
                    if social_data.get('discord'):
                        socials.append(f"💬 Discord: {social_data['discord']}")
                        
                    return "\n".join(socials) if socials else "No social links available"
                    
                return "Social links not available"
                
    except Exception as e:
        logger.error(f"Error fetching social links: {str(e)}")
        return "Error fetching social links"

async def handle_token_info(update: Update, context: CallbackContext, token_address=None):
    """Display token information and trading interface."""
    query = update.callback_query
    user_id = str(query.from_user.id if query else update.effective_user.id)
    
    if token_address:
        # Show loading message
        loading_message = "⏳ Fetching token information..."
        if query:
            await query.message.edit_text(loading_message)
        else:
            msg = await update.message.reply_text(loading_message)
        
        # Fetch token data
        token_data = await fetch_token_info(token_address)
        
        if not token_data:
            error_text = (
                "❌ Error fetching token information.\n\n"
                "This could be due to:\n"
                "• Invalid token contract\n"
                "• Contract not verified\n"
                "• Network issues\n"
                "• Token not listed on Kuru DEX"
            )
            if query:
                await query.message.edit_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
                    ]])
                )
            else:
                await msg.edit_text(error_text)
            return
    else:
        # Use example data for testing
        token_data = {
            "name": "SEED",
            "symbol": "$SEED",
            "address": "0x1e005d033d858a39ce1121c79cdb8acadd139ce4fa21c79cdb8acadd16513a03c9d4cebd",
            "chain": "Sui",
            "exchange": "Kuru DEX",
            "price": "0.0020",
            "base_currency": "SUI",
            "market_cap": "4.20M",
            "liquidity": "1.98K",
            "liquidity_tokens": "(376.33 SUI + 286.47K SEED)",
            "lp_burned": "0%",
            "pair_age": "14 days, 14 hours",
            "security_mintable": "⚠️ This token is still mintable!",
            "security_blacklist": "✅ Cannot be blacklisted",
            "security_modifiable": "✅ Contract is not modifiable",
            "socials": "🌐 Available on request"
        }
    
    # Check if user has selected a wallet
    has_selected_wallet = (
        user_id in users and 
        users[user_id]["wallets"] and 
        context.user_data.get('selected_trading_wallet') is not None
    )
    
    # Format and send token info
    text = format_token_info(token_data)
    
    if query:
        await query.message.edit_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_token_info_keyboard(has_selected_wallet)
        )
    else:
        if 'msg' in locals():
            await msg.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=get_token_info_keyboard(has_selected_wallet)
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=get_token_info_keyboard(has_selected_wallet)
            )

def handle_select_trading_wallet(update: Update, context: CallbackContext):
    """Handle wallet selection for trading."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in users or not users[user_id]["wallets"]:
        query.message.edit_text(
            "You need to create or import a wallet first!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("👛 Manage Wallets", callback_data="wallets")
            ]])
        )
        return
    
    # Create keyboard with user's wallets
    keyboard = []
    for i, wallet in enumerate(users[user_id]["wallets"]):
        address = wallet["address"]
        short_address = f"{address[:6]}...{address[-4:]}"
        balance = "0.00"  # You would fetch the actual balance here
        keyboard.append([
            InlineKeyboardButton(
                f"💼 {short_address} ({balance} SUI)",
                callback_data=f"select_trade_wallet_{i}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="token_info")])
    
    query.message.edit_text(
        "Select a wallet to trade with:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_set_slippage(update: Update, context: CallbackContext):
    """Handle slippage setting."""
    query = update.callback_query
    
    # Create slippage options
    keyboard = [
        [
            InlineKeyboardButton("0.5%", callback_data="set_slippage_0.5"),
            InlineKeyboardButton("1%", callback_data="set_slippage_1"),
            InlineKeyboardButton("2%", callback_data="set_slippage_2")
        ],
        [
            InlineKeyboardButton("3%", callback_data="set_slippage_3"),
            InlineKeyboardButton("5%", callback_data="set_slippage_5"),
            InlineKeyboardButton("Custom", callback_data="set_slippage_custom")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="token_info")]
    ]
    
    query.message.edit_text(
        "Select slippage tolerance:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_set_gas(update: Update, context: CallbackContext):
    """Handle gas price setting."""
    query = update.callback_query
    
    # Create gas options
    keyboard = [
        [
            InlineKeyboardButton("Standard (750)", callback_data="set_gas_750"),
            InlineKeyboardButton("Fast (1000)", callback_data="set_gas_1000")
        ],
        [
            InlineKeyboardButton("Rapid (1500)", callback_data="set_gas_1500"),
            InlineKeyboardButton("Custom", callback_data="set_gas_custom")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="token_info")]
    ]
    
    query.message.edit_text(
        "Select gas price (in MIST):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def button_callback(update: Update, context: CallbackContext):
    """Handle button presses."""
    query = update.callback_query
    query.answer()
    
    if query.data == "token_info":
        handle_token_info(update, context)
    elif query.data == "select_trading_wallet":
        handle_select_trading_wallet(update, context)
    elif query.data.startswith("select_trade_wallet_"):
        wallet_index = int(query.data.split("_")[-1])
        context.user_data['selected_trading_wallet'] = wallet_index
        handle_token_info(update, context)
    elif query.data == "set_slippage":
        handle_set_slippage(update, context)
    elif query.data.startswith("set_slippage_"):
        slippage = query.data.split("_")[-1]
        if slippage != "custom":
            context.user_data['slippage'] = float(slippage)
        handle_token_info(update, context)
    elif query.data == "set_gas":
        handle_set_gas(update, context)
    elif query.data == "manage_orders":
        handle_manage_orders(update, context)
    elif query.data == "active_orders":
        handle_active_orders(update, context)
    elif query.data == "order_history":
        handle_order_history(update, context)
    elif query.data == "cancel_orders":
        handle_cancel_orders(update, context)
    elif query.data.startswith("view_active_"):
        try:
            index = int(query.data.split("_")[-1])
            order = context.user_data.get('active_orders', [])[index]
            show_order_details(update, context, order, is_active=True)
        except (ValueError, IndexError):
            query.message.edit_text(
                "Error: Order not found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="active_orders")
                ]])
            )
    elif query.data.startswith("view_history_"):
        try:
            index = int(query.data.split("_")[-1])
            order = context.user_data.get('order_history', [])[index]
            show_order_details(update, context, order, is_active=False)
        except (ValueError, IndexError):
            query.message.edit_text(
                "Error: Order not found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="order_history")
                ]])
            )
    elif query.data.startswith("cancel_"):
        try:
            index = int(query.data.split("_")[-1])
            order = context.user_data.get('active_orders', [])[index]
            handle_order_cancellation(update, context, order.get("id", ""))
        except (ValueError, IndexError):
            query.message.edit_text(
                "Error: Order not found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="cancel_orders")
                ]])
            )
    elif query.data == "wallets":
        show_wallets(update, context)
    elif query.data == "new_wallet":
        handle_new_wallet(update, context)
    elif query.data == "new_x_wallets":
        handle_new_x_wallets(update, context)
    elif query.data == "import_wallet":
        handle_import_wallet(update, context)
    elif query.data == "delete_wallet":
        handle_delete_wallet(update, context)
    elif query.data == "show_private_key":
        handle_show_private_key(update, context)
    elif query.data.startswith("confirm_delete_"):
        wallet_index = int(query.data.split("_")[-1])
        confirm_delete_wallet(update, context, wallet_index)
    elif query.data.startswith("execute_delete_"):
        wallet_index = int(query.data.split("_")[-1])
        execute_delete_wallet(update, context, wallet_index)
    elif query.data.startswith("confirm_show_key_"):
        wallet_index = int(query.data.split("_")[-1])
        confirm_show_private_key(update, context, wallet_index)
    elif query.data.startswith("execute_show_key_"):
        wallet_index = int(query.data.split("_")[-1])
        execute_show_private_key(update, context, wallet_index)
    elif query.data == "withdraw":
        handle_withdraw(update, context)
    elif query.data.startswith("select_wallet_withdraw_"):
        wallet_index = int(query.data.split("_")[-1])
        handle_wallet_selection_for_withdraw(update, context, wallet_index)
    elif query.data == "withdraw_mon":
        handle_mon_withdrawal(update, context)
    elif query.data == "withdraw_tokens":
        handle_token_withdrawal(update, context)
    elif query.data == "main_menu":
        # Show main menu
        query.message.edit_text(
            "Welcome to Monad Sniper Bot! 🚀\n\nSelect an option:",
            reply_markup=get_main_menu_keyboard()
        )
    elif query.data == "config":
        show_config(update, context)
    elif query.data == "referral":
        show_referral(update, context)
    elif query.data == "portfolio":
        show_portfolio(update, context)
    elif query.data == "guide":
        show_guide(update, context)

def show_config(update: Update, context: CallbackContext):
    """Show configuration interface."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    settings = users[user_id]["settings"]
    
    text = (
        "⚙️ Configuration\n\n"
        f"Current Settings:\n"
        f"• Slippage: {settings['slippage']}%\n"
        f"• Auto Slippage: {'On' if settings['auto_slippage'] else 'Off'}\n"
        f"• Gas Settings: {settings['gas_settings'].title()}"
    )
    
    query.message.reply_text(text)

def show_referral(update: Update, context: CallbackContext):
    """Show referral information."""
    query = update.callback_query
    text = "👥 Referral Program\n\nShare your referral link to earn up to 50% of trading fees!"
    query.message.reply_text(text)

def show_portfolio(update: Update, context: CallbackContext):
    """Show portfolio information."""
    query = update.callback_query
    text = "📊 Portfolio\n\nConnect a wallet to view your portfolio."
    query.message.reply_text(text)

def show_guide(update: Update, context: CallbackContext):
    """Show bot guide."""
    query = update.callback_query
    text = "📖 Trading Bot Guide\n\nLearn how to use all features of the Monad Trading Bot."
    query.message.reply_text(text)

def main():
    """Start the bot."""
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("menu", start))  # Add menu command
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_input))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main() 