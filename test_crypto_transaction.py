from crypto_analyzer import CryptoTransactionAnalyzer
import os

# Создаем экземпляр анализатора криптовалютных транзакций
analyzer = CryptoTransactionAnalyzer()

# Тестируем правильную ETH транзакцию
eth_transaction = {
    'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  # Адрес Виталика Бутерина
    'currency': 'ETH',
    'amount': 1.0
}

print("======== Testing ETH Transaction ========")
risk_score, alerts = analyzer.analyze(eth_transaction)
print(f"Risk Score: {risk_score}")
print(f"Alerts: {alerts}")
print()

# Тестируем BTC транзакцию (которая не поддерживается)
btc_transaction = {
    'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  # Используем ETH адрес, но с BTC валютой
    'currency': 'BTC',
    'amount': 0.1
}

print("======== Testing BTC Transaction ========")
risk_score, alerts = analyzer.analyze(btc_transaction)
print(f"Risk Score: {risk_score}")
print(f"Alerts: {alerts}")