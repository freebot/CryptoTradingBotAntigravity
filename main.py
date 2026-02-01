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
from src.model import RemoteSentimentAnalyzer, PricePredictor
from src.trader import Trader
from src.utils import add_indicators
from src.notion_logger import NotionLogger
from src.supabase_logger import SupabaseLogger
from src.telegram_logger import TelegramLogger
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
            from src.model import SentimentAnalyzer
            analyzer = SentimentAnalyzer()
        else:
            logging.info("Initializing Remote Sentiment Analyzer (Client Mode)...")
            analyzer = RemoteSentimentAnalyzer()
            # 1. Wake up the Space with a Ping
            analyzer.check_status()

    predictor = PricePredictor()
    notion = NotionLogger()
    supabase = SupabaseLogger()
    telegram = TelegramLogger()
    fetcher = NewsFetcher()

    last_news_time = 0
    cached_sent, cached_conf = "NEUTRAL", 0.5

    while True:
        try:
            telegram.send_message("🔄 Iniciando ciclo de trading...")
            logging.info("Bot cycle: Fetching data...")
            df = loader.fetch_ohlcv(settings['symbol'], settings['timeframe'])
            if df.empty: 
                time.sleep(60); continue
            
            # Prepare Data
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
            balance = trader.get_balance()
            event, pnl = trader.check_risk_management(current_price)
            action_taken = None
            
            if event:
                order_result = trader.place_order("sell", 0.01, current_price, event)
                if order_result:
                    action_taken = "SELL"
                    # Log risk event with current sentiment
                    try:
                        telegram.send_message(f"🚨 ORDER EXECUTED: {event} | ID: Check Logs")
                        notion.log_trade(event, current_price, cached_sent, cached_conf, pnl)
                        supabase.log_to_supabase(event, current_price, cached_sent, cached_conf, pnl)
                    except Exception as log_err:
                        telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")

            else:
                # Trading Logic (New Entries)
                tech_signal = predictor.predict_next_move(df)

                if tech_signal == "UP" and cached_sent == "BULLISH" and not trader.is_holding:
                    if balance > 10.0:  # Minimum balance check (e.g., $10 USDT)
                        order_result = trader.place_order("buy", 0.01, current_price, "AI_SIGNAL")
                        if order_result:
                            action_taken = "BUY"
                            try:
                                telegram.send_message(f"✅ REAL BUY ORDER EXECUTED | Price: {current_price}")
                                notion.log_trade("BUY", current_price, cached_sent, cached_conf, 0)
                                supabase.log_to_supabase("BUY", current_price, cached_sent, cached_conf, 0)
                            except Exception as log_err:
                                telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")
                    else:
                        logging.warning(f"⚠️ Insufficient balance to buy: ${balance:.2f}")

                elif tech_signal == "DOWN" and cached_sent == "BEARISH" and trader.is_holding:
                    order_result = trader.place_order("sell", 0.01, current_price, "AI_SIGNAL")
                    if order_result:
                        action_taken = "SELL"
                        try:
                            telegram.send_message(f"🔻 REAL SELL ORDER EXECUTED | Price: {current_price}")
                            notion.log_trade("SELL", current_price, cached_sent, cached_conf, pnl)
                            supabase.log_to_supabase("SELL", current_price, cached_sent, cached_conf, pnl)
                        except Exception as log_err:
                             telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")
            
            # Report final status for this cycle
            if action_taken:
                telegram.report_cycle(action_taken, current_price, cached_sent)
            else:
                telegram.report_cycle("HOLD", current_price, cached_sent)
                # Log HOLD status to Supabase as requested
                try:
                    supabase.log_to_supabase("HOLD", current_price, cached_sent, cached_conf, pnl)
                except Exception as log_err:
                    logging.error(f"Logging Error: {log_err}")

        except Exception as e:
            error_msg = f"Error in bot loop: {e}"
            logging.error(error_msg)
            telegram.report_cycle("ERROR", error=error_msg)

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
        
        # Initialize SentimentAnalyzer locally for Server Mode
        from src.model import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
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