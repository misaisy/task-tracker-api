# Task Tracker API

Сервис для управления задачами.

## Требования

- Python 3.11+
- pip
- Docker и Docker Compose (опционально, для контейнерного запуска)

## Локальный запуск

### 1. Клонируйте репозиторий
```
git clone https://github.com/misaisy/task-tracker-api.git
cd task_tracker_api
```

### 2. Создайте и активируйте виртуальное окружение
```
python -m venv venv
venv\Scripts\activate
```

### 3. Установите зависимости
```
pip install -r requirements.txt
```

### 4. Настройте переменные окружения

Скопируйте файл-образец:
```
cp .env.example .env
```

При необходимости отредактируйте `.env`:
- `APP_PORT=8000` — порт
- `DEBUG=true` — режим отладки
- `LOG_LEVEL=debug` — уровень логирования

### 5. Запустите сервер

Команда для запуска:
```
python run.py
```

### 6. Проверьте работоспособность

Откройте браузер и перейдите по адресу:
`http://127.0.0.1:8000/health`

Или выполните в терминале:
```
curl http://127.0.0.1:8000/health
```

Ожидаемый ответ:

`{"status":"ok"}`

Swagger UI доступен после запуска:
`http://127.0.0.1:8000/docs`

### Запуск тестов

```
pytest tests/ -v
```

## Запуск через Docker

### Сборка и запуск

```
docker compose up -d app
```

### Проверка

```
curl http://127.0.0.1:8000/health
```

### Тесты

```
docker compose run test
```

### Управление

```
docker compose stop                 # остановить
docker compose down                 # остановить и удалить контейнеры
docker compose build --no-cache app # пересобрать образ
docker compose logs -f app          # логи в реальном времени
```

### Миграции

Создать новую миграцию после изменения моделей:
```
docker compose run --rm app alembic revision --autogenerate -m "описание"
```

Применить миграции:
```
docker compose run --rm app alembic upgrade head
```

### Проверка

Запустить сервисы:
```
docker compose up -d
```

Убедиться что контейнер db запущен:
```
docker ps
```

Проверить, что БД доступна:
```
docker compose exec app python -c "from app.db import get_connection; conn = get_connection(); print(conn); conn.close()"
```


## Основные эндпоинты

### Задачи

GET	  /tasks                Список задач с фильтрацией, сортировкой и пагинацией
POST  /tasks	            Создать задачу
GET	  /tasks/{id}	        Получить задачу по ID
PATCH /tasks/{id}	        Частично обновить задачу
POST  /tasks/{id}/assign	Назначить исполнителя
POST  /tasks/{id}/complete  Закрыть задачу
POST  /tasks/{id}/archive	Архивировать задачу
GET	  /tasks/{id}/history	История изменений задачи
GET	  /tasks/summary	    Сводка по статусам и приоритетам
GET	  /tasks/export	        Выгрузка задач в JSON или CSV

### Пользователи

GET	  /users	   Список пользователей
POST  /users	   Создать пользователя
GET	  /users/{id}  Получить пользователя по ID

### Комментарии

GET	  /tasks/{id}/comments  Комментарии к задаче
POST  /tasks/{id}/comments	Добавить комментарий

### Полный API-контракт
docs/API.md

## Линтеры и проверка типов

```
ruff check . --fix  # линтинг и автофикс
mypy app/           # проверка типов
```