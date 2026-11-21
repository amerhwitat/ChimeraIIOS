# RNN/chat adapter and six-case production acceptance

The existing `tools/cognition/trainable_rnn_lm.py` is a research-scale character-level RNN, not a foundation LLM. `koronos_chat.py` is a userspace adapter for a separately installed OpenAI-compatible inference server. It does not bundle weights or claim a model has been trained. AI inference stays in userspace; generated text is untrusted data and is never executed.

## Production acceptance

The contract covers Live, Installer, and Recovery on both BIOS and UEFI. All six cases remain `NOT_RUN` until the production ISO and real serial/debug logs establish:
- a CPL3-originated `USER INIT SYSCALL` for the expected target and a nonzero PID;
- a `USERSPACE READY` acknowledgement from that same target and PID;
- ISO SHA-256, kernel identity/hash, firmware, QEMU version, and artifact/log references.

Separate required evidence:
- Live starts the real Aurora desktop session.
- Installer completes, reboots, and boots the installed system.
- Recovery performs and verifies a real operation on a disposable test image.
- AP startup and genuinely concurrent per-CPU progress demonstrate SMP; a configured `-smp` count or sequential scheduler simulation is insufficient.

Static contract tests and kernel/QEMU smoke tests are not production userspace acceptance. Do not promote or publish a release until the unchanged production verifier and the six real cases pass.

## Reference designs and licensing

- Linux kernel documentation: https://docs.kernel.org/
- Windows user/kernel isolation: https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode
- Apple XNU source and per-file license notices: https://github.com/apple-oss-distributions/xnu
- llama.cpp inference runtime (MIT-licensed runtime; model weights have separate terms): https://github.com/ggml-org/llama.cpp

Use these as architecture references and perform file-level license review before importing code. Do not bulk-copy incompatible kernel code.
