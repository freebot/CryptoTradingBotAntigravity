from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np

app = FastAPI()

# Task: Technical / Backup Brain
# This app is lightweight (no PyTorch/Transformers) and serves two purposes:
# 1. Backup for Sentiment Analysis (Rule-based/Heuristic)
# 2. Future: Heavy Technical Indicator calculation (offloading from client)

class AnalyzeRequest(BaseModel):
    texts: list[str]

class IndicatorRequest(BaseModel):
    prices: list[float]
    period: int = 14

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Fallback Sentiment Analysis using simple Heuristics/Keywords.
    This acts as a backup if the main FinBERT brain is down.
    """
    texts = request.texts
    if not texts:
        return []
    
    results = []
    bullish_keywords = ['buy', 'bull', 'up', 'gain', 'profit', 'surge', 'high', 'breakout']
    bearish_keywords = ['sell', 'bear', 'down', 'loss', 'drop', 'crash', 'low', 'dump']

    for text in texts:
        text_lower = text.lower()
        score = 0
        
        # Simple keyword scoring
        for word in bullish_keywords:
            if word in text_lower: score += 0.1
        for word in bearish_keywords:
            if word in text_lower: score -= 0.1
            
        # Normalize score to [-1, 1] roughly
        score = max(min(score, 0.99), -0.99)
        
        label = "neutral"
        if score > 0.1: label = "positive"
        elif score < -0.1: label = "negative"
        
        results.append({"label": label, "score": abs(score)})

    return results

@app.post("/indicators")
async def calculate_rsi(request: IndicatorRequest):
    """
    Example of offloaded technical calculation (RSI).
    This keeps the main client light.
    """
    prices = request.prices
    period = request.period
    
    if len(prices) < period:
        return {"error": "Not enough data"}

    start_delta = np.diff(prices)
    up = start_delta.clip(min=0)
    down = -1 * start_delta.clip(max=0)
    
    # We generally can't do full RSI without more history, but this shows intent.
    # Simple SMA of gains/losses
    avg_up = np.mean(up[-period:])
    avg_down = np.mean(down[-period:])

    if avg_down == 0:
        rsi = 100
    else:
        rs = avg_up / avg_down
        rsi = 100 - (100 / (1 + rs))
        
    return {"rsi": rsi}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
