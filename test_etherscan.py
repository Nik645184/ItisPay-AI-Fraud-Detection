import os
import requests
import json

# Получаем API ключ из переменных окружения
api_key = os.getenv("ETHERSCAN_API_KEY", "YourApiKeyToken")
print(f"Using API key: {api_key[:4]}...{api_key[-4:]} (middle part hidden)")

# Тестовый адрес Ethereum
test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Известный адрес Виталика Бутерина

# Базовый URL Etherscan API
base_url = "https://api.etherscan.io/api"

# Параметры запроса для получения списка транзакций
params = {
    'module': 'account',
    'action': 'txlist',
    'address': test_address,
    'startblock': 0,
    'endblock': 99999999,
    'page': 1,
    'offset': 3,  # Ограничимся 3 транзакциями для теста
    'sort': 'desc',
    'apikey': api_key
}

try:
    # Отправляем запрос к API
    response = requests.get(base_url, params=params)
    
    # Проверяем код ответа
    print(f"Response status code: {response.status_code}")
    
    # Парсим ответ
    data = response.json()
    
    # Выводим статус и сообщение
    print(f"API Status: {data.get('status')}")
    print(f"API Message: {data.get('message')}")
    
    # Проверяем успешность запроса
    if data.get('status') == '1':
        # Выводим количество полученных транзакций
        transactions = data.get('result', [])
        print(f"Received {len(transactions)} transactions")
        
        # Выводим детали первой транзакции, если есть
        if transactions:
            first_tx = transactions[0]
            print("\nFirst transaction details:")
            print(f"Hash: {first_tx.get('hash')}")
            print(f"From: {first_tx.get('from')}")
            print(f"To: {first_tx.get('to')}")
            print(f"Value: {int(first_tx.get('value', '0')) / 10**18} ETH")
    else:
        # Если запрос не успешен, выводим сообщение об ошибке
        print(f"Error: {data.get('message')}")
        
except Exception as e:
    print(f"Exception occurred: {e}")