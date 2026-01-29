import pandas as pd
import numpy as np

def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    """
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD, MACD Signal, and MACD Histogram.
    """
    exp1 = data['close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    
    return macd, signal_line, histogram

def add_indicators(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    """
    Add technical indicators to the DataFrame.
    """
    df['rsi'] = calculate_rsi(df, settings.get('rsi_period', 14))
    macd, signal, hist = calculate_macd(
        df, 
        settings.get('macd_fast', 12), 
        settings.get('macd_slow', 26), 
        settings.get('macd_signal', 9)
    )
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_hist'] = hist
    
    # Simple Moving Averages
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['sma_200'] = df['close'].rolling(window=200).mean()
    
    return df
