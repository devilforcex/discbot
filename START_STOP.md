# 🚀 DrusaBoT — Как да пусна и спра бота

## ⚡ Бърз старт (само с 2 бутона)

| Действие | Команда |
|----------|---------|
| **Стартирай всички** (Lavalink + Bot + Dashboard) | `start_all.bat` |
| **Спри всички** | `stop_all.bat` |

> ⚠️ **Преди първо стартиране** трябва да имаш `.venv` с инсталирани зависимости:
> ```bash
> python -m venv .venv
> .venv\Scripts\pip install -r requirements.txt
> ```
> Или изпълни **`setup.py`** — той прави всичката настройка автоматично.

---

## 📋 Повече контрол — стартирай поотделно

### 1. Lavalink (аудио сървър)
```bash
# Windows
start_lavalink.bat

# Linux / macOS
./start_lavalink.sh
```
Локация: http://localhost:12333

---

### 2. Бот + Dashboard
```bash
# Windows
start_bot.bat

# Linux / macOS
./start_bot.sh
```
Dashboard: http://localhost:18080

---

### 3. Само Dashboard (опционално)
```bash
# Windows
start_dashboard.bat

# Linux / macOS
./start_dashboard.sh
```

---

## 🛑 Спиране на services

### Вариант А — автоматично (препоръчително)
Стартирай `stop_all.bat`

Той ще спре:
- 🟢 Lavalink (Java процес)
- 🟢 Discord Bot (Python процес)

### Вариант Б — ръчно
Стигни до терминалния прозорец на процеса и натисни **Ctrl + C**.

---

## ✅ Проверки

| Проверка | Команда / URL |
|----------|---------------|
| Bot статус | `http://localhost:18080/api/health` |
| Lavalink статус | `http://localhost:18080/api/health/lavalink` |
| Dashboard | http://localhost:18080 |

---

## ⚠️ Забележки

- **Първо пусни Lavalink**, после бота. Lavalink има нужда от 5–10 секунди да се инициализира.
- Ако dashboard не се появи, увери се че `python -m bot.dashboard.dashboard` е стартиран (или стартирай `start_dashboard.bat`).
- При промяна на код, ботът се рестартира автоматично ако използваш debug режим.

---

**Made with ❤️ за Discord общността** 🎧