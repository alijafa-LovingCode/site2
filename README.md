# Mehrsa Study Planner (برنامه مطالعاتی مهرسا)

یک اپلیکیشن وب خصوصی، فارسی و کاملاً کاربردی برای برنامه‌ریزی درسی و آمادگی آزمون مهرسا، با پنل مدیریت برای علی و یکپارچگی با تلگرام.

A private, Persian-first, fully functional study & exam planning web app for Mehrsa, with an admin panel for Ali and Telegram integration.

---

## فهرست مطالب / Table of Contents

1. [معرفی پروژه / Project Overview](#معرفی-پروژه--project-overview)
2. [معماری / Architecture](#معماری--architecture)
3. [نصب محلی / Local Installation](#نصب-محلی--local-installation)
4. [متغیرهای محیطی / Environment Variables](#متغیرهای-محیطی--environment-variables)
5. [پیکربندی مدیر / Admin Configuration](#پیکربندی-مدیر--admin-configuration)
6. [پیکربندی تلگرام / Telegram Configuration](#پیکربندی-تلگرام--telegram-configuration)
7. [پیکربندی هوش مصنوعی / AI Configuration](#پیکربندی-هوش-مصنوعی--ai-configuration)
8. [اجرای محلی / Running Locally](#اجرای-محلی--running-locally)
9. [اجرای تست‌ها / Running Tests](#اجرای-تستها--running-tests)
10. [مایگریشن دیتابیس / Database Migrations](#مایگریشن-دیتابیس--database-migrations)
11. [راه‌اندازی گیت‌هاب / GitHub Setup](#راهاندازی-گیتهاب--github-setup)
12. [استقرار روی Railway / Railway Deployment](#استقرار-روی-railway--railway-deployment)
13. [عیب‌یابی / Troubleshooting](#عیبیابی--troubleshooting)
14. [امنیت / Security Notes](#امنیت--security-notes)

---

## معرفی پروژه / Project Overview

**فارسی:** این پروژه یک سایت خصوصی مطالعاتی برای مهرسا (دانش‌آموز) با مدیریت علی (ادمین) است. امکانات: برنامه روزانه و هفتگی، سیستم آزمون و شمارش معکوس، کتابخانه منابع آموزشی، دستیار هوش مصنوعی (اختیاری)، چت روزانه کوچک، ربات تلگرام کاملاً فارسی، پیام‌های انگیزشی چرخشی، و پیگیری شخصی خصوصی.

**English:** This is a private study-planning site for Mehrsa (student), managed by Ali (admin). Features: daily & weekly planning, exam countdown system, educational resource library, optional AI assistant, a small daily chat, a fully Persian Telegram bot, a rotating motivational-message cycle, and a private personal cycle tracker.

### امکانات کلیدی / Key Features
- ✅ احراز هویت واقعی سمت سرور با JWT + bcrypt + قفل حساب پس از تلاش‌های ناموفق
- ✅ Real backend authentication (JWT + bcrypt + lockout after failed attempts)
- ✅ موتور برنامه‌ریزی قطعی (بدون نیاز به هوش مصنوعی) + دستیار هوش مصنوعی اختیاری
- ✅ Deterministic planning engine (works without AI) + optional AI assistant (Gemini/OpenAI)
- ✅ ربات تلگرام کاملاً فارسی با دستورات و پاسخ به سوالات تاریخ/آزمون
- ✅ Fully Persian Telegram bot with commands and free-text date/exam Q&A
- ✅ تقویم شمسی (جلالی) در تمام رابط کاربری
- ✅ Persian (Jalali) calendar throughout the UI
- ✅ پیگیری شخصی خصوصی با اعلان "فقط تخمین است"
- ✅ Private personal cycle tracker with "estimate only" disclaimer
- ✅ پشتیبان‌گیری از داده‌های سایت از پنل مدیریت
- ✅ Site data backup/export from the admin panel

---

## معماری / Architecture

```
mehrsa-planner/
│
├── app/
│   ├── main.py                # FastAPI app, routing, startup, error handling
│   ├── config.py               # Environment-driven settings (pydantic-settings)
│   ├── database.py             # SQLAlchemy engine/session (PostgreSQL)
│   ├── models.py               # ORM models (14 tables)
│   ├── schemas.py               # Pydantic request/response schemas
│   │
│   ├── auth/
│   │   ├── security.py          # bcrypt hashing + JWT
│   │   └── deps.py              # get_current_user / require_admin / require_student
│   │
│   ├── routes/                  # One module per feature area (auth, planner,
│   │                             #  exams, resources, messages, chat, cycle,
│   │                             #  telegram, admin, backup, student)
│   │
│   ├── services/
│   │   ├── jalali.py             # Gregorian <-> Persian calendar helpers
│   │   ├── planner_engine.py     # Deterministic study-plan generator
│   │   ├── messages_seed.py      # Default subjects + 30-message pool + cycle logic
│   │   ├── backup_service.py     # JSON export/import for admin backups
│   │   ├── activity_log.py       # Structured activity logging
│   │   └── startup_seed.py       # Seeds Ali/Mehrsa users + defaults on first boot
│   │
│   ├── ai/
│   │   └── ai_client.py          # Gemini / OpenAI-compatible client w/ fallback
│   │
│   ├── telegram/
│   │   ├── bot.py                # Message builders + sendMessage helper
│   │   └── telegram_app.py       # python-telegram-bot polling application
│   │
│   ├── scheduler/
│   │   └── jobs.py               # APScheduler jobs (reminders, cleanup)
│   │
│   └── utils/
│       ├── logging_config.py     # Structured logs w/ secret redaction
│       └── rate_limit.py         # slowapi limiter (shared instance)
│
├── frontend/
│   ├── templates/                # login.html, student.html, admin.html
│   └── static/
│       ├── css/style.css         # Persian RTL, responsive design system
│       └── js/                   # common.js, login.js, student.js, admin.js
│
├── migrations/                    # Alembic migrations (PostgreSQL schema)
├── tests/                         # pytest test suite
├── worker.py                      # Separate process: scheduler + Telegram polling
├── Dockerfile
├── docker-entrypoint.sh
├── railway.toml
├── requirements.txt
├── requirements-dev.txt
├── alembic.ini
├── .env.example
└── .gitignore
```

### چرا دو سرویس (وب + Worker)؟ / Why two services (web + worker)?

**فارسی:** یادآوری‌های تلگرام باید حتی وقتی هیچ‌کس سایت را باز نکرده کار کنند. بنابراین زمان‌بند (Scheduler) و polling ربات تلگرام در یک پردازش جدا (`worker.py`) اجرا می‌شوند که مستقل از سرویس وب روی Railway اجرا می‌شود.

**English:** Telegram reminders must keep working even when nobody has the website open. The scheduler and Telegram bot polling therefore run in a separate process (`worker.py`), deployed as its own Railway service, independent of the web service's uptime.

---

## نصب محلی / Local Installation

### پیش‌نیازها / Prerequisites
- Python 3.12+
- PostgreSQL 14+ (local install or Docker)
- pip

### مراحل / Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/mehrsa-planner.git
cd mehrsa-planner

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file and edit it
cp .env.example .env
# Edit .env: set DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD, etc.

# 5. Start PostgreSQL (example using Docker)
docker run --name mehrsa-postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mehrsa_planner -p 5432:5432 -d postgres:16

# 6. Run database migrations
alembic upgrade head

# 7. Start the web server
uvicorn app.main:app --reload --port 8000

# 8. (Optional, separate terminal) Start the background worker
python worker.py
```

Open `http://localhost:8000` in your browser. You should see the Persian login screen with two cards: علی (Ali) and مهرسا (Mehrsa).

---

## متغیرهای محیطی / Environment Variables

همه مقادیر حساس فقط از طریق متغیرهای محیطی خوانده می‌شوند و هیچ‌کدام در کد frontend قرار نمی‌گیرند. فایل کامل نمونه در `.env.example` موجود است. مهم‌ترین‌ها:

All secrets are read only from environment variables and are never embedded in frontend code. Full example in `.env.example`. Key variables:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (Railway sets this automatically) |
| `SECRET_KEY` | ✅ | Random 64-char hex string used to sign JWT sessions |
| `ADMIN_PASSWORD` | ✅ (first boot only) | Initial password for Ali; seeded once, then managed in the admin panel |
| `STUDENT_PASSWORD` | ✅ (first boot only) | Initial password for Mehrsa |
| `SESSION_EXPIRE_MINUTES` | — | JWT session lifetime (default 1440 = 24h) |
| `APP_TIMEZONE` / `TELEGRAM_TIMEZONE` | — | IANA timezone, e.g. `Asia/Tehran` |
| `TELEGRAM_BOT_TOKEN` | — | From @BotFather; can also be set later in the admin panel |
| `TELEGRAM_CHAT_ID` | — | Mehrsa's/Ali's Telegram chat ID |
| `TELEGRAM_ENABLED` | — | `true`/`false` |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | — | Optional; AI features fall back to the deterministic engine if absent |
| `AI_PROVIDER` | — | `gemini`, `openai`, or `none` |
| `CHAT_RETENTION_HOURS` | — | Daily chat auto-cleanup window (default 24) |
| `CYCLE_ADMIN_ACCESS` | — | `true` to let Ali view Mehrsa's cycle data (default `false`, fully private) |
| `MESSAGE_CYCLE_LENGTH` | — | Motivational message rotation length (default 30) |
| `BACKUP_DIR` | — | Where on-disk backups are written (default `/app/backups`) |

⚠️ **هرگز `.env` واقعی را کامیت نکنید.** فایل `.gitignore` این کار را برای شما مسدود می‌کند.
⚠️ **Never commit your real `.env` file.** `.gitignore` already blocks this.

---

## پیکربندی مدیر / Admin Configuration

**فارسی:** رمز عبور اولیه علی از `ADMIN_PASSWORD` خوانده و در اولین اجرا با bcrypt هش و در دیتابیس ذخیره می‌شود. پس از آن، این متغیر محیطی دیگر خوانده نمی‌شود. علی می‌تواند از تب «تنظیمات» در پنل مدیریت، رمز خود را تغییر دهد.

**English:** Ali's initial password is read from `ADMIN_PASSWORD`, bcrypt-hashed, and stored in the database on first boot. After that, this environment variable is no longer consulted. Ali can change his password anytime from the "تنظیمات / Settings" tab in the admin panel.

---

## پیکربندی تلگرام / Telegram Configuration

1. یک ربات جدید در تلگرام با [@BotFather](https://t.me/BotFather) بسازید و توکن را بگیرید.
   Create a new bot via [@BotFather](https://t.me/BotFather) and copy the token.
2. Chat ID خود (یا مهرسا) را از طریق ربات‌هایی مثل [@userinfobot](https://t.me/userinfobot) پیدا کنید.
   Find your (or Mehrsa's) chat ID using a bot like [@userinfobot](https://t.me/userinfobot).
3. وارد پنل مدیریت → تب «تلگرام» شوید و توکن، Chat ID، ساعت یادآوری و منطقه زمانی را وارد کنید.
   Go to Admin Panel → "تلگرام / Telegram" tab and enter the token, chat ID, reminder time and timezone.
4. گزینه «فعال باشد» را بزنید و روی «ارسال پیام آزمایشی» کلیک کنید تا اتصال را تست کنید.
   Toggle "فعال باشد / Enabled" and click "ارسال پیام آزمایشی / Send Test Message" to verify the connection.
5. سرویس **Worker** روی Railway را یک‌بار ری‌استارت کنید تا اتصال polling تلگرام با توکن جدید برقرار شود.
   Restart the **worker** Railway service once so Telegram polling picks up the new token.

دستورات ربات (به فارسی): `/امروز` `/برنامه` `/امتحان` `/کتاب` `/یادآوری` `/وضعیت`
همچنین می‌توانید سوالاتی مثل «امتحان بعدی من کیه؟» یا «امروز چه روزیه؟» بپرسید.

> **نکته فنی:** تلگرام فقط دستورات لاتین را به‌عنوان "bot command" تشخیص می‌دهد، بنابراین دستورات فارسی به‌صورت متن ساده پردازش می‌شوند — این پروژه این مورد را به‌درستی مدیریت کرده است.
> **Technical note:** Telegram only recognizes Latin-script "/commands" as bot_command entities; Persian slash-commands are therefore handled as plain text matching — this is implemented correctly in `app/telegram/telegram_app.py`.

---

## پیکربندی هوش مصنوعی / AI Configuration

- بدون کلید API، سیستم به‌طور کامل با **موتور برنامه‌ریزی قطعی داخلی** کار می‌کند.
  Without any API key, the system works fully using the **built-in deterministic planning engine**.
- برای فعال‌سازی هوش مصنوعی: `AI_PROVIDER=gemini` (یا `openai`) و کلید متناظر را تنظیم کنید.
  To enable AI: set `AI_PROVIDER=gemini` (or `openai`) and the matching API key.
- کلیدهای API هرگز به frontend ارسال نمی‌شوند؛ تمام تماس‌ها سمت سرور انجام می‌شود.
  API keys are never sent to the frontend; all calls happen server-side.

---

## اجرای محلی / Running Locally

```bash
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000`.

To also run reminders/Telegram locally:
```bash
python worker.py
```

---

## اجرای تست‌ها / Running Tests

تست‌ها از SQLite محلی برای سرعت استفاده می‌کنند (فقط برای تست — production باید PostgreSQL باشد).
Tests use a local SQLite file for speed (test-only — production must use PostgreSQL).

```bash
pip install -r requirements-dev.txt
pytest
```

پوشش تست‌ها شامل: ورود علی/مهرسا، مجوزدهی نقش‌ها، درس‌ها، برنامه روزانه/هفتگی، شمارش معکوس آزمون، منابع، تولید پیام تلگرام، محاسبات تاریخ، محاسبات چرخه، و health endpoint.

Test coverage includes: Ali/Mehrsa login, role authorization, subjects, daily/weekly planner, exam countdown, resources, Telegram message generation, date calculations, cycle calculations, and the health endpoint.

---

## مایگریشن دیتابیس / Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after changing app/models.py
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

سرویس وب هنگام راه‌اندازی به‌صورت ایمن `create_all` را هم صدا می‌زند تا در صورت فراموشی اجرای مایگریشن، جداول ساخته شوند — اما مسیر توصیه‌شده برای تغییرات schema همیشه Alembic است.

The web service also safely calls `create_all` on startup as a safety net if migrations were not run — but Alembic remains the recommended path for schema changes.

---

## راه‌اندازی گیت‌هاب / GitHub Setup

```bash
cd mehrsa-planner
git init
git add .
git commit -m "Initial commit: Mehrsa Study Planner"
git branch -M main
git remote add origin https://github.com/<your-username>/mehrsa-planner.git
git push -u origin main
```

مطمئن شوید `.env` واقعی هرگز commit نشده (توسط `.gitignore` مسدود شده است).
Make sure your real `.env` is never committed (blocked by `.gitignore`).

---

## استقرار روی Railway / Railway Deployment

### مرحله به مرحله / Step by step

1. **ریپازیتوری گیت‌هاب بسازید و پوش کنید** (بخش بالا را ببینید).
   **Create the GitHub repository and push** (see above).

2. **یک پروژه جدید در [Railway](https://railway.app) بسازید** → "Deploy from GitHub repo" → ریپازیتوری خود را انتخاب کنید.
   **Create a new project on [Railway](https://railway.app)** → "Deploy from GitHub repo" → select your repository.

3. **افزودن PostgreSQL:** در پروژه Railway → "+ New" → "Database" → "PostgreSQL". Railway به‌طور خودکار `DATABASE_URL` را برای سرویس‌های متصل تنظیم می‌کند.
   **Add PostgreSQL:** In the Railway project → "+ New" → "Database" → "PostgreSQL". Railway automatically injects `DATABASE_URL` into connected services.

4. **متغیرهای محیطی را تنظیم کنید** (سرویس وب → تب Variables): همه موارد فایل `.env.example` را اضافه کنید (به‌جز `DATABASE_URL` که خودکار است).
   **Set environment variables** (web service → Variables tab): add every value from `.env.example` (except `DATABASE_URL`, which is automatic).
   - `SECRET_KEY` (یک مقدار تصادفی امن بسازید)
   - `ADMIN_PASSWORD`, `STUDENT_PASSWORD`
   - `APP_ENV=production`
   - در صورت نیاز: `TELEGRAM_*`, `GEMINI_API_KEY`/`OPENAI_API_KEY`

5. **دیپلوی کنید.** Railway به‌طور خودکار `Dockerfile` را می‌سازد. entrypoint به‌صورت خودکار `alembic upgrade head` را قبل از اجرای سرور اجرا می‌کند.
   **Deploy.** Railway automatically builds the `Dockerfile`. The entrypoint automatically runs `alembic upgrade head` before starting the server.

6. **بررسی مایگریشن‌ها:** در صورت نیاز به اجرای دستی، از تب "Deployments" → "Shell" استفاده کنید:
   **Verify migrations:** If you ever need to run them manually, use the "Deployments" → "Shell" tab:
   ```bash
   alembic upgrade head
   ```

7. **سرویس Worker را اضافه کنید:** در همان پروژه Railway → "+ New" → "GitHub Repo" → همان ریپازیتوری را دوباره انتخاب کنید تا سرویس دوم ساخته شود. سپس در تنظیمات آن سرویس، "Start Command" را به‌صورت زیر تغییر دهید:
   **Add the Worker service:** In the same Railway project → "+ New" → "GitHub Repo" → select the same repository again to create a second service. Then, in that service's settings, override the "Start Command" to:
   ```
   python worker.py
   ```
   همان متغیرهای محیطی سرویس وب (به‌خصوص `DATABASE_URL`، `TELEGRAM_*`) را برای این سرویس هم تنظیم کنید (یا با "Shared Variables" به اشتراک بگذارید).
   Set the same environment variables as the web service for this one too (or share them via Railway's "Shared Variables").

8. **پیکربندی تلگرام:** پس از دیپلوی، وارد پنل مدیریت شوید و توکن/Chat ID را در تب «تلگرام» وارد کنید، سپس سرویس Worker را یک‌بار ری‌استارت کنید.
   **Configure Telegram:** After deploying, log into the admin panel and enter the token/chat ID under the "تلگرام / Telegram" tab, then restart the worker service once.

9. **دامنه تولیدشده Railway را باز کنید.**
   **Open the generated Railway domain.**

### خلاصه ساختار Railway / Railway architecture summary

```
Railway Project
├── Web Service        (Dockerfile, startCommand from railway.toml, binds 0.0.0.0:$PORT)
├── PostgreSQL Plugin   (provides DATABASE_URL)
└── Worker Service      (same repo/image, startCommand overridden to `python worker.py`)
```

### هلث‌چک / Health Check

`GET /health` → `{"status": "ok"}` — بدون نیاز به احراز هویت، برای healthcheck خودکار Railway استفاده می‌شود (تنظیم‌شده در `railway.toml`).
`GET /health` → `{"status": "ok"}` — no authentication required; used for Railway's automatic healthcheck (configured in `railway.toml`).

---

## عیب‌یابی / Troubleshooting

| مشکل / Issue | راه‌حل / Fix |
|---|---|
| سرور بالا نمی‌آید / Server won't start | بررسی کنید `DATABASE_URL` درست تنظیم شده و PostgreSQL در دسترس است. Check `DATABASE_URL` is correct and PostgreSQL is reachable. |
| خطای ۵۰۰ عمومی / Generic 500 errors | لاگ‌های سرویس وب در Railway را ببینید؛ جزئیات فنی هرگز به کاربر نمایش داده نمی‌شود. Check the web service logs on Railway; technical details are never shown to the user. |
| تلگرام پیام نمی‌فرستد / Telegram not sending | مطمئن شوید توکن و Chat ID درست هستند، "فعال باشد" تیک خورده، و سرویس Worker یک‌بار ری‌استارت شده. Verify token/chat ID are correct, "Enabled" is checked, and the worker service was restarted once. |
| مایگریشن fail می‌شود / Migration fails | مطمئن شوید سرویس PostgreSQL بالا و متصل است؛ سپس از Railway Shell دستی `alembic upgrade head` بزنید. Ensure the PostgreSQL service is up and linked; then run `alembic upgrade head` manually from the Railway shell. |
| رمز علی را فراموش کرده‌اید / Forgot Ali's password | از Railway Variables، `ADMIN_PASSWORD` جدید تنظیم کنید و ردیف کاربر `ali` را در دیتابیس دستی حذف کنید تا در بوت بعدی دوباره seed شود (یا مستقیماً `password_hash` را در دیتابیس با یک هش bcrypt جدید جایگزین کنید). Set a new `ADMIN_PASSWORD` in Railway Variables and delete the `ali` user row in the database so it reseeds on next boot (or directly replace `password_hash` in the DB with a fresh bcrypt hash). |

---

## امنیت / Security Notes

- رمزها هرگز با متن ساده ذخیره نمی‌شوند (bcrypt). Passwords are never stored in plain text (bcrypt).
- توکن‌ها/کلیدها فقط سمت سرور و فقط از متغیرهای محیطی خوانده می‌شوند. Tokens/keys are read only server-side, only from environment variables.
- کوکی‌های session به‌صورت `HttpOnly` و در تولید `Secure` هستند. Session cookies are `HttpOnly` and `Secure` in production.
- تلاش‌های ورود ناموفق محدود و پس از ۵ بار حساب موقتاً قفل می‌شود. Failed login attempts are rate-limited and the account locks temporarily after 5 failures.
- خطاهای داخلی هرگز stack trace را به کاربر نشان نمی‌دهند. Internal errors never expose stack traces to the user.
- داده‌های پیگیری شخصی مهرسا به‌طور پیش‌فرض کاملاً خصوصی است (`CYCLE_ADMIN_ACCESS=false`). Mehrsa's personal cycle-tracking data is fully private by default.

---

پروژه با ❤️ برای مهرسا ساخته شده است. 🌱
Built with ❤️ for Mehrsa. 🌱
