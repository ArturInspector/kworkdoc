"""
Генератор документов - заполнение шаблона DOCX
"""
from docx import Document
from docxtpl import DocxTemplate
from io import BytesIO
from datetime import datetime


def convert_to_genitive(position: str) -> str:
    """
    Преобразование должности в родительный падеж для фразы 'в лице...'
    """
    genitive_map = {
        'Генеральный директор': 'Генерального директора',
        'Директор': 'Директора',
        'Исполнительный директор': 'Исполнительного директора',
        'Управляющий': 'Управляющего',
        'Президент': 'Президента',
        'Председатель': 'Председателя',
    }
    
    return genitive_map.get(position, position + 'а') 


def format_date_russian(date_obj: datetime) -> str:
    """
    Форматирование даты в русский формат: «03» октября 2025
    
    Args:
        date_obj: объект datetime
        
    Returns:
        str: Дата в формате «ДД» месяц ГГГГ
    """
    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    
    day = date_obj.day
    month = months[date_obj.month]
    year = date_obj.year
    
    return f'«{day:02d}» {month} {year}'


def generate_contract(company_data: dict, template_path: str = 'templates/contract_template.docx') -> BytesIO:
    """
    Генерация договора на основе шаблона и данных компании
    
    Args:
        company_data (dict): Данные компании из API
        template_path (str): Путь к шаблону DOCX
        
    Returns:
        BytesIO: Готовый документ в памяти
    """
    
    # Проверка наличия шаблона
    try:
        doc = DocxTemplate(template_path)
    except FileNotFoundError:
        raise FileNotFoundError(f'Шаблон не найден: {template_path}')
    
    # Подготовка контекста для заполнения
    context = prepare_context(company_data)
    
    # Рендерим шаблон с данными
    doc.render(context)
    
    # Сохраняем в BytesIO
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    
    return file_stream


def prepare_context(company_data: dict) -> dict:
    """
    Подготовка контекста с условной логикой для шаблона
    
    Args:
        company_data (dict): Сырые данные компании
        
    Returns:
        dict: Контекст для заполнения шаблона
    """
    
    # Генерируем номер и дату договора
    contract_number = generate_contract_number()
    current_date = format_date_russian(datetime.now())
    
    # Базовые данные ЗАКАЗЧИКА (из API)
    context = {
        # Данные заказчика
        'customer_inn': company_data.get('inn', ''),
        'customer_kpp': company_data.get('kpp', ''),
        'customer_ogrn': company_data.get('ogrn', ''),
        'customer_name': company_data.get('name', ''),  # Краткое название
        'customer_full_name': company_data.get('full_name', ''),  # Полное название
        'customer_legal_address': company_data.get('legal_address', ''),
        'customer_postal_address': company_data.get('postal_address', ''),
        'customer_director': company_data.get('director', ''),
        'customer_director_position': company_data.get('director_position', ''),
        'customer_bank_account': company_data.get('bank_account', ''),
        'customer_bank_name': company_data.get('bank_name', ''),
        'customer_bik': company_data.get('bik', ''),
        'customer_corr_account': company_data.get('corr_account', ''),
        # Договор
        'contract_number': contract_number,
        'contract_date': current_date,
        'current_date': current_date,
    }
    
    # Условная логика (ветвления)
    # Определение типа компании и текста "действующий на основании"
    legal_form = company_data.get('legal_form', '')
    
    if 'ИП' in legal_form or 'Индивидуальный предприниматель' in company_data.get('full_name', ''):
        context['is_ooo'] = False
        context['is_ip'] = True
        context['customer_legal_basis'] = 'свидетельства о государственной регистрации'
        context['customer_acts_as'] = company_data.get('director', '')
        context['customer_position'] = ''
        context['customer_position_genitive'] = ''  # Родительный падеж для ИП не нужен
    elif 'ООО' in legal_form or 'Общество с ограниченной ответственностью' in company_data.get('full_name', ''):
        context['is_ooo'] = True
        context['is_ip'] = False
        context['customer_legal_basis'] = 'Устава'
        context['customer_acts_as'] = company_data.get('director', '')
        position = company_data.get('director_position', 'Генеральный директор')
        context['customer_position'] = position
        # Родительный падеж должности (для "в лице...")
        context['customer_position_genitive'] = convert_to_genitive(position)
    elif 'АО' in legal_form or 'ПАО' in legal_form:
        context['is_ooo'] = False
        context['is_ip'] = False
        context['customer_legal_basis'] = 'Устава'
        context['customer_acts_as'] = company_data.get('director', '')
        position = company_data.get('director_position', 'Генеральный директор')
        context['customer_position'] = position
        context['customer_position_genitive'] = convert_to_genitive(position)
    else:
        # Другие формы (по умолчанию как ООО)
        context['is_ooo'] = False
        context['is_ip'] = False
        context['customer_legal_basis'] = 'учредительных документов'
        context['customer_acts_as'] = company_data.get('director', '')
        position = company_data.get('director_position', '')
        context['customer_position'] = position
        context['customer_position_genitive'] = convert_to_genitive(position) if position else ''
    
    # Пример 2: Размер уставного капитала (если есть)
    capital = company_data.get('capital', '')
    if capital and capital != 'не применимо':
        try:
            capital_int = int(capital)
            if capital_int >= 100000:
                context['large_capital'] = True
                context['capital_text'] = f'с уставным капиталом {capital} рублей'
            else:
                context['large_capital'] = False
                context['capital_text'] = ''
        except ValueError:
            context['large_capital'] = False
            context['capital_text'] = ''
    else:
        context['large_capital'] = False
        context['capital_text'] = ''
    
    # Пример 3: Статус компании
    status = company_data.get('status', 'active')
    context['is_active'] = status == 'active'
    
    # Здесь будут добавляться дополнительные ветвления
    # когда ты пришлешь шаблон с плейсхолдерами
    
    return context


def generate_contract_number() -> str:
    """
    Генерация номера договора
    
    Returns:
        str: Номер договора в формате YYYY-MM-XXXXX
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"DOG-{timestamp}"


def get_filename(company_name: str, contract_number: str, contract_date: str) -> str:
    """
    Генерация имени файла для договора
    Формат: Договор №{номер} от {дата} — {Заказчик} — ИП Лукманов М.И..docx
    
    Args:
        company_name (str): Название компании заказчика
        contract_number (str): Номер договора
        contract_date (str): Дата договора
        
    Returns:
        str: Имя файла
    """
    # Очистка названия от спецсимволов, но оставляем читаемым
    safe_name = ''.join(c for c in company_name if c.isalnum() or c in (' ', '-', '_', '.'))
    safe_name = safe_name.strip()[:50]  # Ограничение длины
    
    return f"Договор №{contract_number} от {contract_date} — {safe_name} — ИП Лукманов М.И..docx"

