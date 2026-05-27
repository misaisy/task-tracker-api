# Task Tracker API — Спецификация

Базовый URL: `http://127.0.0.1:8000`

## Оглавление

- [Задачи](#tasks)
  - [GET /tasks](#get-tasks) — список задач
  - [GET /tasks/{task_id}](#get-taskstask_id) — одна задача
  - [POST /tasks](#post-tasks) — создать задачу
  - [PATCH /tasks/{task_id}](#patch-taskstask_id) — обновить задачу
  - [POST /tasks/{task_id}/assign](#post-taskstask_idassign) — назначить исполнителя
- [Комментарии](#comments)
  - [GET /tasks/{task_id}/comments](#get-taskstask_idcomments) — комментарии задачи
  - [POST /tasks/{task_id}/comments](#post-taskstask_idcomments) — добавить комментарий
- [Действия](#actions)
  - [POST /tasks/{task_id}/archive](#post-taskstask_idarchive) — архивировать задачу
- [Отчёты](#reports)
  - [GET /tasks/summary](#get-taskssummary) — сводка по задачам
  - [GET /tasks/export](#get-tasksexport) — выгрузка задач
- [Общая информация](#general)
  - [Query-параметры](#query-params)
  - [Status-коды](#status-codes)
  - [Формат ошибок](#error-format)

---

## <a id="tasks"></a>Задачи

### <a id="get-tasks"></a>GET /tasks

Возвращает список всех задач с возможностью фильтрации и пагинации.

**Query-параметры:**

| Параметр    | Тип       | По умолчанию | Описание                                                               |
|-------------|-----------|--------------|------------------------------------------------------------------------|
| `status`    | `string`  | —            | Фильтр по статусу: `todo`, `in_progress`, `review`, `done`, `archived` |
| `priority`  | `string`  | —            | Фильтр по приоритету: `low`, `medium`, `high`                          |
| `page`      | `integer` | `1`          | Номер страницы (начиная с 1)                                           |
| `page_size` | `integer` | `20`         | Количество задач на странице (максимум 100)                            |

**Ответ `200 OK`:**

```json
{
  "items": [
    {
      "id": 1,
      "title": "Реализовать healthcheck",
      "description": "Добавить эндпоинт GET /health",
      "priority": "high",
      "status": "done",
      "created_at": "2026-05-27T12:00:00Z"
    },
    {
      "id": 2,
      "title": "Добавить создание задач",
      "description": null,
      "priority": "medium",
      "status": "todo",
      "created_at": "2026-05-27T13:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

**Примеры запросов:**

```bash
# Все задачи
curl http://127.0.0.1:8000/tasks

# Только задачи со статусом todo
curl "http://127.0.0.1:8000/tasks?status=todo"

# Задачи с высоким приоритетом, страница 2
curl "http://127.0.0.1:8000/tasks?priority=high&page=2&page_size=10"
```

### <a id="get-taskstask_id"></a>GET /tasks/task_id

Возвращает одну задачу по её ID.

**Path-параметры:**

|Параметр  |	Тип	 | Описание |
|----------|---------|----------|
|task_id   |integer	 |ID задачи |

**Ответ 200 OK:**
```json
{
  "id": 1,
  "title": "Реализовать healthcheck",
  "description": "Добавить эндпоинт GET /health",
  "priority": "high",
  "status": "done",
  "created_at": "2026-05-27T12:00:00Z"
}
```

**Ответ 404 Not Found:**
```json
{
  "detail": "Task with id=999 not found"
}
```

**Пример запроса:**
```bash
curl http://127.0.0.1:8000/tasks/1
```

### <a id="post-tasks"></a>POST /tasks

Создаёт новую задачу.

**Тело запроса:**
```json
{
  "title": "Новая задача",
  "description": "Подробное описание задачи",
  "priority": "high"
}
```
|Поле	     | Тип	           | Обязательное | По умолчанию | Ограничения       |
|------------|-----------------|--------------|--------------|-------------------|
|title       | string	       | Да	          | —	         | 1-200 символов    |
|description | string или null | Нет	      | null	     | До 1000 символов  |
|priority	 | string	       | Нет	      | "medium"	 | low, medium, high |

*Ответ 201 Created:*
```json
{
  "id": 3,
  "title": "Новая задача",
  "description": "Подробное описание задачи",
  "priority": "high",
  "status": "TODO",
  "created_at": "2026-05-27T14:00:00Z"
}
```

**Ответ 422 Unprocessable Entity (пустой title):**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

**Примеры запросов:**
```bash
# Создать задачу (все поля)
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Новая задача", "description": "Описание", "priority": "high"}'

# Создать задачу (только обязательное поле)
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Простая задача"}'
```

### <a id="patch-taskstask_id"></a>PATCH /tasks/task_id

Частично обновляет существующую задачу.

**Path-параметры:**

| Параметр	   | Тип	 | Описание  |
|--------------|---------|-----------|
| task_id	   | integer | ID задачи |

**Тело запроса (все поля опциональны):**
```json
{
  "title": "Обновлённое название",
  "description": "Новое описание",
  "priority": "low",
  "status": "in_progress"
}
```

**Правила PATCH:**

|Ситуация	                     | Поведение                                                                   |
|--------------------------------|-----------------------------------------------------------------------------|
|Поле не передано	             | Значение не меняется                                                        |
|Поле передано с null	         | Для description — сбрасывается в null. Для title — ошибка (title обязателен)|
|Поле передано с новым значением | Значение обновляется                                                        |
|Поле id	                     | Менять нельзя — игнорируется или возвращается ошибка                        |
|Поле created_at                 | Менять нельзя — игнорируется или возвращается ошибка                        |

**Ответ 200 OK:**
```json
{
  "id": 1,
  "title": "Обновлённое название",
  "description": "Новое описание",
  "priority": "low",
  "status": "in_progress",
  "created_at": "2026-05-27T12:00:00Z"
}
```

**Ответ 404 Not Found:**
```json
{
  "detail": "Task with id=999 not found"
}
```

**Ответ 409 Conflict (попытка изменить архивную задачу):**
```json
{
  "detail": "Cannot modify archived task"
}
```

**Примеры запросов:**
```bash
# Обновить название и приоритет
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Новое название", "priority": "low"}'

# Сбросить описание
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"description": null}'
```

### <a id="post-taskstask_idassign"></a>POST /tasks/task_id/assign

Назначает исполнителя задаче.

**Path-параметры:**

|Параметр | Тип	    | Описание  |
|---------|---------|-----------|
|task_id  |	integer | ID задачи |

**Тело запроса:**
```json
{
  "user_id": 7
}
```

|Поле	 | Тип	   | Обязательное | Описание                    |
|--------|---------|--------------|-----------------------------|
|user_id | integer | Да           | ID пользователя-исполнителя |

**Ответ 200 OK:**
```json
{
  "id": 1,
  "title": "Новая задача",
  "description": null,
  "priority": "high",
  "status": "in_progress",
  "assignee_id": 7,
  "created_at": "2026-05-27T12:00:00Z"
}
```

**Возможные ошибки:**

|Код  |	Когда                        |
|-----|------------------------------|
|404  | Задача не найдена            |
|404  | Пользователь не найден       |
|409  | Задача уже назначена другому |
|409  | Задача архивирована          |

**Пример запроса:**
```bash
curl -X POST http://127.0.0.1:8000/tasks/1/assign \
  -H "Content-Type: application/json" \
  -d '{"user_id": 7}'
```

## <a id="comments"></a>Комментарии

### <a id="get-taskstask_idcomments"></a>GET /tasks/task_id/comments

Возвращает список комментариев к задаче.

**Path-параметры:**

| Параметр | Тип	 | Описание  |
|----------|---------|-----------|
| task_id  | integer | ID задачи |

**Ответ 200 OK:**
```json
{
  "items": [
    {
      "id": 1,
      "task_id": 1,
      "text": "Нужно добавить валидацию",
      "created_at": "2026-05-27T15:00:00Z"
    }
  ],
  "total": 1
}
```

**Ответ 404 Not Found:**
```json
{
  "detail": "Task with id=999 not found"
}
```

**Пример запроса:**
```bash
curl http://127.0.0.1:8000/tasks/1/comments
```

### <a id="post-taskstask_idcomments"></a>POST /tasks/task_id/comments

Добавляет комментарий к задаче.

**Path-параметры:**

|Параметр | Тип	    | Описание  |
|---------|---------|-----------|
|task_id  | integer	| ID задачи |

**Тело запроса:**
```json
{
  "text": "Отличная работа!"
}
```

|Поле | Тип	   | Обязательное| Ограничения    |
|-----|--------|-------------|----------------|
|text | string | Да	         | 1-1000 символов|

**Ответ 201 Created:**
```json
{
  "id": 2,
  "task_id": 1,
  "text": "Отличная работа!",
  "created_at": "2026-05-27T16:00:00Z"
}
```

**Ответ 404 Not Found:**
```json
{
  "detail": "Task with id=999 not found"
}
```

**Пример запроса:**
```bash
curl -X POST http://127.0.0.1:8000/tasks/1/comments \
  -H "Content-Type: application/json" \
  -d '{"text": "Отличная работа!"}'
```

## <a id="actions"></a>Действия

### <a id="post-taskstask_idarchive"></a>POST /tasks/task_id/archive

Архивирует задачу. Архивированную задачу нельзя редактировать или назначать.

**Path-параметры:**

|Параметр | Тип     | Описание  |
|---------|---------|-----------|
|task_id  | integer | ID задачи |

**Ответ 200 OK:**
```json
{
  "id": 1,
  "title": "Новая задача",
  "priority": "high",
  "status": "archived",
  "created_at": "2026-05-27T12:00:00Z"
}
```

**Возможные ошибки:**

| Код | Когда                   |
|-----|-------------------------|
| 404 |	Задача не найдена       |
| 409 | Задача уже архивирована |

**Пример запроса:**
```bash
curl -X POST http://127.0.0.1:8000/tasks/1/archive
```

##<a id="reports"></a>Отчёты

###<a id="get-taskssummary"></a>GET /tasks/summary

Возвращает сводку по задачам — количество задач в каждом статусе.

**Ответ 200 OK:**
```json
{
  "total": 10,
  "by_status": {
    "todo": 4,
    "in_progress": 3,
    "review": 1,
    "done": 2,
    "archived": 0
  },
  "by_priority": {
    "low": 2,
    "medium": 5,
    "high": 3
  }
}
```

**Пример запроса:**
```bash
curl http://127.0.0.1:8000/tasks/summary
```

### <a id="get-tasksexport"></a>GET /tasks/export

Выгружает все задачи в формате, удобном для экспорта.

**Query-параметры:**

|Параметр | Тип	   | По умолчанию | Описание                      |
|---------|--------|--------------|-------------------------------|
|format	  | string | json	      | Формат выгрузки: json или csv |

**Ответ 200 OK (format=json):**
```json
{
  "exported_at": "2026-05-27T17:00:00Z",
  "format": "json",
  "tasks": [
    {
      "id": 1,
      "title": "Задача 1",
      "status": "todo",
      "priority": "high",
      "created_at": "2026-05-27T12:00:00Z"
    }
  ]
}
```

**Ответ 200 OK (format=csv):**
```csv
id,title,status,priority,created_at
1,Задача 1,todo,high,2026-05-27T12:00:00Z
2,Задача 2,done,medium,2026-05-27T13:00:00Z
```

**Примеры запросов:**
```bash
# JSON
curl "http://127.0.0.1:8000/tasks/export?format=json"

# CSV
curl "http://127.0.0.1:8000/tasks/export?format=csv"
```

## <a id="general"></a>Общая информация

### <a id="query-params"></a>Query-параметры

Query-параметры используются для фильтрации, сортировки и пагинации в GET-запросах.

**Общие правила:**

* Все query-параметры опциональны (если не указано иное)

* Параметры с несколькими значениями передаются через запятую: ?status=todo,in_progress

* Параметры пагинации: page (начиная с 1) и page_size (максимум 100)

### <a id="status-codes"></a>Status-коды

| Код | Название	          | Когда используется                                     |
|-----|-----------------------|--------------------------------------------------------|
| 200 | OK	                  | Успешный GET, PUT, PATCH                               |
| 201 | Created	              | Успешный POST (создание ресурса)                       |
| 204 | No Content	          | Успешный DELETE                                        |
| 400 | Bad Request	          | Синтаксическая ошибка в запросе                        |
| 404 | Not Found	          | Ресурс не найден                                       |
| 409 | Conflict	          | Конфликт состояния (архивирование архивного, дубликат) |
| 422 | Unprocessable Entity  | Ошибка валидации полей                                 |
| 500 | Internal Server Error | Неожиданная ошибка сервера                             |

### <a id="error-format"></a>Формат ошибок

Все ошибки возвращаются в едином формате:

**Ошибка валидации (422):**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

**Ошибка "не найдено" (404):**
```json
{
  "detail": "Task with id=999 not found"
}
```

**Ошибка конфликта (409):**
```json
{
  "detail": "Cannot modify archived task"
}
```

**Ошибка сервера (500):**
```json
{
  "detail": "Internal server error"
}
```