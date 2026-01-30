import os
import time
import json
import logging
import random
from src.data_loader import DataLoader
from src.model import SentimentAnalyzer, PricePredictor
from src.trader import Trader
from src.utils import add_indicators
from src.notion_logger import NotionLogger

# Configuración de Logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar configuración o usar valores por defecto
try:
    with open('config/settings.json', 'r') as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {"symbol": "bitcoin", "timeframe": "1h"}

SYMBOL = settings.get("symbol", "bitcoin")
TIMEFRAME = settings.get("timeframe", "1h")

from src.news_fetcher import NewsFetcher

# ... (existing imports)

def main():
    print("\n" + "="*50)
    print("🚀 ANTIGRAVITY CRYPTO BOT - MODO VIRTUAL PRO")
    print("="*50 + "\n")
    
    # --- 1. INICIALIZACIÓN DE COMPONENTES ---
    data_loader = DataLoader()
    sentiment_model = SentimentAnalyzer()
    price_predictor = PricePredictor()
    # Configurar parámetros de riesgo desde settings
    stop_loss = settings.get("stop_loss_pct", 0.02)
    take_profit = settings.get("take_profit_pct", 0.05)
    
    trader = Trader(SYMBOL, stop_loss_pct=stop_loss, take_profit_pct=take_profit)
    notion = NotionLogger()
    news_fetcher = NewsFetcher() # Inicializar NewsFetcher

    # Variables para seguimiento de sesión
    balance_inicial = 10000.0 
    print(f"📡 Monitoreando: {SYMBOL.upper()}")
    print(f"📊 Dashboard Notion: CONECTADO")
    print(f"🛡️ Configuración: SL {stop_loss*100:.1f}% | TP {take_profit*100:.1f}%")

    # Variables de estado para cache de noticias
    last_news_time = 0
    cached_sentiment = "NEUTRAL"
    cached_confidence = 0.0

    try:
        while True:
            print(f"\n--- Ciclo de Mercado: {time.strftime('%H:%M:%S')} ---")
            
            # --- 2. OBTENCIÓN DE DATOS ---
            df = data_loader.fetch_ohlcv(SYMBOL, TIMEFRAME)
            
            if df is None or df.empty:
                print("⚠️ Error de datos (CoinGecko). Reintentando en 60s...")
                if os.getenv("RUN_ONCE") == "true": break
                time.sleep(60)
                continue
            
            # --- 3. ANÁLISIS TÉCNICO Y PRECIO ---
            df = add_indicators(df, settings)
            current_price = float(df['close'].iloc[-1])
            print(f"💰 Precio Actual: ${current_price:,.2f}")

            # --- 4. GESTIÓN DE RIESGO (Prioridad 1) ---
            risk_event, pnl_pct = trader.check_risk_management(current_price)
            
            if risk_event:
                print(f"🚨 {risk_event} DISPARADO! Cerrando posición...")
                trader.place_order("sell", 0.01, current_price, reason=risk_event)
                
                # Actualizar Notion
                notion.log_trade(
                    action=risk_event,
                    price=current_price,
                    sentiment="NEUTRAL",
                    confidence=1.0,
                    profit=pnl_pct
                )
                final_action = risk_event
            
            else:
                # --- 5. ANÁLISIS DE IA Y SEÑALES (Prioridad 2) ---
                technical_signal = price_predictor.predict_next_move(df)
                
                # Control de Tiempos para Noticias (Evitar spam de requests)
                news_interval = settings.get("news_fetch_interval_minutes", 60) * 60
                
                # Si es la primera ejecución O ya pasó el tiempo configurado
                if (time.time() - last_news_time) > news_interval:
                    print(f"📰 Leyendo noticias del mercado (Intervalo: {settings.get('news_fetch_interval_minutes', 60)}m)...")
                    real_news = news_fetcher.get_latest_news(limit=3)
                    
                    # Analizar el sentimiento promedio
                    headline_to_analyze = real_news[0] if real_news else "Bitcoin is neutral"
                    print(f"   ℹ️ Noticia Principal: {headline_to_analyze[:60]}...")
                    
                    sentiment, confidence = sentiment_model.analyze([headline_to_analyze])
                    
                    # Actualizar estado cacheado
                    last_news_time = time.time()
                    cached_sentiment = sentiment
                    cached_confidence = confidence
                else:
                    # Usar valores cacheados
                    sentiment = cached_sentiment
                    confidence = cached_confidence
                    print(f"🧠 Usando sentimiento cacheado: {sentiment} ({confidence:.2f})")
                
                print(f"📊 Señal Técnica: {technical_signal} | 🧠 IA: {sentiment} ({confidence:.2f})")

                final_action = "HOLD"

                # Lógica de Ejecución
                if technical_signal == "UP" and sentiment == "BULLISH":
                    if not trader.is_holding:
                        final_action = "BUY"
                        if trader.place_order("buy", 0.01, current_price, reason="AI_SIGNAL"):
                            notion.log_trade("BUY", current_price, sentiment, confidence, 0)
                    else:
                        print("⏳ Señal de compra recibida, pero ya tienes una posición abierta.")

                elif technical_signal == "DOWN" and sentiment == "BEARISH":
                    if trader.is_holding:
                        final_action = "SELL"
                        if trader.place_order("sell", 0.01, current_price, reason="AI_SIGNAL"):
                            # pnl_pct se calcula dentro del trader al vender
                            notion.log_trade("SELL", current_price, sentiment, confidence, pnl_pct)
                    else:
                        print("⏳ Señal de venta recibida, pero no tienes activos para vender.")

                if final_action == "HOLD":
                    print("☕ Sin cambios. El bot sigue buscando oportunidades...")

            # --- 6. FINALIZACIÓN DE CICLO ---
            if os.getenv("RUN_ONCE") == "true":
                print("\n✅ Ejecución única de GitHub Actions finalizada.")
                break

            print("😴 Durmiendo 60 segundos...")
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"❌ Error Crítico en el bucle principal: {e}")
        # Notificar error a Notion si es posible
        try:
            notion.log_trade("ERROR", 0, "SYSTEM_CRASH", 0, 0)
        except:
            pass

if __name__ == "__main__":
    main()