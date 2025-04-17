import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import os
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from data_generator import generate_sample_transaction

# Configure page
st.set_page_config(
    page_title="AI Fraud Detection - ItisPay",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_URL = os.environ.get("API_URL", "http://localhost:8000")  # FastAPI endpoint

# Custom styling
st.markdown("""
<link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .st-emotion-cache-1629p8f {
        display: inline-block;
    }
    .risk-score-container {
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .low-risk {
        background-color: rgba(0, 128, 0, 0.2);
        border: 1px solid rgba(0, 128, 0, 0.5);
    }
    .medium-risk {
        background-color: rgba(255, 165, 0, 0.2);
        border: 1px solid rgba(255, 165, 0, 0.5);
    }
    .high-risk {
        background-color: rgba(255, 0, 0, 0.2);
        border: 1px solid rgba(255, 0, 0, 0.5);
    }
    .critical-risk {
        background-color: rgba(128, 0, 0, 0.2);
        border: 1px solid rgba(128, 0, 0, 0.5);
    }
    .alert-container {
        background-color: rgba(32, 32, 32, 0.3);
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .alert-icon {
        color: #FFD700;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

def create_risk_gauge(risk_score):
    """Create a risk gauge visualization using Plotly"""
    
    # Define color based on risk score
    if risk_score < 30:
        color = "green"
    elif risk_score < 70:
        color = "orange"
    elif risk_score < 90:
        color = "red"
    else:
        color = "darkred"
    
    # Create gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risk Score"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "rgba(50, 50, 50, 0.2)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': 'rgba(0, 128, 0, 0.3)'},
                {'range': [30, 70], 'color': 'rgba(255, 165, 0, 0.3)'},
                {'range': [70, 90], 'color': 'rgba(255, 0, 0, 0.3)'},
                {'range': [90, 100], 'color': 'rgba(128, 0, 0, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    
    # Update layout
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font={'color': "white", 'family': "Arial"}
    )
    
    return fig

def analyze_transaction(transaction_data):
    """
    Send transaction to API for analysis
    
    Args:
        transaction_data: Dictionary with transaction details
        
    Returns:
        API response or error message
    """
    try:
        response = requests.post(
            f"{API_URL}/fraud-check",
            json=transaction_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

def display_analysis_results(results):
    """
    Display the analysis results in the UI
    
    Args:
        results: Analysis results from the API
    """
    if not results:
        return
    
    # Extract data
    risk_score = results.get('risk_score', 0)
    risk_level = results.get('risk_level', 'Unknown')
    alerts = results.get('alerts', [])
    fiat_risk = results.get('fiat_risk', None)
    crypto_risk = results.get('crypto_risk', None)
    processing_time = results.get('processing_time', 0)
    
    # Create columns for main metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk Score Gauge
        st.plotly_chart(create_risk_gauge(risk_score), use_container_width=True)
    
    with col2:
        # Risk level and details
        risk_class = ""
        if risk_level == "Low":
            risk_class = "low-risk"
        elif risk_level == "Medium":
            risk_class = "medium-risk"
        elif risk_level == "High":
            risk_class = "high-risk"
        elif risk_level == "Critical":
            risk_class = "critical-risk"
        
        st.markdown(f"""
        <div class="risk-score-container {risk_class}">
            <h2>{risk_level} Risk</h2>
            <p>Overall Risk Score: {risk_score}/100</p>
            <p>Processing Time: {processing_time} seconds</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display alerts
    st.subheader("Risk Alerts")
    if alerts:
        for alert in alerts:
            alert_type = "Fiat" if alert.startswith("Fiat") else "Crypto" if alert.startswith("Crypto") else "General"
            st.markdown(f"""
            <div class="alert-container">
                <span class="alert-icon">⚠️</span> <strong>{alert_type}:</strong> {alert.replace('Fiat: ', '').replace('Crypto: ', '')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No risk alerts detected")
    
    # Create tabs for detailed analysis
    tab1, tab2, tab3 = st.tabs(["Combined Analysis", "Fiat Analysis", "Crypto Analysis"])
    
    with tab1:
        # Combined analysis visualization
        st.subheader("Cross-Channel Risk Analysis")
        
        # Create a bar chart comparing fiat and crypto risks
        fiat_risk_score = fiat_risk.get('score', 0) if fiat_risk else 0
        crypto_risk_score = crypto_risk.get('score', 0) if crypto_risk else 0
        
        data = pd.DataFrame({
            'Channel': ['Fiat', 'Crypto', 'Combined'],
            'Risk Score': [fiat_risk_score, crypto_risk_score, risk_score]
        })
        
        fig = px.bar(
            data, 
            x='Channel', 
            y='Risk Score',
            color='Risk Score',
            color_continuous_scale=['green', 'yellow', 'red'],
            range_color=[0, 100],
            title="Risk Scores Across Channels"
        )
        
        fig.update_layout(
            height=400,
            paper_bgcolor='rgba(0, 0, 0, 0)',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            font={'color': "white"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk Contribution 
        st.subheader("Risk Contribution Analysis")
        
        # Only show if both channels are present
        if fiat_risk and crypto_risk:
            contribution_data = {
                'Channel': ['Fiat', 'Crypto'],
                'Contribution': [fiat_risk_score * 0.5, crypto_risk_score * 0.5]
            }
            
            fig = px.pie(
                pd.DataFrame(contribution_data),
                values='Contribution',
                names='Channel',
                title='Risk Contribution by Channel',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            
            fig.update_layout(
                height=400,
                paper_bgcolor='rgba(0, 0, 0, 0)',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                font={'color': "white"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Fiat analysis details
        st.subheader("Fiat Transaction Analysis")
        
        if fiat_risk:
            st.markdown(f"**Risk Score:** {fiat_risk.get('score', 0)}/100")
            
            # Display fiat-specific alerts
            fiat_alerts = fiat_risk.get('alerts', [])
            if fiat_alerts:
                st.subheader("Fiat Alerts")
                for alert in fiat_alerts:
                    st.markdown(f"⚠️ {alert}")
            else:
                st.info("No fiat-specific alerts detected")
            
            # Display geo visualization if applicable
            if any("Geo mismatch" in alert for alert in fiat_alerts):
                st.subheader("Geographic Risk Visualization")
                st.warning("Geographical mismatch detected in transaction")
                
                # This would be enhanced with an actual map in a real implementation
                st.text("A map visualization would be shown here in the full implementation")
        else:
            st.info("No fiat transaction data provided")
    
    with tab3:
        # Crypto analysis details
        st.subheader("Crypto Transaction Analysis")
        
        if crypto_risk:
            st.markdown(f"**Risk Score:** {crypto_risk.get('score', 0)}/100")
            
            # Display crypto-specific alerts
            crypto_alerts = crypto_risk.get('alerts', [])
            if crypto_alerts:
                st.subheader("Crypto Alerts")
                for alert in crypto_alerts:
                    st.markdown(f"⚠️ {alert}")
            else:
                st.info("No crypto-specific alerts detected")
            
            # Display mixer visualization if applicable
            if any("mixer" in alert.lower() for alert in crypto_alerts):
                st.subheader("Mixer Interaction Visualization")
                st.warning("Interactions with mixer services detected")
                
                # In a real implementation, this would show a network graph
                st.text("A network graph visualization would be shown here in the full implementation")
        else:
            st.info("No crypto transaction data provided")

def fetch_transaction_history(
    limit=20, 
    offset=0, 
    min_risk=None, 
    max_risk=None, 
    transaction_type=None
):
    """
    Fetch transaction history from the API
    
    Args:
        limit: Maximum number of transactions
        offset: Pagination offset
        min_risk: Minimum risk score
        max_risk: Maximum risk score
        transaction_type: Filter by transaction type
        
    Returns:
        dict: Transaction history data
    """
    params = {"limit": limit, "offset": offset}
    
    if min_risk is not None:
        params["min_risk"] = min_risk
    
    if max_risk is not None:
        params["max_risk"] = max_risk
    
    if transaction_type:
        params["transaction_type"] = transaction_type
    
    try:
        response = requests.get(f"{API_URL}/transactions", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching transaction history: {e}")
        return {"transactions": [], "total": 0}

def show_transaction_history():
    """Display transaction history page"""
    st.title("Transaction History")
    
    # Filters sidebar
    st.sidebar.title("Filters")
    
    min_risk = st.sidebar.slider(
        "Minimum Risk Score", 
        min_value=0.0, 
        max_value=100.0, 
        value=0.0, 
        step=5.0
    )
    
    max_risk = st.sidebar.slider(
        "Maximum Risk Score", 
        min_value=0.0, 
        max_value=100.0, 
        value=100.0, 
        step=5.0
    )
    
    transaction_type = st.sidebar.selectbox(
        "Transaction Type",
        options=["All", "fiat", "crypto", "both"],
        index=0
    )
    
    transaction_type = None if transaction_type == "All" else transaction_type
    
    # Pagination
    items_per_page = st.sidebar.selectbox(
        "Items per page",
        options=[10, 20, 50, 100],
        index=1
    )
    
    # Fetch data
    history_data = fetch_transaction_history(
        limit=items_per_page,
        min_risk=min_risk if min_risk > 0 else None,
        max_risk=max_risk if max_risk < 100 else None,
        transaction_type=transaction_type
    )
    
    total_count = history_data.get("total", 0)
    transactions = history_data.get("transactions", [])
    
    # Total statistics
    st.metric(label="Total Transactions", value=total_count)
    
    if transactions:
        # Convert to dataframe for display
        df = pd.DataFrame([
            {
                "ID": t["id"],
                "Type": t["transaction_type"],
                "Amount": f"{t['amount']} {t['currency']}",
                "Date": t["timestamp"],
                "Risk Score": t["risk_score"],
                "Risk Level": t["risk_level"]
            }
            for t in transactions
        ])
        
        # Risk level color mapping
        def color_risk_level(val):
            if val == "Low":
                return 'background-color: green; color: white'
            elif val == "Medium":
                return 'background-color: yellow; color: black'
            elif val == "High":
                return 'background-color: orange; color: black'
            else:  # Critical
                return 'background-color: red; color: white'
        
        # Apply styling
        styled_df = df.style.applymap(
            color_risk_level, 
            subset=['Risk Level']
        )
        
        # Display table
        st.dataframe(styled_df)
        
        # Risk distribution chart
        st.subheader("Risk Distribution")
        risk_counts = df["Risk Level"].value_counts().reset_index()
        risk_counts.columns = ["Risk Level", "Count"]
        
        # Set a specific order for risk levels
        risk_order = ["Low", "Medium", "High", "Critical"]
        risk_counts["Risk Level"] = pd.Categorical(
            risk_counts["Risk Level"], 
            categories=risk_order
        )
        risk_counts = risk_counts.sort_values("Risk Level")
        
        # Colors for each risk level
        risk_colors = {
            "Low": "green",
            "Medium": "yellow",
            "High": "orange",
            "Critical": "red"
        }
        
        fig = px.bar(
            risk_counts, 
            x="Risk Level", 
            y="Count",
            color="Risk Level",
            color_discrete_map=risk_colors,
            title="Distribution of Risk Levels"
        )
        
        st.plotly_chart(fig)
        
    else:
        st.info("No transactions found matching the criteria")

def fraud_check_page():
    """Display the fraud check page"""
    st.markdown("### Cross-Channel Fraud Detection for Fiat and Crypto Transactions")
    st.markdown("---")
    
    # Sidebar options for fraud check
    st.sidebar.header("Options")
    
    # Option to use a sample transaction
    use_sample = st.sidebar.checkbox("Use sample transaction", value=False)
    
    # Main form
    st.subheader("Transaction Details")
    
    # Form for transaction input
    with st.form("transaction_form"):
        # Sample transaction data if requested
        sample_data = generate_sample_transaction() if use_sample else None
        
        # Create tabs for fiat and crypto inputs
        input_tab1, input_tab2 = st.tabs(["Fiat Transaction", "Crypto Transaction"])
        
        with input_tab1:
            # Fiat transaction inputs
            include_fiat = st.checkbox("Include Fiat Transaction", value=True)
            
            if include_fiat:
                col1, col2 = st.columns(2)
                
                with col1:
                    fiat_amount = st.number_input(
                        "Amount",
                        min_value=0.01,
                        max_value=1000000.0,
                        value=sample_data["fiat"]["amount"] if sample_data else 1000.0,
                        step=100.0
                    )
                    
                    fiat_currency = st.selectbox(
                        "Currency",
                        options=["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF"],
                        index=0 if not sample_data else ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF"].index(sample_data["fiat"]["currency"])
                    )
                
                with col2:
                    card_country = st.selectbox(
                        "Card Country",
                        options=["US", "GB", "DE", "FR", "JP", "AU", "CA", "CH", "CN", "RU", "IN", "BR", "NG"],
                        index=0 if not sample_data else ["US", "GB", "DE", "FR", "JP", "AU", "CA", "CH", "CN", "RU", "IN", "BR", "NG"].index(sample_data["fiat"]["card_country"])
                    )
                    
                    geo_ip = st.text_input(
                        "IP Address or Country Code",
                        value=sample_data["fiat"]["geo_ip"] if sample_data else "US"
                    )
            
        with input_tab2:
            # Crypto transaction inputs
            include_crypto = st.checkbox("Include Crypto Transaction", value=True)
            
            if include_crypto:
                col1, col2 = st.columns(2)
                
                with col1:
                    crypto_address = st.text_input(
                        "Wallet Address",
                        value=sample_data["crypto"]["address"] if sample_data else "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                    )
                
                with col2:
                    crypto_currency = st.selectbox(
                        "Cryptocurrency",
                        options=["ETH", "BTC", "USDT", "USDC"],
                        index=0 if not sample_data else ["ETH", "BTC", "USDT", "USDC"].index(sample_data["crypto"]["currency"])
                    )
                    
                    crypto_amount = st.number_input(
                        "Amount",
                        min_value=0.000001,
                        max_value=1000.0,
                        value=sample_data["crypto"]["amount"] if sample_data else 0.1,
                        format="%.6f"
                    )
        
        # Submit button
        submitted = st.form_submit_button("Analyze Transaction")
    
    # Process the form submission
    if submitted:
        # Build the transaction data
        transaction_data = {}
        
        if include_fiat:
            transaction_data["fiat"] = {
                "amount": fiat_amount,
                "currency": fiat_currency,
                "card_country": card_country,
                "geo_ip": geo_ip
            }
        
        if include_crypto:
            transaction_data["crypto"] = {
                "address": crypto_address,
                "currency": crypto_currency,
                "amount": crypto_amount
            }
        
        # Validate that at least one transaction type is included
        if not include_fiat and not include_crypto:
            st.error("Please include at least one transaction type (fiat or crypto)")
        else:
            # Show a spinner while analyzing
            with st.spinner("Analyzing transaction..."):
                # Send to API for analysis
                results = analyze_transaction(transaction_data)
                
                # Display the results
                if results:
                    st.success("Analysis complete!")
                    st.markdown("---")
                    display_analysis_results(results)


def main():
    """Main application entry point"""
    # Header
    st.title("🛡️ AI Fraud Detection - ItisPay")
    
    # Add navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Fraud Check", "Transaction History"]
    )
    
    # Sidebar information section
    st.sidebar.header("About")
    st.sidebar.markdown("""
    This AI-powered fraud detection system analyzes both fiat and crypto transactions to provide a unified risk score.
    
    **Features:**
    - Fiat transaction anomaly detection
    - Crypto transaction risk analysis
    - Cross-channel risk scoring
    - Explainable alerts
    """)
    
    st.sidebar.markdown("---")
    
    # Show the selected page
    if page == "Fraud Check":
        fraud_check_page()
    else:
        show_transaction_history()

if __name__ == "__main__":
    main()
