from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Task: Technical Analysis Backup
# This app is for the Technical Brain (crypto-tech-api)
# For now, it acts as a simple fallback or processes price data if needed.
# It uses minimal RAM.

class AnalyzeRequest(BaseModel):
    texts: list[str]

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Mock endpoint for Technical/Backup Brain.
    Ideally, this would run simpler heuristics or a lighter model.
    """
    texts = request.texts
    if not texts:
        return []
    
    # Return NEUTRAL for now as a safe backup
    # Structure must match FinBERT output: [{'label': 'neutral', 'score': 0.5}]
    return [{"label": "neutral", "score": 0.5} for _ in texts]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
