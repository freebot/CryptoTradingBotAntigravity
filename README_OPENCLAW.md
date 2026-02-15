# Integración Segura de OpenClaw con Antigravity

Este documento describe cómo conectar **OpenClaw** (corriendo en AWS u otro servidor lejano) con el **Bot de Trading Antigravity** (en Hugging Face) de manera segura y funcional.

## Capacidades

1.  **Comunicación Segura**: Autenticación vía `X-Auth-Token` (Header).
2.  **Ejecución de Órdenes**: OpenClaw puede ejecutar compras/ventas directamente.
3.  **Registro en Notion**: Todas las operaciones exitosas se registran automáticamente en tu base de datos de Notion con detalles de sentimiento y confianza.
4.  **Datos de Mercado**: OpenClaw recibe precio, tendencia, RSI y volumen en tiempo real.

## Arquitectura

-   **Servidor**: Antigravity Bot (Hugging Face Space)
    -   API: `https://[TU_ESPACIO].hf.space`
    -   Endpoints:
        -   `GET /market/status`: Estado del mercado.
        -   `POST /openclaw/orders`: Ejecución inmediata + Log a Notion.
        -   `POST /openclaw/signal`: Envío de señales de inversión (Sugerencias).

-   **Cliente**: OpenClaw (AWS EC2 e3.micro)
    -   Script: `scripts/openclaw_skill.py`
    -   Lógica: Consulta mercado -> Decide -> Ejecuta.

## Guía de Despliegue en AWS (e3.micro)

### 1. Preparar el Servidor AWS
Conéctate a tu instancia e3.micro vía SSH:
```bash
ssh -i "tu-clave.pem" ubuntu@tu-instancia-aws.com
```

### 2. Configurar el Entorno
Ejecuta estos comandos para preparar Python y las dependencias:
```bash
sudo apt update && sudo apt install -y python3 python3-pip
pip3 install requests
```

### 3. Instalar el Agente OpenClaw
Puedes clonar el repositorio completo o simplemente crear el archivo `openclaw_skill.py`:

**Opción A (Clonar Repo):**
```bash
git clone https://github.com/tu-usuario/CryptoTradingBotAntigravity.git
cd CryptoTradingBotAntigravity
```

**Opción B (Solo el Script):**
```bash
mkdir openclaw && cd openclaw
nano openclaw_skill.py
# (Copea el contenido de scripts/openclaw_skill.py aquí)
```

### 4. Ejecutar con Seguridad
Necesitas definir dos variables de entorno claves:
1.  `ANTIGRAVITY_URL`: La URL de tu Space en Hugging Face (ej. `https://fr33b0t-crypto-bot.hf.space`).
2.  `OPENCLAW_SECRET`: Tu contraseña secreta (Debe coincidir con la variable `OPENCLAW_SECRET` en los Secrets de Hugging Face).

Ejecuta el agente:
```bash
export ANTIGRAVITY_URL="https://fr33b0t-crypto-bot.hf.space"
export OPENCLAW_SECRET="tu_super_secreto_seguro"

# Ejecutar en segundo plano (para que no se cierre al salir de SSH)
nohup python3 openclaw_skill.py > openclaw.log 2>&1 &
```

Para ver los logs:
```bash
tail -f openclaw.log
```

## Configuración en Hugging Face (Servidor)

Asegúrate de configurar los **Secrets** en tu Space de Hugging Face:
1.  Ve a **Settings** -> **Variables and secrets**.
2.  Añade `OPENCLAW_SECRET` con el mismo valor que usaste en AWS.
3.  Asegúrate de que `NOTION_TOKEN` y `NOTION_DATABASE_ID` estén configurados para que el registro funcione.

## Personalización de la Estrategia
Edita la función `analyze_market(data)` en `openclaw_skill.py` para inyectar tu propia lógica o conectar con un LLM externo.
Cuando OpenClaw decida operar, llamará a `execute_order(side, amount, ...)` que automáticamente:
1.  Enviará la orden a Antigravity.
2.  Antigravity ejecutará la orden en Alpaca.
3.  Antigravity registrará la operación en Notion.
