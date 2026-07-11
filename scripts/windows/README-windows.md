# 🪟 DiscBot — Windows Guide

Боте, инсталацията е фиксирана за **`E:\discbot`** — всичко се инсталира
и работи само там (код, `.venv`, `Lavalink.jar`, `.env`, `data/`, `logs/`).
Ако искаш друга папка, сетни `$env:DISCBOT_DIR` в PowerShell преди one-liner-а.

## 🚀 Най-бързият начин (препоръчван)

Отвори **PowerShell** (Win+R → `powershell`) и постави един ред:

```powershell
# Първа инсталация — сваля бота в E:\discbot и те превежда през setup-а
irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/install.ps1 | iex

# По-нататъшни ъпдейти (също в E:\discbot)
irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex
```

> За друга папка (не е нужно в твоя случай):
> ```powershell
> $env:DISCBOT_DIR = 'D:\bots\discbot'
> irm ... | iex
> ```

> Ако ти гръмне с *"execution of scripts is disabled on this system"*,
> пусни веднъж:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> и отговори `Y`. Това е еднократно.

### Какво прави `install.ps1`?
1. Избира директория за инсталация — по подразбиране `%LOCALAPPDATA%\DiscBot` (per-user, без admin права)
2. Тества за `git` и клонира repo-то
3. Проверява за **Python 3.12+** и **Java 17+**; ако липсват, ти отваря download страниците
4. Създава `.venv` и `pip install -r requirements.txt`
5. Копира `.env.example` → `.env`, `application.yml.example` → `application.yml`
6. Сваля най-новия `Lavalink.jar` от GitHub releases
7. Отваря `.env` в Notepad за попълване на токени
8. По желание стартира бота веднага

Инсталаторът е non-destructive — ако папката вече съществува, той сам те пренасочва
към `update.ps1`.

### Какво прави `update.ps1`?
- `git fetch` + `git merge --ff-only`
- Блокира **само tracked** локални промени (като `update.sh`). Untracked файлове
  (`generated-page.html`, локални бележки и т.н.) **не** спират ъпдейта.
- При tracked промени: interactive избор **S**tash / **D**iscard, или force:
  `$env:DISCBOT_FORCE='1'; irm .../update.ps1 | iex`
- Никога не пипа `.env`, `data/`, `logs/` (gitignored)
- Освежава pip зависимостите в `.venv`
- По желание спира стария процес и стартира новия

## 📦 Алтернативен начин — batch файлове (двоен клик)

1. **Инсталирай нужните неща** (веднъж):
   - **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
     - ⚠️ По време на инсталацията **чекни** `Add Python to PATH`
   - **Java 17+** (JRE) — [adoptium.net](https://adoptium.net/)
     - ⚠️ Чекни `Set JAVA_HOME` / `Add to PATH`

2. **Свали/клонирай** repo-то в папка по избор, напр. `C:\DiscBot`

3. **Първоначална настройка** — двойно кликни:
   ```
   scripts\windows\setup.bat
   ```
   Скриптът ще:
   - провери за Python и Java
   - създаде `.venv` и инсталира зависимостите
   - направи `.env` от template-а
   - свали последния `Lavalink.jar`
   - отвори `.env` в Notepad, за да попълниш токените

4. **Попълни `.env`** (трябва поне):
   - `DISCORD_BOT_TOKEN`
   - `GUILD_ID`
   - `MUSIC_CHANNEL_ID`
   - `OWNER_ID`

5. **Стартирай** — двойно кликни `scripts\windows\start.bat` или изпълни в PowerShell:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\windows\start.ps1
   ```
   Ще се отворят два конзолни прозореца — един за Lavalink, един за бота.

6. **Спиране** — `scripts\windows\stop.bat` / `stop.ps1` (или затвори прозорците)

7. **Ъпдейт** — `scripts\windows\update.bat` или `update.ps1`

## 🛠️ Setup.exe (опционално, с Inno Setup)

Ако искаш истински инсталатор с Start Menu / Desktop shortcuts:

1. Свали [Inno Setup 6](https://jrsoftware.org/isinfo.php)
2. Отвори `scripts\windows\DiscBot.iss` в Inno Setup
3. **Compile** → ще получиш `scripts\windows\Output\DiscBotSetup.exe`

> Забележка: setup.exe **не** включва Python, Java и Lavalink.jar — те се
> теглят от потребителя / автоматично от `install.ps1`/`setup.bat`. Това прави
> setup-а малък (под MB) и винаги с последна версия на Lavalink.

## 📂 Всички скриптове в `scripts\windows\`

| Файл | Какво прави |
|---|---|
| `install.ps1` | One-liner PowerShell инсталатор |
| `update.ps1` | One-liner PowerShell ъпдейтър (рестартира бота ако искаш) |
| `start.ps1` | Стартира Lavalink + бота от PowerShell |
| `stop.ps1` | Спира процесите по CIM (без грубо `taskkill`) |
| `setup.bat` | Batch версия на first-time setup |
| `start.bat` | Batch стартиране |
| `stop.bat` | Batch спиране |
| `update.bat` | Batch ъпдейт (git pull + pip install) |
| `DiscBot.iss` | Inno Setup скрипт |
| `README-windows.md` | Този файл |

## ❓ Често срещани проблеми

| Проблем | Решение |
|---|---|
| `'python' is not recognized` | Преинсталирай Python с отметка *Add Python to PATH*, после рестартирай PowerShell. |
| `'java' is not recognized` | Инсталирай Java 17+ от Adoptium и рестартирай. |
| `irm : The request was aborted` / SSL грешка | PowerShell използва по-стар TLS. Пусни: `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12` и пробвай пак. |
| `execution of scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Lavalink тръгва и веднага спира | Провери `application.yml` и че порт 12333 не е зает. |
| Ботът казва `Lavalink not connected` | Изчакай 10-15 сек Lavalink да вдигне. Виж дали паролата в `.env` и `application.yml` съвпада. |
| Ботът не отговаря на команди | Провери `message content intent` в Discord Developer Portal и върния `GUILD_ID`/`MUSIC_CHANNEL_ID`. |
| `update.ps1` отказва да ъпдейтне | Имаш **tracked** локални промени (не untracked файлове). При interactive run избери **S** (stash) или **D** (discard). За one-liner force: `$env:DISCBOT_FORCE='1'; irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 \| iex`. `.env` / `data/` / untracked файлове не се пипат. |

## 🔄 Автоматично стартиране с Windows

Най-лесно:
1. `Win+R` → `shell:startup` (отваря Startup папката)
2. Създай shortcut там, десен клик → Properties:
   - **Target**: `powershell -ExecutionPolicy Bypass -File "C:\Users\<ти>\AppData\Local\DiscBot\scripts\windows\start.ps1"`
   - **Start in**: `C:\Users\<ти>\AppData\Local\DiscBot`
   - **Run**: Minimized (за да не ти изскача прозорец)

За по-сериозно ползване — [NSSM](https://nssm.cc/) за инсталиране на
python и java като Windows услуги.

## 💡 За `update.sh`

`update.sh` е за Linux/Docker. На Windows ползвай `update.ps1` (един ред в
PowerShell) или `update.bat` — те правят същото но за native Windows инсталация.
