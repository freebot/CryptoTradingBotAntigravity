import streamlit as st
import pandas as pd
from supabase import create_client
import ccxt
import os

# --- Page Config ---
st.set_page_config(
    page_title="Crypto Bot Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- Configuration & Styles ---
st.title("🚀 Antigravity Trading Terminal")
st.markdown("### Real-time Market & Bot Intelligence (Bybit Testnet)")

# --- Connections ---
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

@st.cache_resource
def init_exchange():
    api_key = os.environ.get("BYBIT_API_KEY")
    secret = os.environ.get("BYBIT_SECRET_KEY")
    
    if not api_key or not secret:
        return None
        
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': secret,
    })
    exchange.set_sandbox_mode(True)
    return exchange

supabase = init_supabase()
exchange = init_exchange()

# --- Data Fetching ---
def get_trading_data():
    if not supabase:
        st.error("⚠️ Supabase credentials missing.")
        return pd.DataFrame()
    
    try:
        response = supabase.table("trading_logs").select("*").order("created_at", desc=True).limit(500).execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    except Exception as e:
        st.error(f"Error fetching Supabase data: {e}")
        return pd.DataFrame()

def get_real_balance():
    if not exchange:
        return 0.0, 0.0
    try:
        # fetch_balance returns a dict with 'total', 'free', 'used'
        bal = exchange.fetch_balance()
        usdt_total = bal.get('USDT', {}).get('total', 0.0)
        # Assuming we trade BTC for 'Positions' check
        # Or we can check 'used' balance
        return usdt_total, bal
    except Exception as e:
        st.error(f"Error fetching Bybit balance: {e}")
        return 0.0, None

# --- Main App Logic ---
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

# 1. Fetch Real Data
real_balance, full_balance = get_real_balance()
df = get_trading_data()

# 2. Display Top Metrics
col1, col2, col3 = st.columns(3)

# Metrics: Balance
with col1:
    st.metric("💰 Total Balance (Testnet)", f"${real_balance:,.2f} USDT")

# Metrics: Open Positions (Simplified: Non-zero BTC/ETH balance or fetch_positions)
positions_str = "None"
if exchange and full_balance:
    # Try to find any non-zero non-USDT asset
    assets = [k for k, v in full_balance['total'].items() if v > 0 and k != 'USDT']
    if assets:
        positions_str = ", ".join(assets)
    else:
        # Try fetching derivatives positions if applicable, but for Spot it's cleaner above
        pass

with col2:
    st.metric("📊 Posiciones Abiertas", positions_str)

# Metrics: Last PNL
last_pnl = 0.0
if not df.empty:
    # Check last SELL row
    sells = df[df['action'] == 'SELL']
    if not sells.empty:
        last_pnl = sells.iloc[0]['pnl'] # Latest sell PnL

with col3:
    color = "normal"
    if last_pnl > 0: color = "off" # Streamlit metric delta color logic is tricky, usually handled by delta
    st.metric("📉 Mean/Last PNL", f"{last_pnl:.2f}%", delta=f"{last_pnl:.2f}%")

st.divider()

# 3. Chart & Logs
if df.empty:
    st.info("Waiting for historical data in Supabase...")
else:
    # Sort for chart
    df_sorted = df.sort_values(by="created_at")
    
    st.subheader("📈 Ecosystem Price History")
    # Simple line chart of price
    st.line_chart(df_sorted.set_index("created_at")["price"])
    
    st.subheader("📋 Audit Log")
    st.dataframe(
        df[["created_at", "action", "price", "sentiment", "confidence", "pnl"]].sort_values("created_at", ascending=False),
        use_container_width=True
    )
