#!/bin/bash

echo "Запуск деплоя..."

if [ ! -f .env ]; then
    echo "Ошибка: файл .env не найден"
    exit 1
fi

source .env

required_vars=("SECRET_KEY" "USER1_LOGIN" "USER1_PASSWORD" "USER2_LOGIN" "USER2_PASSWORD")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Ошибка: переменная $var не установлена"
        exit 1
    fi
done

echo "Остановка контейнеров..."
docker-compose down

echo "Сборка образа..."
docker-compose build --no-cache

mkdir -p instance/uploads templates

echo "Запуск контейнеров..."
docker-compose up -d

sleep 10

if docker-compose ps | grep -q "Up"; then
    echo "Приложение запущено: http://localhost:5000"
    echo "Пользователи:"
    echo "  - $USER1_LOGIN / $USER1_PASSWORD"
    echo "  - $USER2_LOGIN / $USER2_PASSWORD"
    docker-compose logs --tail=10
else
    echo "Ошибка запуска"
    docker-compose logs
    exit 1
fi

echo "Деплой завершен"
