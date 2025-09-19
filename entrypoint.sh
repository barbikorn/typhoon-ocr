#!/usr/bin/env bash
set -e

# Start Ollama in background
echo "Starting Ollama server..."
OLLAMA_HOST=0.0.0.0 OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}" ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready with better error handling
echo "Waiting for Ollama to start..."
for i in {1..60}; do
  if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  if [ $i -eq 60 ]; then
    echo "Ollama failed to start after 120 seconds"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 1
  fi
  echo "Attempt $i: Ollama not ready yet, waiting..."
  sleep 2
done

# Pre-pull model if specified
if [ -n "$MODEL_NAME" ]; then
  echo "Pulling model: $MODEL_NAME"
  ollama pull "$MODEL_NAME" || echo "Failed to pull model, continuing anyway..."
fi

# Run handler
echo "Starting Python handler..."
python -u rp_handler.py
