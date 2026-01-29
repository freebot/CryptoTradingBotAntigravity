import ccxt
import time
import os
from dotenv import load_dotenv

load_dotenv()

class Trader:
    def __init__(self, symbol, paper_trading=True):
        self.symbol = symbol
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            print("Warning: API Keys not found in .env. Trading functionality will differ.")
        
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'enableRateLimit': True,
        })
        
        if paper_trading:
            self.exchange.set_sandbox_mode(True) 
            # Note: CCXT sandbox mode might require specific URL overrides for some exchanges, 
            # but binance usually handles it with set_sandbox_mode(True) if supported.

    def get_balance(self, currency='USDT'):
        try:
            balance = self.exchange.fetch_balance()
            return balance.get('total', {}).get(currency, 0.0)
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

    def place_order(self, side, amount):
        try:
            order = self.exchange.create_market_order(self.symbol, side, amount)
            print(f"Order placed: {side} {amount} {self.symbol}")
            return order
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

    def log_trade(self, trade_data):
        # Implement logging to CSV
        import csv
        file_exists = os.path.isfile('trades.csv')
        with open('trades.csv', 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'symbol', 'side', 'amount', 'price', 'cost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(trade_data)
