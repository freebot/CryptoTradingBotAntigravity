import requests
import time
import logging
import os

logger = logging.getLogger(__name__)

class WhaleFetcher:
    def __init__(self):
        # API Key from environment
        self.api_key = os.getenv("WHALE_ALERT_API_KEY")
        self.base_url = "https://api.whale-alert.io/v1/transaction"
        self.min_value_usd = 10_000_000 # $10M Minimum

    def get_latest_movements(self):
        """
        Fetches large transactions from Whale Alert.
        Returns a list of summary strings and a sentiment hint.
        """
        if not self.api_key:
            logger.warning("⚠️ No WHALE_ALERT_API_KEY found. Skipping Whale analysis.")
            return [], "NEUTRAL"

        try:
            # Get transactions from last hour
            start_time = int(time.time() - 3600)
            params = {
                "api_key": self.api_key,
                "start": start_time,
                "min_value": self.min_value_usd,
                "limit": 10
            }
            
            response = requests.get(f"{self.base_url}/{self.api_key}/transactions", params=params) # Simplified endpoint logic often requires exact url check
            # Whale alert endpoint structure is slightly different usually: https://api.whale-alert.io/v1/transactions
            # Let's clean that up.
            
            url = "https://api.whale-alert.io/v1/transactions"
            res = requests.get(url, params=params)
            
            if res.status_code != 200:
                logger.error(f"Whale Alert API Error: {res.status_code}")
                return [], "NEUTRAL"
            
            data = res.json()
            transactions = data.get('transactions', [])
            
            whale_summaries = []
            bearish_score = 0
            bullish_score = 0
            
            for tx in transactions:
                amount_usd = tx.get('amount_usd', 0)
                from_type = tx.get('from', {}).get('owner_type', 'unknown')
                to_type = tx.get('to', {}).get('owner_type', 'unknown')
                symbol = tx.get('symbol', '').upper()
                
                # Check for exchange flow
                if to_type == 'exchange':
                    bearish_score += amount_usd
                    sentiment = "BEARISH (Dump Risk)"
                elif from_type == 'exchange' and to_type == 'unknown':
                    bullish_score += amount_usd
                    sentiment = "BULLISH (Accumulation)"
                else:
                    sentiment = "NEUTRAL"
                
                summary = f"WHALE ALERT: {symbol} transfer of ${amount_usd:,.0f} from {from_type} to {to_type}. Sentiment: {sentiment}"
                whale_summaries.append(summary)
            
            # Determine overall whale sentiment
            overall_sentiment = "NEUTRAL"
            if bearish_score > bullish_score * 1.5:
                overall_sentiment = "BEARISH"
            elif bullish_score > bearish_score * 1.5:
                overall_sentiment = "BULLISH"
                
            logger.info(f"🐋 Whale Analysis: {len(whale_summaries)} large txs. Bias: {overall_sentiment}")
            return whale_summaries, overall_sentiment

        except Exception as e:
            logger.error(f"Whale Fetcher Error: {e}")
            return [], "NEUTRAL"
