from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline
import torch
import gc

app = FastAPI()

# Cargar el modelo de análisis de sentimiento (FinBERT)
# Se usa pipeline para facilitar la inferencia
analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")

class AnalyzeRequest(BaseModel):
    texts: list[str]

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Endpoint para analizar una lista de textos.
    Retorna la clasificación de sentimiento para cada texto.
    """
    texts = request.texts
    if not texts:
        return []

    # Optimización de RAM: Desactivar gradientes
    with torch.no_grad():
        results = analyzer(texts)

    # Optimización de RAM: Liberar memoria inmediatamente
    gc.collect()

    return results

if __name__ == "__main__":
    import uvicorn
    # Puerto 7860 requerido para Hugging Face Spaces
    uvicorn.run(app, host="0.0.0.0", port=7860)
