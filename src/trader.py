import os
import datetime
import pandas as pd
import os
import datetime
import pandas as pd
from upstash_redis import Redis
import ccxt

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
        
        # --- Configuración Exchange (Bybit) ---
        api_key = os.getenv("BYBIT_API_KEY")
        secret = os.getenv("BYBIT_SECRET_KEY")
        
        self.exchange = None
        if api_key and secret:
            try:
                self.exchange = ccxt.bybit({
                    'apiKey': api_key,
                    'secret': secret,
                })
                self.exchange.set_sandbox_mode(True)  # MODO DE PRUEBA
                print("✅ Connected to Bybit (Sandbox Mode)")
            except Exception as e:
                print(f"⚠️ Failed to connect to Bybit: {e}")
        else:
             print("⚠️ Bybit credentials missing. Running in Simulation Mode.")
        
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
        """Ejecuta una orden de mercado en Bybit y actualiza el estado"""
        timestamp = datetime.datetime.now().isoformat()
        profit_pct = 0.0
        
        # Simulación si no hay exchange configurado
        if not self.exchange:
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

        # Ejecución Real (Sandbox)
        try:
            if side == "buy" and not self.is_holding:
                # amount es la cantidad de cripto, pero para facilitar usaremos costo en USDT si es posible
                # o asumimos que 'amount' viene calculado correctamente.
                # Para simplificar, compraremos fixed amount o calcularemos based on balance.
                # Aquí asumimos que 'amount' es la cantidad de tokens a comprar.
                
                # Nota: En un entorno real, deberíamos chequear balance primero.
                order = self.exchange.create_market_buy_order(self.symbol, amount)
                
                fill_price = order['price'] if order.get('price') else price # Fallback if None
                if not fill_price or fill_price == 0.0:
                     # Intentar sacar precio de trades si disponible
                     if 'trades' in order and len(order['trades']) > 0:
                         fill_price = order['trades'][0]['price']
                     else:
                         fill_price = price # Last resort fallback
                
                self.is_holding = True
                self.entry_price = float(fill_price)
                
                print(f"🔵 BYBIT BUY: {self.symbol} a ${fill_price:,.2f} | ID: {order['id']}")
                self._save_to_csv(timestamp, "BUY", fill_price, reason, 0.0)
                return True

            elif side == "sell" and self.is_holding:
                order = self.exchange.create_market_sell_order(self.symbol, amount)
                
                fill_price = order['price'] if order.get('price') else price
                if not fill_price or fill_price == 0.0:
                     if 'trades' in order and len(order['trades']) > 0:
                         fill_price = order['trades'][0]['price']
                     else:
                         fill_price = price

                profit_pct = ((float(fill_price) - self.entry_price) / self.entry_price) * 100
                
                print(f"🔴 BYBIT SELL: {self.symbol} a ${fill_price:,.2f} | PNL: {profit_pct:.2f}%")
                
                self.is_holding = False
                self.entry_price = 0.0
                self._save_to_csv(timestamp, "SELL", fill_price, reason, profit_pct)
                return True
                
        except Exception as e:
            print(f"❌ Error executing order on Bybit: {e}")
            return False
            
        return False

    def get_balance(self):
        """Retorna el balance virtual acumulado"""
        return self.virtual_balance

    def _save_to_csv(self, timestamp, action, price, reason, profit):
        """Guarda la operación en el archivo CSV"""
        with open(self.filename, "a") as f:
            f.write(f"{timestamp},{action},{price},{reason},{profit:.2f}\n")