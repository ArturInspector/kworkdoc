"""
Генератор документов - заполнение шаблона DOCX
"""
from docxtpl import DocxTemplate
from io import BytesIO
from datetime import datetime
from app.models import get_executor_profile

GENITIVE_MAP = {
    'Генеральный директор': 'Генерального директора',
    'Директор': 'Директора',
    'Исполнительный директор': 'Исполнительного директора',
    'Управляющий': 'Управляющего',
    'Президент': 'Президента',
    'Председатель': 'Председателя',
    'Учредитель': 'Учредителя',
}

MONTHS_RUSSIAN = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}
UNITS = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
TENS = ['', 'десять', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 
        'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
TEENS = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать',
         'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
HUNDREDS = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 
            'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']
THOUSANDS = ['тысяча', 'тысячи', 'тысяч']


def number_to_words(number: int) -> str:
    """Преобразует число в текст (для сумм в договорах)."""
    if number == 0:
        return 'ноль'
    
    if number < 0:
        return 'минус ' + number_to_words(-number)
    
    if number >= 1000000:
        return str(number)  # Для больших чисел оставляем цифрами
    
    result = []
    
    # Тысячи
    thousands = number // 1000
    if thousands > 0:
        if thousands == 1:
            result.append('одна тысяча')
        elif thousands == 2:
            result.append('две тысячи')
        elif 2 < thousands < 5:
            result.append(UNITS[thousands] + ' тысячи')
        elif thousands < 10:
            result.append(UNITS[thousands] + ' тысяч')
        elif 10 <= thousands < 20:
            result.append(TEENS[thousands - 10] + ' тысяч')
        elif thousands < 100:
            tens_part = thousands // 10
            units_part = thousands % 10
            result.append(TENS[tens_part])
            if units_part == 1:
                result.append('одна тысяча')
            elif units_part == 2:
                result.append('две тысячи')
            elif 2 < units_part < 5:
                result.append(UNITS[units_part] + ' тысячи')
            elif units_part > 0:
                result.append(UNITS[units_part] + ' тысяч')
            else:
                result[-1] += ' тысяч'
    
    remainder = number % 1000
    if remainder > 0:
        hundreds = remainder // 100
        tens = (remainder % 100) // 10
        units = remainder % 10
        
        if hundreds > 0:
            result.append(HUNDREDS[hundreds])
        
        if tens == 1:
            result.append(TEENS[units])
        else:
            if tens > 0:
                result.append(TENS[tens])
            if units > 0:
                result.append(UNITS[units])
    
    return ' '.join(result)


def pluralize_hours(hours: int) -> str:
    """Возвращает правильную форму слова 'час' в зависимости от числа."""
    hours = abs(hours)
    
    if 11 <= hours % 100 <= 14:
        return 'часов'
    
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


def fix_caps(text: str) -> str:
    """Приводит текст в КАПСЕ к нормальному виду с учетом русских правил."""
    if not text or not text.isupper():
        return text
    
    keep_upper = {'ООО', 'ОАО', 'ЗАО', 'ПАО', 'АО', 'ИП', 'ГУП', 'МУП'}
    
    words = text.split()
    result = []
    in_quotes = False
    
    for word in words:
        clean_word = word.strip('",«»()[]')
            
        if any(q in word for q in ['"', '«', '"']):
            in_quotes = True
        
        if clean_word in keep_upper:
            result.append(word)
        elif in_quotes:
            # Для названий в кавычках используем title (каждое слово с заглавной)
            result.append(word.title())
        else:
            # Для обычного текста - только первая буква
            result.append(word.capitalize())
        
        # Проверяем закрывающую кавычку
        if any(q in word for q in ['"', '»', '"']):
            in_quotes = False
    
    return ' '.join(result)


def format_date_russian(date_obj: datetime) -> str:
    """Форматирует дату в русский формат: «ДД» месяц ГГГГ."""
    month = MONTHS_RUSSIAN[date_obj.month]
    return f'«{date_obj.day:02d}» {month} {date_obj.year}'


def generate_contract(company_data: dict,
                      contract_data: dict = None,
                      executor_profile_id: int = None,
                      template_path: str = 'templates/contract_template.docx') -> BytesIO:
    """Генерирует договор (основная)."""
    try:
        doc = DocxTemplate(template_path)
    except FileNotFoundError:
        raise FileNotFoundError(f'Не найден шаблон: {template_path}')
    
    context = prepare_context(company_data, contract_data, executor_profile_id)
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


def prepare_context(company_data: dict, contract_data: dict = None, executor_profile_id: int = None) -> dict:
    """Подготавливает контекст для заполнения шаблона договора."""

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
        'customer_name': fix_caps(company_data.get('name', '')),
        'customer_full_name': fix_caps(company_data.get('full_name', '')),
        'customer_legal_address': fix_caps(company_data.get('legal_address', '')),
        'customer_postal_address': fix_caps(company_data.get('postal_address', '')),
        'customer_director': fix_caps(company_data.get('director', '')),
        'customer_director_position': fix_caps(company_data.get('director_position', '')),
        'customer_bank_account': company_data.get('bank_account', ''),
        'customer_bank_name': fix_caps(company_data.get('bank_name', '')),
        'customer_bik': company_data.get('bik', ''),
        'customer_corr_account': company_data.get('corr_account', ''),
        
        'contract_number': contract_number,
        'contract_date': contract_date,
        'current_date': current_date,
    }
    
    # Данные ИСПОЛНИТЕЛЯ из БД (используем переданный profile_id или дефолтный)
    executor = get_executor_profile(executor_profile_id)
    if executor:
        org_type = executor.get('org_type', 'ИП')
        
        context.update({
            'executor_name': executor.get('full_name', ''),
            'executor_short_name': executor.get('short_name', ''),
            'executor_legal_address': executor.get('legal_address', ''),
            'executor_postal_address': executor.get('postal_address', ''),
            'executor_inn': executor.get('inn', ''),
            'executor_ogrnip': executor.get('ogrn', ''),
            'executor_ogrn': executor.get('ogrn', ''),
            'executor_bank_account': executor.get('bank_account', ''),
            'executor_bank_name': executor.get('bank_name', ''),
            'executor_bik': executor.get('bik', ''),
            'executor_corr_account': executor.get('corr_account', ''),
            'executor_email': executor.get('email', ''),
            'executor_phone': executor.get('phone', ''),
            # Флаги типа организации исполнителя
            'exec_is_ip': org_type == 'ИП',
            'exec_is_ooo': org_type == 'ООО',
        })
    
    if contract_data:
        context['services'] = contract_data.get('services', '')
        context['city'] = contract_data.get('city', '')
        context['hourly_rate'] = contract_data.get('hourly_rate', '')
        context['min_hours'] = contract_data.get('min_hours', '')
        city = contract_data.get('city', 'Казань')
        rate = contract_data.get('hourly_rate', '750')
        hours = contract_data.get('min_hours', '2')
        
        # Преобразуем ставку в число и прописью
        rate_int = int(rate) if rate and rate.isdigit() else 750
        rate_words = number_to_words(rate_int)
        
        hours_int = int(hours) if hours and hours.isdigit() else 2
        hours_word = pluralize_hours(hours_int)
        
        context['hourly_payment_text'] = (
            f'Стоимость погрузочно-разгрузочных работ по г. {city} составит '
            f'{rate} ({rate_words}) рублей чел./час. Минимальный заказ {hours} {hours_word}.'
        )
    
    context.update(_determine_legal_info(company_data))
    context.update(_format_capital(company_data.get('capital', '')))
    
    return context


def generate_contract_number() -> str:
    """Генерирует уникальный номер договора."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"Contract-{timestamp}"


def transliterate(text: str) -> str:
    """Транслитерация кириллицы в латиницу для безопасных имен файлов."""
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        '№': 'N', '—': '-', '–': '-', '"': '', '"': '', '«': '', '»': ''
    }
    
    result = []
    for char in text:
        if char in translit_map:
            result.append(translit_map[char])
        elif char.isalnum() or char in (' ', '-', '_', '.'):
            result.append(char)
        else:
            result.append('_')
    
    return ''.join(result)


def get_filename(company_name: str, contract_number: str, contract_date: str, executor_short_name: str = 'Исполнитель') -> str:
    """Генерирует имя файла для договора (транслитерация кириллицы)."""
    # Транслитерируем все части имени
    safe_name = transliterate(company_name).strip()[:50]
    safe_executor = transliterate(executor_short_name).strip()[:30]
    safe_number = transliterate(contract_number).strip()
    
    # Убираем лишние пробелы и подчеркивания
    safe_name = ' '.join(safe_name.split())
    safe_executor = ' '.join(safe_executor.split())
    
    return f"Contract-{safe_number}-{contract_date}-{safe_name}-{safe_executor}.docx"

