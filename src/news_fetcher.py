import requests
import xml.etree.ElementTree as ET
import random
import logging

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        # Reddit Sources (Community Sentiment)
        self.reddit_sources = [
            "https://www.reddit.com/r/Bitcoin/hot/.rss",
            "https://www.reddit.com/r/CryptoCurrency/hot/.rss",
            "https://www.reddit.com/r/Ethereum/hot/.rss"
        ]
        
        # Professional News Sources (Market Events)
        self.pro_sources = [
            "https://cointelegraph.com/rss",
            "https://cryptopotato.com/feed/",
            "https://www.newsbtc.com/feed/"
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AntigravityBot/1.0'
        }
        
        # Keywords that trigger immediate inclusion
        self.keywords = ["ETF", "SEC", "FED", "BREAKING", "DUMP", "PUMP", "CPI", "INFLATION", "BINANCE", "BLACKROCK"]

    def _fetch_rss(self, url):
        """Helper to fetch and parse a single RSS feed"""
        try:
            logger.info(f"🔍 Buscando noticias en: {url}")
            res = requests.get(url, headers=self.headers, timeout=10)
            
            if res.status_code != 200:
                logger.warning(f"⚠️ Error {res.status_code} fetching {url}")
                return []

            # Parse XML
            root = ET.fromstring(res.content)
            headlines = []
            
            # Generic 'title' tag search handles both RSS and Atom
            for node in root.iter():
                if 'title' in node.tag and node.text:
                    text = node.text.strip()
                    # Basic filter to remove short metadata titles like 'Home'
                    if len(text) > 20: 
                        headlines.append(text)
            
            return headlines
        except Exception as e:
            logger.error(f"❌ Error parsing {url}: {e}")
            return []

    def _select_top_headlines(self, headlines, count=3):
        """Selects top N headlines, prioritizing keywords"""
        priority = []
        normal = []
        
        for h in headlines:
            # Check for keywords case-insensitive
            if any(k in h.upper() for k in self.keywords):
                priority.append(h)
            else:
                normal.append(h)
        
        # Combine: Priority items first, then fill with normal
        selection = priority + normal
        return selection[:count]

    def get_latest_news(self):
        """Fetches a mix of Community (Reddit) and Pro News"""
        
        # 1. Get 3 from Reddit
        reddit_news = []
        random.shuffle(self.reddit_sources)
        for url in self.reddit_sources:
            items = self._fetch_rss(url)
            if items:
                reddit_news = self._select_top_headlines(items, count=3)
                break # Stop after finding one working source to avoid spamming
        
        # 2. Get 3 from Pro News
        pro_news = []
        random.shuffle(self.pro_sources)
        for url in self.pro_sources:
            items = self._fetch_rss(url)
            if items:
                pro_news = self._select_top_headlines(items, count=3)
                break
        
        final_news = reddit_news + pro_news
        
        if not final_news:
            logger.warning("⚠️ No news found from any source.")
            return ["Bitcoin market steady.", "Crypto monitoring active."]
            
        logger.info(f"✅ News Cycle Generated: {len(reddit_news)} Reddit + {len(pro_news)} Pro headlines.")
        return final_news