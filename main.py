"""
ItisPay Fraud Detection - Unified Application
This serves as the entry point for the Gunicorn WSGI server,
providing a complete web application with fraud detection, history and API.
"""

# Import the unified application
from app_unified import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)