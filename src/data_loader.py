import ccxt
import pandas as pd
import requests
import time
import os



class DataLoader:
    def __init__(self, sandbox=True):
        self.exchange = ccxt.bybit({  # <--- Cambiar binance por bybit
            'apiKey': os.getenv('BYBIT_API_KEY'), # <--- Usar nuevas variables
            'secret': os.getenv('BYBIT_SECRET_KEY'),
            'enableRateLimit': True,
        })
        if sandbox:
            self.exchange.set_sandbox_mode(True)
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Fetch OHLCV data from the exchange.
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching OHLCV data: {e}")
            return pd.DataFrame()

    def fetch_coingecko_data(self, coin_id: str, days: str = '30'):
        """
        Fetch historical data from CoinGecko.
        """
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        try:
            response = requests.get(url)
            data = response.json()
            prices = data.get('prices', [])
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching CoinGecko data: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> float:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching ticker: {e}")
            return None
