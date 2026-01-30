import requests
import xml.etree.ElementTree as ET
import random
import logging

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        self.sources = [
            "https://cointelegraph.com/rss",
            "https://cryptopotato.com/feed/",
            "https://beincrypto.com/feed/"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }

    def get_latest_news(self, limit=5):
        random.shuffle(self.sources)
        for source in self.sources:
            try:
                res = requests.get(source, headers=self.headers, timeout=10)
                root = ET.fromstring(res.content)
                news = [item.find('title').text for item in root.findall('.//item')[:limit]]
                if news: return news
            except Exception as e:
                print(f"Error fetching from {source}: {e}")
                continue
        return ["Bitcoin market remains stable.", "Crypto adoption continues."]