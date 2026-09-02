#!/usr/bin/env bash
# Run on the server/VM to diagnose and free Docker disk space.
# Usage:
#   bash scripts/docker_disk_cleanup.sh           # diagnose only (safe, no changes)
#   bash scripts/docker_disk_cleanup.sh --prune    # diagnose + prune unused images/containers/cache
#   bash scripts/docker_disk_cleanup.sh --prune --volumes  # also prune unused volumes (drops unreferenced volume data)
set -euo pipefail

PRUNE=false
PRUNE_VOLUMES=false
for arg in "$@"; do
    case "$arg" in
        --prune) PRUNE=true ;;
        --volumes) PRUNE_VOLUMES=true ;;
        *) echo "Unknown arg: $arg" >&2; exit 1 ;;
    esac
done

echo "=== Disk usage (df -h) ==="
df -h

echo
echo "=== Docker disk usage ==="
docker system df -v

echo
echo "=== BuildKit cache usage ==="
docker buildx du

if [ "$PRUNE" = false ]; then
    echo
    echo "Diagnosis only. Re-run with --prune to reclaim space (add --volumes to also drop unused volumes)."
    exit 0
fi

echo
echo "=== Pruning unused containers, images, networks ==="
docker system prune -af

echo
echo "=== Pruning BuildKit build cache ==="
docker buildx prune -af

if [ "$PRUNE_VOLUMES" = true ]; then
    echo
    echo "=== Pruning unused volumes ==="
    docker volume prune -af
fi

echo
echo "=== Disk usage after cleanup ==="
df -h
