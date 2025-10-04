"""
Сервис для работы с API получения данных по ИНН.
DataNewton API, DaData API, Mock данные (fallback)
"""
import requests
import os

DATANEWTON_API_URL = 'https://api.datanewton.ru/v1/counterparty'
DATANEWTON_API_KEY = os.getenv('DATANEWTON_API_KEY', 'mi76aFMdgvml')
DADATA_API_URL = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party'
DADATA_API_KEY = os.getenv('DADATA_API_KEY', '')
MOCK_DATA = {
    '9728006808': {
        'inn': '9728006808',
        'kpp': '772801001',
        'ogrn': '1207700223257',
        'name': 'ООО "ТЕСТОВАЯ КОМПАНИЯ 1"',
        'full_name': 'Общество с ограниченной ответственностью "ТЕСТОВАЯ КОМПАНИЯ 1"',
        'legal_address': '125047, г. Москва, ул. Тверская, д. 10',
        'postal_address': '125047, г. Москва, ул. Тверская, д. 10',
        'director': 'Иванов Иван Иванович',
        'director_position': 'Генеральный директор',
        'bank_account': '40702810400000123456',
        'bank_name': 'ПАО "Сбербанк"',
        'bik': '044525225',
        'corr_account': '30101810400000000225',
        'legal_form': 'ООО',
    }
}


def fetch_company_data(inn: str, use_api: bool = True) -> dict:
    """Получить данные по ИНН с каскадным фоллбэком: DataNewton → DaData → Mock"""
    if not inn or not inn.isdigit():
        raise ValueError('ИНН должен содержать только цифры')
    if len(inn) not in [10, 12]:
        raise ValueError('ИНН должен содержать 10 или 12 цифр')
    
    if use_api:
        try:
            print(f"[API] DataNewton для ИНН {inn}")
            data = fetch_from_datanewton(inn)
            if data:
                print(f"[API] ✓ DataNewton успешно")
                return data
        except Exception as e:
            print(f"[API] ✗ DataNewton: {e}")
        
        if DADATA_API_KEY:
            try:
                print(f"[API] DaData для ИНН {inn}")
                data = fetch_from_dadata(inn)
                if data:
                    print(f"[API] ✓ DaData успешно")
                    return data
            except Exception as e:
                print(f"[API] ✗ DaData: {e}")
        
        print(f"[API] Используем mock данные")
    
    company_data = MOCK_DATA.get(inn)
    if company_data:
        print(f"[Mock] Найдены данные для ИНН {inn}")
        return company_data
    
    print(f"[Mock] ИНН {inn} не найден")
    return None


def validate_inn(inn: str) -> bool:
    """валидация формата ИНН (10 или 12 цифр)"""
    return inn and inn.isdigit() and len(inn) in [10, 12]


def fetch_from_datanewton(inn: str) -> dict:
    """Получить данные из DataNewton API (ключ в query)"""
    params = {
        'key': DATANEWTON_API_KEY,
        'inn': inn,
        'filters': 'OWNER_BLOCK,ADDRESS_BLOCK'
    }
    
    try:
        response = requests.get(
            DATANEWTON_API_URL,
            headers={'Accept': 'application/json'},
            params=params,
            timeout=10
        )
        
        print(f"[DataNewton] Status: {response.status_code}")
        print(f"[DataNewton] Response: {response.text[:500]}")
        
        response.raise_for_status()
        data = response.json()
        
        if not data or ('company' not in data and 'individual' not in data):
            raise ValueError('Некорректный ответ API')
        
        return parse_datanewton_response(data)
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f'Ошибка DataNewton API: {str(e)}')


def parse_datanewton_response(data: dict) -> dict:
    """Преобразование ответа DataNewton API (company/individual) в единый формат"""
    inn = data.get('inn', '')
    ogrn = data.get('ogrn', '')
    
    if 'individual' in data:
        individual = data.get('individual', {})
        address = individual.get('address', {})
        contacts = individual.get('contacts')
        fio = individual.get('fio', '')
        vid = individual.get('vid_iptext', 'Индивидуальный предприниматель')
        
        return {
            'inn': inn, 'kpp': '', 'ogrn': ogrn,
            'name': f'ИП {fio}', 'full_name': f'{vid} {fio}',
            'legal_address': address.get('line_address', ''),
            'postal_address': address.get('line_address', ''),
            'director': fio, 'director_position': 'Индивидуальный предприниматель',
            'bank_account': contacts.get('bank_account', '') if contacts else '',
            'bank_name': contacts.get('bank_name', '') if contacts else '',
            'bik': contacts.get('bik', '') if contacts else '',
            'corr_account': contacts.get('corr_account', '') if contacts else '',
            'legal_form': 'ИП',
        }
    
    company = data.get('company', {})
    company_names = company.get('company_names', {})
    address = company.get('address', {})
    managers = company.get('managers', [])
    contacts = company.get('contacts')
    owners = company.get('owners', {})
    
    director = ''
    director_position = 'Генеральный директор'
    if managers and len(managers) > 0:
        director = managers[0].get('name', '')
        director_position = managers[0].get('position', 'Генеральный директор')
    elif owners and 'fl' in owners and len(owners['fl']) > 0:
        director = owners['fl'][0].get('name', '')
        director_position = 'Учредитель'
    
    return {
        'inn': inn, 'kpp': company.get('kpp', ''), 'ogrn': ogrn,
        'name': company_names.get('short_name', ''),
        'full_name': company_names.get('full_name', ''),
        'legal_address': address.get('line_address', ''),
        'postal_address': address.get('line_address', ''),
        'director': director, 'director_position': director_position,
        'bank_account': contacts.get('bank_account', '') if contacts else '',
        'bank_name': contacts.get('bank_name', '') if contacts else '',
        'bik': contacts.get('bik', '') if contacts else '',
        'corr_account': contacts.get('corr_account', '') if contacts else '',
        'legal_form': company.get('opf', ''),
    }

