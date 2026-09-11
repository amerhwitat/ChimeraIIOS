# Chimera II OS ISO-Tool Integration

The Chimera II OS repository can be consumed by the ISO-Tool build/image orchestrator.

## Workflow entry points

- `analyze-source` — inspect the Chimera II OS source tree.
- `build-compiled-images` — compile/assemble authorized boot, kernel and application artifacts.
- `import-boot-image` — inspect and stage a bounded boot sector or image artifact.
- `build-iso` — construct the configured Live/Install ISO or IMG.
- `validate-image` — validate the generated image and checksums.

## Runtime resilience

ISO-Tool uses fail-forward isolation for recoverable independent job failures. Errors are logged with type/message, progress advances, and subsequent independent jobs continue. Fatal image-integrity, staging, authorization, and safety failures may still stop publication.

## Offline and network recovery

Local Chimera II OS source builds do not require Internet access. Remote source acquisition can monitor connectivity, wait for recovery, and retry network operations according to the configured retry policy. Retry activity is visible in the GUI's live operation-details pane.

## Boot image import

The import feature treats imported boot sectors as inert data. It does not execute imported boot code. Bounded regions can be staged for an explicitly selected boot profile.

## GUI implementations

ISO-Tool provides Python/Tkinter, C# WPF, and native VC++ Win32 front ends. Each exposes cumulative progress, status text and detailed live operation logging.

The canonical implementation is in `amerhwitat/nlp/ISO-Tool/`.
