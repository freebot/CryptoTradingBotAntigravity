import streamlit as st
import pandas as pd
from supabase import create_client
import os

# --- Page Config ---
st.set_page_config(
    page_title="Crypto Bot Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- Configuration & Styles ---
st.title("🚀 Antigravity Trading Terminal")
st.markdown("### Real-time Market & Bot Intelligence")

# --- Database Connection ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_connection()

# --- Data Fetching ---
def get_trading_data():
    if not supabase:
        st.error("⚠️ Database connection failed. Check SUPABASE_URL and SUPABASE_KEY secrets.")
        return pd.DataFrame()
    
    try:
        # Fetching logs
        response = supabase.table("trading_logs").select("*").order("created_at", desc=True).limit(500).execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- Main App ---
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

df = get_trading_data()

if df.empty:
    st.info("Waiting for data... The bot hasn't logged any trades yet.")
else:
    # Sort for time-series visualization
    df = df.sort_values(by="created_at")
    last_row = df.iloc[-1]

    # --- KPIs / Metrics ---
    col1, col2, col3 = st.columns(3)
    
    price = last_row.get("price", 0)
    sentiment = last_row.get("sentiment", "N/A")
    confidence = last_row.get("confidence", 0)
    
    # Calculate a mock 'Virtual Balance' based on performance
    # Initial balance 10k, compounding PnL from SELL actions
    balance = 10000.0
    for _, row in df.iterrows():
        if row['action'] == 'SELL':
            pnl_pct = row.get('pnl', 0)
            balance += balance * (pnl_pct / 100.0)

    with col1:
        st.metric("💰 Current Price", f"${price:,.2f}")
    
    with col2:
        st.metric("🧠 AI Sentiment", f"{sentiment}", f"{confidence:.2f} Conf.")
        
    with col3:
        pnl_total = (balance - 10000)
        st.metric("💼 Virtual Balance", f"${balance:,.2f}", f"{pnl_total:+.2f} ({((balance/10000)-1)*100:.2f}%)")

    st.divider()

    # --- Charts ---
    st.subheader("📈 Price History")
    # Setting index for proper x-axis
    chart_data = df.set_index("created_at")[["price"]]
    st.line_chart(chart_data)

    # --- Recent Activity Log ---
    st.subheader("📋 Recent Activity")
    # Show latest first
    st.dataframe(
        df[["created_at", "action", "price", "sentiment", "confidence", "pnl"]].sort_values("created_at", ascending=False),
        use_container_width=True
    )
