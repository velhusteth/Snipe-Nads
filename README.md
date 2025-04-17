# Monad Sniper Bot 🚀

A Telegram bot for trading tokens on the Monad blockchain through Kuru DEX.

## Features

- 💼 Wallet Management
  - Create new wallets
  - Import existing wallets
  - View wallet balances
  - Secure private key handling
  
- 📊 Trading Features
  - Token info display
  - Buy/Sell tokens
  - Limit orders
  - Order management
  
- 💰 Portfolio Management
  - View holdings
  - Track profits/losses
  - Transaction history
  
- ⚙️ Configuration
  - Custom slippage settings
  - Gas price settings
  - Auto-slippage option

## Quick Start (Docker)

The easiest way to run the bot is using Docker:

1. Install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

2. Clone the repository:
```bash
git clone https://github.com/yourusername/monad-sniper-bot.git
cd monad-sniper-bot
```

3. Create and configure your `.env` file:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run the deployment script:
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows
docker-compose up -d --build
```

## Manual Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/monad-sniper-bot.git
cd monad-sniper-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the bot:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the bot:
```bash
python bot.py
```

## Configuration

Create a `.env` file with the following variables:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
MONAD_RPC_URL=https://rpc.monad.xyz
EXPLORER_URL=https://explorer.monad.xyz
CHAIN_ID=1
NATIVE_SYMBOL=MON
```

### Getting a Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the token provided by BotFather

## Usage

1. Start the bot by sending `/start` in Telegram
2. Create or import a wallet
3. Use the menu buttons to:
   - View token information
   - Place buy/sell orders
   - Manage your portfolio
   - Configure settings

## Security Considerations

- Never share your private keys
- Keep your `.env` file secure
- Use secure RPC endpoints
- Regularly backup your data directory
- Monitor your bot's activities

## Deployment Options

### Docker (Recommended)
```bash
docker-compose up -d --build
```

### Windows Service
```batch
# Run as Administrator
install_service.bat
```

### Linux Service (systemd)
```bash
sudo cp monad-bot.service /etc/systemd/system/
sudo systemctl enable monad-bot
sudo systemctl start monad-bot
```

## Monitoring

### Docker Logs
```bash
docker-compose logs -f
```

### System Logs
- Windows: Check Windows Event Viewer
- Linux: `journalctl -u monad-bot -f`

## Updating

### Docker
```bash
git pull
docker-compose up -d --build
```

### Manual Installation
```bash
git pull
pip install -r requirements.txt
# Restart the bot
```

## Support

For support:
- Open an issue on GitHub
- Join our [Telegram group](https://t.me/your_support_group)
- Check the [Wiki](https://github.com/yourusername/monad-sniper-bot/wiki)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This bot is provided as-is. Use at your own risk. Always verify transactions before confirming them. 