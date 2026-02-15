#!/bin/bash

# Configuration
# Cambia esto por la URL real de tu Space en Hugging Face
export ANTIGRAVITY_URL="${ANTIGRAVITY_URL:-https://fr33b0t-crypto-bot.hf.space}"

# Este secreto debe coincidir con el que pusiste en los Secrets de Hugging Face
export OPENCLAW_SECRET="${OPENCLAW_SECRET:-changeme_in_production}"

# Intervalo de ejecución en segundos (Default 60s)
export SLEEP_INTERVAL="${SLEEP_INTERVAL:-60}"

echo "Starting OpenClaw Integration..."
echo "Target: $ANTIGRAVITY_URL"
echo "Interval: ${SLEEP_INTERVAL}s"

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
fi

# Run the python script
# Usamos python3 -u para unbuffered output
python3 -u openclaw_skill.py
