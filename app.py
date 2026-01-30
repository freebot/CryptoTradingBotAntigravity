import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.model import SentimentAnalyzer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Brain")

app = FastAPI()

# Global analyzer instance
analyzer = None

class AnalysisRequest(BaseModel):
    texts: list[str]

@app.on_event("startup")
async def startup_event():
    """Load the model when the server starts."""
    global analyzer
    logger.info("Initializing Sentiment Analyzer...")
    try:
        # SentimentAnalyzer handles loading transformers, torch, eval mode, and gc.collect()
        analyzer = SentimentAnalyzer()
        logger.info("Model loaded and ready.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise e

@app.get("/")
def read_root():
    return {"status": "active", "service": "Crypto Sentiment Brain"}

@app.post("/analyze")
def analyze_sentiment(request: AnalysisRequest):
    global analyzer
    if not analyzer:
        raise HTTPException(status_code=503, detail="Model is loading, please wait.")
    
    if not request.texts:
         return {"sentiment": "NEUTRAL", "confidence": 0.0}

    try:
        # analyzer.analyze returns (sentiment_label, confidence_score)
        sentiment, confidence = analyzer.analyze(request.texts)
        return {"sentiment": sentiment, "confidence": confidence}
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Ensure usage of port 7860 as requested
    uvicorn.run(app, host="0.0.0.0", port=7860)
