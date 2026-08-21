#!/bin/sh
set -eu

MODELS="qwen3-embedding:8b"

for model in $MODELS; do
  if ollama list | grep -q "$model"; then
    echo "Model already present, skip: $model"
  else
    echo "Pulling model: $model"
    ollama pull "$model"
  fi
done
