document.addEventListener('DOMContentLoaded', function() {
    const contractDateInput = document.getElementById('contract_date');
    if (contractDateInput) {
        const today = new Date().toISOString().split('T')[0];
        contractDateInput.value = today;
    }
});

document.getElementById('inn').addEventListener('input', function(e) {
    this.value = this.value.replace(/[^0-9]/g, '');
});
const cityInput = document.getElementById('city');
const rateInput = document.getElementById('hourly_rate');
const hoursInput = document.getElementById('min_hours');

function pluralizeHours(hours) {
    hours = Math.abs(hours);
    
    if (hours >= 11 && hours <= 14) {
        return 'часов';
    }
    
    const lastDigit = hours % 10;
    
    if (lastDigit === 1) {
        return 'час';
    } else if (lastDigit >= 2 && lastDigit <= 4) {
        return 'часа';
    } else {
        return 'часов';
    }
}

function updatePreview() {
    const city = cityInput.value || 'Казань';
    const rate = rateInput.value || '750';
    const hours = hoursInput.value || '2';
    const hoursInt = parseInt(hours) || 2;
    const hoursWord = pluralizeHours(hoursInt);
    
    document.getElementById('preview_city').textContent = city;
    document.getElementById('preview_rate').textContent = rate;
    document.getElementById('preview_hours').textContent = `${hours} ${hoursWord}`;
    
    document.getElementById('preview_rate_text').textContent = numberToText(parseInt(rate));
}

if (cityInput) cityInput.addEventListener('input', updatePreview);
if (rateInput) rateInput.addEventListener('input', updatePreview);
if (hoursInput) hoursInput.addEventListener('input', updatePreview);

function numberToText(num) {
    const units = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять'];
    const tens = ['', 'десять', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто'];
    const hundreds = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот'];
    
    if (num === 750) return 'семьсот пятьдесят';
    if (num === 1000) return 'одна тысяча';
    if (num < 10) return units[num];
    if (num < 100) return tens[Math.floor(num / 10)] + ' ' + units[num % 10];
    if (num < 1000) return hundreds[Math.floor(num / 100)] + ' ' + tens[Math.floor((num % 100) / 10)] + ' ' + units[num % 10];
    
    return num.toString();
}
document.getElementById('checkInnBtn').addEventListener('click', async function() {
    const inn = document.getElementById('inn').value.trim();
    const checkBtn = this;
    const btnText = document.getElementById('checkInnBtnText');
    const btnLoader = document.getElementById('checkInnBtnLoader');
    const companyResult = document.getElementById('companyResult');
    const innError = document.getElementById('innError');
    const innErrorText = document.getElementById('innErrorText');
    companyResult.classList.add('hidden');
    innError.classList.add('hidden');
    
    if (!inn) {
        innErrorText.textContent = 'Введите ИНН';
        innError.classList.remove('hidden');
        return;
    }
    
    if (!/^\d{10,12}$/.test(inn)) {
        innErrorText.textContent = 'ИНН должен содержать 10 или 12 цифр';
        innError.classList.remove('hidden');
        return;
    }
    
    checkBtn.disabled = true;
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/check-inn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ inn: inn })
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('companyName').textContent = result.data.full_name || result.data.name || 'Компания';
            companyResult.classList.remove('hidden');
        } else {
            innErrorText.textContent = result.error || 'Компания не найдена';
            innError.classList.remove('hidden');
        }
        
    } catch (error) {
        innErrorText.textContent = 'Ошибка подключения к серверу';
        innError.classList.remove('hidden');
        console.error('Error:', error);
    } finally {
        checkBtn.disabled = false;
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
    }
});
document.getElementById('generateForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');
    
    // Скрыть предыдущие сообщения
    errorMessage.classList.add('hidden');
    successMessage.classList.add('hidden');
    
    // Показать загрузку
    submitBtn.disabled = true;
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'contract.docx';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            successMessage.textContent = '✓ Договор готов, файл загружен';
            successMessage.classList.remove('hidden');
            
            this.reset();
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('contract_date').value = today;
            
            document.getElementById('companyResult').classList.add('hidden');
            
        } else {
            const error = await response.json();
            errorMessage.textContent = '✕ ' + (error.error || 'Ошибка при генерации');
            errorMessage.classList.remove('hidden');
        }
        
    } catch (error) {
        errorMessage.textContent = '✕ Не удалось подключиться к серверу';
        errorMessage.classList.remove('hidden');
        console.error('Error:', error);
    } finally {
        submitBtn.disabled = false;
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
    }
});

