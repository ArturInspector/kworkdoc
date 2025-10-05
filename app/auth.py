from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models import User
from config import config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """страница входа"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('login.html')
        
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """сброс пароля по ключу владельца"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        new_password = request.form.get('new_password', '').strip()
        owner_key = request.form.get('owner_key', '').strip()
        
        if not username or not new_password or not owner_key:
            flash('заполните все поля', 'error')
            return render_template('login.html', show_reset=True)
        
        # Проверяем ключ владельца
        current_config = config['default']
        if owner_key != current_config.OWNER_RESET_KEY:
            flash('Неверный ключ владельца', 'error')
            return render_template('login.html', show_reset=True)
        
        # Проверяем, что пользователь существует
        user = User.get_by_username(username)
        if not user:
            flash('Пользователь с таким логином не найден', 'error')
            return render_template('login.html', show_reset=True)
        
        # Сбрасываем пароль
        if User.reset_password(username, new_password):
            flash('Пароль успешно изменен', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Ошибка при изменении пароля', 'error')
    
    return render_template('login.html', show_reset=True)

