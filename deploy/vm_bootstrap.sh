#!/usr/bin/env bash
# Run ON the VM once (via `gcloud compute ssh VM_NAME --zone=ZONE`).
# Installs Docker + compose plugin. Safe to re-run.
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  echo "Docker installed. Log out and back in (or run 'newgrp docker') for group membership to take effect."
else
  echo "Docker already installed, skip."
fi

# Plain `sudo systemctl ...` fails on this VM (sudo can't exec it directly, even by
# absolute path) — piping into `sudo sh -c` gets a real root shell instead, sidestepping that.
echo "systemctl enable --now docker" | sudo sh
echo "Docker running. Next: copy the repo over and run deploy/vm_deploy.sh"
