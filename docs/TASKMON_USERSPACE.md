# TaskMon userspace utility

TaskMon is a standard-library-only hosted process and memory KPI viewer intended as a first reusable userspace diagnostic app for OctavianOS and ChimeraIIOS.

## Run

```sh
python3 tools/userspace/taskmon.py
python3 tools/userspace/taskmon.py --watch 1 --sort memory --limit 50
python3 tools/userspace/taskmon.py --json
python3 -m unittest discover -s tests -p 'test_taskmon.py'
```

Linux reads `/proc/meminfo`, `/proc/[pid]/stat` and `/proc/[pid]/status`. Windows uses PowerShell/CIM and reports working-set and virtual-size counters. JSON mode is intended for dashboards and future GUI/task-manager frontends.

## KPI semantics and limitations

- **RAM used** = total RAM minus available RAM where the host exposes that estimate.
- **RSS / working set** is resident physical memory attributed to a process.
- **Virtual size** is address-space size; it is not equivalent to committed memory or physical RAM.
- Linux swap counters are exposed when present. Windows swap metrics are currently unavailable in this adapter.
- CPU percentage, page-fault rates, commit limits, per-process page tables, allocation failures, OOM events, and kernel/user memory splits are not yet implemented.
- This is a hosted utility, **not** evidence that native Koronos has procfs, process enumeration, virtual-memory accounting, or a working production initramfs handoff. Native integration requires a stable kernel telemetry ABI or procfs-compatible service and acceptance tests against actual native processes.

Do not use this tool's host process list to satisfy bare-metal OS release gates.
