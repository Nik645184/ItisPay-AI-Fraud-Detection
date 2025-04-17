"""
ItisPay Fraud Detection - USDC Analyzer
This module analyzes USDC (ERC-20) transactions on Ethereum blockchain
"""

import os
import logging
import requests
import time
import json
from typing import Dict, Any, List, Tuple, Optional
from risky_addresses import RISKY_ADDRESSES_WITH_SCORES

# Configure logging
logger = logging.getLogger(__name__)

# Constants
USDC_CONTRACT_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC contract on Ethereum
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"

class EtherscanRateLimiter:
    """Class to handle rate limiting for Etherscan API"""
    def __init__(self, requests_per_second: int = 5):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Maximum number of requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        
    def wait_if_needed(self):
        """Wait if necessary to respect the rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_interval:
            # Need to wait
            wait_time = self.min_interval - elapsed
            time.sleep(wait_time)
            
        # Update last request time
        self.last_request_time = time.time()

def analyze_usdc_erc20_transactions(address: str, etherscan_api_key: str = None) -> float:
    """
    Analyze USDC (ERC-20) transactions for a given Ethereum address
    
    Args:
        address: Ethereum address to analyze
        etherscan_api_key: API key for Etherscan (optional, uses environment variable if not provided)
        
    Returns:
        float: Risk score (0-1) based on percentage of transactions with risky addresses
    """
    # Use provided API key or get from environment
    api_key = etherscan_api_key or os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        logger.error("No Etherscan API key provided")
        return 0.0
    
    # Initialize rate limiter
    rate_limiter = EtherscanRateLimiter()
    
    # Get USDC transactions for the address
    transactions = get_usdc_transactions(address, api_key, rate_limiter)
    
    if not transactions:
        logger.info(f"No USDC transactions found for address: {address}")
        return 0.0
    
    # Analyze transactions
    return calculate_usdc_risk(transactions)

def get_usdc_transactions(address: str, api_key: str, rate_limiter: EtherscanRateLimiter) -> Optional[List[Dict[str, Any]]]:
    """
    Get USDC token transactions for an address using Etherscan API
    
    Args:
        address: Ethereum address to analyze
        api_key: Etherscan API key
        rate_limiter: Rate limiter instance
        
    Returns:
        Optional[List[Dict[str, Any]]]: List of USDC transactions or None if error
    """
    try:
        logger.info(f"Fetching USDC transactions for address: {address}")
        
        # Respect rate limits
        rate_limiter.wait_if_needed()
        
        # Query ERC20 transactions for USDC contract
        params = {
            'module': 'account',
            'action': 'tokentx',
            'contractaddress': USDC_CONTRACT_ADDRESS, 
            'address': address,
            'sort': 'desc',
            'apikey': api_key
        }
        
        response = requests.get(ETHERSCAN_BASE_URL, params=params)
        
        if response.status_code != 200:
            logger.error(f"API request failed with status code: {response.status_code}")
            return None
        
        data = response.json()
        
        if data['status'] != '1':
            logger.warning(f"API returned error: {data.get('message', 'Unknown error')}")
            return None
        
        # Return the transactions
        return data['result']
        
    except Exception as e:
        logger.error(f"Error fetching USDC transactions: {e}")
        return None

def calculate_usdc_risk(transactions: List[Dict[str, Any]]) -> float:
    """
    Calculate risk score based on USDC transactions
    
    Args:
        transactions: List of USDC transactions from Etherscan
        
    Returns:
        float: Risk score (0-1) based on percentage of transactions with risky addresses
    """
    if not transactions:
        return 0.0
    
    total_transactions = len(transactions)
    risky_transactions = 0
    
    # Analyze each transaction
    for tx in transactions:
        sender = tx.get('from', '').lower()
        receiver = tx.get('to', '').lower()
        
        # Check if sender or receiver is in the risky addresses list
        if sender in RISKY_ADDRESSES_WITH_SCORES or receiver in RISKY_ADDRESSES_WITH_SCORES:
            risky_transactions += 1
    
    # Calculate percentage of risky transactions
    risky_percentage = (risky_transactions / total_transactions) * 100
    logger.info(f"USDC analysis: {risky_transactions}/{total_transactions} transactions ({risky_percentage:.2f}%) linked to risky addresses")
    
    # If more than 10% of transactions are with risky addresses, return risk score
    if risky_percentage > 10:
        # Convert percentage to risk score (0-1)
        # Example: 20% -> 0.2, 50% -> 0.5, etc.
        risk_score = min(risky_percentage / 100, 1.0)
        return risk_score
    
    return 0.0

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample address
    sample_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    
    risk_score = analyze_usdc_erc20_transactions(sample_address)
    print(f"USDC Risk Score for {sample_address}: {risk_score}")