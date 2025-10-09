import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login_manager


class User(UserMixin):
    """Модель пользователя"""
    
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    @staticmethod
    def get(user_id):
        """Получить пользователя по ID"""
        conn = get_db_connection()
        user_data = conn.execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        conn.close()
        
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['password_hash'])
        return None
    
    @staticmethod
    def get_by_username(username):
        """Получить пользователя по username"""
        conn = get_db_connection()
        user_data = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['password_hash'])
        return None
    
    def check_password(self, password):
        """Проверить пароль"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def create(username, password):
        """Создать нового пользователя"""
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        
        try:
            conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    @staticmethod
    def reset_password(username, new_password):
        """Сбросить пароль пользователя"""
        password_hash = generate_password_hash(new_password)
        conn = get_db_connection()
        
        try:
            cursor = conn.execute(
                'UPDATE users SET password_hash = ? WHERE username = ?',
                (password_hash, username)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
        finally:
            conn.close()


@login_manager.user_loader
def load_user(user_id):
    """Загрузчик пользователя для Flask-Login"""
    return User.get(int(user_id))


def get_db_connection():
    """Получить соединение с БД"""
    conn = sqlite3.connect('instance/database.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    
    # Создание таблицы пользователей
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contract_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            inn TEXT NOT NULL,
            company_name TEXT,
            filename TEXT NOT NULL,
            contract_number TEXT,
            contract_date TEXT,
            services TEXT,
            city TEXT,
            hourly_rate TEXT,
            min_hours TEXT,
            executor_profile_id INTEGER,
            executor_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (executor_profile_id) REFERENCES executor_profiles (id)
        )
    ''')
    
    # Добавляем колонки для исполнителя если их нет (миграция для существующих БД)
    try:
        conn.execute('ALTER TABLE contract_history ADD COLUMN executor_profile_id INTEGER')
    except:
        pass  # Колонка уже существует
    
    try:
        conn.execute('ALTER TABLE contract_history ADD COLUMN executor_name TEXT')
    except:
        pass  # Колонка уже существует
    
    try:
        conn.execute('ALTER TABLE contract_history ADD COLUMN pricing_services_json TEXT')
    except:
        pass
    
    try:
        conn.execute('ALTER TABLE contract_history ADD COLUMN packing_percentage TEXT')
    except:
        pass
    
    try:
        conn.execute('ALTER TABLE contract_history ADD COLUMN prepayment_amount TEXT')
    except:
        pass
    
    try:
        conn.execute('ALTER TABLE contract_history ADD COLUMN bank_details TEXT')
    except:
        pass
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS executor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name TEXT NOT NULL,
            org_type TEXT NOT NULL,
            full_name TEXT NOT NULL,
            short_name TEXT,
            legal_address TEXT,
            postal_address TEXT,
            inn TEXT NOT NULL,
            ogrn TEXT,
            bank_account TEXT,
            bank_name TEXT,
            bik TEXT,
            corr_account TEXT,
            email TEXT,
            phone TEXT,
            director TEXT,
            director_position TEXT,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Добавляем колонки для директора исполнителя если их нет (миграция)
    try:
        conn.execute('ALTER TABLE executor_profiles ADD COLUMN director TEXT')
    except:
        pass  # Колонка уже существует
    
    try:
        conn.execute('ALTER TABLE executor_profiles ADD COLUMN director_position TEXT')
    except:
        pass  # Колонка уже существует
    
    existing = conn.execute('SELECT COUNT(*) FROM executor_profiles').fetchone()[0]
    if existing == 0:
        conn.execute('''
            INSERT INTO executor_profiles (
                profile_name, org_type, full_name, short_name,
                legal_address, postal_address, inn, ogrn,
                bank_account, bank_name, bik, corr_account,
                email, phone, director, director_position, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'ИП Лукманов',
            'ИП',
            'Индивидуальный предприниматель Лукманов Марат Ильгизович',
            'ИП Лукманов М.И.',
            '420032, Республика Татарстан, г. Казань, ул. Краснококшайская, д. 60, кв. 420',
            '420032, Республика Татарстан, г. Казань, ул. Краснококшайская, д. 60, кв. 420',
            '164509365669',
            '313168915600018',
            '40802810700490014077',
            'Филиал "Центральный" Банка ВТБ (ПАО)',
            '044525411',
            '30101810145250000411',
            'info@standart-express.ru',
            '8 (800) 700-51-53',
            '',  # director - не нужен для ИП
            '',  # director_position - не нужен для ИП
            1
        ))
    
    conn.commit()
    
    # Создаем пользователей из переменных окружения
    create_default_users(conn)
    
    conn.close()
    
    print("база данных инициализирована")


def create_default_users(conn):
    """Создание пользователей по умолчанию из переменных окружения (только если их нет)"""
    users_data = [
        {
            'login': os.getenv('USER1_LOGIN'),
            'password': os.getenv('USER1_PASSWORD')
        },
        {
            'login': os.getenv('USER2_LOGIN'),
            'password': os.getenv('USER2_PASSWORD')
        }
    ]
    
    for user_data in users_data:
        if not user_data['login'] or not user_data['password']:
            continue
        
        existing = conn.execute(
            'SELECT id FROM users WHERE username = ?', (user_data['login'],)
        ).fetchone()
        
        if not existing:
            # Создаем пользователя только если его нет
            try:
                password_hash = generate_password_hash(user_data['password'])
                conn.execute(
                    'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (user_data['login'], password_hash)
                )
                print(f"Пользователь '{user_data['login']}' создан")
            except sqlite3.IntegrityError:
                print(f"Пользователь '{user_data['login']}' уже существует")
        # Если пользователь существует - НЕ обновляем пароль!
    
    conn.commit()


def get_executor_profile(profile_id=None):
    """Получить профиль исполнителя (дефолтный или по ID)"""
    conn = get_db_connection()
    
    if profile_id:
        profile = conn.execute(
            'SELECT * FROM executor_profiles WHERE id = ?', (profile_id,)
        ).fetchone()
    else:
        profile = conn.execute(
            'SELECT * FROM executor_profiles WHERE is_default = 1'
        ).fetchone()
    
    conn.close()
    return dict(profile) if profile else None


def get_all_executor_profiles():
    """Получить все профили исполнителя"""
    conn = get_db_connection()
    profiles = conn.execute(
        'SELECT * FROM executor_profiles ORDER BY is_default DESC, created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(p) for p in profiles]


def save_executor_profile(data, profile_id=None):
    """Сохранить или обновить профиль исполнителя"""
    conn = get_db_connection()
    
    if profile_id:
        # Обновление существующего
        conn.execute('''
            UPDATE executor_profiles SET
                profile_name = ?, org_type = ?, full_name = ?, short_name = ?,
                legal_address = ?, postal_address = ?, inn = ?, ogrn = ?,
                bank_account = ?, bank_name = ?, bik = ?, corr_account = ?,
                email = ?, phone = ?, director = ?, director_position = ?
            WHERE id = ?
        ''', (
            data['profile_name'], data['org_type'], data['full_name'], data['short_name'],
            data['legal_address'], data['postal_address'], data['inn'], data['ogrn'],
            data['bank_account'], data['bank_name'], data['bik'], data['corr_account'],
            data['email'], data['phone'], data.get('director', ''), data.get('director_position', ''), profile_id
        ))
    else:
        # Создание нового
        conn.execute('''
            INSERT INTO executor_profiles (
                profile_name, org_type, full_name, short_name,
                legal_address, postal_address, inn, ogrn,
                bank_account, bank_name, bik, corr_account,
                email, phone, director, director_position, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            data['profile_name'], data['org_type'], data['full_name'], data['short_name'],
            data['legal_address'], data['postal_address'], data['inn'], data['ogrn'],
            data['bank_account'], data['bank_name'], data['bik'], data['corr_account'],
            data['email'], data['phone'], data.get('director', ''), data.get('director_position', '')
        ))
    
    conn.commit()
    conn.close()


def set_default_profile(profile_id):
    """Установить профиль как дефолтный"""
    conn = get_db_connection()
    conn.execute('UPDATE executor_profiles SET is_default = 0')
    conn.execute('UPDATE executor_profiles SET is_default = 1 WHERE id = ?', (profile_id,))
    conn.commit()
    conn.close()

