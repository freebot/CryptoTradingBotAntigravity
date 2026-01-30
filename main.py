import os
import time
import json
import logging
from src.data_loader import DataLoader
from src.model import SentimentAnalyzer, PricePredictor
from src.trader import Trader
from src.utils import add_indicators
from src.notion_logger import NotionLogger
from src.news_fetcher import NewsFetcher

logging.basicConfig(level=logging.INFO)

def main():
    with open('config/settings.json') as f:
        settings = json.load(f)

    loader = DataLoader()
    trader = Trader(settings['symbol'])
    trader.stop_loss_pct = settings['stop_loss_pct']
    trader.take_profit_pct = settings['take_profit_pct']
    
    analyzer = SentimentAnalyzer()
    predictor = PricePredictor()
    notion = NotionLogger()
    fetcher = NewsFetcher()

    last_news_time = 0
    cached_sent, cached_conf = "NEUTRAL", 0.5

    while True:
        df = loader.fetch_ohlcv(settings['symbol'], settings['timeframe'])
        if df.empty: 
            time.sleep(60); continue
        
        current_price = float(df['close'].iloc[-1])
        df = add_indicators(df, settings)

        # 1. Riesgo
        event, pnl = trader.check_risk_management(current_price)
        if event:
            trader.place_order("sell", 0.01, current_price, event)
            notion.log_trade(event, current_price, "NEUTRAL", 1, pnl)
        
        else:
            # 2. IA y Noticias
            if (time.time() - last_news_time) > (settings['news_fetch_interval_minutes'] * 60):
                news = fetcher.get_latest_news()
                cached_sent, cached_conf = analyzer.analyze(news)
                last_news_time = time.time()

            tech_signal = predictor.predict_next_move(df)

            if tech_signal == "UP" and cached_sent == "BULLISH" and not trader.is_holding:
                trader.place_order("buy", 0.01, current_price, "AI_SIGNAL")
                notion.log_trade("BUY", current_price, cached_sent, cached_conf, 0)
            
            elif tech_signal == "DOWN" and cached_sent == "BEARISH" and trader.is_holding:
                trader.place_order("sell", 0.01, current_price, "AI_SIGNAL")
                notion.log_trade("SELL", current_price, cached_sent, cached_conf, pnl)

        if os.getenv("RUN_ONCE") == "true": break
        time.sleep(60)

if __name__ == "__main__":
    main()