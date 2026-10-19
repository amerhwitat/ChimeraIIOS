# RNN research model, chat boundary, and production acceptance

Chimera already contains `tools/cognition/trainable_rnn_lm.py`, a small trainable character-level vanilla RNN. It is a research/ranking model, not a foundation LLM. Real chat requires a separately trained model/runtime and a userspace provider adapter; do not describe catalog ranking or the RNN alone as an LLM.

AI inference stays in userspace. Kernel code must not execute generated text or accept model output as boot, syscall, firmware, or memory-management instructions.

The six-case contract is Live/Installer/Recovery × BIOS/UEFI. All cases are NOT_RUN. Static schema validation is not a boot test. Runtime PASS requires a real production ISO, CPL3-originated init syscall, matching nonzero PID READY acknowledgement, target and firmware identity, ISO/kernel hashes, and serial/debug evidence. Live must start Aurora; Installer must complete/reboot/boot installed OS; Recovery must perform a real operation. Genuine AP-backed concurrent SMP remains a separate gate.

References: https://docs.kernel.org/ ; https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode ; https://github.com/apple-oss-distributions/xnu ; https://github.com/ggml-org/llama.cpp
