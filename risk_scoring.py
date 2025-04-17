from typing import Dict, Any, List, Tuple
import logging
from config import FIAT_WEIGHT, CRYPTO_WEIGHT
from utils import normalize_score, get_risk_level
from fiat_analyzer import FiatTransactionAnalyzer
from crypto_analyzer import CryptoTransactionAnalyzer

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
            'crypto_risk': None
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
        if 'crypto' in transaction and transaction['crypto']:
            crypto_risk_score, crypto_alerts = self.crypto_analyzer.analyze(transaction['crypto'])
            results['crypto_risk'] = {
                'score': round(crypto_risk_score * 100, 2),
                'alerts': crypto_alerts
            }
            
            # Add prefix to crypto alerts for combined list
            crypto_alerts = [f"Crypto: {alert}" for alert in crypto_alerts]
        
        # Calculate combined risk score
        combined_risk = self._calculate_combined_risk(
            fiat_risk_score,
            crypto_risk_score,
            'fiat' in transaction and transaction['fiat'],
            'crypto' in transaction and transaction['crypto']
        )
        
        # Convert to 0-100 scale
        normalized_risk = round(combined_risk * 100, 2)
        results['risk_score'] = normalized_risk
        results['risk_level'] = get_risk_level(normalized_risk)
        
        # Combine alerts
        results['alerts'] = fiat_alerts + crypto_alerts
        
        logger.info(f"Risk analysis complete: score={normalized_risk}, level={results['risk_level']}")
        return results
    
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
