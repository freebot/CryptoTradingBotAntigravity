import requests
import os

class RemoteSentimentAnalyzer:
    def __init__(self, api_url=None):
        # Define failover URLs
        self.default_urls = [
            "https://fr33b0t-crypto-sentiment-api.hf.space/analyze",
            "https://fr33b0t-crypto-tech-api.hf.space/analyze"
        ]
        
        # Priority: explicit arg > env var > default list
        env_url = os.getenv("SENTIMENT_API_URL")
        if api_url:
            self.urls = [api_url]
        elif env_url:
            self.urls = [env_url]
        else:
            self.urls = self.default_urls
            
        print(f"Initialized RemoteSentimentAnalyzer. URLs: {self.urls}")

    def analyze(self, text_list):
        if not text_list:
            return "NEUTRAL", 0.0

        for url in self.urls:
            try:
                # print(f"Querying: {url}...") 
                response = requests.post(url, json={"texts": text_list}, timeout=10)
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # Handle dict response (legacy)
                    if isinstance(results, dict) and "sentiment" in results:
                        return results.get("sentiment", "NEUTRAL"), results.get("confidence", 0.0)
                    
                    # Handle list response (raw classifications)
                    if isinstance(results, list):
                        sentiment_score = 0
                        valid_results = False
                        
                        for res in results:
                            label = res.get('label', '').lower()
                            score = res.get('score', 0)
                            
                            if label == 'positive':
                                sentiment_score += score
                            elif label == 'negative':
                                sentiment_score -= score
                            valid_results = True
                        
                        if not valid_results:
                            continue # Try next URL if response format was weird? Or just return Neutral.
                            
                        avg_score = sentiment_score / len(text_list) if text_list else 0
                        
                        if avg_score > 0.1:
                            return "BULLISH", avg_score
                        elif avg_score < -0.1:
                            return "BEARISH", avg_score
                        else:
                            return "NEUTRAL", avg_score
                
                else:
                    print(f"API Error {response.status_code} from {url}")
            
            except Exception as e:
                print(f"Connection failed to {url}: {e}")
                continue # Try next URL

        print("All Sentiment APIs failed or returned errors.")
        return "NEUTRAL", 0.0

    def check_status(self):
        """Pings the endpoints to wake them up."""
        success = False
        for url in self.urls:
            try:
                # Determine base URL for ping (strip /analyze)
                base_url = url.replace("/analyze", "")
                print(f"Pinging {base_url}...")
                requests.get(base_url, timeout=5)
                success = True
            except Exception:
                pass
        return success

class SentimentAnalyzer:
    def __init__(self, model_name="ProsusAI/finbert"):
        print(f"Loading Sentiment Model locally: {model_name}...")
        try:
            from transformers import pipeline
            import torch
            import gc
            self.pipe = pipeline("text-classification", model=model_name, tokenizer=model_name)
            self.pipe.model.eval()  # Ensure model is in eval mode
            gc.collect()  # Free up memory
        except Exception as e:
            print(f"Error loading model: {e}")
            self.pipe = None

    def analyze(self, text_list):
        import torch
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
