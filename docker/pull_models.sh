#!/bin/sh
set -eu

MODELS="${OLLAMA_EMBED_MODEL} ${OLLAMA_CHAT_MODEL} llama3.1:8b"

for model in $MODELS; do
  if ollama list | grep -q "$model"; then
    echo "Model already present, skip: $model"
  else
    echo "Pulling model: $model"
    ollama pull "$model"
  fi
done
