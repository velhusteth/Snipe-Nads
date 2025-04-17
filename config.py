import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# Blockchain Configuration
MONAD_RPC_URL = os.getenv('MONAD_RPC_URL', 'https://rpc.monad.xyz')
EXPLORER_URL = os.getenv('EXPLORER_URL', 'https://explorer.monad.xyz')
CHAIN_ID = int(os.getenv('CHAIN_ID', '1'))
NATIVE_SYMBOL = os.getenv('NATIVE_SYMBOL', 'MON')

# API Configuration
KURU_API_URL = "https://api.kuru.io"

# Data Storage
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Trading Configuration
DEFAULT_SLIPPAGE = 1.0  # 1%
DEFAULT_GAS_PRICE = 750  # MIST
MAX_SLIPPAGE = 50.0  # 50%
MIN_SLIPPAGE = 0.1  # 0.1%

# Security Configuration
MAX_WALLETS_PER_USER = 10
PRIVATE_KEY_MESSAGE_TIMEOUT = 60  # seconds

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60
MAX_TRADES_PER_MINUTE = 10

# Error Messages
ERRORS = {
    'invalid_token': "Invalid token contract address",
    'insufficient_balance': "Insufficient balance for transaction",
    'network_error': "Network error occurred. Please try again",
    'invalid_amount': "Invalid amount specified",
    'max_wallets_reached': f"Maximum of {MAX_WALLETS_PER_USER} wallets allowed per user",
    'invalid_private_key': "Invalid private key format",
    'unauthorized': "Unauthorized access",
}

# Success Messages
SUCCESS = {
    'wallet_created': "Wallet created successfully",
    'wallet_imported': "Wallet imported successfully",
    'order_placed': "Order placed successfully",
    'order_cancelled': "Order cancelled successfully",
    'withdrawal_processed': "Withdrawal processed successfully",
}

# Monad Network Configuration (Testnet)
MONAD_RPC_URL_TESTNET = os.getenv('MONAD_RPC_URL_TESTNET', 'https://testnet-rpc.monad.xyz')  # Testnet RPC URL
WALLET_PRIVATE_KEY = os.getenv('WALLET_PRIVATE_KEY')

# Trading Configuration
DEFAULT_GAS_LIMIT = 300000

# Network Configuration
NETWORK_NAME = "Monad Testnet"
EXPLORER_API_URL = "https://testnet.monadexplorer.com/api"  # If available 