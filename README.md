# Rexab

Rexab — сервис для совместного ведения расходов в комнате: участники присоединяются по коду или QR, загружают чеки (сумма распознаётся автоматически через OCR) и платежи, а система считает, кто сколько должен, и проводит подтверждённые погашения долгов.

Есть три способа с ним работать: **Telegram-бот** (изначальный интерфейс), **веб-API на FastAPI** и **веб-фронтенд на Next.js**. Все три используют один и тот же слой бизнес-логики (`services/`) и одну базу данных — ни API, ни фронтенд не дублируют и не пересчитывают правила самостоятельно.

```text
Telegram Bot ──┐
               ├──> services/ + repositories/ ──> database (SQLAlchemy + Alembic)
Web (Next.js) ─┴──> FastAPI (api/)
```

## Основные возможности

- регистрация и вход: email+пароль или Telegram Login Widget (веб), автоматическая регистрация через `/start` (бот);
- создание комнаты и получение кода приглашения + QR-кода;
- присоединение к комнате по коду (бот: `/start`/QR, веб: `POST /api/rooms/join`);
- список участников комнаты; владелец может исключать участников (кроме себя), участник может выйти сам;
- загрузка чека фотографией — сумма распознаётся автоматически (OCR), при неудаче бот просит ввести сумму вручную (только в Telegram — веб пока не принимает чеки);
- добавление платежей с указанием плательщика и назначения расхода, равное разделение общей суммы между участниками;
- автоматический пересчёт долгов после добавления/удаления платежа, расчёт «кто кому должен» и оптимизация переводов (минимальное число транзакций);
- settlement: должник или получатель инициирует погашение, получатель подтверждает; сервер сам пересчитывает актуальный долг и отклоняет запрос с устаревшей суммой;
- журнал истории комнаты, персональные уведомления в Telegram об изменении долга;
- закрытие комнаты владельцем (бот — вручную, статус `closed`) или полное удаление комнаты со всеми данными (веб, `DELETE /api/rooms/{id}`, каскадно);
- централизованные проверки прав доступа: почти каждое действие проверяет, что пользователь всё ещё состоит в комнате, а изменяющие действия — что он вправе их совершать. Одна и та же permission-логика используется и ботом, и API.

## Архитектура

```text
Rexab/
├── bot/app.py                  # Telegram-бот: сборка Dispatcher, регистрация роутеров
├── handlers/                   # aiogram-роутеры (по одному файлу на сценарий)
├── api/                        # FastAPI веб-бэкенд
│   ├── main.py                     # приложение, CORS, единый формат ошибок, lifespan (миграции)
│   ├── dependencies.py             # get_session, get_current_user (JWT)
│   ├── routers/                    # auth, rooms, members, payments, settlements, dashboard
│   └── schemas/                    # Pydantic-модели запросов/ответов
├── frontend/                   # Next.js веб-клиент (см. frontend/README.md)
├── services/                   # бизнес-логика и проверки прав — общие для бота и API
│   ├── *_permission_service.py     # разрешено ли действие конкретному пользователю
│   ├── auth_service.py, telegram_auth_service.py   # bcrypt-хэши, JWT, проверка Telegram Login Widget
│   ├── room_service.py, room_member_service.py, room_access_service.py
│   ├── room_view_service.py, room_message_service.py
│   ├── receipt_service.py, room_payment_service.py, settlement_service.py
│   ├── debt_service.py, split_bill_service.py
│   ├── notification_service.py, qr_service.py, user_service.py
│   └── ocr/                        # распознавание суммы чека (pytesseract + OpenCV)
├── repositories/                # SQLAlchemy-запросы, без бизнес-правил
├── database/
│   ├── models.py                    # ORM-модели
│   ├── session.py                   # async engine / sessionmaker
│   └── init_db.py                   # запуск Alembic-миграций при старте (бот и API)
├── alembic/                     # миграции схемы БД
├── keyboards/, states/          # inline-клавиатуры и FSM-состояния бота
├── utils/code_generator.py      # генерация кода комнаты
├── logging_config.py            # настройка logging (консоль + logs/rexab.log)
├── tests/                       # pytest: сервисы, права доступа, все эндпоинты API
├── config.py                    # чтение .env
├── main.py                      # точка входа бота
└── requirements.txt, requirements-api.txt, requirements-dev.txt
```

## Технологии

**Бэкенд:**
- Python 3.12, SQLAlchemy 2 (async) + Alembic — миграции, SQLite для dev/test (Postgres — см. «Продакшен» ниже)
- [aiogram](https://docs.aiogram.dev/) 3 — Telegram Bot API
- FastAPI + Pydantic 2 — веб-API; `bcrypt` — хэширование паролей; `PyJWT` — access-токены
- `pytesseract` + OpenCV + Pillow + NumPy — OCR чеков (нужен установленный в системе Tesseract)
- `qrcode`, `python-dotenv`
- `pytest` + `pytest-asyncio` — тесты (`requirements-dev.txt`)

**Фронтенд:** Next.js (App Router) + TypeScript + Tailwind v4 + Vitest — подробности в [frontend/README.md](frontend/README.md).

## База данных

```text
users, rooms, room_members, room_views, room_messages,
room_payments, room_history, room_settlements, receipts
```

Схема управляется миграциями Alembic (`alembic/versions/`), а не только `Base.metadata.create_all()` — и бот, и API запускают `alembic upgrade head` при старте (`database/init_db.py`). Тесты используют собственную in-memory SQLite-схему и миграции не трогают.

Уникальные ограничения: `room_members(room_id, user_id)`, `room_views(room_id, user_id)`; `users.email` и `users.telegram_id` — nullable + unique (аккаунт может быть Telegram-only, email-only или обоими сразу).

## Работа с сообщениями (Telegram)

`RoomMessageService` сохраняет `chat_id`/`message_id` каждого отправленного ботом сообщения комнаты (`room_messages`) и умеет удалить их все разом (`delete_all`). Основной экран комнаты каждого пользователя отдельно хранится и обновляется через `RoomView` (`room_views`), поэтому меню комнаты редактируется на месте, а не дублируется новыми сообщениями.

> `RoomMessageService.delete_all` реализован, но не вызывается автоматически при закрытии комнаты в боте (`room_close_confirm` только переводит статус в `closed`). Полное каскадное удаление комнаты (включая эти сообщения) доступно через веб — `DELETE /api/rooms/{id}`.

## Транзакции

Репозитории по возможности не делают промежуточный `commit()` — используется `flush()`, а итоговый `commit()` выполняется на уровне бизнес-операции в обработчике/роутере, например:

```text
создание/удаление платежа → история → пересчёт долгов → уведомления → RoomMessage → COMMIT
```

## Логирование

`logging_config.py` настраивает стандартный `logging` (не `print()`) — пишет и в консоль, и в `logs/rexab.log`. Уровень — `LOG_LEVEL` в `.env` (по умолчанию `INFO`). OCR-пайплайн пишет подробности распознавания на уровне `DEBUG`. Секреты (пароли, JWT, `BOT_TOKEN`) в логи не попадают.

## Запуск бота

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Создайте `.env` в корне проекта (см. [.env.example](.env.example) — там же переменные для веб-части):

```env
BOT_TOKEN=токен_бота_из_BotFather
BOT_USERNAME=username_бота_без_@
DATABASE_URL=sqlite+aiosqlite:///split_receipt.db
OCR_LANGUAGES=pol+eng+rus
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
LOG_LEVEL=INFO
```

Всё, кроме `BOT_TOKEN`, необязательно — есть значения по умолчанию (см. `config.py`). Для распознавания чеков должен быть установлен сам [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).

```powershell
python main.py
```

## Запуск веб-API

```powershell
pip install -r requirements.txt -r requirements-api.txt
```

Дополнительно в `.env`: `JWT_SECRET` (обязателен для чего-либо кроме локальной разработки — сгенерировать: `python -c "import secrets; print(secrets.token_hex(32))"`), `CORS_ORIGINS` (по умолчанию `http://localhost:3000`).

```powershell
uvicorn api.main:app --reload --port 8000
```

Миграции применяются автоматически при старте. Документация API — `/docs` (Swagger UI от FastAPI).

## Запуск веб-фронтенда

```powershell
cd frontend
npm install
npm run dev
```

Требует запущенный API (по умолчанию ожидает его на `http://localhost:8000` — переопределяется через `NEXT_PUBLIC_API_URL`, см. `frontend/.env.example`). Подробности — [frontend/README.md](frontend/README.md).

## Тесты

Бэкенд:

```powershell
pip install -r requirements-dev.txt
pytest
```

95 тестов (`tests/`) — сервисы прав доступа, расчёт долгов, чеки, платежи, погашения, и все эндпоинты API (auth, rooms, members, payments, settlements, dashboard) — без обращения к реальному Telegram API.

Фронтенд:

```powershell
cd frontend
npm test
```

32 теста (Vitest + React Testing Library) — подробности в `frontend/README.md`.

## Основной пользовательский сценарий

```text
Регистрация / вход (Telegram или email)
      ↓
Создать комнату → код / QR
      ↓
Пригласить участников
      ↓
Добавить чеки (бот, OCR) и/или платежи (бот или веб)
      ↓
Автоматический расчёт долгов
      ↓
Settlement → подтверждение погашения получателем
      ↓
Владелец закрывает или удаляет комнату
```

## Известные ограничения

- закрытие комнаты в боте не автоматизировано (нет авто-закрытия после погашения всех долгов, хотя `SettlementService.is_room_fully_settled` для этого уже есть) и не чистит связанные Telegram-сообщения — см. «Работа с сообщениями»;
- чеки и OCR доступны только через Telegram-бота, у веба нет загрузки фото;
- в вебе нет формы принудительного добавления участника по id — только самостоятельное вступление по коду (осознанное решение, см. коммит роутера `members`);
- Settings в вебе — только просмотр профиля и выход, редактирования профиля нет (нет соответствующего эндпоинта).

## Продакшен

Для продакшена вместо SQLite предусмотрен Postgres — переключается одной переменной `DATABASE_URL` (`postgresql+asyncpg://...`), схема работает через Alembic одинаково для обоих; убедитесь, что `asyncpg` установлен. `JWT_SECRET` обязателен (без него дефолт — заведомо небезопасное значение для разработки). Секреты (`BOT_TOKEN`, `JWT_SECRET`, `DATABASE_URL`) — только через `.env`, не в git.

## Статус

Backend (бот + API) и frontend реализованы и покрыты тестами: комнаты, участники, чеки с OCR (бот), платежи, расчёт и оптимизация долгов, settlement, dashboard. Права доступа централизованы в `*_permission_service` и переиспользуются между ботом и API. Текущие открытые вопросы — в разделе «Известные ограничения» выше.
