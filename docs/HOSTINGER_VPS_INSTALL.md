# 🚀 Инсталация на DrusaBoT — Hostinger VPS

Пълно ръководство за deploy на DrusaBoT на Hostinger VPS (Ubuntu 22.04/24.04).

---

## 📋 Съдържание

1. [Изисквания](#изисквания)
2. [Подготовка на VPS](#подготовка-на-vps)
3. [Инсталация на зависимости](#инсталация-на-зависимости)
4. [Клониране и настройка на проекта](#клониране-и-настройка-на-проекта)
5. [Lavalink конфигурация](#lavalink-конфигурация)
6. [Systemd услуги (автоматичен старт)](#systemd-услуги-автоматичен-старт)
7. [Nginx Reverse Proxy (по избор)](#nginx-reverse-proxy-по-избор)
8. [Защитна стена и сигурност](#защитна-стена-и-сигурност)
9. [Обновяване](#обновяване)
10. [Отстраняване на проблеми](#отстраняване-на-проблеми)

---

## Изисквания

### Минимален VPS план

| Ресурс | Минимум | Препоръчително |
|--------|---------|----------------|
| **CPU** | 1 vCPU | 2 vCPU |
| **RAM** | 1 GB | 2 GB+ |
| **Диск** | 10 GB | 20 GB+ |
| **OS** | Ubuntu 22.04 | Ubuntu 24.04 |
| **Мрежа** | IPv4 | IPv4 + IPv6 |

### Защо тези ресурси?

- **Python бот**: ~100-200 MB RAM
- **Lavalink (Java)**: ~256-512 MB RAM (зависи от броя едновременни потоци)
- **FastAPI Dashboard**: ~50-100 MB RAM
- **SQLite/PostgreSQL**: ~50-100 MB RAM
- **Общо**: ~500 MB - 1 GB при нормално натоварване

> 💡 **Hostinger KVM 2** (2 vCPU, 8 GB RAM, 100 GB NVMe) е отличен избор за production.

---

## Подготовка на VPS

### 1. Свързване към VPS

```bash
ssh root@YOUR_VPS_IP
```

### 2. Обновяване на системата

```bash
apt update && apt upgrade -y
```

### 3. Създаване на потребител (препоръчително)

```bash
adduser discbot
usermod -aG sudo discbot
su - discbot
```

### 4. Инсталиране на основни инструменти

```bash
sudo apt install -y curl wget git nano htop ufw build-essential
```

---

## Инсталация на зависимости

### 1. Python 3.11+

```bash
# Ubuntu 24.04 има Python 3.12 по подразбиране
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Проверка
python3 --version
# Трябва да е 3.11 или по-нова
```

**Ако Ubuntu 22.04 (Python 3.10 по подразбиране):**

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### 2. Java 17 (за Lavalink)

```bash
sudo apt install -y openjdk-17-jre-headless

# Проверка
java -version
# Трябва да покаже openjdk version "17.x.x"
```

### 3. FFmpeg (за аудио обработка)

```bash
sudo apt install -y ffmpeg

# Проверка
ffmpeg -version
```

### 4. Node.js 20+ (за frontend build, по избор)

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Проверка
node --version
npm --version
```

### 5. PostgreSQL (по избор, за production БД)

```bash
sudo apt install -y postgresql postgresql-contrib

# Създаване на БД и потребител
sudo -u postgres psql
```

```sql
CREATE DATABASE discbot;
CREATE USER discbot WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE discbot TO discbot;
\q
```

---

## Клониране и настройка на проекта

### 1. Клониране на хранилището

```bash
cd /home/discbot
git clone https://github.com/devilforcex/discbot.git
cd discbot
```

### 2. Създаване на виртуална среда

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Инсталиране на Python зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Конфигуриране на .env

```bash
cp .env.example .env
nano .env
```

**Задължителни промени:**

```env
# Discord Bot Token (от https://discord.com/developers/applications)
DISCORD_BOT_TOKEN=your_actual_bot_token

# Lavalink парола (смени с нещо сигурно!)
LAVALINK_PASSWORD=your_strong_password

# Dashboard секрет (генерирай с: python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DASHBOARD_SECRET_KEY=generated_random_secret

# Dashboard порт (или остави 18080)
DASHBOARD_PORT=18080

# CORS - добави домейна си ако имаш такъв
DASHBOARD_CORS_ORIGINS=http://YOUR_VPS_IP:18080,https://your-domain.com

# PostgreSQL (ако използваш)
DATABASE_URL=postgresql+asyncpg://discbot:your_strong_password@localhost:5432/discbot
```

### 5. Изграждане на frontend (по избор, за production dashboard)

```bash
cd web
npm install
npm run build
cd ..
```

---

## Lavalink конфигурация

Lavalink JAR файлът вече е включен в `lavalink/` директорията. Ако трябва да го обновите:

```bash
cd lavalink
wget https://github.com/lavalink-devs/Lavalink/releases/download/4.0.8/Lavalink.jar
cd ..
```

**Редактиране на `lavalink/application.yml`:**

```bash
nano lavalink/application.yml
```

```yaml
server:
  port: 12333
  address: 127.0.0.1  # Само localhost за сигурност!

lavalink:
  server:
    password: "your_strong_password"  # Същата като в .env!
```

---

## Systemd услуги (автоматичен старт)

### 1. Lavalink услуга

```bash
sudo nano /etc/systemd/system/lavalink.service
```

```ini
[Unit]
Description=Lavalink Audio Server
After=network.target

[Service]
Type=simple
User=discbot
WorkingDirectory=/home/discbot/discbot/lavalink
ExecStart=/usr/bin/java -Xms256m -Xmx512m -XX:+UseG1GC -jar Lavalink.jar
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. DrusaBoT услуга

```bash
sudo nano /etc/systemd/system/discbot.service
```

```ini
[Unit]
Description=DrusaBoT Discord Music Bot
After=network.target lavalink.service
Wants=lavalink.service

[Service]
Type=simple
User=discbot
WorkingDirectory=/home/discbot/discbot
ExecStart=/home/discbot/discbot/.venv/bin/python -m bot.main
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 3. Dashboard услуга (по избор)

```bash
sudo nano /etc/systemd/system/discbot-dashboard.service
```

```ini
[Unit]
Description=DrusaBoT Dashboard
After=network.target discbot.service
Wants=discbot.service

[Service]
Type=simple
User=discbot
WorkingDirectory=/home/discbot/discbot
ExecStart=/home/discbot/discbot/.venv/bin/python -m bot.dashboard.dashboard
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 4. Активиране и стартиране

```bash
# Презареждане на systemd
sudo systemctl daemon-reload

# Активиране на услугите (стартират при boot)
sudo systemctl enable lavalink
sudo systemctl enable discbot
sudo systemctl enable discbot-dashboard  # ако използваш dashboard

# Стартиране
sudo systemctl start lavalink
sleep 5  # Изчакай Lavalink да стартира
sudo systemctl start discbot
sudo systemctl start discbot-dashboard  # ако използваш dashboard

# Проверка на статуса
sudo systemctl status lavalink
sudo systemctl status discbot
sudo systemctl status discbot-dashboard
```

### 5. Преглед на логове

```bash
# Lavalink логове
sudo journalctl -u lavalink -f

# Bot логове
sudo journalctl -u discbot -f

# Dashboard логове
sudo journalctl -u discbot-dashboard -f

# Последните 100 реда
sudo journalctl -u discbot -n 100
```

---

## Nginx Reverse Proxy (по избор)

Ако искаш да използваш домейн и HTTPS за dashboard-а:

### 1. Инсталиране на Nginx и Certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 2. Nginx конфигурация

```bash
sudo nano /etc/nginx/sites-available/discbot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:18080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### 3. Активиране и HTTPS

```bash
sudo ln -s /etc/nginx/sites-available/discbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL сертификат (безплатен от Let's Encrypt)
sudo certbot --nginx -d your-domain.com
```

### 4. Обнови .env за HTTPS

```env
DASHBOARD_CORS_ORIGINS=https://your-domain.com
```

---

## Защитна стена и сигурност

### 1. UFW конфигурация

```bash
# Разрешаване на SSH (ВАЖНО!)
sudo ufw allow OpenSSH

# Разрешаване на HTTP/HTTPS (ако използваш Nginx)
sudo ufw allow 'Nginx Full'

# ИЛИ директно dashboard порта (без Nginx)
sudo ufw allow 18080/tcp

# Активиране на защитната стена
sudo ufw enable
sudo ufw status
```

### 2. Fail2ban (препоръчително)

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Автоматични обновления (по избор)

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Обновяване

### Ръчно обновяване

```bash
cd /home/discbot/discbot

# Спри услугите
sudo systemctl stop discbot
sudo systemctl stop discbot-dashboard

# Изтегли последните промени
git pull origin main

# Обнови зависимостите
source .venv/bin/activate
pip install -r requirements.txt

# Обнови frontend (ако има промени)
cd web && npm install && npm run build && cd ..

# Стартирай услугите
sudo systemctl start discbot
sudo systemctl start discbot-dashboard
```

### Автоматичен скрипт за обновяване

```bash
nano /home/discbot/update.sh
```

```bash
#!/bin/bash
set -e

cd /home/discbot/discbot

echo "🛑 Спиране на услугите..."
sudo systemctl stop discbot discbot-dashboard

echo "📥 Изтегляне на обновления..."
git pull origin main

echo "📦 Обновяване на зависимости..."
source .venv/bin/activate
pip install -r requirements.txt

echo "🎨 Обновяване на frontend..."
cd web && npm install && npm run build && cd ..

echo "🚀 Стартиране на услугите..."
sudo systemctl start discbot discbot-dashboard

echo "✅ Обновяването завърши!"
sudo systemctl status discbot --no-pager
```

```bash
chmod +x /home/discbot/update.sh
```

---

## Отстраняване на проблеми

### Ботът не стартира

```bash
# Провери логовете
sudo journalctl -u discbot -n 50

# Чести причини:
# - Грешен DISCORD_BOT_TOKEN
# - Lavalink не е стартиран
# - Липсващи зависимости
```

### Lavalink не стартира

```bash
# Провери Java версията
java -version

# Провери дали порт 12333 е свободен
sudo ss -tlnp | grep 12333

# Провери логовете
sudo journalctl -u lavalink -n 50
```

### Dashboard не е достъпен

```bash
# Провери дали услугата работи
sudo systemctl status discbot-dashboard

# Провери дали порт 18080 е отворен
sudo ufw status | grep 18080

# Провери CORS настройките в .env
grep CORS .env
```

### Високо използване на RAM

```bash
# Провери използването на паметта
htop

# Намали Lavalink heap size
# В lavalink.service: -Xmx256m вместо -Xmx512m

# Ограничи броя на едновременните потоци в application.yml
```

### Ботът не се свързва с Lavalink

```bash
# Провери дали Lavalink работи
curl http://127.0.0.1:12333/version

# Провери паролата в .env и application.yml
grep LAVALINK_PASSWORD .env
grep password lavalink/application.yml
```

---

## 📞 Полезни команди

| Команда | Описание |
|---------|----------|
| `sudo systemctl status discbot` | Статус на бота |
| `sudo systemctl restart discbot` | Рестартиране на бота |
| `sudo journalctl -u discbot -f` | Live логове на бота |
| `sudo journalctl -u lavalink -f` | Live логове на Lavalink |
| `htop` | Мониторинг на ресурсите |
| `df -h` | Свободно място на диска |
| `free -h` | Свободна RAM |

---

## ✅ Чеклист за инсталация

- [ ] VPS е създаден и достъпен чрез SSH
- [ ] Системата е обновена (`apt update && apt upgrade`)
- [ ] Създаден е потребител (не root)
- [ ] Python 3.11+ е инсталиран
- [ ] Java 17 е инсталиран
- [ ] FFmpeg е инсталиран
- [ ] Проектът е клониран
- [ ] `.env` файлът е конфигуриран
- [ ] Lavalink паролата е сменена
- [ ] Dashboard секретът е генериран
- [ ] Discord Bot Token е добавен
- [ ] Systemd услугите са създадени и активирани
- [ ] UFW защитната стена е конфигурирана
- [ ] Ботът е онлайн в Discord
- [ ] Dashboard е достъпен (ако е активиран)

---

## 🔗 Полезни връзки

- [Hostinger VPS документация](https://support.hostinger.com/en/categories/vps)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Lavalink документация](https://lavalink.dev/getting-started/)
- [Let's Encrypt / Certbot](https://certbot.eff.org/)

---

*Последна актуализация: Юли 2026*