import requests
import xml.etree.ElementTree as ET
import logging
import random
import time

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        # Lista de fuentes RSS gratuitas y públicas
        self.rss_sources = [
            "https://cointelegraph.com/rss",
            "https://cryptopotato.com/feed/",
            "https://beincrypto.com/feed/"
        ]

    def get_latest_news(self, limit=5):
        """
        Descarga noticias reales desde feeds RSS públicos.
        No requiere API Keys ni suscripciones.
        """
        news_items = []
        
        # Seleccionamos una fuente aleatoria para variar (y evitar bloqueo por spam requests)
        source = random.choice(self.rss_sources)
        
        try:
            logger.info(f"📰 Descargando noticias de: {source}")
            response = requests.get(source, timeout=10)
            response.raise_for_status()
            
            # Parsear XML (RSS standard)
            root = ET.fromstring(response.content)
            
            # Iterar sobre los items del RSS
            count = 0
            for item in root.findall('.//item'):
                if count >= limit:
                    break
                    
                title = item.find('title').text
                # A veces la descripción tiene HTML, podríamos limpiarlo pero para NLP 
                # suele estar bien tener más contexto o solo el título.
                # Por simplicidad y eficiencia del modelo, usaremos Titulo.
                
                if title:
                    news_items.append(title)
                    count += 1
            
            return news_items

        except Exception as e:
            logger.error(f"⚠️ Error descargando noticias RSS: {e}")
            # Fallback en caso de error de red (evita crash)
            return [
                "Bitcoin price maintains stability amidst global market uncertainty.",
                "Crypto market volatility increases as traders watch key support levels."
            ]
