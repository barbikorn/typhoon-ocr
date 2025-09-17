#!/usr/bin/env bash
set -e

# Start Ollama
OLLAMA_HOST=0.0.0.0 OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}" nohup ollama serve >/tmp/ollama.log 2>&1 &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
for i in {1..30}; do
  if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  echo "Attempt $i: Ollama not ready yet, waiting..."
  sleep 2
done

# Pre-pull model
if [ -n "$MODEL_NAME" ]; then
  echo "Pulling model: $MODEL_NAME"
  ollama pull "$MODEL_NAME" || echo "Failed to pull model, continuing anyway..."
fi

# Run handler
python -u rp_handler.py
