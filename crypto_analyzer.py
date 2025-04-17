import requests
import pandas as pd
import time
from typing import Dict, Any, List, Tuple, Optional
import logging
from config import ETHERSCAN_API_KEY, ETHERSCAN_RATE_LIMIT
from utils import is_valid_eth_address, normalize_score
from risky_addresses import KNOWN_MIXER_ADDRESSES, KNOWN_DARKNET_ADDRESSES

# Configure logging
logger = logging.getLogger(__name__)

class EtherscanRateLimiter:
    """Class to handle rate limiting for Etherscan API"""
    
    def __init__(self, requests_per_second: int = ETHERSCAN_RATE_LIMIT):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect the rate limit"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # If less than the minimum interval has passed, wait
        if time_since_last_request < (1.0 / self.requests_per_second):
            wait_time = (1.0 / self.requests_per_second) - time_since_last_request
            time.sleep(wait_time)
        
        # Update the last request time
        self.last_request_time = time.time()

class CryptoTransactionAnalyzer:
    """
    Analyzes crypto transactions using Etherscan API and known risky addresses
    """
    
    def __init__(self, api_key: str = ETHERSCAN_API_KEY):
        """
        Initialize the crypto transaction analyzer
        
        Args:
            api_key: Etherscan API key
        """
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"
        self.rate_limiter = EtherscanRateLimiter()
        
        # Cache for previous address analyses to reduce API calls
        self.address_cache = {}
        
        logger.info("Crypto Transaction Analyzer initialized")
    
    def analyze(self, transaction: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Analyze a crypto transaction for risks
        
        Args:
            transaction: Dictionary with transaction details
                Required fields: 'address', 'currency', 'amount'
                
        Returns:
            Tuple[float, List[str]]: Risk score (0-1) and list of alerts
        """
        logger.info(f"Analyzing crypto transaction: {transaction}")
        
        # Initialize risks and alerts
        risk_score = 0.0
        alerts = []
        
        # Validate transaction data
        if not self._validate_transaction(transaction):
            logger.warning("Invalid crypto transaction data")
            return 0.8, ["Invalid crypto transaction data"]
        
        # Check if the address is known risky
        address_risk, address_alerts = self._check_known_risky_address(transaction['address'])
        if address_alerts:
            alerts.extend(address_alerts)
            risk_score = max(risk_score, address_risk)
        
        # Get transactions for this address
        transactions = self._get_address_transactions(transaction['address'], transaction['currency'])
        
        # If we have transactions, analyze them
        if transactions:
            # Check for mixer interaction
            mixer_risk, mixer_alerts = self._check_mixer_interaction(transactions)
            if mixer_alerts:
                alerts.extend(mixer_alerts)
                risk_score = max(risk_score, mixer_risk)
            
            # Check transaction patterns
            pattern_risk, pattern_alerts = self._analyze_transaction_patterns(transactions)
            if pattern_alerts:
                alerts.extend(pattern_alerts)
                risk_score = max(risk_score, pattern_risk)
        else:
            # No transaction history found - provide more specific message
            if transaction['currency'] != 'ETH':
                alerts.append(f"No Ethereum transaction history found for this {transaction['currency']} address")
            else:
                alerts.append("No Ethereum transaction history found")
            
            # Assign moderate risk for no history
            risk_score = max(risk_score, 0.4)
        
        logger.info(f"Crypto analysis result: score={risk_score}, alerts={alerts}")
        return risk_score, alerts
    
    def _validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Validate that the transaction contains the required fields
        
        Args:
            transaction: Dictionary with transaction details
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['address', 'currency', 'amount']
        for field in required_fields:
            if field not in transaction:
                logger.warning(f"Missing required field in crypto transaction: {field}")
                return False
        
        # Validate Ethereum address format
        if not is_valid_eth_address(transaction['address']):
            logger.warning(f"Invalid Ethereum address format: {transaction['address']}")
            return False
        
        # Validate amount is numeric
        try:
            float(transaction['amount'])
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount format in crypto transaction: {transaction['amount']}")
            return False
        
        # Process different cryptocurrencies
        cryptocurrency = transaction['currency']
        if cryptocurrency != 'ETH':
            logger.info(f"Processing {cryptocurrency} transaction with Ethereum address verification")
            
            # We support all currencies that use Ethereum-compatible addresses
            supported_currencies = ['ETH', 'USDT', 'USDC', 'BTC', 'DAI', 'LINK', 'UNI']
            if cryptocurrency not in supported_currencies:
                logger.warning(f"Cryptocurrency {cryptocurrency} may have limited analysis support")
        
        return True
    
    def _check_known_risky_address(self, address: str) -> Tuple[float, List[str]]:
        """
        Check if an address is in our list of known risky addresses
        
        Args:
            address: Ethereum address to check
            
        Returns:
            Tuple[float, List[str]]: Risk score and alerts
        """
        risk_score = 0.0
        alerts = []
        
        # Check for mixer addresses
        if address.lower() in KNOWN_MIXER_ADDRESSES:
            risk_score = 0.9
            alerts.append(f"Address is a known mixer: {address}")
        
        # Check for darknet addresses
        if address.lower() in KNOWN_DARKNET_ADDRESSES:
            risk_score = 1.0
            alerts.append(f"Address is associated with darknet markets: {address}")
        
        return risk_score, alerts
    
    def _get_address_transactions(self, address: str, currency: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent transactions for an address using Etherscan API
        
        Args:
            address: Ethereum address
            currency: Cryptocurrency (ETH, etc.)
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of transactions or None if error
        """
        # Check cache first
        if address in self.address_cache:
            logger.info(f"Using cached transaction data for address: {address}")
            return self.address_cache[address]
        
        # Handle different cryptocurrencies
        if currency != 'ETH':
            logger.info(f"Non-ETH currency detected: {currency}. Using compatible ETH address lookup.")
            # For non-ETH currencies, we'll still check the address using Etherscan if it's a valid ETH address
            # But we note that it's a different currency
            if not is_valid_eth_address(address):
                logger.warning(f"Invalid Ethereum address format for {currency} lookup: {address}")
                return None
        
        try:
            logger.info(f"Fetching transactions for address: {address}")
            
            # Respect rate limits
            self.rate_limiter.wait_if_needed()
            
            # Query normal transactions
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'sort': 'desc',
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status code: {response.status_code}")
                return None
            
            data = response.json()
            
            if data['status'] != '1':
                logger.warning(f"API returned error: {data['message']}")
                return None
            
            # Get internal transactions too
            self.rate_limiter.wait_if_needed()
            
            params['action'] = 'txlistinternal'
            response_internal = requests.get(self.base_url, params=params)
            
            if response_internal.status_code == 200:
                data_internal = response_internal.json()
                if data_internal['status'] == '1':
                    # Combine both types of transactions
                    all_transactions = data['result'] + data_internal['result']
                else:
                    all_transactions = data['result']
            else:
                all_transactions = data['result']
            
            # Cache the results
            self.address_cache[address] = all_transactions
            
            return all_transactions
            
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return None
    
    def _check_mixer_interaction(self, transactions: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """
        Check if the address has interacted with known mixer addresses
        
        Args:
            transactions: List of transactions
            
        Returns:
            Tuple[float, List[str]]: Risk score and alerts
        """
        risk_score = 0.0
        alerts = []
        
        if not transactions:
            return risk_score, alerts
        
        # Count transactions with known mixers
        mixer_transactions = 0
        mixer_value = 0.0
        total_value = 0.0
        
        for tx in transactions:
            try:
                # Get the counterparty address
                counterparty = None
                if 'from' in tx and tx['from'].lower() in KNOWN_MIXER_ADDRESSES:
                    counterparty = tx['from'].lower()
                elif 'to' in tx and tx['to'] and tx['to'].lower() in KNOWN_MIXER_ADDRESSES:
                    counterparty = tx['to'].lower()
                
                # Calculate value - safely parse value to avoid integer overflow
                try:
                    raw_value = tx.get('value', '0')
                    # Ensure we're dealing with a string to prevent integer overflow
                    if not isinstance(raw_value, str):
                        raw_value = str(raw_value)
                    # Convert from wei to ETH, safely handling large numbers
                    value = float(raw_value) / 1e18
                    total_value += value
                except (ValueError, OverflowError) as e:
                    logger.warning(f"Error converting transaction value: {e}")
                    value = 0
                
                if counterparty:
                    mixer_transactions += 1
                    mixer_value += value
            except Exception as e:
                logger.error(f"Error processing transaction: {e}")
        
        # Calculate percentage of value from/to mixers
        if total_value > 0:
            mixer_percentage = (mixer_value / total_value) * 100
            
            if mixer_percentage > 0:
                # Risk score based on percentage
                if mixer_percentage > 50:
                    risk_score = 1.0  # Extreme risk
                elif mixer_percentage > 20:
                    risk_score = 0.8  # High risk
                elif mixer_percentage > 5:
                    risk_score = 0.6  # Medium risk
                else:
                    risk_score = 0.4  # Low-medium risk
                
                alerts.append(f"Crypto: {mixer_percentage:.1f}% from/to mixer ({mixer_transactions} transactions)")
        
        return risk_score, alerts
    
    def _analyze_transaction_patterns(self, transactions: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """
        Analyze transaction patterns for suspicious behavior
        
        Args:
            transactions: List of transactions
            
        Returns:
            Tuple[float, List[str]]: Risk score and alerts
        """
        risk_score = 0.0
        alerts = []
        
        if not transactions:
            return risk_score, alerts
        
        # Check for suspicious patterns
        try:
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(transactions)
            
            # Check account age
            if len(df) > 0 and 'timeStamp' in df.columns:
                df['timeStamp'] = pd.to_numeric(df['timeStamp'])
                newest_tx = df['timeStamp'].max()
                oldest_tx = df['timeStamp'].min()
                account_age_days = (newest_tx - oldest_tx) / (60 * 60 * 24)
                
                if account_age_days < 1:
                    risk_score = max(risk_score, 0.7)
                    alerts.append(f"New account: less than 1 day old")
                elif account_age_days < 7:
                    risk_score = max(risk_score, 0.4)
                    alerts.append(f"New account: less than 7 days old")
            
            # Check transaction count
            if len(df) == 1:
                risk_score = max(risk_score, 0.3)
                alerts.append("Single transaction history")
            
            # Check for peeling chains (a chain of transactions decreasing in value)
            # This is a simplified check - a real implementation would be more sophisticated
            if len(df) >= 3 and 'value' in df.columns:
                # Convert values to numeric
                df['value'] = pd.to_numeric(df['value'])
                
                # Sort by timestamp
                if 'timeStamp' in df.columns:
                    df = df.sort_values('timeStamp')
                
                # Check for decreasing values
                values = df['value'].tolist()
                decreasing_count = sum(values[i] > values[i+1] for i in range(len(values)-1))
                
                if decreasing_count >= 2 and decreasing_count > len(values) * 0.5:
                    risk_score = max(risk_score, 0.6)
                    alerts.append("Possible peeling chain detected (decreasing transaction values)")
            
            # Add more pattern analyses as needed
            
        except Exception as e:
            logger.error(f"Error analyzing transaction patterns: {e}")
            # Добавляем информативное сообщение в список предупреждений вместо прекращения анализа
            alerts.append(f"Не удалось выполнить полный анализ транзакций: {str(e)}")
            # Устанавливаем умеренный уровень риска, так как мы не смогли выполнить полный анализ
            risk_score = max(risk_score, 0.3)
        
        return risk_score, alerts

if __name__ == "__main__":
    # Example usage
    analyzer = CryptoTransactionAnalyzer()
    
    # Test with a sample transaction
    sample_transaction = {
        'address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',  # Example address
        'currency': 'ETH',
        'amount': 0.1
    }
    
    risk_score, alerts = analyzer.analyze(sample_transaction)
    print(f"Risk Score: {risk_score}")
    print(f"Alerts: {alerts}")
