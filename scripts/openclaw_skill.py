import requests
import json
import time
import random
from datetime import datetime, timedelta

import os

# --- CONFIGURATION ---
# Configura aquí la IP de tu servidor Antigravity (AWS, Local, etc.)
DEFAULT_URL = "https://fr33b0t-crypto-bot.hf.space"
ANTIGRAVITY_URL = os.getenv("ANTIGRAVITY_URL", DEFAULT_URL)
OPENCLAW_SECRET = os.getenv("OPENCLAW_SECRET", "changeme_in_production")

WAKEUP_ENDPOINT = f"{ANTIGRAVITY_URL}/wake_up"
MARKET_ENDPOINT = f"{ANTIGRAVITY_URL}/market/status"
SIGNAL_ENDPOINT = f"{ANTIGRAVITY_URL}/openclaw/signal"
ORDER_ENDPOINT = f"{ANTIGRAVITY_URL}/openclaw/orders"

HEADERS = {
    "X-Auth-Token": OPENCLAW_SECRET,
    "Content-Type": "application/json"
}

def wake_up_server():
    try:
        requests.get(WAKEUP_ENDPOINT, timeout=5)
#        print("⏰ Ping sent to wake up server.")
    except:
        pass

def fetch_market_data():
    """Obtiene los datos actuales del mercado desde Antigravity."""
    try:
        # 1. First, try to ping to ensure it's awake
        # wake_up_server()
        
        response = requests.get(MARKET_ENDPOINT, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check staleness
        server_ts_iso = data.get("timestamp")
        if server_ts_iso:
            try:
                server_ts = datetime.fromisoformat(server_ts_iso)
                age = (datetime.now() - server_ts).total_seconds()
                if age > 600: # 10 minutes
                    print(f"⚠️ DATA IS OLD ({int(age/60)} mins ago). Server might be frozen.")
                    # Try to hit health check to see status
                    try:
                       health = requests.get(ANTIGRAVITY_URL, timeout=5).json()
                       print(f"🏥 Health Status: {health}")
                    except:
                       print("💀 Server unreachable via Health Check.")
            except:
                pass

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
        response = requests.post(SIGNAL_ENDPOINT, json=signal_payload, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            print(f"🚀 Signal Sent to Antigravity: {signal_payload['signal']} ({signal_payload['confidence']})")
        else:
            print(f"⚠️ Signal rejected: {response.text}")
    except Exception as e:
        print(f"❌ Error sending signal: {e}")

def execute_order(side, amount=0.01, reason="OpenClaw_Direct", sentiment="NEUTRAL", confidence=0.5):
    """
    Ejecuta una orden directa en el bot Antigravity.
    side: 'buy' o 'sell'
    amount: Cantidad de BTC (o la moneda base)
    """
    payload = {
        "side": side,
        "amount": amount,
        "reason": reason,
        "sentiment": sentiment,
        "confidence": confidence
    }
    
    print(f"⚡ Executing Direct Order: {side.upper()} {amount}...")
    try:
        response = requests.post(ORDER_ENDPOINT, json=payload, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Order Executed: {data}")
            return True
        else:
            print(f"❌ Order Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error executing order: {e}")
        return False

def run_openclaw_cycle():
    """Ejecuta un ciclo de análisis."""
    print("--- OpenClaw Agent Cycle Start ---")
    market_data = fetch_market_data()
    if market_data:
        decision = analyze_market(market_data)
        send_signal(decision)
    print("--- Cycle End ---\n")

if __name__ == "__main__":
    sleep_interval = int(os.getenv("SLEEP_INTERVAL", 60))
    print(f"⏱️ OpenClaw loop started. Interval: {sleep_interval}s")
    while True:
        try:
            run_openclaw_cycle()
        except Exception as e:
            print(f"🔥 Critical Error in Main Loop: {e}")
        
        time.sleep(sleep_interval) 
