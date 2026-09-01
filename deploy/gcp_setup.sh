#!/usr/bin/env bash
# Run locally (not on the VM). Requires `gcloud` installed and `gcloud auth login` done.
# Fill in the 4 values below, then: bash deploy/gcp_setup.sh
set -euo pipefail

PROJECT_ID="neurona-491301"
VM_NAME="instance-20260421-014232"
ZONE="us-central1-f"          # e.g. asia-southeast2-a
REGION="us-central1"        # e.g. asia-southeast2 (zone without the trailing -a/-b/-c)

gcloud config set project "$PROJECT_ID"

# 1. Reserve the VM's current external IP so it survives reboots.
CURRENT_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "Current external IP: $CURRENT_IP"

EXISTING_RESERVATION=$(gcloud compute addresses list --regions="$REGION" \
  --filter="address=$CURRENT_IP" --format='get(name)' | head -n1)

if [ -n "$EXISTING_RESERVATION" ]; then
  echo "IP already reserved as '$EXISTING_RESERVATION' (shared with another subdomain on this VM), skip."
elif ! gcloud compute addresses describe "${VM_NAME}-ip" --region="$REGION" >/dev/null 2>&1; then
  gcloud compute addresses create "${VM_NAME}-ip" --region="$REGION" --addresses="$CURRENT_IP"
  echo "Reserved static IP: $CURRENT_IP"
else
  echo "Static IP already reserved, skip."
fi

# 2. Firewall: allow 80/443 from anywhere (needed for Let's Encrypt + public HTTPS access).
if ! gcloud compute firewall-rules describe allow-http-https >/dev/null 2>&1; then
  gcloud compute firewall-rules create allow-http-https \
    --allow=tcp:80,tcp:443 \
    --direction=INGRESS \
    --target-tags=http-server,https-server \
    --description="Staging pilot: inbound HTTP/HTTPS for TestFlight smoke testing"
  echo "Created firewall rule allow-http-https."
else
  echo "Firewall rule allow-http-https already exists, skip."
fi

# Tag the VM so the firewall rule above applies to it.
gcloud compute instances add-tags "$VM_NAME" --zone="$ZONE" --tags=http-server,https-server

echo
echo "Done. Point your DNS A record at: $CURRENT_IP"
echo "Then SSH in and run deploy/vm_bootstrap.sh + deploy/vm_deploy.sh (see deploy/README.md)."
