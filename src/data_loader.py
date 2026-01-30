import requests
import pandas as pd
import time

class DataLoader:
    def __init__(self, sandbox=True):
        self.base_url = "https://api.coingecko.com/api/v3"

    def fetch_ohlcv(self, symbol, timeframe):
        # 1. Mapeo de Símbolo a ID de CoinGecko
        coin_id = symbol.split('/')[0].lower()
        mapping = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "sol": "solana",
            "bnb": "binancecoin"
        }
        coin_id = mapping.get(coin_id, coin_id)

        print(f"Obteniendo datos de {coin_id} desde CoinGecko...")
        
        # 2. Configuración de días según el timeframe deseado (aproximado)
        # Para la API gratuita: 1-2 días da velas de 30m, 7-30 días da velas de 4h.
        days = "1" if "h" in timeframe or "m" in timeframe else "7"
        
        url = f"{self.base_url}/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 429:
                print("⚠️ Rate limit alcanzado (CoinGecko). Esperando 60s...")
                time.sleep(60)
                return pd.DataFrame()
            
            if response.status_code != 200:
                print(f"❌ Error API CoinGecko: {response.status_code}")
                return pd.DataFrame()
                
            data = response.json()
            
            # 3. Crear DataFrame
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            
            # CoinGecko OHLC no trae volumen, lo creamos en 0 por compatibilidad con indicadores
            df['volume'] = 0 
            
            # Convertir timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Asegurar que los datos sean numéricos para los indicadores
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col])
            
            return df
            
        except Exception as e:
            print(f"❌ Error en DataLoader: {e}")
            return pd.DataFrame()