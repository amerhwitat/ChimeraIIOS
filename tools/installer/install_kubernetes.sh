#!/usr/bin/env bash
set -euo pipefail
# Install Kubernetes administration/runtime prerequisites on a Chimera II OS Linux installation.
# This script installs packages only; cluster creation remains an explicit operation.

if [[ "${EUID}" -ne 0 ]]; then echo "Run as root (or through sudo)." >&2; exit 1; fi
command -v apt-get >/dev/null 2>&1 || { echo "This installer currently targets Debian/Ubuntu-compatible Chimera installations." >&2; exit 2; }
apt-get update
apt-get install -y ca-certificates curl gpg containerd
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.37/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
printf '%s\n' 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /' > /etc/apt/sources.list.d/kubernetes.list
apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
systemctl enable --now containerd
systemctl enable kubelet
printf '%s\n' 'Kubernetes prerequisites installed. Use kubeadm init/join explicitly to create or join a cluster.'
