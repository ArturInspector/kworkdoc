from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.inn_service import fetch_company_data, validate_inn
from app.document_generator import generate_contract, get_filename
from app.models import get_db_connection
import traceback

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """главная страница - редирект на dashboard"""
    return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """панель управления с формой для генерации договора"""
    return render_template('dashboard.html', user=current_user)


@main_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """генерация договора по ИНН"""
    
    inn = request.form.get('inn', '').strip()
    
    # валидация
    if not inn:
        return jsonify({'success': False, 'error': 'Введите ИНН'}), 400
    
    if not validate_inn(inn):
        return jsonify({'success': False, 'error': 'Некорректный формат ИНН (должно быть 10 или 12 цифр)'}), 400
    
    try:
        # получение данных по ИНН
        company_data = fetch_company_data(inn)
        
        if not company_data:
            return jsonify({'success': False, 'error': f'Компания с ИНН {inn} не найдена'}), 404
        
        # генерация документа
        doc_stream = generate_contract(company_data)
        
        # генерация имени файла
        from datetime import datetime
        from app.document_generator import generate_contract_number, format_date_russian
        
        contract_number = generate_contract_number()
        contract_date = format_date_russian(datetime.now())
        company_name = company_data.get('name', company_data.get('company_name', 'Компания'))
        
        filename = get_filename(company_name, contract_number, contract_date)
        
        # сохранение в историю
        save_to_history(
            user_id=current_user.id,
            inn=inn,
            company_name=company_name,
            filename=filename
        )
        
        return send_file(
            doc_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except FileNotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"Ошибка при генерации: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500


@main_bp.route('/history')
@login_required
def history():
    """история генераций договоров"""
    conn = get_db_connection()
    
    history_data = conn.execute(
        '''SELECT * FROM contract_history 
           WHERE user_id = ? 
           ORDER BY created_at DESC 
           LIMIT 50''',
        (current_user.id,)
    ).fetchall()
    
    conn.close()
    
    return render_template('history.html', history=history_data, user=current_user)


@main_bp.route('/download/<int:history_id>')
@login_required
def download_from_history(history_id):
    """скачать договор из истории (регенерация по ИНН)"""
    
    conn = get_db_connection()
    record = conn.execute(
        'SELECT * FROM contract_history WHERE id = ? AND user_id = ?',
        (history_id, current_user.id)
    ).fetchone()
    conn.close()
    
    if not record:
        flash('Запись не найдена', 'error')
        return redirect(url_for('main.history'))
    
    try:
        # Регенерируем договор по ИНН
        company_data = fetch_company_data(record['inn'])
        
        if not company_data:
            flash(f'Не удалось получить данные по ИНН {record["inn"]}', 'error')
            return redirect(url_for('main.history'))
        
        # Генерация документа
        doc_stream = generate_contract(company_data)
        
        # Используем сохранённое имя файла
        filename = record['filename']
        
        return send_file(
            doc_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        print(f"Ошибка при скачивании из истории: {traceback.format_exc()}")
        flash(f'Ошибка при генерации: {str(e)}', 'error')
        return redirect(url_for('main.history'))


def save_to_history(user_id: int, inn: str, company_name: str, filename: str):
    """сохранение записи в историю генераций"""
    conn = get_db_connection()
    
    conn.execute(
        '''INSERT INTO contract_history (user_id, inn, company_name, filename)
           VALUES (?, ?, ?, ?)''',
        (user_id, inn, company_name, filename)
    )
    
    conn.commit()
    conn.close()

