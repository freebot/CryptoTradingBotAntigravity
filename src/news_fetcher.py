import requests
import xml.etree.ElementTree as ET
import random
import logging

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        # Añadimos los foros más importantes de Reddit via RSS
        self.sources = [
            "https://www.reddit.com/r/Bitcoin/hot/.rss",
            "https://www.reddit.com/r/CryptoCurrency/hot/.rss",
            "https://www.reddit.com/r/Ethereum/hot/.rss",
            "https://cointelegraph.com/rss"
        ]
        # Reddit es MUY estricto con el User-Agent. 
        # Si no pones uno que parezca humano, te dará error 429.
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AntigravityBot/1.0'
        }

    def get_latest_news(self, limit=5):
        random.shuffle(self.sources)
        for source in self.sources:
            try:
                logger.info(f"🔍 Buscando sentimiento en: {source}")
                res = requests.get(source, headers=self.headers, timeout=10)
                
                # Si Reddit nos bloquea temporalmente, pasamos a la siguiente fuente
                if res.status_code != 200:
                    continue

                root = ET.fromstring(res.content)
                # El RSS de Reddit usa un formato llamado 'Atom', 
                # así que buscamos etiquetas 'title' de forma genérica
                news = [node.text for node in root.iter() if 'title' in node.tag]
                
                # Filtramos títulos poco útiles como el nombre del foro
                news = [n for n in news if len(n) > 20][:limit]
                
                if news: 
                    logger.info(f"✅ {len(news)} temas encontrados en {source}")
                    return news
            except Exception as e:
                logger.error(f"Error en fuente {source}: {e}")
                continue
        
        return ["Bitcoin market sentiment is cautious.", "Ethereum network activity increases."]