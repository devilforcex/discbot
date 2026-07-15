# Railway Deployment Setup

## Проблеми, които бяха оправени

1. **`.gitignore`** изключваше `lavalink/` директорията → Docker билдът не намираше `Lavalink.jar`
2. **Dockerfile** нямаше Java runtime в Stage 2 → Lavalink subprocess не можеше да стартира
3. **`test.yml`** имаше `|| true` което скриваше грешки от тестовете
4. **`deploy.yml`** ползваше `install.sh` за Railway CLI който се чупеше в CI
5. **`requirements.txt`** нямаше `pytest` за CI
6. **Healthcheck падаше** — dashboard-ът не слушаше на `$PORT` (Railway инжектира порта) и
   беше вързан на `127.0.0.1`. Оправено в `bot/dashboard/dashboard.py` (чете `$PORT`, bind `0.0.0.0`)
   и `bot/core/bot.py` (стартира dashboard-а винаги на Railway заради `/api/health`).
   Също `deploy.yml` вече сочи проекта/сървъра директно (`--project` / `--service`).

## Как да настроиш GitHub Secrets

За да работи автоматичният deploy към Railway, трябва да добавиш следния secret в GitHub:

### 1. Генерирай Railway Token
Отиди на https://railway.app/account/tokens и създай нов token.

### 2. Добави в GitHub Secrets
Отиди на: `https://github.com/devilforcex/discbot/settings/secrets/actions`

Добави нов secret:
- **Name**: `RAILWAY_TOKEN`
- **Value**: (токена от Railway)

> Забележка: `deploy.yml` вече сочи директно към проекта (`--project 1ced0dea-...`)
> и сървъра (`--service discbot`), така че CI не се нуждае от допълнителна
> конфигурация на линк.

### 3. Настрой Railway Project
В Railway dashboard:
- Създай нов project (или използвай съществуващ)
- Добави PostgreSQL plugin
- Копирай `DATABASE_URL` от PostgreSQL Variables
- Задай следните environment променливи за сървъра:
  - `DISCORD_BOT_TOKEN` - твоя Discord bot token
  - `GUILD_ID` - ID на сървъра
  - `MUSIC_CHANNEL_ID` - ID на музикалния канал
  - `OWNER_ID` - твоя Discord user ID
  - `DATABASE_URL` - от PostgreSQL plugin-а
  - `DASHBOARD_ENABLED` - `true`
  - `DASHBOARD_PORT` - `18080`
  - `DASHBOARD_SECRET_KEY` - random string
  - `LAVALINK_PASSWORD` - `youshallnotpass`

### 4. Deploy
След като добавиш `RAILWAY_TOKEN` secret, всеки push към `master` ще:
1. Пусне Test workflow (pytest)
2. Ако тестовете минат → пуска Deploy workflow към Railway

## Локален Deploy (алтернатива)

```bash
# Инсталирай Railway CLI
npm install -g @railway/cli

# Логни се
railway login

# Деплой
bash scripts/deploy/railway.sh
```

## Забележки

- `Lavalink.jar` е ~96MB и се качва директно в git (не е идеално, но работи за Railway Docker билд)
- За по-добра практика може да се използва Git LFS или да се свали Lavalink при билд време  
