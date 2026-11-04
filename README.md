# Currency Exchange Service

RESTful веб-сервис для автоматизации процесса обмена валют с интеграцией курсов Национального Банка Республики Беларусь (НБ РБ). Проект выполнен на асинхронном стеке **FastAPI + SQLAlchemy 2.0 (asyncio) + PostgreSQL**, а фоновые задачи и синхронизация курсов управляются с помощью **Taskiq (RabbitMQ)**.

---

## Технологический стек

* **Язык / Фреймворк:** Python 3.11+ / FastAPI
* **База данных:** PostgreSQL
* **ORM & Миграции:** SQLAlchemy 2.0 (AsyncIO), Alembic
* **Брокер сообщений & Фоновые задачи:** RabbitMQ, Taskiq
* **Валидация & Конфигурация:** Pydantic v2, Pydantic-Settings
* **Контейнеризация:** Docker, Docker Compose

---

## Основные возможности и функционал

1. **Автоматическая синхронизация курсов НБ РБ:**
   * Фоновая задача запускается при старте приложения и периодически (1 раз в день).
   * Идемпентность записи: повторный запуск задачи за ту же дату обновляет существующие курсы (`UPDATE`), не дублируя записи (`INSERT`).

2. **Двухэтапный обмен валют:**
   * **Этап 1 (`POST /deals/initiate`):** Предварительный расчет суммы обмена на основе текущего курса, генерация и сохранение незавершенной сделки со статусом `PENDING`.
   * **Этап 2 (`POST /deals/action`):** Подтверждение (`CONFIRM`) или отклонение (`DECLINED`) сделки по ее уникальному `deal_id`.

3. **Справочник и Аналитика:**
   * **`GET /deals/pending`:** Получение списка всех незавершенных сделок (`PENDING`).
   * **`GET /deals/analytics`:** Получение финансовой аналитики за выбранный период (`date_from`, `date_to`) с опциональным фильтром по валюте. Агрегирует приход (`incoming`), расход (`outgoing`) и общее число сделок, где участвовала валюта.

4. **Точность финансовых расчетов:**
   * Все денежные суммы и курсы хранятся и обрабатываются с использованием типа `Decimal` для предотвращения ошибок округления и сериализуются в строки в формате JSON.

---

## Развертывание и запуск проекта

Проект полностью контейнеризован и готов к быстрому запуску через **Docker Compose**.

### Предварительные требования

* Установленный **Docker** и **Docker Compose**.

### Шаги для запуска

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/sawelyew/currency-exchange-service.git
   cd currency-exchange-service
   ```

2. **Создайте файл конфигурации `.env`:**
   Скопируйте пример настроек из файла `.env.example`:
   ```bash
   cp .env.example .env
   ```
   *(Файл содержат дефолтные параметры для подключения к PostgreSQL и RabbitMQ внутри контейнеров Docker).*

3. **Запустите проект с помощью Docker Compose:**
   ```bash
   docker compose up --build
   ```

При запуске автоматически:
* Поднимутся сервисы PostgreSQL, RabbitMQ, FastAPI-приложение и Taskiq Worker.
* Запустятся миграции БД через Alembic (`alembic upgrade head`).
* Выполнится стартовая задача получения курсов валют НБ РБ.

---

## Документация API (Swagger / ReDoc)

После успешного запуска веб-интерфейс Swagger UI и ReDoc доступны по следующим адресам:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **RabbitMQ Management UI:** [http://localhost:15672](http://localhost:15672) *(Логин/Пароль: guest / guest)*

---

## Описание Эндпоинтов API

### 1. Курсы валют и Инициализация

* **`POST /deals/initiate`** — Запрос на инициализацию сделки обмена.
  * **Request Body:**
    ```json
    {
      "source_currency": "USD",
      "target_currency": "BYN",
      "amount": 100.50
    }
    ```
  * **Response Status 200:**
    ```json
    {
      "deal_id": "f73a6211-78c0-4e2c-be2e-a89230d07d9a",
      "target_amount": "299.2790",
      "rate": "2.9779"
    }
    ```

### 2. Фиксация сделки

* **`POST /deals/action`** — Подтвердить или отклонить сделку.
  * **Request Body:**
    ```json
    {
      "deal_id": "f73a6211-78c0-4e2c-be2e-a89230d07d9a",
      "action": "CONFIRM"
    }
    ```
    *(Значения поля `action`: `CONFIRM` или `DECLINE`)*

  * **Response Status 200:**
    ```json
    {
      "deal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "status": "CONFIRMED",
      "message": "Сделка успешно подтверждена и зафиксирована в системе."
    }
    ```
    
### 3. Незавершенные сделки

* **`GET /deals/pending`** — Возвращает список всех сделок со статусом `PENDING`.
  * **Response Status 200:**
    ```json
    {
      "deals": [
        {
          "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
          "source_currency": "USD",
          "target_currency": "BYN",
          "source_amount": "100.5000",
          "target_amount": "299.2790",
          "rate": "2.9779"
        }
      ]
    }
    ```

### 4. Аналитика сделок

* **`GET /deals/analytics`** — Вывод агрегированной аналитики по подтвержденным сделкам.
  * **Query Parameters:**
    * `date_from` *(required)* — Начало периода (`YYYY-MM-DD`).
    * `date_to` *(required)* — Конец периода (`YYYY-MM-DD`).
    * `currency` *(optional)* — Фильтр по ISO-коду валюты (например, `USD`).
  * **Response Status 200:**
    ```json
    {
      "analytics": [
        {
          "currency": "USD",
          "incoming_amount": "251.0000",
          "outgoing_amount": "0.0000",
          "deals_count": 3
        },
        {
          "currency": "BYN",
          "incoming_amount": "0.0000",
          "outgoing_amount": "598.5580",
          "deals_count": 3
        }
      ]
    }
    ```

---

## Структура проекта

```text
currency-exchange-service/
├── alembic/              # Скрипты и конфигурация миграций Alembic
├── app/
│   ├── api/              # Эндпоинты FastAPI (ручки сервиса)
│   ├── core/             # Конфигурация, подключение к БД, брокер сообщений
│   ├── models/           # SQLAlchemy модели базы данных
│   ├── repositories/     # Слой работы с БД (Data Access Layer)
│   ├── schemas/          # Pydantic схемы (DTO)
│   ├── services/         # Бизнес-логика приложений, работы с НБ РБ и фоновой задачей
│   └── main.py           # Точка входа FastAPI приложения
├── .env.example          # Пример файла переменных окружения
├── .gitignore            # Исключения Git
├── alembic.ini           # Конфигурация Alembic
├── docker-compose.yml    # Конфигурация Docker Compose
├── Dockerfile            # Сборка образа приложения
└── requirements.txt      # Зависимости Python
```