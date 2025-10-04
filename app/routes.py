from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.inn_service import fetch_company_data, validate_inn
from app.document_generator import generate_contract, get_filename
from app.models import get_db_connection
import traceback
from datetime import datetime
from app.document_generator import format_date_russian
from urllib.parse import quote

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


@main_bp.route('/api/check-inn', methods=['POST'])
@login_required
def check_inn():
    """AJAX endpoint для проверки ИНН и получения данных"""
    
    data = request.get_json()
    inn = data.get('inn', '').strip() if data else ''
    
    # Валидация
    if not inn:
        return jsonify({'success': False, 'error': 'Введите ИНН'}), 400
    
    if not validate_inn(inn):
        return jsonify({'success': False, 'error': 'Некорректный формат ИНН (должно быть 10 или 12 цифр)'}), 400
    
    try:
        # Получение данных по ИНН
        company_data = fetch_company_data(inn)
        
        if not company_data:
            return jsonify({
                'success': False, 
                'error': f'Компания с ИНН {inn} не найдена ни в одном из источников'
            }), 404
        
        return jsonify({
            'success': True,
            'data': company_data
        }), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"Ошибка при проверке ИНН: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Ошибка сервера: {str(e)}'}), 500


@main_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """генерация договора по ИНН"""
    
    inn = request.form.get('inn', '').strip()
    contract_number = request.form.get('contract_number', '').strip()
    contract_date = request.form.get('contract_date', '').strip()
    services = request.form.get('services', '').strip()
    city = request.form.get('city', '').strip()
    hourly_rate = request.form.get('hourly_rate', '').strip()
    min_hours = request.form.get('min_hours', '').strip()
    
    # валидация
    if not inn:
        return jsonify({'success': False, 'error': 'Введите ИНН'}), 400
    
    if not validate_inn(inn):
        return jsonify({'success': False, 'error': 'Некорректный формат ИНН (должно быть 10 или 12 цифр)'}), 400
    
    if not contract_number:
        return jsonify({'success': False, 'error': 'Введите номер договора'}), 400
        
    if not contract_date:
        return jsonify({'success': False, 'error': 'Введите дату договора'}), 400
        
    if not services:
        return jsonify({'success': False, 'error': 'Введите описание услуг'}), 400
        
    if not city or not hourly_rate or not min_hours:
        return jsonify({'success': False, 'error': 'Заполните все поля почасовой оплаты'}), 400
    
    try:
        company_data = fetch_company_data(inn)
        
        if not company_data:
            return jsonify({'success': False, 'error': f'Компания с ИНН {inn} не найдена'}), 404
        
        contract_data = {
            'contract_number': contract_number,
            'contract_date': contract_date,
            'services': services,
            'city': city,
            'hourly_rate': hourly_rate,
            'min_hours': min_hours
        }
        
        doc_stream = generate_contract(company_data, contract_data)
        
        try:
            date_obj = datetime.strptime(contract_date, '%Y-%m-%d')
            formatted_date = format_date_russian(date_obj)
        except ValueError:
            formatted_date = contract_date
        
        company_name = company_data.get('name', company_data.get('company_name', 'Компания'))
        
        filename = get_filename(company_name, contract_number, formatted_date)
    
        save_to_history(
            user_id=current_user.id,
            inn=inn,
            company_name=company_name,
            filename=filename,
            contract_data=contract_data
        )
        
        response = send_file(
            doc_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

        response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
        return response
        
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
    """скачать договор из истории (регенерация с теми же параметрами)"""
    
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
        company_data = fetch_company_data(record['inn'])
        
        if not company_data:
            flash(f'Не удалось получить данные по ИНН {record["inn"]}', 'error')
            return redirect(url_for('main.history'))
        
        # Восстанавливаем contract_data из истории
        contract_data = None
        if record['contract_number']:
            contract_data = {
                'contract_number': record['contract_number'],
                'contract_date': record['contract_date'],
                'services': record['services'],
                'city': record['city'],
                'hourly_rate': record['hourly_rate'],
                'min_hours': record['min_hours']
            }
        
        doc_stream = generate_contract(company_data, contract_data)
        filename = record['filename']
        
        response = send_file(
            doc_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        # Явно устанавливаем правильный заголовок для кириллицы (RFC 6266)
        from urllib.parse import quote
        response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
        return response
        
    except Exception as e:
        print(f"Ошибка при скачивании из истории: {traceback.format_exc()}")
        flash(f'Ошибка при генерации: {str(e)}', 'error')
        return redirect(url_for('main.history'))


def save_to_history(user_id: int, inn: str, company_name: str, filename: str, contract_data: dict = None):
    """сохранение записи в историю генераций"""
    conn = get_db_connection()
    
    if contract_data:
        conn.execute(
            '''INSERT INTO contract_history 
               (user_id, inn, company_name, filename, contract_number, contract_date, services, city, hourly_rate, min_hours)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, inn, company_name, filename, 
             contract_data.get('contract_number'), contract_data.get('contract_date'),
             contract_data.get('services'), contract_data.get('city'),
             contract_data.get('hourly_rate'), contract_data.get('min_hours'))
        )
    else:
        conn.execute(
            '''INSERT INTO contract_history (user_id, inn, company_name, filename)
               VALUES (?, ?, ?, ?)''',
            (user_id, inn, company_name, filename)
        )
    
    conn.commit()
    conn.close()

