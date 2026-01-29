import time
import json
import logging
from src.data_loader import DataLoader
from src.model import SentimentAnalyzer, PricePredictor
from src.trader import Trader
from src.utils import add_indicators

# Load settings
try:
    with open('config/settings.json', 'r') as f:
        settings = json.load(f)
except FileNotFoundError:
    print("Settings file not found. Using defaults.")
    settings = {"symbol": "BTC/USDT", "timeframe": "1h"}

SYMBOL = settings.get("symbol", "BTC/USDT")
TIMEFRAME = settings.get("timeframe", "1h")

def main():
    print("🚀 Starting Antigravity Crypto Bot...")
    
    # Initialize components
    data_loader = DataLoader(sandbox=True)
    sentiment_model = SentimentAnalyzer()
    price_predictor = PricePredictor()
    trader = Trader(SYMBOL, paper_trading=True)
    
    print(f"Tracking {SYMBOL} on {TIMEFRAME} timeframe.")
    
    # Fake news source for demo purposes
    fake_news = [
        "Bitcoin hits all time high as adoption grows.",
        "Market uncertainty rises due to regulatory concerns.",
        "New upgrades expected to boost network efficiency."
    ]

    try:
        while True:
            print("\n--- New Cycle ---")
            
            # 1. Fetch Data
            df = data_loader.fetch_ohlcv(SYMBOL, TIMEFRAME)
            if df.empty:
                print("No data received. Waiting...")
                time.sleep(60)
                if os.getenv("RUN_ONCE"):
                     break
                continue
            
            # 2. Analyze Data (Technical)
            df = add_indicators(df, settings)
            current_price = df['close'].iloc[-1]
            print(f"Current Price: {current_price}")
            
            technical_signal = price_predictor.predict_next_move(df)
            print(f"Technical Signal: {technical_signal}")
            
            # 3. Analyze Sentiment (Simulated with random news for now)
            # In a real app, you'd fetch news from an API
            import random
            current_news = random.sample(fake_news, 1)
            sentiment, score = sentiment_model.analyze(current_news)
            print(f"Sentiment: {sentiment} (Score: {score:.2f})")
            
            # 4. Decision Logic
            action = "HOLD"
            if technical_signal == "UP" and sentiment == "BULLISH":
                action = "BUY"
            elif technical_signal == "DOWN" and sentiment == "BEARISH":
                action = "SELL"
            
            print(f"Decision: {action}")
            
            # 5. Execute Trade
            if action == "BUY":
                # Calculate amount based on risk? For now fixed small amount
                trader.place_order('buy', 0.001) 
            elif action == "SELL":
                trader.place_order('sell', 0.001)
            
            if os.getenv("RUN_ONCE"):
                print("Single run completed. Exiting.")
                break

            print("Sleeping for 60 seconds...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("Bot stopped by user.")

if __name__ == "__main__":
    main()
