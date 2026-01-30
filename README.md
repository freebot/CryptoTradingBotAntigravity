---
title: Crypto Bot Dashboard
emoji: 📈
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: false
---

# 🚀 Project Antigravity: Intelligent ML Trading Bot

Este es un ecosistema de trading algorítmico diseñado no solo para operar, sino para evolucionar. El proyecto utiliza **Machine Learning (NLP)** para entender el sentimiento del mercado y **Gestión de Riesgos Cuantitativa** para proteger el capital. 

Desarrollado con **Antigravity**, este bot representa el ciclo completo de un ingeniero de software financiero: desde la simulación en la nube hasta el monitoreo profesional en **Notion**.

## 📊 Dashboard de Control (Notion)
A diferencia de otros bots, Project Antigravity no solo escupe texto en una consola. Hemos integrado una **"Pantalla de Comando" en Notion** donde puedes ver en tiempo real desde cualquier dispositivo:
- **Avance del ML:** Sentimiento detectado y nivel de confianza de la IA.
- **Estado de Cuenta:** Ganancias y pérdidas (PnL) acumuladas.
- **Bitácora de Decisiones:** Por qué el bot decidió comprar, vender o ejecutar un Stop Loss.

---

## 🏗️ Arquitectura Híbrida: Client-Server
El sistema ha evolucionado a una arquitectura distribuida inteligente para optimizar recursos:

### 1. 🧠 Los Cerebros (Hugging Face Spaces Distribuidos)
El sistema utiliza una arquitectura de microservicios:
- **Crypto Sentiment API**: Servidor FastAPI dedicado a IA (FinBERT) para análisis de noticias.
- **Crypto Tech API**: Servidor FastAPI para análisis técnico y backup.
- **Crypto Bot Dashboard**: Panel de visualización en Streamlit para monitoreo humano.

### 2. ⚡ El Agente (GitHub Actions / Local)
Actúa como **Cliente Ligero**.
- **Tecnología**: Python plano (sin PyTorch).
- **Eficiencia**: En lugar de descargar modelos pesados, utiliza `RemoteSentimentAnalyzer` para consultar a los Cerebros vía API.
- **Ventaja**: Ejecución ultra-rápida (segundos vs minutos) y mínimo consumo de recursos en CI/CD.

```text
antigravity-trade-bot/
├── .github/workflows/      # Orquestación: Despierta al cerebro antes de operar
├── src/
│   ├── app.py              # Dashboard (Streamlit)
│   ├── sentiment_brain.py  # API de Sentimiento (FastAPI)
│   ├── tech_brain.py       # API Técnica (FastAPI)
│   ├── main.py             # Agente de Trading
│   └── ...
```

🧠 Inteligencia y Estrategia

El bot opera bajo una lógica de Confirmación Dual:

    Análisis de Sentimiento: Utiliza FinBERT de Hugging Face para procesar noticias. Solo compra si el sentimiento es marcadamente "Bullish" (>0.80).

    Filtro Técnico: Utiliza indicadores (RSI, Medias Móviles) para confirmar que el precio no está sobrecomprado.

    🛡️ Risk Management (Nivel Pro):

        Stop Loss (2%): Si el mercado se vuelve en contra, el bot corta la pérdida inmediatamente.

        Take Profit (5%): El bot asegura ganancias automáticamente al alcanzar el objetivo.

📈 Plan de Evolución: De "Estudiante" a "Pro"

Para ganar dinero real, el bot seguirá esta hoja de ruta de crecimiento:
Fase 1: Simulación y Nube (Estado Actual)

    Objetivo: Validar la estrategia sin riesgo.

    Entorno: GitHub Actions / Hugging Face Spaces.

    Datos: CoinGecko API (Evita bloqueos de IP).

    Ejecución: Virtual Paper Trading.

Fase 2: Inteligencia Aumentada (Próximamente)

    Mejora: Conexión con NewsAPI para leer noticias reales en tiempo real.

    Eficiencia: Implementación de Trailing Stop Loss (el stop persigue el precio para maximizar ganancias).

    Análisis: Registro automático de errores y "alucinaciones" de la IA en Notion.

Fase 3: Operación Local (Salto a Real)

    Objetivo: Evitar bloqueos de IP de Exchanges (Binance/Bybit).

    Entorno: Ejecución en servidor local (Raspberry Pi o Laptop 24/7).

    Capital: Inyección de $20 USD reales para probar ejecución, comisiones (fees) y latencia.

Fase 4: Escalabilidad Cuantitativa

    Optimización: Ajuste automático de parámetros basado en el Ratio de Sharpe.

    Diversificación: Operación multi-moneda (BTC, ETH, SOL) simultánea.

    Independencia: Migración a modelos de ML propios ajustados a cripto.

🚀 Guía de Configuración Rápida
1. Variables de Entorno (Secrets)

Configura los siguientes secretos en tu repositorio de GitHub:

    HF_TOKEN: Tu token de Hugging Face.

    NOTION_TOKEN: Token de integración de Notion.

    NOTION_DATABASE_ID: ID de tu base de datos en Notion.

2. Conectar Notion

    Crea una base de datos en Notion con columnas: Fecha, Accion, Precio, Sentimiento, Confianza ML, Profit Acumulado.

    Agrega la conexión de tu integración de Notion a la página.

⚠️ Descargo de Responsabilidad

Este proyecto tiene fines exclusivamente educativos. El trading de criptomonedas implica un riesgo de pérdida total del capital. El autor no se hace responsable por pérdidas financieras derivadas del uso de este código. La fase 1 es puramente virtual.