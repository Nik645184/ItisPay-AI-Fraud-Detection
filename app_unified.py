"""
ItisPay Fraud Detection - Unified Application
This file combines all components (Flask, FastAPI, DB) into a single Flask application
"""

import os
import logging
import json
from datetime import datetime
import pandas as pd
import numpy as np
import time
from flask import Flask, render_template, redirect, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from models import Transaction, db
from risk_scoring import RiskScorer
from data_generator import generate_synthetic_fiat_data, generate_sample_transaction
import plotly.express as px
import plotly.graph_objects as go

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Flask app
logger.info("Initializing Flask app")
app = Flask(__name__)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

# Initialize the risk scorer
risk_scorer = RiskScorer()

# Train the model with synthetic data
fiat_data = generate_synthetic_fiat_data(1000)
risk_scorer.train_models(fiat_data)

# Create database tables if they don't exist, but safely
with app.app_context():
    try:
        logger.info("Creating database tables if they don't exist")
        
        # Check if tables already exist and create them only if needed
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'transactions' not in existing_tables:
            logger.info("Tables don't exist, creating them")
            db.create_all()
        else:
            logger.info("Tables already exist, skipping creation")
    except Exception as e:
        logger.error(f"Error during database setup: {e}")
        # Continue running even if there's a database error

# HTML template for the landing page
LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ItisPay Fraud Detection</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
            background-color: #1e1e1e;
            color: #f0f0f0;
            font-family: Arial, sans-serif;
            min-height: 90vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
        }
        .btn {
            margin: 10px;
        }
        .card {
            margin: 20px 0;
            background-color: #252525;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 5px;
        }
        .feature-list {
            text-align: left;
            margin: 20px auto;
            max-width: 500px;
        }
        .feature-item {
            margin: 10px 0;
            display: flex;
            align-items: flex-start;
        }
        .feature-icon {
            margin-right: 10px;
        }
        .btn-link-custom {
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            margin: 10px;
            text-align: center;
            border: none;
            cursor: pointer;
        }
        .btn-link-custom.secondary {
            background-color: #6c757d;
        }
        .badge {
            display: inline-block;
            padding: 0.25em 0.6em;
            font-size: 75%;
            font-weight: 600;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 0.375rem;
            margin: 0 0.2rem;
        }
        .badge-success {
            background-color: #28a745;
            color: white;
        }
        .badge-info {
            background-color: #17a2b8;
            color: white;
        }
        .row {
            display: flex;
            flex-wrap: wrap;
            margin-right: -15px;
            margin-left: -15px;
        }
        .col-md-4 {
            position: relative;
            width: 100%;
            padding-right: 15px;
            padding-left: 15px;
            flex: 0 0 33.333333%;
            max-width: 33.333333%;
        }
        .mt-4 {
            margin-top: 1.5rem;
        }
        .mb-3 {
            margin-bottom: 1rem;
        }
        .mb-4 {
            margin-bottom: 1.5rem;
        }
        .text-center {
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ ItisPay AI Fraud Detection</h1>
        <p class="lead">
            Cross-Channel Fraud Detection for Fiat and Cryptocurrency Transactions
        </p>
        
        <div class="card">
            <h3>About this System</h3>
            <p>This AI-powered fraud detection system analyzes both fiat and crypto transactions to identify potential fraud risks.</p>
            
            <div class="feature-list">
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <div>Fiat transaction anomaly detection using Isolation Forest</div>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <div>Crypto wallet analysis with Etherscan API integration</div>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <div>Cross-channel risk scoring combining fiat and crypto signals</div>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <div>Explainable risk alerts with specific fraud indicators</div>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <div>PostgreSQL database for transaction history storage</div>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <div>Interactive transaction history with filtering and visualization</div>
                </div>
            </div>
        </div>
        
        <div class="card mt-4">
            <h3>System Components <span class="badge badge-success">Active</span></h3>
            <p>The ItisPay Fraud Detection system includes the following features:</p>
            
            <div class="row text-center mb-4">
                <div class="col-md-4 mb-3">
                    <h5>Fraud Check</h5>
                    <p>Analyze new transactions</p>
                </div>
                <div class="col-md-4 mb-3">
                    <h5>Transaction History</h5>
                    <p>View past transactions</p>
                </div>
                <div class="col-md-4 mb-3">
                    <h5>API Access</h5>
                    <p>Integration options</p>
                </div>
            </div>
        </div>
        
        <a href="/fraud-check" class="btn-link-custom">Fraud Detection</a>
        <a href="/transaction-history" class="btn-link-custom secondary">Transaction History</a>
        <a href="/api-docs" class="btn-link-custom" style="background-color: #17a2b8;">API Documentation</a>
    </div>
</body>
</html>
"""

API_DOCS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ItisPay API Documentation</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
            background-color: #1e1e1e;
            color: #f0f0f0;
            font-family: Arial, sans-serif;
            min-height: 90vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        pre {
            background-color: #252525;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .endpoint {
            background-color: #252525;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .method {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .method.post {
            background-color: #28a745;
            color: white;
        }
        .method.get {
            background-color: #007bff;
            color: white;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #17a2b8;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>
        <h1>ItisPay API Documentation</h1>
        <p>This documentation describes the endpoints available in the ItisPay Fraud Detection API.</p>
        
        <h2>Endpoints</h2>
        
        <div class="endpoint">
            <h3><span class="method post">POST</span> /api/fraud-check</h3>
            <p>Analyze a transaction for fraud risk.</p>
            
            <h4>Request Body:</h4>
            <pre>
{
  "fiat": {
    "amount": 1000,
    "currency": "USD",
    "card_country": "US",
    "geo_ip": "NG"
  },
  "crypto": {
    "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "currency": "ETH",
    "amount": 0.5
  }
}
            </pre>
            
            <h4>Response:</h4>
            <pre>
{
  "risk_score": 75.5,
  "risk_level": "High",
  "alerts": [
    "Card country (US) doesn't match IP location (NG)",
    "Suspicious wallet patterns detected"
  ],
  "fiat_risk": {
    "score": 65.3,
    "alerts": [
      "Card country (US) doesn't match IP location (NG)"
    ]
  },
  "crypto_risk": {
    "score": 85.7,
    "alerts": [
      "Suspicious wallet patterns detected"
    ]
  },
  "processing_time": 0.254
}
            </pre>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span> /api/transactions</h3>
            <p>Get transaction history with optional filtering.</p>
            
            <h4>Query Parameters:</h4>
            <ul>
                <li><code>limit</code> - Maximum number of transactions to return (default: 20)</li>
                <li><code>offset</code> - Number of transactions to skip (default: 0)</li>
                <li><code>min_risk</code> - Minimum risk score filter (optional)</li>
                <li><code>max_risk</code> - Maximum risk score filter (optional)</li>
                <li><code>transaction_type</code> - Filter by transaction type: fiat, crypto, or both (optional)</li>
            </ul>
            
            <h4>Response:</h4>
            <pre>
{
  "transactions": [
    {
      "id": 1,
      "transaction_type": "both",
      "amount": 1000,
      "currency": "USD",
      "timestamp": "2025-04-17T15:30:45.123Z",
      "risk_score": 75.5,
      "risk_level": "High"
    },
    {
      "id": 2,
      "transaction_type": "crypto",
      "amount": 0.5,
      "currency": "ETH",
      "timestamp": "2025-04-17T14:22:31.456Z",
      "risk_score": 35.2,
      "risk_level": "Medium"
    }
  ],
  "total": 2
}
            </pre>
        </div>
        
        <h2>Testing the API</h2>
        <p>You can test the API directly using these endpoints:</p>
        <ul>
            <li>Use <code>/api/fraud-check</code> to analyze a transaction</li>
            <li>Use <code>/api/transactions</code> to retrieve transaction history</li>
        </ul>
    </div>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    """Landing page with links to features"""
    logger.info("Landing page accessed")
    return render_template_string(LANDING_PAGE_HTML)

@app.route('/api-docs')
def api_docs():
    """API documentation page"""
    logger.info("API docs page accessed")
    return render_template_string(API_DOCS_HTML)

@app.route('/fraud-check')
def fraud_check_page():
    """Fraud detection form page"""
    logger.info("Fraud check page accessed")
    
    # Generate a sample transaction
    sample = generate_sample_transaction()
    sample_json = json.dumps(sample, indent=2)
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>ItisPay Fraud Check</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
            background-color: #1e1e1e;
            color: #f0f0f0;
            font-family: Arial, sans-serif;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .card {
            background-color: #252525;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        textarea {
            width: 100%;
            height: 300px;
            background-color: #333;
            color: #f0f0f0;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 10px;
            font-family: monospace;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #17a2b8;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .btn-primary {
            background-color: #007bff;
            border: none;
            padding: 10px 20px;
            color: white;
            border-radius: 4px;
            cursor: pointer;
        }
        .btn-primary:hover {
            background-color: #0069d9;
        }
        .result-box {
            background-color: #333;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .risk-low {
            color: #28a745;
            font-weight: bold;
        }
        .risk-medium {
            color: #ffc107;
            font-weight: bold;
        }
        .risk-high {
            color: #fd7e14;
            font-weight: bold;
        }
        .risk-critical {
            color: #dc3545;
            font-weight: bold;
        }
        .alert-item {
            margin: 5px 0;
            padding-left: 20px;
            position: relative;
        }
        .alert-item:before {
            content: "⚠️";
            position: absolute;
            left: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>
        <h1>Fraud Detection</h1>
        <p>Submit a transaction for analysis. You can edit the JSON below or use the sample provided.</p>
        
        <div class="card">
            <form id="fraud-check-form">
                <div class="form-group">
                    <label for="transaction-json">Transaction JSON:</label>
                    <textarea id="transaction-json" name="transaction_json">{{ sample_json }}</textarea>
                </div>
                <button type="submit" class="btn-primary">Analyze Transaction</button>
            </form>
        </div>
        
        <div id="results" style="display: none;">
            <h2>Analysis Results:</h2>
            <div class="card" id="result-content">
                <div id="risk-score"></div>
                <div id="alerts"></div>
                <h4>Details:</h4>
                <div class="result-box" id="result-json"></div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('fraud-check-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const transactionJson = document.getElementById('transaction-json').value;
            let transaction;
            
            try {
                transaction = JSON.parse(transactionJson);
            } catch (error) {
                alert('Invalid JSON: ' + error.message);
                return;
            }
            
            // Show loading state
            document.getElementById('results').style.display = 'block';
            document.getElementById('result-content').innerHTML = '<p>Analyzing transaction...</p>';
            
            try {
                const response = await fetch('/api/fraud-check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: transactionJson
                });
                
                if (!response.ok) {
                    throw new Error('Error: ' + response.status);
                }
                
                const result = await response.json();
                
                // Check if there's an error in the response
                if (result.error) {
                    document.getElementById('result-content').innerHTML = `
                        <div class="alert alert-danger">
                            <h4>Error:</h4>
                            <p>${result.error}</p>
                            <p>${result.message || ''}</p>
                        </div>
                    `;
                    return;
                }
                
                // Format the risk level with color
                let riskClass = '';
                if (result.risk_level === 'Low') {
                    riskClass = 'risk-low';
                } else if (result.risk_level === 'Medium') {
                    riskClass = 'risk-medium';
                } else if (result.risk_level === 'High') {
                    riskClass = 'risk-high';
                } else if (result.risk_level === 'Critical') {
                    riskClass = 'risk-critical';
                }
                
                // Format alerts
                let alertsHtml = '<h4>Alerts:</h4>';
                if (result.alerts && result.alerts.length > 0) {
                    alertsHtml += '<ul>';
                    result.alerts.forEach(alert => {
                        alertsHtml += `<li class="alert-item">${alert}</li>`;
                    });
                    alertsHtml += '</ul>';
                } else {
                    alertsHtml += '<p>No alerts detected.</p>';
                }
                
                // Determine which risk components are present
                let riskDetails = '<div class="risk-components">';
                
                // Fiat risk
                if (result.fiat_risk) {
                    riskDetails += `
                        <div class="risk-component">
                            <h5>Fiat Risk: ${result.fiat_risk.score.toFixed(1)}</h5>
                            ${result.fiat_risk.alerts && result.fiat_risk.alerts.length > 0 ? 
                                '<ul>' + result.fiat_risk.alerts.map(alert => `<li>${alert}</li>`).join('') + '</ul>' : 
                                '<p>No specific fiat risks detected.</p>'}
                        </div>
                    `;
                }
                
                // Crypto risk
                if (result.crypto_risk) {
                    riskDetails += `
                        <div class="risk-component">
                            <h5>Crypto Risk: ${result.crypto_risk.score.toFixed(1)}</h5>
                            ${result.crypto_risk.alerts && result.crypto_risk.alerts.length > 0 ? 
                                '<ul>' + result.crypto_risk.alerts.map(alert => `<li>${alert}</li>`).join('') + '</ul>' : 
                                '<p>No specific crypto risks detected.</p>'}
                        </div>
                    `;
                }
                
                // USDC risk is now part of the crypto risk analysis
                
                riskDetails += '</div>';
                
                // Rebuild the entire result content
                document.getElementById('result-content').innerHTML = `
                    <h3>Risk Score: <span class="${riskClass}">${result.risk_score.toFixed(1)} (${result.risk_level})</span></h3>
                    <div>${alertsHtml}</div>
                    <h4>Risk Components:</h4>
                    ${riskDetails}
                    <h4>Full Details:</h4>
                    <div class="result-box">${JSON.stringify(result, null, 2)}</div>
                `;
                
            } catch (error) {
                document.getElementById('result-content').innerHTML = '<p>Error: ' + error.message + '</p>';
            }
        });
    </script>
</body>
</html>
    ''', sample_json=sample_json)

@app.route('/transaction-history')
def transaction_history_page():
    """Transaction history page"""
    logger.info("Transaction history page accessed")
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>ItisPay Transaction History</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            padding: 20px;
            background-color: #1e1e1e;
            color: #f0f0f0;
            font-family: Arial, sans-serif;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .card {
            background-color: #252525;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #17a2b8;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .filters {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
            min-width: 150px;
        }
        label {
            margin-bottom: 5px;
        }
        select, input {
            padding: 8px;
            background-color: #333;
            color: #f0f0f0;
            border: 1px solid #444;
            border-radius: 4px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #444;
        }
        th {
            background-color: #333;
        }
        .risk-low {
            background-color: rgba(40, 167, 69, 0.3);
            color: #28a745;
            padding: 3px 8px;
            border-radius: 3px;
        }
        .risk-medium {
            background-color: rgba(255, 193, 7, 0.3);
            color: #ffc107;
            padding: 3px 8px;
            border-radius: 3px;
        }
        .risk-high {
            background-color: rgba(253, 126, 20, 0.3);
            color: #fd7e14;
            padding: 3px 8px;
            border-radius: 3px;
        }
        .risk-critical {
            background-color: rgba(220, 53, 69, 0.3);
            color: #dc3545;
            padding: 3px 8px;
            border-radius: 3px;
        }
        .pagination {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        .pagination button {
            background-color: #333;
            border: none;
            color: #f0f0f0;
            padding: 8px 12px;
            margin: 0 5px;
            cursor: pointer;
            border-radius: 4px;
        }
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .pagination span {
            padding: 8px 12px;
        }
        #chart {
            width: 100%;
            height: 300px;
        }
        .empty-state {
            padding: 30px;
            text-align: center;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>
        <h1>Transaction History</h1>
        
        <div class="card">
            <h3>Filters</h3>
            <div class="filters">
                <div class="filter-group">
                    <label for="type-filter">Transaction Type:</label>
                    <select id="type-filter">
                        <option value="">All Types</option>
                        <option value="fiat">Fiat Only</option>
                        <option value="crypto">Crypto Only</option>
                        <option value="both">Combined</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="min-risk">Min Risk Score:</label>
                    <input type="range" id="min-risk" min="0" max="100" value="0" oninput="document.getElementById('min-risk-value').textContent = this.value">
                    <span id="min-risk-value">0</span>
                </div>
                <div class="filter-group">
                    <label for="max-risk">Max Risk Score:</label>
                    <input type="range" id="max-risk" min="0" max="100" value="100" oninput="document.getElementById('max-risk-value').textContent = this.value">
                    <span id="max-risk-value">100</span>
                </div>
                <div class="filter-group">
                    <label for="limit">Items per page:</label>
                    <select id="limit">
                        <option value="10">10</option>
                        <option value="20" selected>20</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <div class="filter-group" style="justify-content: flex-end;">
                    <button onclick="applyFilters()" style="margin-top: 20px; padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Apply Filters</button>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>Risk Distribution</h3>
            <div id="chart"></div>
        </div>
        
        <div class="card">
            <h3>Transactions</h3>
            <div id="transactions-table">
                <div class="empty-state">Loading transactions...</div>
            </div>
            
            <div class="pagination">
                <button id="prev-page" onclick="changePage(-1)" disabled>Previous</button>
                <span id="page-info">Page 1</span>
                <button id="next-page" onclick="changePage(1)" disabled>Next</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentPage = 1;
        let totalItems = 0;
        let itemsPerPage = 20;
        
        async function fetchTransactions() {
            const typeFilter = document.getElementById('type-filter').value;
            const minRisk = document.getElementById('min-risk').value;
            const maxRisk = document.getElementById('max-risk').value;
            itemsPerPage = parseInt(document.getElementById('limit').value);
            
            const offset = (currentPage - 1) * itemsPerPage;
            
            let url = `/api/transactions?limit=${itemsPerPage}&offset=${offset}`;
            
            if (typeFilter) {
                url += `&transaction_type=${typeFilter}`;
            }
            
            if (minRisk > 0) {
                url += `&min_risk=${minRisk}`;
            }
            
            if (maxRisk < 100) {
                url += `&max_risk=${maxRisk}`;
            }
            
            try {
                const response = await fetch(url);
                
                if (!response.ok) {
                    throw new Error('Error: ' + response.status);
                }
                
                const data = await response.json();
                
                // Update pagination
                totalItems = data.total;
                updatePagination();
                
                // Update table
                updateTransactionsTable(data.transactions);
                
                // Update chart
                updateRiskChart(data.transactions);
                
            } catch (error) {
                document.getElementById('transactions-table').innerHTML = `<div class="empty-state">Error loading transactions: ${error.message}</div>`;
            }
        }
        
        function updateTransactionsTable(transactions) {
            const tableContainer = document.getElementById('transactions-table');
            
            if (!transactions || transactions.length === 0) {
                tableContainer.innerHTML = '<div class="empty-state">No transactions found matching your filters.</div>';
                return;
            }
            
            let tableHtml = `
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Type</th>
                            <th>Amount</th>
                            <th>Date & Time</th>
                            <th>Risk Score</th>
                            <th>Risk Level</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            transactions.forEach(tx => {
                const date = new Date(tx.timestamp).toLocaleString();
                let riskClass = '';
                
                if (tx.risk_level === 'Low') {
                    riskClass = 'risk-low';
                } else if (tx.risk_level === 'Medium') {
                    riskClass = 'risk-medium';
                } else if (tx.risk_level === 'High') {
                    riskClass = 'risk-high';
                } else if (tx.risk_level === 'Critical') {
                    riskClass = 'risk-critical';
                }
                
                tableHtml += `
                    <tr>
                        <td>${tx.id}</td>
                        <td>${tx.transaction_type}</td>
                        <td>${tx.amount} ${tx.currency}</td>
                        <td>${date}</td>
                        <td>${tx.risk_score.toFixed(1)}</td>
                        <td><span class="${riskClass}">${tx.risk_level}</span></td>
                    </tr>
                `;
            });
            
            tableHtml += `
                    </tbody>
                </table>
            `;
            
            tableContainer.innerHTML = tableHtml;
        }
        
        function updateRiskChart(transactions) {
            if (!transactions || transactions.length === 0) {
                document.getElementById('chart').innerHTML = '<div class="empty-state">No data to display.</div>';
                return;
            }
            
            // Count risk levels
            const riskCounts = {
                'Low': 0,
                'Medium': 0,
                'High': 0,
                'Critical': 0
            };
            
            transactions.forEach(tx => {
                if (tx.risk_level in riskCounts) {
                    riskCounts[tx.risk_level]++;
                }
            });
            
            // Create chart data
            const data = [{
                x: Object.keys(riskCounts),
                y: Object.values(riskCounts),
                type: 'bar',
                marker: {
                    color: ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
                }
            }];
            
            const layout = {
                title: 'Risk Level Distribution',
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {
                    color: '#f0f0f0'
                },
                xaxis: {
                    title: 'Risk Level'
                },
                yaxis: {
                    title: 'Count'
                }
            };
            
            Plotly.newPlot('chart', data, layout);
        }
        
        function updatePagination() {
            const totalPages = Math.ceil(totalItems / itemsPerPage);
            
            document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages || 1}`;
            document.getElementById('prev-page').disabled = currentPage <= 1;
            document.getElementById('next-page').disabled = currentPage >= totalPages;
        }
        
        function changePage(change) {
            currentPage += change;
            fetchTransactions();
        }
        
        function applyFilters() {
            currentPage = 1;
            fetchTransactions();
        }
        
        // Initial load
        fetchTransactions();
    </script>
</body>
</html>
    ''')

# API endpoints
@app.route('/api/fraud-check', methods=['POST'])
def api_fraud_check():
    """Analyze a transaction for fraud risk"""
    start_time = time.time()
    
    try:
        # Get transaction data from request
        transaction_data = request.json
        logger.info(f"Received fraud check request: {transaction_data}")
        
        # Analyze the transaction
        results = risk_scorer.analyze_transaction(transaction_data)
        
        # Add processing time
        results['processing_time'] = round(time.time() - start_time, 4)
        
        # Convert all numpy values to Python types
        def convert_numpy_types(obj):
            import numpy as np
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, np.number):  # Check for any numpy numeric type
                return float(obj)
            else:
                return obj
                
        # Convert numpy types to Python types
        results = convert_numpy_types(results)
        
        # Print response status for debugging
        print("Response Status: 200 OK")
        print(f"Response Data: {results}")
        
        # Store in database
        with app.app_context():
            try:
                # Already converted above, but keep this check for safety
                if 'risk_score' in results and hasattr(results['risk_score'], 'item'):
                    results['risk_score'] = float(results['risk_score'])
                
                # Create a transaction record from the API result
                db_transaction = Transaction.from_api_result(transaction_data, results)
                
                # Add and commit to the database
                db.session.add(db_transaction)
                db.session.commit()
                
                logger.info(f"Transaction saved to database with ID: {db_transaction.id}")
            except Exception as db_error:
                logger.error(f"Failed to save transaction to database: {db_error}")
                # Don't fail the API response if database save fails
                db.session.rollback()
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Error analyzing transaction: {e}")
        return jsonify({
            "error": "Transaction analysis failed",
            "message": str(e),
            "processing_time": round(time.time() - start_time, 4)
        }), 500

@app.route('/api/transactions')
def api_transactions():
    """Get transaction history with optional filtering"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    min_risk = request.args.get('min_risk', type=float)
    max_risk = request.args.get('max_risk', type=float)
    transaction_type = request.args.get('transaction_type')
    
    logger.info(f"Getting transaction history with filters: min_risk={min_risk}, max_risk={max_risk}, type={transaction_type}")
    
    try:
        with app.app_context():
            # Build the query
            query = db.session.query(Transaction)
            
            # Apply filters
            if min_risk is not None:
                query = query.filter(Transaction.risk_score >= min_risk)
            
            if max_risk is not None:
                query = query.filter(Transaction.risk_score <= max_risk)
            
            if transaction_type:
                query = query.filter(Transaction.transaction_type == transaction_type)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination and get results
            transactions = query.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit).all()
            
            # Convert to dictionaries for JSON serialization
            result = []
            for tx in transactions:
                result.append({
                    "id": tx.id,
                    "transaction_type": tx.transaction_type,
                    "amount": tx.amount,
                    "currency": tx.currency,
                    "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                    "risk_score": tx.risk_score,
                    "risk_level": tx.risk_level
                })
            
            # Print response status for debugging
            print("Response Status: 200 OK")
            print(f"Response Data: {{'transactions': {len(result)}, 'total': {total_count}}}")
            
            return jsonify({
                "transactions": result,
                "total": total_count
            })
            
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({
            "error": "Failed to fetch transactions",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)