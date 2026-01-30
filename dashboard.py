import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client

# --- Configuration ---
st.set_page_config(page_title="Crypto Bot Dashboard", layout="wide", page_icon="🤖")

# Cache keys and connection to avoid reloading on every interaction
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_supabase()

def get_data():
    if not supabase:
        st.error("Missing Supabase credentials.")
        return pd.DataFrame()
    
    # Fetch logs from Supabase
    try:
        response = supabase.table("trading_logs").select("*").order("created_at", desc=True).limit(100).execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- Layout ---
st.title("🤖 Crypto Trading Bot - Command Center")

# Refresh Button
if st.button("🔄 Update Data"):
    st.cache_data.clear()

df = get_data()

if df.empty:
    st.warning("No trading data found yet.")
else:
    # --- KPIs ---
    latest_entry = df.iloc[0]
    current_price = latest_entry.get('price', 0)
    current_sentiment = latest_entry.get('sentiment', 'NEUTRAL')
    current_confidence = latest_entry.get('confidence', 0.0)
    
    # Calculate Performance Metrics (Simple approximation based on 'pnl' column)
    # We filter only SELL actions to calculate realized PnL
    closed_trades = df[df['action'] == 'SELL']
    total_trades = len(closed_trades)
    win_rate = (closed_trades[closed_trades['pnl'] > 0].shape[0] / total_trades * 100) if total_trades > 0 else 0
    total_profit_pct = closed_trades['pnl'].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${current_price:,.2f}")
    with col2:
        st.metric("Latest Sentiment", current_sentiment, f"{current_confidence:.2f}")
    with col3:
        st.metric("Win Rate", f"{win_rate:.1f}%", f"{total_trades} Trades")
    with col4:
        st.metric("Total Profit (Pct)", f"{total_profit_pct:.2f}%")

    # --- Charts ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Price Evolution")
        # Line Chart for Price
        fig_price = px.line(df, x='created_at', y='price', title='Asset Price Over Time', markers=True)
        # Color line based on sentiment trend if possible, simpler: just price
        fig_price.update_layout(xaxis_title="Time", yaxis_title="Price (USDT)")
        st.plotly_chart(fig_price, use_container_width=True)

    with c2:
        st.subheader("AI Sentiment Gauge")
        # Gauge Chart
        # Map sentiment to value: Bearish=-1, Neutral=0, Bullish=1
        sent_val = 0
        if current_sentiment == "BULLISH": sent_val = 1
        elif current_sentiment == "BEARISH": sent_val = -1
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = sent_val,
            title = {'text': "AI Sentiment Score"},
            delta = {'reference': 0},
            gauge = {
                'axis': {'range': [-1, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [-1, -0.3], 'color': "red"},
                    {'range': [-0.3, 0.3], 'color': "gray"},
                    {'range': [0.3, 1], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': sent_val
                }
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # --- Data Table ---
    st.subheader("Recent Trading Logs")
    st.dataframe(df[['created_at', 'action', 'price', 'sentiment', 'confidence', 'pnl']], use_container_width=True)
