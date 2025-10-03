"""
Сервис для работы с несколькими API для получения данных по ИНН
Поддерживаемые источники:
1. DataNewton API - https://datanewton.ru/docs/api
2. DaData API - https://dadata.ru/api/find-party/
3. Mock данные (для разработки)
"""
import requests
import os
DATANEWTON_API_URL = 'https://api.datanewton.ru/v1/counterparty'
DATANEWTON_API_KEY = os.getenv('DATANEWTON_API_KEY', 'mi76aFMdgvml')  # Тестовый ключ
DADATA_API_URL = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party'
DADATA_API_KEY = os.getenv('DADATA_API_KEY', '')  # Нужно получить на dadata.ru
# Тестовые
MOCK_DATA = {
    '7707083893': {
        'inn': '7707083893',
        'kpp': '770701001',
        'ogrn': '1027700132195',
        'name': 'ООО "РОМАШКА"',
        'full_name': 'Общество с ограниченной ответственностью "РОМАШКА"',
        'legal_address': '119991, г. Москва, ул. Ленина, д. 1, офис 100',
        'postal_address': '119991, г. Москва, ул. Ленина, д. 1, офис 100',
        'director': 'Иванов Иван Иванович',
        'director_position': 'Генеральный директор',
        'bank_account': '40702810400000123456',
        'bank_name': 'ПАО "Сбербанк"',
        'bik': '044525225',
        'corr_account': '30101810400000000225',
        'legal_form': 'ООО',
    },
    '1234567890': {
        'inn': '1234567890',
        'kpp': '123401001',
        'ogrn': '1234567890123',
        'name': 'ИП Петров П.П.',
        'full_name': 'Индивидуальный предприниматель Петров Петр Петрович',
        'legal_address': '123456, г. Санкт-Петербург, пр. Невский, д. 50',
        'postal_address': '123456, г. Санкт-Петербург, пр. Невский, д. 50',
        'director': 'Петров Петр Петрович',
        'director_position': 'Индивидуальный предприниматель',
        'bank_account': '40802810500000654321',
        'bank_name': 'ПАО "ВТБ"',
        'bik': '044525411',
        'corr_account': '30101810145250000411',
        'legal_form': 'ИП',
    }
}


def fetch_company_data(inn: str, use_api: bool = True) -> dict:
    """
    Получить данные компании по ИНН с каскадным фоллбэком:
    1. DataNewton API
    2. DaData API (если первый не сработал)
    3. Mock данные (если оба API недоступны)
    
    Args:
        inn (str): ИНН компании
        use_api (bool): Использовать реальные API (True = пробуем API, False = только mock)
        
    Returns:
        dict: Данные компании или None если не найдено
        
    Raises:
        ValueError: Если ИНН невалидный
    """
    
    # Валидация ИНН
    if not inn or not inn.isdigit():
        raise ValueError('ИНН должен содержать только цифры')
    
    if len(inn) not in [10, 12]:
        raise ValueError('ИНН должен содержать 10 или 12 цифр')
    
    # Если use_api=True, пробуем реальные API
    if use_api:
        # Попытка 1: DataNewton API
        try:
            print(f"[API] Попытка 1: DataNewton API для ИНН {inn}")
            data = fetch_from_datanewton(inn)
            if data:
                print(f"[API] ✓ DataNewton успешно вернул данные")
                return data
        except Exception as e:
            print(f"[API] ✗ DataNewton API не сработал: {e}")
        
        # Попытка 2: DaData API
        if DADATA_API_KEY:
            try:
                print(f"[API] Попытка 2: DaData API для ИНН {inn}")
                data = fetch_from_dadata(inn)
                if data:
                    print(f"[API] ✓ DaData успешно вернул данные")
                    return data
            except Exception as e:
                print(f"[API] ✗ DaData API не сработал: {e}")
        else:
            print(f"[API] Пропускаем DaData (нет API ключа)")
        
        print(f"[API] Все API недоступны, используем mock данные")
    
    # Фоллбэк на mock данные
    company_data = MOCK_DATA.get(inn)
    
    if company_data:
        print(f"[Mock] Найдены тестовые данные для ИНН {inn}")
        return company_data
    else:
        print(f"[Mock] ИНН {inn} не найден в тестовых данных")
        return None


def validate_inn(inn: str) -> bool:
    """
    Валидация формата ИНН
    
    Args:
        inn (str): ИНН для проверки
        
    Returns:
        bool: True если ИНН валидный
    """
    if not inn or not inn.isdigit():
        return False
    
    if len(inn) not in [10, 12]:
        return False
    
    return True


def fetch_from_datanewton(inn: str) -> dict:
    """
    Получить данные из DataNewton API
    Документация: https://datanewton.ru/docs/api
    """
    
    headers = {
        'Authorization': f'Token {DATANEWTON_API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Для DataNewton нужно передавать ogrn, а не inn напрямую
    # Но можем попробовать сначала через inn parameter
    params = {
        'ogrn': inn if len(inn) > 10 else None,  # Если 12-13 цифр, это может быть ОГРН
        'inn': inn,
    }
    
    # Убираем None значения
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = requests.get(
            DATANEWTON_API_URL,
            headers=headers,
            params=params,
            timeout=10
        )
        
        print(f"[DataNewton] Status: {response.status_code}")
        print(f"[DataNewton] Response: {response.text[:200]}")
        
        response.raise_for_status()
        data = response.json()
        
        # Маппинг DataNewton формата в наш формат
        return parse_datanewton_response(data)
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f'Ошибка DataNewton API: {str(e)}')


def parse_datanewton_response(data: dict) -> dict:
    """
    Преобразование ответа DataNewton API в нужный формат
    """
    
    general = data.get('general', {})
    contacts = data.get('contacts', {})
    
    return {
        'inn': general.get('inn', ''),
        'kpp': general.get('kpp', ''),
        'ogrn': general.get('ogrn', ''),
        'name': general.get('shortName', ''),
        'full_name': general.get('fullName', ''),
        'legal_address': general.get('legalAddress', ''),
        'postal_address': general.get('postalAddress', general.get('legalAddress', '')),
        'director': general.get('ceo', {}).get('fullName', ''),
        'director_position': general.get('ceo', {}).get('position', 'Генеральный директор'),
        'bank_account': contacts.get('bankAccount', ''),
        'bank_name': contacts.get('bankName', ''),
        'bik': contacts.get('bik', ''),
        'corr_account': contacts.get('corrAccount', ''),
        'legal_form': general.get('legalForm', ''),
    }

