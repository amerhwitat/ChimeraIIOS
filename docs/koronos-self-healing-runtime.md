# Koronos self-healing runtime and learning roadmap

## First implementation: safe recovery controller

`tools/runtime/koronos-self-heal.py` consumes JSONL telemetry events (`heartbeat`,
`service_failed`, `service_stalled`, `kernel_fault`, and `boot_marker`) and emits a
machine-readable recovery report. It detects missing heartbeats and repeated failures.
It does not assume systemd exists on the bare-metal target.

Default behavior is observation only. A restart can execute only when all three gates
are satisfied: the service is explicitly allowlisted in the policy, the operator passes
`--apply`, and an adapter command is supplied. Repeated failures outside the restart
budget are reported for quarantine/manual intervention. Kernel faults are evidence for
diagnosis, never authorization for a model-generated kernel patch or destructive action.

## Learning stages

1. **Telemetry first:** timestamped scheduler, process, service, memory, IPC, boot-stage,
   and fault events; include boot ID, CPU ID, task/service ID, error code, and correlation ID.
2. **Deterministic baseline:** heartbeat deadlines, dependency-aware service recovery,
   bounded restart budgets, circuit breakers, audit records, and rollback.
3. **RNN/sequence model:** train on labeled event sequences to estimate stall/failure
   risk. Use offline train/validation splits and calibrated thresholds; keep deterministic
   safety policy authoritative.
4. **LLM diagnosis:** provide redacted logs, symbols, source excerpts, and test output to
   produce ranked hypotheses and candidate patches. The LLM must not run commands or write
   kernel memory; patches go through a branch and review.
5. **Reinforcement learning:** initially offline replay/simulation only. Score recovery
   choices by verified recovery, recurrence, service availability, latency, and side effects.
   Do not explore on production systems or let online rewards alter safety constraints.
6. **Acceptance:** unit tests; fault-injection tests; QEMU boot and service-recovery tests;
   verify `USERSPACE READY: init pid=...`; verify Live/Installer/Recovery separately;
   then measure recurrence and rollback behavior. A successful compile alone is not proof.

## Telemetry example

```jsonl
{"type":"heartbeat","service":"kore.service","timestamp":1800000000}
{"type":"service_stalled","service":"kore.service","timestamp":1800000035,"reason":"heartbeat-timeout"}
```

Dry run:

```sh
python3 tools/runtime/koronos-self-heal.py --policy system/services/self-heal-policy.json --events runtime-events.jsonl
```

A deployment-specific adapter is deliberately required for execution. Do not point it at
arbitrary shell input. Keep service names allowlisted, audit output persistent, and recovery
commands narrowly scoped to the target's trusted service manager.

## Current limitations

This adds a deterministic telemetry triage/recovery boundary, not a trained neural network.
No RNN weights, LLM runtime/model, reinforcement-learning policy, production Koronos hook,
or successful QEMU self-heal run is claimed by these files. Integrate the event ABI with
the actual kernel/runtime after confirming the current scheduler and service-manager interfaces.
