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
def init_exchange():
    api_key = os.environ.get("BYBIT_API_KEY")
    secret = os.environ.get("BYBIT_SECRET_KEY")
    
    if not api_key or not secret:
        return None
        
    try:
        # Using 'linear' (USDT Perpetual) as default for fetch_positions consistency
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': secret,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True
            }
        })
        exchange.set_sandbox_mode(True)
        return exchange
    except:
        return None

supabase = init_supabase()
exchange = init_exchange()

# --- Data Functions ---
def get_candles(symbol="BTC/USDT", timeframe="1h", limit=100):
    if not exchange: return pd.DataFrame()
    try:
        # Use Linear Perpetual symbol format for V5
        target_symbol = symbol
        if "USDT" in symbol and ":" not in symbol:
            target_symbol = symbol + ":USDT"

        ohlcv = exchange.fetch_ohlcv(target_symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        # st.sidebar.warning(f"Error fetching candles: {e}")
        return pd.DataFrame()

def get_positions():
    if not exchange: return []
    try:
        # Fetch positions for linear markets (USDT perps)
        positions = exchange.fetch_positions(symbols=["BTC/USDT:USDT", "ETH/USDT:USDT"])
        active = [p for p in positions if float(p['contracts']) > 0]
        return active
    except:
        return []

def get_balance():
    if not exchange: return 0.0, 0.0
    try:
        # Forzar consulta a cuenta UNIFIED
        params = {'accountType': 'UNIFIED'}
        balance = exchange.fetch_balance(params)
        
        # Estructura real de Bybit V5: result -> list -> [0] -> totalEquity
        # Accedemos a través del campo 'info' que contiene la respuesta cruda de la API
        if 'info' in balance and 'result' in balance['info'] and 'list' in balance['info']['result']:
            equity = balance['info']['result']['list'][0]['totalEquity']
            val = float(equity)
            return val, val

        return 0.0, 0.0
    except Exception as e:
        # st.error(f"Error de conexión con Bybit: {e}")
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
bal_wallet, bal_equity = get_balance()
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
m1.metric("💰 Wallet Balance", f"${bal_wallet:,.2f}")
m2.metric("💎 Equity", f"${bal_equity:,.2f}", delta=f"{bal_equity-bal_wallet:+.2f}")
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
    df_candles = get_candles("BTC/USDT", "1h")
    
    fig = go.Figure()
    
    if not df_candles.empty:
        # Candlestick Chart
        fig.add_trace(go.Candlestick(
            x=df_candles['timestamp'],
            open=df_candles['open'], high=df_candles['high'],
            low=df_candles['low'], close=df_candles['close'],
            name='BTC/USDT'
        ))
    elif not df_logs.empty:
        # Fallback: Line Chart from DB Logs
        st.warning("⚠️ No candle data from Bybit. Showing execution history from Database.")
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
            side = pos['side'].upper()
            st.markdown(f"""
            <div style="background-color: #161a25; border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                <strong>{pos['symbol']}</strong> <span style="float:right; font-size:0.8em;">{side}</span><br>
                <div style="margin-top:5px; font-size:1.1em;">
                   uPnL: <span style="color:{'#00ff00' if float(pos['unrealizedPnl'])>=0 else '#ff0000'}">
                   {float(pos['unrealizedPnl']):.2f} USDT
                   </span>
                </div>
                <div style="font-size:0.8em; color:#888; margin-top:5px;">
                    Size: {pos['contracts']} | Entry: ${pos['entryPrice']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active positions found in Bybit.")

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
st.caption("System: Antigravity | Environment: Bybit Testnet | Data: Supabase & ccxt")
