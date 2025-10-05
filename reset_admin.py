"""
Скрипт для сброса логина и пароля единственного пользователя-админа
Использование: python reset_admin.py <new_username> <new_password>
"""
import sys
from werkzeug.security import generate_password_hash
from app.models import get_db_connection, init_db


def reset_admin(new_username, new_password):
    """Сбросить логин и пароль единственного пользователя"""
    init_db()
    conn = get_db_connection()
    
    # Проверяем что есть пользователи
    users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if users_count == 0:
        conn.close()
        return False, "В базе нет пользователей. Сначала создайте пользователя через create_user.py"
    
    # Если пользователей больше одного - предупреждаем
    if users_count > 1:
        print(f"⚠️  В базе найдено {users_count} пользователей. Будут обновлены ВСЕ пользователи!")
        confirm = input("Продолжить? (y/N): ").strip().lower()
        if confirm != 'y':
            conn.close()
            return False, "Операция отменена"
    
    # Обновляем всех пользователей (обычно это один админ)
    password_hash = generate_password_hash(new_password)
    
    # Сначала удаляем всех пользователей
    conn.execute('DELETE FROM users')
    
    # Создаем нового админа
    conn.execute(
        'INSERT INTO users (username, password_hash) VALUES (?, ?)',
        (new_username, password_hash)
    )
    
    conn.commit()
    conn.close()
    
    return True, f"Админ успешно сброшен! Новый логин: {new_username}"


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Использование: python reset_admin.py <new_username> <new_password>")
        print("\nПример:")
        print("  python reset_admin.py admin MyNewPassword123")
        print("\nЭтот скрипт:")
        print("  - Удаляет всех существующих пользователей")
        print("  - Создает нового пользователя с указанными данными")
        sys.exit(1)
    
    new_username = sys.argv[1]
    new_password = sys.argv[2]
    
    if not new_username or not new_password:
        print("❌ Ошибка: логин и пароль не могут быть пустыми")
        sys.exit(1)
    
    if len(new_password) < 6:
        print("⚠️  Предупреждение: пароль слишком короткий (рекомендуется минимум 6 символов)")
    
    success, message = reset_admin(new_username, new_password)
    
    if success:
        print(f"✅ {message}")
        print("\nТеперь вы можете войти в систему с новыми учетными данными.")
    else:
        print(f"❌ {message}")
        sys.exit(1)
