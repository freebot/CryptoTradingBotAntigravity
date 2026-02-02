import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import ccxt
import os
import datetime
from streamlit_autorefresh import st_autorefresh

# --- Page Config ---
st.set_page_config(
    page_title="Antigravity Terminal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh every 5 minutes (300000ms)
st_autorefresh(interval=300000, key="datarefresh")

# --- Custom CSS for "Pro" Look ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stApp {
        background-color: #0e1117;
        color: white;
    }
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
def init_exchange():
    api_key = os.environ.get("BYBIT_API_KEY")
    secret = os.environ.get("BYBIT_SECRET_KEY")
    
    if not api_key or not secret:
        return None
        
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': secret,
            'options': {'defaultType': 'future'}
        })
        exchange.set_sandbox_mode(True)
        return exchange
    except:
        return None

supabase = init_supabase()
exchange = init_exchange()

# --- Data Functions ---
def get_candles(symbol="BTC/USDT", timeframe="1h", limit=100):
    if not exchange:
        return pd.DataFrame()
    try:
        # Bybit symbol conversion if needed, but 'BTC/USDT:USDT' works with fetch_ohlcv in newer ccxt
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        st.error(f"Error fetching candles: {e}")
        return pd.DataFrame()

def get_positions():
    if not exchange:
        return []
    try:
        positions = exchange.fetch_positions(symbols=["BTC/USDT:USDT"]) 
        active = [p for p in positions if float(p['contracts']) > 0]
        return active
    except Exception:
        return []

def get_balance():
    if not exchange:
        # Fallback to Supabase mock balance or 0 if no exchange
        return 0.0, 0.0
    try:
        bal = exchange.fetch_balance()
        total = float(bal['USDT']['total'])
        # Try to calculate 'Equity' roughly: Total Balance + Unrealized PnL from positions
        equity = total # Start with total
        # Add uPnL if available in balance or from positions
        # Bybit 'total' often includes uPnL in 'equity' field if accessing via specific endpoint,
        # but standard ccxt 'total' is usually wallet balance. Let's check positions for uPnL.
        positions = get_positions()
        upnl = sum([float(p['unrealizedPnl']) for p in positions])
        equity += upnl
        return total, equity
    except:
        return 0.0, 0.0

def get_db_stats():
    if not supabase:
        return pd.DataFrame()
    try:
        # Fetch last 50 logs for chart markers and table
        response = supabase.table("trading_logs").select("*").order("created_at", desc=True).limit(50).execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return df
        
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    except:
        return pd.DataFrame()

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ Settings")
    symbol = st.selectbox("Symbol", ["BTC/USDT:USDT", "ETH/USDT:USDT"])
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d", "15m"])
    if st.button("Refresh Data"):
        st.cache_data.clear()

# --- Main Dashboard ---

# 1. Top Metrics Bar
bal_wallet, bal_equity = get_balance()
active_positions = get_positions()
df_logs = get_db_stats()

# Calculate realized PnL from logs if possible or just use equity
realized_pnl = 0.0
if not df_logs.empty:
    realized_pnl = df_logs[df_logs['action'].str.contains('CLOSE', na=False)]['pnl'].sum()

last_sentiment = "NEUTRAL"
last_confidence = 0.0
if not df_logs.empty:
    last_sentiment = df_logs.iloc[0]['sentiment']
    last_confidence = df_logs.iloc[0]['confidence']

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Wallet Balance", f"${bal_wallet:,.2f}")
m2.metric("💎 Equity", f"${bal_equity:,.2f}", delta=f"{bal_equity-bal_wallet:+.2f}")
m3.metric("📈 Total Realized PnL (Logs)", f"{realized_pnl:+.2f}%")
m4.metric("🤖 AI Sentiment", f"{last_sentiment}", f"{last_confidence:.2f} Conf.")

st.markdown("---")

# 2. Main Layout: Chart with Markers (Left 75%) + Positions/Logs (Right 25%)
c1, c2 = st.columns([3, 1])

with c1:
    st.subheader(f"📊 {symbol} Price Action & Trade Markers")
    df_candles = get_candles(symbol, timeframe)
    
    if not df_candles.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_candles['timestamp'],
            open=df_candles['open'],
            high=df_candles['high'],
            low=df_candles['low'],
            close=df_candles['close'],
            name='Price'
        )])
        
        # Add Markers from Logs (Superimpose)
        if not df_logs.empty:
            # Filter trades within the candle time range roughly
            min_time = df_candles['timestamp'].min()
            recent_trades = df_logs[df_logs['created_at'] >= min_time]
            
            for _, trade in recent_trades.iterrows():
                color = "green" if "BUY" in trade['action'] or "OPEN_LONG" in trade['action'] or "CLOSE_SHORT" in trade['action'] else "red"
                symbol_marker = "triangle-up" if color == "green" else "triangle-down"
                
                fig.add_trace(go.Scatter(
                    x=[trade['created_at']],
                    y=[trade['price']],
                    mode='markers',
                    marker=dict(symbol=symbol_marker, size=12, color=color),
                    name=trade['action'],
                    hoverinfo='text',
                    hovertext=f"{trade['action']} <br>Price: {trade['price']} <br>Sent: {trade['sentiment']}"
                ))

        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="white"),
            xaxis_rangeslider_visible=False,
            # legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No candle data available.")

with c2:
    st.subheader("⚡ Live Positions")
    if active_positions:
        for pos in active_positions:
            side = pos['side'].upper() # LONG / SHORT
            size = pos['contracts']
            entry = pos['entryPrice']
            upnl = pos['unrealizedPnl']
            
            st.markdown(f"""
            <div style="border:1px solid #444; padding:10px; border-radius:5px; margin-bottom:10px; background-color: #161a25;">
                <strong>{pos['symbol']}</strong> <br>
                <span style="color:{'#00ff00' if side=='LONG' else '#ff0000'}">{side}</span> x{size}<br>
                Entry: ${entry}<br>
                uPnL: <span style="color:{'#00ff00' if float(upnl)>0 else '#ff0000'}">{upnl} USDT</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active positions.")
        
    st.subheader("📜 Recent History")
    if not df_logs.empty:
        # Show table of last 20 actions
        display_cols = ["created_at", "action", "price", "pnl"]
        st.dataframe(
            df_logs[display_cols].head(20),
            column_config={
                "created_at": st.column_config.DatetimeColumn("Time", format="MM-DD HH:mm"),
                "price": st.column_config.NumberColumn("Price"),
                "pnl": st.column_config.NumberColumn("PnL %", format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )

# --- Footer ---
st.markdown("---")
st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Auto-refresh active (5min).")
