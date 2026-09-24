[CmdletBinding()]
param([string]$Architecture="x86_64",[string]$Disk="$env:USERPROFILE\ChimeraIIOS\chimera-$Architecture.qcow2",[int]$Memory=4096,[int]$CPUs=2)
$ErrorActionPreference="Stop"
$qemu=switch($Architecture){"x86_64"{"qemu-system-x86_64.exe"}"x86"{"qemu-system-i386.exe"}"aarch64"{"qemu-system-aarch64.exe"}"riscv64"{"qemu-system-riscv64.exe"}default{throw "Unsupported architecture: $Architecture"}}
if(-not(Get-Command $qemu -ErrorAction SilentlyContinue)){throw "QEMU not found: $qemu"}
New-Item -ItemType Directory -Force -Path (Split-Path $Disk)|Out-Null
if(-not(Test-Path $Disk)){& qemu-img.exe create -f qcow2 $Disk 32G|Out-Null}
& $qemu -m $Memory -smp $CPUs -name Chimera-II-OS -drive "file=$Disk,if=virtio,format=qcow2" -nic user @args
