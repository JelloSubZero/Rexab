# Rexab

Rexab — Telegram-бот для совместного ведения расходов в комнате: участники присоединяются по коду или QR, загружают чеки (сумма распознаётся автоматически через OCR) и платежи, а бот считает, кто сколько должен, и проводит подтверждённые погашения долгов.

## Основные возможности

- создание комнаты и получение кода приглашения + QR-кода;
- присоединение к комнате по коду через `/start` или по QR;
- список участников комнаты; владелец может исключать участников (кроме себя);
- защита закрытой комнаты от новых участников;
- загрузка чека фотографией — сумма распознаётся автоматически (OCR), при неудаче бот просит ввести сумму вручную;
- просмотр и удаление чеков комнаты;
- добавление платежей с указанием плательщика и назначения расхода;
- просмотр и удаление платежей;
- равное разделение общей суммы между участниками;
- автоматический пересчёт долгов после добавления/удаления платежа;
- расчёт «кто кому должен» и оптимизация переводов (минимальное число транзакций);
- settlement: должник или получатель инициирует погашение, получатель подтверждает; история погашений комнаты;
- журнал истории комнаты (добавление/удаление платежей, вступление участников);
- персональные уведомления участникам об изменении долга;
- закрытие комнаты владельцем (вручную, из меню комнаты);
- централизованные проверки прав доступа: почти каждое действие проверяет, что пользователь всё ещё состоит в комнате, а изменяющие действия — что он вправе их совершать.

## Архитектура

Проект разделён на слои: обработчики Telegram-апдейтов, бизнес-логика, доступ к данным и модели.

```text
Rexab/
├── bot/
│   └── app.py                  # сборка Dispatcher, регистрация роутеров
├── handlers/                   # aiogram-роутеры (по одному файлу на сценарий)
│   ├── start.py
│   ├── room.py
│   ├── room_invite.py
│   ├── room_members.py
│   ├── room_view.py
│   ├── room_history.py
│   ├── receipt.py
│   ├── receipt_callbacks.py
│   ├── room_receipts.py
│   ├── split_bill.py
│   ├── payment.py
│   ├── debt.py
│   ├── settlement.py
│   └── settlement_history.py
├── services/                   # бизнес-логика и проверки прав
│   ├── *_permission_service.py     # разрешено ли действие конкретному пользователю
│   ├── room_service.py, room_member_service.py, room_access_service.py
│   ├── room_view_service.py, room_message_service.py
│   ├── receipt_service.py, room_payment_service.py, settlement_service.py
│   ├── debt_service.py, split_bill_service.py
│   ├── notification_service.py, qr_service.py, user_service.py
│   └── ocr/                        # распознавание суммы чека
│       ├── ocr_service.py              # оркестрация полного цикла
│       ├── engine.py                   # обёртка над pytesseract
│       ├── preprocess.py, cropper.py, locator.py   # подготовка изображения (OpenCV)
│       ├── parser.py, normalizer.py, product_parser.py
│       └── total_extractor.py, total_parser.py     # определение итоговой суммы
├── repositories/                # SQLAlchemy-запросы, без бизнес-правил
├── database/
│   ├── models.py                # ORM-модели
│   ├── session.py                # async engine / sessionmaker
│   └── init_db.py                # создание таблиц при старте
├── keyboards/                   # inline-клавиатуры под каждый экран
├── states/                      # FSM-состояния (ввод чека/платежа)
├── utils/code_generator.py      # генерация кода комнаты
├── tests/                       # pytest, 51 тест на сервисы и права доступа
├── config.py                    # чтение .env, пути static/QR/receipts/logs
└── main.py                      # точка входа
```

## Технологии

- Python 3.12
- [aiogram](https://docs.aiogram.dev/) 3 — Telegram Bot API
- SQLAlchemy 2 (async) + `aiosqlite` — доступ к SQLite
- `pytesseract` + OpenCV (`opencv-python`) + Pillow + NumPy — OCR чеков (нужен установленный в системе Tesseract)
- `qrcode` — генерация QR-приглашений
- `python-dotenv` — конфигурация через `.env`
- `pytest` + `pytest-asyncio` — тесты (`requirements-dev.txt`)

Для базы используется асинхронный SQLAlchemy engine и `async_sessionmaker`. `expire_on_commit=False` включён в конфигурации сессии.

## База данных

Основные сущности:

```text
users
rooms
room_members
room_views
room_messages
room_payments
room_history
room_settlements
receipts
```

Для защиты от дублей используются уникальные ограничения:

```text
room_members   UNIQUE(room_id, user_id)
room_views     UNIQUE(room_id, user_id)
```

## Работа с сообщениями

`RoomMessageService` сохраняет `chat_id`/`message_id` каждого отправленного ботом сообщения комнаты (`room_messages`) и умеет удалить их все разом (`delete_all`). Основной экран комнаты каждого пользователя отдельно хранится и обновляется через `RoomView` (`room_views`), поэтому меню комнаты редактируется на месте, а не дублируется новыми сообщениями.

> На данный момент `RoomMessageService.delete_all` и `RoomService.delete_room` реализованы, но не вызываются автоматически при закрытии комнаты (`room_close_confirm` только переводит комнату в статус `closed`). Это осознанный текущий пробел, а не баг: инфраструктура для полной очистки готова, интеграция ещё не подключена.

## Транзакции

Репозитории по возможности не делают промежуточный `commit()` — используется `flush()`, а итоговый `commit()` выполняется на уровне бизнес-операции в обработчике, например:

```text
создание/удаление платежа → история → пересчёт долгов → уведомления → RoomMessage → COMMIT
```

Это не позволяет зафиксировать только часть операции.

## Запуск

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Создайте `.env` в корне проекта:

```env
BOT_TOKEN=токен_бота_из_BotFather
BOT_USERNAME=username_бота_без_@
DATABASE_URL=sqlite+aiosqlite:///split_receipt.db
OCR_LANGUAGES=pol+eng+rus
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

`DATABASE_URL`, `OCR_LANGUAGES` и `TESSERACT_PATH` необязательны — есть значения по умолчанию (см. `config.py`); `TESSERACT_PATH` нужен, только если `tesseract` не в `PATH`. Для распознавания чеков должен быть установлен сам [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).

Запуск бота:

```powershell
python main.py
```

Таблицы SQLite создаются автоматически при старте (`database/init_db.py`).

## Тесты

```powershell
pip install -r requirements-dev.txt
pytest
```

Тесты (папка `tests/`) покрывают сервисы прав доступа, расчёт долгов, работу с платежами, чеками и погашениями — без обращения к реальному Telegram API.

## Основной пользовательский сценарий

```text
Создать комнату
      ↓
Получить код / QR
      ↓
Пригласить участников
      ↓
Добавить чеки (сумма распознаётся автоматически)
      ↓
Добавить платежи
      ↓
Автоматический расчёт долгов + уведомления участникам
      ↓
Settlement → подтверждение погашения получателем
      ↓
Владелец закрывает комнату вручную
```

## Известные ограничения

- закрытие комнаты не автоматизировано (нет авто-закрытия после погашения всех долгов, хотя `SettlementService.is_room_fully_settled` для этого уже есть) и не чистит связанные Telegram-сообщения — см. раздел «Работа с сообщениями»;
- `requirements.txt` — это неотфильтрованный `pip freeze` из окружения разработки и содержит пакеты, не используемые проектом (например, `paddleocr`, `fastapi`, `redis`, `asyncpg`); перед продакшен-деплоем стоит собрать его заново по фактическим импортам.

## Статус

Основные сценарии — комнаты, участники, чеки с OCR, платежи, расчёт и оптимизация долгов, settlement — реализованы и покрыты тестами. Права доступа недавно централизованы в отдельные `*_permission_service`; текущая работа сосредоточена на стабилизации транзакций и доведении до конца автоматической очистки комнаты при закрытии.
