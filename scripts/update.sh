#!/bin/bash
# ============================================================
#  DrusaBoT — VPS Update Script
#  Run from the project root: ./scripts/update.sh
#  Or from anywhere: /home/discbot/discbot/scripts/update.sh
# ============================================================

set -e

# ── Configuration ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"
WEB_DIR="$PROJECT_DIR/web"

# Service names (set to "" to skip)
SVC_BOT="discbot"
SVC_DASHBOARD="discbot-dashboard"
SVC_LAVALINK="lavalink"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Helpers ────────────────────────────────────────────────
info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERR]${NC} $1"; }

stop_service() {
    local svc="$1"
    if [ -z "$svc" ]; then return; fi
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        info "Stopping $svc..."
        sudo systemctl stop "$svc"
        success "$svc stopped"
    else
        info "$svc is not running, skipping stop"
    fi
}

start_service() {
    local svc="$1"
    if [ -z "$svc" ]; then return; fi
    if systemctl is-enabled --quiet "$svc" 2>/dev/null; then
        info "Starting $svc..."
        sudo systemctl start "$svc"
        success "$svc started"
    else
        warn "$svc is not enabled, skipping start"
    fi
}

# ── Parse arguments ────────────────────────────────────────
SKIP_FRONTEND=false
SKIP_DEPS=false
NO_RESTART=false
BRANCH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-frontend) SKIP_FRONTEND=true; shift ;;
        --skip-deps)     SKIP_DEPS=true; shift ;;
        --no-restart)    NO_RESTART=true; shift ;;
        --branch)        BRANCH="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-frontend   Skip npm install & build"
            echo "  --skip-deps       Skip pip install"
            echo "  --no-restart      Don't restart services after update"
            echo "  --branch BRANCH   Pull from specific branch (default: current)"
            echo "  -h, --help        Show this help"
            exit 0
            ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Start ──────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     DrusaBoT — VPS Update Script        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_DIR"
info "Project directory: $PROJECT_DIR"

# ── Check git repo ─────────────────────────────────────────
if [ ! -d ".git" ]; then
    error "Not a git repository! Run this script from the project root."
    exit 1
fi

# ── Determine branch ───────────────────────────────────────
if [ -z "$BRANCH" ]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi
info "Branch: $BRANCH"

# ── Show current version ───────────────────────────────────
CURRENT_HASH=$(git rev-parse --short HEAD)
CURRENT_MSG=$(git log -1 --pretty=%s)
info "Current: $CURRENT_HASH — $CURRENT_MSG"

# ── Fetch & check for updates ──────────────────────────────
info "Fetching latest changes..."
git fetch origin "$BRANCH" 2>/dev/null

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    error "Could not find remote branch origin/$BRANCH"
    exit 1
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    success "Already up to date! ($CURRENT_HASH)"
    if [ "$NO_RESTART" = false ]; then
        echo ""
        read -p "Restart services anyway? [y/N]: " restart_choice
        if [[ "$restart_choice" =~ ^[Yy]$ ]]; then
            info "Restarting services..."
            stop_service "$SVC_LAVALINK"
            stop_service "$SVC_BOT"
            stop_service "$SVC_DASHBOARD"
            sleep 2
            start_service "$SVC_LAVALINK"
            sleep 3
            start_service "$SVC_BOT"
            start_service "$SVC_DASHBOARD"
        fi
    fi
    echo ""
    success "Nothing to do. Bye!"
    exit 0
fi

# ── Show what will change ──────────────────────────────────
echo ""
info "Changes to be applied:"
git log --oneline "$LOCAL..$REMOTE" | head -20
CHANGES_COUNT=$(git rev-list --count "$LOCAL..$REMOTE")
echo ""
info "$CHANGES_COUNT commit(s) to apply"
echo ""

# ── Stop services ──────────────────────────────────────────
if [ "$NO_RESTART" = false ]; then
    info "Stopping services..."
    stop_service "$SVC_BOT"
    stop_service "$SVC_DASHBOARD"
    # Lavalink usually doesn't need restart on bot update
    echo ""
fi

# ── Pull changes ───────────────────────────────────────────
info "Pulling latest changes..."
git pull origin "$BRANCH"
NEW_HASH=$(git rev-parse --short HEAD)
success "Updated: $CURRENT_HASH → $NEW_HASH"
echo ""

# ── Update Python dependencies ─────────────────────────────
if [ "$SKIP_DEPS" = false ]; then
    if [ -f "requirements.txt" ]; then
        info "Updating Python dependencies..."
        if [ -f "$VENV_DIR/bin/activate" ]; then
            source "$VENV_DIR/bin/activate"
            pip install -q --upgrade pip
            pip install -q -r requirements.txt
            success "Python dependencies updated"
        else
            warn "Virtual environment not found at $VENV_DIR"
            warn "Skipping pip install — run manually if needed"
        fi
        echo ""
    fi
else
    info "Skipping Python dependencies (--skip-deps)"
fi

# ── Update frontend ────────────────────────────────────────
if [ "$SKIP_FRONTEND" = false ]; then
    if [ -d "$WEB_DIR" ] && [ -f "$WEB_DIR/package.json" ]; then
        # Check if web/ files changed
        WEB_CHANGED=$(git diff --name-only "$CURRENT_HASH" "$NEW_HASH" -- web/ 2>/dev/null | head -1)
        if [ -n "$WEB_CHANGED" ] || [ ! -d "$WEB_DIR/dist" ]; then
            info "Frontend changes detected, rebuilding..."
            cd "$WEB_DIR"
            if command -v npm &>/dev/null; then
                npm install --silent 2>/dev/null
                npm run build 2>/dev/null
                success "Frontend rebuilt"
            else
                warn "npm not found — skipping frontend build"
                warn "Install Node.js and run: cd web && npm install && npm run build"
            fi
            cd "$PROJECT_DIR"
        else
            info "No frontend changes, skipping rebuild"
        fi
        echo ""
    fi
else
    info "Skipping frontend (--skip-frontend)"
fi

# ── Run database migrations (if any) ──────────────────────
if [ -d "migrations" ] || [ -f "alembic.ini" ]; then
    info "Checking for database migrations..."
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        if command -v alembic &>/dev/null; then
            alembic upgrade head 2>/dev/null && success "Migrations applied" || warn "No new migrations or alembic not configured"
        fi
    fi
    echo ""
fi

# ── Restart services ───────────────────────────────────────
if [ "$NO_RESTART" = false ]; then
    info "Starting services..."
    start_service "$SVC_BOT"
    start_service "$SVC_DASHBOARD"
    echo ""

    # Wait a moment and show status
    sleep 3
    info "Service status:"
    echo ""
    for svc in "$SVC_BOT" "$SVC_DASHBOARD" "$SVC_LAVALINK"; do
        if [ -n "$svc" ] && systemctl is-enabled --quiet "$svc" 2>/dev/null; then
            STATUS=$(systemctl is-active "$svc" 2>/dev/null)
            if [ "$STATUS" = "active" ]; then
                success "$svc: $STATUS"
            else
                error "$svc: $STATUS"
            fi
        fi
    done
fi

# ── Done ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Update Complete!                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Version: ${CYAN}$CURRENT_HASH${NC} → ${GREEN}$NEW_HASH${NC}"
echo -e "  Commits applied: ${CYAN}$CHANGES_COUNT${NC}"
echo ""
echo -e "  Logs:  ${CYAN}sudo journalctl -u $SVC_BOT -f${NC}"
echo -e "  Status: ${CYAN}sudo systemctl status $SVC_BOT${NC}"
echo ""