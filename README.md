# PocketBase Python SDK

Простой и легкий SDK для взаимодействия с PocketBase API из приложений на Python. SDK обеспечивает удобный доступ ко всем основным функциям PocketBase и упрощает интеграцию в ваши Python-проекты.

## Краткое описание

PocketBase Python SDK позволяет легко взаимодействовать с вашей PocketBase базой данных из Python-кода. SDK предоставляет интуитивно понятный интерфейс для выполнения CRUD-операций, управления аутентификацией и работы с коллекциями.

**Возможности:**
- Авторизация пользователей и администраторов
- Управление коллекциями и записями (CRUD)
- Фильтрация, сортировка и пагинация данных
- Обработка ошибок API
- Работа с файлами и вложениями
- Поддержка расширенных запросов (expand)

## Установка

Просто скопируйте файл `pocketbase_sdk.py` в свой проект и импортируйте его:

```python
from pocketbase_sdk import PocketBase
```

## Примеры использования

### Инициализация клиента

```python
from pocketbase_sdk import PocketBase

# Создание экземпляра клиента с указанием URL вашего PocketBase сервера
pb = PocketBase("http://127.0.0.1:8090")
```

### Авторизация

#### Авторизация пользователя

```python
# Авторизация с email/username и паролем
auth_data = pb.auth.authenticate_with_password(
    "user@example.com",  # Email или username пользователя
    "your_password"      # Пароль пользователя
)

# Получение информации о текущем пользователе
current_user = pb.auth.get_model()
print(f"Авторизован как: {current_user.get('email')}")

# Проверка статуса авторизации
if pb.auth.is_valid:
    print("Пользователь авторизован")
else:
    print("Пользователь не авторизован")

# Выход из системы
pb.auth.clear()
```

#### Авторизация администратора

```python
# Авторизация администратора
admin_auth = pb.admins.authenticate_with_password(
    "admin@example.com",  # Email администратора
    "admin_password"      # Пароль администратора
)
```

### CRUD операции

#### Создание записи (Create)

```python
# Создание новой записи в коллекции "tasks"
new_task = {
    "title": "Новая задача",
    "description": "Описание задачи",
    "is_completed": False,
    "due_date": "2023-12-31 12:00:00"
}

record = pb.collection("tasks").create(new_task)
print(f"Запись создана! ID: {record['id']}")
```

#### Получение списка записей (List)

```python
# Получение списка записей с пагинацией
result = pb.collection("tasks").get_list(
    page=1,           # Номер страницы (по умолчанию: 1)
    per_page=20,      # Записей на странице (по умолчанию: 30)
    filter_str="is_completed = false",  # Фильтр (опционально)
    sort="-created"   # Сортировка (опционально)
)

# Информация о пагинации
print(f"Всего записей: {result['totalItems']}")
print(f"Всего страниц: {result['totalPages']}")

# Получение самих записей
items = result['items']
for item in items:
    print(f"ID: {item['id']}, Заголовок: {item['title']}")
```

#### Получение всех записей (без пагинации)

```python
# Получение полного списка записей
all_records = pb.collection("tasks").get_full_list(
    filter_str="is_completed = true",  # Опциональный фильтр
    sort="-created"                    # Опциональная сортировка
)

print(f"Всего записей: {len(all_records)}")
```

#### Получение одной записи (View)

```python
# Получение одной записи по ID
record_id = "RECORD_ID"  # ID записи
record = pb.collection("tasks").get_one(record_id)

print(f"Заголовок: {record['title']}")
print(f"Описание: {record['description']}")
```

#### Обновление записи (Update)

```python
# Обновление существующей записи
record_id = "RECORD_ID"  # ID записи для обновления

update_data = {
    "title": "Обновленный заголовок",
    "is_completed": True
}

updated_record = pb.collection("tasks").update(record_id, update_data)
print(f"Запись {updated_record['id']} успешно обновлена!")
```

#### Удаление записи (Delete)

```python
# Удаление записи
record_id = "RECORD_ID"  # ID записи для удаления

pb.collection("tasks").delete(record_id)
print(f"Запись {record_id} успешно удалена!")
```

### Фильтрация и сортировка

```python
# Примеры фильтрации
tasks = pb.collection("tasks").get_full_list(
    filter_str="created >= '2023-01-01' && is_completed = false"
)

# Сортировка записей
sorted_tasks = pb.collection("tasks").get_full_list(
    sort="-created,title"  # Сначала по дате создания (убывание), затем по заголовку
)

# Поиск по тексту
search_results = pb.collection("tasks").get_full_list(
    filter_str="title ~ 'проект' || description ~ 'проект'"
)

# Использование расширений (expand)
posts_with_authors = pb.collection("posts").get_full_list(
    expand="author,comments.user"
)
```

### Работа со связанными данными

```python
# Получение связанных записей через связи отношений
post = pb.collection("posts").get_one(
    "POST_ID",
    expand="author,comments,comments.user"  # Расширить автора и комментарии с их пользователями
)

# Доступ к расширенным данным
author = post.get("expand", {}).get("author")
comments = post.get("expand", {}).get("comments", [])

if author:
    print(f"Автор: {author.get('name')}")

for comment in comments:
    user = comment.get("expand", {}).get("user")
    if user:
        print(f"Комментарий от {user.get('name')}: {comment.get('text')}")
```

### Обработка ошибок

```python
from pocketbase_sdk import PocketBaseException

try:
    # Попытка получить несуществующую запись
    record = pb.collection("tasks").get_one("НЕСУЩЕСТВУЮЩИЙ_ID")
except PocketBaseException as e:
    print(f"Ошибка: {e.message}")
    print(f"Код ошибки: {e.status_code}")
```

### Сброс пароля

```python
# Отправка письма для сброса пароля
pb.send_reset_password_email("user@example.com")

# Подтверждение сброса пароля с токеном
pb.confirm_password_reset(
    "RESET_TOKEN",
    "new_password",
    "new_password"  # Подтверждение пароля
)
```

### Проверка здоровья API

```python
# Проверка состояния сервера
health_info = pb.health()
print(f"Сервер работает: {health_info.get('code') == 200}")
```

## Дополнительные возможности

### Обновление токена аутентификации

```python
# Обновление токена без повторного ввода пароля
refreshed_auth = pb.auth.refresh_token()
```

### Верификация email пользователя

```python
# Подтверждение верификации email
pb.confirm_verification("VERIFICATION_TOKEN")
```

## Лицензия

MIT
