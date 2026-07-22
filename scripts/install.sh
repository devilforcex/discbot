#!/bin/bash
# ============================================================
#  DrusaBoT — One-Line VPS Installer
#  Run:
#    curl -fsSL https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/install.sh | bash
#  Or:
#    wget -qO- https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/install.sh | bash
# ============================================================

set -e

# ── Configuration ──────────────────────────────────────────
REPO_URL="https://github.com/devilforcex/discbot.git"
INSTALL_DIR="/home/discbot/discbot"
USER_NAME="discbot"
BRANCH="master"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERR]${NC} $1"; }

# ── Check root ─────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    error "Please run as root or with sudo"
    exit 1
fi

# ── Banner ─────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        DrusaBoT — Automatic VPS Installer                ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Detect OS ──────────────────────────────────────────────
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    error "Cannot detect OS"
    exit 1
fi

if [[ "$OS" != "ubuntu" && "$OS" != "debian" ]]; then
    warn "This script is tested on Ubuntu/Debian. Continuing anyway..."
fi

# ── Create user ────────────────────────────────────────────
if id "$USER_NAME" &>/dev/null; then
    info "User $USER_NAME already exists"
else
    info "Creating user $USER_NAME..."
    adduser --disabled-password --gecos "" "$USER_NAME"
    usermod -aG sudo "$USER_NAME"
    success "User $USER_NAME created"
fi

# ── Update system ──────────────────────────────────────────
info "Updating system packages..."
apt update && apt upgrade -y
success "System updated"

# ── Install dependencies ───────────────────────────────────
info "Installing dependencies..."

# Install base dependencies
apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    ufw \
    build-essential \
    software-properties-common \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    openjdk-17-jre-headless \
    ffmpeg

# Install Node.js 20.x from NodeSource (includes npm)
if ! command -v node &>/dev/null; then
    info "Installing Node.js 20.x..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
else
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 20 ]; then
        info "Upgrading Node.js to 20.x..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt install -y nodejs
    else
        info "Node.js $(node --version) already installed"
    fi
fi

# npm comes bundled with NodeSource Node.js, but ensure it's available
if ! command -v npm &>/dev/null; then
    warn "npm not found, attempting to install separately..."
    apt install -y npm || warn "Could not install npm separately — frontend build will be skipped"
fi

# Ensure Python 3.11+ on Ubuntu 22.04
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    info "Python $PYTHON_VERSION detected, installing Python 3.11..."
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    apt install -y python3.11 python3.11-venv python3.11-dev
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
fi

success "Dependencies installed"

# ── Clone repository ───────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    warn "Directory $INSTALL_DIR already exists"
    read -p "Remove and reinstall? [y/N]: " choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
    else
        info "Using existing directory"
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    info "Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    success "Repository cloned"
fi

cd "$INSTALL_DIR"

# ── Set ownership ──────────────────────────────────────────
chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR"

# ── Create virtual environment ─────────────────────────────
info "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    sudo -u "$USER_NAME" python3 -m venv .venv
fi
success "Virtual environment ready"

# ── Install Python dependencies ────────────────────────────
info "Installing Python dependencies..."
sudo -u "$USER_NAME" bash -c "source $INSTALL_DIR/.venv/bin/activate && pip install -q --upgrade pip && pip install -q -r requirements.txt"
success "Python dependencies installed"

# ── Build frontend ─────────────────────────────────────────
if [ -d "web" ] && [ -f "web/package.json" ]; then
    info "Building frontend..."
    cd web
    npm install --silent
    npm run build
    cd ..
    success "Frontend built"
fi

# ── Create .env ────────────────────────────────────────────
if [ ! -f ".env" ]; then
    info "Creating .env file..."
    sudo -u "$USER_NAME" cp .env.example .env
    success ".env created — please edit it with your tokens!"
else
    info ".env already exists, skipping"
fi

# ── Create systemd services ────────────────────────────────
info "Creating systemd services..."

cat > /etc/systemd/system/lavalink.service <<EOF
[Unit]
Description=Lavalink Audio Server
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$INSTALL_DIR/lavalink
ExecStart=/usr/bin/java -Xms256m -Xmx512m -XX:+UseG1GC -jar Lavalink.jar
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/discbot.service <<EOF
[Unit]
Description=DrusaBoT Discord Music Bot
After=network.target lavalink.service
Wants=lavalink.service

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/python -m bot.main
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/discbot-dashboard.service <<EOF
[Unit]
Description=DrusaBoT Dashboard
After=network.target discbot.service
Wants=discbot.service

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/python -m bot.dashboard.dashboard
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lavalink discbot discbot-dashboard
success "Systemd services created and enabled"

# ── Configure firewall ─────────────────────────────────────
info "Configuring UFW firewall..."
ufw allow OpenSSH
ufw allow 18080/tcp
ufw --force enable
success "Firewall configured"

# ── Final instructions ─────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation Complete!                            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  📁 Install directory: ${CYAN}$INSTALL_DIR${NC}"
echo -e "  👤 User: ${CYAN}$USER_NAME${NC}"
echo ""
echo -e "  ⚠️  ${YELLOW}IMPORTANT: Configure your bot tokens!${NC}"
echo -e "     ${CYAN}nano $INSTALL_DIR/.env${NC}"
echo ""
echo -e "  Required values in .env:"
echo -e "    • DISCORD_BOT_TOKEN"
echo -e "    • LAVALINK_PASSWORD"
echo -e "    • DASHBOARD_SECRET_KEY"
echo ""
echo -e "  🚀 Start services:"
echo -e "     ${CYAN}sudo systemctl start lavalink${NC}"
echo -e "     ${CYAN}sudo systemctl start discbot${NC}"
echo -e "     ${CYAN}sudo systemctl start discbot-dashboard${NC}"
echo ""
echo -e "  📊 Check status:"
echo -e "     ${CYAN}sudo systemctl status discbot${NC}"
echo ""
echo -e "  🔄 Future updates:"
echo -e "     ${CYAN}cd $INSTALL_DIR && ./scripts/update.sh${NC}"
echo ""