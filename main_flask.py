# Import Flask app for Gunicorn
from wsgi import app

# This file is specifically for the Gunicorn WSGI server
# The FastAPI app is served separately via Uvicorn in the run_app workflow