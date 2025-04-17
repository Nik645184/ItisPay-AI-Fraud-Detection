import os
import logging
from flask import Flask, redirect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Initializing Flask app for WSGI")
app = Flask(__name__)

@app.route('/')
def index():
    # Redirect to the FastAPI service
    logger.info("Redirecting to FastAPI service")
    return redirect('/proxy/8000/docs')

@app.route('/ui')
def ui_redirect():
    # In a real implementation, we would redirect to the Streamlit UI 
    logger.info("UI route accessed")
    return """
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
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ ItisPay AI Fraud Detection</h1>
            <p class="lead">
                This service provides real-time fraud detection for fiat and cryptocurrency transactions
            </p>
            <a href="/proxy/8000/docs" class="btn btn-primary">Access API Documentation</a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)