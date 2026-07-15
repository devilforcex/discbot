# ============================================================
#  DiscBot — Multi-stage Docker build
#  Stage 1: Java 17 + Lavalink
#  Stage 2: Python 3.12 + Bot
# ============================================================

# ---------- Stage 1: Lavalink ----------
FROM eclipse-temurin:17-jre-jammy AS lavalink

WORKDIR /lavalink

# Copy Lavalink and its configuration
COPY lavalink/application.yml .
COPY lavalink/Lavalink.jar .
COPY lavalink/plugins/ ./plugins/

# Expose Lavalink port (internal)
EXPOSE 12333

# ---------- Stage 2: Python bot ----------
FROM python:3.12-slim AS bot

# Install Java 17 Runtime for Lavalink subprocess + curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Copy Java + Lavalink from stage 1
COPY --from=lavalink /lavalink /app/lavalink

# Set working directory
WORKDIR /app

# Copy Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/

# Copy environment template (will be overridden by Railway env vars)
COPY .env.example .env.example

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose bot ports
EXPOSE 18080  # Dashboard
EXPOSE 3000   # Landing page

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:18080/api/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]