# Chimera II OS Native Security

Chimera II adds defense-in-depth malware, virus and spyware protection plus host firewall profiles.

## Detection
- SHA-256 intelligence matches
- EICAR regression signature
- local heuristics for suspicious scripts, double extensions and PowerShell download behavior
- optional ClamAV
- optional YARA
- optional local RNN feature scorer
- quarantine and audit-ready JSON output

On-access protection can use Linux fanotify/ClamAV when the kernel and daemon support it.

## Intelligence updates
Security intelligence is data-only, atomic, SHA-256 verified and signature-gated by policy. The update cadence is six hours. RNN model artifacts are model data, never executable code. The ML layer cannot replace the scanner, firewall, kernel or policy.

## Firewall
nftables profiles: private, public, wide-area, and domain. All default to deny inbound and forwarding traffic and allow established return traffic. Domain rules are conservative and must be extended through audited policy.

## Safety
This stack is defense-oriented. It does not execute downloaded samples, auto-modify its own scanner, or treat an LLM as a root authority. Suspicious files are scored and can be quarantined.

## Build/test
The security test suite compiles the Python modules and validates EICAR detection and firewall rendering without applying firewall changes.
