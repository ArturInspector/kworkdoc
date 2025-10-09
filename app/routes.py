from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.inn_service import fetch_company_data, validate_inn
from app.document_generator import generate_contract, get_filename
from app.models import (get_db_connection, get_executor_profile, 
                        get_all_executor_profiles, save_executor_profile, 
                        set_default_profile)
import traceback
from datetime import datetime
from app.document_generator import format_date_russian
import json

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """главная страница - редирект на dashboard"""
    return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """панель управления с формой для генерации договора"""
    profiles = get_all_executor_profiles()
    return render_template('dashboard.html', 
                         user=current_user, 
                         executor_profiles=profiles)


@main_bp.route('/api/check-inn', methods=['POST'])
@login_required
def check_inn():
    """AJAX endpoint для проверки ИНН и получения данных"""
    
    data = request.get_json()
    inn = data.get('inn', '').strip() if data else ''
    use_api_fns = data.get('use_api_fns', False) if data else False
    
    # Валидация
    if not inn:
        return jsonify({'success': False, 'error': 'Введите ИНН'}), 400
    
    if not validate_inn(inn):
        return jsonify({'success': False, 'error': 'Некорректный формат ИНН (должно быть 10 или 12 цифр)'}), 400
    
    try:
        # Получение данных по ИНН
        company_data = fetch_company_data(inn, use_api_fns=use_api_fns)
        
        if not company_data:
            # Если основной API не нашел данные, предлагаем резервный
            if not use_api_fns:
                return jsonify({
                    'success': False, 
                    'error': 'not_found',
                    'message': f'Компания с ИНН {inn} не найдена в основном источнике',
                    'suggest_backup': True
                }), 404
            else:
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
    executor_profile_id = request.form.get('executor_profile_id', '').strip()
    bank_details = request.form.get('bank_details', '').strip()
    
    # Новые поля - услуги с расценками
    pricing_services_json = request.form.get('pricing_services', '').strip()
    packing_percentage = request.form.get('packing_percentage', '').strip()
    prepayment_amount = request.form.get('prepayment_amount', '').strip()
    
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
    
    if not pricing_services_json:
        return jsonify({'success': False, 'error': 'Добавьте хотя бы одну услугу с расценками'}), 400
    
    if not executor_profile_id:
        return jsonify({'success': False, 'error': 'Выберите профиль исполнителя'}), 400
    
    try:
        import json
        pricing_services = json.loads(pricing_services_json)
    except:
        return jsonify({'success': False, 'error': 'Ошибка в данных услуг'}), 400
    
    try:
        company_data = fetch_company_data(inn)
        
        if not company_data:
            return jsonify({'success': False, 'error': f'Компания с ИНН {inn} не найдена'}), 404
        
        contract_data = {
            'contract_number': contract_number,
            'contract_date': contract_date,
            'services': services,
            'pricing_services': pricing_services,
            'packing_percentage': packing_percentage,
            'prepayment_amount': prepayment_amount,
            'bank_details': bank_details
        }
        
        # Дебаг: проверяем что получили bank_details
        print(f"DEBUG: bank_details = '{bank_details}'")
        print(f"DEBUG: contract_data['bank_details'] = '{contract_data.get('bank_details')}'")
        
        doc_stream = generate_contract(company_data, contract_data, int(executor_profile_id))
        

        try:
            date_obj = datetime.strptime(contract_date, '%Y-%m-%d')
            filename_date = date_obj.strftime('%d.%m.%Y')
        except ValueError:
            filename_date = contract_date.replace('-', '.')
        
        company_name = company_data.get('name', company_data.get('company_name', 'Компания'))
        
        # Получаем короткое имя исполнителя для filename
        executor_profile = get_executor_profile(int(executor_profile_id))
        executor_short = executor_profile.get('short_name', 'Исполнитель') if executor_profile else 'Исполнитель'
        
        filename = get_filename(company_name, contract_number, filename_date, executor_short)
    
        save_to_history(
            user_id=current_user.id,
            inn=inn,
            company_name=company_name,
            filename=filename,
            contract_data=contract_data,
            executor_profile_id=int(executor_profile_id),
            executor_name=executor_short
        )
        
        response = send_file(
            doc_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Имя файла уже транслитерировано, дополнительное кодирование не нужно
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
    record_row = conn.execute(
        'SELECT * FROM contract_history WHERE id = ? AND user_id = ?',
        (history_id, current_user.id)
    ).fetchone()
    conn.close()
    
    if not record_row:
        flash('Запись не найдена', 'error')
        return redirect(url_for('main.history'))
    
    # Конвертируем sqlite3.Row в dict для удобства
    record = dict(record_row)
    
    try:
        company_data = fetch_company_data(record['inn'])
        
        if not company_data:
            flash(f'Не удалось получить данные по ИНН {record["inn"]}', 'error')
            return redirect(url_for('main.history'))
        
        # Восстанавливаем contract_data из истории
        contract_data = None
        if record['contract_number']:
 

            pricing_services = []
            if record.get('pricing_services_json'):
                try:
                    pricing_services = json.loads(record['pricing_services_json'])
                except:
                    pass
            
            # Если нет новых данных, используем старый формат для обратной совместимости
            if not pricing_services and record.get('city'):
                pricing_services = [{
                    'name': 'погрузочно-разгрузочных работ',
                    'city_from': record['city'],
                    'city_to': '',
                    'rate': record['hourly_rate'],
                    'unit': 'руб./чел./час',
                    'min_hours': record['min_hours'],
                    'additional_hours': '0'
                }]
            
            contract_data = {
                'contract_number': record['contract_number'],
                'contract_date': record['contract_date'],
                'services': record['services'],
                'pricing_services': pricing_services,
                'packing_percentage': record.get('packing_percentage', ''),
                'prepayment_amount': record.get('prepayment_amount', ''),
                'bank_details': record.get('bank_details', '')
            }
        
        # Используем сохраненный профиль исполнителя или дефолтный
        profile_id = record['executor_profile_id'] if record['executor_profile_id'] else None
        if not profile_id:
            default_profile = get_executor_profile()
            profile_id = default_profile['id'] if default_profile else None
        
        doc_stream = generate_contract(company_data, contract_data, profile_id)
        filename = record['filename']
        
        response = send_file(
            doc_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        # Имя файла уже транслитерировано при сохранении в историю
        return response
        
    except Exception as e:
        print(f"Ошибка при скачивании из истории: {traceback.format_exc()}")
        flash(f'Ошибка при генерации: {str(e)}', 'error')
        return redirect(url_for('main.history'))


def save_to_history(user_id: int, inn: str, company_name: str, filename: str, 
                    contract_data: dict = None, executor_profile_id: int = None, 
                    executor_name: str = None):
    """сохранение записи в историю генераций"""
    import json
    conn = get_db_connection()
    
    if contract_data:
        # Сериализуем pricing_services в JSON
        pricing_services_json = json.dumps(contract_data.get('pricing_services', []), ensure_ascii=False)
        
        conn.execute(
            '''INSERT INTO contract_history 
               (user_id, inn, company_name, filename, contract_number, contract_date, 
                services, city, hourly_rate, min_hours, executor_profile_id, executor_name,
                pricing_services_json, packing_percentage, prepayment_amount, bank_details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, inn, company_name, filename, 
             contract_data.get('contract_number'), contract_data.get('contract_date'),
             contract_data.get('services'), 
             # Оставляем старые поля для обратной совместимости
             contract_data.get('pricing_services', [{}])[0].get('city_from', '') if contract_data.get('pricing_services') else '',
             contract_data.get('pricing_services', [{}])[0].get('rate', '') if contract_data.get('pricing_services') else '',
             contract_data.get('pricing_services', [{}])[0].get('min_hours', '') if contract_data.get('pricing_services') else '',
             executor_profile_id, executor_name,
             pricing_services_json,
             contract_data.get('packing_percentage', ''),
             contract_data.get('prepayment_amount', ''),
             contract_data.get('bank_details', ''))
        )
    else:
        conn.execute(
            '''INSERT INTO contract_history 
               (user_id, inn, company_name, filename, executor_profile_id, executor_name)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, inn, company_name, filename, executor_profile_id, executor_name)
        )
    
    conn.commit()
    conn.close()


@main_bp.route('/settings')
@login_required
def settings():
    """страница настроек реквизитов исполнителя"""
    profiles = get_all_executor_profiles()
    # При заходе на /settings показываем форму создания нового профиля
    return render_template('settings.html', 
                         profiles=profiles, 
                         current_profile=None,
                         user=current_user)


@main_bp.route('/settings/save', methods=['POST'])
@login_required
def save_settings():
    """сохранение реквизитов исполнителя"""
    profile_id = request.form.get('profile_id')
    
    data = {
        'profile_name': request.form.get('profile_name', '').strip(),
        'org_type': request.form.get('org_type', '').strip(),
        'full_name': request.form.get('full_name', '').strip(),
        'short_name': request.form.get('short_name', '').strip(),
        'legal_address': request.form.get('legal_address', '').strip(),
        'postal_address': request.form.get('postal_address', '').strip(),
        'inn': request.form.get('inn', '').strip(),
        'ogrn': request.form.get('ogrn', '').strip(),
        'bank_account': request.form.get('bank_account', '').strip(),
        'bank_name': request.form.get('bank_name', '').strip(),
        'bik': request.form.get('bik', '').strip(),
        'corr_account': request.form.get('corr_account', '').strip(),
        'email': request.form.get('email', '').strip(),
        'phone': request.form.get('phone', '').strip(),
    }
    
    # Базовая валидация
    if not data['profile_name'] or not data['full_name'] or not data['inn']:
        flash('Заполните обязательные поля: Название профиля, Полное название, ИНН', 'error')
        return redirect(url_for('main.settings'))
    
    try:
        save_executor_profile(data, int(profile_id) if profile_id else None)
        flash('Реквизиты успешно сохранены', 'success')
    except Exception as e:
        flash(f'Ошибка при сохранении: {str(e)}', 'error')
    
    return redirect(url_for('main.settings'))


@main_bp.route('/settings/set-default/<int:profile_id>', methods=['POST'])
@login_required
def set_default(profile_id):
    """установить профиль как дефолтный"""
    try:
        set_default_profile(profile_id)
        flash('Профиль установлен по умолчанию', 'success')
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
    
    return redirect(url_for('main.settings'))


@main_bp.route('/settings/delete/<int:profile_id>', methods=['POST'])
@login_required
def delete_profile(profile_id):
    """удалить профиль"""
    try:
        conn = get_db_connection()
        # Проверяем что это не последний профиль
        count = conn.execute('SELECT COUNT(*) FROM executor_profiles').fetchone()[0]
        if count <= 1:
            flash('Нельзя удалить последний профиль', 'error')
        else:
            # Проверяем что это не дефолтный
            is_default = conn.execute(
                'SELECT is_default FROM executor_profiles WHERE id = ?', (profile_id,)
            ).fetchone()
            
            if is_default and is_default[0] == 1:
                flash('Нельзя удалить профиль по умолчанию. Сначала установите другой профиль как основной', 'error')
            else:
                conn.execute('DELETE FROM executor_profiles WHERE id = ?', (profile_id,))
                conn.commit()
                flash('Профиль удалён', 'success')
        conn.close()
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
    
    return redirect(url_for('main.settings'))


@main_bp.route('/settings/edit/<int:profile_id>')
@login_required
def edit_profile(profile_id):
    """редактировать профиль"""
    profiles = get_all_executor_profiles()
    current_profile = get_executor_profile(profile_id)
    return render_template('settings.html', 
                         profiles=profiles, 
                         current_profile=current_profile,
                         edit_mode=True,
                         user=current_user)

