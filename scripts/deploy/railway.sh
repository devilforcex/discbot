#!/bin/bash
# ============================================================
#  DiscBot — Automated Railway Deployment Script
#  ============================================================
#  This script automates the deployment of DiscBot to Railway.
#  It will:
#    1. Check/Install Railway CLI
#    2. Login to Railway
#    3. Create/Select project
#    4. Provision PostgreSQL add-on
#    5. Set environment variables
#    6. Deploy the project
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  DiscBot — Railway Deployment${NC}"
echo -e "${BLUE}============================================${NC}"

# ---- Step 1: Check/Install Railway CLI ----
echo -e "\n${YELLOW}[1/6]${NC} Checking Railway CLI..."

if command -v railway &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Railway CLI found: $(railway --version)"
else
    echo -e "  ${YELLOW}⚠${NC} Railway CLI not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://railway.app/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install railway
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo -e "  ${RED}✗${NC} Windows detected. Please install Railway CLI manually:"
        echo -e "    npm install -g @railway/cli"
        echo -e "    Or download from: https://docs.railway.app/develop/cli"
        exit 1
    else
        echo -e "  ${RED}✗${NC} Unsupported OS. Please install Railway CLI manually."
        exit 1
    fi
    
    echo -e "  ${GREEN}✓${NC} Railway CLI installed"
fi

# ---- Step 2: Login ----
echo -e "\n${YELLOW}[2/6]${NC} Logging in to Railway..."
railway login
echo -e "  ${GREEN}✓${NC} Logged in"

# ---- Step 3: Create/Select Project ----
echo -e "\n${YELLOW}[3/6]${NC} Setting up Railway project..."

PROJECT_NAME="discbot"

# Check if project already exists
if railway project list 2>/dev/null | grep -q "$PROJECT_NAME"; then
    echo -e "  ${GREEN}✓${NC} Project '$PROJECT_NAME' already exists. Linking..."
    railway link
else
    echo -e "  Creating new project: $PROJECT_NAME"
    railway init "$PROJECT_NAME"
    echo -e "  ${GREEN}✓${NC} Project created"
fi

# ---- Step 4: Provision PostgreSQL ----
echo -e "\n${YELLOW}[4/6]${NC} Provisioning PostgreSQL add-on..."

# Check if PostgreSQL is already provisioned
if railway addon list 2>/dev/null | grep -q "postgres"; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL add-on already exists"
else
    echo -e "  Creating PostgreSQL add-on..."
    railway addon create postgres
    echo -e "  ${GREEN}✓${NC} PostgreSQL add-on created"
fi

# ---- Step 5: Set Environment Variables ----
echo -e "\n${YELLOW}[5/6]${NC} Setting environment variables..."

# Get DATABASE_URL from PostgreSQL add-on
DATABASE_URL=$(railway addon postgres --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('DATABASE_URL',''))" 2>/dev/null || echo "")

if [ -n "$DATABASE_URL" ]; then
    railway variable set DATABASE_URL="$DATABASE_URL"
    echo -e "  ${GREEN}✓${NC} DATABASE_URL set"
fi

# Set other required variables (prompt user for sensitive ones)
echo -e "\n  ${YELLOW}Please enter your Discord Bot Token:${NC}"
read -s DISCORD_TOKEN
railway variable set DISCORD_BOT_TOKEN="$DISCORD_TOKEN"
echo -e "  ${GREEN}✓${NC} DISCORD_BOT_TOKEN set"

# Set guild/channel IDs
echo -e "\n  ${YELLOW}Enter your Guild ID (or press Enter for default):${NC}"
read GUILD_ID
if [ -n "$GUILD_ID" ]; then
    railway variable set GUILD_ID="$GUILD_ID"
fi

echo -e "\n  ${YELLOW}Enter your Music Channel ID (or press Enter for default):${NC}"
read MUSIC_CHANNEL_ID
if [ -n "$MUSIC_CHANNEL_ID" ]; then
    railway variable set MUSIC_CHANNEL_ID="$MUSIC_CHANNEL_ID"
fi

echo -e "\n  ${YELLOW}Enter your Owner ID (or press Enter for default):${NC}"
read OWNER_ID
if [ -n "$OWNER_ID" ]; then
    railway variable set OWNER_ID="$OWNER_ID"
fi

# Set Lavalink config for internal communication
railway variable set LAVALINK_HOST="127.0.0.1"
railway variable set LAVALINK_PORT="12333"
railway variable set LAVALINK_PASSWORD="youshallnotpass"
railway variable set LAVALINK_SECURE="false"

# Enable dashboard
railway variable set DASHBOARD_ENABLED="true"
railway variable set DASHBOARD_HOST="0.0.0.0"
railway variable set DASHBOARD_PORT="18080"

# Generate random secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -hex 32)
railway variable set DASHBOARD_SECRET_KEY="$SECRET_KEY"

echo -e "  ${GREEN}✓${NC} All environment variables set"

# ---- Step 6: Deploy ----
echo -e "\n${YELLOW}[6/6]${NC} Deploying to Railway..."
railway up --detach

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ Deployment initiated!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e ""
echo -e "  Monitor deployment:  ${BLUE}railway logs${NC}"
echo -e "  Open dashboard:      ${BLUE}railway open${NC}"
echo -e "  View status:         ${BLUE}railway status${NC}"
echo -e ""
echo -e "  Your bot will be available at the Railway URL"
echo -e "  shown in the Railway dashboard."
echo -e ""