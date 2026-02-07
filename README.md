---
title: Antigravity Trading Ecosystem 📈
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 🚀 Project Antigravity: Distributed ML Trading Ecosystem

Este proyecto ha evolucionado de un simple script a un **ecosistema de trading distribuido**. Utiliza una arquitectura de **Microservicios** para maximizar los recursos gratuitos de la nube, separando la carga pesada de Inteligencia Artificial (Cerebro) de la ejecución lógica y gestión de órdenes (Músculo).

Desarrollado con **Antigravity**, el bot integra análisis de sentimiento en tiempo real, indicadores técnicos avanzados y una infraestructura de grado profesional.

## 🏗️ Arquitectura de Microservicios: "Brain & Muscle"

Para optimizar los límites de 2GB de RAM de Hugging Face y los tiempos de ejecución de GitHub Actions, el sistema se divide en:

### 1. 🧠 Los Cerebros (Hugging Face Spaces)
Servidores dedicados que permanecen encendidos o se "despiertan" bajo demanda:
- **Crypto Sentiment API**: Servidor FastAPI que mantiene cargado el modelo `FinBERT`. Procesa noticias de Reddit y RSS sin que el cliente tenga que cargar pesadas librerías de IA.
- **Crypto Tech API**: Servidor de respaldo para procesamiento matemático y redundancia.
- **Crypto Bot Dashboard**: La cara pública del proyecto. Una interfaz en **Streamlit** que visualiza datos en tiempo real desde Supabase.

### 2. ⚡ El Agente / Músculo (GitHub Actions)
El ejecutor que despierta cada hora (Cron Job) para realizar el ciclo de trading:
- **Tecnología**: Python ligero (Requests + Pandas).
- **Eficiencia**: Consulta a los "Cerebros" vía API, reduciendo el tiempo de ejecución de minutos a segundos.
- **Memoria de Corto Plazo**: Utiliza **Upstash Redis** para recordar el estado de las órdenes entre ejecuciones (Persistencia de `is_holding` y `entry_price`).

### 3. 🗄️ El Almacén (Supabase & Notion)
- **Notion**: Dashboard operativo para humanos. Registro de decisiones y sentimiento.
- **Supabase (PostgreSQL)**: Base de datos histórica para almacenar logs de mercado y alimentar el Dashboard de Streamlit.

---

## 🧠 Estrategia de Inversión: Confirmación Dual

El bot no opera por intuición, sino por **convergencia de datos**:
1.  **Análisis de Sentimiento**: Escanea `r/Bitcoin`, `r/CryptoCurrency` y `r/Ethereum`. Solo permite compras si la IA detecta un sentimiento **BULLISH** con confianza > 0.80.
2.  **Filtro Técnico**: Valida tendencias mediante RSI y Medias Móviles para evitar comprar en techos de mercado.
3.  **🛡️ Gestión de Riesgos (Prioridad Alpha)**:
    - **Stop Loss (2%)**: Protección matemática ante caídas repentinas.
    - **Take Profit (5%)**: Captura de ganancias automatizada.
    - **Persistencia con Redis**: El bot "sabe" que tiene una posición abierta aunque el script se haya cerrado.

---

## 📈 Plan de Evolución

### Fase 1: Cimientos Distribuidos (Actual)
- Despliegue de APIs en Hugging Face.
- Integración de Memoria Persistente con Upstash Redis.
- Monitoreo en Notion.

### Fase 2: Visualización y Alertas (En curso)
- **Dashboard en Streamlit**: Sustitución de logs por gráficas interactivas.
- **Telegram Bot**: Notificaciones "Push" al móvil y comandos de consulta `/status`.
- **Supabase Integration**: Histórico de datos para análisis de rendimiento.

### Fase 3: Operación Real
- Migración a ejecución local (Raspberry Pi/Home Server) para evitar bloqueos de IP de los Exchanges.
- Implementación de **Trailing Stop Loss**.
- Gestión de órdenes reales con capital controlado ($20 USD).

---

## 🚀 Guía de Configuración

### Variables de Entorno (GitHub Secrets)
Para que el ecosistema funcione, configura los siguientes Secrets en tu repositorio:

| Secreto | Función |
| :--- | :--- |
| `HF_TOKEN` | Permiso para actualizar Spaces y despertar la API. |
| `NOTION_TOKEN` / `NOTION_DATABASE_ID` | Conexión con el Dashboard de Notion. |
| `UPSTASH_REDIS_REST_URL` / `TOKEN` | Memoria de corto plazo del bot. |
| `SUPABASE_URL` / `SUPABASE_KEY` | Almacenamiento histórico de trades. |
| `TELEGRAM_BOT_TOKEN` / `CHAT_ID` | Alertas en tiempo real al móvil. |

---

## ⚠️ Descargo de Responsabilidad (Disclaimer)
Este proyecto es estrictamente **educativo**. El trading de criptomonedas conlleva riesgos financieros significativos. La lógica de Machine Learning puede fallar. **Nunca** operes con dinero que no puedas permitirte perder.

---
*Powered by Antigravity, Hugging Face and the Open Source Community.*