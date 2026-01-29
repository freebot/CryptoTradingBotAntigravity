---
title: Antigravity Crypto Bot
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_file: main.py
pinned: false
---

# 🚀 Project Antigravity: ML Crypto Trading Bot

Este es un proyecto experimental diseñado para construir un bot de trading de criptomonedas automatizado utilizando Machine Learning. El objetivo principal es el aprendizaje del ciclo completo de desarrollo: desde la obtención de datos y entrenamiento de modelos, hasta la ejecución de órdenes en un entorno de prueba (dinero ficticio).

Desarrollado con Antigravity, este proyecto aprovecha las capacidades de "Vibecoding" para agilizar la escritura de código y la orquestación de agentes.
🎯 Objetivos del Proyecto

    Aprender: Entender cómo interactúan las APIs financieras con modelos de IA.

    Predecir: Usar modelos de Hugging Face para análisis de sentimiento y predicción de precios.[1]

    Simular: Operar en el Binance Testnet (dinero falso) para medir el rendimiento sin riesgo.

    Nube: Ejecutar el bot de forma gratuita o de bajo coste utilizando GitHub Actions o Hugging Face Spaces.

🛠️ Tecnologías y Recursos[2][3][4][5][6][7]

    IDE & Framework: Antigravity (Google Gemini 3 Agent Framework).

    Machine Learning: Hugging Face (Transformers para sentimiento y LSTMs para series temporales).

    Exchange API: Binance Testnet (Paper Trading con $15,000 ficticios).

    Data Source: CoinGecko API (Datos históricos y market cap gratuitos).

    Lenguaje: Python 3.10+.

    Infraestructura: GitHub Actions (para ejecución programada) o Hugging Face Spaces (Docker).

🏗️ Estructura del Proyecto
code Text

antigravity-trade-bot/
├── .github/workflows/      # Ejecución automática (cron job)
├── src/
│   ├── data_loader.py      # Conexión con CoinGecko/Binance
│   ├── model.py            # Lógica de ML (Hugging Face)
│   ├── trader.py           # Ejecución de órdenes en Testnet
│   └── utils.py            # Indicadores técnicos (RSI, MACD)
├── config/
│   └── settings.json       # Configuración de pares (ej. BTC/USDT)
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
└── .env.example            # Variables de entorno (API Keys)

🚀 Guía de Configuración
1. Obtener API Keys (Gratis)

    Binance Testnet: Ve a Binance Spot Testnet, logueate con tu GitHub y genera tu API_KEY y SECRET_KEY.

    Hugging Face: Crea una cuenta en Hugging Face y obtén un Token de lectura para descargar modelos.

2. Configurar el Entorno

Copia el archivo .env.example a .env y rellena tus datos:
code Bash

BINANCE_API_KEY=tu_key_de_testnet
BINANCE_SECRET_KEY=tu_secret_de_testnet
HF_TOKEN=tu_token_de_huggingface

3. Instalación

Si usas Antigravity, puedes simplemente pedirle al agente: "Instala las dependencias necesarias para un bot de trading con CCXT y Hugging Face" o correr:
code Bash

pip install ccxt transformers torch pandas python-dotenv

🧠 Lógica de Inteligencia Artificial

El bot utiliza un enfoque de Ensemble Learning:

    Análisis de Sentimiento: Usa el modelo ProsusAI/finbert de Hugging Face para analizar noticias recientes y determinar si el mercado es "Bullish" o "Bearish".

    Predicción Técnica: Un modelo de regresión simple o LSTM para predecir el siguiente movimiento basado en el histórico de precios.

    Decisión: Solo ejecuta una compra si ambos modelos (Sentimiento + Técnico) coinciden.

☁️ Despliegue en la Nube (Gratis)

Para que el bot corra 24/7 o por intervalos sin dejar tu PC encendida:

    Opción A (GitHub Actions): Configura un "Workflow" que se ejecute cada 1 hora. Es ideal para aprender cómo funcionan los pipelines de CI/CD aplicados a finanzas.

    Opción B (Hugging Face Spaces): Crea un "Space" tipo Docker o Streamlit. Te permite tener una interfaz visual para ver tus ganancias en tiempo real.

📈 Medición de Resultados

El bot registrará cada operación en un archivo trades.csv local y mostrará:

    Balance Inicial: $15,000 (Mock)

    Win Rate: % de operaciones ganadoras.

    Profit/Loss (P&L): Ganancia neta acumulada.[8]

⚠️ Descargo de Responsabilidad (Disclaimer)

Este proyecto es estrictamente educativo. El uso de algoritmos de trading conlleva riesgos financieros significativos. Nunca uses este bot con dinero real sin una validación exhaustiva y bajo tu propia responsabilidad.
