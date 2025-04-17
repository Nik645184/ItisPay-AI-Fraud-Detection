import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import Dict, List, Tuple, Any, Optional
import logging
from config import ISOLATION_FOREST_CONTAMINATION, ISOLATION_FOREST_RANDOM_STATE
from utils import is_valid_ip, get_country_from_ip, normalize_score

# Configure logging
logger = logging.getLogger(__name__)

class FiatTransactionAnalyzer:
    """
    Analyzes fiat transactions for anomalies using Isolation Forest
    """
    
    def __init__(self):
        """Initialize the fiat transaction analyzer"""
        # Initialize the Isolation Forest model
        self.model = IsolationForest(
            contamination=ISOLATION_FOREST_CONTAMINATION,
            random_state=ISOLATION_FOREST_RANDOM_STATE
        )
        self.is_trained = False
        self.training_data = pd.DataFrame()
        
        # Feature importance tracking (for explanation)
        self.feature_importance = {}
        
        logger.info("Fiat Transaction Analyzer initialized")
    
    def train(self, data: pd.DataFrame) -> None:
        """
        Train the anomaly detection model on historical data
        
        Args:
            data: DataFrame with fiat transaction data
        """
        if data.empty:
            logger.warning("Training data is empty, skipping training")
            return
        
        logger.info(f"Training fiat anomaly detection model on {len(data)} transactions")
        
        # Preprocess the data
        X = self._preprocess_data(data)
        
        # Train the model
        self.model.fit(X)
        self.is_trained = True
        self.training_data = data.copy()
        
        logger.info("Fiat anomaly detection model trained successfully")
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the data for the model
        
        Args:
            data: DataFrame with raw transaction data
            
        Returns:
            pd.DataFrame: Preprocessed data ready for the model
        """
        # Make a copy to avoid modifying the original
        processed = data.copy()
        
        # One-hot encode categorical features
        if 'currency' in processed.columns:
            currency_dummies = pd.get_dummies(processed['currency'], prefix='currency')
            processed = pd.concat([processed, currency_dummies], axis=1)
        
        if 'card_country' in processed.columns:
            card_country_dummies = pd.get_dummies(processed['card_country'], prefix='card')
            processed = pd.concat([processed, card_country_dummies], axis=1)
        
        if 'geo_ip' in processed.columns:
            geo_ip_dummies = pd.get_dummies(processed['geo_ip'], prefix='geo')
            processed = pd.concat([processed, geo_ip_dummies], axis=1)
        
        # Create a geo mismatch feature
        if 'card_country' in processed.columns and 'geo_ip' in processed.columns:
            processed['geo_mismatch'] = (processed['card_country'] != processed['geo_ip']).astype(int)
        
        # Drop the original categorical columns
        processed = processed.drop(columns=['currency', 'card_country', 'geo_ip'], errors='ignore')
        
        # Add any other preprocessing steps as needed
        # For example, log transformation of amount
        if 'amount' in processed.columns:
            processed['log_amount'] = np.log1p(processed['amount'])
            processed = processed.drop(columns=['amount'])
        
        # Filter out any non-numeric columns
        numeric_columns = processed.select_dtypes(include=[np.number]).columns
        return processed[numeric_columns]
    
    def analyze(self, transaction: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Analyze a single fiat transaction for anomalies
        
        Args:
            transaction: Dictionary with transaction details
            
        Returns:
            Tuple[float, List[str]]: Risk score (0-1) and list of alerts
        """
        logger.info(f"Analyzing fiat transaction: {transaction}")
        
        # Initialize empty alerts list
        alerts = []
        
        # Validate transaction data
        if not self._validate_transaction(transaction):
            logger.warning("Invalid transaction data")
            return 0.8, ["Invalid transaction data"]
        
        # Basic rule-based checks
        rule_score, rule_alerts = self._rule_based_analysis(transaction)
        alerts.extend(rule_alerts)
        
        # Model-based anomaly detection
        if self.is_trained:
            model_score, model_alerts = self._model_based_analysis(transaction)
            alerts.extend(model_alerts)
            
            # Combine rule-based and model-based scores (weighted average)
            combined_score = 0.7 * model_score + 0.3 * rule_score
        else:
            # If the model is not trained, use only rule-based score
            logger.warning("Model not trained, using only rule-based analysis")
            combined_score = rule_score
        
        logger.info(f"Fiat analysis result: score={combined_score}, alerts={alerts}")
        return combined_score, alerts
    
    def _validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Validate that the transaction data has the required fields
        
        Args:
            transaction: Dictionary with transaction details
            
        Returns:
            bool: True if transaction is valid, False otherwise
        """
        required_fields = ['amount', 'currency', 'card_country', 'geo_ip']
        for field in required_fields:
            if field not in transaction:
                logger.warning(f"Missing required field: {field}")
                return False
            
            # Validate IP format
            if field == 'geo_ip' and not is_valid_ip(transaction[field]):
                logger.warning(f"Invalid IP format: {transaction[field]}")
                # We'll still continue the analysis but flag it
        
        return True
    
    def _rule_based_analysis(self, transaction: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Perform rule-based analysis on the transaction
        
        Args:
            transaction: Dictionary with transaction details
            
        Returns:
            Tuple[float, List[str]]: Risk score (0-1) and list of alerts
        """
        risk_score = 0.0
        alerts = []
        
        # Check for geo mismatch
        if transaction['card_country'] != transaction['geo_ip']:
            # Get actual country from IP if it's a valid IP format
            if is_valid_ip(transaction['geo_ip']):
                ip_country = get_country_from_ip(transaction['geo_ip'])
                if ip_country and ip_country != transaction['card_country']:
                    risk_score += 0.5
                    alerts.append(f"Geo mismatch: {ip_country} IP vs {transaction['card_country']} card")
            else:
                # If it's a country code directly
                risk_score += 0.5
                alerts.append(f"Geo mismatch: {transaction['geo_ip']} vs {transaction['card_country']}")
        
        # Check for unusual amount
        amount = transaction['amount']
        if amount > 10000:
            risk_score += 0.3
            alerts.append(f"Large transaction amount: {amount} {transaction['currency']}")
        
        # Check for high-risk countries
        from fatf_lists import FATF_GREY_LIST
        if transaction['card_country'] in FATF_GREY_LIST:
            risk_score += 0.4
            alerts.append(f"Card from FATF grey-listed country: {transaction['card_country']}")
        
        if transaction['geo_ip'] in FATF_GREY_LIST:
            risk_score += 0.4
            alerts.append(f"IP from FATF grey-listed country: {transaction['geo_ip']}")
        
        # Cap the risk score at 1.0
        risk_score = min(risk_score, 1.0)
        
        return risk_score, alerts
    
    def _model_based_analysis(self, transaction: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Perform model-based anomaly detection on the transaction
        
        Args:
            transaction: Dictionary with transaction details
            
        Returns:
            Tuple[float, List[str]]: Risk score (0-1) and list of alerts
        """
        # Convert transaction to DataFrame
        df = pd.DataFrame([transaction])
        
        # Preprocess the transaction
        X = self._preprocess_data(df)
        
        # Ensure the columns match the training data
        trained_columns = self._preprocess_data(self.training_data.head(1)).columns
        missing_columns = set(trained_columns) - set(X.columns)
        
        # Add missing columns with zeros
        for col in missing_columns:
            X[col] = 0
        
        # Ensure column order matches
        X = X[trained_columns]
        
        # Get anomaly score
        anomaly_score = self.model.decision_function([X.iloc[0].values])[0]
        
        # Convert to risk score (inverted, normalize from -1 to 1 range to 0 to 1)
        # Anomaly scores are negative for outliers, positive for inliers
        risk_score = (0.5 - (anomaly_score / 2))
        
        # Generate alerts
        alerts = []
        if risk_score > 0.7:
            alerts.append("Transaction flagged as anomalous by ML model")
            
            # Add more detailed explanation
            # For now, just a placeholder, could be enhanced with SHAP values etc.
            if 'geo_mismatch' in X.columns and X['geo_mismatch'].iloc[0] > 0:
                alerts.append("Unusual geographic pattern detected")
            
            if 'log_amount' in X.columns:
                if X['log_amount'].iloc[0] > np.log1p(5000):
                    alerts.append("Unusual transaction amount")
        
        return risk_score, alerts

if __name__ == "__main__":
    # Example usage
    from data_generator import generate_synthetic_fiat_data
    
    # Generate sample data
    data = generate_synthetic_fiat_data(1000)
    
    # Create analyzer and train
    analyzer = FiatTransactionAnalyzer()
    analyzer.train(data)
    
    # Test with a sample transaction
    sample_transaction = {
        'amount': 5000,
        'currency': 'USD',
        'card_country': 'US',
        'geo_ip': 'NG'
    }
    
    risk_score, alerts = analyzer.analyze(sample_transaction)
    print(f"Risk Score: {risk_score}")
    print(f"Alerts: {alerts}")
