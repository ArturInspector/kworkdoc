"""
Генератор документов - заполнение шаблона DOCX
"""
from docxtpl import DocxTemplate
from io import BytesIO
from datetime import datetime


GENITIVE_MAP = {
    'Генеральный директор': 'Генерального директора',
    'Директор': 'Директора',
    'Исполнительный директор': 'Исполнительного директора',
    'Управляющий': 'Управляющего',
    'Президент': 'Президента',
    'Председатель': 'Председателя',
}

MONTHS_RUSSIAN = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}

# Словари для преобразования чисел в текст
UNITS = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
TENS = ['', 'десять', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 
        'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
TEENS = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать',
         'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
HUNDREDS = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 
            'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']
THOUSANDS = ['тысяча', 'тысячи', 'тысяч']


def pluralize_hours(hours: int) -> str:
    """Возвращает правильную форму слова 'час' в зависимости от числа."""
    hours = abs(hours)
    
    # Для чисел 11-14 всегда используем "часов"
    if 11 <= hours % 100 <= 14:
        return 'часов'
    
    # Проверяем последнюю цифру
    last_digit = hours % 10
    
    if last_digit == 1:
        return 'час'
    elif 2 <= last_digit <= 4:
        return 'часа'
    else:
        return 'часов'


def convert_to_genitive(position: str) -> str:
    """конвертит должность в родительный падеж."""
    return GENITIVE_MAP.get(position, position + 'а')


def format_date_russian(date_obj: datetime) -> str:
    """Форматирует дату в русский формат: «ДД» месяц ГГГГ."""
    month = MONTHS_RUSSIAN[date_obj.month]
    return f'«{date_obj.day:02d}» {month} {date_obj.year}'


def generate_contract(company_data: dict,
                      contract_data: dict = None,
                      template_path: str = 'templates/contract_template.docx') -> BytesIO:
    """Генерирует договор (основная)."""
    try:
        doc = DocxTemplate(template_path)
    except FileNotFoundError:
        raise FileNotFoundError(f'Не найден шаблон: {template_path}')
    
    context = prepare_context(company_data, contract_data)
    doc.render(context)
    
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    
    return file_stream


def _determine_legal_info(company_data: dict) -> dict:
    """Определяет тип компании и юридическую информацию."""
    legal_form = company_data.get('legal_form', '').lower()
    full_name = company_data.get('full_name', '').lower()
    name = company_data.get('name', '').lower()
    director = company_data.get('director', '')
    position = company_data.get('director_position', 'Генеральный директор')
    
    if ('ип' in legal_form or 'индивидуальн' in legal_form or 
        'индивидуальн' in full_name or 'индивидуальн' in name):
        return {
            'is_ooo': False,
            'is_ip': True,
            'customer_legal_basis': 'свидетельства о государственной регистрации',
            'customer_acts_as': director,
            'customer_position': '',
            'customer_position_genitive': ''
        }
    
    if ('ооо' in name or 'ооо' in full_name or 
        'обществ' in legal_form and 'ограниченн' in legal_form):
        return {
            'is_ooo': True,
            'is_ip': False,
            'customer_legal_basis': 'Устава',
            'customer_acts_as': director,
            'customer_position': position,
            'customer_position_genitive': convert_to_genitive(position)
        }
    
    # АО/ПАО: проверяем варианты
    if ('пао' in name or 'ао' in name or 
        'акционерн' in legal_form or 'акционерн' in full_name):
        return {
            'is_ooo': False,
            'is_ip': False,
            'customer_legal_basis': 'Устава',
            'customer_acts_as': director,
            'customer_position': position,
            'customer_position_genitive': convert_to_genitive(position)
        }
    
    # Fallback для других форм
    return {
        'is_ooo': False,
        'is_ip': False,
        'customer_legal_basis': 'учредительных документов',
        'customer_acts_as': director,
        'customer_position': position,
        'customer_position_genitive': convert_to_genitive(position) if position else ''
    }


def _format_capital(capital: str) -> dict:
    """Форматирует информацию об уставном капитале."""
    if not capital or capital == 'не применимо':
        return {'large_capital': False, 'capital_text': ''}
    
    try:
        capital_int = int(capital)
        if capital_int >= 100000:
            return {
                'large_capital': True,
                'capital_text': f'с уставным капиталом {capital} рублей'
            }
    except ValueError:
        pass
    
    return {'large_capital': False, 'capital_text': ''}


def prepare_context(company_data: dict, contract_data: dict = None) -> dict:
    """Подготавливает контекст для заполнения шаблона договора."""
    
    # Используем данные из формы или генерируем автоматически
    if contract_data:
        contract_number = contract_data.get('contract_number', generate_contract_number())
        # Преобразуем дату из YYYY-MM-DD в русский формат
        contract_date_str = contract_data.get('contract_date', '')
        try:
            date_obj = datetime.strptime(contract_date_str, '%Y-%m-%d')
            contract_date = format_date_russian(date_obj)
        except ValueError:
            contract_date = format_date_russian(datetime.now())
    else:
        contract_number = generate_contract_number()
        contract_date = format_date_russian(datetime.now())
    
    current_date = format_date_russian(datetime.now())
    
    context = {
        'customer_inn': company_data.get('inn', ''),
        'customer_kpp': company_data.get('kpp', ''),
        'customer_ogrn': company_data.get('ogrn', ''),
        'customer_name': company_data.get('name', ''),
        'customer_full_name': company_data.get('full_name', ''),
        'customer_legal_address': company_data.get('legal_address', ''),
        'customer_postal_address': company_data.get('postal_address', ''),
        'customer_director': company_data.get('director', ''),
        'customer_director_position': company_data.get('director_position', ''),
        'customer_bank_account': company_data.get('bank_account', ''),
        'customer_bank_name': company_data.get('bank_name', ''),
        'customer_bik': company_data.get('bik', ''),
        'customer_corr_account': company_data.get('corr_account', ''),
        
        'contract_number': contract_number,
        'contract_date': contract_date,
        'current_date': current_date,
    }
    
    if contract_data:
        context['services'] = contract_data.get('services', '')
        context['city'] = contract_data.get('city', '')
        context['hourly_rate'] = contract_data.get('hourly_rate', '')
        context['min_hours'] = contract_data.get('min_hours', '')
        city = contract_data.get('city', 'Казань')
        rate = contract_data.get('hourly_rate', '750')
        hours = contract_data.get('min_hours', '2')
        hours_int = int(hours) if hours and hours.isdigit() else 2
        hours_word = pluralize_hours(hours_int)
        context['hourly_payment_text'] = (
            f'Стоимость погрузочно-разгрузочных работ по г. {city} составит '
            f'{rate} рублей чел./час. Минимальный заказ {hours} {hours_word}.'
        )
    
    context.update(_determine_legal_info(company_data))
    context.update(_format_capital(company_data.get('capital', '')))
    
    return context


def generate_contract_number() -> str:
    """Генерирует уникальный номер договора."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"Contract-{timestamp}"


def get_filename(company_name: str, contract_number: str, contract_date: str) -> str:
    """Генерирует имя файла для договора."""
    safe_name = ''.join(
        c for c in company_name
        if c.isalnum() or c in (' ', '-', '_', '.')
    )
    safe_name = safe_name.strip()[:50]
    
    return f"Договор №{contract_number} от {contract_date} — {safe_name} — ИП Лукманов М.И..docx"

