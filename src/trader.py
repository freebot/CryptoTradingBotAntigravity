import os
import datetime
import pandas as pd
from upstash_redis import Redis
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class Trader:
    def __init__(self, symbol, stop_loss_pct=0.02, take_profit_pct=0.05):
        # Normalizar símbolo para Alpaca (Ej: BTC/USD)
        self.symbol = "BTC/USD"
        if "ETH" in symbol: self.symbol = "ETH/USD"
        
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
        
        # --- Parámetros de Riesgo ---
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # --- Configuración Alpaca Paper Trading ---
        api_key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_SECRET_KEY")
        # El endpoint por defecto de la librería suele ser paper, pero podemos ser explícitos si quisiéramos
        # paper=True se encarga de usar https://paper-api.alpaca.markets
        
        self.trading_client = None
        if api_key and secret:
            try:
                self.trading_client = TradingClient(api_key, secret, paper=True)
                # Quick test
                acc = self.trading_client.get_account()
                print(f"✅ Connected to Alpaca | Buying Power: ${acc.buying_power}")
            except Exception as e:
                print(f"⚠️ Failed to connect to Alpaca: {e}")
        else:
             print("⚠️ Alpaca credentials missing. Running in Simulation Mode.")
        
        # --- Estado Inicial (Redis o Local) ---
        if self.redis:
            if not self.redis.get("trader:position"):
                self.redis.set("trader:position", "NONE")
            if not self.redis.get("trader:entry_price"):
                self.redis.set("trader:entry_price", "0.0")
        else:
            self._position = "NONE"
            self._entry_price = 0.0

        self.virtual_balance = 100000.0 # Paper starting balance sim

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
        Revisa SL/TP.
        Pos LONG: (Actual - Entry) / Entry
        Pos SHORT: (Entry - Actual) / Entry
        """
        pos = self.position
        if pos == "NONE": return None, 0.0

        entry = self.entry_price
        if entry == 0: return None, 0.0
        
        profit_pct = 0.0
        if pos == "LONG":
            profit_pct = (current_price - entry) / entry
        elif pos == "SHORT":
            profit_pct = (entry - current_price) / entry # Si precio baja, ganamos (+)
            
        # Si profit_pct es -0.05 significa perdida del 5%
        # Stop Loss Trigger: Si profit <= -SL_PCT (ej: -0.02)
        if profit_pct <= -self.stop_loss_pct:
            return "STOP_LOSS", profit_pct * 100
        
        # Take Profit Trigger: Si profit >= TP_PCT (ej: 0.05)
        if profit_pct >= self.take_profit_pct:
            return "TAKE_PROFIT", profit_pct * 100
            
        return None, profit_pct * 100

    def place_order(self, side, amount, price, reason="AI_Signal"):
        """
        Ejecuta orden real en Alpaca para Crypto.
        side: 'buy' o 'sell'.
        amount: Cantidad de activo base (ej 0.01 BTC).
        """
        timestamp = datetime.datetime.now().isoformat()
        current_pos = self.position
        
        # Mapeo de lógica
        action_type = ""
        if current_pos == "NONE":
            if side == "buy": action_type = "OPEN_LONG"
            elif side == "sell": action_type = "OPEN_SHORT"
        elif current_pos == "LONG" and side == "sell":
             action_type = "CLOSE_LONG"
        elif current_pos == "SHORT" and side == "buy":
             action_type = "CLOSE_SHORT"
        
        if not action_type:
            print(f"⚠️ Action Invalid: {side} while in {current_pos}")
            return False

        # --- REAL TRADING via ALPACA ---
        if self.trading_client:
            try:
                alpaca_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
                
                # Market Order
                req = MarketOrderRequest(
                    symbol=self.symbol,
                    qty=amount,
                    side=alpaca_side,
                    time_in_force=TimeInForce.GTC
                )
                
                print(f"🚀 Enviando orden a Alpaca: {action_type} {self.symbol}...")
                order = self.trading_client.submit_order(req)
                
                # Actualizar estado interno (Asumimos fill al precio actual para el tracking rápido)
                # En sistemas reales se usaría websocket para confirmar fill
                if "OPEN" in action_type:
                    self.position = "LONG" if side == "buy" else "SHORT"
                    self.entry_price = price
                else:
                    # Cerrando posición
                    # Cálculo PnL Estimado
                    pnl = 0.0
                    entry = self.entry_price
                    if current_pos == "LONG": pnl = ((price - entry)/entry)*100
                    else: pnl = ((entry - price)/entry)*100
                    
                    self.position = "NONE"
                    self.entry_price = 0.0
                    print(f"💰 {action_type} Completado. PnL Est: {pnl:.2f}%")
                    self._save_to_csv(timestamp, action_type, price, reason, pnl)
                
                return action_type
                
            except Exception as e:
                print(f"❌ Error Alpaca Order: {e}")
                return False
        
        # --- SIMULATION FALLBACK ---
        else:
            # Lógica de simulación idéntica...
            # (Omitida para brevedad si ya tienes credenciales, pero buena práctica dejarla)
            print(f"🔵 SIMULATION {action_type} @ ${price:,.2f}")
            if "OPEN" in action_type:
                self.position = "LONG" if side == "buy" else "SHORT"
                self.entry_price = price
            else:
                pnl = 0.0
                entry = self.entry_price
                if current_pos == "LONG": pnl = ((price - entry)/entry)*100
                else: pnl = ((entry - price)/entry)*100
                self.position = "NONE"
                self.entry_price = 0.0
                self._save_to_csv(timestamp, action_type, price, reason, pnl)
            return action_type

    def get_balance(self):
        if self.trading_client:
            try:
                acc = self.trading_client.get_account()
                return float(acc.equity) # Retorna Equidad Total
            except:
                return 0.0
        return self.virtual_balance

    def _save_to_csv(self, timestamp, action, price, reason, profit):
        with open(self.filename, "a") as f:
            f.write(f"{timestamp},{action},{price},{reason},{profit:.2f}\n")