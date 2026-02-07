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
from src.whale_fetcher import WhaleFetcher

logging.basicConfig(level=logging.INFO)

# --- FastAPI Setup ---
app = FastAPI()

# Global analyzer instance to be shared
analyzer = None
# Global state for OpenClaw integration
latest_market_data = {}
openclaw_input = {}
latest_market_data_lock = threading.Lock()
openclaw_input_lock = threading.Lock()

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

# --- OpenClaw Integration Endpoints ---
class OpenClawSignal(BaseModel):
    action: str = None # "buy", "sell", "hold"
    sentiment: str = None # "BULLISH", "BEARISH", "NEUTRAL"
    confidence: float = 0.0
    reason: str = "OpenClaw Intelligence"

@app.get("/market/status")
def get_market_status():
    with latest_market_data_lock:
        return latest_market_data

@app.post("/openclaw/signal")
def receive_openclaw_signal(signal: OpenClawSignal):
    global openclaw_input
    with openclaw_input_lock:
        openclaw_input = {
            "action": signal.action,
            "sentiment": signal.sentiment,
            "confidence": signal.confidence,
            "reason": signal.reason,
            "timestamp": time.time()
        }
    return {"status": "Signal received", "data": openclaw_input}

# --- Bot Logic ---
def run_bot_loop():
    global analyzer
    logging.info("Starting Trading Bot Loop...")
    
    # Wait 10 seconds to allow server to start and system to settle
    time.sleep(10)
    
    with open('config/settings.json') as f:
        settings = json.load(f)
    
    # Force Alpaca standard symbol
    settings['symbol'] = 'BTC/USD'

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
    whale_tracker = WhaleFetcher()

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

            # Update Global State for OpenClaw
            with latest_market_data_lock:
                latest_market_data.update({
                    "symbol": settings['symbol'],
                    "price": current_price,
                    "timestamp": time.time(),
                    "indicators": {
                        "rsi": float(df['rti'].iloc[-1]) if 'rti' in df else 0, # Assuming rti is rsi
                        "close": float(df['close'].iloc[-1])
                    }
                })

            # 2. IA y Noticias (Obtener noticias y sentimiento ANTES de riesgo)
            try:
                if (time.time() - last_news_time) > (settings['news_fetch_interval_minutes'] * 60):
                    news = fetcher.get_latest_news()
                    whale_txts, whale_bias = whale_tracker.get_latest_movements()
                    
                    combined_context = news + whale_txts
                    
                    if combined_context:
                        # 3. Consultar sentimiento a la API del Space (Cerebro Unificado)
                        logging.info(f"Analyzing context: {len(news)} news + {len(whale_txts)} whale signals...")
                        cached_sent, cached_conf = analyzer.analyze(combined_context)
                    else:
                        logging.info("No new context (news/whales) to analyze.")
                        
                    last_news_time = time.time()
            except Exception as e:
                logging.error(f"⚠️ Error en módulo de noticias/IA: {e}")

            # Check OpenClaw Signals but ensure thread safety
            oc_action = None
            oc_sentiment = None
            with openclaw_input_lock:
                if openclaw_input and (time.time() - openclaw_input.get("timestamp", 0) < 300): # 5 mins expiry
                    logging.info(f"🦁 OpenClaw Signal Detected: {openclaw_input}")
                    oc_sentiment = openclaw_input.get("sentiment")
                    if openclaw_input.get("confidence", 0) > cached_conf:
                         cached_sent = oc_sentiment
                         logging.info(f"🦁 OpenClaw overwrote sentiment to {cached_sent}")
                    
                    if openclaw_input.get("action") in ["buy", "sell"]:
                        oc_action = openclaw_input.get("action")

            # 4. Ejecutar lógica de riesgo y Notion
            balance = trader.get_balance()
            event, pnl = trader.check_risk_management(current_price)
            action_taken = None
            
            if event:
                # Risk Management Triggered (SL/TP) - Close Position
                current_pos = trader.position
                trade_side = "sell" if current_pos == "LONG" else "buy"
                
                order_result = trader.place_order(trade_side, 0.01, current_price, event)
                if order_result:
                    action_taken = f"{event}_{current_pos}"
                    try:
                        telegram.send_message(f"🚨 RISK TRIGGERED: {event} ({current_pos}) | ID: Check Logs")
                        notion.log_trade(action=f"CLOSE_{current_pos}", price=float(current_price), sentiment=cached_sent, confidence=float(cached_conf), profit=float(pnl))
                        supabase.log_to_supabase(f"CLOSE_{current_pos}", current_price, cached_sent, cached_conf, pnl)
                    except Exception as log_err:
                        telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")

            else:
                # Trading Logic (New Entries)
                tech_signal = predictor.predict_next_move(df)

                # --- Logic for LONG Position ---
                # OpenClaw Override or Standard Logic
                should_long = (tech_signal == "UP" and cached_sent == "BULLISH" and cached_conf >= 0.60)
                if oc_action == "buy": should_long = True

                if should_long:
                    if trader.position == "NONE":
                        if balance > 10.0:
                            if trader.place_order("buy", 0.01, current_price, "AI_LONG"):
                                action_taken = "OPEN_LONG"
                                try:
                                    telegram.send_message(f"✅ REAL LONG OPENED | Price: {current_price}")
                                    notion.log_trade(action="OPEN_LONG", price=float(current_price), sentiment=cached_sent, confidence=float(cached_conf), profit=0.0)
                                    supabase.log_to_supabase("OPEN_LONG", current_price, cached_sent, cached_conf, 0)
                                except Exception as log_err:
                                    telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")
                        else:
                            logging.warning(f"⚠️ Insufficient balance for LONG: ${balance:.2f}")

                    elif trader.position == "SHORT":
                        # Signal UP + BULLISH while holding SHORT -> Close Short (Cover)
                        if trader.place_order("buy", 0.01, current_price, "AI_COVER"):
                            action_taken = "CLOSE_SHORT"
                            try:
                                telegram.send_message(f"🔄 REAL SHORT CLOSED | Price: {current_price}")
                                notion.log_trade(action="CLOSE_SHORT", price=float(current_price), sentiment=cached_sent, confidence=float(cached_conf), profit=float(pnl))
                                supabase.log_to_supabase("CLOSE_SHORT", current_price, cached_sent, cached_conf, pnl)
                            except Exception as log_err:
                                 telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")

                # --- Logic for SHORT Position ---
                # OpenClaw Override or Standard Logic
                should_short = (tech_signal == "DOWN" and cached_sent == "BEARISH" and cached_conf >= 0.60)
                if oc_action == "sell": should_short = True

                if should_short:
                    if trader.position == "NONE":
                        if balance > 10.0:
                            if trader.place_order("sell", 0.01, current_price, "AI_SHORT"):
                                action_taken = "OPEN_SHORT"
                                try:
                                    telegram.send_message(f"🔻 REAL SHORT OPENED | Price: {current_price}")
                                    notion.log_trade(action="OPEN_SHORT", price=float(current_price), sentiment=cached_sent, confidence=float(cached_conf), profit=0.0)
                                    supabase.log_to_supabase("OPEN_SHORT", current_price, cached_sent, cached_conf, 0)
                                except Exception as log_err:
                                    telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")
                        else:
                             logging.warning(f"⚠️ Insufficient balance for SHORT: ${balance:.2f}")

                    elif trader.position == "LONG":
                         # Signal DOWN + BEARISH while holding LONG -> Close Long (Sell)
                        if trader.place_order("sell", 0.01, current_price, "AI_SELL"):
                            action_taken = "CLOSE_LONG"
                            try:
                                telegram.send_message(f"📉 REAL LONG CLOSED | Price: {current_price}")
                                notion.log_trade(action="CLOSE_LONG", price=float(current_price), sentiment=cached_sent, confidence=float(cached_conf), profit=float(pnl))
                                supabase.log_to_supabase("CLOSE_LONG", current_price, cached_sent, cached_conf, pnl)
                            except Exception as log_err:
                                 telegram.report_cycle("ERROR", error=f"Logging Error: {log_err}")
            
            # Report final status for this cycle
            if action_taken:
                telegram.report_cycle(action_taken, current_price, cached_sent)
            else:
                telegram.report_cycle("HOLD", current_price, cached_sent)
                # Log HOLD status to Supabase as requested
                try:
                    notion.log_trade(action="WATCHING", price=float(current_price), sentiment=cached_sent, confidence=float(cached_conf), profit=float(pnl))
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
        
        # Start API for Local OpenClaw connection
        server_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "0.0.0.0", "port": 8000})
        server_thread.start()

        # Run trading bot directly (blocking)
        # Analyzer will be initialized as Remote in run_bot_loop
        run_bot_loop()

if __name__ == "__main__":
    main()