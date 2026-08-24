#!/bin/sh
set -eu

COLLECTIONS="${QDRANT_COLLECTION}"

for collection in $COLLECTIONS; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "${QDRANT_URL}/collections/${collection}")
  if [ "$status" = "200" ]; then
    schema=$(curl -sf "${QDRANT_URL}/collections/${collection}")
    if ! echo "$schema" | grep -q '"docs":' || ! echo "$schema" | grep -q '"transactions":'; then
      echo "ERROR: Collection '$collection' exists with an incompatible schema (expected named vectors 'docs' and 'transactions'). Drop the collection and re-run ingestion to migrate." >&2
      exit 1
    fi
    echo "Collection already exists, skip: $collection"
  else
    echo "Creating collection: $collection"
    curl -sf -X PUT "${QDRANT_URL}/collections/${collection}" \
      -H "Content-Type: application/json" \
      -d "{\"vectors\": {\"docs\": {\"size\": ${EMBED_DIM}, \"distance\": \"Cosine\"}, \"transactions\": {\"size\": ${EMBED_DIM}, \"distance\": \"Cosine\"}}}"
    echo "Created collection: $collection"
  fi
done
