#!/bin/bash
# ============================================================
#  DiscBot Docker Entrypoint
#  Starts Lavalink as a subprocess, waits for it, then starts bot
# ============================================================
set -e

echo "============================================"
echo "  DiscBot - Starting up..."
echo "============================================"

# Start Lavalink in background
echo "[1/3] Starting Lavalink server..."
cd /app/lavalink
java -jar Lavalink.jar &
LAVALINK_PID=$!
cd /app

# Wait for Lavalink to be ready
echo "[2/3] Waiting for Lavalink to be ready..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:12333/ > /dev/null 2>&1; then
        echo "  Lavalink is ready! (attempt $i)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  WARNING: Lavalink did not respond in time, starting bot anyway..."
    fi
    sleep 2
done

# Start the bot
echo "[3/3] Starting Discord bot..."
cd /app
exec python -m bot.main