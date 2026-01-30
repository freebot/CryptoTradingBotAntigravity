import os
import datetime
import pandas as pd

class Trader:
    def __init__(self, symbol, paper_trading=True):
        self.symbol = symbol
        self.filename = "trading_results.csv"
        
        # --- Parámetros de Riesgo Virtual ---
        self.stop_loss_pct = 0.02   # 2% máximo de pérdida
        self.take_profit_pct = 0.05  # 5% objetivo de ganancia
        
        # --- Estado de la Cartera Virtual ---
        self.is_holding = False
        self.entry_price = 0.0
        self.virtual_balance = 10000.0 # Empezamos con $10,000 USD ficticios

        # Crear archivo de logs si no existe
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("timestamp,action,price,reason,profit_pct\n")

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