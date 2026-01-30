import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import time

# --- Configuration ---
st.set_page_config(page_title="Antigravity Trading Terminal", layout="wide", page_icon="🚀")

# --- Initialize Connections ---
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
        st.error("⚠️ Supabase Credentials (SUPABASE_URL, SUPABASE_KEY) are missing in Space Settings.")
        return pd.DataFrame()
    
    try:
        # Fetch last 200 logs
        response = supabase.table("trading_logs").select("*").order("created_at", desc=True).limit(200).execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        # Ensure created_at is datetime
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    except Exception as e:
        st.error(f"Error connecting to DB: {e}")
        return pd.DataFrame()

# --- Main Dashboard Logic ---
st.title('🚀 Antigravity Trading Terminal')

# Auto-refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

df = get_data()

if df.empty:
    st.info("👋 Welcome! The database is currently empty. Waiting for the bot to make its first move...")
    st.markdown("make sure your bot is running and `UPSTASH_REDIS` + `SUPABASE` variables are set correctly.")

else:
    # --- Data Processing ---
    # Sort by date ascending for calculations
    df_sorted = df.sort_values(by='created_at', ascending=True)
    
    # 1. Metrics Calculation
    latest_log = df_sorted.iloc[-1]
    current_price = latest_log.get('price', 0.0)
    current_sentiment = latest_log.get('sentiment', "NEUTRAL")
    
    # Virtual Balance Calculation (Theoretical)
    # Assumes Start = $10,000 and full compounding on every SELL
    virtual_balance = 10000.0
    for index, row in df_sorted.iterrows():
        if row['action'] == 'SELL':
            # pnl is percentage (e.g., 5.0 for 5%)
            pnl_pct = row.get('pnl', 0.0)
            # Assuming we trade with full portfolio for simplicity of this metric, 
            # or we can assume fixed position. Let's assume proportional growth.
            # Trade logic in Trader.py: virtual_balance += (virtual_balance * (profit_pct / 100))
            # Wait, Trader.py logic was exactly that. So we replicate it.
            virtual_balance += virtual_balance * (pnl_pct / 100)

    # 2. Display Metrics Columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Current Price", f"${current_price:,.2f}")
    
    with col2:
        sentiment_color = "off"
        if current_sentiment == "BULLISH":
            sentiment_color = "normal" # Greenish usually in standard themes or custom delta
        st.metric("🧠 AI Sentiment", current_sentiment, delta=None) # Start simple

    with col3:
        # Show delta from 10k
        pnl_total_pct = ((virtual_balance - 10000) / 10000) * 100
        st.metric("💼 Virtual Balance", f"${virtual_balance:,.2f}", f"{pnl_total_pct:.2f}%")

    # 3. Price Chart
    st.subheader("Price History")
    # Streamlit line_chart expects index to be x-axis usually or specify x/y
    chart_data = df_sorted[['created_at', 'price']].set_index('created_at')
    st.line_chart(chart_data)

    # 4. Recent Trades Table (Raw Data)
    st.subheader("📋 Recent Activity")
    
    # Formatting for display
    display_df = df.copy() # Latest first
    display_df = display_df[['created_at', 'action', 'price', 'sentiment', 'confidence', 'pnl']]
    st.dataframe(display_df, use_container_width=True)
