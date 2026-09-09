## Развертывание вручную (Ubuntu)

1. Клонировать репозиторий
```bash
git clone https://github.com/evgenemit/nbrb.git
cd nbrb
```

2. Установить uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

3. Установить зависимоcти
```bash
uv sync --locked
```

4. Создать .env файл
```bash
touch .env
```
```bash
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_name
DB_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

API_URL=https://api.nbrb.by/exrates/rates
```
5. Установить PostgreSQL
```bash
sudo apt install postgresql postgresql-contrib
```
6. Создать базу данных
```bash
sudo -u postgres psql

CREATE DATABASE your_name;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_name TO your_user;
\c your_name
GRANT ALL ON SCHEMA public TO your_user;
GRANT ALL ON SCHEMA public TO public;
```

7. Запустить миграции
```bash
uv run alembic upgrade head
```
8. Запустить тесты
```bash
uv run pytest
```

9. Запустить приложение
```bash
uv run fastapi run src/api/main.py --port 80
```

## Развертывание c Docker

1. Клонировать репозиторий
```bash
git clone https://github.com/evgenemit/nbrb.git
cd nbrb
```
2. Создать .env файл
```bash
touch .env
```
```bash
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_name
DB_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

API_URL=https://api.nbrb.by/exrates/rates
``` 
3. Запустить приложение
```bash
sudo docker compose up -d
```

## Описание API

Базовый url: `http://127.0.0.1`

### 1. Получить список всех доступных для обмена валют
```http
GET /currencies/
```

Ответы:

|Код|Тип|Описание|
|---|---|---|
|200|`application/json`|Возвращает список объектов класса CurrencyPublic|

Примеры ответа:
```json
200 Successful Response
[
  {
    "abbreviation": "AUD",
    "id": 440,
    "rate": 2.216,
    "full_name": "1 Австралийский доллар"
  },
  {
    "abbreviation": "AZN",
    "id": 507,
    "rate": 1.7879,
    "full_name": "1 Азербайджанский манат"
  }
]
```

### 2. Создать сделку
Первый этап обмена валют. Создание сделки.
```http
POST /trades/
{
  "amount": 0,
  "from_cur_id": 0,
  "to_cur_id": 0
}
```
Принимает данные в формате `application/json` .

- amount - (обязательное) - сумма сделки в исходной валюте
- from_cur_id - (обязательное) - id исходной валюты
- to_cur_id - (обязательное) - id целевой валюты

Ответы:

|Код|Тип|Описание|
|---|---|---|
|200|`application/json`|Возвращает один объект TradePublic|
|404|`application/json`|Не найдены одна или обе валюты|
|422|`application/json`|Ошибка валидации данных|

Примеры ответа:
```json
200 Successful Response
{
  "amount": 35.4,
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "rate": 1.1601
}
```
```json
422 Validation Error
{
  "detail": [
    {
      "loc": [
        "string",
        0
      ],
      "msg": "string",
      "type": "string",
      "input": "string",
      "ctx": {}
    }
  ]
}
```
```json
404 Not Found
{
  "detail": "Not Found"
}
```

### 3. Подтвердить/отклонить сделку
Второй этап обмена валют. Изменение статуса сделки.
```http
PATCH /trades/
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "approved"
}
```
Принимает данные в формате `application/json` .

- id - (обязательное) - id сделки
- status - (обязательное) - статус сделки ("approved" или "rejected")

Ответы:

|Код|Тип|Описание|
|---|---|---|
|200|`application/json`|Возвращает один объект TradeUpdate|
|404|`application/json`|Не найдена сделка|
|409|`application/json`|Невозможно обновить статус сделки, у которой уже есть статус|
|422|`application/json`|Ошибка валидации данных|

Примеры ответа:
```json
200 Successful Response
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "approved"
}
```
```json
422 Validation Error
{
  "detail": [
    {
      "loc": [
        "string",
        0
      ],
      "msg": "string",
      "type": "string",
      "input": "string",
      "ctx": {}
    }
  ]
}
```
```json
404 Not Found
{
  "detail": "Not Found"
}
```
```json
409 Conflict
{
  "detail": "Cannot change status of trade because it is already set (approved)"
}
```

### 4. Информация о подвержденных сделках за интервал времени
```http
GET /trades/
```
Принимает параметры

- date_from - (обязательное) - дата с
- date_to - (обязательное) - дата по
- cur_id - id валюты

Ответы:

|Код|Тип|Описание|
|---|---|---|
|200|`application/json`|Возвращает один список объектов класса Report|
|422|`application/json`|Ошибка валидации данных|

Примеры ответа:
```json
200 Successful Response
[
  {
    "cur_id": 1,
    "sum_added": "1000.23",
    "sum_removed": "31.85",
    "count": 2
  }
]
```
```json
422 Validation Error
{
  "detail": [
    {
      "loc": [
        "string",
        0
      ],
      "msg": "string",
      "type": "string",
      "input": "string",
      "ctx": {}
    }
  ]
}
```

### 5. Получить список незавершенных сделок
```http
GET /trades/uncomplete/
```

Ответы:

|Код|Тип|Описание|
|---|---|---|
|200|`application/json`|Возвращает список объектов класса Trade|

Примеры ответа:
```json
200 Successful Response
[
  {
    "id": "01a0876e-d9ab-7776-bf6f-47445053edaf",
    "amount": 0.07,
    "rate": 0.0074,
    "from_cur": {
      "abbreviation": "DZD",
      "id": 465,
      "rate": 2.293,
      "full_name": "100 Алжирских динаров"
    },
    "to_cur": {
      "abbreviation": "USD",
      "id": 431,
      "rate": 3.072,
      "full_name": "1 Доллар США"
    }
  }
]
```

### Классы обектов ответов
#### CurrencyPublic
- id - id валюты
- abbreviation - буквенный код
- rate - курс
- full_name - количество единиц и наименование валюты
#### TradePublic
- id - id сделки
- amount - сумма в целевой валюте
- rate - курс
#### TradeUpdate
- id - id сделки
- status - статус сделки ("approved" или "rejected")
#### Report
- cur_id - id валюты
- sum_added - сумма полученная в кассу
- sum_removed - сумма ушедшая из кассы
- count - количество сделок
#### Trade
- id - id сделки
- amount - сумма в целевой валюте
- rate - курс
- from_cur - **CurrencyPublic**
- to_cur - **CurrencyPublic**
