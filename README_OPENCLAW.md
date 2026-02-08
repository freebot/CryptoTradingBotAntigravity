# Integración de OpenClaw con Antigravity

Este documento describe cómo conectar **OpenClaw** (u otro agente externo) con el **Bot de Trading Antigravity**.

## Arquitectura

1. **Antigravity (Servidor)**: El bot de trading principal ahora expone una API REST local en el puerto `8000`.
   - `GET /market/status`: Provee precio actual, indicadores técnicos (RSI, etc.) y estado.
   - `GET /markets/status`: Alias del anterior (para evitar errores de typo).
   - `POST /openclaw/signal`: Recibe señales de trading ("buy", "sell", "hold") y análisis de sentimiento.
   - `POST /openclaw/orders`: (NUEVO) Ejecuta una orden de compra/venta inmediatamente. JSON: `{"side": "buy", "amount": 0.01}`.

2. **OpenClaw (Cliente)**: Un script de Python (Skill) que consulta el estado del mercado, aplica inteligencia (LLM o Algorítmica), y envía órdenes al bot.

## Pasos para Ejecutar

### Lado 1: Antigravity (El Bot)
El bot ahora inicia automáticamente el servidor API cuando se ejecuta.

1. Instalar dependencias nuevas:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecutar el bot normalmente:
   ```bash
   python main.py
   ```
   *Verás en los logs que el servidor API inicia en `http://0.0.0.0:8000`.*

### Lado 2: OpenClaw (El Agente)
Tienes un script listo para usar en `scripts/openclaw_skill.py`.

1. **Configurar OpenClaw**:
   - Asegúrate de que OpenClaw tenga acceso a Python y a la red local.
   - Instala la librería `requests` en el entorno de OpenClaw si no la tiene.

2. **Ejecutar el Skill**:
   Puedes ejecutar el script manualmente para probar la conexión:
   ```bash
   python scripts/openclaw_skill.py
   ```

   O configurarlo dentro de OpenClaw como una tarea programada (cron job) para que corra cada minuto.

## Personalización de Inteligencia
Edita `scripts/openclaw_skill.py` en la función `analyze_market(data)`.
Ahí puedes conectar tu LLM favorito o agregar lógica compleja. El bot Antigravity priorizará las señales de OpenClaw sobre su estrategia técnica estándar si la confianza es alta.
