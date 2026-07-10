FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Runtime dependencies only. Build tools are intentionally avoided to keep the
# image small; Python packages used by this project ship wheels on supported
# platforms.
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY bot ./bot
COPY docs ./docs
COPY README.md ./README.md
COPY application.yml.example ./application.yml.example

RUN useradd --create-home --shell /usr/sbin/nologin discbot \
    && mkdir -p /app/data /app/logs \
    && chown -R discbot:discbot /app
USER discbot

CMD ["python", "-m", "bot.main"]
