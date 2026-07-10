#!/usr/bin/env bash
# Fast, non-destructive update for an existing DiscBot checkout.
# Usage:
#   ./update.sh              # update Git, then rebuild/restart Docker Compose
#   ./update.sh --pull-only  # update Git only

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PULL_ONLY=false

usage() {
    cat <<'EOF'
Usage: ./update.sh [--pull-only] [--help]

  --pull-only  Fetch and fast-forward the current Git branch without restarting
               Docker services.
  --help       Show this help message.
EOF
}

log() {
    printf '\n\033[1;36m==>\033[0m %s\n' "$*"
}

fail() {
    printf '\n\033[1;31mError:\033[0m %s\n' "$*" >&2
    exit 1
}

while (($#)); do
    case "$1" in
        --pull-only)
            PULL_ONLY=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            fail "Unknown option: $1"
            ;;
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

UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)"
if [[ -z "$UPSTREAM" ]]; then
    REMOTE="${UPDATE_REMOTE:-origin}"
    UPSTREAM="$REMOTE/$BRANCH"
else
    REMOTE="${UPSTREAM%%/*}"
fi

log "Fetching $REMOTE and updating branch $BRANCH"
git fetch --prune "$REMOTE"
git rev-parse --verify --quiet "$UPSTREAM^{commit}" >/dev/null || \
    fail "Upstream branch '$UPSTREAM' does not exist. Configure it with: git branch --set-upstream-to=<remote>/<branch>"

OLD_REV="$(git rev-parse HEAD)"
# Fast-forward only: this deliberately refuses merges and destructive resets.
git merge --ff-only "$UPSTREAM"
NEW_REV="$(git rev-parse HEAD)"

if [[ "$OLD_REV" == "$NEW_REV" ]]; then
    log "Source is already up to date ($(git rev-parse --short HEAD))"
else
    log "Source updated: ${OLD_REV:0:7} -> ${NEW_REV:0:7}"
fi

if [[ "$PULL_ONLY" == true ]]; then
    log "Done (Git update only)"
    exit 0
fi

[[ -f .env ]] || fail ".env is missing. Create it with 'cp .env.example .env' and add your secrets."
command -v docker >/dev/null 2>&1 || \
    fail "Docker is not installed. The source was updated; restart the bot manually."
docker compose version >/dev/null 2>&1 || \
    fail "Docker Compose v2 is unavailable. The source was updated; restart the bot manually."

log "Pulling the latest Lavalink image"
docker compose pull lavalink

log "Rebuilding and restarting DiscBot"
docker compose up -d --build --remove-orphans

log "Update complete"
docker compose ps
