"""
ItisPay Fraud Detection - Combined Application Starter
This script starts both the FastAPI and Streamlit components of the fraud detection system.
"""

import os
import sys
import logging
import time
import multiprocessing
from multiprocessing import Process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_fastapi():
    """Start the FastAPI server for the API backend"""
    logger.info("Starting FastAPI server on port 8000...")
    # Import here to avoid circular imports
    import uvicorn
    from api import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def start_streamlit():
    """Start the Streamlit UI on port 8501"""
    logger.info("Starting Streamlit UI on port 8501...")
    os.system(f"{sys.executable} -m streamlit run ui.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true")

def main():
    """
    Main function to start both the FastAPI server and Streamlit UI
    in separate processes for the combined application
    """
    logger.info("Starting ItisPay Fraud Detection services...")
    
    # Get Replit domain if available, or use localhost otherwise
    replit_domain = os.environ.get("REPL_SLUG")
    if replit_domain:
        # We're in Replit, use proxy URLs
        base_url = f"https://{replit_domain}.replit.app"
        api_url = f"{base_url}/proxy/8000"
    else:
        # Local development
        api_url = "http://localhost:8000"
    
    # Set the API URL environment variable for the UI to connect to
    os.environ["API_URL"] = api_url
    logger.info(f"Setting API_URL to {api_url}")
    
    # Start API server in a separate process
    api_process = Process(target=start_fastapi)
    api_process.daemon = True
    api_process.start()
    
    # Allow API to start up
    time.sleep(2)
    
    # Start Streamlit in the main process
    start_streamlit()

if __name__ == "__main__":
    main()