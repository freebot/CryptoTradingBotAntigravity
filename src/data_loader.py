import requests
import pandas as pd
import time

class DataLoader:
    def __init__(self, sandbox=True):
        self.base_url = "https://api.coingecko.com/api/v3"

    def fetch_ohlcv(self, symbol, timeframe):
        """
        Symbol debe ser el ID de CoinGecko (ej: 'bitcoin', 'ethereum')
        Timeframe en la API gratuita de CoinGecko es automático según los días.
        """
        # Limpiamos el symbol por si viene como BTC/USDT
        coin_id = symbol.split('/')[0].lower()
        if coin_id == "btc": coin_id = "bitcoin"
        if coin_id == "eth": coin_id = "ethereum"

        print(f"Obteniendo datos de {coin_id} desde CoinGecko...")
        
        # Endpoint de CoinGecko para OHLC (Gratis)
        # days=1 nos da datos de cada 30 min, days=7 o mas nos da datos cada 4 horas
        url = f"{self.base_url}/coins/{coin_id}/ohlc?vs_currency=usd&days=7"
        
        try:
            response = requests.get(url)
            if response.status_code == 429:
                print("⚠️ Rate limit alcanzado en CoinGecko. Esperando...")
                return pd.DataFrame()
            
            data = response.json()
            
            # Formato de respuesta: [ [timestamp, open, high, low, close], ... ]
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            
            # Convertir timestamp a fecha legible
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            print(f"Error en CoinGecko: {e}")
            return pd.DataFrame()
