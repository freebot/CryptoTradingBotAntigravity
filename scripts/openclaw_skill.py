import requests
import json
import time
import random
from datetime import datetime

import os

# --- CONFIGURATION ---
# Configura aquí la IP de tu servidor Antigravity (AWS, Local, etc.)
DEFAULT_URL = "http://52.1.65.187:8000" 
ANTIGRAVITY_URL = os.getenv("ANTIGRAVITY_URL", DEFAULT_URL)

MARKET_ENDPOINT = f"{ANTIGRAVITY_URL}/market/status"
SIGNAL_ENDPOINT = f"{ANTIGRAVITY_URL}/openclaw/signal"

print(f"🔌 OpenClaw Skill conectando a: {ANTIGRAVITY_URL}")

def fetch_market_data():
    """Obtiene los datos actuales del mercado desde Antigravity."""
    try:
        response = requests.get(MARKET_ENDPOINT, timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Market Data Received: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        return None

def analyze_market(data):
    """
    Simula la inteligencia avanzada de OpenClaw.
    """
    if not data:
        return None

    # Extraer datos con el nuevo formato
    price = data.get("current_price", 0)
    rsi = data.get("rsi", 50)
    trend = data.get("trend", "neutral")
    ma_50 = data.get("moving_average", 0)
    volume = data.get("volume", 0)
    
    print(f"🧠 OpenClaw Thinking... (Price: {price}, RSI: {rsi}, Trend: {trend})")
    
    # Init Signal Structure
    signal_payload = {
        "signal": "hold",
        "confidence": 0.5,
        "sentiment_analysis": "Market is stable, watching...",
        "timestamp": datetime.now().isoformat(),
        "source": "OpenClaw_Skill_v1",
        "additional_data": {
            "strategy": "RSI_Trend_Follow",
            "internal_score": 0
        }
    }

    # Estrategia simple de Ejemplo
    # Si la tendencia es UP y el RSI no está sobrecomprado (>70), considerar COMPRA
    if trend == "up" and rsi < 70:
        if rsi < 40: # Pullback en tendencia alcista
            signal_payload["signal"] = "buy"
            signal_payload["confidence"] = 0.85
            signal_payload["sentiment_analysis"] = f"Strong Uptrend with RSI Pullback ({rsi:.1f}). Buying dip."
        else:
            signal_payload["signal"] = "buy"
            signal_payload["confidence"] = 0.65 # Confianza media
            signal_payload["sentiment_analysis"] = "Trend is Up. Accumulating."

    elif trend == "down" and rsi > 30:
        if rsi > 60: # Rebote en tendencia bajista
            signal_payload["signal"] = "sell"
            signal_payload["confidence"] = 0.85
            signal_payload["sentiment_analysis"] = f"Downtrend with RSI Spike ({rsi:.1f}). Selling rally."
        else:
            signal_payload["signal"] = "sell"
            signal_payload["confidence"] = 0.65
            signal_payload["sentiment_analysis"] = "Trend is Down. Distributing."

    return signal_payload

def send_signal(signal_payload):
    """Envía la señal de trading a Antigravity."""
    if not signal_payload:
        return

    try:
        response = requests.post(SIGNAL_ENDPOINT, json=signal_payload, timeout=5)
        if response.status_code == 200:
            print(f"🚀 Signal Sent to Antigravity: {signal_payload['signal']} ({signal_payload['confidence']})")
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
    while True:
        run_openclaw_cycle()
        time.sleep(60) 
