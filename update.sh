#!/usr/bin/env bash
# Fast, non-destructive update for an existing DiscBot checkout.
# Usage:
#   ./update.sh              # update Git, then rebuild/restart Docker Compose (if Docker is present)
#   ./update.sh --pull-only  # update Git only (no Docker, no restart)
#   ./update.sh --no-docker  # update Git, skip Docker restart even if Docker is installed
#   ./update.sh --help

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PULL_ONLY=false
NO_DOCKER=false

usage() {
    cat <<'EOF'
Usage: ./update.sh [--pull-only] [--no-docker] [--help]

  --pull-only  Fetch and fast-forward the current Git branch without restarting
               Docker services or touching anything else.
  --no-docker  Update source, but skip Docker restart even if Docker is installed
               (useful for native / venv-based runs).
  --help       Show this help message.
EOF
}

log()  { printf '\n\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
warn() { printf '    \033[1;33m!\033[0m   %s\n' "$*"; }
fail() { printf '\n\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

while (($#)); do
    case "$1" in
        --pull-only) PULL_ONLY=true ;;
        --no-docker) NO_DOCKER=true ;;
        -h|--help)   usage; exit 0 ;;
        *) usage >&2; fail "Unknown option: $1" ;;
    esac
    shift
done

cd "$ROOT_DIR"
command -v git >/dev/null 2>&1 || fail "git is not installed."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "$ROOT_DIR is not a Git checkout."

BRANCH="$(git symbolic-ref --quiet --short HEAD)" || \
    fail "The repository is in detached HEAD state. Check out a branch first."

# Never overwrite tracked local edits. Ignored runtime files such as .env,
# data/, and logs/ are left untouched by the Git update.
if ! git diff --quiet || ! git diff --cached --quiet; then
    git status --short
    fail "Tracked local changes found. Commit or stash them before updating."
fi

# Determine remote+upstream; fall back to origin/<current branch> if no upstream set.
if UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)" && [[ -n "$UPSTREAM" ]]; then
    REMOTE="${UPSTREAM%%/*}"
else
    REMOTE="${UPDATE_REMOTE:-origin}"
    UPSTREAM="$REMOTE/$BRANCH"
    warn "No upstream tracking branch configured for '$BRANCH'. Assuming '$UPSTREAM'."
fi

log "Fetching $REMOTE and updating branch $BRANCH"
git fetch --prune "$REMOTE"
if ! git rev-parse --verify --quiet "$UPSTREAM^{commit}" >/dev/null; then
    fail "Upstream branch '$UPSTREAM' does not exist on remote. Create it or set upstream with: git branch --set-upstream-to=<remote>/<branch>"
fi

OLD_REV="$(git rev-parse HEAD)"
# Fast-forward only: this deliberately refuses merges and destructive resets.
if ! git merge --ff-only "$UPSTREAM"; then
    fail "Fast-forward failed (history has diverged). Resolve manually: rebase or reset to '$UPSTREAM'."
fi
NEW_REV="$(git rev-parse HEAD)"

if [[ "$OLD_REV" == "$NEW_REV" ]]; then
    ok "Source is already up to date ($(git rev-parse --short HEAD))"
else
    ok "Source updated: ${OLD_REV:0:7} -> ${NEW_REV:0:7}"
fi

# Refresh venv dependencies if a virtual environment exists (native install)
if [[ -d .venv ]] && [[ -x .venv/bin/python ]]; then
    log "Refreshing Python dependencies in .venv"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install -r requirements.txt --upgrade
    ok "dependencies up to date"
fi

if [[ "$PULL_ONLY" == true ]]; then
    log "Done (Git update only)"
    exit 0
fi

# Docker path — only if Docker is installed AND --no-docker is not set
if [[ "$NO_DOCKER" == true ]]; then
    log "Skipping Docker restart (--no-docker)"
    log "Update complete. Restart the bot yourself to apply changes."
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    warn "Docker is not installed — not restarting via Compose."
    warn "If you run the bot natively, restart it manually (e.g. ./start.sh or systemctl)."
    log "Update complete"
    exit 0
fi

if ! docker compose version >/dev/null 2>&1; then
    warn "Docker Compose v2 is unavailable — not restarting via Compose."
    log "Update complete. Restart the bot manually."
    exit 0
fi

if [[ ! -f .env ]]; then
    warn ".env is missing — cannot restart via Compose. Create .env from .env.example first."
    log "Source was updated; start Docker manually when ready."
    exit 0
fi

log "Pulling the latest Lavalink image"
docker compose pull lavalink

log "Rebuilding and restarting DiscBot"
docker compose up -d --build --remove-orphans

log "Update complete"
docker compose ps
