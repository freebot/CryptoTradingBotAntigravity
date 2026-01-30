import os
import time
import json
import logging
import random
from src.data_loader import DataLoader
from src.model import SentimentAnalyzer, PricePredictor
from src.trader import Trader
from src.utils import add_indicators
from src.notion_logger import NotionLogger  # <--- Nueva integración

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar configuración
try:
    with open('config/settings.json', 'r') as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {"symbol": "bitcoin", "timeframe": "1h"}

# Para CoinGecko usamos IDs como 'bitcoin' o 'ethereum'
SYMBOL = settings.get("symbol", "bitcoin")
TIMEFRAME = settings.get("timeframe", "1h")

def main():
    print("🚀 Starting Antigravity Crypto Bot (Virtual Edition)...")
    
    # --- INICIALIZACIÓN DE COMPONENTES ---
    data_loader = DataLoader()
    sentiment_model = SentimentAnalyzer()
    price_predictor = PricePredictor()
    trader = Trader(SYMBOL)
    notion = NotionLogger() # <--- Logger de Notion

    # --- SIMULACIÓN DE CARTERA ---
    # En un bot real, esto se leería del exchange. 
    # Aquí lo iniciamos para medir el aprendizaje.
    balance_inicial = 10000.0  # $10,000 USD ficticios
    # Intentamos cargar el balance actual si existe un archivo local, si no, el inicial
    balance_actual = balance_inicial 

    print(f"Tracking {SYMBOL} on {TIMEFRAME} timeframe.")
    print(f"Notion Dashboard: Conectado.")

    # Fuente de noticias para análisis de sentimiento (Demo)
    # En el futuro, Antigravity puede ayudarte a conectar NewsAPI aquí
    fake_news = [
        "Bitcoin adoption grows as major banks open crypto desks.",
        "Market experiences volatility amid global economic shifts.",
        "New institutional interest drives crypto markets higher.",
        "Regulatory updates create temporary uncertainty in trading.",
        "Technological breakthroughs improve blockchain scalability."
    ]

    try:
        while True:
            print("\n--- New Cycle ---")
            
            # 1. OBTENCIÓN DE DATOS (CoinGecko)
            df = data_loader.fetch_ohlcv(SYMBOL, TIMEFRAME)
            
            if df is None or df.empty:
                print("⚠️ No se recibieron datos de mercado. Reintentando...")
                if os.getenv("RUN_ONCE") == "true": break
                time.sleep(60)
                continue
            
            # 2. ANÁLISIS TÉCNICO
            df = add_indicators(df, settings)
            current_price = float(df['close'].iloc[-1])
            print(f"💰 Precio Actual ({SYMBOL}): ${current_price:,.2f}")
            
            technical_signal = price_predictor.predict_next_move(df)
            print(f"📊 Señal Técnica: {technical_signal}")
            
            # 3. ANÁLISIS DE IA (Hugging Face - FinBERT)
            current_news = random.sample(fake_news, 1)
            sentiment, score = sentiment_model.analyze(current_news)
            print(f"🧠 IA Sentiment: {sentiment} (Confianza: {score:.2f})")
            
            # 4. LÓGICA DE DECISIÓN
            action = "HOLD"
            if technical_signal == "UP" and sentiment == "BULLISH":
                action = "BUY"
            elif technical_signal == "DOWN" and sentiment == "BEARISH":
                action = "SELL"
            
            print(f"🎯 Decisión final: {action}")
            
            # 5. EJECUCIÓN VIRTUAL Y NOTION
            # Calculamos un profit simulado muy básico para el dashboard
            # (En BUY el balance baja, en SELL sube, aquí lo simplificamos a % de cambio)
            profit_simulado = balance_actual - balance_inicial

            if action != "HOLD":
                # Ejecutamos en nuestro trader virtual (guarda en CSV local)
                trader.place_order(action.lower(), 0.01, current_price)
                
                # Actualizamos Notion
                # Esta es la parte que alimenta tu pantalla de Notion
                notion.log_trade(
                    action=action,
                    price=current_price,
                    sentiment=sentiment,
                    confidence=score,
                    profit=profit_simulado
                )
            else:
                # Opcional: También puedes loguear los "HOLD" en Notion cada X tiempo
                print("☕ Manteniendo posición. No se enviaron datos a Notion.")

            # --- CONTROL DE EJECUCIÓN (GitHub Actions / Cloud) ---
            if os.getenv("RUN_ONCE") == "true":
                print("\n✅ Ciclo único completado con éxito.")
                break

            print("⏳ Esperando siguiente ciclo (60s)...")
            time.sleep(60)
            
    except Exception as e:
        print(f"❌ Error Crítico: {e}")
        # Intentar reportar el error a Notion antes de morir
        try:
            notion.log_trade("ERROR", 0, str(e)[:20], 0, 0)
        except:
            pass

if __name__ == "__main__":
    main()