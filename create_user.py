"""
Скрипт для создания пользователя
"""
from app.models import User, init_db

if __name__ == '__main__':
    # Инициализация БД
    init_db()
    
    print("=== Создание пользователя ===\n")
    
    username = input("Введите логин: ").strip()
    if not username:
        print("Ошибка: логин не может быть пустым")
        exit(1)
    
    password = input("Введите пароль: ").strip()
    if not password:
        print("Ошибка: пароль не может быть пустым")
        exit(1)
    
    # Создание пользователя
    if User.create(username, password):
        print(f"\n✅ Пользователь '{username}' успешно создан!")
    else:
        print(f"\n❌ Ошибка: пользователь '{username}' уже существует")

