#!/usr/bin/env bash
# Run locally (not on the VM). Requires `gcloud` installed and `gcloud auth login` done.
# Usage: bash deploy/gcp/vm_ssh.sh
set -euo pipefail

PROJECT_ID="neurona-491301"
VM_NAME="instance-20260421-014232"
ZONE="us-central1-f"

gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT_ID"