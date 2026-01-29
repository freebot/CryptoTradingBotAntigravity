import ccxt
import time
import os
from dotenv import load_dotenv

load_dotenv()

class Trader:
    def __init__(self, symbol, paper_trading=True):
        self.symbol = symbol
        self.filename = "trading_results.csv"
        # Si el archivo no existe, creamos la cabecera
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("timestamp,action,price,amount\n")

    def place_order(self, side, amount, price):
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        
        print(f"✅ ORDEN VIRTUAL: {side.upper()} {amount} {self.symbol} a ${price}")
        
        # Guardamos el trade en el CSV
        with open(self.filename, "a") as f:
            f.write(f"{timestamp},{side},{price},{amount}\n")
        
        return True
    
    def get_balance(self, currency='USDT'):
        try:
            balance = self.exchange.fetch_balance()
            return balance.get('total', {}).get(currency, 0.0)
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

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
