# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директории для данных
RUN mkdir -p instance/uploads

# Создаем пользователя для запуска приложения
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Переключаемся на пользователя
USER appuser

# Открываем порт
EXPOSE 5000

# Команда запуска
CMD ["sh", "-c", "python3 create_users.py && gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app"]
