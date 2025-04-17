from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import json
import datetime
from typing import Dict, List, Any, Optional
import time
import logging
from risk_scoring import RiskScorer
from data_generator import generate_synthetic_fiat_data
from utils import is_valid_ip, is_valid_eth_address
from sqlalchemy.orm import Session
from models import Transaction, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="AI Fraud Detection for ItisPay",
    description="Cross-Channel Fraud Detection API for fiat and crypto transactions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the risk scorer
risk_scorer = RiskScorer()

# Generate synthetic data and train the model
fiat_data = generate_synthetic_fiat_data(1000)
risk_scorer.train_models(fiat_data)

# Define the request models
class FiatTransaction(BaseModel):
    amount: float = Field(..., description="Transaction amount", gt=0)
    currency: str = Field(..., description="Currency code (e.g., USD, EUR)")
    card_country: str = Field(..., description="Card issuing country (2-letter code)")
    geo_ip: str = Field(..., description="IP address or country code of the transaction")
    
    @validator('card_country')
    def validate_card_country(cls, v):
        if len(v) != 2:
            raise ValueError('card_country must be a 2-letter country code')
        return v
    
    @validator('geo_ip')
    def validate_geo_ip(cls, v):
        if len(v) == 2:  # Country code
            return v
        if not is_valid_ip(v):
            raise ValueError('geo_ip must be a valid IP address or 2-letter country code')
        return v

class CryptoTransaction(BaseModel):
    address: str = Field(..., description="Crypto wallet address")
    currency: str = Field(..., description="Cryptocurrency (e.g., ETH, BTC)")
    amount: float = Field(..., description="Transaction amount", gt=0)
    
    @validator('address')
    def validate_address(cls, v):
        if not is_valid_eth_address(v):
            raise ValueError('address must be a valid Ethereum address')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        supported = ['ETH', 'BTC', 'USDT', 'USDC']
        if v not in supported:
            raise ValueError(f'currency must be one of {supported}')
        return v

class TransactionRequest(BaseModel):
    fiat: Optional[FiatTransaction] = Field(None, description="Fiat transaction details")
    crypto: Optional[CryptoTransaction] = Field(None, description="Crypto transaction details")
    
    @validator('fiat', 'crypto')
    def validate_at_least_one(cls, v, values):
        if 'fiat' not in values and v is None:
            raise ValueError('At least one of fiat or crypto must be provided')
        return v

class RiskResponse(BaseModel):
    risk_score: float = Field(..., description="Overall risk score (0-100)")
    risk_level: str = Field(..., description="Risk level (Low, Medium, High, Critical)")
    alerts: List[str] = Field(..., description="List of risk alerts")
    fiat_risk: Optional[Dict[str, Any]] = Field(None, description="Fiat risk details")
    crypto_risk: Optional[Dict[str, Any]] = Field(None, description="Crypto risk details")
    processing_time: float = Field(..., description="Processing time in seconds")

# Database dependency
def get_db():
    """FastAPI Dependency for getting a database session"""
    try:
        # Create a new database session
        db_session = db.session
        yield db_session
    finally:
        # Close the session
        db_session.close()

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    client_ip = request.client.host if request.client else "Unknown"
    
    # Log the request
    logger.info(f"Request from {client_ip}: {request.method} {request.url.path}")
    
    # Process the request
    response = await call_next(request)
    
    # Log the response time
    process_time = time.time() - start_time
    logger.info(f"Response time: {process_time:.4f}s")
    
    return response

@app.get("/")
async def root():
    """API root endpoint with information about the service"""
    return {
        "name": "AI Fraud Detection API for ItisPay",
        "version": "1.0.0",
        "description": "Cross-Channel Fraud Detection for fiat and crypto transactions",
        "endpoints": [
            {
                "path": "/fraud-check",
                "method": "POST",
                "description": "Analyze a transaction for fraud risk"
            }
        ]
    }

@app.post("/fraud-check", response_model=RiskResponse)
async def fraud_check(transaction: TransactionRequest, db_session: Session = Depends(get_db)):
    """
    Analyze a transaction for fraud risk and store in database
    
    Args:
        transaction: Transaction details with fiat and/or crypto components
        db_session: Database session (injected by FastAPI)
        
    Returns:
        RiskResponse: Risk analysis results
    """
    start_time = time.time()
    logger.info(f"Received fraud check request: {transaction}")
    
    # Convert Pydantic model to dict
    transaction_dict = transaction.dict()
    
    try:
        # Analyze the transaction
        results = risk_scorer.analyze_transaction(transaction_dict)
        
        # Add processing time
        results['processing_time'] = round(time.time() - start_time, 4)
        
        # Store the transaction and analysis in the database
        try:
            # Create a transaction record from the API result
            db_transaction = Transaction.from_api_result(transaction_dict, results)
            
            # Add and commit to the database
            db_session.add(db_transaction)
            db_session.commit()
            
            logger.info(f"Transaction saved to database with ID: {db_transaction.id}")
        except Exception as db_error:
            logger.error(f"Failed to save transaction to database: {db_error}")
            # Don't fail the API response if database save fails
            db_session.rollback()
        
        return results
    except Exception as e:
        logger.error(f"Error analyzing transaction: {e}")
        processing_time = round(time.time() - start_time, 4)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Transaction analysis failed",
                "message": str(e),
                "processing_time": processing_time
            }
        )

# Transaction history response model
class TransactionHistoryItem(BaseModel):
    id: int
    transaction_type: str
    amount: float
    currency: str
    timestamp: datetime.datetime
    risk_score: float
    risk_level: str
    
    class Config:
        orm_mode = True

class TransactionHistoryResponse(BaseModel):
    transactions: List[TransactionHistoryItem]
    total: int

@app.get("/transactions", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    db_session: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    min_risk: Optional[float] = None,
    max_risk: Optional[float] = None,
    transaction_type: Optional[str] = None
):
    """
    Get transaction history with optional filtering
    
    Args:
        db_session: Database session
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip
        min_risk: Minimum risk score filter
        max_risk: Maximum risk score filter
        transaction_type: Filter by transaction type (fiat, crypto, or both)
        
    Returns:
        List of transactions
    """
    logger.info(f"Getting transaction history with filters: min_risk={min_risk}, max_risk={max_risk}, type={transaction_type}")
    
    # Build the query
    query = db_session.query(Transaction)
    
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
    
    return {
        "transactions": transactions,
        "total": total_count
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
