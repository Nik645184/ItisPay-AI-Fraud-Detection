import os

# API Configuration
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "YourApiKeyToken")

# Risk Score Configuration
FIAT_WEIGHT = 0.5
CRYPTO_WEIGHT = 0.5

# Risk Thresholds
LOW_RISK_THRESHOLD = 30
MEDIUM_RISK_THRESHOLD = 70
HIGH_RISK_THRESHOLD = 90

# Anomaly Detection Parameters
ISOLATION_FOREST_CONTAMINATION = 0.05  # Expected proportion of outliers
ISOLATION_FOREST_RANDOM_STATE = 42  # For reproducibility

# API Request Rate Limits (requests per second)
ETHERSCAN_RATE_LIMIT = 5

# Performance Configuration
PROCESSING_TIMEOUT = 1.0  # Maximum transaction processing time in seconds

# Data Generation Settings
SYNTHETIC_DATA_SIZE = 1000  # Number of synthetic transactions to generate
