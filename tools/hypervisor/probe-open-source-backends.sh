#!/usr/bin/env bash
set -Eeuo pipefail

# Capability inventory only. Detection does not imply the OS has integrated
# the backend or that any guest has booted successfully.
host="$(uname -s 2>/dev/null || printf unknown)"
printf 'host_os=%s\n' "$host"
printf '%-20s %-14s %s\n' BACKEND STATUS DETAIL

probe() {
  local backend="$1" binary="$2" detail="$3"
  if command -v "$binary" >/dev/null 2>&1; then
    printf '%-20s %-14s %s (%s)\n' "$backend" detected "$detail" "$(command -v "$binary")"
  else
    printf '%-20s %-14s %s\n' "$backend" unavailable "$detail"
  fi
}

probe qemu-tcg qemu-system-x86_64 'QEMU binary; TCG emulation capability only'
if [[ "$host" == Linux ]] && [[ -e /dev/kvm ]]; then
  if [[ -r /dev/kvm && -w /dev/kvm ]]; then
    printf '%-20s %-14s %s\n' kvm candidate '/dev/kvm is readable/writable; verify CPU and permission policy'
  else
    printf '%-20s %-14s %s\n' kvm blocked '/dev/kvm exists but current user lacks read/write access'
  fi
else
  printf '%-20s %-14s %s\n' kvm unavailable 'requires Linux /dev/kvm and hardware/host support'
fi
probe xen xl 'Xen xl toolstack; check Xen host/dom0 state separately'
probe bhyve bhyve 'FreeBSD bhyve; FreeBSD host required'
probe virtualbox VBoxManage 'VirtualBox base package; extension pack excluded from OSS claim'
probe firecracker firecracker 'Firecracker VMM; Linux/KVM and jailer policy required'
probe cloud-hypervisor cloud-hypervisor 'Cloud Hypervisor; Linux/KVM required'
probe crosvm crosvm 'crosvm; Linux/KVM and device sandbox required'
probe acrn acrn-dm 'ACRN device model; supported embedded platform required'
probe jailhouse jailhouse 'Jailhouse; supported Linux root cell/platform required'
probe openbsd-vmm vmd 'OpenBSD vmm/vmd; OpenBSD host required'
probe netbsd-nvmm nvmmctl 'NetBSD NVMM tooling; NetBSD host required'

cat <<'NOTICE'
NOTE: This is host-tool discovery, not an integration or guest-boot test.
QEMU TCG is software emulation, not hardware virtualization. Backends not
listed by this script (including board/firmware-managed Bao and Hafnium
deployments) require platform-specific validation. Never enable a backend
or claim support solely because an executable is present.
NOTICE
