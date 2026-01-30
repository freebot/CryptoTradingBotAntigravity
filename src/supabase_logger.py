import os
from supabase import create_client, Client
import logging

class SupabaseLogger:
    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            logging.warning("⚠️ Supabase credentials not found. Logging disabled.")
            self.supabase: Client = None
        else:
            try:
                self.supabase: Client = create_client(url, key)
                logging.info("✅ Connected to Supabase for Logging")
            except Exception as e:
                logging.error(f"❌ Failed to connect to Supabase: {e}")
                self.supabase = None

    def log_trade(self, action: str, price: float, sentiment: str, confidence: float, pnl: float = 0.0):
        """
        Logs a trade or action to the 'trading_logs' table in Supabase.
        """
        if not self.supabase:
            return

        data = {
            "action": action,
            "price": price,
            "sentiment": sentiment,
            "confidence": confidence,
            "pnl": pnl,
            # timestamp is usually handled by the database default (now()) or we can send it explicitly
        }

        try:
            response = self.supabase.table("trading_logs").insert(data).execute()
            # logging.info(f"📝 Logged to Supabase: {response}")
        except Exception as e:
            logging.error(f"❌ Error logging to Supabase: {e}")
