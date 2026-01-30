import os
import requests
import logging

class TelegramLogger:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        if not self.bot_token or not self.chat_id:
            logging.warning("⚠️ Telegram Logs disabled: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")

    def send_message(self, text):
        """Sends a raw text message to the configured Telegram chat."""
        if not self.bot_token or not self.chat_id:
            return

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            response = requests.post(self.base_url, json=payload, timeout=10)
            if response.status_code != 200:
                logging.error(f"❌ Telegram API Error: {response.text}")
        except Exception as e:
            logging.error(f"❌ Failed to send Telegram message: {e}")

    def report_cycle(self, status, price=None, sentiment=None, error=None):
        """
        Reports the result of a bot cycle with meaningful emojis.
        
        Args:
            status (str): "SUCCESS", "ERROR", "BUY", "SELL", "HOLD"
            price (float): Current asset price.
            sentiment (str): BULLISH, BEARISH, NEUTRAL
            error (str, optional): Error message if status is ERROR.
        """
        if not self.bot_token or not self.chat_id:
            return

        message = ""
        
        if status == "ERROR":
            message = f"🚨 *CRITICAL ERROR*\n\nThe bot encountered an issue:\n`{error}`"
        
        elif status == "BUY":
            message = f"🟢 *BUY SIGNAL EXECUTED* 🚀\n\nPrice: `${price:,.2f}`\nSentiment: {sentiment}"
        
        elif status == "SELL":
            message = f"🔴 *SELL SIGNAL EXECUTED* 📉\n\nPrice: `${price:,.2f}`\nSentiment: {sentiment}"
        
        elif status == "HOLD":
            # For routine checks, we might want to be less verbose or just log stats
            icon = "🐂" if sentiment == "BULLISH" else "🐻" if sentiment == "BEARISH" else "😐"
            message = f"🛡️ *HOLDING POSITION*\n\nPrice: `${price:,.2f}`\nAI Sentiment: {icon} {sentiment}\nSystem Status: Online ✅"
        
        elif status == "SUCCESS": # Generic success / Startup
             message = f"🤖 *Antigravity Bot Cycle Complete*\n\nPrice: `${price:,.2f}`\nSentiment: {sentiment}"

        # Send if we constructed a message
        if message:
            self.send_message(message)
