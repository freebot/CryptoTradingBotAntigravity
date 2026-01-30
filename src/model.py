import requests
import os
import gc
import torch

class RemoteSentimentAnalyzer:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("SENTIMENT_API_URL")
        print(f"Initialized RemoteSentimentAnalyzer. API: {self.api_url}")

    def analyze(self, text_list):
        if not text_list or not self.api_url:
            return "NEUTRAL", 0.0

        try:
            # We assume the endpoint is /analyze as configured previously
            response = requests.post(self.api_url, json={"texts": text_list}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("sentiment", "NEUTRAL"), data.get("confidence", 0.0)
            else:
                print(f"API Error {response.status_code}: {response.text}")
                return "NEUTRAL", 0.0
        except Exception as e:
            print(f"API Request Failed: {e}")
            return "NEUTRAL", 0.0

class SentimentAnalyzer:
    def __init__(self, model_name="ProsusAI/finbert"):
        print(f"Loading Sentiment Model locally: {model_name}...")
        try:
            from transformers import pipeline
            self.pipe = pipeline("text-classification", model=model_name, tokenizer=model_name)
            self.pipe.model.eval()  # Ensure model is in eval mode
            gc.collect()  # Free up memory
        except Exception as e:
            print(f"Error loading model: {e}")
            self.pipe = None

    def analyze(self, text_list):
        if not self.pipe:
            return "NEUTRAL", 0.0
        
        with torch.no_grad():
            results = self.pipe(text_list)
        # Simple aggregation logic
        sentiment_score = 0
        for res in results:
            if res['label'] == 'positive':
                sentiment_score += res['score']
            elif res['label'] == 'negative':
                sentiment_score -= res['score']
        
        avg_score = sentiment_score / len(text_list) if text_list else 0
        
        if avg_score > 0.1:
            return "BULLISH", avg_score
        elif avg_score < -0.1:
            return "BEARISH", avg_score
        else:
            return "NEUTRAL", avg_score

class PricePredictor:
    def __init__(self):
        # In a real scenario, load a saved PyTorch/TensorFlow model here
        pass

    def predict_next_move(self, df):
        """
        Dummy prediction logic for demonstration.
        In reality, this would prepare features from 'df' and feed into an LSTM.
        """
        if df.empty:
            return "HOLD"
        
        # Simple heuristic for demonstration:
        # If SMA_50 > SMA_200 (Golden Cross) -> UP
        last_row = df.iloc[-1]
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            if last_row['sma_50'] > last_row['sma_200']:
                return "UP"
            elif last_row['sma_50'] < last_row['sma_200']:
                return "DOWN"
        
        return "HOLD"
