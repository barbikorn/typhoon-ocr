#!/usr/bin/env bash
set -e

# Start Ollama
OLLAMA_HOST=0.0.0.0 OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}" nohup ollama serve >/tmp/ollama.log 2>&1 &

# Pre-pull model
sleep 2
if [ -n "$MODEL_NAME" ]; then
  ollama pull "$MODEL_NAME" || true
fi

# Run handler
python -u rp_handler.py
