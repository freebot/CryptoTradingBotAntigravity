from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline
import torch
import gc

app = FastAPI()

# Task: Sentiment Analysis (FinBERT)
# This app is specifically for the Sentiment Brain (crypto-sentiment-api)
try:
    analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    print("✅ Model ProsusAI/finbert loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    analyzer = None

class AnalyzeRequest(BaseModel):
    texts: list[str]

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Endpoint for sentiment analysis.
    """
    texts = request.texts
    if not texts:
        return []

    if not analyzer:
         return [{"label": "neutral", "score": 0.0}]

    # Memory Optimization
    with torch.no_grad():
        results = analyzer(texts)

    gc.collect()

    # Returns [{'label': 'positive', 'score': 0.9}, ...]
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
