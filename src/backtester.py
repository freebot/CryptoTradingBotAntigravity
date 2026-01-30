import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from src.trader import Trader
from src.utils import add_indicators
from src.model import PricePredictor
import logging

# Configurar logger para backtest silencioso
logger = logging.getLogger("Backtester")
logging.basicConfig(level=logging.INFO)

class BacktestTrader(Trader):
    """
    Versión del Trader optimizada para simulación en memoria.
    No escribe a CSV, guarda en lista para análisis.
    """
    def __init__(self, symbol, stop_loss_pct, take_profit_pct, initial_balance=10000):
        super().__init__(symbol, stop_loss_pct, take_profit_pct)
        self.virtual_balance = initial_balance
        self.initial_balance = initial_balance
        self.trades = [] # Lista de diccionarios con historia
        self.equity_curve = [] # Evolución del balance

    def _save_to_csv(self, timestamp, action, price, reason, profit):
        # Sobreescribimos para no dañar el CSV real y guardar en memoria
        self.trades.append({
            "timestamp": timestamp,
            "action": action,
            "price": price,
            "reason": reason,
            "profit_pct": profit,
            "balance": self.virtual_balance
        })

    def force_close(self, price, timestamp, reason="END_OF_BACKTEST"):
        """Cierra posiciones abiertas al final del backtest"""
        if self.is_holding:
            self.place_order("sell", 0, price, reason)

class Backtester:
    def __init__(self, symbol="BTC-USD", timeframe="1h", period="60d"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.period = period
        self.price_predictor = PricePredictor()
    
    def fetch_data(self):
        print(f"📥 Descargando datos históricos de {self.symbol} ({self.period})...")
        # Usamos yfinance que es gratuito y robusto para históricos
        df = yf.download(tickers=self.symbol, period=self.period, interval=self.timeframe, progress=False)
        if df.empty:
            raise ValueError("No se pudieron descargar datos.")
        
        # Corrección para versiones nuevas de yfinance que devuelven MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            try:
                # Intentar obtener nivel de 'Price' si existe, o colapsar
                df.columns = df.columns.get_level_values(0)
            except:
                pass

        # Estandarizar columnas a minúsculas para compatibilidad con utils.py
        df.columns = [str(c).lower() for c in df.columns]
        # yfinance devuelve 'Adj Close' a veces, nos aseguramos de tener 'close'
        if 'adj close' in df.columns:
            df['close'] = df['adj close']
            
        print(f"✅ Datos cargados: {len(df)} velas.")
        return df

    def run(self, stop_loss=0.02, take_profit=0.05):
        df = self.fetch_data()
        
        # Simulamos settings
        settings = {
            "rsi_period": 14, 
            "macd_fast": 12, "macd_slow": 26, "macd_signal": 9 
        }
        
        # Añadir indicadores (reutilizamos la lógica real del bot)
        df = add_indicators(df, settings)
        
        # Inicializar Trader Simulado
        trader = BacktestTrader(self.symbol, stop_loss, take_profit)
        
        print("\n▶️ Iniciando Simulación...")
        
        for index, row in df.iterrows():
            current_price = row['close']
            
            # 1. Gestión de Riesgo (Check SL/TP)
            risk_event, pnl = trader.check_risk_management(current_price)
            if risk_event:
                trader.place_order("sell", 0, current_price, reason=risk_event)
                continue # Si vendimos, pasamos a la siguiente vela
            
            # 2. Lógica de Trading (Simplificada sin Noticias Históricas)
            # Para el backtest, asumimos que el Sentiment es NEUTRAL o 
            # confiamos puramente en el técnico para validar la robustez base.
            
            # Generar ventana de datos (lookback) para el predictor
            # (En una implementación real compleja pasaríamos el slice histórico df.iloc[:i])
            # Aquí pasamos el DF completo pero el predictor dummy solo mira la última fila actual
            # Para ser estrictos deberíamos pasar df.iloc[:i+1], pero por rendimiento
            # y dado que nuestro predictor dummy es simple, usaremos la lógica row por row simulada.
            
            current_slice = df.loc[:index] 
            signal = self.price_predictor.predict_next_move(current_slice)
            
            # Lógica de Compra
            if signal == "UP" and not trader.is_holding:
                # Simulamos slippage o spread simple (0.1%)
                buy_price = current_price * 1.001 
                trader.place_order("buy", 0, buy_price, reason="TECH_SIGNAL")
                
            # Lógica de Venta por Señal Técnica
            elif signal == "DOWN" and trader.is_holding:
                sell_price = current_price * 0.999
                trader.place_order("sell", 0, sell_price, reason="TECH_SIGNAL")
            
            # Registrar evolución de capital (Equity Curve)
            # Si holding, valor = balance + valor actual activo
            equity = trader.virtual_balance
            if trader.is_holding:
                # Valor flotante
                profit_unrealized = (current_price - trader.entry_price) / trader.entry_price
                equity = trader.virtual_balance * (1 + profit_unrealized) # Aproximación
                
            trader.equity_curve.append(equity)

        # Cierre forzoso al final
        last_price = df.iloc[-1]['close']
        trader.force_close(last_price, "END_OF_TEST")
        
        return trader

def analyze_results(trader):
    trades = pd.DataFrame(trader.trades)
    
    print("\n" + "="*40)
    print("📊 REPORTE DE RESULTADOS (BACKTEST)")
    print("="*40)
    
    if trades.empty:
        print("⚠️ No se realizaron operaciones.")
        return

    total_trades = len(trades[trades['action'] == 'SELL'])
    wins = len(trades[(trades['action'] == 'SELL') & (trades['profit_pct'] > 0)])
    losses = len(trades[(trades['action'] == 'SELL') & (trades['profit_pct'] <= 0)])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    initial = trader.initial_balance
    final = trader.virtual_balance
    roi_pct = ((final - initial) / initial) * 100
    
    print(f"💰 Balance Inicial:   ${initial:,.2f}")
    print(f"🏁 Balance Final:     ${final:,.2f}")
    print(f"📈 ROI Total:         {roi_pct:.2f}%")
    print("-" * 20)
    print(f"🤝 Total Operaciones: {total_trades}")
    print(f"✅ Ganadoras:         {wins}")
    print(f"❌ Perdedoras:        {losses}")
    print(f"🎯 Win Rate:          {win_rate:.2f}%")
    
    print("\n📝 Historial Reciente:")
    print(trades[['action', 'price', 'reason', 'profit_pct']].tail())

    # Devolver DataFrame para potenciar análisis gráfico si se desea
    return trades

if __name__ == "__main__":
    # Configuración del Backtest
    # Usamos BTC-USD de Yahoo Finance
    bt = Backtester(symbol="BTC-USD", period="60d", timeframe="1h")
    
    # Ejecutar con SL=2%, TP=5%
    trader_result = bt.run(stop_loss=0.02, take_profit=0.05)
    
    analyze_results(trader_result)
