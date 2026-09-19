#!/usr/bin/env bash
set -u
fail=0
check() {
  if command -v "$1" >/dev/null 2>&1; then
    printf '%-18s OK\n' "$1"
  else
    printf '%-18s MISSING\n' "$1"
    fail=1
  fi
}
for tool in kubectl kubeadm oc openstack aws az gcloud terraform; do check "$tool"; done
exit "$fail"
