import requests
import json
import time
import random

# --- CONFIGURATION ---
ANTIGRAVITY_URL = "http://127.0.0.1:8000"  # Local URL where Antigravity is running
MARKET_ENDPOINT = f"{ANTIGRAVITY_URL}/market/status"
SIGNAL_ENDPOINT = f"{ANTIGRAVITY_URL}/openclaw/signal"

def fetch_market_data():
    """Obtiene los datos actuales del mercado desde Antigravity."""
    try:
        response = requests.get(MARKET_ENDPOINT, timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Market Data Received: {data}")
        return data
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        return None

def analyze_market(data):
    """
    Simula la inteligencia avanzada de OpenClaw.
    Aquí es donde conectarías tu modelo de LLM real o estrategia compleja.
    """
    if not data:
        return None

    price = data.get("price", 0)
    indicators = data.get("indicators", {})
    rsi = indicators.get("rsi", 50)
    
    # --- LOGICA DE EJEMPLO (MEJORAR CON LLM) ---
    print(f"🧠 OpenClaw Thinking... (Price: {price}, RSI: {rsi})")
    
    signal = {
        "action": "hold",
        "sentiment": "NEUTRAL",
        "confidence": 0.5,
        "reason": "Market is stable, watching..."
    }

    # Estrategia simple de Momentum + RSI
    if rsi < 30:
        signal["action"] = "buy"
        signal["sentiment"] = "BULLISH"
        signal["confidence"] = 0.85
        signal["reason"] = f"RSI Oversold ({rsi:.2f}) - Buying opportunity detected by OpenClaw"
    elif rsi > 70:
        signal["action"] = "sell"
        signal["sentiment"] = "BEARISH"
        signal["confidence"] = 0.85
        signal["reason"] = f"RSI Overbought ({rsi:.2f}) - Selling pressure imminent"
    else:
        # Random "Smart" Insight for the middle range
        if random.random() > 0.8:
            signal["sentiment"] = "BULLISH"
            signal["confidence"] = 0.65
            signal["reason"] = "OpenClaw detects accumulation pattern on lower timeframes."

    return signal

def send_signal(signal):
    """Envía la señal de trading a Antigravity."""
    if not signal:
        return

    try:
        response = requests.post(SIGNAL_ENDPOINT, json=signal, timeout=5)
        if response.status_code == 200:
            print(f"🚀 Signal Sent to Antigravity: {signal}")
        else:
            print(f"⚠️ Signal rejected: {response.text}")
    except Exception as e:
        print(f"❌ Error sending signal: {e}")

def run_openclaw_cycle():
    """Ejecuta un ciclo de análisis."""
    print("--- OpenClaw Agent Cycle Start ---")
    market_data = fetch_market_data()
    if market_data:
        decision = analyze_market(market_data)
        send_signal(decision)
    print("--- Cycle End ---\n")

if __name__ == "__main__":
    # Ejecutar en bucle (o una sola vez si es una Task programada)
    while True:
        run_openclaw_cycle()
        time.sleep(60)  # Analizar cada minuto
