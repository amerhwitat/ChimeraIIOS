# Chimera II OS Resource and Reboot Policy

## Small-memory knowledge database

Knowledge storage is **disk-first and bounded in RAM**. JSON remains the interchange/audit representation, while columnar data is stored on disk. Only bounded metadata, indexes and hot query results belong in memory. Large documents are streamed and embeddings may be memory-mapped or disk-backed.

The default knowledge cache is limited to 4096 metadata entries and 2% of system RAM. Provenance and hashes are retained even when content is evicted.

Apache Parquet is a column-oriented format intended for efficient storage/retrieval with compression and encoding, so Chimera can keep bulk knowledge on storage and project only needed columns into memory.

## Opportunistic background work

`chm-resource-manager` monitors CPU, memory and I/O pressure. Background work is allowed to expand when the machine is quiet and is reduced or paused when pressure rises. The design reserves interactive capacity rather than attempting to consume every free cycle.

The Linux PSI model provides CPU, memory and I/O pressure measurements and supports dynamic workload management; Chimera uses the same concept for its host-compatible implementation.

## Reboot-required patches

A staged patch may create `/run/chimera/reboot.pending`. The patch engine never silently reboots.

Aurora/CLI exposes:
- `chm-reboot status`
- `chm-reboot now`
- `chm-reboot later`
- `chm-reboot cancel`

`now` records user approval; actual hardware/platform reboot remains delegated to Koronos/Aegis. `later` keeps the OS running and preserves the pending request for the next user decision.

## Safety and stability

Kernel, bootloader and security-policy replacements remain explicitly privileged. Resource pressure can pause background work instead of forcing memory reclamation that harms foreground applications. No policy here disables the host's normal OOM/reclaim safety mechanisms.
