import os
import datetime
import pandas as pd
from upstash_redis import Redis
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class Trader:
    def __init__(self, symbol, stop_loss_pct=0.02, take_profit_pct=0.05):
        # Alpaca uses standard symbols like "BTC/USD"
        self.symbol = "BTC/USD" if "BTC" in symbol or "USD" in symbol else symbol
        
        self.filename = "trading_results.csv"
        
        # --- Redis Connection for State Persistence ---
        url = os.getenv("UPSTASH_REDIS_REST_URL")
        token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        
        self.redis = None
        if url and token:
            try:
                self.redis = Redis(url=url, token=token)
                self.redis.get("test_connection")
                print("✅ Connected to Upstash Redis for State Memory")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}. Using local memory (stateless).")
        
        # --- Parámetros de Riesgo (Configurables) ---
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # --- Configuración Exchange (Alpaca) ---
        api_key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_SECRET_KEY")
        
        self.trading_client = None
        if api_key and secret:
            try:
                self.trading_client = TradingClient(api_key, secret, paper=True)
                # Quick test
                self.trading_client.get_account()
                print("✅ Connected to Alpaca (Paper Trading)")
            except Exception as e:
                print(f"⚠️ Failed to connect to Alpaca: {e}")
        else:
             print("⚠️ Alpaca credentials missing. Running in Simulation Mode.")
        
        # --- Estado Inicial (Solo si no existe en Redis) ---
        if self.redis:
            # Initialize keys if they assume empty state
            if not self.redis.get("trader:position"):
                self.redis.set("trader:position", "NONE") # NONE, LONG, SHORT
            if not self.redis.get("trader:entry_price"):
                self.redis.set("trader:entry_price", "0.0")
        else:
            # Fallback local state
            self._position = "NONE"
            self._entry_price = 0.0

        self.virtual_balance = 10000.0 

        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("timestamp,action,price,reason,profit_pct\n")

    @property
    def position(self):
        if self.redis:
            val = self.redis.get("trader:position")
            return val if val else "NONE"
        return self._position

    @position.setter
    def position(self, value):
        if self.redis:
            self.redis.set("trader:position", value)
        else:
            self._position = value

    @property
    def is_holding(self):
        return self.position != "NONE"

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
        Revisa si el precio toca SL/TP para la posición actual (LONG o SHORT).
        Retorna (Evento, Porcentaje_Ganancia)
        """
        pos = self.position
        if pos == "NONE":
            return None, 0.0

        if pos == "LONG":
            # Si sube ganamos
            change_pct = (current_price - self.entry_price) / self.entry_price
        elif pos == "SHORT":
            # Si baja ganamos (entrada - actual) / entrada
            change_pct = (self.entry_price - current_price) / self.entry_price
        else:
            return None, 0.0
        
        if change_pct <= -self.stop_loss_pct:
            return "STOP_LOSS", change_pct * 100
        
        if change_pct >= self.take_profit_pct:
            return "TAKE_PROFIT", change_pct * 100

        return None, change_pct * 100

    def place_order(self, side, amount, price, reason="AI_Signal"):
        """
        Ejecuta orden en Alpaca.
        side: 'buy' (LONG/COVER) o 'sell' (SHORT/DUMP).
        amount: Notional or qty. We'll use approx qty based on $ amount if needed or fixed qty.
        Current calling code sends 0.01 which seems like BTC quantity.
        """
        timestamp = datetime.datetime.now().isoformat()
        current_pos = self.position
        
        # --- Determine Logic ---
        action_type = ""
        if current_pos == "NONE":
            if side == "buy": action_type = "OPEN_LONG"
            elif side == "sell": action_type = "OPEN_SHORT"
        elif current_pos == "LONG" and side == "sell":
             action_type = "CLOSE_LONG"
        elif current_pos == "SHORT" and side == "buy":
             action_type = "CLOSE_SHORT"
        
        if not action_type:
            print(f"⚠️ Invalid Action: Side {side} with Position {current_pos}")
            return False

        # --- Real Execution (Alpaca) ---
        if self.trading_client:
            try:
                # Map side
                alpaca_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
                
                # Create Market Order
                # We use amount as Qty. If calling code sends 0.01 BTC, that's Qty.
                order_data = MarketOrderRequest(
                    symbol=self.symbol,
                    qty=amount,
                    side=alpaca_side,
                    time_in_force=TimeInForce.GTC
                )
                
                print(f"🚀 ALPACA SUBMITTING {action_type} for {self.symbol}...")
                order = self.trading_client.submit_order(order_data)
                
                # Ideally fetch updated fill price, but for speed we might trust 'price' argument or fetch latest
                # Alpaca orders fill async. We will log the 'trigger' price.
                fill_price = price 
                
                # Update State
                if "OPEN" in action_type:
                    self.position = "LONG" if side == "buy" else "SHORT"
                    self.entry_price = fill_price
                    print(f"✅ ALPACA {action_type} Submitted. Ref price: ${fill_price:,.2f}")
                    self._save_to_csv(timestamp, action_type, fill_price, reason, 0.0)
                else: # CLOSE
                    profit_pct = 0.0
                    if current_pos == "LONG":
                        profit_pct = ((fill_price - self.entry_price) / self.entry_price) * 100
                    else: # SHORT
                        profit_pct = ((self.entry_price - fill_price) / self.entry_price) * 100
                    
                    print(f"💰 ALPACA {action_type} Submitted. Est PnL: {profit_pct:.2f}%")
                    
                    self.position = "NONE"
                    self.entry_price = 0.0
                    self._save_to_csv(timestamp, action_type, fill_price, reason, profit_pct)
                
                return True

            except Exception as e:
                print(f"❌ Error executing order on Alpaca: {e}")
                return False
        
        # --- Simulation Fallback ---
        else:
            if "OPEN" in action_type:
                self.position = "LONG" if side == "buy" else "SHORT"
                self.entry_price = price
                print(f"🔵 SIMULATION {action_type}: {self.symbol} at ${price:,.2f}")
                self._save_to_csv(timestamp, action_type, price, reason, 0.0)
                return True
            else: # CLOSE
                profit_pct = 0.0
                if current_pos == "LONG":
                    profit_pct = ((price - self.entry_price) / self.entry_price) * 100
                else: # SHORT
                    profit_pct = ((self.entry_price - price) / self.entry_price) * 100
                
                self.virtual_balance += (self.virtual_balance * (profit_pct / 100))
                print(f"🔴 SIMULATION {action_type}: {self.symbol} at ${price:,.2f} | PnL: {profit_pct:.2f}%")
                
                self.position = "NONE"
                self.entry_price = 0.0
                self._save_to_csv(timestamp, action_type, price, reason, profit_pct)
                return True

    def get_balance(self):
        """Retorna el 'cash' disponible en Alpaca"""
        if self.trading_client:
            try:
                account = self.trading_client.get_account()
                # 'cash' is a string in Alpaca API response usually
                return float(account.cash)
            except Exception as e:
                print(f"⚠️ Error fetching Alpaca balance: {e}")
                return 0.0
        return self.virtual_balance

    def _save_to_csv(self, timestamp, action, price, reason, profit):
        """Guarda la operación en el archivo CSV"""
        with open(self.filename, "a") as f:
            f.write(f"{timestamp},{action},{price},{reason},{profit:.2f}\n")