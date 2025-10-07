// Инициализация даты
document.addEventListener('DOMContentLoaded', function() {
    const contractDateInput = document.getElementById('contract_date');
    if (contractDateInput) {
        const today = new Date().toISOString().split('T')[0];
        contractDateInput.value = today;
    }
    
    // Добавляем первую услугу по умолчанию
    addService();
    
    // Обработчики для дополнительных условий
    setupAdditionalConditions();
});

// Валидация ИНН - только цифры
document.getElementById('inn').addEventListener('input', function(e) {
    this.value = this.value.replace(/[^0-9]/g, '');
});

// ========================================
// УПРАВЛЕНИЕ УСЛУГАМИ
// ========================================

let serviceCounter = 0;

function addService() {
    serviceCounter++;
    const container = document.getElementById('servicesContainer');
    
    const serviceDiv = document.createElement('div');
    serviceDiv.className = 'service-item bg-dark-bg/30 rounded-lg p-4 border border-dark-border/50 relative';
    serviceDiv.dataset.serviceId = serviceCounter;
    
    serviceDiv.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <h4 class="text-md font-medium text-white">Услуга #${serviceCounter}</h4>
            <button 
                type="button" 
                onclick="removeService(${serviceCounter})"
                class="text-red-400 hover:text-red-300 transition-colors p-1"
                title="Удалить услугу"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Название услуги -->
            <div class="md:col-span-2 group">
                <label class="block text-sm font-medium mb-2 text-dark-text">
                    Название услуги *
                </label>
                <input 
                    type="text" 
                    name="service_${serviceCounter}_name"
                    class="service-name w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-white placeholder-dark-muted transition-all"
                    placeholder="погрузочно-разгрузочных работ"
                    required
                >
            </div>
            
            <!-- Город откуда -->
            <div class="group">
                <label class="block text-sm font-medium mb-2 text-dark-text">
                    Город (откуда) *
                </label>
                <input 
                    type="text" 
                    name="service_${serviceCounter}_city_from"
                    class="service-city-from w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-white placeholder-dark-muted transition-all"
                    placeholder="Мытищи"
                    required
                >
            </div>
            
            <!-- Город куда (опционально) -->
            <div class="group">
                <label class="block text-sm font-medium mb-2 text-dark-text">
                    Город (куда) - опционально
                </label>
                <input 
                    type="text" 
                    name="service_${serviceCounter}_city_to"
                    class="service-city-to w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-white placeholder-dark-muted transition-all"
                    placeholder="Москва"
                >
            </div>
            
            <!-- Ставка -->
            <div class="group">
                <label class="block text-sm font-medium mb-2 text-dark-text">
                    Ставка (руб.) *
                </label>
                <input 
                    type="number" 
                    name="service_${serviceCounter}_rate"
                    class="service-rate w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-white placeholder-dark-muted transition-all"
                    placeholder="1300"
                    min="0"
                    required
                >
            </div>
            
            <!-- Единица измерения -->
            <div class="group">
                <label class="block text-sm font-medium mb-2 text-dark-text">
                    Единица измерения *
                </label>
                <select 
                    name="service_${serviceCounter}_unit"
                    class="service-unit w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-white transition-all"
                    required
                >
                    <option value="руб./чел./час">руб./чел./час</option>
                    <option value="руб./авто./час">руб./авто./час</option>
                    <option value="руб./час">руб./час</option>
                    <option value="руб. (фиксированно)">руб. (фиксированно)</option>
                </select>
            </div>
            
            <!-- Минимальный заказ -->
            <div class="group hourly-fields-${serviceCounter}">
                <label class="block text-sm font-medium mb-2 text-dark-text">
                    Минимальный заказ (часы) *
                </label>
                <input 
                    type="number" 
                    name="service_${serviceCounter}_min_hours"
                    class="service-min-hours w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-white placeholder-dark-muted transition-all"
                    placeholder="4"
                    min="1"
                    required
                >
            </div>
            
            <!-- Дополнительные часы -->
            <div class="group hourly-fields-${serviceCounter}">
                <label class="block text-sm font-medium mb-2 text-dark-text">
                    Доп. часы за удаленность
                </label>
                <input 
                    type="number" 
                    name="service_${serviceCounter}_additional_hours"
                    class="service-additional-hours w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-white placeholder-dark-muted transition-all"
                    placeholder="0"
                    min="0"
                    value="0"
                >
            </div>
        </div>
    `;
    
    container.appendChild(serviceDiv);
    
    // Добавляем обработчик для переключения единиц измерения
    const unitSelect = serviceDiv.querySelector('.service-unit');
    const minHoursInput = serviceDiv.querySelector('.service-min-hours');
    const hourlyFields = serviceDiv.querySelectorAll(`.hourly-fields-${serviceCounter}`);
    
    unitSelect.addEventListener('change', function() {
        const isFixed = this.value === 'руб. (фиксированно)';
        
        hourlyFields.forEach(field => {
            if (isFixed) {
                field.style.display = 'none';
                // Убираем required для скрытых полей
                const input = field.querySelector('input');
                if (input) {
                    input.removeAttribute('required');
                    // Устанавливаем допустимое значение для избежания валидации
                    if (input.classList.contains('service-min-hours')) {
                        input.value = '1';
                    } else {
                        input.value = '0';
                    }
                }
            } else {
                field.style.display = '';
                field.classList.remove('hidden');
                // Возвращаем required для минимального заказа
                if (field.querySelector('.service-min-hours')) {
                    minHoursInput.setAttribute('required', 'required');
                    if (minHoursInput.value === '1' || minHoursInput.value === '0') {
                        minHoursInput.value = '4'; // Значение по умолчанию
                    }
                }
            }
        });
        
        updateAllPreviews();
    });
    
    // Добавляем обработчики для обновления превью
    const inputs = serviceDiv.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('input', updateAllPreviews);
    });
    
    updateAllPreviews();
}

function removeService(serviceId) {
    const serviceItem = document.querySelector(`[data-service-id="${serviceId}"]`);
    if (serviceItem) {
        // Проверяем, не последняя ли это услуга
        const servicesCount = document.querySelectorAll('.service-item').length;
        if (servicesCount <= 1) {
            alert('Должна быть хотя бы одна услуга');
            return;
        }
        
        serviceItem.remove();
        updateAllPreviews();
    }
}

// Кнопка добавления услуги
document.getElementById('addServiceBtn').addEventListener('click', addService);

// ========================================
// ПРЕВЬЮ
// ========================================

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

function numberToText(num) {
    const units = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять'];
    const unitsF = ['', 'одна', 'две', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять'];
    const tens = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто'];
    const teens = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать'];
    const hundreds = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот'];
    
    if (num === 0) return 'ноль';
    if (num >= 1000000) return num.toString();
    
    let result = [];
    
    // Тысячи
    const thousands = Math.floor(num / 1000);
    if (thousands > 0) {
        const hundredsT = Math.floor(thousands / 100);
        const tensT = Math.floor((thousands % 100) / 10);
        const unitsT = thousands % 10;
        
        if (hundredsT > 0) result.push(hundreds[hundredsT]);
        
        if (tensT === 1) {
            result.push(teens[unitsT]);
        } else {
            if (tensT > 0) result.push(tens[tensT]);
            if (unitsT > 0) result.push(unitsF[unitsT]);
        }
        
        // Правильное склонение слова "тысяча"
        if (thousands % 100 >= 11 && thousands % 100 <= 14) {
            result.push('тысяч');
        } else if (unitsT === 1) {
            result.push('тысяча');
        } else if (unitsT >= 2 && unitsT <= 4) {
            result.push('тысячи');
        } else if (unitsT >= 5 || unitsT === 0) {
            result.push('тысяч');
        }
    }
    
    // Сотни, десятки, единицы
    const remainder = num % 1000;
    if (remainder > 0) {
        const hundredsR = Math.floor(remainder / 100);
        const tensR = Math.floor((remainder % 100) / 10);
        const unitsR = remainder % 10;
        
        if (hundredsR > 0) result.push(hundreds[hundredsR]);
        
        if (tensR === 1) {
            result.push(teens[unitsR]);
        } else {
            if (tensR > 0) result.push(tens[tensR]);
            if (unitsR > 0) result.push(units[unitsR]);
        }
    }
    
    return result.filter(w => w).join(' ');
}

function updateAllPreviews() {
    const previewContainer = document.getElementById('servicesPreview');
    const serviceItems = document.querySelectorAll('.service-item');
    
    let previewHTML = '';
    
    serviceItems.forEach((item, index) => {
        const name = item.querySelector('.service-name').value || 'услуг';
        const cityFrom = item.querySelector('.service-city-from').value || 'Город';
        const cityTo = item.querySelector('.service-city-to').value;
        const rate = parseInt(item.querySelector('.service-rate').value) || 0;
        const unit = item.querySelector('.service-unit').value;
        const minHours = parseInt(item.querySelector('.service-min-hours').value) || 0;
        const additionalHours = parseInt(item.querySelector('.service-additional-hours').value) || 0;
        
        const rateText = numberToText(rate);
        const isFixed = unit === 'руб. (фиксированно)';
        
        // Формируем текст города
        let cityText = '';
        if (cityTo) {
            // Если есть откуда и куда - используем "из ... в ..."
            cityText = `из г. ${cityFrom} в г. ${cityTo}`;
        } else {
            // Если только один город - просто "в г. X"
            cityText = `в г. ${cityFrom}`;
        }
        
        let servicePreview = '';
        
        if (isFixed) {
            // Для фиксированной ставки не упоминаем часы
            servicePreview = `Стоимость ${name} ${cityText} составит ${rate} (${rateText}) рублей.`;
        } else {
            // Для почасовой оплаты
            const hoursWord = pluralizeHours(minHours);
            servicePreview = `Стоимость ${name} ${cityText} составит ${rate} (${rateText}) ${unit}, минимальный заказ ${minHours} ${hoursWord}.`;
            
            if (additionalHours > 0) {
                const addHoursWord = pluralizeHours(additionalHours);
                servicePreview += ` Оплачивается ${additionalHours} ${addHoursWord === 'час' ? 'дополнительный час' : addHoursWord === 'часа' ? 'дополнительных часа' : 'дополнительных часов'} в размере ${rate} (${rateText}) ${unit} к отработанному времени за удаленность.`;
            }
        }
        
        previewHTML += `<p class="text-blue-200">${servicePreview}</p>`;
    });
    
    // Добавляем упаковочные материалы
    const includePacking = document.getElementById('include_packing').checked;
    if (includePacking) {
        const packingPercentage = document.getElementById('packing_percentage').value || 50;
        previewHTML += `<p class="text-blue-200">Упаковочный материал оплачивается по чеку, так же оплачивается ${packingPercentage}% от суммы в чеке.</p>`;
    }
    
    // Добавляем предоплату
    const includePrepayment = document.getElementById('include_prepayment').checked;
    if (includePrepayment) {
        const prepaymentAmount = parseInt(document.getElementById('prepayment_amount').value) || 0;
        if (prepaymentAmount > 0) {
            const prepaymentText = numberToText(prepaymentAmount);
            previewHTML += `<p class="text-blue-200">Оплачивается предоплата в размере ${prepaymentAmount} (${prepaymentText}) рублей.</p>`;
        }
    }
    
    previewContainer.innerHTML = previewHTML || '<p class="text-dark-muted">Заполните поля услуг для просмотра</p>';
}

// ========================================
// ДОПОЛНИТЕЛЬНЫЕ УСЛОВИЯ
// ========================================

function setupAdditionalConditions() {
    const includePacking = document.getElementById('include_packing');
    const packingFields = document.getElementById('packingFields');
    const packingPercentage = document.getElementById('packing_percentage');
    
    const includePrepayment = document.getElementById('include_prepayment');
    const prepaymentFields = document.getElementById('prepaymentFields');
    const prepaymentAmount = document.getElementById('prepayment_amount');
    
    includePacking.addEventListener('change', function() {
        if (this.checked) {
            packingFields.classList.remove('hidden');
        } else {
            packingFields.classList.add('hidden');
        }
        updateAllPreviews();
    });
    
    includePrepayment.addEventListener('change', function() {
        if (this.checked) {
            prepaymentFields.classList.remove('hidden');
        } else {
            prepaymentFields.classList.add('hidden');
        }
        updateAllPreviews();
    });
    
    packingPercentage.addEventListener('input', updateAllPreviews);
    prepaymentAmount.addEventListener('input', updateAllPreviews);
}

// ========================================
// ПРОВЕРКА ИНН
// ========================================

const checkInnBtn = document.getElementById('checkInnBtn');
if (checkInnBtn) {
    checkInnBtn.addEventListener('click', async function() {
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
            innErrorText.textContent = 'введите ИНН';
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
            } else if (result.suggest_backup) {
                innErrorText.innerHTML = `
                    <div class="space-y-3">
                        <p>${result.message}</p>
                        <p class="text-orange-300"><strong>Доступен резервный сервис API-FNS</strong></p>
                        <p class="text-xs text-orange-200">⚠️ Ограничение: 100 запросов. Использовать только при необходимости.</p>
                        <button type="button" onclick="useBackupApi('${inn}')" 
                                class="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium transition-colors">
                            Использовать резервный сервис
                        </button>
                    </div>
                `;
                innError.classList.remove('hidden');
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
}

// Функция для использования резервного API
window.useBackupApi = async function(inn) {
    const innError = document.getElementById('innError');
    const innErrorText = document.getElementById('innErrorText');
    const companyResult = document.getElementById('companyResult');
    
    innError.classList.add('hidden');
    companyResult.classList.add('hidden');
    
    innErrorText.innerHTML = `
        <div class="flex items-center gap-3">
            <svg class="animate-spin h-5 w-5 text-orange-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Поиск в резервном сервисе...</span>
        </div>
    `;
    innError.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/check-inn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ inn: inn, use_api_fns: true })
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('companyName').textContent = result.data.full_name || result.data.name || 'Компания';
            companyResult.classList.remove('hidden');
            innError.classList.add('hidden');
        } else {
            innErrorText.textContent = result.error || 'Компания не найдена в резервном сервисе';
            innError.classList.remove('hidden');
        }
        
    } catch (error) {
        innErrorText.textContent = 'Ошибка подключения к резервному сервису';
        innError.classList.remove('hidden');
        console.error('Error:', error);
    }
};

// ========================================
// ОТПРАВКА ФОРМЫ
// ========================================

const generateForm = document.getElementById('generateForm');
if (generateForm) {
    generateForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Убираем required у всех скрытых полей перед отправкой
        const hiddenRequiredFields = this.querySelectorAll('input[required]');
        hiddenRequiredFields.forEach(field => {
            if (field.offsetParent === null || field.style.display === 'none') {
                field.removeAttribute('required');
            }
        });
        
        const formData = new FormData();
        
        // Базовые поля
        formData.append('inn', document.getElementById('inn').value);
        formData.append('contract_number', document.getElementById('contract_number').value);
        formData.append('contract_date', document.getElementById('contract_date').value);
        formData.append('services', document.getElementById('services').value);
        formData.append('executor_profile_id', document.getElementById('executor_profile_id').value);
        
        // Банковские реквизиты (опционально)
        const bankDetailsField = document.getElementById('bank_details');
        if (bankDetailsField) {
            formData.append('bank_details', bankDetailsField.value);
        }
        
        // Собираем все услуги
        const serviceItems = document.querySelectorAll('.service-item');
        const servicesData = [];
        
        serviceItems.forEach(item => {
            const serviceData = {
                name: item.querySelector('.service-name').value,
                city_from: item.querySelector('.service-city-from').value,
                city_to: item.querySelector('.service-city-to').value,
                rate: item.querySelector('.service-rate').value,
                unit: item.querySelector('.service-unit').value,
                min_hours: item.querySelector('.service-min-hours').value,
                additional_hours: item.querySelector('.service-additional-hours').value || '0'
            };
            servicesData.push(serviceData);
        });
        
        formData.append('pricing_services', JSON.stringify(servicesData));
        
        // Дополнительные условия
        if (document.getElementById('include_packing').checked) {
            formData.append('packing_percentage', document.getElementById('packing_percentage').value);
        }
        
        if (document.getElementById('include_prepayment').checked) {
            formData.append('prepayment_amount', document.getElementById('prepayment_amount').value);
        }
        
        const submitBtn = document.getElementById('submitBtn');
        const btnText = document.getElementById('btnText');
        const btnLoader = document.getElementById('btnLoader');
        const errorMessage = document.getElementById('errorMessage');
        const successMessage = document.getElementById('successMessage');
        
        errorMessage.classList.add('hidden');
        successMessage.classList.add('hidden');
        
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
                
                // Сбрасываем форму, но оставляем одну услугу
                this.reset();
                const today = new Date().toISOString().split('T')[0];
                document.getElementById('contract_date').value = today;
                document.getElementById('companyResult').classList.add('hidden');
                
                // Очищаем услуги и добавляем одну новую
                document.getElementById('servicesContainer').innerHTML = '';
                serviceCounter = 0;
                addService();
                
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
}
