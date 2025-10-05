#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем деплой приложения...${NC}"



# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден. Создайте .env файл с необходимыми переменными окружения.${NC}"
    exit 1
fi

source .env

required_vars=("SECRET_KEY" "1USERLOGIN" "1USERPASSWORD" "2USERLOGIN" "2USERPASSWORD")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Переменная $var не установлена в .env файле.${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Все обязательные переменные окружения установлены.${NC}"

# Останавливаем существующие контейнеры
echo -e "${YELLOW}🛑 Останавливаем существующие контейнеры...${NC}"
docker-compose down

# Собираем образ
echo -e "${YELLOW}🔨 Собираем Docker образ...${NC}"
docker-compose build --no-cache

# Создаем необходимые директории
echo -e "${YELLOW}📁 Создаем необходимые директории...${NC}"
mkdir -p instance/uploads
mkdir -p templates

# Запускаем контейнеры
echo -e "${YELLOW}🚀 Запускаем контейнеры...${NC}"
docker-compose up -d

# Ждем запуска приложения
echo -e "${YELLOW}⏳ Ждем запуска приложения...${NC}"
sleep 10

# Проверяем статус контейнеров
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Приложение успешно запущено!${NC}"
    echo -e "${GREEN}🌐 Приложение доступно по адресу: http://localhost:5000${NC}"
    echo -e "${GREEN}👤 Пользователи:${NC}"
    echo -e "   - Логин: $1USERLOGIN, Пароль: $1USERPASSWORD"
    echo -e "   - Логин: $2USERLOGIN, Пароль: $2USERPASSWORD"
    
    # Показываем логи
    echo -e "${YELLOW}📋 Логи приложения:${NC}"
    docker-compose logs --tail=20
else
    echo -e "${RED}❌ Ошибка при запуске приложения. Проверьте логи:${NC}"
    docker-compose logs
    exit 1
fi

echo -e "${GREEN}🎉 Деплой завершен успешно!${NC}"
