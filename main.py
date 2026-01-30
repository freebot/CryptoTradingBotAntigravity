import os
import time

# Ensure logs are not buffered
os.environ["PYTHONUNBUFFERED"] = "1"
import json
import logging
import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.data_loader import DataLoader
from src.model import SentimentAnalyzer, RemoteSentimentAnalyzer, PricePredictor
from src.trader import Trader
from src.utils import add_indicators
from src.notion_logger import NotionLogger
from src.news_fetcher import NewsFetcher

logging.basicConfig(level=logging.INFO)

# --- FastAPI Setup ---
app = FastAPI()

# Global analyzer instance to be shared
analyzer = None

class SentimentRequest(BaseModel):
    texts: list[str]

@app.post("/analyze")
def analyze_sentiment(request: SentimentRequest):
    global analyzer
    if not analyzer:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        sentiment, confidence = analyzer.analyze(request.texts)
        return {"sentiment": sentiment, "confidence": confidence}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "running", "mode": "hybrid" if os.getenv("SPACE_ID") else "client"}

# --- Bot Logic ---
def run_bot_loop():
    global analyzer
    logging.info("Starting Trading Bot Loop...")
    
    # Wait 10 seconds to allow server to start and system to settle
    time.sleep(10)
    
    with open('config/settings.json') as f:
        settings = json.load(f)

    loader = DataLoader()
    trader = Trader(settings['symbol'])
    trader.stop_loss_pct = settings['stop_loss_pct']
    trader.take_profit_pct = settings['take_profit_pct']
    
    if analyzer is None:
        if os.getenv("SPACE_ID"):
            logging.info("Initializing Local Sentiment Analyzer (Server Mode)...")
            analyzer = SentimentAnalyzer()
        else:
            logging.info("Initializing Remote Sentiment Analyzer (Client Mode)...")
            analyzer = RemoteSentimentAnalyzer()
            # 1. Wake up the Space with a Ping
            analyzer.check_status()

    predictor = PricePredictor()
    notion = NotionLogger()
    fetcher = NewsFetcher()

    last_news_time = 0
    cached_sent, cached_conf = "NEUTRAL", 0.5

    while True:
        try:
            logging.info("Bot cycle: Fetching data...")
            df = loader.fetch_ohlcv(settings['symbol'], settings['timeframe'])
            if df.empty: 
                time.sleep(60); continue
            
            current_price = float(df['close'].iloc[-1])
            df = add_indicators(df, settings)

            current_price = float(df['close'].iloc[-1])
            df = add_indicators(df, settings)

            # 2. IA y Noticias (Obtener noticias y sentimiento ANTES de riesgo)
            try:
                if (time.time() - last_news_time) > (settings['news_fetch_interval_minutes'] * 60):
                    news = fetcher.get_latest_news()
                    if news:
                        # 3. Consultar sentimiento a la API del Space
                        logging.info("Analyzing news sentiment...")
                        cached_sent, cached_conf = analyzer.analyze(news)
                    else:
                        logging.info("No news found to analyze.")
                    last_news_time = time.time()
            except Exception as e:
                logging.error(f"⚠️ Error en módulo de noticias/IA: {e}")

            # 4. Ejecutar lógica de riesgo y Notion
            event, pnl = trader.check_risk_management(current_price)
            if event:
                trader.place_order("sell", 0.01, current_price, event)
                # Log risk event with current sentiment
                notion.log_trade(event, current_price, cached_sent, cached_conf, pnl)
            
            else:
                # Trading Logic (New Entries)
                tech_signal = predictor.predict_next_move(df)

                if tech_signal == "UP" and cached_sent == "BULLISH" and not trader.is_holding:
                    trader.place_order("buy", 0.01, current_price, "AI_SIGNAL")
                    notion.log_trade("BUY", current_price, cached_sent, cached_conf, 0)
                
                elif tech_signal == "DOWN" and cached_sent == "BEARISH" and trader.is_holding:
                    trader.place_order("sell", 0.01, current_price, "AI_SIGNAL")
                    notion.log_trade("SELL", current_price, cached_sent, cached_conf, pnl)

        except Exception as e:
            logging.error(f"Error in bot loop: {e}")

        if os.getenv("RUN_ONCE") == "true": 
            logging.info("RUN_ONCE is true, exiting bot loop.")
            break
            
        time.sleep(60)

def main():
    global analyzer
    
    if os.getenv("SPACE_ID"):
        # Server Mode (Hugging Face Space)
        logging.info("🚀 Starting in SERVER MODE (Hugging Face Space)")
        
        # Start API Server in background thread
        server_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "0.0.0.0", "port": 7860})
        server_thread.start()
        
        # Run trading bot in main thread
        run_bot_loop()
        
    else:
        # Client Mode (GitHub Actions / Local)
        logging.info("🌍 Starting in CLIENT MODE")
        
        # Run trading bot directly (blocking)
        # Analyzer will be initialized as Remote in run_bot_loop
        run_bot_loop()

if __name__ == "__main__":
    main()