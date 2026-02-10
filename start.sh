#!/bin/bash

# --- Start Script for Antigravity ---

echo "🚀 Launching Antigravity Ecosystem..."

# 1. Start the Trading Bot + API (main.py) in the background
# The API will listen on port 8000 (defined in main.py for Client Mode)
# or 7860 (for Space Mode, though usually Spaces override this script)
echo "Starting Bot & API (Port 8000)..."
# API start in background with logging to both file and stdout
python main.py 2>&1 | tee api.log &

echo "Starting Dashboard (Port 8501)..."
# Streamlit start in background
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &

echo "Testing Nginx Config..."
nginx -t

echo "Starting Nginx Proxy (Port 7860)..."
# Nginx in foreground to keep container alive
nginx -g "daemon off;"
