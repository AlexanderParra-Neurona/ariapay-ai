#!/bin/sh
set -eu

COLLECTIONS="${QDRANT_COLLECTION}"

for collection in $COLLECTIONS; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "${QDRANT_URL}/collections/${collection}")
  if [ "$status" = "200" ]; then
    echo "Collection already exists, skip: $collection"
  else
    echo "Creating collection: $collection"
    curl -sf -X PUT "${QDRANT_URL}/collections/${collection}" \
      -H "Content-Type: application/json" \
      -d "{\"vectors\": {\"size\": ${EMBED_DIM}, \"distance\": \"Cosine\"}}"
    echo "Created collection: $collection"
  fi
done
