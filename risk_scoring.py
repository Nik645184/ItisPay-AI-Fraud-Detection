from typing import Dict, Any, List, Tuple
import logging
import os
from config import FIAT_WEIGHT, CRYPTO_WEIGHT, USDC_WEIGHT
from utils import normalize_score, get_risk_level
from fiat_analyzer import FiatTransactionAnalyzer
from crypto_analyzer import CryptoTransactionAnalyzer
from usdc_analyzer import analyze_usdc_erc20_transactions

# Configure logging
logger = logging.getLogger(__name__)

class RiskScorer:
    """
    Handles cross-channel risk scoring by combining fiat and crypto risks
    """
    
    def __init__(self):
        """Initialize the risk scorer with analyzers"""
        self.fiat_analyzer = FiatTransactionAnalyzer()
        self.crypto_analyzer = CryptoTransactionAnalyzer()
        logger.info("Risk Scorer initialized")
    
    def train_models(self, fiat_data=None):
        """
        Train the underlying models with historical data
        
        Args:
            fiat_data: DataFrame with historical fiat transactions
        """
        if fiat_data is not None:
            logger.info("Training fiat transaction analyzer")
            self.fiat_analyzer.train(fiat_data)
    
    def analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a transaction with both fiat and crypto components
        
        Args:
            transaction: Dictionary with 'fiat' and 'crypto' components
                Example: {
                    'fiat': {'amount': 1000, 'currency': 'USD', 'card_country': 'US', 'geo_ip': 'NG'},
                    'crypto': {'address': '0x123...', 'currency': 'ETH', 'amount': 0.1}
                }
        
        Returns:
            Dict[str, Any]: Analysis results with risk score and alerts
        """
        logger.info(f"Analyzing transaction: {transaction}")
        
        # Initialize results
        results = {
            'risk_score': 0,
            'risk_level': 'Unknown',
            'alerts': [],
            'fiat_risk': None,
            'crypto_risk': None,
            'usdc_risk': None
        }
        
        # Analyze fiat component if present
        fiat_risk_score = 0
        fiat_alerts = []
        if 'fiat' in transaction and transaction['fiat']:
            fiat_risk_score, fiat_alerts = self.fiat_analyzer.analyze(transaction['fiat'])
            results['fiat_risk'] = {
                'score': round(fiat_risk_score * 100, 2),
                'alerts': fiat_alerts
            }
            
            # Add prefix to fiat alerts for combined list
            fiat_alerts = [f"Fiat: {alert}" for alert in fiat_alerts]
        
        # Analyze crypto component if present
        crypto_risk_score = 0
        crypto_alerts = []
        has_crypto = False
        if 'crypto' in transaction and transaction['crypto']:
            has_crypto = True
            crypto_risk_score, crypto_alerts = self.crypto_analyzer.analyze(transaction['crypto'])
            results['crypto_risk'] = {
                'score': round(crypto_risk_score * 100, 2),
                'alerts': crypto_alerts
            }
            
            # Add prefix to crypto alerts for combined list
            crypto_alerts = [f"Crypto: {alert}" for alert in crypto_alerts]
        
        # Analyze USDC transactions if crypto component is present
        usdc_risk_score = 0
        usdc_alerts = []
        has_usdc_analysis = False
        if has_crypto and transaction['crypto'].get('currency') == 'USDC':
            # Get the crypto address for USDC analysis
            address = transaction['crypto'].get('address')
            if address:
                # Analyze USDC transactions
                etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")
                usdc_risk_score = analyze_usdc_erc20_transactions(address, etherscan_api_key)
                
                # Generate alert if risk is detected
                if usdc_risk_score > 0:
                    usdc_alerts = [f"USDC transactions linked to risky addresses: {usdc_risk_score * 100:.1f}%"]
                    has_usdc_analysis = True
                    
                # Store USDC risk results
                results['usdc_risk'] = {
                    'score': round(usdc_risk_score * 100, 2),
                    'alerts': usdc_alerts
                }
                
                # Add prefix to USDC alerts for combined list
                usdc_alerts = [f"USDC: {alert}" for alert in usdc_alerts]
        
        # Calculate combined risk score with USDC analysis
        combined_risk = self._calculate_combined_risk_with_usdc(
            fiat_risk_score,
            crypto_risk_score,
            usdc_risk_score,
            'fiat' in transaction and transaction['fiat'],
            has_crypto,
            has_usdc_analysis
        )
        
        # Convert to 0-100 scale
        normalized_risk = round(combined_risk * 100, 2)
        results['risk_score'] = normalized_risk
        results['risk_level'] = get_risk_level(normalized_risk)
        
        # Combine alerts
        results['alerts'] = fiat_alerts + crypto_alerts + usdc_alerts
        
        logger.info(f"Risk analysis complete: score={normalized_risk}, level={results['risk_level']}")
        return results
    
    def _calculate_combined_risk_with_usdc(self, fiat_risk: float, crypto_risk: float, usdc_risk: float, 
                                    has_fiat: bool, has_crypto: bool, has_usdc: bool) -> float:
        """
        Calculate the combined risk score based on fiat, crypto, and USDC components
        
        Args:
            fiat_risk: Risk score from fiat analysis (0-1)
            crypto_risk: Risk score from crypto analysis (0-1)
            usdc_risk: Risk score from USDC analysis (0-1)
            has_fiat: Whether the transaction has a fiat component
            has_crypto: Whether the transaction has a crypto component
            has_usdc: Whether the transaction has a USDC analysis component
        
        Returns:
            float: Combined risk score (0-1)
        """
        if has_fiat and has_crypto and has_usdc:
            # Formula: total_risk = (fiat_risk * FIAT_WEIGHT) + (crypto_risk * CRYPTO_WEIGHT) + (usdc_risk * USDC_WEIGHT)
            combined_risk = (fiat_risk * FIAT_WEIGHT) + (crypto_risk * CRYPTO_WEIGHT) + (usdc_risk * USDC_WEIGHT)
        elif has_fiat and has_crypto:
            # No USDC component, redistribute weights
            fiat_weight = FIAT_WEIGHT / (FIAT_WEIGHT + CRYPTO_WEIGHT) 
            crypto_weight = CRYPTO_WEIGHT / (FIAT_WEIGHT + CRYPTO_WEIGHT)
            combined_risk = (fiat_risk * fiat_weight) + (crypto_risk * crypto_weight)
        elif has_fiat and has_usdc:
            # No crypto component, redistribute weights
            fiat_weight = FIAT_WEIGHT / (FIAT_WEIGHT + USDC_WEIGHT)
            usdc_weight = USDC_WEIGHT / (FIAT_WEIGHT + USDC_WEIGHT)
            combined_risk = (fiat_risk * fiat_weight) + (usdc_risk * usdc_weight)
        elif has_crypto and has_usdc:
            # No fiat component, redistribute weights
            crypto_weight = CRYPTO_WEIGHT / (CRYPTO_WEIGHT + USDC_WEIGHT)
            usdc_weight = USDC_WEIGHT / (CRYPTO_WEIGHT + USDC_WEIGHT)
            combined_risk = (crypto_risk * crypto_weight) + (usdc_risk * usdc_weight)
        elif has_fiat:
            # Only fiat component
            combined_risk = fiat_risk
        elif has_crypto:
            # Only crypto component
            combined_risk = crypto_risk
        elif has_usdc:
            # Only USDC component
            combined_risk = usdc_risk
        else:
            # No components (shouldn't happen)
            combined_risk = 0.0
        
        return combined_risk
    
    def _calculate_combined_risk(self, fiat_risk: float, crypto_risk: float, has_fiat: bool, has_crypto: bool) -> float:
        """
        Calculate the combined risk score based on fiat and crypto components
        
        Args:
            fiat_risk: Risk score from fiat analysis (0-1)
            crypto_risk: Risk score from crypto analysis (0-1)
            has_fiat: Whether the transaction has a fiat component
            has_crypto: Whether the transaction has a crypto component
        
        Returns:
            float: Combined risk score (0-1)
        """
        if has_fiat and has_crypto:
            # Formula: total_risk = (fiat_risk * FIAT_WEIGHT) + (crypto_risk * CRYPTO_WEIGHT)
            combined_risk = (fiat_risk * FIAT_WEIGHT) + (crypto_risk * CRYPTO_WEIGHT)
        elif has_fiat:
            # Only fiat component
            combined_risk = fiat_risk
        elif has_crypto:
            # Only crypto component
            combined_risk = crypto_risk
        else:
            # No components (shouldn't happen)
            combined_risk = 0.0
        
        return combined_risk

if __name__ == "__main__":
    # Example usage
    from data_generator import generate_synthetic_fiat_data, generate_sample_transaction
    
    # Generate sample data for training
    fiat_data = generate_synthetic_fiat_data(1000)
    
    # Create risk scorer and train models
    scorer = RiskScorer()
    scorer.train_models(fiat_data)
    
    # Test with a sample transaction
    sample_transaction = generate_sample_transaction()
    results = scorer.analyze_transaction(sample_transaction)
    
    print(f"Transaction: {sample_transaction}")
    print(f"Risk Score: {results['risk_score']}")
    print(f"Risk Level: {results['risk_level']}")
    print(f"Alerts: {results['alerts']}")
    if results['fiat_risk']:
        print(f"Fiat Risk: {results['fiat_risk']['score']}")
    if results['crypto_risk']:
        print(f"Crypto Risk: {results['crypto_risk']['score']}")
