# Koronos self-healing runtime and ISA-aware learning context

`tools/runtime/koronos-learning-context.py` normalizes the ISA database, CPU facts,
native command registrations, and compatibility command catalog into
`KORONOS-LEARNING-CONTEXT-1`.

Run:
```sh
python3 tools/runtime/koronos-learning-context.py --mode both --output /tmp/koronos-learning-context.json
python3 -m json.tool /tmp/koronos-learning-context.json >/dev/null
```

Profiles include native host architecture, pointer width, CPU model/flags, catalogued
instruction forms, native command registrations, compatibility command names, and target
architecture aliases. RNN inputs can include temporal event sequences and ISA/mode fields;
LLM diagnosis context includes CPU/ISA/command/recovery evidence; offline RL state includes
service state, restart budget, provider availability, and verified prior outcomes.

This is deterministic feature extraction, **not a trained model**. The ISA catalog is
partial. Presence in the catalog does not mean an instruction is implemented or runnable.
Foreign binaries require an actual compatibility provider, ABI/runtime and validated
backend. Models may recommend hypotheses or rank bounded actions, but cannot execute
commands, patch kernel code, or mutate safety policy.