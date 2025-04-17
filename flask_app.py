"""
ItisPay Fraud Detection - Flask Application
This serves as the entry point for the Gunicorn WSGI server,
providing a simple landing page that links to the FastAPI docs and Streamlit UI.
"""

import os
import logging
from flask import Flask, redirect, render_template_string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Initializing Flask app for WSGI")
app = Flask(__name__)

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
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 90vh;
        }
        .container {
            max-width: 800px;
            text-align: center;
        }
        .btn {
            margin: 10px;
        }
        .card {
            margin: 20px 0;
            background-color: #252525;
            border: 1px solid #333;
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
        .btn-link-manual {
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            margin: 10px;
            text-align: center;
        }
        .btn-link-manual.secondary {
            background-color: #6c757d;
        }
        .manual-instruction {
            margin: 15px;
            padding: 15px;
            background-color: rgba(255, 255, 100, 0.2);
            border-radius: 5px;
            max-width: 500px;
            text-align: left;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ ItisPay AI Fraud Detection</h1>
        <p class="lead">
            Cross-Channel Fraud Detection for Fiat and Cryptocurrency Transactions
        </p>
        
        <div class="card p-3">
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
            </div>
        </div>
        
        <div class="manual-instruction">
            <p><strong>Для доступа к компонентам системы:</strong></p>
            <ol>
                <li>Откройте интерактивный интерфейс, добавив к текущему URL следующий путь: <code>/proxy/8501/</code></li>
                <li>Для доступа к API документации добавьте: <code>/proxy/8000/docs</code></li>
            </ol>
        </div>
        
        <div>
            <a class="btn-link-manual" id="ui-link" href="#" onclick="window.open(window.location.origin + '/proxy/8501/', '_blank')">Запустить интерфейс</a>
            <a class="btn-link-manual secondary" id="api-link" href="#" onclick="window.open(window.location.origin + '/proxy/8000/docs', '_blank')">API документация</a>
        </div>
    </div>
    
    <script>
    // Add JavaScript to help with navigation
    document.addEventListener('DOMContentLoaded', function() {
        console.log("Page loaded");
        
        // Get the current domain
        const domain = window.location.origin;
        console.log("Current domain:", domain);
        
        // Update links for direct navigation
        document.getElementById('ui-link').href = domain + '/proxy/8501/';
        document.getElementById('api-link').href = domain + '/proxy/8000/docs';
    });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Landing page with links to UI and API docs"""
    logger.info("Landing page accessed")
    return render_template_string(LANDING_PAGE_HTML)

@app.route('/api')
def api_redirect():
    """Redirect to FastAPI documentation"""
    logger.info("Redirecting to FastAPI docs")
    # URL for API docs in Replit environment
    return redirect('https://8000-bluecatlabs-itispayfrau-d58j18w2w0d.ws-eu110.gitpod.io/docs')

@app.route('/ui')
def ui_redirect():
    """Redirect to Streamlit UI"""
    logger.info("Redirecting to Streamlit UI")
    # URL for Streamlit UI in Replit environment
    return redirect('https://3000-bluecatlabs-itispayfrau-d58j18w2w0d.ws-eu110.gitpod.io/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)