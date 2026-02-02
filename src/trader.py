import os
import datetime
import pandas as pd
from upstash_redis import Redis
import ccxt

class Trader:
    def __init__(self, symbol, stop_loss_pct=0.02, take_profit_pct=0.05):
        # Update symbol for derivatives if needed (linear per user request)
        # Assuming symbol comes as "BTC/USDT", we might need "BTC/USDT:USDT" for future in some contexts
        # But commonly ccxt handles "BTC/USDT" with defaultType='future' correctly.
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
        
        # --- Configuración Exchange (Bybit) ---
        api_key = os.getenv("BYBIT_API_KEY")
        secret = os.getenv("BYBIT_SECRET_KEY")
        
        self.exchange = None
        if api_key and secret:
            try:
                self.exchange = ccxt.bybit({
                    'apiKey': api_key,
                    'secret': secret,
                    'options': {
                        'defaultType': 'future' # IMPORTANT for Shorting
                    }
                })
                self.exchange.set_sandbox_mode(True)  # MODO DE PRUEBA
                print("✅ Connected to Bybit (Sandbox Mode - Future)")
            except Exception as e:
                print(f"⚠️ Failed to connect to Bybit: {e}")
        else:
             print("⚠️ Bybit credentials missing. Running in Simulation Mode.")
        
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
        # Compatible property for existing checks, though specific long/short checks preferred
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

        # Logic is uniform: change_pct is profit relative to entry
        # If change_pct is negative, we differ from 'profit'.
        # Actually standard definition of profit % is similar.
        
        if change_pct <= -self.stop_loss_pct:
            return "STOP_LOSS", change_pct * 100
        
        if change_pct >= self.take_profit_pct:
            return "TAKE_PROFIT", change_pct * 100

        return None, change_pct * 100

    def place_order(self, side, amount, price, reason="AI_Signal"):
        """
        Ejecuta orden en Bybit.
        side: 'buy' o 'sell'.
        Dependiendo de self.position, esto abrirá o cerrará posiciones.
        - NONE + buy -> OPEN LONG
        - NONE + sell -> OPEN SHORT
        - LONG + sell -> CLOSE LONG
        - SHORT + buy -> CLOSE SHORT
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

        # --- Simulation Mode ---
        if not self.exchange:
            if "OPEN" in action_type:
                self.position = "LONG" if side == "buy" else "SHORT"
                self.entry_price = price
                print(f"🔵 SIMULATION {action_type}: {self.symbol} at ${price:,.2f}")
                self._save_to_csv(timestamp, action_type, price, reason, 0.0)
                return True
            else: # CLOSE
                # PnL calc
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

        # --- Real Execution (Sandbox Future) ---
        try:
            order = None
            if side == "buy":
                order = self.exchange.create_market_buy_order(self.symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(self.symbol, amount)
            
            # Get Fill Price
            fill_price = order['price'] if order.get('price') else price
            if not fill_price or fill_price == 0.0:
                 if 'trades' in order and len(order['trades']) > 0:
                     fill_price = order['trades'][0]['price']
                 else:
                     fill_price = price
            fill_price = float(fill_price)

            # Update State
            if "OPEN" in action_type:
                self.position = "LONG" if side == "buy" else "SHORT"
                self.entry_price = fill_price
                print(f"🚀 BYBIT {action_type}: {self.symbol} at ${fill_price:,.2f}")
                self._save_to_csv(timestamp, action_type, fill_price, reason, 0.0)
            else: # CLOSE
                profit_pct = 0.0
                if current_pos == "LONG":
                    profit_pct = ((fill_price - self.entry_price) / self.entry_price) * 100
                else: # SHORT
                    profit_pct = ((self.entry_price - fill_price) / self.entry_price) * 100
                
                print(f"💰 BYBIT {action_type}: {self.symbol} at ${fill_price:,.2f} | PnL: {profit_pct:.2f}%")
                
                self.position = "NONE"
                self.entry_price = 0.0
                self._save_to_csv(timestamp, action_type, fill_price, reason, profit_pct)
            
            return True

        except Exception as e:
            print(f"❌ Error executing order on Bybit: {e}")
            return False

    def get_balance(self):
        """Retorna el balance virtual acumulado"""
        return self.virtual_balance

    def _save_to_csv(self, timestamp, action, price, reason, profit):
        """Guarda la operación en el archivo CSV"""
        with open(self.filename, "a") as f:
            f.write(f"{timestamp},{action},{price},{reason},{profit:.2f}\n")