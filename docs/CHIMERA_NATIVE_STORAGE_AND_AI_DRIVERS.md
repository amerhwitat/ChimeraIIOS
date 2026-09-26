# Chimera II OS native storage and hardware-learning policy

## Native QFS block filesystem

Chimera II OS now declares **QFS** as its native filesystem target.

The default allocation block is **4 KiB (4096 bytes)**. The installer can select 8, 16, 32, or 64 KiB explicitly. The selected value is recorded in the QFS superblock and in the installation configuration.

The native installer refuses a block size larger than the running kernel page size because filesystems with blocks larger than the kernel page size may not be mountable. This is consistent with the constraints documented for ext4 and XFS. See the Linux ext4 documentation and mkfs documentation for the corresponding page-size limitation. citeturn0search0turn0search2turn0search3

Examples:

```bash
# Default 4 KiB
tools/storage/chimera-qfs image.qfs --size $((8*1024*1024*1024)) --force

# Explicit 16 KiB research/installation target
tools/storage/chimera-qfs image.qfs --size $((16*1024*1024*1024)) --block-size 16384 --force
```

The current implementation provides the native format/superblock and formatter contract. It does **not** claim that the complete QFS VFS, directory/extent allocator, journal, snapshot, and recovery implementation is finished.

## Hardware study and driver recommendations

At boot/first boot Chimera can collect:

- PCI device IDs and currently bound kernel drivers
- USB devices
- DMI/system information
- sysfs topology
- block devices and physical/logical sector geometry
- CPU architecture and kernel page size
- loaded kernel modules

The inventory is passed to an auditable recurrent evidence scorer. It produces:

`/var/lib/chimera/drivers/ai-recommendations.json`

The recommendation engine currently uses a deterministic recurrent state model as the safe baseline and exposes a production hook for a trained GRU/Transformer/LLM node. It is deliberately **recommendation-only**: it does not silently install an arbitrary driver because a model scored it highly.

Driver selection policy remains:

1. in-tree Chimera/Koronos-compatible driver
2. signed distribution package
3. signed firmware
4. fwupd/LVFS
5. verified vendor repository

Unsigned vendor installers, unknown kernel modules, and arbitrary curl-to-shell installation are prohibited by policy.

The Linux kernel exposes driver binding through sysfs, which is useful for controlled device/driver matching and explicit administrative overrides. citeturn0search10

## 128D hardware reasoning direction

The recommendation record is designed to preserve evidence separately from model state so later Chimera Nucleus/RNN/LLM nodes can learn a hardware representation rather than treating a generated recommendation as ground truth.

Future training inputs can include the device vector, driver binding, firmware state, I/O geometry, thermal/power state, benchmark telemetry, and successful/failed driver outcomes.
