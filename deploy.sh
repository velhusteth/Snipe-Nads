#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check for Docker
echo -e "${YELLOW}Checking for Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check for Docker Compose
echo -e "${YELLOW}Checking for Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${RED}No .env file found!${NC}"
    echo "Creating example .env file..."
    cat > .env << EOL
TELEGRAM_BOT_TOKEN=your_bot_token_here
MONAD_RPC_URL=https://rpc.monad.xyz
EXPLORER_URL=https://explorer.monad.xyz
CHAIN_ID=1
NATIVE_SYMBOL=MON
EOL
    echo -e "${YELLOW}Please edit .env file with your configuration and run this script again.${NC}"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Build and start the containers
echo -e "${YELLOW}Building and starting the bot...${NC}"
docker-compose up -d --build

# Check if containers are running
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Bot is now running!${NC}"
    echo -e "To view logs: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "To stop: ${YELLOW}docker-compose down${NC}"
else
    echo -e "${RED}Failed to start the bot. Check the logs above for errors.${NC}"
    exit 1
fi 