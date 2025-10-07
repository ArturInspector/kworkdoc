import os
from flask import Flask
from flask_login import LoginManager
from config import config

# Инициализация расширений
login_manager = LoginManager()


def create_app(config_name='default'):
    """Фабрика приложений Flask"""
    
    app = Flask(__name__)
    
    # Загрузка конфигурации
    app.config.from_object(config[config_name])
    
    # директории
    os.makedirs('instance', exist_ok=True)
    os.makedirs('instance/uploads', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Инициализация расширений
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    # Импорт моделей
    from app import models
    
    # Инициализация БД
    models.init_db()
    
    # Регистрация blueprints
    from app.auth import auth_bp
    from app.routes import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    return app

