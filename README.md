## РГЗ (вариант 12): RESTful API на Flask для управления инвентарём склада

Реализовано REST API для управления товарами (инвентарь) с хранением данных в **PostgreSQL**, а также генерация сводного отчёта по инвентарю. Добавлены **unit‑тесты** и **CI workflow GitHub Actions** (pytest + bandit).

### 1) Требования

- **Python**: 3.11+  
- **Docker** (рекомендуется): для запуска PostgreSQL локально

### 2) Быстрый старт (локально)

#### 2.1. Поднять PostgreSQL через Docker

В корне проекта:

```powershell
docker compose up -d
```

Параметры БД уже совпадают с `env.example`.

Если Docker Desktop не запущен, `docker compose` может ругаться на отсутствие Docker Engine — просто запусти Docker Desktop и повтори команду.

Если встретишь ошибку `project name must not be empty`, используй явное имя проекта:

```powershell
docker compose -p rgz up -d
```

#### 2.2. Установить зависимости и запустить API

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item env.example .env
python -m flask --app wsgi run --port 5000
```

Проверка:

```powershell
curl.exe http://127.0.0.1:5000/health
```

### 3) Эндпоинты

#### Товары

- **POST** `/items` — добавить товар  
- **GET** `/items` — список товаров (фильтр: `?category=...`)  
- **PUT** `/items/<id>` — обновить товар  
- **DELETE** `/items/<id>` — удалить товар  

Дополнительно (для удобства):  
- **GET** `/items/<id>` — получить товар по id

#### Отчёты

- **GET** `/reports/summary` — сводный отчёт (JSON)  
- **GET** `/reports/summary?format=csv` — сводный отчёт (CSV)

### 4) Примеры запросов (удобно для скриншотов в отчёт)

> Для PowerShell лучше использовать `curl.exe` (а не алиас `curl`).

#### 4.1. Создание товара

```powershell
curl.exe -X POST http://127.0.0.1:5000/items `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"Keyboard\",\"quantity\":10,\"price\":2500.50,\"category\":\"electronics\"}"
```

#### 4.2. Список товаров + фильтр по категории

```powershell
curl.exe http://127.0.0.1:5000/items
curl.exe "http://127.0.0.1:5000/items?category=electronics"
```

#### 4.3. Обновление товара

```powershell
curl.exe -X PUT http://127.0.0.1:5000/items/1 `
  -H "Content-Type: application/json" `
  -d "{\"quantity\":8}"
```

#### 4.4. Удаление товара

```powershell
curl.exe -X DELETE http://127.0.0.1:5000/items/1
```

#### 4.5. Сводный отчёт (JSON/CSV)

```powershell
curl.exe http://127.0.0.1:5000/reports/summary
curl.exe "http://127.0.0.1:5000/reports/summary?format=csv"
```

### 5) Тесты и security‑проверка (Bandit)

```powershell
python -m pytest -q
python -m bandit -r app -x tests
```

Чтобы прогнать тесты на PostgreSQL (например, после `docker compose up -d`), можно задать переменную:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg2://inventory:inventory@localhost:5432/inventory"
python -m pytest -q
```

### 6) GitHub Actions (что сделать тебе + что заскринить)

Я добавил workflow `.github/workflows/ci.yml`.

#### 6.1. Залить код в GitHub

```powershell
git add .
git commit -m "Variant 12: Flask inventory API + tests + CI"
git push origin main
```

#### 6.2. Где сделать скриншоты для отчёта

- **GitHub → вкладка Actions**: запуск workflow после push (статус зелёный).
- Детали job: скрин шагов `Bandit` и `Pytest`.
- (Опционально) Скрины терминала с примерами запросов из раздела 4.
