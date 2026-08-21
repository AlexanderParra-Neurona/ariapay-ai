#!/bin/sh
set -eu

MODELS="${EMBED_MODEL} ${CHAT_MODEL}"

for model in $MODELS; do
  if ollama list | grep -q "$model"; then
    echo "Model already present, skip: $model"
  else
    echo "Pulling model: $model"
    ollama pull "$model"
  fi
done
