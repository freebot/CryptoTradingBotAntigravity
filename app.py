from fastapi import FastAPI
from transformers import pipeline
from pydantic import BaseModel
import torch
import gc

app = FastAPI()

# Initialize the pipeline once
# task="sentiment-analysis" is an alias for "text-classification"
analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")

class AnalyzeRequest(BaseModel):
    texts: list[str]

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    texts = request.texts
    if not texts:
        return []
    
    # Run inference with memory optimizations
    with torch.no_grad():
        results = analyzer(texts)
    
    # Free memory immediately
    gc.collect()
    
    # Return raw list of [{'label': 'positive', 'score': 0.99}, ...]
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
