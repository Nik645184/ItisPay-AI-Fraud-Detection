"""
ItisPay Fraud Detection - Database Models
This module defines SQLAlchemy ORM models for the fraud detection system.
"""
import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

# This will be initialized in main.py
db = SQLAlchemy()

class Transaction(db.Model):
    """Base transaction model containing shared properties"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    transaction_type = Column(String(10), nullable=False)  # 'fiat' or 'crypto'
    
    # Shared properties
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Risk assessment result
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)  # Low, Medium, High, Critical
    alerts = Column(JSON, nullable=True)  # Store alert messages as JSON array
    
    # Relationship to specific transaction types
    fiat_details = relationship("FiatTransactionDetails", 
                               back_populates="transaction", 
                               uselist=False,
                               cascade="all, delete-orphan")
    crypto_details = relationship("CryptoTransactionDetails", 
                                 back_populates="transaction", 
                                 uselist=False,
                                 cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, score={self.risk_score})>"
    
    @classmethod
    def from_api_result(cls, transaction_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> "Transaction":
        """
        Create a transaction record from API input and analysis result
        
        Args:
            transaction_data: Original transaction data with fiat and/or crypto components
            analysis_result: Analysis result from the risk scorer
            
        Returns:
            Transaction: New transaction record
        """
        # Determine transaction type and create base record
        has_fiat = transaction_data.get('fiat') is not None
        has_crypto = transaction_data.get('crypto') is not None
        
        if has_fiat and has_crypto:
            transaction_type = 'both'
        elif has_fiat:
            transaction_type = 'fiat'
        else:
            transaction_type = 'crypto'
        
        # Create base transaction record
        transaction = cls(
            transaction_type=transaction_type,
            risk_score=analysis_result['risk_score'],
            risk_level=analysis_result['risk_level'],
            alerts=analysis_result['alerts'],
            # Use either fiat or crypto amount as the main amount
            amount=transaction_data.get('fiat', {}).get('amount') if has_fiat else transaction_data.get('crypto', {}).get('amount'),
            currency=transaction_data.get('fiat', {}).get('currency') if has_fiat else transaction_data.get('crypto', {}).get('currency')
        )
        
        # Create related detail records
        if has_fiat:
            fiat_data = transaction_data['fiat']
            fiat_details = FiatTransactionDetails(
                card_country=fiat_data.get('card_country'),
                geo_ip=fiat_data.get('geo_ip'),
                mismatch_location=analysis_result.get('fiat_risk', {}).get('mismatch_location', False),
                fatf_listed=analysis_result.get('fiat_risk', {}).get('fatf_listed', False),
                amount_anomaly=analysis_result.get('fiat_risk', {}).get('amount_anomaly', False)
            )
            transaction.fiat_details = fiat_details
        
        if has_crypto:
            crypto_data = transaction_data['crypto']
            crypto_details = CryptoTransactionDetails(
                address=crypto_data.get('address'),
                mixer_interaction=analysis_result.get('crypto_risk', {}).get('mixer_interaction', False),
                suspicious_patterns=analysis_result.get('crypto_risk', {}).get('suspicious_patterns', False),
                known_risky=analysis_result.get('crypto_risk', {}).get('known_risky', False)
            )
            transaction.crypto_details = crypto_details
        
        return transaction


class FiatTransactionDetails(db.Model):
    """Fiat transaction specific details"""
    __tablename__ = 'fiat_transaction_details'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    transaction = relationship("Transaction", back_populates="fiat_details")
    
    # Fiat-specific fields
    card_country = Column(String(2), nullable=True)
    geo_ip = Column(String(50), nullable=True)  # IP or country code
    
    # Risk factors
    mismatch_location = Column(Boolean, default=False)
    fatf_listed = Column(Boolean, default=False)
    amount_anomaly = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<FiatDetails(id={self.id}, country={self.card_country})>"


class CryptoTransactionDetails(db.Model):
    """Cryptocurrency transaction specific details"""
    __tablename__ = 'crypto_transaction_details'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    transaction = relationship("Transaction", back_populates="crypto_details")
    
    # Crypto-specific fields
    address = Column(String(100), nullable=True)
    
    # Risk factors
    mixer_interaction = Column(Boolean, default=False)
    suspicious_patterns = Column(Boolean, default=False)
    known_risky = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<CryptoDetails(id={self.id}, address={self.address})>"