import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Базовая конфигурация приложения"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.getenv('DATABASE_PATH', 'instance/database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Configuration
    DATANEWTON_API_KEY = os.getenv('DATANEWTON_API_KEY', 'mi76aFMdgvml')
    DADATA_API_KEY = os.getenv('DADATA_API_KEY', '')
    
    # Upload/Download
    UPLOAD_FOLDER = 'instance/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Session
    PERMANENT_SESSION_LIFETIME = 3600  # 1 час


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    TESTING = False


# Выбор конфигурации в зависимости от окружения
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

