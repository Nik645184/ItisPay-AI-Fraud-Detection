import pandas as pd
import numpy as np
from faker import Faker
import random
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Initialize faker
fake = Faker()

def generate_synthetic_fiat_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic fiat transaction data
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        pd.DataFrame: Generated synthetic data
    """
    logger.info(f"Generating {n_samples} synthetic fiat transactions")
    
    # List of currencies and countries
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'HKD', 'NZD']
    countries = ['US', 'GB', 'DE', 'FR', 'JP', 'AU', 'CA', 'CH', 'CN', 'HK', 'NZ', 'RU', 'IN', 'BR', 'NG']
    
    # Generate base data
    data = []
    for _ in range(n_samples):
        # Base legitimate transaction
        card_country = random.choice(countries)
        geo_ip = card_country  # Most transactions have matching country
        
        # Introduce some anomalies (10% of transactions)
        if random.random() < 0.1:
            # Geo mismatch
            geo_ip = random.choice([c for c in countries if c != card_country])
        
        # Generate transaction amount (log-normal distribution for more realistic amounts)
        amount = np.exp(np.random.normal(5, 1.5))  # Centered around ~150 with long tail
        
        # Create transaction
        transaction = {
            'amount': round(amount, 2),
            'currency': random.choice(currencies),
            'card_country': card_country,
            'geo_ip': geo_ip
        }
        data.append(transaction)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create some more complex anomalies
    # 5% of transactions with unusual amounts
    unusual_indices = np.random.choice(
        range(n_samples), 
        size=int(n_samples * 0.05), 
        replace=False
    )
    df.loc[unusual_indices, 'amount'] = np.exp(np.random.normal(9, 1))  # Much larger amounts
    
    return df

def generate_synthetic_crypto_addresses(n_addresses: int = 100) -> List[str]:
    """
    Generate synthetic Ethereum addresses
    
    Args:
        n_addresses: Number of addresses to generate
        
    Returns:
        List[str]: List of Ethereum addresses
    """
    addresses = []
    for _ in range(n_addresses):
        address = "0x" + ''.join(random.choices('0123456789abcdef', k=40))
        addresses.append(address)
    return addresses

def generate_mixed_risk_addresses(n_addresses: int = 100) -> Dict[str, float]:
    """
    Generate addresses with associated risk scores
    
    Args:
        n_addresses: Number of addresses to generate
        
    Returns:
        Dict[str, float]: Dictionary mapping addresses to risk scores
    """
    addresses = generate_synthetic_crypto_addresses(n_addresses)
    risk_scores = {}
    
    for addr in addresses:
        # Assign random risk score (mostly low, some high)
        if random.random() < 0.8:  # 80% low risk
            risk = random.uniform(0, 0.3)
        else:  # 20% high risk
            risk = random.uniform(0.7, 1.0)
        risk_scores[addr] = risk
    
    return risk_scores

def generate_synthetic_crypto_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic crypto transaction data
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        pd.DataFrame: Generated synthetic data
    """
    logger.info(f"Generating {n_samples} synthetic crypto transactions")
    
    # Generate addresses
    addresses = generate_synthetic_crypto_addresses(n_samples // 10)  # Reuse addresses
    
    # Currencies and their approximate values in USD
    crypto_currencies = {
        'ETH': 2500,
        'BTC': 40000,
        'USDT': 1,
        'USDC': 1,
        'BNB': 400,
        'XRP': 0.5,
        'SOL': 100,
        'ADA': 0.4,
        'DOGE': 0.1,
        'MATIC': 0.8
    }
    
    # Generate transactions
    data = []
    for _ in range(n_samples):
        currency = random.choice(list(crypto_currencies.keys()))
        base_value = crypto_currencies[currency]
        
        # Generate amount (in the cryptocurrency)
        if currency in ['USDT', 'USDC']:
            # Stablecoins often have larger transaction amounts
            amount = round(random.lognormvariate(5, 2), 2)
        elif currency in ['BTC', 'ETH']:
            # Major cryptos often have smaller fractional amounts
            amount = round(random.lognormvariate(-1, 1.5), 6)
        else:
            # Other altcoins
            amount = round(random.lognormvariate(2, 2), 4)
        
        transaction = {
            'address': random.choice(addresses),
            'currency': currency,
            'amount': amount,
            'usd_value': round(amount * base_value, 2)
        }
        data.append(transaction)
    
    return pd.DataFrame(data)

def generate_sample_transaction() -> Dict[str, Any]:
    """
    Generate a sample transaction combining fiat and crypto data
    
    Returns:
        Dict[str, Any]: Sample transaction data
    """
    # Generate country info
    card_country = random.choice(['US', 'GB', 'DE', 'FR', 'JP', 'AU', 'CA'])
    
    # 85% chance of geo matching card country
    if random.random() < 0.85:
        geo_ip = card_country
    else:
        geo_ip = random.choice(['US', 'GB', 'DE', 'FR', 'JP', 'RU', 'NG', 'IN'])
    
    # Generate amount (log-normal for realistic amounts)
    amount = round(np.exp(np.random.normal(5, 1.5)), 2)
    
    # Generate crypto part
    crypto = {
        'address': "0x" + ''.join(random.choices('0123456789abcdef', k=40)),
        'currency': random.choice(['ETH', 'BTC', 'USDT', 'USDC']),
        'amount': round(random.lognormvariate(0, 1), 6)
    }
    
    # Create transaction
    transaction = {
        'fiat': {
            'amount': amount,
            'currency': random.choice(['USD', 'EUR', 'GBP']),
            'card_country': card_country,
            'geo_ip': geo_ip
        },
        'crypto': crypto
    }
    
    return transaction

if __name__ == "__main__":
    # Test data generation
    fiat_df = generate_synthetic_fiat_data(10)
    crypto_df = generate_synthetic_crypto_data(10)
    
    print("Sample Fiat Data:")
    print(fiat_df.head())
    
    print("\nSample Crypto Data:")
    print(crypto_df.head())
    
    print("\nSample Combined Transaction:")
    print(generate_sample_transaction())
