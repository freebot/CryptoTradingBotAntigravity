import os
import datetime
import pandas as pd
import os
import datetime
import pandas as pd
from upstash_redis import Redis

class Trader:
    def __init__(self, symbol, stop_loss_pct=0.02, take_profit_pct=0.05):
        self.symbol = symbol
        self.filename = "trading_results.csv"
        
        # --- Redis Connection for State Persistence ---
        url = os.getenv("UPSTASH_REDIS_REST_URL")
        token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        
        self.redis = None
        if url and token:
            try:
                self.redis = Redis(url=url, token=token)
                # Test connection (simple get)
                self.redis.get("test_connection")
                print("✅ Connected to Upstash Redis for State Memory")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}. Using local memory (stateless).")
        
        # --- Parámetros de Riesgo (Configurables) ---
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # --- Estado Inicial (Solo si no existe en Redis) ---
        if self.redis:
            # Initialize keys if they assume empty state
            if not self.redis.get("trader:is_holding"):
                self.redis.set("trader:is_holding", "0")
            if not self.redis.get("trader:entry_price"):
                self.redis.set("trader:entry_price", "0.0")
        else:
            # Fallback local state
            self._is_holding = False
            self._entry_price = 0.0

        self.virtual_balance = 10000.0 

        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("timestamp,action,price,reason,profit_pct\n")

    @property
    def is_holding(self):
        if self.redis:
            val = self.redis.get("trader:is_holding")
            return val == "1" if val else False
        return self._is_holding

    @is_holding.setter
    def is_holding(self, value):
        if self.redis:
            self.redis.set("trader:is_holding", "1" if value else "0")
        else:
            self._is_holding = value

    @property
    def entry_price(self):
        if self.redis:
            val = self.redis.get("trader:entry_price")
            return float(val) if val else 0.0
        return self._entry_price

    @entry_price.setter
    def entry_price(self, value):
        if self.redis:
            self.redis.set("trader:entry_price", str(value))
        else:
            self._entry_price = value

    def check_risk_management(self, current_price):
        """
        Revisa si el precio actual toca el Stop Loss o el Take Profit.
        Retorna (Evento, Porcentaje_Ganancia)
        """
        if not self.is_holding:
            return None, 0.0

        # Calcular cuánto ha ganado o perdido desde la entrada
        change_pct = (current_price - self.entry_price) / self.entry_price

        if change_pct <= -self.stop_loss_pct:
            return "STOP_LOSS", change_pct * 100
        
        if change_pct >= self.take_profit_pct:
            return "TAKE_PROFIT", change_pct * 100

        return None, change_pct * 100

    def place_order(self, side, amount, price, reason="AI_Signal"):
        """Simula una orden de compra o venta y la registra"""
        timestamp = datetime.datetime.now().isoformat()
        profit_pct = 0.0

        if side == "buy" and not self.is_holding:
            self.is_holding = True
            self.entry_price = price
            print(f"🔵 COMPRA VIRTUAL: {self.symbol} a ${price:,.2f} | Razón: {reason}")
            self._save_to_csv(timestamp, "BUY", price, reason, 0.0)
            return True

        elif side == "sell" and self.is_holding:
            profit_pct = ((price - self.entry_price) / self.entry_price) * 100
            self.virtual_balance += (self.virtual_balance * (profit_pct / 100))
            
            print(f"🔴 VENTA VIRTUAL: {self.symbol} a ${price:,.2f} | PNL: {profit_pct:.2f}% | Razón: {reason}")
            
            self.is_holding = False
            self.entry_price = 0.0
            self._save_to_csv(timestamp, "SELL", price, reason, profit_pct)
            return True
        
        return False

    def get_balance(self):
        """Retorna el balance virtual acumulado"""
        return self.virtual_balance

    def _save_to_csv(self, timestamp, action, price, reason, profit):
        """Guarda la operación en el archivo CSV"""
        with open(self.filename, "a") as f:
            f.write(f"{timestamp},{action},{price},{reason},{profit:.2f}\n")