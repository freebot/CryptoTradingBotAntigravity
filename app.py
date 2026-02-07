import streamlit as st
import pandas as pd
import os
import requests
from alpaca.trading.client import TradingClient
from supabase import create_client

st.set_page_config(page_title="Antigravity Terminal", layout="wide")

# --- VERIFICACIÓN DE SECRETS ---
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')
sb_url = os.getenv("SUPABASE_URL")
sb_key = os.getenv("SUPABASE_KEY")

if not api_key or not secret_key:
    st.error("❌ Faltan las llaves de Alpaca (API_KEY o SECRET_KEY) en los Secrets.")
    st.stop()

# --- CONEXIONES ---
@st.cache_resource
def init_clients():
    # Obligatorio paper=True para dinero ficticio
    alpaca = TradingClient(api_key, secret_key, paper=True)
    sb = create_client(sb_url, sb_key)
    return alpaca, sb

try:
    alpaca, supabase = init_clients()
    account = alpaca.get_account()

    st.title("🚀 Antigravity Trading Terminal")
    
    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    # Mostramos la equidad total (dinero + valor de cryptos)
    m1.metric("Wallet Balance", f"${float(account.equity):,.2f}")
    m2.metric("Cash Available", f"${float(account.cash):,.2f}")
    
    # Leer historial de Supabase
    res = supabase.table("trading_logs").select("*").order("created_at", desc=True).limit(100).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        last = df.iloc[0]
        m3.metric("Realized PnL", f"{last.get('pnl', 0):.2f}%")
        # Color dinámico para el sentimiento
        sent = last['sentiment']
        color = "normal" if sent == "BULLISH" else "inverse"
        m4.metric("AI Sentiment", sent, delta=f"{last['confidence']:.2f} Conf.", delta_color=color)

        # --- GRÁFICA LIMPIA ---
        st.divider()
        st.subheader("📈 Market Overview")
        # LIMPIEZA: Solo graficar si el precio es mayor a 1000 (evita los ceros que vimos en tu captura)
        df_plot = df[df['price'] > 1000].copy()
        df_plot['created_at'] = pd.to_datetime(df_plot['created_at'])
        st.line_chart(df_plot.set_index('created_at')['price'])

        # --- LOGS RECIENTES ---
        st.subheader("📜 Recent History")
        st.dataframe(df[['created_at', 'action', 'price', 'sentiment']], use_container_width=True)
    else:
        st.info("Esperando datos de la base de datos...")

    # --- API CHECK ---
    st.divider()
    st.subheader("🔌 System Status")
    m5, m6 = st.columns(2)
    
    # Check internal API connectivity
    api_online = False
    api_url = "http://127.0.0.1:8000/market/status"
    try:
        resp = requests.get(api_url, timeout=2)
        if resp.status_code == 200:
            api_online = True
    except:
        pass

    if api_online:
        m5.success("✅ Internal API: ONLINE")
    else:
        m5.error("❌ Internal API: OFFLINE (Check Logs)")

    # Display Public URL Helper
    hf_space_host = os.getenv("SPACE_HOST", "fr33b0t-crypto-bot.hf.space") # Default guess
    public_url = f"https://{hf_space_host}"
    
    st.info(f"🔗 **API Public Endpoint**: `{public_url}/market/status` (Use this for OpenClaw)")

except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
