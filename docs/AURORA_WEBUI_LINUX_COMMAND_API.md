# Aurora Web UI Linux Command API

The Web UI and standalone console consume the same `config/linux-command-registry.json` capability model.

## WebSocket endpoint

`/api/v1/terminal`

Client request:

```json
{"type":"execute","command":"ls -la","session":"optional-session-id"}
```

Server events:

```json
{"type":"stdout","data":"..."}
{"type":"stderr","data":"..."}
{"type":"exit","code":0}
{"type":"error","code":"CAPABILITY_DENIED","message":"..."}
```

## Security boundary

The browser cannot execute arbitrary host commands directly. The terminal service parses the command, resolves it through the capability registry, applies session/user policy, checks privileged capabilities, and executes inside the selected Chimera environment/container/VM. `sudo`, mount/partition operations, ownership changes, and other privileged operations require explicit capabilities.

## Performance

- One event loop per service shard where practical.
- Bounded worker pools for CPU-heavy commands.
- Async I/O for network/file streams.
- Backpressure on WebSocket output.
- Cancellation propagated to the child/process group.
- Per-session buffers rather than a global lock.
- Optional CPU affinity for benchmarked workloads.
- Deterministic serial mode for tests and debugging.

## Desktop integration

Aurora Glass, Windows-like, macOS-like, Windows 95-like, Linux-like, and Arabic/English desktop shells use this same API. The visual desktop is therefore independent of command implementation while retaining a common terminal and system-management surface.
