import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import User, init_db

def create_users_from_env():
    load_dotenv()
    
    print("Инициализация базы данных...")
    init_db()
    
    users_data = [
        {
            'login': os.getenv('1USERLOGIN'),
            'password': os.getenv('1USERPASSWORD')
        },
        {
            'login': os.getenv('2USERLOGIN'),
            'password': os.getenv('2USERPASSWORD')
        }
    ]
    
    for user_data in users_data:
        if not user_data['login'] or not user_data['password']:
            continue
            
        existing_user = User.get_by_username(user_data['login'])
        
        if existing_user:
            User.reset_password(user_data['login'], user_data['password'])
            print(f"Пароль для '{user_data['login']}' обновлен")
        else:
            success = User.create(user_data['login'], user_data['password'])
            if success:
                print(f"Пользователь '{user_data['login']}' создан")
            else:
                print(f"Ошибка создания '{user_data['login']}'")

if __name__ == '__main__':
    create_users_from_env()
