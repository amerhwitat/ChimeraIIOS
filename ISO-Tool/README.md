# Chimera II OS ISO-Tool Integration

The Chimera II OS repository can be consumed by the ISO-Tool build/image orchestrator. ISO-Tool uses a fail-forward job policy: an independent compile, assembly, documentation, or boot-artifact runtime failure is recorded in the live log and the next independent job continues.

## Runtime-error behavior

- Job-level failures are caught and logged with type/message.
- Failed/skipped jobs advance the overall progress counter.
- Independent jobs continue.
- Fatal image-integrity, staging, authorization, or safety failures may still stop the operation.
- The GUI shows a live operation-details section while work is running.

## GUI implementations

ISO-Tool provides Python/Tkinter, C# WPF, and native VC++ Win32 front ends. Each exposes a cumulative progress bar, status text, and detailed live log.

See the canonical implementation in `amerhwitat/nlp/ISO-Tool/` and the local Chimera II OS boot-planner definitions under `ISO-Tool/` when synchronized into this repository.
