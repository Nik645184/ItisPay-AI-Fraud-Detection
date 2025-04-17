"""
ItisPay Fraud Detection - Flask Application
This serves as the entry point for the Gunicorn WSGI server,
providing a simple landing page that links to the FastAPI docs and Streamlit UI.
"""

import os
import logging
from flask import Flask, redirect, render_template_string

# Import SQLAlchemy and models
from models import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Initializing Flask app for WSGI")
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
        
        <a href="/proxy/8501/" class="btn btn-primary btn-lg">Launch Interactive UI</a>
        <a href="/proxy/8000/docs" class="btn btn-secondary btn-lg">API Documentation</a>
    </div>
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
    return redirect('/proxy/8000/docs')

@app.route('/ui')
def ui_redirect():
    """Redirect to Streamlit UI"""
    logger.info("Redirecting to Streamlit UI")
    return redirect('/proxy/8501/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)