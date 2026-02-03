import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import os
import datetime
from streamlit_autorefresh import st_autorefresh
from alpaca.trading.client import TradingClient

# --- Page Config ---
st.set_page_config(
    page_title="Antigravity Terminal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh every 5 minutes (300000ms)
st_autorefresh(interval=300000, key="datarefresh")

# --- Custom CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    .bullish { color: #00ff00; font-weight: bold; }
    .bearish { color: #ff0000; font-weight: bold; }
    .neutral { color: #aaaaaa; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Antigravity Trading Terminal")

# --- Connections ---
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

@st.cache_resource
def init_alpaca():
    api_key = os.environ.get("ALPACA_API_KEY")
    secret = os.environ.get("ALPACA_SECRET_KEY")
    
    if not api_key or not secret:
        return None
        
    try:
        # Paper Trading Default
        client = TradingClient(api_key, secret, paper=True)
        return client
    except:
        return None

supabase = init_supabase()
trading_client = init_alpaca()

# --- Data Functions ---
def get_candles(symbol="BTC/USD", timeframe="1h", limit=100):
    # For now, we rely on Supabase logs Fallback since migrating candles to Alpaca requires CryptoHistoricalDataClient
    # logic which adds dependency complexity. The user primarily asked for Balance migration.
    # We return empty to trigger the Fallback logic in the UI which plots execution points.
    return pd.DataFrame() 

def get_positions():
    if not trading_client: return []
    try:
        positions = trading_client.get_all_positions()
        # Convert Alpaca Position objects to dict-like structure for the UI
        active = []
        for p in positions:
            active.append({
                'symbol': p.symbol,
                'side': p.side.name if hasattr(p.side, 'name') else str(p.side),
                'contracts': p.qty,
                'entryPrice': p.avg_entry_price,
                'unrealizedPnl': p.unrealized_pl
            })
        return active
    except:
        return []

def get_balance():
    if not trading_client: return 0.0, 0.0
    try:
        account = trading_client.get_account()
        # Alpaca returns strings
        equity = float(account.equity)
        cash = float(account.cash)
        return cash, equity # Return Cash, Equity
    except Exception as e:
        st.sidebar.error(f"Alpaca API Error: {e}")
        return 0.0, 0.0

def get_db_logs():
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table("trading_logs").select("*").order("created_at", desc=True).limit(100).execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            # Filter out zero/null/anomalous prices to prevent chart drops
            df = df[df['price'] > 1000]
        return df
    except:
        return pd.DataFrame()

# --- Main Dashboard ---

# 1. Fetch Data
bal_cash, bal_equity = get_balance()
active_positions = get_positions()
df_logs = get_db_logs()

# Calculate Metrics
realized_pnl = 0.0
last_sentiment = "NEUTRAL"
last_confidence = 0.0

if not df_logs.empty:
    realized_pnl = df_logs[df_logs['action'].str.contains('CLOSE', na=False)]['pnl'].sum()
    
    # Get latest log entry
    latest_log = df_logs.iloc[0]
    last_sentiment = latest_log.get('sentiment', 'WAITING...')
    try:
        last_confidence = float(latest_log.get('confidence', 0.0))
    except:
        last_confidence = 0.0
else:
    realized_pnl = 0.0
    last_sentiment = "WAITING..."
    last_confidence = 0.0

# 2. Top Metrics Bar
m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Wallet Balance", f"${bal_equity:,.2f}") # Shown as Total Equity
m2.metric("💵 Cash Available", f"${bal_cash:,.2f}") # Shown as Cash
m3.metric("📈 Realized PnL", f"{realized_pnl:+.2f}%")

# Custom Sentiment Metric with Color
sent_color = "neutral"
if "bull" in last_sentiment.lower(): sent_color = "bullish"
if "bear" in last_sentiment.lower(): sent_color = "bearish"

m4.markdown(f"""
<div style="text-align: center;">
    <span style="font-size: 0.8rem; color: #888;">AI Sentiment</span><br>
    <span class="{sent_color}" style="font-size: 1.5rem;">{last_sentiment}</span><br>
    <span style="font-size: 0.8rem;">{last_confidence:.2f} Conf.</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# 3. Chart & Details
c1, c2 = st.columns([3, 1])

with c1:
    st.subheader("📊 Market Overview")
    
    # Try getting Candles first
    df_candles = get_candles("BTC/USD", "1h")
    
    fig = go.Figure()
    
    if not df_candles.empty:
        # Candlestick Chart (Placeholder if we implement Alpaca Data)
        fig.add_trace(go.Candlestick(
            x=df_candles['timestamp'],
            open=df_candles['open'], high=df_candles['high'],
            low=df_candles['low'], close=df_candles['close'],
            name='BTC/USD'
        ))
    elif not df_logs.empty:
        # Fallback: Line Chart from DB Logs
        if df_candles.empty:
             st.info("ℹ️ Displaying Trade Execution History (Alpaca Data Pending)")
        
        df_sorted = df_logs.sort_values('created_at')
        fig.add_trace(go.Scatter(
            x=df_sorted['created_at'],
            y=df_sorted['price'],
            mode='lines+markers',
            name='Exec Price',
            line=dict(color='#ffaa00')
        ))
    
    # Add Markers for Actions (works on both charts)
    if not df_logs.empty:
        markers = df_logs[df_logs['action'].isin(['BUY', 'SELL', 'OPEN_LONG', 'OPEN_SHORT', 'CLOSE_LONG', 'CLOSE_SHORT'])]
        for _, trade in markers.iterrows():
            color = "green" if "BUY" in trade['action'] or "LONG" in trade['action'] else "red"
            symbol_mk = "triangle-up" if color == "green" else "triangle-down"
            
            fig.add_trace(go.Scatter(
                x=[trade['created_at']], y=[trade['price']],
                mode='markers',
                marker=dict(symbol=symbol_mk, size=14, color=color),
                name=trade['action'],
                hovertext=f"{trade['action']} @ ${trade['price']}"
            ))

    fig.update_layout(
        height=600,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(color="white"),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("⚡ Active Positions")
    if active_positions:
        for pos in active_positions:
            # Handle string conversions safely
            unrealized_pnl = float(pos['unrealizedPnl']) if pos['unrealizedPnl'] else 0.0
            
            st.markdown(f"""
            <div style="background-color: #161a25; border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                <strong>{pos['symbol']}</strong> <span style="float:right; font-size:0.8em;">{pos['side'].upper()}</span><br>
                <div style="margin-top:5px; font-size:1.1em;">
                   uPnL: <span style="color:{'#00ff00' if unrealized_pnl >= 0 else '#ff0000'}">
                   ${unrealized_pnl:.2f}
                   </span>
                </div>
                <div style="font-size:0.8em; color:#888; margin-top:5px;">
                    Qty: {pos['contracts']} | Entry: ${float(pos['entryPrice']):.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active positions in Alpaca.")

    st.subheader("📜 Recent Logs")
    if not df_logs.empty:
        st.dataframe(
            df_logs[["created_at", "action", "price"]].head(15),
            column_config={
                "created_at": st.column_config.DatetimeColumn("Time", format="HH:mm"),
                "price": st.column_config.NumberColumn("Price")
            },
            hide_index=True,
            use_container_width=True
        )

# Footer
st.markdown("---")
st.caption("System: Antigravity | Environment: Alpaca Paper Trading | Data: Supabase & Alpaca-py")
