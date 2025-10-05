## управление пользователями

### Сброс админа

**Выполнять в консоли сервера через Docker:**

```bash
docker exec -it <container_name> python reset_admin.py <new_username> <new_password>
```

**пример:**
```bash
docker exec -it kworkdoc_app_1 python reset_admin.py admin NewPassword123
```

**Инструкция:**
1. Подключитесь к VPS по SSH
2. Найдите имя контейнера: `docker ps`
3. Выполните команду сброса админа
4. Войдите в систему с новыми данными

**Альтернативный способ (через bash):**
```bash
docker exec -it <container_name> bash
python reset_admin.py admin NewPassword123
exit
```

## Перезапуск сервиса

### Если сервис перестал работать

**1. Проверить статус контейнеров:**
```bash
docker ps -a
```

**2. Перезапустить контейнер:**
```bash
docker restart <container_name>
```

**3. Если не помогает - пересоздать контейнер:**
```bash
docker-compose down
docker-compose up -d
```

```

## API сервисы

### Основной сервис: DataNewton
- Используется по умолчанию для поиска компаний по ИНН
- API ключ: `DATANEWTON_API_KEY` в переменных окружения

### Резервный сервис: API-FNS
- Используется только при явном подтверждении пользователя
- Ограничение: 100 запросов
- API ключ: `API_FNS_API_KEY` в переменных окружения
- Активируется только если основной сервис не нашел данные

### Логика работы:
1. Сначала поиск в DataNewton
2. Если не найдено - предлагается резервный API-FNS
3. Пользователь подтверждает использование резервного сервиса
4. При отказе - используется mock данные или показывается ошибка

## Тестовые данные

Для тестирования доступны следующие ИНН:
- `9728006808` - Тестовая компания (DataNewton API)
- `1234567890` - ИП Петров П.П. (Mock данные)

## структура Flask

```
kworkdoc/
├── app/
│   ├── __init__.py          # Инициализация Flask
│   ├── auth.py              # Аутентификация
│   ├── routes.py            # Роуты
│   ├── models.py            # Модели БД
│   ├── inn_service.py       # API сервис
│   ├── document_generator.py # Генерация DOCX
│   └── templates/           # HTML шаблоны
├── templates/               # DOCX шаблоны договоров
├── instance/                # БД
├── config.py                # Конфигурация
├── requirements.txt         # Зависимости
└── run.py                   # Точка входа
```